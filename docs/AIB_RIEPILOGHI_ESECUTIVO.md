# RICERCA SISTEMATICA BOLLETTINI ANTINCENDIO BOSCHIVO - RIEPILOGO ESECUTIVO

This document is archived. The canonical source inventory is [OFFICIAL_AIB_SOURCES_ITALY.md](OFFICIAL_AIB_SOURCES_ITALY.md), which now owns the regional tables, readiness labels, and source notes.

If you need the high-level summary for planning, use [ROADMAP.md](ROADMAP.md) and [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) instead of maintaining a second inventory.
- **Stagionale (periodico):** 5 regioni
- **Su richiesta / Non automatizzato:** 3 regioni

### Validazione endpoint
- **HTTP 200/301 online:** 15+ portali confermati raggiungibili (11 maggio 2026)
- **Pattern API non standard:** ARPAE (ER), ARPAL (LI) - richiedono verifica dettagliata
- **Timeout/DNS issues:** Riscontrati su alcuni domini da container; raccomandata validazione da IP fisso

---

## RACCOMANDAZIONI INTEGRAZIONE MULTI-REGIONE

### PRIORITÀ 1: Implementazione immediata (Tier 1)
```
Regioni: Friuli-Venezia Giulia, Alto Adige/Bolzano
Metodo: Direct WMS/WFS GetMap + GeoJSON conversion
Sforzo: Medio-Alto (GIS infrastructure)
ROI: Alto (geo-precision + seasonality coverage)
Timeline: 2-4 settimane
```

### PRIORITÀ 2: Expansion con HTML scraping (Tier 2-3)
```
Regioni: Emilia-Romagna (ARPAE), Toscana, Lazio, Sicilia, Sardegna, Piemonte
Metodo: HTML tabella parsing + PDF extraction (PyPDF/pdfplumber)
Sforzo: Basso-Medio (1-2 giorni per regione)
ROI: Molto alto (copertura +60% popolazione)
Pattern: requests + BeautifulSoup → normalized JSON
Timeline: 4-6 settimane (iterativo)
```

### PRIORITÀ 3: Fallback / Manual coordination (Tier 4)
```
Regioni: Basilicata, Calabria, Molise, Puglia, Marche, Abruzzo, Campania
Metodo: Contact-based API request oppure batch email coordination
Costo: Basso (contact info)
Fallback: Email subscribe per updates
Timeline: On-demand
```

### REGIONI SKIP (No bulletin disponibile)
```
Umbria, Valle d'Aosta: Non hanno bulletin pubblico regolare
Azione: Monitor per future policy changes; mantieni contatto istituzionale
```

---

## PROSSIMI STEP CONSIGLIATI

1. **Validazione rapida:** Testare i 3 URL Tier-1 (FVG, Alto Adige) con curl/WebDriver per confirmare formato WMS
2. **Campionamento dati:** Prelevare 1 bollettino per ogni Top-10 regione per testing parser
3. **Partnership ARPA:** Contattare ARPAE/ARPAL per scoprire API ufficiali (spesso non pubbliche ma disponibili per partner)
4. **HTML parser templates:** Creare 5 parser-stub per regioni Tier 2 (ER, Toscana, Lazio) come PoC
5. **Geo-normalization:** Allineare zone geografiche tra diverse regioni (province, settori rischio) per geocoding coerente

---

## FILE DI RICERCA GENERATI

- **AIB_BOLLETTINI_RICERCA_SISTEMATICA.md** - Report dettagliato con tutti gli endpoint
- **OFFICIAL_AIB_SOURCES_ITALY.md** - Inventory aggiornato con URL e readiness tier
- **this file** - Riepilogo esecutivo con tabella sintetica

**Ricerca completata: 11 maggio 2026**
