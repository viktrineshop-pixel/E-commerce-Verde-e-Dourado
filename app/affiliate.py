from urllib.parse import unquote, urlsplit


PARTNER_ROUTES: dict[str, str] = {
    "Amazon": "/lojas/amazon",
    "Mercado Livre": "/lojas/mercado-livre",
    "Shopee": "/lojas/shopee",
}


def safe_affiliate_url(value: str) -> bool:
    if not isinstance(value, str) or not value or len(value) > 2048:
        return False
    decoded = unquote(value)
    if (
        any(
            c.isspace() or ord(c) < 32 or 127 <= ord(c) <= 159
            for c in f"{value}{decoded}"
        )
        or "\\" in decoded
    ):
        return False
    try:
        parts = urlsplit(value)
        port = parts.port
        return (
            parts.scheme == "https"
            and bool(parts.netloc)
            and bool(parts.hostname)
            and not parts.netloc.endswith(":")
            and parts.username is None
            and parts.password is None
            and (port is None or 1 <= port <= 65535)
        )
    except ValueError:
        return False


def effective_destination(partner_name: str, affiliate_url: str) -> str:
    if safe_affiliate_url(affiliate_url):
        return affiliate_url
    return PARTNER_ROUTES.get(partner_name, "/")
