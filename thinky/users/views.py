import random
import string
from datetime import date, timedelta

from drf_spectacular.utils import OpenApiTypes, extend_schema
from game_sessions.models import GameSession
from levels.models import UserUnlockedCard
from questions.models import Question
from questions.serializers import QuestionBankSerializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Classroom, User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


# --- Serializers ---
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


class CustomTeacherQuestionSerializer(serializers.Serializer):
    question_text = serializers.CharField(required=True)
    option_a = serializers.CharField(required=True)
    option_b = serializers.CharField(required=True)
    option_c = serializers.CharField(required=True)
    option_d = serializers.CharField(required=True)
    correct_answer = serializers.CharField(max_length=1)
    hint = serializers.CharField(required=False, allow_blank=True, default="")


class CompleteHomeworkSerializer(serializers.Serializer):
    level_id = serializers.IntegerField(required=True)
    question_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list,
        help_text="قائمة بـ IDs الأسئلة المختارة"
    )
    custom_questions = CustomTeacherQuestionSerializer(many=True, required=False, default=list)


class AddChildInputSerializer(serializers.Serializer):
    child_username = serializers.CharField(help_text="اسم المستخدم الخاص بالطفل")
    child_password = serializers.CharField(write_only=True, help_text="كلمة مرور حساب الطفل للتأكيد")


# --- Views ---

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
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    responses={200: UserProfileResponseSerializer},
    description="جلب بيانات الملف الشخصي للمستخدم وحساب عمره وجنسه وإعادة ضبط الستريك إذا انقطع"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    user = request.user
    today = date.today()
    age = None

    # 🌟 Duolingo Streak Reset: Reset to 0 if user missed more than 1 day
    if user.last_activity_date:
        days_passed = (today - user.last_activity_date).days
        if days_passed > 1:
            user.streak_count = 0
            user.save(update_fields=['streak_count'])

    if user.birthday:
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
        "streak_count": user.streak_count
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_library(request):
    unlocked_entries = UserUnlockedCard.objects.filter(user=request.user).select_related('card')
    
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
        student_ids = classroom.students.values_list('id', flat=True)
        all_sessions = GameSession.objects.filter(user_id__in=student_ids, is_active=False).select_related('user', 'levelid')
        
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
            "performance_by_level": level_reports
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
        sessions = GameSession.objects.filter(user=child, is_active=False).select_related('levelid').order_by('-id')
        
        level_history = []
        for s in sessions:
            level_history.append({
                "level_number": s.levelid.level_number,
                "score": f"{s.score}%",
            })

        children_stats.append({
            "name": child.username,
            "total_points": child.total_points,
            "streak": child.streak_count,
            "level_performance": level_history,
            #"date": s.created_at.strftime("%Y-%m-%d")
        })

    return Response(children_stats)


