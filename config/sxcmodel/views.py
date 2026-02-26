import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, TemplateView

from .constants import MAX_TIME_SECONDS, TIME_WEIGHT
from .models import Leaderboard, Question, QuizAttempt, UserAnswer
from .utils import build_question_sequence, compute_final_grade, get_section_label


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class AttemptMixin:
    """
    Shared helper that resolves a QuizAttempt from the URL's session_key,
    enforcing that it belongs to the logged-in user.
    require_incomplete=True  → 404 if already completed
    require_completed=True   → 404 if not yet completed
    """
    require_incomplete: bool = False
    require_completed: bool = False

    def get_attempt(self, session_key):
        qs = QuizAttempt.objects.filter(session_key=session_key, user=self.request.user)
        if self.require_incomplete:
            qs = qs.filter(is_completed=False)
        if self.require_completed:
            qs = qs.filter(is_completed=True)
        return get_object_or_404(qs)


def _elapsed_seconds(attempt) -> int:
    """Wall-clock seconds since attempt started (server-side, cannot be spoofed)."""
    return int((timezone.now() - attempt.start_time).total_seconds())


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Landing page. Shows best stats, any resumable attempt, full history,
    and a Start button.
    """
    template_name = 'sxcmodel/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user

        ctx['best_attempt'] = (
            QuizAttempt.objects.filter(user=user, is_completed=True)
            .order_by('-final_grade')
            .first()
        )
        ctx['incomplete_attempt'] = (
            QuizAttempt.objects.filter(user=user, is_completed=False)
            .order_by('-start_time')
            .first()
        )
        ctx['completed_attempts'] = (
            QuizAttempt.objects.filter(user=user, is_completed=True)
            .order_by('-start_time')
        )
        return ctx


# ---------------------------------------------------------------------------
# Start / Resume
# ---------------------------------------------------------------------------

class StartExamView(LoginRequiredMixin, View):
    """
    Creates a fresh QuizAttempt (closing any incomplete ones) and redirects
    to section 0.  Accepts both GET and POST so the dashboard confirm dialog works.
    """

    def get(self, request):
        return self._start(request)

    def post(self, request):
        return self._start(request)

    def _start(self, request):
        QuizAttempt.objects.filter(user=request.user, is_completed=False).update(is_completed=True)

        sequence = build_question_sequence()
        attempt = QuizAttempt.objects.create(
            user=request.user,
            question_sequence=sequence,
            current_section_index=0,
        )
        return redirect('sxcmodel:section', session_key=attempt.session_key, section_index=0)


class ResumeExamView(LoginRequiredMixin, AttemptMixin, View):
    """Redirects to the user's saved section in an existing incomplete attempt."""
    require_incomplete = True

    def get(self, request, session_key):
        attempt = self.get_attempt(session_key)
        return redirect(
            'sxcmodel:section',
            session_key=attempt.session_key,
            section_index=attempt.current_section_index,
        )


# ---------------------------------------------------------------------------
# Section (exam page)
# ---------------------------------------------------------------------------

class SectionView(LoginRequiredMixin, AttemptMixin, View):
    """
    GET  — render the question form for one section.
    POST — save answers, advance to next section (or trigger submit).
    """
    require_incomplete = True
    template_name = 'sxcmodel/section.html'

    # ---- private helpers -------------------------------------------------

    def _ordered_questions(self, attempt, section_index):
        """Return questions in the exact order stored in question_sequence."""
        ids = attempt.question_sequence[section_index]
        lookup = {q.id: q for q in Question.objects.filter(id__in=ids)}
        return [lookup[qid] for qid in ids if qid in lookup]

    def _existing_answers(self, attempt, questions):
        return {
            ua.question_id: ua.selected_option
            for ua in UserAnswer.objects.filter(attempt=attempt, question__in=questions)
        }

    # ---- GET -------------------------------------------------------------

    def get(self, request, session_key, section_index):
        attempt = self.get_attempt(session_key)
        sequence = attempt.question_sequence

        if section_index >= len(sequence):
            return redirect('sxcmodel:submit', session_key=session_key)

        if attempt.current_section_index != section_index:
            attempt.current_section_index = section_index
            attempt.save(update_fields=['current_section_index'])

        questions = self._ordered_questions(attempt, section_index)
        elapsed = _elapsed_seconds(attempt)

        return render(request, self.template_name, {
            'attempt': attempt,
            'questions': questions,
            'section_index': section_index,
            'total_sections': len(sequence),
            'section_number': section_index + 1,
            'subject_label': get_section_label(questions[0].subject) if questions else '',
            'is_last_section': section_index == len(sequence) - 1,
            'existing_answers': self._existing_answers(attempt, questions),
            'time_remaining': max(0, MAX_TIME_SECONDS - elapsed),
            'max_time': MAX_TIME_SECONDS,
            'session_key': str(session_key),
        })

    # ---- POST ------------------------------------------------------------

    def post(self, request, session_key, section_index):
        attempt = self.get_attempt(session_key)
        sequence = attempt.question_sequence

        if section_index >= len(sequence):
            return redirect('sxcmodel:submit', session_key=session_key)

        questions = self._ordered_questions(attempt, section_index)
        time_taken = int(request.POST.get('time_taken_seconds', 0))
        per_q_time = time_taken // max(len(questions), 1)

        for question in questions:
            raw = request.POST.get(f'answer_{question.id}')
            selected = int(raw) if raw and raw.isdigit() else None
            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_option': selected, 'time_taken_seconds': per_q_time},
            )

        next_index = section_index + 1
        if next_index >= len(sequence):
            return redirect('sxcmodel:submit', session_key=attempt.session_key)

        attempt.current_section_index = next_index
        attempt.save(update_fields=['current_section_index'])
        return redirect('sxcmodel:section', session_key=attempt.session_key, section_index=next_index)


