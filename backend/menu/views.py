from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_staff_tenant, resolve_tenant
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
    return Response(
        [{"id": b.id, "name": b.name, "address": b.address, "phone": b.phone, "hours": b.hours} for b in qs]
    )


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
                "icon": p.category.icon,
                "is_featured": p.is_featured,
                "prep_time_minutes": p.prep_time_minutes,
                "option_groups": [group_payload(g) for g in groups[p.pk]],
            }
        )
    return Response({"branch": {"id": branch.id, "name": branch.name}, "categories": list(menu.values())})


class AvailabilitySerializer(serializers.Serializer):
    branch = serializers.IntegerField()
    product = serializers.IntegerField()
    is_available = serializers.BooleanField()


@api_view(["GET"])
def staff_availability(request):
    """Productos activos con su disponibilidad en una sucursal (?branch=<id>), para marcar agotados."""
    tenant = resolve_staff_tenant(request)
    try:
        branch = Branch.objects.for_tenant(tenant).get(pk=int(request.query_params.get("branch", "")))
    except (ValueError, Branch.DoesNotExist):
        raise serializers.ValidationError({"branch": "Sucursal no encontrada."})
    hidden = set(
        BranchProduct.objects.for_tenant(tenant).filter(branch=branch, is_available=False).values_list("product_id", flat=True)
    )
    products = Product.objects.for_tenant(tenant).filter(is_active=True).select_related("category")
    return Response(
        [
            {"id": p.id, "name": p.name, "category": p.category.name, "is_available": p.id not in hidden}
            for p in products
        ]
    )


@api_view(["POST"])
def staff_set_availability(request):
    tenant = resolve_staff_tenant(request)
    serializer = AvailabilitySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    try:
        branch = Branch.objects.for_tenant(tenant).get(pk=data["branch"])
        product = Product.objects.for_tenant(tenant).get(pk=data["product"])
    except (Branch.DoesNotExist, Product.DoesNotExist):
        raise serializers.ValidationError("Sucursal o producto no encontrado.")
    BranchProduct.objects.update_or_create(
        tenant=tenant, branch=branch, product=product, defaults={"is_available": data["is_available"]}
    )
    return Response({"id": product.id, "is_available": data["is_available"]})
