from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    path('signup/',                          views.SignUpView.as_view(),               name='signup'),
    path('login/',                           views.LoginView.as_view(),                name='login'),
    path('logout/',                          views.LogoutView.as_view(),               name='logout'),
    path('email-sent/',                      views.EmailSentView.as_view(),            name='email_sent'),
    path('verify/<uuid:token>/',             views.VerifyEmailView.as_view(),          name='verify_email'),
    path('resend-verification/',             views.ResendVerificationView.as_view(),   name='resend_verification'),
    path('onboarding/',                      views.OnboardingView.as_view(),           name='onboarding'),
    path('dashboard/',                       views.DashboardView.as_view(),            name='dashboard'),
    path('delete-account/',                  views.DeleteAccountView.as_view(),        name='delete_account'),
    path('delete-account/request-otp/',      views.RequestDeletionOTPView.as_view(),   name='request_deletion_otp'),

    # Password reset flow
    path('forgot-password/',                 views.ForgotPasswordView.as_view(),       name='forgot_password'),
    path('forgot-password/sent/',            views.PasswordResetSentView.as_view(),    name='password_reset_sent'),
    path('reset/<uuid:token>/',              views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/',                      views.PasswordResetDoneView.as_view(),    name='password_reset_done'),

    # SSO via allauth
    path('social/',                          include('allauth.urls')),
]