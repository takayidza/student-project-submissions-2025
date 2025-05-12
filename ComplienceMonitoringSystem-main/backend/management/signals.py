from django.db.models.signals import post_save, post_delete, m2m_changed
from django.dispatch import receiver
from django.db import transaction
from .models import (
    Device,
    InstalledSoftware,
    Policy,
    PolicyCriteria,
    BlockedSoftware
)
from .scanners.compliance_scanner import ComplianceScanner
import logging

logger = logging.getLogger(__name__)


class ScanRegistry:
    """Thread-safe registry to track in-progress scans"""
    _scans_in_progress = set()

    @classmethod
    def register_scan(cls, device_id):
        if device_id in cls._scans_in_progress:
            return False
        cls._scans_in_progress.add(device_id)
        return True

    @classmethod
    def unregister_scan(cls, device_id):
        cls._scans_in_progress.discard(device_id)


def safe_scan_device(device):
    """Thread-safe device scanning with loop prevention"""
    if not ScanRegistry.register_scan(device.id):
        logger.debug(f"Scan already in progress for device {device.id}, skipping")
        return

    try:
        scanner = ComplianceScanner()
        with transaction.atomic():
            return scanner.scan_device(device)
    except Exception as e:
        logger.error(f"Error scanning device {device.id}: {str(e)}")
    finally:
        ScanRegistry.unregister_scan(device.id)


@receiver(post_save, sender=Device)
def scan_device_on_save(sender, instance, created, **kwargs):
    """Trigger scan on device save, skip during raw operations"""
    if kwargs.get('raw', False) or getattr(instance, '_no_signal', False):
        return

    # Use transaction.on_commit to defer until after save completes
    transaction.on_commit(lambda: safe_scan_device(instance))


@receiver(post_save, sender=InstalledSoftware)
@receiver(post_delete, sender=InstalledSoftware)
def scan_device_on_software_change(sender, instance, **kwargs):
    """Trigger scan when software changes, skip during raw operations"""
    if kwargs.get('raw', False) or getattr(instance, '_no_signal', False):
        return

    transaction.on_commit(lambda: safe_scan_device(instance.device))


@receiver(post_save, sender=BlockedSoftware)
@receiver(post_delete, sender=BlockedSoftware)
def scan_on_blocked_software_change(sender, instance, **kwargs):
    """Scan affected devices when blocked software changes"""
    if kwargs.get('raw', False):
        return

    def _scan_affected():
        applicable_os = instance.applicable_os
        qs = Device.objects.all()
        if applicable_os != 'all':
            qs = qs.filter(os=applicable_os)

        for device in qs.only('id'):
            safe_scan_device(device)

    transaction.on_commit(_scan_affected)


@receiver(post_save, sender=Policy)
@receiver(post_delete, sender=Policy)
@receiver(post_save, sender=PolicyCriteria)
@receiver(post_delete, sender=PolicyCriteria)
def scan_on_policy_change(sender, instance, **kwargs):
    """Scan all devices when policies change"""
    if kwargs.get('raw', False):
        return

    def _scan_all():
        for device in Device.objects.only('id'):
            safe_scan_device(device)

    transaction.on_commit(_scan_all)


@receiver(m2m_changed, sender=Device.user)
def scan_device_on_user_change(sender, instance, action, **kwargs):
    """Trigger scan when device user assignment changes"""
    if action in ['post_add', 'post_remove', 'post_clear'] and not kwargs.get('raw', False):
        transaction.on_commit(lambda: safe_scan_device(instance))


from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import sync_to_async
from .models import Notification
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)
class TelegramBot:
    BASE_URL = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/"

    @staticmethod
    def send_message(chat_id, text):
        try:
            url = TelegramBot.BASE_URL + "sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None

import threading

@receiver(post_save, sender=Notification)
def send_telegram_notification(sender, instance, created, **kwargs):
    if created and instance.user.telegram_chat_id:
        emoji = "⚠️" if instance.notification_type != 'compliant' else "✅"
        message = (
            f"{emoji} <b>New Notification</b> {emoji}\n\n"
            f"<b>Type:</b> {instance.get_notification_type_display()}\n"
            f"<b>Device:</b> {instance.device.hostname}\n"
            f"<b>Message:</b> {instance.message}\n"
            f"<b>Time:</b> {instance.timestamp.strftime('%Y-%m-%d %H:%M')}\n"
        )

        if instance.policy:
            message += f"<b>Policy:</b> {instance.policy.name}\n"

        # Run Telegram send in a separate thread
        threading.Thread(target=TelegramBot.send_message, args=(instance.user.telegram_chat_id, message)).start()

