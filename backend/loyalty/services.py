import secrets

from django.db import IntegrityError, transaction
from django.db.models import Sum

from .models import LoyaltyAccount, LoyaltyProgram, LoyaltyReward, LoyaltyTransaction


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


def summary(tenant, user):
    """Datos de la tarjeta para la app, o None si la lealtad está apagada."""
    program = active_program(tenant)
    if program is None:
        return None
    account = get_or_create_account(tenant, user)
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
