# Developer Guide - Implementing a New Regional Connector

**Last Updated:** 2026-05-11  
**Target Audience:** Backend developers implementing new region connectors

---

## Quick Start: Add a New Region in 5 Steps

### 1. Gather Source Information

From `sources.yml`, extract:
```yaml
source_id: "sicilia"
institution: "Protezione Civile Sicilia"
bulletin_url: "https://www.protezionecivilesicilia.it/web/protezionecivilesicilia"
parser_type: "html_pdf"  # or json_api, wms, etc.
update_cadence: "daily (May-August, extended)"
confidence: "HIGH"
```

### 2. Download Sample Bulletins

**For HTML regions:**
```bash
curl -L "https://www.protezionecivilesicilia.it/web/protezionecivilesicilia" \
  -o tests/collectors/fixtures/sicilia_sample_page.html
```

**For PDF regions:**
```bash
# Download latest bulletin PDF manually
# Save as: tests/collectors/fixtures/sicilia_sample_bulletin_20260511.pdf
```

**For JSON API:**
```bash
curl -L "https://api.example.com/risk/current" \
  | jq . > tests/collectors/fixtures/sicilia_sample_api.json
```

### 3. Create Connector Class

**File:** `collectors/sicilia.py`

```python
from datetime import datetime
from typing import List
from collectors.base import Connector, RiskEntry
from schemas.normalized_risk_entry import NormalizedRiskEntry

class SiciliaConnector(Connector):
    """
    Protezione Civile Sicilia connector.
    Source: https://www.protezionecivilesicilia.it
    Format: HTML + PDF bulletin
    Update: Daily (seasonal, May-August)
    Confidence: HIGH
    """
    
    source_id = "sicilia"
    update_cadence = "daily"
    max_latency_seconds = 10
    
    def fetch_source(self) -> bytes:
        """Fetch raw bulletin from Protezione Civile Sicilia portal."""
        import requests
        
        url = "https://www.protezionecivilesicilia.it/web/protezionecivilesicilia"
        resp = requests.get(
            url,
            timeout=(5, 10),  # (connect, read)
            headers={"User-Agent": "aib-telegram-bot/1.0"}
        )
        resp.raise_for_status()
        return resp.content
    
    def parse_bulletin(self, raw: bytes) -> List[RiskEntry]:
        """Parse HTML bulletin into normalized risk entries."""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(raw, "html.parser")
        
        # Example: Find table with zone data
        table = soup.find("table", attrs={"class": "bollettino-rischi"})
        if not table:
            self.logger.warning("No bollettino table found; returning empty list")
            return []
        
        entries = []
        for row in table.find_all("tr")[1:]:  # Skip header
            try:
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue
                
                zone_name = cells[0].text.strip()
                zone_id = self._normalize_zone_id(zone_name)  # Custom mapping function
                risk_raw = cells[1].text.strip().lower()
                risk_level = self._normalize_risk_level(risk_raw)
                
                entry = RiskEntry(
                    source_id=self.source_id,
                    zone_id=zone_id,
                    zone_name=zone_name,
                    risk_level_norm=risk_level,
                    risk_index_raw=risk_raw,
                    published_at=datetime.utcnow(),
                    confidence="HIGH",
                )
                entries.append(entry)
            except Exception as e:
                self.logger.error(f"Error parsing row: {e}", extra={"row": str(row)})
                continue
        
        return entries
    
    def _normalize_zone_id(self, zone_name: str) -> str:
        """Map zone name to normalized ID (e.g., 'Palermo' -> 'SI-PA-01')."""
        zone_map = {
            "Palermo": "SI-PA-01",
            "Messina": "SI-ME-02",
            "Catania": "SI-CT-03",
            # ... complete mapping
        }
        return zone_map.get(zone_name, f"SI-UNKNOWN-{zone_name[:2].upper()}")
    
    def _normalize_risk_level(self, raw: str) -> str:
        """Map regional risk labels to standard: low, medium, high, very_high."""
        risk_map = {
            "basso": "low",
            "moderato": "medium",
            "elevato": "high",
            "molto elevato": "very_high",
        }
        return risk_map.get(raw.lower(), "unknown")
```

### 4. Write Unit Tests

**File:** `tests/collectors/test_sicilia.py`

