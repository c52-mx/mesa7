from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import Order
from orders.services import create_order
from tenants.models import Membership, Tenant

from .models import LoyaltyAccount, LoyaltyProgram, LoyaltyReward, LoyaltyTransaction
from .services import balance, get_or_create_account

User = get_user_model()


class StaffLoyaltyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name="Uno", slug="uno")
        cls.other = Tenant.objects.create(name="Dos", slug="dos")
        LoyaltyProgram.objects.create(tenant=cls.tenant, spend_per_point=10)
        cls.cafe = LoyaltyReward.objects.create(tenant=cls.tenant, points_required=5, name="Café")
        cls.postre = LoyaltyReward.objects.create(tenant=cls.tenant, points_required=20, name="Postre")
        cls.foreign_reward = LoyaltyReward.objects.create(tenant=cls.other, points_required=1, name="Ajeno")
        cls.customer = User.objects.create_user("ana@x.com", password="x", full_name="Ana Pérez")
        cls.staff = User.objects.create_user("caja@x.com", password="x")
        cls.visitor = User.objects.create_user("vis@x.com", password="x")
        Membership.objects.create(user=cls.customer, tenant=cls.tenant)
        Membership.objects.create(user=cls.staff, tenant=cls.tenant, role="staff")
        Membership.objects.create(user=cls.visitor, tenant=cls.other, role="customer")
        cls.account = get_or_create_account(cls.tenant, cls.customer)
        LoyaltyTransaction.objects.create(tenant=cls.tenant, account=cls.account, points=12, kind="adjust")

    def as_user(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def lookup(self, code, user=None):
        return self.as_user(user or self.staff).get("/api/staff/loyalty/lookup/", {"code": code})

    def test_lookup_by_code_with_spaces_or_qr_text(self):
        code = self.account.member_code
        spaced = f"{code[:4]} {code[4:8]} {code[8:]}"
        for raw in (code, spaced, f"mesa7:uno:{code}"):
            data = self.lookup(raw).json()
            self.assertEqual((data["customer"], data["points"]), ("Ana Pérez", 12))
        self.assertEqual([r["unlocked"] for r in data["rewards"]], [True, False])

    def test_unknown_code_and_other_tenant_qr(self):
        self.assertEqual(self.lookup("000000000000").status_code, 404)
        self.assertEqual(self.lookup(f"mesa7:dos:{self.account.member_code}").status_code, 400)
        self.assertEqual(self.lookup("mesa7:malformado").status_code, 400)

    def test_customers_and_other_tenants_cannot_use_the_cash_register(self):
        self.assertEqual(self.lookup(self.account.member_code, self.customer).status_code, 403)
        self.assertEqual(self.lookup(self.account.member_code, self.visitor).status_code, 403)
        self.assertEqual(self.as_user(self.staff).get("/api/staff/loyalty/lookup/").status_code, 400)

    def test_redeem_discounts_points_and_records_who_did_it(self):
        response = self.as_user(self.staff).post(
            "/api/staff/loyalty/redeem/", {"code": self.account.member_code, "reward": self.cafe.pk}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["points"], 7)
        movement = LoyaltyTransaction.objects.get(kind="redeem")
        self.assertEqual((movement.points, movement.staff, movement.note), (-5, self.staff, "Canje: Café"))

    def test_redeem_rejects_insufficient_points_and_foreign_or_inactive_rewards(self):
        client = self.as_user(self.staff)
        code = self.account.member_code
        for reward in (self.postre.pk, self.foreign_reward.pk, 99999):
            response = client.post("/api/staff/loyalty/redeem/", {"code": code, "reward": reward}, format="json")
            self.assertEqual(response.status_code, 400)
        self.cafe.is_active = False
        self.cafe.save()
        self.assertEqual(
            client.post("/api/staff/loyalty/redeem/", {"code": code, "reward": self.cafe.pk}, format="json").status_code,
            400,
        )
        self.assertEqual(balance(self.account), 12)

    def test_cannot_redeem_twice_with_only_enough_points_for_one(self):
        client = self.as_user(self.staff)
        body = {"code": self.account.member_code, "reward": self.cafe.pk}
        client.post("/api/staff/loyalty/redeem/", body, format="json")
        client.post("/api/staff/loyalty/redeem/", body, format="json")  # 12 -> 7 -> 2
        self.assertEqual(balance(self.account), 2)
        self.assertEqual(client.post("/api/staff/loyalty/redeem/", body, format="json").status_code, 400)
        self.assertEqual(balance(self.account), 2)

    def test_counter_purchase_earns_points_like_orders(self):
        response = self.as_user(self.staff).post(
            "/api/staff/loyalty/earn/", {"code": self.account.member_code, "amount": "125.50"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["points"], 12 + 12)  # 125.50 // 10 = 12
        earned = LoyaltyTransaction.objects.get(note__startswith="Compra en mostrador")
        self.assertEqual((earned.points, earned.kind, earned.staff), (12, "earn", self.staff))
        self.assertIn("125.50", earned.note)

    def test_counter_purchase_validates_the_amount(self):
        client = self.as_user(self.staff)
        for amount in ("0", "-5", "abc", "5", "NaN", "Infinity", "1000000", ""):
            response = client.post(
                "/api/staff/loyalty/earn/", {"code": self.account.member_code, "amount": amount}, format="json"
            )
            self.assertEqual(response.status_code, 400, amount)
        self.assertEqual(balance(self.account), 12)

    def test_disabled_loyalty_blocks_the_cash_register(self):
        self.tenant.loyalty_enabled = False
        self.tenant.save()
        self.assertEqual(self.lookup(self.account.member_code).status_code, 404)

    def test_cash_register_requires_login(self):
        self.assertEqual(APIClient().get("/api/staff/loyalty/lookup/", {"code": "1"}).status_code, 401)


class KdsPaymentTests(TestCase):
    def setUp(self):
        from orders.test_realtime import make_world

        make_world(self)
        self.order = create_order(
            tenant=self.tenant, branch=self.branch, customer=self.ana,
            items=[{"product": self.latte.id, "quantity": 1}],
        )

    def post(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client.post(f"/api/kds/orders/{self.order.pk}/paid/")

    def test_staff_marks_paid_and_it_is_idempotent(self):
        for _ in range(2):
            response = self.post(self.staff)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["payment_status"], "paid")
        self.assertEqual(Order.objects.get().payment_status, "paid")

    def test_customer_cannot_mark_paid(self):
        self.assertEqual(self.post(self.ana).status_code, 403)
        self.assertEqual(Order.objects.get().payment_status, "pending")


class SeedCafecinTests(TestCase):
    def test_cafecin_is_loaded_with_branch_data_and_is_idempotent(self):
        from menu.models import Product
        from tenants.models import Branch

        call_command("seed_cafecin")
        call_command("seed_cafecin")
        tenant = Tenant.objects.get(slug="cafecin")
        branch = Branch.objects.get(tenant=tenant)
        self.assertEqual(branch.phone, "55 5049 9486")
        self.assertIn("Ojo de Agua", branch.address)
        self.assertEqual(Product.objects.for_tenant(tenant).count(), 23)
        self.assertEqual(Product.objects.for_tenant(tenant).filter(is_featured=True).count(), 4)
        self.assertEqual(LoyaltyReward.objects.for_tenant(tenant).count(), 4)

    def test_demo_and_cafecin_do_not_mix(self):
        from menu.models import Product

        call_command("seed_demo")
        call_command("seed_cafecin")
        self.assertEqual(Product.objects.for_tenant(Tenant.objects.get(slug="demo")).count(), 14)

    def test_reset_demo_clears_orders_and_points_only_for_that_tenant(self):
        from orders.test_realtime import make_world

        call_command("seed_cafecin")
        make_world(self)  # otro negocio ("uno") con su propia cuenta de lealtad
        LoyaltyProgram.objects.create(tenant=self.tenant, spend_per_point=10)
        mine = get_or_create_account(self.tenant, self.ana)
        LoyaltyTransaction.objects.create(tenant=self.tenant, account=mine, points=5, kind="adjust")
        cafecin = Tenant.objects.get(slug="cafecin")
        other = get_or_create_account(cafecin, self.bob)
        LoyaltyTransaction.objects.create(tenant=cafecin, account=other, points=9, kind="adjust")

        from django.core.management.base import CommandError

        with self.assertRaises(CommandError):
            call_command("reset_demo", tenant="cafecin")  # sin --yes no borra
        self.assertEqual(LoyaltyTransaction.objects.count(), 2)
        call_command("reset_demo", tenant="cafecin", yes=True)
        self.assertEqual(LoyaltyAccount.objects.for_tenant(cafecin).count(), 0)
        self.assertEqual(LoyaltyTransaction.objects.for_tenant(self.tenant).count(), 1)
        self.assertTrue(User.objects.filter(email="bob@x.com").exists())
