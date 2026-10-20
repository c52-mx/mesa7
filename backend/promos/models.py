from django.db import models

from tenants.models import TenantModel


class Banner(TenantModel):
    """Promoción del carrusel del Inicio de la app."""

    title = models.CharField(max_length=80)
    text = models.CharField(max_length=200, blank=True)
    image_url = models.URLField(blank=True, help_text="Opcional. Sin imagen se muestra con los colores de la marca.")
    position = models.PositiveIntegerField(default=0, help_text="Orden de aparición (menor primero)")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["position", "id"]

    def __str__(self):
        return self.title
