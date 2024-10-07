"""
Tests for models.
"""

import io
from PIL import Image
from unittest.mock import patch
from django.core.files.uploadedfile import SimpleUploadedFile
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


def create_instructor(**params):
    """Create and return a new instructor."""
    default_user = {
        "email": "instructor@example.com",
        "password": "testpass123",
        "name": "Instructor",
    }
    default_user.update(params)

    return get_user_model().objects.create_superuser(**default_user)


def create_meditation_session(**params):
    meditation_session = {
        "name": "Mindful Morning",
        "description": "Test description",
        "duration": 40,
        "start_time": timezone.now(),
    }
    meditation_session.update(**params)
    return models.MeditationSession.create(**meditation_session)


def create_test_image():
    """Create a dummy image for avatar."""
    image = Image.new(
        "RGB", (100, 100), color="blue"
    )  # Tworzy niebieski obrazek 100x100
    byte_arr = io.BytesIO()
    image.save(byte_arr, format="PNG")
    byte_arr.seek(0)
    return SimpleUploadedFile(
        "avatar.png", byte_arr.read(), content_type="image/png"
    )


class ModelTests(TestCase):
    """Test models."""

    def test_create_user_with_email_successful(self):
        """Test creating a user with email is successful."""
        email = "test@example.com"
        password = "Test123"

        user = create_user(email=email, password=password)

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
            f"{meditation_session.name} "
            f"by {meditation_session.instructor}",
        )

    def test_meditation_session_name_numbering(self):
        """Test that meditation session names are correctly numbered."""
        instructor = create_user(email="test1@example.com", name="Test1")
        session1 = create_meditation_session(instructor=instructor)
        session2 = create_meditation_session(instructor=instructor)
        session3 = create_meditation_session(instructor=instructor)

        self.assertEqual(session1.name, "Mindful Morning #1")
        self.assertEqual(session2.name, "Mindful Morning #2")
        self.assertEqual(session3.name, "Mindful Morning #3")

    def test_create_enrollment(self):
        """Test a creating enrollment successful."""
        user = create_user()
        instructor = create_instructor()
        meditation_session = create_meditation_session(instructor=instructor)
        enrollment = models.Enrollment.objects.create(
            user=user,
            session=meditation_session,
        )

        self.assertEqual(
            str(enrollment), f"User: {user} enrolled in {meditation_session}"
        )

    def test_create_technique(self):
        """Test a creating technique successful."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="Test123", name="Testname"
        )
        technique = models.Technique.objects.create(
            name="Test Name", description="Test description", instructor=user
        )

        self.assertEqual(str(technique), f"{technique.name}")

    def test_create_rating(self):
        """Test a creating rating successful."""
        user = get_user_model().objects.create_user(
            email="test@example.com", password="Test123", name="Testname"
        )
        instructor = create_instructor()
        meditation_session = create_meditation_session(
            instructor=instructor,
            is_completed=True,
        )
        rating = models.Rating.objects.create(
            user=user,
            session=meditation_session,
            rating=5,
            comment="Awesome session.",
        )

        self.assertEqual(
            str(rating),
            f"{user.name} rated {meditation_session.name} ({rating.rating}/5)",
        )

    def test_create_user_profile(self):
        """Test creating user profile successful."""
        user = create_user(email="test2@example.com", name="Test User 2")
        user_profile = models.UserProfile.objects.get(user=user)

        self.assertEqual(str(user_profile), f"{user.name}'s profile")

    @patch("core.models.uuid.uuid4")
    def test_generate_image_path(self, mock_uuid):
        """Test generating path for image is successful."""
        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.avatar_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/avatar/{uuid}.jpg")

    def test_create_subscription(self):
        """Test creating subscription for user successful."""
        user = create_user(email="test@example.com", name="Test User")
        start_date = timezone.now()
        end_date = start_date + timezone.timedelta(days=30)

        subscription = models.Subscription.objects.create(
            user=user, start_date=start_date, end_date=end_date, is_active=True
        )

        self.assertEqual(str(subscription), f"Subscription for {user.email}")

    def test_create_message(self):
        """Test creating a message successful."""
        sender = create_user(email="sender@example.com", name="Sender")
        receiver = create_user(email="receiver@example.com", name="Receiver")

        message = models.Message.objects.create(
            sender=sender, receiver=receiver, content="Test content."
        )

        self.assertEqual(
            str(message), f"From {sender} to {receiver} at {message.timestamp}"
        )
