import logging
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


def send_smart_email(subject, recipient_list, template_name, context,
                     from_email=None):
    """
    A universal email utility.
    - subject: String
    - recipient_list: List of emails ['user@example.com']
    - template_name: Path to HTML template 'emails/welcome.html'
    - context: Dictionary for the template {'name': 'Prashant'}
    """
    try:
        # 1. Render HTML version
        html_message = render_to_string(template_name, context)

        # 2. Create plain text version for older email clients
        plain_message = strip_tags(html_message)

        # 3. Use the default from_email if none provided
        sender = from_email or settings.DEFAULT_FROM_EMAIL

        # 4. Send using Django's standard interface
        # (Anymail will automatically catch this and send via Resend API)
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=sender,
            recipient_list=recipient_list,
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Email failure to {recipient_list}: {str(e)}")
        # In development, you want to see the error
        if settings.DEBUG:
            raise e
        return False