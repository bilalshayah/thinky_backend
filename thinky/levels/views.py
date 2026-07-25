from django.shortcuts import render
from .models import Level , UserLevel , GameWorld, PlanetCard
from .serializers import LevelSerializer , UserLevelSerializer, WorldSerializer
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import LevelStatusSerializer , CardSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from django.db import models

# --- Serializers المخصصة لتوثيق ردود الخريطة والعوالم في Swagger ---
class GameWorldResponseSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="معرف العالم")
    name = serializers.CharField(help_text="اسم العالم (مثل: الفضاء، الغابة)")
    is_playable = serializers.BooleanField(help_text="هل العالم متاح للعب حالياً للطفل بناءً على تقدمه")
    message = serializers.CharField(help_text="رسالة توضيحية لحالة العالم للاعب")

class WorldLevelsListSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="معرف المستوى")
    level_number = serializers.IntegerField(help_text="رقم المستوى الترتيبي")
    intro_message = serializers.CharField(help_text="الرسالة الترحيبية للمستوى")

class WorldLevelsResponseSerializer(serializers.Serializer):
    world_name = serializers.CharField(help_text="اسم العالم المطلوب")
    levels = WorldLevelsListSerializer(many=True, help_text="قائمة المستويات التابعة لهذا العالم")


# =====================================================================
# 🌟 1. الـ APIs العامة والإدارية (العوالم والمستويات العامة) - CRUD Methods
# =====================================================================

class WORLDListCreateView(ListCreateAPIView):
    """إضافة عالم جديد أو عرض كل العوالم (قاعدة بيانات عامة)"""
    queryset = GameWorld.objects.all()
    serializer_class = WorldSerializer

class WORLDDetailView(RetrieveUpdateDestroyAPIView):
    """جلب عالم محدد بالـ ID، تعديله، أو حذفه بالكامل"""
    queryset = GameWorld.objects.all()
    serializer_class = WorldSerializer

class LevelListCreateView(ListCreateAPIView):
    """إضافة مستوى جديد أو عرض كل المستويات العامة"""
    queryset = Level.objects.all()
    serializer_class = LevelSerializer

class LevelDetailView(RetrieveUpdateDestroyAPIView):
    """جلب مستوى محدد بالـ ID، تعديله، أو حذفه"""
    queryset = Level.objects.all()
    serializer_class = LevelSerializer


# =====================================================================
# 🌟 2. الـ APIs الخاصة بتقدم المستخدم وحالته الشخصية (User Levels) - CRUD
# =====================================================================

class UserLevelListCreateView(ListCreateAPIView):
    """عرض أو إنشاء سجلات تقدم الطلاب في المستويات"""
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer

class UserLevelDetailView(RetrieveUpdateDestroyAPIView):
    """تحديث أو حذف سجل تقدم طالب في مستوى معين عبر الـ ID"""
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer

class CardListCreateView(ListCreateAPIView):
    """إضافة بطاقة جديدة أو عرض كل البطاقات العامة"""
    queryset = PlanetCard.objects.all()
    serializer_class = CardSerializer

class CardDetailView(RetrieveUpdateDestroyAPIView):
    """جلب بطاقة محددة بالـ ID، تعديله، أو حذفه"""
    queryset = PlanetCard.objects.all()
    serializer_class = CardSerializer

# =====================================================================
# 🌟 3. الـ APIs الذكية المخصصة للعبة (الفرونت إند والـ Flutter)
# =====================================================================

@extend_schema(
    summary="جلب قائمة العوالم المخصصة للمستخدم الحالي بناءً على النقاط المطلوبة في الموديل",
    description="تتحقق من إجمالي نقاط الطفل الحالية، وتفتح العوالم الديناميكية بناءً على قيمة النقاط المحددة في الموديل.",
    responses={200: GameWorldResponseSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_worlds(request):
    """
    جلب العوالم وحالتها الديناميكية بناءً على النقاط المطلوبة المخزنة في الـ Model
    """
    worlds = GameWorld.objects.all().order_by('id')
    user = request.user
    data = []

    if not worlds.exists():
        return Response([])

    # 1️⃣ حساب إجمالي النقاط الحالية التي جمعها الطفل من المستويات التي أكملها
    try:
        # نقوم بجمع النقاط المكتسبة من جدول UserLevel للمستويات الـ COMPLETED فقط
        total_points = UserLevel.objects.filter(
            user=user, 
            status='COMPLETED'
        ).aggregate(total=models.Sum('points_earned'))['total'] or 0
    except Exception:
        total_points = 0

    # 2️⃣ فحص كل عالم ومقارنة نقاط الطفل بالنقاط المطلوبة من الموديل
    for index, w in enumerate(worlds):
        # 🌟 جلب النقاط المطلوبة لفتح العالم مباشرة من حقل الموديل (points_to_open)
        # إذا كان اسم الحقل في الموديل عندك مختلف (مثلاً points_required)، قمي بتعديل الاسم هنا فقط.
        points_needed = getattr(w, 'points_to_open', 0)
        
        if index == 0:
            # العالم الأول مفتوح دائماً كترحيب بالطفل عند التسجيل
            is_playable = True
            message = "مرحباً بك في عالمك الأول! جاهز للمغامرة واللعب؟ 🚀"
        else:
            # العوالم التالية: نقارن إجمالي نقاط الطفل بالنقاط المطلوبة لفتح هذا العالم
            if total_points >= points_needed:
                is_playable = True
                message = f"رائع! لقد جمعت {total_points} نقطة وفتحت هذا العالم بنجاح 🎉"
            else:
                is_playable = False
                points_still_needed = points_needed - total_points
                message = f"🔒 هذا العالم مغلق. تحتاج إلى جمع {points_still_needed} نقطة إضافية لفتحه!"

        data.append({
            "id": w.id,
            "name": w.name,
            "is_playable": is_playable,
            "points_required": points_needed,
            "current_user_points": total_points,
            "message": message
        })
        
    return Response(data)



@extend_schema(
    summary="جلب خريطة مستويات المستخدم الشخصية (My Map)",
    description="تُرجع الخريطة الكاملة للمستويات مرتبة برقم المستوى، وتتضمن حالة كل مستوى بالنسبة للطفل الحالي (مفتوح Unlocked، مغلق Locked، أو مكتمل Completed) بناءً على التوكن الممرر.",
    responses={200: LevelStatusSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_map(request):
    levels = Level.objects.all().order_by('level_number')
    serializer = LevelStatusSerializer(levels, many=True, context={'request': request})
    
    return Response(serializer.data)