from django.db import models
from django.conf import settings
from levels.models import Level
# Create your models here.
class GameSession(models.Model):
    PHASE_CHOICES = [('analysis', 'Analysis'), ('training', 'Training'), ('testing', 'Testing')]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    levelid= models.ForeignKey(Level, on_delete=models.CASCADE)
    energy = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default='analysis')
    is_active = models.BooleanField(default=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished = models.BooleanField(default=False)

    
    current_group = models.CharField(max_length=50, null=True, blank=True) # MASTER, STRUGGLER, etc.
    next_difficulty = models.CharField(max_length=20, default='medium')   # easy, medium, hard
    active_character = models.CharField(max_length=50, default='hakeem')  # hakeem, villain
    ai_message = models.TextField(null=True, blank=True)                # رسالة Gemini
    target_skill = models.ForeignKey('questions.Skill', on_delete=models.SET_NULL, null=True, blank=True)
    
