import reflex as rx

from datetime import datetime
from typing import TypedDict
from sqlalchemy import text
from app.discovery import safe_https


class OfferView(TypedDict):
    id: int
    merchant: str
    price: str
    source: str
    observed: str
    updated: str
    checked: str
    comparison: str
    disclosure: str
    history: list[str]
    history_note: str
    terms: list[str]


class ProductView(TypedDict):
    id: int
    key: str
    title: str
    description: str
    category: str
    image_url: str
    brand_model: str
    variant: str
    currency: str
    updated: str
    offers: list[OfferView]


PUBLIC_CTE = r"""
WITH RECURSIVE active_categories AS (
    SELECT id, parent_id, name, name::text AS path, ARRAY[id] AS visited
    FROM categories WHERE active = true AND parent_id IS NULL
    UNION ALL
    SELECT c.id, c.parent_id, c.name, a.path || ' / ' || c.name, a.visited || c.id
    FROM categories c JOIN active_categories a ON c.parent_id = a.id
    WHERE c.active = true AND NOT c.id = ANY(a.visited)
), eligible AS (
    SELECT p.id AS product_id, p.title, p.short_description, p.description,
           p.brand, p.model, p.image_url, p.updated_at AS product_updated,
           c.id AS category_id, c.path AS category_path, c.visited,
           o.id AS offer_id, o.variant_id, v.title AS variant_title,
           v.image_url AS variant_image, o.currency, o.price_centavos,
           o.source, o.observed_at, o.updated_at AS offer_updated,
           o.last_checked_at, m.id AS merchant_id, m.name AS merchant,
           m.allowed_domains, ap.tracking_domains, l.affiliate_url,
           l.destination_url, l.validated_at, l.expires_at, l.campaign_id
    FROM products p
    JOIN active_categories c ON c.id = p.category_id
    JOIN offers o ON o.product_id = p.id
    JOIN merchants m ON m.id = o.merchant_id
    JOIN affiliate_links l ON l.offer_id = o.id
    LEFT JOIN product_variants v ON v.id = o.variant_id AND v.product_id = p.id
    LEFT JOIN affiliate_programs ap ON ap.id = o.program_id AND ap.merchant_id = m.id
    WHERE p.status = 'published' AND p.sku NOT LIKE 'DEMO-%'
      AND o.status = 'published' AND m.status = 'active'
      AND (o.variant_id IS NULL OR v.status = 'published')
      AND (o.program_id IS NULL OR ap.status = 'active')
            AND p.reviewed_at IS NOT NULL AND length(trim(p.reviewed_by_sub)) > 0
      AND o.price_centavos IS NOT NULL AND o.price_centavos >= 0
      AND length(trim(o.source)) > 0 AND o.observed_at <= CURRENT_TIMESTAMP
      AND o.reviewed_at IS NOT NULL AND length(trim(o.reviewed_by_sub)) > 0
      AND l.validation_status = 'valid' AND l.validated_at IS NOT NULL
      AND length(trim(l.validated_by_sub)) > 0
      AND l.validation_metadata ->> 'same_offer_confirmed' = 'true'
      AND l.validation_metadata ->> 'review_kind' = 'manual'
      AND (l.expires_at IS NULL OR l.expires_at > CURRENT_TIMESTAMP)
      AND l.destination_url ~ '^https://[a-z0-9.-]+(:[4][4][3])?(/|\?|$)'
      AND l.affiliate_url ~ '^https://[a-z0-9.-]+(:[4][4][3])?(/|\?|$)'
      AND l.destination_url !~* '[[:space:]\\#]|%0[0-9a-f]|%1[0-9a-f]|%20|%25|%5c|%7f'
      AND l.affiliate_url !~* '[[:space:]\\#]|%0[0-9a-f]|%1[0-9a-f]|%20|%25|%5c|%7f'
      AND EXISTS (
          SELECT 1 FROM json_array_elements_text(COALESCE(m.allowed_domains, '[]'::json)) d(domain)
          WHERE substring(l.destination_url FROM '^https://([^/:?]+)') = d.domain
             OR substring(l.destination_url FROM '^https://([^/:?]+)') LIKE '%.' || d.domain
      )
      AND EXISTS (
          SELECT 1 FROM (
              SELECT domain FROM json_array_elements_text(COALESCE(m.allowed_domains, '[]'::json)) d(domain)
              UNION ALL
              SELECT domain FROM json_array_elements_text(COALESCE(ap.tracking_domains, '[]'::json)) d(domain)
          ) domains
          WHERE substring(l.affiliate_url FROM '^https://([^/:?]+)') = domains.domain
             OR substring(l.affiliate_url FROM '^https://([^/:?]+)') LIKE '%.' || domains.domain
      )
      AND EXISTS (
          SELECT 1 FROM price_observations po
          WHERE po.offer_id = o.id AND po.price_centavos = o.price_centavos
            AND po.currency = o.currency AND po.source = o.source
            AND po.observed_at = o.observed_at AND length(trim(po.recorded_by_sub)) > 0
            AND po.evidence_url ~ '^https://[a-z0-9.-]+(:[4][4][3])?(/|\?|$)'
            AND po.evidence_url !~* '[[:space:]\\#]|%0[0-9a-f]|%1[0-9a-f]|%20|%25|%5c|%7f'
            AND EXISTS (
                SELECT 1 FROM json_array_elements_text(COALESCE(m.allowed_domains, '[]'::json)) d(domain)
                WHERE substring(po.evidence_url FROM '^https://([^/:?]+)') = d.domain
                   OR substring(po.evidence_url FROM '^https://([^/:?]+)') LIKE '%.' || d.domain
            )
      )
)
"""


