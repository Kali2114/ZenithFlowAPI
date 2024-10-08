"""
Test for reminders with Celery.
"""

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from django.contrib.auth import get_user_model

from core.models import MeditationSession
from config.tasks import check_sessions_for_reminder


class TestReminderTask(TestCase):

    def setUp(self):
        self.instructor = get_user_model().objects.create_user(
            email="instructor@example.com",
            password="password123",
            name="Instructor",
        )

        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="password123",
            name="User",
        )

        tomorrow = timezone.now() + timedelta(days=1)
        self.session = MeditationSession.objects.create(
            name="Test Session",
            description="Test description",
            duration=60,
            start_time=tomorrow,
            instructor=self.instructor,
        )

        self.session.enrollments.create(user=self.user)

    # TODO configure celery

    @patch("config.tasks.send_email_reminder")
    def test_reminder_sent_for_upcoming_sessions(self, mock_send_email):

        tomorrow = timezone.now() + timedelta(days=1)
        MeditationSession.objects.create(
            name="Test Session1",
            description="Test description",
            duration=60,
            start_time=tomorrow,
            instructor=self.instructor,
        )

        check_sessions_for_reminder()
        self.assertTrue(mock_send_email.called)
