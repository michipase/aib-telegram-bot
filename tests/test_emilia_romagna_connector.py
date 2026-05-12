import json
import shutil
import unittest
from pathlib import Path

from collectors.emilia_romagna import EmiliaRomagnaConnector
from collectors.orchestrator import ConnectorOrchestrator


class FixtureEmiliaRomagnaConnector(EmiliaRomagnaConnector):
    def __init__(self, fixture_path: str | Path) -> None:
        super().__init__(verify_ssl=False)
        self.fixture_path = Path(fixture_path)

    def fetch_source(self) -> str:
        return self.fixture_path.read_text(encoding="utf-8")


class EmiliaRomagnaConnectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts")
        shutil.rmtree(self.output_root, ignore_errors=True)
        self.connector = FixtureEmiliaRomagnaConnector(
            fixture_path="tests/fixtures/emilia_romagna_bulletin_sample.html",
        )
        self.expected_output_path = Path("tests/fixtures/emilia_romagna_expected_output.json")

    def test_parse_fixture_extracts_entries(self) -> None:
        bulletin = self.connector.run()

        self.assertEqual(bulletin.source_id, "emilia_romagna")
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(bulletin.days[0].day.strftime("%Y-%m-%d"), "2026-05-11")
        self.assertEqual(len(bulletin.entries), 4)
        self.assertEqual(len(bulletin.days[0].zones), 4)
        self.assertEqual(bulletin.entries[0].zone_id, "ER-PC")
        self.assertEqual(bulletin.entries[1].zone_id, "ER-BO")

    def test_parse_fixture_extracts_date(self) -> None:
        bulletin = self.connector.run()
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-11")

    def test_parse_fixture_uses_numeric_indice_for_risk(self) -> None:
        bulletin = self.connector.run()
        self.assertEqual(bulletin.entries[0].risk_level, "BASSO")
        self.assertEqual(bulletin.entries[1].risk_level, "ALTO")
        self.assertEqual(bulletin.entries[2].risk_level, "MOLTO ALTO")

    def test_parse_fixture_reads_fwi_decimal_with_comma(self) -> None:
        bulletin = self.connector.run()
        self.assertEqual(bulletin.entries[0].fwi, 5.4)

    def test_parse_fixture_skips_empty_zone_rows(self) -> None:
        bulletin = self.connector.run()
        zone_names = [entry.zone_name for entry in bulletin.entries]
        self.assertNotIn("", zone_names)

    def test_normalize_zone_id_known_province(self) -> None:
        self.assertEqual(self.connector._normalize_zone_id("Reggio Emilia"), "ER-RE")

    def test_normalize_zone_id_unknown(self) -> None:
        zone_id = self.connector._normalize_zone_id("Area Sconosciuta 99")
        self.assertTrue(zone_id.startswith("ER-UNK-"))

    def test_normalize_risk_level_from_label(self) -> None:
        self.assertEqual(self.connector._normalize_risk_level("moderato", None), "MEDIO")

    def test_parse_without_table_returns_empty_entries(self) -> None:
        bulletin = self.connector.parse_bulletin("<html><body>Nessuna tabella</body></html>")
        self.assertEqual(bulletin.entries, [])
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(bulletin.days[0].zones, [])

    def test_orchestrator_persists_fixture_run_output(self) -> None:
        orchestrator = ConnectorOrchestrator(self.output_root)
        result = orchestrator.run_connector(self.connector, run_label="emilia-fixture")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())

        parsed_payload = json.loads(result.parsed_path.read_text(encoding="utf-8"))
        expected_payload = json.loads(self.expected_output_path.read_text(encoding="utf-8"))

        self.assertEqual(parsed_payload, expected_payload)

    def test_extract_latest_pdf_document_url_prefers_highest_bulletin_number(self) -> None:
        html = """
        <html><body>
          <a href="/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026/bollettino-9-verde-3-10-maggio-2026.pdf">b9</a>
          <a href="/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026/copy_of_bollettino-10-verde-11-17-maggio-2026.pdf">copy</a>
          <a href="/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026/bollettino-10-verde-11-17-maggio-2026.pdf">b10</a>
        </body></html>
        """
        url = self.connector._extract_latest_pdf_document_url(
            html,
            base_url="https://protezionecivile.regione.emilia-romagna.it/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026",
        )
        self.assertIn("bollettino-10-verde-11-17-maggio-2026.pdf", url)
        self.assertNotIn("copy_of", url)

    def test_extract_pdf_download_url_from_wrapper_html(self) -> None:
        wrapper_html = """
        <html><body>
          <a href="/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026/bollettino-10-verde-11-17-maggio-2026.pdf/@@download/file">Scarica</a>
        </body></html>
        """
        download_url = self.connector._extract_pdf_download_url(
            wrapper_html,
            base_url="https://protezionecivile.regione.emilia-romagna.it/rischi-previsione-prevenzione/rischio-incendi/bollettini-incendi-boschivi/2026/bollettino-10-verde-11-17-maggio-2026.pdf",
        )
        self.assertTrue(download_url.endswith("@@download/file"))

    def test_parse_pdf_bulletin_builds_single_regional_entry(self) -> None:
        payload = {
            "kind": "pdf",
            "source_url": "https://example.test/bollettino-10-verde-11-17-maggio-2026.pdf",
            "download_url": "https://example.test/bollettino-10-verde-11-17-maggio-2026.pdf/@@download/file",
            "bulletin_name": "bollettino-10-verde-11-17-maggio-2026.pdf",
        }

        bulletin = self.connector.parse_bulletin(payload)
        self.assertEqual(bulletin.source_url, payload["source_url"])
        self.assertEqual(len(bulletin.days), 1)
        self.assertEqual(len(bulletin.entries), 1)
        self.assertEqual(bulletin.entries[0].zone_id, "ER-REG")
        self.assertEqual(bulletin.entries[0].risk_level, "BASSO")
        self.assertEqual(bulletin.entries[0].indice, 2)
        self.assertEqual(bulletin.days[0].day.strftime("%Y-%m-%d"), "2026-05-11")
