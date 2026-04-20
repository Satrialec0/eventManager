from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.models import EventStatus, ListingSource


class VenueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    external_key: str | None


class TeamOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    abbrev: str
    name: str
    mlb_team_id: int | None


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    mlb_game_pk: int | None
    starts_at: datetime
    status: EventStatus
    venue: VenueOut
    home_team: TeamOut
    away_team: TeamOut


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    observed_at: datetime
    source: ListingSource
    all_in_price: float
    currency: str
    quantity: int
    section_label: str | None = None


class SeriesPoint(BaseModel):
    observed_at: datetime
    all_in_price: float


class DealScoreOut(BaseModel):
    section_id: uuid.UUID
    section_label: str | None
    source: ListingSource
    p_best: float | None
    p_ref: float | None
    deal_pct: float | None


class SavedSearchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    season_year: int
    active: bool
    venue: VenueOut
    home_team: TeamOut
