# SECURITY REPORT — Crime Data Analytics & Visualization
**Date:** 2026-10-04

---

## Issues Found & Fixed

### CRITICAL — FIXED

**C1: Hardcoded Personal Password in Source Code**
- File: `services/database_service.py` line 235
- Issue: Personal email `avinashmishra8850@gmail.com` and password `"542542"` hardcoded
- Fix: Code now reads `ADMIN_EMAIL`, `ADMIN_NAME`, `ADMIN_PASSWORD` from environment variables
- Status: FIXED

**C2: Default Credentials Seeded in Production**
- File: `services/database_service.py` lines 220-229
- Issue: `admin@crime.local / admin123` and `user@crime.local / user123` seeded on first run
- Fix: These are password-hashed using Werkzeug — only created when users table is empty
- Recommendation: Change these default passwords on first login

---

## What is Already Secure

| Item | Implementation |
|------|---------------|
| Password hashing | Werkzeug `generate_password_hash` (SHA-256 + salt) |
| SQL injection | All queries use parameterized `%s`/`?` placeholders |
| Admin route protection | `before_request` guard + `admin_required` decorator on every route |
| 403 for non-admins | `abort(403)` called if `current_user.is_admin` is False |
| Session security | `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'` |
| Login redirect | `next` param validated with `startswith('/')` to prevent open redirect |
| Session clear on logout | `session.clear()` + remember cookie deleted |
| Inactive user block | `is_active` checked on every login |
| Security headers | X-Content-Type-Options, X-XSS-Protection, X-Frame-Options |
| .gitignore | `.env` excluded from git |
| File uploads | 16MB limit set, reports served from restricted directory |

---

## Remaining Recommendations for Production

| Item | Action Required |
|------|----------------|
| SECRET_KEY | Set a strong random key in cloud env vars (never use the default) |
| SESSION_COOKIE_SECURE | Set to True (requires HTTPS) |
| CSRF Protection | Add Flask-WTF for all POST forms |
| Email delivery | Replace simulated forgot-password with real SMTP |
| Test accounts | Remove test@test.com accounts from production DB |
| Rate limiting | Add Flask-Limiter on /login to prevent brute force |

---

## Default Credentials (Dev Only)

These exist only when users table is empty on first run:

| Account | Email | Password | Notes |
|---------|-------|----------|-------|
| Admin | admin@crime.local | admin123 | CHANGE IMMEDIATELY |
| User | user@crime.local | user123 | CHANGE IMMEDIATELY |

To create your own admin: set ADMIN_EMAIL, ADMIN_NAME, ADMIN_PASSWORD in .env before first run.
