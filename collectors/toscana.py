from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Connector


TOSCANA_URL = "https://www.protezionecivilecomunale.toscana.it"


@dataclass(frozen=True)
class ToscanaRiskEntry:
    zone_id: str
    zone_name: str
    risk_level: str
    indice: int | None
    fwi: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToscanaBulletin:
    source_id: str
    source_url: str
    days: list["ToscanaDay"]

    @property
    def published_at(self) -> datetime | None:
        if not self.days:
            return None
        return self.days[0].day

    @property
    def entries(self) -> list[ToscanaRiskEntry]:
        if not self.days:
            return []
        return self.days[0].zones


@dataclass(frozen=True)
class ToscanaDay:
    day: datetime | None
    zones: list[ToscanaRiskEntry]


class ToscanaConnector(Connector):
    def __init__(
        self,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        super().__init__(
            "toscana",
            verify_ssl=verify_ssl,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries=retries,
        )

    def fetch_source(self) -> dict[str, Any]:
        html = self.get_text(TOSCANA_URL)
        pdf_url = self._discover_pdf_url(html)
        pdf_bytes = self._fetch_pdf_bytes(pdf_url) if pdf_url else None
        return {
            "html": html,
            "pdf_url": pdf_url,
            "pdf_bytes": pdf_bytes,
        }

    def parse_bulletin(self, raw_source: Any) -> ToscanaBulletin:
        html, pdf_bytes = self._coerce_raw_source(raw_source)

        html_entries = self._parse_html_entries(html) if html else []
        pdf_entries = self._parse_pdf_entries(pdf_bytes) if pdf_bytes and not html_entries else []
        entries = html_entries or pdf_entries

        published_at = self._extract_published_at(html) if html else None
        if published_at is None and pdf_bytes:
            published_at = self._extract_published_at(self._extract_pdf_text(pdf_bytes))

        return ToscanaBulletin(
            source_id=self.source_id,
            source_url=TOSCANA_URL,
            days=[
                ToscanaDay(
                    day=published_at,
                    zones=entries,
                )
            ],
        )

    def _fetch_pdf_bytes(self, pdf_url: str) -> bytes | None:
        response = self.session.get(pdf_url, timeout=self.timeout, verify=self.verify_ssl)
        response.raise_for_status()
        return response.content

    @classmethod
    def _coerce_raw_source(cls, raw_source: Any) -> tuple[str, bytes | None]:
        if isinstance(raw_source, dict):
            html = raw_source.get("html") or ""
            pdf_bytes = raw_source.get("pdf_bytes")
            if isinstance(pdf_bytes, str):
                pdf_bytes = pdf_bytes.encode("utf-8")
            return str(html), pdf_bytes
        if isinstance(raw_source, bytes):
            return "", raw_source
        return str(raw_source), None

    @classmethod
    def _parse_html_entries(cls, html: str) -> list[ToscanaRiskEntry]:
        soup = BeautifulSoup(html, "html.parser")
        table = cls._select_data_table(soup)
        if table is None:
            return []

        header_labels = [cls._normalize_label(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        zone_idx = cls._find_col_idx(header_labels, ["zona", "area", "settore"])
        risk_idx = cls._find_col_idx(header_labels, ["rischio", "pericolo", "livello"])
        indice_idx = cls._find_col_idx(header_labels, ["indice", "classe"])
        fwi_idx = cls._find_col_idx(header_labels, ["fwi"])

        entries: list[ToscanaRiskEntry] = []
        for row in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cells:
                continue

            zone_name = cls._safe_get(cells, zone_idx) or cls._safe_get(cells, 0)
            if not zone_name:
                continue

            risk_raw = cls._safe_get(cells, risk_idx)
            indice = cls._coerce_int(cls._safe_get(cells, indice_idx))
            fwi = cls._coerce_float(cls._safe_get(cells, fwi_idx))
            entries.append(
                ToscanaRiskEntry(
                    zone_id=cls._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=cls._normalize_risk_level(risk_raw, indice),
                    indice=indice,
                    fwi=fwi,
                )
            )

        return entries

    @classmethod
    def _parse_pdf_entries(cls, pdf_bytes: bytes) -> list[ToscanaRiskEntry]:
        text = cls._extract_pdf_text(pdf_bytes)
        entries: list[ToscanaRiskEntry] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            normalized_line = cls._normalize_label(line)
            if "zona" in normalized_line and ("rischio" in normalized_line or "livello" in normalized_line):
                continue

            parts = [part.strip() for part in re.split(r"\s*[;|]\s*", line) if part.strip()]
            if len(parts) < 2:
                continue

            zone_name = parts[0]
            risk_raw = parts[1]
            indice = cls._coerce_int(parts[2]) if len(parts) > 2 else None
            fwi = cls._coerce_float(parts[3]) if len(parts) > 3 else None
            entries.append(
                ToscanaRiskEntry(
                    zone_id=cls._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=cls._normalize_risk_level(risk_raw, indice),
                    indice=indice,
                    fwi=fwi,
                )
            )

        return entries

    @classmethod
    def _discover_pdf_url(cls, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            label = cls._normalize_label(anchor.get_text(" ", strip=True))
            href_norm = cls._normalize_label(href)
            if ".pdf" not in href.lower():
                continue
            score = 0
            if "incendi" in label or "aib" in label or "bollett" in label:
                score += 2
            if "incendi" in href_norm or "aib" in href_norm or "bollett" in href_norm:
                score += 1
            candidates.extend([href] * max(score, 1))

        if not candidates:
            return None

        return urljoin(TOSCANA_URL, candidates[-1])

    @staticmethod
    def _select_data_table(soup: BeautifulSoup) -> Any:
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
            if not headers:
                continue
            has_zone = any("zona" in header or "area" in header or "settore" in header for header in headers)
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
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        text = pdf_bytes.decode("latin-1", errors="ignore")
        literal_chunks = re.findall(r"\(([^()]*)\)", text)
        if literal_chunks:
            text = "\n".join(literal_chunks)
        return text.replace("\\n", "\n")

    @staticmethod
    def _normalize_label(label: str) -> str:
        text = unicodedata.normalize("NFKD", label)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text.lower()).strip()

    @classmethod
    def _normalize_zone_id(cls, zone_name: str) -> str:
        key = cls._normalize_label(zone_name)
        zone_map = {
            "appennino": "TOS-APP",
            "colline": "TOS-COL",
            "littorale": "TOS-LIT",
            "arcipelago": "TOS-ARC",
            "nord ovest": "TOS-NO",
            "nord-est": "TOS-NE",
            "nord est": "TOS-NE",
            "centro": "TOS-CEN",
            "sud": "TOS-SUD",
            "amiata": "TOS-AMI",
            "valdarno": "TOS-VAL",
            "maremma": "TOS-MAR",
        }

        for zone_key, zone_id in zone_map.items():
            if zone_key in key:
                return zone_id

        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-") or "unknown"
        return f"TOS-UNK-{slug[:12].upper()}"

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
        if any(token in risk for token in ("molto alto", "estremo", "rosso", "5", "4")):
            return "MOLTO ALTO"
        if any(token in risk for token in ("alto", "arancione", "3")):
            return "ALTO"
        if any(token in risk for token in ("medio", "moderato", "giallo")):
            return "MEDIO"
        if any(token in risk for token in ("basso", "verde", "1", "2")):
            return "BASSO"
        return "ND"

    @staticmethod
    def _extract_published_at(source_text: str) -> datetime | None:
        if not source_text:
            return None

        match = re.search(r"(\d{2}/\d{2}/\d{4})", source_text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d/%m/%Y")
            except ValueError:
                return None

        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", source_text)
        if not iso_match:
            return None

        try:
            return datetime.strptime(iso_match.group(1), "%Y-%m-%d")
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
from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import Connector


TOSCANA_URL = "https://www.protezionecivilecomunale.toscana.it"


@dataclass(frozen=True)
class ToscanaRiskEntry:
    zone_id: str
    zone_name: str
    risk_level: str
    indice: int | None
    fwi: float | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToscanaBulletin:
    source_id: str
    source_url: str
    days: list["ToscanaDay"]

    @property
    def published_at(self) -> datetime | None:
        if not self.days:
            return None
        return self.days[0].day

    @property
    def entries(self) -> list[ToscanaRiskEntry]:
        if not self.days:
            return []
        return self.days[0].zones


@dataclass(frozen=True)
class ToscanaDay:
    day: datetime | None
    zones: list[ToscanaRiskEntry]


class ToscanaConnector(Connector):
    def __init__(
        self,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        super().__init__(
            "toscana",
            verify_ssl=verify_ssl,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries=retries,
        )

    def fetch_source(self) -> dict[str, Any]:
        html = self.get_text(TOSCANA_URL)
        pdf_url = self._discover_pdf_url(html)
        pdf_bytes = self._fetch_pdf_bytes(pdf_url) if pdf_url else None
        return {
            "html": html,
            "pdf_url": pdf_url,
            "pdf_bytes": pdf_bytes,
        }

    def parse_bulletin(self, raw_source: Any) -> ToscanaBulletin:
        html, pdf_bytes = self._coerce_raw_source(raw_source)

        html_entries = self._parse_html_entries(html) if html else []
        pdf_entries = self._parse_pdf_entries(pdf_bytes) if pdf_bytes and not html_entries else []
        entries = html_entries or pdf_entries

        published_at = self._extract_published_at(html) if html else None
        if published_at is None and pdf_bytes:
            published_at = self._extract_published_at(self._extract_pdf_text(pdf_bytes))

        return ToscanaBulletin(
            source_id=self.source_id,
            source_url=TOSCANA_URL,
            days=[
                ToscanaDay(
                    day=published_at,
                    zones=entries,
                )
            ],
        )

    def _fetch_pdf_bytes(self, pdf_url: str) -> bytes | None:
        response = self.session.get(pdf_url, timeout=self.timeout, verify=self.verify_ssl)
        response.raise_for_status()
        return response.content

    @classmethod
    def _coerce_raw_source(cls, raw_source: Any) -> tuple[str, bytes | None]:
        if isinstance(raw_source, dict):
            html = raw_source.get("html") or ""
            pdf_bytes = raw_source.get("pdf_bytes")
            if isinstance(pdf_bytes, str):
                pdf_bytes = pdf_bytes.encode("utf-8")
            return str(html), pdf_bytes
        if isinstance(raw_source, bytes):
            return "", raw_source
        return str(raw_source), None

    @classmethod
    def _parse_html_entries(cls, html: str) -> list[ToscanaRiskEntry]:
        soup = BeautifulSoup(html, "html.parser")
        table = cls._select_data_table(soup)
        if table is None:
            return []

        header_labels = [cls._normalize_label(th.get_text(" ", strip=True)) for th in table.find_all("th")]
        zone_idx = cls._find_col_idx(header_labels, ["zona", "area", "settore"])
        risk_idx = cls._find_col_idx(header_labels, ["rischio", "pericolo", "livello"])
        indice_idx = cls._find_col_idx(header_labels, ["indice", "classe"])
        fwi_idx = cls._find_col_idx(header_labels, ["fwi"])

        entries: list[ToscanaRiskEntry] = []
        for row in table.find_all("tr"):
            cells = [td.get_text(" ", strip=True) for td in row.find_all("td")]
            if not cells:
                continue

            zone_name = cls._safe_get(cells, zone_idx) or cls._safe_get(cells, 0)
            if not zone_name:
                continue

            risk_raw = cls._safe_get(cells, risk_idx)
            indice = cls._coerce_int(cls._safe_get(cells, indice_idx))
            fwi = cls._coerce_float(cls._safe_get(cells, fwi_idx))
            entries.append(
                ToscanaRiskEntry(
                    zone_id=cls._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=cls._normalize_risk_level(risk_raw, indice),
                    indice=indice,
                    fwi=fwi,
                )
            )

        return entries

    @classmethod
    def _parse_pdf_entries(cls, pdf_bytes: bytes) -> list[ToscanaRiskEntry]:
        text = cls._extract_pdf_text(pdf_bytes)
        entries: list[ToscanaRiskEntry] = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if "zona" in cls._normalize_label(line) and ("rischio" in cls._normalize_label(line) or "livello" in cls._normalize_label(line)):
                continue

            parts = [part.strip() for part in re.split(r"\s*[;|]\s*", line) if part.strip()]
            if len(parts) < 2:
                continue

            zone_name = parts[0]
            risk_raw = parts[1]
            indice = cls._coerce_int(parts[2]) if len(parts) > 2 else None
            fwi = cls._coerce_float(parts[3]) if len(parts) > 3 else None
            entries.append(
                ToscanaRiskEntry(
                    zone_id=cls._normalize_zone_id(zone_name),
                    zone_name=zone_name,
                    risk_level=cls._normalize_risk_level(risk_raw, indice),
                    indice=indice,
                    fwi=fwi,
                )
            )

        return entries

    @classmethod
    def _discover_pdf_url(cls, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[str] = []
        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()
            label = cls._normalize_label(anchor.get_text(" ", strip=True))
            href_norm = cls._normalize_label(href)
            if ".pdf" not in href.lower():
                continue
            score = 0
            if "incendi" in label or "aib" in label or "bollett" in label:
                score += 2
            if "incendi" in href_norm or "aib" in href_norm or "bollett" in href_norm:
                score += 1
            candidates.extend([href] * max(score, 1))

        if not candidates:
            return None

        return urljoin(TOSCANA_URL, candidates[-1])

    @staticmethod
    def _select_data_table(soup: BeautifulSoup) -> Any:
        for table in soup.find_all("table"):
            headers = [th.get_text(" ", strip=True).lower() for th in table.find_all("th")]
            if not headers:
                continue
            has_zone = any("zona" in header or "area" in header or "settore" in header for header in headers)
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
    def _extract_pdf_text(pdf_bytes: bytes) -> str:
        text = pdf_bytes.decode("latin-1", errors="ignore")
        literal_chunks = re.findall(r"\(([^()]*)\)", text)
        if literal_chunks:
            text = "\n".join(literal_chunks)
        return text.replace("\\n", "\n")

    @staticmethod
    def _normalize_label(label: str) -> str:
        text = unicodedata.normalize("NFKD", label)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", text.lower()).strip()

    @classmethod
    def _normalize_zone_id(cls, zone_name: str) -> str:
        key = cls._normalize_label(zone_name)
        zone_map = {
            "appennino": "TOS-APP",
            "colline": "TOS-COL",
            "littorale": "TOS-LIT",
            "arcipelago": "TOS-ARC",
            "nord ovest": "TOS-NO",
            "nord-est": "TOS-NE",
            "nord est": "TOS-NE",
            "centro": "TOS-CEN",
            "sud": "TOS-SUD",
            "amiata": "TOS-AMI",
            "valdarno": "TOS-VAL",
            "maremma": "TOS-MAR",
        }
        for zone_key, zone_id in zone_map.items():
            if zone_key in key:
                return zone_id

        slug = re.sub(r"[^a-z0-9]+", "-", key).strip("-") or "unknown"
        return f"TOS-UNK-{slug[:12].upper()}"

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
        if any(token in risk for token in ("molto alto", "estremo", "rosso", "5", "4")):
            return "MOLTO ALTO"
        if any(token in risk for token in ("alto", "arancione", "3")):
            return "ALTO"
        if any(token in risk for token in ("medio", "moderato", "giallo")):
            return "MEDIO"
        if any(token in risk for token in ("basso", "verde", "1", "2")):
            return "BASSO"
        return "ND"

    @staticmethod
    def _extract_published_at(source_text: str) -> datetime | None:
        if not source_text:
            return None

        match = re.search(r"(\d{2}/\d{2}/\d{4})", source_text)
        if match:
            try:
                return datetime.strptime(match.group(1), "%d/%m/%Y")
            except ValueError:
                return None

        iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", source_text)
        if not iso_match:
            return None

        try:
            return datetime.strptime(iso_match.group(1), "%Y-%m-%d")
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