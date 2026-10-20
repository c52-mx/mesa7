from django.contrib import admin

from tenants.admin import TenantAdminMixin

from .models import Banner


@admin.register(Banner)
class BannerAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("title", "position", "is_active", "tenant")
    list_editable = ("position", "is_active")
