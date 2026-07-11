from django.shortcuts import render
from .models import Level , UserLevel , GameWorld
from .serializers import LevelSerializer , UserLevelSerializer, WorldSerializer
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .serializers import LevelStatusSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

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


# =====================================================================
# 🌟 3. الـ APIs الذكية المخصصة للعبة (الفرونت إند والـ Flutter)
# =====================================================================

@extend_schema(
    summary="جلب قائمة العوالم المخصصة للمستخدم الحالي (تحديد المفتوح والمغلق للطفل)",
    description="تتحقق من هوية الطفل عبر التوكن، وترجع العوالم مع تحديد ما إذا كان العالم مفتوحاً له بناءً على تقدمه في اللعبة.",
    responses={200: GameWorldResponseSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_worlds(request):
    """
    جلب العوالم وحالتها الديناميكية الخاصة بكل طفل على حدة (تفتح بالتوالي)
    """
    worlds = GameWorld.objects.all().order_by('id')
    user = request.user
    data = []

    # جلب معرفات المستويات التي نجح فيها الطفل أو فتحها بالفعل
    unlocked_level_ids = UserLevel.objects.filter(
        user=user, 
        status__in=['UNLOCKED', 'COMPLETED']
    ).values_list('level_id', flat=True)

    for index, w in enumerate(worlds):
        # العالم الأول (Index 0) يكون مفتوحاً بشكل تلقائي دائماً للجميع كبداية للعبة
        if index == 0:
            is_playable = True
            message = "جاهز للمغامرة واللعب! 🚀"
        else:
            # العوالم التالية تفتح فقط إذا كان الطفل قد فتح أو أنهى مستويات من العالم السابق له
            previous_world = worlds[index - 1]
            prev_world_levels = previous_world.levels.values_list('id', flat=True)
            
            # شرط الذكاء: إذا كان هناك تداخل أو نجاح في مستويات العالم السابق، يفتح العالم التالي
            has_progress_in_prev = any(l_id in unlocked_level_ids for l_id in prev_world_levels)
            
            if has_progress_in_prev or w.is_active:
                is_playable = True
                message = "لقد فتحت هذا العالم بنجاح! 🎉"
            else:
                is_playable = False
                message = "🔒 هذا العالم مغلق. أكمل العوالم السابقة أولاً لتفتحه!"

        data.append({
            "id": w.id,
            "name": w.name,
            "is_playable": is_playable,
            "message": message
        })
        
    return Response(data)


@extend_schema(
    summary="جلب مستويات عالم محدد عبر الـ ID",
    description="تستقبل المعرّف الرقمي الخاص بالعالم لترجع قائمة بجميع المستويات التابعة له إذا كان العالم فعالاً ونشطاً.",
    responses={
        200: WorldLevelsResponseSerializer,
        403: serializers.Serializer(help_text="العالم مغلق حالياً")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_world_levels(request, world_slug):
    """
    جلب مستويات عالم محدد عبر الـ ID
    """
    world = get_object_or_404(GameWorld, id=world_slug)
    
    # جلب مستويات هذا العالم فقط وترتيبها تصاعدياً
    levels = world.levels.all().order_by('level_number')
    
    return Response({
        "world_name": world.name,
        "levels": list(levels.values('id', 'level_number', 'intro_message')) 
    })


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