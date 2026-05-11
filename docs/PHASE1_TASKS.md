# Phase 1 Task Breakdown & Jira Card Template

**Project:** AIB Multi-Region Ingestion (Phase 1)  
**Epic:** Connector Framework + 3-Region Pilot (Weeks 0-8)  

---

## Work Breakdown Structure

```
EPIC: Phase 1 Ingestion (6-8 weeks)
│
├── TASK BATCH 0: Prerequisites (Week 0 - 1 week)
│   ├── Schema finalization & DB setup
│   ├── Docker Compose env + CI/CD stub
│   └── Team environment setup
│
├── TASK BATCH 1: Framework + Veneto (Week 1 - 1 week)
│   ├── Connector base class (base.py)
│   ├── Veneto refactor (veneto.py) + tests
│   ├── Orchestrator + scheduler
│   └── Ingestion pipeline validation
│
├── TASK BATCH 2: Emilia-Romagna HTML Parser (Week 2 - 1 week)
│   ├── HTML parser implementation
│   ├── CSS selector + data mapping
│   ├── Unit tests (10+)
│   └── Fallback chain integration
│
├── TASK BATCH 3: Toscana PDF Parser + 3-Region Validation (Week 3 - 1 week)
│   ├── PDF/HTML parser (toscana.py)
│   ├── Zone mapping + confidence scoring
│   ├── Integration test (3-region)
│   └── Monitoring dashboard setup
│
├── TASK BATCH 4: Hardening + Production Deployment (Week 4 - 1 week)
│   ├── Error handling & retry logic
│   ├── Structured logging + alerting
│   ├── Security hardening (SSL, timeouts)
│   ├── Prod database setup
│   └── Production deployment + validation
│
└── TASK BATCH 5: Phase 2 Prep (Weeks 5-8)
    ├── Postmortem + learnings doc
    ├── PostGIS + geospatial layer design
    ├── Tier 2 region queue preparation
    └── Phase 2 kickoff
```

---

## Jira Card Templates

### TASK: (Week 0) Database Schema & Models Finalization

```
Title: DB Schema finalization: raw_bulletins, normalized_risk, sources_metadata
Type: Story
Epic: Phase 1 Ingestion
Priority: P0 (Blocker)
Duration: 2 days
Owner: Senior Backend Dev
Assignee: [Assign to DB specialist]

Description:
Finalize and test database schema for ingestion layer:
- raw_bulletins table (audit trail, raw payload storage)
- current_risk table (normalized entries, indexed by zone_id)
- sources_metadata table (source config, last_fetch, status)

Acceptance Criteria:
  ✓ Schema diagram documented (miro/lucidchart)
  ✓ Alembic migration scripts created and tested locally
  ✓ Sample data loads without errors
  ✓ Queries for "latest risk by zone" < 100ms
  ✓ Team can run 'make init-db-local' and have working schema

Definition of Done:
  ✓ Code reviewed
  ✓ CI test passes (schema validation)
  ✓ Docker compose includes DB with seeded data
  ✓ README updated with DB setup steps

Blockers/Dependencies:
  - Requires finalized normalized schema from DATA_SOURCES_ITALY.md
```

### TASK: (Week 1) Base Connector Class Implementation

```
Title: Implement abstract Connector base class
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker)
Duration: 2 days
Owner: Senior Backend Dev

Description:
Create abstract base class for all regional connectors to ensure consistent interface:

Key Methods:
  - fetch_source() → raw bytes/response
  - parse_bulletin(raw) → List[RiskEntry]
  - validate_schema(entries) → bool
  - extract_metadata() → SourceMetadata

Acceptance Criteria:
  ✓ Base class defined in collectors/base.py
  ✓ Abstract methods with clear docstrings
  ✓ Logging infrastructure built-in
  ✓ Timeout + retry handling generic
  ✓ 5 unit tests covering base behaviors

Definition of Done:
  ✓ Code reviewed by 2nd senior dev
  ✓ CI tests pass (100% coverage)
  ✓ Used by Veneto connector implementation (Week 1)
  ✓ Integration guide added to DEVELOPER_GUIDE.md

Blockers/Dependencies:
  - Requires schema finalization (previous task)
  - Must be done before any regional connectors
```

### TASK: (Week 1) Refactor Veneto Connector

