"""MiniLMS WSGI Application Entry Point
Exposes standard WSGI callable 'app' and 'application' for production servers
such as Waitress (Windows) and Gunicorn (Linux/POSIX).
"""
import os
import sys
from pathlib import Path

# Ensure application root directory is on the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import create_app
from app.config import Config

# Create application in production mode
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    ENV = 'production'

app = create_app(ProductionConfig)
application = app  # WSGI standard alias

if __name__ == '__main__':
    # Direct fallback runner for development
    app.run(host='127.0.0.1', port=5000, debug=False)
