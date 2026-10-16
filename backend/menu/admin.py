from django.contrib import admin

from tenants.admin import TenantAdminMixin

from .models import BranchProduct, Category, Product


@admin.register(Category)
class CategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "position", "tenant")


@admin.register(Product)
class ProductAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "price", "prep_time_minutes", "is_active")
    list_filter = ("category", "is_active")


@admin.register(BranchProduct)
class BranchProductAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("product", "branch", "is_available")
    list_filter = ("branch", "is_available")
