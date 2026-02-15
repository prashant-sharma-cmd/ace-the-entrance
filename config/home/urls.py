from django.urls import path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.HomePageView.as_view(), name='index'),
    path('contact_us/', views.ContactUsView.as_view(), name='contact_us'),
    # path('signup/', views.SignUpView.as_view(), name='signup'),
]