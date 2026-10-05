# Crime Data Analytics and Visualization

An analytical web application for exploring, visualizing, and reporting on Indian crime statistics across states, districts, and local areas. Built with Python, Flask, SQLite/MySQL, Pandas, Plotly, ReportLab, and Power BI.

---

## 📌 Project Architecture

The system implements a 3-tier geographic hierarchy:
$$\text{State} \longrightarrow \text{District} \longrightarrow \text{Area}$$

### Core Modules:
1. **Interactive Dashboard (`/dashboard`)**: National summary metrics, trend timelines, geographic distributions, and area ranking tables.
2. **Visualizations Studio (`/visualization`)**: Area × Crime Type incidence heatmaps, top affected areas ranking, and chargesheet vs. conviction rate comparative analysis.
3. **Statistical Analytics (`/analytics`)**: District and area comparative analytics, year-over-year rate changes, and crime density indices.
4. **Data Management & Search (`/crime-data`)**: Comprehensive search with multi-parameter filtering, sorting, pagination, and CSV data export.
5. **PDF & Official Reports (`/reports`)**: On-demand server-side PDF generation using ReportLab with tables, key metrics, and date timestamps.
6. **Power BI Studio (`/powerbi`)**: Interactive web-based BI interface with slicers and KPI cards, plus an automated Excel export for Power BI Desktop.
7. **Admin Control Panel (`/admin/dashboard`)**: User account management, record audits, and bulk data operations.

---

## 🛠 Technology Stack

- **Backend Framework**: Python 3.10+ / Flask, Flask-Login, Werkzeug Security
- **Database Layer**: SQLite (default, zero configuration required) with optional MySQL 8.0 support
- **Data Processing**: Pandas, NumPy
- **Interactive Visualizations**: Plotly.js & Python Plotly
- **Document Generation**: ReportLab (PDF), OpenPyXL (Excel)
- **Business Intelligence**: Microsoft Power BI Desktop & In-App BI Studio
- **Frontend**: HTML5, CSS3, JavaScript (Fetch API), Bootstrap 5, FontAwesome 6

---

## 🚀 How to Run in VS Code on Windows

### Option 1: One-Click Startup (Recommended)
Double-click `Run_Project.bat` located in the root directory. It automatically activates your Python environment, verifies dependencies, and starts the server.

### Option 2: Step-by-Step in VS Code Terminal

1. **Open the project folder in VS Code**:
   `File > Open Folder...` -> Select `crime data`.

2. **Open the Integrated Terminal**:
   Press `Ctrl + ~` (or `Terminal > New Terminal`).

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Start the Flask Application**:
   ```powershell
   python app.py
   ```

5. **Open in Browser**:
   Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## 🔐 Login Credentials

| Role | Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Admin** | `avinashmishra8850@gmail.com` | `542542` | Full access, Admin Panel, User Management, CRUD |
| **Admin (Alternative)** | `admin@crime.local` | `admin123` | Backup Administrator account |
| **Standard User** | `user@crime.local` | `user123` | Dashboard, Visualizations, Analytics, Reports, Search |

---

## 🗄️ Database Configuration (SQLite vs MySQL)

The application includes an automatic dual-database engine configured in `.env`:

### Default: SQLite (Ready to use immediately)
No database server installation required. The database file is located at `database/crime_analytics.db` with all 72,480 validated crime records preloaded.
```ini
DB_TYPE=sqlite
DB_NAME=database/crime_analytics.db
```

