import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Crea el superusuario de DJANGO_SUPERUSER_EMAIL / DJANGO_SUPERUSER_PASSWORD si no existe. "
        "Nunca modifica uno existente."
    )

    def handle(self, *args, **options):
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        if not email or not password:
            self.stdout.write("ensure_superuser: variables no definidas, se omite.")
            return
        User = get_user_model()
        if User.objects.filter(email=email.strip().lower()).exists():
            self.stdout.write("ensure_superuser: ya existe.")
            return
        User.objects.create_superuser(email, password)
        self.stdout.write(self.style.SUCCESS("ensure_superuser: creado."))
