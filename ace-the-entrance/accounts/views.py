import logging
import threading

from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView, FormView
from django_ratelimit.decorators import ratelimit

from .forms import SignUpForm, OnboardingForm
from .models import User, EmailVerificationToken, UserOnboarding, DeletionOTP
from .email_utils import send_verification_email, send_deletion_otp_email, send_password_reset_email
from .mixins import GuestOnlyMixin, VerifiedEmailRequiredMixin, OnboardingCompletedMixin

logger = logging.getLogger(__name__)


# ── Async helpers ─────────────────────────────────────────────────────────────

def _run_async(fn, *args):
    """Run fn(*args) in a daemon thread so the HTTP response isn't blocked.
    Never pass the request object — it's not thread-safe after response is sent.
    Extract what you need (e.g. build_absolute_uri) before calling this.
    """
    t = threading.Thread(target=fn, args=args)
    t.daemon = True
    t.start()


# ── Signup ────────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='5/10m', method='POST', block=False),
    name='post'
)
class SignUpView(GuestOnlyMixin, FormView):
    template_name = 'accounts/signup.html'
    form_class    = SignUpForm

    def post(self, request, *args, **kwargs):
        if getattr(request, 'limited', False):
            messages.error(request, "Too many sign-up attempts. Please wait 10 minutes.")
            return redirect('accounts:signup')
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        # Extract base URL before spawning thread — request is not thread-safe
        base_url = self.request.build_absolute_uri('/')[:-1]
        _run_async(send_verification_email, base_url, user)
        messages.success(
            self.request,
            "Almost there! Check your email and click the verification link to activate your account."
        )
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

        # Activate the account and mark email as verified in one save
        user.is_active     = True
        user.email_verified = True
        user.save(update_fields=['is_active', 'email_verified'])

        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])

        # Log the user in immediately after verification
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
        if getattr(request, 'limited', False):
            messages.error(request, "Too many requests. Please wait 10 minutes before trying again.")
            return redirect('accounts:resend_verification')

        if request.POST.get('honeypot'):
            messages.success(request, "If that email exists and is unverified, we've sent a new link.")
            return redirect('accounts:email_sent')

        email = request.POST.get('email', '').strip()

        try:
            user = User.objects.get(email=email, is_active=False, email_verified=False)
            base_url = request.build_absolute_uri('/')[:-1]
            _run_async(send_verification_email, base_url, user)
        except User.DoesNotExist:
            pass  # Always show the same response — prevents email enumeration

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
        if getattr(request, 'limited', False):
            return render(request, self.template_name, {
                'error': "Too many login attempts. Please wait 5 minutes."
            })

        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # authenticate() returns None for inactive (unverified) users
        user = authenticate(request, username=email, password=password)

        if not user:
            # Check for unverified account — but only AFTER authenticate() has
            # already done its constant-time work, so we don't add a timing gap.
            # Use filter+first (no exception path) to keep timing uniform.
            unverified = User.objects.filter(
                email=email, is_active=False, email_verified=False
            ).first()
            if unverified:
                base_url = request.build_absolute_uri('/')[:-1]
                _run_async(send_verification_email, base_url, unverified)
                return render(request, self.template_name, {
                    'error': "Your email isn't verified yet. We've resent the verification link."
                })

            return render(request, self.template_name, {
                'error': "Invalid email or password."
            })

        login(request, user)

        # remember_me: persist session for 30 days, otherwise expire on close
        if request.POST.get('remember_me'):
            request.session.set_expiry(60 * 60 * 24 * 30)
        else:
            request.session.set_expiry(0)

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
        onboarding               = form.save(commit=False)
        onboarding.completed     = True
        onboarding.complete_date = timezone.now()
        onboarding.save()
        messages.success(self.request, "Welcome! Your profile is all set.")
        return redirect('accounts:dashboard')


# ── Logout ────────────────────────────────────────────────────────────────────

class LogoutView(LoginRequiredMixin, View):
    """POST-only to prevent CSRF logout attacks via <img src='/logout/'>."""
    login_url = '/accounts/login/'

    def post(self, request):
        logout(request)
        messages.info(request, "You've been logged out.")
        return redirect('/accounts/login/')

    def get(self, request):
        # Show a confirmation page for direct GET visits
        return render(request, 'accounts/logout_confirm.html')


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardView(OnboardingCompletedMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    login_url     = '/accounts/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user']       = self.request.user
        context['onboarding'] = getattr(self.request.user, 'onboarding', None)
        # Tell the template whether this user has a usable password
        context['has_password'] = self.request.user.has_usable_password()
        # Tell the template if the user just requested a deletion OTP
        context['otp_requested'] = DeletionOTP.objects.filter(
            user=self.request.user, is_used=False
        ).exists()
        return context


