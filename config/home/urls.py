from django.urls import path
from . import views

app_name = 'home'
urlpatterns = [
    path('', views.HomePageView.as_view(), name='index'),
    path('contact_us/', views.ContactUsView.as_view(), name='contact_us'),
    path('facebook/', views.redirect_to_facebook, name='facebook'),
    path('instagram/', views.redirect_to_instagram, name='instagram'),
    path('daraz/', views.redirect_to_daraz, name='daraz'),
]