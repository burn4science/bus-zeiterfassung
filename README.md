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

Die Vorlage muss unter `data/Dienstzeitblatt_template.xlsx` liegen.
Zellen-Mapping: siehe [docs/template-mapping.md](docs/template-mapping.md).

## Tests

Tests laufen im Container (mit Dev-Dependencies):

```bash
docker compose run --rm --build app bash
# im Container:
uv sync && uv run pytest
```

PDF-Tests werden automatisch übersprungen, wenn `soffice` / `libreoffice`
nicht installiert ist.

## Deployment (Proxmox LXC)

```bash
# auf dem LXC:
git clone <repo> && cd bus-zeiterfassung
cp .env.example .env     # PIN_HASH, SECRET_KEY setzen
docker compose up -d --build
```

Zugriff vom iPhone / Laptop über die Tailscale-URL des LXC.
`./data/` enthält DB und Exporte — in Backup-Plan aufnehmen.
