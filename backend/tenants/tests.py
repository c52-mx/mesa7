from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Branch, Membership, Tenant


class AdminScopingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name="Uno", slug="uno")
        cls.t2 = Tenant.objects.create(name="Dos", slug="dos")
        cls.own = Branch.objects.create(tenant=cls.t1, name="Propia")
        cls.foreign = Branch.objects.create(tenant=cls.t2, name="Ajena")
        cls.staff = get_user_model().objects.create_user(
            "staff@x.com", password="x", is_staff=True
        )
        Membership.objects.create(user=cls.staff, tenant=cls.t1, role="owner")

    def test_staff_sees_only_own_tenant_in_admin(self):
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.set(Permission.objects.filter(codename__endswith="branch"))
        self.client.force_login(self.staff)
        html = self.client.get("/admin/tenants/branch/").content.decode()
        self.assertIn("Propia", html)
        self.assertNotIn("Ajena", html)

    def test_staff_save_forces_own_tenant(self):
        from django.contrib.auth.models import Permission

        self.staff.user_permissions.set(Permission.objects.filter(codename__endswith="branch"))
        self.client.force_login(self.staff)
        self.client.post("/admin/tenants/branch/add/", {"name": "Nueva", "is_active": "on"})
        self.assertEqual(Branch.objects.get(name="Nueva").tenant, self.t1)


class BrandingTests(TestCase):
    def test_public_branding_without_auth(self):
        Tenant.objects.create(
            name="Cafecín", slug="cafecin", primary_color="#F07830", secondary_color="#781818"
        )
        data = self.client.get("/api/tenants/cafecin/").json()
        self.assertEqual(data["primary_color"], "#F07830")
        self.assertEqual(data["name"], "Cafecín")
        self.assertNotIn("id", data)

    def test_inactive_or_unknown_tenant_is_404(self):
        Tenant.objects.create(name="Off", slug="off", is_active=False)
        self.assertEqual(self.client.get("/api/tenants/off/").status_code, 404)
        self.assertEqual(self.client.get("/api/tenants/nope/").status_code, 404)

    def test_invalid_color_is_rejected(self):
        from django.core.exceptions import ValidationError

        tenant = Tenant(name="X", slug="x", primary_color="naranja")
        with self.assertRaises(ValidationError):
            tenant.full_clean()

class LogoTests(TestCase):
    def test_server_path_logo_becomes_absolute_url(self):
        Tenant.objects.create(name="Uno", slug="uno", logo_url="/static/brands/cafecin.jpg")
        data = self.client.get("/api/tenants/uno/").json()
        self.assertTrue(data["logo_url"].startswith("http://testserver/static/brands/"))

    def test_full_url_and_empty_logo_are_returned_as_is(self):
        Tenant.objects.create(name="Dos", slug="dos", logo_url="https://cdn.example.com/logo.png")
        Tenant.objects.create(name="Tres", slug="tres")
        self.assertEqual(self.client.get("/api/tenants/dos/").json()["logo_url"], "https://cdn.example.com/logo.png")
        self.assertEqual(self.client.get("/api/tenants/tres/").json()["logo_url"], "")
