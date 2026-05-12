from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from .base import Connector


ALTO_ADIGE_BOLZANO_URL = "https://www.provincia.bz.it/protezione-civile/bollettini-rischi"


@dataclass(frozen=True)
class AltoAdigeBolzanoRiskEntry:
    zone_id: str
    zone_name: str
    risk_level: str
    indice: int | None
    fwi: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AltoAdigeBolzanoDay:
    day: datetime | None
    zones: list[AltoAdigeBolzanoRiskEntry]


@dataclass(frozen=True)
class AltoAdigeBolzanoBulletin:
    source_id: str
    source_url: str
    days: list[AltoAdigeBolzanoDay]

    @property
    def published_at(self) -> datetime | None:
        if not self.days:
            return None
        return self.days[0].day

    @property
    def entries(self) -> list[AltoAdigeBolzanoRiskEntry]:
        if not self.days:
            return []
        return self.days[0].zones


class AltoAdigeBolzanoConnector(Connector):
    def __init__(
        self,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        super().__init__(
            "alto_adige_bolzano",
            verify_ssl=verify_ssl,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries=retries,
        )

    def fetch_source(self) -> str:
        try:
            return self.get_text(ALTO_ADIGE_BOLZANO_URL)
        except Exception:
            # Attempt language-neutral fallback path
            fallback = ALTO_ADIGE_BOLZANO_URL.replace("/protezione-civile/", "/zivilschutz/")
            return self.get_text(fallback)

    def parse_bulletin(self, raw_source: str) -> AltoAdigeBolzanoBulletin:
        soup = BeautifulSoup(raw_source, "html.parser")
        page_text = soup.get_text(" ", strip=True)
        published_at = self._extract_published_at(page_text)

        table = self._select_data_table(soup)
        if table is None:
            return AltoAdigeBolzanoBulletin(
                source_id=self.source_id,
                source_url=ALTO_ADIGE_BOLZANO_URL,
                days=[AltoAdigeBolzanoDay(day=published_at, zones=[])],
            )

        header_labels = [
            self._normalize_label(th.get_text(" ", strip=True)) for th in table.find_all("th")
        ]
        zone_idx = self._find_col_idx(header_labels, ["zona", "gebiet", "area", "distretto", "bezirk"])
        risk_idx = self._find_col_idx(header_labels, ["rischio", "gefahr", "pericolo", "livello", "stufe"])
        indice_idx = self._find_col_idx(header_labels, ["indice", "index"])
        fwi_idx = self._find_col_idx(header_labels, ["fwi"])

        entries: list[AltoAdigeBolzanoRiskEntry] = []
        for row in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cells:
                continue

            zone_name = self._safe_get(cells, zone_idx) or self._safe_get(cells, 0)
            if not zone_name:
                continue

            risk_raw = self._safe_get(cells, risk_idx)
            indice = self._coerce_int(self._safe_get(cells, indice_idx))
            fwi = self._coerce_float(self._safe_get(cells, fwi_idx))
            risk_level = self._normalize_risk_level(risk_raw, indice)

            entries.append(
                AltoAdigeBolzanoRiskEntry(
                    zone_id=self._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=risk_level,
                    indice=indice,
                    fwi=fwi,
                )
            )

        return AltoAdigeBolzanoBulletin(
            source_id=self.source_id,
            source_url=ALTO_ADIGE_BOLZANO_URL,
            days=[AltoAdigeBolzanoDay(day=published_at, zones=entries)],
        )

    @staticmethod
    def _select_data_table(soup: BeautifulSoup) -> Any:
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
            if not headers:
                continue
            has_zone = any(
                kw in h for h in headers for kw in ("zona", "gebiet", "area", "distretto", "bezirk")
            )
            has_risk = any(
                kw in h for h in headers for kw in ("rischio", "gefahr", "pericolo", "indice", "stufe", "fwi")
            )
            if has_zone and has_risk:
                return table
        return None

    @staticmethod
    def _find_col_idx(labels: list[str], keywords: list[str]) -> int | None:
        for idx, label in enumerate(labels):
            if any(keyword in label for keyword in keywords):
                return idx
        return None

    @staticmethod
    def _safe_get(values: list[str], idx: int | None) -> str | None:
        if idx is None or idx < 0 or idx >= len(values):
            return None
        value = values[idx].strip()
        return value or None

    @staticmethod
    def _normalize_label(label: str) -> str:
        text = unicodedata.normalize("NFKD", label)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text.lower()).strip()

    @classmethod
    def _normalize_zone_id(cls, zone_name: str) -> str:
        key = cls._normalize_label(zone_name)
        zone_map = {
            # Capoluogo
            "bolzano": "BZ-BZ",
            "bozen": "BZ-BZ",
            # Comprensori / Bezirksgemeinschaften
            "burgraviato": "BZ-BG",
            "burggrafenamt": "BZ-BG",
            "merano": "BZ-ME",
            "meran": "BZ-ME",
            "obervinschgau": "BZ-OV",
            "alta val venosta": "BZ-OV",
            "vinschgau": "BZ-VV",
            "val venosta": "BZ-VV",
            "eisacktal": "BZ-EI",
            "val d'isarco": "BZ-EI",
            "bressanone": "BZ-BX",
            "brixen": "BZ-BX",
            "wipptal": "BZ-WI",
            "alta valle isarco": "BZ-WI",
            "vipiteno": "BZ-ST",
            "sterzing": "BZ-ST",
            "pustertal": "BZ-PT",
            "val pusteria": "BZ-PT",
            "brunico": "BZ-BK",
            "bruneck": "BZ-BK",
            "alta pusteria": "BZ-HP",
            "hochpustertal": "BZ-HP",
            "oltradige bassa atesina": "BZ-OL",
            "uberetscher tal": "BZ-OL",
            "oltradige": "BZ-OL",
            "val gardena": "BZ-VG",
            "groedner tal": "BZ-VG",
            "alto adige orientale": "BZ-OR",
            "salten schlern": "BZ-SS",
            "salto sciliar": "BZ-SS",
        }
        for zone_key, zone_id in zone_map.items():
            if zone_key in key:
                return zone_id
        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-") or "unknown"
        return f"BZ-UNK-{slug[:12].upper()}"

    @classmethod
    def _normalize_risk_level(cls, risk_raw: str | None, indice: int | None) -> str:
        if indice is not None:
            if indice <= 2:
                return "BASSO"
            if indice == 3:
                return "MEDIO"
            if indice == 4:
                return "ALTO"
            return "MOLTO ALTO"

        if not risk_raw:
            return "ND"

        risk = cls._normalize_label(risk_raw)
        # IT + DE labels
        if any(t in risk for t in ("molto alto", "sehr hoch", "estremo", "extrem", "rosso", "rot")):
            return "MOLTO ALTO"
        if any(t in risk for t in ("alto", "hoch", "arancione", "orange")):
            return "ALTO"
        if any(t in risk for t in ("medio", "mittel", "moderato", "mabig", "giallo", "gelb")):
            return "MEDIO"
        if any(t in risk for t in ("basso", "niedrig", "gering", "verde", "grun", "gruen")):
            return "BASSO"
        return "ND"

    @staticmethod
    def _extract_published_at(page_text: str) -> datetime | None:
        # IT format: 12/05/2026
        m = re.search(r"(\d{2}/\d{2}/\d{4})", page_text)
        if m:
            try:
                return datetime.strptime(m.group(1), "%d/%m/%Y")
            except ValueError:
                pass
        # ISO format: 2026-05-12
        m = re.search(r"(\d{4}-\d{2}-\d{2})", page_text)
        if m:
            try:
                return datetime.strptime(m.group(1), "%Y-%m-%d")
            except ValueError:
                pass
        # DE format: 12.05.2026
        m = re.search(r"(\d{2}\.\d{2}\.\d{4})", page_text)
        if m:
            try:
                return datetime.strptime(m.group(1), "%d.%m.%Y")
            except ValueError:
                pass
        return None

    @staticmethod
    def _coerce_int(value: str | None) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_float(value: str | None) -> float | None:
        if value is None:
            return None
        normalized = value.replace(",", ".")
        try:
            return float(normalized)
        except (TypeError, ValueError):
            return None
