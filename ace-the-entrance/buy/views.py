import re
import logging
import threading

from django.shortcuts import render, redirect
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django_ratelimit.decorators import ratelimit
from django.core.cache import cache

from utils.email_service import send_smart_email

logger = logging.getLogger(__name__)

# ── Field length caps ──────────────────────────────────────────────────────────

MAX_LENGTHS = {
    'full_name': 100,
    'phone':      20,
    'email':     254,
    'address':   300,
    'city':      100,
    'notes':     500,
}

VALID_QUANTITIES = {'1', '2', '3', '4', '5'}


# ── Helpers ────────────────────────────────────────────────────────────────────

def sanitise(value: str) -> str:
    """Strip newlines to prevent email body injection."""
    if not value: return ""
    return value.replace('\n', ' ').replace('\r', ' ').strip()


def send_order_email_in_background(subject, context, recipient_list, reply_to_email):
    """Send email in a background thread so the request is not blocked."""
    try:
        send_smart_email(
            subject=subject,
            recipient_list=recipient_list,
            template_name="emails/order_notification.html",
            context=context,
            reply_to=reply_to_email
        )
    except Exception as e:
        logger.error(f"Order email failed: {e}", exc_info=True)


# ── View ───────────────────────────────────────────────────────────────────────

@method_decorator(
    ratelimit(key='ip', rate='1/5m', method='POST', block=False),
    name='post'
)
class BuyPageView(View):
    template_name = 'buy/index.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):

        # 1. IP rate limit
        if getattr(request, 'limited', False):
            messages.error(request, 'Please wait 5 minutes before placing another order!')
            return redirect('buy:index')

        # 2. Honeypot — bots fill hidden fields, real users never do
        if request.POST.get('honeypot'):
            messages.success(request, 'Order Sent Successfully!')   # fake success so bots think it worked
            return redirect('buy:index')

        # 3. Collect and sanitise (strips newlines — prevents email body injection)
        full_name = sanitise(request.POST.get('full_name', ''))
        phone     = sanitise(request.POST.get('phone', ''))
        email     = sanitise(request.POST.get('email', ''))
        address   = sanitise(request.POST.get('address', ''))
        city      = sanitise(request.POST.get('city', ''))
        quantity  = sanitise(request.POST.get('quantity', ''))
        notes     = sanitise(request.POST.get('notes', ''))

        # 4. Required fields
        if not all([full_name, phone, address, city, quantity]):
            messages.error(request, 'Please enter correct details!')
            return redirect('buy:index')

        # 5. Length limits — prevents memory/log exhaustion
        field_values = {
            'full_name': full_name,
            'phone':     phone,
            'email':     email,
            'address':   address,
            'city':      city,
            'notes':     notes,
        }
        for field, max_len in MAX_LENGTHS.items():
            if len(field_values[field]) > max_len:
                messages.error(request, 'Please enter correct details!')
                return redirect('buy:index')

        # 6. Phone format — Nepal numbers: 96XXXXXXXX to 99XXXXXXXX
        if not re.fullmatch(r'9[6-9]\d{8}', phone):
            messages.error(request, 'Please enter correct details!')
            return redirect('buy:index')

        # 7. Email format (optional field)
        if email:
            try:
                validate_email(email)
            except ValidationError:
                messages.error(request, 'Please enter correct details!')
                return redirect('buy:index')

        # 8. Quantity whitelist — prevents POST tampering (e.g. quantity=9999)
        if quantity not in VALID_QUANTITIES:
            messages.error(request, 'Please enter correct details')
            return redirect('buy:index')

        # 9. Per-phone rate limit — catches VPN/proxy IP bypass
        phone_key = f"order_rate:{phone}"
        if cache.get(phone_key):
            messages.error(request, 'Please wait 5 minutes before placing another order!')
            return redirect('buy:index')
        cache.set(phone_key, 1, timeout=300)   # block same phone for 5 minutes

        # 10. Build and send email
        subject = f"📚 New Order: {full_name} ({quantity} qty)"

        # We pass a dictionary (context) instead of a formatted string
        email_context = {
            'full_name': full_name,
            'phone': phone,
            'email': email,
            'address': address,
            'city': city,
            'quantity': quantity,
            'notes': notes,
        }

        try:
            # We use the customer's email as 'reply_to' so you can just click
            # 'Reply' in your Gmail to contact them.
            customer_email = email if email else None

            email_thread = threading.Thread(
                target=send_order_email_in_background,
                args=(
                    subject,
                    email_context,
                    ['acetheentrance@gmail.com', 'rockyrocks246810@gmail.com'],
                    customer_email,  # This is the reply_to
                )
            )
            email_thread.daemon = True
            email_thread.start()
            messages.success(request, 'Order Sent Successfully!')
        except Exception as e:
            logger.error(f"Failed to start email thread: {e}", exc_info=True)
            messages.error(request,
                           'Failed to place order! Please contact us via phone.')

        return redirect('buy:index')