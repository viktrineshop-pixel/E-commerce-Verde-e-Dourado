import reflex as rx

import ipaddress
import json
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import unquote, urlsplit
from uuid import uuid4
from sqlalchemy import select, func, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import (
    Product,
    Category,
    Merchant,
    AffiliateProgram,
    ProductVariant,
    Offer,
    AffiliateLink,
    Campaign,
    CampaignOffer,
    PriceObservation,
    DuplicateReview,
    ProductAudit,
)
from app.states.admin_state import parse_brl, safe_image_url


MODELS = {
    "product": Product,
    "category": Category,
    "merchant": Merchant,
    "program": AffiliateProgram,
    "variant": ProductVariant,
    "offer": Offer,
    "link": AffiliateLink,
    "campaign": Campaign,
    "campaign_offer": CampaignOffer,
    "observation": PriceObservation,
    "duplicate": DuplicateReview,
    "audit": ProductAudit,
}
LABELS = {
    "product": "Produtos editoriais",
    "category": "Categorias",
    "merchant": "Lojas",
    "program": "Programas de afiliados",
    "variant": "Variantes",
    "offer": "Ofertas",
    "link": "Links por oferta",
    "campaign": "Campanhas",
    "campaign_offer": "Ofertas nas campanhas",
    "observation": "Observações de preço",
    "duplicate": "Revisão de duplicados",
    "audit": "Histórico de auditoria",
}
# name, label, control, options; these are editor definitions, not catalog data.
FIELDS = {
    "product": [
        ("title", "Título editorial", "text", ""),
        ("short_description", "Resumo editorial", "textarea", ""),
        ("description", "Descrição completa", "textarea", ""),
        ("brand", "Marca (opcional)", "text", ""),
        ("model", "Modelo (opcional)", "text", ""),
        ("gtin", "GTIN / EAN (opcional; dígitos com verificador)", "text", ""),
        ("category_id", "ID da categoria (opcional no rascunho)", "number", ""),
        ("image_url", "Imagem permanente HTTPS ou caminho local", "text", ""),
        ("attributes", "Atributos — objeto JSON (opcional)", "textarea", ""),
        ("provenance", "Proveniência — objeto JSON (opcional)", "textarea", ""),
        (
            "status",
            "Estado editorial",
            "select",
            "draft|in_review|published|archived",
        ),
    ],
    "category": [
        ("name", "Nome", "text", ""),
        ("slug", "Slug (normalizado ao salvar)", "text", ""),
        ("parent_id", "ID da categoria pai (vazio para raiz)", "number", ""),
        ("description", "Descrição", "textarea", ""),
        ("position", "Posição", "number", ""),
        ("active", "Disponibilidade", "select", "false|true"),
    ],
    "merchant": [
        ("name", "Nome da loja", "text", ""),
        ("slug", "Slug", "text", ""),
        ("website_url", "Site HTTPS", "text", ""),
        (
            "allowed_domains",
            "Domínios oficiais permitidos (um por linha; sem https://)",
            "textarea",
            "",
        ),
        ("logo_url", "Imagem do logo (opcional)", "text", ""),
        ("description", "Descrição", "textarea", ""),
        ("provenance", "Proveniência — objeto JSON", "textarea", ""),
        ("status", "Estado", "select", "draft|active|inactive"),
    ],
    "program": [
        ("merchant_id", "ID da loja", "number", ""),
        ("code", "Código do programa", "text", ""),
        ("name", "Nome", "text", ""),
        ("network", "Rede (opcional)", "text", ""),
        ("terms_url", "Termos HTTPS (opcional)", "text", ""),
        (
            "tracking_domains",
            "Domínios de tracking autorizados (um por linha)",
            "textarea",
            "",
        ),
        ("provenance", "Proveniência — objeto JSON", "textarea", ""),
        ("status", "Estado", "select", "draft|active|inactive"),
    ],
    "variant": [
        ("product_id", "ID do produto editorial", "number", ""),
        ("variant_key", "Chave da variante (normalizada)", "text", ""),
        ("title", "Título", "text", ""),
        ("sku", "Identificador SKU (opcional)", "text", ""),
        ("gtin", "GTIN / EAN (opcional)", "text", ""),
        ("attributes", "Atributos — objeto JSON", "textarea", ""),
        ("image_url", "Imagem permanente (opcional)", "text", ""),
        ("provenance", "Proveniência — objeto JSON", "textarea", ""),
        ("status", "Estado", "select", "draft|published|archived"),
    ],
    "offer": [
        ("product_id", "ID do produto editorial", "number", ""),
        ("merchant_id", "ID da loja", "number", ""),
        ("variant_id", "ID da variante deste produto (opcional)", "number", ""),
        ("program_id", "ID do programa desta loja (opcional)", "number", ""),
        ("external_id", "Identificador do item na loja (opcional)", "text", ""),
        ("provenance", "Proveniência — objeto JSON", "textarea", ""),
        (
            "status",
            "Estado da oferta",
            "select",
            "draft|published|unavailable|invalid|archived",
        ),
    ],
    "link": [
        ("offer_id", "ID da oferta (um único link por oferta)", "number", ""),
        ("destination_url", "Destino HTTPS do item na loja", "text", ""),
        (
            "affiliate_url",
            "URL HTTPS de afiliado para o MESMO item/oferta",
            "text",
            "",
        ),
        (
            "tracking_code",
            "Código de tracking (opcional; não é uma credencial)",
            "text",
            "",
        ),
        ("campaign_id", "ID da campanha (opcional)", "number", ""),
        ("expires_at", "Expiração (ISO 8601 com fuso; opcional)", "text", ""),
        (
            "validation_status",
            "Revisão do link",
            "select",
            "pending|valid|invalid|expired",
        ),
        ("validation_error", "Notas / motivo de invalidação", "textarea", ""),
    ],
    "campaign": [
        ("title", "Título", "text", ""),
        ("slug", "Slug", "text", ""),
        ("description", "Descrição", "textarea", ""),
        ("starts_at", "Início (ISO 8601 com fuso; opcional)", "text", ""),
        ("ends_at", "Fim (ISO 8601 com fuso; opcional)", "text", ""),
        ("status", "Estado", "select", "draft|published|archived"),
    ],
    "campaign_offer": [
        ("campaign_id", "ID da campanha", "number", ""),
        ("offer_id", "ID da oferta", "number", ""),
        ("position", "Posição na campanha", "number", ""),
    ],
    "observation": [
        ("offer_id", "ID da oferta observada", "number", ""),
        (
            "price_centavos",
            "Preço efetivamente observado em BRL (ex.: 129,90)",
            "text",
            "",
        ),
        ("source", "Fonte manual (ex.: página oficial consultada)", "text", ""),
        (
            "observed_at",
            "Momento da observação (ISO 8601 com fuso)",
            "text",
            "",
        ),
        ("evidence_url", "URL HTTPS da evidência do item na loja", "text", ""),
        (
            "provenance",
            "Evidência / contexto — objeto JSON (opcional)",
            "textarea",
            "",
        ),
    ],
    "duplicate": [
        (
            "status",
            "Decisão (sem mesclar registros)",
            "select",
            "pending|duplicate|distinct|dismissed",
        ),
        ("resolution_notes", "Justificativa da decisão", "textarea", ""),
    ],
    "audit": [],
}
STATUS_NAMES = {
    "draft": "Rascunho",
    "in_review": "Em revisão",
    "published": "Publicado",
    "archived": "Arquivado",
    "active": "Ativo",
    "inactive": "Inativo",
    "unavailable": "Indisponível",
    "invalid": "Inválido",
    "pending": "Pendente",
    "valid": "Válido · revisão manual",
    "expired": "Expirado",
    "duplicate": "Duplicado",
    "distinct": "Distinto",
    "dismissed": "Descartado",
    "true": "Ativa",
    "false": "Inativa",
}


