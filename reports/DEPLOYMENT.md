Deployment Guide
================

## 🚀 Deploying on Render (render.com) - Step-by-Step

AutoIntel AI is configured with production-ready settings (`render.yaml`, `gunicorn`, dynamic `$PORT` binding, and automatic SQLite/PostgreSQL/MySQL database fallback).

### Method 1: 1-Click Blueprint (Recommended)

1. Sign up or log in to **[Render](https://dashboard.render.com/)**.
2. Click **New +** in the top right and select **Blueprint**.
3. Connect your GitHub account and select your repository: `https://github.com/ElipeNiharika/AutoIntel-AI`.
4. Render will automatically detect [`render.yaml`](file:///c:/AI_Vehicle_Service_Repair_Insurance_Intelligence/render.yaml):
   - **Name**: `autointel-ai`
   - **Runtime**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT`
   - **Plan**: `Free`
5. Click **Apply**.
6. Render will build and deploy the web service. Once finished, your live URL will be active (e.g. `https://autointel-ai.onrender.com`).

---

### Method 2: Manual Web Service Setup

If you prefer to configure manually on Render without Blueprints:
1. Go to **[Render Dashboard](https://dashboard.render.com/)** -> **New +** -> **Web Service**.
2. Select your repository: `https://github.com/ElipeNiharika/AutoIntel-AI`.
3. Configure the following fields:
   - **Name**: `autointel-ai`
   - **Region**: Any (e.g. `Oregon (US West)` or `Frankfurt (EU Central)`)
   - **Branch**: `main`
   - **Root Directory**: (Leave blank)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --upgrade pip && pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     gunicorn app:app --workers 1 --threads 4 --timeout 120 --bind 0.0.0.0:$PORT
     ```
   - **Instance Type**: `Free`
4. Under **Environment Variables**, add:
   - `PYTHON_VERSION`: `3.10.13`
   - `FLASK_SECRET`: `your-random-secret-key-here`
   - *(Optional)* `DATABASE_URL`: If using Render's PostgreSQL or an external MySQL database. (If omitted, the app will automatically run on SQLite).
5. Click **Create Web Service**.

---

## 🐳 Docker Deployment

1. Build and start services:
```bash
docker-compose up --build
```
2. The Flask app will be available at `http://localhost:5000` and MySQL at `localhost:3306`.

---

## 🔑 Default Accounts (Initial Login)
- **Administrator**: `admin@autointel.ai` / `Admin@123`
- **Technician**: `technician@autointel.ai` / `Technician@123`
