from django.urls import path
from .views import UserPointsTransactions, PointsListCreateView ,get_my_points

urlpatterns = [
    path("", PointsListCreateView.as_view()),
    path("<int:pk>/",UserPointsTransactions.as_view()),
    path("my-points/",get_my_points)

]