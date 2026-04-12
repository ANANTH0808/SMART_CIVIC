from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

from .models import Complaint, Comment, Notification


def make_user(username='testuser', password='pass1234', is_superuser=False):
    if is_superuser:
        return User.objects.create_superuser(username=username, password=password)
    return User.objects.create_user(username=username, password=password)


def make_complaint(user, **kwargs):
    defaults = {
        'title': 'Test Complaint',
        'desc': 'Some description',
        'location': 'Test Location',
        'category': 'general',
        'status': 'pending',
    }
    defaults.update(kwargs)
    return Complaint.objects.create(user=user, **defaults)


# ─────────────────────────── MODEL TESTS ───────────────────────────

class ComplaintModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_str(self):
        c = make_complaint(self.user, title='Broken Road')
        self.assertEqual(str(c), 'Broken Road')

    def test_default_status_is_pending(self):
        c = make_complaint(self.user)
        self.assertEqual(c.status, 'pending')

    def test_default_category_is_general(self):
        c = Complaint.objects.create(
            user=self.user, title='T', desc='D', location='L'
        )
        self.assertEqual(c.category, 'general')

    def test_lat_lng_nullable(self):
        c = make_complaint(self.user, latitude=None, longitude=None)
        self.assertIsNone(c.latitude)
        self.assertIsNone(c.longitude)


class CommentModelTest(TestCase):

    def setUp(self):
        self.user = make_user()
        self.complaint = make_complaint(self.user)

    def test_comment_creation(self):
        comment = Comment.objects.create(
            complaint=self.complaint,
            user=self.user,
            text='Great complaint!',
        )
        self.assertEqual(comment.text, 'Great complaint!')
        self.assertEqual(comment.complaint, self.complaint)


class NotificationModelTest(TestCase):

    def setUp(self):
        self.user = make_user()

    def test_notification_creation(self):
        n = Notification.objects.create(user=self.user, message='Status updated')
        self.assertEqual(n.message, 'Status updated')
        self.assertEqual(n.user, self.user)


# ─────────────────────────── VIEW TESTS ────────────────────────────

class UserDashboardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_dashboard_requires_login(self):
        self.client.logout()
        resp = self.client.get('/complaints/dashboard/')
        self.assertRedirects(resp, '/login/?next=/complaints/dashboard/')

    def test_admin_redirected_away_from_user_dashboard(self):
        admin = make_user(username='admin2', is_superuser=True)
        self.client.login(username='admin2', password='pass1234')
        resp = self.client.get('/complaints/dashboard/')
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_dashboard_shows_own_complaints(self):
        make_complaint(self.user, title='My Complaint')
        other = make_user(username='other')
        make_complaint(other, title='Other Complaint')
        resp = self.client.get('/complaints/dashboard/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'My Complaint')
        self.assertNotContains(resp, 'Other Complaint')

    def test_dashboard_status_filter(self):
        make_complaint(self.user, title='Pending One', status='pending')
        make_complaint(self.user, title='Resolved One', status='resolved')
        resp = self.client.get('/complaints/dashboard/?status=pending')
        self.assertContains(resp, 'Pending One')
        self.assertNotContains(resp, 'Resolved One')

    def test_dashboard_stats_context(self):
        make_complaint(self.user, status='pending')
        make_complaint(self.user, status='inprogress')
        make_complaint(self.user, status='resolved')
        resp = self.client.get('/complaints/dashboard/')
        self.assertEqual(resp.context['total'], 3)
        self.assertEqual(resp.context['pending'], 1)
        self.assertEqual(resp.context['progress'], 1)
        self.assertEqual(resp.context['resolved'], 1)


class CreateComplaintTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_get_create_page(self):
        resp = self.client.get('/complaints/create-ui/')
        self.assertEqual(resp.status_code, 200)

    def test_create_complaint_post(self):
        resp = self.client.post('/complaints/create-ui/', {
            'title': 'Road Pothole',
            'desc': 'There is a big pothole on street',
            'location': 'Main St',
            'latitude': '',
            'longitude': '',
        })
        self.assertRedirects(resp, '/complaints/dashboard/')
        self.assertEqual(Complaint.objects.count(), 1)
        c = Complaint.objects.first()
        self.assertEqual(c.title, 'Road Pothole')
        self.assertEqual(c.category, 'road')   # auto-detected from 'pothole'
        self.assertIsNone(c.latitude)
        self.assertIsNone(c.longitude)

    def test_create_with_lat_lng(self):
        self.client.post('/complaints/create-ui/', {
            'title': 'Water Leak',
            'desc': 'water leak near pipe',
            'location': 'Park Ave',
            'latitude': '13.08',
            'longitude': '80.27',
        })
        c = Complaint.objects.first()
        self.assertAlmostEqual(c.latitude, 13.08)
        self.assertAlmostEqual(c.longitude, 80.27)
        self.assertEqual(c.category, 'water')

    def test_category_auto_detection_sanitation(self):
        self.client.post('/complaints/create-ui/', {
            'title': 'Garbage',
            'desc': 'garbage not collected',
            'location': 'Side Road',
            'latitude': '',
            'longitude': '',
        })
        c = Complaint.objects.first()
        self.assertEqual(c.category, 'sanitation')

    def test_category_defaults_to_general(self):
        self.client.post('/complaints/create-ui/', {
            'title': 'Something Else',
            'desc': 'unrelated description',
            'location': 'Somewhere',
            'latitude': '',
            'longitude': '',
        })
        c = Complaint.objects.first()
        self.assertEqual(c.category, 'general')


class DetailViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')
        self.complaint = make_complaint(self.user, title='Detail Test')

    def test_detail_page_loads(self):
        resp = self.client.get(f'/complaints/detail/{self.complaint.id}/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Detail Test')

    def test_detail_404_for_missing(self):
        resp = self.client.get('/complaints/detail/9999/')
        self.assertEqual(resp.status_code, 404)


class AddCommentTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')
        self.complaint = make_complaint(self.user)

    def test_add_valid_comment(self):
        self.client.post(f'/complaints/comment/{self.complaint.id}/', {'text': 'Great work!'})
        self.assertEqual(Comment.objects.count(), 1)
        self.assertEqual(Comment.objects.first().text, 'Great work!')

    def test_empty_comment_not_saved(self):
        self.client.post(f'/complaints/comment/{self.complaint.id}/', {'text': '   '})
        self.assertEqual(Comment.objects.count(), 0)

    def test_comment_redirects_to_detail(self):
        resp = self.client.post(f'/complaints/comment/{self.complaint.id}/', {'text': 'Hi'})
        self.assertRedirects(resp, f'/complaints/detail/{self.complaint.id}/')


class UpdateStatusTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user(username='admin', is_superuser=True)
        self.user = make_user()
        self.complaint = make_complaint(self.user)

    def test_admin_can_update_status(self):
        self.client.login(username='admin', password='pass1234')
        self.client.post(f'/complaints/update/{self.complaint.id}/', {'status': 'resolved'})
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')

    def test_status_update_creates_notification(self):
        self.client.login(username='admin', password='pass1234')
        self.client.post(f'/complaints/update/{self.complaint.id}/', {'status': 'inprogress'})
        self.assertEqual(Notification.objects.filter(user=self.user).count(), 1)

    def test_invalid_status_not_saved(self):
        self.client.login(username='admin', password='pass1234')
        self.client.post(f'/complaints/update/{self.complaint.id}/', {'status': 'hacked'})
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'pending')  # unchanged

    def test_admin_redirected_to_admin_dashboard(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(f'/complaints/update/{self.complaint.id}/', {'status': 'resolved'})
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_user_redirected_to_user_dashboard(self):
        self.client.login(username='testuser', password='pass1234')
        resp = self.client.post(f'/complaints/update/{self.complaint.id}/', {'status': 'resolved'})
        self.assertRedirects(resp, '/complaints/dashboard/')


class DeleteComplaintTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.other = make_user(username='other')
        self.admin = make_user(username='admin', is_superuser=True)

    def test_owner_can_delete(self):
        c = make_complaint(self.user)
        self.client.login(username='testuser', password='pass1234')
        self.client.post(f'/complaints/delete/{c.id}/')
        self.assertEqual(Complaint.objects.count(), 0)

    def test_admin_can_delete_any(self):
        c = make_complaint(self.user)
        self.client.login(username='admin', password='pass1234')
        self.client.post(f'/complaints/delete/{c.id}/')
        self.assertEqual(Complaint.objects.count(), 0)

    def test_other_user_cannot_delete(self):
        c = make_complaint(self.user)
        self.client.login(username='other', password='pass1234')
        self.client.post(f'/complaints/delete/{c.id}/')
        self.assertEqual(Complaint.objects.count(), 1)

    def test_delete_redirects_admin_to_admin_dashboard(self):
        c = make_complaint(self.user)
        self.client.login(username='admin', password='pass1234')
        resp = self.client.post(f'/complaints/delete/{c.id}/')
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_delete_redirects_user_to_user_dashboard(self):
        c = make_complaint(self.user)
        self.client.login(username='testuser', password='pass1234')
        resp = self.client.post(f'/complaints/delete/{c.id}/')
        self.assertRedirects(resp, '/complaints/dashboard/')


class AdminDashboardTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user(username='admin', is_superuser=True)
        self.user = make_user()

    def test_admin_can_access(self):
        self.client.login(username='admin', password='pass1234')
        resp = self.client.get('/complaints/admin-dashboard/')
        self.assertEqual(resp.status_code, 200)

    def test_non_admin_redirected(self):
        self.client.login(username='testuser', password='pass1234')
        resp = self.client.get('/complaints/admin-dashboard/')
        self.assertRedirects(resp, '/complaints/dashboard/')

    def test_admin_sees_all_complaints(self):
        make_complaint(self.user, title='User Complaint')
        make_complaint(self.admin, title='Admin Complaint')
        self.client.login(username='admin', password='pass1234')
        resp = self.client.get('/complaints/admin-dashboard/')
        self.assertContains(resp, 'User Complaint')
        self.assertContains(resp, 'Admin Complaint')


class ProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_profile_page_loads(self):
        resp = self.client.get('/complaints/profile/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'testuser')


class EditProfileTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_edit_profile_updates_username(self):
        self.client.post('/complaints/edit-profile/', {
            'username': 'newname',
            'email': 'new@test.com',
        })
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'newname')
        self.assertEqual(self.user.email, 'new@test.com')

    def test_duplicate_username_shows_error(self):
        make_user(username='taken')
        resp = self.client.post('/complaints/edit-profile/', {
            'username': 'taken',
            'email': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'already taken')
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, 'testuser')  # unchanged

    def test_empty_username_shows_error(self):
        resp = self.client.post('/complaints/edit-profile/', {
            'username': '',
            'email': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'cannot be empty')


class AdminLoginViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.admin = make_user(username='admin', is_superuser=True)

    def test_admin_login_success(self):
        resp = self.client.post('/complaints/admin-login/', {
            'username': 'admin',
            'password': 'pass1234',
        })
        self.assertRedirects(resp, '/complaints/admin-dashboard/')

    def test_admin_login_wrong_password(self):
        resp = self.client.post('/complaints/admin-login/', {
            'username': 'admin',
            'password': 'wrong',
        })
        self.assertContains(resp, 'Invalid admin credentials')

    def test_non_admin_user_cannot_login_as_admin(self):
        make_user(username='regular')
        resp = self.client.post('/complaints/admin-login/', {
            'username': 'regular',
            'password': 'pass1234',
        })
        self.assertContains(resp, 'Invalid admin credentials')


class KanbanTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_kanban_loads(self):
        make_complaint(self.user, status='pending', title='P1')
        make_complaint(self.user, status='inprogress', title='In1')
        make_complaint(self.user, status='resolved', title='R1')
        resp = self.client.get('/complaints/kanban/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['pending'].count(), 1)
        self.assertEqual(resp.context['progress'].count(), 1)
        self.assertEqual(resp.context['resolved'].count(), 1)


class NotificationsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = make_user()
        self.client.login(username='testuser', password='pass1234')

    def test_notifications_page(self):
        Notification.objects.create(user=self.user, message='Your complaint was resolved')
        resp = self.client.get('/complaints/notifications/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Your complaint was resolved')

    def test_only_own_notifications_shown(self):
        other = make_user(username='other')
        Notification.objects.create(user=self.user, message='Mine')
        Notification.objects.create(user=other, message='Theirs')
        resp = self.client.get('/complaints/notifications/')
        self.assertContains(resp, 'Mine')
        self.assertNotContains(resp, 'Theirs')
