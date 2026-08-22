import random
import string
from datetime import date

from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import OpenApiTypes, extend_schema

from .models import Classroom, User
from .serializers import (
    LoginSerializer, 
    RegisterSerializer, 
    UserSerializer, 
    CreateHomeworkSerializer, 
    AddSingleQuestionSerializer
)

# استيرادات من تطبيقات أخرى داخل المشروع
from game_sessions.models import GameSession
from levels.models import Level, UserUnlockedCard
from questions.models import Question, Skill
from questions.serializers import QuestionBankSerializer


# --- Serializers المساعدة لـ Swagger ---
class UserProfileResponseSerializer(serializers.Serializer):
    username = serializers.CharField()
    age = serializers.IntegerField()
    total_points = serializers.IntegerField()
    gender = serializers.CharField()
    gender_display = serializers.CharField()
    streak_count = serializers.IntegerField()

class ClassSerializer(serializers.Serializer):
    name = serializers.CharField()

class JoinClassSerializer(serializers.Serializer):
    code = serializers.CharField()

class AddChildInputSerializer(serializers.Serializer):
    child_username = serializers.CharField(help_text="اسم المستخدم الخاص بالطفل")
    child_password = serializers.CharField(write_only=True, help_text="كلمة مرور حساب الطفل للتأكيد")


# --- Views ---

