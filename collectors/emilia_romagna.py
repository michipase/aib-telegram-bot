from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from urllib.parse import urljoin
from typing import Any

from bs4 import BeautifulSoup

from .base import Connector


EMILIA_ROMAGNA_URL = "https://www.arpae.it/it/meteo/avvisi/bollettino-incendi-boschivi"
EMILIA_ROMAGNA_FALLBACK_URL = (
    "https://www.arpae.it/it/meteo/avvisi"
)
EMILIA_ROMAGNA_PDF_INDEX_URL = (
    "https://protezionecivile.regione.emilia-romagna.it/rischi-previsione-prevenzione/"
    "rischio-incendi/bollettini-incendi-boschivi/{year}"
)


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
    days: list["EmiliaRomagnaDay"]

    @property
    def published_at(self) -> datetime | None:
        if not self.days:
            return None
        return self.days[0].day

    @property
    def entries(self) -> list[EmiliaRomagnaRiskEntry]:
        if not self.days:
            return []
        return self.days[0].zones


@dataclass(frozen=True)
class EmiliaRomagnaDay:
    day: datetime | None
    zones: list[EmiliaRomagnaRiskEntry]


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

    def fetch_source(self) -> Any:
        try:
            return self.get_text(EMILIA_ROMAGNA_URL)
        except Exception:
            return self._fetch_pdf_source()

    def parse_bulletin(self, raw_source: Any) -> EmiliaRomagnaBulletin:
        if isinstance(raw_source, dict) and raw_source.get("kind") == "pdf":
            return self._parse_pdf_bulletin(raw_source)

        soup = BeautifulSoup(raw_source, "html.parser")
        page_text = soup.get_text(" ", strip=True)
        published_at = self._extract_published_at(page_text)

        table = self._select_data_table(soup)
        if table is None:
            return EmiliaRomagnaBulletin(
                source_id=self.source_id,
                source_url=EMILIA_ROMAGNA_URL,
                days=[
                    EmiliaRomagnaDay(
                        day=published_at,
                        zones=[],
                    )
                ],
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
            days=[
                EmiliaRomagnaDay(
                    day=published_at,
                    zones=entries,
                )
            ],
        )

    def _fetch_pdf_source(self) -> dict[str, str]:
        now = datetime.now(UTC)
        index_url = EMILIA_ROMAGNA_PDF_INDEX_URL.format(year=now.year)
        index_html = self.get_text(index_url)

        bulletin_url = self._extract_latest_pdf_document_url(index_html, base_url=index_url)
        wrapper_html = self.get_text(bulletin_url)
        download_url = self._extract_pdf_download_url(wrapper_html, base_url=bulletin_url)

        return {
            "kind": "pdf",
            "source_url": bulletin_url,
            "download_url": download_url,
            "bulletin_name": bulletin_url.rsplit("/", 1)[-1],
        }

    def _parse_pdf_bulletin(self, payload: dict[str, str]) -> EmiliaRomagnaBulletin:
        bulletin_name = payload.get("bulletin_name", "")
        published_at = self._extract_date_from_pdf_name(bulletin_name)
        risk_level = self._extract_risk_from_pdf_name(bulletin_name)
        indice = self._risk_to_indice(risk_level)

        entry = EmiliaRomagnaRiskEntry(
            zone_id="ER-REG",
            zone_name="Emilia-Romagna",
            risk_level=risk_level,
            indice=indice,
            fwi=None,
        )

        return EmiliaRomagnaBulletin(
            source_id=self.source_id,
            source_url=payload.get("source_url", EMILIA_ROMAGNA_PDF_INDEX_URL.format(year=datetime.now(UTC).year)),
            days=[
                EmiliaRomagnaDay(
                    day=published_at,
                    zones=[entry],
                )
            ],
        )

    @staticmethod
    def _extract_latest_pdf_document_url(index_html: str, *, base_url: str) -> str:
        normalized = index_html.replace("\\u002F", "/").replace("\\/", "/")

        candidates = set(
            re.findall(r"(?:https?://[^\"\s<>]+|/[^\"\s<>]+)\.pdf", normalized, flags=re.IGNORECASE)
        )
        filtered = [
            item
            for item in candidates
            if "bollettino" in item.lower()
            and "copy" not in item.lower()
            and "rischio-incendi/bollettini-incendi-boschivi" in item
        ]
        if not filtered:
            raise ValueError("No Emilia-Romagna AIB PDF bulletin found on index page")

        def rank(url: str) -> tuple[int, str]:
            match = re.search(r"bollettino-(\d+)", url, flags=re.IGNORECASE)
            number = int(match.group(1)) if match else -1
            return number, url

        best = sorted(filtered, key=rank)[-1]
        return urljoin(base_url, best)

    @staticmethod
    def _extract_pdf_download_url(wrapper_html: str, *, base_url: str) -> str:
        soup = BeautifulSoup(wrapper_html, "html.parser")
        anchor = soup.find("a", href=re.compile(r"@@download/file", re.IGNORECASE))
        if not anchor or not anchor.get("href"):
            raise ValueError("Unable to resolve PDF download URL for Emilia-Romagna bulletin")
        return urljoin(base_url, str(anchor["href"]))

    @staticmethod
    def _extract_date_from_pdf_name(name: str) -> datetime | None:
        months = {
            "gennaio": 1,
            "febbraio": 2,
            "marzo": 3,
            "aprile": 4,
            "maggio": 5,
            "giugno": 6,
            "luglio": 7,
            "agosto": 8,
            "settembre": 9,
            "ottobre": 10,
            "novembre": 11,
            "dicembre": 12,
        }

        normalized = name.lower().replace("_", "-")
        match = re.search(
            r"-(\d{1,2})(?:-\d{1,2})?-(gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre)-(\d{4})",
            normalized,
        )
        if not match:
            return None

        day = int(match.group(1))
        month = months.get(match.group(2))
        year = int(match.group(3))
        if month is None:
            return None
        try:
            return datetime(year, month, day)
        except ValueError:
            return None

    @staticmethod
    def _extract_risk_from_pdf_name(name: str) -> str:
        normalized = name.lower().replace("_", "-")
        if "verde" in normalized:
            return "BASSO"
        if "giallo" in normalized:
            return "MEDIO"
        if "arancione" in normalized:
            return "ALTO"
        if "rosso" in normalized:
            return "MOLTO ALTO"
        return "ND"

    @staticmethod
    def _risk_to_indice(risk_level: str) -> int | None:
        mapping = {
            "BASSO": 2,
            "MEDIO": 3,
            "ALTO": 4,
            "MOLTO ALTO": 5,
        }
        return mapping.get(risk_level)

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
    def _is_atom_feed(source_text: str) -> bool:
        lowered = source_text.lower()
        return "<feed" in lowered and "www.w3.org/2005/atom" in lowered

    @staticmethod
    def _extract_atom_feed_published_at(source_text: str) -> datetime | None:
        match = re.search(r"<updated>([^<]+)</updated>", source_text)
        if not match:
            return None

        updated = match.group(1).strip()
        try:
            return datetime.strptime(updated, "%Y-%m-%dT%H:%M:%SZ")
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