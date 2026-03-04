import threading
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from django_ratelimit.decorators import ratelimit


def send_order_email_in_background(subject, message, from_email, recipient_list):
    """Send email in a background thread so the request isn't blocked."""
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=False,
        )
    except Exception:
        pass  # Failure handled via messages in the view


@method_decorator(
    ratelimit(key='ip', rate='1/5m', method='POST', block=False),
    name='post'
)
class BuyPageView(View):
    template_name = 'buy/index.html'

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        # ── Rate limit check ──────────────────────────────────────────────
        was_limited = getattr(request, 'limited', False)
        if was_limited:
            messages.error(request, 'rate_limited')
            return redirect('buy:index')

        # ── Honeypot bot check ────────────────────────────────────────────
        # Hidden field in the form. Real users never fill it; bots usually do.
        if request.POST.get('honeypot'):
            # Silently fake success so bots don't know they were caught
            messages.success(request, 'order_sent')
            return redirect('buy:index')

        # ── Collect & sanitise form data ──────────────────────────────────
        full_name = request.POST.get('full_name', '').strip()
        phone     = request.POST.get('phone', '').strip()
        email     = request.POST.get('email', '').strip()
        address   = request.POST.get('address', '').strip()
        city      = request.POST.get('city', '').strip()
        quantity  = request.POST.get('quantity', '1').strip()
        notes     = request.POST.get('notes', '').strip()

        # Basic server-side validation for required fields
        if not all([full_name, phone, address, city, quantity]):
            messages.error(request, 'validation_error')
            return redirect('buy:index')

        # ── Build email body ──────────────────────────────────────────────
        subject = f"📦 New Book Order from {full_name}"
        email_body = f"""
New Book Order Request
======================

Full Name        : {full_name}
Phone            : {phone}
Email            : {email or 'Not provided'}
City / District  : {city}
Delivery Address : {address}
Quantity         : {quantity}
Additional Notes : {notes or 'N/A'}
"""

        # ── Send in background thread (non-blocking) ──────────────────────
        try:
            email_thread = threading.Thread(
                target=send_order_email_in_background,
                args=(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    ['acetheentrance@gmail.com', 'rockyrocks246810@gmail.com'],
                )
            )
            email_thread.daemon = True  # Won't block server shutdown
            email_thread.start()

            messages.success(request, 'order_sent')
        except Exception:
            messages.error(request, 'order_failed')

        return redirect('buy:index')