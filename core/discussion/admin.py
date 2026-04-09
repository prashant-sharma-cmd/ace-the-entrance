# forum/admin.py
from django.contrib import admin
from .models import Thread, Reply

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display  = ("title", "author", "category", "likes", "created_at")
    list_filter   = ("category",)
    search_fields = ("title", "author__username")

@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display  = ("thread", "author", "likes", "created_at")
    search_fields = ("author__username",)