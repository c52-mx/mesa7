from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from tenants.models import Tenant

User = get_user_model()


def memberships_payload(user):
    qs = user.memberships.filter(tenant__is_active=True).select_related("tenant")
    return [{"tenant": m.tenant.slug, "name": m.tenant.name, "role": m.role} for m in qs]


def auth_payload(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "memberships": memberships_payload(user),
    }


class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        attrs[self.username_field] = attrs[self.username_field].strip().lower()
        data = super().validate(attrs)
        data["memberships"] = memberships_payload(self.user)
        return data


class RegisterSerializer(serializers.Serializer):
    tenant = serializers.SlugRelatedField(
        slug_field="slug", queryset=Tenant.objects.filter(is_active=True)
    )
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)

    def validate_email(self, value):
        return value.strip().lower()
