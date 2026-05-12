from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup

from .base import Connector


EMILIA_ROMAGNA_URL = "https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi"


@dataclass(frozen=True)
class EmiliaRomagnaRiskEntry:
    zone_id: str
    zone_name: str
    risk_level: str
    indice: int | None
    fwi: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmiliaRomagnaBulletin:
    source_id: str
    source_url: str
    published_at: datetime | None
    entries: list[EmiliaRomagnaRiskEntry]


class EmiliaRomagnaConnector(Connector):
    def __init__(
        self,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        super().__init__(
            "emilia_romagna",
            verify_ssl=verify_ssl,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries=retries,
        )

    def fetch_source(self) -> str:
        return self.get_text(EMILIA_ROMAGNA_URL)

    def parse_bulletin(self, raw_source: str) -> EmiliaRomagnaBulletin:
        soup = BeautifulSoup(raw_source, "html.parser")
        page_text = soup.get_text(" ", strip=True)
        published_at = self._extract_published_at(page_text)

        table = self._select_data_table(soup)
        if table is None:
            return EmiliaRomagnaBulletin(
                source_id=self.source_id,
                source_url=EMILIA_ROMAGNA_URL,
                published_at=published_at,
                entries=[],
            )

        header_labels = [self._normalize_label(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        zone_idx = self._find_col_idx(header_labels, ["zona", "provincia", "area"])
        risk_idx = self._find_col_idx(header_labels, ["rischio", "pericolo", "livello"])
        indice_idx = self._find_col_idx(header_labels, ["indice"])
        fwi_idx = self._find_col_idx(header_labels, ["fwi"])

        entries: list[EmiliaRomagnaRiskEntry] = []
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
                EmiliaRomagnaRiskEntry(
                    zone_id=self._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=risk_level,
                    indice=indice,
                    fwi=fwi,
                )
            )

        return EmiliaRomagnaBulletin(
            source_id=self.source_id,
            source_url=EMILIA_ROMAGNA_URL,
            published_at=published_at,
            entries=entries,
        )

    @staticmethod
    def _select_data_table(soup: BeautifulSoup) -> Any:
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
            if not headers:
                continue
            has_zone = any("zona" in header or "provincia" in header or "area" in header for header in headers)
            has_risk = any("rischio" in header or "pericolo" in header or "indice" in header for header in headers)
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
            "piacenza": "ER-PC",
            "parma": "ER-PR",
            "reggio emilia": "ER-RE",
            "modena": "ER-MO",
            "bologna": "ER-BO",
            "ferrara": "ER-FE",
            "ravenna": "ER-RA",
            "forli cesena": "ER-FC",
            "forli-cesena": "ER-FC",
            "rimini": "ER-RN",
            "appennino": "ER-APP",
            "pianura": "ER-PLA",
        }

        for zone_key, zone_id in zone_map.items():
            if zone_key in key:
                return zone_id

        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-") or "unknown"
        return f"ER-UNK-{slug[:12].upper()}"

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
        if any(token in risk for token in ("molto alto", "estremo", "rosso", "4")):
            return "MOLTO ALTO"
        if any(token in risk for token in ("alto", "arancione", "3")):
            return "ALTO"
        if any(token in risk for token in ("medio", "moderato", "giallo")):
            return "MEDIO"
        if any(token in risk for token in ("basso", "verde", "1", "2")):
            return "BASSO"
        return "ND"

    @staticmethod
    def _extract_published_at(page_text: str) -> datetime | None:
        match = re.search(r"(\d{2}/\d{2}/\d{4})", page_text)
        if not match:
            return None

        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y")
        except ValueError:
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