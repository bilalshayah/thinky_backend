from rest_framework import serializers
from .models import AnswerAttempt


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerAttempt
        fields = "__all__"