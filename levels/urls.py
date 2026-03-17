from django.urls import path
from .views import LevelListCreateView , LevelDetailView  ,  UserLevelDetailView , UserLevelListCreateView ,  get_my_map

urlpatterns = [
    path('levels/', LevelListCreateView.as_view()),
    path('levels/<int:pk>/', LevelDetailView.as_view()),
        path('user-levels/', UserLevelListCreateView.as_view()),
    path('user-levels/<int:pk>/', UserLevelDetailView.as_view()),
    path('my-map/', get_my_map, name='user-levels-map'),

]
