# RICERCA SISTEMATICA: Bollettini Antincendio Boschivo (AIB)

This document is archived. The canonical inventory of source URLs, format notes, and readiness tiers now lives in [OFFICIAL_AIB_SOURCES_ITALY.md](OFFICIAL_AIB_SOURCES_ITALY.md).

Use that file as the single source of truth for source selection and keep this document only for historical context.
```json
{
  "categoria": "PRIORITY_HIGH",
  "regioni": ["Veneto"],
  "metodo": "Direct JSON API",
  "esempio": "https://www.arpa.veneto.it/bollettini/fwi.json",
  "frequenza": "Giornaliera",
  "configurazione": "Direct HTTP fetch + parse JSON"
}
```

### Tier 2: WMS/WFS Geospatiale
```json
{
  "categoria": "PRIORITY_MEDIUM",
  "regioni": ["Friuli-Venezia Giulia", "Alto Adige"],
  "metodo": "OGC WMS/WFS services",
  "frequenza": "Giornaliera",
  "configurazione": "GetMap/GetFeature requests, convert to GeoJSON"
}
```

### Tier 3: HTML Table Scraping (Regioni con HTML tabella disponibile)
```json
{
  "categoria": "PRIORITY_MEDIUM_PLUS",
  "regioni": ["Piemonte", "Lombardia", "Toscana", "Lazio", "Sardegna", "Sicilia", "Calabria"],
  "metodo": "HTML parsing",
  "configurazione": "BeautifulSoup/Selector per tabella → JSON normalization",
  "caveats": "Strutture HTML variabili; testing requires per-region"
}
```

### Tier 4: PDF + Manual Contact (Comunicazione diretta richiesta)
```json
{
  "categoria": "PRIORITY_LOW",
  "regioni": ["Basilicata", "Puglia", "Molise", "Umbria", "Valle d'Aosta"],
  "metodo": "PDF download + OCR oppure contatto diretto",
  "configurazione": "pdfplumber per parsing; fallback email contact",
  "note": "Non automatizzabili; suggest partnership/API institutionale"
}
```

---

## SCHEMA NORMALIZZAZIONE DATI

Proposto per convergenza multi-regione:

```json
{
  "regione": "Veneto",
  "data_bollettino": "2026-05-11",
  "ente_fonte": "ARPAV",
  "dati_meteo": {
    "temp_max": 28,
    "umidita_min": 35,
    "vento_velocity": 12
  },
  "indici_pericolo": {
    "fwi_index": 85,
    "livello_rischio": "ALTO",
    "ffmc": 92,
    "dmc": 72,
    "dc": 480
  },
  "validita": {
    "pubblicazione": "2026-05-11T06:00:00Z",
    "scadenza": "2026-05-12T06:00:00Z"
  },
  "metadata": {
    "url_source": "https://www.arpa.veneto.it/bollettini/fwi.json",
    "formato": "JSON",
    "ultima_modifica": "2026-05-11T06:15:00Z"
  },
  "zone_allerta": [
    {
      "id": "VE-NORD",
      "nome": "Dolomiti-Belluno",
      "fwi": 78,
      "livello": "MOLTO_ALTO"
    }
  ]
}
```

---

## CONTATTI TECNICI PRINCIPALI

| **Ente** | **Email** | **Telefono** | **Portale** |
|---|---|---|---|
| Protezione Civile Nazionale | — | — | https://www.protezionecivile.gov.it |
| ARPAV (Veneto) | info@arpa.veneto.it | 049.8208.111 | https://www.arpa.veneto.it |
| ARPAE (Emilia-Romagna) | — | 051.6416111 | https://www.arpae.it |
| ARPAL (Liguria) | — | 010.280.6570 | https://www.arpal.gov.it |
| ARPA FVG | info@arpa.fvg.it | 0432.555111 | https://www.arpa.fvg.it |
| Protezione Civile Lazio | info@protezionecivilelazio.it | 06.51963000 | https://www.protezionecivilelazio.it |
| Protezione Civile Calabria | protezionecivile@regione.calabria.it | 090.37891700 | https://www.regione.calabria.it |

---

## CONCLUSIONI E PROSSIMI STEP

1. **Implementazione immediata:** Veneto (già in uso) rimane prioritario e stabile
2. **Espansione immediata:** Implementare Tier 2 (WMS/WFS) per FVG e Alto Adige
3. **Scraping controllato:** Implementare HTML parsing per le 7 regioni Tier 3 su base sperimentale
4. **Partnership istituzionale:** Contattare ARPAE, ARPAL per API officiali (prospettiva EDA/EGDI)
5. **Fallback:** Per Molise, Umbria, Valle d'Aosta, mantenere contatti diretti e/o comunicazione manuale

**Last Updated:** 11 maggio 2026

---

*Ricerca eseguita in accordo con criteri di ricerca sistematica su portali ufficiali. Alcuni URL sono soggetti a variazione temporale e richiedono verifica periodica per mantenere accuracy.*
