"""Read-only MLB Stats API client (schedule). gated by docs/data-contract.md §1."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import httpx

from app.adapters.schedule import ScheduleGame, ScheduleProvider


class MlbStatsApiScheduleProvider(ScheduleProvider):
    source_id = "mlb_statsapi"
    base_url = "https://statsapi.mlb.com/api/v1"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def fetch_home_games_sync(
        self,
        *,
        team_mlb_id: int,
        season_start: datetime,
        season_end: datetime,
    ) -> list[ScheduleGame]:
        params = {
            "sportId": 1,
            "teamId": team_mlb_id,
            "startDate": season_start.date().isoformat(),
            "endDate": season_end.date().isoformat(),
            "hydrate": "team,venue",
        }
        url = f"{self.base_url}/schedule"
        own = self._client is None
        client = self._client or httpx.Client(timeout=30.0)
        try:
            time.sleep(0.25)
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        finally:
            if own:
                client.close()

        dates = data.get("dates") or []
        games: list[ScheduleGame] = []
        for d in dates:
            for g in d.get("games") or []:
                parsed = _parse_game(g, team_mlb_id)
                if parsed:
                    games.append(parsed)
        return games

    async def fetch_home_games(
        self,
        *,
        team_mlb_id: int,
        season_start: datetime,
        season_end: datetime,
    ) -> list[ScheduleGame]:
        return self.fetch_home_games_sync(
            team_mlb_id=team_mlb_id, season_start=season_start, season_end=season_end
        )


def _parse_game(raw: dict[str, Any], home_team_mlb_id: int) -> ScheduleGame | None:
    teams = raw.get("teams") or {}
    home = (teams.get("home") or {}).get("team") or {}
    away = (teams.get("away") or {}).get("team") or {}
    if int(home.get("id", 0)) != home_team_mlb_id:
        return None
    game_pk = int(raw["gamePk"])
    game_date = raw.get("gameDate")
    if not game_date:
        return None
    starts_at = datetime.fromisoformat(game_date.replace("Z", "+00:00"))
    if starts_at.tzinfo is None:
        starts_at = starts_at.replace(tzinfo=timezone.utc)
    venue = raw.get("venue") or {}
    venue_id = venue.get("id")
    venue_name = venue.get("name")
    status = (raw.get("status") or {}).get("detailedState") or "Scheduled"
    return ScheduleGame(
        external_game_pk=game_pk,
        starts_at=starts_at,
        home_team_mlb_id=int(home["id"]),
        away_team_mlb_id=int(away["id"]),
        venue_mlb_id=int(venue_id) if venue_id is not None else None,
        venue_name=venue_name,
        status=status,
    )
