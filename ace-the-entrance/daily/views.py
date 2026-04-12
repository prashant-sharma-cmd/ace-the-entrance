from django.http import JsonResponse
from django.views import View
from django.views.generic import TemplateView

from daily.models import DailyQuiz, QuizAttempt
from django.utils import timezone
import random
import json


class DailyQuizView(TemplateView):
    template_name = 'daily/quiz.html'

class DailyQuizAPI(View):

    @staticmethod
    def get(request):
        today = timezone.now().date()
        weekday = today.weekday()

        if weekday == 5:
            return JsonResponse({
                'weekend': True,
            }, status=200)

        quiz = DailyQuiz.objects.prefetch_related('questions__choices').filter(
            date=today).first()

        if not quiz:
            from daily.script import generate_daily_quiz
            generate_daily_quiz()
            quiz = DailyQuiz.objects.prefetch_related(
                'questions__choices').filter(date=today).first()

        questions = list(quiz.questions.all())
        random.shuffle(questions)
        quiz_data = []
        for question in questions:
            choices = list(question.choices.all())
            random.shuffle(choices)
            quiz_data.append({
                'id': question.id,
                'question' : question.text,
                'choices' : [
                    {
                        'id' : choice.id,
                        'text' : choice.text,
                        'isCorrect' : choice.is_correct,
                    } for choice in choices
                ],
            })

        return JsonResponse({'questions' : quiz_data})

class SubmitQuizScoreAPI(View):
    """
    POST { "score": <int>, "total": <int> }

    • Logged-in users  → upsert a QuizAttempt row for today, return saved=True
    • Anonymous users  → do nothing,                        return saved=False

    The frontend calls this silently after submitQuiz(); it never blocks
    the results screen for either type of user.
    """

    def post(self, request):
        try:
            body  = json.loads(request.body)
            score = int(body['score'])
            total = int(body['total'])
        except (KeyError, ValueError, json.JSONDecodeError):
            return JsonResponse({'error': 'Invalid payload.'}, status=400)

        if score < 0 or total <= 0 or score > total:
            return JsonResponse({'error': 'Score values out of range.'}, status=400)

        if not request.user.is_authenticated:
            return JsonResponse({'saved': False, 'reason': 'anonymous'})

        today = timezone.now().date()
        attempt, created = QuizAttempt.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={'score': score, 'total': total},
        )

        return JsonResponse({
            'saved':   True,
            'created': created,  
            'date':    str(today),
            'score':   attempt.score,
            'total':   attempt.total,
        })