def blank(kind: str) -> dict[str, str]:
    values = {name: "" for name, _, _, _ in FIELDS[kind]}
    for name, _, control, choices in FIELDS[kind]:
        if control == "select":
            values[name] = choices.split("|")[0]
    if "position" in values:
        values["position"] = "0"
    return values


def normalize_slug(value: str) -> str:
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not value or len(value) > 160:
        raise ValueError(
            "Slug/chave precisa conter letras ou números e ter até 160 caracteres."
        )
    return value


def normalize_gtin(value: str) -> str | None:
    if not value.strip():
        return None
    value = re.sub(r"[\s-]", "", value)
    if not re.fullmatch(r"\d{8}|\d{12}|\d{13}|\d{14}", value):
        raise ValueError("GTIN precisa ter 8, 12, 13 ou 14 dígitos.")
    check = (
        10
        - sum(
            int(c) * (3 if i % 2 == 0 else 1)
            for i, c in enumerate(reversed(value[:-1]))
        )
        % 10
    ) % 10
    if check != int(value[-1]):
        raise ValueError("Dígito verificador do GTIN inválido.")
    return value.zfill(14)


def safe_https(value: str, domains: list[str] | None = None) -> bool:
    try:
        decoded = value
        for _ in range(3):
            decoded = unquote(decoded)
        if (
            not value
            or len(value) > 2048
            or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in decoded)
            or "\\" in decoded
        ):
            return False
        url = urlsplit(value)
        host = (url.hostname or "").lower()
        if (
            url.scheme != "https"
            or not value.startswith("https://")
            or url.username is not None
            or url.password is not None
            or url.port not in (None, 443)
            or "%" in url.netloc
            or url.fragment
        ):
            return False
        if not re.fullmatch(
            r"(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}", host
        ):
            return False
        try:
            ipaddress.ip_address(host)
            return False
        except ValueError:
            pass
        if host.endswith(
            (".localhost", ".local", ".internal", ".test", ".invalid")
        ):
            return False
        return domains is None or any(
            host == d or host.endswith(f".{d}") for d in domains
        )
    except ValueError:
        return False


def domains_value(raw: str) -> list[str]:
    domains = sorted(
        set(
            part.strip().lower()
            for part in re.split(r"[\s,]+", raw)
            if part.strip()
        )
    )
    if len(domains) > 30 or any(
        not safe_https(f"https://{d}") for d in domains
    ):
        raise ValueError(
            "Informe até 30 domínios públicos completos, sem protocolo, caminho, porta ou curingas."
        )
    return domains


