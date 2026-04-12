from django.urls import include, path
from daily import views

app_name = 'daily'
urlpatterns = [
    path('quiz/', views.DailyQuizView.as_view(), name='quiz' ),
    path('api/questions/', views.DailyQuizAPI.as_view(), name='get_questions' ),
    path('api/submit/', views.SubmitQuizScoreAPI.as_view(), name='submit_score'), 
]