const base = "";

export type UUID = string;

export interface VenueOut {
  id: UUID;
  name: string;
  external_key: string | null;
}

export interface TeamOut {
  id: UUID;
  abbrev: string;
  name: string;
  mlb_team_id: number | null;
}

export interface SavedSearchOut {
  id: UUID;
  name: string;
  season_year: number;
  active: boolean;
  venue: VenueOut;
  home_team: TeamOut;
}

export interface EventOut {
  id: UUID;
  mlb_game_pk: number | null;
  starts_at: string;
  status: string;
  venue: VenueOut;
  home_team: TeamOut;
  away_team: TeamOut;
}

export interface SeriesPoint {
  observed_at: string;
  all_in_price: number;
}

export interface DealScoreOut {
  section_id: UUID;
  section_label: string | null;
  source: string;
  p_best: number | null;
  p_ref: number | null;
  deal_pct: number | null;
}

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${base}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  return r.json() as Promise<T>;
}

export const api = {
  health: () => getJson<{ status: string }>("/api/health"),
  savedSearches: () => getJson<SavedSearchOut[]>("/api/saved-searches"),
  events: (savedSearchId?: UUID) =>
    getJson<EventOut[]>(
      savedSearchId ? `/api/events?saved_search_id=${savedSearchId}` : "/api/events"
    ),
  series: (eventId: UUID, sectionId: UUID, source = "manual") =>
    getJson<SeriesPoint[]>(
      `/api/events/${eventId}/series?section_id=${sectionId}&source=${source}`
    ),
  dealScores: (eventId: UUID, savedSearchId?: UUID) =>
    getJson<DealScoreOut[]>(
      savedSearchId
        ? `/api/events/${eventId}/deal-scores?saved_search_id=${savedSearchId}`
        : `/api/events/${eventId}/deal-scores`
    ),
};
