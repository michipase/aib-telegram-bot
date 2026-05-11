# Implementation Plan - Multi-Region AIB Ingestion (Phase 1-2)

**Status:** DRAFT (Ready for Dev Team Kickoff)  
**Prepared:** 2026-05-11  
**Target Completion:** Phase 1 Week 6-8 (Veneto production baseline + 2 pilot regions)  

---

## Executive Summary

This document outlines the practical implementation roadmap for the multi-region wildfire bulletin ingestion system (AIB - Antincendio Boschivo). It translates the source registry (`sources.yml`) and readiness tiers into executable work breakdown, dependencies, and go/no-go criteria.

**Phase 1 Scope:** Production Veneto baseline → 2 additional pilot regions (Emilia-Romagna + Toscana)  
**Phase 2 Scope:** Geolocation API + spatial layer + progressively add 9+ more regions  

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLIENT LAYER (External)                      │
│  - User Telegram Bot                                             │
│  - Geographic query API (/risk?lat=X&lon=Y)                     │
│  - Admin console (source monitoring)                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    INGESTION LAYER (Phase 1)                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Connector Framework (collectors/)                       │   │
│  │  - Base class: Connector(ABC)                            │   │
│  │  - Concrete: VenetoConnector, EmiliaConnector, etc.      │   │
│  │  - Methods: fetch(), parse(), validate(), extract_meta()│   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────────────┐   │
│  │  Source Registry Cache (sources.yml in memory)           │   │
│  │  - URL mapping, parser hints, fallback chain            │   │
│  └──────────────┬───────────────────────────────────────────┘   │
│                 │                                                 │
│  ┌──────────────▼───────────────────────────────────────────┐   │
│  │  Normalized Data Schema (docs/DATA_SOURCES_ITALY.md)    │   │
│  │  - risk_level, source_id, zone_id, timestamp, etc.      │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                    STORAGE LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Database (PostgreSQL + PostGIS for Phase 2)            │   │
│  │  - raw_bulletins (audit table)                          │   │
│  │  - current_risk (normalized, indexed by zone_id)        │   │
│  │  - zones (geospatial boundary geometries)               │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Cache (Redis) - Phase 2 addition                       │   │
│  │  - "zone_id → risk" TTL 1h                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Phase 1 Detailed Timeline (6-8 Weeks)

### Week 0 (Setup & Prerequisites) - 1 week

**Owner:** DevOps + Tech Lead

**Deliverables:**
- [ ] Database schema finalized: `raw_bulletins`, `current_risk`, `sources_metadata`
- [ ] Docker compose env setup with PostgreSQL + test data
- [ ] CI/CD pipeline stub: connector unit test runner
- [ ] Dev environment validated on each team member's local

**Dependencies:**
- Finalized normalized schema (from `DATA_SOURCES_ITALY.md`)
- Database access credentials for staging

**Success Criteria:**
- `make test-db-local` passes
- Sample fixture data loads and queries work
- Team can run connectors locally

---

### Week 1 (Framework + Veneto Refactor) - 1 week

**Owner:** Senior Backend Dev + QA

**Task Breakdown:**

#### 1.1 - Connector Base Framework
- **Location:** `collectors/base.py`
- **Implement:**
  ```python
  class Connector(ABC):
      def __init__(self, source_id: str, config: dict)
      def fetch_source(self) -> bytes  # raw payload
      def parse_bulletin(self, raw: bytes) -> List[RiskEntry]  # schema-compliant
      def validate_schema(self, entries: List[RiskEntry]) -> bool
      def extract_metadata(self) -> SourceMetadata  # timestamp, confidence
  ```
- **Tests:** 5 unit tests covering fetch/parse/validate happy path + error cases
- **Estimate:** 2 days

#### 1.2 - Refactor Veneto Connector
- **Location:** `collectors/veneto.py`
- **Input:** Refactor hardcoded logic from `main.py`
- **Extend:** Add `verify_ssl=True`, timeout handling, retry logic
- **Tests:** 8 unit tests (include sample `fwi.json` fixture)
- **Estimate:** 2 days

#### 1.3 - Ingestion Orchestrator (Scheduler)
- **Location:** `collectors/orchestrator.py`
- **Implement:**
  - Load `sources.yml` config
  - Cyclic job scheduler (APScheduler or similar)
  - For each enabled source: instantiate Connector → fetch → parse → store → log
  - Fallback chain: source A fails → try fallback source
