from django.db import models
from django.conf import settings
# Create your models here.

class GameWorld(models.Model):
    name = models.CharField(max_length=100) # الاسم المعروض (الفضاء، الغابة)
    is_active = models.BooleanField(default=False) # تفعيل العالم برمجياً أو تركه كواجهة فقط
    description = models.TextField(blank=True, null=True)
    points_to_open = models.IntegerField(default=0)

    def __str__(self):
        return self.name 
    

class Level(models.Model):

    level_number = models.IntegerField()
    required_score = models.IntegerField(default=50)
    intro_message = models.TextField(default="")
    planet_name = models.CharField(max_length=100, blank=True, null=True)
    is_homework= models.BooleanField(default=False)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="created_levels"
    ) # المعلم الذي أنشأ هذا الواجب
    classroom = models.ForeignKey(
        'users.Classroom',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="homework_levels"
    )
    world = models.ForeignKey(GameWorld, on_delete=models.SET_NULL, null=True, blank=True, related_name='levels')


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


class PlanetCard(models.Model):
    planet_name = models.CharField(max_length=100, unique=True)
    unlock_at_level_number = models.IntegerField() 

    def __str__(self):
        return self.planet_name
    
class UserUnlockedCard(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    card = models.ForeignKey(PlanetCard, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'card')



