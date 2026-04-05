# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from .models import User
from datetime import date
from drf_spectacular.utils import extend_schema, OpenApiTypes

# --- سيريالايزر مساعد لعرض بيانات الملف الشخصي في Swagger ---
class UserProfileResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    age = serializers.IntegerField()
    total_points = serializers.IntegerField()
    gender = serializers.CharField()
    gender_display = serializers.CharField()

# --- الـ Views ---

@extend_schema(
    request=RegisterSerializer,
    responses={201: OpenApiTypes.OBJECT},
    description="إنشاء حساب مستخدم جديد مع تحديد الجنس (M/F)"
)
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


@extend_schema(
    request=LoginSerializer,
    responses={200: OpenApiTypes.OBJECT},
    description="تسجيل الدخول والحصول على التوكن (Access & Refresh)"
)
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
    """عرض قائمة المستخدمين أو إنشاء مستخدم جديد"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    """عرض، تحديث، أو حذف بيانات مستخدم محدد"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    responses={200: UserProfileResponseSerializer},
    description="جلب بيانات الملف الشخصي للمستخدم وحساب عمره وجنسه"
)
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
        "total_points": user.total_points,
        "gender": user.gender,
        "gender_display": user.get_gender_display()
    }

    return Response(data)