from django.shortcuts import render
from .models import Points
from rest_framework.generics import ListCreateAPIView , RetrieveUpdateDestroyAPIView
from .serializers import PointsSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from rest_framework.decorators import permission_classes , api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
# Create your views here
class PointsListCreateView(ListCreateAPIView):
    queryset = Points.objects.all()
    serializer_class = PointsSerializer

class UserPointsTransactions(generics.ListAPIView):

    serializer_class = PointsSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return Points.objects.filter(user_id=user_id).order_by('-created_at')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_points(request):
    my_points= Points.objects.filter(user = request.user)
    serializer = PointsSerializer(my_points,many=True)
    return Response(serializer.data)