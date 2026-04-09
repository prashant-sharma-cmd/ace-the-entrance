from django.db import models


class Update(models.Model):
    CATEGORY_CHOICES = [
        ('entrance', 'Entrance Update'),
        ('changelog', 'Website Changelog'),
    ]

    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    ]

    title = models.CharField(max_length=255)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='entrance')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    body = models.TextField()
    image = models.ImageField(upload_to='updates/images/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Update'
        verbose_name_plural = 'Updates'

    def __str__(self):
        return f"[{self.get_category_display()}] {self.title}"