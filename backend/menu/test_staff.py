from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from promos.models import Banner
from tenants.models import Branch, Membership, Tenant

from .models import BranchProduct, Category, Product

User = get_user_model()


class StaffCatalogTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tenant = Tenant.objects.create(name="Uno", slug="uno")
        cls.other = Tenant.objects.create(name="Dos", slug="dos")
        cls.branch = Branch.objects.create(tenant=cls.tenant, name="Centro")
        cls.foreign_branch = Branch.objects.create(tenant=cls.other, name="Ajena")
        cat = Category.objects.create(tenant=cls.tenant, name="Bebidas")
        cls.latte = Product.objects.create(tenant=cls.tenant, category=cat, name="Latte", price="55")
        foreign_cat = Category.objects.create(tenant=cls.other, name="Otras")
        cls.foreign_product = Product.objects.create(tenant=cls.other, category=foreign_cat, name="Ajeno", price="1")
        cls.banner = Banner.objects.create(tenant=cls.tenant, title="2x1")
        cls.foreign_banner = Banner.objects.create(tenant=cls.other, title="Ajeno")
        cls.owner = User.objects.create_user("dueno@x.com", password="x")
        cls.staff = User.objects.create_user("caja@x.com", password="x")
        cls.customer = User.objects.create_user("ana@x.com", password="x")
        Membership.objects.create(user=cls.owner, tenant=cls.tenant, role="owner")
        Membership.objects.create(user=cls.staff, tenant=cls.tenant, role="staff")
        Membership.objects.create(user=cls.customer, tenant=cls.tenant)

    def as_user(self, user):
        client = APIClient()
        client.force_authenticate(user)
        return client

    def set_availability(self, user, product, available, branch=None):
        return self.as_user(user).post(
            "/api/staff/availability/set/",
            {"branch": (branch or self.branch).pk, "product": product.pk, "is_available": available},
            format="json",
        )

    def test_staff_marks_product_unavailable_and_back(self):
        self.assertEqual(self.set_availability(self.staff, self.latte, False).status_code, 200)
        menu = self.as_user(self.customer).get(f"/api/branches/{self.branch.pk}/menu/").json()
        self.assertEqual(menu["categories"], [])
        listed = self.as_user(self.staff).get("/api/staff/availability/", {"branch": self.branch.pk}).json()
        self.assertEqual([(p["name"], p["is_available"]) for p in listed], [("Latte", False)])
        self.set_availability(self.staff, self.latte, True)
        self.assertEqual(BranchProduct.objects.count(), 1)
        self.assertTrue(BranchProduct.objects.get().is_available)

    def test_customer_cannot_change_availability(self):
        self.assertEqual(self.set_availability(self.customer, self.latte, False).status_code, 403)
        self.assertEqual(self.as_user(self.customer).get("/api/staff/availability/", {"branch": self.branch.pk}).status_code, 403)

    def test_availability_rejects_other_tenant_data(self):
        self.assertEqual(self.set_availability(self.staff, self.foreign_product, False).status_code, 400)
        self.assertEqual(self.set_availability(self.staff, self.latte, False, self.foreign_branch).status_code, 400)
        self.assertEqual(self.as_user(self.staff).get("/api/staff/availability/", {"branch": self.foreign_branch.pk}).status_code, 400)
        self.assertEqual(BranchProduct.objects.count(), 0)

    def test_owner_toggles_banner(self):
        client = self.as_user(self.owner)
        self.assertEqual(client.get("/api/staff/banners/").json()[0]["title"], "2x1")
        response = client.patch(f"/api/staff/banners/{self.banner.pk}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 200)
        self.banner.refresh_from_db()
        self.assertFalse(self.banner.is_active)
        self.assertEqual(self.as_user(self.customer).get("/api/banners/").json(), [])

    def test_banners_are_owner_only_and_tenant_scoped(self):
        self.assertEqual(self.as_user(self.staff).get("/api/staff/banners/").status_code, 403)
        self.assertEqual(self.as_user(self.customer).get("/api/staff/banners/").status_code, 403)
        response = self.as_user(self.owner).patch(f"/api/staff/banners/{self.foreign_banner.pk}/", {"is_active": False}, format="json")
        self.assertEqual(response.status_code, 404)
        self.foreign_banner.refresh_from_db()
        self.assertTrue(self.foreign_banner.is_active)
