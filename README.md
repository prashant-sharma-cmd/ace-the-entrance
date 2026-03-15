# Ace The Entrance 🎓

[![Django Version](https://img.shields.io/badge/Django-6.0.2-green.svg)](https://www.djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ace The Entrance** is an open-source web platform designed to help students in Nepal prepare for competitive +2 entrance exams for prestigious institutions like St. Xavier's College (Maitighar), KMC, SOS, and Budhanilkantha. 

This application serves as the digital companion to the "Ace The Entrance" book, providing interactive tools to supplement traditional studying.

## 🚀 Key Features

- **Daily Quiz:** A fresh set of Science, Mathematics, English, and IQ/GK questions every 24 hours to keep the brain sharp.
- **SXC Model Sets:** Full-length, timed (90 mins) simulation exams featuring 100 questions based on past memory-based papers from St. Xavier's College.
- **Discussion Forum:** A community hub for aspirants to post doubts, debate solutions, and share resources.
- **Progress Tracking:** User dashboards to monitor quiz performance and exam readiness.
- **Social Authentication:** Easy sign-in via Google, GitHub, and Twitter (powered by `django-allauth`).
- **Automated Scheduling:** Daily quiz resets and updates via `django-crontab`.

## 🛠️ Tech Stack

- **Backend:** [Django 6.0.2](https://docs.djangoproject.com/en/5.0/) (The web framework for perfectionists with deadlines)
- **Database:** [PostgreSQL](https://www.postgresql.org/)
- **Caching/Task Queue:** [Redis](https://redis.io/)
- **Frontend:** Django Templates with Custom CSS & JavaScript.
- **Static Files:** [WhiteNoise](https://whitenoise.readthedocs.io/) (for serving files efficiently in production).

---

## 💻 Local Development Setup

To get this project running on your local machine, follow these steps:

### 1. Prerequisites
- Python 3.12+
- PostgreSQL installed and running
- Redis installed and running

### 2. Clone the Repository
```bash
git clone https://github.com/prashant-sharma-cmd/ace-the-entrance.git
cd ace-the-entrance
```

### 3. Setup Virtual Environment
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Mac/Linux:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Variables
Create a `.env` file in the project root and add your credentials (refer to `config/settings.py` for required keys):
```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DJANGO_ENVIRONMENT=development

DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=127.0.0.1
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1

# Optional: Email & OAuth
EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
OAUTH_GOOGLE_CLIENT_ID=your-id
OAUTH_GOOGLE_CLIENT_SECRET=your-secret
```

### 6. Initialize Database
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run the Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000` to see the app!

---

## 📁 Project Structure

```text
ace-the-entrance/
├── accounts/       # Custom user models and profiles
├── daily/          # Daily quiz logic and question bank
├── sxcmodel/       # Mock exam engine and timers
├── discussion/     # Community forum and comments logic
├── home/           # Landing pages and contact forms
├── config/         # Project settings and URL routing
├── static/         # Global CSS, JS, and Images
├── media/          # User-uploaded content (Profile pics, etc.)
└── manage.py
```

---

## 🤝 Contributing (Open Source)

We believe in accessible education for all students in Nepal. Contributions are welcome! 

1. **Fork** the Project.
2. Create your **Feature Branch** (`git checkout -b feature/AmazingFeature`).
3. **Commit** your Changes (`git commit -m 'Add some AmazingFeature'`).
4. **Push** to the Branch (`git push origin feature/AmazingFeature`).
5. Open a **Pull Request**.

### Upcoming Roadmap:
- [ ] Integration of Celery for background email processing.
- [ ] Leaderboard system for top-performing students.
- [ ] Dark mode support for late-night studying.
- [ ] PDF generation for model set results.

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

## ✍️ Authors

- **Prashant Sharma** - *Lead Developer & Author* - [@prashant-sharma-cmd](https://github.com/prashant-sharma-cmd)
- **Ace The Entrance Team** - St. Xavier's Alumni and Medical Students.