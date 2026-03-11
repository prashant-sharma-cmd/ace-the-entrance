import logging

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)


def send_verification_email(base_url, user):
    """
    Deletes any existing token, creates a fresh one, and emails the
    verification link.  Always called from a background thread.
    Accepts base_url (string) instead of request — request is not thread-safe.
    """
    from .models import EmailVerificationToken
    try:
        EmailVerificationToken.objects.filter(user=user).delete()
        token_obj = EmailVerificationToken.objects.create(user=user)

        verify_path = reverse('accounts:verify_email', args=[str(token_obj.token)])
        verify_url  = base_url + verify_path

        send_mail(
            subject="Verify your email address",
            message=f"""Hi {user.username},

Thanks for signing up! Please verify your email by clicking the link below:

{verify_url}

This link expires in 24 hours. If you didn't sign up, ignore this email.

— The Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}", exc_info=True)


def send_deletion_otp_email(user):
    """
    Generates a fresh 6-digit OTP and emails it to the user for account
    deletion confirmation.  Used for Google/SSO users who have no password.
    Always called from a background thread.
    """
    from .models import DeletionOTP
    try:
        DeletionOTP.objects.filter(user=user).delete()
        code = DeletionOTP.generate_code()
        DeletionOTP.objects.create(user=user, code=code)

        send_mail(
            subject="Your account deletion code",
            message=f"""Hi {user.username},

We received a request to permanently delete your account.

Your confirmation code is:

    {code}

This code expires in 10 minutes. If you didn't request this, you can safely ignore this email — your account will not be deleted.

— The Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send deletion OTP to {user.email}: {e}", exc_info=True)


def send_password_reset_email(base_url, user):
    """
    Deletes any existing reset token, creates a fresh one, and emails the
    reset link.  Always called from a background thread.
    Accepts base_url (string) instead of request — request is not thread-safe.
    """
    from .models import PasswordResetToken
    try:
        PasswordResetToken.objects.filter(user=user).delete()
        token_obj = PasswordResetToken.objects.create(user=user)

        reset_path = reverse('accounts:password_reset_confirm', args=[str(token_obj.token)])
        reset_url  = base_url + reset_path

        send_mail(
            subject="Reset your password",
            message=f"""Hi {user.username},

We received a request to reset the password for your account.

Click the link below to choose a new password:

{reset_url}

This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email — your password will not change.

— The Team""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}", exc_info=True)