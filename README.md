# Ace The Entrance - Backend 

[![Django](https://img.shields.io/badge/Framework-Django%205.0-092e20?logo=django)](https://www.djangoproject.com/) [![Docker](https://img.shields.io/badge/Deployment-Docker-2496ed?logo=docker)](https://www.docker.com/) [![Postgres](https://img.shields.io/badge/Database-PostgreSQL-336791?logo=postgresql)](https://www.postgresql.org/)

**Ace The Entrance** is the backend engine powering Nepal's premier entrance preparation platform. It manages an ecosystem of 3000+ MCQs, automated daily quizzes, and secure user onboarding for students targeting top-tier +2 colleges like St. Xavier's, KMC, and SOS.

**Live Platform:** [acetheentrance.com](https://acetheentrance.com)

---

## Key Features

- **Automated Quiz Engine:** Daily content generation and scheduling via `django-crontab`.
- **Infrastructure:** Containerized with Docker, proxied via Nginx, and cached with Redis.
- **Auto-Configuring:** Automated database migrations and superuser creation on container startup.
- **Security:** Social login (Google/GitHub), SSL/HSTS hardening, and production-ready middleware.

---

## Installation & Setup

### 1. Prerequisites
- Clone the repository:
  ```bash
  git clone https://github.com/prashant-sharma-cmd/ace-the-entrance.git
  cd ace-the-entrance
  ```
- Create your environment file:
  ```bash
  cp .env.example .env
  ```

---

### Option A: Docker Setup (Fully Automated)
This is the recommended way to run the full stack (Django, Postgres, Redis).

1. **Start the application in the background:**
   ```bash
   docker-compose up --build -d
   ```
2. **Verify the logs:**
   ```bash
   docker-compose logs -f web
   ```
*The app will be live at `http://localhost:8000`. Migrations and admin creation happen automatically.*

---

### Option B: Local Development Setup
Use this for running Django directly on your host machine. *Requires local PostgreSQL and Redis.*

1. **Setup Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Run Server:**
   ```bash
   python manage.py migrate
   python manage.py collectstatic --noinput
   python manage.py runserver
   ```

---

## ⚙️ Environment Variables (.env)

The application uses a `.env` file for all secrets. See `.env.example` for the full list of required keys.

| Variable | Description |
|:---|:---|
| `DJANGO_DEBUG` | Set to `True` for local development |
| `DJANGO_ENVIRONMENT` | `development` or `production` |
| `DB_NAME/USER/PASS` | PostgreSQL connection details |
| `REDIS_URL` | Redis endpoint (e.g., `redis://redis:6379/1`) |
| `DJANGO_SUPERUSER_...`| Credentials for automated admin creation |

---

## Data Management & Seeding

After setting up the database, you need to populate the question bank using the built-in management commands and sample CSV files located in the `data/` folder.

### 1. Daily Quiz Import
- **Format:** Comma-separated (`,`)
- **Subjects:** physics, chemistry, biology, maths, english, gkiq
- **Command:**
  ```bash
  # Docker
  docker-compose exec web python manage.py daily_import_questions data/sample-daily-questions.csv
  
  # Local
  python manage.py daily_import_questions data/sample-daily-questions.csv
  ```

### 2. SXC Model Set Import
- **Format:** Semicolon-separated (`;`)
- **Subjects:** PHY, CHE, BIO, MAT, ENG, IQ_GK | **Answers:** a, b, c, d
- **Command:**
  ```bash
  # Docker
  docker-compose exec web python manage.py sxcmodel_import_questions data/sample-sxc-model-set.csv
  
  # Local
  python manage.py sxcmodel_import_questions data/sample-sxc-model-set.csv
  ```

---

## System Architecture

- **Web Server:** Gunicorn managed by Nginx (Reverse Proxy).
- **Task Scheduling:** **Django Crontab** handles daily model set updates at midnight.
- **Static Assets:** Managed via **WhiteNoise** with Gzip compression and browser caching.
- **Email:** Integrated with **Resend** (Anymail) for transactional emails in production.

---

## Contributing & Privacy

We are committed to helping students across Nepal through Open Source.
- **Data Privacy:** Do **not** commit custom question bank CSVs or real `.env` files.
- **Media/Logs:** Files inside `media/` or `logs/` are ignored by Git. Use `MEDIA_ROOT` for dynamic file handling.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---