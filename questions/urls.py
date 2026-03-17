from django.urls import path
from .views import QuestionListCreateView , QusetionDetailView , SkillDetailView , SkillListCreateView

urlpatterns = [
    path('', QuestionListCreateView.as_view()),
    path('<int:pk>/', QusetionDetailView.as_view()),
        path('skill/', SkillListCreateView.as_view()),
    path('skill/<int:pk>/', SkillDetailView.as_view()),
]