def date_value(raw: str) -> datetime | None:
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as e:
        raise ValueError(
            "Data inválida. Exemplo: 2026-03-10T14:30:00-03:00."
        ) from e
    if value.tzinfo is None:
        raise ValueError("Inclua o fuso horário na data (ex.: -03:00).")
    return value.astimezone(timezone.utc)


def json_value(raw: str) -> dict[str, object] | None:
    if not raw:
        return None
    try:
        value = json.loads(
            raw,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError("JSON não finito.")
            ),
        )
    except (ValueError, TypeError) as e:
        raise ValueError(
            'Use um objeto JSON válido, como {"cor": "azul"}.'
        ) from e
    if not isinstance(value, dict):
        raise ValueError("Atributos/proveniência precisam ser objetos JSON.")
    return value


def serialize(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (dict, list)):
        return json.loads(json.dumps(value, default=str))
    return value


def snapshot(row: object) -> dict[str, object]:
    return {
        c.name: serialize(getattr(row, c.name))
        for c in row.__table__.columns
        if c.name not in ("created_at", "updated_at")
    }


async def audit(
    session: AsyncSession,
    row: object,
    before: dict[str, object],
    actor: str,
    action: str,
    reason: str,
    product_id: int | None = None,
):
    await session.flush()
    after = snapshot(row)
    diff = {
        key: {"before": before.get(key), "after": value}
        for key, value in after.items()
        if before.get(key) != value
    }
    if diff:
        session.add(
            ProductAudit(
                product_id=product_id,
                actor_sub=actor,
                entity=row.__tablename__,
                entity_id=row.id,
                action=action,
                reason=reason,
                diff=diff,
            )
        )


async def get_row(session: AsyncSession, model: type, record_id: int | None):
    row = await session.scalar(
        select(model).where(model.id == record_id).with_for_update()
    )
    if row is None:
        raise ValueError(
            f"Registro relacionado não encontrado ({model.__tablename__}, ID {record_id})."
        )
    return row


async def active_category(session: AsyncSession, category_id: int | None):
    if not category_id:
        raise ValueError("Publicação exige uma categoria ativa.")
    seen: set[int] = set()
    while category_id:
        if category_id in seen:
            raise ValueError("Hierarquia de categorias contém um ciclo.")
        seen.add(category_id)
        category = await get_row(session, Category, category_id)
        if not category.active:
            raise ValueError(
                "A categoria e todos os seus ancestrais precisam estar ativos."
            )
        category_id = category.parent_id


async def validate_link(
    session: AsyncSession, link: AffiliateLink, offer: Offer
):
    if link.offer_id != offer.id:
        raise ValueError("O link precisa pertencer à mesma oferta.")
    merchant = await get_row(session, Merchant, offer.merchant_id)
    if merchant.status != "active":
        raise ValueError("A loja precisa estar ativa.")
    if not merchant.allowed_domains or not safe_https(
        link.destination_url or "", merchant.allowed_domains
    ):
        raise ValueError(
            "Destino deve ser HTTPS em um domínio oficial autorizado desta loja."
        )
    allowed = list(merchant.allowed_domains)
    if offer.program_id:
        program = await get_row(session, AffiliateProgram, offer.program_id)
        if program.merchant_id != merchant.id or program.status != "active":
            raise ValueError(
                "Programa deve estar ativo e pertencer à mesma loja da oferta."
            )
        allowed.extend(program.tracking_domains or [])
    if not safe_https(link.affiliate_url or "", allowed):
        raise ValueError(
            "URL de afiliado deve ser HTTPS em domínio da loja ou de tracking do programa desta oferta."
        )
    if link.expires_at and link.expires_at <= datetime.now(timezone.utc):
        raise ValueError(
            "O link expirou; corrija a data antes de validar/publicar."
        )
    if (
        link.validation_status != "valid"
        or not link.validated_at
        or not link.validated_by_sub
    ):
        raise ValueError(
            "O link exige revisão manual válida por administrador."
        )
    metadata = link.validation_metadata or {}
    if (
        metadata.get("same_offer_confirmed") is not True
        or metadata.get("review_kind") != "manual"
    ):
        raise ValueError(
            "Confirme manualmente que os dois URLs correspondem ao mesmo item/oferta."
        )
    if link.campaign_id:
        await get_row(session, Campaign, link.campaign_id)


