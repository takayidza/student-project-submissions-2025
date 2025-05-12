# models.py
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db.models import Q
from django.utils import timezone

from management.ai.anomaly_detector import AnomalyDetector
from management.ai.compliance_analyzer import ComplianceAnalyzer
import logging

logger = logging.getLogger(__name__)

STATUS_CHOICES = [
        ('warning', 'Warning'),
        ('non-compliant', 'Non-Compliant'),
        ('compliant', 'Compliant'),
    ]

DEVICE_TYPE_CHOICES = [
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('server', 'Server'),
    ]


# Custom User model with roles (Admin/User)
class User(AbstractUser):
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('User', 'User'),
    ]
    role = models.CharField(max_length=5, choices=ROLE_CHOICES, default='Admin')
    telegram_chat_id = models.CharField(max_length=50, blank=True, null=True)
    last_scan = models.DateTimeField(null=True, blank=True)
    # Override related_name for groups and user_permissions to avoid clashes
    groups = models.ManyToManyField(
        Group,
        related_name='custom_user_set',  # Change this to avoid clashes
        blank=True,
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='custom_user_permissions_set',  # Change this to avoid clashes
        blank=True,
    )

    def __str__(self):
        return self.username


# Device Model
class Device(models.Model):

    
    OS_CHOICES = [
        ('Windows', 'Windows'),
        ('Windows Server', 'Windows Server'),
        ('macOS', 'macOS'),
        ('Ubuntu', 'Ubuntu'),
        ('Debian', 'Debian'),
        ('Fedora', 'Fedora'),
        ('Red Hat', 'Red Hat Enterprise Linux'),
        ('CentOS', 'CentOS'),
        ('SUSE', 'SUSE Linux'),
        ('Arch Linux', 'Arch Linux'),
        ('Kali Linux', 'Kali Linux'),
        ('FreeBSD', 'FreeBSD'),
        ('OpenBSD', 'OpenBSD'),
        ('iOS', 'iOS'),
        ('iPadOS', 'iPadOS'),
        ('Android', 'Android'),
        ('Chrome OS', 'Chrome OS'),
        ('Solaris', 'Solaris'),
        ('IBM AIX', 'IBM AIX'),
        ('HP-UX', 'HP-UX'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    department = models.CharField(max_length=100)
    machine_id = models.CharField(max_length=100, default="Allan")
    ip_address = models.CharField(max_length=100, default="127.0.0.1")
    hostname = models.CharField(max_length=100)
    os = models.CharField(max_length=50, choices=OS_CHOICES)
    last_scan = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='non-compliant',  # Default status
    )
    actions = models.TextField()
    device_type = models.CharField(max_length=10, choices=DEVICE_TYPE_CHOICES , default="laptop")
    # Metrics fields
    cpu_usage = models.FloatField(default=0.0)  # CPU usage in percentage
    memory_usage = models.FloatField(default=0.0)  # Memory usage in percentage
    disk_usage = models.FloatField(default=0.0)  # Disk usage in percentage
    network_download_speed = models.FloatField(default=0.0)  # Download speed in KB/s
    network_upload_speed = models.FloatField(default=0.0)  # Upload speed in KB/s
    json_data = models.JSONField(null=True, blank=True)
    def __str__(self):
        return f"{self.hostname} Device - {self.user.username}"

    def save(self, *args, **kwargs):
        """
        Override save with signal control and validation
        """
        from django.db import transaction
        from django.core.exceptions import ValidationError
        if not self.pk and not self.hostname:
            raise ValidationError("Hostname is required")

        using = kwargs.pop('using', 'default')
        update_fields = kwargs.get('update_fields')

        with transaction.atomic(using=using):
            # Skip signal processing for internal updates
            if getattr(self, '_no_signal', False):
                kwargs['_no_signal'] = True
                super().save(*args, **kwargs)
                return

            # Normal save with signals
            super().save(*args, **kwargs)

            # Ensure related objects are in consistent state
            if update_fields is None or 'status' in update_fields:
                self.installedsoftware.exclude(
                    status='approved'
                ).update(status='approved')

    def make_compliant(self):
        self.status = 'compliant'
        self.save()

    def make_non_compliant(self):
        self.status = 'non-compliant'
        self.save()

    def get_cpu_usage_color(self):
        if self.cpu_usage > 80:
            return 'danger'
        elif self.cpu_usage > 60:
            return 'warning'
        else:
            return 'primary'

    def get_memory_usage_color(self):
        if self.memory_usage > 85:
            return 'danger'
        elif self.memory_usage > 70:
            return 'warning'
        else:
            return 'info'

    def get_disk_usage_color(self):
        if self.disk_usage > 90:
            return 'danger'
        elif self.disk_usage > 80:
            return 'warning'
        else:
            return 'success'

    def get_security_status_color(self):
        # Assuming a higher percentage means more vulnerabilities for this example
        if self.security_status > 70:
            return 'danger'
        elif self.security_status > 50:
            return 'warning'
        else:
            return 'success'

    @property
    def security_status(self):
        """
        Return an integer score based on the current status.
        """
        status_score_map = {
            'compliant': 20,
            'warning': 65,
            'non-compliant': 90,
        }
        return status_score_map.get(self.status, 0)
    def analyze_compliance(self):
        """Enhanced compliance analysis with error handling and logging"""
        from .models import InstalledSoftware, ActivityReport
        from .ai.compliance_analyzer import ComplianceAnalyzer

        try:
            # Gather comprehensive data
            software_list = list(self.installedsoftware.all().values(
                'name', 'version', 'publisher', 'install_date'
            ))

            historical_reports = list(ActivityReport.objects.filter(
                device=self
            ).order_by('-scan_time').values('scan_status', 'compliance_status', 'scan_time')[:10])

            device_data = {
                'os': self.os,
                'device_type': self.device_type,
                'last_scan': self.last_scan,
                'historical_reports': historical_reports,
                'ip_address': self.ip_address,
                'hostname': self.hostname
            }

            # AI analysis with fallback
            analyzer = ComplianceAnalyzer()
            analysis = analyzer.predict_compliance_status(device_data, software_list)

            # Handle analysis errors
            if analysis.get('status') == 'error':
                logger.error(
                    f"Compliance analysis failed for device {self.id}: {analysis.get('error')}"
                )
                return {
                    'status': 'error',
                    'error': analysis.get('error'),
                    'device_id': self.id
                }

            # Update device status and actions
            self.status = analysis['status']
            self.actions = analysis['recommended_actions']
            self.save()

            # Create detailed notification if non-compliant
            if analysis['status'] != 'compliant':
                self._create_compliance_notification(analysis)

            # Log the analysis result
            logger.info(
                f"Compliance analysis completed for device {self.id}. "
                f"Status: {analysis['status']}. Confidence: {analysis['confidence']:.2f}"
            )

            return analysis

        except Exception as e:
            logger.exception(f"Unexpected error analyzing device {self.id}")
            return {
                'status': 'error',
                'error': str(e),
                'device_id': self.id
            }

    def _create_compliance_notification(self, analysis):
        """Helper method to create detailed notifications"""
        from .models import Notification

        # Get all admins and the device owner
        recipients = list(User.objects.filter(role='Admin'))
        if self.user and self.user not in recipients:
            recipients.append(self.user)
        policy, created = Policy.objects.get_or_create(name='AI Analysis')
        for user in recipients:
            # Create the notification
            Notification.objects.create(
                user=user,
                device=self,
                notification_type=analysis['status'],
                message=(
                    f"Compliance Alert for {self.hostname}:\n"
                    f"Status: {analysis['status'].upper()}\n"
                    f"Reason: {analysis['explanation']}\n"
                    f"Required Actions: {analysis['recommended_actions']}"
                ),
                policy=policy,  # Use the policy object from get_or_create
                timestamp=timezone.now()  # Ensure timezone.now() is used correctly
            )

    def check_for_anomalies(self):
        """Enhanced anomaly detection with peer comparison"""
        from .ai.anomaly_detector import AnomalyDetector

        try:
            detector = AnomalyDetector()

            # Get comparable peers
            peers = Device.objects.filter(
                department=self.department,
                device_type=self.device_type
            ).exclude(pk=self.pk).select_related('user')

            if not peers.exists():
                return {
                    'is_anomaly': False,
                    'reason': 'No comparable devices in department',
                    'device_id': self.id
                }

            # Prepare peer data with more features
            peer_data = []
            for peer in peers:
                peer_data.append({
                    'os': peer.os,
                    'software_count': peer.installedsoftware.count(),
                    'status': peer.status,
                    'last_scan_age': (timezone.now() - peer.last_scan).days,
                    'user_role': peer.user.role if peer.user else 'unknown'
                })

            # Current device data
            current_data = {
                'os': self.os,
                'software_count': self.installedsoftware.count(),
                'status': self.status,
                'last_scan_age': (timezone.now() - self.last_scan).days,
                'user_role': self.user.role if self.user else 'unknown'
            }

            # Detect anomaly
            result = detector.detect(current_data, peer_data)
            result['device_id'] = self.id

            # Create notification if anomaly found
            if result.get('is_anomaly'):
                self._create_anomaly_notification(result)

            return result

        except Exception as e:
            logger.exception(f"Anomaly detection failed for device {self.id}")
            return {
                'is_anomaly': False,
                'error': str(e),
                'device_id': self.id
            }

    def _create_anomaly_notification(self, anomaly_result):
        """Helper method to create anomaly notifications"""
        from .models import Notification

        Notification.objects.create(
            user=self.user or User.objects.filter(role='Admin').first(),
            device=self,
            notification_type='warning',
            message=(
                f"Anomaly Detected in {self.hostname}:\n"
                f"Score: {anomaly_result.get('score', 0):.2f}\n"
                f"Reason: {anomaly_result.get('description', 'Unknown')}"
            ),
            policy=None,
            timestamp=timezone.now()
        )

# Installed Software Model
class InstalledSoftware(models.Model):
    STATUS_CHOICES = [
        ('approved','Approved'),
        ('restricted','Restricted'),
        ('blocked', 'Blocked')
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='installedsoftware')
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    publisher = models.CharField(max_length=100)
    install_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='approved')

    def __str__(self):
        return f"{self.name} - {self.version} (On {self.device})"

    from django.db.models import Q
    def save(self, *args, **kwargs):
        """
        Override save with signal control and validation
        """
        if not self.name:
            raise ValidationError("Software name is required")

        using = kwargs.pop('using', 'default')

        with transaction.atomic(using=using):
            # Skip signal processing for internal updates
            if getattr(self, '_no_signal', False):
                # kwargs['_no_signal'] = True
                super().save(*args, **kwargs)
                return

            # Normal save with signals
            super().save(*args, **kwargs)

            # Update blocked status without recursion
            if not getattr(self, '_skip_blocked_check', False):
                self._skip_blocked_check = True
                try:
                    self.update_block_status(no_signal=True)
                finally:
                    delattr(self, '_skip_blocked_check')

    def update_block_status(self, no_signal=False):
        """
        Update blocked status with signal control
        """
        current_os = self.device.os
        is_blocked = BlockedSoftware.objects.filter(
            active=True,
            name__iexact=self.name
        ).filter(
            Q(publisher__iexact=self.publisher) | Q(publisher='')
        ).filter(
            Q(applicable_os='all') | Q(applicable_os__iexact=current_os)
        ).exists()

        with transaction.atomic():
            # Get fresh instance to avoid race conditions
            software = InstalledSoftware.objects.get(pk=self.pk)

            if is_blocked and software.status != 'blocked':
                software.status = 'blocked'
                software.save(update_fields=['status'], _no_signal=no_signal)
            elif not is_blocked and software.status == 'blocked':
                software.status = 'approved'
                software.save(update_fields=['status'], _no_signal=no_signal)

    def check_if_blocked(self):
        """
        Check if this installed software is listed in the BlockedSoftware model.
        Updates status and returns True if blocked.
        """
        current_os = self.device.os  # Assuming device has an `operating_system` field

        blocked_matches = BlockedSoftware.objects.filter(
            Q(active=True),
            Q(name__iexact=self.name),
            Q(publisher__iexact=self.publisher) | Q(publisher=''),
            Q(applicable_os='all') | Q(applicable_os__iexact=current_os)
        )

        if blocked_matches.exists():
            self.status = 'blocked'
            self.save()

            # Notify admin
            admin_users = User.objects.filter(role='Admin')
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    device=self.device,
                    notification_type='error',
                    message=f"Blocked software detected: {self.name} {self.version}",
                    policy=None
                )
            return True
        return False

    def check_for_malware(self):
        """Check if software appears malicious"""
        from .ai.malware_detector import MalwareDetector

        detector = MalwareDetector()
        risk_score = detector.assess_risk(
            self.name,
            self.publisher,
            self.version
        )

        if risk_score > 0.85:  # High risk threshold
            self.status = 'blocked'
            self.save()

            # Notify admin
            admin_users = User.objects.filter(role='Admin')
            for admin in admin_users:
                Notification.objects.create(
                    user=admin,
                    device=self.device,
                    notification_type='warning',
                    message=f"Potential malware detected: {self.name} {self.version}",
                    policy=None
                )

        return risk_score


