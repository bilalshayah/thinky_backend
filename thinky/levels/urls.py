from django.urls import path
from .views import (
    LevelListCreateView, 
    LevelDetailView,  
    UserLevelDetailView, 
    UserLevelListCreateView,  
    get_my_map, 
    WORLDListCreateView,
    WORLDDetailView,
    get_user_worlds ,
    CardDetailView,
    CardListCreateView
)

urlpatterns = [
    # 🗺️ مسارات العوالم والمستويات المخصصة للطفل (Game App APIs)
    path('worlds/my/', get_user_worlds, name='get_user_worlds'),
    path('my-map/', get_my_map, name='user-levels-map'),

    # 🎛️ مسارات الـ CRUD لإدارة العوالم (لوحة التحكم / Admin)
    path('worlds/', WORLDListCreateView.as_view(), name='world-list-create'),
    path('worlds/<int:pk>/', WORLDDetailView.as_view(), name='world-detail-update-delete'),
    
    # 📝 مسارات الـ CRUD لإدارة المستويات العامة
    path('levels/', LevelListCreateView.as_view()),
    path('levels/<int:pk>/', LevelDetailView.as_view()),
    
    # 📊 مسارات الـ CRUD لمتابعة سجلات تقدم الطلاب
    path('user-levels/', UserLevelListCreateView.as_view()),
    path('user-levels/<int:pk>/', UserLevelDetailView.as_view()),
    path('cards/', CardListCreateView.as_view()),
    path('card/<int:pk>/', CardDetailView.as_view()),
    
]