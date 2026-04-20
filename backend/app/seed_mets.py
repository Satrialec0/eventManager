"""Seed Mets home 2026 saved search, premium section placeholders, demo observations."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    AlertRule,
    Event,
    ListingObservation,
    ListingSource,
    NotificationChannel,
    NotificationKind,
    SavedSearch,
    SavedSearchSection,
    SectionGroup,
    Team,
    Venue,
)

METS_MLB_ID = 121
SEASON_YEAR = 2026
# Citi Field in MLB Stats API (do not use “first 2026 home game” — that is usually spring training elsewhere).
CITI_FIELD_EXTERNAL_KEY = "mlb_venue_3289"


def _citi_field_venue(db: Session) -> Venue:
    venue = db.execute(
        select(Venue).where(Venue.external_key == CITI_FIELD_EXTERNAL_KEY)
    ).scalar_one_or_none()
    if venue:
        return venue
    raise RuntimeError(
        "Citi Field venue row not found (expected external_key mlb_venue_3289). "
        "Run: python -m app.cli sync-schedule"
    )


def _reconcile_saved_search_to_citi(db: Session, ss: SavedSearch, citi: Venue) -> None:
    """If an older seed bound the search to a spring-training park, move it to Citi Field."""
    if ss.venue_id == citi.id:
        return
    section_ids = (
        db.execute(
            select(SavedSearchSection.section_group_id).where(SavedSearchSection.saved_search_id == ss.id)
        )
        .scalars()
        .all()
    )
    for sid in section_ids:
        sg = db.get(SectionGroup, sid)
        if sg is not None:
            sg.venue_id = citi.id
    ss.venue_id = citi.id


def ensure_mets_saved_search(db: Session) -> SavedSearch:
    mets = db.execute(select(Team).where(Team.mlb_team_id == METS_MLB_ID)).scalar_one_or_none()
    if not mets:
        raise RuntimeError("Run schedule sync first so Mets team exists.")

    citi = _citi_field_venue(db)

    existing = db.execute(select(SavedSearch).where(SavedSearch.name == "Mets home 2026")).scalar_one_or_none()
    if existing:
        _reconcile_saved_search_to_citi(db, existing, citi)
        db.commit()
        db.refresh(existing)
        return existing

    venue = citi

    sections = [
        SectionGroup(id=uuid.uuid4(), venue_id=venue.id, label="Delta Sky360 Club", sort_order=10),
        SectionGroup(id=uuid.uuid4(), venue_id=venue.id, label="Caesars Club / Premium", sort_order=20),
        SectionGroup(id=uuid.uuid4(), venue_id=venue.id, label="Field / Baseline Boxes", sort_order=30),
    ]
    for s in sections:
        db.add(s)

    ss = SavedSearch(
        id=uuid.uuid4(),
        name="Mets home 2026",
        venue_id=venue.id,
        home_team_id=mets.id,
        season_year=SEASON_YEAR,
        active=True,
    )
    db.add(ss)
    db.flush()
    for s in sections:
        db.add(SavedSearchSection(saved_search_id=ss.id, section_group_id=s.id))

    ch = NotificationChannel(
        id=uuid.uuid4(),
        kind=NotificationKind.log,
        label="local log",
        config={"path": "stdout"},
    )
    db.add(ch)
    db.flush()
    db.add(
        AlertRule(
            id=uuid.uuid4(),
            saved_search_id=ss.id,
            deal_pct_threshold=0.15,
            max_price=None,
            cooldown_seconds=3600,
            enabled=True,
            notification_channel_id=ch.id,
        )
    )

    # Demo observations for charting / deal score on first regular-season home game at Citi Field
    first = (
        db.execute(
            select(Event)
            .where(Event.home_team_id == mets.id, Event.venue_id == venue.id)
            .where(Event.starts_at >= datetime(SEASON_YEAR, 1, 1, tzinfo=timezone.utc))
            .order_by(Event.starts_at.asc())
            .limit(1)
        )
        .scalar_one()
    )
    sec = sections[0]
    base = datetime.now(timezone.utc) - timedelta(days=10)
    prices = [420, 410, 395, 360, 340, 330]
    for i, p in enumerate(prices):
        db.add(
            ListingObservation(
                id=uuid.uuid4(),
                event_id=first.id,
                section_id=sec.id,
                source=ListingSource.manual,
                observed_at=base + timedelta(days=i),
                currency="USD",
                all_in_price=p,
                quantity=2,
                notes="seed demo",
            )
        )

    db.commit()
    db.refresh(ss)
    return ss
