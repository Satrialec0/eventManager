# Deal score specification

Transparent metrics only — **no** scraped third-party “demand” or black-box ML.

## v1 (ship first)

Per tuple `(event_id, section_id, source)` where `source ∈ { manual, … }`:

1. **`p_best`** — minimum `all_in_price` among `listing_observations` in the **last 7 days** (or since first observation if fewer than 7 days of history).
2. **`p_ref`** — rolling **median** of **daily minima** of `p_best` over the last **14 days** (if fewer than 3 samples, fall back to median of available daily minima; if none, score undefined).
3. **`deal_pct`** — `(p_ref - p_best) / p_ref` when `p_ref > 0`; else `null`.

**Alert condition (v1):** fire when `deal_pct ≥ user_threshold` (e.g. 0.15 = 15% off reference) **and** `cooldown_seconds` elapsed since last fire for the same `alert_rule_id`.

**Edge cases:**

- If only one observation exists, `p_ref = p_best` → `deal_pct = 0` (no deal signal yet).
- Currency mismatch within a tuple: exclude or normalize — implementation uses single `currency` per observation; mixed currency returns no score.

## v2 (opponent-aware — backlog)

After enough history:

1. Define **`OpponentTier`** enum (manual seed): e.g. `rival`, `division`, `interleague_star`, `standard`.
2. Assign tier per `(home_team, away_team)` in config table or seed file — **human curated**, not scraped.
3. Maintain **`p_ref_tier`** = median of daily minima of `p_best` per `(section_id, opponent_tier)` over a **season-to-date** window.
4. **`deal_pct_v2`** = `(p_ref_tier - p_best) / p_ref_tier` when defined.

**Constraint:** All inputs from **our own** `listing_observations` + curated tiers + schedule metadata permitted by `data-contract.md`.

## v3+ (filters — backlog)

Optional filters only when **permitted** structured fields exist on `Event` (e.g. promo flag from MLB feed if allowed, or `notes` field you edit manually):

- Exclude observations on giveaway nights if you tag `event.promo = true`.
- Never infer promo from unofficial scraping.

## Explicit non-goals

- No “expected price” from external resale indices without a compliant API row in the compliance matrix.
- No web scraping of StubHub/SeatGeek/GameTime HTML or undocumented mobile APIs.