def money(cents: int, currency: str) -> str:
    value = f"{cents / 100:,.2f}"
    formatted = value.replace(",", "|").replace(".", ",").replace("|", ".")
    return f"{'R$' if currency == 'BRL' else currency} {formatted}"


def timestamp(value: datetime | None) -> str:
    return value.isoformat() if value else "Não informado"


def group_rows(rows) -> list[ProductView]:
    groups: dict[tuple[int, int, str], ProductView] = {}
    prices: dict[tuple[int, int, str], list[int]] = {}
    for row in rows:
        key = (row["product_id"], row["variant_id"] or 0, row["currency"])
        prices.setdefault(key, []).append(row["price_centavos"])
    for row in rows:
        key = (row["product_id"], row["variant_id"] or 0, row["currency"])
        allowed = [
            *(row["allowed_domains"] or []),
            *(row["tracking_domains"] or []),
        ]
        if not safe_https(row["affiliate_url"], allowed) or not safe_https(
            row["destination_url"], row["allowed_domains"] or []
        ):
            continue
        if key not in groups:
            image = (
                row["variant_image"] or row["image_url"] or "/placeholder.svg"
            )
            if not (
                image.startswith("/") and not image.startswith("//")
            ) and not safe_https(image):
                image = "/placeholder.svg"
            groups[key] = ProductView(
                id=row["product_id"],
                key=f"{key[0]}-{key[1]}-{key[2]}",
                title=row["title"],
                description=row["short_description"] or row["description"],
                category=row["category_path"],
                image_url=image,
                brand_model=" · ".join(
                    v for v in (row["brand"], row["model"]) if v
                ),
                variant=row["variant_title"]
                or "Produto sem variante especificada",
                currency=row["currency"],
                updated=timestamp(row["product_updated"]),
                offers=[],
            )
        minimum = min(prices[key])
        comparison = "Única oferta elegível neste grupo"
        if len(prices[key]) >= 2:
            comparison = (
                "Menor preço observado neste grupo"
                if row["price_centavos"] == minimum
                else f"{money(row['price_centavos'] - minimum, row['currency'])} acima do menor observado"
            )
        groups[key]["offers"].append(
            OfferView(
                id=row["offer_id"],
                merchant=row["merchant"],
                price=money(row["price_centavos"], row["currency"]),
                source=row["source"],
                observed=timestamp(row["observed_at"]),
                updated=timestamp(row["offer_updated"]),
                checked=timestamp(row["validated_at"]),
                comparison=comparison,
                disclosure=f"Ao seguir para {row['merchant']}, a Viktrine pode receber comissão por este link de afiliado. Compra e condições são da loja externa; preço, frete e disponibilidade não são garantidos.",
                history=[],
                history_note="Histórico insuficiente: são necessárias pelo menos duas observações reais desta oferta e moeda.",
                terms=[],
            )
        )
    return list(groups.values())


