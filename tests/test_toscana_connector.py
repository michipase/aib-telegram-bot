import json
import shutil
import unittest
from pathlib import Path

from collectors.orchestrator import ConnectorOrchestrator
from collectors.toscana import ToscanaConnector


class FixtureToscanaConnector(ToscanaConnector):
    def __init__(self, fixture_path: str | Path, *, pdf_fixture_path: str | Path | None = None) -> None:
        super().__init__(verify_ssl=False)
        self.fixture_path = Path(fixture_path)
        self.pdf_fixture_path = Path(pdf_fixture_path) if pdf_fixture_path else None

    def fetch_source(self) -> dict[str, object]:
        html = self.fixture_path.read_text(encoding="utf-8")
        pdf_bytes = None
        if self.pdf_fixture_path is not None:
            pdf_bytes = self.pdf_fixture_path.read_bytes()
        return {
            "html": html,
            "pdf_bytes": pdf_bytes,
        }


class TestToscanaConnector(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts")
        shutil.rmtree(self.output_root, ignore_errors=True)

    def test_parse_html_fixture_extracts_entries(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")

        bulletin = connector.run()

        self.assertEqual(bulletin.source_id, "toscana")
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-12")
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(len(bulletin.days[0].zones), 3)
        self.assertEqual(bulletin.entries[0].zone_id, "TOS-APP")
        self.assertEqual(bulletin.entries[1].risk_level, "ALTO")
        self.assertEqual(bulletin.entries[2].fwi, 31.0)

    def test_parse_pdf_fixture_as_fallback(self) -> None:
        connector = FixtureToscanaConnector(
            "tests/fixtures/toscana_bulletin_sample.html",
            pdf_fixture_path="tests/fixtures/toscana_bulletin_sample.pdf",
        )

        bulletin = connector.parse_bulletin(
            {
                "html": "<html><body><p>Nessuna tabella disponibile</p></body></html>",
                "pdf_bytes": connector.pdf_fixture_path.read_bytes(),
            }
        )

        self.assertEqual(len(bulletin.entries), 2)
        self.assertEqual(bulletin.entries[0].zone_id, "TOS-COL")
        self.assertEqual(bulletin.entries[0].risk_level, "MEDIO")
        self.assertEqual(bulletin.entries[1].zone_id, "TOS-MAR")
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-12")

    def test_discover_pdf_url_prefers_bulletin_link(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")
        html = connector.fixture_path.read_text(encoding="utf-8")

        pdf_url = connector._discover_pdf_url(html)

        self.assertEqual(pdf_url, "https://www.protezionecivilecomunale.toscana.it/media/bollettino_incendi_20260512.pdf")

    def test_parse_without_table_returns_empty_entries(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")

        bulletin = connector.parse_bulletin("<html><body>Bollettino del 12/05/2026</body></html>")

        self.assertEqual(bulletin.entries, [])
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(bulletin.days[0].zones, [])

    def test_orchestrator_persists_fixture_run_output(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")
        orchestrator = ConnectorOrchestrator(self.output_root)

        result = orchestrator.run_connector(connector, run_label="toscana-fixture")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())

        parsed_payload = json.loads(result.parsed_path.read_text(encoding="utf-8"))
        self.assertEqual(parsed_payload["source_id"], "toscana")
        self.assertEqual(len(parsed_payload["days"]), 1)
        self.assertEqual(len(parsed_payload["days"][0]["zones"]), 3)
import json
import shutil
import unittest
from pathlib import Path

from collectors.orchestrator import ConnectorOrchestrator
from collectors.toscana import ToscanaConnector


class FixtureToscanaConnector(ToscanaConnector):
    def __init__(self, fixture_path: str | Path, *, pdf_fixture_path: str | Path | None = None) -> None:
        super().__init__(verify_ssl=False)
        self.fixture_path = Path(fixture_path)
        self.pdf_fixture_path = Path(pdf_fixture_path) if pdf_fixture_path else None

    def fetch_source(self) -> dict[str, object]:
        html = self.fixture_path.read_text(encoding="utf-8")
        pdf_bytes = None
        if self.pdf_fixture_path is not None:
            pdf_bytes = self.pdf_fixture_path.read_bytes()
        return {
            "html": html,
            "pdf_bytes": pdf_bytes,
        }


class ToscanaConnectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts")
        shutil.rmtree(self.output_root, ignore_errors=True)

    def test_parse_html_fixture_extracts_entries(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")

        bulletin = connector.run()

        self.assertEqual(bulletin.source_id, "toscana")
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-12")
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(len(bulletin.days[0].zones), 3)
        self.assertEqual(bulletin.entries[0].zone_id, "TOS-APP")
        self.assertEqual(bulletin.entries[1].risk_level, "ALTO")
        self.assertEqual(bulletin.entries[2].fwi, 31.0)

    def test_parse_pdf_fixture_as_fallback(self) -> None:
        connector = FixtureToscanaConnector(
            "tests/fixtures/toscana_bulletin_sample.html",
            pdf_fixture_path="tests/fixtures/toscana_bulletin_sample.pdf",
        )

        bulletin = connector.parse_bulletin(
            {
                "html": "<html><body><p>Nessuna tabella disponibile</p></body></html>",
                "pdf_bytes": connector.pdf_fixture_path.read_bytes(),
            }
        )

        self.assertEqual(len(bulletin.entries), 2)
        self.assertEqual(bulletin.entries[0].zone_id, "TOS-COL")
        self.assertEqual(bulletin.entries[0].risk_level, "MEDIO")
        self.assertEqual(bulletin.entries[1].zone_id, "TOS-MAR")
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-12")

    def test_discover_pdf_url_prefers_bulletin_link(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")
        html = connector.fixture_path.read_text(encoding="utf-8")

        pdf_url = connector._discover_pdf_url(html)

        self.assertEqual(pdf_url, "https://www.protezionecivilecomunale.toscana.it/media/bollettino_incendi_20260512.pdf")

    def test_parse_without_table_returns_empty_entries(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")

        bulletin = connector.parse_bulletin("<html><body>Bollettino del 12/05/2026</body></html>")

        self.assertEqual(bulletin.entries, [])
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(bulletin.days[0].zones, [])

    def test_orchestrator_persists_fixture_run_output(self) -> None:
        connector = FixtureToscanaConnector("tests/fixtures/toscana_bulletin_sample.html")
        orchestrator = ConnectorOrchestrator(self.output_root)

        result = orchestrator.run_connector(connector, run_label="toscana-fixture")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())

        parsed_payload = json.loads(result.parsed_path.read_text(encoding="utf-8"))
        self.assertEqual(parsed_payload["source_id"], "toscana")
        self.assertEqual(len(parsed_payload["days"]), 1)
        self.assertEqual(len(parsed_payload["days"][0]["zones"]), 3)