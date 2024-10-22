"""
Serializers for the user API.
"""

from django.contrib.auth import (
    get_user_model,
    authenticate,
)
from django.utils.translation import gettext as _
from rest_framework import serializers

from core.models import (
    UserProfile,
    Subscription,
    Message,
    InstructorRating,
    PanelAdmin,
    MeditationSession,
)


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get("email")
        password = attrs.get("password")
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            msg = _("Unable to authenticate with provided credentials.")
            raise serializers.ValidationError(msg, code="authorization")

        attrs["user"] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""

    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "user",
            "biography",
            "avatar",
            "sessions_attended",
            "total_time_spent",
        ]
        read_only_fields = ["sessions_attended", "total_time_spent"]


class UserAvatarSerializer(serializers.ModelSerializer):
    """Serializer for uploading avatars to users."""

    class Meta:
        model = UserProfile
        fields = ["id", "avatar"]
        read_only_fields = ["id"]
        extra_kwargs = {"avatar": {"required": "False"}}


class SubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for subscriptions."""

    class Meta:
        model = Subscription
        fields = ["id", "user", "start_date", "end_date", "cost", "is_active"]
        read_only_fields = [
            "id",
            "user",
            "start_date",
            "end_date",
            "cost",
            "is_active",
        ]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for the message object."""

    sender = serializers.ReadOnlyField(source="sender.id")
    receiver = serializers.PrimaryKeyRelatedField(
        queryset=get_user_model().objects.all()
    )

    class Meta:
        model = Message
        fields = [
            "id",
            "sender",
            "receiver",
            "content",
            "timestamp",
            "is_read",
        ]
        read_only_fields = ["id", "sender", "timestamp", "is_read"]


class InstructorRatingSerializer(serializers.ModelSerializer):
    """Serializer for the instructor rating object."""

    class Meta:
        model = InstructorRating
        fields = [
            "id",
            "user",
            "instructor",
            "rating",
            "comment",
            "created_at",
        ]
        read_only_fields = ["id", "user", "created_at"]

    def validate_rating(self, value):
        """Validate the rating value to ensure it is between 1 and 5."""
        if value <= 0 or value > 5:
            raise serializers.ValidationError(
                "Rating must be between 1 and 5."
            )
        return value

    def validate_comment(self, value):
        """Validate that the comment has at least 6 characters"""
        if len(value) < 6:
            raise serializers.ValidationError(
                "Comment must have at least 6 characters."
            )
        return value


class PanelAdminSerializer(serializers.ModelSerializer):
    """Serializer for panel admin object."""

    all_users = serializers.SerializerMethodField()
    active_subscribers = serializers.SerializerMethodField()
    all_sessions = serializers.SerializerMethodField()
    instructor_sessions = serializers.SerializerMethodField()
    participants_per_session = serializers.SerializerMethodField()

    class Meta:
        model = PanelAdmin
        fields = [
            "all_users",
            "active_subscribers",
            "all_sessions",
            "instructor_sessions",
            "participants_per_session",
        ]

    def get_all_users(self, obj):
        """Get all registered users."""
        return get_user_model().objects.count()

    def get_active_subscribers(self, obj):
        """Get count of active subscribers."""
        return Subscription.objects.filter(is_active=True).count()

    def get_all_sessions(self, obj):
        """Get count of all meditation sessions."""
        return MeditationSession.objects.count()

    def get_instructor_sessions(self, obj):
        """Get count of sessions conducted by the logged-in instructor."""
        return MeditationSession.objects.filter(
            instructor=obj.instructor
        ).count()

    def get_participants_per_session(self, obj):
        """Get list of sessions with the number of participants."""
        sessions = MeditationSession.objects.filter(instructor=obj.instructor)
        return {
            session.name: session.enrollments.count() for session in sessions
        }
