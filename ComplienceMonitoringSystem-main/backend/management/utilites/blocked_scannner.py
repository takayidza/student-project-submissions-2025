from django.db.models import Q
from django.utils import timezone
from management.models import Device, InstalledSoftware, BlockedSoftware, Notification, User, Policy
import logging

logger = logging.getLogger(__name__)

def check_blocked_software_and_update_device(device):
    """
    Checks if any installed software on a device is in the blocked software list.
    If blocked software is found, it makes the device non-compliant and updates
    the status of the blocked software to 'blocked'.

    Args:
        device (Device): The Device instance to check.

    Returns:
        bool: True if blocked software was found and actions were taken, False otherwise.
    """
    blocked_found = False
    notifications = []
    hostname = getattr(device, 'hostname', 'unknown_device')  # Safely get hostname for logging

    logger.info(f"Checking for blocked software on device: {hostname} (ID: {device.id})")

    for installed_software in device.installedsoftware.all():
        software_name = getattr(installed_software, 'name', 'unknown_software')
        software_version = getattr(installed_software, 'version', 'unknown_version')
        software_publisher = getattr(installed_software, 'publisher', 'unknown_publisher')

        logger.debug(f"Checking installed software: {software_name} ({software_version}) by {software_publisher}")

        # Check if the installed software matches any active blocked software
        blocked_software_matches = BlockedSoftware.objects.filter(
            active=True,
            name__iexact=software_name,
            publisher__iexact=software_publisher,
            applicable_os__in=['all', device.os]
        )

        if blocked_software_matches.exists():
            blocked_found = True
            logger.warning(
                f"Blocked software found on {hostname}: "
                f"{software_name} ({software_version}) by {software_publisher}"
            )

            # Mark the device as non-compliant if not already
            if device.status != 'compliant':
                device.make_non_compliant()
                device.save()  # Save the device status immediately
                notifications.append(
                    Notification(
                        user=device.user,
                        device=device,
                        notification_type='non-compliant',
                        message=f"Device {hostname} marked as non-compliant due to blocked software: {software_name}.",
                        timestamp=timezone.now()
                    )
                )
                # Notify Admins as well
                for admin in User.objects.filter(role='Admin'):
                    policy , created= Policy.objects.get_or_create(name="Blocked Software Policy", description="System generated policy to automatically picks blocked software from devices")
                    notifications.append(
                        Notification(
                            user=admin,
                            device=device,
                            notification_type='non-compliant',
                            policy = policy,
                            message=f"Device {hostname} marked as non-compliant due to blocked software: {software_name}.",
                            timestamp=timezone.now()
                        )
                    )
                logger.info(f"Device {hostname} marked as non-compliant.")

            # Update the installed software status to 'blocked' if not already
            if installed_software.status != 'blocked':
                installed_software.status = 'blocked'
                installed_software.save()  # Save the software status immediately
                notifications.append(
                    Notification(
                        user=device.user,
                        device=device,
                        notification_type='warning',
                        message=f"Software '{software_name} ({software_version})' on {hostname} has been blocked.",
                        timestamp=timezone.now()
                    )
                )
                # Notify Admins as well
                for admin in User.objects.filter(role='Admin'):
                    notifications.append(
                        Notification(
                            user=admin,
                            device=device,
                            notification_type='warning',
                            message=f"Software '{software_name} ({software_version})' on {hostname} has been blocked.",
                            timestamp=timezone.now()
                        )
                    )
                logger.info(f"Software '{software_name}' on {hostname} status updated to 'blocked'.")
        else:
            logger.debug(f"Installed software '{software_name}' is not in the blocked list.")

    # Bulk create notifications to improve efficiency
    if notifications:
        Notification.objects.bulk_create(notifications)
        logger.info(f"Created {len(notifications)} notifications for device {hostname}.")
    else:
        logger.info(f"No blocked software found or no status changes needed for device {hostname}.")

    return blocked_found

# Example usage (assuming you have a Device instance named 'my_device'):
# from yourapp.models import Device
# import logging
#
# logging.basicConfig(level=logging.INFO)  # Configure logging level
#
# try:
#     my_device = Device.objects.get(hostname='some_hostname')
#     if check_blocked_software_and_update_device(my_device):
#         logger.info(f"Blocked software found on {my_device.hostname}. Device marked non-compliant and software status updated.")
#     else:
#         logger.info(f"No blocked software found on {my_device.hostname}.")
# except Device.DoesNotExist:
#     logger.error("Device not found.")