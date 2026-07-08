from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Classroom

# تسجيل موديل المستخدم المخصص باحترافية لحمايته من كراش الـ 500
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # إضافة الحقول الجديدة المخصصة (role, total_points, gender) لكي تظهر في لوحة التحكم
    fieldsets = UserAdmin.fieldsets + (
        ('معلومات اللعبة والأدوار', {'fields': ('role', 'gender', 'total_points', 'streak_count', 'parent_of')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('معلومات اللعبة والأدوار', {'fields': ('role', 'gender', 'total_points', 'streak_count')}),
    )
    list_display = ['username', 'email', 'role', 'total_points', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser']

# تسجيل موديل الفصول الدراسية أيضاً لكي تتمكني من التحكم به
@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'teacher', 'class_code']
    search_fields = ['name', 'class_code']