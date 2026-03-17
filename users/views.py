from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny ,IsAuthenticated
from rest_framework.decorators import permission_classes
from .serializers import RegisterSerializer , LoginSerializer , UserSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListCreateAPIView
from .models import User
from datetime import date

@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):

    serializer = RegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "User created successfully"},
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=400)

@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):

    serializer = LoginSerializer(data=request.data)

    if serializer.is_valid():

        user = serializer.validated_data["user"]
        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        user_data = UserSerializer(user).data

        return Response({
            "access": access,
            "refresh": refresh,
            "user": user_data
        })

    return Response(serializer.errors, status=400)


class UserListCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):

    user = request.user

    age = None

    if user.birthday:

        today = date.today()
        birthday = user.birthday

        age = today.year - birthday.year - (
            (today.month, today.day) < (birthday.month, birthday.day)
        )

    data = {
        "username": user.username,
        "age": age,
        "total_points": user.total_points
    }

    return Response(data)