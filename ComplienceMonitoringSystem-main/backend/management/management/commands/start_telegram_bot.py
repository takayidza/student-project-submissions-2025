import asyncio
import logging
from django.core.management.base import BaseCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from django.conf import settings
from django.contrib.auth import authenticate
from asgiref.sync import sync_to_async
from management.models import User, Device, InstalledSoftware  # Import the Software model
from management.scanners.compliance_scanner import ComplianceScanner

from datetime import datetime, timedelta
import json
import subprocess  # Import the subprocess module

# Conversation states
USERNAME, PASSWORD, AUTHENTICATED = range(3)

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


# ==================== AUTHENTICATION FLOW ====================

async def start(update, context):
    """Start the authentication process"""
    await update.message.reply_text(
        "🔐 Please authenticate with your Django account.\n"
        "Enter your username:"
    )
    return USERNAME


async def username_received(update, context):
    """Store username and prompt for password"""
    context.user_data['username'] = update.message.text
    await update.message.reply_text("🔑 Now enter your password:")
    return PASSWORD


async def authenticate_user(update, context):
    """Verify credentials and authenticate user"""
    username = context.user_data['username']
    password = update.message.text

    user = await sync_to_async(authenticate)(
        username=username,
        password=password
    )

    if user is not None:
        user.telegram_chat_id = update.message.chat.id
        await sync_to_async(user.save)()

        await update.message.reply_text(
            f"✅ Authentication successful!\n"
            f"Welcome, {user.username}!"
        )
        return await authenticated_menu(update, context)
    else:
        await update.message.reply_text(
            "❌ Authentication failed. Please check your credentials.\n"
            "Type /start to try again."
        )
        return ConversationHandler.END


async def cancel(update, context):
    """Cancel the authentication process"""
    await update.message.reply_text(
        "Authentication cancelled. Type /start to begin again."
    )
    return ConversationHandler.END


# ==================== AUTHENTICATED COMMANDS ====================

async def get_user_devices(update, context):
    """Get and display the devices associated with the authenticated user."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_chat_id=update.message.chat.id)
        devices = await sync_to_async(list)(Device.objects.filter(user=user))

        if devices:
            device_list = "\n".join([f"- {device.hostname} ({device.ip_address})" for device in devices])
            message = f"Your registered devices:\n{device_list}"
        else:
            message = "You have no devices registered."

        await update.message.reply_text(message)
    except User.DoesNotExist:
        await update.message.reply_text("⚠️ User not found. Please log in again with /start.")
    except Exception as e:
        logger.error(f"Error fetching user devices: {e}", exc_info=True)
        await update.message.reply_text("❌ Failed to fetch your devices. Please try again.")
    return AUTHENTICATED


async def get_installed_software(update, context):
    """Get and display the installed software on the user's devices."""
    try:
        user = await sync_to_async(User.objects.get)(telegram_chat_id=update.message.chat.id)
        devices = await sync_to_async(list)(Device.objects.filter(user=user))

        if not devices:
            await update.message.reply_text("You have no devices registered.")
            return AUTHENTICATED

        software_list = {}
        for device in devices:
            try:
                # Fetch installed software using the related manager.
                softwares = await sync_to_async(list)(device.installedsoftware.all())  # Fetch all related software
                software_names = [software.name for software in softwares] # Extract the names.

                software_list[device.hostname] = software_names

            except Exception as e:
                logger.error(f"Error getting software list from {device.hostname}: {e}")
                software_list[device.hostname] = [f"Error: {e}"]

        # Format the output for the Telegram message.
        message = "Installed Software:\n"
        for hostname, software in software_list.items():
            message += f"\n--- {hostname} ---\n"
            if software:
                message += "\n".join(software)
            else:
                message += "No software information available."

        # Telegram messages have a max length; truncate if needed
        if len(message) > 4000:
            message = message[:3900] + "\n...(truncated)"
        await update.message.reply_text(message)

    except User.DoesNotExist:
        await update.message.reply_text("⚠️ User not found. Please log in again with /start.")
    except Exception as e:
        logger.error(f"Error fetching installed software: {e}", exc_info=True)
        await update.message.reply_text("❌ Failed to fetch installed software. Please try again.")
    return AUTHENTICATED



