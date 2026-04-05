from django.urls import path
from .views import register , login , UserListCreateView,UserDetailView, user_profile

urlpatterns = [
    path("register/", register),
    path("login/", login),
    path('', UserListCreateView.as_view()),
    path('<int:pk>/', UserDetailView.as_view()),
    path("info/",user_profile)
]