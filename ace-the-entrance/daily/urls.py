from django.urls import include, path
from daily import views

app_name = 'daily'
urlpatterns = [
    path('quiz/', views.DailyQuizView.as_view(), name='quiz' ),
    path('quiz/api/questions/', views.DailyQuizAPI.as_view(), name='get_questions' ),
]