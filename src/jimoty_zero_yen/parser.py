from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import List, Optional

from .models import Listing

ISO_DATE_PATTERNS = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
)

_PRICE_RE = re.compile(r"(\d+)")
_ID_RE = re.compile(r"/(?:items/)?([\w-]+)$")
_SCRIPT_RE = re.compile(
    r"<script[^>]+type=\"application/ld\+json\"[^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class _ParsedItem:
    url: Optional[str] = None
    title: Optional[str] = None
    price_text: Optional[str] = None
    location: Optional[str] = None
    posted_at: Optional[str] = None
    thumbnail: Optional[str] = None


class _ListingHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: List[_ParsedItem] = []
        self._current: Optional[_ParsedItem] = None
        self._current_field: Optional[str] = None
        self._buffer: List[str] = []
        self._depth: int = 0

    # ------------------------------------------------------------------
    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attr_dict = {name: (value or "") for name, value in attrs}
        classes = set(attr_dict.get("class", "").split())
        data_cy = attr_dict.get("data-cy", "")

        is_item_tag = tag in {"li", "article", "div"}
        item_condition = (
            data_cy == "item"
            or any(cls.startswith("p-items__item") for cls in classes)
            or attr_dict.get("data-testid") == "item-card"
        )

        if self._current is None and is_item_tag and item_condition:
            self._current = _ParsedItem()
            self._depth = 1
            return

        if self._current is not None:
            self._depth += 1
            if tag == "a" and "href" in attr_dict:
                self._current.url = attr_dict["href"]
                self._start_capture("title")
            elif tag == "span":
                if (
                    data_cy == "item-price"
                    or "p-items-price" in classes
                    or "p-item__price" in classes
                ):
                    self._start_capture("price_text")
                elif (
                    data_cy == "item-region"
                    or "p-items-region" in classes
                    or "p-item__pref" in classes
                ):
                    self._start_capture("location")
            elif tag == "time":
                if "datetime" in attr_dict:
                    self._current.posted_at = attr_dict["datetime"]
            elif tag == "img" and "src" in attr_dict and not self._current.thumbnail:
                self._current.thumbnail = attr_dict["src"]

    # ------------------------------------------------------------------
    def handle_endtag(self, tag: str) -> None:
        if self._current is None:
            return

        if self._current_field and tag in {"a", "span"}:
            text = unescape("".join(self._buffer)).strip()
            if text:
                setattr(self._current, self._current_field, text)
            self._current_field = None
            self._buffer = []
            return

        self._depth -= 1
        if self._depth <= 0:
            self.items.append(self._current)
            self._current = None
            self._current_field = None
            self._buffer = []
            self._depth = 0

    # ------------------------------------------------------------------
    def handle_data(self, data: str) -> None:
        if self._current is not None and self._current_field:
            self._buffer.append(data)

    # ------------------------------------------------------------------
    def _start_capture(self, field: str) -> None:
        if getattr(self._current, field) is None:
            self._current_field = field
            self._buffer = []


class JimotyParser:
    """Parse Jimoty listing search pages into :class:`Listing` objects."""

    def parse_listings(self, html: str) -> List[Listing]:
        listings = self._parse_from_json_ld(html)
        if listings:
            return listings
        return self._parse_from_dom(html)

    # ------------------------------------------------------------------
    def _parse_from_json_ld(self, html: str) -> List[Listing]:
        listings: List[Listing] = []
        for match in _SCRIPT_RE.finditer(html):
            data = self._safe_load_json(match.group(1))
            if not data:
                continue
            listings.extend(self._parse_ld_data(data))
        return listings

    def _parse_ld_data(self, data) -> List[Listing]:
        if isinstance(data, list):
            listings: List[Listing] = []
            for item in data:
                listings.extend(self._parse_ld_data(item))
            return listings

        if not isinstance(data, dict):
            return []

        if data.get("@type") == "ItemList" and "itemListElement" in data:
            return [self._listing_from_ld_item(item) for item in data["itemListElement"] if item]

        if "@graph" in data and isinstance(data["@graph"], list):
            listings: List[Listing] = []
            for entry in data["@graph"]:
                listings.extend(self._parse_ld_data(entry))
            return listings

        if data.get("@type") in {"ListItem", "Product", "Offer"}:
            return [self._listing_from_ld_item(data)]

        return []

    def _listing_from_ld_item(self, data: dict) -> Listing:
        item = data.get("item") if isinstance(data.get("item"), dict) else data
        url = item.get("url") or item.get("@id") or data.get("url")
        title = item.get("name") or data.get("name") or ""

        offers = item.get("offers") or data.get("offers")
        if isinstance(offers, list):
            offer = offers[0] if offers else {}
        elif isinstance(offers, dict):
            offer = offers
        else:
            offer = {}

        price_raw = offer.get("price")
        price = self._parse_price(price_raw)

        listing_id = self._extract_listing_id(url) or title

        posted_at = None
        for key in ("datePosted", "availabilityStarts", "startDate"):
            value = item.get(key) or data.get(key)
            if isinstance(value, str):
                posted_at = self._parse_datetime(value)
                if posted_at:
                    break

        location = None
        for key in ("areaServed", "address", "availableAtOrFrom"):
            value = item.get(key) or data.get(key)
            if isinstance(value, dict):
                location = value.get("name") or value.get("addressLocality")
            elif isinstance(value, str):
                location = value
            if location:
                break

        thumb = None
        image = item.get("image") or data.get("image")
        if isinstance(image, list) and image:
            thumb = image[0]
        elif isinstance(image, str):
            thumb = image

        return Listing(
            id=str(listing_id),
            title=title.strip(),
            price=price,
            url=url,
            location=location,
            posted_at=posted_at,
            thumbnail_url=thumb,
        )

    # ------------------------------------------------------------------
    def _parse_from_dom(self, html: str) -> List[Listing]:
        parser = _ListingHTMLParser()
        parser.feed(html)
        listings: List[Listing] = []
        for item in parser.items:
            if not (item.url or item.title):
                continue
            listing_id = self._extract_listing_id(item.url) or (item.title or "")
            listings.append(
                Listing(
                    id=str(listing_id),
                    title=(item.title or "").strip(),
                    price=self._parse_price(item.price_text),
                    url=item.url or "",
                    location=item.location,
                    posted_at=self._parse_datetime(item.posted_at) if item.posted_at else None,
                    thumbnail_url=item.thumbnail,
                )
            )
        return listings

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_price(value) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        match = _PRICE_RE.search(str(value))
        if match:
            return int(match.group(1))
        return 0

    @staticmethod
    def _parse_datetime(value: str | None) -> datetime | None:
        if not value:
            return None
        for pattern in ISO_DATE_PATTERNS:
            try:
                return datetime.strptime(value, pattern)
            except ValueError:
                continue
        return None

    @staticmethod
    def _safe_load_json(raw: str | None):
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    @staticmethod
    def _extract_listing_id(url: str | None) -> str | None:
        if not url:
            return None
        match = _ID_RE.search(url)
        if match:
            return match.group(1)
        return None


__all__ = ["JimotyParser"]
