from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Set

from .models import Listing


class ListingCache:
    """Disk-backed cache that keeps track of seen listing identifiers."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._ids: Set[str] = set()
        self._load()

    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text("utf-8"))
        except json.JSONDecodeError:
            data = []
        if isinstance(data, list):
            self._ids = {str(item) for item in data}

    # ------------------------------------------------------------------
    def _flush(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(sorted(self._ids)), encoding="utf-8")

    # ------------------------------------------------------------------
    def seen(self, listing_id: str) -> bool:
        return listing_id in self._ids

    # ------------------------------------------------------------------
    def mark_seen(self, listing: Listing) -> bool:
        """Register a listing as seen and return True if it was new."""

        is_new = listing.id not in self._ids
        self._ids.add(listing.id)
        self._flush()
        return is_new

    # ------------------------------------------------------------------
    def filter_new(self, listings: Iterable[Listing]) -> list[Listing]:
        """Return only the listings that have not been seen before."""

        new_listings = []
        for listing in listings:
            if listing.id not in self._ids:
                new_listings.append(listing)
                self._ids.add(listing.id)
        if new_listings:
            self._flush()
        return new_listings


__all__ = ["ListingCache"]
