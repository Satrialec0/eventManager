from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ScheduleGame:
    """Normalized game row from a schedule provider."""

    external_game_pk: int
    starts_at: datetime
    home_team_mlb_id: int
    away_team_mlb_id: int
    venue_mlb_id: int | None
    venue_name: str | None
    status: str


@runtime_checkable
class ScheduleProvider(Protocol):
    """Sanctioned schedule ingestion (see docs/data-contract.md)."""

    source_id: str

    async def fetch_home_games(
        self,
        *,
        team_mlb_id: int,
        season_start: datetime,
        season_end: datetime,
    ) -> list[ScheduleGame]:
        ...
