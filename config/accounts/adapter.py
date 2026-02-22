# accounts/adapter.py
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """Controls redirect after normal email/password login."""

    def get_login_redirect_url(self, request):
        user = request.user
        # If onboarding not done, send them there first
        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return '/accounts/onboarding/'
        return '/accounts/dashboard/'


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """Controls redirect after Google, Facebook, GitHub etc. login."""

    def get_connect_redirect_url(self, request, socialaccount):
        return '/accounts/dashboard/'

    def save_user(self, request, sociallogin, form=None):
        """
        Called when a NEW social account user is created.
        We can pre-populate fields from the social provider data here.
        """
        user = super().save_user(request, sociallogin, form)

        # Google/Facebook give us the email already verified
        # so we mark email_verified = True for SSO users
        user.email_verified = True
        user.save()
        return user