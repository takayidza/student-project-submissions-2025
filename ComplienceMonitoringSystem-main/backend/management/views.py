import socket

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count , Q
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseForbidden
from datetime import datetime
import platform , re
from .utils import evaluate_device_compliance, get_installed_software, detect_os, detect_device_type

from .models import (
    User, Device, InstalledSoftware, Policy, 
    PolicyCriteria, Notification, ActivityReport ,BlockedSoftware, InstalledSoftware
)
from .forms import (
    LoginForm, DeviceForm, PolicyForm, PolicyCriteriaForm , BlockedSoftwareForm
)


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test

def is_admin(user):
    return user.role == 'Admin'

@login_required
def monitoring(request):
    """
    Main monitoring dashboard showing all devices with real-time status
    """
    devices = Device.objects.all()
    if request.user.role != 'Admin':
        # Filter devices based on user permissions if not admin
        devices = devices.filter(owner=request.user)
    
    context = {
        'devices': devices,
        'page_title': 'Live Monitoring',
    }
    return render(request, 'dashboard/monitoring/index.html', context)

@login_required
def device_monitoring(request, device_id):
    """
    Detailed monitoring view for a specific device
    """
    device = get_object_or_404(Device, pk=device_id)
    
    # Check if user has permission to view this device
    if request.user.role != 'Admin' and device.owner != request.user:
        return HttpResponseForbidden("You don't have permission to monitor this device")
    
    # Get monitoring data for this device
    monitoring_data = device # You'll need to implement this method
    
    context = {
        'device': device,
        'monitoring_data': monitoring_data,
        'page_title': f'Monitoring: {device.id}',
    }
    return render(request, 'dashboard/monitoring/device_detail.html', context)

@login_required
@user_passes_test(is_admin)
def monitoring_logs(request):
    """
    View for historical monitoring logs (admin only)
    """
    logs = MonitoringLog.objects.all().order_by('-timestamp')
    
    # Add filtering options
    device_filter = request.GET.get('device')
    if device_filter:
        logs = logs.filter(device_id=device_filter)
    
    date_from = request.GET.get('date_from')
    if date_from:
        logs = logs.filter(timestamp__gte=date_from)
    
    date_to = request.GET.get('date_to')
    if date_to:
        logs = logs.filter(timestamp__lte=date_to)
    
    context = {
        'logs': logs,
        'devices': Device.objects.all(),  # For the filter dropdown
        'page_title': 'Monitoring Logs',
    }
    return render(request, 'monitoring/logs.html', context)

# Authentication Views
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                
                # Register device if it doesn't exist or update existing device
                device = register_device(request, user)
                
                # Scan for installed software and check compliance
                # scan_result = scan_device_software(device)
                #
                # # Show message based on compliance status
                # if scan_result['status'] == 'compliant':
                #     messages.success(request, f"Welcome back, {user.username}! Your device is compliant.")
                # elif scan_result['status'] == 'warning':
                #     messages.warning(request, f"Welcome back, {user.username}. Your device has some warnings that need attention.")
                # else:
                #     messages.error(request, f"Welcome back, {user.username}. Your device is non-compliant with security policies.")

                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = LoginForm()
    
    return render(request, 'login.html', {'form': form})


import platform
import socket
import uuid
import logging
import re
import subprocess

from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

logger = logging.getLogger(__name__)

import socket
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]  # get first IP if multiple
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
def get_client_hostname(ip):
    try:
        hostname = socket.gethostbyaddr(ip)[0]
    except socket.herror:
        hostname = 'Unknown'
    return hostname
from user_agents import parse

def get_client_os(request):
    """
    Returns the operating system family from the client's User-Agent string.
    Requires `user-agents` package.
    """
    ua_string = request.META.get('HTTP_USER_AGENT', '')
    user_agent = parse(ua_string)
    return user_agent.os.family

