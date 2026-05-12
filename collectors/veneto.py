from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .base import Connector


VENETO_FWI_URL = "https://www.ambienteveneto.it/incendi/dati/FWI.json"
VENETO_MAP_URL = "https://www.ambienteveneto.it/incendi/venetorischio.html"


@dataclass(frozen=True)
class VenetoRiskEntry:
    zone_id: str
    zone_name: str
    fwi: float | None
    indice: int | None
    risk_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VenetoBulletin:
    source_id: str
    source_url: str
    days: list["VenetoDay"]

    @property
    def valid_for_date(self) -> datetime:
        return self.days[0].day

    @property
    def entries(self) -> list[VenetoRiskEntry]:
        return self.days[0].zones


@dataclass(frozen=True)
class VenetoDay:
    day: datetime
    zones: list[VenetoRiskEntry]


class VenetoConnector(Connector):
    def __init__(
        self,
        zone_metadata_path: str | Path,
        *,
        verify_ssl: bool = True,
        connect_timeout: int = 5,
        read_timeout: int = 15,
        retries: int = 2,
    ) -> None:
        super().__init__(
            "veneto",
            verify_ssl=verify_ssl,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            retries=retries,
        )
        self.zone_metadata_path = Path(zone_metadata_path)

    def fetch_source(self) -> dict[str, Any]:
        return self.get_json(VENETO_FWI_URL)

    def fetch_map_svg(self) -> str:
        return self.get_text(VENETO_MAP_URL)

    def parse_bulletin(self, raw_source: dict[str, Any]) -> VenetoBulletin:
        days = raw_source.get("GIORNI") or []
        if not days:
            raise ValueError("FWI payload does not contain any day entry")

        current_day = days[0]
        valid_for_date = datetime.strptime(str(current_day["GIORNO"]), "%Y%m%d")
        zone_lookup = self._load_zone_lookup()

        entries: list[VenetoRiskEntry] = []
        for raw_zone in current_day.get("ZONE", []):
            zone_id = str(raw_zone.get("ZONA", "")).zfill(2)
            if not zone_id or zone_id not in zone_lookup:
                continue
            if int(zone_id) > 26:
                continue

            zone_name = self._normalize_zone_name(zone_lookup[zone_id])
            indice = self._coerce_int(raw_zone.get("INDICE"))
            fwi = self._coerce_float(raw_zone.get("FWI"))
            entries.append(
                VenetoRiskEntry(
                    zone_id=zone_id,
                    zone_name=zone_name,
                    fwi=fwi,
                    indice=indice,
                    risk_level=self._calc_risk(indice),
                )
            )

        return VenetoBulletin(
            source_id=self.source_id,
            source_url=VENETO_FWI_URL,
            days=[
                VenetoDay(
                    day=valid_for_date,
                    zones=entries,
                )
            ],
        )

    def _load_zone_lookup(self) -> dict[str, str]:
        with self.zone_metadata_path.open("r", encoding="utf-8") as handle:
            zone_rows = json.load(handle)
        return {str(zone_id).zfill(2): zone_name for zone_id, zone_name in zone_rows}

    @staticmethod
    def _normalize_zone_name(zone_name: str) -> str:
        if zone_name.startswith("Non Montana "):
            return zone_name.replace("Non Montana ", "", 1) + " Non Montana"
        return zone_name

    @staticmethod
    def _calc_risk(indice: int | None) -> str:
        if indice is None:
            return "ND"
        if indice <= 2:
            return "BASSO"
        if indice == 3:
            return "MEDIO"
        if indice == 4:
            return "ALTO"
        return "MOLTO ALTO"

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None