from django.urls import path
from .views import UserStoreDetailView ,UserStoreListCreateView , get_my_items

urlpatterns = [
    path("",UserStoreListCreateView.as_view()),
    path("<int:pk>/",UserStoreDetailView.as_view()),
path('my-store', get_my_items),
]