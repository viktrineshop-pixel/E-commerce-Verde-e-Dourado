import reflex as rx

import unittest
from unittest.mock import patch
from app.catalog_import import parse_csv, MAX_BYTES
from app.link_health import public_addresses, check_url


class ImportTests(unittest.TestCase):
    def test_bom_and_draft(self):
        rows = parse_csv(
            "product", b"\xef\xbb\xbftitle,status\nEditorial,draft\n"
        )
        self.assertEqual(rows[0]["title"], "Editorial")
        self.assertEqual(rows[0]["status"], "draft")

    def test_reject_evidence_status_and_shape(self):
        for kind, payload in [
            ("product", b"title,status\nItem,published\n"),
            ("offer", b"product_id,merchant_id,price_centavos\n1,1,100\n"),
            ("product", b"title,title\nA,B\n"),
            ("product", b"title\nA,B\n"),
            (
                "link",
                b"offer_id,destination_url,affiliate_url,validation_status\n1,https://example.com,https://example.com,valid\n",
            ),
        ]:
            with self.assertRaises(ValueError):
                parse_csv(kind, payload)

    def test_limits(self):
        with self.assertRaises(ValueError):
            parse_csv("product", b"x" * (MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            parse_csv("product", f"title\n{'Item\n' * 101}".encode())
        with self.assertRaises(ValueError):
            parse_csv("product", b"title\n\xff")

    def test_public_dns_all_addresses(self):
        def records(*addresses):
            return [(0, 0, 0, "", (address, 443)) for address in addresses]

        self.assertEqual(
            public_addresses(records("93.184.216.34")), ["93.184.216.34"]
        )
        for address in (
            "127.0.0.1",
            "10.0.0.1",
            "169.254.169.254",
            "::1",
            "::ffff:93.184.216.34",
            "224.0.0.1",
        ):
            with self.assertRaises(ValueError):
                public_addresses(records("93.184.216.34", address))


class NetworkTests(unittest.IsolatedAsyncioTestCase):
    async def test_private_dns_prevents_http_client(self):
        from unittest.mock import AsyncMock

        resolver = AsyncMock(
            return_value=[(0, 0, 0, "", ("169.254.169.254", 443))]
        )
        loop = __import__("asyncio").get_running_loop()
        with (
            patch.object(loop, "getaddrinfo", resolver),
            patch("app.link_health.httpx.AsyncClient") as client,
        ):
            result = await check_url(
                "https://merchant.com/item", ["merchant.com"]
            )
        self.assertFalse(result["healthy"])
        client.assert_not_called()

    async def test_arbitrary_host_blocked_before_dns(self):
        with patch("asyncio.get_running_loop") as loop:
            result = await check_url(
                "https://evil.example.com", ["merchant.com"]
            )
        self.assertFalse(result["healthy"])
        loop.assert_not_called()


if __name__ == "__main__":
    unittest.main()
