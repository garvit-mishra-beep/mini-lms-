"""File upload security service for MiniLMS.
Provides strict file validation:
  1. Whitelisted file extensions
  2. Safe filename sanitization (guarding against path traversal and null bytes)
  3. Maximum file size enforcement (10 MB limit)
  4. Explicit rejection of executable/script extensions (.exe, .php, .py, .sh, .bat, .js)
"""
import os
import re
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'csv', 'zip', 'png', 'jpg', 'jpeg'}
DANGEROUS_EXTENSIONS = {'exe', 'php', 'py', 'sh', 'bat', 'cmd', 'js', 'jsp', 'vbs', 'ps1', 'cgi', 'pl'}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 # 10 MB

def is_extension_allowed(filename: str) -> bool:
    """Check if the filename has an allowed safe extension."""
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS

def validate_file_upload(filename: str, file_size_bytes: int = 0) -> tuple[bool, str]:
    """Validate uploaded file attributes.
    Returns: (is_valid: bool, sanitized_name_or_error_msg: str)
    """
    if not filename or not filename.strip():
        return False, "ERROR: Filename cannot be empty."

    # Guard against null bytes
    if '\x00' in filename:
        return False, "SECURITY_VIOLATION: Null byte injection detected in filename."

    # Guard against directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        # We sanitize, but flag blatant traversal attempts
        sanitized = secure_filename(filename)
        if not sanitized:
            return False, "SECURITY_VIOLATION: Path traversal attempted; filename invalid."
    else:
        sanitized = secure_filename(filename)

    if not sanitized:
        return False, "ERROR: Invalid filename after security sanitization."

    ext = sanitized.rsplit('.', 1)[1].lower() if '.' in sanitized else ''
    if ext in DANGEROUS_EXTENSIONS:
        return False, f"SECURITY_VIOLATION: Executable or script extension '.{ext}' is strictly prohibited."

    if ext not in ALLOWED_EXTENSIONS:
        return False, f"ERROR: Extension '.{ext}' is not permitted. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}."

    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
        return False, f"ERROR: File size exceeds the maximum limit of {max_mb} MB."

    return True, sanitized
