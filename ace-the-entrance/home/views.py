import re
import logging
import threading

from django.shortcuts import redirect
from django.views.generic import View, TemplateView
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────────

MAX_LENGTHS = {
    'name':    100,
    'email':   254,
    'message': 2000,
}


# ── Helpers ────────────────────────────────────────────────────────────────────

def sanitise(value: str) -> str:
    """Strip newlines to prevent email header/body injection."""
    return value.replace('\n', ' ').replace('\r', ' ').strip()


def send_email_in_background(subject, message, sender, recipients):
    try:
        send_mail(
            subject,
            message,
            sender,
            recipients,
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Contact email failed: {e}", exc_info=True)


# ── Views ──────────────────────────────────────────────────────────────────────

class HomePageView(TemplateView):
    template_name = 'home/index.html'


@method_decorator(
    ratelimit(key='ip', rate='1/5m', method='POST', block=False),
    name='post'
)
class ContactUsView(View):
    template_name = 'home/index.html'

    def post(self, request):

        # 1. IP rate limit
        if getattr(request, 'limited', False):
            messages.error(request, 'You are sending multiple requests too quickly.!')
            return redirect('home:index')

        # 2. Honeypot
        if request.POST.get('honeypot'):
            messages.success(request, 'Email Sent Successfully.')   # fake success for bots
            return redirect('home:index')

        # 3. Collect and sanitise
        name    = sanitise(request.POST.get('name', ''))
        email   = sanitise(request.POST.get('email', ''))
        message = sanitise(request.POST.get('message', ''))

        # 4. Required field check
        if not all([name, email, message]):
            messages.error(request, 'Please make sure all the details are correct.')
            return redirect('home:index')

        # 5. Length limits
        field_values = {'name': name, 'email': email, 'message': message}
        for field, max_len in MAX_LENGTHS.items():
            if len(field_values[field]) > max_len:
                messages.error(request, 'Please make sure all the details are correct.')
                return redirect('home:index')

        # 6. Email format validation
        try:
            validate_email(email)
        except ValidationError:
            messages.error(request, 'Please make sure all the details are correct.')
            return redirect('home:index')

        # 7. Per-email rate limit (catches VPN/proxy IP bypass)
        email_key = f"contact_rate:{email.lower()}"
        if cache.get(email_key):
            messages.error(request, 'contact_rate_limited')
            return redirect('home:index')
        cache.set(email_key, 1, timeout=300)   # block same email for 5 minutes

        # 8. Build and send
        subject       = f"New Contact Form Message from {name}"
        email_message = f"Name    : {name}\nEmail   : {email}\n\nMessage :\n{message}"

        try:
            email_thread = threading.Thread(
                target=send_email_in_background,
                args=(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    ['acetheentrance@gmail.com'],
                )
            )
            email_thread.daemon = True
            email_thread.start()
            messages.success(request, 'contact_sent')
        except Exception as e:
            logger.error(f"Failed to start contact email thread: {e}", exc_info=True)
            messages.error(request, 'Failed to send the contact email.')

        return redirect('home:index')


# ── Simple redirects ───────────────────────────────────────────────────────────
# Hardcoded destinations only — never accept URL from request params

def redirect_to_facebook(request):
    return redirect('https://www.facebook.com/profile.php?id=61573984108480')

def redirect_to_instagram(request):
    return redirect('https://www.instagram.com/ace_the_entrance/')

def redirect_to_daraz(request):
    return redirect('https://www.daraz.pk/')

def redirect_to_whatsapp(request):
    return redirect('https://wa.me/85270396856')