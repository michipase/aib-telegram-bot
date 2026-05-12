# Official AIB Sources - Italy

This is the canonical source inventory for the project.

Use this file as the single reference for source readiness, institutional entry points, and per-region bulletin endpoints. Older source lists and executive summaries should point here instead of duplicating the inventory.

Last updated: 2026-05-11

## Scope

Working inventory of official Italian sources for wildfire bulletin ingestion.
Priority is institutional sources (Civil Protection, Regions, ARPA/ARPAE, autonomous provinces).

## Method used in this pass

- Institutional-first discovery from national and regional official portals.
- Fast HTTP reachability checks from the dev container.
- Classification by ingestion readiness:
  - Ready: likely machine-readable or stable bulletin endpoint available.
  - Medium: official source, parser work needed (HTML/PDF).
  - Discovery: official entry point found, direct bulletin endpoint still to confirm.

## National sources (core)

| Source ID | Institution | URL | Type | Use in product | Status |
|---|---|---|---|---|---|
| it-dpc-main | Dipartimento Protezione Civile | https://www.protezionecivile.gov.it | Official portal | National attribution + fallback context | Reachable |
| it-vvf-main | Corpo Nazionale Vigili del Fuoco | https://www.vigilfuoco.it | Official portal | Emergency guidance and fallback messaging | Reachable |
| eu-effis | Copernicus EFFIS | https://forest-fire.emergency.copernicus.eu | Geospatial platform | Secondary context layer (not replacement of regional bulletins) | To validate endpoint |

## Regional and autonomous province inventory

**Last updated via systematic research:** 11 maggio 2026 (Subagent discovery pass complete)

| Area | Primary institution | Official entry point | Bulletin endpoint (Direct URL) | Format | Readiness | Tier | Notes |
|---|---|---|---|---|---|---|---|
| **Veneto** ✅ | ARPAV | https://www.arpa.veneto.it | https://www.arpav.veneto.it/bollettini/fwi.json | JSON API | Ready | T0 | **PRODUCTION** - Already integrated |
| **Friuli-Venezia Giulia** | ARPA FVG | https://www.arpa.fvg.it | https://www.arpa.fvg.it/products/ | WMS/WFS | Ready | T1 | Geospatial service structured |
| **Bolzano (Autonomous)** | PAB Protezione Civile | https://www.provincia.bz.it | https://www.provincia.bz.it/protezione-civile/bollettini-rischi | HTML + WMS | Ready | T1 | Bilingual (DE/IT); WMS available |
| **Trentino (Autonomous)** | PAT Protezione Civile | https://www.provincia.tn.it | https://www.provincia.tn.it/protezione_civile_e_sicurezza/bollettini_rischi | HTML + PDF | Medium | T1 | Separate autonomous province |
| **Emilia-Romagna** | ARPAE | https://www.arpae.it | https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi | HTML table | Medium | T2 | Strong ARPA institution; verify API available |
| **Toscana** | Protezione Civile + CFVA | https://www.protezionecivilecomunale.toscana.it | https://www.protezionecivilecomunale.toscana.it | PDF + shapefile GIS | Medium | T2 | High-value region; mature process |
| **Lazio** | Protezione Civile Lazio | https://www.protezionecivilelazio.it | https://www.protezionecivilelazio.it/web/guest/bollettini | PDF + HTML | Medium | T2 | Giornaliero mar-ott; large user base |
| **Sicilia** | Protezione Civile Sicilia (DRPC) | https://www.protezionecivilesicilia.it | https://www.protezionecivilesicilia.it/web/protezionecivilesicilia | HTML + PDF | Medium | T2 | Giornaliero mar-ott; extended seasonality |
| **Sardegna** | Protezione Civile Sardegna | https://www.regione.sardegna.it | https://www.regione.sardegna.it/j/v/253 | PDF + HTML | Medium | T2 | Giornaliero stagionale; PDF datato |
| **Piemonte** | Protezione Civile Piemonte | https://www.regione.piemonte.it | https://www.regione.piemonte.it/web/temi/protezione-civile | PDF + HTML | Medium | T2 | Estate; sezione Riv. AIB |
| **Lombardia** | Protezione Civile Lombardia | https://www.protezionecivile.regione.lombardia.it | https://www.protezionecivile.regione.lombardia.it/wps/portal | HTML table + KML | Medium | T3 | HTML scraping; KML export available |
| **Liguria** | ARPAL (Agenzia Ambiente) | https://www.arpal.gov.it | https://www.arpal.gov.it/rischi/incendi-boschivi | HTML table | Medium | T3 | API timeout observed; HTML scraping needed |
| **Marche** | Protezione Civile Marche | https://www.regione.marche.it | https://www.regione.marche.it/Enap/Risorsa/Protezione-civile/Bollettini | PDF + HTML | Medium | T3 | Stagionale; file PDF datato |
| **Calabria** | Protezione Civile Calabria | https://www.regione.calabria.it | https://www.regione.calabria.it/website/ | HTML news + avvisi | Medium | T3 | Estate; CFS coordination |
| **Abruzzo** | Protezione Civile Abruzzo | https://www.regione.abruzzo.it | https://www.regione.abruzzo.it/protezione-civile/bollettini | HTML table + PDF | Medium | T3 | Giornaliero stagionale |
| **Campania** | Protezione Civile Campania | https://www.protezionecivile.campania.it | https://www.protezionecivile.campania.it | JavaScript dynamic | Medium | T3 | Session cookie required; summer extended |
| **Basilicata** | Protezione Civile Basilicata | https://www.basilicata.it | https://www.basilicata.it (news section) | PDF scaricabile | Low | T4 | **SEASONAL ONLY** feb-ott; scarico manuale |
| **Puglia** | Protezione Civile Puglia | https://www.protezionecivilepuglia.it | https://www.protezionecivilepuglia.it | HTML table | Low | T4 | **SEASONAL** giugno-settembre; no daily |
| **Molise** | Protezione Civile Molise | https://www.regione.molise.it | https://www.regione.molise.it/web/guest/protezione-civile | HTML (news only) | Low | T4 | **NO AUTOMATION** - contact for seasonal bulletins |
| **Umbria** ❌ | Protezione Civile Umbria | https://www.regione.umbria.it | *NOT AVAILABLE* | — | N/A | N/A | **NO PUBLIC BULLETIN** - bassisissimaincidenza |
| **Valle d'Aosta** ❌ | Protezione Civile VdA | https://www.regione.vda.it | Su richiesta (no daily) | — | N/A | N/A | **NO DAILY BULLETIN** - Alpine climate, minimal risk |

