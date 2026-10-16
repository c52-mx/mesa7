from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LoginView, RegisterView, devices
from menu.views import branch_menu, branches

from orders.views import kds_orders, kds_set_status, order_detail, orders

from .views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/devices/", devices),
    path("api/branches/", branches),
    path("api/branches/<int:branch_id>/menu/", branch_menu),
    path("api/orders/", orders),
    path("api/orders/<int:order_id>/", order_detail),
    path("api/kds/orders/", kds_orders),
    path("api/kds/orders/<int:order_id>/status/", kds_set_status),
]
