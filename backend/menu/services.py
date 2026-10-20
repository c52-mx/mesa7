from django.db.models import Prefetch

from .models import Option, ProductOptionGroup


def option_groups_for(products):
    """Grupos de opciones vigentes por producto: {product_id: [grupo, ...]}.

    Cada grupo trae sus opciones activas. `required` es el mínimo efectivo: si un grupo pide más
    opciones de las que hay activas, se baja al número disponible para no bloquear el pedido.
    Los grupos sin opciones activas se omiten.
    """
    links = (
        ProductOptionGroup.objects.filter(product__in=products)
        .select_related("group")
        .prefetch_related(
            Prefetch("group__options", queryset=Option.objects.filter(is_active=True), to_attr="active_options")
        )
    )
    result = {product.pk: [] for product in products}
    for link in links:
        options = link.group.active_options
        if not options:
            continue
        result[link.product_id].append(
            {
                "id": link.group_id,
                "name": link.group.name,
                "required": min(link.group.min_select, len(options)),
                "max_select": link.group.max_select,
                "options": [
                    {"id": o.pk, "name": o.name, "price_delta": o.price_delta, "is_popular": o.is_popular}
                    for o in options
                ],
            }
        )
    return result
