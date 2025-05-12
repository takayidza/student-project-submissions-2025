import re
import logging
from django.db import models
from django.utils import timezone
from .models import Device, InstalledSoftware, Notification, Policy, ActivityReport, BlockedSoftware

import platform
import os
import subprocess
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

# Set up logging
logger = logging.getLogger(__name__)


def detect_os():
    """
    Detect the operating system name
    """
    try:
        return "Unknown"
    except Exception as e:
        logger.error(f"Error detecting OS: {str(e)}")
        return "Unknown"


def detect_device_type():
    """
    Detect the device type (desktop, laptop, mobile, server)
    This is a placeholder implementation and may need to be customized
    """
    try:
        machine = platform.machine().lower()
        if "arm" in machine or "aarch" in machine:
            logger.debug(f"Detected mobile device with machine type: {machine}")
            return "mobile"
        elif "x86" in machine or "amd64" in machine or "intel" in machine:
            logger.debug(f"Detected desktop device with machine type: {machine}")
            return "desktop"
        else:
            logger.debug(f"Defaulting to desktop for machine type: {machine}")
            return "desktop"
    except Exception as e:
        logger.error(f"Error detecting device type: {str(e)}")
        return "desktop"


def get_installed_software(device):
    """
    Return a list of installed software dicts based on the OS type.
    Each dict should have keys: 'name', 'version', 'publisher'
    """
    print(device, 'got device')
    try:
        software_list = list(InstalledSoftware.objects.filter(device=device).values(
            'name', 'version', 'publisher'))
        logger.debug(f"Retrieved {len(software_list)} installed software records for device {device}")
        return software_list
    except Exception as e:
        logger.error(f"Error retrieving installed software for device {device}: {str(e)}")
        return []


def get_windows_installed_software():
    """
    Retrieve installed software on Windows.
    This is a stub implementation and should be replaced with actual code.
    """
    logger.debug("Getting Windows installed software (stub implementation)")
    return [
        {'name': 'Microsoft Office', 'version': '2019', 'publisher': 'Microsoft'},
        {'name': 'Google Chrome', 'version': '90.0', 'publisher': 'Google LLC'},
    ]


def get_macos_installed_software():
    """
    Retrieve installed software on macOS.
    This is a stub implementation and should be replaced with actual code.
    """
    logger.debug("Getting macOS installed software (stub implementation)")
    return [
        {'name': 'Safari', 'version': '14.0', 'publisher': 'Apple'},
        {'name': 'Xcode', 'version': '12.4', 'publisher': 'Apple'},
    ]


def get_linux_installed_software():
    """
    Retrieve installed software on Linux.
    This is a stub implementation and should be replaced with actual code.
    """
    logger.debug("Getting Linux installed software (stub implementation)")
    return [
        {'name': 'vim', 'version': '8.2', 'publisher': 'Open Source'},
        {'name': 'gcc', 'version': '9.3', 'publisher': 'GNU'},
    ]


