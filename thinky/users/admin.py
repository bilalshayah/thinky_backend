# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Classroom

class CustomUserAdmin(UserAdmin):
    # إضافة الحقول الجديدة لواجهة الإدارة
    fieldsets = UserAdmin.fieldsets + (
        ('Educational Info', {'fields': ('role', 'parent_of', 'gender', 'birthday', 'total_points', 'streak_count')}),
    )
    list_display = ['username', 'email', 'role', 'is_staff']
    filter_horizontal = ('parent_of',) # لتسهيل اختيار الأطفال للوالد

admin.site.register(User, CustomUserAdmin)
admin.site.register(Classroom)