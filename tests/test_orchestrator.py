import json
import shutil
import unittest
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from collectors.base import Connector
from collectors.orchestrator import ConnectorOrchestrator


@dataclass(frozen=True)
class FakeBulletin:
    source_id: str
    entries: list[dict]


@dataclass(frozen=True)
class FakeDay:
    day: datetime
    zones: list[dict]


@dataclass(frozen=True)
class FakeDailyBulletin:
    source_id: str
    source_url: str
    days: list[FakeDay]


class FakeConnector(Connector):
    def __init__(self) -> None:
        super().__init__("fake-source")

    def fetch_source(self) -> dict:
        return {"ok": True, "items": [1, 2, 3]}

    def parse_bulletin(self, raw_source: dict) -> FakeBulletin:
        return FakeBulletin(source_id=self.source_id, entries=[{"count": len(raw_source["items"])}])


class FakeDailyConnector(Connector):
    def __init__(self, source_id: str, source_url: str, zones: list[dict]) -> None:
        super().__init__(source_id)
        self.source_url = source_url
        self.zones = zones

    def fetch_source(self) -> dict:
        return {"ok": True}

    def parse_bulletin(self, raw_source: dict) -> FakeDailyBulletin:
        return FakeDailyBulletin(
            source_id=self.source_id,
            source_url=self.source_url,
            days=[
                FakeDay(
                    day=datetime(2026, 5, 11),
                    zones=self.zones,
                )
            ],
        )


class ConnectorOrchestratorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts")
        shutil.rmtree(self.output_root, ignore_errors=True)

    def test_run_connector_saves_raw_and_parsed_output(self) -> None:
        orchestrator = ConnectorOrchestrator(self.output_root)
        result = orchestrator.run_connector(FakeConnector(), run_label="unit")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())

        raw_payload = json.loads(result.raw_path.read_text(encoding="utf-8"))
        parsed_payload = json.loads(result.parsed_path.read_text(encoding="utf-8"))

        self.assertEqual(raw_payload["items"], [1, 2, 3])
        self.assertEqual(parsed_payload["source_id"], "fake-source")
        self.assertEqual(parsed_payload["entries"][0]["count"], 3)

    def test_run_daily_aggregation_saves_single_cross_source_file(self) -> None:
        orchestrator = ConnectorOrchestrator(self.output_root)
        connectors = [
            FakeDailyConnector(
                source_id="veneto",
                source_url="https://example.test/veneto",
                zones=[{"zone_id": "01", "zone_name": "A", "risk_level": "BASSO", "indice": 1, "fwi": 0.0}],
            ),
            FakeDailyConnector(
                source_id="emilia_romagna",
                source_url="https://example.test/emilia",
                zones=[{"zone_id": "ER-BO", "zone_name": "Bologna", "risk_level": "ALTO", "indice": 4, "fwi": 18.0}],
            ),
        ]

        result = orchestrator.run_daily_aggregation(connectors)

        self.assertEqual(result.day, "2026-05-11")
        self.assertTrue(result.output_path.exists())
        self.assertIsNotNone(result.latest_path)
        assert result.latest_path is not None
        self.assertTrue(result.latest_path.exists())
        self.assertEqual(result.sources_count, 2)
        self.assertEqual(result.zones_count, 2)

        payload = json.loads(result.output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["day"], "2026-05-11")
        self.assertEqual(len(payload["sources"]), 2)
        self.assertEqual(len(payload["zones"]), 2)
        self.assertEqual(payload["zones"][0]["source_id"], "veneto")
        self.assertEqual(payload["zones"][1]["source_id"], "emilia_romagna")