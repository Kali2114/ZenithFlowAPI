"""
Serializers for meditation session APIs.
"""

from rest_framework import serializers

from core.models import MeditationSession


class MeditationSessionSerializer(serializers.ModelSerializer):
    """Serializer for meditation sessions."""

    class Meta:
        model = MeditationSession
        fields = ["id", "name", "start_time"]
        read_only_fields = ["id"]
