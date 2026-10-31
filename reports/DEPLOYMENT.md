Deployment Guide
================

Local Docker (recommended):
1. Build and start services:
```bash
docker-compose up --build
```
2. The Flask app will be available at `http://localhost:5000` and MySQL at `localhost:3306`.

Cloud (example):
- Push image to container registry and run behind a load balancer. Ensure `MYSQL_URL` env var points to a managed MySQL instance.

Systemd (bare VM):
- Create a systemd unit to start the Docker Compose stack, or install Python and run the Flask app via Gunicorn with a reverse proxy (Nginx).

Notes:
- Set `FLASK_SECRET` to a secure value in production.
- Configure TLS via reverse proxy.