### Switching to MySQL:
1. Ensure MySQL Server is running.
2. Create the database:
   ```sql
   CREATE DATABASE crime_analytics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
3. Update `.env`:
   ```ini
   DB_TYPE=mysql
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_DB=crime_analytics
   ```
4. Restart `python app.py`. The application will automatically create all tables and seed initial data.

---

## 📊 Power BI Integration

The project provides two seamless methods to analyze crime data with Power BI:

### 1. In-App Power BI Studio
Visit `/powerbi` directly inside the web application for an interactive business intelligence interface featuring:
- Dynamic slicers for State and Year
- Real-time KPI scorecards (Total Cases, Conviction Rate, Chargesheet Rate)
- Pre-built DAX measure definitions and formulas

### 2. External Power BI Desktop
An automated, multi-sheet analytical Excel dataset has been generated at:
`data/powerbi_crime_dataset.xlsx` (and on your Desktop as `CRIME_DATA_POWERBI.xlsx`).

**Data Model Structure**:
- `Crime_Raw_Data`: Full 72,480 records
- `State_Analytics`: State-level aggregations and conviction metrics
- `Crime_Type_Analytics`: Breakdown by 12 IPC categories
- `Yearly_Trends`: 2021–2025 longitudinal metrics
- `DAX_Measures_Reference`: Pre-written DAX formulas ready to paste into Power BI Desktop

**How to Open**:
1. Double-click `Launch_PowerBI_Dashboard.bat` or open Microsoft Power BI Desktop.
2. Select **Get Data > Excel Workbook**.
3. Choose `data/powerbi_crime_dataset.xlsx`.
4. Select all tables and click **Load**.

---

## 🧪 Automated Testing & Data Validation

### Run Full Test Suite (15 Test Cases):
```powershell
python tests/test_full_suite.py
```
Validates routes, role-based access control, database queries, Plotly chart generation, CSV exports, ReportLab PDF generation, and Power BI dataset integrity.

### Run Crime Dataset Audit (72,480 Records):
```powershell
python scripts/validate_crime_data.py
```
Audits row counts, missing values, duplicates, numeric boundaries, states, and crime categories.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/summary` | GET | Returns national KPI summary figures |
| `/api/trends` | GET | Returns longitudinal year-over-year trend data |
| `/api/state-statistics` | GET | Returns state-level aggregated statistics |
| `/api/area-statistics` | GET | Returns area-level ranking and crime figures |
| `/api/crime-types` | GET | Lists unique crime categories |
| `/api/districts/<state>` | GET | Dynamic dropdown: fetches districts for selected state |
| `/api/areas/<district>` | GET | Dynamic dropdown: fetches areas for selected district |
| `/reports/download-pdf` | GET | Generates and downloads official PDF summary report |
| `/crime-data/export` | GET | Exports filtered records as CSV |
| `/powerbi/download-dataset` | GET | Downloads pre-formatted Power BI Excel workbook (Requires Login) |

---

## 🌐 Production Deployment Guide

The project is fully prepared for multi-environment cloud and server deployment:

### 1. Cloud PaaS (Render, Railway, Heroku)
- **WSGI Server**: Pre-configured with `gunicorn` via `Procfile` (`web: gunicorn wsgi:app`).
- **Port Handling**: Dynamically reads `$PORT` provided by cloud hosts.
- **Database**: Automatically detects and parses `DATABASE_URL` (MySQL or SQLite).
- **HTTPS Reverse Proxy**: Integrated with `ProxyFix` middleware for seamless SSL/TLS redirect and IP logging.

### 2. Windows Server / Local Production
- Double-click `Run_Production_Server.bat` to launch with **Waitress** (a multi-threaded, production-grade WSGI server for Windows).

### 3. Docker Deployment
A lightweight multi-stage `Dockerfile` is included:
```bash
docker build -t crime-analytics .
docker run -p 5000:5000 -e SECRET_KEY="your_secret" crime-analytics
```

### 4. Key Production Environment Variables
| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Auto-generated safe)* | Cryptographic session signing key |
| `DATABASE_URL` | *(None)* | Cloud database connection string (`mysql://...`) |
| `DB_TYPE` | `sqlite` | Database engine selector (`sqlite` or `mysql`) |
| `PORT` | `5000` | Port assigned by hosting provider |
| `FLASK_DEBUG` | `False` | Debug mode toggle (Keep `False` in production) |

