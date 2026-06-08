from rest_framework import serializers
from .models import GameSession


class GameSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameSession
        fields = "__all__"