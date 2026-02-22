from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView, FormView, RedirectView

from .forms import SignUpForm, OnboardingForm
from .models import User, EmailVerificationToken, UserOnboarding
from .email_utils import send_verification_email
from .mixins import GuestOnlyMixin, VerifiedEmailRequiredMixin, OnboardingCompletedMixin

# ── Signup ────────────────────────────────────────────────────────────────────
class SignUpView(GuestOnlyMixin, FormView):
    template_name = 'accounts/signup.html'
    form_class = SignUpForm

    def dispatch(self, request, *args, **kwargs):
        # Redirect already logged-in users
        if request.user.is_authenticated:
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        send_verification_email(self.request, user)
        messages.success(self.request, "Account created! Check your email to "
                                       "verify your account.")
        return redirect('accounts:email_sent')

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))


# ── Email Sent Confirmation Page ──────────────────────────────────────────────
class EmailSentView(TemplateView):
    template_name = 'accounts/email_sent.html'


# ── Verify Email via Token Link ───────────────────────────────────────────────
class VerifyEmailView(View):

    def get(self, request, token):
        token_obj = get_object_or_404(EmailVerificationToken, token=token, is_used=False)

        if token_obj.is_expired():
            messages.error(request, "This verification link has expired. Please request a new one.")
            return redirect('accounts:resend_verification')

        user = token_obj.user
        user.email_verified = True
        user.save()

        token_obj.is_used = True
        token_obj.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Email verified! Let's finish setting up your account.")
        return redirect('accounts:onboarding')


# ── Resend Verification Email ─────────────────────────────────────────────────
class ResendVerificationView(View):
    template_name = 'accounts/resend_verification.html'

    def get(self, request):
        return self.render(request)

    def post(self, request):
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email, email_verified=False)
            send_verification_email(request, user)
        except User.DoesNotExist:
            pass  # Don't reveal whether the email exists

        # Always show the same message for security
        messages.success(request, "If that email exists and is unverified, we've sent a new link.")
        return redirect('accounts:email_sent')

    def render(self, request):
        from django.shortcuts import render
        return render(request, self.template_name)


# ── Login ─────────────────────────────────────────────────────────────────────
class LoginView(GuestOnlyMixin, View):
    template_name = 'accounts/login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return self.render(request)

    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)

        if not user:
            return self.render(request, error="Invalid email or password.")

        if not user.email_verified:
            send_verification_email(request, user)
            return self.render(
                request,
                error="Please verify your email first. We've resent the verification link."
            )

        login(request, user)

        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return redirect('accounts:onboarding')

        return redirect('accounts:dashboard')

    def render(self, request, error=None):
        from django.shortcuts import render
        return render(request, self.template_name, {'error': error})


# ── Onboarding ────────────────────────────────────────────────────────────────
class OnboardingView(VerifiedEmailRequiredMixin, FormView):
    template_name = 'accounts/onboarding.html'
    form_class = OnboardingForm
    login_url = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            onboarding = UserOnboarding.objects.filter(user=request.user).first()
            if onboarding and onboarding.completed:
                return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Bind form to existing onboarding instance if it exists
        onboarding, _ = UserOnboarding.objects.get_or_create(user=self.request.user)
        kwargs['instance'] = onboarding
        return kwargs

    def form_valid(self, form):
        onboarding = form.save(commit=False)
        onboarding.completed = True
        onboarding.completed_at = timezone.now()
        onboarding.save()
        messages.success(self.request, "Welcome! Your profile is all set.")
        return redirect('accounts:dashboard')


# ── Logout ────────────────────────────────────────────────────────────────────
class LogoutView(RedirectView):
    url = '/accounts/login/'

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "You've been logged out.")
        return super().get(request, *args, **kwargs)


# ── Dashboard ─────────────────────────────────────────────────────────────────
class DashboardView(OnboardingCompletedMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    login_url = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.request.user
        context['onboarding'] = getattr(self.request.user, 'onboarding', None)
        return context