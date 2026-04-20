import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type EventOut, type SavedSearchOut } from "../api";

export default function Dashboard() {
  const [searches, setSearches] = useState<SavedSearchOut[]>([]);
  const [events, setEvents] = useState<EventOut[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api
      .savedSearches()
      .then((s) => {
        setSearches(s);
        if (s[0]) setSelected(s[0].id);
      })
      .catch((e: Error) => setErr(e.message));
  }, []);

  useEffect(() => {
    if (!selected) {
      setEvents([]);
      return;
    }
    api
      .events(selected)
      .then(setEvents)
      .catch((e: Error) => setErr(e.message));
  }, [selected]);

  const selectedSearch = searches.find((s) => s.id === selected);
  const seasonLabel = selectedSearch?.season_year;

  return (
    <div>
      <h1>Saved searches</h1>
      {err && <p style={{ color: "#b91c1c" }}>{err}</p>}
      <div className="card">
        {searches.length === 0 && <p>No saved searches yet. Run backend seed: <code>python -m app.cli seed-mets</code></p>}
        <ul style={{ listStyle: "none", padding: 0 }}>
          {searches.map((s) => (
            <li key={s.id} style={{ marginBottom: "0.5rem" }}>
              <label>
                <input
                  type="radio"
                  name="ss"
                  checked={selected === s.id}
                  onChange={() => setSelected(s.id)}
                />{" "}
                {s.name} — {s.home_team.abbrev} @ {s.venue.name} ({s.season_year})
              </label>
            </li>
          ))}
        </ul>
      </div>

      <h2>Upcoming games</h2>
      <div className="card">
        <p style={{ marginTop: 0, color: "#64748b", fontSize: "0.9rem" }}>
          {events.length === 0
            ? "No games loaded for this saved search."
            : `${events.length} home game${events.length === 1 ? "" : "s"}${seasonLabel != null ? ` (${seasonLabel} season)` : ""}`}
        </p>
        <div
          style={{
            maxHeight: "70vh",
            overflow: "auto",
            border: "1px solid #e2e8f0",
            borderRadius: 6,
          }}
        >
          <table>
            <thead style={{ position: "sticky", top: 0, background: "#fff", zIndex: 1 }}>
              <tr>
                <th>When (UTC)</th>
                <th>Matchup</th>
                <th>Status</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.starts_at).toISOString().slice(0, 16)}</td>
                  <td>
                    {e.away_team.abbrev} @ {e.home_team.abbrev}
                  </td>
                  <td>{e.status}</td>
                  <td>
                    <Link to={`/events/${e.id}?ss=${selected ?? ""}`}>Charts</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
