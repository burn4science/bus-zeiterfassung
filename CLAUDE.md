# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Docker Workflow

Development and testing happen inside Docker.

```bash
docker compose up -d --build     # Build and start the app
docker compose logs -f           # Follow logs
docker compose down              # Stop
```

The production image (`Dockerfile`) is a two-stage build: a `builder` stage that installs Python deps via `uv`, and a `runtime` stage that adds LibreOffice for PDF conversion. Dev dependencies are **not** installed in the production image.

To run tests or linting inside a container with dev deps:
```bash
docker compose run --rm --build app bash  # Then inside: uv sync && uv run pytest
```

Generate a PIN hash for `.env`:
```bash
docker compose run --rm app python -m bus_zeiterfassung.auth hash <pin>
```

## Architecture

**Purpose**: Self-hosted time tracking app for bus supervision ("Busbegleitung"). Tracks work sessions and exports them into an Excel monthly template (*Dienstzeitblatt*), converted to PDF via headless LibreOffice.

**Stack**: FastAPI + HTMX + Jinja2 (server-side HTML), SQLite via SQLModel (async), openpyxl for Excel, itsdangerous for sessions.

**Package layout** (`src/bus_zeiterfassung/`):

| Module | Role |
|---|---|
| `main.py` | FastAPI app init, middleware, router mounting |
| `config.py` | Pydantic-settings from `.env` (PIN_HASH, SECRET_KEY, TZ, TEMPLATE_PATH, DATABASE_URL, EXPORT_DIR) |
| `models.py` | `TimeEntry` SQLModel table (day, start, end, note) |
| `db.py` | Async SQLite engine, session dependency |
| `auth.py` | Argon2 PIN verify, session cookie, `require_login` FastAPI dependency |
| `timeutil.py` | Timezone-aware datetime helpers (default: Europe/Berlin) |
| `routes/pages.py` | `GET /`, `/month`, `/login` + `POST /login` |
| `routes/entries.py` | `POST /start`, `/stop`, `/entries` CRUD |
| `routes/export.py` | `POST /export/{month_key}` → xlsx + pdf |
| `services/excel.py` | `fill_template(entries, year, month)` — fills xlsx template cells |
| `services/pdf.py` | `xlsx_to_pdf(path)` — shells out to `soffice` |

**Core data flow**: User clocks in (`/start` → open `TimeEntry`), clocks out (`/stop` → sets `end`). At month end, `/export/{YYYY-MM}` groups entries by day (max 4 sessions/day), fills the Excel template (see `docs/template-mapping.md` for exact cell layout), and converts to PDF.

## Testing Notes

- Tests use in-memory SQLite and override `get_session` / `require_login` via FastAPI dependency injection.
- PDF tests auto-skip if `soffice`/`libreoffice` is not installed.
- `asyncio_mode = "auto"` — async tests are detected without decorators.

## Environment

Copy `.env.example` to `.env`. Required: `PIN_HASH`, `SECRET_KEY` (≥32 chars). The Excel template (`data/Dienstzeitblatt_template.xlsx`) is not in the repo and must be provided separately — it is volume-mounted at `/app/data`.
