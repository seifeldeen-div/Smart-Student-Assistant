from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from accounts.decorators import role_required
from courses.models import Course

from .forms import QuestionForm, QuizForm
from .models import Question, Quiz, StudentAnswer, StudentQuizAttempt
from .signals import notify_open_quiz


def _role(user):
    if user.is_superuser:
        return "admin"
    return getattr(getattr(user, "profile", None), "role", None)


def _owned_quizzes(user):
    if user.is_superuser or _role(user) == "admin":
        return Quiz.objects.select_related("course")
    return Quiz.objects.filter(course__instructor=user).select_related("course")


def _student_quizzes(user):
    current_time = timezone.now()
    return Quiz.objects.filter(
        course__students=user,
        start_time__lte=current_time,
        end_time__gte=current_time,
    ).select_related("course").prefetch_related("questions")


def _quiz_or_404(user, quiz_id):
    quiz = _owned_quizzes(user).filter(id=quiz_id).first()
    if quiz is None:
        raise Http404
    return quiz


def _recalculate_total_marks(quiz):
    quiz.total_marks = quiz.question_total_marks
    Quiz.objects.filter(pk=quiz.pk).update(total_marks=quiz.total_marks)


def _ensure_open_notifications(user):
    for quiz in _student_quizzes(user):
        notify_open_quiz(quiz)


@login_required
def quiz_list(request):
    if _role(request.user) == "student":
        _ensure_open_notifications(request.user)
        quizzes = _student_quizzes(request.user)
        attempts = {
            attempt.quiz_id: attempt
            for attempt in StudentQuizAttempt.objects.filter(student=request.user, quiz__in=quizzes)
        }
        for quiz in quizzes:
            quiz.student_attempt = attempts.get(quiz.id)
        return render(request, "quizzes/quiz_list.html", {"quizzes": quizzes})
    quizzes = _owned_quizzes(request.user).prefetch_related("questions")
    return render(request, "quizzes/instructor_quiz_list.html", {"quizzes": quizzes})


@role_required("instructor", "admin")
def quiz_create(request, course_id):
    course = Course.objects.filter(id=course_id).first()
    if course is None or (_role(request.user) not in {"admin"} and not request.user.is_superuser and course.instructor_id != request.user.id):
        raise Http404
    form = QuizForm(request.POST or None)
    if form.is_valid():
        quiz = form.save(commit=False)
        quiz.course = course
        quiz.save()
        return redirect("quiz_question_create", quiz_id=quiz.id)
    return render(request, "quizzes/quiz_form.html", {"form": form, "course": course, "title": "Create Quiz"})


@role_required("instructor", "admin")
def quiz_update(request, quiz_id):
    quiz = _quiz_or_404(request.user, quiz_id)
    form = QuizForm(request.POST or None, instance=quiz)
    if form.is_valid():
        form.save()
        return redirect("instructor_quiz_submissions", quiz_id=quiz.id)
    return render(request, "quizzes/quiz_form.html", {"form": form, "course": quiz.course, "quiz": quiz, "title": "Edit Quiz"})


@role_required("instructor", "admin")
def quiz_question_create(request, quiz_id):
    quiz = _quiz_or_404(request.user, quiz_id)
    form = QuestionForm(request.POST or None)
    if form.is_valid():
        question = form.save(commit=False)
        question.quiz = quiz
        question.save()
        _recalculate_total_marks(quiz)
        return redirect("quiz_question_create", quiz_id=quiz.id)
    return render(request, "quizzes/question_form.html", {"form": form, "quiz": quiz, "questions": quiz.questions.all()})


@role_required("instructor", "admin")
def quiz_question_update(request, question_id):
    question = Question.objects.select_related("quiz").filter(id=question_id).first()
    if question is None or not _owned_quizzes(request.user).filter(id=question.quiz_id).exists():
        raise Http404
    form = QuestionForm(request.POST or None, instance=question)
    if form.is_valid():
        form.save()
        _recalculate_total_marks(question.quiz)
        return redirect("quiz_question_create", quiz_id=question.quiz_id)
    return render(request, "quizzes/question_form.html", {"form": form, "quiz": question.quiz, "questions": question.quiz.questions.all()})


@role_required("instructor", "admin")
@require_http_methods(["POST"])
def quiz_question_delete(request, question_id):
    question = Question.objects.select_related("quiz").filter(id=question_id).first()
    if question is None or not _owned_quizzes(request.user).filter(id=question.quiz_id).exists():
        raise Http404
    quiz = question.quiz
    question.delete()
    _recalculate_total_marks(quiz)
    return redirect("quiz_question_create", quiz_id=quiz.id)


@role_required("student")
def quiz_attempt(request, quiz_id):
    quiz = _student_quizzes(request.user).filter(id=quiz_id).first()
    if quiz is None:
        raise Http404
    attempt, _ = StudentQuizAttempt.objects.get_or_create(quiz=quiz, student=request.user)
    if attempt.completed:
        return redirect("quiz_review", attempt_id=attempt.id)

    questions = list(quiz.questions.all())
    if request.method == "POST":
        score = 0
        with transaction.atomic():
            for question in questions:
                selected = request.POST.get(f"question_{question.id}", "")
                if selected not in dict(Question.OPTION_CHOICES):
                    selected = ""
                StudentAnswer.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={"selected_option": selected},
                )
                if selected == question.correct_option:
                    score += question.marks
            attempt.score = score
            attempt.completed = True
            attempt.submitted_at = timezone.now()
            attempt.save(update_fields=["score", "completed", "submitted_at"])
        return redirect("quiz_review", attempt_id=attempt.id)

    return render(request, "quizzes/quiz_attempt.html", {"quiz": quiz, "questions": questions})


@role_required("student")
def quiz_review(request, attempt_id):
    attempt = StudentQuizAttempt.objects.filter(
        id=attempt_id,
        student=request.user,
        completed=True,
    ).select_related("quiz", "quiz__course").prefetch_related("answers__question").first()
    if attempt is None:
        raise Http404
    answers = {answer.question_id: answer for answer in attempt.answers.all()}
    return render(request, "quizzes/quiz_review.html", {"attempt": attempt, "questions": attempt.quiz.questions.all(), "answers": answers})


@role_required("instructor", "admin")
def instructor_quiz_submissions(request, quiz_id):
    quiz = _quiz_or_404(request.user, quiz_id)
    attempts = quiz.attempts.filter(completed=True).select_related("student")
    return render(request, "quizzes/instructor_submissions.html", {"quiz": quiz, "attempts": attempts})


@role_required("instructor", "admin")
def instructor_attempt_detail(request, attempt_id):
    attempt = StudentQuizAttempt.objects.filter(id=attempt_id).select_related("quiz", "quiz__course", "student").prefetch_related("answers__question").first()
    if attempt is None or not _owned_quizzes(request.user).filter(id=attempt.quiz_id).exists():
        raise Http404
    answers = {answer.question_id: answer for answer in attempt.answers.all()}
    return render(request, "quizzes/instructor_attempt_detail.html", {"attempt": attempt, "questions": attempt.quiz.questions.all(), "answers": answers})