from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView , RetrieveUpdateDestroyAPIView , ListAPIView
from .models import UserStore
from .serializers import UserSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes , api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
# Create your views here.
'''''
class UserStoreListCreateView(ListCreateAPIView):
    queryset = UserStore.objects.all()
    serializer_class = UserSerializer

class UserStoreDetailView(RetrieveUpdateDestroyAPIView):
    queryset = UserStore.objects.all()
    serializer_class = UserSerializer
'''
@extend_schema(
    summary="جلب المشتريات والعناصر الخاصة بالمستخدم الحالي (My Store)",
    description="تُرجع قائمة كاملة بجميع العناصر والبطاقات الثقافية التي قام الطفل بشرائها من المتجر، حيث يتم تصفيتها تلقائياً بناءً على توكن الحساب المسجل دون الحاجة لإرسال أي معرفات في الرابط.",
    responses={200: UserSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_items(request):
    """
    هذه الدالة تعيد كل الأشياء التي اشتراها المستخدم الحالي فقط
    بدون الحاجة لإرسال ID في الرابط
    """
    # نأتي بالمشتريات الخاصة بالمستخدم من الـ Token مباشرة
    purchases = UserStore.objects.filter(user=request.user)
    serializer = UserSerializer(purchases, many=True)
    
    return Response(serializer.data)