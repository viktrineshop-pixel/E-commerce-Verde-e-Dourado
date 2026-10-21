import reflex as rx

import csv
import io
import re
from uuid import uuid4
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from app.discovery import (
    FIELDS,
    MODELS,
    blank,
    parse_fields,
    validate_record,
    audit,
    get_row,
    reconcile_publication,
)
from app.models import Offer, Merchant, AffiliateProgram

MAX_BYTES = 524288
MAX_ROWS = 100
KINDS = (
    "category",
    "merchant",
    "program",
    "product",
    "variant",
    "offer",
    "link",
)
REQUIRED = {
    "category": ("name",),
    "merchant": ("name",),
    "program": ("merchant_id", "code"),
    "product": ("title",),
    "variant": ("product_id", "variant_key"),
    "offer": ("product_id", "merchant_id"),
    "link": ("offer_id", "destination_url", "affiliate_url"),
}


def columns(kind: str) -> list[str]:
    if kind not in KINDS:
        raise ValueError("Tipo de importação não permitido.")
    return [
        name
        for name, _, _, _ in FIELDS[kind]
        if name not in ("provenance", "validation_error", "campaign_id")
    ]


def template(kind: str) -> str:
    return f"{','.join(columns(kind))}\n"


def parse_csv(kind: str, data: bytes) -> list[dict[str, str]]:
    allowed = columns(kind)
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Envie um CSV não vazio de até 512 KiB.")
    try:
        content = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as e:
        raise ValueError(
            "Codificação inválida: salve como CSV UTF-8 (BOM permitido)."
        ) from e
    if "\x00" in content:
        raise ValueError(
            "Arquivo contém caracteres NUL; exporte novamente como texto UTF-8."
        )
    reader = csv.DictReader(io.StringIO(content, newline=""), strict=True)
    headers = reader.fieldnames or []
    if not headers or len(headers) != len(set(headers)):
        raise ValueError("Cabeçalho ausente ou com colunas repetidas.")
    unknown = set(headers) - set(allowed)
    if unknown:
        raise ValueError(
            f"Colunas não permitidas: {', '.join(sorted(unknown))}. Use o modelo; preços, evidências, revisões e credenciais não são importáveis."
        )
    missing = set(REQUIRED[kind]) - set(headers)
    if missing:
        raise ValueError(
            f"Faltam colunas obrigatórias: {', '.join(sorted(missing))}."
        )
    rows: list[dict[str, str]] = []
    try:
        for number, raw in enumerate(reader, 2):
            if len(rows) >= MAX_ROWS:
                raise ValueError(
                    "Máximo de 100 registros por arquivo; divida em lotes."
                )
            if None in raw or any(value is None for value in raw.values()):
                raise ValueError(
                    f"Registro {number}: quantidade de células diferente do cabeçalho. Confira vírgulas e aspas."
                )
            values = blank(kind)
            values.update({key: value.strip() for key, value in raw.items()})
            if "status" in values and values["status"] != "draft":
                raise ValueError(
                    f"Registro {number}: status deve ser draft; ativação/publicação exige revisão separada."
                )
            if kind == "link" and values["validation_status"] != "pending":
                raise ValueError(
                    f"Registro {number}: validation_status deve ser pending; o CSV não verifica links."
                )
            if kind == "category" and values["active"] not in ("true", "false"):
                raise ValueError(
                    f"Registro {number}: active aceita somente true ou false."
                )
            rows.append(values)
    except csv.Error as e:
        raise ValueError(
            f"CSV malformado próximo à linha física {reader.line_num}: {e}."
        ) from e
    if not rows:
        raise ValueError(
            "O CSV contém apenas cabeçalho; inclua ao menos um registro."
        )
    return rows