def scan_device_software(device):
    """
    Scan for installed software on the device and check against blocked software database
    """
    logger.info(f"Starting software scan for device {device.id} ({device.hostname})")

    try:
        installed_software = get_installed_software(device)
        logger.debug(f"Found {len(installed_software)} installed software items")

        # Get all active software-related policies and their criteria
        active_policies = Policy.objects.filter(category='Software', active=True)
        policy_criteria = []
        for policy in active_policies:
            policy_criteria.extend(policy.criteria.all())

        logger.debug(
            f"Found {len(active_policies)} active software policies with {len(policy_criteria)} total criteria")

        # Build a set of software names listed in any policy criteria for filtering
        listed_software_names = set()
        for crit in policy_criteria:
            if crit.criteria_type == 'installedsoftware__name':
                listed_software_names.add(crit.value.lower())

        logger.debug(f"Found {len(listed_software_names)} unique software names in policy criteria")

        # Filter installed software to only those listed in policies
        filtered_installed_software = [sw for sw in installed_software if sw['name'].lower() in listed_software_names]
        logger.debug(f"Filtered to {len(filtered_installed_software)} relevant software items based on policies")

        # Get applicable blocked software for this OS
        blocked_software = BlockedSoftware.objects.filter(
            models.Q(applicable_os=device.os) | models.Q(applicable_os='all'),
            active=True
        )
        logger.debug(f"Found {len(blocked_software)} blocked software records applicable to {device.os}")

        # Get approved software names from active "Microsoft Approved Software" policy criteria
        approved_software_names = set()
        policy = Policy.objects.get_or_create(name='Microsoft Approved Software', active=True)
        try:
            approved_policy = policy
            approved_criteria = approved_policy.criteria.filter(criteria_type='installedsoftware__name',
                                                                condition='equals')
            for crit in approved_criteria:
                approved_software_names.add(crit.value.lower())
            logger.debug(
                f"Found {len(approved_software_names)} approved software names in Microsoft Approved Software policy")
        except Policy.DoesNotExist:
            logger.debug("No Microsoft Approved Software policy found")
            approved_software_names = set()

        # Create activity report for this scan
        scan_report_content = []
        compliance_status = 'compliant'
        blocked_found = []

        logger.info(f"Processing {len(filtered_installed_software)} software items for compliance checks")

        # Save installed software to database and check for blocked software
        for software in filtered_installed_software:
            try:
                # Save or update the software entry
                sw_record, created = InstalledSoftware.objects.update_or_create(
                    device=device,
                    name=software['name'],
                    defaults={
                        'version': software.get('version', ''),
                        'publisher': software.get('publisher', 'Unknown'),
                        'status': 'active'
                    }
                )
                logger.debug(f"{'Created' if created else 'Updated'} software record: {software['name']}")

                # Check if this software is in the approved list
                if software['name'].lower() in approved_software_names:
                    # Mark as approved, do not block
                    sw_record.status = 'approved'
                    sw_record.save()
                    scan_report_content.append(f"APPROVED: {software['name']} {software.get('version', '')}")
                    logger.debug(f"Approved software: {software['name']}")
                    continue

                # Check if this software is in the blocked list
                is_blocked = False
                matched_blocked_sw = None

                for blocked in blocked_software:
                    try:
                        # Check if software name matches blocked software
                        if blocked.detection_pattern:
                            # Use regex pattern if available
                            if re.search(blocked.detection_pattern, software['name'], re.IGNORECASE):
                                is_blocked = True
                                matched_blocked_sw = blocked
                                break
                        else:
                            # Simple case-insensitive substring match
                            if blocked.name.lower() in software['name'].lower():
                                is_blocked = True
                                matched_blocked_sw = blocked
                                break
                    except re.error as e:
                        logger.error(f"Regex error in blocked software pattern {blocked.detection_pattern}: {str(e)}")
                        continue

                if is_blocked and matched_blocked_sw:
                    blocked_found.append({
                        'software': software,
                        'blocked_record': matched_blocked_sw
                    })

                    # Set compliance status based on severity of the highest blocked software
                    if matched_blocked_sw.severity in ['critical', 'high']:
                        compliance_status = 'non-compliant'
                    elif matched_blocked_sw.severity == 'medium' and compliance_status != 'non-compliant':
                        compliance_status = 'warning'

                    # Update software status
                    sw_record.status = 'blocked'
                    sw_record.save()

                    scan_report_content.append(
                        f"BLOCKED ({matched_blocked_sw.severity.upper()}): {software['name']} {software.get('version', '')}")
                    logger.warning(
                        f"Blocked software detected: {software['name']} (severity: {matched_blocked_sw.severity})")
                else:
                    # Mark software as approved if in approved list, else active
                    if software['name'].lower() in approved_software_names:
                        sw_record.status = 'approved'
                    else:
                        sw_record.status = 'active'
                    sw_record.save()
                    scan_report_content.append(f"OK: {software['name']} {software.get('version', '')}")
                    logger.debug(f"Allowed software: {software['name']}")
            except Exception as e:
                logger.error(f"Error processing software {software.get('name', 'unknown')}: {str(e)}")
                continue

        # Update device status based on scan results
        device.status = compliance_status
        device.last_scan = timezone.now()
        if compliance_status != 'compliant':
            device.actions = 'Remove blocked software'
        else:
            device.actions = 'No action required'
        device.save()
        logger.info(f"Updated device {device.id} status to {compliance_status}")

        # Create activity report
        try:
            activity_report = ActivityReport.objects.create(
                device=device,
                scan_status=compliance_status,
                compliance_status=compliance_status,
                actions_taken='Software scan completed',
                scan_report='\n'.join(scan_report_content)
            )
            logger.debug(f"Created activity report {activity_report.id} for device {device.id}")
        except Exception as e:
            logger.error(f"Error creating activity report: {str(e)}")

        # Create notifications for blocked software
        try:
            # Get policy for software compliance
            software_policy = Policy.objects.filter(category='Software', active=True).first()
            if not software_policy:
                software_policy = Policy.objects.filter(active=True).first()
                logger.debug("No software-specific policy found, using first active policy")

            if software_policy and blocked_found:
                logger.info(f"Creating notifications for {len(blocked_found)} blocked software items")
                for blocked_item in blocked_found:
                    blocked_sw = blocked_item['blocked_record']
                    software = blocked_item['software']

                    try:
                        notification = Notification.objects.create(
                            user=device.user,
                            device=device,
                            notification_type='non-compliant' if blocked_sw.severity in ['critical',
                                                                                         'high'] else 'warning',
                            message=f"Blocked software detected: {software['name']} {software.get('version', '')}. Severity: {blocked_sw.severity.upper()}. {blocked_sw.description}",
                            timestamp=timezone.now(),
                            policy=software_policy,
                            read=False
                        )
                        logger.debug(f"Created notification {notification.id} for blocked software")
                    except Exception as e:
                        logger.error(f"Error creating notification for blocked software: {str(e)}")
        except Exception as e:
            logger.error(f"Error in notification creation process: {str(e)}")

    except Exception as e:
        logger.error(f"Error in software scan for device {device.id}: {str(e)}")
        # Create error activity report
        try:
            ActivityReport.objects.create(
                device=device,
                scan_status='error',
                compliance_status='unknown',
                actions_taken='Software scan failed',
                scan_report=f"Error during scan: {str(e)}"
            )
        except Exception as inner_e:
            logger.error(f"Error creating error activity report: {str(inner_e)}")


