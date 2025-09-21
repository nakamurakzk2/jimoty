from __future__ import annotations

import argparse
import json
from datetime import timezone
from pathlib import Path
from typing import Iterable

from .cache import ListingCache
from .client import JimotyClient
from .models import Listing


def _listing_to_dict(listing: Listing) -> dict:
    data = {
        "id": listing.id,
        "title": listing.title,
        "price": listing.price,
        "url": listing.url,
        "location": listing.location,
        "thumbnail_url": listing.thumbnail_url,
    }
    if listing.posted_at:
        data["posted_at"] = listing.posted_at.astimezone(timezone.utc).isoformat()
    return data


def collect_listings(pages: int, cache: ListingCache | None) -> list[Listing]:
    client = JimotyClient()
    listings = client.fetch_zero_yen_listings(pages=pages)
    if cache:
        return cache.filter_new(listings)
    return listings


def run_cli(args: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Collect new zero-yen listings from Jimoty")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch (default: 1)")
    parser.add_argument("--cache", type=Path, help="Path to cache file that tracks seen listings")
    parser.add_argument("--json", action="store_true", help="Output listings as JSON")

    parsed = parser.parse_args(args=args)

    cache = ListingCache(parsed.cache) if parsed.cache else None
    listings = collect_listings(parsed.pages, cache)

    if parsed.json:
        payload = [_listing_to_dict(listing) for listing in listings]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        for listing in listings:
            print(f"[{listing.id}] {listing.title} ({listing.location or 'エリア不明'}) -> {listing.url}")


if __name__ == "__main__":  # pragma: no cover
    run_cli()
