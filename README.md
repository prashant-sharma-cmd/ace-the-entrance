
# Ace The Entrance (Nepal) 🇳🇵

[![Django Version](https://img.shields.io/badge/Django-6.0.2-green.svg)](https://www.djangoproject.com/)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Ace The Entrance** is an open-source web platform designed to help students in Nepal prepare for competitive +2 entrance exams for prestigious institutions like **St. Xavier's College (Maitighar)**, KMC, SOS, and Budhanilkantha.

This application is the digital companion to the "Ace The Entrance" book, providing interactive tools to supplement traditional study methods.

---

## 🚀 Key Features

- **Daily Questions:** A fresh set of Science, Mathematics, English, and IQ/GK questions every 24 hours to train speed and accuracy.
- **SXC Model Sets:** Full-length, 100-question timed (90 mins) simulation exams based on actual past entrance papers.
- **Discussion Forum:** A community hub for aspirants to brainstorm solutions, debate answers, and share resources.
- **Entrance Updates:** Stay informed with the latest notices regarding exam dates, admission criteria, and scholarship news.

## 🛠️ Tech Stack

- **Backend:** Django 6.0.2 (PostgreSQL as the database)
- **Caching:** Redis (used for caching and session management)
- **Frontend:** Django Templates with vanilla CSS and JavaScript
- **Server:** Gunicorn + Nginx (intended for VPS deployment)
- **Auth:** `django-allauth` for social (Google) and local authentication.

---

## 📁 Project Structure

```text
ace-the-entrance/
├── .venv/                  # Virtual Environment
├── ace-the-entrance/       # Source Code Root
│   ├── about/              # Information about the book and authors
│   ├── accounts/           # User models, profiles, and onboarding
│   ├── buy/                # Book purchase and distribution logic
│   ├── config/             # Django settings and core URL routing
│   ├── daily/              # Daily Quiz app (Command: daily_import_questions)
│   ├── data/               # CSV templates and topics.json reference
│   ├── discussion/         # Forum, Threads, and Replies logic
│   ├── home/               # Landing page and contact forms
│   ├── logs/               # Application logs (Git-ignored)
│   ├── media/              # User-uploaded images (Git-ignored content)
│   ├── sxcmodel/           # Mock exam engine (Command: sxcmodel_import_questions)
│   ├── tos/                # Terms of Service and Privacy Policy
│   ├── updates/            # News and announcements for students
│   ├── manage.py           # Django CLI
│   └── .env                # Secrets and environment variables
└── requirements.txt        # Python dependencies
```

---

## 💻 Local Installation

### 1. Prerequisites
- Python 3.12+
- PostgreSQL
- Redis Server

### 2. Setup Environment
```bash
git clone https://github.com/prashant-sharma-cmd/ace-the-entrance.git
cd ace-the-entrance
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the `ace-the-entrance/` source root:
```env
DJANGO_SECRET_KEY='your-secret-key'
DJANGO_DEBUG=True
DJANGO_ENVIRONMENT=development

DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=127.0.0.1
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/1
```

---

## 📊 Importing Question Data

Populate the database using the built-in management commands and the sample CSV files located in the `data/` folder.

### Daily Quiz Import
- **Command:** `python manage.py daily_import_questions data/sample-daily-questions.csv`
- **Format:** Comma-separated (`,`)
- **Subjects:** `physics`, `chemistry`, `biology`, `maths`, `english`, `gkiq`

### SXC Model Set Import
- **Command:** `python manage.py sxcmodel_import_questions data/sample-sxc-model-set.csv`
- **Format:** Semicolon-separated (`;`)
- **Subjects:** `PHY`, `CHE`, `BIO`, `MAT`, `ENG`, `IQ_GK`
- **Answers:** Stored as letters (`a`, `b`, `c`, `d`).

---

## 🤝 Contributing

We are committed to keeping this project **Open Source** to help students across Nepal.

- **Data Privacy:** Do not commit your question bank CSVs or personal `.env` files.
- **Media:** Always use the `MEDIA_ROOT` for file handling; never commit files inside the `media/` or `logs/` directories.

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---