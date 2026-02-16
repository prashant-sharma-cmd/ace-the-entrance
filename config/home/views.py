from django.shortcuts import redirect
from django.views.generic import View, TemplateView

from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit

import threading

def send_email_in_background(subject, message, sender, recipients):
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recipients,
        fail_silently=False,
    )


class HomePageView(TemplateView):
    template_name = 'home/index.html'

@method_decorator(ratelimit(key='ip', rate='1/5m', method='POST', block=False), name='post')
class ContactUsView(View):
    template_name = 'home/index.html'

    def post(self, request):
        was_limited = getattr(request, 'limited', False)

        if was_limited:
            messages.error(request, "You are sending emails too fast. Please wait 5 minutes.")
            return redirect('home:index')

        if request.POST.get('honeypot'):
            messages.success(request,
                             'Email sent successfully! We will get back to you soon.')
            return redirect('home:index')

        name = self.request.POST.get('name')
        sender_email = self.request.POST.get('email')
        message = self.request.POST.get('message')

        subject = f"New Contact Form Submission from {name}"
        email_message = f"Message:\n{message}\nFrom:{sender_email}"
        recipient_list = ['acetheentrance@gmail.com']

        try:
            email_thread = threading.Thread(
                target=send_email_in_background,
                args=(subject, email_message, settings.EMAIL_HOST_USER,
                      recipient_list)
            )
            email_thread.start()
            messages.success(request,
                             'Email sent successfully! We will get back to you soon.')
            return redirect('home:index')
        except Exception as e:
            messages.error(request, f'Something went wrong.')
            return redirect('home:index')

def redirect_to_facebook(request):
    return redirect('https://www.facebook.com/profile.php?id=61573984108480')

def redirect_to_instagram(request):
    return redirect('https://www.instagram.com/ace_the_entrance/')

def redirect_to_daraz(request):
    return redirect('https://www.daraz.pk/')

