from django.urls import path
from .views import DashboardView, StartQuizView, TakeQuizView, SubmitQuizView

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('start/', StartQuizView.as_view(), name='start_quiz'),
    path('take/<int:attempt_id>/<int:page_index>/', TakeQuizView.as_view(), name='take_quiz'),
    path('submit/<int:attempt_id>/', SubmitQuizView.as_view(), name='submit_quiz'),
]