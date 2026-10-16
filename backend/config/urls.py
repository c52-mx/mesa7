from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from menu.views import branch_menu, branches

from .views import health

urlpatterns = [
    path("api/branches/", branches),
    path("api/branches/<int:branch_id>/menu/", branch_menu),
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/token/", TokenObtainPairView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
]
