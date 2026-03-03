from django.contrib import admin
from .models import Update


@admin.register(Update)
class UpdateAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'is_published', 'created_at')
    list_filter = ('category', 'priority', 'is_published')
    search_fields = ('title', 'body')
    list_editable = ('is_published', 'priority')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Content', {
            'fields': ('title', 'category', 'body', 'image')
        }),
        ('Settings', {
            'fields': ('priority', 'is_published')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )