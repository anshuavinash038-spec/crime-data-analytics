import os
import sys
import unittest
import json

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import Config
from models.user_model import User
from models.crime_model import CrimeModel
from services.database_service import DatabaseService
from services.visualization_service import VisualizationService
from services.report_service import ReportService
from werkzeug.security import generate_password_hash

class FullProjectTestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config['TESTING'] = True
        cls.app.config['WTF_CSRF_ENABLED'] = False

        # Create guaranteed test user accounts
        DatabaseService.execute_query(
            "DELETE FROM users WHERE email IN ('suite_admin@test.com', 'suite_user@test.com')",
            fetch_all=False
        )

        User.create_user("Suite Admin", "suite_admin@test.com", "AdminPass123!", role="ADMIN")
        User.create_user("Suite User", "suite_user@test.com", "UserPass123!", role="USER")

    def setUp(self):
        self.client = self.app.test_client()

    # --- 1. App Startup & Public Routes ---
    def test_01_homepage_status(self):
        """Verify homepage loads with HTTP 200"""
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Crime Data Analytics', res.data)

    def test_02_powerbi_requires_authentication(self):
        """Verify Power BI page redirects unauthenticated users to login"""
        res = self.client.get('/powerbi')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

        # Once logged in, Power BI page is accessible
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=True)
            auth_res = self.client.get('/powerbi')
            self.assertEqual(auth_res.status_code, 200)
            self.assertIn(b'Power BI', auth_res.data)

    def test_03_login_page_renders(self):
        """Verify login page displays form"""
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Sign In', res.data)

    # --- 2. Authentication & Authorization ---
    def test_04_user_login_success(self):
        """Verify normal user login redirects to dashboard"""
        with self.client:
            res = self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/dashboard', res.headers.get('Location', ''))

    def test_05_admin_login_success(self):
        """Verify admin user login redirects to admin dashboard"""
        with self.client:
            res = self.client.post('/login', data={
                'email': 'suite_admin@test.com',
                'password': 'AdminPass123!'
            }, follow_redirects=False)
            self.assertEqual(res.status_code, 302)
            self.assertIn('/admin/dashboard', res.headers.get('Location', ''))

    def test_06_unauthorized_admin_access_blocked(self):
        """Verify normal user gets 403 Forbidden when trying to access admin panel"""
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=True)
            res = self.client.get('/admin/dashboard')
            self.assertEqual(res.status_code, 403)
            self.assertIn(b'403 Forbidden', res.data)

    def test_07_authorized_admin_access_allowed(self):
        """Verify admin user successfully accesses admin dashboard"""
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_admin@test.com',
                'password': 'AdminPass123!'
            }, follow_redirects=True)
            res = self.client.get('/admin/dashboard')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b'Admin', res.data)

    # --- 3. Database & Crime Model Aggregations ---
    def test_08_crime_summary_statistics(self):
        """Verify database summary statistics are populated and valid"""
        stats = CrimeModel.get_summary_stats()
        self.assertIsInstance(stats, dict)
        self.assertGreater(stats.get('total_cases', 0), 0)
        self.assertGreater(stats.get('total_states', 0), 0)
        self.assertGreater(stats.get('total_districts', 0), 0)

    def test_09_crime_filters_query(self):
        """Verify querying crime records with filters works properly"""
        records = CrimeModel.get_all(filters={'state': 'Maharashtra'}, limit=10)
        self.assertIsInstance(records, list)
        for r in records:
            self.assertEqual(r['state'], 'Maharashtra')

    # --- 4. Visualizations & Chart Services ---
    def test_10_dashboard_charts_generation(self):
        """Verify chart service generates valid Plotly JSON structures"""
        charts = VisualizationService.get_dashboard_charts()
        self.assertIn('chart_year', charts)
        self.assertIn('chart_crime_type', charts)
        self.assertIn('chart_state', charts)
        # Parse JSON to confirm valid chart payload
        year_chart_obj = json.loads(charts['chart_year'])
        self.assertIn('data', year_chart_obj)
        self.assertIn('layout', year_chart_obj)

    # --- 5. Export & Report Services ---
    def test_11_csv_export_endpoint(self):
        """Verify CSV export endpoint returns valid CSV content"""
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=True)
            res = self.client.get('/crime-data/export')
            self.assertEqual(res.status_code, 200)
            self.assertIn('text/csv', res.headers.get('Content-Type', ''))
            self.assertTrue(b'Cases_Reported' in res.data or b'cases_reported' in res.data)

    def test_12_pdf_report_generation(self):
        """Verify server-side ReportLab PDF report generation creates valid PDF"""
        pdf_filename = ReportService.generate_pdf_report(filters={'state': 'Gujarat'})
        self.assertTrue(pdf_filename.endswith('.pdf'))
        pdf_path = os.path.join(Config.REPORTS_DIR, pdf_filename)
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 1000)

    def test_13_pdf_download_endpoint(self):
        """Verify /reports/download-pdf returns application/pdf"""
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=True)
            res = self.client.get('/reports/download-pdf')
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.headers.get('Content-Type'), 'application/pdf')

    def test_14_powerbi_dataset_download(self):
        """Verify /powerbi/download-dataset serves the dataset file when authenticated"""
        with self.client:
            self.client.post('/login', data={
                'email': 'suite_user@test.com',
                'password': 'UserPass123!'
            }, follow_redirects=True)
            res = self.client.get('/powerbi/download-dataset')
            self.assertEqual(res.status_code, 200)
            self.assertGreater(len(res.data), 100000)

    # --- 6. Error Handling ---
    def test_15_404_error_page(self):
        """Verify 404 page handler returns custom 404 template"""
        res = self.client.get('/non_existent_page_url_12345')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b'404', res.data)

if __name__ == '__main__':
    unittest.main()
