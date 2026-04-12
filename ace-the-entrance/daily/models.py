from django.utils import timezone
from django.db import models
from django.conf import settings

class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Topic(models.Model):
    name = models.CharField(max_length=100)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='topics')

    def __str__(self):
        return f"{self.name} - {self.subject.name}"

class Question(models.Model):
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    last_appeared = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.topic} - {self.text}"

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.TextField()
    is_correct = models.BooleanField(default=False)

class DailyQuiz(models.Model):
    date = models.DateField(unique=True, default=timezone.now)
    questions = models.ManyToManyField(Question)

class QuizAttempt(models.Model):
    """
    Records one quiz sitting for an authenticated user.
    Anonymous users are silently skipped — nothing is stored.
    """
    user = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.CASCADE,
                    related_name='daily_quiz_attempts',
                )
    date       = models.DateField()          
    score      = models.PositiveIntegerField()   
    total      = models.PositiveIntegerField()   
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} | {self.date} | {self.score}/{self.total}"
