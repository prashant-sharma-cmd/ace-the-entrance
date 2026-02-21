from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from .models import EmailVerificationToken


def send_verification_email(request, user):
    # Delete any old token and create a fresh one
    EmailVerificationToken.objects.filter(user=user).delete()
    token_obj = EmailVerificationToken.objects.create(user=user)

    verify_url = request.build_absolute_uri(
        reverse('verify_email', args=[str(token_obj.token)])
    )

    subject = "Verify your email address"
    message = f"""
Hi {user.username},

Thanks for signing up! Please verify your email by clicking the link below:

{verify_url}

This link expires in 24 hours. If you didn't sign up, ignore this email.

— The Team
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )