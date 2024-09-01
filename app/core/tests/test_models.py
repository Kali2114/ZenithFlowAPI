"""
Tests for models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models
from django.utils import timezone


def create_user(**params):
    """Create and return a new user."""
    default_user = {
        "email": "test@example.com",
        "password": "Test123",
        "name": "TestName",
    }
    default_user.update(**params)

    return get_user_model().objects.create_user(**default_user)


def create_meditation_session(**params):
    meditation_session = {
        'name':  "Mindful Morning",
        'description': "Test description",
        'duration': 40,
        'start_time': timezone.now(),
    }
    meditation_session.update(**params)
    return models.MeditationSession.create(**meditation_session)


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful."""
        email = "test@example.com"
        password = "Test123"

        user = create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test the email is normalized for new users."""
        sample_emails = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@ExAmple.com", "Test2@example.com"],
            ["Test3@example.COM", "Test3@example.com"],
        ]
        for idx, (email, expected) in enumerate(sample_emails):
            user = create_user(
                email=email,
                password="Test123",
                name=f"User{idx}",
            )
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raise_error(self):
        """Test raises ValueError when creating user without email."""
        with self.assertRaises(ValueError):
            create_user(email="")

    def test_new_user_without_name_raise_error(self):
        """Test raises ValueError when creating user without email."""
        with self.assertRaises(ValueError):
            create_user(name="")

    def test_create_superuser(self):
        """Test creating a superuser successful."""
        user = get_user_model().objects.create_superuser(
            email="example@test.com",
            password="Test123",
            name="Test_Name",
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_meditation_session(self):
        """Test creating a meditations session successful."""
        instructor = create_user()
        meditation_session = create_meditation_session(instructor=instructor)

        self.assertEqual(
            str(meditation_session),
            f"{meditation_session.name} " f"by {meditation_session.instructor}",
        )

    def test_meditation_session_name_numbering(self):
        """Test that meditation session names are correctly numbered."""
        instructor = create_user(email='test1@example.com', name='Test1')
        session1 = create_meditation_session(instructor=instructor)
        session2 = create_meditation_session(instructor=instructor)
        session3 = create_meditation_session(instructor=instructor)

        self.assertEqual(session1.name, 'Mindful Morning #1')
        self.assertEqual(session2.name, 'Mindful Morning #2')
        self.assertEqual(session3.name, 'Mindful Morning #3')
