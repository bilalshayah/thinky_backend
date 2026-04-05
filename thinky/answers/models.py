from django.db import models
from django.conf import settings
from questions.models import Question
from game_sessions.models import GameSession


class AnswerAttempt(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    session = models.ForeignKey(GameSession, on_delete=models.CASCADE)

    question = models.ForeignKey(Question, on_delete=models.CASCADE)

    selected_answer = models.CharField(max_length=1)

    is_correct = models.BooleanField()

    #attempt_number = models.IntegerField()

    time_taken = models.FloatField()

    hints_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)