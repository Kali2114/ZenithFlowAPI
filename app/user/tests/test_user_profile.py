"""
Test for user profile.
"""

import os
import tempfile

from PIL import Image

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from core.models import (
    UserProfile,
    MeditationSession,
    Enrollment,
)


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "testpass123",
        "name": "testname",
    }
    default_user.update(params)

    return get_user_model().objects.create_user(**default_user)


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return get_user_model().objects.create_superuser(**default_user)


def detail_url(user_id):
    """Create and return a detail url for user profile."""
    return reverse("user:userprofile-detail", args=[user_id])


def create_meditation_session(**params):
    """Create and return a new meditation session."""
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


def image_upload_url(user_id):
    """Create and return an image upload URL."""
    return reverse("user:upload-avatar", args=[user_id])


class PublicUserProfileTests(TestCase):
    """Public tests for the user profile."""

    def setUp(self):
        self.client = APIClient()

    def test_login_required_to_get_user_profile(self):
        """Test that login is required to get the user profile."""
        url = detail_url(1)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserProfileTests(TestCase):
    """Private tests for the user profile."""

    def setUp(self):
        self.user = create_user()
        self.instructor = create_instructor()
        self.session = create_meditation_session(instructor=self.instructor)
        self.profile = UserProfile.objects.get(user=self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_new_user_profile_failed(self):
        """Test that user cannot create a new user profile."""
        payload = {"user": self.user.id, "biography": "Test bio"}
        url = detail_url(self.user.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_own_profile_success(self):
        """Test that authenticated user can update own profile successful."""
        payload = {"biography": "Nothing else."}
        url = detail_url(self.user.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user_profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(user_profile.biography, payload["biography"])

    def test_cannot_update_readonly_fields(self):
        """Test that readonly fields cannot be updated by the user."""
        payload = {"sessions_attended": 10, "total_time_spent": 100}
        url = detail_url(self.user.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user_profile = UserProfile.objects.get(user=self.user)
        self.assertNotEqual(
            user_profile.sessions_attended, payload["sessions_attended"]
        )
        self.assertNotEqual(
            user_profile.total_time_spent, payload["total_time_spent"]
        )

    def test_update_another_user_profile_failed(self):
        """Test that authenticated user cannot update another user profile."""
        another_user = create_user(
            email="another@example.com", name="Another User"
        )
        payload = {"biography": "Nothing else."}
        url = detail_url(another_user.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_user_profile_failed(self):
        """Test that the DELETE method is not allowed for user profiles."""
        url = detail_url(self.user.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        user_profile = UserProfile.objects.filter(user=self.user).exists()
        self.assertTrue(user_profile)

    def test_session_completion_updates_profile(self):
        """Test that completing a session updates the user's profile."""
        Enrollment.objects.create(user=self.user, session=self.session)
        self.session.is_completed = True
        self.session.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.sessions_attended, 1)
        self.assertEqual(self.profile.total_time_spent, 40)

    def test_session_completion_does_not_update_profile_of_other_user(self):
        """Test that completing a session by another
        user does not affect the logged-in user's profile."""
        another_user = create_user(
            email="another@example.com", name="Another User"
        )
        Enrollment.objects.create(user=another_user, session=self.session)
        self.session.is_completed = True
        self.session.save()

        self.profile.refresh_from_db()
        self.assertEqual(self.profile.sessions_attended, 0)
        self.assertEqual(self.profile.total_time_spent, 0)


class ImageUploadTests(TestCase):
    """Tests for the image upload API."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        self.user.user_profile.avatar.delete()

    def test_upload_image(self):
        """Test uploading an image to user's avatar."""
        url = image_upload_url(self.user.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as image_file:
            img = Image.new("RGB", (10, 10))
            img.save(image_file, format="JPEG")
            image_file.seek(0)
            payload = {"avatar": image_file}
            res = self.client.patch(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIn("avatar", res.data)
        self.assertTrue(os.path.exists(self.user.user_profile.avatar.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid image."""
        url = image_upload_url(self.user.id)
        payload = {"avatar": "bad request"}
        res = self.client.patch(url, payload, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