```
Title: Refactor Veneto connector into new Connector framework
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Critical Path)
Duration: 2 days
Owner: Backend Dev (Mid-level)

Description:
Refactor existing monolithic Veneto ingestion code (from main.py) into new framework:
- Inherit from Connector base class
- Remove verify=False + hardcoded logic
- Add proper retry + timeout handling
- Implement SSL cert validation
- Create comprehensive test suite

Input Files:
  - main.py (current FWI.json logic)
  - Zone mapping from zone.json

Output Files:
  - collectors/veneto.py
  - tests/collectors/test_veneto.py
  - tests/collectors/fixtures/veneto_sample_fwi.json

Acceptance Criteria:
  ✓ Daily AIB fetch succeeds (JSON parsing correct)
  ✓ Schema validation passes (all fields present)
  ✓ 8 unit tests covering normal + error cases
  ✓ Fixture FWI.json loaded and parsed correctly
  ✓ No verify=False in code

Definition of Done:
  ✓ Code reviewed + approved
  ✓ ≥95% unit test coverage
  ✓ Staging environment ingests daily bulletins
  ✓ Zone ID mapping 100% correct vs. zone.json baseline

Blockers/Dependencies:
  - Requires base Connector class (previous task)
  - Requires DATABASE schema (Week 0)
```

### TASK: (Week 1) Orchestrator + Scheduler Implementation

```
Title: Implement Connector orchestrator + scheduling system
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Critical Path)
Duration: 2 days
Owner: Backend Dev (Mid-level)

Description:
Build orchestration layer that:
1. Loads sources.yml configuration
2. Instantiates regional connectors dynamically
3. Schedules daily ingestion runs (APScheduler or similar)
4. Implements fallback chain (Primary → Fallback A → Fallback B)
5. Logs each fetch/parse/store event
6. Handles connector errors gracefully

Architecture:
  - IngestionOrchestrator class loads sources.yml
  - PeriodicJob spawns Connector for each enabled source
  - Results (success/error) logged + stored in sources_metadata
  - Email/Slack alert on source failure

Acceptance Criteria:
  ✓ Orchestrator loads and validates sources.yml
  ✓ Veneto connector fetches daily without errors for 3 days local test
  ✓ Fallback chain tested (mock primary failure → fallback activates)
  ✓ Structured logs (JSON) with source_id, timestamp, error_type
  ✓ 4 integration tests

Definition of Done:
  ✓ Code review approved
  ✓ Local dry-run successful for 1 week
  ✓ Prometheus/StatsD integration stub (ready for monitoring in Week 4)

Blockers/Dependencies:
  - Requires base Connector (previous task)
  - Requires Veneto refactor (parallel task)
```

### TASK: (Week 2) Emilia-Romagna HTML Parser Implementation

```
Title: Implement Emilia-Romagna HTML parser connector
Type: Task
Epic: Phase 1 Ingestion
Priority: P1 (High)
Duration: 3 days
Owner: Backend Dev (Intermediate)

Description:
Build HTML table scraper for ARPAE Emilia-Romagna regional bulletin:
- Fetch HTML from https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi
- Parse table using CSS selectors (BeautifulSoup)
- Map zone names → normalized zone IDs
- Extract risk level + FWI index if available
- Handle missing/null data gracefully

Input Files:
  - Real HTML samples from ARPAE portal (2-3 fixture pages)
  - Zone mapping: ER region zones

Output Files:
  - collectors/emilia_romagna.py
  - tests/collectors/test_emilia_romagna.py
  - tests/collectors/fixtures/emilia_romagna_sample_page_*.html

Acceptance Criteria:
  ✓ HTML parser successfully extracts ≥95% of zones
  ✓ Zone ID mapping 100% accurate (vs. reference list)
  ✓ 10 unit tests (happy path, edge cases, malformed data)
  ✓ Fallback URL defined in sources.yml
  ✓ Timeout enforced (10s max)

Definition of Done:
  ✓ Code reviewed
  ✓ ≥90% coverage
  ✓ Fixture pages current (downloaded < 7 days ago)
  ✓ Zone mapping document included in PR

Blockers/Dependencies:
  - Requires base Connector (Week 1)
  - Requires zone mapping reference (provided in docs/)
  - Requires sample HTML from portal
```

### TASK: (Week 3) Toscana PDF + HTML Parser Implementation

```
Title: Implement Toscana PDF/HTML multi-format parser connector
Type: Task
Epic: Phase 1 Ingestion
Priority: P1 (High)
Duration: 3 days
Owner: Backend Dev (Intermediate)

Description:
Build mixed PDF/HTML parser for Toscana Protezione Civile bulletin:
- Support both PDF text extraction + HTML table parsing
- Fetch from https://www.protezionecivilecomunale.toscana.it
- Prefer HTML (higher readability) but fallback to PDF if needed
- Extract zones, risk levels, confidence scores
- Handle seasonal publication gaps

Technical Decisions:
- PDF parsing: pdfplumber or PyPDF2
- Zone mapping: Toscana-specific regions (11 zones)
- Confidence: HTML → HIGH, PDF → MEDIUM

Output Files:
  - collectors/toscana.py
  - tests/collectors/test_toscana.py
  - tests/collectors/fixtures/toscana_sample_page.html
  - tests/collectors/fixtures/toscana_sample_bulletin_*.pdf

Acceptance Criteria:
  ✓ HTML parser achieves ≥95% zone extraction
  ✓ PDF fallback works (tested with real PDF fixtures)
  ✓ 8 unit tests (HTML, PDF, malformed cases)
  ✓ Zone ID mapping 100% vs. reference
  ✓ Seasonal gates handled (publication only May-Oct)

Definition of Done:
  ✓ Code reviewed
  ✓ ≥85% coverage (PDF parsing harder to test)
  ✓ Real PDF + HTML fixtures included
  ✓ Seasonal boundary logic documented

Blockers/Dependencies:
  - Requires base Connector (Week 1)
  - Requires sample PDF + HTML from portal
  - Requires Emilia-Romagna parser as reference implementation
```

