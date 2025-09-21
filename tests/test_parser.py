from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path

from jimoty_zero_yen.parser import JimotyParser


class JimotyParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sample_html = Path("tests/data/sample_listings.html").read_text("utf-8")

    def test_parse_listings_prefers_json_ld(self) -> None:
        parser = JimotyParser()
        listings = parser.parse_listings(self.sample_html)

        self.assertEqual(len(listings), 2)
        first = listings[0]
        self.assertEqual(first.id, "article-abcd1")
        self.assertEqual(first.title, "無料ソファ")
        self.assertEqual(first.price, 0)
        self.assertEqual(first.location, "東京都")
        self.assertEqual(first.thumbnail_url, "https://images.example.com/sofa.jpg")
        self.assertEqual(first.posted_at, datetime(2024, 1, 4, 22, 0, tzinfo=timezone.utc))

    def test_parse_listings_from_dom_when_no_json_ld(self) -> None:
        parser = JimotyParser()
        html_without_ld = self.sample_html.replace("type=\"application/ld+json\"", "type=\"text/plain\"")
        listings = parser.parse_listings(html_without_ld)

        self.assertEqual(len(listings), 1)
        listing = listings[0]
        self.assertEqual(listing.id, "article-abcd3")
        self.assertEqual(listing.title, "炊飯器を無料で譲ります")
        self.assertEqual(listing.price, 0)
        self.assertEqual(listing.location, "北海道")
        self.assertEqual(listing.posted_at, datetime(2024, 1, 5, 1, 30, tzinfo=timezone.utc))


if __name__ == "__main__":
    unittest.main()
