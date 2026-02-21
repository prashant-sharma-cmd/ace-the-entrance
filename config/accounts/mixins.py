# accounts/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect


class GuestOnlyMixin:
    """Redirects authenticated users away from guest-only pages like login/signup."""
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class VerifiedEmailRequiredMixin(LoginRequiredMixin):
    """Ensures user is logged in AND has verified their email."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        if not request.user.email_verified:
            return redirect('accounts:email_sent')
        return super().dispatch(request, *args, **kwargs)


class OnboardingCompletedMixin(VerifiedEmailRequiredMixin):
    """Ensures user has completed onboarding before accessing protected pages."""
    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        # Only check onboarding if super() didn't redirect
        if hasattr(result, 'status_code') and result.status_code in (301, 302):
            return result
        user = request.user
        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return redirect('accounts: onboarding')
        return result