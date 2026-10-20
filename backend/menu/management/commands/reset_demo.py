from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from loyalty.models import LoyaltyAccount, LoyaltyTransaction
from orders.models import Order
from tenants.models import Tenant


class Command(BaseCommand):
    help = (
        "Borra los pedidos y los puntos de un negocio para repetir la demo desde cero. "
        "Conserva usuarios, menú y configuración. Requiere --yes."
    )

    def add_arguments(self, parser):
        parser.add_argument("--tenant", required=True, help="slug del negocio, por ejemplo cafecin")
        parser.add_argument("--yes", action="store_true", help="confirma el borrado")

    @transaction.atomic
    def handle(self, *args, tenant, yes, **options):
        try:
            tenant_obj = Tenant.objects.get(slug=tenant)
        except Tenant.DoesNotExist:
            raise CommandError(f"No existe el negocio '{tenant}'.")
        orders = Order.objects.for_tenant(tenant_obj)
        accounts = LoyaltyAccount.objects.for_tenant(tenant_obj)
        summary = f"{orders.count()} pedido(s) y {accounts.count()} tarjeta(s) de '{tenant}'"
        if not yes:
            raise CommandError(f"Se borrarían {summary}. Repite con --yes para confirmar.")
        # Primero los movimientos: referencian pedidos y no permiten borrarlos antes.
        LoyaltyTransaction.objects.for_tenant(tenant_obj).delete()
        orders.delete()
        accounts.delete()
        self.stdout.write(self.style.SUCCESS(f"Borrado: {summary}."))