# ---------------------------------------------------------------------------
# Submit
# ---------------------------------------------------------------------------

class SubmitExamView(LoginRequiredMixin, AttemptMixin, View):
    """
    Finalises the attempt: computes all scores, marks it complete, redirects
    to results.  Accepts GET so the JS auto-submit (form POST) and direct URL
    navigation both work gracefully.
    """
    require_incomplete = True

    def get(self, request, session_key):
        return self._finalise(request, session_key)

    def post(self, request, session_key):
        return self._finalise(request, session_key)

    def _finalise(self, request, session_key):
        attempt = self.get_attempt(session_key)
        answers = UserAnswer.objects.filter(attempt=attempt).select_related('question')
        total_questions = sum(len(s) for s in attempt.question_sequence)

        correct = sum(1 for a in answers if a.selected_option == a.question.correct_option)
        incorrect = sum(
            1 for a in answers
            if a.selected_option is not None and a.selected_option != a.question.correct_option
        )
        elapsed = _elapsed_seconds(attempt)

        attempt.end_time = timezone.now()
        attempt.correct_count = correct
        attempt.incorrect_count = incorrect
        attempt.unattempted_count = total_questions - correct - incorrect
        attempt.raw_score = correct - 0.25 * incorrect
        attempt.total_time_seconds = elapsed
        attempt.final_grade = compute_final_grade(correct, incorrect, total_questions, elapsed)
        attempt.is_completed = True
        attempt.save()

        # --- Update the Leaderboard table (upsert best score) ---
        # Only write if there is no existing entry, or this attempt beats it.
        existing = Leaderboard.objects.filter(user=request.user).first()
        if existing is None or attempt.final_grade > existing.final_grade:
            Leaderboard.objects.update_or_create(
                user=request.user,
                defaults={
                    'attempt': attempt,
                    'final_grade': attempt.final_grade,
                    'raw_score': attempt.raw_score,
                    'correct_count': attempt.correct_count,
                    'incorrect_count': attempt.incorrect_count,
                    'total_time_seconds': attempt.total_time_seconds,
                    'achieved_at': attempt.end_time,
                },
            )

        return redirect('sxcmodel:results', session_key=session_key)


# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------

class ResultsView(LoginRequiredMixin, AttemptMixin, TemplateView):
    """Marks + time breakdown after a completed attempt."""
    require_completed = True
    template_name = 'sxcmodel/results.html'

    def get(self, request, session_key, **kwargs):
        attempt = self.get_attempt(session_key)
        total_questions = sum(len(s) for s in attempt.question_sequence)
        avg_time = attempt.total_time_seconds / total_questions if total_questions else 0
        time_bonus = max(0.0, 1 - attempt.total_time_seconds / MAX_TIME_SECONDS) * 20

        context = self.get_context_data(
            attempt=attempt,
            total_questions=total_questions,
            avg_time_seconds=int(avg_time),
            speed_bonus=round(time_bonus, 0),
        )
        return self.render_to_response(context)


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

class LeaderboardView(ListView):
    """
    Reads directly from the Leaderboard table — one pre-computed row per user,
    already ordered by final_grade DESC.  No aggregation, no sorting in Python.
    No login required.
    """
    template_name = 'sxcmodel/leaderboard.html'
    context_object_name = 'entries'

    def get_queryset(self):
        return Leaderboard.objects.select_related('user', 'attempt').order_by('-final_grade')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        current_user_rank = None
        if self.request.user.is_authenticated:
            for rank, entry in enumerate(ctx['entries'], 1):
                if entry.user_id == self.request.user.id:
                    current_user_rank = rank
                    break
        ctx['current_user_rank'] = current_user_rank
        return ctx


# ---------------------------------------------------------------------------
# AJAX: auto-save progress
# ---------------------------------------------------------------------------

class SaveProgressView(LoginRequiredMixin, AttemptMixin, View):
    """
    Called every 30 s by the exam JS to persist current answers without
    navigating away.
    Body: JSON { "answers": { "<question_id>": <int|null>, … } }
    """
    require_incomplete = True
    http_method_names = ['post']

    def post(self, request, session_key):
        attempt = self.get_attempt(session_key)

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        for q_id_str, selected in data.get('answers', {}).items():
            try:
                question = Question.objects.get(pk=int(q_id_str))
            except (ValueError, Question.DoesNotExist):
                continue

            UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={'selected_option': selected},
            )

        return JsonResponse({'status': 'ok'})