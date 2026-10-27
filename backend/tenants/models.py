from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


hex_color = RegexValidator(r"^#[0-9a-fA-F]{6}$", "Usa un color hexadecimal como #F07830.")


class Tenant(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    # Marca blanca: la app toma estos valores del tenant; el resto del tema se deriva en la app.
    primary_color = models.CharField(max_length=7, default="#171717", validators=[hex_color])
    secondary_color = models.CharField(max_length=7, default="#F5F5F5", validators=[hex_color])
    logo_url = models.CharField(
        max_length=300, blank=True, help_text="URL completa o una ruta del servidor como /static/brands/logo.jpg"
    )
    loyalty_enabled = models.BooleanField(
        default=True, help_text="Si se apaga, la app oculta la tarjeta y los puntos."
    )
    # Módulos contratables de la suite (la lealtad es el de arriba).
    orders_enabled = models.BooleanField(
        default=True, help_text="Pedidos móviles: si se apaga, la app oculta menú y carrito y la API rechaza pedidos."
    )
    kds_enabled = models.BooleanField(
        default=True, help_text="Tablero de pedidos (KDS): si se apaga, el personal no lo ve."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)

    def for_tenant_ids(self, tenant_ids):
        return self.filter(tenant_id__in=tenant_ids)


class TenantModel(models.Model):
    """Base de toda tabla de negocio: lleva tenant_id y se filtra siempre por tenant."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="+")

    objects = TenantQuerySet.as_manager()

    # Campos FK que deben pertenecer al mismo tenant que el registro.
    tenant_fk_fields = ()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.tenant_id is None:  # el admin asigna el tenant después de validar el formulario
            return
        for name in self.tenant_fk_fields:
            related = getattr(self, name, None)
            if related is not None and related.tenant_id != self.tenant_id:
                raise ValidationError({name: "Pertenece a otro tenant."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Membership(models.Model):
    """Enlaza un usuario con un tenant (staff del negocio o cliente)."""

    class Role(models.TextChoices):
        OWNER = "owner", "Dueño"
        STAFF = "staff", "Staff"
        CUSTOMER = "customer", "Cliente"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "tenant"], name="uniq_membership_user_tenant")
        ]

    def __str__(self):
        return f"{self.user} @ {self.tenant} ({self.role})"


class Branch(TenantModel):
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    hours = models.CharField(max_length=120, blank=True, help_text="Texto libre, por ejemplo: Todos los días · cierra 10 p. m.")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "branches"

    def __str__(self):
        return self.name


def user_tenant_ids(user):
    return list(
        user.memberships.filter(tenant__is_active=True).values_list("tenant_id", flat=True)
    )
