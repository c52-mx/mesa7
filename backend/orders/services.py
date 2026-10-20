import math
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from loyalty.services import award_for_order
from menu.models import BranchProduct, Product
from menu.services import option_groups_for

from .models import Order, OrderItem
from .realtime import publish_order

# Pedidos que la cocina prepara en paralelo (baristas/estaciones). Ajustable por sucursal más adelante.
KITCHEN_CONCURRENCY = 2

TRANSITIONS = {
    Order.Status.RECEIVED: {Order.Status.PREPARING, Order.Status.CANCELLED},
    Order.Status.PREPARING: {Order.Status.READY, Order.Status.CANCELLED},
    Order.Status.READY: {Order.Status.DELIVERED, Order.Status.CANCELLED},
}


def own_prep_minutes(lines):
    """Preparación del pedido: nunca menos que su producto más lento."""
    slowest = max(product.prep_time_minutes for product, _ in lines)
    parallel = math.ceil(
        sum(product.prep_time_minutes * qty for product, qty in lines) / KITCHEN_CONCURRENCY
    )
    return max(slowest, parallel)


def kitchen_backlog_minutes(tenant, branch):
    """Minutos de trabajo pendientes en el KDS real de la sucursal, repartidos entre la cocina."""
    pending = (
        Order.objects.for_tenant(tenant)
        .filter(branch=branch, status__in=Order.IN_KITCHEN)
        .aggregate(total=Sum("prep_minutes"))["total"]
        or 0
    )
    return math.ceil(pending / KITCHEN_CONCURRENCY)


def choose_options(product, groups, option_ids):
    """Valida las opciones elegidas contra los grupos del producto y devuelve su detalle.

    Cada grupo debe respetar su mínimo (obligatorio) y su máximo. Una opción que no pertenece a un
    grupo vigente del producto se rechaza.
    """
    by_id = {o["id"]: (g, o) for g in groups for o in g["options"]}
    if len(set(option_ids)) != len(option_ids) or any(i not in by_id for i in option_ids):
        raise ValidationError({"items": f"Opciones no válidas para {product.name}."})
    chosen = [by_id[i] for i in option_ids]
    for group in groups:
        count = sum(1 for g, _ in chosen if g["id"] == group["id"])
        if count < group["required"] or count > group["max_select"]:
            rule = (
                f"elige {group['required']}"
                if group["required"] == group["max_select"]
                else f"elige de {group['required']} a {group['max_select']}"
            )
            raise ValidationError({"items": f"{product.name}: en «{group['name']}» {rule}."})
    return [
        {"group": g["name"], "name": o["name"], "price_delta": str(o["price_delta"])} for g, o in chosen
    ]


@transaction.atomic
def create_order(*, tenant, branch, customer, items, notes=""):
    """items: lista de líneas {"product": id, "quantity": n, "options": [id, ...], "notes": "..."}.

    Cada línea es independiente: el mismo producto con otras opciones o notas es otra línea.
    """
    product_ids = {item["product"] for item in items}
    products = {
        p.pk: p
        for p in Product.objects.for_tenant(tenant).filter(pk__in=product_ids, is_active=True)
    }
    hidden = set(
        BranchProduct.objects.for_tenant(tenant)
        .filter(branch=branch, is_available=False, product_id__in=product_ids)
        .values_list("product_id", flat=True)
    )
    missing = [pk for pk in product_ids if pk not in products or pk in hidden]
    if missing:
        raise ValidationError({"items": f"Productos no disponibles en esta sucursal: {sorted(missing)}"})

    groups = option_groups_for(list(products.values()))
    lines = []  # (producto, cantidad, opciones elegidas, notas, precio unitario con extras)
    for item in items:
        product = products[item["product"]]
        chosen = choose_options(product, groups[product.pk], item.get("options", []))
        unit_price = product.price + sum(Decimal(o["price_delta"]) for o in chosen)
        lines.append((product, item["quantity"], chosen, item.get("notes", "").strip(), unit_price))

    prep = own_prep_minutes([(product, qty) for product, qty, *_ in lines])
    eta = kitchen_backlog_minutes(tenant, branch) + prep
    order = Order.objects.create(
        tenant=tenant,
        branch=branch,
        customer=customer,
        notes=notes,
        total=sum(unit * qty for _, qty, _, _, unit in lines),
        prep_minutes=prep,
        estimated_ready_at=timezone.now() + timedelta(minutes=eta),
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                tenant=tenant,
                order=order,
                product=product,
                name=product.name,
                unit_price=unit,
                quantity=qty,
                options=chosen,
                notes=line_notes,
            )
            for product, qty, chosen, line_notes, unit in lines
        ]
    )
    # lambda y no partial: con robust=True Django lee func.__qualname__ al registrar el error.
    transaction.on_commit(lambda: publish_order(order.pk), robust=True)
    return order


def change_status(order, new_status, *, force=False):
    """Cambia el estado y avisa (tiempo real, push, puntos).

    El KDS solo sigue el flujo normal; `force=True` (soporte desde el admin) permite corregir
    cualquier estado.
    """
    if force and new_status == order.status:
        return order
    if not force and new_status not in TRANSITIONS.get(order.status, set()):
        raise ValidationError({"status": f"No se puede pasar de '{order.status}' a '{new_status}'."})
    order.status = new_status
    order.status_changed_at = timezone.now()
    order.save(update_fields=["status", "status_changed_at"])
    if new_status == Order.Status.DELIVERED:
        award_for_order(order)
    transaction.on_commit(lambda: publish_order(order.pk, push=True), robust=True)
    return order
