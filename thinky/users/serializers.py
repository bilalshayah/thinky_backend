from rest_framework import serializers
from .models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from levels.models import Level, UserLevel

class UserSerializer(serializers.ModelSerializer):
    # حقل إضافي لعرض الكلمة كاملة (Male/Female) بدلاً من الحرف فقط
    gender_display = serializers.CharField(source='get_gender_display', read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "email", "phone_number", 
            "birthday", "gender", "gender_display", "total_points","streak_count","role"
        ]
        extra_kwargs = {
            "password": {"write_only": True}
        }

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='STUDENT')

    class Meta:
        model = User
        fields = [
            "username", 
            "password", 
            "phone_number", 
            "birthday",
            "gender" ,
            "role"
        ]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            phone_number=validated_data.get("phone_number"),
            birthday=validated_data.get("birthday"),
            gender=validated_data.get("gender", "M") ,
            role=validated_data.get("role", "STUDENT")
        )

        # منطق فتح المستوى الأول (بقي كما هو)
        if user.role == 'STUDENT':
            first_level = Level.objects.order_by("level_number").first()
            if first_level:
                UserLevel.objects.get_or_create(user=user, level=first_level, is_unlocked=True)

        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError("Invalid username or password")

        refresh = RefreshToken.for_user(user)

        return {
            "user": user,
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        }

# --- Serializers المخصصة لهيكلية الواجبات الجديدة ---

class CreateHomeworkSerializer(serializers.Serializer):
    level_id = serializers.IntegerField(required=True)
    classroom_id = serializers.IntegerField(required=True)  # 🔑 إضافة حقل رقم الصف

class AddSingleQuestionSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField(required=True)
    question_text = serializers.CharField(required=True)
    option_a = serializers.CharField(required=True)
    option_b = serializers.CharField(required=True)
    option_c = serializers.CharField(required=True)
    option_d = serializers.CharField(required=True)
    correct_answer = serializers.CharField(max_length=1)
    points= serializers.IntegerField(required=True)
    hint = serializers.CharField(required=False, allow_blank=True, default="")
    skill_name = serializers.CharField(required=False, default="General") # إتاحة اختيار المهارة