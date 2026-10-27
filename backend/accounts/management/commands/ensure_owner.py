import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from tenants.models import Membership, Tenant


class Command(BaseCommand):
    help = (
        "Crea el dueño de DJANGO_OWNER_EMAIL / DJANGO_OWNER_PASSWORD con rol owner en DJANGO_OWNER_TENANT "
        "(por defecto cafecin) si no existe. Si DJANGO_RESET_EMAILS (correos separados por coma) está definido, "
        "les asigna DJANGO_OWNER_PASSWORD; quita esa variable después de un arranque. Lista los usuarios al final."
    )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_OWNER_EMAIL", "").strip().lower()
        password = os.environ.get("DJANGO_OWNER_PASSWORD", "")
        slug = os.environ.get("DJANGO_OWNER_TENANT", "cafecin")
        User = get_user_model()
        if not email or not password:
            self.stdout.write("ensure_owner: variables no definidas, se omite.")
            return
        tenant = Tenant.objects.filter(slug=slug).first()
        if tenant is None:
            self.stdout.write(f"ensure_owner: no existe el negocio '{slug}', se omite.")
        else:
            user = User.objects.filter(email=email).first()
            created = user is None
            if created:
                user = User.objects.create_user(email, password, full_name="Admin")
            Membership.objects.update_or_create(user=user, tenant=tenant, defaults={"role": Membership.Role.OWNER})
            self.stdout.write(self.style.SUCCESS(f"ensure_owner: {'creado' if created else 'ya existía'} ({email} en {slug})."))
        for reset in filter(None, (e.strip().lower() for e in os.environ.get("DJANGO_RESET_EMAILS", "").split(","))):
            target = User.objects.filter(email=reset).first()
            if target is None:
                self.stdout.write(f"ensure_owner: {reset} no existe, no se cambia la contraseña.")
                continue
            target.set_password(password)
            target.save(update_fields=["password"])
            self.stdout.write(self.style.SUCCESS(f"ensure_owner: contraseña asignada a {reset}."))
        for m in Membership.objects.select_related("user", "tenant").order_by("tenant__slug", "role", "user__email"):
            self.stdout.write(f"usuario: {m.tenant.slug} | {m.role} | {m.user.email} | superuser={m.user.is_superuser}")
        for u in User.objects.filter(memberships__isnull=True):
            self.stdout.write(f"usuario: sin membresía | {u.email} | superuser={u.is_superuser}")
