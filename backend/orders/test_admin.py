from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

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
                "payment_status": "pending",
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
    def test_mark_paid_action(self):
        response = self.client.post(
            "/admin/orders/order/", {"action": "mark_paid", "_selected_action": [str(self.order.pk)]}
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.get().payment_status, "paid")

    def test_payment_status_can_be_corrected_from_the_form(self):
        item = self.order.items.get()
        self.client.post(
            f"/admin/orders/order/{self.order.pk}/change/",
            {
                "status": "received", "payment_status": "paid",
                "items-TOTAL_FORMS": "1", "items-INITIAL_FORMS": "1",
                "items-MIN_NUM_FORMS": "0", "items-MAX_NUM_FORMS": "1000",
                "items-0-id": str(item.pk), "items-0-order": str(self.order.pk),
            },
        )
        self.assertEqual(Order.objects.get().payment_status, "paid")


class PaymentMethodTests(TestCase):
    def setUp(self):
        make_world(self)
        self.client = APIClient()
        self.client.force_authenticate(self.ana)

    def place(self, **extra):
        body = {"branch": self.branch.id, "items": [{"product": self.latte.id, "quantity": 1}], **extra}
        return self.client.post("/api/orders/", body, format="json")

    def test_defaults_to_counter_and_pending(self):
        body = self.place().json()
        self.assertEqual((body["payment_method"], body["payment_status"]), ("counter", "pending"))

    def test_counter_is_accepted_explicitly(self):
        self.assertEqual(self.place(payment_method="counter").status_code, 201)

    def test_online_payment_is_not_available_yet(self):
        response = self.place(payment_method="online")
        self.assertEqual(response.status_code, 400)
        self.assertIn("payment_method", response.json())
        self.assertEqual(Order.objects.count(), 0)

    def test_unknown_method_is_rejected(self):
        self.assertEqual(self.place(payment_method="bitcoin").status_code, 400)
