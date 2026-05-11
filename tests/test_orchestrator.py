import json
import shutil
import unittest
from dataclasses import dataclass
from pathlib import Path

from collectors.base import Connector
from collectors.orchestrator import ConnectorOrchestrator


@dataclass(frozen=True)
class FakeBulletin:
    source_id: str
    entries: list[dict]


class FakeConnector(Connector):
    def __init__(self) -> None:
        super().__init__("fake-source")

    def fetch_source(self) -> dict:
        return {"ok": True, "items": [1, 2, 3]}

    def parse_bulletin(self, raw_source: dict) -> FakeBulletin:
        return FakeBulletin(source_id=self.source_id, entries=[{"count": len(raw_source["items"])}])


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