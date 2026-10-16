from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Tenant(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class TenantQuerySet(models.QuerySet):
    def for_tenant(self, tenant):
        return self.filter(tenant=tenant)


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
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "branches"

    def __str__(self):
        return self.name


def get_tenant(user):
    """Tenant del usuario (primer membership), o None."""
    if not user or not user.is_authenticated:
        return None
    membership = user.memberships.select_related("tenant").first()
    return membership.tenant if membership else None
