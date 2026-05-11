# Data Sources for an Italy-Wide Wildfire Risk Tool

Last updated: 2026-05-11

## Goal

Identify reliable sources to power a public-facing product that answers:

- Is it safe to perform activities in a specific location today?
- What is the current wildfire risk level and trend?
- Should users receive location-based alerts?

## Source selection criteria

- Official institutional origin whenever possible.
- Machine-readable format preferred (API, JSON, CSV, WMS/WFS).
- Stable update frequency and metadata.
- Clear usage terms/license.
- Geographic granularity usable for geolocation matching.

## Source categories

## 1) Institutional wildfire bulletins (regional)

Primary source category for legal/operational reliability.

Examples (to integrate via per-region adapters):

- Regione Veneto / ARPAV / Ambiente Veneto:
  - Current project source (`FWI.json` and map assets).
- Regional Civil Protection portals:
  - Daily/periodic bollettini AIB.
  - In some regions available as PDF, HTML tables, or map services.

Integration notes:

- Build one connector per region.
- Convert each region format into one normalized schema.
- Keep source URL + publication timestamp for traceability.

## 2) National Civil Protection context (Italy)

Use for authoritative context and national-level communication.

- Dipartimento della Protezione Civile:
  - wildfire risk communication pages,
  - campaign-level official notices,
  - risk guidance content.

Integration notes:

- Useful for policy messaging and user-facing explanations.
- Not always a direct daily geocoded risk feed, so combine with regional feeds.

## 3) Meteorological and drought indicators

Useful to improve predictive quality and explain risk changes.

Potential providers:

- Regional ARPA meteorological open datasets.
- National/international weather APIs with clear licenses.
- Copernicus climate/fire layers (where applicable and license-compatible).

Integration notes:

- Use as supporting indicators, not replacement for official local bulletins.
- Cache aggressively and monitor quota limits.

## 4) Active fire / hotspot detection

Useful for situational awareness.

Potential providers:

- Copernicus Emergency Management / EFFIS products.
- Satellite hotspot feeds (e.g., FIRMS-like services), if license permits.

Integration notes:

- Mark as "observed hotspots" not "forecast risk".
- Add confidence and timestamp fields in UI/API.

## 5) Geographic boundary datasets

Required to map GPS points to warning zones.

Potential providers:

- ISTAT administrative boundaries.
- Regional geospatial portals (WMS/WFS/GeoJSON/shapefiles).

Integration notes:

- Maintain versioned geospatial layers.
- Precompute spatial indexes for fast reverse lookup.

## 6) User communication channels

Delivery sources are internal systems, but policy constraints matter.

- Telegram Bot API (already used).
- Transactional email providers for newsletter/alerts.

Integration notes:

- Double opt-in for email.
- Explicit consent for geolocated alerts.
- Unsubscribe and preference center mandatory.

## Recommended normalized schema (minimum)

- `source_id` (string)
- `source_name` (string)
- `region` (string)
- `zone_id` (string)
- `zone_name` (string)
- `risk_index_raw` (number/string)
- `risk_level_norm` (enum: low, medium, high, very_high, unknown)
- `published_at` (datetime, UTC)
- `valid_for_date` (date, local)
- `geometry_ref` (zone geometry id)
- `source_url` (string)
- `ingested_at` (datetime)

## Compliance and legal checks before public launch

- Verify each source terms of use and redistribution rights.
- Add attribution per source in product UI/API docs.
- Publish privacy policy and data retention policy.
- GDPR records:
  - lawful basis for geolocation,
  - consent logs for newsletter,
  - DSR workflow (access/delete/export).

## Practical next research pass (execution checklist)

1. Inventory all 20 regions and autonomous provinces.
2. For each, collect:
   - official bulletin URL,
   - update schedule,
   - format type,
   - legal terms,
   - fallback endpoint/contact.
3. Rank connectors by complexity (easy/medium/hard).
4. Implement 3 pilot regions before full rollout.
