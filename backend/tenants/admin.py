from django.contrib import admin

from .models import Branch, Membership, Tenant, TenantModel, user_tenant_ids


class TenantAdminMixin:
    """Un usuario staff solo ve y edita datos de sus tenants; el superusuario ve todo.

    Con un solo tenant, el campo tenant se oculta y se asigna solo.
    """

    def _tenant_ids(self, request):
        return None if request.user.is_superuser else user_tenant_ids(request.user)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        ids = self._tenant_ids(request)
        return qs if ids is None else qs.for_tenant_ids(ids)

    def get_exclude(self, request, obj=None):
        exclude = list(super().get_exclude(request, obj) or [])
        ids = self._tenant_ids(request)
        if ids is not None and len(ids) == 1:
            exclude.append("tenant")
        return exclude

    def save_model(self, request, obj, form, change):
        ids = self._tenant_ids(request)
        if ids is not None and len(ids) == 1:
            obj.tenant_id = ids[0]
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        ids = self._tenant_ids(request)
        if ids is not None:
            related = db_field.remote_field.model
            if related is Tenant:
                kwargs["queryset"] = Tenant.objects.filter(pk__in=ids)
            elif issubclass(related, TenantModel):
                kwargs["queryset"] = related.objects.for_tenant_ids(ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "primary_color", "secondary_color", "loyalty_enabled", "is_active")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "role")
    list_filter = ("tenant", "role")


@admin.register(Branch)
class BranchAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ("name", "tenant", "is_active")
