from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
class Complaint(models.Model):
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('inprogress', 'inprogress'),
        ('resolved', 'resolved'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    desc = models.TextField()
    image = models.ImageField(upload_to='complaints/', null=True, blank=True)
    location = models.CharField(max_length=225)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    status = models.CharField(choices=STATUS_CHOICES, max_length=20, default='pending')
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)