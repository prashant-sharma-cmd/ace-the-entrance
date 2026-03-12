"""
Management command to import questions from a CSV file into the database.

CSV format expected:
    subject, question, option1, option2, option3, option4, answer, image

    - subject : must match one of PHY, CHE, BIO, MAT, ENG, IQ_GK
    - answer  : a / b / c / d  (case-insensitive)
    - image   : absolute/relative path to an image file, or FALSE if none

Usage:
    python manage.py sxcmodel_import_questions path/to/questions.csv

Options:
    --clear     Delete all existing questions before importing
    --skip-bad  Skip rows with errors instead of stopping (default: stop on error)
    --delimiter Specify CSV delimiter (default: auto-detect)
"""

import csv
import os
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sxcmodel.models import Question

ANSWER_MAP = {'a': 1, 'b': 2, 'c': 3, 'd': 4}

VALID_SUBJECTS = {code for code, _ in Question.SUBJECT_CHOICES}

# Map common alternate subject names → canonical codes
SUBJECT_ALIASES = {
    # Physics
    'physics': 'PHY', 'phy': 'PHY', 'ph': 'PHY',
    # Chemistry
    'chemistry': 'CHE', 'che': 'CHE', 'chem': 'CHE',
    # Biology
    'biology': 'BIO', 'bio': 'BIO',
    # Maths
    'maths': 'MAT', 'math': 'MAT', 'mathematics': 'MAT', 'mat': 'MAT',
    # English
    'english': 'ENG', 'eng': 'ENG',
    # IQ/GK
    'iq_gk': 'IQ_GK', 'iq/gk': 'IQ_GK', 'iq': 'IQ_GK', 'gk': 'IQ_GK',
    'general knowledge': 'IQ_GK', 'iq gk': 'IQ_GK',
}


def resolve_subject(raw: str) -> str:
    """Return canonical subject code or raise ValueError."""
    clean = raw.strip()
    if clean in VALID_SUBJECTS:
        return clean
    alias = SUBJECT_ALIASES.get(clean.lower())
    if alias:
        return alias
    raise ValueError(
        f"Unknown subject '{raw}'. Valid values: {', '.join(sorted(VALID_SUBJECTS))} "
        f"(or aliases like 'Physics', 'Maths', etc.)"
    )


def resolve_answer(raw: str) -> int:
    """Return correct_option integer (1–4) from 'a'/'b'/'c'/'d'."""
    clean = raw.strip().lower()
    if clean not in ANSWER_MAP:
        raise ValueError(f"Invalid answer '{raw}'. Must be a, b, c, or d.")
    return ANSWER_MAP[clean]


def resolve_image(raw: str, csv_dir: Path, row_num: int):
    """
    Return a relative path (str) suitable for ImageField, or None.
    Copies the source image into MEDIA_ROOT/question_diagrams/ if needed.
    """
    clean = raw.strip()
    if not clean or clean.upper() == 'FALSE':
        return None

    # Resolve source path: absolute OR relative to the CSV's directory
    src = Path(clean)
    if not src.is_absolute():
        src = csv_dir / src

    if not src.exists():
        raise FileNotFoundError(
            f"Image not found: '{clean}' (resolved to '{src}')"
        )

    dest_dir = Path(settings.MEDIA_ROOT) / 'sxcmodelset'
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / src.name

    # Copy only if not already there (or sizes differ)
    if not dest.exists() or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)

    # Return the relative path stored in ImageField  e.g. question_diagrams/img.png
    return f'sxcmodelset/{src.name}'