async def authenticated_menu(update, context):
    """Show authenticated user menu"""
    user = await sync_to_async(User.objects.get)(
        telegram_chat_id=update.message.chat.id
    )

    menu_text = (
        f"👋 Welcome, {user.username} (Role: {user.role})!\n\n"
        "Available commands:\n"
        "/scan - Run compliance scan (Admin only)\n"
        "/status - Check your devices\n"
        "/mydevices - List your registered devices\n"
        "/software - List installed software\n"
        "/logout - End your session"
    )

    await update.message.reply_text(menu_text)
    return AUTHENTICATED


@sync_to_async(thread_sensitive=False)
def scan_single_device(device):
    """Run a compliance scan for a single device in a thread-safe way."""
    scanner = ComplianceScanner()
    try:
        is_compliant, violations = scanner.scan_device(device)
        return is_compliant, violations
    except Exception as e:
        logger.error(f"Error scanning device {device.hostname}: {e}")
        return None, None



async def scan_devices(update, context):
    """Run compliance scan on all devices"""
    try:
        user = await sync_to_async(User.objects.get)(telegram_chat_id=update.message.chat.id)

        if user.role != 'Admin':
            await update.message.reply_text("❌ Only admins can run scans.")
            return AUTHENTICATED

        # Rate limiting
        from datetime import timedelta
        from django.utils import timezone
        # if user.last_scan and user.last_scan > timezone.now() - timedelta(seconds=20):
        #     await update.message.reply_text("❌ You can only run scans every 30 minutes.")
        #     return AUTHENTICATED

        await update.message.reply_text("🔍 Starting compliance scan...")

        # Fetch all devices
        devices = await sync_to_async(list)(Device.objects.all())

        batch_size = 5
        for i in range(0, len(devices), batch_size):
            batch = devices[i:i + batch_size]

            tasks = [scan_single_device(device) for device in batch]
            results = await asyncio.gather(*tasks)

            for device, (is_compliant, violations) in zip(batch, results):
                if is_compliant is None:
                    await update.message.reply_text(f"❌ Failed to scan {device.hostname}")
                    continue

                if is_compliant:
                    message = f"✅ {device.hostname} - COMPLIANT"
                else:
                    # Send raw JSON violations
                    violation_json = json.dumps(violations, indent=2)
                    message = (
                        f"⚠️ {device.hostname} - NON-COMPLIANT\n"
                        f"Violations ({len(violations)}):\n"
                        f"```json\n{violation_json}\n```"
                    )

                # Telegram messages have a max length; truncate if needed
                if len(message) > 4000:
                    message = message[:3900] + "\n...(truncated)"

                await update.message.reply_text(message, parse_mode='Markdown')

        # Update last scan time
        user.last_scan = datetime.now()
        await sync_to_async(user.save)()

        await update.message.reply_text("✅ Scan completed!")

    except Exception as e:
        logger.error(f"Scan error: {e}", exc_info=True)
        await update.message.reply_text("❌ Scan failed. Please check logs.")

    return AUTHENTICATED


async def logout(update, context):
    """Clear user session"""
    user = await sync_to_async(User.objects.get)(
        telegram_chat_id=update.message.chat.id
    )
    user.telegram_chat_id = None
    await sync_to_async(user.save)()

    await update.message.reply_text(
        "👋 You've been logged out. Use /start to authenticate again."
    )
    return ConversationHandler.END


# ==================== BOT SETUP ====================

class Command(BaseCommand):
    help = 'Starts the authenticated Telegram bot with scanning capabilities'

    async def error_handler(self, update, context):
        """Log errors caused by updates."""
        logger.error(f'Update {update} caused error {context.error}', exc_info=True)
        if update and update.message:
            await update.message.reply_text(
                "⚠️ An error occurred. Please try again or contact support."
            )

    def handle(self, *args, **options):
        # Create the Application
        application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

        # Main conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler("start", start)],
            states={
                USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_received)],
                PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, authenticate_user)],
                AUTHENTICATED: [
                    CommandHandler("scan", scan_devices),
                    CommandHandler("logout", logout),
                    CommandHandler("status", authenticated_menu),
                    CommandHandler("mydevices", get_user_devices),
                    CommandHandler("software", get_installed_software),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, authenticated_menu)
                ],
            },
            fallbacks=[CommandHandler("cancel", cancel)],
            conversation_timeout=300,  # 5 minute timeout
        )

        application.add_handler(conv_handler)
        application.add_error_handler(self.error_handler)

        # Start the bot
        self.stdout.write(self.style.SUCCESS('Starting authenticated bot...'))
        application.run_polling()
