# AIB Telegram Bot (Veneto) and National Expansion Plan

Unofficial project to publish daily wildfire risk updates (AIB) from official sources.

Current production behavior:

- Reads official Veneto daily data.
- Generates a risk map image and a summary table image.
- Sends both to Telegram on a daily schedule.

Public channel:
- https://t.me/AIBVenetoBollettini

## Why this project exists

Associations, volunteers, and citizens often struggle to quickly understand:

- what is safe vs unsafe in a specific area,
- whether conditions changed today,
- where to find reliable official updates.

This project aims to make official wildfire-risk information easier to consume.

## Current stack

- Python script runner
- Requests + BeautifulSoup for data retrieval/parsing
- Pandas for tabular transformation
- imgkit/wkhtmltoimage for rendering images
- python-telegram-bot for delivery
- GitHub Actions for daily execution

## Repository structure

- `main.py`: current end-to-end script (collect, transform, render, notify)
- `zone.json`: Veneto zone metadata
- `style/df_style.css`: style for generated risk table
- `.github/workflows/main.yml`: scheduled daily run
- `VERSION`: app version in MAJOR.MINOR.PATCH format
- `.githooks/pre-commit`: repository-managed hook for patch auto-bump
- `scripts/bump-version.sh`: patch bump helper script
- `docs/TECH_ANALYSIS.md`: technical code analysis and improvement areas
- `docs/DATA_SOURCES_ITALY.md`: research and source strategy for Italy-wide data
- `docs/ROADMAP.md`: product and engineering roadmap

## Data source in use today (Veneto)

- JSON risk data:
	- https://www.ambienteveneto.it/incendi/dati/FWI.json
- Map SVG page:
	- https://www.ambienteveneto.it/stazioni/incendi/venetorischio.html

## Local setup

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

## Versioning

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

- Script is monolithic and Veneto-only.
- Some network calls currently disable TLS verification.
- Scraping and rendering are coupled to external page structure.
- Error handling is broad in some sections, reducing observability.

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

## Disclaimer

This tool is intended to improve access to official information, not replace official directives from Civil Protection authorities.
