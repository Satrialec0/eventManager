from __future__ import annotations

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import (
    Event,
    ListingObservation,
    ListingSource,
    SavedSearch,
    SavedSearchSection,
    SectionGroup,
)
from app.scoring import compute_deal_score_v1
from app.schemas import DealScoreOut, EventOut, ObservationOut, SavedSearchOut, SeriesPoint

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/saved-searches", response_model=list[SavedSearchOut])
def list_saved_searches(db: Session = Depends(get_db)) -> list[SavedSearchOut]:
    rows = (
        db.execute(
            select(SavedSearch).options(
                joinedload(SavedSearch.venue),
                joinedload(SavedSearch.home_team),
            )
        )
        .scalars()
        .unique()
        .all()
    )
    return list(rows)


@router.get("/events", response_model=list[EventOut])
def list_events(
    saved_search_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[EventOut]:
    if saved_search_id is None:
        q = (
            select(Event)
            .options(
                joinedload(Event.venue),
                joinedload(Event.home_team),
                joinedload(Event.away_team),
            )
            .order_by(Event.starts_at.asc())
            .limit(200)
        )
        rows = db.execute(q).scalars().unique().all()
        return list(rows)

    ss = db.get(SavedSearch, saved_search_id)
    if not ss:
        raise HTTPException(404, "saved search not found")
    q = (
        select(Event)
        .where(Event.home_team_id == ss.home_team_id, Event.venue_id == ss.venue_id)
        .options(
            joinedload(Event.venue),
            joinedload(Event.home_team),
            joinedload(Event.away_team),
        )
        .order_by(Event.starts_at.asc())
    )
    rows = db.execute(q).scalars().unique().all()
    return [e for e in rows if e.starts_at.year == ss.season_year]


@router.get("/events/{event_id}/observations", response_model=list[ObservationOut])
def list_observations(
    event_id: uuid.UUID,
    section_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ObservationOut]:
    q = select(ListingObservation).where(ListingObservation.event_id == event_id)
    if section_id:
        q = q.where(ListingObservation.section_id == section_id)
    q = q.order_by(ListingObservation.observed_at.asc())
    rows = db.execute(q).scalars().all()
    out: list[ObservationOut] = []
    for o in rows:
        sec = db.get(SectionGroup, o.section_id)
        out.append(
            ObservationOut(
                id=o.id,
                observed_at=o.observed_at,
                source=o.source,
                all_in_price=float(o.all_in_price),
                currency=o.currency,
                quantity=o.quantity,
                section_label=sec.label if sec else None,
            )
        )
    return out


@router.get("/events/{event_id}/series", response_model=list[SeriesPoint])
def observation_series(
    event_id: uuid.UUID,
    section_id: uuid.UUID = Query(...),
    source: ListingSource = Query(default=ListingSource.manual),
    db: Session = Depends(get_db),
) -> list[SeriesPoint]:
    rows = (
        db.execute(
            select(ListingObservation)
            .where(
                ListingObservation.event_id == event_id,
                ListingObservation.section_id == section_id,
                ListingObservation.source == source,
            )
            .order_by(ListingObservation.observed_at.asc())
        )
        .scalars()
        .all()
    )
    return [
        SeriesPoint(observed_at=o.observed_at, all_in_price=float(o.all_in_price)) for o in rows
    ]


@router.get("/events/{event_id}/deal-scores", response_model=list[DealScoreOut])
def deal_scores(
    event_id: uuid.UUID,
    saved_search_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DealScoreOut]:
    section_ids: list[uuid.UUID] = []
    if saved_search_id:
        ss = db.get(SavedSearch, saved_search_id)
        if not ss:
            raise HTTPException(404, "saved search not found")
        links = db.execute(
            select(SavedSearchSection.section_group_id).where(
                SavedSearchSection.saved_search_id == ss.id
            )
        ).all()
        section_ids = [row[0] for row in links]
    if not section_ids:
        section_ids = [
            r[0]
            for r in db.execute(
                select(ListingObservation.section_id)
                .where(ListingObservation.event_id == event_id)
                .distinct()
            ).all()
        ]
    out: list[DealScoreOut] = []
    for sid in section_ids:
        sec = db.get(SectionGroup, sid)
        for src in (ListingSource.manual,):
            score = compute_deal_score_v1(db, event_id=event_id, section_id=sid, source=src)
            out.append(
                DealScoreOut(
                    section_id=sid,
                    section_label=sec.label if sec else None,
                    source=src,
                    p_best=score.p_best,
                    p_ref=score.p_ref,
                    deal_pct=score.deal_pct,
                )
            )
    return out
