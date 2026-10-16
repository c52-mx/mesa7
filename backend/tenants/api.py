from rest_framework.exceptions import NotFound, ParseError


def resolve_tenant(request):
    """Tenant de la petición: header X-Tenant (slug), o el único del usuario.

    Solo acepta tenants en los que el usuario tiene membresía.
    """
    memberships = request.user.memberships.filter(tenant__is_active=True).select_related("tenant")
    slug = request.headers.get("X-Tenant")
    if slug:
        membership = memberships.filter(tenant__slug=slug).first()
        if membership is None:
            raise NotFound("Tenant no encontrado.")
        return membership.tenant
    found = list(memberships[:2])
    if not found:
        raise NotFound("El usuario no pertenece a ningún tenant.")
    if len(found) > 1:
        raise ParseError("Indica el tenant con el header X-Tenant.")
    return found[0].tenant
