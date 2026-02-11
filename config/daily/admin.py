from django.contrib import admin

from daily.models import Subject, Topic, Question, Choice, DailyQuiz

admin.site.register(Subject)
admin.site.register(Topic)
admin.site.register(Question)
admin.site.register(Choice)

@admin.register(DailyQuiz)
class DailyQuizAdmin(admin.ModelAdmin):
    filter_horizontal = ('questions',)