async def validate_offer(session: AsyncSession, offer: Offer):
    product = await get_row(session, Product, offer.product_id)
    if product.status == "archived" or product.sku.startswith("DEMO-"):
        raise ValueError(
            "Ofertas de produto arquivado ou demonstrativo não podem ser publicadas."
        )
    await active_category(session, product.category_id)
    if offer.variant_id:
        variant = await get_row(session, ProductVariant, offer.variant_id)
        if variant.product_id != product.id or variant.status != "published":
            raise ValueError(
                "Variante precisa estar publicada e pertencer ao produto da oferta."
            )
    if (
        offer.price_centavos is None
        or not offer.source
        or not offer.observed_at
        or not offer.reviewed_at
        or not offer.reviewed_by_sub
    ):
        raise ValueError(
            "Registre uma observação real de preço e revise a oferta antes de publicar."
        )
    observation = await session.scalar(
        select(PriceObservation)
        .where(
            PriceObservation.offer_id == offer.id,
            PriceObservation.price_centavos == offer.price_centavos,
            PriceObservation.source == offer.source,
            PriceObservation.observed_at == offer.observed_at,
            PriceObservation.currency == offer.currency,
        )
        .limit(1)
    )
    if (
        observation is None
        or not observation.recorded_by_sub
        or not observation.evidence_url
    ):
        raise ValueError(
            "Preço, fonte e horário precisam corresponder a uma observação real desta oferta."
        )
    merchant = await get_row(session, Merchant, offer.merchant_id)
    if not safe_https(observation.evidence_url, merchant.allowed_domains or []):
        raise ValueError(
            "Evidência de preço deve estar em domínio autorizado da mesma loja."
        )
    link = await session.scalar(
        select(AffiliateLink)
        .where(AffiliateLink.offer_id == offer.id)
        .with_for_update()
    )
    if link is None:
        raise ValueError(
            "Cadastre e revise o link individual desta oferta antes de publicar."
        )
    await validate_link(session, link, offer)


async def validate_product(session: AsyncSession, product: Product):
    if product.sku.startswith("DEMO-"):
        raise ValueError(
            "Catálogo demonstrativo permanece rascunho; crie um produto editorial com dados reais."
        )
    if (
        not product.title.strip()
        or not product.description.strip()
        or not (product.short_description or "").strip()
    ):
        raise ValueError(
            "Publicação exige título, resumo e descrição editorial."
        )
    if any(
        re.search(r"<[^>]*>|[\x00-\x08\x0b\x0c\x0e-\x1f]", v)
        for v in (
            product.title,
            product.description,
            product.short_description or "",
        )
    ):
        raise ValueError(
            "Texto editorial deve ser texto simples, sem HTML ou controles."
        )
    if (
        not safe_image_url(product.image_url)
        or product.image_url.startswith(("/_upload", "/placeholder"))
        or (
            not product.image_url.startswith("/")
            and not safe_https(product.image_url)
        )
    ):
        raise ValueError(
            "Publicação exige imagem permanente segura; placeholder e upload temporário não são aceitos."
        )
    await active_category(session, product.category_id)
    if not product.reviewed_by_sub or not product.reviewed_at:
        raise ValueError("Confirme a revisão editorial por administrador.")
    pending = await session.scalar(
        select(DuplicateReview.id)
        .where(
            or_(
                DuplicateReview.product_id == product.id,
                DuplicateReview.candidate_product_id == product.id,
            ),
            DuplicateReview.status.in_(["pending", "duplicate"]),
        )
        .limit(1)
    )
    if pending:
        raise ValueError(
            "Resolva candidatos pendentes/duplicados antes da publicação (não há mesclagem automática)."
        )
    offers = (
        await session.scalars(
            select(Offer)
            .where(Offer.product_id == product.id, Offer.status == "published")
            .with_for_update()
        )
    ).all()
    for offer in offers:
        try:
            await validate_offer(session, offer)
            return
        except ValueError:
            continue
    raise ValueError(
        "Produto exige ao menos uma oferta publicada com preço observado, fonte, horário e link revisado da mesma oferta."
    )


def parse_fields(kind: str, fields: dict[str, str]) -> dict[str, object]:
    values: dict[str, object] = {}
    for name, label, control, choices in FIELDS[kind]:
        raw = fields.get(name, "").strip()
        if len(raw) > 10000:
            raise ValueError(f"{label}: limite de 10.000 caracteres.")
        column = MODELS[kind].__table__.c[name]
        limit = getattr(column.type, "length", None)
        if limit and name != "gtin" and len(raw) > limit:
            raise ValueError(f"{label}: limite de {limit} caracteres.")
        if control == "select" and raw not in choices.split("|"):
            raise ValueError(f"{label}: escolha um estado permitido.")
        if name.endswith("_id") or name == "position":
            if not raw and name != "position":
                values[name] = None
            elif (
                not re.fullmatch(r"\d{1,10}", raw)
                or int(raw) > 2147483647
                or (name.endswith("_id") and int(raw) < 1)
            ):
                raise ValueError(
                    f"{label}: informe um ID inteiro positivo / posição não negativa."
                )
            else:
                values[name] = int(raw)
        elif name == "active":
            values[name] = raw == "true"
        elif name in ("slug", "variant_key"):
            values[name] = normalize_slug(
                raw or fields.get("name", "") or fields.get("title", "")
            )
        elif name == "gtin":
            values[name] = normalize_gtin(raw)
        elif name in ("attributes", "provenance"):
            values[name] = json_value(raw)
        elif name in ("allowed_domains", "tracking_domains"):
            values[name] = domains_value(raw)
        elif name in ("starts_at", "ends_at", "expires_at", "observed_at"):
            values[name] = date_value(raw)
        elif name == "price_centavos":
            values[name] = parse_brl(raw)
        else:
            values[name] = raw or (None if column.nullable else "")
    return values


