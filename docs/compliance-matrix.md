# Compliance and access matrix (Phase 0)

**Purpose:** Single source of truth for whether automated data collection from each vendor is allowed for this **personal, non-commercial** project.  
**Rule:** Ambiguous rows default to **no automation** until clarified in writing with the vendor or a lawyer.  
**Disclaimer:** Engineering checklist only — not legal advice.

**Matrix row template:**  
`Vendor | Desired data | Documented access path | ToS/API URLs (cited) | Cost | Personal-use OK? | Rate/caching/attribution | Verdict | Allowed automation summary`

---

## API registration playbook (do in your browser)

No third-party tool can accept vendor contracts or complete OAuth on your behalf. Use the steps below, then fill **Registration status** and paste any **exact quote snippets** you rely on into the vendor rows.

| Vendor | Free / $0 access? | What to do (order) | Secrets to store later (repo: env only) |
| --- | --- | --- | --- |
| **MLB Stats API** (`statsapi.mlb.com`) | Yes — no API key for basic schedule JSON | No signup. Read [MLB Terms of Use](https://www.mlb.com/official-information/terms-of-use) and decide whether schedule JSON at `statsapi.mlb.com` is within your comfort zone versus the **MLB Digital Properties** definition (see **ToS snapshots** below). | None |
| **SeatGeek Platform** | Documented as free with identification ([SeatGeek Platform docs](https://seatgeek.github.io/)) | (1) Create a SeatGeek user account. (2) Request keys at [seatgeek.com/account/develop](https://seatgeek.com/account/develop). (3) Accept current [API/SDK Terms](https://seatgeek.com/api-terms) in the browser (capture “last updated” from the page). (4) In [Developer Portal — APIs](https://portal.seatgeek.com/apis), confirm which **products** you are approved for — **event discovery** endpoints are well documented; **ticket listing / price** fields may depend on your approval tier — verify before coding. | `SEATGEEK_CLIENT_ID`, optional `SEATGEEK_CLIENT_SECRET` (wired in `backend/app/config.py` when you add them to `.env`) |
| **StubHub** | **Not** self-serve “free tier” as of last check | [developer.stubhub.com](https://developer.stubhub.com/) states they are migrating to a new API and ask you to **email** [affiliates@stubhub.com](mailto:affiliates@stubhub.com) (buyer/affiliate-style discovery) or [api.support@stubhub.com](mailto:api.support@stubhub.com) (seller tooling) with a short description of the app. Expect manual onboarding, not an instant key. Regional hubs (e.g. [developer.stubhub.ie](https://developer.stubhub.ie/)) may differ — use the portal matching your region. | As provided if approved (e.g. OAuth client id/secret — document when received) |
| **GameTime** | No documented **buyer** or **public listing** API for hobby automation | Consumer app + [seller API terms](https://gametime.co/api-seller-terms) are aimed at marketplace participants — not assumed to grant unattended price aggregation. **Skip registration** for API until a written, key-based path exists. | N/A |

---

## ToS snapshots (engineering capture — re-verify in browser)

**MLB.com Terms of Use** — footer on fetched page: **LAST UPDATED: MARCH 11, 2025** — [https://www.mlb.com/official-information/terms-of-use](https://www.mlb.com/official-information/terms-of-use)

Relevant prohibition (Section 1; “You must not use the MLB Digital Properties…”) includes: *“(xi) use automated scripts to collect information from or otherwise interact with the MLB Digital Properties;”* — whether `statsapi.mlb.com` JSON is included in “MLB Digital Properties” is **not decided here**; treat schedule ingestion as **AllowedWithConstraints** only after your own reading (or vendor clarification).

**SeatGeek API/SDK Terms** — [https://seatgeek.com/api-terms](https://seatgeek.com/api-terms) — automated fetch returned HTTP 403 from this environment; open the page locally and record the **“last updated”** date and any clauses on caching, storage, and redistribution.

---

## Registration status (fill as you complete steps)

| Vendor | Account / request sent | Keys or access received | Date | Notes |
| --- | --- | --- | --- | --- |
| MLB Stats API | N/A | N/A |  | ToU review only |
| SeatGeek | ☐ | ☐ |  | Paste API Terms “last updated” when done |
| StubHub | ☐ | ☐ |  | Paste response / agreement summary if approved |
| GameTime | N/A | N/A |  | Until documented API path exists |

---

## Implementation order (after compliance, before marketplace HTTP)

1. **SeatGeek first (if keys + terms allow):** Once this matrix and your notes show **keys obtained** and acceptable **API Terms** language for your storage pattern, update [data-contract.md](data-contract.md) §1 for `seatgeek` to **Yes, constrained** with permitted endpoints and rate limits, add env vars to `.env`, then replace `StubMarketplaceAdapter` with a real client behind the same `MarketplaceAdapter` port (`backend/app/adapters/marketplace.py`).
2. **StubHub:** Only after written access (email/partner flow) and matrix row moves to **AllowedWithConstraints** or better; mirror into `data-contract.md`.
3. **GameTime:** Leave stub until a key-based, documented path exists.
4. **MLB schedule:** `MlbStatsApiScheduleProvider` is already the sanctioned pattern; keep refresh cadence per `data-contract.md` §3.

---

## Schedule / event truth (non-marketplace)

| Field | Value |
| --- | --- |
| **Vendor** | MLB / MLB Advanced Media (schedule & team metadata via **MLB Stats API** public `statsapi.mlb.com` JSON) |
| **Desired data** | Game PK, datetime, home/away, teams, venue for building `Event` rows (e.g. Mets home 2026). |
| **Documented access path** | Public read-only HTTP JSON documented by community and mirrored in open-source clients; **no** API key for basic schedule endpoints. **You must** confirm current [MLB.com Terms of Use](https://www.mlb.com/official-information/terms-of-use) (see “last updated” on that page) for your automation pattern (polling frequency, storage, attribution). |
| **ToS/API URLs** | [https://www.mlb.com/official-information/terms-of-use](https://www.mlb.com/official-information/terms-of-use) — MLB Digital Properties use; [https://statsapi.mlb.com/](https://statsapi.mlb.com/) (host only — no standalone public API ToS page located as of doc date). |
| **Cost** | $0 |
| **Personal-use OK?** | **Unclear** without reading full MLB ToU for automated access + storage; treat as **personal, low-volume, read-only** until you verify. |
| **Rate/caching/attribution** | Self-imposed: **≤ 1 req/s** burst, exponential backoff on errors; cache responses per `data-contract.md`; attribute “Data courtesy MLB” in UI if ToU requires. |
| **Verdict** | `AllowedWithConstraints` — **only** schedule/metadata endpoints implemented in `MlbStatsApiScheduleProvider`; **no** scraping of mlb.com HTML. |
| **Allowed automation summary** | Fetch JSON schedule for a team/season window and upsert canonical `Event` rows **if** your reading of MLB ToU permits this use; otherwise switch this row to `HumanOnly` and enter games manually. |

---

## StubHub

| Field | Value |
| --- | --- |
| **Vendor** | StubHub (viagogo group) |
| **Desired data** | Listings, all-in price, section, quantity, deep links. |
| **Documented access path** | [StubHub Developer Portal](https://developer.stubhub.com/) currently directs developers to **email** for new API access (buyer/affiliate vs seller tracks) — **not** an instant self-serve key; regional sites (e.g. [developer.stubhub.ie](https://developer.stubhub.ie/)) may differ. |
| **ToS/API URLs** | Developer hub: [https://developer.stubhub.com/](https://developer.stubhub.com/); regional portal terms (example): [https://developer.stubhub.ie/terms-and-conditions](https://developer.stubhub.ie/terms-and-conditions) — **verify** the portal that matches your account region. |
| **Cost** | Typically partner / commercial track; not assumed $0. |
| **Personal-use OK?** | Developer programs are usually **commercial/partner**-oriented; **unclear** for hobby automation without contract. |
| **Rate/caching/attribution** | As per executed developer agreement (not filled here). |
| **Verdict** | `NotAvailableWithoutContract` for this repo **until** you have keys + written terms allowing your use. |
| **Allowed automation summary** | **None** in code without Phase 0 update to `AllowedWithConstraints` and `data-contract.md` update. |

---

## SeatGeek

| Field | Value |
| --- | --- |
| **Vendor** | SeatGeek |
| **Desired data** | Events, listings, prices, sections. |
| **Documented access path** | SeatGeek **Platform API** — request `client_id` (and optional secret) at [seatgeek.com/account/develop](https://seatgeek.com/account/develop); docs at [seatgeek.github.io](https://seatgeek.github.io/). **Partner / portal** products (e.g. [portal.seatgeek.com/apis](https://portal.seatgeek.com/apis)) may govern listing/inventory features — confirm what your keys unlock. |
| **ToS/API URLs** | [https://seatgeek.com/api-terms](https://seatgeek.com/api-terms) (SeatGeek API/SDK Terms); general [https://seatgeek.com/terms](https://seatgeek.com/terms); portal [https://portal.seatgeek.com/](https://portal.seatgeek.com/). |
| **Cost** | Often $0 to start for approved apps; partner/rev-share possible — confirm in portal. |
| **Personal-use OK?** | API terms bind **you** as developer; personal app may still be acceptable if portal allows — **verify** “Application” definition and restrictions on storage/redistribution. |
| **Rate/caching/attribution** | Per API terms and portal rate limits; cache only as permitted. |
| **Verdict** | `AllowedWithConstraints` **only after** you register, accept current API terms, and document allowed scopes in `data-contract.md`. Until then: `HumanOnly`. |
| **Allowed automation summary** | **None** until keys + contract row updated; then only documented endpoints with compliance to API Terms. |

---

## GameTime

| Field | Value |
| --- | --- |
| **Vendor** | GameTime (Gametime United Inc.) |
| **Desired data** | Listings, prices, sections. |
| **Documented access path** | Consumer site/app; **seller API** terms exist for commercial integrations — not assumed available for hobby polling. |
| **ToS/API URLs** | [https://gametime.co/terms-of-service](https://gametime.co/terms-of-service); API seller terms: [https://gametime.co/api-seller-terms](https://gametime.co/api-seller-terms). |
| **Cost** | Unknown without sales/API agreement. |
| **Personal-use OK?** | **Unclear** for unattended price aggregation; default conservative. |
| **Rate/caching/attribution** | N/A until permitted API path exists. |
| **Verdict** | `HumanOnly` until a documented, key-based API path is approved for your use case. |
| **Allowed automation summary** | **None**. |

---

## Summary

| Vendor | Verdict (as of this doc) |
| --- | --- |
| MLB Stats API (schedule JSON) | `AllowedWithConstraints` — implement only after you confirm MLB ToU; use low rate limits. |
| StubHub | `NotAvailableWithoutContract` |
| SeatGeek | `HumanOnly` until portal onboarding complete → then `AllowedWithConstraints` |
| GameTime | `HumanOnly` |

**Next action before marketplace adapters:** Complete rows in **Registration status**, add **exact quote snippets** and **“last updated”** dates from each ToS page you rely on (especially SeatGeek API Terms opened in your browser), then mirror permissions into [data-contract.md](data-contract.md) following **Implementation order** above.
