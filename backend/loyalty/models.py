from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from tenants.models import TenantModel


class LoyaltyProgram(TenantModel):
    """Reglas de acumulación del negocio (una por tenant)."""

    spend_per_point = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=10,
        validators=[MinValueValidator(0.01)],
        help_text="Pesos que se gastan para ganar 1 punto",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant"], name="uniq_loyalty_program_per_tenant")
        ]

    def __str__(self):
        return f"Programa de {self.tenant}"


class LoyaltyReward(TenantModel):
    """Hito de la barra de progreso: a cuántos puntos se desbloquea qué premio."""

    name = models.CharField(max_length=120)
    points_required = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["points_required"]

    def __str__(self):
        return f"{self.name} ({self.points_required} pts)"


class LoyaltyAccount(TenantModel):
    """Tarjeta de un cliente en un negocio. member_code es lo que lleva el QR."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="loyalty_accounts"
    )
    member_code = models.CharField(max_length=12)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "user"], name="uniq_loyalty_account_user"),
            models.UniqueConstraint(fields=["tenant", "member_code"], name="uniq_loyalty_member_code"),
        ]

    def __str__(self):
        return f"{self.user} · {self.member_code}"


class LoyaltyTransaction(TenantModel):
    """Libro de movimientos: el saldo es la suma de los puntos."""

    tenant_fk_fields = ("account", "order")

    class Kind(models.TextChoices):
        EARN = "earn", "Acumulación"
        REDEEM = "redeem", "Canje"
        ADJUST = "adjust", "Ajuste manual"

    account = models.ForeignKey(LoyaltyAccount, on_delete=models.CASCADE, related_name="transactions")
    points = models.IntegerField(help_text="Positivo suma, negativo resta")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    order = models.ForeignKey("orders.Order", null=True, blank=True, on_delete=models.PROTECT, related_name="+")
    note = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            # Un pedido solo acumula puntos una vez.
            models.UniqueConstraint(
                fields=["order"], condition=models.Q(kind="earn"), name="uniq_earn_per_order"
            )
        ]

    def __str__(self):
        return f"{self.points:+d} · {self.account}"
