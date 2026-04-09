from allauth.socialaccount.signals import social_account_added, pre_social_login
from allauth.socialaccount.models import SocialLogin
from django.dispatch import receiver

@receiver(pre_social_login)
def mark_email_verified_on_social_login(sender, request, sociallogin, **kwargs):
    """
    When a user logs in via social auth, mark their email as verified
    and activate the account if it wasn't already.
    """
    user = sociallogin.user
    if user.pk:  # existing user
        if not user.email_verified:
            user.email_verified = True
            user.is_active = True
            user.save(update_fields=['email_verified', 'is_active'])