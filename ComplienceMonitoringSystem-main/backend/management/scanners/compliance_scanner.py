import logging
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from ..models import (
    Device,
    InstalledSoftware,
    Policy,
    PolicyCriteria,
    BlockedSoftware,
    Notification,
    ActivityReport,
    User
)
from django.utils import timezone
from management.models import Notification

logger = logging.getLogger(__name__)
def notify_compliant_device(device, policy=None):
    if device:
        message = f"Device '{device.hostname}' is compliant."
        if policy:
            message += f" Policy '{policy.name}' has been applied."

        try:
            notification = Notification.objects.create(
                user=device.user,
                device=device,
                notification_type='compliant',
                message=message,
                policy=policy
            )
            logger.info(f"Notification created for compliant device '{device.hostname}' (User: {device.user.username}).")
        except Exception as e:
            logger.error(f"Failed to create notification for device '{device.hostname}': {str(e)}")

class ComplianceScanner:
    def __init__(self):
        self.scan_time = timezone.now()
        logger.info(f"Initializing Compliance Scanner at {self.scan_time}")
        self.blocked_policy, created = Policy.objects.get_or_create(
            name='Blocked Software Policy',
            defaults={
                'category': 'Security',
                'description': 'Automatically created policy for blocked software violations',
                'active': True
            }
        )
        if created:
            logger.info(f"Created Blocked Software Policy: {self.blocked_policy.name} (ID: {self.blocked_policy.id})")
        else:
            logger.info(
                f"Using existing Blocked Software Policy: {self.blocked_policy.name} (ID: {self.blocked_policy.id})")

        self.remediation_model = self._train_remediation_model()
        logger.info("Remediation model trained successfully.")
        self.violations = []
        self.compliant = True
        self.blocked_software_found = False
        self.device = None  # Will be set during scan

    def _train_remediation_model(self):
        """
        Enhanced remediation suggestion model with more detailed suggestions.
        Logs the process and suggestions.
        """
        logger.info("Training remediation suggestion model...")

        def suggest_remediation(violation_details, device_os):
            violation_type = violation_details.get('type')
            device_os = device_os.lower()
            log_message = f"Generating remediation for {violation_type} on {device_os}: "

            if violation_type == 'blocked_software':
                software_name = violation_details.get('name', 'this software')
                if 'windows' in device_os:
                    suggestion = (
                        f"1. Open Control Panel -> Programs -> Programs and Features\n"
                        f"2. Locate '{software_name}' in the list\n"
                        f"3. Click Uninstall and follow the prompts\n"
                        f"4. Restart the device if prompted"
                    )
                elif 'linux' in device_os:
                    suggestion = (
                        f"1. Open terminal\n"
                        f"2. Run appropriate command based on package manager:\n"
                        f"   - Debian/Ubuntu: `sudo apt remove {software_name}`\n"
                        f"   - RedHat/CentOS: `sudo yum remove {software_name}`\n"
                        f"   - Arch: `sudo pacman -R {software_name}`\n"
                        f"3. Confirm removal when prompted"
                    )
                elif 'macos' in device_os:
                    suggestion = (
                        f"1. Open Finder and go to Applications folder\n"
                        f"2. Locate '{software_name}' application\n"
                        f"3. Drag it to the Trash\n"
                        f"4. Empty Trash to complete uninstallation"
                    )
                else:
                    suggestion = f"Refer to your OS documentation to uninstall '{software_name}'"
                logger.debug(log_message + f"Blocked Software - {suggestion}")
                return suggestion

            elif violation_type == 'policy_violation':
                criteria_type = violation_details.get('criteria', '').lower()
                condition = violation_details.get('condition', '').lower()
                value = violation_details.get('value', '')

                if 'software' in criteria_type:
                    if 'should be' in condition or condition == 'equals':
                        if 'windows' in device_os:
                            suggestion = f"Download and install '{value}' from the official vendor website"
                        elif 'linux' in device_os:
                            suggestion = (
                                f"Install using package manager:\n"
                                f"- Debian/Ubuntu: `sudo apt install {value}`\n"
                                f"- RedHat/CentOS: `sudo yum install {value}`\n"
                                f"- Arch: `sudo pacman -S {value}`"
                            )
                        elif 'macos' in device_os:
                            suggestion = f"Install '{value}' using Homebrew (`brew install {value}`) or download from vendor"
                        logger.debug(log_message + f"Policy Violation (Software - Install) - {suggestion}")
                        return suggestion
                    else:
                        suggestion = self.suggest_remediation(
                            {'type': 'blocked_software', 'name': value},
                            device_os
                        )
                        logger.debug(log_message + f"Policy Violation (Software - Uninstall) - {suggestion}")
                        return suggestion

                elif 'os' in criteria_type:
                    if condition == 'minimum':
                        suggestion = (
                            f"Upgrade operating system to at least version {value}:\n"
                            f"- Windows: Settings -> Update & Security -> Windows Update\n"
                            f"- macOS: App Store -> Updates\n"
                            f"- Linux: Follow distribution upgrade instructions"
                        )
                        logger.debug(log_message + f"Policy Violation (OS - Minimum) - {suggestion}")
                        return suggestion

                elif 'last scan' in criteria_type:
                    suggestion = (
                        f"Run a new compliance scan on the device:\n"
                        f"1. Open the device management client\n"
                        f"2. Navigate to Compliance section\n"
                        f"3. Click 'Run Scan Now'"
                    )
                    logger.debug(log_message + f"Policy Violation (Last Scan) - {suggestion}")
                    return suggestion

            default_suggestion = (
                "Recommended remediation steps:\n"
                "1. Review the policy requirements\n"
                "2. Consult IT documentation\n"
                "3. Contact help desk if unsure"
            )
            logger.debug(log_message + f"Default - {default_suggestion}")
            return default_suggestion

        return suggest_remediation

    def scan_device(self, device):
        """
        Perform a comprehensive compliance scan on a device.
        Logs each stage of the scan.
        Returns a tuple: (is_compliant, violations)
        """
        self.device = device
        logger.info(f"Starting compliance scan for device {device.hostname} (ID: {device.id})")

        # Reset scan state
        logger.debug(f"Resetting scan state for {device.hostname}")
        self.violations = []
        self.compliant = True
        self.blocked_software_found = False

        # Check for blocked software (highest priority)
        logger.info(f"Checking for blocked software on {device.hostname}")
        self._check_blocked_software()
        logger.info(
            f"Blocked software check completed for {device.hostname}. Found blocked software: {self.blocked_software_found}")

        # Only check other policies if no blocked software found
        if not self.blocked_software_found:
            logger.info(f"No blocked software found, proceeding to check policy compliance for {device.hostname}")
            self._check_policy_compliance()
        else:
            logger.info(f"Blocked software found, skipping general policy compliance checks for {device.hostname}")

        # Determine final compliance status
        if self.blocked_software_found or self.violations:
            self.compliant = False
            logger.warning(
                f"Device {self.device.hostname} is non-compliant. Blocked software found: {self.blocked_software_found}, Policy violations: {len(self.violations)}")
        else:
            self.compliant = True
            logger.info(f"Device {self.device.hostname} is compliant.")

        # Update device status and create reports
        logger.info(f"Updating device status for {self.device.hostname}")
        self._update_device_status()
        logger.info(f"Creating activity report for {self.device.hostname}")
        self._create_activity_report()
        logger.info(f"Creating notifications for {self.device.hostname}")
        self._create_notifications()

        logger.info(
            f"Completed compliance scan for device {self.device.hostname}. Compliant: {self.compliant}, Violations: {len(self.violations)}")
        return self.compliant, self.violations

    def _check_blocked_software(self):
        """Check for any blocked software on the device"""
        logger.debug(f"Checking blocked software for device {self.device.hostname}")

        # First reset any previously blocked software that's no longer blocked
        for software in self.device.installedsoftware.filter(status='blocked'):
            if not self._is_software_blocked(software):
                software.status = 'approved'
                software.save()
                logger.info(
                    f"Software '{software.name}' on {self.device.hostname} is no longer blocked, status updated to approved")
            else:
                logger.debug(f"Software '{software.name}' on {self.device.hostname} is still blocked.")

        # Check all installed software against blocked list
        for software in self.device.installedsoftware.all():
            if self._is_software_blocked(software):
                logger.warning(f"Blocking software '{software.name} {software.version}' found on {self.device.hostname}")
                self.blocked_software_found = True
                software.status = 'blocked'
                software.save()
                self.save_software_status(software)  # uses new method
                violation = {
                    'type': 'blocked_software',
                    'name': software.name,
                    'version': software.version,
                    'publisher': software.publisher,
                    'policy': self.blocked_policy.name,
                    'criteria': 'blocked_software',
                    'condition': 'equals',
                    'value': f"{software.name} ({software.publisher})",
                    'description': f"Found blocked software: {software.name} {software.version}"
                }
                self.violations.append(violation)
                logger.warning(f"Blocked software '{software.name} {software.version}' found on {self.device.hostname}")
            else:
                logger.debug(f"Software '{software.name}' on {self.device.hostname} is not blocked.")

    def _is_software_blocked(self, software):
        """Check if specific software is in the blocked list"""
        is_blocked = BlockedSoftware.objects.filter(
            active=True,
            name__iexact=software.name,
            publisher__iexact=software.publisher,
        ).filter(
            Q(applicable_os='all') | Q(applicable_os__iexact=self.device.os)
        ).exists()
        logger.debug(
            f"Checking if '{software.name}' on {self.device.hostname} (Publisher: '{software.publisher}', OS: '{self.device.os}') is blocked: {is_blocked}")
        return is_blocked

    def save_software_status(self, software):
        """Helper method to save software status and log the operation"""
        try:
            software.save()
            logger.debug(
                f"Saved status '{software.status}' for software '{software.name}' on device '{self.device.hostname}'")
        except Exception as e:
            logger.error(
                f"Failed to save status for software '{software.name}' on device '{self.device.hostname}': {e}")

    def _check_policy_compliance(self):
        """Check device against all active policies"""
        active_policies = Policy.objects.filter(active=True).prefetch_related('criteria')
        logger.debug(f"Checking {active_policies.count()} active policies for device {self.device.hostname}")

        for policy in active_policies:
            logger.info(f"Evaluating policy: {policy.name} (ID: {policy.id}) for device {self.device.hostname}")
            self._evaluate_policy(policy)

    def _evaluate_policy(self, policy):
        """Evaluate a single policy against the device"""
        logger.debug(f"Evaluating policy: {policy.name} for device {self.device.hostname}")

        for criteria in policy.criteria.all():
            logger.debug(
                f"Checking criteria: {criteria.criteria_type} - {criteria.condition} {criteria.value} for policy '{policy.name}' on {self.device.hostname}")
            if not self._check_criteria(criteria):
                violation = {
                    'type': 'policy_violation',
                    'policy': policy.name,
                    'criteria': criteria.criteria_type,
                    'condition': criteria.condition,
                    'value': criteria.value,
                    'description': criteria.description
                }
                self.violations.append(violation)
                logger.warning(
                    f"Policy violation on {self.device.hostname}: Policy '{policy.name}', Criteria '{criteria.description}'")
            else:
                logger.debug(
                    f"Criteria '{criteria.description}' for policy '{policy.name}' on {self.device.hostname} is met.")

    def _check_criteria(self, criteria):
        """Check a single policy criteria against the device"""
        criteria_type = criteria.criteria_type.lower()
        logger.debug(f"Checking criteria type: {criteria_type}")

        if criteria_type == 'installed_software' or criteria_type == 'software':
            result = self._check_software_criteria(criteria)
            logger.debug(f"Software criteria check result: {result}")
            return result
        elif criteria_type == 'os_version' or criteria_type == 'os':
            result = self._check_os_criteria(criteria)
            logger.debug(f"OS criteria check result: {result}")
            return result
        elif criteria_type == 'last_scan_time' or criteria_type == 'last scan':
            result = self._check_last_scan_criteria(criteria)
            logger.debug(f"Last scan criteria check result: {result}")
            return result
        elif criteria_type == 'device_type' or criteria_type == 'device type':
            result = self._check_device_type_criteria(criteria)
            logger.debug(f"Device type criteria check result: {result}")
            return result
        else:
            logger.error(f"Unknown criteria type: {criteria_type}")
            return False

    def _check_software_criteria(self, criteria):
        """Check installed software criteria"""
        installed_software = self.device.installedsoftware.all()
        logger.debug(f"Total installed software items on device: {installed_software.count()}")

        for sw in installed_software:
            logger.debug(f"Software: Name='{sw.name}', Version='{sw.version}', Status='{sw.status}'")
        condition = criteria.condition.lower()
        value = criteria.value.lower()

        if condition == 'equals':
            # Check if specific software is installed
            name, version = value.split(':') if ':' in value else (value, None)

            if version:
                logger.debug(f"Checking for exact match of {name} version {version}")
                return installed_software.filter(
                    name__iexact=name,
                    version__iexact=version
                ).exists()

            logger.debug(f"Checking for exact match of {name} (any version)")
            return installed_software.filter(name__iexact=name).exists()

        elif condition == 'contains':
            logger.debug(f"Checking for software containing: {value}")
            return installed_software.filter(name__icontains=value).exists()

        elif condition == 'minimum':
            try:
                min_count = int(value)
                logger.debug(f"Checking for at least {min_count} software items installed")
                return installed_software.count() >= min_count
            except ValueError:
                logger.error(f"Invalid minimum count value: {criteria.value}")
                return False

        elif condition == 'should not be installed':
            logger.debug(f"Checking if software '{value}' is NOT installed")
            return not installed_software.filter(name__iexact=value).exists()

        logger.warning(f"Unsupported condition type: {criteria.condition}")
        return False

    def _check_os_criteria(self, criteria):
        """Check OS-related policy criteria"""
        device_os = self.device.os.lower()
        expected = criteria.value.lower()
        condition = criteria.condition.lower()
        logger.debug(f"Checking OS criteria: Condition '{condition}', Expected '{expected}', Device OS '{device_os}'")

        if condition == 'equals':
            result = device_os == expected
            logger.debug(f"OS equals '{expected}' check: {result}")
            return result
        elif condition == 'contains':
            result = expected in device_os
            logger.debug(f"OS contains '{expected}' check: {result}")
            return result
        elif condition == 'minimum':
            # Simple version comparison - in production you'd use proper version comparison
            result = device_os >= expected
            logger.debug(f"OS ('{device_os}') is minimum '{expected}' check: {result}")
            return result

        logger.warning(f"Unsupported OS condition: {condition}")
        return False

    def _check_last_scan_criteria(self, criteria):
        """Check last scan time criteria"""
        try:
            max_hours = int(criteria.value)
            threshold = timezone.now() - timedelta(hours=max_hours)
            last_scan = self.device.last_scan
            result = last_scan and last_scan >= threshold
            logger.debug(
                f"Last scan within {max_hours} hours (Last Scan: {last_scan}, Threshold: {threshold}): {result}")
            return result
        except ValueError:
            logger.error(f"Invalid hours value: {criteria.value}")
            return False

    def _check_device_type_criteria(self, criteria):
        """Check device type criteria"""
        device_type = self.device.device_type.lower()
        expected = criteria.value.lower()
        condition = criteria.condition.lower()
        logger.debug(
            f"Checking device type criteria: Condition '{condition}', Expected '{expected}', Device Type '{device_type}'")

        if condition == 'equals':
            result = device_type == expected
            logger.debug(f"Device type equals '{expected}' check: {result}")
            return result
        elif condition == 'contains':
            result = expected in device_type
            logger.debug(f"Device type contains '{expected}' check: {result}")
            return result

        logger.warning(f"Unsupported device type condition: {condition}")
        return False

    def _update_device_status(self):
        """Update device status based on scan results"""
        try:
            if not self.compliant:
                self.device.status = 'non-compliant'
                actions = []
                for violation in self.violations:
                    remediation = self.remediation_model(violation, self.device.os)
                    actions.append(f"{violation['policy']}: {remediation}")

                self.device.actions = "\n".join(actions)
                logger.warning(f"Device {self.device.hostname} marked non-compliant. Actions: {self.device.actions}")
            else:
                self.device.status = 'compliant'
                self.device.actions = "No actions required"
                logger.info(f"Device {self.device.hostname} is compliant")

            self.device.last_scan = self.scan_time
            self.device.save()
            logger.debug(
                f"Device status updated for {self.device.hostname}. Status: {self.device.status}, Last Scan: {self.device.last_scan}")
        except Exception as e:
            logger.error(f"Failed to update device status for {self.device.hostname}: {e}")

    def _create_activity_report(self):
        """Create detailed activity report for the scan"""
        report_details = ""
        if self.blocked_software_found:
            report_details = "Blocked software found:\n"
            report_details += "\n".join(
                f"- {v['name']} {v['version']} (Policy: {v['policy']})"
                for v in self.violations if v['type'] == 'blocked_software'
            )
            if len(self.violations) > 1:
                report_details += "\nOther policy violations:\n"

        if not self.blocked_software_found and self.violations:
            report_details = "Policy violations found:\n"

        if self.violations:
            report_details += "\n".join(
                f"- {v['policy']}: {v['description']}"
                for v in self.violations if v.get('type') != 'blocked_software'
            )
        else:
            report_details = "No violations found - device is compliant"

        try:
            ActivityReport.objects.create(
                device=self.device,
                scan_time=self.scan_time,
                scan_status='compliant' if self.compliant else 'non-compliant',
                compliance_status='compliant' if self.compliant else 'non-compliant',
                actions_taken="Scan completed",
                scan_report=report_details
            )
            logger.info(f"Activity report created for device {self.device.hostname}")
        except Exception as e:
            logger.error(f"Failed to create activity report for device {self.device.hostname}: {e}")

    def _create_notifications(self):
        """Create notifications for violations"""
        if not self.violations:
            logger.info(f"No violations found, no notifications to create for device {self.device.hostname}")
            # notification = Notification.objects.create(notification_type='compliant', message='Your Device is Compliant', device=self.device, user=self.device.user, policy=Policy.objects.get_or_create("Compliance Devices Policy"))
            # notification.save()
            policy, created = Policy.objects.get_or_create(
                name='Compliant Devices  Policy',
                defaults={
                    'category': 'Security',
                    'description': 'Automatically created policy for compliant devices',
                    'active': True
                }
            )
            notify_compliant_device(device=self.device, policy=policy)

            return

        users_to_notify = set()

        # Always notify device owner if exists
        if self.device.user:
            users_to_notify.add(self.device.user)
            logger.debug(f"Added device owner {self.device.user.username} to notification list")

        # Notify all admins for blocked software
        if self.blocked_software_found:
            admins = User.objects.filter(role='Admin')
            users_to_notify.update(admins)
            for admin in admins:
                logger.debug(f"Added admin {admin.username} to notification list for blocked software")

        created_count = 0

        for user in users_to_notify:
            for violation in self.violations:
                policy = self.blocked_policy if violation['type'] == 'blocked_software' else \
                    Policy.objects.filter(name=violation['policy']).first()
                if policy:
                    notification = Notification(
                        user=user,
                        device=self.device,
                        notification_type='non-compliant',
                        message=(
                            f"Compliance issue on {self.device.hostname}:\n"
                            f"Policy: {violation['policy']}\n"
                            f"Issue: {violation['description']}\n"
                            f"Action required: {self.remediation_model(violation, self.device.os)}"
                        ),
                        policy=policy,
                        timestamp=self.scan_time
                    )
                    try:
                        notification.save()
                        created_count += 1
                        logger.debug(
                            f"Created notification for user {user.username} about violation: {violation['description']}")
                    except Exception as e:
                        logger.error(f"Failed to create notification for user {user.username}: {e}")
                else:
                    logger.warning(f"Policy '{violation['policy']}' not found. Cannot create notification.")

        logger.info(f"Created {created_count} notifications for device {self.device.hostname}")

    # def _create_notifications(self):
    #     """Create notifications for violations"""
    #     if not self.violations:
    #         logger.info(f"No violations found, no notifications to create for device {self.device.hostname}")
    #         return
    #
    #     notifications = []
    #     users_to_notify = set()
    #
    #     # Always notify device owner if exists
    #     if self.device.user:
    #         users_to_notify.add(self.device.user)
    #         logger.debug(f"Added device owner {self.device.user.username} to notification list")
    #
    #     # Notify all admins for blocked software
    #     if self.blocked_software_found:
    #         admins = User.objects.filter(role='Admin')
    #         users_to_notify.update(admins)
    #         for admin in admins:
    #             logger.debug(f"Added admin {admin.username} to notification list for blocked software")
    #
    #     for user in users_to_notify:
    #         for violation in self.violations:
    #             policy = self.blocked_policy if violation['type'] == 'blocked_software' else \
    #                 Policy.objects.filter(name=violation['policy']).first()
    #             if policy:
    #                 notifications.append(Notification(
    #                     user=user,
    #                     device=self.device,
    #                     notification_type='non-compliant',
    #                     message=(
    #                         f"Compliance issue on {self.device.hostname}:\n"
    #                         f"Policy: {violation['policy']}\n"
    #                         f"Issue: {violation['description']}\n"
    #                         f"Action required: {self.remediation_model(violation, self.device.os)}"
    #                     ),
    #                     policy=policy,
    #                     timestamp=self.scan_time
    #                 ))
    #                 logger.debug(
    #                     f"Prepared notification for user {user.username} about violation: {violation['description']}")
    #             else:
    #                 logger.warning(f"Policy '{violation['policy']}' not found.  Cannot create notification.")
    #
    #     try:
    #         Notification.objects.bulk_create(notifications)
    #         logger.info(f"Created {len(notifications)} notifications for device {self.device.hostname}")
    #     except Exception as e:
    #         logger.error(f"Failed to create notifications for device {self.device.hostname}: {e}")



def scan_all_devices():
    """Scan all devices for compliance"""
    scanner = ComplianceScanner()
    devices = Device.objects.all()
    logger.info(f"Starting compliance scan for all devices ({devices.count()} found)")

    for device in devices:
        try:
            is_compliant, violations = scanner.scan_device(device)
            logger.info(f"Scanned {device.hostname} - Compliant: {is_compliant}")
            if violations:
                logger.warning(f"Found {len(violations)} violations on {device.hostname}")

        except Exception as e:
            logger.error(f"Failed to scan device {device.hostname}: {str(e)}")
    logger.info("Finished scanning all devices.")



def scan_single_device(device_id):
    """Scan a single device by ID"""
    scanner = ComplianceScanner()
    try:
        device = Device.objects.get(id=device_id)
        logger.info(f"Starting compliance scan for single device with id: {device_id}, hostname: {device.hostname}")
        is_compliant, violations = scanner.scan_device(device)
        logger.info(f"Scanned device {device.hostname} - Compliant: {is_compliant}")
        return is_compliant, violations
    except Device.DoesNotExist:
        logger.error(f"Device with id {device_id} not found.")
        return None, None
    except Exception as e:
        logger.error(f"Failed to scan device with id {device_id}: {str(e)}")
        return None, None
