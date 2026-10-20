from django.contrib import admin

from tenants.admin import TenantAdminMixin

from .models import LoyaltyAccount, LoyaltyProgram, LoyaltyReward, LoyaltyTransaction


@admin.register(LoyaltyProgram)
class LoyaltyProgramAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("tenant", "spend_per_point", "is_active")


@admin.register(LoyaltyReward)
class LoyaltyRewardAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "points_required", "is_active", "tenant")
    ordering = ("points_required",)


@admin.register(LoyaltyAccount)
class LoyaltyAccountAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("user", "member_code", "tenant", "created_at")
    search_fields = ("user__email", "user__full_name", "member_code")
    readonly_fields = ("member_code",)


@admin.register(LoyaltyTransaction)
class LoyaltyTransactionAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Libro de movimientos. Los ajustes manuales (regalar o corregir puntos) se hacen aquí."""

    list_display = ("account", "points", "kind", "note", "created_at")
    list_filter = ("kind",)
    search_fields = ("account__user__email", "account__member_code")
