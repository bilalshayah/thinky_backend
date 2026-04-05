from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
import requests
import json

from .models import GameSession
from .serializers import GameSessionSerializer
from levels.models import Level, UserLevel
from questions.models import Question
from questions.serializers import QuestionGameSerializer
from answers.models import AnswerAttempt
from points.models import Points
from ai_engine.step2 import extract_behavior_features
from ai_engine.classifier import AIDecisionEngine

# --- Serializers ---
class StartSessionInputSerializer(serializers.Serializer):
    level_id = serializers.IntegerField()

class ANSWERSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    session_id = serializers.IntegerField()
    selected_answer = serializers.CharField()
    wants_hint = serializers.BooleanField(default=False)
    time_taken = serializers.FloatField()

class FINISHSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()

# --- Serializer لطلب التلميح ---
class HINTInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(help_text="ID الخاص بالسؤال الذي تريد تلميحاً له")

# --- Views ---

@extend_schema(request=StartSessionInputSerializer, responses={201: GameSessionSerializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_session(request):
    level_id = request.data.get("level_id")
    try:
        level = Level.objects.get(id=level_id)
    except Level.DoesNotExist:
        return Response({"error": "level does not exist!"}, status=404)

    session = GameSession.objects.create(
        user=request.user, levelid=level, phase="analysis", is_active=True
    )
    return Response({
        "session_id": session.id,
        "phase": session.phase,
        "intro_message": level.intro_message
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mission_questions(request, session_id):
    try:
        session = GameSession.objects.get(id=session_id, user=request.user, is_active=True)
    except GameSession.DoesNotExist:
        return Response({"error": "Session not found"}, status=404)

    ai_feedback_data = {}
    weak_skill = "General"
    current_difficulty = session.next_difficulty 

    past_attempts = AnswerAttempt.objects.filter(session=session).order_by('-id')[:5]
    
    if past_attempts.exists() and session.phase != "testing":
        attempts_list = [{
            'is_correct': a.is_correct,
            'time_taken': a.time_taken,
            'hints': 1 if a.hints_used else 0,
            'allowed_time': 30,
            'skill': a.question.skill.name if a.question.skill else "General"
        } for a in past_attempts]

        features, weak_skill = extract_behavior_features(attempts_list)
        engine = AIDecisionEngine()
        decision = engine.get_decision(features, weak_skill, request.user)

        session.next_difficulty = decision.get("next_difficulty", "MEDIUM")
        session.save()

        # طلب الرد من الذكاء الاصطناعي
        final_msg = "أنت بطل! استمر 👏"
        try:
            api_key = "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" 
            url = "https://openrouter.ai/api/v1/chat/completions"
            data = {
                "model": "openrouter/auto", 
                "messages": [{"role": "user", "content": decision.get("gemini_prompt")}]
            }
            response = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=data, timeout=10)
            res_json = response.json()
            final_msg = res_json['choices'][0]['message']['content'].strip()
        except:
            final_msg = "واصل التقدم يا ذكي!"

        ai_feedback_data = {
            "message": final_msg,
            "student_type": decision.get("group"),
            "weak_skill": weak_skill,
            "character": decision.get("character_type") # هذا سيخبر فلاتر من يظهر (Villain vs Hakeem)
        }

    # جلب الأسئلة
    answered_ids = AnswerAttempt.objects.filter(session=session).values_list('question_id', flat=True)
    base_qs = Question.objects.filter(level=session.levelid).exclude(id__in=answered_ids)

    if session.phase == "training":
        final_list = list(base_qs.filter(skill__name__iexact=weak_skill, difficulty=current_difficulty)[:3])
        needed = 5 - len(final_list)
        final_list += list(base_qs.exclude(id__in=[q.id for q in final_list])[:needed])
    else:
        final_list = base_qs.order_by('?')[:5]
    
    return Response({
        "current_phase": session.phase,
        "questions": QuestionGameSerializer(final_list, many=True).data,
        "ai_feedback": ai_feedback_data
    })


# --- دالة طلب التلميح (التي سقطت سهواً) ---

@extend_schema(
    request=HINTInputSerializer,
    responses={200: serializers.Serializer} # استجابة نجاح
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_hint(request):
    question_id = request.data.get("question_id")
    HINT_COST = 10  # تكلفة التلميح

    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return Response({"error": "Question not found"}, status=404)

    # 1. التحقق من النقاط
    if request.user.total_points < HINT_COST:
        return Response({
            "status": "insufficient_points",
            "message": "عذراً! لا تملك نقاطاً كافية لرؤية التلميح. حاول الحل بنفسك لتكسب المزيد!",
            "current_points": request.user.total_points
        }, status=402)

    # 2. خصم النقاط وتفعيل ظهور الحكيم في قاعدة البيانات
    with transaction.atomic():
        request.user.total_points -= HINT_COST
        request.user.save()
        
        # تفعيل ظهور الحكيم لهذا السؤال تحديداً
        question.is_hakeem = True 
        question.save()
        
        # تسجيل العملية في جدول النقاط
        Points.objects.create(
            user=request.user, 
            amount=HINT_COST, 
            type='spend', 
            question=question
        )

    return Response({
        "status": "success",
        "hint_text": question.hint,
        "remaining_points": request.user.total_points,
        "is_hakeem": question.is_hakeem
    })



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    data = request.data
    try:
        session = GameSession.objects.get(id=data.get("session_id"), user=request.user)
        question = Question.objects.get(id=data.get("question_id"))
    except:
        return Response({"error": "Data not found"}, status=404)

    if AnswerAttempt.objects.filter(session=session, question=question).exists():
        return Response({"error": "Already answered!"}, status=400)

    is_correct = (data.get("selected_answer").strip().upper() == question.correct_answer.strip().upper())

    with transaction.atomic():
        session.energy += 2 if is_correct else 1
        if is_correct:
            if not Points.objects.filter(user=request.user, question=question).exists():
                request.user.total_points += question.points
                Points.objects.create(user=request.user, amount=question.points, type='earn', question=question)
            session.score += 1
        
        AnswerAttempt.objects.create(
            user=request.user, session=session, question=question,
            selected_answer=data.get("selected_answer"), is_correct=is_correct,
            hints_used=data.get("wants_hint", False), time_taken=data.get("time_taken")
        )
        session.save()
        request.user.save()

    total_answered = AnswerAttempt.objects.filter(session=session).count()
    return Response({
        "is_correct": is_correct,
        "live_score": f"{int((session.score/total_answered)*100)}%" if total_answered > 0 else "0%",
        "explanation": question.explanation if not is_correct else "رائع!",
        "character": "hakeem" if (not is_correct and question.is_hakeem) else "none"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_stage(request):
    session_id = request.data.get("session_id")
    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except:
        return Response({"error": "Not found"}, status=404)
    
    if session.phase == "testing":
        total = AnswerAttempt.objects.filter(session=session).count()
        session.score = int((session.score / total) * 100) if total > 0 else 0
        passed = session.score >= session.levelid.required_score
        
        if passed:
            ul, _ = UserLevel.objects.get_or_create(user=request.user, level=session.levelid)
            ul.is_completed = True
            ul.save()
            next_l = Level.objects.filter(level_number=session.levelid.level_number + 1).first()
            if next_l:
                unl, _ = UserLevel.objects.get_or_create(user=request.user, level=next_l)
                unl.is_unlocked = True
                unl.save()

        session.is_active = False
        session.save()
        return Response({"status": "finished", "passed": passed, "final_score": f"{session.score}%"})

    session.phase = "training" if session.phase == "analysis" else "testing"
    session.save()
    return Response({"status": "updated", "new_phase": session.phase})