# ── Account Deletion ──────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='3/10m', method='POST', block=False),
    name='dispatch'
)
class DeleteAccountView(LoginRequiredMixin, View):
    """
    Two flows:
      - Password users:  confirm with their password (POST confirm_password)
      - SSO/Google users: confirm with a 6-digit OTP sent to their email
    The template shows the correct form based on has_usable_password().
    """
    login_url = '/accounts/login/'

    def post(self, request):
        if getattr(request, 'limited', False):
            messages.error(request, "Too many attempts. Please wait 10 minutes.")
            return redirect('accounts:dashboard')

        user = request.user

        if user.has_usable_password():
            # ── Password flow ──────────────────────────────────────────────
            password = request.POST.get('confirm_password', '')
            if not password or not user.check_password(password):
                messages.error(request, "Incorrect password. Account not deleted.")
                return redirect('accounts:dashboard')
        else:
            # ── OTP flow ───────────────────────────────────────────────────
            submitted_code = request.POST.get('otp_code', '').strip()
            try:
                otp = DeletionOTP.objects.get(user=user, is_used=False)
            except DeletionOTP.DoesNotExist:
                messages.error(request, "No OTP found. Please request a new one.")
                return redirect('accounts:dashboard')

            if otp.is_expired():
                otp.delete()
                messages.error(request, "Your OTP has expired. Please request a new one.")
                return redirect('accounts:dashboard')

            if otp.is_locked():
                otp.delete()
                messages.error(request, "Too many incorrect attempts. Please request a new code.")
                return redirect('accounts:dashboard')

            if otp.code != submitted_code:
                otp.attempt_count += 1
                otp.save(update_fields=['attempt_count'])
                remaining = otp.MAX_ATTEMPTS - otp.attempt_count
                messages.error(request, f"Incorrect code. {remaining} attempt(s) remaining.")
                return redirect('accounts:dashboard')

            otp.is_used = True
            otp.save(update_fields=['is_used'])

        logout(request)
        user.delete()
        messages.success(request, "Your account has been permanently deleted.")
        return redirect('home:index')


@method_decorator(
    ratelimit(key='ip', rate='3/10m', method='POST', block=False),
    name='dispatch'
)
class RequestDeletionOTPView(LoginRequiredMixin, View):
    """
    Sends a deletion OTP to the logged-in user's email.
    Only meaningful for SSO users — password users never see this button.
    Supports both normal POST (redirect) and AJAX fetch (JSON 200).
    """
    login_url = '/accounts/login/'

    def post(self, request):
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if getattr(request, 'limited', False):
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse(
                    {'error': 'Too many requests. Please wait 10 minutes.'},
                    status=429)
            messages.error(request,
                           "Too many requests. Please wait 10 minutes.")
            return redirect('accounts:dashboard')

        if request.user.has_usable_password():
            if is_ajax:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Not allowed.'}, status=400)
            return redirect('accounts:dashboard')

        _run_async(send_deletion_otp_email, request.user)

        if is_ajax:
            from django.http import JsonResponse
            return JsonResponse({'ok': True})

        messages.success(request,
                         "A 6-digit code has been sent to your email. It expires in 10 minutes.")
        return redirect('accounts:dashboard')

# ── Forgot Password ───────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='5/10m', method='POST', block=False),
    name='dispatch'
)
class ForgotPasswordView(View):
    """
    Step 1 — user enters their email.
    Always shows the same success message to prevent email enumeration.
    """
    template_name = 'accounts/forgot_password.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, self.template_name)

    def post(self, request):
        if getattr(request, 'limited', False):
            messages.error(request, "Too many requests. Please wait 10 minutes.")
            return redirect('accounts:forgot_password')

        # Honeypot check
        if request.POST.get('honeypot'):
            return redirect('accounts:password_reset_sent')

        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email, is_active=True)
            if user.has_usable_password():
                base_url = request.build_absolute_uri('/')[:-1]
                _run_async(send_password_reset_email, base_url, user)
        except User.DoesNotExist:
            pass  # Same response regardless — no email enumeration

        return redirect('accounts:password_reset_sent')


class PasswordResetSentView(TemplateView):
    """Step 2 — confirmation page after submitting the email."""
    template_name = 'accounts/password_reset_sent.html'


@method_decorator(
    ratelimit(key='ip', rate='5/10m', method='POST', block=False),
    name='dispatch'
)
class PasswordResetConfirmView(View):
    """
    Step 3 — user clicks the link from their email and sets a new password.
    """
    template_name = 'accounts/password_reset_confirm.html'

    def _get_valid_token(self, token):
        """Return token object or None if invalid/expired/used."""
        from .models import PasswordResetToken
        try:
            obj = PasswordResetToken.objects.get(token=token, is_used=False)
            if obj.is_expired():
                obj.delete()
                return None
            return obj
        except PasswordResetToken.DoesNotExist:
            return None

    def get(self, request, token):
        token_obj = self._get_valid_token(token)
        if not token_obj:
            messages.error(request, "This reset link is invalid or has expired.")
            return redirect('accounts:forgot_password')
        return render(request, self.template_name, {'token': token})

    def post(self, request, token):
        if getattr(request, 'limited', False):
            messages.error(request, "Too many attempts. Please request a new reset link.")
            return redirect('accounts:forgot_password')

        token_obj = self._get_valid_token(token)
        if not token_obj:
            messages.error(request, "This reset link is invalid or has expired.")
            return redirect('accounts:forgot_password')

        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        if not password1:
            return render(request, self.template_name, {
                'token': token,
                'error': "Please enter a new password."
            })
        if len(password1) < 8:
            return render(request, self.template_name, {
                'token': token,
                'error': "Password must be at least 8 characters."
            })
        if password1 != password2:
            return render(request, self.template_name, {
                'token': token,
                'error': "Passwords do not match."
            })

        user = token_obj.user
        user.set_password(password1)
        user.save(update_fields=['password'])

        # Invalidate the token
        token_obj.is_used = True
        token_obj.save(update_fields=['is_used'])

        # Log the user in and rotate the session hash so any stolen
        # pre-reset sessions are immediately invalidated (#5)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        return redirect('accounts:password_reset_done')


class PasswordResetDoneView(TemplateView):
    """Step 4 — success page shown after password is changed."""
    template_name = 'accounts/password_reset_done.html'