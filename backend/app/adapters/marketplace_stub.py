"""Stub marketplace adapters — outbound calls blocked until compliance-matrix allows."""

from __future__ import annotations

from datetime import datetime, timezone

from app.adapters.marketplace import MarketplaceAdapter, MarketplaceListingSnapshot


class StubMarketplaceAdapter:
    """Raises if invoked; documents port for StubHub / SeatGeek / GameTime."""

    vendor: str

    def __init__(self, vendor: str) -> None:
        self.vendor = vendor

    async def fetch_listings(
        self,
        *,
        event_external_id: str,
        section_external_id: str | None = None,
    ) -> list[MarketplaceListingSnapshot]:
        raise RuntimeError(
            f"{self.vendor} adapter is disabled. Update docs/compliance-matrix.md and "
            f"docs/data-contract.md before enabling HTTP."
        )


def stubhub() -> MarketplaceAdapter:
    return StubMarketplaceAdapter("stubhub")  # type: ignore[return-value]


def seatgeek() -> MarketplaceAdapter:
    return StubMarketplaceAdapter("seatgeek")  # type: ignore[return-value]


def gametime() -> MarketplaceAdapter:
    return StubMarketplaceAdapter("gametime")  # type: ignore[return-value]
