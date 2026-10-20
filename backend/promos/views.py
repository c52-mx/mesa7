from rest_framework.decorators import api_view
from rest_framework.response import Response

from tenants.api import resolve_tenant

from .models import Banner


@api_view(["GET"])
def banners(request):
    tenant = resolve_tenant(request)
    active = Banner.objects.for_tenant(tenant).filter(is_active=True)
    return Response(
        [{"id": b.pk, "title": b.title, "text": b.text, "image_url": b.image_url} for b in active]
    )
