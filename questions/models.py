from django.db import models
from levels.models import Level
class Skill(models.Model):

    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name  
    

class Question(models.Model):

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    level = models.ForeignKey(Level, on_delete=models.CASCADE,null=True,blank=True)

    question_text = models.TextField()

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE,null=True,blank=True)

    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES,null=True,blank=True)

    option_a = models.CharField(max_length=100)

    option_b = models.CharField(max_length=100)

    option_c = models.CharField(max_length=100)

    option_d = models.CharField(max_length=100)

    correct_answer = models.CharField(max_length=1)

    points = models.IntegerField(default=0)

    is_hakeem = models.BooleanField(default=False)
    
    hint = models.TextField(default=" ")

    explanation = models.TextField(default=' ')
    def __str__(self):
        return self.question_text