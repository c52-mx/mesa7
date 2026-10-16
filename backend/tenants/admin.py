from django.contrib import admin

from .models import Branch, Membership, Tenant, get_tenant


class TenantAdminMixin:
    """Un usuario staff solo ve y edita datos de su tenant; el superusuario ve todo."""

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.for_tenant(get_tenant(request.user))

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        if not request.user.is_superuser:
            exclude.append("tenant")
        return exclude

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.tenant = get_tenant(request.user)
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        related = db_field.remote_field.model
        if not request.user.is_superuser and hasattr(related.objects, "for_tenant"):
            kwargs["queryset"] = related.objects.for_tenant(get_tenant(request.user))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role")
    list_filter = ("tenant", "role")


@admin.register(Branch)
class BranchAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active")
