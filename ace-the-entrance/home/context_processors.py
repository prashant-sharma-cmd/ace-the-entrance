from django.conf import settings

def project_settings(request):
    return {
        'PROJECT_NAME': getattr(settings, 'PROJECT_NAME', 'Default')
    }