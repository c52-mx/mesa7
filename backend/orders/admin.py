from django.contrib import admin, messages

from tenants.admin import TenantAdminMixin

from .models import Order, OrderItem
from .services import change_status


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ("name", "options", "notes", "unit_price", "quantity")
    readonly_fields = fields
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


def status_action(status):
    @admin.action(description=f"Marcar como: {Order.Status(status).label}")
    def action(modeladmin, request, queryset):
        for order in queryset:
            change_status(order, status, force=True)
        modeladmin.message_user(
            request, f"{queryset.count()} pedido(s) marcados como «{Order.Status(status).label}».", messages.SUCCESS
        )

    action.__name__ = f"mark_{status}"
    return action


@admin.register(Order)
class OrderAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Vista de soporte: los pedidos se crean desde la app; aquí se consultan y se corrige el estado.

    Un cambio de estado desde aquí avisa al cliente igual que el KDS (tiempo real, push y puntos).
    """

    list_display = ("id", "branch", "customer", "status", "total", "created_at")
    list_filter = ("branch", "status")
    fields = (
        "branch", "customer", "status", "total", "notes",
        "prep_minutes", "estimated_ready_at", "created_at",
    )
    readonly_fields = tuple(f for f in fields if f != "status")
    inlines = [OrderItemInline]
    actions = [status_action(s) for s in ("preparing", "ready", "delivered", "cancelled")]

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            new_status = obj.status
            obj.status = form.initial["status"]  # el servicio hace el cambio y avisa
            change_status(obj, new_status, force=True)
            return
        super().save_model(request, obj, form, change)
