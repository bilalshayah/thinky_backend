from django.contrib.auth.models import AbstractUser
from django.db import models


# models.py
class User(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    ROLE_CHOICES = [
        ('STUDENT', 'Student'),
        ('TEACHER', 'Teacher'),
        ('PARENT', 'Parent'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STUDENT')
    
    # حقل إضافي للوالدين لربطهم بأطفالهم
    # الوالد يمكنه مراقبة أكثر من طفل، والطفل يراقبه والد واحد (أو أكثر)
    parent_of = models.ManyToManyField(
        'self', 
        blank=True, 
        symmetrical=False, 
        related_name='parents',
        limit_choices_to={'role': 'STUDENT'}
    )

    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    total_points = models.IntegerField(default=0)
    streak_count = models.IntegerField(default=0)
    last_activity_date = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='M') 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
    
# models.py

class Classroom(models.Model):
    name = models.CharField(max_length=100) # مثلاً: فصل الأبطال
    teacher = models.ForeignKey(
        'User', 
        on_delete=models.CASCADE, 
        related_name='teacher_chapters',
        limit_choices_to={'role': 'TEACHER'}
    )
    # كود فريد يعطيه المعلم للطلاب لينضموا للفصل
    class_code = models.CharField(max_length=8, unique=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    students = models.ManyToManyField(User, related_name='joined_classes', blank=True)

    def __str__(self):
        return f"{self.name} - {self.teacher.username}"