from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_tenant
from tenants.models import Branch

from .models import BranchProduct, Product


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
    products = (
        Product.objects.for_tenant(tenant)
        .filter(is_active=True)
        .exclude(pk__in=hidden)
        .select_related("category")
    )
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
                "prep_time_minutes": p.prep_time_minutes,
            }
        )
    return Response({"branch": {"id": branch.id, "name": branch.name}, "categories": list(menu.values())})
