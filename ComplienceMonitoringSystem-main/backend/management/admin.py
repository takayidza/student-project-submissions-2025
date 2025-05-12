from django.contrib import admin
from .models import User, Device, InstalledSoftware, Notification, ActivityReport, Policy, PolicyCriteria , BlockedSoftware

@admin.register(BlockedSoftware)
class BlockedSoftwareAdmin(admin.ModelAdmin):
    list_display = ('name', 'publisher', 'applicable_os', 'severity', 'active')
    list_filter = ('applicable_os', 'severity', 'active', 'created_at')
    search_fields = ('name', 'publisher', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('name', 'publisher', 'applicable_os', 'active')
        }),
        ('Detection Details', {
            'fields': ('description', 'severity', 'detection_pattern')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
# Custom User Admin
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    search_fields = ('username', 'email')
    list_filter = ('role', 'is_active')
    ordering = ('username',)

# Register User model with custom admin
admin.site.register(User, UserAdmin)

# Device Admin
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'os', 'last_scan', 'status', 'device_type')
    search_fields = ('user__username', 'department', 'os')
    list_filter = ('os', 'status')
    ordering = ('user',)

# Register Device model with custom admin
admin.site.register(Device, DeviceAdmin)

# Installed Software Admin
class InstalledSoftwareAdmin(admin.ModelAdmin):
    list_display = ('device', 'name', 'version', 'install_date', 'status')
    search_fields = ('device__user__username', 'name')
    list_filter = ('status',)
    ordering = ('device',)

# Register Installed Software model with custom admin
admin.site.register(InstalledSoftware, InstalledSoftwareAdmin)

# Notification Admin
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'device', 'notification_type', 'message', 'timestamp', 'read', 'policy')
    search_fields = ('user__username', 'device__user__username', 'notification_type', 'message')
    list_filter = ('notification_type', 'read', 'timestamp')
    ordering = ('-timestamp',)

# Register Notification model with custom admin
admin.site.register(Notification, NotificationAdmin)

# Activity Report Admin
class ActivityReportAdmin(admin.ModelAdmin):
    list_display = ('device', 'scan_time', 'scan_status', 'compliance_status', 'actions_taken', 'scan_report')
    search_fields = ('device__user__username', 'device__department')
    list_filter = ('scan_status', 'compliance_status')
    ordering = ('-scan_time',)

# Register ActivityReport model with custom admin
admin.site.register(ActivityReport, ActivityReportAdmin)

# Policy Admin
class PolicyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    ordering = ('name',)

# Register Policy model with custom admin
admin.site.register(Policy, PolicyAdmin)

# PolicyCriteria Admin
class PolicyCriteriaAdmin(admin.ModelAdmin):
    list_display = ('policy', 'criteria_type', 'condition', 'value', 'description')
    search_fields = ('policy__name', 'criteria_type', 'condition', 'value')
    list_filter = ('criteria_type',)
    ordering = ('policy',)

# Register PolicyCriteria model with custom admin
admin.site.register(PolicyCriteria, PolicyCriteriaAdmin)
