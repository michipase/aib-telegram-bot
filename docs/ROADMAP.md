# Product & Engineering Roadmap

Last updated: 2026-05-11

## Vision

Build a public, trustworthy, and easy-to-use wildfire risk assistant for Italy that can:

- infer risk from user GPS position,
- explain what is safe/not safe in plain language,
- notify users via Telegram or email.

## Principles

- Official data first.
- Explainability over black-box scoring.
- Privacy by design.
- Graceful degradation when sources fail.

## Phase 0 - Stabilize current bot (1-2 weeks)

Deliverables:

- Refactor `main.py` into modules (`collector`, `transform`, `render`, `notify`).
- Remove `verify=False` and improve request timeouts/retries.
- Add structured logs and alerting on failed daily runs.
- Clean dependencies to minimum required.
- Add complete docs and runbook.

Exit criteria:

- Daily Veneto bulletin delivery with <1% monthly failure.
- Reproducible local setup and CI run.

## Phase 1 - Multi-region ingestion MVP (3-6 weeks)

Deliverables:

- Connector framework with normalized schema.
- Integrate 3 regions (including Veneto).
- Source metadata registry (`sources.yml`): URL, parser type, cadence, legal notes.
- Raw payload archival for audit/debug.

Exit criteria:

- 3 regions active with automated ingestion and validation checks.
- Source freshness dashboard.

## Phase 2 - Geolocation + API (4-6 weeks)

Deliverables:

- Geospatial layer management and point-in-polygon lookup.
- API endpoint: `GET /risk?lat=...&lon=...`.
- Risk response with:
  - official level,
  - confidence,
  - source timestamp,
  - plain-language recommendations.

Exit criteria:

- P95 API latency <300ms for lookup endpoint.
- Correct zone mapping on test set.

## Phase 3 - Authentication and subscriptions (3-5 weeks)

Deliverables:

- User accounts and login.
- Newsletter subscription with double opt-in.
- Channel preferences (Telegram, email, both).
- Notification policies:
  - daily digest,
  - risk change alerts,
  - severe risk immediate alerts.

Exit criteria:

- End-to-end consent-compliant onboarding.
- Unsubscribe and preference updates self-service.

## Phase 4 - Public web app UX (4-8 weeks)

Deliverables:

- Mobile-first interface with current risk, map, trend, and guidance.
- Location permission flow and manual location fallback.
- Explainability panel: "why this risk" + source attribution.
- Accessibility baseline (WCAG-oriented).

Exit criteria:

- Usability tests with volunteer groups (AGESCI + partner associations).
- Core journeys completed in <3 interactions.

## Phase 5 - Nationwide scaling and operations (ongoing)

Deliverables:

- Complete coverage for all regions/provinces.
- SLOs and incident response process.
- Abuse/rate limit protection.
- Public status page and changelog.

Exit criteria:

- Production reliability targets met for 3 consecutive months.

## Cross-cutting tracks

## Data quality

- Schema validation at ingestion.
- Outlier and stale-data detection.
- Manual override workflow for source anomalies.

## Security and privacy

- Secret management and key rotation.
- Encryption in transit and at rest.
- Data minimization for geolocation.

## Governance

- Source legal registry and attribution policy.
- Transparency note: tool supports decisions but does not replace official directives.

## Suggested KPIs

- Data freshness SLA by region.
- Notification delivery success rate.
- False/late alert rate.
- User retention and opt-out rate.
- Mean time to detect source failures.
