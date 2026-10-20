from django.http import Http404
from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_tenant

from .services import summary


@api_view(["GET"])
def loyalty(request):
    tenant = resolve_tenant(request)
    data = summary(tenant, request.user)
    if data is None:
        raise Http404  # lealtad apagada o sin programa configurado
    data["name"] = request.user.full_name or request.user.email.split("@")[0]
    return Response(data)