def evaluate_device_compliance(device, policy):
    """
    Evaluate a device against the given policy's criteria.
    If all criteria are met, mark device as compliant.
    """
    logger.info(f"Starting compliance evaluation for device {device.id} against policy {policy.id} ({policy.name})")

    try:
        criteria = policy.criteria.all()
        device_compliant = True
        reasons = []
        logger.debug(f"Policy has {len(criteria)} criteria to evaluate")

        for criterion in criteria:
            try:
                # Handle related fields like 'installedsoftware__name'
                if '__' in criterion.criteria_type:
                    related_field, related_attr = criterion.criteria_type.split('__', 1)
                    related_objects = getattr(device, related_field).all()
                    match_found = False

                    logger.debug(
                        f"Evaluating related field {related_field}.{related_attr} with {related_objects.count()} objects")

                    for obj in related_objects:
                        device_value = getattr(obj, related_attr, None)
                        if device_value is None:
                            continue

                        condition = criterion.condition.lower()
                        expected_value = criterion.value

                        if condition == 'equals':
                            if str(device_value).lower() == expected_value.lower():
                                match_found = True
                                break
                        elif condition == 'contains':
                            if expected_value.lower() in str(device_value).lower():
                                match_found = True
                                break
                        elif condition == 'regex':
                            try:
                                if re.search(expected_value, str(device_value)):
                                    match_found = True
                                    break
                            except re.error as e:
                                logger.error(f"Invalid regex pattern in criterion {criterion.id}: {expected_value}")
                                continue

                    if not match_found:
                        device_compliant = False
                        reasons.append(
                            f"No related {related_field} with {related_attr} matching {criterion.condition} {criterion.value}")
                        logger.debug(f"Failed related field criterion: {related_field}.{related_attr}")
                else:
                    device_value = getattr(device, criterion.criteria_type, None)
                    if device_value is None:
                        device_compliant = False
                        reasons.append(f"Device missing attribute {criterion.criteria_type}")
                        logger.debug(f"Missing device attribute: {criterion.criteria_type}")
                        continue

                    condition = criterion.condition.lower()
                    expected_value = criterion.value
                    logger.debug(
                        f"Evaluating {criterion.criteria_type} (value: {device_value}) with condition {condition} against {expected_value}")

                    if condition == 'equals':
                        if str(device_value).lower() != expected_value.lower():
                            device_compliant = False
                            reasons.append(f"{criterion.criteria_type} does not equal {expected_value}")
                            logger.debug(f"Failed equals condition: {device_value} != {expected_value}")
                    elif condition == 'contains':
                        if expected_value.lower() not in str(device_value).lower():
                            device_compliant = False
                            reasons.append(f"{criterion.criteria_type} does not contain {expected_value}")
                            logger.debug(f"Failed contains condition: {expected_value} not in {device_value}")
                    elif condition == 'regex':
                        try:
                            if not re.search(expected_value, str(device_value)):
                                device_compliant = False
                                reasons.append(f"{criterion.criteria_type} does not match regex {expected_value}")
                                logger.debug(f"Failed regex condition: {device_value} doesn't match {expected_value}")
                        except re.error as e:
                            logger.error(f"Invalid regex pattern in criterion {criterion.id}: {expected_value}")
                            device_compliant = False
                            reasons.append(f"Invalid regex pattern in criterion: {expected_value}")
                    else:
                        # Unknown condition type
                        device_compliant = False
                        reasons.append(f"Unknown condition {condition} for {criterion.criteria_type}")
                        logger.warning(f"Unknown condition type: {condition}")
            except Exception as e:
                logger.error(f"Error evaluating criterion {criterion.id}: {str(e)}")
                device_compliant = False
                reasons.append(f"Error evaluating criterion: {str(e)}")

        if device_compliant:
            device.status = 'compliant'
            device.actions = 'Device meets all policy criteria.'
            logger.info(f"Device {device.id} is compliant with policy {policy.id}")
        else:
            # If device is not compliant, do not change status here (could be set by other logic)
            reasons_text = '; '.join(reasons)
            device.actions = f"Non-compliant: {reasons_text}"
            logger.warning(f"Device {device.id} is non-compliant with policy {policy.id}: {reasons_text}")

        device.save()

        # Create activity report
        try:
            activity_report = ActivityReport.objects.create(
                device=device,
                scan_status=device.status,
                compliance_status=device.status,
                actions_taken=device.actions,
                scan_report=f"Compliance evaluation against policy '{policy.name}'."
            )
            logger.debug(f"Created activity report {activity_report.id} for compliance evaluation")
        except Exception as e:
            logger.error(f"Error creating activity report: {str(e)}")

        # Create notification for compliance
        try:
            notification = Notification.objects.create(
                user=device.user,
                device=device,
                notification_type=device.status,
                message=f"Device compliance status updated to {device.status} based on policy '{policy.name}'.",
                timestamp=timezone.now(),
                policy=policy,
                read=False
            )
            logger.debug(f"Created notification {notification.id} for compliance status")
        except Exception as e:
            logger.error(f"Error creating compliance notification: {str(e)}")

    except Exception as e:
        logger.error(f"Error in compliance evaluation for device {device.id}: {str(e)}")
        # Create error activity report
        try:
            ActivityReport.objects.create(
                device=device,
                scan_status='error',
                compliance_status='unknown',
                actions_taken='Compliance evaluation failed',
                scan_report=f"Error during evaluation: {str(e)}"
            )
        except Exception as inner_e:
            logger.error(f"Error creating error activity report: {str(inner_e)}")

# monitoring/utils.py
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def send_monitoring_command(command):
    """
    Send a command to all monitoring clients from synchronous Django code
    Usage: send_monitoring_command("df -h")
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "monitoring_clients",  # This needs to match your routing
        {
            "type": "send_command",
            "command": command
        }
    )