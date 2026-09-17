from django.contrib import admin

from .models import Question, Quiz, StudentAnswer, StudentQuizAttempt


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "start_time", "end_time", "total_marks")
    list_filter = ("course",)
    inlines = [QuestionInline]


admin.site.register(StudentQuizAttempt)
admin.site.register(StudentAnswer)
