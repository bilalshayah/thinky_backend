# views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer
from rest_framework.generics import RetrieveUpdateDestroyAPIView, ListCreateAPIView
from .models import User, Classroom 
from datetime import date
from drf_spectacular.utils import extend_schema, OpenApiTypes
from levels.models import UserUnlockedCard
from game_sessions.models import GameSession
import random
import string
from questions.models import Question
from questions.serializers import QuestionBankSerializer
# --- سيريالايزر مساعد لعرض بيانات الملف الشخصي في Swagger ---
class UserProfileResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    age = serializers.IntegerField()
    total_points = serializers.IntegerField()
    gender = serializers.CharField()
    gender_display = serializers.CharField()


class ClassSerializer(serializers.Serializer):
    name = serializers.CharField()

class JoinClassSerializer(serializers.Serializer):
    code = serializers.CharField()

class BankSerializer(serializers.Serializer):
    level_id = serializers.IntegerField()
    # نستخدم ListField لكي نرسل قائمة من الأرقام [1, 2, 3]
    question_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="قائمة بـ IDs الأسئلة المختارة"
    )
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
        "gender_display": user.get_gender_display(),
        "streak_count":user.streak_count
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_library(request):
    
    # جلب السجلات المرتبطة بالمستخدم مع بيانات البطاقة
    unlocked_entries = UserUnlockedCard.objects.filter(user=request.user).select_related('card')
    
    # تنسيق البيانات لترسل لـ Flutter
    cards_data = []
    for entry in unlocked_entries:
        cards_data.append({
            "planet_name": entry.card.planet_name,
            "unlocked_at": entry.unlocked_at.strftime("%Y-%m-%d")
        })
    
    return Response({
        "total_cards": len(cards_data),
        "library": cards_data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=403)


    classrooms = Classroom.objects.filter(teacher=request.user)
    
    results = []
    for classroom in classrooms:
        # جلب جميع الطلاب في هذا الفصل
        student_ids = classroom.students.values_list('id', flat=True)
        
        # جلب جميع محاولات هؤلاء الطلاب في جميع المستويات
        all_sessions = GameSession.objects.filter(user_id__in=student_ids, is_active=False).select_related('user', 'levelid')
        
        # تنظيم البيانات حسب المستوى
        level_reports = {}
        for s in all_sessions:
            lv_num = s.levelid.level_number
            if lv_num not in level_reports:
                level_reports[lv_num] = []
            
            level_reports[lv_num].append({
                "student_name": s.user.username,
                "score": s.score
            })

        results.append({
            "class_name": classroom.name,
            "class_code": classroom.class_code,
            "performance_by_level": level_reports # سيعيد قاموساً: { "1": [{"student": "Sami", "score": 80}, ...], "2": [...] }
        })

    return Response(results)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="جلب تقارير أداء الطلاب في الفصل الخاص بالمعلم"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_dashboard(request):
    if request.user.role != 'PARENT':
        return Response({"error": "Unauthorized"}, status=403)

    children = request.user.parent_of.all()
    
    children_stats = []
    for child in children:
        # جلب جميع الجلسات المنتهية لهذا الطفل مرتبة من الأحدث
        sessions = GameSession.objects.filter(user=child, is_active=False).select_related('levelid').order_by('-id')
        
        level_history = []
        for s in sessions:
            level_history.append({
                "level_number": s.levelid.level_number,
                "score": f"{s.score}%",
                "date": s.created_at.strftime("%Y-%m-%d")
            })

        children_stats.append({
            "name": child.username,
            "total_points": child.total_points,
            "streak": child.streak_count,
            "level_performance": level_history # قائمة بكل المستويات ودرجاتها
        })

    return Response(children_stats)

@extend_schema(
    request=ClassSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_classroom(request):
    # التأكد أن المستخدم معلم
    if request.user.role != 'TEACHER':
        return Response({"error": "Only teachers can create classes"}, status=403)
    
    name = request.data.get("name")
    if not name:
        return Response({"error": "Class name is required"}, status=400)

    # توليد كود عشوائي فريد من 6 أرقام وحروف
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    classroom = Classroom.objects.create(
        name=name,
        teacher=request.user,
        class_code=code
    )
    
    return Response({
        "message": "Class created successfully",
        "class_name": classroom.name,
        "class_code": classroom.class_code
    })


@extend_schema(
    request=JoinClassSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_classroom(request):
    # التأكد أن المستخدم طالب
    if request.user.role != 'STUDENT':
        return Response({"error": "Only students can join classes"}, status=403)
    
    code = request.data.get("class_code")
    try:
        classroom = Classroom.objects.get(class_code=code)
        classroom.students.add(request.user) # ربط الطالب بالفصل
        return Response({"message": f"Successfully joined {classroom.name}"})
    except Classroom.DoesNotExist:
        return Response({"error": "Invalid class code"}, status=404)
    


class AddChildInputSerializer(serializers.Serializer):
    child_username = serializers.CharField(help_text="اسم المستخدم الخاص بالطفل الذي تريد إضافته")

@extend_schema(
    request=AddChildInputSerializer, # هكذا سيظهر الحقل في Swagger
    responses={200: OpenApiTypes.OBJECT},
    description="ربط الوالد بطفله عن طريق اسم المستخدم الخاص بالطفل"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_child(request):
    if request.user.role != 'PARENT':
        return Response({"error": "Only parents can add children"}, status=403)
    
    child_username = request.data.get("child_username")
    try:
        
        child = User.objects.get(username=child_username, role='STUDENT')
        request.user.children.add(child) # ربط الوالد بالطفل
        return Response({"message": f"Child {child_username} added successfully"})
    except User.DoesNotExist:
        return Response({"error": "Child not found"}, status=404)
    


@extend_schema(
    responses={200: QuestionBankSerializer(many=True)},
    description="عرض قائمة الأسئلة المتاحة في المستوى ليختار منها المعلم"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_level_question_bank(request, level_id):
    """جلب كل الأسئلة العامة لمستوى معين ليختار منها المعلم"""
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=403)
    

    # نجلب الأسئلة العامة (التي ليس لها معلم) المرتبطة بهذا المستوى
    questions = Question.objects.filter(level_id=level_id, created_by__isnull=True)
    serializer = QuestionBankSerializer(questions, many=True)
    return Response(serializer.data)

@extend_schema(
    request=BankSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_create_homework(request):
    """حفظ الواجب المكون من أسئلة اختارها المعلم"""
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=403)

    level_id = request.data.get("level_id") # المستوى الأصلي
    selected_ids = request.data.get("question_ids") # قائمة الـ IDs المختارة

    try:
        from levels.models import Level
        original_level = Level.objects.get(id=level_id)
        
        # إنشاء مستوى "واجب" جديد مستنسخ من الأصلي
        homework_level = Level.objects.create(
            level_number=original_level.level_number,
            is_homework=True,
            teacher=request.user,
            required_score=original_level.required_score
        )

        # ربط الأسئلة المختارة بهذا الواجب الجديد
        from questions.models import Question
        Question.objects.filter(id__in=selected_ids).update(level=homework_level)

        return Response({"message": "Homework created!", "homework_level_id": homework_level.id})
    except Exception as e:
        return Response({"error": str(e)}, status=400)