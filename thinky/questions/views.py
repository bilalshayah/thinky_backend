from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from .models import Question, Skill
from .serializers import QuestionSerializer, SkillSerializer

# Create your views here.

class QuestionListCreateView(ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    # 🌟 دعم رفع الأسئلة دفعة واحدة عند استخدام هذه الـ View
    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data'), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)


class QusetionDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class SkillListCreateView(ListCreateAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


class SkillDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer


# 1️⃣ إضافة سؤال واحد فقط
class QuestionCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request=QuestionSerializer,
        responses={201: QuestionSerializer},
        description="هذه الـ Endpoint تتيح لك إضافة سؤال واحد جديد فقط إلى قاعدة البيانات."
    )
    def post(self, request):
        serializer = QuestionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2️⃣ إضافة قائمة من الأسئلة دفعة واحدة (Bulk Create)
class QuestionBulkCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=QuestionSerializer(many=True), # 🌟 هنا نخبر Swagger أنها قائمة من الأسئلة وليست سؤالاً واحداً
        responses={201: {"type": "object", "properties": {"message": {"type": "string"}}}},
        description="هذه الـ Endpoint تتيح لك رفع قائمة (List) كاملة من الأسئلة دفعة واحدة."
    )
    def post(self, request, *args, **kwargs):
        if not isinstance(request.data, list):
            return Response(
                {"error": "المعطيات غير صالحة. يجب إرسال قائمة (List) من الأسئلة وليس سؤالاً واحداً."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = QuestionSerializer(data=request.data, many=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": f"تم بنجاح حفظ {len(serializer.data)} سؤال جديد! 🎉"},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)