async def detect_duplicates(
    session: AsyncSession, product: Product, actor: str, reason: str
):
    variants = select(ProductVariant.gtin).where(
        ProductVariant.product_id == product.id,
        ProductVariant.gtin.is_not(None),
    )
    matches = [
        Product.gtin.in_(variants),
        Product.id.in_(
            select(ProductVariant.product_id).where(
                ProductVariant.gtin.in_(variants)
            )
        ),
    ]
    if product.gtin:
        matches.extend(
            [
                Product.gtin == product.gtin,
                Product.id.in_(
                    select(ProductVariant.product_id).where(
                        ProductVariant.gtin == product.gtin
                    )
                ),
            ]
        )
    if product.brand and product.model:
        matches.append(
            (
                func.lower(func.trim(Product.brand))
                == product.brand.strip().lower()
            )
            & (
                func.lower(func.trim(Product.model))
                == product.model.strip().lower()
            )
        )
    candidates = (
        await session.scalars(
            select(Product.id).where(Product.id != product.id, or_(*matches))
        )
    ).all()
    for candidate in candidates:
        low, high = sorted((product.id, candidate))
        review = await session.scalar(
            select(DuplicateReview)
            .where(
                DuplicateReview.product_id == low,
                DuplicateReview.candidate_product_id == high,
            )
            .with_for_update()
        )
        evidence = {
            "gtin": product.gtin,
            "brand": product.brand,
            "model": product.model,
            "trigger_product_id": product.id,
        }
        if review is None:
            review = DuplicateReview(
                product_id=low,
                candidate_product_id=high,
                detected_by_sub=actor,
                source="identifier_or_brand_model",
                evidence=evidence,
            )
            session.add(review)
            await audit(
                session,
                review,
                {},
                actor,
                "duplicate_candidate",
                reason,
                product.id,
            )
        elif review.evidence != evidence:
            before = snapshot(review)
            review.status = "pending"
            review.evidence = evidence
            review.reviewed_at = None
            review.reviewed_by_sub = None
            await audit(
                session,
                review,
                before,
                actor,
                "duplicate_recheck",
                reason,
                product.id,
            )


