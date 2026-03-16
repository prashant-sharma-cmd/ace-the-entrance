#!/bin/bash
# entrypoint.sh

set -e

echo "Waiting for the PostgreSQL database to be ready..."
while ! python manage.py check --database default > /dev/null 2>&1; do
  echo "Database unavailable, waiting 2 seconds..."
  sleep 2
done

echo "Database is up! Running migrations..."
python manage.py migrate --noinput

echo "Importing default data..."
python manage.py daily_import_questions data/sample-daily-questions.csv || true
python manage.py sxcmodel_import_questions data/sample-sxc-model-set.csv || true

echo "Creating superuser if not exists..."
python manage.py shell -c "
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme')
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'Superuser {username} created.')
"

echo "Starting the application server..."
exec "$@"