from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models import User
from points.models import Points
from user_store.models import UserStore
from .models import Store
# Create your views here.
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListCreateAPIView
from .serializers import StoreSerializer
from points.models import Points
from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import serializers
# Create your views here.

class StoreListCreateView(ListCreateAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer

class StoreDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Store.objects.all()
    serializer_class = StoreSerializer


class BUYSerializer(serializers.Serializer):
    item_id = serializers.IntegerField(help_text="ID الخاص بالمستوى")

@extend_schema(
    request=BUYSerializer, # هنا نخبر Swagger بالمدخلات
    responses={201: StoreSerializer}, 
    description="بدء جلسة لعب جديدة باستخدام رقم المستوى"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buy_item(request):
    user = request.user
    item_id = request.data.get("item_id")
    try:
        item = Store.objects.get(id=item_id)
    except Store.DoesNotExist :
        return Response({"error!":"this item does not exist"},status=404)
    if user.total_points >= item.required_points:
        user.total_points -= item.required_points
        user.save()

        Points.objects.create(
        user=user,
        amount= item.required_points,
        type='spend',
        store_item=item
    )
        UserStore.objects.create(
          user=user,
          item=item
        )
        Points.objects.create(
       user=user,
       type="spend",
       amount= item.required_points,
       store_item=item
    )

        purchase_status = True
    else:
      purchase_status = False
    if purchase_status:
      return Response({"message": "تم الشراء بنجاح! استمتع بغرضك الجديد", "remaining_points": user.total_points})
    else:
      return Response({"error": "للأسف، لا تملك نقاطاً كافية"}, status=400)