```python
import pytest
from pathlib import Path
from collectors.sicilia import SiciliaConnector
from schemas.normalized_risk_entry import NormalizedRiskEntry

FIXTURE_DIR = Path(__file__).parent / "fixtures"

class TestSiciliaConnector:
    
    @pytest.fixture
    def connector(self):
        """Create connector instance for tests."""
        return SiciliaConnector(source_id="sicilia")
    
    @pytest.fixture
    def sample_html(self):
        """Load sample HTML fixture."""
        with open(FIXTURE_DIR / "sicilia_sample_page.html", "rb") as f:
            return f.read()
    
    def test_parse_html_successfully(self, connector, sample_html):
        """Test: Successfully parse sample HTML bulletin."""
        entries = connector.parse_bulletin(sample_html)
        
        assert len(entries) > 0, "Should parse at least one zone"
        assert all(hasattr(e, 'zone_id') for e in entries)
        assert all(e.risk_level_norm in ["low", "medium", "high", "very_high", "unknown"] 
                   for e in entries)
    
    def test_zone_id_normalization(self, connector):
        """Test: Zone names correctly mapped to IDs."""
        assert connector._normalize_zone_id("Palermo") == "SI-PA-01"
        assert connector._normalize_zone_id("Messina") == "SI-ME-02"
    
    def test_risk_level_normalization(self, connector):
        """Test: Risk labels correctly normalized."""
        assert connector._normalize_risk_level("basso") == "low"
        assert connector._normalize_risk_level("Elevato") == "high"
        assert connector._normalize_risk_level("unknown_level") == "unknown"
    
    def test_malformed_data_handling(self, connector):
        """Test: Malformed rows skipped gracefully."""
        bad_html = b"<table><tr><td>Incomplete</td></tr></table>"
        entries = connector.parse_bulletin(bad_html)
        
        assert len(entries) == 0, "Should skip incomplete rows"
    
    def test_missing_table_handling(self, connector):
        """Test: Missing table handled gracefully."""
        no_table_html = b"<html><body>No bulletin today</body></html>"
        entries = connector.parse_bulletin(no_table_html)
        
        assert len(entries) == 0
        # Logger should have warning message
```

### 5. Register in Orchestrator

**File:** `collectors/orchestrator.py`

```python
# Add import
from collectors.sicilia import SiciliaConnector

# Register in connector registry
CONNECTOR_REGISTRY = {
    "veneto": VenetoConnector,
    "emilia_romagna": EmiliaRomagnaConnector,
    "toscana": ToscanaConnector,
    "sicilia": SiciliaConnector,  # <-- ADD THIS
    # ... more regions
}
```

### 6. Save and Inspect Output

For the Emilia-Romagna connector, the repository keeps an example HTML bulletin and the expected parsed output under `tests/fixtures/` so you can compare local runs against a checked-in reference.

- HTML fixture: `tests/fixtures/emilia_romagna_bulletin_sample.html`
- Expected parsed output: `tests/fixtures/emilia_romagna_expected_output.json`
- Integration-style test: `tests/test_emilia_romagna_connector.py`

Use this command to validate the connector locally:

```bash
PYTHONPATH=. pytest -q tests/test_emilia_romagna_connector.py
```

---

## Common Patterns & Utilities

### Parsing Helpers

**HTML Table Parser (common for most regions):**
```python
from collections import defaultdict

def extract_table_data(html: bytes, table_selector: str) -> List[dict]:
    """Generic HTML table parser."""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, "html.parser")
    table = soup.select_one(table_selector)
    
    if not table:
        return []
    
    headers = [th.text.strip() for th in table.find_all("th")]
    rows = []
    
    for tr in table.find_all("tr")[1:]:  # Skip header
        cells = [td.text.strip() for td in tr.find_all("td")]
        if len(cells) == len(headers):
            rows.append(dict(zip(headers, cells)))
    
    return rows
```

**PDF Text Parser (for PDF-only regions):**
```python
def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from PDF bulletin."""
    import pdfplumber
    from io import BytesIO
    
    text = []
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text.append(page.extract_text())
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""
    
    return "\n".join(text)
```

### Zone ID Mapping

**Standardized mapping from regional names to national codes:**

```python
# schemas/zone_mappings.py

ZONE_MAPPINGS = {
    "sicilia": {
        "Palermo": "SI-PA-01",
        "Messina": "SI-ME-02",
        "Catania": "SI-CT-03",
        # ... complete Sicilia zones
    },
    "toscana": {
        "Arezzo": "TO-AR-01",
        "Firenze": "TO-FI-02",
        # ... complete Toscana zones
    },
}

def get_zone_id(region: str, zone_name: str) -> str:
    """Lookup normalized zone ID."""
    mapping = ZONE_MAPPINGS.get(region, {})
    return mapping.get(zone_name, f"UNKNOWN-{zone_name[:3]}")
```

### Error Handling & Logging

**Structured logging in connectors:**

```python
import logging
import json

class Connector:
    def __init__(self, source_id: str):
        self.logger = logging.getLogger(f"collectors.{source_id}")
    
    def fetch_source(self) -> bytes:
        try:
            # ... fetch logic
        except requests.Timeout:
            self.logger.error(
                "Timeout fetching source",
                extra={
                    "source_id": self.source_id,
                    "timeout": 10,
                    "attempt": 1,
                }
            )
            raise
```

