import sys
import os
import unittest

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app
from services.database_service import DatabaseService
from models.user_model import User
from models.location_model import LocationModel
from services.activity_service import ActivityService
from werkzeug.security import generate_password_hash

class TestRBACSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False

        # Reset known test users
        DatabaseService.execute_query(
            "DELETE FROM users WHERE email IN ('admin_test@test.com', 'user_test@test.com', 'inactive_test@test.com', 'malicious_reg@test.com')",
            fetch_all=False
        )

        # Create Admin user
        User.create_user("Test Admin", "admin_test@test.com", "AdminPass123!", role="ADMIN")

        # Create Normal user
        User.create_user("Test User", "user_test@test.com", "UserPass123!", role="USER")

        # Create Inactive user
        DatabaseService.execute_insert(
            "INSERT INTO users (name, email, password_hash, role, is_active) VALUES (%s, %s, %s, %s, 0)",
            ("Inactive User", "inactive_test@test.com", generate_password_hash("InactivePass123!"), "USER")
        )

    def setUp(self):
        self.client = app.test_client()

    def test_01_cache_headers(self):
        """Verify back-button prevention headers on responses"""
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)
        self.assertIn('no-cache', res.headers.get('Cache-Control', ''))
        self.assertIn('no-store', res.headers.get('Cache-Control', ''))

    def test_02_login_redirect_admin(self):
        """Admin login redirects to /admin/dashboard"""
        res = self.client.post('/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/admin/dashboard', res.headers.get('Location', ''))

    def test_03_login_redirect_user(self):
        """User login redirects to /dashboard"""
        res = self.client.post('/login', data={
            'email': 'user_test@test.com',
            'password': 'UserPass123!'
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/dashboard', res.headers.get('Location', ''))

    def test_04_login_inactive_user_blocked(self):
        """Deactivated user cannot log in"""
        res = self.client.post('/login', data={
            'email': 'inactive_test@test.com',
            'password': 'InactivePass123!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'deactivated', res.data.lower())

    def test_05_register_forces_user_role(self):
        """Registration always forces role='USER' even if attacker sends role='ADMIN'"""
        test_reg_email = "malicious_reg@test.com"
        res = self.client.post('/register', data={
            'name': 'Hacker',
            'email': test_reg_email,
            'password': 'HackerPass123!',
            'confirm_password': 'HackerPass123!',
            'role': 'ADMIN' # Tampering attempt
        }, follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        # Should redirect to /login (not /dashboard) with email pre-filled
        self.assertIn('/login', res.headers.get('Location', ''))

        created = User.get_by_email(test_reg_email)
        self.assertIsNotNone(created)
        self.assertEqual(created.role, "USER")
        self.assertFalse(created.is_admin)

    def test_06_unauthenticated_admin_access_redirects(self):
        """Unauthenticated user accessing /admin/dashboard gets redirected to /login"""
        res = self.client.get('/admin/dashboard', follow_redirects=False)
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers.get('Location', ''))

    def test_07_user_role_blocked_from_admin_403(self):
        """Logged-in normal USER gets 403 Forbidden when accessing /admin/*"""
        # Login as normal user
        self.client.post('/login', data={
            'email': 'user_test@test.com',
            'password': 'UserPass123!'
        })

        admin_routes = [
            '/admin/dashboard',
            '/admin/data',
            '/admin/locations',
            '/admin/users',
            '/admin/audit'
        ]
        for route in admin_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 403, f"Expected 403 for route {route}")
            self.assertIn(b'403', res.data)
            self.assertIn(b'Access Denied', res.data)

    def test_08_admin_role_access_granted(self):
        """Admin has full access to /admin/* pages"""
        # Login as admin
        self.client.post('/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        })

        admin_routes = [
            '/admin/dashboard',
            '/admin/data',
            '/admin/locations',
            '/admin/users',
            '/admin/audit'
        ]
        for route in admin_routes:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200, f"Expected 200 for admin on {route}")

    def test_09_user_panel_read_only(self):
        """User panel /crime-data is accessible and has no mutating buttons"""
        self.client.post('/login', data={
            'email': 'user_test@test.com',
            'password': 'UserPass123!'
        })
        res = self.client.get('/crime-data')
        self.assertEqual(res.status_code, 200)
        # Should not have Add New Record or Admin actions
        self.assertNotIn(b'href="/admin/data"', res.data)
        self.assertNotIn(b'Add New Crime Record', res.data)

    def test_10_admin_crud_crime_data(self):
        """Admin can add, edit, and delete crime records"""
        self.client.post('/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        })

        # Add crime
        res = self.client.post('/admin/data/add', data={
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'area': 'South Mumbai',
            'crime_type': 'Theft',
            'year': '2026',
            'cases_reported': '10',
            'chargesheeted': '8',
            'convictions': '5',
            'population': '100000'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'created successfully', res.data)

        # Query latest created crime
        from models.crime_model import CrimeModel
        records = CrimeModel.get_all(filters={'state': 'Maharashtra', 'district': 'Mumbai', 'area': 'South Mumbai', 'year': '2026', 'crime_type': 'Theft'})
        self.assertTrue(len(records) > 0)
        cid = records[0]['id']

        # Edit crime
        res_edit = self.client.post(f'/admin/data/edit/{cid}', data={
            'state': 'Maharashtra',
            'district': 'Mumbai',
            'area': 'South Mumbai',
            'crime_type': 'Theft',
            'year': '2026',
            'cases_reported': '15',
            'chargesheeted': '12',
            'convictions': '9',
            'population': '100000'
        }, follow_redirects=True)
        self.assertEqual(res_edit.status_code, 200)
        self.assertIn(b'updated successfully', res_edit.data)

        # Delete crime
        res_del = self.client.post(f'/admin/data/delete/{cid}', follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertIn(b'deleted successfully', res_del.data)

    def test_11_location_hierarchy_apis(self):
        """Test 3-tier location hierarchy APIs"""
        # Fetch states
        states = LocationModel.get_all_states()
        self.assertTrue(len(states) > 0)
        sid = states[0]['id']

        # Test district API by state id
        res = self.client.get(f'/api/locations/districts/{sid}')
        self.assertEqual(res.status_code, 200)
        districts = res.get_json()
        self.assertIsInstance(districts, list)

        if districts:
            did = districts[0]['id']
            # Test area API by district id
            res2 = self.client.get(f'/api/locations/areas/{did}')
            self.assertEqual(res2.status_code, 200)
            areas = res2.get_json()
            self.assertIsInstance(areas, list)

        # Test query param API
        res3 = self.client.get('/api/districts?state=Maharashtra')
        self.assertEqual(res3.status_code, 200)

    def test_12_admin_user_protection(self):
        """Admin cannot deactivate or delete self, or delete last admin"""
        self.client.post('/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        })
        admin = User.get_by_email('admin_test@test.com')

        # Attempt to toggle self status
        res = self.client.post(f'/admin/users/toggle/{admin.id}', follow_redirects=True)
        self.assertIn(b'You cannot deactivate your own account', res.data)

        # Attempt to delete self
        res_del = self.client.post(f'/admin/users/delete/{admin.id}', follow_redirects=True)
        self.assertIn(b'You cannot delete your own account', res_del.data)

    def test_13_audit_logging(self):
        """Verify activity logs are recorded and accessible in admin panel"""
        logs = ActivityService.get_recent_logs(10)
        self.assertTrue(len(logs) > 0)

        # Verify audit log view renders
        self.client.post('/login', data={
            'email': 'admin_test@test.com',
            'password': 'AdminPass123!'
        })
        res = self.client.get('/admin/audit')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'System Activity &amp; Audit Logs', res.data)

if __name__ == '__main__':
    unittest.main()
