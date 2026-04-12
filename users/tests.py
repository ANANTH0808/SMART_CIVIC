from django.test import TestCase, Client
from django.contrib.auth.models import User


def make_user(username='testuser', password='pass1234'):
    return User.objects.create_user(username=username, password=password)


# ─────────────────────────── HOME ───────────────────────────

class HomeViewTest(TestCase):

    def test_home_page_loads(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)


# ─────────────────────────── USER LOGIN ───────────────────────────

class UserLoginTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user()

    def test_get_login_page(self):
        resp = self.client.get('/userlogin/')
        self.assertEqual(resp.status_code, 200)

    def test_login_success_redirects_to_dashboard(self):
        resp = self.client.post('/userlogin/', {
            'username': 'testuser',
            'password': 'pass1234',
        })
        self.assertRedirects(resp, '/complaints/dashboard/')

    def test_login_wrong_password_shows_error(self):
        resp = self.client.post('/userlogin/', {
            'username': 'testuser',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_login_missing_fields_shows_error(self):
        resp = self.client.post('/userlogin/', {
            'username': '',
            'password': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_login_nonexistent_user_shows_error(self):
        resp = self.client.post('/userlogin/', {
            'username': 'nobody',
            'password': 'pass1234',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')


# ─────────────────────────── ADMIN LOGIN ───────────────────────────

class AdminLoginTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(
            username='admin', password='adminpass'
        )
        self.regular = make_user()

    def test_get_admin_login_page(self):
        resp = self.client.get('/adminlogin/')
        self.assertEqual(resp.status_code, 200)

    def test_admin_login_success(self):
        resp = self.client.post('/adminlogin/', {
            'username': 'admin',
            'password': 'adminpass',
        })
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_regular_user_cannot_use_admin_login(self):
        resp = self.client.post('/adminlogin/', {
            'username': 'testuser',
            'password': 'pass1234',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid admin credentials')

    def test_wrong_password_shows_error(self):
        resp = self.client.post('/adminlogin/', {
            'username': 'admin',
            'password': 'wrongpass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid admin credentials')


# ─────────────────────────── REGISTER ───────────────────────────

class RegisterTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_get_register_page(self):
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)

    def test_register_creates_user(self):
        resp = self.client.post('/register/', {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass',
        })
        self.assertRedirects(resp, '/login/')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_saves_email(self):
        self.client.post('/register/', {
            'username': 'emailuser',
            'email': 'email@example.com',
            'password': 'securepass',
        })
        user = User.objects.get(username='emailuser')
        self.assertEqual(user.email, 'email@example.com')

    def test_register_duplicate_username_shows_error(self):
        make_user(username='existing')
        resp = self.client.post('/register/', {
            'username': 'existing',
            'email': '',
            'password': 'securepass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already taken')
        self.assertEqual(User.objects.filter(username='existing').count(), 1)

    def test_register_empty_username_shows_error(self):
        resp = self.client.post('/register/', {
            'username': '',
            'email': '',
            'password': 'securepass',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'required')

    def test_register_empty_password_shows_error(self):
        resp = self.client.post('/register/', {
            'username': 'someone',
            'email': '',
            'password': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'required')


# ─────────────────── MAIN LOGIN (role-aware) ───────────────────

class MainLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser(username='superadmin', password='pass1234')
        self.user = make_user()

    def test_main_login_page_loads(self):
        resp = self.client.get('/login/')
        self.assertEqual(resp.status_code, 200)

    def test_citizen_redirected_to_user_dashboard(self):
        resp = self.client.post('/login/', {'username': 'testuser', 'password': 'pass1234'})
        self.assertRedirects(resp, '/complaints/dashboard/')

    def test_admin_redirected_to_admin_dashboard(self):
        resp = self.client.post('/login/', {'username': 'superadmin', 'password': 'pass1234'})
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_wrong_credentials_shows_error(self):
        resp = self.client.post('/login/', {'username': 'testuser', 'password': 'wrong'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_user_login_portal_admin_redirected_to_admin_dashboard(self):
        """Admin logging in via /userlogin/ should still reach admin dashboard."""
        resp = self.client.post('/userlogin/', {'username': 'superadmin', 'password': 'pass1234'})
        self.assertRedirects(resp, '/complaints/admin-dashboard/')


# ─────────────────────────── LOGOUT ───────────────────────────

class LogoutTest(TestCase):

    def setUp(self):
        self.client = Client()
        make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_logout_redirects_home(self):
        resp = self.client.get('/logout/')
        self.assertRedirects(resp, '/')

    def test_user_is_logged_out(self):
        self.client.get('/logout/')
        resp = self.client.get('/complaints/dashboard/')
        self.assertRedirects(resp, '/login/?next=/complaints/dashboard/')
