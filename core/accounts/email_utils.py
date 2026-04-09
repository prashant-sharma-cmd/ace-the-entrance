import logging

from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from utils.email_service import send_smart_email

logger = logging.getLogger(__name__)


def send_verification_email(base_url, user):
    """
    Deletes any existing token, creates a fresh one, and emails the
    verification link. Always called from a background thread.
    """
    from .models import EmailVerificationToken
    try:
        EmailVerificationToken.objects.filter(user=user).delete()
        token_obj = EmailVerificationToken.objects.create(user=user)

        verify_path = reverse('accounts:verify_email',
                              args=[str(token_obj.token)])
        verify_url = base_url + verify_path

        send_smart_email(
            subject="Verify your email address",
            recipient_list=[user.email],
            template_name="emails/verify_email.html",
            context={
                "username": user.username,
                "verify_url": verify_url,
            }
        )
        logger.info(f"Verification email sent to {user.email}")

    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}",
                     exc_info=True)


def send_deletion_otp_email(user):
    """
    Generates a fresh 6-digit OTP and emails it for account deletion.
    """
    from .models import DeletionOTP
    try:
        # 1. OTP Logic
        DeletionOTP.objects.filter(user=user).delete()
        code = DeletionOTP.generate_code()
        DeletionOTP.objects.create(user=user, code=code)

        # 2. Send via Smart Utility
        send_smart_email(
            subject="Your account deletion code",
            recipient_list=[user.email],
            template_name="emails/deletion_otp.html",
            context={
                "username": user.username,
                "code": code,
            }
        )
    except Exception as e:
        logger.error(f"Failed to send deletion OTP to {user.email}: {e}", exc_info=True)


def send_password_reset_email(base_url, user):
    """
    Deletes any existing reset token and emails the reset link.
    """
    from .models import PasswordResetToken
    try:
        # 1. Token Logic
        PasswordResetToken.objects.filter(user=user).delete()
        token_obj = PasswordResetToken.objects.create(user=user)

        # 2. URL Generation
        reset_path = reverse('accounts:password_reset_confirm', args=[str(token_obj.token)])
        reset_url = base_url + reset_path

        # 3. Send via Smart Utility
        send_smart_email(
            subject="Reset your password",
            recipient_list=[user.email],
            template_name="emails/password_reset.html",
            context={
                "username": user.username,
                "reset_url": reset_url,
            }
        )
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {e}", exc_info=True)