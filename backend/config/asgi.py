import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from orders.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        # Sin AllowedHostsOriginValidator a propósito: las apps nativas no envían Origin y la
        # autenticación va por token en el primer mensaje (no hay cookies que robar).
        "websocket": URLRouter(websocket_urlpatterns),
    }
)
