import random
from .constants import (
    MAX_TIME_SECONDS, QUESTIONS_PER_SECTION,
    RANDOMIZED_SUBJECTS, ORDERED_SUBJECTS, MARKS_WEIGHT, TIME_WEIGHT
)
from .models import Question


def build_question_sequence():
    """
    Returns a list-of-lists: each inner list contains Question PKs for one section.
    Randomized subjects appear in a random order among themselves, with their
    question order also shuffled. ENG and IQ_GK always come last, in DB order.
    """
    sequence = []

    # Shuffle which randomized subjects appear first
    randomized = list(RANDOMIZED_SUBJECTS)
    random.shuffle(randomized)

    for subject in randomized:
        q_ids = list(
            Question.objects.filter(subject=subject)
            .values_list('id', flat=True)
        )
        random.shuffle(q_ids)
        # Take only QUESTIONS_PER_SECTION if more exist
        sequence.append(q_ids[:QUESTIONS_PER_SECTION])

    for subject in ORDERED_SUBJECTS:
        q_ids = list(
            Question.objects.filter(subject=subject)
            .order_by('id')
            .values_list('id', flat=True)
        )
        sequence.append(q_ids[:QUESTIONS_PER_SECTION])

    return sequence


def compute_final_grade(correct, incorrect, total_questions, time_seconds):
    """
    final_grade is out of 100.

    Marks component (80 pts max):
      raw_score = correct - 0.25 * incorrect
      marks_score = (raw_score / total_questions) * 80
      clamped to [0, 80]

    Time bonus component (20 pts max):
      time_bonus = max(0, 1 - time_seconds / MAX_TIME_SECONDS)
      time_score = time_bonus * 20

    final_grade = marks_score + time_score
    """
    if total_questions == 0:
        return 0.0

    raw_score = correct - 0.25 * incorrect
    marks_score = max(0.0, (raw_score / total_questions) * 80)
    marks_score = min(marks_score, 80.0)

    time_bonus = max(0.0, 1 - time_seconds / MAX_TIME_SECONDS)
    time_score = time_bonus * 20

    return round(marks_score + time_score, 2)


def get_section_label(subject_code):
    labels = {
        'PHY': 'Physics', 'CHE': 'Chemistry', 'BIO': 'Biology',
        'MAT': 'Maths', 'ENG': 'English', 'IQ_GK': 'IQ / GK',
    }
    return labels.get(subject_code, subject_code)