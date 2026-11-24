# MiniLMS Production Deployment Guide

This directory contains production deployment configurations, container definitions, and reverse proxy specifications for the **MiniLMS** platform.

---

## Deployment Options

### 1. Docker Compose (Multi-Container Orchestration)

The quickest method to deploy MiniLMS in an isolated environment with containerized MySQL 8.0:

```bash
# From repository root
docker-compose -f deployment/docker-compose.yml up -d --build
```

- **Web Application**: Exposed on port `5000` (`http://localhost:5000`)
- **MySQL Server**: Running on internal network port `3306` with persistent volume `mysql_data`
- **Health Check**: Automated container health probe at `http://localhost:5000/auth/login`

To view container logs:
```bash
docker-compose -f deployment/docker-compose.yml logs -f
```

To stop containers:
```bash
docker-compose -f deployment/docker-compose.yml down
```

---

### 2. Bare-Metal / Linux VM Deployment (Gunicorn + Systemd)

For deploying on Ubuntu/Debian Linux servers:

#### Step 1: Install System Dependencies
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip mysql-server nginx
```

#### Step 2: Set Up Directory & Virtual Environment
```bash
sudo mkdir -p /opt/minilms
sudo cp -r . /opt/minilms/
cd /opt/minilms
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt gunicorn
```

#### Step 3: Install & Enable Systemd Service
```bash
sudo cp deployment/systemd/minilms.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable minilms
sudo systemctl start minilms
sudo systemctl status minilms
```

---

### 3. Nginx Reverse Proxy Configuration

Nginx acts as the front-facing web server handling SSL termination, static file serving, and request buffering:

```bash
# Copy site configuration
sudo cp deployment/nginx.conf /etc/nginx/sites-available/minilms
sudo ln -s /etc/nginx/sites-available/minilms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

Static assets are served directly by Nginx from `/app/app/static/` with a 30-day cache header, offloading static requests from the Python WSGI workers.

---

## Production Security Checklist

1. **Database Password**: Never deploy with default MySQL root passwords. Always set a strong password in `.env`.
2. **Flask Secret Key**: Generate a 64-character cryptographic random string:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. **Debug Mode**: Ensure `DEBUG=False` in production (enforced automatically in `wsgi.py`).
4. **Firewall**: Restrict MySQL port `3306` to localhost (`127.0.0.1`) or private VPC interfaces only.
