from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from accounts.views import LoginView, RegisterView
from menu.views import branch_menu, branches

from .views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health),
    path("api/auth/register/", RegisterView.as_view()),
    path("api/auth/login/", LoginView.as_view()),
    path("api/auth/token/refresh/", TokenRefreshView.as_view()),
    path("api/branches/", branches),
    path("api/branches/<int:branch_id>/menu/", branch_menu),
]