@extend_schema(
    request=RegisterSerializer,
    responses={201: OpenApiTypes.OBJECT},
    description="إنشاء حساب مستخدم جديد"
)
@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "User created successfully"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    responses={200: UserProfileResponseSerializer},
    description="جلب بيانات الملف الشخصي للمستخدم"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    today = date.today()
    age = None

    if user.last_activity_date:
        days_passed = (today - user.last_activity_date).days
        if days_passed > 1:
            user.streak_count = 0
            user.save(update_fields=['streak_count'])

    if user.birthday:
        birthday = user.birthday
        age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))

    data = {
        "username": user.username,
        "age": age,
        "total_points": user.total_points,
        "gender": user.gender,
        "gender_display": user.get_gender_display(),
        "streak_count": user.streak_count
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_library(request):
    unlocked_entries = UserUnlockedCard.objects.filter(user=request.user).select_related('card')
    cards_data = [
        {
            "planet_name": entry.card.planet_name,
            "unlocked_at": entry.unlocked_at.strftime("%Y-%m-%d")
        }
        for entry in unlocked_entries
    ]
    return Response({"total_cards": len(cards_data), "library": cards_data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_dashboard(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    classrooms = Classroom.objects.filter(teacher=request.user)
    results = []
    
    for classroom in classrooms:
        student_ids = classroom.students.values_list('id', flat=True)
        all_sessions = GameSession.objects.filter(user_id__in=student_ids, is_active=False).select_related('user', 'levelid')
        
        level_reports = {}
        for s in all_sessions:
            lv_num = s.levelid.level_number
            if lv_num not in level_reports:
                level_reports[lv_num] = []
            
            level_reports[lv_num].append({
    "student_name": s.user.username,
    "score": s.score,
    "ai_group": s.current_group if s.current_group else "N/A"  # 🌟 أضيفي هذا السطر هنا
})

        results.append({
            "class_name": classroom.name,
            "class_code": classroom.class_code,
            "performance_by_level": level_reports
        })

    return Response(results)


@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="جلب تقارير أداء الأطفال المرتبطين بحساب الوالد"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def parent_dashboard(request):
    if request.user.role != 'PARENT':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    children = request.user.parent_of.all()
    children_stats = []
    
    for child in children:
        sessions = GameSession.objects.filter(user=child, is_active=False).select_related('levelid').order_by('-id')
        
        # 🌟 جلب أحدث جلسة للحصول على النمط المحفوظ
        latest_session = sessions.first()
        student_group = latest_session.current_group if (latest_session and latest_session.current_group) else "N/A"

        level_history = [
            {
                "level_number": s.levelid.level_number,
                "score": f"{s.score}%",
            }
            for s in sessions
        ]

        children_stats.append({
            "name": child.username,
            "total_points": child.total_points,
            "streak": child.streak_count,
            "ai_group": student_group,  # 🌟 تم إضافة اسم المجموعة هنا
            "level_performance": level_history
        })

    return Response(children_stats)


@extend_schema(request=ClassSerializer, responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_classroom(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Only teachers can create classes"}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get("name")
    if not name:
        return Response({"error": "Class name is required"}, status=status.HTTP_400_BAD_REQUEST)

    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    classroom = Classroom.objects.create(name=name, teacher=request.user, class_code=code)
    
    return Response({
        "message": "Class created successfully",
        "classroom_id": classroom.id,
        "class_name": classroom.name,
        "class_code": classroom.class_code
    })

@extend_schema(
    responses={200: OpenApiTypes.OBJECT},
    description="جلب كافة الصفوف التي أنشأها المعلم مع كود الصف وعدد الطلاب"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_teacher_classrooms(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized. Only teachers can view their classrooms."}, status=status.HTTP_403_FORBIDDEN)

    classrooms = Classroom.objects.filter(teacher=request.user)
    
    data = [
        {
            "classroom_id": classroom.id,
            "name": classroom.name,
            "class_code": classroom.class_code,
            "students_count": classroom.students.count(),
            "created_at": classroom.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        for classroom in classrooms
    ]

    return Response(data, status=status.HTTP_200_OK)


@extend_schema(request=JoinClassSerializer, responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def join_classroom(request):
    if request.user.role != 'STUDENT':
        return Response({"error": "Only students can join classes"}, status=status.HTTP_403_FORBIDDEN)
    
    code = request.data.get("code")
    try:
        classroom = Classroom.objects.get(class_code=code)
        classroom.students.add(request.user)
        return Response({"message": f"Successfully joined {classroom.name}","classroom_id": classroom.id,})
    except Classroom.DoesNotExist:
        return Response({"error": "Invalid class code"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(request=AddChildInputSerializer, responses={200: OpenApiTypes.OBJECT})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_child(request):
    if request.user.role != 'PARENT':
        return Response({"error": "Only parents can add children"}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = AddChildInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    child_username = serializer.validated_data.get("child_username")
    child_password = serializer.validated_data.get("child_password")
    
    try:
        child = User.objects.get(username=child_username, role='STUDENT')
        if not child.check_password(child_password):
            return Response({"error": "كلمة المرور الخاصة بالطفل غير صحيحة!"}, status=status.HTTP_401_UNAUTHORIZED)
            
        request.user.parent_of.add(child) 
        return Response({"message": f"Successfully linked with child {child_username}"})
    except User.DoesNotExist:
        return Response({"error": "Child not found"}, status=status.HTTP_404_NOT_FOUND)


# 🌟 دالة جلب بنك الأسئلة الموحدة (تدعم كلاً من Path parameter و Query parameter)
@extend_schema(
    responses={200: QuestionBankSerializer(many=True)},
    description="جلب كافة تفاصيل الأسئلة المتاحة لمستوى معين معلم لتمكينه من اختيار الأسئلة"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_level_question_bank(request, level_id=None):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)
    
    target_level_id = level_id or request.query_params.get('level_id')
    if not target_level_id:
        return Response({"error": "level_id parameter is required"}, status=status.HTTP_400_BAD_REQUEST)

    questions = Question.objects.filter(level_id=target_level_id, created_by__isnull=True)
    serializer = QuestionBankSerializer(questions, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=CreateHomeworkSerializer,
    responses={201: OpenApiTypes.OBJECT},
    description="تأسيس الواجب ببياناته الأساسية وإرجاع ID الواجب ورقم الصف"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_homework(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CreateHomeworkSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    level_id = serializer.validated_data["level_id"]
    classroom_id = serializer.validated_data["classroom_id"]

    try:
        classroom = Classroom.objects.get(id=classroom_id, teacher=request.user)
        original_level = Level.objects.get(id=level_id)
        
        homework_level = Level.objects.create(
            level_number=original_level.level_number,
            is_homework=True,
            teacher=request.user,
            classroom=classroom,
            required_score=original_level.required_score
        )

        return Response({
            "message": "Homework created successfully for this classroom",
            "assignment_id": homework_level.id,
            "classroom_id": classroom.id
        }, status=status.HTTP_201_CREATED)

    except Classroom.DoesNotExist:
        return Response({"error": "Classroom not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)
    except Level.DoesNotExist:
        return Response({"error": "Original level not found"}, status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    request=AddSingleQuestionSerializer,
    responses={201: OpenApiTypes.OBJECT},
    description="إضافة سؤال مخصص أو اختيار سؤال من البنك وربطه بالواجب"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_homework_question(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

    serializer = AddSingleQuestionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    assignment_id = data["assignment_id"]

    try:
        homework_level = Level.objects.get(id=assignment_id, is_homework=True, teacher=request.user)
        skill_name = data.get("skill_name", "General")
        default_skill, _ = Skill.objects.get_or_create(name=skill_name)

        question = Question.objects.create(
            level=homework_level,
            question_text=data['question_text'],
            option_a=data['option_a'],
            option_b=data['option_b'],
            option_c=data['option_c'],
            option_d=data['option_d'],
            correct_answer=data['correct_answer'].upper(),
            hint=data.get('hint', ''),
            skill=default_skill,
            difficulty="MEDIUM",
            created_by=request.user
        )

        return Response({
            "message": "Question added to homework successfully",
            "question_id": question.id,
            "assignment_id": homework_level.id
        }, status=status.HTTP_201_CREATED)

    except Level.DoesNotExist:
        return Response({"error": "Assignment not found or unauthorized"}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_student_classroom_homeworks(request, classroom_id):
    if request.user.role != 'STUDENT':
        return Response({"error": "Only students can view homeworks"}, status=status.HTTP_403_FORBIDDEN)

    try:
        classroom = Classroom.objects.get(id=classroom_id, students=request.user)
        homeworks = Level.objects.filter(classroom=classroom, is_homework=True)

        data = [
            {
                "homework_id": hw.id,
                "level_number": hw.level_number,
                "teacher_name": hw.teacher.username if hw.teacher else "Teacher",
                "total_questions": hw.question_set.count()
            }
            for hw in homeworks
        ]

        return Response(data, status=status.HTTP_200_OK)

    except Classroom.DoesNotExist:
        return Response({"error": "You are not enrolled in this classroom"}, status=status.HTTP_404_NOT_FOUND)