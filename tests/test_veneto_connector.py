import json
import shutil
import unittest
from pathlib import Path

from collectors.orchestrator import ConnectorOrchestrator
from collectors.veneto import VenetoConnector


class FixtureVenetoConnector(VenetoConnector):
    def __init__(self, zone_metadata_path: str | Path, fixture_path: str | Path) -> None:
        super().__init__(zone_metadata_path, verify_ssl=False)
        self.fixture_path = Path(fixture_path)

    def fetch_source(self) -> dict:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))


class VenetoConnectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts")
        shutil.rmtree(self.output_root, ignore_errors=True)

    def test_parse_fixture_filters_secondary_zones_and_normalizes_names(self) -> None:
        connector = FixtureVenetoConnector(
            zone_metadata_path="zone.json",
            fixture_path="tests/fixtures/veneto_fwi_sample.json",
        )

        bulletin = connector.run()

        self.assertEqual(bulletin.source_id, "veneto")
        self.assertEqual(bulletin.valid_for_date.strftime("%Y-%m-%d"), "2026-05-11")
        self.assertEqual(len(bulletin.entries), 2)
        self.assertEqual(bulletin.entries[0].zone_id, "01")
        self.assertEqual(bulletin.entries[0].risk_level, "BASSO")
        self.assertEqual(bulletin.entries[1].zone_name, "Provincia di Padova Non Montana")
        self.assertEqual(bulletin.entries[1].risk_level, "ALTO")

    def test_orchestrator_persists_fixture_run_output(self) -> None:
        connector = FixtureVenetoConnector(
            zone_metadata_path="zone.json",
            fixture_path="tests/fixtures/veneto_fwi_sample.json",
        )
        orchestrator = ConnectorOrchestrator(self.output_root)

        result = orchestrator.run_connector(connector, run_label="veneto-fixture")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())

        parsed_payload = json.loads(result.parsed_path.read_text(encoding="utf-8"))
        self.assertEqual(parsed_payload["source_id"], "veneto")
        self.assertEqual(len(parsed_payload["entries"]), 2)