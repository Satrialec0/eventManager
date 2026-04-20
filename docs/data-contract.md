# Minimum viable data contract

Derived from [compliance-matrix.md](compliance-matrix.md). **Any adapter or worker must comply with this document.** If implementation needs a field not listed here, update **compliance-matrix** first, then this file.

## 1. Permitted data sources (automation)

| Source ID | Automation allowed? | Permitted operations | Forbidden |
| --- | --- | --- | --- |
| `mlb_statsapi` | **Yes, constrained** | HTTP GET JSON from `https://statsapi.mlb.com/api/v1/` for **schedule** and **venue/team** metadata only; upsert into `events`, `venues`, `teams`. No HTML scraping of mlb.com. | High-frequency polling; resale prices; redistribution of raw JSON to third parties. |
| `stubhub` | **No** | — | Any HTTP client until matrix = `AllowedWithConstraints` or better **and** this table updated. |
| `seatgeek` | **No** | — | Same as StubHub until developer agreement + keys documented here. |
| `gametime` | **No** | — | Same as above. |
| `manual` | **Yes** | User-entered or CSV-imported `listing_observations` with `source = manual`. | Claiming vendor provenance for manual rows. |

## 2. Fields we may store

### Core entities

- **Venue:** `id`, `external_key`, `name`, `city`, `timezone` (optional).
- **Team:** `id`, `mlb_team_id`, `abbrev`, `name`.
- **Event:** `id`, `mlb_game_pk` (nullable), `venue_id`, `home_team_id`, `away_team_id`, `starts_at`, `status` (scheduled/live/final/cancelled).
- **SectionGroup / Section:** `id`, `venue_id`, `label`, `sort_order`; optional `external_map` JSON for future marketplace IDs.
- **ListingObservation:** `id`, `event_id`, `section_id`, `source` enum, `observed_at`, `currency`, `all_in_price` (numeric), `quantity`, `external_listing_id` (nullable), `notes` (nullable). **`raw_payload` JSONB:** only populated for sources whose matrix row **explicitly** allows retention; currently **omit or null** for all marketplace adapters (not implemented).

### Saved search & alerts

- **SavedSearch:** `id`, `name`, `venue_id`, `home_team_id`, `season_year`, `active`.
- **SavedSearchSection:** link saved search ↔ section groups user cares about.
- **AlertRule:** `id`, `saved_search_id`, `deal_pct_threshold` (nullable), `max_price` (nullable), `cooldown_seconds`, `enabled`.
- **NotificationChannel:** `id`, `kind` (`email` \| `telegram` \| `log`), `config` JSON (e.g. SMTP — store secrets only in env, not DB).
- **AlertFire:** `id`, `alert_rule_id`, `fired_at`, `payload_summary` (short text, no PII).

## 3. Refresh cadence & rate limits

| Source | Max sustained | Notes |
| --- | --- | --- |
| `mlb_statsapi` | 1 request / second | Backoff 2^n seconds on 4xx/5xx up to 5 minutes. Refresh schedule at most **daily** off-season, **hourly** on game weeks if needed. |
| Marketplace (future) | As per vendor | Document per-vendor row when enabled. |

## 4. Retention & TTL

- **ListingObservation:** retain **24 months** by default; operator may purge older rows.
- **raw_payload:** **do not store** until a vendor row allows it; if enabled later, default TTL **7 days** unless terms require shorter.
- **AlertFire:** retain **90 days**.

## 5. Logging & redaction

- Logs: **no** full payment info, seller real names, or full API payloads for marketplace (not in use).
- Log: `correlation_id`, `source`, HTTP status, latency, **event_id** only.

## 6. Adapter gating rule

No Python module under `backend/app/adapters/` may perform outbound HTTP to vendor **V** unless:

1. [compliance-matrix.md](compliance-matrix.md) lists **V** with verdict `AllowedAsProposed` or `AllowedWithConstraints`, and  
2. This document’s §1 table has **Automation allowed? = Yes** for **V**.