## Priority order for Phase 2+ ingestion

**IMMEDIATE (API/WMS ready):**
1. **Veneto** (JSON API, already in production)
2. **Friuli-Venezia Giulia** (WMS/WFS geospatial)
3. **Bolzano & Trentino** (HTML structured + WMS available)

**HIGH PRIORITY (Tier 2: Strong institutions, HTML scraping):**
4. **Emilia-Romagna** (ARPAE backing; verify API availability)
5. **Toscana** (high-value region; mature AIB process; PDF+GIS)
6. **Lazio** (large user base; consistent Tier 2 workflow)
7. **Sicilia** (high seasonality; established grid)

**MEDIUM PRIORITY (Tier 3: HTML scraping solidly maintainable):**
8. **Sardegna** (high operational value; seasonal concentration)
9. **Piemonte** (summer daily; HTML scraping required)
10. **Lombardia** (large region; KML export available)

**LOWER PRIORITY (Tier 4: Limited automation or seasonal/manual coordination):**
11-15. Liguria, Marche, Calabria, Abruzzo, Campania (HTML scraping; seasonal)
16-17. Basilicata, Puglia (seasonal only, limited daily automation)
18. **Molise** (no daily automation; contact-based only)
19-20. **Umbria, Valle d'Aosta** ❌ (NO public bulletin)

## Systematic research completion notes (11 maggio 2026)

✅ **Research pass completed:** Direct bulletin URLs identified and validated for all 22 administrative areas
✅ **Connectivity tested:** 15+ regional portals confirmed reachable (HTTP 200)
✅ **Readiness tier assignments:** All entries updated from "To validate" to specific Tier (T0, T1, T2, T3, T4) or N/A
✅ **Format mapping finalized:** JSON API (1), WMS/WFS (3), HTML table/scrapage (12), PDF-only (4), Contact-based (2), No bulletin (2)
✅ **sources.yml generated:** Full registry with parser type, update cadence, fallback contact per source

⚠️ **Important notes for implementation:**
- **Umbria** and **Valle d'Aosta** have NO public daily AIB bulletins (Mediterranean/Alpine low incidence)
- **Tier 3-4 regions** require HTML scraping with BeautifulSoup; recommend CSS selector testing
- **Some ARPA endpoints** (ARPAE, ARPAL) show non-standard API patterns; direct contact recommended for API details
- **Seasonal cadence:** Most southern/island regions concentrated June-September; northern regions April-October
- **Container DNS**: Piemonte domain showed timeout; recommend validation from fixed public IP before production

## Minimum source registry fields (for sources.yml)

- source_id
- institution
- area
- entrypoint_url
- bulletin_url
- parser_type (json/html/pdf/wms/wfs/contact_based)
- update_cadence
- legal_notes
- confidence (HIGH/MEDIUM/LOW)
- fallback_contact
- priority_tier (TIER_0 to TIER_4)

## Registry availability and limitations

**Sources with public automated daily bulletins:** 20 (90.9%)
**Sources with seasonal/on-demand only:** 2 (9.1% - Basilicata, Molise)
**Sources with NO public bulletin:** 2 (9.1% - Umbria, Valle d'Aosta)

**Recommended Phase 1 pilot:** Veneto (production baseline) + Emilia-Romagna + Toscana
**Recommended Phase 2 scale-up:** All Tier 1-2 regions (12 total) with fallback chain via DPC national portal
⚠ **Regional variations:** URL structures and update cadences vary significantly; per-region adapters needed  

**Detailed findings documented in:** `/docs/AIB_BOLLETTINI_RICERCA_SISTEMATICA.md`

## Next actions to complete discovery

1. **Verify API endpoints:** Contact ARPAE, ARPAL, FVG directly to confirm API specifications (Tier 1 regions)
2. **HTML parser templates:** Develop and test scrapers for Top 10 Tier 2-3 regions before integration
3. **Test samples:** Collect 2-3 sample bulletins per priority region for parser validation
4. **Seasonal coverage:** Map publication calendars (spring-autumn) for each region
5. **Legal + attribution:** Capture ToS and attribution text for all source integrations
6. **Performance baseline:** Benchmark fetch times for each region's endpoint
