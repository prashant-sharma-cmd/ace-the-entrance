from django.contrib import admin
from .models import Leaderboard, Question, QuizAttempt, UserAnswer


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ('user', 'final_grade', 'raw_score', 'correct_count', 'incorrect_count', 'total_time_seconds', 'achieved_at')
    ordering = ('-final_grade',)
    readonly_fields = ('user', 'attempt', 'final_grade', 'raw_score', 'correct_count',
                       'incorrect_count', 'total_time_seconds', 'achieved_at')



@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'text_preview', 'correct_option')
    list_filter = ('subject',)
    search_fields = ('text',)

    def text_preview(self, obj):
        return obj.text[:60]
    text_preview.short_description = 'Question'


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_option', 'is_correct_display')

    def is_correct_display(self, obj):
        return obj.is_correct()
    is_correct_display.short_description = 'Correct?'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'start_time', 'is_completed',
        'correct_count', 'incorrect_count', 'raw_score', 'final_grade'
    )
    list_filter = ('is_completed',)
    search_fields = ('user__username',)
    inlines = [UserAnswerInline]
    readonly_fields = ('session_key', 'start_time')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'attempt', 'question', 'selected_option')
    list_filter = ('attempt__user',)