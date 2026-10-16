from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from tenants.models import Membership

from .serializers import LoginSerializer, RegisterSerializer, auth_payload

User = get_user_model()


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class RegisterView(APIView):
    """Registra un cliente en un tenant.

    Si el email ya existe y la contraseña coincide, solo agrega la membresía al tenant
    (un mismo usuario puede ser cliente de varios negocios).
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "register"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = User.objects.filter(email=data["email"]).first()
        if user is None:
            try:
                validate_password(data["password"])
            except DjangoValidationError as exc:
                raise serializers.ValidationError({"password": list(exc.messages)})
            user = User.objects.create_user(
                data["email"],
                data["password"],
                full_name=data.get("full_name", ""),
                phone=data.get("phone", ""),
            )
        elif not user.check_password(data["password"]) or not user.is_active:
            raise serializers.ValidationError({"email": "No se pudo registrar con esos datos."})

        Membership.objects.get_or_create(
            user=user, tenant=data["tenant"], defaults={"role": Membership.Role.CUSTOMER}
        )
        return Response(auth_payload(user), status=status.HTTP_201_CREATED)
