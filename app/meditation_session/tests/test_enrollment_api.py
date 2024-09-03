"""
Tests for enrollment API.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from core.models import MeditationSession, Enrollment
from meditation_session.serializers import (
    EnrollmentSerializer,
    EnrollmentDetailSerializer,
)


ENROLLMENT_URL = reverse("meditation_session:enrollment-list")


def detail_url(enrollment_id):
    return reverse(
        "meditation_session:enrollment-detail", args=[enrollment_id]
    )


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return get_user_model().objects.create_superuser(**default_user)


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "Testpass123",
        "name": "Testname",
    }
    default_user.update(**params)

    return get_user_model().objects.create_user(**default_user)


def create_meditation_session(**params):
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return MeditationSession.create(**meditation_session)


class PublicEnrollmentApiTests(TestCase):
    """Test unauthenticated API request."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to retrieving enrollments."""
        res = self.client.get(ENROLLMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateEnrollmentApiTests(TestCase):
    """Test authenticated user API request."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.instructor = create_instructor()
        self.session = create_meditation_session(instructor=self.instructor)

    def test_retrieve_enrollments(self):
        """Test retrieving a list of enrollments."""
        Enrollment.objects.create(user=self.user, session=self.session)
        res = self.client.get(ENROLLMENT_URL)

        enrollment = Enrollment.objects.all()
        serializer = EnrollmentSerializer(enrollment, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_enrollments_listing_to_user(self):
        """Test retrieving a list of enrollments listing to user."""
        session1 = create_meditation_session(
            name="Morning Meditation", instructor=self.instructor
        )
        session2 = create_meditation_session(
            name="Evening Meditation", instructor=self.instructor
        )
        Enrollment.objects.create(user=self.user, session=session1)
        Enrollment.objects.create(user=self.user, session=session2)
        other_user = create_user(
            email="test1@examl",
            password="Test123",
            name="other_user",
        )
        session3 = create_meditation_session(
            name="Afternoon", instructor=self.instructor
        )
        Enrollment.objects.create(user=other_user, session=session3)

        res = self.client.get(ENROLLMENT_URL)
        enrollments = Enrollment.objects.filter(user=self.user).order_by(
            "-enrolled_at"
        )
        serializer = EnrollmentSerializer(enrollments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_get_enrollment_detail(self):
        """Test get enrollment detail."""
        enrollment = Enrollment.objects.create(
            user=self.user, session=self.session
        )
        url = detail_url(enrollment.id)
        res = self.client.get(url)
        serializer = EnrollmentDetailSerializer(enrollment)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_enrollment(self):
        """Test creating an enrollment by user."""
        payload = {"session": self.session.id}
        res = self.client.post(ENROLLMENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        enrollment = Enrollment.objects.get(id=res.data["id"])
        self.assertEqual(self.user, enrollment.user)
        self.assertEqual(enrollment.session, self.session)

    def test_create_enrollment_full_session_fails(self):
        """Test creating enrollment when meditation session is full fails."""
        other_user = create_user(email="other@example.com", name="Other")
        session = create_meditation_session(
            instructor=self.instructor, max_participants=1
        )
        Enrollment.objects.create(user=other_user, session=session)
        payload = {"session": session.id}
        res = self.client.post(ENROLLMENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(session.enrollments.count(), 1)

    def test_create_duplicate_enrollment_fails(self):
        """Test creating a duplicate enrollment fails."""
        Enrollment.objects.create(user=self.user, session=self.session)
        payload = {"session": self.session.id}
        res = self.client.post(ENROLLMENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_enrollment_not_allowed(self):
        """Test updating an enrollment is not allowed."""
        enrollment = Enrollment.objects.create(
            user=self.user, session=self.session
        )
        session2 = create_meditation_session(
            name="Afternoon Meditation", instructor=self.instructor
        )
        user2 = create_user(name="User2", email="user2@example.com")
        payload = {"session": session2.id, "user": user2}
        url = detail_url(enrollment.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(enrollment.session, self.session)
        self.assertEqual(enrollment.user, self.user)

    def test_delete_enrollment(self):
        """Test deleting an enrollment successful."""
        enrollment = Enrollment.objects.create(
            user=self.user, session=self.session
        )
        url = detail_url(enrollment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        enrollment_exists = Enrollment.objects.filter(
            id=enrollment.id
        ).exists()
        self.assertFalse(enrollment_exists)

    def test_delete_another_user_enrollment_fails(self):
        """Test deleting other user enrollment fails."""
        other_user = create_user(name="other user", email="other@example.com")
        enrollment = Enrollment.objects.create(
            user=other_user, session=self.session
        )
        url = detail_url(enrollment.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        enrollment_exists = Enrollment.objects.filter(
            id=enrollment.id
        ).exists()
        self.assertTrue(enrollment_exists)
