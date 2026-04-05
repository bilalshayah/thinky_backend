from django.urls import path
from .views import AnswerDetailView, AnswerListCreateView

urlpatterns = [
    path('', AnswerListCreateView.as_view()),
    path('<int:pk>/', AnswerDetailView.as_view()),
]