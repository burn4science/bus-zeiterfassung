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
| `templating.py` | Jinja2Templates instance + custom filters (`weekday_de` for German day names) |
| `routes/pages.py` | `GET /`, `/month`, `/login` + `POST /login` |
| `routes/entries.py` | `POST /start`, `/stop`, `/entries` CRUD + shared helpers |
| `routes/export.py` | `POST /export/{month_key}` → xlsx + pdf |
| `services/excel.py` | `fill_template(entries, year, month)` — fills xlsx template cells |
| `services/pdf.py` | `xlsx_to_pdf(path)` — shells out to `soffice` |

**Core data flow**: User clocks in (`/start` → open `TimeEntry`), clocks out (`/stop` → sets `end`). At month end, `/export/{YYYY-MM}` groups entries by day (max 4 sessions/day), fills the Excel template (see `docs/template-mapping.md` for exact cell layout), and converts to PDF.

**URL params**: `GET /?d=YYYY-MM-DD` — day view for a specific date (defaults to today). `GET /month?m=YYYY-MM` — month view (defaults to current month). Short aliases kept in URL via `Query(alias=...)` so Python variables stay descriptive.

## Non-obvious Patterns

**Dual-context HTMX endpoints**: `POST /entries/{id}/update` and `POST /entries/{id}/delete` serve both the "Erfassen" (day) and "Monat" (month) views. They detect which view to re-render via a hidden `view` form field (`"today"` or absent). When `view=today`, they return `partials/today_card.html`; otherwise a single `partials/month_row.html` row. A `selected_day` hidden field threads the currently-viewed date back through edit/delete so the card stays on the same day after mutation.

**`_next_nav_day` helper** (`routes/entries.py`): computes the next navigation target for the day view's `>` arrow. Past days go day-by-day; today and future days jump to the nearest date that has an entry (or disable the arrow if none exists). Imported by `routes/pages.py` — don't duplicate this logic.

**`partials/today_card.html`** is both a full-page include (via `today.html`) and a direct HTMX swap target (`#today-card`). All mutation endpoints (`/start`, `/stop`, `/entries`, update, delete with `view=today`) return this partial directly.

## Testing Notes

- Tests use in-memory SQLite and override `get_session` / `require_login` via FastAPI dependency injection.
- PDF tests auto-skip if `soffice`/`libreoffice` is not installed.
- `asyncio_mode = "auto"` — async tests are detected without decorators.

## Environment

Copy `.env.example` to `.env`. Required: `PIN_HASH`, `SECRET_KEY` (≥32 chars). The Excel template (`assets/Dienstzeitblatt_template.xlsx`) is not in the repo and must be provided separately — it is volume-mounted at `/app/data`.
