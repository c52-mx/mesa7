from django.core.management.base import BaseCommand

from menu.seeding import load_tenant

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
# Grupos de opciones: nombre -> (mínimo, máximo, [(opción, cargo extra, popular)])
GRUPOS = {
    "Tamaño": (1, 1, [("Chico", "0", False), ("Grande", "12", True)]),
    "Tipo de leche": (
        1, 1,
        [("Entera", "0", False), ("Deslactosada", "14", True), ("Almendra", "17", False), ("Avena", "17", False)],
    ),
    "Extras": (
        0, 3,
        [("Shot extra", "14", True), ("Crema batida", "10", False), ("Jarabe de vainilla", "14", False),
         ("Jarabe de caramelo", "14", False)],
    ),
    "¿Lo calentamos?": (1, 1, [("Sí, caliente", "0", True), ("No, así está bien", "0", False)]),
    "Acompañamiento": (0, 1, [("Bola de helado", "22", True), ("Salsa de caramelo", "8", False)]),
}
CON_LECHE = {"Latte", "Capuchino", "Moka", "Chai latte", "Frappé de caramelo"}
POR_CATEGORIA = {
    "Bebidas calientes": ["Tamaño", "Extras"],
    "Bebidas frías": ["Tamaño", "Extras"],
    "Alimentos": ["¿Lo calentamos?"],
    "Postres": ["Acompañamiento"],
}


def grupos_de(producto, categoria):
    grupos = list(POR_CATEGORIA.get(categoria, []))
    if producto in CON_LECHE:
        grupos.insert(1, "Tipo de leche")
    return grupos


CONFIG = {
    "slug": "demo",
    "name": "Café Demo",
    # Paleta de Cafecín (naranja del logo y vino de la bufanda)
    "primary_color": "#F07830",
    "secondary_color": "#781818",
    "logo_url": "/static/brands/cafecin.jpg",
    "branches": [
        ("Centro", "Av. Juárez 100", "", ""),
        ("Norte", "Blvd. Norte 250", "", ""),
    ],
    "menu": MENU,
    "icons": {"Bebidas calientes": "cafe", "Bebidas frías": "cold", "Alimentos": "food", "Postres": "dessert"},
    "featured": {"Latte", "Frappé de caramelo", "Cheesecake", "Croissant"},
    "groups": GRUPOS,
    "groups_for": grupos_de,
    "hidden": {"Norte": ["Frappé de caramelo", "Cheesecake"]},
    "spend_per_point": 10,
    # Hitos de la barra de progreso: (puntos, premio). 1 punto por cada $10 gastados.
    "rewards": [
        (25, "Americano de cortesía"),
        (50, "Postre de cortesía"),
        (75, "Sándwich de cortesía"),
        (100, "Bebida y postre de cortesía"),
    ],
    "banners": [
        ("Bienvenido a Café Demo", "Pide desde tu celular y recoge sin filas."),
        ("Suma puntos con cada pedido", "1 punto por cada $10. Canjéalos por bebidas y postres."),
        ("Cold brew de temporada", "Pruébalo hoy en cualquier sucursal."),
    ],
}


class Command(BaseCommand):
    help = "Crea (o actualiza) un tenant demo de cafetería. Es idempotente."

    def handle(self, *args, **options):
        tenant = load_tenant(CONFIG)
        self.stdout.write(self.style.SUCCESS(f"Demo listo: tenant '{tenant.slug}'."))
