from rest_framework import serializers
from .models import Question , Skill


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        #fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'hint', 'is_hakeem']
        fields = "__all__"

class QuestionGameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        #fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'hint', 'is_hakeem']
        fields = "__all__"

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = "__all__"
        #fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'hint', 'is_hakeem']


class QuestionBankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'question_text', 'difficulty', 'skill']