async def validate_record(
    session: AsyncSession,
    kind: str,
    row: object,
    reviewed: bool,
    actor: str,
    reason: str,
):
    now = datetime.now(timezone.utc)
    if kind == "product":
        if not row.title.strip():
            raise ValueError("Informe o título do produto, mesmo no rascunho.")
        if row.category_id:
            await get_row(session, Category, row.category_id)
            if row.status in ("in_review", "published"):
                await active_category(session, row.category_id)
        if row.image_url and (
            not safe_image_url(row.image_url)
            or row.image_url.startswith("/_upload")
        ):
            raise ValueError(
                "Imagem deve usar HTTPS ou caminho permanente seguro."
            )
        if row.sku.startswith("DEMO-") and row.status != "draft":
            raise ValueError(
                "Produto demonstrativo deve permanecer em rascunho."
            )
        row.reviewed_at = now if reviewed else None
        row.reviewed_by_sub = actor if reviewed else None
        await detect_duplicates(session, row, actor, reason)
        if row.status == "published":
            await validate_product(session, row)
    elif kind == "category":
        if not row.name.strip():
            raise ValueError("Informe o nome da categoria.")
        parent_id, seen = row.parent_id, {row.id}
        while parent_id:
            if parent_id in seen:
                raise ValueError(
                    "Categoria não pode ser descendente de si mesma."
                )
            seen.add(parent_id)
            parent = await get_row(session, Category, parent_id)
            if row.active and not parent.active:
                raise ValueError("Categoria ativa exige ancestrais ativos.")
            parent_id = parent.parent_id
    elif kind == "merchant":
        if not row.name.strip():
            raise ValueError("Informe o nome da loja.")
        if row.website_url and not safe_https(row.website_url):
            raise ValueError("Site da loja deve ser HTTPS público seguro.")
        if row.logo_url and not safe_image_url(row.logo_url):
            raise ValueError("Logo deve ser uma imagem segura.")
        if row.status == "active" and (
            not row.allowed_domains
            or not safe_https(row.website_url or "", row.allowed_domains)
        ):
            raise ValueError(
                "Loja ativa exige site HTTPS em seus domínios oficiais permitidos."
            )
    elif kind == "program":
        merchant = await get_row(session, Merchant, row.merchant_id)
        if not row.code.strip():
            raise ValueError("Informe o código do programa.")
        if row.status == "active" and merchant.status != "active":
            raise ValueError("Programa ativo exige loja ativa.")
        if row.terms_url and not safe_https(row.terms_url):
            raise ValueError("Termos devem usar HTTPS seguro.")
    elif kind == "variant":
        product = await get_row(session, Product, row.product_id)
        if row.image_url and (
            not safe_image_url(row.image_url)
            or row.image_url.startswith("/_upload")
        ):
            raise ValueError("Imagem da variante inválida.")
        if row.status == "published":
            if (
                not row.title
                or not row.attributes
                or product.status == "archived"
                or product.sku.startswith("DEMO-")
            ):
                raise ValueError(
                    "Variante publicada exige título, atributos e produto real não arquivado."
                )
            await active_category(session, product.category_id)
        await detect_duplicates(session, product, actor, reason)
    elif kind == "offer":
        product = await get_row(session, Product, row.product_id)
        merchant = await get_row(session, Merchant, row.merchant_id)
        if merchant.status != "active":
            raise ValueError("Escolha uma loja ativa para a oferta.")
        if row.variant_id:
            variant = await get_row(session, ProductVariant, row.variant_id)
            if variant.product_id != row.product_id:
                raise ValueError("A variante pertence a outro produto.")
        if row.program_id:
            program = await get_row(session, AffiliateProgram, row.program_id)
            if (
                program.merchant_id != row.merchant_id
                or program.status != "active"
            ):
                raise ValueError(
                    "Programa precisa estar ativo e pertencer à loja desta oferta."
                )
        row.reviewed_at = now if reviewed else None
        row.reviewed_by_sub = actor if reviewed else None
        if row.status == "published":
            await validate_offer(session, row)
    elif kind == "link":
        offer = await get_row(session, Offer, row.offer_id)
        if row.campaign_id:
            await get_row(session, Campaign, row.campaign_id)
        for url in (row.destination_url, row.affiliate_url):
            if url and not safe_https(url):
                raise ValueError(
                    "URLs do link precisam ser HTTPS públicas seguras, sem credenciais ou controles."
                )
        row.validated_at = (
            now if reviewed and row.validation_status == "valid" else None
        )
        row.validated_by_sub = actor if row.validated_at else None
        row.validation_metadata = {
            "review_kind": "manual",
            "same_offer_confirmed": bool(row.validated_at),
            "notes": reason,
            "network_check_performed": False,
        }
        if row.validation_status == "valid":
            await validate_link(session, row, offer)
    elif kind == "observation":
        offer = await get_row(session, Offer, row.offer_id)
        merchant = await get_row(session, Merchant, offer.merchant_id)
        if (
            merchant.status != "active"
            or not row.source
            or not row.observed_at
            or row.observed_at > now
            or not safe_https(
                row.evidence_url or "", merchant.allowed_domains or []
            )
        ):
            raise ValueError(
                "Observação exige loja ativa, preço, fonte, horário não futuro com fuso e evidência HTTPS da mesma loja."
            )
        if not reviewed:
            raise ValueError(
                "Confirme que o preço e o horário foram realmente observados na evidência fornecida."
            )
        row.recorded_by_sub = actor
        row.provenance = {
            **(row.provenance or {}),
            "record_kind": "manual_observation",
            "notes": reason,
            "automatic_verification": False,
        }
        # An older observation is historical evidence, not the new current price.
        if offer.observed_at is None or row.observed_at >= offer.observed_at:
            before = snapshot(offer)
            offer.price_centavos, offer.currency = (
                row.price_centavos,
                row.currency,
            )
            offer.source, offer.observed_at = row.source, row.observed_at
            offer.status = "draft"
            offer.reviewed_at = None
            offer.reviewed_by_sub = None
            await audit(
                session,
                offer,
                before,
                actor,
                "manual_price_update",
                reason,
                offer.product_id,
            )
    elif kind == "campaign":
        if not row.title.strip():
            raise ValueError("Informe o título da campanha.")
        if row.starts_at and row.ends_at and row.ends_at <= row.starts_at:
            raise ValueError("O fim deve ocorrer depois do início.")
        if row.status == "published":
            if row.ends_at and row.ends_at <= now:
                raise ValueError("Campanha encerrada não pode ser publicada.")
            links = (
                await session.scalars(
                    select(Offer)
                    .join(CampaignOffer, CampaignOffer.offer_id == Offer.id)
                    .where(CampaignOffer.campaign_id == row.id)
                )
            ).all()
            if not links:
                raise ValueError(
                    "Associe ao menos uma oferta antes de publicar a campanha."
                )
            for offer in links:
                if offer.status != "published":
                    raise ValueError(
                        "Todas as ofertas da campanha precisam estar publicadas."
                    )
                await validate_offer(session, offer)
    elif kind == "campaign_offer":
        campaign = await get_row(session, Campaign, row.campaign_id)
        offer = await get_row(session, Offer, row.offer_id)
        if campaign.status == "archived" or offer.status == "archived":
            raise ValueError("Campanha/oferta arquivada não aceita associação.")
        if campaign.status == "published":
            if offer.status != "published":
                raise ValueError("Campanha publicada exige oferta publicada.")
            await validate_offer(session, offer)
    elif kind == "duplicate":
        if row.status != "pending":
            if not reviewed or not row.resolution_notes:
                raise ValueError(
                    "Decisão exige confirmação manual e justificativa."
                )
            row.reviewed_at, row.reviewed_by_sub = now, actor
        else:
            row.reviewed_at, row.reviewed_by_sub = None, None


