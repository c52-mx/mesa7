from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from tenants.models import TenantModel


class Category(TenantModel):
    name = models.CharField(max_length=120)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(TenantModel):
    tenant_fk_fields = ("category",)

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    image_url = models.URLField(blank=True, help_text="Foto del producto (opcional)")
    is_featured = models.BooleanField(default=False, help_text="Aparece en la sección Destacados")
    prep_time_minutes = models.PositiveIntegerField(
        default=5, help_text="Tiempo estándar de preparación"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__position", "name"]

    def __str__(self):
        return self.name


class BranchProduct(TenantModel):
    """Disponibilidad de un producto en una sucursal.

    Sin registro, el producto está disponible; un registro con is_available=False lo oculta.
    """

    tenant_fk_fields = ("branch", "product")

    branch = models.ForeignKey("tenants.Branch", on_delete=models.CASCADE, related_name="+")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="+")
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["branch", "product"], name="uniq_branch_product")
        ]

    def __str__(self):
        return f"{self.product} @ {self.branch}"


class OptionGroup(TenantModel):
    """Grupo de opciones reutilizable (Tamaño, Tipo de leche, Extras...) que se asigna a productos."""

    name = models.CharField(max_length=120)
    min_select = models.PositiveSmallIntegerField(
        default=0, help_text="Mínimo a elegir. 0 = opcional, 1 o más = obligatorio"
    )
    max_select = models.PositiveSmallIntegerField(
        default=1, validators=[MinValueValidator(1)], help_text="Máximo a elegir"
    )

    class Meta:
        ordering = ["name"]

    def clean(self):
        super().clean()
        if self.max_select is not None and self.min_select is not None and self.max_select < self.min_select:
            raise ValidationError({"max_select": "El máximo no puede ser menor que el mínimo."})

    def __str__(self):
        return self.name


class Option(TenantModel):
    tenant_fk_fields = ("group",)

    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name="options")
    name = models.CharField(max_length=120)
    price_delta = models.DecimalField(
        max_digits=8, decimal_places=2, default=0, validators=[MinValueValidator(0)],
        help_text="Cargo extra en pesos (0 si no cuesta)",
    )
    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.name


class ProductOptionGroup(TenantModel):
    """Qué grupos de opciones tiene un producto y en qué orden aparecen."""

    tenant_fk_fields = ("product", "group")

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="option_links")
    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE, related_name="+")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["position", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "group"], name="uniq_product_option_group")
        ]

    def __str__(self):
        return f"{self.product} · {self.group}"
