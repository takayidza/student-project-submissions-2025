import uuid
from django.db import models
from accounts.models import CustomUser 
class AccidentProneArea(models.Model):
    RISK_LEVEL_CHOICES = [
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    risk_level = models.CharField(max_length=6, choices=RISK_LEVEL_CHOICES)
    accident_prone = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.risk_level} Risk at ({self.latitude}, {self.longitude})"

class History(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    area = models.ForeignKey(AccidentProneArea, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    speed = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.user} at {self.timestamp}"

class Alert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField(null=True, blank=True)
    start = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert for {self.user} at {self.timestamp}"

class Setting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    notification_enabled = models.BooleanField(default=True)
    language = models.CharField(max_length=20, default='English')

    def __str__(self):
        return f"Settings for {self.user}"

class Prediction(models.Model):
    PREDICTION_RESULT_CHOICES = [
        ('Safe', 'Safe'),
        ('Accident Prone', 'Accident Prone'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8)
    longitude = models.DecimalField(max_digits=11, decimal_places=8)
    prediction_result = models.CharField(max_length=20, choices=PREDICTION_RESULT_CHOICES)
    model_confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prediction for {self.user if self.user else 'Unknown'} at {self.timestamp}"

STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Start', 'Start'),
        ('Arrived', 'Arrived'),
    ]
class Journey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    start = models.CharField(max_length=255, null=True, blank=True)
    destination = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} at {self.timestamp}"
    

class SafetyNotification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.message} at {self.timestamp}"
