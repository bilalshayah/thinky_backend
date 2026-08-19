from django.urls import path
from .views import (
    register, 
    login, 
    UserListCreateView, 
    UserDetailView, 
    user_profile, 
    get_user_library, 
    create_classroom, 
    parent_dashboard, 
    teacher_dashboard, 
    add_child, 
    join_classroom, 
    get_level_question_bank, 
    create_homework, 
    add_homework_question, 
    get_student_classroom_homeworks,
)

urlpatterns = [
    path("register/", register, name='register'),
    path("login/", login, name='login'),
    path('', UserListCreateView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path("info/", user_profile, name='user-profile'),
    path("cards/", get_user_library, name='user-library'),
    path("classroom/", create_classroom, name='create-classroom'),
    path("parent/", parent_dashboard, name='parent-dashboard'),
    path("teacher/", teacher_dashboard, name='teacher-dashboard'),
    path("join/", join_classroom, name='join-classroom'),
    path("add_child/", add_child, name='add-child'),
    
    # 🌟 مسارات الواجبات وبنك الأسئلة
    path('question-bank/', get_level_question_bank, name='get_question_bank_query'),
    path('question-bank/<int:level_id>/', get_level_question_bank, name='get_question_bank_path'),
    path('homeworks/', create_homework, name='create_homework'),
    path('homework-questions/', add_homework_question, name='add_homework_question'),
    path('classrooms/<int:classroom_id>/homeworks/', get_student_classroom_homeworks, name='student-classroom-homeworks'),

]