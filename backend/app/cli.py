"""CLI: schedule sync and Mets seed (Typer)."""

from __future__ import annotations

from datetime import datetime, timezone

import typer

from app.adapters.mlb_statsapi import MlbStatsApiScheduleProvider
from app.db import SessionLocal
from app.seed_mets import ensure_mets_saved_search
from app.services.schedule_sync import sync_games

app = typer.Typer(no_args_is_help=True)
METS_MLB_ID = 121


@app.command()
def sync_schedule(
    team_id: int = METS_MLB_ID,
    year: int = 2026,
) -> None:
    """Fetch home games from MLB Stats API and upsert events."""
    start = datetime(year, 1, 1, tzinfo=timezone.utc)
    end = datetime(year, 12, 31, tzinfo=timezone.utc)
    provider = MlbStatsApiScheduleProvider()
    games = provider.fetch_home_games_sync(team_mlb_id=team_id, season_start=start, season_end=end)
    typer.echo(f"Fetched {len(games)} home games for team {team_id} ({year})")
    db = SessionLocal()
    try:
        n = sync_games(db, games)
        typer.echo(f"Upserted {n} event rows")
    finally:
        db.close()


@app.command()
def seed_mets() -> None:
    """Create saved search, sections, alert rule, and demo observations."""
    db = SessionLocal()
    try:
        ss = ensure_mets_saved_search(db)
        typer.echo(f"Saved search ready: {ss.id}")
    finally:
        db.close()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