### TASK: (Week 3) Multi-Region Integration Test & Monitoring

```
Title: 3-Region integration test + basic monitoring dashboard
Type: Story
Epic: Phase 1 Ingestion
Priority: P1 (High)
Duration: 2 days
Owner: QA Lead + Backend Dev

Description:
Deploy 3-region ingestion (Veneto + ER + Toscana) to staging:
- Run live ingestion for 7 days
- Monitor success rates, data freshness, latency
- Spot-check zone mappings vs. reference
- Generate monitoring dashboard (Grafana or CSV)

Acceptance Criteria:
  ✓ All 3 regions fetch successfully ≥99% of the time (1 failure acceptable per week)
  ✓ Average latency per region < 10s
  ✓ Data freshness < 2h old daily
  ✓ Zone ID mapping validated on sample (20 zones per region)
  ✓ No schema validation errors in logs
  ✓ Dashboard shows these metrics

Definition of Done:
  ✓ 7-day staging run completed
  ✓ Monitoring dashboard shared with team
  ✓ Go/No-Go decision made (proceed to Week 4 or extend)
  ✓ Risk/learnings document started

Blockers/Dependencies:
  - Requires all 3 connectors ready (Veneto, ER, Toscana)
```

### TASK: (Week 4) Error Handling & Retry Logic

```
Title: Implement robust error handling + exponential backoff
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Prod Safety)
Duration: 1 day
Owner: Backend Dev (Senior)

Description:
Add production-grade error handling to orchestrator:
- Exponential backoff: 1s, 2s, 4s, 8s, 16s (max)
- Circuit breaker: disable source after 3 consecutive failures
- Transient vs. permanent error classification
- Graceful degradation (source A fails → use source B)
- Structured error logging

Error Types Handled:
  - HTTP 5xx → transient (retry)
  - HTTP 4xx (not 404) → transient (retry)
  - HTTP 404 → permanent (alert + skip)
  - Timeout → transient (retry with backoff)
  - Parse failure → investigate (log full payload)

Implementation:
  - DecoratorError handling in base.py
  - CircuitBreaker class (state: CLOSED, OPEN, HALF_OPEN)
  - Configuration in sources.yml per source

Acceptance Criteria:
  ✓ 4 unit tests covering backoff + circuit breaker
  ✓ Backoff timing correct (tested with mock time)
  ✓ Circuit breaker triggers after 3 failures
  ✓ Logs include error classification + retry count

Definition of Done:
  ✓ Code reviewed
  ✓ Local test passes (simulate failures)
  ✓ Prod-ready: tested with real network failures
```

### TASK: (Week 4) Structured Logging + Alerting

```
Title: Add structured JSON logging + Slack/email alerts
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Ops Visibility)
Duration: 1 day
Owner: Backend Dev (Senior)

Description:
Implement structured logging for operations visibility:
- JSON format: timestamp, source_id, region, error_type, stacktrace
- Log rotation: daily, 7-day retention
- Alert on:
  1. Source fetch failure (alert after 2 retries)
  2. Schema validation failure (alert immediately)
  3. Stale data (>6h old, alert once/day)
  4. Circuit breaker open (alert immediately)

Channels:
  - Slack: #aib-ingestion-alerts (prod-only)
  - Email: ops-on-call@corp.com (critical failures)
  - Logs: logs/ingestion.json (local + aggregated to ELK)

Acceptance Criteria:
  ✓ Logs contain all required fields (timestamp, source_id, error_type)
  ✓ Alert fired correctly on failure scenarios (tested)
  ✓ No alert spam (aggregation logic correct)
  ✓ ≥95% of errors logged

Definition of Done:
  ✓ Code reviewed
  ✓ Local alert test passed (manual Slack test)
  ✓ Log format documented for ops team
  ✓ Rotation policy verified
```

### TASK: (Week 4) Security Hardening