- **Tests:** 3 integration tests (mock HTTP responses)
- **Estimate:** 2 days

**Deliverables:**
- [ ] `collectors/base.py` merged + code review approved
- [ ] `collectors/veneto.py` refactored + regression tests pass
- [ ] `collectors/orchestrator.py` live + test data flowing to DB
- [ ] Veneto ingestion CI pipeline green

**Success Criteria:**
- Veneto daily bulletins fetched and normalized without errors
- <1% ingestion failure rate on local test runs
- Structured logs available for troubleshooting

---

### Week 2 (Emilia-Romagna HTML Parser) - 1 week

**Owner:** Backend Dev + QA

**Task Breakdown:**

#### 2.1 - Emilia-Romagna HTML Parser
- **Location:** `collectors/emilia_romagna.py`
- **Challenge:** HTML table scraping + CSS selector strategy
- **Input:** Sample HTML bulletin pages from https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi
- **Implement:**
  - `BeautifulSoup` to extract zone data
  - Zone ID mapping: HTML table → normalized schema
  - Handle missing/null data gracefully
- **Tests:** 10 unit tests (5+ fixture HTML pages covering edge cases)
- **Estimate:** 3 days

#### 2.2 - Source Fallback Chain (ER)
- **Implementation:**
  - If ER API fails → fallback to HTML scraping URL
  - If both fail → fallback to DPC national context
- **Tests:** 2 integration tests (mock timeout + 404)
- **Estimate:** 1 day

**Deliverables:**
- [ ] `collectors/emilia_romagna.py` + fixture pages merged
- [ ] Fallback chain tested in orchestrator
- [ ] ER zone mapping validated against reference set

**Success Criteria:**
- HTML parser correctly extracts ≥95% of zones from sample pages
- Fallback triggers appropriately on network errors
- Normalized data matches schema validation

---

### Week 3 (Toscana PDF Parser + 3-Region Validation) - 1 week

**Owner:** Backend Dev + QA Lead

**Task Breakdown:**

#### 3.1 - Toscana PDF/HTML Parser
- **Location:** `collectors/toscana.py`
- **Challenge:** Mixed PDF + HTML handling
- **Input:** Sample bulletins from https://www.protezionecivilecomunale.toscana.it
- **Implement:**
  - PDF text extraction (PyPDF2 or pdfplumber)
  - HTML fallback (portal has both)
  - Zone ID mapping + confidence scoring (PDF < HTML readability)
- **Tests:** 8 unit tests (4 PDF fixtures + 4 HTML fixtures)
- **Estimate:** 3 days

#### 3.2 - 3-Region Integration Validation
- **Scope:** Veneto + Emilia-Romagna + Toscana live ingestion for 1 week
- **Monitoring:**
  - Daily check on fetch success rates
  - Data quality spot-checks (zone IDs match reference)
  - Latency monitoring (parse time per region)
  - Alert on stale bulletins (>6h old)
- **Tests:** 5 integration tests (multi-region orchestration)
- **Estimate:** 2 days

**Deliverables:**
- [ ] `collectors/toscana.py` + fixtures merged
- [ ] 3-region ingestion live in staging for UAT
- [ ] Monitoring dashboard (Grafana or simple CSV export)
- [ ] Go/No-go decision: ready to promote to prod?

**Success Criteria:**
- All 3 regions fetch + parse daily without manual intervention
- Average fetch latency <5s per region
- Zone ID mapping 100% correct on validation set
- Data freshness <2h old every day

---

### Week 4 (Hardening + Production Deployment) - 1 week

**Owner:** DevOps + Backend Lead

**Task Breakdown:**

#### 4.1 - Error Handling & Retry Logic
- **Location:** `collectors/orchestrator.py` + connectors
- **Implement:**
  - Exponential backoff: 1s, 2s, 4s, 8s, 16s max
  - Transient vs. permanent error differentiation
  - Circuit breaker pattern (disable source if >3 consecutive failures)
- **Tests:** 4 unit tests (simulate various failure modes)
- **Estimate:** 1 day

#### 4.2 - Structured Logging & Alerting
- **Location:** Logging config + Slack/email alerts
- **Implement:**
  - JSON logs with context (source_id, region, timestamp, error_type)
  - Alert on: ingestion failure, stale data, schema validation failure
  - Runbook links in alert messages
- **Tests:** 2 integration tests (alert triggers)
- **Estimate:** 1 day

