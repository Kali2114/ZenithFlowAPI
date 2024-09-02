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


ENROLMENT_URL = reverse("meditation_session:enrollment-list")


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
        res = self.client.get(ENROLMENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateEnrollmentApiTests(TestCase):
    """Test authenticated user API request."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_enrollments(self):
        """Test retrieving a list of enrollments."""
        instructor = create_instructor()
        session = create_meditation_session(instructor=instructor)
        Enrollment.objects.create(user=self.user, session=session)
        res = self.client.get(ENROLMENT_URL)

        enrollment = Enrollment.objects.all()
        serializer = EnrollmentSerializer(enrollment, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_retrieve_enrollments_listing_to_user(self):
        """Test retrieving a list of enrollments listing to user."""
        instructor = create_instructor()
        session1 = create_meditation_session(
            name="Morning Meditation", instructor=instructor
        )
        session2 = create_meditation_session(
            name="Evening Meditation", instructor=instructor
        )
        Enrollment.objects.create(user=self.user, session=session1)
        Enrollment.objects.create(user=self.user, session=session2)
        other_user = create_user(
            email="test1@examl",
            password="Test123",
            name="other_user",
        )
        session3 = create_meditation_session(
            name="Afternoon", instructor=instructor
        )
        Enrollment.objects.create(user=other_user, session=session3)

        res = self.client.get(ENROLMENT_URL)
        enrollments = Enrollment.objects.filter(user=self.user).order_by(
            "-enrolled_at"
        )
        serializer = EnrollmentSerializer(enrollments, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data, serializer.data)

    def test_get_enrollment_detail(self):
        """Test get enrollment detail."""
        instructor = create_instructor()
        session = create_meditation_session(
            name="Morning Meditation", instructor=instructor
        )
        enrollment = Enrollment.objects.create(user=self.user, session=session)
        url = detail_url(enrollment.id)
        res = self.client.get(url)
        serializer = EnrollmentDetailSerializer(enrollment)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
