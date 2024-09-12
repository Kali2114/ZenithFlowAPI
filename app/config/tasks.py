"""
Celery tasks.
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from django.core.mail import send_mail

from core.models import MeditationSession, User

import logging

logger = logging.getLogger(__name__)


@shared_task
def send_email_reminder(email, session):
    """Send email reminder for upcoming session."""
    subject = f"Reminder: Upcoming Meditation Session {session.name}"
    message = (
        f"Hi,\n\nThis is a reminder that you are enrolled in the "
        f"meditation session '{session.name}'"
        f" happening on {session.start_time}.\n\n"
        "Please make sure to join on time.\n\n"
        "Best regards,\nZenithFlow"
    )
    logger.info(f"Sending email to {email} for session {session.name}")
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=True,
    )


@shared_task()
def check_sessions_for_reminder():
    """Task to check and send reminders
    for upcoming sessions."""
    logger.info(
        f"Checking sessions for date: "
        f"{timezone.now().date() + timedelta(days=1)}"
    )
    tomorrow = timezone.now().date() + timedelta(days=1)
    print(f"Checking sessions for date: {tomorrow}")
    upcoming_session = MeditationSession.objects.filter(
        start_time__date=tomorrow
    )

    for session in upcoming_session:
        logger.info(f"Found session: {session.name}")
        print(f"Found session: {session.name}")
        users = User.objects.filter(enrollments__session=session)
        for user in users:
            print(f"Sending reminder to {user.email}")
            send_email_reminder(user.email, session)


# @shared_task()
# def check_sessions_for_reminder():
#     """Testowa wersja taska."""
#     send_email_reminder('test@example.com', 'TestSession')
