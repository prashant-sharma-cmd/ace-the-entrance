from django.shortcuts import render
from django.views import View
from daily.models import DailyQuiz
from django.utils import timezone


class DailyQuizView(View):
    def get(self, request):
        template_name = 'daily/quiz.html'
        today = timezone.now().date()

        # Use prefetch_related for maximum speed (1 query for quiz + 1 for all choices)
        quiz = DailyQuiz.objects.prefetch_related('questions__choices').filter(
            date=today).first()

        if not quiz:
            # Fallback: if cron failed, generate it on the fly
            from daily.script import generate_daily_quiz
            generate_daily_quiz()
            quiz = DailyQuiz.objects.prefetch_related(
                'questions__choices').filter(date=today).first()

        return render(self.request, template_name, {'quiz': quiz})
