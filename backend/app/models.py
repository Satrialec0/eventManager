from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class EventStatus(str, enum.Enum):
    scheduled = "scheduled"
    live = "live"
    final = "final"
    cancelled = "cancelled"
    postponed = "postponed"


class ListingSource(str, enum.Enum):
    manual = "manual"
    stubhub = "stubhub"
    seatgeek = "seatgeek"
    gametime = "gametime"


class OpponentTier(str, enum.Enum):
    rival = "rival"
    division = "division"
    interleague_star = "interleague_star"
    standard = "standard"


class NotificationKind(str, enum.Enum):
    email = "email"
    telegram = "telegram"
    log = "log"


class Venue(Base):
    __tablename__ = "venues"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_key: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    city: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    events: Mapped[list["Event"]] = relationship(back_populates="venue")
    section_groups: Mapped[list["SectionGroup"]] = relationship(back_populates="venue")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mlb_team_id: Mapped[Optional[int]] = mapped_column(Integer, unique=True, nullable=True)
    abbrev: Mapped[str] = mapped_column(String(8), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    home_events: Mapped[list["Event"]] = relationship(
        foreign_keys="Event.home_team_id", back_populates="home_team"
    )
    away_events: Mapped[list["Event"]] = relationship(
        foreign_keys="Event.away_team_id", back_populates="away_team"
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("mlb_game_pk", name="uq_events_mlb_game_pk"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mlb_game_pk: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id"), nullable=False)
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    away_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[EventStatus] = mapped_column(Enum(EventStatus), nullable=False, default=EventStatus.scheduled)
    opponent_tier: Mapped[Optional[OpponentTier]] = mapped_column(Enum(OpponentTier), nullable=True)

    venue: Mapped["Venue"] = relationship(back_populates="events")
    home_team: Mapped["Team"] = relationship(foreign_keys=[home_team_id], back_populates="home_events")
    away_team: Mapped["Team"] = relationship(foreign_keys=[away_team_id], back_populates="away_events")
    observations: Mapped[list["ListingObservation"]] = relationship(back_populates="event")


class SectionGroup(Base):
    __tablename__ = "section_groups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id"), nullable=False)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    venue: Mapped["Venue"] = relationship(back_populates="section_groups")
    observations: Mapped[list["ListingObservation"]] = relationship(back_populates="section")


class ListingObservation(Base):
    __tablename__ = "listing_observations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id"), nullable=False)
    section_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("section_groups.id"), nullable=False)
    source: Mapped[ListingSource] = mapped_column(Enum(ListingSource), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="USD")
    all_in_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    external_listing_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    event: Mapped["Event"] = relationship(back_populates="observations")
    section: Mapped["SectionGroup"] = relationship(back_populates="observations")


class SavedSearch(Base):
    __tablename__ = "saved_searches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    venue_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("venues.id"), nullable=False)
    home_team_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("teams.id"), nullable=False)
    season_year: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    venue: Mapped["Venue"] = relationship()
    home_team: Mapped["Team"] = relationship()
    sections: Mapped[list["SavedSearchSection"]] = relationship(
        back_populates="saved_search", cascade="all, delete-orphan"
    )
    alert_rules: Mapped[list["AlertRule"]] = relationship(
        back_populates="saved_search", cascade="all, delete-orphan"
    )


class SavedSearchSection(Base):
    __tablename__ = "saved_search_sections"

    saved_search_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("saved_searches.id", ondelete="CASCADE"), primary_key=True
    )
    section_group_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("section_groups.id", ondelete="CASCADE"), primary_key=True
    )

    saved_search: Mapped["SavedSearch"] = relationship(back_populates="sections")
    section_group: Mapped["SectionGroup"] = relationship()


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    saved_search_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("saved_searches.id", ondelete="CASCADE"))
    deal_pct_threshold: Mapped[Optional[float]] = mapped_column(Numeric(6, 4), nullable=True)
    max_price: Mapped[Optional[float]] = mapped_column(Numeric(12, 2), nullable=True)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_channel_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("notification_channels.id"), nullable=True
    )

    saved_search: Mapped["SavedSearch"] = relationship(back_populates="alert_rules")
    notification_channel: Mapped[Optional["NotificationChannel"]] = relationship(back_populates="alert_rules")
    fires: Mapped[list["AlertFire"]] = relationship(back_populates="alert_rule")


class NotificationChannel(Base):
    __tablename__ = "notification_channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    kind: Mapped[NotificationKind] = mapped_column(Enum(NotificationKind), nullable=False)
    label: Mapped[str] = mapped_column(String(128), nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    alert_rules: Mapped[list["AlertRule"]] = relationship(back_populates="notification_channel")


class AlertFire(Base):
    __tablename__ = "alert_fires"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_rule_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("alert_rules.id", ondelete="CASCADE"))
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    payload_summary: Mapped[str] = mapped_column(String(512), nullable=False)

    alert_rule: Mapped["AlertRule"] = relationship(back_populates="fires")