async def catalog_page(
    search: str,
    category: str,
    merchant: str,
    minimum: int,
    maximum: int,
    sort: str,
    page: int,
):
    terms = search.split()
    params: dict[str, str | int] = {
        "category": category,
        "category_prefix": f"{category.replace(chr(92), chr(92) * 2).replace('%', chr(92) + '%').replace('_', chr(92) + '_')} / %",
        "merchant": merchant,
        "minimum": minimum,
        "maximum": maximum,
    }
    clauses = [
        "(:category = 'Todos' OR category_path = :category OR EXISTS (SELECT 1 FROM active_categories ancestor WHERE ancestor.path = :category AND ancestor.id = ANY(eligible.visited)))",
        "(:merchant = '' OR merchant = :merchant)",
        "(:minimum < 0 OR (currency = 'BRL' AND price_centavos >= :minimum))",
        "(:maximum < 0 OR (currency = 'BRL' AND price_centavos <= :maximum))",
    ]
    for i, term in enumerate(terms):
        params[f"term{i}"] = (
            f"%{term.replace(chr(92), chr(92) * 2).replace('%', chr(92) + '%').replace('_', chr(92) + '_')}%"
        )
        clauses.append(
            f"(title ILIKE :term{i} ESCAPE '\\' OR brand ILIKE :term{i} ESCAPE '\\' OR model ILIKE :term{i} ESCAPE '\\')"
        )
    where = " AND ".join(clauses)
    order = {
        "Menor preço": "currency, lowest ASC, product_id",
        "Maior preço": "currency, highest DESC, product_id",
        "Mais recentes": "newest DESC, product_id DESC",
    }.get(sort, "product_id DESC")
    async with rx.asession() as session:
        total = int(
            await session.scalar(
                text(
                    f"{PUBLIC_CTE} SELECT count(*) FROM (SELECT product_id, variant_id, currency FROM eligible WHERE {where} GROUP BY product_id, variant_id, currency) g"
                ),
                params,
            )
            or 0
        )
        page = min(max(1, page), max(1, (total + 11) // 12))
        params.update(offset=(page - 1) * 12)
        rows = (
            (
                await session.execute(
                    text(f"""{PUBLIC_CTE}, selected AS (
            SELECT product_id, variant_id, currency, min(price_centavos) AS lowest,
                   max(price_centavos) AS highest, max(observed_at) AS newest
            FROM eligible WHERE {where} GROUP BY product_id, variant_id, currency
            ORDER BY {order} LIMIT 12 OFFSET :offset
        ) SELECT e.* FROM eligible e JOIN selected s ON s.product_id = e.product_id
            AND COALESCE(s.variant_id, 0) = COALESCE(e.variant_id, 0) AND s.currency = e.currency
            WHERE (:merchant = '' OR e.merchant = :merchant)
            ORDER BY {order.replace("product_id", "s.product_id").replace("currency", "s.currency")}, e.price_centavos, e.offer_id
        """),
                    params,
                )
            )
            .mappings()
            .all()
        )
    return group_rows(rows), total, page


async def filter_options() -> tuple[list[str], list[str]]:
    async with rx.asession() as session:
        rows = (
            (
                await session.execute(
                    text(
                        f"{PUBLIC_CTE} SELECT 'category' AS kind, path AS value FROM active_categories UNION SELECT 'merchant', merchant FROM eligible ORDER BY kind, value"
                    )
                )
            )
            .mappings()
            .all()
        )
    return ["Todos", *(r["value"] for r in rows if r["kind"] == "category")], [
        r["value"] for r in rows if r["kind"] == "merchant"
    ]


async def product_detail(product_id: int) -> list[ProductView]:
    async with rx.asession() as session:
        rows = (
            (
                await session.execute(
                    text(
                        f"{PUBLIC_CTE} SELECT * FROM eligible WHERE product_id = :id ORDER BY variant_id NULLS FIRST, currency, price_centavos, offer_id"
                    ),
                    {"id": product_id},
                )
            )
            .mappings()
            .all()
        )
        groups = group_rows(rows)
        history = (
            (
                await session.execute(
                    text(f"""{PUBLIC_CTE}, observations AS (
            SELECT po.id, po.offer_id, po.currency, po.price_centavos, po.source, po.observed_at,
                   count(*) OVER (PARTITION BY po.offer_id, po.currency) AS count_rows,
                   row_number() OVER (PARTITION BY po.offer_id, po.currency ORDER BY po.observed_at DESC, po.id DESC) AS rank
            FROM price_observations po JOIN eligible e ON e.offer_id = po.offer_id AND e.currency = po.currency
            WHERE e.product_id = :id AND po.observed_at <= CURRENT_TIMESTAMP
              AND length(trim(po.recorded_by_sub)) > 0 AND length(trim(po.source)) > 0
              AND po.price_centavos IS NOT NULL
              AND po.evidence_url ~ '^https://[a-z0-9.-]+(:[4][4][3])?(/|\\?|$)'
              AND po.evidence_url !~* '[[:space:]\\\\#]|%0[0-9a-f]|%1[0-9a-f]|%20|%25|%5c|%7f'
              AND EXISTS (
                  SELECT 1 FROM json_array_elements_text(COALESCE(e.allowed_domains, '[]'::json)) d(domain)
                  WHERE substring(po.evidence_url FROM '^https://([^/:?]+)') = d.domain
                     OR substring(po.evidence_url FROM '^https://([^/:?]+)') LIKE '%.' || d.domain
              )
        ) SELECT * FROM observations WHERE count_rows >= 2 AND rank <= 100 ORDER BY observed_at, id
        """),
                    {"id": product_id},
                )
            )
            .mappings()
            .all()
        )
        campaigns = (
            (
                await session.execute(
                    text(f"""{PUBLIC_CTE}
            SELECT DISTINCT e.offer_id, c.title, c.description, c.starts_at, c.ends_at, c.updated_at
            FROM eligible e JOIN campaigns c ON c.id = e.campaign_id OR EXISTS (
                SELECT 1 FROM campaign_offers co WHERE co.campaign_id = c.id AND co.offer_id = e.offer_id)
            WHERE e.product_id = :id AND c.status = 'published'
              AND (c.starts_at IS NULL OR c.starts_at <= CURRENT_TIMESTAMP)
              AND (c.ends_at IS NULL OR c.ends_at > CURRENT_TIMESTAMP)
            ORDER BY e.offer_id, c.title LIMIT 200
        """),
                    {"id": product_id},
                )
            )
            .mappings()
            .all()
        )
    for group in groups:
        for offer in group["offers"]:
            observations = [r for r in history if r["offer_id"] == offer["id"]]
            offer["history"] = [
                f"{timestamp(r['observed_at'])} · {money(r['price_centavos'], r['currency'])} · Fonte: {r['source']}"
                for r in observations
            ]
            if observations:
                offer["history_note"] = (
                    "Observações persistidas desta oferta e moeda, em ordem cronológica; até 100 mais recentes. Não é monitoramento automático."
                )
            offer["terms"] = [
                f"{r['title']} · {r['description'] or 'Termos não informados'} · Início: {timestamp(r['starts_at'])} · Fim: {timestamp(r['ends_at'])} · Atualização: {timestamp(r['updated_at'])}. Informação editorial associada a esta oferta; confirme a aplicação na loja."
                for r in campaigns
                if r["offer_id"] == offer["id"]
            ]
    return groups


async def eligible_product(session, product_id: int) -> bool:
    return bool(
        await session.scalar(
            text(
                f"{PUBLIC_CTE} SELECT product_id FROM eligible WHERE product_id = :id LIMIT 1"
            ),
            {"id": product_id},
        )
    )
