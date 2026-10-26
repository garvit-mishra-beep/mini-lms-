"""Authentication User Model integrating with Flask-Login and MySQL users table."""
from flask_login import UserMixin
from werkzeug.security import check_password_hash
from app.db import fetch_one

class User(UserMixin):
    def __init__(self, user_dict):
        self.id = user_dict['user_id']
        self.user_id = user_dict['user_id']
        self.full_name = user_dict['full_name']
        self.email = user_dict['email']
        self.password_hash = user_dict['password_hash']
        self.role = user_dict['role']
        self.status = user_dict['status']
        self.student_id = user_dict.get('student_id')
        self.teacher_id = user_dict.get('teacher_id')

    @property
    def is_active(self):
        return self.status == 'ACTIVE'

    @property
    def is_admin(self):
        return self.role == 'ADMIN'

    @property
    def is_teacher(self):
        return self.role == 'TEACHER'

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_id(cls, user_id):
        row = fetch_one("""
            SELECT u.user_id, u.full_name, u.email, u.password_hash, u.role, u.status,
                   s.student_id, t.teacher_id
            FROM users u
            LEFT JOIN students s ON s.user_id = u.user_id
            LEFT JOIN teachers t ON t.user_id = u.user_id
            WHERE u.user_id = %s
        """, (user_id,))
        return cls(row) if row else None

    @classmethod
    def get_by_email(cls, email):
        row = fetch_one("""
            SELECT u.user_id, u.full_name, u.email, u.password_hash, u.role, u.status,
                   s.student_id, t.teacher_id
            FROM users u
            LEFT JOIN students s ON s.user_id = u.user_id
            LEFT JOIN teachers t ON t.user_id = u.user_id
            WHERE LOWER(u.email) = LOWER(%s)
        """, (email,))
        return cls(row) if row else None
