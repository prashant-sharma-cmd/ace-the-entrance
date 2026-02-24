# models.py
from django.db import models
from django.contrib.auth.models import User
import uuid


class Question(models.Model):
    SUBJECT_CHOICES = [
        ('PHY', 'Physics'), ('CHE', 'Chemistry'), ('BIO', 'Biology'),
        ('MAT', 'Maths'), ('ENG', 'English'), ('IQ_GK', 'IQ/GK'),
    ]
    subject = models.CharField(max_length=10, choices=SUBJECT_CHOICES)
    text = models.TextField()
    image = models.ImageField(upload_to='question_diagrams/', blank=True,
                              null=True)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'),
                 (4, 'Option 4')]
    )

    def __str__(self):
        return f"[{self.subject}] {self.text[:40]}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    question_sequence = models.JSONField(
        default=list)  # [[PHY q_ids], [CHE q_ids], ...]

    # Raw score fields
    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)
    unattempted_count = models.IntegerField(default=0)
    raw_score = models.FloatField(default=0.0)  # correct - 0.25 * incorrect

    # Time fields
    total_time_seconds = models.IntegerField(default=0)  # actual seconds taken

    # Final computed grade (0–100)
    final_grade = models.FloatField(default=0.0)

    is_completed = models.BooleanField(default=False)
    session_key = models.UUIDField(default=uuid.uuid4,
                                   unique=True)  # for recovery


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE,
                                related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.IntegerField(null=True,
                                          blank=True)  # null = skipped