#### 4.3 - Security Hardening
- **Location:** `main.py` + collectors
- **Implement:**
  - Remove `verify=False` from all requests (proper SSL cert validation)
  - Secret management for source credentials (if any)
  - Request timeouts enforced (connect=5s, read=10s)
- **Tests:** 2 security tests (cert validation, timeout enforcement)
- **Estimate:** 1 day

#### 4.4 - Production Deployment Checklist
- Database backups configured
- Rollback procedure documented
- On-call runbook distributed
- Monitoring alerts configured in production
- 24h test run: all 3 regions without intervention
- **Estimate:** 1 day

**Deliverables:**
- [ ] All retries + error handling merged
- [ ] Logging + alerting live in staging
- [ ] Production database + secrets setup complete
- [ ] Go/No-go prod launch meeting

**Success Criteria:**
- Production deployment completed with zero downtime
- Monitoring alerts verified and on-call acknowledged
- All 3 regions healthy 24h post-launch

---

### Weeks 5-8 (Phase 2 Prep + Documentation)

**Owner:** Full team

**Tasks:**
1. Collect learnings from Week 1-4 into Phase 2 backlog
2. Prepare geospatial layer design (PostGIS schema)
3. Parallel work: Document existing processes into runbook
4. Plan Tier 2 region expansion (4 additional regions by week 12)

---

## Task Breakdown by Tier

### Tier 1 (Ready/High Priority Regions)

| Region | Parser Type | Owner | Duration | Dependencies | Status |
|---|---|---|---|---|---|
| **Veneto** | JSON API | Senior Dev | 2d | Schema finalized | Week 1 |
| **Emilia-Romagna** | HTML table | Mid Dev | 3d | Veneto framework done | Week 2 |
| **Toscana** | PDF + HTML | Mid Dev | 3d | ER parser template | Week 3 |
| **FVG** (WMS) | WMS/WFS | GIS Specialist | 4d | PostGIS setup | Week 6+ |
| **Bolzano/Trento** | HTML structured | Junior Dev | 3d each | ER template | Week 8+ |

### Tier 2 (Medium Priority)

| Region | Parser Type | Est. Duration | Notes |
|---|---|---|---|
| Lazio | HTML/PDF | 3d | Mixed content; moderate complexity |
| Sicilia | HTML/PDF | 3d | Island region; seasonal gate |
| Sardegna | HTML/PDF | 3d | Seasonal concentration; fallback CFS |
| Piemonte | HTML/PDF | 3d | Seasonal; endpoint stability check |
| Lombardia | HTML + KML | 3d | KML export parsing possible |

### Tier 3-4 (Backlog)

| Region | Parser Type | Est. Duration | Notes |
|---|---|---|---|
| Liguria | HTML scraping | 2d | ARPAL; API timeout issue |
| Marche, Calabria, Abruzzo | HTML/PDF | 2d each | Seasonal; simpler HTML |
| Basilicata, Molise, Puglia | Contact-based | TBD | Manual coordination required |

---

## Directory Structure & File Organization

```
aib-telegram-bot/
├── collectors/
│   ├── __init__.py
│   ├── base.py                    # Abstract Connector class
│   ├── orchestrator.py            # Scheduler + coordination
│   ├── veneto.py                  # VenetoConnector (JSON API)
│   ├── emilia_romagna.py          # EmiliaConnector (HTML scraping)
│   ├── toscana.py                 # ToscanaConnector (PDF + HTML)
│   ├── fvg.py                     # FVGConnector (WMS/WFS) [Phase 2]
│   └── tier2/
│       ├── lazio.py
│       ├── sicilia.py
│       └── ... (other T2 regions)
│
├── tests/
│   ├── collectors/
│   │   ├── test_base.py
│   │   ├── test_veneto.py
│   │   ├── test_emilia_romagna.py
│   │   ├── test_toscana.py
│   │   └── fixtures/
│   │       ├── veneto_sample_fwi.json
│   │       ├── emilia_romagna_sample_page.html
│   │       ├── toscana_sample_bulletin.pdf
│   │       └── ...
│   └── integration/
│       ├── test_orchestrator.py
│       └── test_multi_region_flow.py
│
├── schemas/
│   ├── normalized_risk_entry.py   # Pydantic model for normalized data
│   └── source_metadata.py         # Metadata model
│
├── db/
│   ├── models.py                  # SQLAlchemy ORM models
│   ├── migrations/                # Alembic DB migrations
│   └── seeds/
│       └── test_data.sql          # Test fixtures
│
├── docs/
│   ├── ROADMAP.md                 # (updated: Phase 1-2 weekly breakdown)
│   ├── OFFICIAL_AIB_SOURCES_ITALY.md
│   ├── IMPLEMENTATION_PLAN.md     # (this file)
│   ├── DATA_SOURCES_ITALY.md      # (normalized schema reference)
│   └── RUNBOOK.md                 # Operational runbook [Phase 1 Week 7]
│
├── sources.yml                    # Source registry (all 25 sources)
└── main.py                        # Entry point (refactored for orchestrator)
```

