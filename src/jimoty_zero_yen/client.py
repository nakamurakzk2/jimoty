from __future__ import annotations

import logging
from typing import Callable, List, Optional
from urllib import error, request
from urllib.parse import urlencode, urljoin

from .models import Listing
from .parser import JimotyParser

LOGGER = logging.getLogger(__name__)


class JimotyClient:
    """HTTP client that fetches Jimoty listings without external dependencies."""

    BASE_URL = "https://jmty.jp"
    SEARCH_PATH = "/all/sale"
    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    )

    def __init__(
        self,
        parser: Optional[JimotyParser] = None,
        timeout: int = 10,
        fetcher: Optional[Callable[[str], Optional[str]]] = None,
    ) -> None:
        self.parser = parser or JimotyParser()
        self.timeout = timeout
        self._fetcher = fetcher

    # ------------------------------------------------------------------
    def fetch_zero_yen_listings(self, pages: int = 1) -> List[Listing]:
        listings: List[Listing] = []
        for page in range(1, max(pages, 1) + 1):
            url = self._build_search_url(page=page)
            html = self._fetch(url)
            if not html:
                break
            page_listings = self.parser.parse_listings(html)
            listings.extend(page_listings)
            if not page_listings:
                break
        return listings

    # ------------------------------------------------------------------
    def _fetch(self, url: str) -> Optional[str]:
        if self._fetcher:
            return self._fetcher(url)

        req = request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with request.urlopen(req, timeout=self.timeout) as response:
                encoding = response.headers.get_content_charset() or "utf-8"
                return response.read().decode(encoding, errors="replace")
        except (error.URLError, error.HTTPError) as exc:  # pragma: no cover - logging only
            LOGGER.warning("Failed to fetch Jimoty listings: %s", exc)
            return None

    # ------------------------------------------------------------------
    def _build_search_url(self, page: int = 1) -> str:
        params = {
            "price": 0,
            "page": page,
            "st": "new",
        }
        return urljoin(self.BASE_URL, f"{self.SEARCH_PATH}?{urlencode(params)}")


__all__ = ["JimotyClient"]
