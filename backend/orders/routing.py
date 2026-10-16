from django.urls import path

from .consumers import KdsConsumer, OrderConsumer

websocket_urlpatterns = [
    path("ws/orders/<int:order_id>/", OrderConsumer.as_asgi()),
    path("ws/kds/<int:branch_id>/", KdsConsumer.as_asgi()),
]
