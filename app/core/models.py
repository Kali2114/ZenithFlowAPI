"""
User models.
"""

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


class MeditationSession(models.Model):
    """Model for meditation session object."""
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    instructor = models.ForeignKey('User', on_delete=models.CASCADE)
    duration = models.PositiveIntegerField()
    start_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=constants.MEDITATION_SESSION_CHOICES, default='ongoing')
    max_participants = models.PositiveIntegerField(default=20)
    created_at = models.DateTimeField(auto_now_add=True)

    #TODO Many to many with techniques.

    def __str__(self):
        return f'{self.name} by {self.instructor}'

    @classmethod
    def create(cls, name, instructor, duration, start_time, **kwargs):
        with transaction.atomic():
            existing_session = cls.objects.filter(name__startswith=name)
            count = existing_session.count()

            if count == 0:
                full_name = f'{name} #1'
            else:
                full_name = f'{name} #{count + 1}'

            session = cls(
                name=full_name,
                instructor=instructor,
                duration=duration,
                start_time=start_time,
                **kwargs
            )
            session.save()
            return session
