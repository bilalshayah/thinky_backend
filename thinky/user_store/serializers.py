from rest_framework import serializers
from .models import UserStore


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStore
        fields = "__all__"