from django.shortcuts import render
from .models import Level , UserLevel , GameWorld
from .serializers import LevelSerializer , UserLevelSerializer
from rest_framework.generics import ListCreateAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
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
    is_playable = serializers.BooleanField(help_text="هل العالم متاح للعب حالياً أم مغلق")
    message = serializers.CharField(help_text="رسالة توضيحية لحالة العالم للاعب")

class WorldLevelsListSerializer(serializers.Serializer):
    id = serializers.IntegerField(help_text="معرف المستوى")
    level_number = serializers.IntegerField(help_text="رقم المستوى الترتيبي")
    intro_message = serializers.CharField(help_text="الرسالة الترحيبية للمستوى")

class WorldLevelsResponseSerializer(serializers.Serializer):
    world_name = serializers.CharField(help_text="اسم العالم المطلوب")
    levels = WorldLevelsListSerializer(many=True, help_text="قائمة المستويات التابعة لهذا العالم")

@extend_schema(
    summary="جلب قائمة جميع العوالم وحالتها",
    description="ترجع هذه الدالة جميع العوالم المتاحة في اللعبة لتعرض في القائمة الرئيسية وتوضح أي العوالم مفتوح للعب (مثل الفضاء) وأيها سيفتح قريباً.",
    responses={200: GameWorldResponseSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_game_worlds(request):
    """
    إرجاع جميع العوالم المتاحة وحالتها للواجهة الجديدة
    """
    worlds = GameWorld.objects.all()
    data = []
    for w in worlds:
        data.append({
            "id": w.id,
            "name": w.name,
            "is_playable": w.is_active, # الفضاء سيكون True، والبقية False
            "message": "جاهز للعب!" if w.is_active else "قريباً في التحديث القادم!"
        })
    return Response(data)


@extend_schema(
    summary="جلب مستويات عالم محدد عبر الـ Slug",
    description="تستقبل الـ Slug الخاص بالعالم (مثل space) لترجع قائمة بجميع المستويات التابعة له إذا كان العالم فعالاً ونشطاً.",
    responses={
        200: WorldLevelsResponseSerializer,
        403: serializers.Serializer(help_text="العالم مغلق حالياً")
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_world_levels(request, world_slug):
    """
    جلب مستويات عالم محدد إذا كان فعالاً (مثل الفضاء)
    """
    world = get_object_or_404(GameWorld, slug=world_slug)
    
    # إذا كان العالم غير مفعل (مثل الغابة)، نرجع استجابة فارغة أو رسالة مغلق
    if not world.is_active:
        return Response({
            "error": "This world is currently locked.",
            "levels": []
        }, status=403)
        
    # جلب مستويات هذا العالم فقط وترتيبها
    levels = world.levels.all().order_by('level_number')
    
    # هنا يمكنك استخدام السيريالايزر الخاص بالمستويات لديكِ لعرض البيانات للفروتيند
    # مثال افتراضي:
    return Response({
        "world_name": world.name,
        "levels": list(levels.values('id', 'level_number', 'intro_message')) # عدلي الحقول حسب الحاجة
    })


class LevelListCreateView(ListCreateAPIView):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer


class LevelDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Level.objects.all()
    serializer_class = LevelSerializer



class UserLevelDetailView(RetrieveUpdateDestroyAPIView):
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer

class UserLevelListCreateView(ListCreateAPIView):
    queryset = UserLevel.objects.all()
    serializer_class = UserLevelSerializer


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

