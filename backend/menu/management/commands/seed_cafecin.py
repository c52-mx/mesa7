from django.core.management.base import BaseCommand

from menu.seeding import load_tenant

# Menú y precios de EJEMPLO para presentar al prospecto; el negocio los reemplaza desde el admin.
MENU = [
    ("Cafés calientes", [
        ("Espresso", "38", 2, "Shot doble de espresso"),
        ("Americano", "42", 3, "Espresso con agua caliente"),
        ("Café de olla", "45", 4, "Canela y piloncillo"),
        ("Capuchino", "58", 4, "Espresso, leche y espuma"),
        ("Latte", "60", 4, "Espresso con leche vaporizada"),
        ("Moka", "66", 5, "Espresso, chocolate y leche"),
        ("Gloria", "72", 5, "El café de la casa: espresso, cajeta y canela"),
    ]),
    ("Bebidas frías", [
        ("Cold brew", "62", 2, "Café en infusión fría por 12 horas"),
        ("Frappé de cajeta", "74", 6, "Café frappé con cajeta y crema"),
        ("Limonada mineral", "45", 3, "Limón, agua mineral y hielo"),
        ("Té helado de jamaica", "42", 2, "Jamaica natural con hielo"),
    ]),
    ("Panadería", [
        ("Concha", "30", 2, "La de la casa: vainilla o chocolate"),
        ("Cuernito", "38", 2, "Hojaldre de mantequilla"),
        ("Pan de elote", "42", 2, "Rebanada tibia"),
        ("Croissant", "48", 3, "Mantequilla, horneado del día"),
    ]),
    ("Alimentos", [
        ("Molletes", "85", 8, "Frijoles, queso gratinado y pico de gallo"),
        ("Baguette de jamón y queso", "92", 6, "Jamón, queso y arúgula"),
        ("Sándwich de pollo", "98", 8, "Pollo, aguacate y chipotle"),
        ("Chilaquiles", "110", 10, "Salsa verde o roja, crema y queso"),
    ]),
    ("Postres", [
        ("Cheesecake", "78", 2, "Rebanada con frutos rojos"),
        ("Brownie", "55", 2, "Chocolate oscuro con nuez"),
        ("Pastel de zanahoria", "70", 2, "Con betún de queso crema"),
        ("Flan napolitano", "60", 2, "Receta de la casa"),
    ]),
]
GRUPOS = {
    "Tamaño": (1, 1, [("Chico", "0", False), ("Grande", "12", True)]),
    "Tipo de leche": (
        1, 1,
        [("Entera", "0", False), ("Deslactosada", "14", True), ("Almendra", "17", False), ("Avena", "17", False)],
    ),
    "Extras": (
        0, 3,
        [("Shot extra", "14", True), ("Crema batida", "10", False), ("Jarabe de vainilla", "14", False),
         ("Jarabe de cajeta", "14", False)],
    ),
    "Sabor": (1, 1, [("Vainilla", "0", True), ("Chocolate", "0", False)]),
    "¿Lo calentamos?": (1, 1, [("Sí, caliente", "0", True), ("No, así está bien", "0", False)]),
    "Acompañamiento": (0, 1, [("Bola de helado", "22", True), ("Salsa de cajeta", "8", False)]),
}
CON_LECHE = {"Capuchino", "Latte", "Moka", "Gloria", "Frappé de cajeta"}
POR_CATEGORIA = {
    "Cafés calientes": ["Tamaño", "Extras"],
    "Bebidas frías": ["Tamaño", "Extras"],
    "Panadería": ["¿Lo calentamos?"],
    "Alimentos": ["¿Lo calentamos?"],
    "Postres": ["Acompañamiento"],
}


def grupos_de(producto, categoria):
    if producto == "Concha":
        return ["Sabor", "¿Lo calentamos?"]
    grupos = list(POR_CATEGORIA.get(categoria, []))
    if producto in CON_LECHE:
        grupos.insert(1, "Tipo de leche")
    return grupos


CONFIG = {
    "slug": "cafecin",
    "name": "Cafecín",
    "primary_color": "#F07830",
    "secondary_color": "#781818",
    "logo_url": "/static/brands/cafecin.jpg",
    "branches": [
        (
            "Multiplaza Ojo de Agua",
            "Multi Plaza Ojo de Agua, Boulevard Santa Cruz Ojo de Agua 88, 55760 Ojo de Agua, Méx.",
            "55 5049 9486",
            "Todos los días · cierra 10 p. m.",
        ),
    ],
    "menu": MENU,
    "icons": {
        "Cafés calientes": "cafe", "Bebidas frías": "cold", "Panadería": "dessert",
        "Alimentos": "food", "Postres": "dessert",
    },
    "featured": {"Gloria", "Frappé de cajeta", "Concha", "Cheesecake"},
    "groups": GRUPOS,
    "groups_for": grupos_de,
    "spend_per_point": 10,
    "rewards": [
        (25, "Café americano de cortesía"),
        (50, "Concha de cortesía"),
        (75, "Postre de cortesía"),
        (100, "Bebida y postre de cortesía"),
    ],
    "banners": [
        ("El café que sabe a Gloria", "Pide desde tu celular y recoge sin filas."),
        ("Suma puntos con cada visita", "1 punto por cada $10. Canjéalos por café, pan y postres."),
        ("La concha de la casa", "Vainilla o chocolate, recién horneada."),
    ],
}


class Command(BaseCommand):
    help = "Crea (o actualiza) el negocio Cafecín con datos de ejemplo para la presentación. Es idempotente."

    def handle(self, *args, **options):
        tenant = load_tenant(CONFIG)
        self.stdout.write(self.style.SUCCESS(f"Cafecín listo: tenant '{tenant.slug}'."))
