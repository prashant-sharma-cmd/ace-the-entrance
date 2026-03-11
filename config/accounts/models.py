import uuid
import random

from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    email          = models.EmailField(unique=True)
    email_verified = models.BooleanField(default=False)
    phone_number   = PhoneNumberField(blank=True, null=True, unique=True)
    first_name     = models.CharField(max_length=30, blank=True)
    last_name      = models.CharField(max_length=30, blank=True)

    # Account is inactive until email is verified.
    # authenticate() returns None for inactive users so unverified users
    # simply cannot log in — no extra guard needed in LoginView.
    # We keep email_verified separately to distinguish "not yet verified"
    # from "disabled by admin".
    is_active = models.BooleanField(default=False)

    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return self.email


class UserOnboarding(models.Model):
    PURPOSE_CHOICES = [
        ('daily_quiz',    'Daily Questions'),
        ('discussion',    'Engaging in Discussion'),
        ('sxc_model_set', 'Checking Model Set'),
        ('book_info',     'Learn More About Book'),
        ('all',           'Everything'),
        ('other',         'Other'),
    ]

    FREQUENCY_CHOICES = [
        ('daily',   'Daily'),
        ('weekly',  'Weekly'),
        ('monthly', 'Monthly'),
        ('rarely',  'Rarely'),
    ]

    DISCOVERY_CHOICES = [
        ('official',  'Official Book'),
        ('google',    'Google Search'),
        ('facebook',  'Facebook'),
        ('instagram', 'Instagram'),
        ('friend',    'Friend / Teacher'),
        ('other',     'Other'),
    ]

    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding')
    primary_purpose   = models.CharField(max_length=100, choices=PURPOSE_CHOICES)
    visit_frequency   = models.CharField(max_length=100, choices=FREQUENCY_CHOICES)
    how_discovered    = models.CharField(max_length=100, choices=DISCOVERY_CHOICES)
    newsletter_opt_in = models.BooleanField(default=False)
    completed         = models.BooleanField(default=False)
    complete_date     = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Onboarding: {self.user}"


class EmailVerificationToken(models.Model):
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='email_verification_token')
    token      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=24)

    def __str__(self):
        return f"Token for {self.user.email}"


class DeletionOTP(models.Model):
    """
    6-digit OTP for confirming account deletion for Google/SSO users who
    have no password.  Expires after 10 minutes, single-use.
    """
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='deletion_otp')
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    @staticmethod
    def generate_code():
        return f"{random.randint(0, 999999):06d}"

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"DeletionOTP for {self.user.email}"


class PasswordResetToken(models.Model):
    """
    Secure single-use token for password reset links.
    Expires after 1 hour, invalidated on use.
    """
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name='password_reset_token')
    token      = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def is_expired(self):
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() > self.created_at + timedelta(hours=1)

    def __str__(self):
        return f"PasswordResetToken for {self.user.email}"