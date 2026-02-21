# accounts/middleware.py
from django.shortcuts import redirect
from django.urls import reverse

EXEMPT_URLS = [
    '/accounts/login/',
    '/accounts/signup/',
    '/accounts/logout/',
    '/accounts/email-sent/',
    '/accounts/resend-verification/',
    '/accounts/social/',   # SSO callbacks must stay open
]

class EmailVerificationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            path = request.path_info
            is_exempt = any(path.startswith(url) for url in EXEMPT_URLS)
            is_verify_link = path.startswith('/accounts/verify/')

            if not request.user.email_verified and not is_exempt and not is_verify_link:
                return redirect(reverse('accounts:email_sent'))

        return self.get_response(request)