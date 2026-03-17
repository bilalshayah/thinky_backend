from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    email = models.EmailField(blank=True, null=True)

    phone_number = models.CharField(max_length=15, blank=True, null=True)

    birthday = models.DateField(blank=True, null=True)

    total_points = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username