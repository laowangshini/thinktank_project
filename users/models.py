from django.db import models
from django.contrib.auth.models import AbstractUser

class User(models.Model):
    ROLE_CHOICES = [
        ('editor', 'Editor'),
        ('admin', 'Admin'),
        ('researcher', 'Researcher'),
    ]

    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)  # 注意：建议用 Django 的 password hashing
    full_name = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'users'