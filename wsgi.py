"""Entry point for gunicorn: gunicorn wsgi:app"""
from app.api import create_app

app = create_app()
