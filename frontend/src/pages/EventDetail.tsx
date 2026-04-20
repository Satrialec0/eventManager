import { useEffect, useMemo, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { api, type DealScoreOut, type SeriesPoint } from "../api";

export default function EventDetail() {
  const { eventId } = useParams();
  const [params] = useSearchParams();
  const ss = params.get("ss") || undefined;

  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [scores, setScores] = useState<DealScoreOut[]>([]);
  const [sectionId, setSectionId] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!eventId) return;
    api
      .dealScores(eventId, ss)
      .then((ds) => {
        setScores(ds);
        const first = ds.find((d) => d.section_id);
        if (first) setSectionId(first.section_id);
      })
      .catch((e: Error) => setErr(e.message));
  }, [eventId, ss]);

  useEffect(() => {
    if (!eventId || !sectionId) return;
    api
      .series(eventId, sectionId, "manual")
      .then(setSeries)
      .catch((e: Error) => setErr(e.message));
  }, [eventId, sectionId]);

  const chartData = useMemo(
    () =>
      series.map((p) => ({
        t: new Date(p.observed_at).toLocaleDateString(),
        price: p.all_in_price,
      })),
    [series]
  );

  if (!eventId) return <p>Missing event</p>;

  return (
    <div>
      <p>
        <Link to="/">← Back</Link>
      </p>
      <h1>Event {eventId.slice(0, 8)}…</h1>
      {err && <p style={{ color: "brown" }}>{err}</p>}

      <div className="card">
        <h2>Deal scores (v1)</h2>
        <table>
          <thead>
            <tr>
              <th>Section</th>
              <th>Source</th>
              <th>p_best</th>
              <th>p_ref</th>
              <th>deal_pct</th>
            </tr>
          </thead>
          <tbody>
            {scores.map((r) => (
              <tr key={`${r.section_id}-${r.source}`}>
                <td>
                  <label>
                    <input
                      type="radio"
                      name="sec"
                      checked={sectionId === r.section_id}
                      onChange={() => setSectionId(r.section_id)}
                    />{" "}
                    {r.section_label ?? r.section_id}
                  </label>
                </td>
                <td>{r.source}</td>
                <td>{r.p_best?.toFixed(2) ?? "—"}</td>
                <td>{r.p_ref?.toFixed(2) ?? "—"}</td>
                <td>{r.deal_pct != null ? (r.deal_pct * 100).toFixed(1) + "%" : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h2>Price history (manual)</h2>
        {chartData.length === 0 ? (
          <p>No observations for this section. Add rows via API or seed.</p>
        ) : (
          <div style={{ width: "100%", height: 320 }}>
            <ResponsiveContainer>
              <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="t" />
                <YAxis domain={["auto", "auto"]} />
                <Tooltip />
                <Line type="monotone" dataKey="price" stroke="#2563eb" dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}
