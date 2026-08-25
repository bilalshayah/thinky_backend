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
from django.conf import settings

# --- Serializers ---
# --- Serializers المخصصة لتوثيق مخرجات الـ AI والأسئلة في Swagger ---
class AIFeedbackResponseSerializer(serializers.Serializer):
    message = serializers.CharField(help_text="النص التعليمي أو النفسي المولد من جميناي")
    student_type = serializers.CharField(help_text="النمط السلوكي الحالي المكتشف للطفل")
    weak_skill = serializers.CharField(help_text="المهارة الرياضية الضعيفة التي تحتاج تقوية")
    common_mistake = serializers.CharField(help_text="نوع الخطأ الشائع المرصود")
    character_type = serializers.CharField(help_text="نوع الشخصية المتحدثة (hakeem أو villain)")

class GetMissionQuestionsResponseSerializer(serializers.Serializer):
    current_phase = serializers.CharField(help_text="المرحلة الحالية للعبة (analysis, training)")
    is_homework = serializers.BooleanField(help_text="هل المرحلة واجب بيئي أم لعب حر")
    allowed_difficulties = serializers.ListField(child=serializers.CharField(), help_text="الصعوبات المسموح بها حالياً")
    questions = QuestionGameSerializer(many=True, help_text="قائمة الأسئلة الخمسة المخصصة المرجوعة للطفل")
    ai_feedback = AIFeedbackResponseSerializer(help_text="بيانات رد الذكاء الاصطناعي والدعم النفسي")


class StartSessionInputSerializer(serializers.Serializer):
    level_id = serializers.IntegerField()

class ANSWERSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    session_id = serializers.IntegerField()
    selected_answer = serializers.CharField()
    time_taken = serializers.FloatField()

class FINISHSerializer(serializers.Serializer):
    session_id = serializers.IntegerField()

class HINTInputSerializer(serializers.Serializer):
    question_id = serializers.IntegerField(help_text="ID الخاص بالسؤال الذي تريد تلميحاً له")
    session_id = serializers.IntegerField(help_text="ID الخاص بجلسة اللعبة الحالية")

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


