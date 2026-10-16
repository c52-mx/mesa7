from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from menu.models import BranchProduct, Category, Product
from tenants.models import Branch, Membership, Tenant

from .models import Order

User = get_user_model()


class OrderTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name="Uno", slug="uno")
        cls.t2 = Tenant.objects.create(name="Dos", slug="dos")
        cls.branch = Branch.objects.create(tenant=cls.t1, name="Centro")
        cls.other_branch = Branch.objects.create(tenant=cls.t2, name="Ajena")
        cat = Category.objects.create(tenant=cls.t1, name="Bebidas")
        cls.latte = Product.objects.create(
            tenant=cls.t1, category=cat, name="Latte", price="55.00", prep_time_minutes=4
        )
        cls.cake = Product.objects.create(
            tenant=cls.t1, category=cat, name="Cheesecake", price="75.00", prep_time_minutes=2
        )
        BranchProduct.objects.create(
            tenant=cls.t1, branch=cls.branch, product=cls.cake, is_available=False
        )
        other_cat = Category.objects.create(tenant=cls.t2, name="X")
        cls.foreign = Product.objects.create(tenant=cls.t2, category=other_cat, name="Aj", price="1")
        cls.ana = User.objects.create_user("ana@x.com", password="x")
        cls.bob = User.objects.create_user("bob@x.com", password="x")
        cls.staff = User.objects.create_user("staff@x.com", password="x")
        Membership.objects.create(user=cls.ana, tenant=cls.t1)
        Membership.objects.create(user=cls.bob, tenant=cls.t1)
        Membership.objects.create(user=cls.staff, tenant=cls.t1, role="staff")

    def as_user(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def place(self, user, items=None, branch=None):
        return self.as_user(user).post(
            "/api/orders/",
            {
                "branch": (branch or self.branch).id,
                "items": items if items is not None else [{"product": self.latte.id, "quantity": 2}],
            },
            format="json",
        )

    def test_create_order_computes_total_and_snapshot(self):
        response = self.place(self.ana)
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["total"], "110.00")
        self.assertEqual(body["status"], "received")
        self.assertEqual(body["items"][0]["name"], "Latte")
        self.latte.price = "99"
        self.latte.save()
        self.assertEqual(Order.objects.get().items.get().unit_price, 55)

    def test_rejects_product_hidden_in_branch_or_other_tenant(self):
        for pid in (self.cake.id, self.foreign.id):
            response = self.place(self.ana, [{"product": pid, "quantity": 1}])
            self.assertEqual(response.status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_rejects_other_tenant_branch_and_bad_quantity(self):
        self.assertEqual(self.place(self.ana, branch=self.other_branch).status_code, 400)
        bad = self.place(self.ana, [{"product": self.latte.id, "quantity": 0}])
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(self.place(self.ana, items=[]).status_code, 400)

    def test_eta_grows_with_kitchen_backlog(self):
        first = self.place(self.ana).json()
        second = self.place(self.bob).json()
        gap = lambda o: Order.objects.get(pk=o["id"]).estimated_ready_at
        self.assertGreater(gap(second), gap(first))

    def test_customer_sees_only_own_orders(self):
        order_id = self.place(self.ana).json()["id"]
        self.assertEqual(len(self.as_user(self.ana).get("/api/orders/").json()), 1)
        self.assertEqual(self.as_user(self.bob).get("/api/orders/").json(), [])
        self.assertEqual(self.as_user(self.bob).get(f"/api/orders/{order_id}/").status_code, 404)

    def test_kds_requires_staff(self):
        response = self.as_user(self.ana).get(f"/api/kds/orders/?branch={self.branch.id}")
        self.assertEqual(response.status_code, 403)

    def test_kds_lists_active_orders_with_semaphore(self):
        order_id = self.place(self.ana).json()["id"]
        Order.objects.filter(pk=order_id).update(
            created_at=timezone.now() - timedelta(minutes=60)
        )
        data = self.as_user(self.staff).get(f"/api/kds/orders/?branch={self.branch.id}").json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["semaphore"], "red")
        self.assertEqual(data[0]["customer"], "ana@x.com")

    def test_kds_status_flow(self):
        order_id = self.place(self.ana).json()["id"]
        staff = self.as_user(self.staff)
        url = f"/api/kds/orders/{order_id}/status/"
        self.assertEqual(staff.post(url, {"status": "ready"}).status_code, 400)  # salta un paso
        for status in ("preparing", "ready", "delivered"):
            self.assertEqual(staff.post(url, {"status": status}).json()["status"], status)
        self.assertEqual(staff.post(url, {"status": "cancelled"}).status_code, 400)  # ya entregado
        listed = staff.get(f"/api/kds/orders/?branch={self.branch.id}").json()
        self.assertEqual(listed, [])

    def test_staff_of_other_tenant_cannot_touch_order(self):
        order_id = self.place(self.ana).json()["id"]
        outsider = User.objects.create_user("out@x.com", password="x")
        Membership.objects.create(user=outsider, tenant=self.t2, role="staff")
        response = self.as_user(outsider).post(
            f"/api/kds/orders/{order_id}/status/", {"status": "preparing"}
        )
        self.assertEqual(response.status_code, 404)
