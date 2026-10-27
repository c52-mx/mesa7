from django.http import Http404
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_staff_tenant, resolve_tenant

from .models import Banner


@api_view(["GET"])
def banners(request):
    tenant = resolve_tenant(request)
    active = Banner.objects.for_tenant(tenant).filter(is_active=True)
    return Response(
        [{"id": b.pk, "title": b.title, "text": b.text, "image_url": b.image_url} for b in active]
    )


class ToggleSerializer(serializers.Serializer):
    is_active = serializers.BooleanField()


@api_view(["GET"])
def staff_banners(request):
    """Todas las promociones del negocio (activas o no), para que el dueño las encienda o apague."""
    tenant = resolve_staff_tenant(request, owner_only=True)
    return Response(
        [{"id": b.pk, "title": b.title, "text": b.text, "is_active": b.is_active} for b in Banner.objects.for_tenant(tenant)]
    )


@api_view(["PATCH"])
def staff_banner_toggle(request, banner_id):
    tenant = resolve_staff_tenant(request, owner_only=True)
    serializer = ToggleSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    try:
        banner = Banner.objects.for_tenant(tenant).get(pk=banner_id)
    except Banner.DoesNotExist:
        raise Http404
    banner.is_active = serializer.validated_data["is_active"]
    banner.save(update_fields=["is_active"])
    return Response({"id": banner.pk, "title": banner.title, "text": banner.text, "is_active": banner.is_active})
