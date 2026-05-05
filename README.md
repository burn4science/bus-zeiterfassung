# bus-zeiterfassung

Self-hosted Zeiterfassungs-App für die Busbegleitung. FastAPI + HTMX + SQLite,
füllt eine Excel-Monatsvorlage (`Dienstzeitblatt_template.xlsx`) und exportiert
sie per Headless-LibreOffice als PDF.

## Entwicklung

```bash
cp .env.example .env

# PIN-Hash erzeugen (z. B. für PIN "1234"):
docker compose run --rm app python -m bus_zeiterfassung.auth hash 1234

# SECRET_KEY erzeugen:
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

docker compose up -d --build   # App bauen und starten
docker compose logs -f         # Logs verfolgen
docker compose down            # Stoppen
```

Die Vorlage muss unter `assets/Dienstzeitblatt_template.xlsx` liegen.
Zellen-Mapping: siehe [docs/template-mapping.md](docs/template-mapping.md).

## Konfiguration (`.env`)

| Variable | Standard | Beschreibung |
|---|---|---|
| `PIN_HASH` | — | **Pflicht.** Argon2-Hash des Login-PINs |
| `SECRET_KEY` | — | **Pflicht.** ≥ 32 Zeichen, für Session-Cookies |
| `TZ` | `Europe/Berlin` | Zeitzone für Stempelzeiten |
| `EMPLOYEE_NAME` | `""` | Name, der im Dienstzeitblatt erscheint |
| `TEMPLATE_PATH` | `assets/Dienstzeitblatt_template.xlsx` | Pfad zur Excel-Vorlage |
| `SIGNATURE_PATH` | — | Lokale PNG-Datei für Unterschrift im Export |
| `SIGNATURE_URL` | — | Remote-PNG (z. B. Nextcloud-Freigabelink `…/download`) |
| `DATABASE_URL` | `sqlite:///data/db.sqlite3` | SQLite-Datenbankpfad |
| `EXPORT_DIR` | `data/exports` | Zielverzeichnis für `.xlsx`- und `.pdf`-Exporte |

`SIGNATURE_PATH` hat Vorrang vor `SIGNATURE_URL`. Ist beides nicht gesetzt, wird keine Unterschrift eingefügt.

## Tests

Tests laufen im Container (mit Dev-Dependencies):

```bash
docker compose run --rm --build app bash
# im Container:
uv sync && uv run pytest
```

PDF-Tests werden automatisch übersprungen, wenn `soffice` / `libreoffice`
nicht installiert ist.

## Funktionsüberblick

| Ansicht | URL | Beschreibung |
|---|---|---|
| Erfassen | `/?d=YYYY-MM-DD` | Tagesansicht mit Start/Stopp, manuellem Eintrag, Inline-Bearbeitung. Navigiert tageweise durch die Vergangenheit; springt in der Zukunft nur zu Tagen mit Einträgen. |
| Monat | `/month?m=YYYY-MM` | Monatsübersicht mit Inline-Bearbeitung, Vor-/Zurück-Navigation und PDF-Export. |

Einträge können in beiden Ansichten inline bearbeitet und gelöscht werden (Stift- und Papierkorb-Icon). Neue Jinja2-Filter: `weekday_de` für deutsche Wochentagsnamen (in `templating.py`).

## Deployment (Proxmox LXC)

```bash
# auf dem LXC:
git clone <repo> && cd bus-zeiterfassung
cp .env.example .env     # PIN_HASH, SECRET_KEY setzen
docker compose up -d --build
```

Zugriff vom iPhone / Laptop über die Tailscale-URL des LXC.
`./data/` enthält DB und Exporte — in Backup-Plan aufnehmen.
