import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tenants.models import Membership, Tenant


class Command(BaseCommand):
    help = (
        "Crea el usuario de caja de DJANGO_STAFF_EMAIL / DJANGO_STAFF_PASSWORD con rol staff en "
        "DJANGO_STAFF_TENANT (por defecto cafecin) si no existe. Nunca cambia la contraseña de uno existente."
    )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_STAFF_EMAIL", "").strip().lower()
        password = os.environ.get("DJANGO_STAFF_PASSWORD", "")
        slug = os.environ.get("DJANGO_STAFF_TENANT", "cafecin")
        if not email or not password:
            self.stdout.write("ensure_staff: variables no definidas, se omite.")
            return
        tenant = Tenant.objects.filter(slug=slug).first()
        if tenant is None:
            self.stdout.write(f"ensure_staff: no existe el negocio '{slug}', se omite.")
            return
        User = get_user_model()
        user = User.objects.filter(email=email).first()
        created = user is None
        if created:
            user = User.objects.create_user(email, password, full_name="Caja")
        Membership.objects.update_or_create(user=user, tenant=tenant, defaults={"role": Membership.Role.STAFF})
        self.stdout.write(self.style.SUCCESS(f"ensure_staff: {'creado' if created else 'ya existía'} ({email} en {slug})."))
