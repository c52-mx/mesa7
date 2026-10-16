from types import SimpleNamespace
from unittest import mock

from channels.db import database_sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from menu.models import Category, Product
from tenants.models import Branch, Membership, Tenant

from .consumers import CLOSE_FORBIDDEN, CLOSE_UNAUTHENTICATED
from .routing import websocket_urlpatterns
from .services import change_status, create_order

User = get_user_model()
IN_MEMORY = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
app = URLRouter(websocket_urlpatterns)


def make_world(case):
    case.tenant = Tenant.objects.create(name="Uno", slug="uno")
    case.branch = Branch.objects.create(tenant=case.tenant, name="Centro")
    cat = Category.objects.create(tenant=case.tenant, name="Bebidas")
    case.latte = Product.objects.create(tenant=case.tenant, category=cat, name="Latte", price="55")
    case.ana = User.objects.create_user("ana@x.com", password="x")
    case.bob = User.objects.create_user("bob@x.com", password="x")
    case.staff = User.objects.create_user("staff@x.com", password="x")
    Membership.objects.create(user=case.ana, tenant=case.tenant)
    Membership.objects.create(user=case.bob, tenant=case.tenant)
    Membership.objects.create(user=case.staff, tenant=case.tenant, role="staff")


def token(user):
    return str(RefreshToken.for_user(user).access_token)


@override_settings(CHANNEL_LAYERS=IN_MEMORY)
class WebSocketTests(TransactionTestCase):
    def setUp(self):
        make_world(self)

    async def place(self, user=None):
        return await database_sync_to_async(create_order)(
            tenant=self.tenant,
            branch=self.branch,
            customer=user or self.ana,
            items=[{"product": self.latte.id, "quantity": 1}],
        )

    async def connect(self, path, user, tenant=None):
        comm = WebsocketCommunicator(app, path)
        connected, _ = await comm.connect()
        self.assertTrue(connected)
        await comm.send_json_to({"type": "auth", "token": token(user), "tenant": tenant})
        return comm

    async def test_customer_follows_own_order(self):
        order = await self.place()
        comm = await self.connect(f"/ws/orders/{order.pk}/", self.ana)
        self.assertEqual(await comm.receive_json_from(), {"type": "ready"})
        await database_sync_to_async(change_status)(order, "preparing")
        event = await comm.receive_json_from()
        self.assertEqual(event["type"], "order.update")
        self.assertEqual(event["order"]["status"], "preparing")
        await comm.disconnect()

    async def test_kds_receives_new_and_updated_orders(self):
        comm = await self.connect(f"/ws/kds/{self.branch.pk}/", self.staff)
        self.assertEqual(await comm.receive_json_from(), {"type": "ready"})
        order = await self.place()
        created = await comm.receive_json_from()
        self.assertEqual(created["order"]["id"], order.pk)
        self.assertIn("semaphore", created["order"])
        await database_sync_to_async(change_status)(order, "preparing")
        self.assertEqual((await comm.receive_json_from())["order"]["status"], "preparing")
        await comm.disconnect()

    async def test_other_customer_cannot_follow_order(self):
        order = await self.place()
        comm = await self.connect(f"/ws/orders/{order.pk}/", self.bob)
        output = await comm.receive_output()
        self.assertEqual(output["type"], "websocket.close")
        self.assertEqual(output["code"], CLOSE_FORBIDDEN)

    async def test_customer_cannot_open_kds(self):
        comm = await self.connect(f"/ws/kds/{self.branch.pk}/", self.ana)
        self.assertEqual((await comm.receive_output())["code"], CLOSE_FORBIDDEN)

    async def test_invalid_token_is_closed(self):
        comm = WebsocketCommunicator(app, f"/ws/kds/{self.branch.pk}/")
        await comm.connect()
        await comm.send_json_to({"type": "auth", "token": "basura"})
        self.assertEqual((await comm.receive_output())["code"], CLOSE_UNAUTHENTICATED)


class PublishFailureTests(TransactionTestCase):
    def setUp(self):
        make_world(self)

    def test_failed_publish_does_not_break_status_change(self):
        with mock.patch("orders.services.publish_order", side_effect=RuntimeError("redis caído")):
            order = create_order(
                tenant=self.tenant,
                branch=self.branch,
                customer=self.ana,
                items=[{"product": self.latte.id, "quantity": 1}],
            )
            change_status(order, "preparing")
        order.refresh_from_db()
        self.assertEqual(order.status, "preparing")


@override_settings(CHANNEL_LAYERS=IN_MEMORY)
class PushTests(TestCase):
    def setUp(self):
        make_world(self)
        self.client = APIClient()
        self.client.force_authenticate(self.ana)

    def test_status_change_sends_push_to_registered_devices(self):
        response = self.client.post(
            "/api/devices/", {"token": "ExponentPushToken[abc]", "platform": "ios"}
        )
        self.assertEqual(response.status_code, 204)
        order = create_order(
            tenant=self.tenant,
            branch=self.branch,
            customer=self.ana,
            items=[{"product": self.latte.id, "quantity": 1}],
        )
        sent = []
        inline = lambda target, args=(), daemon=None: SimpleNamespace(start=lambda: target(*args))
        with mock.patch("orders.push._post", sent.append), mock.patch(
            "orders.push.threading", SimpleNamespace(Thread=inline)
        ), self.captureOnCommitCallbacks(execute=True):
            change_status(order, "preparing")
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0][0]["to"], "ExponentPushToken[abc]")
        self.assertIn("en preparación", sent[0][0]["body"])

    def test_device_token_moves_to_current_account_and_can_be_removed(self):
        self.client.post("/api/devices/", {"token": "T1"})
        other = APIClient()
        other.force_authenticate(self.bob)
        other.post("/api/devices/", {"token": "T1"})
        self.assertEqual(self.bob.device_tokens.count(), 1)
        self.assertEqual(self.ana.device_tokens.count(), 0)
        other.delete("/api/devices/", {"token": "T1"})
        self.assertEqual(self.bob.device_tokens.count(), 0)
