from rest_framework.exceptions import NotFound, ParseError, PermissionDenied

from .models import Membership


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


def resolve_staff_tenant(request):
    """Tenant de la petición, solo si el usuario es dueño o staff de ese negocio."""
    membership = resolve_membership(request)
    if membership.role not in (Membership.Role.OWNER, Membership.Role.STAFF):
        raise PermissionDenied("Solo el personal del negocio puede hacer esto.")
    return membership.tenant
