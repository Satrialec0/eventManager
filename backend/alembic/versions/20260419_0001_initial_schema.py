"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-19

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _enum(name: str, *values: str) -> postgresql.ENUM:
    e = postgresql.ENUM(*values, name=name, create_type=True)
    e.create(op.get_bind(), checkfirst=True)
    return postgresql.ENUM(*values, name=name, create_type=False)


def upgrade() -> None:
    eventstatus = _enum("eventstatus", "scheduled", "live", "final", "cancelled", "postponed")
    listsource = _enum("listingsource", "manual", "stubhub", "seatgeek", "gametime")
    opptier = _enum("opponenttier", "rival", "division", "interleague_star", "standard")
    notifkind = _enum("notificationkind", "email", "telegram", "log")

    op.create_table(
        "venues",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("external_key", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("city", sa.String(length=128), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
    )
    op.create_index("ix_venues_external_key", "venues", ["external_key"], unique=True)

    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mlb_team_id", sa.Integer(), nullable=True),
        sa.Column("abbrev", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
    )
    op.create_index("ix_teams_mlb_team_id", "teams", ["mlb_team_id"], unique=True)

    op.create_table(
        "section_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("label", sa.String(length=256), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mlb_game_pk", sa.Integer(), nullable=True),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("away_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", eventstatus, nullable=False, server_default="scheduled"),
        sa.Column("opponent_tier", opptier, nullable=True),
        sa.UniqueConstraint("mlb_game_pk", name="uq_events_mlb_game_pk"),
    )

    op.create_table(
        "listing_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("section_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("section_groups.id"), nullable=False),
        sa.Column("source", listsource, nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="USD"),
        sa.Column("all_in_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("external_listing_id", sa.String(length=256), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "saved_searches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("venue_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("venues.id"), nullable=False),
        sa.Column("home_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id"), nullable=False),
        sa.Column("season_year", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.create_table(
        "notification_channels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("kind", notifkind, nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "saved_search_sections",
        sa.Column("saved_search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("saved_searches.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("section_group_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("section_groups.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "alert_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("saved_search_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("saved_searches.id", ondelete="CASCADE"), nullable=False),
        sa.Column("deal_pct_threshold", sa.Numeric(6, 4), nullable=True),
        sa.Column("max_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("cooldown_seconds", sa.Integer(), nullable=False, server_default="3600"),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notification_channel_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("notification_channels.id"), nullable=True),
    )

    op.create_table(
        "alert_fires",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("alert_rule_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fired_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("payload_summary", sa.String(length=512), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("alert_fires")
    op.drop_table("alert_rules")
    op.drop_table("saved_search_sections")
    op.drop_table("notification_channels")
    op.drop_table("saved_searches")
    op.drop_table("listing_observations")
    op.drop_table("events")
    op.drop_table("section_groups")
    op.drop_table("teams")
    op.drop_table("venues")
    postgresql.ENUM(name="notificationkind").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="opponenttier").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="listingsource").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="eventstatus").drop(op.get_bind(), checkfirst=True)
