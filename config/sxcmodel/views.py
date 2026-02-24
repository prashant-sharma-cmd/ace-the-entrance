import random
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .models import Question, QuizAttempt, UserAnswer


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'sxcmodel/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check for unfinished quiz
        context['active_attempt'] = QuizAttempt.objects.filter(
            user=self.request.user, is_completed=False
        ).first()
        # Top 50 Leaderboard
        context['leaderboard'] = QuizAttempt.objects.filter(
            is_completed=True
        ).order_by('-final_grade')[:50]

        return context


class StartQuizView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')

        if action == 'new':
            # Delete old incomplete attempts
            QuizAttempt.objects.filter(user=request.user,
                                       is_completed=False).delete()

            # Generate Sequence
            subjects = ['PHY', 'CHE', 'BIO', 'MAT', 'ENG', 'IQ_GK']
            random.shuffle(subjects)

            sequence = []
            for sub in subjects:
                q_ids = list(
                    Question.objects.filter(subject=sub).values_list('id',
                                                                     flat=True))
                random.shuffle(q_ids)
                sequence.append(q_ids)  # E.g., Appends 20 shuffled Physics IDs

            attempt = QuizAttempt.objects.create(user=request.user,
                                                 question_sequence=sequence)
            return redirect('take_quiz', attempt_id=attempt.id, page_index=0)

        elif action == 'resume':
            attempt = QuizAttempt.objects.filter(user=request.user,
                                                 is_completed=False).first()
            if attempt:
                return redirect('take_quiz', attempt_id=attempt.id,
                                page_index=0)

        return redirect('dashboard')

class TakeQuizView(LoginRequiredMixin, View):

    def get_attempt_and_questions(self, attempt_id, page_index):
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=self.request.user, is_completed=False)
        current_page_q_ids = attempt.question_sequence[page_index]

        questions = list(Question.objects.filter(id__in=current_page_q_ids))
        questions.sort(key=lambda x: current_page_q_ids.index(x.id))
        return attempt, questions

    def get(self, request, attempt_id, page_index, *args, **kwargs):
        attempt, questions = self.get_attempt_and_questions(attempt_id, page_index)

        # Calculate time remaining for the 1.5 Hour (5400 seconds) timer
        elapsed_time = (timezone.now() - attempt.start_time).total_seconds()
        time_remaining = max(0, 5400 - int(elapsed_time))

        user_answers = dict(
            UserAnswer.objects.filter(attempt=attempt).values_list('question_id', 'selected_option')
        )
        for q in questions:
            q.selected_option = user_answers.get(q.id, None)

        context = {
            'attempt': attempt,
            'questions': questions,
            'page_index': page_index,
            'total_pages': len(attempt.question_sequence),
            'time_remaining': time_remaining, # Pass to template
        }
        return render(request, 'quiz/take_quiz.html', context)

    def post(self, request, attempt_id, page_index, *args, **kwargs):
        attempt, questions = self.get_attempt_and_questions(attempt_id, page_index)

        for q in questions:
            selected = request.POST.get(f'question_{q.id}')
            if selected:
                UserAnswer.objects.update_or_create(
                    attempt=attempt, question=q,
                    defaults={'selected_option': int(selected)}
                )

        # If JS timer forced a submit, redirect straight to submission
        if request.POST.get('force_submit') == '1':
            return redirect('submit_quiz', attempt_id=attempt.id)

        if page_index < len(attempt.question_sequence) - 1:
            return redirect('take_quiz', attempt_id=attempt.id, page_index=page_index + 1)
        else:
            return redirect('submit_quiz', attempt_id=attempt.id)

class SubmitQuizView(LoginRequiredMixin, View):
    def get(self, request, attempt_id, *args, **kwargs):
        # We allow fetching completed attempts so users can refresh their results page
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)

        if not attempt.is_completed:
            attempt.end_time = timezone.now()
            time_taken = (attempt.end_time - attempt.start_time).total_seconds()

            # Enforce the 1.5 hour max limit on the backend (plus 5 seconds buffer)
            if time_taken > 5405:
                time_taken = 5400

            correct = 0
            incorrect = 0

            answers = attempt.answers.all()
            for ans in answers:
                if ans.selected_option is not None:
                    if ans.selected_option == ans.question.correct_option:
                        correct += 1
                    else:
                        incorrect += 1

            unattempted = 100 - (correct + incorrect)
            score = correct - (incorrect * 0.25)

            final_grade = score + (100.0 / (time_taken + 100.0))

            attempt.correct_answers = correct
            attempt.incorrect_answers = incorrect
            attempt.unattempted_answers = unattempted
            attempt.score = score
            attempt.final_grade = round(final_grade, 5)
            attempt.time_taken_seconds = int(time_taken)
            attempt.is_completed = True
            attempt.save()

        time_per_question = attempt.time_taken_seconds / 100.0

        return render(request, 'quiz/result.html', {
            'attempt': attempt,
            'time_per_question': round(time_per_question, 2)
        })