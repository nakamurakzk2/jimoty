from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from jimoty_zero_yen.cache import ListingCache
from jimoty_zero_yen.models import Listing


class ListingCacheTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.cache_path = Path(self.temp_dir.name) / "cache.json"

    def _listing(self, listing_id: str) -> Listing:
        return Listing(id=listing_id, title="", price=0, url=f"https://example.com/{listing_id}")

    def test_cache_persists_seen_listings(self) -> None:
        cache = ListingCache(self.cache_path)
        self.assertFalse(cache.seen("abc"))
        self.assertTrue(cache.mark_seen(self._listing("abc")))
        self.assertTrue(cache.seen("abc"))

        cache = ListingCache(self.cache_path)
        self.assertTrue(cache.seen("abc"))

    def test_cache_filters_new_entries(self) -> None:
        cache = ListingCache(self.cache_path)
        listings = [self._listing("a"), self._listing("b"), self._listing("c")]

        new_listings = cache.filter_new(listings)
        self.assertEqual([listing.id for listing in new_listings], ["a", "b", "c"])

        additional = [self._listing("b"), self._listing("d")]
        new_listings = cache.filter_new(additional)
        self.assertEqual([listing.id for listing in new_listings], ["d"])


if __name__ == "__main__":
    unittest.main()
