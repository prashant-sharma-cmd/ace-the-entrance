from django.urls import path
from . import views

app_name = 'sxcmodel'
urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('start/', views.StartExamView.as_view(), name='start'),
    path('resume/<uuid:session_key>/', views.ResumeExamView.as_view(), name='resume'),
    path('exam/<uuid:session_key>/section/<int:section_index>/', views.SectionView.as_view(), name='section'),
    path('exam/<uuid:session_key>/submit/', views.SubmitExamView.as_view(), name='submit'),
    path('exam/<uuid:session_key>/results/', views.ResultsView.as_view(), name='results'),
    path('exam/<uuid:session_key>/save/', views.SaveProgressView.as_view(), name='save_progress'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
]