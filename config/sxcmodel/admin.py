from django.contrib import admin
from .models import Question, QuizAttempt, UserAnswer


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'short_text', 'correct_option')
    list_filter = ('subject',)
    search_fields = ('text', 'option_1', 'option_2', 'option_3', 'option_4')

    def short_text(self, obj):
        if len(obj.text) > 50:
            return obj.text[:50] + '...'
        return obj.text

    short_text.short_description = 'Question Text'


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option')
    can_delete = False

    # We set max_num to 0 so we don't accidentally add new answers from the attempt screen
    max_num = 0


class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'raw_score', 'final_grade', 'is_completed',
                    'start_time')
    list_filter = ('is_completed', 'start_time')

    # Allows you to search for a specific user's attempt using their username
    search_fields = ('user__username', 'session_key')

    readonly_fields = ('session_key', 'start_time', 'end_time')
    inlines = [UserAnswerInline]


class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_option')
    list_filter = ('selected_option',)
    search_fields = ('attempt__user__username', 'question__text')


admin.site.register(Question, QuestionAdmin)
admin.site.register(QuizAttempt, QuizAttemptAdmin)
admin.site.register(UserAnswer, UserAnswerAdmin)
