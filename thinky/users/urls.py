from django.urls import path
from .views import register , login , UserListCreateView,UserDetailView, user_profile , get_user_library , create_classroom , parent_dashboard , teacher_dashboard , add_child , join_classroom , get_level_question_bank ,teacher_create_homework

urlpatterns = [
    path("register/", register),
    path("login/", login),
    path('', UserListCreateView.as_view()),
    path('<int:pk>/', UserDetailView.as_view()),
    path("info/",user_profile),
    path("cards/",get_user_library),
    path("classroom/",create_classroom),
    path("parent/",parent_dashboard),
    path("teacher/",teacher_dashboard),
    path("join/",join_classroom),
    path("add_chiled/",add_child),
    path("questions-bank/<int:level_id>",get_level_question_bank),
    path("creating-homework/",teacher_create_homework),
]