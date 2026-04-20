import { Link, Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import EventDetail from "./pages/EventDetail";

export default function App() {
  return (
    <>
      <header style={{ padding: "1rem 1.5rem", borderBottom: "1px solid #e2e8f0", background: "#fff" }}>
        <Link to="/" style={{ fontWeight: 700, textDecoration: "none", color: "#0f172a" }}>
          eventManager
        </Link>
        <span style={{ marginLeft: "1rem", color: "#64748b", fontSize: "0.9rem" }}>
          personal deal tracker
        </span>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/events/:eventId" element={<EventDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}
