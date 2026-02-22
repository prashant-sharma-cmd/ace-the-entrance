import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

class User(AbstractUser):
    email = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    phone_number = PhoneNumberField(blank=True, null=True, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email

class UserOnboarding(models.Model):
    PURPOSE_CHOICES = [
        ('daily_quiz', 'Solving Daily Questions'),
        ('discussion', 'Engaging in Discussion Forums'),
        ('sxc_model_set', 'Checking Out Model Set'),
        ('all', 'Making Complete Use of the Website'),
        ('other', 'Other')
    ]

    FREQUENCY_CHOICES = [
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('rarely', 'Rarely'),
    ]

    DISCOVERY_CHOICES = [
        ('official', 'Official Book'),
        ('google', 'Google Search'),
        ('facebook', 'Facebook'),
        ('instagram', 'Instagram'),
        ('friend', 'Friend'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE,
                                related_name='onboarding')
    primary_purpose = models.CharField(max_length=100, choices=PURPOSE_CHOICES)
    visit_frequency = models.CharField(max_length=100, choices=FREQUENCY_CHOICES)
    how_discovered = models.CharField(max_length=100, choices=DISCOVERY_CHOICES)
    completed = models.BooleanField(default=False)
    complete_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Onboarding: {self.user}"

class EmailVerificationToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification_token')
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Token for {self.user.email}"