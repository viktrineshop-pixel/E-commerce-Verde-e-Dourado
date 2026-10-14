import reflex as rx
from urllib.parse import unquote, urlsplit


PARTNER_ROUTES = {
    "Amazon": "/lojas/amazon",
    "Mercado Livre": "/lojas/mercado-livre",
    "Shopee": "/lojas/shopee",
}


def safe_affiliate_url(value: str) -> bool:
    if not value or len(value) > 2048:
        return False
    decoded = unquote(value)
    if (
        any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in decoded)
        or "\\" in decoded
    ):
        return False
    try:
        parts = urlsplit(value)
        port = parts.port
        hostname = parts.hostname
        return (
            value.lower().startswith("https://")
            and parts.scheme == "https"
            and bool(hostname)
            and bool(parts.netloc)
            and parts.username is None
            and parts.password is None
            and (port is None or 1 <= port <= 65535)
            and "%" not in parts.netloc
        )
    except ValueError:
        return False


def effective_destination(partner_name: str, affiliate_url: str) -> str:
    return (
        affiliate_url
        if safe_affiliate_url(affiliate_url)
        else PARTNER_ROUTES.get(partner_name, "/lojas/amazon")
    )
