from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import Order
from tenants.models import Branch, Membership, Tenant

from .models import Category, Option, OptionGroup, Product, ProductOptionGroup

User = get_user_model()


class OptionsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name="Uno", slug="uno")
        cls.other = Tenant.objects.create(name="Dos", slug="dos")
        cls.branch = Branch.objects.create(tenant=cls.tenant, name="Centro")
        cat = Category.objects.create(tenant=cls.tenant, name="Bebidas")
        cls.latte = Product.objects.create(tenant=cls.tenant, category=cat, name="Latte", price="55")
        cls.cake = Product.objects.create(tenant=cls.tenant, category=cat, name="Pastel", price="40")

        cls.size = OptionGroup.objects.create(tenant=cls.tenant, name="Tamaño", min_select=1, max_select=1)
        cls.chico = Option.objects.create(tenant=cls.tenant, group=cls.size, name="Chico", price_delta=0)
        cls.grande = Option.objects.create(tenant=cls.tenant, group=cls.size, name="Grande", price_delta=12)
        cls.extras = OptionGroup.objects.create(tenant=cls.tenant, name="Extras", min_select=0, max_select=2)
        cls.shot = Option.objects.create(tenant=cls.tenant, group=cls.extras, name="Shot", price_delta=14)
        cls.crema = Option.objects.create(tenant=cls.tenant, group=cls.extras, name="Crema", price_delta=10)
        cls.jarabe = Option.objects.create(tenant=cls.tenant, group=cls.extras, name="Jarabe", price_delta=14)
        cls.inactive = Option.objects.create(
            tenant=cls.tenant, group=cls.extras, name="Agotado", price_delta=5, is_active=False
        )
        for position, group in enumerate([cls.size, cls.extras]):
            ProductOptionGroup.objects.create(tenant=cls.tenant, product=cls.latte, group=group, position=position)

        cls.user = User.objects.create_user("ana@x.com", password="x")
        Membership.objects.create(user=cls.user, tenant=cls.tenant)

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def place(self, lines):
        return self.client.post("/api/orders/", {"branch": self.branch.id, "items": lines}, format="json")

    def line(self, options=(), quantity=1, notes="", product=None):
        return {"product": (product or self.latte).id, "quantity": quantity,
                "options": [o.id for o in options], "notes": notes}

    def test_menu_lists_groups_with_rules_and_hides_inactive_options(self):
        menu = self.client.get(f"/api/branches/{self.branch.id}/menu/").json()
        products = {p["name"]: p for c in menu["categories"] for p in c["products"]}
        groups = products["Latte"]["option_groups"]
        self.assertEqual([g["name"] for g in groups], ["Tamaño", "Extras"])
        self.assertEqual((groups[0]["required"], groups[0]["max_select"]), (1, 1))
        self.assertEqual(groups[1]["required"], 0)
        self.assertNotIn("Agotado", [o["name"] for o in groups[1]["options"]])
        self.assertEqual(products["Pastel"]["option_groups"], [])

    def test_price_includes_extras_and_snapshot_is_stored(self):
        response = self.place([self.line([self.grande, self.shot, self.crema], quantity=2, notes="sin canela")])
        self.assertEqual(response.status_code, 201)
        body = response.json()
        # (55 + 12 + 14 + 10) x 2
        self.assertEqual(body["total"], "182.00")
        item = body["items"][0]
        self.assertEqual(item["unit_price"], "91.00")
        self.assertEqual(item["notes"], "sin canela")
        self.assertEqual(
            [(o["group"], o["name"], o["price_delta"]) for o in item["options"]],
            [("Tamaño", "Grande", "12.00"), ("Extras", "Shot", "14.00"), ("Extras", "Crema", "10.00")],
        )
        # El menú puede cambiar después: el pedido conserva lo que se compró.
        self.grande.price_delta = 99
        self.grande.save()
        self.assertEqual(Order.objects.get().items.get().options[0]["price_delta"], "12.00")

    def test_same_product_with_different_options_is_separate_lines(self):
        response = self.place([self.line([self.chico]), self.line([self.grande])])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()["items"]), 2)
        self.assertEqual(response.json()["total"], "122.00")

    def test_required_group_must_be_chosen(self):
        self.assertEqual(self.place([self.line([])]).status_code, 400)
        self.assertEqual(self.place([self.line([self.shot])]).status_code, 400)  # falta Tamaño

    def test_max_select_is_enforced(self):
        too_many = self.place([self.line([self.chico, self.shot, self.crema, self.jarabe])])
        self.assertEqual(too_many.status_code, 400)
        two_sizes = self.place([self.line([self.chico, self.grande])])
        self.assertEqual(two_sizes.status_code, 400)

    def test_option_from_another_product_inactive_or_foreign_is_rejected(self):
        self.assertEqual(self.place([self.line([self.chico, self.inactive])]).status_code, 400)
        self.assertEqual(self.place([self.line([self.chico], product=self.cake)]).status_code, 400)
        self.assertEqual(self.place([self.line([self.chico, self.chico])]).status_code, 400)
        self.assertEqual(Order.objects.count(), 0)

    def test_product_without_groups_still_orders_without_options(self):
        response = self.place([self.line(product=self.cake, quantity=3)])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["total"], "120.00")

    def test_group_asking_more_than_available_does_not_block(self):
        # Mínimo 3 pero solo hay 2 opciones activas: se baja a 2 para poder pedir.
        group = OptionGroup.objects.create(tenant=self.tenant, name="Salsa", min_select=3, max_select=3)
        a = Option.objects.create(tenant=self.tenant, group=group, name="A")
        b = Option.objects.create(tenant=self.tenant, group=group, name="B")
        ProductOptionGroup.objects.create(tenant=self.tenant, product=self.cake, group=group)
        self.assertEqual(self.place([self.line([a, b], product=self.cake)]).status_code, 201)

    def test_group_max_cannot_be_below_min(self):
        from django.core.exceptions import ValidationError

        with self.assertRaises(ValidationError):
            OptionGroup(tenant=self.tenant, name="X", min_select=2, max_select=1).full_clean()


class OptionAdminTests(TestCase):
    def test_staff_creates_group_with_inline_options_in_own_tenant(self):
        tenant = Tenant.objects.create(name="Uno", slug="uno")
        staff = User.objects.create_user("staff@x.com", password="x", is_staff=True)
        Membership.objects.create(user=staff, tenant=tenant, role="owner")
        staff.user_permissions.set(
            Permission.objects.filter(codename__in=[
                "add_optiongroup", "change_optiongroup", "view_optiongroup",
                "add_option", "change_option", "view_option", "delete_option",
            ])
        )
        self.client.force_login(staff)
        response = self.client.post(
            "/admin/menu/optiongroup/add/",
            {
                "name": "Tipo de leche", "min_select": "1", "max_select": "1",
                "options-TOTAL_FORMS": "2", "options-INITIAL_FORMS": "0",
                "options-MIN_NUM_FORMS": "0", "options-MAX_NUM_FORMS": "1000",
                "options-0-name": "Entera", "options-0-price_delta": "0", "options-0-position": "0",
                "options-0-is_active": "on",
                "options-1-name": "Avena", "options-1-price_delta": "17", "options-1-position": "1",
                "options-1-is_active": "on",
            },
        )
        self.assertEqual(response.status_code, 302, getattr(response, "content", b"")[:300])
        group = OptionGroup.objects.get(name="Tipo de leche")
        self.assertEqual(group.tenant, tenant)
        self.assertEqual(sorted(Option.objects.values_list("name", "tenant_id")), [("Avena", tenant.id), ("Entera", tenant.id)])