@extend_schema(
    summary="جلب أسئلة المرحلة الحالية ومعالجة رد الذكاء الاصطناعي",
    description="تقوم الدالة بتحليل أول 5 محاولات للطفل برمجياً وسلوكياً عند انتقاله لطور التدريب، وتحديد نمطه السلوكي، ثم استدعاء جميناي لبناء النص التربوي المبسط وإرجاع قائمة الأسئلة المخصصة لعلاج المهارة الضعيفة.",
    responses={200: GetMissionQuestionsResponseSerializer}
)
@extend_schema(
    summary="جلب أسئلة المرحلة الحالية ومعالجة رد الذكاء الاصطناعي",
    description="تقوم الدالة بتحليل أول 5 محاولات للطفل برمجياً وسلوكياً عند انتقاله لطور التدريب، وتحديد نمطه السلوكي، ثم استدعاء جميناي لبناء النص التربوي المبسط وإرجاع قائمة الأسئلة المخصصة لعلاج المهارة الضعيفة.",
    responses={200: GetMissionQuestionsResponseSerializer}
)
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

    all_session_attempts = AnswerAttempt.objects.filter(session=session).order_by('-id')
    
    # 🌟 الـ AI يتدخل ويعمل بالكامل فور الانتقال لطور الـ training لبناء خطة الدعم المخصصة
    if all_session_attempts.exists() and session.phase == "training":
        wrong_attempts = all_session_attempts.filter(is_correct=False)
        wrong_details = []
        for wa in wrong_attempts:
            wrong_details.append({
                "question": wa.question.question_text,
                "correct_answer": wa.question.correct_answer,
                "student_answer": getattr(wa, 'student_answer', 'Unknown')
            })

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

        # 1. استخراج الميزات الأساسية للمظهر السلوكي
        features, weak_skill, common_mistake = extract_behavior_features(attempts_list)
        
        # 2. استدعاء محرك الـ AI لاتخاذ القرار وتعيين مجموعة من المجموعات الـ 5
        engine = AIDecisionEngine()
        decision = engine.get_decision(features, weak_skill, common_mistake, request.user, wrong_details)
        session.current_group = decision.get("group", "N/A")
        session.save(update_fields=['current_group'])
        
        allowed_difficulties = decision.get("suggested_difficulties", ["EASY", "MEDIUM"])
        
        # 3. مهمة الباك إند الصافية: تمرير البرومبت الجاهز واستقبال النص النهائي من خادم الـ AI
        ready_prompt = decision.get("gemini_prompt", "شجع الطالب بأسلوب مبسط")
        final_msg = engine.get_ai_response(ready_prompt)

        # 4. تحديد طبيعة حركة الشخصيات داخل طور التدريب بناءً على التصنيف المستلم
        character_type = "none"
        if session.phase == "training":
            if decision.get("group") == "MASTER":
                character_type = "villain"
            else:
                character_type = "hakeem"

        ai_feedback_data = {
            "message": final_msg,
            "student_type": decision.get("group"),
            "weak_skill": weak_skill,
            "common_mistake": common_mistake,
            "character_type": character_type  
        }

    # === الجزء المصلح لاختيار الأسئلة وتكملة الـ AI عند انتهاء أسئلة المعلم ===
    
    answered_ids = AnswerAttempt.objects.filter(session=session).values_list('question_id', flat=True)
    level = session.levelid
    is_homework = getattr(level, 'is_homework', False)
    teacher = getattr(level, 'teacher', None)

    # 1. أسئلة المعلم المتبقية في الواجب والتي لم يُجب عليها الطالب بعد
    teacher_qs = Question.objects.filter(level=level, created_by=teacher).exclude(id__in=answered_ids) if (is_homework and teacher) else Question.objects.none()
    
    # 2. بنك أسئلة النظام العام غير المجاب عليها (نتحقق من نفس المستوى أولاً، وإذا كان الواجب مخصصاً جلبنا أسئلة بنك النظام العامة)
    system_qs = Question.objects.filter(created_by__isnull=True).exclude(id__in=answered_ids)
    level_system_qs = system_qs.filter(level=level)
    if not level_system_qs.exists():
        level_system_qs = system_qs

    if session.phase == "analysis":
        # عرض أسئلة المعلم أولاً
        final_list = list(teacher_qs[:5])
        
        # إذا كانت أسئلة المعلم أقل من 5، يكمل النظام من أسئلة البنك العام
        if len(final_list) < 5:
            needed = 5 - len(final_list)
            used_ids = [q.id for q in final_list]
            additional_qs = list(level_system_qs.exclude(id__in=used_ids).order_by('?')[:needed])
            final_list.extend(additional_qs)

    else: # phase == "training"
        used_ids = list(answered_ids)

        # 🌟 تصفية أسئلة المعلم المتبقية حسب الصعوبات المسموح بها والمهارة الضعيفة
        focused_teacher_qs = list(
            teacher_qs.filter(
                skill__name__iexact=weak_skill,
                difficulty__in=allowed_difficulties
            )[:3]
        )
        used_ids.extend([q.id for q in focused_teacher_qs])

        needed_focused = 3 - len(focused_teacher_qs)
        
        # 🌟 تصفية أسئلة بنك النظام حسب الصعوبات المسموح بها والمهارة الضعيفة
        focused_system_qs = list(
            level_system_qs.filter(
                skill__name__iexact=weak_skill,
                difficulty__in=allowed_difficulties
            ).exclude(id__in=used_ids)[:needed_focused]
        )
        
        final_list = focused_teacher_qs + focused_system_qs
        used_ids.extend([q.id for q in focused_system_qs])

        # 🌟 تكملة المتبقي لـ 5 أسئلة مع الالتزام بالصعوبات المسموح بها أيضاً
        if len(final_list) < 5:
            needed = 5 - len(final_list)
            remaining_qs = list(
                level_system_qs.filter(
                    difficulty__in=allowed_difficulties
                ).exclude(id__in=used_ids).order_by('?')[:needed]
            )
            final_list.extend(remaining_qs)

        # 🌟 احتياطي: في حال عدم وجود أسئلة كافية تطابق الصعوبات، تجلب من بنك الأسئلة المتاح المفلتر بالصعوبة
        if len(final_list) < 5:
            needed = 5 - len(final_list)
            fallback_qs = list(
                Question.objects.filter(
                    difficulty__in=allowed_difficulties
                ).exclude(id__in=[q.id for q in final_list]).order_by('?')[:needed]
            )
            final_list.extend(fallback_qs)

    # احترازي أخير: في حال نفاد كافة الأسئلة غير المجاب عليها نهائياً
    if not final_list:
        final_list = list(Question.objects.exclude(id__in=answered_ids)[:5])
    
    return Response({
        "current_phase": session.phase,
        "is_homework": is_homework,
        "allowed_difficulties": allowed_difficulties,
        "questions": QuestionGameSerializer(final_list, many=True).data,
        "ai_feedback": ai_feedback_data
    })


