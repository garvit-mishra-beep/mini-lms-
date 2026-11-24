# Security Policy

## Supported Versions

The following table indicates which versions of MiniLMS currently receive security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

We take the security and integrity of MiniLMS seriously. If you discover a security vulnerability, please report it responsibly by following these steps:

1. **Do not create a public GitHub issue.** Public issues expose the vulnerability before a remediation can be released.
2. Email the maintainers directly at **security-advisory@minilms.org** (or contact the project administrator).
3. Include detailed information about the vulnerability:
   - Type of vulnerability (e.g., SQL Injection, Privilege Escalation, XSS, CSRF).
   - Step-by-step reproduction instructions or proof-of-concept.
   - Affected components, routes, or database objects.
   - Potential impact of exploitation.
4. You will receive an initial response acknowledging receipt within 48 hours.
5. Once a fix has been verified, a security patch will be released along with appropriate attribution.

---

## Security Best Practices for Deployment

- Never run the application with default credentials or `FLASK_ENV=development` in production.
- Always change default database passwords and `SECRET_KEY` in your `.env` file before deploying.
- Ensure MySQL 8.0 is bound only to `localhost` or private VPC interfaces.
- Deploy behind an SSL/TLS terminating reverse proxy (such as Nginx).
