from django.urls import path
from discussion import views

app_name = 'discussion'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index' ),
]