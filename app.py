"""MiniLMS: Full-Stack Learning Management System for MySQL 8 minilms_db.
Entry point for Windows batch scripts and Python execution.
"""
from app import create_app
from app.config import Config
from app.db import fetch_all, fetch_one, scalar, execute_query, call_proc

app = create_app()

if __name__ == '__main__':
    print(f"Starting MiniLMS upgraded platform on http://127.0.0.1:{Config.PORT}...")
    app.run(host='127.0.0.1', port=Config.PORT, debug=False)