async def reconcile_publication(session: AsyncSession, actor: str, reason: str):
    # Only publication candidates are inspected; drafts and demo prices are never promoted.
    offers = await session.stream_scalars(
        select(Offer).where(Offer.status == "published").with_for_update()
    )
    async for offer in offers:
        try:
            await validate_offer(session, offer)
        except ValueError as e:
            before = snapshot(offer)
            offer.status = "draft"
            offer.reviewed_by_sub, offer.reviewed_at = None, None
            await audit(
                session,
                offer,
                before,
                actor,
                "publication_invalidated",
                f"{reason} · {e}",
                offer.product_id,
            )
    products = await session.stream_scalars(
        select(Product).where(Product.status == "published").with_for_update()
    )
    async for product in products:
        try:
            await validate_product(session, product)
        except ValueError as e:
            before = snapshot(product)
            product.status = "draft"
            product.reviewed_by_sub, product.reviewed_at = None, None
            await audit(
                session,
                product,
                before,
                actor,
                "publication_invalidated",
                f"{reason} · {e}",
                product.id,
            )
    campaigns = await session.stream_scalars(
        select(Campaign).where(Campaign.status == "published").with_for_update()
    )
    async for campaign in campaigns:
        try:
            await validate_record(
                session, "campaign", campaign, False, actor, reason
            )
        except ValueError as e:
            before = snapshot(campaign)
            campaign.status = "draft"
            await audit(
                session,
                campaign,
                before,
                actor,
                "publication_invalidated",
                f"{reason} · {e}",
            )


async def save_record(
    kind: str, record_id: int, fields: dict[str, str], expected: str, actor: str
) -> int:
    if (
        kind not in MODELS
        or kind in ("audit",)
        or (kind == "duplicate" and not record_id)
    ):
        raise ValueError("Operação indisponível.")
    reason = fields.get("reason", "").strip()
    if not reason or len(reason) > 2000:
        raise ValueError(
            "Informe o motivo / contexto da alteração (até 2.000 caracteres)."
        )
    if not actor or len(actor) > 255:
        raise ValueError("Identidade administrativa inválida.")
    values = parse_fields(kind, fields)
    required = {
        "product": ["title"],
        "category": ["name"],
        "merchant": ["name"],
        "program": ["merchant_id", "code"],
        "variant": ["product_id", "variant_key"],
        "offer": ["product_id", "merchant_id"],
        "link": ["offer_id"],
        "observation": ["offer_id", "source", "observed_at", "evidence_url"],
        "campaign": ["title"],
        "campaign_offer": ["campaign_id", "offer_id"],
    }
    for name in required.get(kind, []):
        if values.get(name) in (None, ""):
            raise ValueError(f"Campo obrigatório: {name}.")
    for name in (
        "title",
        "name",
        "description",
        "short_description",
        "brand",
        "model",
    ):
        value = values.get(name)
        if isinstance(value, str) and re.search(
            r"<[^>]*>|[\x00-\x08\x0b\x0c\x0e-\x1f]", value
        ):
            raise ValueError(
                f"{name}: use texto simples, sem HTML ou caracteres de controle."
            )
    if kind == "observation" and fields.get("reviewed") != "on":
        raise ValueError(
            "Confirme que o preço e horário foram realmente observados na evidência fornecida."
        )
    async with rx.asession() as session:
        async with session.begin():
            await session.execute(
                text("SELECT pg_advisory_xact_lock(71420932)")
            )
            if record_id:
                row = await get_row(session, MODELS[kind], record_id)
                if kind == "observation":
                    raise ValueError(
                        "Observações são imutáveis: registre uma nova evidência, sem reescrever o histórico."
                    )
                current_version = (
                    row.updated_at.isoformat()
                    if hasattr(row, "updated_at")
                    else json.dumps(snapshot(row), sort_keys=True, default=str)
                )
                if current_version != expected:
                    raise ValueError(
                        "Registro alterado em outra sessão. Reabra antes de salvar; seu formulário foi mantido."
                    )
                before = snapshot(row)
            else:
                row = MODELS[kind](
                    **(
                        {"sku": f"VK-{uuid4().hex.upper()}"}
                        if kind == "product"
                        else {}
                    )
                )
                session.add(row)
                before = {}
            # The relation of an existing child record is immutable: edit the child, not its owner.
            if record_id:
                owners = {
                    "offer": ["product_id", "merchant_id"],
                    "variant": ["product_id"],
                    "link": ["offer_id"],
                    "program": ["merchant_id"],
                    "campaign_offer": ["campaign_id", "offer_id"],
                }
                for name in owners.get(kind, []):
                    if getattr(row, name) != values[name]:
                        raise ValueError(
                            "Vínculo principal não pode mudar. Crie um registro separado para o novo vínculo."
                        )
            for name, value in values.items():
                setattr(row, name, value)
            # Flush in draft/pending first: constraints require review evidence on final transitions.
            desired = getattr(row, "status", None)
            desired_link = getattr(row, "validation_status", None)
            if desired == "published":
                row.status = "draft"
            if desired_link == "valid":
                row.validation_status = "pending"
            if kind == "duplicate" and desired != "pending":
                row.status = "pending"
            await session.flush()
            if desired is not None:
                row.status = desired
            if desired_link is not None:
                row.validation_status = desired_link
            with session.no_autoflush:
                await validate_record(
                    session,
                    kind,
                    row,
                    fields.get("reviewed") == "on",
                    actor,
                    reason,
                )
            product_id = (
                row.id
                if kind == "product"
                else getattr(row, "product_id", None)
            )
            if kind in ("link", "observation", "campaign_offer"):
                offer = await get_row(session, Offer, row.offer_id)
                product_id = offer.product_id
            await audit(
                session,
                row,
                before,
                actor,
                "update" if record_id else "create",
                reason,
                product_id,
            )
            await reconcile_publication(session, actor, reason)
            saved_id = row.id
    return saved_id


