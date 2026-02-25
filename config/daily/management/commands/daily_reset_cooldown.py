from django.core.management.base import BaseCommand
from daily.models import Question, Subject


class Command(BaseCommand):
    help = 'Resets the cooldown for questions'

    def add_arguments(self, parser):
        # Optional: allow resetting only one subject
        parser.add_argument('--subject', type=str,
                            help='Reset only a specific subject')

    def handle(self, *args, **options):
        subject_name = options['subject']

        if subject_name:
            # Reset only questions in a specific subject
            qs = Question.objects.filter(
                topic__subject__name__iexact=subject_name)
            if not qs.exists():
                self.stdout.write(self.style.ERROR(
                    f"No questions found for subject '{subject_name}'"))
                return

            count = qs.count()
            qs.update(last_appeared=None)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully reset {count} questions for '{subject_name}'."))

        else:
            # Reset everything
            count = Question.objects.count()
            Question.objects.update(last_appeared=None)
            self.stdout.write(self.style.SUCCESS(
                f"Successfully reset the cooldown for all {count} questions."))