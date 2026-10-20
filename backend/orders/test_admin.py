from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase

from loyalty.models import LoyaltyProgram, LoyaltyTransaction

from .models import Order
from .services import create_order
from .test_realtime import make_world

User = get_user_model()


class AdminStatusTests(TestCase):
    def setUp(self):
        make_world(self)
        LoyaltyProgram.objects.create(tenant=self.tenant, spend_per_point=10)
        self.order = create_order(
            tenant=self.tenant,
            branch=self.branch,
            customer=self.ana,
            items=[{"product": self.latte.id, "quantity": 2}],  # $110 -> 11 puntos
        )
        self.admin = User.objects.create_superuser("root@x.com", "x")
        self.client.force_login(self.admin)

    def change_form(self, status):
        item = self.order.items.get()
        return self.client.post(
            f"/admin/orders/order/{self.order.pk}/change/",
            {
                "status": status,
                "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
                "items-0-id": str(item.pk), "items-0-order": str(self.order.pk),
            },
        )

    def test_changing_status_in_admin_notifies_the_customer(self):
        with mock.patch("orders.services.publish_order") as publish, self.captureOnCommitCallbacks(execute=True):
            response = self.change_form("preparing")
        self.assertEqual(response.status_code, 302)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "preparing")
        publish.assert_called_once_with(self.order.pk, push=True)

    def test_delivering_from_admin_awards_loyalty_points(self):
        with mock.patch("orders.services.publish_order"), self.captureOnCommitCallbacks(execute=True):
            self.change_form("delivered")  # el admin permite saltar pasos
        self.assertEqual(LoyaltyTransaction.objects.get().points, 11)

    def test_saving_without_changing_status_does_not_notify(self):
        with mock.patch("orders.services.publish_order") as publish, self.captureOnCommitCallbacks(execute=True):
            self.change_form("received")
        publish.assert_not_called()

    def test_bulk_action_marks_orders_and_notifies(self):
        with mock.patch("orders.services.publish_order") as publish, self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(
                "/admin/orders/order/",
                {"action": "mark_ready", "_selected_action": [str(self.order.pk)]},
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.get().status, "ready")
        publish.assert_called_once_with(self.order.pk, push=True)