---

## Testing Checklist

Before submitting PR:

- [ ] **Unit tests pass:** `pytest tests/collectors/test_<region>.py -v`
- [ ] **Fixture files included:** 2+ real sample bulletins in `tests/collectors/fixtures/`
- [ ] **Coverage ≥80%:** `pytest --cov=collectors.<region>`
- [ ] **No hardcoded URLs:** All URLs in `sources.yml` or config
- [ ] **Timeout enforced:** All network calls have `timeout=(5, 10)`
- [ ] **Logging context:** Errors include `source_id`, `region`, timestamp
- [ ] **Schema validation:** All `RiskEntry` fields match schema
- [ ] **Fallback defined:** Fallback source documented in sources.yml
- [ ] **Zone ID mapping verified:** Manual spot-check of 5+ zones against reference
- [ ] **Docstrings present:** Module, class, and method docstrings complete

---

## Debugging Tips

### 1. Test fetch in isolation

```bash
python -c "
from collectors.sicilia import SiciliaConnector
c = SiciliaConnector()
raw = c.fetch_source()
print(f'Fetched {len(raw)} bytes')
"
```

### 2. Parse local fixture

```bash
python -c "
from collectors.sicilia import SiciliaConnector
c = SiciliaConnector()
with open('tests/collectors/fixtures/sicilia_sample_page.html', 'rb') as f:
    entries = c.parse_bulletin(f.read())
    for e in entries[:3]:
        print(f'{e.zone_id}: {e.risk_level_norm}')
"
```

### 3. Run orchestrator in dry-run mode

```bash
python -m collectors.orchestrator --region sicilia --dry-run
```

### 4. Check logs for errors

```bash
# If using structured JSON logging:
tail -f logs/ingestion.json | jq 'select(.level == "ERROR")'
```

### 5. Validate schema compliance

```bash
python -c "
from collectors.sicilia import SiciliaConnector
from schemas.normalized_risk_entry import NormalizedRiskEntry
c = SiciliaConnector()
with open('tests/collectors/fixtures/sicilia_sample_page.html', 'rb') as f:
    entries = c.parse_bulletin(f.read())
    for entry in entries:
        NormalizedRiskEntry(**entry.dict())  # Raises ValidationError if schema mismatch
"
```

---

## Common Pitfalls & Solutions

| Problem | Cause | Solution |
|---|---|---|
| **Empty zone list** | HTML selector wrong | Compare portal HTML structure with fixture; print `soup.prettify()` |
| **Zone ID mismatches** | Mapping incomplete | Manually verify 100% of zones in mapping dict against reference |
| **Timeouts in prod** | Slow regional server | Increase timeout (e.g., 15s) in connector config; add backoff retry |
| **Test fixtures stale** | HTML portal changed | Re-download fixture quarterly; tag fixture date in comments |
| **Schema validation failures** | Missing required fields | Check all required fields in `NormalizedRiskEntry` model; add defaults |
| **Encoding issues** | UTF-8 assume broken on some servers | Use `requests.encoding = 'utf-8'` explicitly; test with `\xc3\xa9` (é) |

---

## Checklist for Deployment

**Before promoting region connector to production:**

1. **Code Review (1 reviewer)**
   - [ ] Naming consistent with other connectors
   - [ ] No hardcoded secrets
   - [ ] Error handling robust
   - [ ] Logging informative

2. **Testing & Validation (QA)**
   - [ ] Unit test suite green (pytest)
   - [ ] 5+ real sample bulletins parsed correctly
   - [ ] Zone mapping 100% correct on reference set
   - [ ] Fallback chain tested (primary + fallback sources)

3. **Staging Deployment (1 week)**
   - [ ] Connector live on staging; manual fetch succeeds
   - [ ] Daily ingestion runs for 7 days; ≥99% success rate
   - [ ] No schema validation errors in logs
   - [ ] Data freshness <2h old every day

4. **Production Deployment (DevOps)**
   - [ ] Monitoring alerts configured
   - [ ] On-call runbook updated
   - [ ] Rollback plan tested
   - [ ] Deployment window scheduled (low-traffic time)

---

## Resources

- **Base Connector Class:** `collectors/base.py`
- **Normalized Schema:** `schemas/normalized_risk_entry.py`
- **Source Registry:** `sources.yml`
- **Real Examples:** `collectors/veneto.py`, `collectors/emilia_romagna.py`
- **Test Examples:** `tests/collectors/test_veneto.py`
- **CI/CD Pipeline:** `.github/workflows/test-collectors.yml`

---

**Questions?** Reach out to `dev-lead@aib-telegram-bot` or check `#dev-eng` Slack channel.
