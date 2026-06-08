from django.db import models
from django.conf import settings
from store.models import Store

class UserStore(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    item = models.ForeignKey(Store, on_delete=models.CASCADE)

