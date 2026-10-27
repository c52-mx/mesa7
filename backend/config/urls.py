from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LoginView, RegisterView, devices, me
from loyalty.views import loyalty, staff_earn, staff_lookup, staff_redeem, staff_report
from promos.views import banners
from menu.views import branch_menu, branches

from tenants.api import tenant_branding
from orders.views import kds_mark_paid, kds_orders, kds_set_status, order_detail, orders

from .views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/tenants/<slug:slug>/", tenant_branding),
    path("api/devices/", devices),
    path("api/me/", me),
    path("api/loyalty/", loyalty),
    path("api/staff/loyalty/lookup/", staff_lookup),
    path("api/staff/loyalty/redeem/", staff_redeem),
    path("api/staff/loyalty/earn/", staff_earn),
    path("api/staff/loyalty/report/", staff_report),
    path("api/banners/", banners),
    path("api/branches/", branches),
    path("api/branches/<int:branch_id>/menu/", branch_menu),
    path("api/orders/", orders),
    path("api/orders/<int:order_id>/", order_detail),
    path("api/kds/orders/", kds_orders),
    path("api/kds/orders/<int:order_id>/status/", kds_set_status),
    path("api/kds/orders/<int:order_id>/paid/", kds_mark_paid),
]