```
Title: Security review + SSL/timeout hardening
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Compliance)
Duration: 1 day
Owner: Security + Backend Lead

Description:
Ensure production-grade security:
- Remove all verify=False (SSL cert validation enabled)
- Enforce timeouts: connect=5s, read=10s
- Secret management (if credentials needed)
- Input validation (reject malformed data)
- Rate limiting awareness (regional APIs)

Security Checklist:
  ✓ No hardcoded secrets in code
  ✓ SSL verification enabled for all requests
  ✓ Timeouts enforced (no unbounded waits)
  ✓ Input sanitized (no code injection)
  ✓ Log redaction (no secrets in logs)

Acceptance Criteria:
  ✓ Security review approved
  ✓ 2 security tests pass (cert validation, timeout enforcement)
  ✓ Secrets stored in env/vault (not code)
  ✓ OWASP compliance checklist signed off

Definition of Done:
  ✓ Security team approval
  ✓ Penetration test (if required by policy)
  ✓ Prod deployment approval granted
```

### TASK: (Week 4) Production Database Setup & Migration

```
Title: Production DB setup + schema migration validation
Type: Task
Epic: Phase 1 Ingestion
Priority: P0 (Blocker - Deployment Gate)
Duration: 1 day
Owner: DevOps + Backend

Description:
Set up production PostgreSQL database:
- Allocate RDS or managed PostgreSQL instance
- Configure backups (daily, 30-day retention)
- Run schema migrations (Alembic)
- Load reference data (zone boundaries if applicable)
- Configure monitoring + alerts on DB health

Steps:
  1. Create prod DB instance (terraform or manual)
  2. Seed with reference data
  3. Test connection from app servers
  4. Backup policy confirmed
  5. Connect to monitoring system (CloudWatch, Datadog, etc.)

Acceptance Criteria:
  ✓ DB is reachable from app servers
  ✓ Schema migrations ran successfully
  ✓ Test data loaded correctly
  ✓ Backups configured (test restore procedure)
  ✓ Monitoring alerts working (CPU, disk, connections)

Definition of Done:
  ✓ DevOps approval
  ✓ Connection string provided to backend team
  ✓ Backup/restore process documented
```

---

## Sprint Velocity & Capacity Planning

### Recommended Team Composition

| Role | Weeks 0-4 | Weeks 5-8 |
|---|---|---|
| Senior Backend Dev | 50% (tech lead) | 30% (advisory) |
| Mid Backend Dev (2x) | 100% each | 80% each |
| Junior Backend Dev | 50% | 60% |
| QA/Test Lead | 50% | 60% |
| DevOps/Infra | 40% | 40% |
| **Total: 4.3 FTE** | **Weeks 0-4** | **Weeks 5-8** |

### Estimated Effort per Task (in person-days)

| Task | Estimate | Notes |
|---|---|---|
| DB Schema (Week 0) | 3d | Depends on schema complexity |
| Base Connector (Week 1) | 2d | Abstract design; reusable |
| Veneto Refactor (Week 1) | 2d | Refactoring + testing |
| Orchestrator (Week 1) | 2d | Scheduler + fallback logic |
| Emilia-Romagna (Week 2) | 3d | HTML parsing; zone mapping |
| Toscana (Week 3) | 3d | PDF + HTML mixed format |
| Integration Test (Week 3) | 2d | QA validation + monitoring |
| Error Handling (Week 4) | 1d | Exponential backoff + circuit breaker |
| Logging + Alerts (Week 4) | 1d | Structured logs + alerting |
| Security Hardening (Week 4) | 1d | SSL + timeout enforcement |
| Prod DB Setup (Week 4) | 1d | DevOps work |
| **TOTAL** | **22 person-days** | ~4-5 weeks for 2x Mid devs |

---

## Definition of Done (DoD) Checklist

All tasks must comply with:

- [ ] **Code**
  - [ ] PR created with clear description
  - [ ] ≥1 code review approval (2 for framework tasks)
  - [ ] CI pipeline green (tests + linting)
  - [ ] ≥80% test coverage (85% for critical paths)
  - [ ] No hardcoded secrets/URLs

- [ ] **Testing**
  - [ ] Unit tests written (happy path + edge cases)
  - [ ] Integration tests for multi-component tasks
  - [ ] Real fixture data used (not mocks)
  - [ ] Error cases validated

- [ ] **Documentation**
  - [ ] Docstrings added (module + functions)
  - [ ] README/inline comments for complex logic
  - [ ] Changes logged in CHANGELOG.md
  - [ ] Related docs (DEVELOPER_GUIDE, runbook) updated

- [ ] **Operations Readiness**
  - [ ] Alert/logging in place
  - [ ] Runbook section drafted
  - [ ] Known limitations documented
  - [ ] Rollback procedure clear

---

**Next Step:** Copy these cards into Jira; assign owners; schedule kickoff meeting for Week 0.
