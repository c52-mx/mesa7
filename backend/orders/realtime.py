from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from accounts.models import DeviceToken

from .models import Order
from .payloads import jsonable, order_payload
from .push import notify_status


def order_group(order_id):
    return f"order.{order_id}"


def kds_group(tenant_id, branch_id):
    return f"kds.{tenant_id}.{branch_id}"


def publish_order(order_id, push=False):
    """Envía el pedido al seguimiento del cliente y al KDS de su sucursal (y push si cambió de estado)."""
    order = (
        Order.objects.select_related("customer")
        .prefetch_related("items")
        .get(pk=order_id)
    )
    send = async_to_sync(get_channel_layer().group_send)
    send(
        order_group(order.pk),
        {"type": "order.update", "order": jsonable(order_payload(order))},
    )
    send(
        kds_group(order.tenant_id, order.branch_id),
        {"type": "order.update", "order": jsonable(order_payload(order, kds=True))},
    )
    if push:
        tokens = list(DeviceToken.objects.filter(user=order.customer).values_list("token", flat=True))
        notify_status(order, tokens)
