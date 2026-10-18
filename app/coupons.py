import reflex as rx

import re
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from zoneinfo import ZoneInfo
from app.models import Coupon


COUPON_ZONE = ZoneInfo("America/Sao_Paulo")


def normalize_code(value: str) -> str:
    code = value.strip().upper()
    if not re.fullmatch(r"[A-Z0-9-]{1,100}", code):
        raise ValueError("Use de 1 a 100 letras, números ou hífen no código.")
    return code


def parse_coupon_value(kind: str, value: str) -> int:
    raw = value.strip()
    if kind == "percent":
        if not re.fullmatch(r"[0-9]{1,3}", raw) or not 1 <= int(raw) <= 100:
            raise ValueError("Informe um percentual inteiro de 1 a 100.")
        return int(raw)
    if kind != "fixed":
        raise ValueError("Escolha percentual ou valor fixo em BRL.")
    raw = raw.removeprefix("R$").strip()
    if not re.fullmatch(r"[0-9]{1,9}(?:[.,][0-9]{1,2})?", raw):
        raise ValueError(
            "Use um valor como 20,00, sem milhares e com até duas casas decimais."
        )
    cents = int(Decimal(raw.replace(",", ".")) * 100)
    if cents <= 0:
        raise ValueError("O desconto fixo deve ser maior que zero.")
    return cents


def coupon_expiration(value: str) -> datetime | None:
    if not value.strip():
        return None
    try:
        day = date.fromisoformat(value.strip())
        return datetime.combine(
            day + timedelta(days=1), time.min, COUPON_ZONE
        ).astimezone(timezone.utc)
    except (ValueError, OverflowError) as e:
        raise ValueError("Informe uma data válida para a validade.") from e


def expiration_day(value: datetime | None) -> str:
    if value is None:
        return ""
    aware = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return (
        (aware.astimezone(COUPON_ZONE) - timedelta(microseconds=1))
        .date()
        .isoformat()
    )


def coupon_discount(coupon: Coupon | None, subtotal: int, now: datetime) -> int:
    if coupon is None:
        raise ValueError("Cupom não encontrado. Confira o código informado.")
    if not coupon.active:
        raise ValueError(
            "Este cupom está desativado. Remova-o ou aplique outro código."
        )
    expires = coupon.expires_at
    if expires is not None:
        aware = (
            expires if expires.tzinfo else expires.replace(tzinfo=timezone.utc)
        )
        if aware <= now:
            raise ValueError(
                "Este cupom expirou. Remova-o ou aplique outro código."
            )
    if subtotal <= 0:
        raise ValueError(
            "Adicione produtos com valor à sacola antes de aplicar um cupom."
        )
    value = coupon.discount_value
    if (
        value <= 0
        or coupon.discount_kind not in ("percent", "fixed")
        or (coupon.discount_kind == "percent" and value > 100)
    ):
        raise ValueError("Este cupom não possui um desconto válido.")
    discount = (
        subtotal * value // 100 if coupon.discount_kind == "percent" else value
    )
    discount = min(subtotal, discount)
    if discount <= 0:
        raise ValueError(
            "O valor da sacola é insuficiente para gerar desconto com este cupom."
        )
    return discount
