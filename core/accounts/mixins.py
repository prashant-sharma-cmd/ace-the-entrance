from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class GuestOnlyMixin:
    """Redirects authenticated users away from guest-only pages like login/signup."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class VerifiedEmailRequiredMixin(LoginRequiredMixin):
    """Ensures user is logged in AND has verified their email.
    Social auth users are considered verified by virtue of their provider.
    """

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        user = request.user
        # Social auth users are email-verified by their provider
        has_social = SocialAccount.objects.filter(user=user).exists()

        if not user.email_verified and not has_social:
            return redirect('accounts:email_sent')

        # Lazily heal the flag so future checks are fast (DB hit only once)
        if not user.email_verified and has_social:
            user.email_verified = True
            user.is_active = True
            user.save(update_fields=['email_verified', 'is_active'])

        return super(LoginRequiredMixin, self).dispatch(request, *args,
                                                        **kwargs)


class OnboardingCompletedMixin(VerifiedEmailRequiredMixin):
    """Ensures user has completed onboarding before accessing protected pages."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        # Only check onboarding if super() didn't redirect
        if hasattr(result, 'status_code') and result.status_code in (301, 302):
            return result
        user = request.user
        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return redirect('accounts:onboarding')
        return result