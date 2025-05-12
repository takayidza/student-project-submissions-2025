import logging
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
from pathlib import Path
import os
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
from .compliance_analyzer import ComplianceAnalyzer

logger = logging.getLogger(__name__)


class ComplianceScanner:
    def __init__(self):
        self.scan_time = timezone.now()
        logger.info(f"Initializing Compliance Scanner at {self.scan_time}")

        # Initialize analyzer
        self.analyzer = ComplianceAnalyzer()

        # Setup blocked software policy
        self.blocked_policy, created = Policy.objects.get_or_create(
            name='Blocked Software Policy',
            defaults={
                'category': 'Security',
                'description': 'Automatically created policy for blocked software violations',
                'active': True,
                'severity': 'critical'
            }
        )
        if created:
            logger.info(f"Created Blocked Software Policy (ID: {self.blocked_policy.id})")

        # Initialize state
        self.violations = []
        self.compliant = True
        self.blocked_software_found = False
        self.device = None
        self.ml_assessment = None

    def scan_device(self, device):
        """Perform comprehensive compliance scan with ML integration"""
        self.device = device
        logger.info(f"Starting compliance scan for {device.hostname}")

        # Step 1: Get ML-based initial assessment
        self.ml_assessment = self._get_ml_assessment()
        logger.info(f"Initial ML assessment: {self.ml_assessment['status']}")

        # Step 2: Reset scan state
        self._reset_scan_state()

        # Step 3: Perform detailed checks (order by priority)
        self._check_blocked_software()  # Highest priority
        if not self.blocked_software_found:
            self._check_policy_compliance()

        # Step 4: Determine final compliance status
        self._determine_compliance()

        # Step 5: Update system state
        self._update_device_status()
        self._create_activity_report()
        self._create_notifications()

        logger.info(f"Completed scan for {device.hostname}. Compliant: {self.compliant}")
        return self.compliant, self.violations

    def _get_ml_assessment(self):
        """Prepare data and get ML assessment"""
        device_data = {
            'os': self.device.os,
            'device_type': self.device.device_type,
            'last_scan': self.device.last_scan,
            'historical_reports': list(
                self.device.activity_report_set.all().values(
                    'scan_status', 'compliance_status'
                )[:100]  # Limit to most recent 100 reports
            )
        }

        software_list = [
            {
                'name': sw.name,
                'version': sw.version,
                'publisher': sw.publisher
            }
            for sw in self.device.installedsoftware.all()
        ]

        return self.analyzer.predict_compliance_status(device_data, software_list)

    def _reset_scan_state(self):
        """Reset all scan-related state variables"""
        self.violations = []
        self.compliant = True
        self.blocked_software_found = False

    def _check_blocked_software(self):
        """Check for any blocked software on the device"""
        logger.debug(f"Checking blocked software for {self.device.hostname}")

        # First reset any previously blocked software that's no longer blocked
        for software in self.device.installedsoftware.filter(status='blocked'):
            if not self._is_software_blocked(software):
                software.status = 'approved'
                software.save()
                logger.info(f"Unblocked {software.name} on {self.device.hostname}")

        # Check all installed software against blocked list
        for software in self.device.installedsoftware.all():
            if self._is_software_blocked(software):
                self._handle_blocked_software(software)

    def _is_software_blocked(self, software):
        """Check if specific software is in the blocked list"""
        return BlockedSoftware.objects.filter(
            active=True,
            name__iexact=software.name,
            publisher__iexact=software.publisher,
        ).filter(
            Q(applicable_os='all') | Q(applicable_os__iexact=self.device.os)
        ).exists()

    def _handle_blocked_software(self, software):
        """Handle the discovery of blocked software"""
        self.blocked_software_found = True
        software.status = 'blocked'
        software.save()

        violation = {
            'type': 'blocked_software',
            'name': software.name,
            'version': software.version,
            'publisher': software.publisher,
            'policy': self.blocked_policy.name,
            'criteria': 'blocked_software',
            'condition': 'equals',
            'value': f"{software.name} ({software.publisher})",
            'description': f"Found blocked software: {software.name} {software.version}",
            'severity': 'critical'
        }
        self.violations.append(violation)
        logger.warning(f"Blocked software found: {software.name} on {self.device.hostname}")

    def _check_policy_compliance(self):
        """Check device against all active policies"""
        active_policies = Policy.objects.filter(active=True).prefetch_related('criteria')
        logger.info(f"Checking {active_policies.count()} policies for {self.device.hostname}")

        for policy in active_policies:
            self._evaluate_policy(policy)

    def _evaluate_policy(self, policy):
        """Evaluate a single policy against the device"""
        for criteria in policy.criteria.all():
            if not self._check_criteria(criteria):
                self._record_policy_violation(policy, criteria)

    def _record_policy_violation(self, policy, criteria):
        """Record a policy violation"""
        violation = {
            'type': 'policy_violation',
            'policy': policy.name,
            'criteria': criteria.criteria_type,
            'condition': criteria.condition,
            'value': criteria.value,
            'description': criteria.description,
            'severity': policy.severity or 'medium'
        }
        self.violations.append(violation)
        logger.warning(f"Policy violation: {policy.name} on {self.device.hostname}")

    def _check_criteria(self, criteria):
        """Check a single policy criteria against the device"""
        criteria_type = criteria.criteria_type.lower()

        check_methods = {
            'installed_software': self._check_software_criteria,
            'software': self._check_software_criteria,
            'os_version': self._check_os_criteria,
            'os': self._check_os_criteria,
            'last_scan_time': self._check_last_scan_criteria,
            'last scan': self._check_last_scan_criteria,
            'device_type': self._check_device_type_criteria,
            'device type': self._check_device_type_criteria
        }

        check_method = check_methods.get(criteria_type)
        if not check_method:
            logger.error(f"Unknown criteria type: {criteria_type}")
            return False

        return check_method(criteria)

    def _check_software_criteria(self, criteria):
        """Check installed software criteria"""
        installed_software = self.device.installedsoftware.all()
        condition = criteria.condition.lower()
        value = criteria.value.lower()

        if condition == 'equals':
            name, version = value.split(':') if ':' in value else (value, None)
            if version:
                return installed_software.filter(
                    name__iexact=name,
                    version__iexact=version
                ).exists()
            return installed_software.filter(name__iexact=name).exists()

        elif condition == 'contains':
            return installed_software.filter(name__icontains=value).exists()

        elif condition == 'minimum':
            try:
                return installed_software.count() >= int(value)
            except ValueError:
                logger.error(f"Invalid minimum count: {value}")
                return False

        elif condition == 'should not be installed':
            return not installed_software.filter(name__iexact=value).exists()

        logger.warning(f"Unsupported condition: {condition}")
        return False

    def _check_os_criteria(self, criteria):
        """Check OS-related policy criteria"""
        device_os = self.device.os.lower()
        expected = criteria.value.lower()
        condition = criteria.condition.lower()

        if condition == 'equals':
            return device_os == expected
        elif condition == 'contains':
            return expected in device_os
        elif condition == 'minimum':
            return device_os >= expected  # Simple version comparison

        logger.warning(f"Unsupported OS condition: {condition}")
        return False

    def _check_last_scan_criteria(self, criteria):
        """Check last scan time criteria"""
        try:
            max_hours = int(criteria.value)
            threshold = timezone.now() - timedelta(hours=max_hours)
            return self.device.last_scan and self.device.last_scan >= threshold
        except ValueError:
            logger.error(f"Invalid hours value: {criteria.value}")
            return False

    def _check_device_type_criteria(self, criteria):
        """Check device type criteria"""
        device_type = self.device.device_type.lower()
        expected = criteria.value.lower()
        condition = criteria.condition.lower()

        if condition == 'equals':
            return device_type == expected
        elif condition == 'contains':
            return expected in device_type

        logger.warning(f"Unsupported device type condition: {condition}")
        return False

    def _determine_compliance(self):
        """Determine final compliance status based on findings"""
        self.compliant = not (self.blocked_software_found or self.violations)

        # Validate ML assessment against actual findings
        if self.ml_assessment['status'] != 'error':
            ml_correct = (
                    (self.ml_assessment['status'] == 'compliant' and self.compliant) or
                    (self.ml_assessment['status'] == 'non-compliant' and not self.compliant)
            )
            logger.info(
                f"ML validation: {'Correct' if ml_correct else 'Incorrect'} "
                f"(Predicted: {self.ml_assessment['status']}, Actual: {self.compliant})"
            )

    def _update_device_status(self):
        """Update device status based on scan results"""
        try:
            if not self.compliant:
                self.device.status = 'non-compliant'
                actions = self._generate_remediation_actions()
                self.device.actions = actions
                logger.warning(f"Device {self.device.hostname} marked non-compliant")
            else:
                self.device.status = 'compliant'
                self.device.actions = "No actions required"
                logger.info(f"Device {self.device.hostname} is compliant")

            self.device.last_scan = self.scan_time
            self.device.save()
        except Exception as e:
            logger.error(f"Failed to update device status: {str(e)}")

    def _generate_remediation_actions(self):
        """Generate remediation actions based on violations"""
        actions = []

        # Add ML recommendations if available
        if self.ml_assessment.get('recommended_actions'):
            actions.append("ML Recommendations:")
            actions.append(self.ml_assessment['recommended_actions'])

        # Add violation-specific actions
        for violation in self.violations:
            remediation = self._get_remediation_suggestion(violation)
            actions.append(f"{violation['policy']}: {remediation}")

        return "\n".join(actions)

    def _get_remediation_suggestion(self, violation):
        """Get remediation suggestion for a specific violation"""
        if violation['type'] == 'blocked_software':
            return (
                f"Remove blocked software: {violation['name']} "
                f"(Publisher: {violation['publisher']})"
            )

        elif violation['type'] == 'policy_violation':
            criteria_type = violation['criteria'].lower()

            if 'software' in criteria_type:
                if 'should not be' in violation['condition'].lower():
                    return f"Uninstall software: {violation['value']}"
                else:
                    return f"Install required software: {violation['value']}"

            elif 'os' in criteria_type:
                return f"Update OS to meet requirement: {violation['value']}"

            elif 'last scan' in criteria_type:
                return "Run a new compliance scan immediately"

        return "Review policy requirements and consult IT documentation"

    def _create_activity_report(self):
        """Create detailed activity report for the scan"""
        try:
            report_details = self._generate_report_details()

            ActivityReport.objects.create(
                device=self.device,
                scan_time=self.scan_time,
                scan_status='compliant' if self.compliant else 'non-compliant',
                compliance_status='compliant' if self.compliant else 'non-compliant',
                actions_taken="Scan completed",
                scan_report=report_details,
                ml_insights=self.ml_assessment.get('explanation', ''),
                ml_confidence=self.ml_assessment.get('confidence', 0),
                ml_status=self.ml_assessment.get('status', '')
            )
        except Exception as e:
            logger.error(f"Failed to create activity report: {str(e)}")

    def _generate_report_details(self):
        """Generate detailed report content"""
        report = []

        # Add ML assessment section
        if self.ml_assessment['status'] != 'error':
            report.append(
                f"ML Assessment: {self.ml_assessment['status']} "
                f"(Confidence: {self.ml_assessment['confidence']:.0%})"
            )
            report.append(f"Explanation: {self.ml_assessment['explanation']}")
            report.append("")

        # Add violations section
        if self.blocked_software_found:
            report.append("Critical Issues Found:")
            report.extend(
                f"- {v['name']} {v['version']} (Blocked Software)"
                for v in self.violations if v['type'] == 'blocked_software'
            )
            report.append("")

        if self.violations:
            report.append("Policy Violations:")
            report.extend(
                f"- {v['policy']}: {v['description']} (Severity: {v['severity']})"
                for v in self.violations if v['type'] != 'blocked_software'
            )
        else:
            report.append("No violations found - device is compliant")

        return "\n".join(report)

    def _create_notifications(self):
        """Create notifications for violations"""
        if not self.violations:
            logger.info("No violations found, skipping notifications")
            return

        try:
            # Determine who to notify
            recipients = self._get_notification_recipients()

            # Prepare notifications
            notifications = [
                self._create_notification_for_user(user)
                for user in recipients
            ]

            # Bulk create notifications
            Notification.objects.bulk_create(notifications)
            logger.info(f"Created {len(notifications)} notifications")
        except Exception as e:
            logger.error(f"Failed to create notifications: {str(e)}")

    def _get_notification_recipients(self):
        """Determine who should receive notifications"""
        recipients = set()

        # Always notify device owner if exists
        if self.device.user:
            recipients.add(self.device.user)

        # Notify admins for critical issues
        if any(v['severity'] == 'critical' for v in self.violations):
            recipients.update(User.objects.filter(role='Admin'))

        # Notify security team for high severity
        if any(v['severity'] in ['critical', 'high'] for v in self.violations):
            recipients.update(User.objects.filter(role='Security'))

        return recipients

    def _create_notification_for_user(self, user):
        """Create a notification for a specific user"""
        # Prepare violation summary
        violations_summary = "\n".join(
            f"- {v['policy']}: {v['description']}"
            for v in self.violations
        )

        # Prepare message
        message = (
            f"Compliance Alert for {self.device.hostname}:\n"
            f"Status: {'Compliant' if self.compliant else 'Non-Compliant'}\n"
            f"Issues Found:\n{violations_summary}\n\n"
            f"Recommended Actions:\n{self.device.actions}"
        )

        return Notification(
            user=user,
            device=self.device,
            notification_type='non-compliant' if not self.compliant else 'info',
            message=message,
            policy=self.blocked_policy if self.blocked_software_found else None,
            timestamp=self.scan_time,
            severity='critical' if self.blocked_software_found else 'high'
        )


def scan_all_devices():
    """Scan all devices for compliance"""
    scanner = ComplianceScanner()
    devices = Device.objects.all().order_by('-last_scan')[:1000]  # Limit to 1000 devices

    logger.info(f"Starting compliance scan for {devices.count()} devices")

    results = []
    for device in devices:
        try:
            is_compliant, violations = scanner.scan_device(device)
            results.append({
                'device': device.hostname,
                'compliant': is_compliant,
                'violations': len(violations)
            })
        except Exception as e:
            logger.error(f"Failed to scan {device.hostname}: {str(e)}")
            results.append({
                'device': device.hostname,
                'error': str(e)
            })

    logger.info("Completed scanning all devices")
    return results


def scan_single_device(device_id):
    """Scan a single device by ID"""
    try:
        device = Device.objects.get(id=device_id)
        scanner = ComplianceScanner()
        return scanner.scan_device(device)
    except Device.DoesNotExist:
        logger.error(f"Device {device_id} not found")
        return None, None
    except Exception as e:
        logger.error(f"Error scanning device {device_id}: {str(e)}")
        return None, None