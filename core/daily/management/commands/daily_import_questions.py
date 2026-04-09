import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from daily.models import Subject, Topic, Question, Choice

class Command(BaseCommand):
    help = 'Imports questions from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str,
                            help='The path to the CSV file')

    def handle(self, *args, **options):
        file_path = options['csv_file']

        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f"File '{file_path}' does not exist."))
            return

        self.stdout.write(
            self.style.SUCCESS(f"Starting import from {file_path}..."))

        # We use a transaction so that if one row fails, nothing is saved (data integrity)
        try:
            with transaction.atomic():
                with open(file_path, mode='r', encoding='utf-8-sig') as file:
                    reader = csv.DictReader(file)

                    count = 0
                    for row in reader:
                        subj_name = row['subject'].strip()
                        top_name = row['topic'].strip()
                        q_text = row['question_text'].strip()
                        ans_text = row['correct_answer'].strip()

                        subject_obj, _ = Subject.objects.get_or_create(
                            name=subj_name)

                        topic_obj, _ = Topic.objects.get_or_create(
                            name=top_name,
                            subject=subject_obj
                        )

                        question_obj, created = Question.objects.get_or_create(
                            topic=topic_obj,
                            text=q_text
                        )

                        if created:
                            choices = [
                                row['choice1'].strip(),
                                row['choice2'].strip(),
                                row['choice3'].strip(),
                                row['choice4'].strip()
                            ]

                            for choice_text in choices:
                                is_correct = (choice_text == ans_text)

                                Choice.objects.create(
                                    question=question_obj,
                                    text=choice_text,
                                    is_correct=is_correct
                                )
                            count += 1

            self.stdout.write(self.style.SUCCESS(
                f"Successfully imported {count} new questions!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))