from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_staff_tenant, resolve_tenant

from .services import customer_summary, earn_at_counter, find_account, redeem_reward, summary


@api_view(["GET"])
def loyalty(request):
    tenant = resolve_tenant(request)
    data = summary(tenant, request.user)
    if data is None:
        raise Http404  # lealtad apagada o sin programa configurado
    data["name"] = request.user.full_name or request.user.email.split("@")[0]
    return Response(data)


class LookupSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=100)


class RedeemSerializer(LookupSerializer):
    reward = serializers.IntegerField()


class EarnSerializer(LookupSerializer):
    amount = serializers.CharField(max_length=20)


def _account(request, serializer_class):
    tenant = resolve_staff_tenant(request)
    serializer = serializer_class(data=request.data if request.method == "POST" else request.query_params)
    serializer.is_valid(raise_exception=True)
    return tenant, find_account(tenant, serializer.validated_data["code"]), serializer.validated_data


@api_view(["GET"])
def staff_lookup(request):
    """Caja: datos de la tarjeta de un cliente (código de 12 dígitos o texto del QR)."""
    tenant, account, _ = _account(request, LookupSerializer)
    return Response(customer_summary(tenant, account))


@api_view(["POST"])
def staff_redeem(request):
    tenant, account, data = _account(request, RedeemSerializer)
    redeem_reward(tenant, account, data["reward"], request.user)
    return Response(customer_summary(tenant, account))


@api_view(["POST"])
def staff_earn(request):
    tenant, account, data = _account(request, EarnSerializer)
    earn_at_counter(tenant, account, data["amount"], request.user)
    return Response(customer_summary(tenant, account))
