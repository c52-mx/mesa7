from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MesaUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "phone", "is_staff", "is_active")
    search_fields = ("email", "full_name", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Datos", {"fields": ("full_name", "phone")}),
        (
            "Permisos",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
