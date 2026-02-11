from django.core.management.base import BaseCommand
from daily.script import generate_daily_quiz

class Command(BaseCommand):
    help = 'Generates the 10 questions for today'

    def handle(self, *args, **kwargs):
        quiz = generate_daily_quiz()
        if quiz:
            self.stdout.write(self.style.SUCCESS('Successfully generated today\'s quiz'))
        else:
            self.stdout.write(self.style.WARNING('No questions available to generate quiz'))