from django.urls import path
from .views import LevelListCreateView , LevelDetailView  ,  UserLevelDetailView , UserLevelListCreateView ,  get_my_map, get_game_worlds, get_world_levels, WORLDListCreateView

urlpatterns = [
    path('levels/', LevelListCreateView.as_view()),
    path('add-worlds/', WORLDListCreateView.as_view()),
    path('levels/<int:pk>/', LevelDetailView.as_view()),
        path('user-levels/', UserLevelListCreateView.as_view()),
    path('user-levels/<int:pk>/', UserLevelDetailView.as_view()),
    path('my-map/', get_my_map, name='user-levels-map'),
    path('worlds',get_game_worlds),
    path('world-levels/<str:world_slug>/',get_world_levels),
    


]
