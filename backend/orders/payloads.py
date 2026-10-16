import json

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

from .models import Order


def semaphore(order, now):
    """Verde mientras no pase el tiempo estimado; amarillo hasta +50 %; rojo después."""
    if order.status not in Order.IN_KITCHEN:
        return "green"
    ratio = (now - order.created_at).total_seconds() / 60 / max(order.prep_minutes, 1)
    return "green" if ratio <= 1 else "yellow" if ratio <= 1.5 else "red"


def order_payload(order, kds=False):
    now = timezone.now()
    data = {
        "id": order.pk,
        "status": order.status,
        "branch": order.branch_id,
        "total": str(order.total),
        "notes": order.notes,
        "created_at": order.created_at,
        "status_changed_at": order.status_changed_at,
        "estimated_ready_at": order.estimated_ready_at,
        "items": [
            {"product": i.product_id, "name": i.name, "quantity": i.quantity, "unit_price": str(i.unit_price)}
            for i in order.items.all()
        ],
    }
    if kds:
        data["customer"] = order.customer.full_name or order.customer.email
        data["elapsed_seconds"] = int((now - order.created_at).total_seconds())
        data["prep_minutes"] = order.prep_minutes
        data["semaphore"] = semaphore(order, now)
    return data


def jsonable(data):
    """Los mensajes del channel layer deben ser serializables (fechas -> texto)."""
    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))
