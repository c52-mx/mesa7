import asyncio

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from rest_framework_simplejwt.authentication import JWTAuthentication

from tenants.api import membership_for
from tenants.models import Branch, Membership

from .models import Order
from .realtime import kds_group, order_group

CLOSE_UNAUTHENTICATED = 4401
CLOSE_FORBIDDEN = 4403
AUTH_TIMEOUT_SECONDS = 10


class AuthenticatedConsumer(AsyncJsonWebsocketConsumer):
    """Handshake por mensaje: {"type": "auth", "token": <JWT>, "tenant": <slug, opcional>}.

    El token va en el primer mensaje y no en la URL, para que no quede en logs de acceso.
    Tras autenticar y autorizar, el socket se suscribe a un solo grupo y recibe eventos.
    """

    group = None
    deadline = None

    async def connect(self):
        await self.accept()
        self.deadline = asyncio.create_task(self._close_if_unauthenticated())

    async def _close_if_unauthenticated(self):
        await asyncio.sleep(AUTH_TIMEOUT_SECONDS)
        if self.group is None:
            await self.close(code=CLOSE_UNAUTHENTICATED)

    async def disconnect(self, code):
        if self.deadline:
            self.deadline.cancel()
        if self.group:
            await self.channel_layer.group_discard(self.group, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if self.group is not None:
            return
        user = await self._authenticate(content)
        if user is None:
            return await self.close(code=CLOSE_UNAUTHENTICATED)
        group = await self._authorize(user, content.get("tenant"))
        if group is None:
            return await self.close(code=CLOSE_FORBIDDEN)
        self.group = group
        await self.channel_layer.group_add(group, self.channel_name)
        await self.send_json({"type": "ready"})

    @database_sync_to_async
    def _authenticate(self, content):
        if content.get("type") != "auth" or not isinstance(content.get("token"), str):
            return None
        auth = JWTAuthentication()
        try:
            return auth.get_user(auth.get_validated_token(content["token"]))
        except Exception:
            return None

    @database_sync_to_async
    def _authorize(self, user, tenant_slug):
        try:
            membership = membership_for(user, tenant_slug)
        except Exception:
            return None
        return self.group_for(user, membership)

    def group_for(self, user, membership):
        raise NotImplementedError

    async def order_update(self, event):
        await self.send_json({"type": "order.update", "order": event["order"]})


class OrderConsumer(AuthenticatedConsumer):
    """Seguimiento en vivo de un pedido, solo para su dueño."""

    def group_for(self, user, membership):
        order_id = self.scope["url_route"]["kwargs"]["order_id"]
        exists = Order.objects.for_tenant(membership.tenant).filter(pk=order_id, customer=user).exists()
        return order_group(order_id) if exists else None


class KdsConsumer(AuthenticatedConsumer):
    """Pedidos de una sucursal en vivo, solo para el personal del negocio."""

    def group_for(self, user, membership):
        if membership.role not in (Membership.Role.OWNER, Membership.Role.STAFF):
            return None
        branch_id = self.scope["url_route"]["kwargs"]["branch_id"]
        if not Branch.objects.for_tenant(membership.tenant).filter(pk=branch_id).exists():
            return None
        return kds_group(membership.tenant_id, branch_id)
