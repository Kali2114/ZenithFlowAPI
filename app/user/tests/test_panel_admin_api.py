"""
Test for panel admin API.
"""

from rest_framework.test import APITestCase

from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

from core.models import User


def panel_admin_detail_url(instructor_id):
    """Get and return a panel admin detail url."""
    return reverse("user:panel_admin", args=[instructor_id])


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "testname",
    }
    default_user.update(params)

    return User.objects.create_user(**default_user)


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return User.objects.create_superuser(**default_user)


class PublicPanelAdminTests(APITestCase):
    """Public tests for the panel admin."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_to_get_user_profile(self):
        """Test that login is required to get the user profile."""
        url = panel_admin_detail_url(1)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class InstructorPanelAdminTests(APITestCase):
    """Private tests for the panel admin."""

    def setUp(self):
        self.client = APIClient()
        self.instructor = create_instructor()
        self.client.force_authenticate(user=self.instructor)

    def test_get_panel_admin_data(self):
        """Test that get panel admin data by instructor successful."""
        url = panel_admin_detail_url(self.instructor.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("all_users", res.data)
        self.assertIn("active_subscribers", res.data)
        self.assertIn("all_sessions", res.data)
        self.assertIn("instructor_sessions", res.data)
        self.assertIn("participants_per_session", res.data)


class UserPanelAdminTests(APITestCase):
    """Private tests for the panel admin."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def test_get_panel_admin_data(self):
        """Test that get panel admin data by user failed."""
        url = panel_admin_detail_url(1)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)
