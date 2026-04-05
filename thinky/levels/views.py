from django.shortcuts import render
from .models import Level , UserLevel
from .serializers import LevelSerializer , UserLevelSerializer
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .serializers import LevelStatusSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class LevelListCreateView(ListCreateAPIView):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer


class LevelDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer



class UserLevelDetailView(RetrieveUpdateDestroyAPIView):
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer

class UserLevelListCreateView(ListCreateAPIView):
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_map(request):
    levels = Level.objects.all().order_by('level_number')
    serializer = LevelStatusSerializer(levels, many=True, context={'request': request})
    
    return Response(serializer.data)