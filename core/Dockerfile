FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt is now accessible because context is the root
COPY requirements.txt /app/

RUN pip install --upgrade pip \
    && pip install -r requirements.txt gunicorn

# Copy everything from root into /app
COPY . /app/

# entrypoint.sh is now at /app/core/entrypoint.sh
RUN chmod +x /app/core/entrypoint.sh

# Switch to the subfolder where manage.py lives
WORKDIR /app/core

EXPOSE 8000

ENTRYPOINT ["/app/core/entrypoint.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]