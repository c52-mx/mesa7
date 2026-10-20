from django.conf import settings
from django.db import models
from django.utils import timezone

from tenants.models import TenantModel


class Order(TenantModel):
    tenant_fk_fields = ("branch",)

    class Status(models.TextChoices):
        RECEIVED = "received", "Recibido"
        PREPARING = "preparing", "En preparación"
        READY = "ready", "Listo"
        DELIVERED = "delivered", "Entregado"
        CANCELLED = "cancelled", "Cancelado"

    class PaymentMethod(models.TextChoices):
        COUNTER = "counter", "En el mostrador"
        ONLINE = "online", "En la app"

    class PaymentStatus(models.TextChoices):
        PENDING = "pending", "Pendiente"
        PAID = "paid", "Pagado"

    ACTIVE = (Status.RECEIVED, Status.PREPARING, Status.READY)
    # Pedidos que todavía ocupan a la cocina (para calcular el ETA).
    IN_KITCHEN = (Status.RECEIVED, Status.PREPARING)

    branch = models.ForeignKey("tenants.Branch", on_delete=models.PROTECT, related_name="+")
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="orders"
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.RECEIVED, db_index=True
    )
    notes = models.TextField(blank=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COUNTER)
    payment_status = models.CharField(
        max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING, db_index=True
    )
    total = models.DecimalField(max_digits=10, decimal_places=2)
    prep_minutes = models.PositiveIntegerField(help_text="Preparación estimada de este pedido")
    estimated_ready_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    status_changed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Pedido #{self.pk}"


class OrderItem(TenantModel):
    tenant_fk_fields = ("order", "product")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("menu.Product", on_delete=models.PROTECT, related_name="+")
    # Copia al momento de la compra: el menú puede cambiar después.
    name = models.CharField(max_length=120)
    unit_price = models.DecimalField(
        max_digits=8, decimal_places=2, help_text="Precio de una pieza, ya con los extras elegidos"
    )
    quantity = models.PositiveSmallIntegerField()
    # Opciones elegidas al momento de la compra: [{"group": "Tamaño", "name": "Grande", "price_delta": "12.00"}]
    options = models.JSONField(default=list, blank=True)
    notes = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.name}"
