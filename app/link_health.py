import reflex as rx

import asyncio
import ipaddress
import logging
import socket
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit
import httpx
from sqlalchemy import select, text
from app.discovery import (
    safe_https,
    get_row,
    audit,
    snapshot,
    reconcile_publication,
)
from app.models import Offer, AffiliateLink, Merchant, AffiliateProgram

BODY_CAP = 65536


def public_addresses(records: list[tuple]) -> list[str]:
    addresses = sorted({record[4][0] for record in records})
    if not addresses or any(
        not ipaddress.ip_address(value).is_global
        or ipaddress.ip_address(value).is_multicast
        or ipaddress.ip_address(value).ipv4_mapped is not None
        for value in addresses
        if ":" in value
    ):
        raise ValueError("DNS recusado: endereço não público ou mapeado.")
    if any(
        not ipaddress.ip_address(value).is_global
        or ipaddress.ip_address(value).is_multicast
        for value in addresses
    ):
        raise ValueError("DNS recusado: todos os endereços devem ser públicos.")
    return addresses


async def check_url(
    url: str, domains: list[str]
) -> dict[str, str | int | bool]:
    result: dict[str, str | int | bool] = {
        "url": url,
        "http_status": 0,
        "resolved_url": "",
        "error": "",
        "healthy": False,
        "method": "HEAD",
    }
    try:
        async with asyncio.timeout(15):
            if not safe_https(url, domains):
                raise ValueError(
                    "HTTPS/domínio não autorizado para esta oferta."
                )
            parts = urlsplit(url)
            host = parts.hostname or ""
            records = await asyncio.get_running_loop().getaddrinfo(
                host, 443, type=socket.SOCK_STREAM
            )
            addresses = public_addresses(records)
            address = addresses[0]
            authority = f"[{address}]" if ":" in address else address
            pinned = urlunsplit(
                ("https", authority, parts.path or "/", parts.query, "")
            )
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(5.0, connect=4.0),
                follow_redirects=False,
                trust_env=False,
                limits=httpx.Limits(
                    max_connections=1, max_keepalive_connections=0
                ),
            ) as client:
                for method in ("HEAD", "GET"):
                    headers = {
                        "Host": host,
                        "User-Agent": "Viktrine-LinkHealth/1.0",
                        "Accept-Encoding": "identity",
                    }
                    if method == "GET":
                        headers["Range"] = f"bytes=0-{BODY_CAP - 1}"
                    async with client.stream(
                        method,
                        pinned,
                        headers=headers,
                        extensions={"sni_hostname": host},
                    ) as response:
                        result["method"] = method
                        result["http_status"] = response.status_code
                        result["resolved_url"] = url
                        if method == "HEAD" and response.status_code in (
                            405,
                            501,
                        ):
                            continue
                        if 300 <= response.status_code < 400:
                            raise ValueError(
                                "Redirecionamento não seguido. Revise o destino e os domínios; nenhum hop foi acessado."
                            )
                        if not 200 <= response.status_code < 300:
                            raise ValueError(
                                f"HTTP {response.status_code}; revise bloqueio, expiração ou indisponibilidade."
                            )
                        if method == "GET":
                            count = 0
                            async for chunk in response.aiter_raw(
                                chunk_size=8192
                            ):
                                count += len(chunk)
                                if count > BODY_CAP:
                                    raise ValueError(
                                        "Resposta excede 64 KiB; checagem interrompida sem armazenar conteúdo."
                                    )
                        result["healthy"] = True
                        break
    except Exception as e:
        logging.exception(f"Error: {e}")
        result["error"] = (
            str(e)
            if isinstance(e, ValueError)
            else "Falha de DNS, TLS, conexão ou tempo limite; tente novamente."
        )
    return result


async def persisted_targets(session, offer_id: int):
    offer = await get_row(session, Offer, offer_id)
    link = await session.scalar(
        select(AffiliateLink)
        .where(AffiliateLink.offer_id == offer_id)
        .with_for_update()
    )
    if link is None:
        raise ValueError("Cadastre primeiro o link desta oferta.")
    merchant = await get_row(session, Merchant, offer.merchant_id)
    allowed = list(merchant.allowed_domains or [])
    if offer.program_id:
        program = await get_row(session, AffiliateProgram, offer.program_id)
        if program.merchant_id != merchant.id:
            raise ValueError("Programa não corresponde à loja da oferta.")
        allowed.extend(program.tracking_domains or [])
    targets = (
        (link.destination_url or "", list(merchant.allowed_domains or [])),
        (link.affiliate_url or "", allowed),
    )
    return offer, link, targets


async def verify_offer(offer_id: int, actor: str) -> str:
    if offer_id <= 0 or not actor:
        raise ValueError("Oferta/identidade inválida.")
    async with rx.asession() as session:
        _, link, targets = await persisted_targets(session, offer_id)
        version = link.updated_at.isoformat()
    results = [await check_url(url, domains) for url, domains in targets]
    async with rx.asession() as session:
        async with session.begin():
            await session.execute(
                text("SELECT pg_advisory_xact_lock(71420932)")
            )
            offer, link, current = await persisted_targets(session, offer_id)
            if current != targets or link.updated_at.isoformat() != version:
                raise ValueError(
                    "Link/domínios alterados durante a checagem; resultado descartado. Execute novamente."
                )
            before, offer_before = snapshot(link), snapshot(offer)
            now = datetime.now(timezone.utc)
            healthy = all(result["healthy"] for result in results)
            link.last_checked_at = now
            offer.last_checked_at = now
            link.http_status = int(results[-1]["http_status"]) or None
            link.resolved_url = str(results[-1]["resolved_url"]) or None
            link.validation_error = (
                " · ".join(
                    str(result["error"])
                    for result in results
                    if result["error"]
                )
                or None
            )
            link.validation_metadata = {
                **(link.validation_metadata or {}),
                "network_health": "healthy" if healthy else "failed",
                "network_check_performed": True,
                "checked_at": now.isoformat(),
                "redirects_followed": False,
                "http_checks": results,
            }
            if not healthy:
                link.validation_status = "invalid"
                link.validated_at = None
                link.validated_by_sub = None
            await audit(
                session,
                link,
                before,
                actor,
                "http_link_check",
                "Checagem HTTP dos URLs persistidos; não confirma item, preço ou venda",
                offer.product_id,
            )
            await audit(
                session,
                offer,
                offer_before,
                actor,
                "http_link_check",
                "Horário da checagem HTTP",
                offer.product_id,
            )
            await reconcile_publication(session, actor, "Checagem HTTP de link")
    return (
        "HTTP saudável nos dois URLs; não confirma o mesmo produto nem conversão. Revisão manual permanece necessária."
        if healthy
        else "Checagem falhou; link invalidado e publicações dependentes reavaliadas. Revise e cheque novamente."
    )
