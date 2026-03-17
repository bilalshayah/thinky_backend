from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


class CustomUserAdmin(UserAdmin):

    model = User

    fieldsets = UserAdmin.fieldsets + (
        ("Extra Info", {
            "fields": ("phone_number", "birthday", "total_points")
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {
            "fields": ("phone_number", "birthday")
        }),
    )


admin.site.register(User, CustomUserAdmin)