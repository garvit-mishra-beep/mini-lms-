# MiniLMS Deployment Guide

This directory contains production deployment configurations for MiniLMS:

- `Dockerfile`: Multi-stage, security-hardened container specification running Gunicorn.
- `docker-compose.yml`: Local orchestrator provisioning MySQL 8.0 and the MiniLMS Flask web service.
- `nginx.conf`: Reverse proxy configuration handling static asset caching, request buffering, and SSL termination.
- `systemd/minilms.service`: Linux systemd unit definition for bare-metal or VM hosting.

## Quick Docker Launch

```bash
docker-compose -f deployment/docker-compose.yml up -d
```
