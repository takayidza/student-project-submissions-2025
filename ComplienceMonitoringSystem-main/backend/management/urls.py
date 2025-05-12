from django.urls import path, include
from . import views
from . import api_views
from .views import device_compliance_analysis, retrain_compliance_model, scan_all_devices, analyze_device, \
    check_anomalies, scan_software, scan_one_device, ReportsView, DeviceReportView, ComplianceReportView
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, get_device_by_hostname

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')

urlpatterns = [

    path('api/', include(router.urls)),
    path('api/devices/by-hostname/<str:hostname>/', get_device_by_hostname, name='device-by-hostname'),
    path('api/download/client.exe/', api_views.download_client_exe, name='download_client_exe'),
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),  # Main dashboard as homepage
    path('dashboard/', views.dashboard, name='dashboard'),  # Alternative path
    
    # Devices
    path('devices/', views.device_list, name='device_list'),
    path('devices/add/', views.device_create, name='device_create'),
    path('devices/<int:pk>/', views.device_detail, name='device_detail'),
    path('devices/<int:pk>/edit/', views.device_update, name='device_update'),
    path('devices/<int:pk>/delete/', views.device_delete, name='device_delete'),
    
    # Monitoring
    path('monitoring/', views.monitoring, name='monitoring'),
    path('monitoring/<int:device_id>/', views.device_monitoring, name='device_monitoring'),
    path('monitoring/logs/', views.monitoring_logs, name='monitoring_logs'),
    
    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/<int:pk>/', views.notification_detail, name='notification_detail'),
    path('notifications/mark-read/<int:pk>/', views.notification_mark_read, name='notification_mark_read'),
    
    # Policies
    path('policies/', views.policy_list, name='policy_list'),
    path('policies/add/', views.policy_create, name='policy_create'),
    path('policies/<int:pk>/', views.policy_detail, name='policy_detail'),
    path('policies/<int:pk>/edit/', views.policy_update, name='policy_update'),
    path('policies/<int:pk>/delete/', views.policy_delete, name='policy_delete'),
    
    # Policy Criteria
    path('policies/<int:policy_id>/criteria/add/', views.policy_criteria_create, name='policy_criteria_create'),
    path('policies/criteria/<int:pk>/edit/', views.policy_criteria_update, name='policy_criteria_update'),
    path('policies/criteria/<int:pk>/delete/', views.policy_criteria_delete, name='policy_criteria_delete'),
    
    path('blocked-software/', views.blocked_software_list, name='blocked_software_list'),
    path('blocked-software/add/', views.blocked_software_create, name='blocked_software_create'),
    path('blocked-software/<int:pk>/', views.blocked_software_detail, name='blocked_software_detail'),
    path('blocked-software/<int:pk>/edit/', views.blocked_software_update, name='blocked_software_update'),
    path('blocked-software/<int:pk>/delete/', views.blocked_software_delete, name='blocked_software_delete'),
    path('blocked-software/<int:pk>/toggle-active/', views.blocked_software_toggle_active, name='blocked_software_toggle_active'),

    path('api/device/<int:device_id>/compliance/', device_compliance_analysis, name='device_compliance_analysis'),
    path('api/compliance/retrain/', retrain_compliance_model, name='retrain_compliance_model'),
    path('scan-all-devices/', scan_all_devices, name='scan_all_devices'),
    path('device/<int:device_id>/scan/', scan_one_device, name='scan-one-device'),

    path('devices/<int:device_id>/analyze/', analyze_device, name='analyze_device'),
    path('devices/<int:device_id>/check-anomalies/', check_anomalies, name='check_anomalies'),
    path('software/<int:software_id>/scan/', scan_software, name='scan_software'),

    path('api/devices/<int:device_id>/monitoring/', api_views.device_monitoring, name='api_device_monitoring'),
    path('api/devices/<int:device_id>/process/<int:pid>/', api_views.process_details, name='api_process_details'),
    path('api/devices/<int:device_id>/process/<int:pid>/kill/', api_views.kill_process, name='api_kill_process'),

    path('software/<int:pk>/', views.SoftwareDetailView.as_view(), name='software_detail'),
    path('software/<int:pk>/update/', views.SoftwareUpdateView.as_view(), name='software_update'),
    path('software/<int:pk>/delete/', views.software_delete, name='software_delete'),
    path('software/<int:pk>/approve/', views.software_approve, name='software_approve'),
    path('software/<int:pk>/restrict/', views.software_restrict, name='software_restrict'),
    path('software/<int:pk>/block/', views.software_block, name='software_block'),
    path('software/<int:pk>/scan/', views.scan_software, name='scan_software'),
    # path('software/versions/<str:name>/', views.software_versions, name='software_versions'),

    path('reports/', ReportsView.as_view(), name='reports_dashboard'),
    path('reports/device/<int:device_id>/', DeviceReportView.as_view(), name='device_report'),
    path('reports/compliance/', ComplianceReportView.as_view(), name='compliance_report'),
]
