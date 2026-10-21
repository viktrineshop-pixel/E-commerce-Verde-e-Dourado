import reflex as rx
import ipaddress
import logging
import re
import struct
import unicodedata
from typing import TypedDict
from urllib.parse import unquote, urlsplit
from sqlalchemy import text
from starlette.requests import Request
from starlette.responses import Response
from reflex.vars.base import VarData
from reflex.utils.imports import ImportVar

MAX_FILE_BYTES = 15 * 1024 * 1024
MAX_BATCH_BYTES = 40 * 1024 * 1024
MEDIA_TYPES = {
    "image/jpeg": "image",
    "image/png": "image",
    "image/webp": "image",
    "video/mp4": "video",
    "video/webm": "video",
}


class LandingMedia(TypedDict):
    id: int
    tipo: str
    content_type: str
    filename: str
    url: str


class LandingView(TypedDict):
    id: int
    nome: str
    descricao: str
    slug: str
    url: str
    published: bool
    media: list[LandingMedia]


def empty_landing() -> LandingView:
    return {
        "id": 0,
        "nome": "",
        "descricao": "",
        "slug": "",
        "url": "",
        "published": False,
        "media": [],
    }


def normalize_slug(value: str) -> str:
    if len(value) > 1000:
        raise ValueError("Slug muito longo.")
    ascii_name = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if not slug or len(slug) > 250:
        raise ValueError(
            "Use um slug de 1 a 250 caracteres, com letras e números."
        )
    if slug.isdigit():
        slug = f"produto-{slug}"
    if len(slug) > 250:
        raise ValueError("Slug muito longo.")
    return slug


def unique_slug(base: str, existing: set[str]) -> str:
    candidate = base
    suffix = 2
    while candidate in existing:
        tail = f"-{suffix}"
        candidate = f"{base[: 250 - len(tail)].rstrip('-')}{tail}"
        suffix += 1
    return candidate


def safe_landing_url(value: str) -> bool:
    if not value or len(value) > 2048 or not value.startswith("https://"):
        return False
    decoded = value
    for _ in range(4):
        decoded = unquote(decoded)
        if (
            any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in decoded)
            or "\\" in decoded
        ):
            return False
    try:
        parts = urlsplit(value)
        host = (parts.hostname or "").lower().rstrip(".")
        if (
            parts.scheme != "https"
            or not host
            or parts.username is not None
            or parts.password is not None
            or "%" in parts.netloc
        ):
            return False
        if parts.port is not None and not 1 <= parts.port <= 65535:
            return False
        if host == "localhost" or host.endswith(
            (".localhost", ".local", ".internal", ".test", ".invalid")
        ):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            # Reject legacy numeric host notation that browsers interpret as IPs.
            if re.fullmatch(
                r"(?:0x[0-9a-f]+|[0-9]+)(?:\.(?:0x[0-9a-f]+|[0-9]+))*", host
            ):
                return False
            labels = host.encode("idna").decode("ascii").split(".")
            return len(labels) >= 2 and all(
                re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
                for label in labels
            )
        return (
            address.is_global
            and not address.is_multicast
            and not address.is_unspecified
            and not (
                getattr(address, "ipv4_mapped", None)
                and not address.ipv4_mapped.is_global
            )
        )
    except (ValueError, UnicodeError):
        logging.exception("Unexpected error")
        return False


