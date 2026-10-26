"""MiniLMS Application Configuration"""
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use environment secret key; generate a secure random one if missing
    _env_secret = os.getenv('FLASK_SECRET_KEY')
    SECRET_KEY = _env_secret if _env_secret and _env_secret != 'replace_with_a_random_private_string' else secrets.token_hex(32)
    
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'minilms_db')
    TEST_DB_NAME = os.getenv('TEST_DB_NAME', 'minilms_test_db')
    PORT = int(os.getenv('PORT', 5000))
    
    # Demonstration mode security flag: must be explicitly true for 1-click viva switching
    DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() in ('true', '1', 'yes', 'on')
    DEMO_USER_PASSWORD = os.getenv('DEMO_USER_PASSWORD', '')
    
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours

class TestConfig(Config):
    TESTING = True
    DB_NAME = os.getenv('TEST_DB_NAME', 'minilms_test_db')
    DEMO_MODE = False
