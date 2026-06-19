import random
from django.db import models
from django.contrib.auth.models import AbstractUser

def generate_user_id():
    # Since we can't reference CustomUser directly before it is defined,
    # we will do the collision check dynamically or just generate it.
    # To follow the rules strictly:
    uid = random.randint(100000, 999999)
    return uid

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('analyst', 'Analyst'),
        ('viewer', 'Viewer'),
    )
    
    user_id = models.IntegerField(unique=True, editable=False, db_index=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.user_id:
            # Collision check
            while True:
                uid = random.randint(100000, 999999)
                if not CustomUser.objects.filter(user_id=uid).exists():
                    self.user_id = uid
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('dataset_upload', 'Dataset Upload'),
        ('dataset_activate', 'Dataset Activate'),
        ('dataset_delete', 'Dataset Delete'),
        ('export_report', 'Export Report'),
        ('role_change', 'Role Change'),
        ('user_status', 'User Status Change'),
        ('user_delete', 'User Delete'),
    )

    actor = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='audit_events')
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    target = models.CharField(max_length=255, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        actor = self.actor.username if self.actor else 'system'
        return f"{actor}: {self.get_action_display()} {self.target}".strip()
