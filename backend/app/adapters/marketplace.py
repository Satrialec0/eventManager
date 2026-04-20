from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class MarketplaceListingSnapshot:
    """Single listing observation candidate (before persistence rules)."""

    external_listing_id: str | None
    all_in_price: float
    quantity: int
    currency: str
    observed_at: datetime


@runtime_checkable
class MarketplaceAdapter(Protocol):
    vendor: str

    async def fetch_listings(
        self,
        *,
        event_external_id: str,
        section_external_id: str | None = None,
    ) -> list[MarketplaceListingSnapshot]:
        ...
