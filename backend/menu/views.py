from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_tenant
from tenants.models import Branch

from .models import BranchProduct, Product
from .services import option_groups_for


def group_payload(group):
    return {
        "id": group["id"],
        "name": group["name"],
        "required": group["required"],
        "max_select": group["max_select"],
        "options": [{**o, "price_delta": str(o["price_delta"])} for o in group["options"]],
    }


@api_view(["GET"])
def branches(request):
    tenant = resolve_tenant(request)
    qs = Branch.objects.for_tenant(tenant).filter(is_active=True).order_by("name")
    return Response([{"id": b.id, "name": b.name, "address": b.address} for b in qs])


@api_view(["GET"])
def branch_menu(request, branch_id):
    tenant = resolve_tenant(request)
    try:
        branch = Branch.objects.for_tenant(tenant).get(pk=branch_id, is_active=True)
    except Branch.DoesNotExist:
        raise Http404
    hidden = BranchProduct.objects.for_tenant(tenant).filter(
        branch=branch, is_available=False
    ).values("product_id")
    products = list(
        Product.objects.for_tenant(tenant)
        .filter(is_active=True)
        .exclude(pk__in=hidden)
        .select_related("category")
    )
    groups = option_groups_for(products)
    menu = {}
    for p in products:
        entry = menu.setdefault(
            p.category_id, {"id": p.category_id, "name": p.category.name, "products": []}
        )
        entry["products"].append(
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "price": str(p.price),
                "image_url": p.image_url,
                "is_featured": p.is_featured,
                "prep_time_minutes": p.prep_time_minutes,
                "option_groups": [group_payload(g) for g in groups[p.pk]],
            }
        )
    return Response({"branch": {"id": branch.id, "name": branch.name}, "categories": list(menu.values())})
