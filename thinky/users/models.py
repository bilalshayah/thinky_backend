from django.contrib.auth.models import AbstractUser
from django.db import models


# models.py
class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    total_points = models.IntegerField(default=0)
    # إضافة حقل الجنس هنا
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M') 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username