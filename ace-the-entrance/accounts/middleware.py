from django.shortcuts import redirect
from django.urls import reverse
from allauth.socialaccount.models import SocialAccount

EXEMPT_URLS = {
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/logout/',
    '/accounts/email-sent/',
    '/accounts/resend-verification/',
    '/accounts/forgot-password/',
    '/accounts/forgot-password/sent/',
    '/accounts/reset/done/',
}

VERIFY_PREFIX  = '/accounts/verify/'
RESET_PREFIX   = '/accounts/reset/'
SOCIAL_PREFIX  = '/accounts/social/'


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info

            is_exempt = (
                path in EXEMPT_URLS
                or path.startswith(VERIFY_PREFIX)
                or path.startswith(RESET_PREFIX)
                or path.startswith(SOCIAL_PREFIX)
            )

            if not request.user.email_verified and not is_exempt:
                # Social auth users are always considered verified
                has_social = SocialAccount.objects.filter(
                    user=request.user
                ).exists()
                if not has_social:
                    return redirect(reverse('accounts:email_sent'))

        return self.get_response(request)