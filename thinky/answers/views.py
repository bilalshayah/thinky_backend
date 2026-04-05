from django.shortcuts import render
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListCreateAPIView
from .models import AnswerAttempt
from .serializers import AnswerSerializer
# Create your views here.

class AnswerListCreateView(ListCreateAPIView):
    queryset = AnswerAttempt.objects.all()
    serializer_class = AnswerSerializer

class AnswerDetailView(RetrieveUpdateDestroyAPIView):
    queryset = AnswerAttempt.objects.all()
    serializer_class = AnswerSerializer