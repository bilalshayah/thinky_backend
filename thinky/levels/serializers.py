from rest_framework import serializers
from .models import Level , UserLevel


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = "__all__"

class UserLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLevel
        fields = "__all__"


class LevelStatusSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.SerializerMethodField()
    is_completed = serializers.SerializerMethodField()

    class Meta:
        model = Level
        fields = ['id', 'level_number', 'required_score', 'intro_message', 'is_completed','is_unlocked']

    def get_is_unlocked(self, obj):
        user = self.context.get('request').user
        user_level = UserLevel.objects.filter(user=user, level=obj).first()
        return user_level.is_unlocked if user_level else (obj.level_number == 1)

    def get_is_completed(self, obj):
        user = self.context.get('request').user
        user_level = UserLevel.objects.filter(user=user, level=obj).first()
        return user_level.is_completed if user_level else False