from django.core.management.base import BaseCommand

from loyalty.models import LoyaltyProgram, LoyaltyReward
from menu.models import BranchProduct, Category, Product
from promos.models import Banner
from tenants.models import Branch, Tenant

# (categoría, [(producto, precio MXN, minutos de preparación, descripción)])
MENU = [
    ("Bebidas calientes", [
        ("Espresso", "35", 2, "Shot doble de espresso"),
        ("Americano", "40", 3, "Espresso con agua caliente"),
        ("Latte", "55", 4, "Espresso con leche vaporizada"),
        ("Capuchino", "55", 4, "Espresso, leche y espuma"),
        ("Moka", "62", 5, "Espresso, chocolate y leche"),
        ("Chai latte", "58", 5, "Té chai especiado con leche"),
    ]),
    ("Bebidas frías", [
        ("Cold brew", "58", 2, "Café en infusión fría 12 h"),
        ("Frappé de caramelo", "68", 6, "Café frappé con caramelo"),
        ("Limonada mineral", "40", 3, "Limón, agua mineral y hielo"),
    ]),
    ("Alimentos", [
        ("Croissant", "45", 3, "Mantequilla, horneado del día"),
        ("Baguette de jamón y queso", "85", 6, "Jamón, queso y arúgula"),
        ("Sándwich de pollo", "95", 8, "Pollo, aguacate y chipotle"),
    ]),
    ("Postres", [
        ("Cheesecake", "75", 2, "Rebanada con frutos rojos"),
        ("Brownie", "50", 2, "Chocolate oscuro con nuez"),
    ]),
]
# Hitos de la barra de progreso: (puntos, premio). 1 punto por cada $10 gastados.
RECOMPENSAS = [
    (25, "Americano de cortesía"),
    (50, "Postre de cortesía"),
    (75, "Sándwich de cortesía"),
    (100, "Bebida y postre de cortesía"),
]
BANNERS = [
    ("Bienvenido a Café Demo", "Pide desde tu celular y recoge sin filas."),
    ("Suma puntos con cada pedido", "1 punto por cada $10. Canjéalos por bebidas y postres."),
    ("Cold brew de temporada", "Pruébalo hoy en cualquier sucursal."),
]
SUCURSALES = [("Centro", "Av. Juárez 100"), ("Norte", "Blvd. Norte 250")]
NO_DISPONIBLE_EN_NORTE = ["Frappé de caramelo", "Cheesecake"]


class Command(BaseCommand):
    help = "Crea (o actualiza) un tenant demo de cafetería. Es idempotente."

    def handle(self, *args, **options):
        tenant, _ = Tenant.objects.update_or_create(
            slug="demo",
            defaults={
                "name": "Café Demo",
                # Paleta de Cafecín (naranja del logo y vino de la bufanda)
                "primary_color": "#F07830",
                "secondary_color": "#781818",
            },
        )
        branches = {
            name: Branch.objects.get_or_create(
                tenant=tenant, name=name, defaults={"address": address}
            )[0]
            for name, address in SUCURSALES
        }
        products = {}
        for position, (cat_name, items) in enumerate(MENU):
            category, _ = Category.objects.update_or_create(
                tenant=tenant, name=cat_name, defaults={"position": position}
            )
            for name, price, prep, description in items:
                products[name], _ = Product.objects.update_or_create(
                    tenant=tenant,
                    category=category,
                    name=name,
                    defaults={
                        "price": price,
                        "prep_time_minutes": prep,
                        "description": description,
                    },
                )
        for name in NO_DISPONIBLE_EN_NORTE:
            BranchProduct.objects.update_or_create(
                tenant=tenant,
                branch=branches["Norte"],
                product=products[name],
                defaults={"is_available": False},
            )
        LoyaltyProgram.objects.get_or_create(tenant=tenant, defaults={"spend_per_point": 10})
        for points, name in RECOMPENSAS:
            LoyaltyReward.objects.update_or_create(
                tenant=tenant, points_required=points, defaults={"name": name}
            )
        for position, (title, text) in enumerate(BANNERS):
            Banner.objects.update_or_create(
                tenant=tenant, title=title, defaults={"text": text, "position": position}
            )
        self.stdout.write(self.style.SUCCESS(f"Demo listo: tenant '{tenant.slug}'."))