async def validate_import_row(
    session,
    kind: str,
    fields: dict[str, str],
    actor: str,
    reason: str,
    commit: bool,
):
    if kind not in KINDS:
        raise ValueError("Tipo de importação não permitido.")
    if fields.get("status", "draft") != "draft" or (
        kind == "link" and fields.get("validation_status") != "pending"
    ):
        raise ValueError("Importação exige rascunho ou link pendente.")
    values = parse_fields(kind, fields)
    for name in REQUIRED[kind]:
        if values.get(name) in (None, ""):
            raise ValueError(f"{name}: campo obrigatório vazio.")
    for name, value in values.items():
        if isinstance(value, str) and re.search(
            r"<[^>]*>|[\x00-\x08\x0b\x0c\x0e-\x1f]", value
        ):
            raise ValueError(
                f"{name}: use texto simples, sem HTML ou controles."
            )
    model = MODELS[kind]
    row = model(
        **values,
        **({"sku": f"VK-{uuid4().hex.upper()}"} if kind == "product" else {}),
    )
    if commit:
        await session.flush()
        product_id = row.id
    with session.no_autoflush:
        await validate_record(
            session, kind, row, False, actor, reason, preview=not commit
        )
        if kind == "link":
            from app.discovery import safe_https

            offer = await get_row(session, Offer, row.offer_id)
            merchant = await get_row(session, Merchant, offer.merchant_id)
            allowed = list(merchant.allowed_domains or [])
            if offer.program_id:
                program = await get_row(
                    session, AffiliateProgram, offer.program_id
                )
                if program.merchant_id != merchant.id:
                    raise ValueError("O programa pertence a outra loja.")
                allowed.extend(program.tracking_domains or [])
            if not safe_https(
                row.destination_url, merchant.allowed_domains or []
            ) or not safe_https(row.affiliate_url, allowed):
                raise ValueError(
                    "URLs devem pertencer aos domínios autorizados da loja/programa desta oferta."
                )
        unique = {
            "category": ("slug",),
            "merchant": ("slug",),
            "program": ("merchant_id", "code"),
            "variant": ("product_id", "variant_key"),
            "link": ("offer_id",),
        }.get(kind, ())
        if unique:
            statement = select(model.id)
            for name in unique:
                statement = statement.where(
                    getattr(model, name) == getattr(row, name)
                )
            if commit:
                statement = statement.where(model.id != row.id)
            if await session.scalar(statement.limit(1)):
                raise ValueError(
                    f"Chave já existente ({', '.join(unique)}); importação somente insere, não sobrescreve."
                )
    if commit:
        session.add(row)
        await session.flush()
        product_id = (
            row.id if kind == "product" else getattr(row, "product_id", None)
        )
        if kind == "link":
            product_id = offer.product_id
        await audit(session, row, {}, actor, "csv_import", reason, product_id)
    return row


async def preview_import(
    kind: str, rows: list[dict[str, str]], actor: str
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    async with rx.asession() as session:
        for number, fields in enumerate(rows, 2):
            try:
                row = await validate_import_row(
                    session,
                    kind,
                    fields,
                    actor,
                    "Prévia CSV sem escrita",
                    False,
                )
                keys = {
                    "category": (row.slug,) if kind == "category" else (),
                    "merchant": (row.slug,) if kind == "merchant" else (),
                    "program": (row.merchant_id, row.code)
                    if kind == "program"
                    else (),
                    "variant": (row.product_id, row.variant_key)
                    if kind == "variant"
                    else (),
                    "link": (row.offer_id,) if kind == "link" else (),
                }
                key = str(keys.get(kind, ()))
                if key != "()" and key in seen:
                    raise ValueError(
                        "Chave repetida dentro do arquivo; remova a duplicata."
                    )
                seen.add(key)
            except ValueError as e:
                errors.append(f"Registro {number}: {e}")
        await session.rollback()
    return errors


async def commit_import(
    kind: str, rows: list[dict[str, str]], actor: str, reason: str
) -> list[int]:
    if not actor or not reason.strip() or len(reason) > 2000:
        raise ValueError(
            "Informe um motivo de até 2.000 caracteres e use uma identidade administrativa válida."
        )
    if kind not in KINDS or not 1 <= len(rows) <= MAX_ROWS:
        raise ValueError("Tipo/lote inválido; faça nova prévia.")
    ids: list[int] = []
    async with rx.asession() as session:
        async with session.begin():
            await session.execute(
                text("SELECT pg_advisory_xact_lock(71420932)")
            )
            for number, fields in enumerate(rows, 2):
                try:
                    row = await validate_import_row(
                        session,
                        kind,
                        fields,
                        actor,
                        f"CSV · registro {number} · {reason}",
                        True,
                    )
                    ids.append(row.id)
                except (ValueError, IntegrityError) as e:
                    raise ValueError(
                        f"Registro {number}: vínculo/chave inválido ou alterado após a prévia. {str(e) if isinstance(e, ValueError) else 'Conflito de chave; confira os IDs e identificadores.'} Todo o lote foi revertido."
                    ) from e
            await reconcile_publication(
                session, actor, f"Importação CSV · {reason}"
            )
    return ids
