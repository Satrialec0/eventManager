"""Deal score v1 per docs/deal-score-spec.md."""

from __future__ import annotations

import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ListingObservation, ListingSource


@dataclass(frozen=True)
class DealScoreV1:
    p_best: float | None
    p_ref: float | None
    deal_pct: float | None


def _to_float(x: Decimal | float) -> float:
    if isinstance(x, Decimal):
        return float(x)
    return float(x)


def compute_deal_score_v1(
    db: Session,
    *,
    event_id: uuid.UUID,
    section_id: uuid.UUID,
    source: ListingSource,
    now: datetime | None = None,
) -> DealScoreV1:
    now = now or datetime.now(timezone.utc)
    window_best_end = now
    window_best_start = now - timedelta(days=7)
    window_ref_end = now
    window_ref_start = now - timedelta(days=14)

    obs = db.execute(
        select(ListingObservation)
        .where(
            ListingObservation.event_id == event_id,
            ListingObservation.section_id == section_id,
            ListingObservation.source == source,
            ListingObservation.observed_at >= window_ref_start,
            ListingObservation.observed_at <= window_ref_end,
        )
        .order_by(ListingObservation.observed_at.asc())
    ).scalars().all()

    if not obs:
        return DealScoreV1(None, None, None)

    # p_best: min price in last 7d
    recent = [o for o in obs if o.observed_at >= window_best_start]
    if not recent:
        recent = obs
    p_best = min(_to_float(o.all_in_price) for o in recent)

    # daily minima for p_ref (14d window)
    by_day: dict[str, list[float]] = {}
    for o in obs:
        day_key = o.observed_at.astimezone(timezone.utc).date().isoformat()
        price = _to_float(o.all_in_price)
        by_day.setdefault(day_key, []).append(price)
    daily_mins = [min(prices) for prices in by_day.values()]
    if len(daily_mins) < 1:
        p_ref = None
    else:
        p_ref = float(statistics.median(daily_mins))

    if p_ref is None or p_ref <= 0:
        return DealScoreV1(p_best, p_ref, None)
    deal_pct = (p_ref - p_best) / p_ref
    return DealScoreV1(p_best, p_ref, deal_pct)
