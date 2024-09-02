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


class MeditationSessionDetailSerializer(serializers.ModelSerializer):
    """Serializer for meditation session detail view."""

    class Meta(MeditationSessionSerializer.Meta):
        fields = MeditationSessionSerializer.Meta.fields + [
            'instructor',
            'description',
            'duration',
            'status',
            'max_participants',
            'created_at'
        ]
        read_only_fields = MeditationSessionSerializer.Meta.read_only_fields + ['instructor']
