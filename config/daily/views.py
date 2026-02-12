from django.http import JsonResponse
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView

from daily.models import DailyQuiz
from django.utils import timezone
import random


class DailyQuizView(TemplateView):
    template_name = 'daily/quiz.html'

class DailyQuizAPI(View):

    @staticmethod
    def get(request):
        today = timezone.now().date()

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
