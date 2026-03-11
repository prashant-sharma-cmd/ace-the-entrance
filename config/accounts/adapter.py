from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Controls redirect after normal email/password login."""

    def get_login_redirect_url(self, request):
        user = request.user
        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return '/accounts/onboarding/'
        return '/accounts/dashboard/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Controls redirect after Google etc. OAuth login."""

    def get_connect_redirect_url(self, request, socialaccount):
        return '/accounts/dashboard/'

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Google has already verified the email — activate the account
        # immediately and skip the email verification flow entirely.
        user.is_active      = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])
        return user