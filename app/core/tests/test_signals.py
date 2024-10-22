"""
Tests for signals.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from core.models import (
    UserProfile,
    PanelAdmin,
)


class UserProfileSignalTests(TestCase):
    """Test that the user profile is created and deleted with user."""

    def test_profile_created_on_user_creation(self):
        """Test that a profile is created when a user is created."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass123", name="Test User"
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_deleted_on_user_deletion(self):
        """Test that the profile is deleted when the user is deleted."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="testpass123", name="Test User"
        )
        user_id = user.id
        user.delete()

        self.assertFalse(UserProfile.objects.filter(user_id=user_id).exists())


class PanelAdminSignalTest(TestCase):
    """Test that the panel admin is created and deleted with instructor."""

    def test_panel_admin_created_on_instructor_creation(self):
        instructor = get_user_model().objects.create_superuser(
            email="instructor@example.com",
            password="testpass123",
            name="Instructor",
        )

        self.assertTrue(
            PanelAdmin.objects.filter(instructor=instructor).exists()
        )

    def test_panel_admin_deleted_on_instructor_deletion(self):
        instructor = get_user_model().objects.create_superuser(
            email="instructor@example.com",
            password="testpass123",
            name="Instructor",
        )
        instructor_id = instructor.id
        instructor.delete()

        self.assertFalse(
            PanelAdmin.objects.filter(instructor_id=instructor_id).exists()
        )
