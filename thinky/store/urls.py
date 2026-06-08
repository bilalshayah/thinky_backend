from django.urls import path
from .views import StoreDetailView , StoreListCreateView ,buy_item

urlpatterns =[
    path("",StoreListCreateView.as_view()),
    path("<int:pk>/",StoreDetailView.as_view()),
    path("buy/",buy_item)
]