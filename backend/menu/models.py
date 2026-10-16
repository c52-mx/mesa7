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
