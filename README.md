# AIB Telegram Bot

Official-source wildfire risk bot for Italy. The project currently runs Veneto in production and already includes connectors and fixtures for Emilia-Romagna.

Public channel:
- https://t.me/AIBVenetoBollettini

## Current state

- Production flow: read Veneto daily data, render the risk map/table, send both to Telegram.
- Extensible ingestion flow: region connectors in `collectors/` with normalized outputs and daily aggregation support.
- Development output: connector runs and aggregated daily JSON are written under `.dev-output/connectors/`.

## Canonical docs

- [docs/ROADMAP.md](docs/ROADMAP.md): strategic roadmap and future phases.
- [docs/TECH_ANALYSIS.md](docs/TECH_ANALYSIS.md): current limitations and target architecture.
- [docs/OFFICIAL_AIB_SOURCES_ITALY.md](docs/OFFICIAL_AIB_SOURCES_ITALY.md): canonical source inventory.
- [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md): tactical implementation plan.
- [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md): connector implementation pattern.
- [docs/DATA_SOURCES_ITALY.md](docs/DATA_SOURCES_ITALY.md): source-selection criteria and normalized schema.

## Quick start

### 1) Install system dependencies

Use:

```bash
./install.sh
```

This installs Python and wkhtmltopdf/wkhtmltoimage dependencies needed by imgkit.

### 2) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment variables

Copy `.env.example` to `.env` and set values:

```env
BOT_TOKEN=...
GROUP_CHAT_ID=...
ALERT_CHAT_ID=... # optional, defaults to GROUP_CHAT_ID
```

Optional network flag:

```env
VENETO_SOURCE_VERIFY_SSL=true
```

### 4) Run the current bot

```bash
python main.py
```

Generated media is saved under `media/`.

## Runtime data

- Veneto connector inputs:
	- https://www.ambienteveneto.it/incendi/dati/FWI.json
	- https://www.ambienteveneto.it/stazioni/incendi/venetorischio.html
- Daily aggregated connector output:
	- `.dev-output/connectors/daily/YYYY-MM-DD.json`
	- `.dev-output/connectors/daily/latest.json`

## Failure alerting

- On unhandled errors, the bot logs a structured `run_failed` event.
- It also sends a Telegram alert message to `ALERT_CHAT_ID`.
- If `ALERT_CHAT_ID` is not set, alerts are sent to `GROUP_CHAT_ID`.

## Notes

- The repository is moving toward a single canonical Italy-wide daily JSON.
- Use the docs above as the primary reference instead of the older per-topic notes.

### 1) Install system dependencies

Use:

```bash
./install.sh
```

This installs Python and wkhtmltopdf/wkhtmltoimage dependencies needed by imgkit.

### 2) Create and activate virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3) Configure environment variables

Copy `.env.example` to `.env` and set values:

```env
BOT_TOKEN=...
GROUP_CHAT_ID=...
```

### 4) Run the bot

```bash
python main.py
```

Generated media is saved under `media/`.

- `VERSION` starts at `0.0.0`.
- Patch (`x.y.Z`) is incremented automatically on each commit via pre-commit hook.
- Major/minor (`X.Y.z`) are manual and must be edited directly in `VERSION`.
- The hook updates `VERSION` and stages it automatically.

If hooks are not active yet, run:

```bash
./install.sh
```

This configures `core.hooksPath` to `.githooks`.

## GitHub Actions schedule

The bot runs daily via workflow:

- File: `.github/workflows/main.yml`
- Cron: `5 13 * * *` (UTC)

Required repository secrets:

- `BOT_TOKEN`
- `GROUP_CHAT_ID`

## Known limitations in current implementation

- Current production bulletin flow is still Veneto-only.
- Rendering depends on external HTML/SVG stability of source pages.
- Multi-region notifications are not yet wired into the daily sender.

For full analysis, see:

- `docs/TECH_ANALYSIS.md`

## Multi-region and public product direction

The project includes documentation for expanding to:

- multi-region Italy coverage,
- location-based risk query (GPS),
- login + subscription preferences,
- Telegram and email alert delivery,
- privacy and source-governance requirements for public launch.

See:

- `docs/DATA_SOURCES_ITALY.md`
- `docs/ROADMAP.md`

## Testing

Run the suite with:

```bash
PYTHONPATH=. pytest -q
```

## Run all collectors

To run all currently implemented collectors and persist their raw and parsed payloads:

```bash
python scripts/run_all_collectors.py --fixtures
```

This is the safest local mode because it uses the checked-in fixtures for Veneto, Emilia-Romagna and Toscana.

To try live sources instead:

```bash
python scripts/run_all_collectors.py
```

To enable SSL verification for live sources:

```bash
python scripts/run_all_collectors.py --verify-ssl
```

Each successful run prints the paths of:

- the raw payload JSON for that collector
- the parsed normalized JSON for that collector
- the aggregated daily JSON combining all successful collectors

Generated files are written under [.dev-output/connectors](.dev-output/connectors), typically:

- [.dev-output/connectors/veneto/latest/raw.json](.dev-output/connectors/veneto/latest/raw.json)
- [.dev-output/connectors/veneto/latest/parsed.json](.dev-output/connectors/veneto/latest/parsed.json)
- [.dev-output/connectors/emilia_romagna/latest/parsed.json](.dev-output/connectors/emilia_romagna/latest/parsed.json)
- [.dev-output/connectors/toscana/latest/parsed.json](.dev-output/connectors/toscana/latest/parsed.json)
- [.dev-output/connectors/daily/latest.json](.dev-output/connectors/daily/latest.json)

To inspect the aggregate quickly from shell:

```bash
python -m json.tool .dev-output/connectors/daily/latest.json | head -n 80
```

## Disclaimer

This tool is intended to improve access to official information, not replace official directives from Civil Protection authorities.
