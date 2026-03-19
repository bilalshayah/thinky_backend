from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from .serializers import GameSessionSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework.response import Response
from django.db import transaction
from questions.serializers import QuestionGameSerializer
from .models import GameSession
from levels.models import Level, UserLevel
from questions.models import Question
from questions.serializers import QuestionSerializer
from answers.models import AnswerAttempt
from points.models import Points


class SessionListCreateView(ListCreateAPIView):
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer




class SessionDetailView(RetrieveUpdateDestroyAPIView):
    queryset = GameSession.objects.all()
    serializer_class = GameSessionSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    level_id = request.data.get("level_id")
    try:
        level = Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        return Response({"error": "level dose not exist!"}, status=404)

  
    session = GameSession.objects.create(
        user=request.user,
        levelid=level,
        phase="analysis",
        energy=0,
        score=0,
        is_active=True
    )

    return Response({
        "session_id": session.id,
        "phase": session.phase,
        "energy": session.energy,
        "message": "ready for the game?",
        "intro_message":level.intro_message
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mission_questions(request, session_id):
    try:
        session = GameSession.objects.get(id=session_id, user=request.user, is_active=True)
    except GameSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

  
    answered_ids = AnswerAttempt.objects.filter(session=session).values_list('question_id', flat=True)
    
    # اختيار الأسئلة بناءً على المرحلة (مستقبلاً هنا يتدخل الـ AI)
    # حالياً نستبعد الأسئلة القديمة تماماً
    questions = Question.objects.filter(level=session.levelid).exclude(id__in=answered_ids).order_by('?')[:2]
    
    # استخدام السيريالايزر الآمن (بدون correct_answer)
    serializer = QuestionGameSerializer(questions, many=True)
    return Response({
        "current_phase": session.phase,
        "questions": serializer.data
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    session_id = request.data.get("session_id")
    question_id = request.data.get("question_id")
    selected_answer = request.data.get("selected_answer")
    wants_hint = request.data.get("wants_hint", False)
    time_taken=request.data.get("time_taken")

    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
        question = Question.objects.get(id=question_id)
    except:
        return Response({"error": "Data not found"}, status=404)

    # --- الحل: منع تكرار الإجابة على نفس السؤال ---
    if AnswerAttempt.objects.filter(session=session, question=question).exists():
        return Response({"error": "You have already answered this question!"}, status=400)

    is_correct = (selected_answer.strip().upper() == question.correct_answer.strip().upper())

    with transaction.atomic():
        # منطق الطاقة والنقاط (نفسه سابقاً)
        session.energy += 2 if is_correct else 1
        
        points_earned = 0
        if is_correct:
            # التحقق من أن الطفل لم يربح نقاط هذا السؤال "أبداً" في أي جلسة سابقة
            already_earned = Points.objects.filter(user=request.user, question=question).exists()
            if not already_earned:
                points_earned = question.points
                request.user.total_points += points_earned
                Points.objects.create(user=request.user, amount=points_earned, type='earn', question=question)
            
            session.score += 1

        AnswerAttempt.objects.create(
            user=request.user, session=session, question=question,
            selected_answer=selected_answer, is_correct=is_correct,
            hints_used=wants_hint, time_taken=time_taken
        )
        session.save()
        request.user.save()

    # حساب النسبة المئوية المباشرة (Live Score %)
    total_answered = AnswerAttempt.objects.filter(session=session).count()
    current_percentage = (session.score / total_answered) * 100 if total_answered > 0 else 0

    return Response({
        "is_correct": is_correct,
        "live_score": f"{int(current_percentage)}%",
        "energy": session.energy,
        "explanation": question.explanation if not is_correct else "Correct!",
        "character": "hakeem" if (not is_correct and question.is_hakeem) else "none"
    })
# ---------------------------------
# 4. تحديث المرحلة (المهمة التالية)
# ---------------------------------
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_stage(request):
    session_id = request.data.get("session_id")
    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except GameSession.DoesNotExist:
        return Response({"error": "session not found!"}, status=404)
    
    # 1. التحقق من شرط الطاقة للعبور للمراحل التالية (باستثناء مرحلة الاختبار)
    if session.energy < 1 and session.phase != "testing":
        return Response({
            "status": "low_energy",
            "message": "طاقتك لا تكفي للمهمة القادمة! حل مزيد من الأسئلة لجمع الطاقة."
        }, status=400)

    # 2. منطق إنهاء المستوى (مرحلة الاختبار النهائية)
    if session.phase == "testing":
        # حساب إجمالي الأسئلة التي حاول الطفل حلها في هذه الجلسة
        total_attempts = AnswerAttempt.objects.filter(session=session).count()
        
        # تحويل السكور من "عدد" إلى "نسبة مئوية"
        # المعادلة: (عدد الإجابات الصحيحة / إجمالي المحاولات) * 100
        if total_attempts > 0:
            final_percentage = (session.score / total_attempts) * 100
        else:
            final_percentage = 0

        # تحديث السكور في قاعدة البيانات ليصبح النسبة المئوية
        session.score = int(final_percentage)
        
        # المقارنة بين النسبة التي حققها والنسبة المطلوبة للنجاح
        passed = session.score >= session.levelid.required_score
        
        if passed:
            # 1. تحديث المستوى الحالي كمكتمل
            user_lvl, _ = UserLevel.objects.get_or_create(user=request.user, level=session.levelid)
            user_lvl.is_completed = True
            user_lvl.save()
            
            # 2. فتح المستوى التالي (بشكل صريح)
            next_lvl = Level.objects.filter(level_number=session.levelid.level_number + 1).first()
            if next_lvl:
                # نستخدم update_or_create أو نعدل يدوياً لنضمن التغيير
                user_lvl_next, created = UserLevel.objects.get_or_create(
                    user=request.user, 
                    level=next_lvl
                )
                user_lvl_next.is_unlocked = True # نضمن أنها أصبحت True هنا
                user_lvl_next.save()

        # إغلاق الجلسة وحفظ النتائج النهائية
        session.is_active = False
        session.save()
        
        return Response({
            "status": "level_finished", 
            "passed": passed, 
            "final_score": f"{session.score}%", # إرجاع النسبة المئوية واضحة للـ Flutter
            "required_score": f"{session.levelid.required_score}%"
        })

    # 3. الانتقال للمرحلة التالية (Analysis -> Training -> Testing)
    if session.phase == "analysis":
        session.phase = "training"
    elif session.phase == "training":
        session.phase = "testing"
    
    session.save()
    return Response({
        "status": "phase_updated", 
        "new_phase": session.phase,
        "current_energy": session.energy
    })