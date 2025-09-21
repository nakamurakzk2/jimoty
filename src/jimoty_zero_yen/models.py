from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class Listing:
    """Structured representation of a Jimoty listing."""

    id: str
    title: str
    price: int
    url: str
    location: Optional[str] = None
    posted_at: Optional[datetime] = None
    thumbnail_url: Optional[str] = None

    @property
    def is_zero_yen(self) -> bool:
        """Return True if the listing is advertised as free."""

        return self.price == 0


__all__ = ["Listing"]