async def read_page(
    kind: str, page: int, query: str = "", status: str = "", product_id: int = 0
) -> tuple[list[dict[str, str]], int]:
    model = MODELS[kind]
    statement = select(model)
    title_column = next(
        (
            getattr(model, name)
            for name in ("title", "name", "code", "entity")
            if hasattr(model, name)
        ),
        None,
    )
    if query:
        if query.isdigit():
            statement = statement.where(model.id == int(query))
        elif title_column is not None:
            escaped = (
                query.replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )
            statement = statement.where(
                title_column.ilike(f"%{escaped}%", escape="\\")
            )
        else:
            raise ValueError("Neste painel a busca é pelo ID numérico.")
    if status:
        column = getattr(
            model, "status", getattr(model, "validation_status", None)
        )
        if kind == "category":
            if status not in ("active", "inactive"):
                raise ValueError(
                    "Categorias aceitam os filtros Ativo ou Inativo."
                )
            statement = statement.where(Category.active == (status == "active"))
        elif column is not None:
            statement = statement.where(column == status)
    if product_id:
        if kind == "product":
            statement = statement.where(Product.id == product_id)
        elif hasattr(model, "product_id"):
            statement = statement.where(model.product_id == product_id)
        elif kind in ("link", "observation", "campaign_offer"):
            statement = statement.where(
                model.offer_id.in_(
                    select(Offer.id).where(Offer.product_id == product_id)
                )
            )
    async with rx.asession() as session:
        total = int(
            await session.scalar(
                select(func.count()).select_from(statement.subquery())
            )
            or 0
        )
        page = min(max(1, page), max(1, (total + 14) // 15))
        rows = (
            await session.scalars(
                statement.order_by(model.id.desc())
                .offset((page - 1) * 15)
                .limit(15)
            )
        ).all()
        result = []
        for row in rows:
            title = next(
                (
                    str(getattr(row, name))
                    for name in ("title", "name", "code")
                    if getattr(row, name, None)
                ),
                f"{LABELS[kind]} #{row.id}",
            )
            state = getattr(
                row, "status", getattr(row, "validation_status", "")
            )
            if kind == "category":
                state = "active" if row.active else "inactive"
            relations = " · ".join(
                f"{name.removesuffix('_id')} #{getattr(row, name)}"
                for name in (
                    "product_id",
                    "candidate_product_id",
                    "merchant_id",
                    "program_id",
                    "variant_id",
                    "offer_id",
                    "campaign_id",
                    "parent_id",
                )
                if getattr(row, name, None)
            )
            details = relations
            if kind == "product":
                details = f"{row.sku} · {row.brand or 'Sem marca'} · {row.model or 'Sem modelo'} · categoria #{row.category_id or '—'}"
            if kind == "offer":
                price = (
                    "Sem preço observado"
                    if row.price_centavos is None
                    else f"BRL {row.price_centavos / 100:.2f} · {row.source or 'Sem fonte'} · {row.observed_at.isoformat() if row.observed_at else 'Sem horário'}"
                )
                details = f"{relations} · {price}"
            if kind == "observation":
                details = f"{relations} · BRL {row.price_centavos / 100:.2f} · {row.source} · {row.observed_at.isoformat()} · registro manual"
            if kind == "audit":
                title = f"{row.entity} #{row.entity_id} · {row.action}"
                details = f"{row.created_at.isoformat()} · responsável {row.actor_sub} · {row.reason or ''}"
            extra = json.dumps(
                row.diff
                if kind == "audit"
                else (row.evidence or {})
                if kind == "duplicate"
                else {},
                ensure_ascii=False,
                indent=2,
                default=str,
            )
            result.append(
                {
                    "id": str(row.id),
                    "title": title,
                    "status": STATUS_NAMES.get(state, state),
                    "details": details,
                    "extra": extra,
                    "demo": "true"
                    if kind == "product" and row.sku.startswith("DEMO-")
                    else "false",
                }
            )
    return result, total


async def read_editor(kind: str, record_id: int) -> tuple[dict[str, str], str]:
    async with rx.asession() as session:
        row = await get_row(session, MODELS[kind], record_id)
        values = blank(kind)
        for name in values:
            value = getattr(row, name)
            if isinstance(value, dict):
                values[name] = json.dumps(value, ensure_ascii=False, indent=2)
            elif isinstance(value, list):
                values[name] = "\n".join(value)
            elif isinstance(value, datetime):
                values[name] = value.isoformat()
            elif isinstance(value, bool):
                values[name] = "true" if value else "false"
            else:
                values[name] = "" if value is None else str(value)
        return values, row.updated_at.isoformat() if hasattr(
            row, "updated_at"
        ) else json.dumps(snapshot(row), sort_keys=True, default=str)
