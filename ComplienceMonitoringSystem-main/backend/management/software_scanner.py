import re
from django.utils import timezone
from django.db.models import Q

from management.models import Notification, Policy, ActivityReport, InstalledSoftware, BlockedSoftware


def scan_device_software(device):
    """
    Scan for installed software on the device and check against blocked software database
    Returns a tuple: (compliance_status, scan_report_content, blocked_software_found)
    """
    # Get installed software (now properly returning model instances)
    installed_software = get_installed_software(device)

    # Get all active blocked software that applies to this device's OS
    blocked_software = BlockedSoftware.objects.filter(
        Q(applicable_os=device.os) | Q(applicable_os='all'),
        active=True
    )

    scan_report_content = []
    compliance_status = 'compliant'
    blocked_found = []

    # Process each installed software
    for software in installed_software:
        software_name = software.name  # Access as model attribute, not dictionary key
        software_version = software.version or ''  # Handle None case
        publisher = software.publisher or 'Unknown'

        # Check if this software is blocked
        is_blocked = False
        matched_block = None
        match_reason = ""

        for blocked in blocked_software:
            # Check using detection pattern if available
            if blocked.detection_pattern:
                try:
                    if re.search(blocked.detection_pattern, software_name, re.IGNORECASE):
                        is_blocked = True
                        matched_block = blocked
                        match_reason = f"matched pattern '{blocked.detection_pattern}'"
                        break
                except re.error:
                    # Handle invalid regex patterns
                    continue

            # Check for exact name match (case insensitive)
            if blocked.name.lower() == software_name.lower():
                is_blocked = True
                matched_block = blocked
                match_reason = "exact name match"
                break

            # Check for name contains (case insensitive)
            if blocked.name.lower() in software_name.lower():
                is_blocked = True
                matched_block = blocked
                match_reason = f"name contains '{blocked.name}'"
                break

            # Check publisher if provided in both records
            if (blocked.publisher and
                    publisher.lower() == blocked.publisher.lower() and
                    blocked.name.lower() in software_name.lower()):
                is_blocked = True
                matched_block = blocked
                match_reason = f"publisher match with '{blocked.publisher}'"
                break

        # Update the software record status
        software.status = 'blocked' if is_blocked else 'active'
        software.save()

        if is_blocked and matched_block:
            blocked_found.append({
                'software': {
                    'name': software_name,
                    'version': software_version,
                    'publisher': publisher
                },
                'blocked_record': matched_block,
                'reason': match_reason
            })

            # Update compliance status based on severity
            if matched_block.severity in ['critical', 'high']:
                compliance_status = 'non-compliant'
            elif matched_block.severity == 'medium' and compliance_status != 'non-compliant':
                compliance_status = 'warning'

            scan_report_content.append(
                f"BLOCKED ({matched_block.severity.upper()}): {software_name} {software_version} "
                f"(Reason: {match_reason}, Policy: {matched_block.description})"
            )
        else:
            scan_report_content.append(f"ALLOWED: {software_name} {software_version}")

    return compliance_status, scan_report_content, blocked_found


def perform_device_scan(device):
    """
    Complete device scanning process including status updates and notifications
    """
    compliance_status, scan_report, blocked_software = scan_device_software(device)

    # Update device status
    device.status = compliance_status
    device.last_scan = timezone.now()

    if blocked_software:
        blocked_names = ", ".join([sw['software']['name'] for sw in blocked_software])
        device.actions = f"Remove blocked software: {blocked_names}"
    else:
        device.actions = "No action required"

    device.save()

    # Create activity report
    ActivityReport.objects.create(
        device=device,
        scan_status=compliance_status,
        compliance_status=compliance_status,
        actions_taken='Software scan completed',
        scan_report='\n'.join(scan_report)
    )

    # Create notifications if blocked software found
    if blocked_software:
        # Find the most appropriate policy to associate with these notifications
        software_policy = Policy.objects.filter(
            Q(name__icontains='software') | Q(category__icontains='software'),
            active=True
        ).first()

        if not software_policy:
            software_policy = Policy.objects.filter(active=True).first()

        for blocked_item in blocked_software:
            software = blocked_item['software']
            blocked = blocked_item['blocked_record']

            # Determine notification type based on severity
            notification_type = 'non-compliant' if blocked.severity in ['critical', 'high'] else 'warning'

            Notification.objects.create(
                user=device.user,
                device=device,
                notification_type=notification_type,
                message=(
                    f"Blocked software detected: {software['name']} {software.get('version', '')}\n"
                    f"Severity: {blocked.severity.upper()}\n"
                    f"Reason: {blocked_item['reason']}\n"
                    f"Action Required: {blocked.description}"
                ),
                timestamp=timezone.now(),
                policy=software_policy,
                read=False
            )

    return {
        'status': compliance_status,
        'blocked_software_count': len(blocked_software),
        'scan_report': scan_report
    }


def get_installed_software(device):
    """
    Returns installed software as queryset of InstalledSoftware model instances
    """
    return InstalledSoftware.objects.filter(device=device)

