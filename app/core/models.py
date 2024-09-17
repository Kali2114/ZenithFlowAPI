"""
User models.
"""

import uuid
import os

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import (
    models,
    transaction,
)
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone

from core import constants


def avatar_file_path(instance, filename):
    """Generate file path for user avatar."""
    ext = os.path.splitext(filename)[1]
    filename = f"{uuid.uuid4()}{ext}"

    return os.path.join("uploads", "avatar", filename)


class UserManager(BaseUserManager):
    """Manage for users."""

    def create_user(self, email, name, password=None, **kwargs):
        """Create, save and return a new user."""
        if not email:
            raise ValueError("Email is required.")
        if not name:
            raise ValueError("Name is required.")
        user = self.model(
            email=self.normalize_email(email), name=name, **kwargs
        )
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, name, password):
        """Create, save and return a new superuser."""
        user = self.create_user(email=email, name=name, password=password)
        user.is_superuser = True
        user.is_staff = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """User in the system."""

    email = models.EmailField(max_length=255, unique=True)
    name = models.CharField(max_length=255, unique=True)
    date_joined = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"


class UserProfile(models.Model):
    """Model for user pofile."""

    user = models.OneToOneField(
        "User", on_delete=models.CASCADE, related_name="user_profile"
    )
    avatar = models.ImageField(
        upload_to=avatar_file_path, blank=True, null=True
    )
    biography = models.TextField(blank=True, null=True)
    sessions_attended = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.user.name}'s profile"

    def update_sessions_and_time(self):
        """Update the total numer of sessions attended and total time spent."""
        complete_session = self.user.enrollments.filter(
            session__is_completed=True
        ).select_related("session")
        self.sessions_attended = complete_session.count()
        self.total_time_spent = sum(
            enrollment.session.duration for enrollment in complete_session
        )
        self.save()


class MeditationSession(models.Model):
    """Model for meditation session object."""

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    instructor = models.ForeignKey("User", on_delete=models.CASCADE)
    duration = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=constants.MEDITATION_SESSION_CHOICES,
        default="ongoing",
    )
    max_participants = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)
    techniques = models.ManyToManyField("Technique", related_name="sessions")
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} by {self.instructor}"

    @classmethod
    def create(cls, name, instructor, duration, start_time, **kwargs):
        with transaction.atomic():
            existing_session = cls.objects.filter(name__startswith=name)
            count = existing_session.count()

            if count == 0:
                full_name = f"{name} #1"
            else:
                full_name = f"{name} #{count + 1}"

            session = cls(
                name=full_name,
                instructor=instructor,
                duration=duration,
                start_time=start_time,
                **kwargs,
            )
            session.save()
            return session

    def current_participants(self):
        return Enrollment.objects.filter(session=self).count()


class Enrollment(models.Model):
    """Model representing a user's enrollment in a meditation session."""

    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="enrollments"
    )
    session = models.ForeignKey(
        "MeditationSession",
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "session"], name="unique_user_session"
            )
        ]

    def __str__(self):
        return f"User: {self.user} enrolled in {self.session}"


class Technique(models.Model):
    """Model for technique object."""

    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    instructor = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="techniques"
    )

    def __str__(self):
        return self.name


class Rating(models.Model):
    """Model for rating object."""

    session = models.ForeignKey(
        "MeditationSession", on_delete=models.CASCADE, related_name="ratings"
    )
    user = models.ForeignKey(
        "User", on_delete=models.CASCADE, related_name="ratings"
    )
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.name} rated {self.session.name} ({self.rating}/5)"
