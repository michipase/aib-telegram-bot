from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from .base import Connector


@dataclass(frozen=True)
class ConnectorRunResult:
    source_id: str
    output_dir: Path
    raw_path: Path
    parsed_path: Path


@dataclass(frozen=True)
class DailyAggregationResult:
    day: str
    output_path: Path
    latest_path: Path | None
    sources_count: int
    zones_count: int


class ConnectorOrchestrator:
    def __init__(self, output_root: str | Path = ".dev-output/connectors") -> None:
        self.output_root = Path(output_root)

    def run_connector(self, connector: Connector, *, run_label: str | None = None) -> ConnectorRunResult:
        raw_payload = connector.fetch_source()
        parsed_payload = connector.parse_bulletin(raw_payload)

        output_dir = self._build_output_dir(connector.source_id, run_label=run_label)
        output_dir.mkdir(parents=True, exist_ok=True)

        raw_path = output_dir / "raw.json"
        parsed_path = output_dir / "parsed.json"

        raw_path.write_text(
            json.dumps(self._to_serializable(raw_payload), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        parsed_path.write_text(
            json.dumps(self._to_serializable(parsed_payload), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return ConnectorRunResult(
            source_id=connector.source_id,
            output_dir=output_dir,
            raw_path=raw_path,
            parsed_path=parsed_path,
        )

    def run_daily_aggregation(
        self,
        connectors: list[Connector],
        *,
        target_day: str | date | datetime | None = None,
        latest_label: str | None = "latest",
    ) -> DailyAggregationResult:
        serialized_bulletins: list[dict[str, Any]] = []
        for connector in connectors:
            parsed_payload = connector.parse_bulletin(connector.fetch_source())
            serialized_payload = self._to_serializable(parsed_payload)
            if isinstance(serialized_payload, dict):
                serialized_bulletins.append(serialized_payload)

        selected_day = self._resolve_target_day(serialized_bulletins, target_day=target_day)
        aggregated_payload = self._build_daily_payload(serialized_bulletins, day=selected_day)

        daily_dir = self.output_root / "daily"
        daily_dir.mkdir(parents=True, exist_ok=True)

        output_path = daily_dir / f"{selected_day}.json"
        output_path.write_text(
            json.dumps(aggregated_payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        latest_path: Path | None = None
        if latest_label:
            latest_path = daily_dir / f"{latest_label}.json"
            latest_path.write_text(
                json.dumps(aggregated_payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        return DailyAggregationResult(
            day=selected_day,
            output_path=output_path,
            latest_path=latest_path,
            sources_count=len(aggregated_payload["sources"]),
            zones_count=len(aggregated_payload["zones"]),
        )

    def _build_output_dir(self, source_id: str, *, run_label: str | None) -> Path:
        suffix = run_label or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return self.output_root / source_id / suffix

    def _build_daily_payload(self, bulletins: list[dict[str, Any]], *, day: str) -> dict[str, Any]:
        sources: list[dict[str, Any]] = []
        zones: list[dict[str, Any]] = []

        for bulletin in bulletins:
            source_id = bulletin.get("source_id")
            source_url = bulletin.get("source_url")
            day_entries = bulletin.get("days") or []
            day_data = self._find_day_entry(day_entries, day=day)
            if day_data is None:
                continue

            day_zones = day_data.get("zones") or []
            sources.append(
                {
                    "source_id": source_id,
                    "source_url": source_url,
                    "zones_count": len(day_zones),
                }
            )

            for zone in day_zones:
                zone_payload = dict(zone)
                zone_payload["source_id"] = source_id
                zones.append(zone_payload)

        return {
            "day": day,
            "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "sources": sources,
            "zones": zones,
        }

    def _find_day_entry(self, day_entries: list[dict[str, Any]], *, day: str) -> dict[str, Any] | None:
        for entry in day_entries:
            current = entry.get("day")
            if self._normalize_day_str(current) == day:
                return entry
        return None

    def _resolve_target_day(self, bulletins: list[dict[str, Any]], *, target_day: str | date | datetime | None) -> str:
        if target_day is not None:
            return self._normalize_day_str(target_day)

        detected_days: list[str] = []
        for bulletin in bulletins:
            for day_entry in bulletin.get("days") or []:
                normalized = self._normalize_day_str(day_entry.get("day"))
                if normalized:
                    detected_days.append(normalized)

        if detected_days:
            return sorted(detected_days)[-1]

        return datetime.utcnow().date().isoformat()

    def _normalize_day_str(self, value: str | date | datetime | Any) -> str:
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()

        text = str(value).strip()
        if not text:
            return ""
        return text[:10]

    def _to_serializable(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return self._to_serializable(asdict(payload))
        if isinstance(payload, dict):
            return {key: self._to_serializable(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._to_serializable(item) for item in payload]
        if isinstance(payload, tuple):
            return [self._to_serializable(item) for item in payload]
        if isinstance(payload, bytes):
            return payload.decode("latin-1", errors="replace")
        if isinstance(payload, (datetime, date)):
            return payload.isoformat()
        return payload