def valid_media(data: bytes, content_type: str) -> bool:
    if (
        content_type not in MEDIA_TYPES
        or not data
        or len(data) > MAX_FILE_BYTES
    ):
        return False
    if content_type == "image/jpeg":
        return (
            len(data) >= 12
            and data.startswith(b"\xff\xd8\xff")
            and data.endswith(b"\xff\xd9")
            and data[3] not in (0x00, 0xFF)
        )
    if content_type == "image/png":
        return (
            len(data) >= 45
            and data.startswith(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
            and data.endswith(b"\x00\x00\x00\x00IEND\xaeB`\x82")
            and int.from_bytes(data[16:20], "big") > 0
            and int.from_bytes(data[20:24], "big") > 0
        )
    if content_type == "image/webp":
        return (
            len(data) >= 20
            and data[:4] == b"RIFF"
            and data[8:12] == b"WEBP"
            and data[12:16] in (b"VP8 ", b"VP8L", b"VP8X")
            and int.from_bytes(data[4:8], "little") == len(data) - 8
        )
    if content_type == "video/mp4":
        if len(data) < 24 or data[4:8] != b"ftyp":
            return False
        size = struct.unpack(">I", data[:4])[0]
        if size < 16 or size > len(data) or size > 4096 or size % 4:
            return False
        brands = {data[8:12], *[data[i : i + 4] for i in range(16, size, 4)]}
        return bool(
            brands
            & {b"isom", b"iso2", b"mp41", b"mp42", b"avc1", b"M4V ", b"dash"}
        ) and (b"mdat" in data[size:] or b"moov" in data[size:])
    # EBML header must declare the WebM DocType, not merely Matroska/EBML.
    if not data.startswith(b"\x1a\x45\xdf\xa3") or len(data) < 16:
        return False
    first = data[4]
    width = next((n for n in range(1, 9) if first & (1 << (8 - n))), 0)
    if not width or len(data) < 5 + width:
        return False
    size = int.from_bytes(data[4 : 4 + width], "big") & ((1 << (7 * width)) - 1)
    end = 4 + width + size
    return (
        end <= len(data)
        and b"\x42\x82\x84webm" in data[4 + width : end]
        and b"\x18\x53\x80\x67" in data[end:]
    )


def landing_is_public(published: bool, url: str, slug: str) -> bool:
    try:
        return (
            published
            and safe_landing_url(url)
            and normalize_slug(slug) == slug
            and not slug.isdigit()
        )
    except ValueError:
        return False


def media_url(media_id: rx.Var[int]) -> rx.Var[str]:
    return rx.Var(
        _js_expr=f"`${{String(getBackendURL(env.UPLOAD)).replace(/\\/_upload\\/?$/, '')}}/media/prova-social/${{{media_id}}}`",
        _var_type=str,
        _var_data=VarData(
            imports={
                "$/utils/state": ["getBackendURL"],
                "$/env.json": [ImportVar(tag="env", is_default=True)],
            }
        ),
    )


async def published_landing(slug: str) -> LandingView:
    if not slug or len(slug) > 250 or normalize_slug(slug) != slug:
        return empty_landing()
    async with rx.asession() as session:
        row = (
            (
                await session.execute(
                    text(
                        "SELECT id, nome, descricao, slug, link_afiliado_original FROM produtos WHERE slug = :slug AND published = true LIMIT 1"
                    ),
                    {"slug": slug},
                )
            )
            .mappings()
            .first()
        )
        if row is None or not landing_is_public(
            True, row["link_afiliado_original"], row["slug"]
        ):
            return empty_landing()
        rows = (
            (
                await session.execute(
                    text(
                        "SELECT id, tipo, content_type, filename, url_ficheiro FROM media_prova_social WHERE produto_id = :id AND file_bytes IS NOT NULL ORDER BY position, id LIMIT 100"
                    ),
                    {"id": row["id"]},
                )
            )
            .mappings()
            .all()
        )
        media = [
            LandingMedia(
                id=m["id"],
                tipo=m["tipo"],
                content_type=m["content_type"],
                filename=m["filename"] or "Mídia do produto",
                url=m["url_ficheiro"],
            )
            for m in rows
            if MEDIA_TYPES.get(m["content_type"]) == m["tipo"]
            and m["url_ficheiro"] == f"/media/prova-social/{m['id']}"
        ]
        return LandingView(
            id=row["id"],
            nome=row["nome"],
            descricao=row["descricao"],
            slug=row["slug"],
            url=row["link_afiliado_original"],
            published=True,
            media=media,
        )


async def serve_landing_media(request: Request) -> Response:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
        "Referrer-Policy": "no-referrer",
    }
    raw = str(request.path_params.get("media_id", ""))
    if not re.fullmatch(r"[1-9][0-9]{0,9}", raw) or int(raw) > 2147483647:
        return Response(status_code=404, headers=headers)
    try:
        async with rx.asession() as session:
            row = (
                (
                    await session.execute(
                        text(
                            "SELECT m.file_bytes, m.content_type, m.tipo, m.url_ficheiro, p.link_afiliado_original, p.slug FROM media_prova_social m JOIN produtos p ON p.id = m.produto_id WHERE m.id = :id AND p.published = true AND m.file_bytes IS NOT NULL LIMIT 1"
                        ),
                        {"id": int(raw)},
                    )
                )
                .mappings()
                .first()
            )
        if (
            row is None
            or not landing_is_public(
                True, row["link_afiliado_original"], row["slug"]
            )
            or MEDIA_TYPES.get(row["content_type"]) != row["tipo"]
            or row["url_ficheiro"] != f"/media/prova-social/{raw}"
        ):
            return Response(status_code=404, headers=headers)
        data = bytes(row["file_bytes"])
        if not valid_media(data, row["content_type"]):
            return Response(status_code=404, headers=headers)
        headers["Content-Disposition"] = "inline"
        headers["Content-Security-Policy"] = "default-src 'none'; sandbox"
        # Never cache: an unpublication must apply to the next request.
        return Response(data, media_type=row["content_type"], headers=headers)
    except Exception as e:
        logging.exception(f"Error: {e}")
        return Response(status_code=503, headers=headers)
