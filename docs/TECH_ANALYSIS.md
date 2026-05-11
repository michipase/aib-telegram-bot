# Technical Analysis (Current State)

Last updated: 2026-05-11

## What the project does today

`main.py` is a daily bot script that:

1. Downloads Veneto wildfire risk data from `FWI.json`.
2. Merges those values with zone labels in `zone.json`.
3. Builds:
   - a colorized table image,
   - a colorized Veneto SVG map image.
4. Sends both images to a Telegram group/channel.

The GitHub Action in `.github/workflows/main.yml` runs the script every day at 13:05 UTC.

## Positive points

- Uses an official regional source (`ambienteveneto.it`) for core daily data.
- Produces easy-to-read visual output for Telegram users.
- Automated daily execution via GitHub Actions.
- Environment variable fallback (`.env`) for local runs.

## Main technical limitations

### 1) Monolithic script

All logic is in one file (`main.py`): network I/O, data cleaning, rendering, and Telegram delivery.

Impact:
- Harder testing.
- Harder maintenance.
- Harder multi-region extension.

### 2) Scraping/rendering fragility

- HTML/SVG scraping depends on page structure (`<g id="GI_...">`).
- `imgkit` + `wkhtmltoimage` can be fragile in CI and adds system dependencies.

Impact:
- Breakage risk if source layout changes.
- More infra/setup complexity.

### 3) Security/network hygiene

`requests.get(..., verify=False)` disables TLS verification.

Impact:
- Lower transport security.
- Possible warning suppression of real certificate issues.

### 4) Data model constraints

- Local `zone.json` is static and Veneto-only.
- Hard-coded filter `id <= 26` excludes additional zone variants present in data.

Impact:
- Limited geographical coverage.
- Data updates require repo edits.

### 5) Error handling and observability

- Broad `except:` blocks hide failures.
- Minimal logging (`log.txt` opened but not structured logging).

Impact:
- Difficult debugging in production.
- Less transparent failures.

### 6) Dependency footprint

`requirements.txt` includes packages not directly used by the script.

Impact:
- Slower builds.
- Larger attack/dependency surface.

## Suggested target architecture

A modular pipeline:

- `collectors/`:
  - region-specific adapters (`veneto.py`, `sardegna.py`, ...)
  - each returns normalized records.
- `core/`:
  - normalization schema and validation.
  - geospatial point-in-zone lookup.
  - alert rules engine.
- `delivery/`:
  - Telegram sender.
  - email sender.
- `api/`:
  - endpoints for app/web clients.
- `scheduler/`:
  - periodic ingestion.
  - retry/dead-letter policy.

## Public service readiness checklist

- Replace scraping where possible with structured APIs/files (JSON/CSV/WMS/WFS).
- Add tests:
  - parser unit tests (fixtures),
  - end-to-end smoke tests.
- Add strict typing and linting.
- Implement structured logs and metrics.
- Define source attribution and license notices.
- Define privacy policy and GDPR flows (location + login + newsletter consent).

## Lightweight improvement opportunities (short term)

- Remove `verify=False`.
- Split script into functions/modules.
- Use direct SVG handling and image conversion fallback strategy.
- Introduce robust retries and explicit exceptions.
- Minimize dependencies in `requirements.txt`.
- Add `.env.example` and runbook docs.
