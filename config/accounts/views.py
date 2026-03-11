import logging
import threading

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, FormView, RedirectView
from django_ratelimit.decorators import ratelimit

from .forms import SignUpForm, OnboardingForm
from .models import User, EmailVerificationToken, UserOnboarding
from .email_utils import send_verification_email
from .mixins import GuestOnlyMixin, VerifiedEmailRequiredMixin, OnboardingCompletedMixin

logger = logging.getLogger(__name__)


def _send_verification_async(request, user):
    """Fire-and-forget wrapper so signup/resend don't block on SMTP."""
    thread = threading.Thread(target=send_verification_email, args=(request, user))
    thread.daemon = True
    thread.start()


# ── Signup ────────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='5/10m', method='POST', block=False),
    name='post'
)
class SignUpView(GuestOnlyMixin, FormView):
    template_name = 'accounts/signup.html'
    form_class = SignUpForm

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            messages.error(request, "Too many sign-up attempts. Please wait 10 minutes.")
            return redirect('accounts:signup')
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        _send_verification_async(self.request, user)
        messages.success(self.request, "Account created! Check your email to verify your account.")
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

        # FIX: check account is still active before logging in
        if not user.is_active:
            messages.error(request, "This account has been disabled.")
            return redirect('accounts:login')

        user.email_verified = True
        user.save()

        token_obj.is_used = True
        token_obj.save()

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, "Email verified! Let's finish setting up your account.")
        return redirect('accounts:onboarding')


# ── Resend Verification Email ─────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='3/10m', method='POST', block=False),
    name='dispatch'
)
class ResendVerificationView(View):
    template_name = 'accounts/resend_verification.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # FIX: rate limit to prevent email bombing
        if getattr(request, 'limited', False):
            messages.error(request, "Too many requests. Please wait 10 minutes before trying again.")
            return redirect('accounts:resend_verification')

        # FIX: honeypot check
        if request.POST.get('honeypot'):
            messages.success(request, "If that email exists and is unverified, we've sent a new link.")
            return redirect('accounts:email_sent')

        email = request.POST.get('email', '').strip()

        try:
            user = User.objects.get(email=email, email_verified=False)
            _send_verification_async(request, user)
        except User.DoesNotExist:
            pass  # Don't reveal whether the email exists

        # Always show the same message — prevents email enumeration
        messages.success(request, "If that email exists and is unverified, we've sent a new link.")
        return redirect('accounts:email_sent')


# ── Login ─────────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='5/5m', method='POST', block=False),
    name='dispatch'
)
class LoginView(GuestOnlyMixin, View):
    template_name = 'accounts/login.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # FIX: rate limit brute force attempts
        if getattr(request, 'limited', False):
            return render(request, self.template_name, {
                'error': "Too many login attempts. Please wait 5 minutes."
            })

        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        user     = authenticate(request, username=email, password=password)

        if not user:
            return render(request, self.template_name, {
                'error': "Invalid email or password."
            })

        if not user.is_active:
            return render(request, self.template_name, {
                'error': "This account has been disabled."
            })

        if not user.email_verified:
            _send_verification_async(request, user)
            return render(request, self.template_name, {
                'error': "Please verify your email first. We've resent the verification link."
            })

        login(request, user)

        # FIX: implement remember_me properly
        remember = request.POST.get('remember_me')
        if remember:
            request.session.set_expiry(60 * 60 * 24 * 30)   # 30 days
        else:
            request.session.set_expiry(0)                    # expires on browser close

        if not hasattr(user, 'onboarding') or not user.onboarding.completed:
            return redirect('accounts:onboarding')

        return redirect('accounts:dashboard')


# ── Onboarding ────────────────────────────────────────────────────────────────

class OnboardingView(VerifiedEmailRequiredMixin, FormView):
    template_name = 'accounts/onboarding.html'
    form_class    = OnboardingForm
    login_url     = '/accounts/login/'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            onboarding = UserOnboarding.objects.filter(user=request.user).first()
            if onboarding and onboarding.completed:
                return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        onboarding, _ = UserOnboarding.objects.get_or_create(user=self.request.user)
        kwargs['instance'] = onboarding
        return kwargs

    def form_valid(self, form):
        onboarding = form.save(commit=False)
        onboarding.completed    = True
        # FIX: use the correct field name from the model
        onboarding.complete_date = timezone.now()
        onboarding.save()
        messages.success(self.request, "Welcome! Your profile is all set.")
        return redirect('accounts:dashboard')


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(LoginRequiredMixin, View):
    """
    FIX: logout is now POST-only to prevent CSRF logout attacks
    (e.g. a malicious page with <img src='/accounts/logout/'> logging users out).
    Update your logout links/buttons to use a small POST form instead of <a href>.
    """
    login_url = '/accounts/login/'

    def post(self, request):
        logout(request)
        messages.info(request, "You've been logged out.")
        return redirect('/accounts/login/')

    def get(self, request):
        # Graceful fallback: show a confirmation page rather than silently failing
        return render(request, 'accounts/logout_confirm.html')


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardView(OnboardingCompletedMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    login_url     = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user']       = self.request.user
        context['onboarding'] = getattr(self.request.user, 'onboarding', None)
        return context


# ── Account Deletion ──────────────────────────────────────────────────────────

class DeleteAccountView(LoginRequiredMixin, View):
    login_url = '/accounts/login/'

    def post(self, request):
        # FIX: require password confirmation server-side — JS confirm() is client-side only
        password = request.POST.get('confirm_password', '')
        if not password or not request.user.check_password(password):
            messages.error(request, "Incorrect password. Account not deleted.")
            return redirect('accounts:dashboard')

        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect('home:index')