def register_device(request, user):
    """
    Register a device if it does not exist. Update info if it does.
    """
    client_ip = get_client_ip(request)
    os_name = get_client_os(request)
    device_type = detect_device_type()
    hostname =  get_client_hostname(client_ip)  #platform.node() or socket.gethostname()

    # Try to get a unique machine identifier
    try:
        system_platform = platform.system()
        if system_platform == "Windows":
            import wmi
            machine_id = wmi.WMI().Win32_ComputerSystemProduct()[0].UUID
        elif system_platform == "Linux":
            with open('/etc/machine-id', 'r') as f:
                machine_id = f.read().strip()
        elif system_platform == "Darwin":
            ioreg_output = subprocess.check_output(["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]).decode()
            machine_id = re.search(r'"IOPlatformUUID" = "([^"]+)"', ioreg_output).group(1)
        else:
            machine_id = str(uuid.getnode())
    except Exception as e:
        logger.warning(f"Failed to get hardware ID: {e}")
        machine_id = f"{hostname}-{user.username}"

    department = getattr(user, 'department', 'General')
    ip_address = get_client_ip(request)

    try:
        with transaction.atomic():
            device = Device.objects.filter(user=user).first()

            if device:
                device.hostname = hostname
                device.ip_address = ip_address
                device.save()
                return device

            device = Device.objects.filter(hostname=hostname).first()

            if device:
                device.machine_id = machine_id
                device.ip_address = ip_address
                device.user = user
                device.save()
                return device

            # Create new device
            device = Device.objects.create(
                user=user,
                hostname=hostname,
                machine_id=machine_id,
                os=os_name,
                department=department,
                device_type=device_type,
                status='non-compliant',
                ip_address=ip_address,
                actions='New device registered. Scan required.'
            )

            ActivityReport.objects.create(
                device=device,
                scan_status='non-compliant',
                compliance_status='non-compliant',
                actions_taken='New device registered',
                scan_report=f'Device registration. OS: {os_name}, Type: {device_type}, Hostname: {hostname}'
            )

            default_policy = Policy.objects.filter(active=True).first()
            if default_policy:
                Notification.objects.create(
                    user=user,
                    device=device,
                    notification_type='non-compliant',
                    message=f'New device {hostname} has been registered and requires a compliance scan',
                    policy=default_policy
                )

            return device
    except Exception as e:
        logger.error(f"Failed to register device for user {user.username}: {e}")
        raise

from .utils import evaluate_device_compliance

def scan_device_software(device):
    """
    Scan for installed software and check against blocked software database
    """
    # Get installed software based on OS
    installed_software = get_installed_software(device)
    
    # Get applicable blocked software for this OS
    blocked_software = BlockedSoftware.objects.filter(
        Q(applicable_os=device.os) | Q(applicable_os='all'),
        active=True
    )
    
    # Track scan results
    scan_report_content = []
    compliance_status = 'compliant'
    blocked_found = []
    
    # Process each installed software
    for software in installed_software:
        # Save or update the software entry
        sw_record, created = InstalledSoftware.objects.update_or_create(
            device=device,
            name=software['name'],
            defaults={
                'version': software.get('version') or 'Unknown',
                'publisher': software.get('publisher', 'Unknown'),
                'status': 'active'
            }
        )
        
        # Check if this software is in the blocked list
        is_blocked = False
        matched_blocked_sw = None
        
        for blocked in blocked_software:
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
        
        if is_blocked and matched_blocked_sw:
            blocked_found.append({
                'software': software,
                'blocked_record': matched_blocked_sw
            })
            
            # Set compliance status based on severity
            if matched_blocked_sw.severity in ['critical', 'high']:
                compliance_status = 'non-compliant'
            elif matched_blocked_sw.severity == 'medium' and compliance_status != 'non-compliant':
                compliance_status = 'warning'
            
            # Update software status
            sw_record.status = 'blocked'
            sw_record.save()
            
            scan_report_content.append(f"BLOCKED ({matched_blocked_sw.severity.upper()}): {software['name']} {software.get('version', '')}")
        else:
            scan_report_content.append(f"OK: {software['name']} {software.get('version', '')}")
    
    # Update device status
    device.status = compliance_status
    if compliance_status != 'compliant':
        device.actions = 'Remove blocked software'
    else:
        device.actions = 'No action required'
    device.save()
    
    # Evaluate device compliance against active policies
    active_policies = Policy.objects.filter(active=True)
    for policy in active_policies:
        evaluate_device_compliance(device, policy)
    
    # Create activity report
    activity_report = ActivityReport.objects.create(
        device=device,
        scan_status=compliance_status,
        compliance_status=compliance_status,
        actions_taken='Software scan completed during login',
        scan_report='\n'.join(scan_report_content)
    )
    
    # Create notifications for blocked software
    try:
        # Get policy for software compliance
        software_policy = Policy.objects.filter(category='Software', active=True).first()
        if not software_policy:
            software_policy = Policy.objects.filter(active=True).first()
            
        if software_policy and blocked_found:
            for blocked_item in blocked_found:
                blocked_sw = blocked_item['blocked_record']
                software = blocked_item['software']
                
                Notification.objects.create(
                    user=device.user,
                    device=device,
                    notification_type='non-compliant' if blocked_sw.severity in ['critical', 'high'] else 'warning',
                    message=f"Blocked software detected: {software['name']} {software.get('version', '')}. Severity: {blocked_sw.severity.upper()}. {blocked_sw.description}",
                    timestamp=datetime.now(),
                    policy=software_policy,
                    read=False
                )
    except Policy.DoesNotExist:
        pass  # Handle case where no policies exist
    
    return {
        'status': compliance_status,
        'blocked_count': len(blocked_found),
        'scanned_count': len(installed_software),
        'activity_report': activity_report
    }

def get_client_ip(request):
    """Get the client's IP address from the request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip



@login_required
@user_passes_test(is_admin)
def blocked_software_list(request):
    """
    View to list all blocked software entries
    """
    blocked_software = BlockedSoftware.objects.all()
    
    # Apply filters if provided
    os_filter = request.GET.get('os')
    if os_filter:
        blocked_software = blocked_software.filter(applicable_os=os_filter)
        
    severity_filter = request.GET.get('severity')
    if severity_filter:
        blocked_software = blocked_software.filter(severity=severity_filter)
        
    active_filter = request.GET.get('active')
    if active_filter is not None:
        blocked_software = blocked_software.filter(active=(active_filter == '1'))
    
    # Get stats about blocked software usage
    blocked_software = blocked_software.annotate(
        installations_count=Count('applicable_os', distinct=True)
    )
    
    # Get OS choices for the filter dropdown
    os_choices = dict(BlockedSoftware.OS_CHOICES)
    severity_choices = dict(BlockedSoftware.SEVERITY_CHOICES)
    
    context = {
        'page_title': 'Blocked Software',
        'blocked_software': blocked_software,
        'os_choices': os_choices,
        'severity_choices': severity_choices,
        'os_filter': os_filter,
        'severity_filter': severity_filter,
        'active_filter': active_filter,
    }
    
    return render(request, 'dashboard/blocked_software/list.html', context)

@login_required
@user_passes_test(is_admin)
def blocked_software_detail(request, pk):
    """
    View to see details of a blocked software entry
    """
    software = get_object_or_404(BlockedSoftware, pk=pk)
    
    # Get installations of this blocked software
    installations = InstalledSoftware.objects.filter(status='blocked')
    
    # Filter based on the detection pattern or name
    if software.detection_pattern:
        # This would need a raw query or a more complex filter in a real implementation
        # For simplicity, we'll just use the name-based filter here
        installations = installations.filter(name__icontains=software.name)
    else:
        installations = installations.filter(name__icontains=software.name)
    
    context = {
        'page_title': f'Blocked Software: {software.name}',
        'software': software,
        'installations': installations,
    }
    
    return render(request, 'blocked_software/detail.html', context)

@login_required
@user_passes_test(is_admin)
def blocked_software_create(request):
    """
    View to create a new blocked software entry
    """
    if request.method == 'POST':
        form = BlockedSoftwareForm(request.POST)
        if form.is_valid():
            blocked_software = form.save(commit=False)
            blocked_software.created_by = request.user
            blocked_software.save()
            
            messages.success(request, f"Blocked software '{blocked_software.name}' created successfully.")
            return redirect('blocked_software_list')
    else:
        form = BlockedSoftwareForm()
    
    context = {
        'page_title': 'Add Blocked Software',
        'form': form,
    }
    
    return render(request, 'dashboard/blocked_software/form.html', context)

@login_required
@user_passes_test(is_admin)
def blocked_software_update(request, pk):
    """
    View to update a blocked software entry
    """
    software = get_object_or_404(BlockedSoftware, pk=pk)
    
    if request.method == 'POST':
        form = BlockedSoftwareForm(request.POST, instance=software)
        if form.is_valid():
            form.save()
            
            messages.success(request, f"Blocked software '{software.name}' updated successfully.")
            return redirect('blocked_software_list')
    else:
        form = BlockedSoftwareForm(instance=software)
    
    context = {
        'page_title': f'Edit Blocked Software: {software.name}',
        'form': form,
        'software': software,
    }
    
    return render(request, 'blocked_software/form.html', context)

@login_required
@user_passes_test(is_admin)
def blocked_software_delete(request, pk):
    """
    View to delete a blocked software entry
    """
    software = get_object_or_404(BlockedSoftware, pk=pk)
    
    if request.method == 'POST':
        name = software.name
        software.delete()
        messages.success(request, f"Blocked software '{name}' deleted successfully.")
        return redirect('blocked_software_list')
    
    context = {
        'page_title': f'Delete Blocked Software: {software.name}',
        'software': software,
    }
    
    return render(request, 'blocked_software/delete.html', context)

@login_required
@user_passes_test(is_admin)
def blocked_software_toggle_active(request, pk):
    """
    View to quickly toggle the active status of a blocked software
    """
    software = get_object_or_404(BlockedSoftware, pk=pk)
    software.active = not software.active
    software.save()
    
    status = "activated" if software.active else "deactivated"
    messages.success(request, f"Blocked software '{software.name}' {status} successfully.")
    
    # Return to the previous page if available
    if 'next' in request.GET:
        return HttpResponseRedirect(request.GET['next'])
    
    return redirect('blocked_software_list')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

# Dashboard View
@login_required
def dashboard(request):
    # Get statistics for dashboard
    total_devices = Device.objects.count()
    compliant_devices = Device.objects.filter(status='compliant').count()
    non_compliant_devices = Device.objects.filter(status='non-compliant').count()
    warning_devices = Device.objects.filter(status='warning').count()
    
    # Get device distribution by type
    device_types = Device.objects.values('device_type').annotate(count=Count('device_type'))
    
    # Get device distribution by OS
    os_distribution = Device.objects.values('os').annotate(count=Count('os'))
    
    # Get recent notifications
    recent_notifications = Notification.objects.filter(read=False).order_by('-timestamp')[:5]
    
    context = {
        'total_devices': total_devices,
        'compliant_devices': compliant_devices,
        'non_compliant_devices': non_compliant_devices,
        'warning_devices': warning_devices,
        'device_types': device_types,
        'os_distribution': os_distribution,
        'recent_notifications': recent_notifications,
    }
    
    return render(request, 'dashboard/dashboard.html', context)

# Device Views
@login_required
def device_list(request):
    # For Admin users, show all devices
    if request.user.role == 'Admin':
        devices = Device.objects.all()
    # For regular users, show only their devices
    else:
        devices = Device.objects.filter(user=request.user)
        
    return render(request, 'dashboard/device/device_list.html', {'devices': devices})

@login_required
def device_detail(request, pk):
    device = get_object_or_404(Device, pk=pk)
    
    # Check if user has permission to view this device
    if request.user.role != 'Admin' and device.user != request.user:
        messages.error(request, "You don't have permission to view this device.")
        return redirect('device_list')
    
    # Get installed software for this device
    installed_software = InstalledSoftware.objects.filter(device=device)
    
    # Get activity reports for this device
    activity_reports = ActivityReport.objects.filter(device=device).order_by('-scan_time')
    
    context = {
        'device': device,
        'installed_software': installed_software,
        'activity_reports': activity_reports,
    }
    
    return render(request, 'dashboard/device/device_detail.html', context)

@login_required
def device_create(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            # Create new device but don't save yet
            device = form.save(commit=False)
            
            # Set the user based on form input (admins) or current user (regular users)
            if request.user.role == 'Admin' and 'user' in form.cleaned_data:
                device.user = form.cleaned_data['user']
            else:
                device.user = request.user
                
            # Save the device
            device.save()
            messages.success(request, "Device added successfully.")
            return redirect('device_detail', pk=device.pk)
    else:
        # For admins, show form with user field
        if request.user.role == 'Admin':
            form = DeviceForm()
        # For regular users, show form without user field
        else:
            form = DeviceForm(exclude_fields=['user'])
    
    return render(request, 'dashboard/device/device_form.html', {'form': form, 'action': 'Add'})

@login_required
def device_update(request, pk):
    device = get_object_or_404(Device, pk=pk)
    
    # Check if user has permission to edit this device
    if request.user.role != 'Admin' and device.user != request.user:
        messages.error(request, "You don't have permission to edit this device.")
        return redirect('device_list')
    
    if request.method == 'POST':
        # For admins, allow changing all fields including user
        if request.user.role == 'Admin':
            form = DeviceForm(request.POST, instance=device)
        # For regular users, exclude certain fields
        else:
            form = DeviceForm(request.POST, instance=device, exclude_fields=['user'])
            
        if form.is_valid():
            form.save()
            messages.success(request, "Device updated successfully.")
            return redirect('device_detail', pk=device.pk)
    else:
        # For admins, show form with all fields
        if request.user.role == 'Admin':
            form = DeviceForm(instance=device)
        # For regular users, show form with restricted fields
        else:
            form = DeviceForm(instance=device, exclude_fields=['user'])
    
    return render(request, 'dashboard/device/device_form.html', {'form': form, 'device': device, 'action': 'Edit'})

@login_required
def device_delete(request, pk):
    device = get_object_or_404(Device, pk=pk)
    
    # Check if user has permission to delete this device
    if request.user.role != 'Admin' and device.user != request.user:
        messages.error(request, "You don't have permission to delete this device.")
        return redirect('device_list')
    
    if request.method == 'POST':
        device.delete()
        messages.success(request, "Device deleted successfully.")
        return redirect('device_list')
    
    return render(request, 'dashboard/device/device_confirm_delete.html', {'device': device})

# Notification Views
@login_required
def notification_list(request):
    # For Admin users, show all notifications
    if request.user.role == 'Admin':
        notifications = Notification.objects.all().order_by('-timestamp')
    # For regular users, show only their notifications
    else:
        notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
        
    return render(request, 'dashboard/notification/notification_list.html', {'notifications': notifications})

@login_required
def notification_detail(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    # Check if user has permission to view this notification
    if request.user.role != 'Admin' and notification.user != request.user:
        messages.error(request, "You don't have permission to view this notification.")
        return redirect('notification_list')
    
    # Mark as read when viewed
    if not notification.read:
        notification.read = True
        notification.save()
    
    return render(request, 'dashboard/notification/notification_detail.html', {'notification': notification})

@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk)
    
    # Check if user has permission
    if request.user.role != 'Admin' and notification.user != request.user:
        messages.error(request, "You don't have permission to update this notification.")
        return redirect('notification_list')
    
    notification.read = True
    notification.save()
    
    # Return to referring page or notification list
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('notification_list')))

# Policy Views
@login_required
def policy_list(request):
    # Only admins can view policies
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to view policies.")
        return redirect('dashboard')
    
    policies = Policy.objects.all()
    return render(request, 'dashboard/policy/policy_list.html', {'policies': policies})

@login_required
def policy_detail(request, pk):
    # Only admins can view policy details
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to view policy details.")
        return redirect('dashboard')
    
    policy = get_object_or_404(Policy, pk=pk)
    criteria = PolicyCriteria.objects.filter(policy=policy)
    
    return render(request, 'dashboard/policy/policy_detail.html', {
        'policy': policy,
        'criteria': criteria
    })

@login_required
def policy_create(request):
    # Only admins can create policies
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to create policies.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PolicyForm(request.POST)
        if form.is_valid():
            policy = form.save()
            messages.success(request, "Policy created successfully.")
            return redirect('policy_detail', pk=policy.pk)
    else:
        form = PolicyForm()
    
    return render(request, 'dashboard/policy/policy_form.html', {'form': form, 'action': 'Create'})

@login_required
def policy_update(request, pk):
    # Only admins can update policies
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to update policies.")
        return redirect('dashboard')
    
    policy = get_object_or_404(Policy, pk=pk)
    
    if request.method == 'POST':
        form = PolicyForm(request.POST, instance=policy)
        if form.is_valid():
            form.save()
            messages.success(request, "Policy updated successfully.")
            return redirect('policy_detail', pk=policy.pk)
    else:
        form = PolicyForm(instance=policy)
    
    return render(request, 'dashboard/policy/policy_form.html', {
        'form': form, 
        'policy': policy,
        'action': 'Update'
    })

@login_required
def policy_delete(request, pk):
    # Only admins can delete policies
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to delete policies.")
        return redirect('dashboard')
    
    policy = get_object_or_404(Policy, pk=pk)
    
    if request.method == 'POST':
        policy.delete()
        messages.success(request, "Policy deleted successfully.")
        return redirect('policy_list')
    
    return render(request, 'dashboard/policy/policy_confirm_delete.html', {'policy': policy})

# Policy Criteria Views
@login_required
def policy_criteria_create(request, policy_id):
    # Only admins can create policy criteria
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to create policy criteria.")
        return redirect('dashboard')
    
    policy = get_object_or_404(Policy, pk=policy_id)
    
    if request.method == 'POST':
        form = PolicyCriteriaForm(request.POST)
        if form.is_valid():
            criteria = form.save(commit=False)
            criteria.policy = policy
            criteria.save()
            messages.success(request, "Policy criteria added successfully.")
            return redirect('policy_detail', pk=policy.pk)
    else:
        form = PolicyCriteriaForm()
    
    return render(request, 'dashboard/policy/policy_criteria_form.html', {
        'form': form,
        'policy': policy,
        'action': 'Add'
    })

@login_required
def policy_criteria_update(request, pk):
    # Only admins can update policy criteria
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to update policy criteria.")
        return redirect('dashboard')
    
    criteria = get_object_or_404(PolicyCriteria, pk=pk)
    policy = criteria.policy
    
    if request.method == 'POST':
        form = PolicyCriteriaForm(request.POST, instance=criteria)
        if form.is_valid():
            form.save()
            messages.success(request, "Policy criteria updated successfully.")
            return redirect('policy_detail', pk=policy.pk)
    else:
        form = PolicyCriteriaForm(instance=criteria)
    
    return render(request, 'dashboard/policy/policy_criteria_form.html', {
        'form': form,
        'criteria': criteria,
        'policy': policy,
        'action': 'Update'
    })

@login_required
def policy_criteria_delete(request, pk):
    # Only admins can delete policy criteria
    if request.user.role != 'Admin':
        messages.error(request, "You don't have permission to delete policy criteria.")
        return redirect('dashboard')
    
    criteria = get_object_or_404(PolicyCriteria, pk=pk)
    policy = criteria.policy
    
    if request.method == 'POST':
        criteria.delete()
        messages.success(request, "Policy criteria deleted successfully.")
        return redirect('policy_detail', pk=policy.pk)
    
    return render(request, 'dashboard/policy/policy_criteria_confirm_delete.html', {
        'criteria': criteria,
        'policy': policy
    })
    
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Device
from .ai.compliance_analyzer import ComplianceAnalyzer

@api_view(['GET'])
def device_compliance_analysis(request, device_id):
    try:
        device = Device.objects.get(pk=device_id)
        analysis = device.analyze_compliance()
        return Response(analysis)
    except Device.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)

@api_view(['POST'])
def retrain_compliance_model(request):
    from django.core.management import call_command
    call_command('train_ai_models')
    return Response({"status": "retraining started"})

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Device
from management.utilites.scanner import DeviceScanner  # Adjust this import path as needed
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Device

@api_view(['POST'])
def scan_one_device(request, device_id):
    try:
        device = Device.objects.get(id=device_id)
    except Device.DoesNotExist:
        return Response({
            "error": "Device not found"
        }, status=status.HTTP_404_NOT_FOUND)

    scanner = DeviceScanner(device)
    result = scanner.scan_device()

    return Response({
        "message": f"Scan completed for device {device.id}",
        "device_id": device.id,
        "device_name": str(device),
        "scan_result": result
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
def scan_all_devices(request):
    devices = Device.objects.all()
    results = []

    for device in devices:
        scanner = DeviceScanner(device)
        result = scanner.scan_device()
        results.append({
            "device_id": device.id,
            "device_name": str(device),
            "scan_result": result,
        })

    return Response({
        "message": "Scan completed for all devices",
        "results": results
    }, status=status.HTTP_200_OK)
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from management.models import Device, InstalledSoftware
from management.ai.compliance_analyzer import ComplianceAnalyzer
from management.ai.anomaly_detector import AnomalyDetector
from management.ai.malware_detector import MalwareDetector
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_device(request, device_id):
    """API endpoint to analyze device compliance"""
    try:
        device = Device.objects.get(pk=device_id)
        result = device.analyze_compliance()
        return Response(result)
    except Device.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)
    except Exception as e:
        logger.error(f"Error analyzing device {device_id}: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_anomalies(request, device_id):
    """API endpoint to check for anomalies"""
    try:
        device = Device.objects.get(pk=device_id)
        result = device.check_for_anomalies()
        return Response(result)
    except Device.DoesNotExist:
        return Response({"error": "Device not found"}, status=404)
    except Exception as e:
        logger.error(f"Error checking anomalies for device {device_id}: {str(e)}")
        return Response({"error": str(e)}, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def scan_software(request, software_id):
    """API endpoint to scan software for malware"""
    try:
        software = InstalledSoftware.objects.get(pk=software_id)
        detector = MalwareDetector()
        risk_score = detector.assess_risk(
            software.name,
            software.publisher,
            software.version
        )
        return Response({
            "software_id": software_id,
            "name": software.name,
            "risk_score": risk_score,
            "is_malicious": risk_score > 0.85
        })
    except InstalledSoftware.DoesNotExist:
        return Response({"error": "Software not found"}, status=404)
    except Exception as e:
        logger.error(f"Error scanning software {software_id}: {str(e)}")
        return Response({"error": str(e)}, status=500)


from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from .models import InstalledSoftware, Device
from .forms import InstalledSoftwareForm
from django.http import JsonResponse


class SoftwareDetailView(LoginRequiredMixin, DetailView):
    model = InstalledSoftware
    template_name = 'dashboard/software/software_detail.html'
    context_object_name = 'software'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        software = self.get_object()

        # Get related software (same name, different devices/versions)
        context['related_software'] = InstalledSoftware.objects.filter(
            name=software.name
        ).exclude(pk=software.pk).select_related('device')[:10]

        # Get activity logs (you'll need to implement this model)
        context['activity_logs'] = []  # Replace with actual query if you have logs

        return context


class SoftwareUpdateView(LoginRequiredMixin, UpdateView):
    model = InstalledSoftware
    form_class = InstalledSoftwareForm
    template_name = 'dashboard/software/software_form.html'

    def get_success_url(self):
        return reverse_lazy('software_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Software information updated successfully.')
        return super().form_valid(form)


@login_required
def software_delete(request, pk):
    software = get_object_or_404(InstalledSoftware, pk=pk)
    device_pk = software.device.pk
    if request.method == 'POST':
        software.delete()
        messages.success(request, 'Software record deleted successfully.')
        return redirect('device_detail', pk=device_pk)
    return render(request, 'software/software_confirm_delete.html', {'software': software})


@login_required
def software_approve(request, pk):
    software = get_object_or_404(InstalledSoftware, pk=pk)
    software.status = 'approved'
    software.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Software approved successfully.'})
    messages.success(request, 'Software approved successfully.')
    return redirect('software_detail', pk=pk)


@login_required
def software_restrict(request, pk):
    software = get_object_or_404(InstalledSoftware, pk=pk)
    software.status = 'restricted'
    software.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Software restricted successfully.'})
    messages.success(request, 'Software restricted successfully.')
    return redirect('software_detail', pk=pk)


@login_required
def software_block(request, pk):
    software = get_object_or_404(InstalledSoftware, pk=pk)
    software.status = 'blocked'
    software.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'message': 'Software blocked successfully.'})
    messages.success(request, 'Software blocked successfully.')
    return redirect('software_detail', pk=pk)


@login_required
def scan_software(request, pk):
    software = get_object_or_404(InstalledSoftware, pk=pk)
    risk_score = software.check_for_malware()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f'Scan completed with risk score: {risk_score}',
            'risk_score': risk_score,
            'is_malicious': risk_score > 0.85
        })

    if risk_score > 0.85:
        messages.warning(request, f'Potential malware detected! Risk score: {risk_score}')
    else:
        messages.success(request, f'Scan completed. Risk score: {risk_score}')

    return redirect('software_detail', pk=pk)


from django.shortcuts import render
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Device, ActivityReport, InstalledSoftware, Notification
from django.db.models import Count, Q
from datetime import datetime, timedelta
from django.utils import timezone


class ReportsView(LoginRequiredMixin, View):
    template_name = 'dashboard/reports/dashboard.html'

    def get(self, request):
        # Device status statistics
        device_status = Device.objects.all().values('status').annotate(count=Count('status'))
        status_data = {item['status']: item['count'] for item in device_status}

        # Software compliance statistics
        software_status = InstalledSoftware.objects.all().values('status').annotate(count=Count('status'))
        software_data = {item['status']: item['count'] for item in software_status}

        # Recent activity reports
        recent_reports = ActivityReport.objects.select_related('device').order_by('-scan_time')[:10]

        # Notification statistics
        notifications = Notification.objects.filter(
            timestamp__gte=timezone.now() - timedelta(days=7)
        ).values('notification_type').annotate(count=Count('notification_type'))
        notification_data = {item['notification_type']: item['count'] for item in notifications}

        # Device type distribution
        device_types = Device.objects.values('device_type').annotate(count=Count('device_type'))
        device_type_data = {item['device_type']: item['count'] for item in device_types}

        context = {
            'status_data': status_data,
            'software_data': software_data,
            'recent_reports': recent_reports,
            'notification_data': notification_data,
            'device_type_data': device_type_data,
        }

        return render(request, self.template_name, context)


from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from .models import Device


class DeviceReportView(LoginRequiredMixin, ListView):
    template_name = 'dashboard/reports/device_report.html'
    context_object_name = 'compliance_history'
    paginate_by = 10

    def get_queryset(self):
        device = get_object_or_404(Device, pk=self.kwargs['device_id'])
        return device.activity_report_set.order_by('-scan_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        device = get_object_or_404(Device, pk=self.kwargs['device_id'])

        context['device'] = device
        context['software_list'] = device.installedsoftware.all()
        return context


class ComplianceReportView(LoginRequiredMixin, View):
    template_name = 'dashboard/reports/compliance_report.html'

    def get(self, request):
        # Get non-compliant devices
        non_compliant_devices = Device.objects.filter(
            Q(status='non-compliant') | Q(status='warning')
        ).select_related('user').order_by('-last_scan')

        # Get blocked software installations
        blocked_software = InstalledSoftware.objects.filter(
            status='blocked'
        ).select_related('device', 'device__user')

        context = {
            'non_compliant_devices': non_compliant_devices,
            'blocked_software': blocked_software,
        }

        return render(request, self.template_name, context)


# views.py
from rest_framework import viewsets, generics
from rest_framework.response import Response
from rest_framework.decorators import action, api_view
from .models import Device
from .serializers import DeviceSerializer
from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# ViewSet with search filter
class DeviceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer
    filter_backends = [SearchFilter]
    search_fields = ['hostname', 'ip_address', 'department', 'os']

# Optional: Detail endpoint via /api/devices/by-hostname/{hostname}/
@api_view(['GET'])
def get_device_by_hostname(request, hostname):
    device = get_object_or_404(Device, hostname=hostname)
    serializer = DeviceSerializer(device)
    return Response(serializer.data)
