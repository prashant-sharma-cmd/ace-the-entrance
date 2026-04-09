from django.db import models
from accounts.models import User
import uuid


class Question(models.Model):
    SUBJECT_CHOICES = [
        ('PHY', 'Physics'), ('CHE', 'Chemistry'), ('BIO', 'Biology'),
        ('MAT', 'Maths'), ('ENG', 'English'), ('IQ_GK', 'IQ/GK'),
    ]
    subject = models.CharField(max_length=10, choices=SUBJECT_CHOICES)
    text = models.TextField()
    image = models.ImageField(upload_to='question_diagrams/', blank=True, null=True)
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_option = models.IntegerField(
        choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')]
    )

    @property
    def options_list(self):
        """Returns [(1, opt1), (2, opt2), (3, opt3), (4, opt4)]"""
        return [
            (1, self.option_1),
            (2, self.option_2),
            (3, self.option_3),
            (4, self.option_4),
        ]

    def __str__(self):
        return f"[{self.subject}] {self.text[:40]}"


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attempts')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    question_sequence = models.JSONField(default=list)  # [[PHY q_ids], [CHE q_ids], ...]

    # Raw score fields
    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)
    unattempted_count = models.IntegerField(default=0)
    raw_score = models.FloatField(default=0.0)  # correct - 0.25 * incorrect

    # Time fields
    total_time_seconds = models.IntegerField(default=0)

    # Final computed grade (0–100)
    # Formula: final_grade = (raw_score / total_questions) * 80 + time_bonus * 20
    # time_bonus = max(0, 1 - (total_time_seconds / MAX_TIME_SECONDS))
    # This gives 80% weightage to marks and 20% to speed.
    final_grade = models.FloatField(default=0.0)

    is_completed = models.BooleanField(default=False)
    session_key = models.UUIDField(default=uuid.uuid4, unique=True)

    # Track the current page/section index so user can resume
    current_section_index = models.IntegerField(default=0)

    class Meta:
        ordering = ['-final_grade']

    def __str__(self):
        return f"{self.user.username} – attempt {self.pk} (grade={self.final_grade:.1f})"


class Leaderboard(models.Model):
    """
    Denormalised table — one row per user, always reflecting their single
    best completed attempt.  Updated by SubmitExamView whenever a new
    attempt beats the stored final_grade.  Never queried with aggregation;
    leaderboard reads are a simple ORDER BY on this table.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='leaderboard_entry')
    attempt = models.OneToOneField(
        'QuizAttempt', on_delete=models.CASCADE, related_name='leaderboard_entry'
    )

    # Denormalised score columns (mirrors the linked attempt) so the
    # leaderboard page needs zero joins beyond the user FK.
    final_grade = models.FloatField(db_index=True)
    raw_score = models.FloatField()
    correct_count = models.IntegerField()
    incorrect_count = models.IntegerField()
    total_time_seconds = models.IntegerField()
    achieved_at = models.DateTimeField()  # = attempt.end_time

    class Meta:
        ordering = ['-final_grade']

    def __str__(self):
        return f"{self.user.username} — {self.final_grade:.1f}"


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.IntegerField(null=True, blank=True)  # null = skipped
    time_taken_seconds = models.IntegerField(default=0)  # per-question timer

    class Meta:
        unique_together = ('attempt', 'question')

    def is_correct(self):
        return self.selected_option == self.question.correct_option

    def __str__(self):
        return f"Attempt {self.attempt_id} | Q{self.question_id} → {self.selected_option}"