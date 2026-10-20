from django.db import transaction
from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_staff_tenant, resolve_tenant
from tenants.models import Branch

from .models import Order
from .payloads import order_payload
from .services import change_status, create_order


class ItemSerializer(serializers.Serializer):
    product = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, max_value=20)
    options = serializers.ListField(child=serializers.IntegerField(), required=False, default=list, max_length=30)
    notes = serializers.CharField(required=False, allow_blank=True, default="", max_length=200)


class OrderCreateSerializer(serializers.Serializer):
    branch = serializers.IntegerField()
    items = ItemSerializer(many=True, allow_empty=False, max_length=50)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


def _orders(tenant):
    return (
        Order.objects.for_tenant(tenant)
        .select_related("customer")
        .prefetch_related("items")
    )


@api_view(["GET", "POST"])
def orders(request):
    tenant = resolve_tenant(request)
    if request.method == "POST":
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        try:
            branch = Branch.objects.for_tenant(tenant).get(pk=data["branch"], is_active=True)
        except Branch.DoesNotExist:
            raise serializers.ValidationError({"branch": "Sucursal no encontrada."})
        order = create_order(
            tenant=tenant,
            branch=branch,
            customer=request.user,
            items=data["items"],
            notes=data.get("notes", ""),
        )
        return Response(order_payload(_orders(tenant).get(pk=order.pk)), status=201)
    mine = _orders(tenant).filter(customer=request.user)[:50]
    return Response([order_payload(o) for o in mine])


@api_view(["GET"])
def order_detail(request, order_id):
    tenant = resolve_tenant(request)
    try:
        order = _orders(tenant).get(pk=order_id, customer=request.user)
    except Order.DoesNotExist:
        raise Http404
    return Response(order_payload(order))


@api_view(["GET"])
def kds_orders(request):
    tenant = resolve_staff_tenant(request)
    try:
        branch_id = int(request.query_params.get("branch", ""))
    except ValueError:
        raise serializers.ValidationError({"branch": "Indica la sucursal (?branch=<id>)."})
    active = _orders(tenant).filter(branch_id=branch_id, status__in=Order.ACTIVE).order_by("created_at")
    return Response([order_payload(o, kds=True) for o in active])


@api_view(["POST"])
def kds_set_status(request, order_id):
    tenant = resolve_staff_tenant(request)
    new_status = request.data.get("status")
    with transaction.atomic():
        try:
            order = Order.objects.for_tenant(tenant).select_for_update().get(pk=order_id)
        except Order.DoesNotExist:
            raise Http404
        change_status(order, new_status)
    return Response(order_payload(_orders(tenant).get(pk=order.pk), kds=True))
