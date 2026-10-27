from django.http import Http404
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.exceptions import NotFound, ParseError, PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Membership, Tenant


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def tenant_branding(request, slug):
    """Marca pública del negocio: la app la necesita antes de que el usuario inicie sesión."""
    try:
        tenant = Tenant.objects.get(slug=slug, is_active=True)
    except Tenant.DoesNotExist:
        raise Http404
    logo = tenant.logo_url
    if logo.startswith("/"):  # ruta del propio servidor: la app necesita la URL completa
        logo = request.build_absolute_uri(logo)
    return Response(
        {
            "slug": tenant.slug,
            "name": tenant.name,
            "primary_color": tenant.primary_color,
            "secondary_color": tenant.secondary_color,
            "logo_url": logo,
            "loyalty_enabled": tenant.loyalty_enabled,
            "orders_enabled": tenant.orders_enabled,
            "kds_enabled": tenant.kds_enabled,
        }
    )


def resolve_membership(request):
    return membership_for(request.user, request.headers.get("X-Tenant"))


def membership_for(user, slug=None):
    """Membresía del usuario: la del tenant `slug` (header X-Tenant), o la única que tenga.

    Solo acepta tenants en los que el usuario tiene membresía.
    """
    memberships = user.memberships.filter(tenant__is_active=True).select_related("tenant")
    if slug:
        membership = memberships.filter(tenant__slug=slug).first()
        if membership is None:
            raise NotFound("Tenant no encontrado.")
        return membership
    found = list(memberships[:2])
    if not found:
        raise NotFound("El usuario no pertenece a ningún tenant.")
    if len(found) > 1:
        raise ParseError("Indica el tenant con el header X-Tenant.")
    return found[0]


def resolve_tenant(request):
    return resolve_membership(request).tenant


def require_module(tenant, flag):
    """Rechaza (404) si el negocio no tiene contratado el módulo (`orders_enabled`, `kds_enabled`...)."""
    if not getattr(tenant, flag):
        raise NotFound("Este módulo no está activo en el negocio.")
    return tenant


def resolve_staff_tenant(request, owner_only=False):
    """Tenant de la petición, solo si el usuario es dueño o staff (solo dueño con `owner_only`) de ese negocio."""
    membership = resolve_membership(request)
    allowed = (Membership.Role.OWNER,) if owner_only else (Membership.Role.OWNER, Membership.Role.STAFF)
    if membership.role not in allowed:
        raise PermissionDenied("Solo el dueño del negocio puede hacer esto." if owner_only else "Solo el personal del negocio puede hacer esto.")
    return membership.tenant