@extend_schema(request=HINTInputSerializer, responses={200: serializers.Serializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_hint(request):
    question_id = request.data.get("question_id")
    session_id = request.data.get("session_id")
    HINT_COST = 10  

    try:
        question = Question.objects.get(id=question_id)
        session = GameSession.objects.get(id=session_id, user=request.user)
    except:
        return Response({"error": "Question or Session not found"}, status=404)

    if request.user.total_points < HINT_COST:
        return Response({
            "status": "insufficient_points",
            "message": "عذراً! لا تملك نقاطاً كافية لرؤية التلميح. حاول الحل بنفسك لتكسب المزيد!",
            "current_points": request.user.total_points
        }, status=402)

    with transaction.atomic():
        request.user.total_points -= HINT_COST
        request.user.save()
        
        Points.objects.create(
            user=request.user, 
            amount=HINT_COST, 
            type='spend', 
            question=question
        )

        attempt, created = AnswerAttempt.objects.get_or_create(
            user=request.user,
            session=session,
            question=question,
            defaults={'hints_used': True, 'is_correct': False, 'time_taken': 0}
        )
        if not created:
            attempt.hints_used = True
            attempt.save()
        
    return Response({
        "status": "success",
        "hint_text": question.hint,
        "remaining_points": request.user.total_points,
        "hints_used": True
    })

TOTAL_LEVEL_QUESTIONS = 10  # إجمالي أسئلة المستوى (5 تحليل + 5 تدريب)

@extend_schema(request=ANSWERSerializer, responses={200: serializers.Serializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_answer(request):
    data = request.data
    try:
        session = GameSession.objects.get(id=data.get("session_id"), user=request.user)
        question = Question.objects.get(id=data.get("question_id"))
    except:
        return Response({"error": "Data not found"}, status=404)

    is_correct = (data.get("selected_answer").strip().upper() == question.correct_answer.strip().upper())

    with transaction.atomic():
        session.energy += 1 if is_correct else 0
        
        if is_correct:
            if not Points.objects.filter(user=request.user, question=question, type='earn').exists():
                request.user.total_points += question.points
                Points.objects.create(user=request.user, amount=question.points, type='earn', question=question)
            session.score += 1
        
        existing_attempt = AnswerAttempt.objects.filter(session=session, question=question).first()
        
        if existing_attempt:
            existing_attempt.selected_answer = data.get("selected_answer")
            existing_attempt.is_correct = is_correct
            existing_attempt.time_taken = data.get("time_taken")
            existing_attempt.save()
        else:
            AnswerAttempt.objects.create(
                user=request.user, session=session, question=question,
                selected_answer=data.get("selected_answer"), is_correct=is_correct,
                hints_used=data.get("wants_hint", False), time_taken=data.get("time_taken")
            )
        
        total_answered_in_session = AnswerAttempt.objects.filter(session=session).count()
        
        phase_updated = False
        new_phase_name = session.phase
        
        # الانتقال المباشر لطور الـ training بعد حل أول 5 أسئلة
        if session.phase == "analysis" and total_answered_in_session >= 5:
            session.phase = "training"
            phase_updated = True
            new_phase_name = "training"
        elif session.phase == "training" and total_answered_in_session >= TOTAL_LEVEL_QUESTIONS:
            new_phase_name = "training"
            
        session.save()
        request.user.save()

    total_answered = AnswerAttempt.objects.filter(session=session).count()
    
    # 🌟 حساب الـ live_score بناءً على إجمالي الأسئلة الـ 10 للمستوى كاملاً
    live_score_percentage = int((session.score / TOTAL_LEVEL_QUESTIONS) * 100)

    return Response({
        "is_correct": is_correct,
        "live_score": f"{live_score_percentage}%",
        "correct_answers_count": session.score,
        "total_questions_in_level": TOTAL_LEVEL_QUESTIONS,
        "explanation": question.explanation if not is_correct else "رائع!",
        "character": "hakeem" if (not is_correct and existing_attempt and existing_attempt.hints_used) else "none",
        "phase_updated": phase_updated,
        "current_phase": new_phase_name,
        "total_answered_global": total_answered
    })


@extend_schema(request=FINISHSerializer, responses={200: serializers.Serializer})
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_stage(request):
    session_id = request.data.get("session_id")
    try:
        session = GameSession.objects.get(id=session_id, user=request.user)
    except:
        return Response({"error": "Not found"}, status=404)
    
    attempts = AnswerAttempt.objects.filter(session=session)
    total_answered = attempts.count()
    
    # 🌟 حماية أمنية: يمنع إنهاء المستوى أو النجاح فيه إذا لم يحل الطالب الـ 10 أسئلة كاملة
    if total_answered < TOTAL_LEVEL_QUESTIONS:
        return Response({
            "status": "incomplete",
            "message": f"لم تقم بإكمال جميع الأسئلة بعد! لقد أجبت على {total_answered} من أصل {TOTAL_LEVEL_QUESTIONS} أسئلة.",
            "total_answered": total_answered,
            "required_questions": TOTAL_LEVEL_QUESTIONS
        }, status=400)

    # 🌟 حساب النتيجة النهائية قسمةً على 10 (إجمالي أسئلة المستوى)
    card_to_unlock = None
    new_card_unlocked = False
    
    final_score_percentage = int((session.score / TOTAL_LEVEL_QUESTIONS) * 100)
    session.score = final_score_percentage
    passed = session.score >= session.levelid.required_score
    
    if passed:
        user = request.user
        today = date.today()
        yesterday = today - timedelta(days=1)

        if user.last_activity_date == yesterday:
            user.streak_count += 1
        elif user.last_activity_date != today:
            user.streak_count = 1
        
        user.last_activity_date = today
        user.total_points += 50  
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
        "points_earned_this_level": session.score, 
        "streak_count": request.user.streak_count,
        "new_card_unlocked": new_card_unlocked,
        "card_details": {
            "planet_name": card_to_unlock.planet_name,
        } if card_to_unlock else None,
    })