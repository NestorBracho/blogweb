# Nestor Bracho – Personal Blog

A minimalist, SEO-optimized personal blog built with **Django**, supporting:
- Markdown-based posts
- Code highlighting with copy buttons
- SQLite for low-cost hosting
- Full-text Spanish & English content
- Deployed on **AWS Lightsail** with Gunicorn + Nginx + HTTPS

---

## 🔍 Features

- 🔥 Django backend for flexibility and scalability
- 📝 Blog post creation in Markdown
- 🧠 Syntax highlighting with Pygments + clipboard copy buttons
- 💡 Dynamic meta tags for SEO and social sharing (Open Graph + Twitter Cards)
- 🌐 Multi-language support (EN / ES)
- 🔒 HTTPS with Certbot on Nginx
- 🚀 One-click deployment on AWS Lightsail

---

## ✨ Quick Start (Dev)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (runtime + ruff, coverage)
pip install -r requirements-dev.txt
pre-commit install  # optional: run ruff on every commit

# Configure: set SECRET_KEY and DEBUG=True
cp .env.example .env

# Setup database
python manage.py migrate
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## ✅ Checks

The same checks run in GitHub Actions on every push and pull request:

```bash
ruff check .
ruff format --check .
coverage run manage.py test && coverage report
```
