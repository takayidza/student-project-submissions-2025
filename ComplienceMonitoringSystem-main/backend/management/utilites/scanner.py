import logging
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q



# Set up logging
logger = logging.getLogger(__name__)


class DeviceScanner:
    def __init__(self, device):
        self.device = device
        self.violations = []
        self.compliant = True
        self.blocked_software_found = False
        self._check_blocked_software()
        logger.info(f"Initialized scanner for device: {device.hostname} (ID: {device.id})")

    def scan_device(self):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Scan the device against all active policies"""
        logger.info(f"Starting scan for device: {self.device.hostname}")

        # Reset compliance status for this scan (but don't reset device status yet)
        self.compliant = True
        self.violations = []
        self.blocked_software_found = False

        # First check for blocked software (highest priority check)
        self._check_blocked_software()

        # Only proceed with other policy checks if no blocked software was found
        if not self.blocked_software_found:
            # Get all active policies
            active_policies = Policy.objects.filter(active=True)
            logger.debug(f"Found {active_policies.count()} active policies to check")

            # Check device against each policy
            for policy in active_policies:
                logger.debug(f"Checking policy: {policy.name} (ID: {policy.id})")
                self._check_policy(policy)

        # Update device status based on scan results
        # If device was already non-compliant, keep it that way regardless of current scan results
        if self.device.status == 'non-compliant':
            logger.info("Device was already non-compliant - maintaining status")
            self.compliant = False
        else:
            if self.blocked_software_found or self.violations:
                logger.warning(
                    f"Device has {'blocked software' if self.blocked_software_found else ''} {len(self.violations)} policy violations")
                self.device.status = 'non-compliant'
                self.compliant = False
            else:
                logger.info("Device is fully compliant with all policies")
                self.device.status = 'compliant'

        self.device.last_scan = timezone.now()
        self.device.save()
        logger.debug("Updated device status and last scan time")

        # Create activity report
        self._create_activity_report()

        logger.info(f"Scan completed for device: {self.device.hostname}. Compliant: {self.compliant}")
        return self.compliant, self.violations

    def _check_blocked_software(self):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Check for blocked software on the device and update statuses"""
        logger.debug("Checking for blocked software")
        notifications = []
        hostname = getattr(self.device, 'hostname', 'unknown_device')

        logger.info(f"Checking for blocked software on device: {hostname} (ID: {self.device.id})")

        # First, reset any previously blocked software that's no longer in the blocked list
        for installed_software in self.device.installedsoftware.filter(status='blocked'):
            software_name = getattr(installed_software, 'name', 'unknown_software')
            software_publisher = getattr(installed_software, 'publisher', 'unknown_publisher')

            # Check if this software is no longer blocked
            is_blocked = BlockedSoftware.objects.filter(
                active=True,
                name__iexact=software_name,
                publisher__iexact=software_publisher,
                applicable_os__in=['all', self.device.os]
            ).exists()


            if not is_blocked:
                installed_software.status = 'approved'
                installed_software.save()
                logger.info(
                    f"Software '{software_name}' on {hostname} status updated to 'approved' as it's no longer blocked")

        # Now check for currently blocked software
        for installed_software in self.device.installedsoftware.all():
            software_name = getattr(installed_software, 'name', 'unknown_software')
            software_version = getattr(installed_software, 'version', 'unknown_version')
            software_publisher = getattr(installed_software, 'publisher', 'unknown_publisher')

            logger.debug(f"Checking installed software: {software_name} ({software_version}) by {software_publisher}")

            # Check if the installed software matches any active blocked software
            blocked_software_matches = BlockedSoftware.objects.filter(
                active=True,
                name__iexact=software_name,
                publisher__iexact=software_publisher,
                applicable_os__in=['all', self.device.os]
            )

            if blocked_software_matches.exists():
                self.blocked_software_found = True
                logger.warning(
                    f"Blocked software found on {hostname}: "
                    f"{software_name} ({software_version}) by {software_publisher}"
                )

                # Mark the installed software as 'blocked' if not already
                if installed_software.status != 'blocked':
                    installed_software.status = 'blocked'
                    installed_software.device.status = 'non-complant'
                    installed_software.save()
                    policy, created = Policy.objects.get_or_create(
                        name="Blocked Software Policy",
                        description="System generated policy to automatically picks blocked software from devices"
                    )
                    notifications.append(
                        Notification(
                            user=self.device.user,
                            device=self.device,
                            notification_type='warning',
                            policy=policy,
                            message=f"Software '{software_name} ({software_version})' on {hostname} has been blocked.",
                            timestamp=timezone.now()
                        )
                    )
                    # Notify Admins as well
                    for admin in User.objects.filter(role='Admin'):
                        notifications.append(
                            Notification(
                                user=admin,
                                device=self.device,
                                notification_type='warning',
                                message=f"Software '{software_name} ({software_version})' on {hostname} has been blocked.",
                                timestamp=timezone.now()
                            )
                        )
                    logger.info(f"Software '{software_name}' on {hostname} status updated to 'blocked'.")

                # Add to violations list
                self.violations.append({
                    'policy': 'Blocked Software Policy',
                    'criteria': 'blocked_software',
                    'condition': 'equals',
                    'expected': f"Blocked: {software_name} ({software_publisher})",
                    'description': f"Found blocked software: {software_name}."
                })
            else:
                logger.debug(f"Installed software '{software_name}' is not in the blocked list.")

        # Bulk create notifications
        if notifications:
            Notification.objects.bulk_create(notifications)
            logger.info(f"Created {len(notifications)} notifications for device {hostname}.")

        return self.blocked_software_found

    def _check_policy(self, policy):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Check device against a specific policy's criteria"""
        logger.debug(f"Evaluating policy: {policy.name}")
        criteria_count = policy.criteria.count()
        logger.debug(f"Policy has {criteria_count} criteria to check")

        for criteria in policy.criteria.all():
            criteria_result = self._check_criteria(criteria)
            logger.debug(
                f"Criteria check - Type: {criteria.criteria_type}, "
                f"Condition: {criteria.condition}, Value: {criteria.value}, "
                f"Result: {'PASS' if criteria_result else 'FAIL'}"
            )

            if not criteria_result:
                violation = {
                    'policy': policy.name,
                    'criteria': criteria.criteria_type,
                    'condition': criteria.condition,
                    'expected': criteria.value,
                    'description': criteria.description
                }
                self.violations.append(violation)
                logger.warning(
                    f"Policy violation detected - Policy: {policy.name}, "
                    f"Criteria: {criteria.criteria_type}, "
                    f"Expected: {criteria.condition} {criteria.value}"
                )

    def _check_criteria(self, criteria):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Check a single criteria against the device"""
        criteria_type = criteria.criteria_type.lower()

        try:
            # Check different criteria types
            if criteria_type == 'os':
                return self._check_os_criteria(criteria)
            elif criteria_type == 'software':
                return self._check_software_criteria(criteria)
            elif criteria_type == 'last scan time':
                return self._check_last_scan_criteria(criteria)
            elif criteria_type == 'device type':
                return self._check_device_type_criteria(criteria)
            elif criteria_type == 'blocked software':
                return not self.blocked_software_found  # Already checked in _check_blocked_software

            logger.error(f"Unknown criteria type: {criteria_type}")
            return False
        except Exception as e:
            logger.error(f"Error evaluating criteria {criteria.id}: {str(e)}")
            return False

    def _check_os_criteria(self, criteria):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User

        """Check OS criteria"""
        device_os = self.device.os.lower()
        expected_os = criteria.value.lower()

        if criteria.condition == 'equals':
            return device_os == expected_os
        elif criteria.condition == 'contains':
            return expected_os in device_os

        logger.warning(f"Unsupported condition for OS criteria: {criteria.condition}")
        return False

    def _check_software_criteria(self, criteria):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User

        """Check installed software criteria"""
        installed_software = self.device.installedsoftware.filter(status='approved')
        logger.debug(f"Found {installed_software.count()} approved software items on device")

        if criteria.condition == 'equals':
            # Check if specific software is installed
            name, version = criteria.value.split(':') if ':' in criteria.value else (criteria.value, None)

            if version:
                logger.debug(f"Checking for exact match of {name} version {version}")
                return installed_software.filter(name__iexact=name, version__iexact=version).exists()
            logger.debug(f"Checking for exact match of {name} (any version)")
            return installed_software.filter(name__iexact=name).exists()

        elif criteria.condition == 'contains':
            logger.debug(f"Checking for software containing: {criteria.value}")
            return installed_software.filter(name__icontains=criteria.value).exists()

        elif criteria.condition == 'minimum':
            # Check minimum number of software installed
            try:
                min_count = int(criteria.value)
                logger.debug(f"Checking for at least {min_count} software items installed")
                return installed_software.count() >= min_count
            except ValueError:
                logger.error(f"Invalid minimum count value: {criteria.value}")
                return False

        logger.warning(f"Unsupported condition for software criteria: {criteria.condition}")
        return False

    def _check_last_scan_criteria(self, criteria):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Check last scan time criteria"""
        try:
            max_hours = int(criteria.value)
            time_threshold = timezone.now() - timedelta(hours=max_hours)
            logger.debug(f"Checking if last scan ({self.device.last_scan}) is within {max_hours} hours")
            return self.device.last_scan >= time_threshold
        except ValueError:
            logger.error(f"Invalid hours value for last scan criteria: {criteria.value}")
            return False

    def _check_device_type_criteria(self, criteria):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Check device type criteria"""
        device_type = self.device.device_type.lower()
        expected_type = criteria.value.lower()

        if criteria.condition == 'equals':
            return device_type == expected_type
        elif criteria.condition == 'contains':
            return expected_type in device_type

        logger.warning(f"Unsupported condition for device type criteria: {criteria.condition}")
        return False

    def _create_activity_report(self):
        from management.models import Policy, Notification, ActivityReport, BlockedSoftware, InstalledSoftware, User
        """Create an activity report for the scan"""
        logger.debug("Creating activity report")

        report_details = "\n".join([
            f"Policy: {v['policy']}\nCriteria: {v['criteria']}\nExpected: {v['expected']}\nDescription: {v['description']}\n"
            for v in self.violations
        ]) if self.violations else "Device is fully compliant with all policies"

        if self.blocked_software_found:
            report_details = "Blocked software found.\n" + report_details

        actions_taken = "Scan completed. " + (
            "No violations found." if self.compliant
            else f"Found {len(self.violations)} policy violations."
        )

        ActivityReport.objects.create(
            device=self.device,
            scan_status=self.device.status,
            compliance_status='compliant' if self.compliant else 'non-compliant',
            actions_taken=actions_taken,
            scan_report=report_details
        )
        logger.info("Activity report created successfully")

        # Create notifications if device is non-compliant
        if not self.compliant and self.device.user:
            logger.debug("Creating notifications for policy violations")
            for violation in self.violations:
                try:
                    policy = Policy.objects.get(name=violation['policy'])
                    Notification.objects.create(
                        user=self.device.user,
                        device=self.device,
                        notification_type='non-compliant',
                        message=f"Device {self.device.hostname} violates policy {policy.name}: {violation['description']}",
                        policy=policy
                    )
                    logger.debug(f"Created notification for violation: {violation['description']}")
                except Policy.DoesNotExist:
                    logger.error(f"Policy not found: {violation['policy']}")
                except Exception as e:
                    logger.error(f"Failed to create notification: {str(e)}")