---

## Dependency Management & Critical Path

```
┌─────────────────────┐
│   Week 0: Prerequisites
│   - DB schema
│   - CI/CD setup
└────────────┬────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│   Week 1: Framework + Veneto
│   - Base Connector class
│   - Veneto refactor + test
│   - Orchestrator basics
└────────────┬────────────────────────────┘
             │
        ┌────┴────┬────────────────┐
        ▼         ▼                ▼
   Week 2      Week 3           Week 4
   Emilia-     Toscana          Hardening
   Romagna     + 3-Reg          + Prod
   HTML        validation       Deploy
   parser
        │         │                │
        └────┬────┴────────┬───────┘
             ▼             ▼
      ┌──────────────────────────┐
      │   Week 5+ Phase 2 Prep
      │   - PostGIS setup
      │   - Geospatial layer
      │   - Tier 2 region queue
      └──────────────────────────┘
```

**Critical Path Milestones:**
1. Base Connector class done → blocks all region implementations
2. Veneto refactored → template for other JSON-based sources
3. HTML parser template (ER) → template for HTML/PDF scrapers
4. 3-region validation pass → gates production deployment
5. Prod monitoring healthy 24h → Stage gate for Phase 2

---

## Testing Strategy & Validation

### Unit Tests

**Per Connector:**
- Happy-path fetch + parse (1 test)
- Schema validation passes (1 test)
- Malformed data rejection (1 test)
- HTTP error handling (1 test)
- Timeout + retry behavior (1 test)
- Zone ID mapping correctness (2 tests with >5 samples each)

**Total:** 8 tests per connector

**Fixtures:**
- Real sample bulletins from each region (1-3 examples)
- Edge cases: missing fields, null values, encoding issues

### Integration Tests

**Orchestrator:**
- Multi-region parallel fetch (1 test)
- Fallback chain trigger on failure (1 test)
- Stale data detection (1 test)
- Database transaction rollback on schema violation (1 test)
- Concurrent connector runs (1 test)

**Total:** 5 tests

### Validation Set

**Per Region (after Week 3):**
1. **Zone mapping:** Map top 10 sample zones → expected zone IDs (100% match required)
2. **Data freshness:** Ingeston runs daily → data <2h old
3. **Absence errors:** No SQL constraint violations or parse exceptions
4. **Fallback activation:** Manually disable primary source → verify fallback activates within 2 min

---

## Risk Register & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| **HTML scraping brittle** (T2-T3 regions change portal layouts mid-way) | Medium | High | Maintain 2+ CSS selector variants; monthly portal check; alert on parse % drop |
| **API rate limiting** (ARPAE, others) | Medium | Medium | Exponential backoff + circuit breaker; fallback to HTML scraping |
| **Network latency** (slow regional portals) | High | Low | Timeout=10s; async fetch where possible; cache aggressively |
| **Schema evolution** (regions add/remove zones mid-season) | Low | Medium | Schema versioning; notification from Civil Protection contact; gradual rollout |
| **Database size explosion** (raw_bulletins audit table) | Low | High | Archive raw data daily to cold storage; retention policy (90 days online) |
| **Prod downtime during Phase 1** | Low | High | Canary deployment; feature flag per region; rollback plan tested |
| **FWI/EFFIS API unavailability** (EU service issues) | Low | Low | Fallback to regional sources only; graceful degradation |

---

## Success Criteria (End of Phase 1, Week 8)

### Functional
- [ ] Veneto + ER + Toscana ingesting daily without manual intervention
- [ ] All normalized data passing schema validation (100%)
- [ ] Fallback chain verified (tested + logs) for each region
- [ ] Zone ID mapping validated for pilot regions (100% accuracy on reference set)

### Performance
- [ ] P95 ingestion latency per region: <10s
- [ ] Database query (current risk by zone_id): <100ms
- [ ] Daily ingestion success rate: ≥99% (1 failure per 100 runs acceptable)

