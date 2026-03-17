from django.db import models
from django.conf import settings
# Create your models here.
class Level(models.Model):

    level_number = models.IntegerField()
    required_score = models.IntegerField(default=50)


    def __str__(self):
        return str(self.level_number)
    

class UserLevel(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    level = models.ForeignKey(Level, on_delete=models.CASCADE)

    is_unlocked = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'level')

class StudentSkillMastery(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    skill = models.ForeignKey('questions.Skill', on_delete=models.CASCADE)
    mastery_score = models.FloatField(default=0.0) # القيمة التي سيقوم الـ AI بتعديلها
    last_attempt_date = models.DateTimeField(auto_now=True)