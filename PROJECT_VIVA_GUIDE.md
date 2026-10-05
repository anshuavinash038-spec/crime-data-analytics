# 🎓 PROJECT VIVA GUIDE — Crime Data Analytics & Visualization

---

## 1. Quick Project Overview
- **Project Name:** Crime Data Analytics and Visualization System
- **Domain:** Web Development, Data Analytics, Information Security, Business Intelligence
- **Stack:** Python 3.12, Flask, SQLite/MySQL, Plotly.js, ReportLab (PDF), Microsoft Power BI, HTML5/Bootstrap 5

---

## 2. Core Architecture & Tech Explanation

### Q1: Flask Application Architecture kya hai?
**Answer:** Application Factory Pattern (`create_app()`) use karta hai. Sabhi features 10 Blueprints mein modular structured hain (`auth`, `dashboard`, `crime`, `analysis`, `visualization`, `search`, `reports`, `powerbi`, `admin`, `api`).

### Q2: Authentication aur Role-Based Access Control (RBAC) kaise chalta hai?
**Answer:** `Flask-Login` library use karta hai. 
- Password hashing `werkzeug.security.generate_password_hash` (PBKDF2/SHA-256) se hoti hai.
- Admin routes dual protection se secure hain: `@admin_required` decorator + `before_request` hook jo non-admin user ko HTTP 403 Forbidden return karta hai.

### Q3: Database design aur source of truth kya hai?
**Answer:** Single Source of Truth = SQLite database (`database/crime_analytics.db`), jisme **2,52,240 real crime records** hain. `DatabaseService` abstraction layer SQLite aur MySQL dono ko support karti hai.

### Q4: Power BI integration kaise kaam karti hai?
**Answer:** SQLite database se pre-cleaned Excel workbook (`POWERBI_READY_DATA.xlsx`) generate hota hai. Power BI Desktop me is dataset ko connect karke 6 sheets aur dynamic DAX measures se visual dashbaord display hota hai.

---

## 3. Key Calculations & DAX Measures

| Metric | Formula | Explanation |
|--------|---------|-------------|
| **Total Cases** | `SUM(cases_reported)` | Total logged crime instances |
| **Chargesheet Rate %** | `(SUM(chargesheeted) / SUM(cases_reported)) * 100` | % of cases investigated & chargesheeted |
| **Conviction Rate %** | `(SUM(convictions) / SUM(chargesheeted)) * 100` | % of chargesheeted cases resulting in judicial conviction |
| **Avg Crime Rate / 100k** | `(SUM(cases_reported) / SUM(population)) * 100,000` | Population-weighted crime density |

---

## 4. Top 10 Viva Examiner Questions & Answers

1. **Q: Tumne data secure kaise rakha hai?**  
   *A:* Passwords salted hashes mein stored hain. Parameterized queries (`%s` / `?`) use karke SQL injection roka gaya hai. Admin endpoints 403 authorization guarded hain. Secret key `.env` se read hoti hai.

2. **Q: Kya ye real data hai ya fake sample?**  
   *A:* Ye genuine 2,52,240 records ka dataset hai jisme 28 States, 740 Districts, aur 4,125 Areas (Sub-districts) cover hote hain (2021–2025).

3. **Q: Geographical Hierarchy kaise work karti hai?**  
   *A:* `State → District → Area` (Level-3 cascading). State change hone par dynamic API `/api/districts?state=...` hit hoke filtered districts load karti hai.

4. **Q: PDF Report kaise generate hoti hai?**  
   *A:* `ReportLab` Python library canvas drawing aur table layout APIs se server-side dynamic PDF build karti hai.

5. **Q: 28/28 tests passed ka kya matlab hai?**  
   *A:* Pytest test suite app startup, auth, RBAC, DB CRUD, Plotly chart generation, CSV export, PDF download, aur Power BI data export sab automated test karti hai.

---

## 5. Demonstration Steps for Examiner

1. **Step 1:** Show Homepage (`http://127.0.0.1:5000/`)
2. **Step 2:** User Login (`user@crime.local` / `user123`) → Show User Dashboard & Plotly Visualizations
3. **Step 3:** Show Search & Filter (Filter state = *Maharashtra*, year = *2024*)
4. **Step 4:** Show Analytics & Power BI Desktop section
5. **Step 5:** Generate & Download PDF Report
6. **Step 6:** Logout & Admin Login (`admin@crime.local` / `admin123`) → Show Admin Panel, Activity Logs, and User Management
