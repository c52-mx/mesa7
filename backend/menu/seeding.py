"""Carga idempotente de un negocio completo (marca, sucursales, menú, opciones, lealtad y promos).

La usan los comandos `seed_demo` y `seed_cafecin`; cada uno solo define sus datos.
"""

from loyalty.models import LoyaltyProgram, LoyaltyReward
from promos.models import Banner
from tenants.models import Branch, Tenant

from .models import BranchProduct, Category, Option, OptionGroup, Product, ProductOptionGroup


def load_tenant(cfg):
    """cfg: ver los comandos. Vuelve a correr sin duplicar; los datos del cfg pisan lo existente."""
    tenant, _ = Tenant.objects.update_or_create(
        slug=cfg["slug"],
        defaults={
            "name": cfg["name"],
            "primary_color": cfg["primary_color"],
            "secondary_color": cfg["secondary_color"],
            "logo_url": cfg["logo_url"],
        },
    )

    branches = {}
    for name, address, phone, hours in cfg["branches"]:
        branches[name], _ = Branch.objects.update_or_create(
            tenant=tenant, name=name, defaults={"address": address, "phone": phone, "hours": hours}
        )

    products = {}
    for position, (category_name, items) in enumerate(cfg["menu"]):
        category, _ = Category.objects.update_or_create(
            tenant=tenant, name=category_name, defaults={"position": position, "icon": cfg["icons"][category_name]}
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
                    "is_featured": name in cfg["featured"],
                },
            )

    groups = {}
    for group_name, (minimum, maximum, options) in cfg["groups"].items():
        groups[group_name], _ = OptionGroup.objects.update_or_create(
            tenant=tenant, name=group_name, defaults={"min_select": minimum, "max_select": maximum}
        )
        for position, (option_name, extra, popular) in enumerate(options):
            Option.objects.update_or_create(
                tenant=tenant,
                group=groups[group_name],
                name=option_name,
                defaults={"price_delta": extra, "is_popular": popular, "position": position},
            )
    for name, product in products.items():
        for position, group_name in enumerate(cfg["groups_for"](name, product.category.name)):
            ProductOptionGroup.objects.update_or_create(
                tenant=tenant, product=product, group=groups[group_name], defaults={"position": position}
            )

    for branch_name, product_names in cfg.get("hidden", {}).items():
        for name in product_names:
            BranchProduct.objects.update_or_create(
                tenant=tenant, branch=branches[branch_name], product=products[name], defaults={"is_available": False}
            )

    LoyaltyProgram.objects.get_or_create(tenant=tenant, defaults={"spend_per_point": cfg["spend_per_point"]})
    for points, name in cfg["rewards"]:
        LoyaltyReward.objects.update_or_create(tenant=tenant, points_required=points, defaults={"name": name})
    for position, (title, text) in enumerate(cfg["banners"]):
        Banner.objects.update_or_create(tenant=tenant, title=title, defaults={"text": text, "position": position})
    return tenant
