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
