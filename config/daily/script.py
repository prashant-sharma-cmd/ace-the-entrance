import datetime
from django.utils import timezone
from daily.models import Subject, Question, DailyQuiz
from django.db import models
import random

REPETITION = 150

def generate_daily_quiz():
    today = timezone.now().date()
    limit_date = today - datetime.timedelta(days=REPETITION)

    # Determining the Subject
    day_map = {6: "Physics", 0: "Chemistry", 1:"Biology", 2:"Maths",
               3: "English", 4: "IQ/GK"}
    subject_name = day_map.get(today.weekday())
    subject = Subject.objects.get(name=subject_name)

    eligible_qs = Question.objects.filter(topic__subject=subject,
                                                 is_active=True).filter(
        models.Q(last_appeared__lt=limit_date) | models.Q(last_appeared__isnull=True)
    ).select_related('topic').order_by('?')

    questions_by_topic = {}
    for q in eligible_qs:
        questions_by_topic.setdefault(q.topic.id, []).append(q)

    selected_questions = []
    topic_ids = list(questions_by_topic.keys())
    random.shuffle(topic_ids)

    for t_id in topic_ids:
        if len(selected_questions) >= 10: break
        selected_questions.append(questions_by_topic[t_id].pop(0))

    for t_id in topic_ids:
        if len(selected_questions) >= 10: break
        if questions_by_topic[t_id]:
            selected_questions.append(questions_by_topic[t_id].pop(0))

    quiz, created = DailyQuiz.objects.get_or_create(date=today)
    if created:
        quiz.questions.set(selected_questions)
        Question.objects.filter(id__in=[q.id for q in selected_questions]).update(last_appeared=today)

    return selected_questions