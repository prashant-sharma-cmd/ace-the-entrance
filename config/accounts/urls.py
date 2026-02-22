# accounts/urls.py
from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('email-sent/', views.EmailSentView.as_view(), name='email_sent'),
    path('verify/<uuid:token>/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationView.as_view(), name='resend_verification'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),

    # SSO via allauth
    path('social/', include('allauth.urls')),
]