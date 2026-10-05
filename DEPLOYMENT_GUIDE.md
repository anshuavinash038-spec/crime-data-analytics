# DEPLOYMENT GUIDE — Crime Data Analytics & Visualization

---

## Local Setup

### Requirements
- Python 3.10+
- pip
- (Optional) virtualenv

### Steps

```bash
# 1. Go to project folder
cd "c:\Users\avinash mishra\Downloads\crime data"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment (copy and edit)
copy .env.example .env
# Edit .env: set your SECRET_KEY, and optionally ADMIN_EMAIL/ADMIN_PASSWORD

# 4. Run the app
python app.py
# Open http://127.0.0.1:5000
```

Default credentials (dev only, change immediately):
- Admin: admin@crime.local / admin123
- User: user@crime.local / user123

---

## Cloud Deployment — Railway

### 1. Required Files (already present)
- `wsgi.py` — WSGI entry point
- `Procfile` — Process configuration
- `requirements.txt` — Dependencies

### 2. Deploy Steps

1. Push project to GitHub (make sure `.env` is in `.gitignore`)
2. Go to https://railway.app → New Project → Deploy from GitHub
3. Select your repository
4. Set Environment Variables in Railway dashboard:

```
SECRET_KEY=<generate a random 32-char string>
DB_TYPE=sqlite
FLASK_DEBUG=False
SESSION_COOKIE_SECURE=True
ADMIN_EMAIL=your-email@example.com
ADMIN_NAME=Your Name
ADMIN_PASSWORD=your-secure-password
```

5. Railway will auto-detect `Procfile` and start the app
6. Add a Persistent Volume for the database:
   - Mount path: `/app/database`
   - This keeps your SQLite DB between deployments

### 3. Important Production Settings

```python
# These MUST be set via env vars in production:
SECRET_KEY=<strong-random-key>          # Never use the default
SESSION_COOKIE_SECURE=True              # Requires HTTPS
FLASK_DEBUG=False                       # Never enable in production
```

---

## Cloud Deployment — Render

1. Create account at https://render.com
2. New Web Service → Connect GitHub repo
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `gunicorn wsgi:app`
5. Add environment variables (same as Railway above)
6. Add Persistent Disk:
   - Mount Path: `/opt/render/project/src/database`
   - Update `SQLITE_PATH` env var to match

---

## Power BI Data Refresh

When database data changes:

```bash
# Step 1: Regenerate Excel workbook
python scripts/prepare_powerbi_dataset.py

# Step 2: In Power BI Desktop
# Home → Transform Data → Data Source Settings → Change Source
# Select: data/powerbi_crime_dataset.xlsx
# Click Home → Refresh
```

---

## Database Backup

```bash
# Manual backup
copy "database\crime_analytics.db" "database\backup_YYYYMMDD.db"

# Automated (PowerShell)
$date = Get-Date -Format "yyyyMMdd"
Copy-Item "database\crime_analytics.db" "database\backup_$date.db"
```

---

## Running Tests

```bash
python -m pytest tests/test_full_suite.py -v
```

Expected: 15/15 PASSED

---

## Rollback Procedure

If deployment fails:
1. Stop the running instance
2. Restore database from backup: `copy backup_YYYYMMDD.db crime_analytics.db`
3. Revert code to last working git commit: `git revert HEAD`
4. Redeploy

---

## Gunicorn Command

```bash
gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

---

## Health Check

Route: `GET /` — Returns 200 if app is running normally.
