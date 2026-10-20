from django.contrib import admin

from tenants.admin import TenantAdminMixin, TenantInlineMixin

from .models import BranchProduct, Category, Option, OptionGroup, Product, ProductOptionGroup


class OptionInline(TenantInlineMixin, admin.TabularInline):
    model = Option
    extra = 2
    fields = ("name", "price_delta", "is_popular", "is_active", "position")


class ProductOptionGroupInline(TenantInlineMixin, admin.TabularInline):
    model = ProductOptionGroup
    extra = 1
    fields = ("group", "position")


@admin.register(Category)
class CategoryAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "position", "tenant")


@admin.register(Product)
class ProductAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "category", "price", "prep_time_minutes", "is_featured", "is_active")
    list_filter = ("category", "is_featured", "is_active")
    inlines = [ProductOptionGroupInline]


@admin.register(OptionGroup)
class OptionGroupAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Grupos reutilizables (Tamaño, Tipo de leche, Extras); se asignan a cada producto."""

    list_display = ("name", "min_select", "max_select", "tenant")
    inlines = [OptionInline]


@admin.register(BranchProduct)
class BranchProductAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("product", "branch", "is_available")
    list_filter = ("branch", "is_available")
