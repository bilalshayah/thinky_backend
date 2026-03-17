from django.db import models
from django.conf import settings
from questions.models import Question
from store.models import Store
# Create your models here.

class Points(models.Model):

    TRANSACTION_TYPE = [
        ('earn', 'Earn'),
        ('spend', 'Spend'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    amount = models.IntegerField()

    type = models.CharField(max_length=10, choices=TRANSACTION_TYPE)

    question = models.ForeignKey(
    Question,
    on_delete=models.CASCADE,
    related_name="point_transactions",
    null=True,blank=True
     )

    store_item = models.ForeignKey(
        Store,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(auto_now_add=True)