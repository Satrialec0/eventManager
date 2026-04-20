"""Upsert venues, teams, and events from ScheduleGame rows."""

from __future__ import annotations

import time
import uuid

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.adapters.schedule import ScheduleGame
from app.models import Event, EventStatus, Team, Venue


def _status_from_api(label: str) -> EventStatus:
    s = label.lower()
    if "final" in s or "game over" in s:
        return EventStatus.final
    if "live" in s or "progress" in s:
        return EventStatus.live
    if "postpon" in s:
        return EventStatus.postponed
    if "cancel" in s:
        return EventStatus.cancelled
    return EventStatus.scheduled


def _get_or_create_team(db: Session, mlb_id: int, client: httpx.Client) -> Team:
    existing = db.execute(select(Team).where(Team.mlb_team_id == mlb_id)).scalar_one_or_none()
    if existing:
        return existing
    time.sleep(0.25)  # data-contract pacing
    r = client.get(f"https://statsapi.mlb.com/api/v1/teams/{mlb_id}")
    r.raise_for_status()
    t = r.json().get("teams", [{}])[0]
    abbrev = t.get("abbreviation") or str(mlb_id)
    name = t.get("name") or abbrev
    team = Team(id=uuid.uuid4(), mlb_team_id=mlb_id, abbrev=abbrev, name=name)
    db.add(team)
    db.flush()
    return team


def _get_or_create_venue(
    db: Session,
    *,
    venue_mlb_id: int | None,
    venue_name: str | None,
    client: httpx.Client,
) -> Venue:
    key = f"mlb_venue_{venue_mlb_id}" if venue_mlb_id is not None else None
    if key:
        existing = db.execute(select(Venue).where(Venue.external_key == key)).scalar_one_or_none()
        if existing:
            return existing
    name = venue_name or "Unknown venue"
    venue = Venue(
        id=uuid.uuid4(),
        external_key=key,
        name=name,
        city=None,
        timezone=None,
    )
    db.add(venue)
    db.flush()
    return venue


def sync_games(db: Session, games: list[ScheduleGame]) -> int:
    """Upsert events by mlb_game_pk. Returns count of rows touched."""
    client = httpx.Client(timeout=30.0)
    try:
        count = 0
        for g in games:
            home = _get_or_create_team(db, g.home_team_mlb_id, client)
            away = _get_or_create_team(db, g.away_team_mlb_id, client)
            venue = _get_or_create_venue(
                db,
                venue_mlb_id=g.venue_mlb_id,
                venue_name=g.venue_name,
                client=client,
            )
            existing = db.execute(select(Event).where(Event.mlb_game_pk == g.external_game_pk)).scalar_one_or_none()
            status = _status_from_api(g.status)
            if existing:
                existing.starts_at = g.starts_at
                existing.status = status
                existing.venue_id = venue.id
                existing.home_team_id = home.id
                existing.away_team_id = away.id
            else:
                db.add(
                    Event(
                        id=uuid.uuid4(),
                        mlb_game_pk=g.external_game_pk,
                        venue_id=venue.id,
                        home_team_id=home.id,
                        away_team_id=away.id,
                        starts_at=g.starts_at,
                        status=status,
                    )
                )
            count += 1
        db.commit()
        return count
    finally:
        client.close()
