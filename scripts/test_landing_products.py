import reflex as rx
import struct
import unittest
from unittest.mock import AsyncMock, patch
from starlette.requests import Request
from app.landing_products import (
    normalize_slug,
    unique_slug,
    safe_landing_url,
    valid_media,
    landing_is_public,
    published_landing,
    serve_landing_media,
    MAX_FILE_BYTES,
)


class LandingValidationTests(unittest.TestCase):
    def test_slug_normalization(self):
        self.assertEqual(
            normalize_slug("  Câmera & Café — Premium! "), "camera-cafe-premium"
        )
        self.assertEqual(normalize_slug("123"), "produto-123")
        self.assertEqual(
            unique_slug("camera", {"camera", "camera-2"}), "camera-3"
        )
        self.assertLessEqual(len(unique_slug("a" * 250, {"a" * 250})), 250)
        for raw in ("", "!!!", "a" * 251):
            with self.assertRaises(ValueError):
                normalize_slug(raw)

    def test_https_destination(self):
        for url in (
            "https://www.amazon.com.br/dp/ABC?tag=original-20",
            "https://loja.example.com/produto#detalhes",
            "https://8.8.8.8/item",
        ):
            self.assertTrue(safe_landing_url(url), url)
        for url in (
            "javascript:alert(1)",
            "http://example.com",
            "https://user:pass@example.com",
            "https://localhost",
            "https://shop.localhost/item",
            "https://127.0.0.1",
            "https://10.1.1.1",
            "https://192.168.0.1",
            "https://[::1]",
            "https://[::ffff:127.0.0.1]",
            "https://2130706433",
            "https://0x7f000001",
            "https://127.1",
            "https://example.com/%0a",
            "https://example.com/%250d",
            "https://example.com\\evil",
            "https://example.com:99999",
            "https://example.com/has space",
            "https://example.com/%7f",
        ):
            self.assertFalse(safe_landing_url(url), url)

    def test_signatures_and_mime(self):
        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            + struct.pack(">II", 1, 1)
            + b"\x08\x02\x00\x00\x00"
            + b"\x00" * 4
            + b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        jpeg = (
            b"\xff\xd8\xff\xe0"
            + b"\x00\x10JFIF\x00"
            + b"\x00" * 10
            + b"\xff\xd9"
        )
        webp = (
            b"RIFF"
            + struct.pack("<I", 16)
            + b"WEBPVP8 "
            + struct.pack("<I", 4)
            + b"\x00" * 4
        )
        mp4 = (
            struct.pack(">I", 24)
            + b"ftypisom\x00\x00\x00\x00isommp42"
            + struct.pack(">I", 8)
            + b"mdat"
        )
        webm = b"\x1a\x45\xdf\xa3\x87\x42\x82\x84webm\x18\x53\x80\x67\x80"
        samples = {
            "image/jpeg": jpeg,
            "image/png": png,
            "image/webp": webp,
            "video/mp4": mp4,
            "video/webm": webm,
        }
        for mime, data in samples.items():
            self.assertTrue(valid_media(data, mime), mime)
            self.assertFalse(valid_media(b"<script>alert(1)</script>", mime))
            self.assertFalse(valid_media(data, "text/html"))
        self.assertFalse(
            valid_media(
                b"<svg xmlns='http://www.w3.org/2000/svg'/>", "image/svg+xml"
            )
        )
        self.assertFalse(valid_media(b"\x89PNG\r\n\x1a\n", "image/png"))
        self.assertFalse(
            valid_media(b"\x1a\x45\xdf\xa3\x87\x42\x82\x84mkv!", "video/webm")
        )
        self.assertFalse(valid_media(b"x" * (MAX_FILE_BYTES + 1), "image/jpeg"))

    def test_drafts_and_invalid_links_are_never_public(self):
        self.assertFalse(
            landing_is_public(False, "https://example.com/item", "produto")
        )
        self.assertFalse(
            landing_is_public(True, "javascript:alert(1)", "produto")
        )
        self.assertFalse(
            landing_is_public(True, "https://example.com/item", "123")
        )
        self.assertFalse(
            landing_is_public(
                True, "https://example.com/item", "Não normalizado"
            )
        )
        self.assertTrue(
            landing_is_public(True, "https://example.com/item", "produto")
        )


class PublicDraftTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_lookup_filters_drafts(self):
        session = AsyncMock()
        result = unittest.mock.MagicMock()
        result.mappings.return_value.first.return_value = None
        session.execute.return_value = result
        context = unittest.mock.MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        with patch("app.landing_products.rx.asession", return_value=context):
            product = await published_landing("draft-product")
        self.assertEqual(product["id"], 0)
        self.assertEqual(product["media"], [])
        self.assertEqual(product["url"], "")
        self.assertIn(
            "published = true", str(session.execute.call_args.args[0])
        )

    async def test_draft_media_returns_404_and_is_not_cached(self):
        session = AsyncMock()
        result = unittest.mock.MagicMock()
        result.mappings.return_value.first.return_value = None
        session.execute.return_value = result
        context = unittest.mock.MagicMock()
        context.__aenter__ = AsyncMock(return_value=session)
        context.__aexit__ = AsyncMock(return_value=False)
        request = Request(
            {
                "type": "http",
                "method": "GET",
                "path": "/media/prova-social/1",
                "headers": [],
                "path_params": {"media_id": "1"},
            }
        )
        with patch("app.landing_products.rx.asession", return_value=context):
            response = await serve_landing_media(request)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.headers["x-content-type-options"], "nosniff")
        self.assertIn(
            "p.published = true", str(session.execute.call_args.args[0])
        )


if __name__ == "__main__":
    unittest.main()
