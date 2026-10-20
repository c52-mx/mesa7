import math
from datetime import timedelta

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from loyalty.services import award_for_order
from menu.models import BranchProduct, Product

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


@transaction.atomic
def create_order(*, tenant, branch, customer, items, notes=""):
    """items: lista de {"product": id, "quantity": n}."""
    quantities = {}
    for item in items:
        quantities[item["product"]] = quantities.get(item["product"], 0) + item["quantity"]

    products = {
        p.pk: p
        for p in Product.objects.for_tenant(tenant).filter(pk__in=quantities, is_active=True)
    }
    hidden = set(
        BranchProduct.objects.for_tenant(tenant)
        .filter(branch=branch, is_available=False, product_id__in=quantities)
        .values_list("product_id", flat=True)
    )
    missing = [pk for pk in quantities if pk not in products or pk in hidden]
    if missing:
        raise ValidationError({"items": f"Productos no disponibles en esta sucursal: {sorted(missing)}"})

    lines = [(products[pk], qty) for pk, qty in quantities.items()]
    prep = own_prep_minutes(lines)
    eta = kitchen_backlog_minutes(tenant, branch) + prep
    order = Order.objects.create(
        tenant=tenant,
        branch=branch,
        customer=customer,
        notes=notes,
        total=sum(p.price * qty for p, qty in lines),
        prep_minutes=prep,
        estimated_ready_at=timezone.now() + timedelta(minutes=eta),
    )
    OrderItem.objects.bulk_create(
        [
            OrderItem(
                tenant=tenant, order=order, product=p, name=p.name, unit_price=p.price, quantity=qty
            )
            for p, qty in lines
        ]
    )
    # lambda y no partial: con robust=True Django lee func.__qualname__ al registrar el error.
    transaction.on_commit(lambda: publish_order(order.pk), robust=True)
    return order


def change_status(order, new_status):
    if new_status not in TRANSITIONS.get(order.status, set()):
        raise ValidationError({"status": f"No se puede pasar de '{order.status}' a '{new_status}'."})
    order.status = new_status
    order.status_changed_at = timezone.now()
    order.save(update_fields=["status", "status_changed_at"])
    if new_status == Order.Status.DELIVERED:
        award_for_order(order)
    transaction.on_commit(lambda: publish_order(order.pk, push=True), robust=True)
    return order