### Operational
- [ ] Monitoring alerts live + acknowledged by on-call
- [ ] Runbook completed + team trained
- [ ] CI pipeline green for all tests (no flakes >1% rate)
- [ ] Production deployment completed with zero downtime
- [ ] 24h health check post-prod-deploy passed

### Documentation
- [ ] All connectors have docstrings + module-level comments
- [ ] Test fixtures documented (source, date fetched, notes)
- [ ] Runbook with troubleshooting section completed

---

## Phase 2 (Weeks 9-14): Geolocation + API

Once Phase 1 stabilized (metrics green for 1 week):

1. **PostGIS Layer:** Import ISTAT zone boundaries + precompute spatial indexes
2. **Reverse Geocoding:** Implement point-in-polygon lookup (<5ms latency)
3. **API Endpoint:** `GET /risk?lat=X&lon=Y` with normalized response schema
4. **Cache Layer:** Redis integration for zone → risk mapping (TTL 1h)
5. **T2 Region Queue:** Parallel implementation of 4-5 additional regions
6. **API Documentation:** OpenAPI/Swagger schema published

**Target:** API live with 3-7 regions by week 14.

---

## Go/No-Go Decision Gates

### Gate 1: End of Week 1
**Question:** Is Veneto connector working as expected?
- Criteria: Daily fetch succeeds ≥99%, parse latency <5s
- **Go:** Proceed to Week 2 ER implementation
- **No-Go:** Extend Week 1; debug + refactor base framework

### Gate 2: End of Week 2
**Question:** Are HTML scrapers viable for multi-region scale?
- Criteria: ER parser achieves ≥95% zone accuracy; fixture coverage >80%
- **Go:** Proceed to Week 3 Toscana + validation
- **No-Go:** Pivot to direct API contacts; skip HTML scrapers; contact ARPAE/ARPAL for API deprecation timelines

### Gate 3: End of Week 3
**Question:** Can we handle 3-region ingestion stably?
- Criteria: All 3 regions ≥99% success, no schema violations, fallback tested
- **Go:** Proceed to Week 4 hardening + prod deployment
- **No-Go:** Extend Week 3-4; fix data quality issues; add more fixtures

### Gate 4: End of Week 4
**Question:** Is production deployment safe?
- Criteria: 24h staging test passed, monitoring verified, team trained
- **Go:** Deploy to production
- **No-Go:** Delay to next sprint; complete runbook + on-call handoff first

---

## Communication & Stakeholders

**Weekly Standup (Tuesdays 10:00):**
- Status on Phase 1 tasks (blockers, risks)
- Demo of working connectors
- Decisions on Tier 2 region prioritization

**Stakeholder Updates (Fridays 15:00):**
- Progress vs. timeline
- Risk escalations
- Phase 2 planning

**On-Call Handoff (Week 5):**
- Production monitoring intro
- Runbook walkthrough
- Escalation procedures

---

## Appendix: Quick Reference

### Sample Connector Skeleton

```python
# collectors/emilia_romagna.py

from collectors.base import Connector, RiskEntry
from datetime import datetime
from bs4 import BeautifulSoup

class EmiliaRomagnaConnector(Connector):
    source_id = "emilia_romagna"
    
    def fetch_source(self) -> bytes:
        import requests
        resp = requests.get(
            "https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi",
            timeout=(5, 10)
        )
        resp.raise_for_status()
        return resp.content
    
    def parse_bulletin(self, raw: bytes) -> List[RiskEntry]:
        soup = BeautifulSoup(raw, "html.parser")
        table = soup.find("table", class_="bollettino-aib")
        
        entries = []
        for row in table.find_all("tr")[1:]:  # Skip header
            cells = row.find_all("td")
            zone_id = cells[0].text.strip()
            risk_level = cells[1].text.strip()
            
            entries.append(RiskEntry(
                source_id=self.source_id,
                zone_id=zone_id,
                risk_level_norm=self._normalize_risk(risk_level),
                published_at=datetime.utcnow(),
            ))
        
        return entries
```

### Running Tests Locally

```bash
# Unit tests for Veneto connector
pytest tests/collectors/test_veneto.py -v

# All collector tests
pytest tests/collectors/ -v --cov=collectors

# Integration test (3-region orchestrator)
pytest tests/integration/test_orchestrator.py -v

# Quick validation script
python -m collectors.orchestrator --dry-run --region veneto
```

---

**Next Step:** Schedule team kickoff meeting (Week 0) to finalize schedule, assign owners, and unblock prerequisites.
