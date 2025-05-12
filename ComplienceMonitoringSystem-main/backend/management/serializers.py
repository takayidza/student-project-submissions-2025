from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import *

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Get the username and password from the request
        username = attrs.get("username")
        password = attrs.get("password")
        
        # Authenticate the user using Django's built-in authentication system
        user = authenticate(username=username, password=password)
        
        print(user,user)
        
        if user is None or not user.is_active:
            # Raise an error if the user is inactive or credentials are invalid
            raise serializers.ValidationError("No active account found with the given credentials")
        
        # Call the parent method to get the token data
        data = super().validate(attrs)
        
        # Add any custom fields to the token response, like the user's role
        data['role'] = user.role if hasattr(user, 'role') else 'user'
        
        return data


# Serializer for GET operations (to display the data)
class DeviceGetSerializer(serializers.ModelSerializer):
    # Optionally, you can also add the related user's username to make the user readable
    user = serializers.StringRelatedField()

    class Meta:
        model = Device
        fields = '__all__'  # This will include all fields from the Device model

# Serializer for POST operations (to handle data creation)
class DevicePostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['user', 'department', 'os', 'status', 'actions', 'device_type']  # Specify which fields are allowed for POST

    # Optional: You can also add validation for fields if necessary
    def validate_status(self, value):
        # Ensure status is one of the predefined choices
        if value not in dict(Device.STATUS_CHOICES).keys():
            raise serializers.ValidationError("Invalid status")
        return value
    

class NotificationSerializer(serializers.ModelSerializer):
    # To serialize related fields
    user = serializers.StringRelatedField()  # Display the username
    notification_type = serializers.ChoiceField(choices=STATUS_CHOICES)  # Notification type
    policy_name = serializers.CharField(source='policy.name')  # Policy name field

    class Meta:
        model = Notification
        fields = ['user', 'device', 'notification_type', 'message', 'timestamp', 'read', 'policy', 'policy_name']
        read_only_fields = ['timestamp']

class NotificationPostSerializer(serializers.ModelSerializer):
    # For creating new notifications, no need for read-only fields
    class Meta:
        model = Notification
        fields = ['user', 'device', 'notification_type', 'message', 'timestamp', 'read', 'policy']

    def create(self, validated_data):
        # In case of any specific processing before creating an instance (if needed)
        notification = Notification.objects.create(**validated_data)
        return notification




# Serializer for POST operations (to handle data creation)
class PolicyPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Policy
        fields = ['name', 'category', 'description', 'active']  # Specify which fields are allowed for POST

    def validate_active(self, value):
        # Ensure the active field is a boolean
        if not isinstance(value, bool):
            raise serializers.ValidationError("Active field must be a boolean value.")
        return value
    
# Serializer for GET operations (to display the data)
class PolicyCriteriaGetSerializer(serializers.ModelSerializer):
    # Optional: You can also display the related policy name for easier readability
    policy_name = serializers.CharField(source='policy.name')

    class Meta:
        model = PolicyCriteria
        fields = ['policy', 'criteria_type', 'condition', 'value', 'description', 'policy_name']

# Serializer for POST operations (to handle data creation)
class PolicyCriteriaPostSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyCriteria
        fields = ['policy', 'criteria_type', 'condition', 'value', 'description']

    
# Serializer for GET operations (to display the data)
class PolicyGetSerializer(serializers.ModelSerializer):
    criteria = PolicyCriteriaPostSerializer(many=True, read_only=True)  # Assuming a ForeignKey or ManyToMany

    class Meta:
        model = Policy
        fields = '__all__'


# serializers.py
from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'id', 'hostname', 'ip_address', 'department', 'os', 'status',
            'device_type', 'cpu_usage', 'memory_usage', 'disk_usage',
            'network_download_speed', 'network_upload_speed'
        ]
