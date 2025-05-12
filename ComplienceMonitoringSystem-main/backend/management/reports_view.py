from django.shortcuts import render
from django.views import View
from django.db.models import Count, Q, F, Case, When, Value, IntegerField, CharField
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Device, InstalledSoftware, ActivityReport, Notification, Policy, BlockedSoftware


class ReportsView(LoginRequiredMixin, View):
    template_name = 'reports/reports.html'

    def get(self, request):
        context = {
            'report_types': self.get_report_types(),
            'selected_report': request.GET.get('report', 'compliance_summary'),
            'time_range': request.GET.get('time_range', '7d'),
        }

        report_method = getattr(self, f"get_{context['selected_report']}_report", None)
        if report_method:
            context.update(report_method(request))

        return render(request, self.template_name, context)

    def get_report_types(self):
        return [
            {'id': 'compliance_summary', 'name': 'Compliance Summary'},
            {'id': 'device_status', 'name': 'Device Status Distribution'},
            {'id': 'software_inventory', 'name': 'Software Inventory'},
            {'id': 'blocked_software', 'name': 'Blocked Software Detections'},
            {'id': 'policy_violations', 'name': 'Policy Violations'},
            {'id': 'anomalies', 'name': 'Anomaly Detection'},
            {'id': 'scan_activity', 'name': 'Scan Activity'},
            {'id': 'notification_summary', 'name': 'Notification Summary'},
            {'id': 'os_distribution', 'name': 'OS Distribution'},
        ]

    def get_time_filters(self, time_range):
        now = timezone.now()
        if time_range == '24h':
            return now - timedelta(hours=24)
        elif time_range == '7d':
            return now - timedelta(days=7)
        elif time_range == '30d':
            return now - timedelta(days=30)
        elif time_range == '90d':
            return now - timedelta(days=90)
        return None

    def get_compliance_summary_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        device_status = (
            Device.objects
            .values('status')
            .annotate(count=Count('id'))
        )

        scan_trends_qs = ActivityReport.objects
        if time_filter:
            scan_trends_qs = scan_trends_qs.filter(scan_time__gte=time_filter)

        scan_trends = (
            scan_trends_qs
            .values('scan_time__date')
            .annotate(
                compliant=Count(Case(When(compliance_status='compliant', then=1))),
                non_compliant=Count(Case(When(compliance_status='non-compliant', then=1))),
                warning=Count(Case(When(compliance_status='warning', then=1)))
            )
            .order_by('scan_time__date')
        )

        common_issues = (
            ActivityReport.objects
            .filter(compliance_status='non-compliant')
            .values('actions_taken')
            .annotate(count=Count('id'))
            .order_by('-count')[:5]
        )

        return {
            'device_status': list(device_status),
            'scan_trends': list(scan_trends),
            'common_issues': list(common_issues),
            'report_title': 'Compliance Summary Report',
        }

    def get_device_status_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        status_by_type = (
            Device.objects
            .values('device_type', 'status')
            .annotate(count=Count('id'))
            .order_by('device_type', 'status')
        )

        status_by_dept = (
            Device.objects
            .values('department', 'status')
            .annotate(count=Count('id'))
            .order_by('department', 'status')
        )

        status_changes_qs = ActivityReport.objects
        if time_filter:
            status_changes_qs = status_changes_qs.filter(scan_time__gte=time_filter)

        status_changes = (
            status_changes_qs
            .values('scan_time__date', 'scan_status')
            .annotate(count=Count('id'))
            .order_by('scan_time__date', 'scan_status')
        )

        return {
            'status_by_type': list(status_by_type),
            'status_by_dept': list(status_by_dept),
            'status_changes': list(status_changes),
            'report_title': 'Device Status Distribution Report',
        }

    def get_software_inventory_report(self, request):
        common_software = (
            InstalledSoftware.objects
            .values('name', 'publisher', 'status')
            .annotate(
                install_count=Count('id'),
                device_count=Count('device', distinct=True)
            )
            .order_by('-device_count')[:20]
        )

        software_by_status = (
            InstalledSoftware.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        software_by_os = (
            InstalledSoftware.objects
            .values('device__os', 'status')
            .annotate(count=Count('id'))
            .order_by('device__os', '-count')
        )

        return {
            'common_software': list(common_software),
            'software_by_status': list(software_by_status),
            'software_by_os': list(software_by_os),
            'report_title': 'Software Inventory Report',
        }

    def get_blocked_software_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        detections_qs = InstalledSoftware.objects.filter(status='blocked')
        if time_filter:
            detections_qs = detections_qs.filter(install_date__gte=time_filter)

        detections = (
            detections_qs
            .values('name', 'publisher', 'version', 'device__hostname', 'device__department')
            .annotate(count=Count('id'))
        )

        frequent_blocked = (
            InstalledSoftware.objects
            .filter(status='blocked')
            .values('name', 'publisher')
            .annotate(
                count=Count('id'),
                device_count=Count('device', distinct=True)
            )
            .order_by('-count')[:10]
        )

        blocked_by_dept = (
            InstalledSoftware.objects
            .filter(status='blocked')
            .values('device__department', 'name')
            .annotate(count=Count('id'))
            .order_by('device__department', '-count')
        )

        return {
            'detections': list(detections),
            'frequent_blocked': list(frequent_blocked),
            'blocked_by_dept': list(blocked_by_dept),
            'report_title': 'Blocked Software Detections Report',
        }

    def get_policy_violations_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        violations_qs = Notification.objects.filter(notification_type='non-compliant', policy__isnull=False)
        if time_filter:
            violations_qs = violations_qs.filter(timestamp__gte=time_filter)

        violations = (
            violations_qs
            .values('policy__name', 'device__hostname', 'device__department')
            .annotate(count=Count('id'))
        )

        violations_by_policy = (
            violations_qs
            .values('policy__name')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        violations_by_dept = (
            violations_qs
            .values('device__department', 'policy__name')
            .annotate(count=Count('id'))
            .order_by('device__department', '-count')
        )

        return {
            'violations': list(violations),
            'violations_by_policy': list(violations_by_policy),
            'violations_by_dept': list(violations_by_dept),
            'report_title': 'Policy Violations Report',
        }

    def get_anomalies_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        anomalies_qs = Notification.objects.filter(notification_type='warning', policy__isnull=True)
        if time_filter:
            anomalies_qs = anomalies_qs.filter(timestamp__gte=time_filter)

        anomalies = (
            anomalies_qs
            .values('device__hostname', 'device__department', 'message')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        anomaly_types = (
            anomalies_qs
            .annotate(
                anomaly_type=Case(
                    When(message__icontains='CPU', then=Value('CPU Usage')),
                    When(message__icontains='memory', then=Value('Memory Usage')),
                    When(message__icontains='disk', then=Value('Disk Usage')),
                    When(message__icontains='network', then=Value('Network Activity')),
                    default=Value('Other'),
                    output_field=CharField()
                )
            )
            .values('anomaly_type')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return {
            'anomalies': list(anomalies),
            'anomaly_types': list(anomaly_types),
            'report_title': 'Anomaly Detection Report',
        }

    def get_scan_activity_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        scan_qs = ActivityReport.objects
        if time_filter:
            scan_qs = scan_qs.filter(scan_time__gte=time_filter)

        scan_activity = (
            scan_qs
            .values('scan_time__date')
            .annotate(
                scan_count=Count('id'),
                device_count=Count('device', distinct=True)
            )
            .order_by('scan_time__date')
        )

        scan_results = (
            scan_qs
            .values('scan_status')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        active_devices = (
            scan_qs
            .values('device__hostname', 'device__department')
            .annotate(
                scan_count=Count('id'),
                last_scan=F('device__last_scan')
            )
            .order_by('-scan_count')[:10]
        )

        return {
            'scan_activity': list(scan_activity),
            'scan_results': list(scan_results),
            'active_devices': list(active_devices),
            'report_title': 'Scan Activity Report',
        }

    def get_notification_summary_report(self, request):
        time_filter = self.get_time_filters(request.GET.get('time_range', '7d'))

        notification_qs = Notification.objects
        if time_filter:
            notification_qs = notification_qs.filter(timestamp__gte=time_filter)

        notification_trends = (
            notification_qs
            .values('timestamp__date', 'notification_type')
            .annotate(count=Count('id'))
            .order_by('timestamp__date', 'notification_type')
        )

        return {
            'notification_trends': list(notification_trends),
            'report_title': 'Notification Summary Report',
        }

    def get_os_distribution_report(self, request):
        os_distribution = (
            Device.objects
            .values('os')
            .annotate(count=Count('id'))
            .order_by('-count')
        )

        return {
            'os_distribution': list(os_distribution),
            'report_title': 'OS Distribution Report',
        }
