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
from levels.models import Level, UserLevel , PlanetCard ,UserUnlockedCard
from questions.models import Question
from questions.serializers import QuestionGameSerializer
from answers.models import AnswerAttempt
from points.models import Points
from ai_engine.step2 import extract_behavior_features
from ai_engine.classifier import AIDecisionEngine
from datetime import date, timedelta
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
    common_mistake = "None"
    allowed_difficulties = ["EASY", "MEDIUM"] 

    # جلب جميع المحاولات السابقة لهذه الجلسة لتجنب خطأ الـ Slice
    all_session_attempts = AnswerAttempt.objects.filter(session=session).order_by('-id')
    
    if all_session_attempts.exists() and session.phase != "testing":
        # 1. جمع تفاصيل كل الإجابات الخاطئة في الجلسة لتحليلها رقمياً
        wrong_attempts = all_session_attempts.filter(is_correct=False)
        wrong_details = []
        for wa in wrong_attempts:
            wrong_details.append({
                "question": wa.question.question_text,
                "correct_answer": wa.question.correct_answer,
                "student_answer": getattr(wa, 'student_answer', 'Unknown') # تأكدي من وجود هذا الحقل في Model[cite: 1]
            })

        # 2. تحديد آخر 5 محاولات لتحليل السلوك العام (Profiling)
        past_attempts = all_session_attempts[:5]
        attempts_list = []
        for a in past_attempts:
            q_time = getattr(a.question, 'allowed_time', 60) 
            attempts_list.append({
                'is_correct': a.is_correct,
                'time_taken': a.time_taken,
                'hints': 1 if a.hints_used else 0, 
                'allowed_time': q_time, 
                'skill': a.question.skill.name if a.question.skill else "General",
                'mistake_type': getattr(a, 'mistake_type', 'None')
            })

        # استخراج الميزات السلوكية
        features, weak_skill, common_mistake = extract_behavior_features(attempts_list)
        
        engine = AIDecisionEngine()
        # تمرير قائمة الأخطاء الكاملة للمحرك ليقوم بالتحليل الرياضي[cite: 1]
        decision = engine.get_decision(features, weak_skill, common_mistake, request.user, wrong_details)
        
        allowed_difficulties = decision.get("suggested_difficulties", ["EASY", "MEDIUM"])
        
        final_msg = "واصل التقدم يا بطل!"
        try:
            api_key = "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" 
            url = "https://openrouter.ai/api/v1/chat/completions"
            data = {
                "model": "google/gemini-2.0-flash-lite-001", 
                "messages": [{"role": "user", "content": decision.get("gemini_prompt")}]
            }
            response = requests.post(url, headers={"Authorization": f"Bearer {api_key}"}, json=data, timeout=10)
            res_json = response.json()
            if 'choices' in res_json:
                final_msg = res_json['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"AI Connection Error: {e}")

        ai_feedback_data = {
            "message": final_msg,
            "student_type": decision.get("group"),
            "weak_skill": weak_skill,
            "common_mistake": common_mistake
        }

    # --- منطق جلب الأسئلة الجديدة ---
    answered_ids = AnswerAttempt.objects.filter(session=session).values_list('question_id', flat=True)
    level = session.levelid
    is_homework = getattr(level, 'is_homework', False)
    teacher = getattr(level, 'teacher', None)

    if is_homework and teacher:
        initial_qs = Question.objects.filter(level=level, created_by=teacher).exclude(id__in=answered_ids)
    else:
        initial_qs = Question.objects.filter(level=level, created_by__isnull=True).exclude(id__in=answered_ids)

    base_qs = initial_qs.filter(difficulty__in=allowed_difficulties)
    if not base_qs.exists():
        base_qs = initial_qs

    if session.phase == "training":
        final_list = list(base_qs.filter(skill__name__iexact=weak_skill)[:3])
        needed = 5 - len(final_list)
        final_list += list(base_qs.exclude(id__in=[q.id for q in final_list])[:needed])
    else:
        final_list = list(base_qs.order_by('?')[:5])
    
    if not final_list:
        final_list = list(Question.objects.filter(level=level)[:5])
    
    return Response({
        "current_phase": session.phase,
        "is_homework": is_homework,
        "allowed_difficulties": allowed_difficulties,
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

        # تفعيل ظهور الحكيم لهذا السؤال تحديداً
    question.is_hakeem = True 
    question.save()
        
    return Response({
        "status": "success",
        "hint_text": question.hint,
        "remaining_points": request.user.total_points,
        "is_hakeem": question.is_hakeem
    })


@extend_schema(
    request=ANSWERSerializer,
    responses={200: serializers.Serializer} # استجابة نجاح
)
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

@extend_schema(
    request=FINISHSerializer,
    responses={200: serializers.Serializer} # استجابة نجاح
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_stage(request):
    session_id = request.data.get("session_id")
    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except:
        return Response({"error": "Not found"}, status=404)
    
    if session.phase == "testing":
        card_to_unlock = None
        new_card_unlocked = False
        
        # --- [تعديل ريري: منطق جرد النقاط النهائي] ---
        attempts = AnswerAttempt.objects.filter(session=session)
        total = attempts.count()
        
        level_points_balance = 0
        HINT_COST = 10

        with transaction.atomic():
            for a in attempts:
                # 1. إضافة نقاط السؤال إذا كانت الإجابة صحيحة
                if a.is_correct:
                    level_points_balance += a.question.points
                    Points.objects.create(
                        user=request.user, 
                        amount=a.question.points, 
                        type='earn', 
                        question=a.question
                    )
                
                # 2. خصم نقاط التلميح إذا استُخدم
                if a.hints_used:
                    level_points_balance -= HINT_COST
                    Points.objects.create(
                        user=request.user, 
                        amount=HINT_COST, 
                        type='spend', 
                        question=a.question
                    )

            # 3. تحديث الرصيد الكلي للمستخدم بـ "صافي" نقاط المرحلة
            request.user.total_points += level_points_balance
            request.user.save()
        # --- [نهاية تعديل النقاط] ---

        # حساب الـ Score كنسبة مئوية (لأغراض النجاح فقط)
        session.score = int((session.score / total) * 100) if total > 0 else 0
        passed = session.score >= session.levelid.required_score
        
        if passed:
            # --- منطق الستريك ---
            user = request.user
            today = date.today()
            yesterday = today - timedelta(days=1)

            if user.last_activity_date == yesterday:
                user.streak_count += 1
            elif user.last_activity_date != today:
                user.streak_count = 1
            
            user.last_activity_date = today
            user.total_points += 50  # مكافأة الستريك
            user.save()

            ul, _ = UserLevel.objects.get_or_create(user=request.user, level=session.levelid)
            ul.is_completed = True
            ul.save()
            
            card_to_unlock = PlanetCard.objects.filter(unlock_at_level_number=session.levelid.level_number).first()
            if card_to_unlock:
                obj, created = UserUnlockedCard.objects.get_or_create(user=request.user, card=card_to_unlock)
                new_card_unlocked = created

            next_l = Level.objects.filter(level_number=session.levelid.level_number + 1).first()
            if next_l:
                unl, _ = UserLevel.objects.get_or_create(user=request.user, level=next_l)
                unl.is_unlocked = True
                unl.save()

        session.is_active = False
        session.save()
        
        return Response({
            "status": "finished", 
            "passed": passed, 
            "final_score": f"{session.score}%",
            "points_earned_this_level": level_points_balance, # النقاط الصافية للمرحلة
            "streak_count": request.user.streak_count,
            "new_card_unlocked": new_card_unlocked,
            "card_details": {
                "planet_name": card_to_unlock.planet_name,
            } if card_to_unlock else None,
        })

    # التحويل بين المراحل (Analysis -> Training -> Testing)
    session.phase = "training" if session.phase == "analysis" else "testing"
    session.save()
    return Response({"status": "updated", "new_phase": session.phase})