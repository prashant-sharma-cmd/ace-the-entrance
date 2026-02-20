# forum/models.py
from django.db import models
from django.conf import settings

class Thread(models.Model):
    CATEGORY_CHOICES = [
        ("Science",  "Science"),
        ("Maths",     "Maths"),
        ("English", "English"),
        ("GK & IQ",     "GK & IQ"),
        ("General",     "General"),
    ]

    title      = models.CharField(max_length=255)
    body       = models.TextField()
    category   = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="General")
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads")
    likes      = models.PositiveIntegerField(default=0)
    image      = models.ImageField(upload_to='discussion/threads/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Reply(models.Model):
    thread     = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="replies")
    body       = models.TextField()
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="replies")
    likes      = models.PositiveIntegerField(default=0)
    image      = models.ImageField(upload_to='discussion/replies/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author} on '{self.thread}'"