class Policy(models.Model):
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    description = models.TextField()
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set when created
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Override save with validation"""
        if not self.name:
            raise ValidationError("Policy name is required")
        super().save(*args, **kwargs)

    
class PolicyCriteria(models.Model):
    CONDITION_CHOICE = [
        ('equals','Equals'),
        ('contains','Contains'),
        ('minimum','Minimum'),
        ('maximum','Maximum'),
    ]
    CRITERIA_TYPE = [
        ('device_type', 'Device Type'),
        ('os_version', 'OS Version'),
        ('last_scan_time', 'Last Scan Time'),
        ('installed_software', 'Software Installed'),
    ]
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name='criteria')
    criteria_type = models.CharField(max_length=255, choices=CRITERIA_TYPE)
    condition = models.CharField(max_length=255, choices=CONDITION_CHOICE, default='equals')
    value = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Criteria for {self.policy.name}"

    def clean(self):
        """Validation for condition types"""
        if self.condition not in dict(self.CONDITION_CHOICE).keys():
            raise ValidationError(f"Invalid condition: {self.condition}")

    def save(self, *args, **kwargs):
        """Override save with validation"""
        self.clean()
        super().save(*args, **kwargs)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)  # Device reference
    notification_type = models.CharField(max_length=20, choices=[('warning', 'Warning'), ('non-compliant', 'Non-Compliant'), ('compliant', 'Compliant')], default='non-compliant')  # Notification type
    message = models.TextField()  # The notification message
    timestamp = models.DateTimeField(auto_now_add=True)  # When the notification was created
    read = models.BooleanField(default=False)  # Whether the notification is read or not
    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, null=True, blank=True)  # Policy reference
    violation_details = models.JSONField(null=True, blank=True)
    #TODO
    # add description of what exactly is causing device to be non compliant
    
    def __str__(self):
        return f"Notification for {self.user.username} at {self.timestamp}"


# Activity Report Model
class ActivityReport(models.Model):
    COMPLIANCE_CHOICES = [
        ('compliant', 'Compliant'),
        ('non-compliant', 'Non-Compliant'),
        ('warning', 'Warning'),
    ]

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='activity_report_set')
    scan_time = models.DateTimeField(auto_now_add=True)  # Time when the scan was performed
    scan_status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,  # Reusing the status choices from Device model
        default='non-compliant',  # Default status
    )
    compliance_status = models.CharField(
        max_length=20,
        choices=COMPLIANCE_CHOICES,  # New field for compliance status
        default='non-compliant',  # Default compliance status
    )
    actions_taken = models.TextField()  # Actions taken during or after the scan
    scan_report = models.TextField()  # Any details or reports generated from the scan

    def __str__(self):
        return f"Scan Report for {self.device} at {self.scan_time}"


from django.db import models

class BlockedSoftware(models.Model):
    """Model for storing blocked software information"""
    
    OS_CHOICES = [
        ('all', 'All Operating Systems'),
        ('Windows', 'Windows'),
        ('Windows Server', 'Windows Server'),
        ('macOS', 'macOS'),
        ('Ubuntu', 'Ubuntu'),
        ('Debian', 'Debian'),
        ('Fedora', 'Fedora'),
        ('Red Hat', 'Red Hat Enterprise Linux'),
        ('CentOS', 'CentOS'),
        ('SUSE', 'SUSE Linux'),
        ('Arch Linux', 'Arch Linux'),
        ('Kali Linux', 'Kali Linux'),
        ('FreeBSD', 'FreeBSD'),
        ('OpenBSD', 'OpenBSD'),
        ('iOS', 'iOS'),
        ('iPadOS', 'iPadOS'),
        ('Android', 'Android'),
        ('Chrome OS', 'Chrome OS'),
        ('Solaris', 'Solaris'),
        ('IBM AIX', 'IBM AIX'),
        ('HP-UX', 'HP-UX'),
    ]
    
    SEVERITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    name = models.CharField(max_length=255, help_text="Name of the blocked software")
    publisher = models.CharField(max_length=255, blank=True, help_text="Publisher or vendor of the software")
    applicable_os = models.CharField(max_length=50, choices=OS_CHOICES, default='all', help_text="OS this block applies to")
    description = models.TextField(blank=True, help_text="Description of why this software is blocked")
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium', help_text="Severity level of this violation")
    active = models.BooleanField(default=True, help_text="Whether this block is active")
    detection_pattern = models.CharField(max_length=255, blank=True, help_text="Regex pattern to detect this software")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('User', on_delete=models.SET_NULL, null=True, related_name='created_blocks')
    
    class Meta:
        ordering = ['-severity', 'name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['applicable_os']),
            models.Index(fields=['active']),
            models.Index(fields=['severity']),
        ]
        unique_together = ['name', 'publisher', 'applicable_os']
    
    def __str__(self):
        os_text = "All OS" if self.applicable_os == 'all' else self.applicable_os
        return f"{self.name} ({self.publisher}) - {os_text} - {self.get_severity_display()}"

    def clean(self):
        """Validation for OS choices"""
        if self.applicable_os not in dict(self.OS_CHOICES).keys():
            raise ValidationError(f"Invalid OS choice: {self.applicable_os}")

    def save(self, *args, **kwargs):
        """Override save with validation"""
        self.clean()
        super().save(*args, **kwargs)