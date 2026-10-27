import secrets
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Sum
from rest_framework.exceptions import NotFound, ValidationError

from .models import LoyaltyAccount, LoyaltyProgram, LoyaltyReward, LoyaltyTransaction

MAX_COUNTER_AMOUNT = Decimal("100000")


def active_program(tenant):
    """Programa vigente, o None si el negocio lo apagó o no lo ha configurado."""
    if not tenant.loyalty_enabled:
        return None
    return LoyaltyProgram.objects.for_tenant(tenant).filter(is_active=True).first()


def get_or_create_account(tenant, user):
    account = LoyaltyAccount.objects.for_tenant(tenant).filter(user=user).first()
    while account is None:
        code = "".join(str(secrets.randbelow(10)) for _ in range(12))
        try:
            with transaction.atomic():
                account = LoyaltyAccount.objects.create(tenant=tenant, user=user, member_code=code)
        except IntegrityError:
            # Código repetido o cuenta creada en paralelo: se vuelve a buscar o se reintenta.
            account = LoyaltyAccount.objects.for_tenant(tenant).filter(user=user).first()
    return account


def balance(account):
    return account.transactions.aggregate(total=Sum("points"))["total"] or 0


def award_for_order(order):
    """Suma los puntos de un pedido entregado (una sola vez por pedido)."""
    program = active_program(order.tenant)
    if program is None:
        return None
    points = int(order.total // program.spend_per_point)
    if points <= 0:
        return None
    account = get_or_create_account(order.tenant, order.customer)
    transaction_, _ = LoyaltyTransaction.objects.get_or_create(
        order=order,
        kind=LoyaltyTransaction.Kind.EARN,
        defaults={"tenant": order.tenant, "account": account, "points": points},
    )
    return transaction_


def build_summary(tenant, account, program):
    points = balance(account)
    rewards = [
        {
            "id": r.pk,
            "name": r.name,
            "points_required": r.points_required,
            "unlocked": points >= r.points_required,
        }
        for r in LoyaltyReward.objects.for_tenant(tenant).filter(is_active=True)
    ]
    upcoming = next((r for r in rewards if not r["unlocked"]), None)
    return {
        "member_code": account.member_code,
        "qr": f"mesa7:{tenant.slug}:{account.member_code}",
        "points": points,
        "spend_per_point": str(program.spend_per_point),
        "rewards": rewards,
        "next_reward": upcoming and {**upcoming, "missing": upcoming["points_required"] - points},
        "recent": [
            {"points": t.points, "kind": t.kind, "note": t.note, "created_at": t.created_at}
            for t in account.transactions.all()[:10]
        ],
    }


def summary(tenant, user):
    """Datos de la tarjeta para la app, o None si la lealtad está apagada."""
    program = active_program(tenant)
    if program is None:
        return None
    return build_summary(tenant, get_or_create_account(tenant, user), program)


# --- Caja (personal del negocio) -------------------------------------------------------------


def require_program(tenant):
    program = active_program(tenant)
    if program is None:
        raise NotFound("La lealtad no está activa en este negocio.")
    return program


def find_account(tenant, raw_code):
    """Busca la tarjeta por el código de 12 dígitos o por el texto completo del QR."""
    code = (raw_code or "").strip()
    if code.lower().startswith("mesa7:"):
        parts = code.split(":")
        if len(parts) != 3 or parts[1] != tenant.slug:
            raise ValidationError({"code": "Este QR es de otro negocio."})
        code = parts[2]
    code = code.replace(" ", "")
    account = LoyaltyAccount.objects.for_tenant(tenant).select_related("user").filter(member_code=code).first()
    if account is None:
        raise NotFound("No encontramos esa tarjeta.")
    return account


def customer_summary(tenant, account):
    data = build_summary(tenant, account, require_program(tenant))
    data["customer"] = account.user.full_name or account.user.email
    return data


@transaction.atomic
def redeem_reward(tenant, account, reward_id, staff):
    """Canjea una recompensa: descuenta sus puntos. El saldo se revisa con la cuenta bloqueada."""
    require_program(tenant)
    LoyaltyAccount.objects.select_for_update().get(pk=account.pk)
    reward = LoyaltyReward.objects.for_tenant(tenant).filter(pk=reward_id, is_active=True).first()
    if reward is None:
        raise ValidationError({"reward": "Recompensa no disponible."})
    if balance(account) < reward.points_required:
        raise ValidationError({"reward": "El cliente no tiene puntos suficientes."})
    return LoyaltyTransaction.objects.create(
        tenant=tenant,
        account=account,
        points=-reward.points_required,
        kind=LoyaltyTransaction.Kind.REDEEM,
        note=f"Canje: {reward.name}",
        staff=staff,
    )


@transaction.atomic
def earn_at_counter(tenant, account, amount, staff, reference=""):
    """Suma puntos por una compra pagada en el mostrador, con el mismo valor que los pedidos.

    `reference` es el folio del ticket en el POS del negocio; si se repite, se rechaza.
    """
    program = require_program(tenant)
    reference = (reference or "").strip()
    try:
        amount = Decimal(str(amount))
    except InvalidOperation:
        raise ValidationError({"amount": "Monto no válido."})
    if not amount.is_finite() or amount <= 0 or amount > MAX_COUNTER_AMOUNT:
        raise ValidationError({"amount": "Monto no válido."})
    points = int(amount // program.spend_per_point)
    if points <= 0:
        raise ValidationError({"amount": f"Se necesita al menos ${program.spend_per_point} para sumar un punto."})
    amount = amount.quantize(Decimal("0.01"))
    duplicate = ValidationError({"reference": "Ese ticket ya se registró."})
    if reference and LoyaltyTransaction.objects.for_tenant(tenant).filter(
        kind=LoyaltyTransaction.Kind.EARN, reference=reference
    ).exists():
        raise duplicate
    try:
        with transaction.atomic():
            return LoyaltyTransaction.objects.create(
                tenant=tenant,
                account=account,
                points=points,
                kind=LoyaltyTransaction.Kind.EARN,
                note=f"Compra en mostrador ${amount}",
                amount=amount,
                reference=reference,
                staff=staff,
            )
    except IntegrityError:  # el mismo folio llegó en paralelo
        raise duplicate


def counter_report(tenant, day):
    """Compras de mostrador registradas en `day` (fecha local), con totales por cajero."""
    purchases = list(
        LoyaltyTransaction.objects.for_tenant(tenant)
        .filter(kind=LoyaltyTransaction.Kind.EARN, amount__isnull=False, created_at__date=day)
        .select_related("account__user", "staff")
        .order_by("-created_at", "-id")
    )
    by_staff = {}
    for p in purchases:
        who = (p.staff.full_name or p.staff.email) if p.staff else "—"
        row = by_staff.setdefault(who, {"staff": who, "count": 0, "amount": Decimal("0")})
        row["count"] += 1
        row["amount"] += p.amount
    return {
        "date": day.isoformat(),
        "count": len(purchases),
        "amount": str(sum((p.amount for p in purchases), Decimal("0"))),
        "points": sum(p.points for p in purchases),
        "by_staff": [{**r, "amount": str(r["amount"])} for r in by_staff.values()],
        "purchases": [
            {
                "created_at": p.created_at,
                "customer": p.account.user.full_name or p.account.user.email,
                "amount": str(p.amount),
                "points": p.points,
                "reference": p.reference,
                "staff": (p.staff.full_name or p.staff.email) if p.staff else "—",
            }
            for p in purchases
        ],
    }
