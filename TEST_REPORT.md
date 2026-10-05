# TEST REPORT — Crime Data Analytics & Visualization
**Date:** 2026-10-04 | **Python:** 3.12.10 | **pytest:** 9.1.1

---

## Test Suite: tests/test_full_suite.py

Run command: `python -m pytest tests/test_full_suite.py -v`

| # | Test Name | Description | Result | Time |
|---|-----------|-------------|--------|------|
| 1 | test_01_homepage_status | Homepage loads with HTTP 200 | PASS | - |
| 2 | test_02_powerbi_requires_authentication | Power BI redirects unauthenticated users | PASS | - |
| 3 | test_03_login_page_renders | Login page renders form | PASS | - |
| 4 | test_04_user_login_success | Normal user login → /dashboard redirect | PASS | - |
| 5 | test_05_admin_login_success | Admin login → /admin/dashboard redirect | PASS | - |
| 6 | test_06_unauthorized_admin_access_blocked | Normal user gets 403 on admin route | PASS | - |
| 7 | test_07_authorized_admin_access_allowed | Admin can access /admin/dashboard | PASS | - |
| 8 | test_08_crime_summary_statistics | DB stats populated and valid | PASS | - |
| 9 | test_09_crime_filters_query | Maharashtra filter returns correct records | PASS | - |
| 10 | test_10_dashboard_charts_generation | Plotly chart JSON valid (data + layout keys) | PASS | - |
| 11 | test_11_csv_export_endpoint | CSV export returns 200 + text/csv | PASS | - |
| 12 | test_12_pdf_report_generation | ReportService generates valid PDF file | PASS | - |
| 13 | test_13_pdf_download_endpoint | /reports/download-pdf returns application/pdf | PASS | - |
| 14 | test_14_powerbi_dataset_download | /powerbi/download-dataset returns >100KB file | PASS | - |
| 15 | test_15_404_error_page | Custom 404 page shown for invalid routes | PASS | - |

**TOTAL: 15 PASSED | 0 FAILED | 0 SKIPPED**  
**Total Runtime: 57.40 seconds**

---

## Test Coverage Areas

| Area | Covered |
|------|---------|
| Application startup | YES |
| Public homepage | YES |
| Login page rendering | YES |
| User authentication | YES |
| Admin authentication | YES |
| Role-based authorization | YES |
| Admin route protection (403) | YES |
| Database CRUD stats | YES |
| Filter queries | YES |
| Plotly chart generation | YES |
| CSV export | YES |
| PDF generation | YES |
| PDF download | YES |
| Power BI file download | YES |
| 404 error handling | YES |

## NOT YET Covered (Recommendations)

| Area | Recommended Test |
|------|-----------------|
| Registration form validation | Test empty fields, short password, duplicate email |
| State-District-Area cascade API | Test /api/districts?state=Maharashtra |
| Admin CRUD: add/edit/delete record | Test POST to /admin/data/add |
| Admin user management | Test enable/disable user |
| Invalid login attempts | Test wrong password, inactive user |
| Year filter on charts | Test filter=2023 changes chart data |
| Password change | Test /profile/change-password |
| Password reset flow | Test token generation and expiry |