class Command(BaseCommand):
    help = 'Import questions from a CSV file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Path to the CSV file',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            default=False,
            help='Delete ALL existing questions before importing',
        )
        parser.add_argument(
            '--skip-bad',
            action='store_true',
            default=False,
            help='Skip rows with errors and continue (default: abort on first error)',
        )
        parser.add_argument(
            '--delimiter',
            type=str,
            default=None,
            help='CSV delimiter character. Auto-detected if not provided.',
        )

    def handle(self, *args, **options):
        csv_path = Path(options['csv_file']).resolve()

        if not csv_path.exists():
            raise CommandError(f"File not found: {csv_path}")

        if not csv_path.suffix.lower() == '.csv':
            self.stdout.write(self.style.WARNING(
                f"⚠  File does not have a .csv extension — proceeding anyway."
            ))

        csv_dir = csv_path.parent

        # ── Optional: clear existing questions ──────────────────────────────
        if options['clear']:
            count = Question.objects.count()
            Question.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'🗑  Deleted {count} existing questions.'
            ))

        # ── Open and sniff the CSV ───────────────────────────────────────────
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            sample = f.read(4096)

        if options['delimiter']:
            dialect_kwargs = {'delimiter': options['delimiter']}
        else:
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=',\t;|')
                dialect_kwargs = {'dialect': dialect}
            except csv.Error:
                dialect_kwargs = {'delimiter': ','}  # safe fallback

        # ── Expected column names (case-insensitive) ─────────────────────────
        REQUIRED_COLS = {'subject', 'question', 'option1', 'option2', 'option3', 'option4', 'answer', 'image'}

        created = 0
        skipped = 0
        errors = []

        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, **dialect_kwargs)

            # Normalise header names to lowercase & strip whitespace
            if reader.fieldnames is None:
                raise CommandError("CSV file appears to be empty or has no header row.")

            reader.fieldnames = [name.strip().lower() for name in reader.fieldnames]

            missing = REQUIRED_COLS - set(reader.fieldnames)
            if missing:
                raise CommandError(
                    f"Missing required columns: {', '.join(sorted(missing))}\n"
                    f"Found columns: {', '.join(reader.fieldnames)}"
                )

            self.stdout.write(f"\n📂 Importing from: {csv_path}")
            self.stdout.write(f"   Columns detected: {', '.join(reader.fieldnames)}\n")

            for row_num, row in enumerate(reader, start=2):  # row 1 = header
                # Strip whitespace from all values
                row = {k: (v.strip() if v else '') for k, v in row.items()}

                try:
                    subject = resolve_subject(row['subject'])
                    correct_option = resolve_answer(row['answer'])
                    image_path = resolve_image(row['image'], csv_dir, row_num)

                    text = row['question']
                    if not text:
                        raise ValueError("Question text cannot be empty.")

                    o1 = row['option1']
                    o2 = row['option2']
                    o3 = row['option3']
                    o4 = row['option4']

                    if not all([o1, o2, o3, o4]):
                        raise ValueError("All four options must be non-empty.")

                    Question.objects.create(
                        subject=subject,
                        text=text,
                        option_1=o1,
                        option_2=o2,
                        option_3=o3,
                        option_4=o4,
                        correct_option=correct_option,
                        image=image_path or '',
                    )
                    created += 1

                    if created % 10 == 0:
                        self.stdout.write(f'   ✓ {created} questions imported…', ending='\r')
                        self.stdout.flush()

                except (ValueError, FileNotFoundError) as e:
                    msg = f"Row {row_num}: {e}"
                    if options['skip_bad']:
                        errors.append(msg)
                        skipped += 1
                        self.stdout.write(self.style.WARNING(f'   ⚠  Skipping — {msg}'))
                    else:
                        raise CommandError(
                            f"\n❌ Error on {msg}\n\n"
                            f"Row data: {dict(row)}\n\n"
                            f"Use --skip-bad to skip problematic rows and continue."
                        )

        # ── Summary ─────────────────────────────────────────────────────────
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'✅ Done! {created} questions imported successfully.'
        ))
        if skipped:
            self.stdout.write(self.style.WARNING(
                f'⚠  {skipped} rows skipped due to errors:'
            ))
            for err in errors:
                self.stdout.write(f'   • {err}')

        total = Question.objects.count()
        self.stdout.write(f'\n📊 Total questions in database: {total}\n')