from django import forms
from .models import User, Device, Policy, PolicyCriteria, Notification, ActivityReport , BlockedSoftware

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control bg-light border-start-0', 
            'placeholder': 'Enter your username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control bg-light border-start-0', 
            'placeholder': 'Enter your password'
        })
    )


class BlockedSoftwareForm(forms.ModelForm):
    class Meta:
        model = BlockedSoftware
        fields = [
            'name', 
            'publisher', 
            'applicable_os', 
            'description', 
            'severity', 
            'active', 
            'detection_pattern'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'detection_pattern': forms.TextInput(attrs={'placeholder': 'Regular expression pattern to match software names'}),
        }
    
    def clean_detection_pattern(self):
        pattern = self.cleaned_data.get('detection_pattern')
        if pattern:
            # Validate that the pattern is a valid regex
            try:
                import re
                re.compile(pattern)
            except re.error:
                raise forms.ValidationError("Please enter a valid regular expression pattern")
        return pattern
    
class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['user', 'department', 'os', 'device_type', 'status', 'actions']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'os': forms.Select(attrs={'class': 'form-select'}),
            'device_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'actions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        exclude_fields = kwargs.pop('exclude_fields', [])
        super(DeviceForm, self).__init__(*args, **kwargs)
        
        # If user field should be excluded
        if 'user' in exclude_fields and 'user' in self.fields:
            del self.fields['user']
        elif 'user' in self.fields:
            # Only show user field with proper styling
            self.fields['user'].widget = forms.Select(attrs={'class': 'form-select'})
            # Limit choices to only show users with 'User' role for Admin users
            self.fields['user'].queryset = User.objects.filter(role='User')

class PolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = ['name', 'category', 'description', 'active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
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
class PolicyCriteriaForm(forms.ModelForm):
    criteria_type = forms.ChoiceField(
        choices=CRITERIA_TYPE,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    condition = forms.ChoiceField(
        choices=CONDITION_CHOICE,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    class Meta:
        model = PolicyCriteria
        fields = ['criteria_type', 'condition', 'value', 'description']
        widgets = {
            'value': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class NotificationFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All'),
        ('read', 'Read'),
        ('unread', 'Unread'),
    ]
    
    TYPE_CHOICES = [
        ('', 'All Types'),
        ('warning', 'Warning'),
        ('non-compliant', 'Non-Compliant'),
        ('compliant', 'Compliant'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    notification_type = forms.ChoiceField(
        choices=TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    from_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    to_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )

class DeviceFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Status'),
        ('compliant', 'Compliant'),
        ('non-compliant', 'Non-Compliant'),
        ('warning', 'Warning'),
    ]
    
    OS_CHOICES = [
        ('', 'All OS'),
        ('Windows', 'Windows'),
        ('Linux', 'Linux'),
        ('macOS', 'macOS'),
    ]
    
    DEVICE_TYPE_CHOICES = [
        ('', 'All Types'),
        ('desktop', 'Desktop'),
        ('laptop', 'Laptop'),
        ('mobile', 'Mobile'),
        ('server', 'Server'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    os = forms.ChoiceField(
        choices=OS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    device_type = forms.ChoiceField(
        choices=DEVICE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Department'})
    )


from django import forms
from .models import InstalledSoftware

class InstalledSoftwareForm(forms.ModelForm):
    class Meta:
        model = InstalledSoftware
        fields = ['name', 'version', 'publisher', 'status',]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            # 'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            # 'install_location': forms.TextInput(attrs={'class': 'form-control'}),
            # 'registry_key': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name