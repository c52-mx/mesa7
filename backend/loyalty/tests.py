from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from menu.models import Category, Product
from orders.services import change_status, create_order
from promos.models import Banner
from tenants.models import Branch, Membership, Tenant

from .models import LoyaltyAccount, LoyaltyProgram, LoyaltyReward, LoyaltyTransaction

User = get_user_model()


class LoyaltyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name="Uno", slug="uno")
        cls.other = Tenant.objects.create(name="Dos", slug="dos")
        cls.branch = Branch.objects.create(tenant=cls.tenant, name="Centro")
        cat = Category.objects.create(tenant=cls.tenant, name="Bebidas")
        cls.latte = Product.objects.create(tenant=cls.tenant, category=cat, name="Latte", price="55")
        cls.ana = User.objects.create_user("ana@x.com", password="x", full_name="Ana Pérez")
        cls.bob = User.objects.create_user("bob@x.com", password="x")
        Membership.objects.create(user=cls.ana, tenant=cls.tenant)
        Membership.objects.create(user=cls.bob, tenant=cls.other)
        LoyaltyProgram.objects.create(tenant=cls.tenant, spend_per_point=10)
        for points, name in [(5, "Galleta"), (20, "Bebida")]:
            LoyaltyReward.objects.create(tenant=cls.tenant, points_required=points, name=name)

    def client_for(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def deliver(self, quantity=2):
        order = create_order(
            tenant=self.tenant,
            branch=self.branch,
            customer=self.ana,
            items=[{"product": self.latte.id, "quantity": quantity}],
        )
        for status in ("preparing", "ready", "delivered"):
            change_status(order, status)
        return order

    def test_points_are_earned_when_order_is_delivered(self):
        order = self.deliver(quantity=2)  # $110 -> 11 puntos
        earned = LoyaltyTransaction.objects.get()
        self.assertEqual((earned.points, earned.kind, earned.order_id), (11, "earn", order.pk))

    def test_no_points_before_delivery(self):
        order = create_order(
            tenant=self.tenant, branch=self.branch, customer=self.ana,
            items=[{"product": self.latte.id, "quantity": 2}],
        )
        change_status(order, "preparing")
        self.assertEqual(LoyaltyTransaction.objects.count(), 0)

    def test_disabled_loyalty_earns_nothing_and_endpoint_is_404(self):
        self.tenant.loyalty_enabled = False
        self.tenant.save()
        self.deliver()
        self.assertEqual(LoyaltyTransaction.objects.count(), 0)
        self.assertEqual(self.client_for(self.ana).get("/api/loyalty/").status_code, 404)

    def test_summary_progress_and_qr(self):
        self.deliver(quantity=2)  # 11 puntos: desbloquea 5, falta para 20
        data = self.client_for(self.ana).get("/api/loyalty/").json()
        self.assertEqual(data["points"], 11)
        self.assertEqual([r["unlocked"] for r in data["rewards"]], [True, False])
        self.assertEqual(data["next_reward"]["name"], "Bebida")
        self.assertEqual(data["next_reward"]["missing"], 9)
        self.assertEqual(data["qr"], f"mesa7:uno:{data['member_code']}")
        self.assertEqual(len(data["member_code"]), 12)
        self.assertEqual(data["name"], "Ana Pérez")
        self.assertEqual(len(data["recent"]), 1)

    def test_account_is_created_once_per_user(self):
        client = self.client_for(self.ana)
        first = client.get("/api/loyalty/").json()["member_code"]
        second = client.get("/api/loyalty/").json()["member_code"]
        self.assertEqual(first, second)
        self.assertEqual(LoyaltyAccount.objects.count(), 1)

    def test_manual_adjustment_counts_in_balance(self):
        account = LoyaltyAccount.objects.create(tenant=self.tenant, user=self.ana, member_code="000000000001")
        LoyaltyTransaction.objects.create(tenant=self.tenant, account=account, points=30, kind="adjust", note="Cortesía")
        self.assertEqual(self.client_for(self.ana).get("/api/loyalty/").json()["points"], 30)

    def test_other_tenant_user_has_no_program(self):
        self.assertEqual(self.client_for(self.bob).get("/api/loyalty/").status_code, 404)


class PromosAndProfileTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name="Uno", slug="uno")
        cls.t2 = Tenant.objects.create(name="Dos", slug="dos")
        Banner.objects.create(tenant=cls.t1, title="B", position=2)
        Banner.objects.create(tenant=cls.t1, title="A", position=1)
        Banner.objects.create(tenant=cls.t1, title="Oculto", is_active=False)
        Banner.objects.create(tenant=cls.t2, title="Ajeno")
        cls.user = User.objects.create_user("ana@x.com", password="x")
        Membership.objects.create(user=cls.user, tenant=cls.t1)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_banners_are_active_ordered_and_scoped(self):
        titles = [b["title"] for b in self.client.get("/api/banners/").json()]
        self.assertEqual(titles, ["A", "B"])

    def test_me_get_and_patch(self):
        self.assertEqual(self.client.get("/api/me/").json()["email"], "ana@x.com")
        response = self.client.patch("/api/me/", {"full_name": " Ana  ", "phone": "555"}, format="json")
        self.assertEqual(response.json()["full_name"], "Ana")
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "555")

    def test_branding_exposes_loyalty_flag(self):
        self.assertTrue(self.client.get("/api/tenants/uno/").json()["loyalty_enabled"])
