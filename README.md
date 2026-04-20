# eventManager

Personal, **ToS-aware** ticket deal tracker. See [docs/initial-use-case.md](docs/initial-use-case.md), [docs/compliance-matrix.md](docs/compliance-matrix.md), [docs/data-contract.md](docs/data-contract.md), and [docs/deal-score-spec.md](docs/deal-score-spec.md).

## Ports vs other projects

Your **jobscout** stack (`jobscout/docker-compose.yml` on your machine) uses:

- **8001** — FastAPI / uvicorn (`jobscout_backend`)
- **5432** — Postgres (`jobscout_db`)

**eventManager** is wired to avoid those host ports:

- **8002** — eventManager API (uvicorn in Docker, or use the same port if you run uvicorn on the host)
- **5433** — eventManager Postgres on the host (maps to 5432 inside the container)

If you change these in `docker-compose.yml`, update `DATABASE_URL`, this README, and `frontend/vite.config.ts` proxy targets.

## Stack

- **Postgres 16** + optional **FastAPI** via Docker Compose
- **SQLAlchemy** + **Alembic** (`backend/`)
- **React** + **Vite** + **Recharts** (`frontend/`)

## Quick start

1. Copy env files:

   ```powershell
   copy .env.example .env
   copy .env.example backend\.env
   ```

   `DATABASE_URL` must use **port 5433** when talking to eventManager’s DB from Windows (see `.env.example`).

2. Start **Postgres + API** (uvicorn in Docker):

   ```powershell
   docker compose up -d --build
   ```

   API: `http://127.0.0.1:8002` — OpenAPI: `http://127.0.0.1:8002/docs`

   Postgres only (no API):

   ```powershell
   docker compose up -d db
   ```

3. **Migrations** (from host, with DB running):

   ```powershell
   cd backend
   python -m pip install -r requirements.txt
   $env:PYTHONPATH="."
   python -m alembic upgrade head
   ```

4. Import Mets 2026 home schedule and seed saved search + demo prices:

   ```powershell
   python -m app.cli sync-schedule
   python -m app.cli seed-mets
   ```

5. **API on the host instead of Docker** (optional):

   ```powershell
   cd backend
   python -m uvicorn app.main:app --reload --port 8002
   ```

   Stop the `api` service first so the port is free: `docker compose stop api`.

6. Web UI:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://localhost:5173`. Vite proxies `/api` to `http://127.0.0.1:8002`.

## Backup

```powershell
docker compose exec db pg_dump -U eventmanager eventmanager > backup.sql
```

## Compliance

Do not enable marketplace HTTP adapters until [docs/compliance-matrix.md](docs/compliance-matrix.md) and [docs/data-contract.md](docs/data-contract.md) are updated for that vendor.
