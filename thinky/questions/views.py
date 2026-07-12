from django.shortcuts import render
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.generics import ListCreateAPIView
from .serializers import QuestionSerializer , SkillSerializer
from .models import Question , Skill
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
# Create your views here.

class QuestionListCreateView(ListCreateAPIView):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    # 🌟 إضافة هذا التعديل الذكي ليدعم رفع الأسئلة دفعة واحدة (Bulk Create)
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


class QuestionBulkCreateView(APIView):
    permission_classes = [IsAuthenticated]

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