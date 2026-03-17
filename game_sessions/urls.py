from django.urls import path
from . import views

urlpatterns = [

    path('start-session/', views.start_session, name='start_session'),

    path('submit-answer/', views.submit_answer, name='submit_answer'),

    path('next-question/<int:session_id>/', views.get_mission_questions, name='next_question'),

    path('finish-session/', views.finish_stage, name='finish_session'),
    path("",views.SessionListCreateView.as_view()),
    path("<int:pk>/",views.SessionDetailView.as_view())

]