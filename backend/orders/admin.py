from django.contrib import admin

from tenants.admin import TenantAdminMixin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "unit_price", "quantity")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Vista de soporte: los pedidos se crean desde la app; aquí solo se consultan y se corrige el estado."""

    list_display = ("id", "branch", "customer", "status", "total", "created_at")
    list_filter = ("branch", "status")
    fields = (
        "branch", "customer", "status", "total", "notes",
        "prep_minutes", "estimated_ready_at", "created_at",
    )
    readonly_fields = tuple(f for f in fields if f != "status")
    inlines = [OrderItemInline]

    def has_add_permission(self, request):
        return False
