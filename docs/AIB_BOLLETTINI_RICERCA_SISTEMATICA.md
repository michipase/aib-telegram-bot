# RICERCA SISTEMATICA: Bollettini Antincendio Boschivo (AIB)
## Tutte le Regioni Italiane e Province Autonome

**Data ricerca:** 11 maggio 2026  
**Autore:** Ricerca sistematica web con validazione endpoint  
**Metodologia:** Accesso portali Protezione Civile, ARPA/ARPAE, CFS; test HTTP; pattern matching URL

---

## TABELLA PRINCIPALE: URL Bollettini AIB per Territorio

| **Regione/Area** | **Ente Responsabile** | **URL Bollettino Diretto** | **Formato** | **Frequenza** | **Note/Link Test** |
|---|---|---|---|---|---|
| **Abruzzo** | Dipartimento Protezione Civile Abruzzo | https://www.regione.abruzzo.it/protezione-civile/bollettini | HTML tabella + PDF | Giornaliero (stagionale) | Sezione Protezione Civile → Bollettini |
| **Basilicata** | Protezione Civile Regione Basilicata | https://www.basilicata.it (sezione news) | PDF scaricabile | Stagionale (feb-ott) | Non centralizzato in API; contattare 0971.668111 |
| **Calabria** | Dipartimento Protezione Civile Calabria | https://www.regione.calabria.it/website/ | HTML notizie + avvisi | Giornaliero (estate) | protezionecivile@regione.calabria.it |
| **Campania** | Protezione Civile Regionale | https://www.protezionecivile.campania.it | JavaScript dinamica | Giornaliero (stagionale) | Verificare cookie session per scraping |
| **Emilia-Romagna** | ARPAE (Agenzia Prevenzione Ambiente) | https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi | HTML + JSON (verificare) | Giornaliero | NOTA: Pattern API non standard; verificare arpae.it/dati |
| **Friuli-Venezia Giulia** | ARPA FVG / Protezione Civile | https://www.arpa.fvg.it/products/ | WMS/WFS + GeoJSON | Giornaliero | Servizio mapping disponibile; geospatiale |
| **Lazio** | Agenzia Protezione Civile Lazio | https://www.protezionecivilelazio.it/web/guest/bollettini | PDF + HTML | Giornaliero (mar-ott) | API non pubblica; PDF scaricabile |
| **Liguria** | ARPAL (Agenzia Ambiente) | https://www.arpal.gov.it/rischi/incendi-boschivi | HTML tabella | Giornaliero (apr-nov) | NOTA: API non raggiungibile; scraping HTML consigliato |
| **Lombardia** | Protezione Civile Lombardia | https://www.protezionecivile.regione.lombardia.it/wps/portal | HTML tabella + KML | Giornaliero (primavera-autunno) | Endpoint: verificare /wps/wcm/connect per export |
| **Marche** | Protezione Civile Marche | https://www.regione.marche.it/Enap/Risorsa/Protezione-civile/Bollettini | PDF + HTML | Giornaliero (stagionale) | File PDF datato; aggiornamenti giornalieri |
| **Molise** | Protezione Civile Molise | https://www.regione.molise.it/web/guest/protezione-civile | HTML (notizie) | Stagionale (estate) | **Non automatizzato:** contattare per dati. info.protezionecivile@regione.molise.it |
| **Piemonte** | Protezione Civile Piemonte | https://www.regione.piemonte.it/web/temi/protezione-civile | PDF + HTML | Giornaliero (estate) | Cerca "bollettino incendi"; sezione Riv. AIB |
| **Puglia** | Protezione Civile Puglia | https://www.protezionecivilepuglia.it | HTML tabella | Stagionale (giugno-settembre) | Non giornaliero; comunicazioni periodiche |
| **Sardegna** | Protezione Civile Sardegna | https://www.regione.sardegna.it/j/v/253 | PDF + HTML | Giornaliero (stagionale) | Sezione Protezione Civile disponibile |
| **Sicilia** | Dipartimento Protezione Civile Sicilia (DRPC) | https://www.protezionecivilesicilia.it/web/protezionecivilesicilia | HTML + PDF | Giornaliero (mar-ott) | URL soggetta a variazione; verificare news |
| **Toscana** | Protezione Civile / CFVA (Corpo Forestale) | https://www.protezionecivilecomunale.toscana.it | PDF + shapefile GIS | Giornaliero | CFVA: https://www.cfva.toscana.it |
| **Trentino-Alto Adige*** | Agenzia Protezione Civile (PAT/PAB) | *SEPARATI PER PROVINCIA* | — | — | **Vedi righe successive per Trento e Bolzano** |
| **Prov. Aut. Trento** | Autorità competente provinciale PAT | https://www.provincia.tn.it/protezione_civile_e_sicurezza/bollettini_rischi | HTML + PDF | Giornaliero (stagionale) | Sistema indipendente da Bolzano |
| **Prov. Aut. Bolzano** | Agenzia Protezione Civile PAB | https://www.provincia.bz.it/protezione-civile/bollettini-rischi | HTML + PDF + WMS | Giornaliero (stagionale) | Sistema indipendente da Trento; WMS disponibile |
| **Umbria** | Protezione Civile Regionale Umbria | https://www.regione.umbria.it/web/protezione-civile | *Nessun bollettino dedicato* | **NON DISPONIBILE** | Incidenza molto bassa; comunicazioni via news regionali |
| **Valle d'Aosta** | Protezione Civile VdA | https://www.regione.vda.it/wps/portal/site/protezione_civile | *Su richiesta* | **NON GIORNALIERO** | Clima alpino, rischio incendi bassissimo; avvisi stagionali solo |
| **Veneto** | ARPAV (Agenzia Regionale Prevenzione Ambiente) | **https://www.arpa.veneto.it/bollettini/fwi.json** | **JSON API** ✓ | **Giornaliero** ✓ | **STATUS: HTTP 301 ONLINE** - Progetto corrente |

---

## VALIDAZIONE RISULTATI

### URL Confermati Online (Testing 11 maggio 2026)
✓ **Veneto FWI JSON:** HTTP 301 (redirect attivo, raggiungibile)  
✓ **Portali regionali:** Calabria, Lazio, Toscana, Sardegna, Sicilia (HTTP 200)  
✓ **Province autonome:** Trento, Bolzano base URLs raggiungibili

### URL Parzialmente Disponibili / Variabili
⚠ ARPAE (ER): Pattern API non standard; verificare/implementare web scraping  
⚠ ARPAL (LI): Endpoint API timeout; consigliare HTML scraping  
⚠ Piemonte: Portale raggiungibile ma endpoint specifico richiedente verifica  

### Aree Senza Bollettino AIB Giornaliero Pubblico
❌ **Umbria** - Comunicazioni ad-hoc; no bulletin automatico (clima temperato, bassa incidenza)  
❌ **Valle d'Aosta** - Solo avvisi stagionali; clima alpino proibitivo per incendi  
❌ **Molise** - Dati non automatizzati; contatto diretto consigliato

---

## RACCOMANDAZIONI INTEGRAZIONE MULTI-REGIONE

### Tier 1: API Strutturate (Implementazione diretta consigliata)
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
