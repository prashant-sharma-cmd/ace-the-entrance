from django.shortcuts import redirect
from django.urls import reverse

# FIX: exact paths only — startswith prefix matching could accidentally exempt
# unintended URLs (e.g. a future /accounts/socialdata/ would be exempt under
# the old /accounts/social/ prefix rule).
EXEMPT_URLS = {
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/logout/',
    '/accounts/email-sent/',
    '/accounts/resend-verification/',
}

# Kept as a prefix since verify links include a UUID segment
VERIFY_PREFIX = '/accounts/verify/'

# SSO callbacks use a dynamic prefix — kept as prefix match
SOCIAL_PREFIX = '/accounts/social/'


class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info

            # FIX: exact set lookup for known exempt paths
            is_exempt = (
                path in EXEMPT_URLS
                or path.startswith(VERIFY_PREFIX)
                or path.startswith(SOCIAL_PREFIX)
            )

            if not request.user.email_verified and not is_exempt:
                return redirect(reverse('accounts:email_sent'))

        return self.get_response(request)