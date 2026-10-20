from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers, status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from tenants.models import Membership

from .models import DeviceToken
from .serializers import LoginSerializer, RegisterSerializer, auth_payload

User = get_user_model()


class DeviceSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=200)
    platform = serializers.CharField(max_length=10, required=False, allow_blank=True)


@api_view(["POST", "DELETE"])
def devices(request):
    """Registra (POST) o quita (DELETE, al cerrar sesión) el token push del dispositivo."""
    serializer = DeviceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data
    if request.method == "DELETE":
        DeviceToken.objects.filter(user=request.user, token=data["token"]).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    # Si el dispositivo cambia de cuenta, el token pasa a la cuenta actual.
    DeviceToken.objects.update_or_create(
        token=data["token"], defaults={"user": request.user, "platform": data.get("platform", "")}
    )
    return Response(status=status.HTTP_204_NO_CONTENT)


class ProfileSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)


@api_view(["GET", "PATCH"])
def me(request):
    """Datos del usuario; el correo no se edita desde aquí."""
    user = request.user
    if request.method == "PATCH":
        serializer = ProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(user, field, value.strip())
        user.save(update_fields=list(serializer.validated_data))
    return Response({"email": user.email, "full_name": user.full_name, "phone": user.phone})


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
