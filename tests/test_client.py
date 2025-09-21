from __future__ import annotations

import unittest

from jimoty_zero_yen.client import JimotyClient
from jimoty_zero_yen.models import Listing


class JimotyClientTests(unittest.TestCase):
    def test_builds_search_url_with_params(self) -> None:
        client = JimotyClient(fetcher=lambda url: "")
        url = client._build_search_url(page=2)
        self.assertIn("price=0", url)
        self.assertIn("page=2", url)

    def test_fetches_until_empty_page(self) -> None:
        pages = []

        def fake_fetch(url: str) -> str:
            pages.append(url)
            if len(pages) == 1:
                return "<html></html>"
            return ""

        parser_call_order = []

        class FakeParser:
            def parse_listings(self, html: str):
                parser_call_order.append(html)
                if html:
                    return [Listing(id="1", title="", price=0, url="https://example.com/1")]
                return []

        client = JimotyClient(parser=FakeParser(), fetcher=fake_fetch)
        listings = client.fetch_zero_yen_listings(pages=3)

        self.assertEqual(len(listings), 1)
        self.assertEqual(len(pages), 2)
        self.assertEqual(len(parser_call_order), 1)


if __name__ == "__main__":
    unittest.main()
