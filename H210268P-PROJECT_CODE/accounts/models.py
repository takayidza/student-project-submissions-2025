from django.db import models
from django.contrib.auth.models import AbstractUser

ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Basic User', 'Basic User'),
    ]
# Create your models here.
import uuid
class CustomUser(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='customuser_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default='Basic User',
        help_text='Role of the user',
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=15, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = 'Admin'
        super().save(*args, **kwargs)


class About(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='about')
    about = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"About {self.user.username}"