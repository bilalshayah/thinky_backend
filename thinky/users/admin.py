from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # إضافة الحقول الجديدة لعرضها في قائمة المستخدمين (Table)
    list_display = ("username", "email", "gender", "total_points", "is_staff")
    
    # إضافة الحقل الجديد داخل صفحة تعديل/إضافة المستخدم
    fieldsets = UserAdmin.fieldsets + (
        ("Additional Info", {"fields": ("gender", "phone_number", "birthday", "total_points")}),
    )
    
    # إضافة الحقل عند إنشاء مستخدم جديد من الأدمن
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional Info", {"fields": ("gender", "phone_number", "birthday")}),
    )

admin.site.register(User, CustomUserAdmin)