from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .base import Connector


@dataclass(frozen=True)
class ConnectorRunResult:
    source_id: str
    output_dir: Path
    raw_path: Path
    parsed_path: Path


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

    def _build_output_dir(self, source_id: str, *, run_label: str | None) -> Path:
        suffix = run_label or datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        return self.output_root / source_id / suffix

    def _to_serializable(self, payload: Any) -> Any:
        if is_dataclass(payload):
            return self._to_serializable(asdict(payload))
        if isinstance(payload, dict):
            return {key: self._to_serializable(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._to_serializable(item) for item in payload]
        if isinstance(payload, tuple):
            return [self._to_serializable(item) for item in payload]
        if isinstance(payload, (datetime, date)):
            return payload.isoformat()
        return payload