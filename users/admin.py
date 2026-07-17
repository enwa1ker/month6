from django.contrib import admin

from users.models import CustomUser
from django.contrib.auth.admin import UserAdmin


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ["id", "email", "phone_number", "birthdate", "is_active"]
    list_editable = ["is_active"]
    ordering = ["email"]
    search_fields = ["email", "phone_number"]

    fieldsets = (
        (None, {"fields": ("email", "password", "phone_number", "birthdate", "is_active")} ),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "phone_number", "password1", "password2", "is_active", "is_staff", "is_superuser"),
        }),
    )
