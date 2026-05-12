# Phase 1 Task Breakdown & Jira Card Template

This historical task breakdown has been consolidated into [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Keep this file only as an archive pointer until it is removed entirely.

For the active tactical plan and task structure, use [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md).

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
