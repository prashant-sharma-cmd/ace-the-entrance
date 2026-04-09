# forum/models.py
import uuid
import os
from django.db import models
from django.conf import settings


# ── Upload path helpers ────────────────────────────────────────────────────────

def thread_image_path(instance, filename):
    """Store as  discussion/threads/<uuid>.webp  — unpredictable, no collisions."""
    ext = os.path.splitext(filename)[1].lower() or ".webp"
    return f"discussion/threads/{uuid.uuid4().hex}{ext}"


def reply_image_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower() or ".webp"
    return f"discussion/replies/{uuid.uuid4().hex}{ext}"


# ── Models ─────────────────────────────────────────────────────────────────────

class Thread(models.Model):
    CATEGORY_CHOICES = [
        ("Science",  "Science"),
        ("Maths",    "Maths"),
        ("English",  "English"),
        ("GK & IQ",  "GK & IQ"),
        ("General",  "General"),
    ]

    title      = models.CharField(max_length=255)
    body       = models.TextField()
    category   = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="General")
    author     = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="threads")
    likes      = models.PositiveIntegerField(default=0)
    image      = models.ImageField(upload_to=thread_image_path, null=True, blank=True)
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
    image      = models.ImageField(upload_to=reply_image_path, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Reply by {self.author} on '{self.thread}'"


class ThreadLike(models.Model):
    """One row per (user, thread) pair — enforces one like per user at DB level."""
    user   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name="thread_likes")

    class Meta:
        unique_together = ("user", "thread")


class ReplyLike(models.Model):
    """One row per (user, reply) pair — enforces one like per user at DB level."""
    user  = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reply = models.ForeignKey(Reply, on_delete=models.CASCADE, related_name="reply_likes")

    class Meta:
        unique_together = ("user", "reply")