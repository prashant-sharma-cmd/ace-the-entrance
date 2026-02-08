from django.urls import path
from . import views

app_name = 'sxcmodel'
urlpatterns = [
    path('', views.TestView.as_view(), name='test'),
]