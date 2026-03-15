import datetime
import random
from django.utils import timezone
from django.db import models
from daily.models import Subject, Question, DailyQuiz

REPETITION = 150


def generate_daily_quiz():
    now = timezone.now()
    today_date = now.date()
    limit_date = today_date - datetime.timedelta(days=REPETITION)

    # 1. Added Saturday (5) to prevent crashes
    day_map = {
        0: "Chemistry", 1: "Biology", 2: "Maths",
        3: "English", 4: "GKIQ", 5: "GKIQ",  # Fallback for Saturday
        6: "Physics"
    }

    subject_name = day_map.get(today_date.weekday())

    # 2. Add error handling so it doesn't crash if subject is missing
    try:
        subject = Subject.objects.get(name=subject_name)
    except Subject.DoesNotExist:
        print(f"Error: Subject '{subject_name}' not found in database.")
        return []

    eligible_qs = Question.objects.filter(
        topic__subject=subject,
        is_active=True
    ).filter(
        models.Q(last_appeared__lt=limit_date) | models.Q(
            last_appeared__isnull=True)
    ).select_related('topic').order_by('?')

    # Grouping by Topic ID
    questions_by_topic = {}
    for q in eligible_qs:
        questions_by_topic.setdefault(q.topic_id, []).append(q)

    selected_questions = []
    topic_ids = list(questions_by_topic.keys())
    random.shuffle(topic_ids)  # Randomize topic order for variety

    # Track how many questions we've taken from each topic
    topic_usage_counters = {t_id: 0 for t_id in topic_ids}

    # ROUND-ROBIN SELECTION
    # We keep looping through the topics until we have 10 questions
    # OR we run out of available questions/hit the topic caps.
    while len(selected_questions) < 10:
        added_in_this_loop = False

        for t_id in topic_ids:
            if len(selected_questions) >= 10:
                break

            # CHECK LIMITS:
            # 1. Has the topic reached the 5-question cap?
            # 2. Are there questions left in this topic's list?
            if topic_usage_counters[t_id] < 5 and questions_by_topic[t_id]:
                selected_questions.append(questions_by_topic[t_id].pop(0))
                topic_usage_counters[t_id] += 1
                added_in_this_loop = True

        # Safety break: if we checked every topic and couldn't add even one question,
        # it means we are truly out of eligible questions.
        if not added_in_this_loop:
            break

    # Save to database
    if selected_questions:
        quiz, _ = DailyQuiz.objects.get_or_create(date=today_date)
        quiz.questions.set(selected_questions)
        Question.objects.filter(
            id__in=[q.id for q in selected_questions]).update(
            last_appeared=now)
        print(
            f"Generated {len(selected_questions)} questions for {subject_name}.")

    return selected_questions