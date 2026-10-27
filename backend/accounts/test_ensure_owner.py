import os
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from tenants.models import Membership, Tenant

User = get_user_model()


class EnsureOwnerTests(TestCase):
    def run_command(self, **env):
        with mock.patch.dict(os.environ, env, clear=False):
            call_command("ensure_owner", stdout=StringIO())

    def test_creates_owner_once_and_resets_only_listed_passwords(self):
        tenant = Tenant.objects.create(name="Cafecín", slug="cafecin")
        other = User.objects.create_user("otro@x.com", password="original")
        listed = User.objects.create_user("lista@x.com", password="original")
        env = {"DJANGO_OWNER_EMAIL": "Admin@x.com", "DJANGO_OWNER_PASSWORD": "Nueva123!", "DJANGO_RESET_EMAILS": "lista@x.com"}
        self.run_command(**env)
        owner = User.objects.get(email="admin@x.com")
        self.assertTrue(owner.check_password("Nueva123!"))
        self.assertEqual(Membership.objects.get(user=owner, tenant=tenant).role, "owner")
        listed.refresh_from_db(); other.refresh_from_db()
        self.assertTrue(listed.check_password("Nueva123!"))
        self.assertTrue(other.check_password("original"))
        owner.set_password("cambiada"); owner.save()
        self.run_command(**{**env, "DJANGO_RESET_EMAILS": ""})
        owner.refresh_from_db()
        self.assertTrue(owner.check_password("cambiada"))
