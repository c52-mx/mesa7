from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from tenants.models import Branch, Membership, Tenant

User = get_user_model()
PASSWORD = "Clave-segura-123"


class AuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name="Café Uno", slug="uno")
        cls.t2 = Tenant.objects.create(name="Café Dos", slug="dos")
        Branch.objects.create(tenant=cls.t1, name="Centro")
        Branch.objects.create(tenant=cls.t2, name="Sur")

    def setUp(self):
        cache.clear()  # reinicia los throttles
        self.client = APIClient()

    def register(self, tenant="uno", email="Cli@X.com", password=PASSWORD):
        return self.client.post(
            "/api/auth/register/", {"tenant": tenant, "email": email, "password": password}
        )

    def test_register_creates_customer_and_returns_tokens(self):
        response = self.register()
        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertIn("access", body)
        self.assertEqual(body["memberships"], [{"tenant": "uno", "name": "Café Uno", "role": "customer"}])
        self.assertTrue(User.objects.filter(email="cli@x.com").exists())

    def test_register_rejects_weak_password_and_unknown_tenant(self):
        self.assertEqual(self.register(password="123").status_code, 400)
        self.assertEqual(self.register(tenant="nope").status_code, 400)

    def test_same_user_joins_second_tenant_with_correct_password(self):
        self.register()
        response = self.register(tenant="dos")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.json()["memberships"]), 2)
        self.assertEqual(User.objects.count(), 1)

    def test_existing_email_with_wrong_password_is_rejected(self):
        self.register()
        self.assertEqual(self.register(tenant="dos", password="Otra-clave-456").status_code, 400)
        self.assertEqual(Membership.objects.count(), 1)

    def test_login_returns_memberships(self):
        self.register()
        response = self.client.post("/api/auth/login/", {"email": "CLI@x.com", "password": PASSWORD})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["memberships"][0]["tenant"], "uno")

    def test_multi_tenant_user_must_choose_tenant(self):
        self.register()
        token = self.register(tenant="dos").json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/branches/").status_code, 400)
        names = [b["name"] for b in self.client.get("/api/branches/", HTTP_X_TENANT="dos").json()]
        self.assertEqual(names, ["Sur"])

    def test_cannot_use_tenant_without_membership(self):
        token = self.register().json()["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(self.client.get("/api/branches/", HTTP_X_TENANT="dos").status_code, 404)


class CommandTests(TestCase):
    def test_seed_demo_is_idempotent_and_hides_products_per_branch(self):
        call_command("seed_demo")
        call_command("seed_demo")
        user = User.objects.create_user("c@x.com", password=PASSWORD)
        Membership.objects.create(user=user, tenant=Tenant.objects.get(slug="demo"))
        client = APIClient()
        client.force_authenticate(user)
        branches = {b["name"]: b["id"] for b in client.get("/api/branches/").json()}
        def count(name):
            menu = client.get(f"/api/branches/{branches[name]}/menu/").json()
            return sum(len(c["products"]) for c in menu["categories"])
        self.assertEqual(count("Centro"), 14)
        self.assertEqual(count("Norte"), 12)

    def test_ensure_superuser_creates_once(self):
        import os
        from unittest import mock

        env = {"DJANGO_SUPERUSER_EMAIL": "Admin@X.com", "DJANGO_SUPERUSER_PASSWORD": "pw"}
        with mock.patch.dict(os.environ, env):
            call_command("ensure_superuser")
            User.objects.filter(email="admin@x.com").update(is_active=False)
            call_command("ensure_superuser")
        user = User.objects.get(email="admin@x.com")
        self.assertTrue(user.is_superuser)
        self.assertFalse(user.is_active)  # no se tocó el existente

class EnsureStaffTests(TestCase):
    def test_creates_staff_once_and_never_resets_the_password(self):
        import os
        from unittest import mock

        Tenant.objects.create(name="Cafecín", slug="cafecin")
        env = {"DJANGO_STAFF_EMAIL": "Caja@X.com", "DJANGO_STAFF_PASSWORD": "pw-1"}
        with mock.patch.dict(os.environ, env):
            call_command("ensure_staff")
            user = User.objects.get(email="caja@x.com")
            user.set_password("cambiada")
            user.save()
            call_command("ensure_staff")
        user = User.objects.get(email="caja@x.com")
        self.assertTrue(user.check_password("cambiada"))
        self.assertEqual(Membership.objects.get(user=user).role, "staff")

    def test_skips_when_variables_or_tenant_are_missing(self):
        import os
        from unittest import mock

        with mock.patch.dict(os.environ, {"DJANGO_STAFF_EMAIL": "a@x.com", "DJANGO_STAFF_PASSWORD": "x"}):
            call_command("ensure_staff")  # el negocio no existe
        self.assertFalse(User.objects.filter(email="a@x.com").exists())
        call_command("ensure_staff")  # sin variables
