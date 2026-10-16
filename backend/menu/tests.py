from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Branch, Membership, Tenant

from .models import BranchProduct, Category, Product


class MenuTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.t1 = Tenant.objects.create(name="Café Uno", slug="uno")
        cls.t2 = Tenant.objects.create(name="Café Dos", slug="dos")
        cls.user = User.objects.create_user("ana@x.com", password="x")
        Membership.objects.create(user=cls.user, tenant=cls.t1)
        cls.b1 = Branch.objects.create(tenant=cls.t1, name="Centro")
        cls.b2 = Branch.objects.create(tenant=cls.t1, name="Norte")
        cls.other_branch = Branch.objects.create(tenant=cls.t2, name="Ajena")
        cat = Category.objects.create(tenant=cls.t1, name="Bebidas")
        cls.latte = Product.objects.create(tenant=cls.t1, category=cat, name="Latte", price="55")
        cls.mocha = Product.objects.create(tenant=cls.t1, category=cat, name="Moka", price="60")
        other_cat = Category.objects.create(tenant=cls.t2, name="Otras")
        Product.objects.create(tenant=cls.t2, category=other_cat, name="Ajeno", price="1")
        BranchProduct.objects.create(
            tenant=cls.t1, branch=cls.b2, product=cls.mocha, is_available=False
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def names(self, branch):
        data = self.client.get(f"/api/branches/{branch.id}/menu/").json()
        return [p["name"] for c in data["categories"] for p in c["products"]]

    def test_requires_auth(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/branches/").status_code, 401)

    def test_branches_only_own_tenant(self):
        names = [b["name"] for b in self.client.get("/api/branches/").json()]
        self.assertEqual(sorted(names), ["Centro", "Norte"])

    def test_menu_filters_by_branch_availability(self):
        self.assertEqual(sorted(self.names(self.b1)), ["Latte", "Moka"])
        self.assertEqual(self.names(self.b2), ["Latte"])

    def test_other_tenant_branch_is_404(self):
        response = self.client.get(f"/api/branches/{self.other_branch.id}/menu/")
        self.assertEqual(response.status_code, 404)

    def test_cross_tenant_reference_rejected(self):
        foreign_cat = Category.objects.create(tenant=self.t2, name="X")
        with self.assertRaises(ValidationError):
            Product.objects.create(tenant=self.t1, category=foreign_cat, name="Mal", price="1")
