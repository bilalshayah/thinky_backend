from django.contrib import admin
from .models import Level, UserLevel, PlanetCard , UserUnlockedCard
# Register your models here.
admin.site.register(Level)
admin.site.register(UserLevel)
admin.site.register(PlanetCard)
admin.site.register(UserUnlockedCard)