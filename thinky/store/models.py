from django.db import models
# Create your models here.
class Store(models.Model):
    name=models.CharField(max_length=100)
    required_points= models.IntegerField()
    description=models.TextField()
    def __str__(self):
        return self.name