@extend_schema(
    request=ClassSerializer,
    responses={200: OpenApiTypes.OBJECT},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_classroom(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Only teachers can create classes"}, status=403)
    
    name = request.data.get("name")
    if not name:
        return Response({"error": "Class name is required"}, status=400)

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
    if request.user.role != 'STUDENT':
        return Response({"error": "Only students can join classes"}, status=403)
    
    code = request.data.get("code")
    try:
        classroom = Classroom.objects.get(class_code=code)
        classroom.students.add(request.user)
        return Response({"message": f"Successfully joined {classroom.name}"})
    except Classroom.DoesNotExist:
        return Response({"error": "Invalid class code"}, status=404)


@extend_schema(
    request=AddChildInputSerializer,
    responses={200: OpenApiTypes.OBJECT},
    description="ربط الوالد بطفله بأمان عبر اسم المستخدم وكلمة المرور الخاصة بالطفل"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_child(request):
    if request.user.role != 'PARENT':
        return Response({"error": "Only parents can add children"}, status=403)
    
    serializer = AddChildInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
        
    child_username = serializer.validated_data.get("child_username")
    child_password = serializer.validated_data.get("child_password")
    
    try:
        child = User.objects.get(username=child_username, role='STUDENT')
        
        if not child.check_password(child_password):
            return Response({"error": "كلمة المرور الخاصة بالطفل غير صحيحة!"}, status=401)
            
        request.user.parent_of.add(child) 
        
        return Response({"message": f"Successfully linked with child {child_username}"})
    except User.DoesNotExist:
        return Response({"error": "Child not found"}, status=404)


@extend_schema(
    responses={200: QuestionBankSerializer(many=True)},
    description="عرض قائمة الأسئلة المتاحة في المستوى ليختار منها المعلم"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_level_question_bank(request, level_id):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=403)
    
    questions = Question.objects.filter(level_id=level_id, created_by__isnull=True)
    serializer = QuestionBankSerializer(questions, many=True)
    return Response(serializer.data)


@extend_schema(
    request=CompleteHomeworkSerializer,
    responses={200: OpenApiTypes.OBJECT},
    description="إنشاء واجب مخصص: يجمع بين الأسئلة المختارة والمكتوبة يدوياً، مع إكمال النقص تلقائياً بالـ AI إلى 5 أسئلة"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def teacher_create_homework(request):
    if request.user.role != 'TEACHER':
        return Response({"error": "Unauthorized"}, status=403)

    serializer = CompleteHomeworkSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    validated_data = serializer.validated_data
    level_id = validated_data["level_id"]
    selected_ids = validated_data["question_ids"]
    custom_questions_data = validated_data["custom_questions"]

    try:
        from levels.models import Level
        original_level = Level.objects.get(id=level_id)
        
        homework_level = Level.objects.create(
            level_number=original_level.level_number,
            is_homework=True,
            teacher=request.user,
            required_score=original_level.required_score
        )

        final_questions_to_add = []

        if selected_ids:
            ready_questions = Question.objects.filter(id__in=selected_ids)
            for q in ready_questions:
                q.level = homework_level
                q.save()
                final_questions_to_add.append(q)

        from questions.models import Skill
        default_skill, _ = Skill.objects.get_or_create(name="Teacher Custom")

        for q_data in custom_questions_data:
            new_custom_q = Question.objects.create(
                level=homework_level,
                question_text=q_data['question_text'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct_answer'].upper(),
                hint=q_data.get('hint', ''),
                skill=default_skill,
                difficulty="MEDIUM",
                created_by=request.user
            )
            final_questions_to_add.append(new_custom_q)

        REQUIRED_COUNT = 5
        current_count = len(final_questions_to_add)
        ai_filled_triggered = False

        if current_count < REQUIRED_COUNT:
            needed_count = REQUIRED_COUNT - current_count
            
            used_texts = [q.question_text for q in final_questions_to_add]
            backup_pool = Question.objects.filter(level_id=level_id, created_by__isnull=True).exclude(question_text__in=used_texts)
            
            backup_list = list(backup_pool)
            if len(backup_list) >= needed_count:
                ai_filled_questions = random.sample(backup_list, needed_count)
            else:
                ai_filled_questions = backup_list
            
            for bg_q in ai_filled_questions:
                Question.objects.create(
                    level=homework_level,
                    question_text=bg_q.question_text,
                    option_a=bg_q.option_a,
                    option_b=bg_q.option_b,
                    option_c=bg_q.option_c,
                    option_d=bg_q.option_d,
                    correct_answer=bg_q.correct_answer,
                    hint=bg_q.hint,
                    skill=bg_q.skill,
                    difficulty=bg_q.difficulty
                )
            ai_filled_triggered = True

        return Response({
            "message": "Homework created successfully with all combined rules!",
            "homework_level_id": homework_level.id,
            "ai_auto_fill_triggered": ai_filled_triggered,
            "total_questions_secured": Question.objects.filter(level=homework_level).count()
        }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=400)