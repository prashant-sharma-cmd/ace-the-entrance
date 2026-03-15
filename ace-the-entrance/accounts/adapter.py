from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.account.adapter import DefaultAccountAdapter

from django.http import HttpResponseRedirect
from django.urls import  reverse


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

    def pre_social_login(self, request, sociallogin):
        """
        Fires before allauth processes the social login.
        If the user is already logged in, skip the whole flow and go to dashboard.
        """
        # Already logged in — just go to dashboard regardless
        if request.user.is_authenticated:
            raise ImmediateHttpResponse(
                HttpResponseRedirect(reverse('accounts:dashboard'))
            )

        # Not logged in but social account maps to an existing user by email —
        # connect and log them in rather than erroring
        if not sociallogin.is_existing:
            from .models import User
            try:
                email = sociallogin.user.email
                if email:
                    existing_user = User.objects.get(email=email)
                    sociallogin.connect(request, existing_user)
            except User.DoesNotExist:
                pass

    def on_authentication_error(self, request, provider, error=None,
                                exception=None, extra_context=None):
        """Route all social auth errors to our styled login page."""
        from django.contrib import messages
        messages.error(request,
                       "Sign in with Google failed. Please try again.")
        raise ImmediateHttpResponse(
            HttpResponseRedirect(reverse('accounts:login'))
        )

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Google has already verified the email — activate the account
        # immediately and skip the email verification flow entirely.
        user.is_active      = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])
        return user