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

from django.db.models import Avg, Count
from answers.models import AnswerAttempt  # 🌟 تأكدي من استيراد الموديل



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

from ai_engine.classifier import AIDecisionEngine

# 🌟 قاموس النصائح الاحتياطية المخصصة لأولياء الأمور
PARENT_FALLBACK_ADVICE = {
    "MASTER": "طفلك متفوق وسريع الفهم! شجعه على حل المسائل المتقدمة وتحدي نفسه دون خوف من الخطأ.",
    "RECKLESS": "طفلك يتسرع أحياناً في اختيار الإجابة. ننصح بتدريبه على التأنّي وقراءة السؤال كاملاً قبل الحل.",
    "HESITANT": "طفلك يتردد أثناء الحل ويحتاج إلى دعم معنوي. شجعه وامتدح محاولاته لتعزيز ثقته بنفسه.",
    "STRUGGLING": "طفلك يواجه بعض الصعوبة في هذه المهارة. ننصح بمراجعة المفاهيم الأساسية معه ببطء ومساعدته بخطوات مبسطة.",
    "GAMER": "طفلك يحب التجربة والاستكشاف! وجه شغفه نحو التفكير المنطقي قبل اختيار الإجابة."
}

def generate_gemini_advice(student_name, group_name):
    # 1. إذا لم يكن للطفل نمط محدد بعد
    if not group_name or group_name == "N/A":
        return f"واصل تشجيع {student_name} ومتابعة أداءه في حل التمارين لتحديد نمطه السلوكي."

    # 2. محاولة جلب النصيحة ديناميكياً من Gemini
    try:
        prompt = (
            f"أنت خبير تربوي. اكتب نصيحة تربوية مبسطة ومباشرة في سطر واحد لولي أمر الطفل {student_name} "
            f"الذي ينتمي للنمط السلوكي '{group_name}' لتوضيح كيف يمكن لولي الأمر مساعدته وتطوير مستواه في المنزل."
        )
        engine = AIDecisionEngine()
        response_text = engine.get_ai_response(prompt)
        
        if response_text and len(response_text.strip()) > 5:
            return response_text.strip()
    except Exception:
        pass

    # 3. 🌟 الـ Fallback المخصص لولي الأمر في حال عدم استجابة الـ AI
    return PARENT_FALLBACK_ADVICE.get(
        group_name, 
        f"استمر في تشجيع {student_name} ومتابعة تقدمه المستمر وتوفير البيئة المناسبة له."
    )
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


class UserStreakResponseSerializer(serializers.Serializer):
    streak_count = serializers.IntegerField(help_text="عدد أيام الـ Streak الحالية للمستخدم")

@extend_schema(
    responses={200: UserStreakResponseSerializer},
    description="جلب عدد أيام الـ Streak الخاصة بالطفل/المستخدم بشكل منفصل"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_streak(request):
    user = request.user
    today = date.today()

    # التحقق مما إذا كان المستخدم قد انقطع عن اللعب لأكثر من يوم لتصفير الـ Streak
    if user.last_activity_date:
        days_passed = (today - user.last_activity_date).days
        if days_passed > 1:
            user.streak_count = 0
            user.save(update_fields=['streak_count'])

    return Response({
        "streak_count": user.streak_count,
    }, status=status.HTTP_200_OK)

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
        
        # 🌟 تصفية الجلسات المخصصة لهذه الشعبة بالتحديد عن طريق levelid__classroom
        all_sessions = GameSession.objects.filter(
            user_id__in=student_ids, 
            is_active=False,
            levelid__classroom=classroom  # 🌟 التعديل الجوهري: ربط المستوى بالشعبة الحالية فقط
        ).select_related('user', 'levelid').order_by('user_id', 'levelid', '-id')
        
        level_reports = {}
        seen_students_per_level = set()

        for s in all_sessions:
            lv_num = s.levelid.level_number
            key = (lv_num, s.user_id)
            
            # أخذ أحدث نتيجة فقط للطالب في هذا المستوى الخاص بهذه الشعبة
            if key in seen_students_per_level:
                continue
            seen_students_per_level.add(key)

            if lv_num not in level_reports:
                level_reports[lv_num] = []
            
            level_reports[lv_num].append({
                "student_name": s.user.username,
                "score": s.score,
                "ai_group": s.current_group if s.current_group else "N/A"
            })
        class_ai_insight = generate_class_ai_summary(classroom.name, level_reports)

        results.append({
            "class_name": classroom.name,
            "class_code": classroom.class_code,
            "class_ai_insight": class_ai_insight,  # 🌟 التقرير الذكي للشعبة
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
        # 1. جلب الجلسات المكتملة للطفل
        sessions = GameSession.objects.filter(user=child, is_active=False).select_related('levelid').order_by('-id')
        
        latest_session = sessions.first()
        student_group = latest_session.current_group if (latest_session and latest_session.current_group) else "N/A"

        # 2. 🌟 حساب إجمالي الأسئلة ومتوسط وقت الإجابة للطفل عبر جميع جلساته
        child_attempts = AnswerAttempt.objects.filter(user=child)
        
        total_questions_answered = child_attempts.count()
        
        # حساب متوسط الوقت بالثواني وتقريبه لمنزلتين عشريتين
        avg_time_data = child_attempts.aggregate(Avg('time_taken'))['time_taken__avg']
        avg_time_seconds = round(avg_time_data, 2) if avg_time_data is not None else 0.0

        level_history = [
            {
                "level_number": s.levelid.level_number,
                "score": f"{s.score}%",
            }
            for s in sessions
        ]

        # 3. إرجاع البيانات المحدثة بالكامل
        children_stats.append({
            "name": child.username,
            "total_points": child.total_points,
            "streak": child.streak_count,
            "ai_group": student_group,
            "total_questions_answered": total_questions_answered,  # 🌟 إجمالي الأسئلة المجاوب عليها
            "average_time_per_question_seconds": avg_time_seconds,  # 🌟 متوسط الوقت المستغرق بالسؤال (بالثواني)
            "level_performance": level_history,
            "ai_advice": generate_gemini_advice(child.username, student_group),
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


def generate_class_ai_summary(class_name, level_reports):
    # إذا لم تكن هناك بيانات للطلاب بعد
    if not level_reports:
        return f"لا توجد نشاطات كافية حالياً لتوليد تقرير الذكاء الاصطناعي لشعبة {class_name}."

    # تجميع الأنماط السلوكية والدرجات المتاحة للشعبة
    groups_summary = []
    for lv, students in level_reports.items():
        for s in students:
            groups_summary.append(f"الطالب {s['student_name']}: النمط ({s['ai_group']}) - الدرجة ({s['score']}%)")

    students_data_str = ", ".join(groups_summary)

    try:
        prompt = (
            f"أنت مستشار تعليمي ذكي. قم بتحليل أداء الطلاب التالي في شعبة '{class_name}':\n"
            f"{students_data_str}\n"
            f"قدم للمعلم ملخصاً تحليلياً في سطرين يوضح: 1) النمط العام أو الملاحظة الأساسية على أداء الشعبة، 2) نصيحة تعليمية مخصصة للمعلم لتطوير مستواهم."
        )
        engine = AIDecisionEngine()
        response_text = engine.get_ai_response(prompt)
        
        if response_text and len(response_text.strip()) > 5:
            return response_text.strip()
    except Exception:
        pass

    # الـ Fallback الاحتياطي المعلم عند تعثر الـ AI
    return f"شعبة {class_name} تسير بشكل جيد. يُنصح بمتابعة الطلاب الذين ينتمون لنمطي HESITANT و STRUGGLING وتزويدهم بتمارين إضافية."