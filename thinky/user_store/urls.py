from django.urls import path
from .views import get_my_items
#from .views import  UserStoreDetailView ,UserStoreListCreateView 

urlpatterns = [
    #path("",UserStoreListCreateView.as_view()),
    #path("<int:pk>/",UserStoreDetailView.as_view()),
path('my-store', get_my_items),
]