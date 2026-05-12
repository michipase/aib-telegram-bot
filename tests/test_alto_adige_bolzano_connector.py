import shutil
import unittest
from pathlib import Path

from collectors.alto_adige_bolzano import AltoAdigeBolzanoConnector
from collectors.orchestrator import ConnectorOrchestrator


class FixtureAltoAdigeBolzanoConnector(AltoAdigeBolzanoConnector):
    def __init__(self, fixture_path: str | Path) -> None:
        super().__init__(verify_ssl=False)
        self.fixture_path = Path(fixture_path)

    def fetch_source(self) -> str:
        return self.fixture_path.read_text(encoding="utf-8")


class AltoAdigeBolzanoConnectorTest(unittest.TestCase):
    def setUp(self) -> None:
        self.output_root = Path(".dev-output/test-artifacts-bolzano")
        shutil.rmtree(self.output_root, ignore_errors=True)
        self.connector = FixtureAltoAdigeBolzanoConnector(
            fixture_path="tests/fixtures/alto_adige_bulletin_sample.html",
        )

    def test_source_id(self) -> None:
        self.assertEqual(self.connector.source_id, "alto_adige_bolzano")

    def test_parse_fixture_extracts_entries(self) -> None:
        bulletin = self.connector.run()

        self.assertEqual(bulletin.source_id, "alto_adige_bolzano")
        self.assertEqual(len(bulletin.days), 1)
        # 5 zone valide (la riga vuota viene scartata)
        self.assertEqual(len(bulletin.entries), 5)
        self.assertEqual(len(bulletin.days[0].zones), 5)

    def test_parse_fixture_extracts_date(self) -> None:
        bulletin = self.connector.run()
        self.assertIsNotNone(bulletin.published_at)
        assert bulletin.published_at is not None
        self.assertEqual(bulletin.published_at.strftime("%Y-%m-%d"), "2026-05-12")

    def test_parse_fixture_zone_ids(self) -> None:
        bulletin = self.connector.run()
        zone_ids = [e.zone_id for e in bulletin.entries]
        self.assertIn("BZ-BZ", zone_ids)   # Bolzano
        self.assertIn("BZ-ME", zone_ids)   # Merano
        self.assertIn("BZ-BX", zone_ids)   # Bressanone
        self.assertIn("BZ-VV", zone_ids)   # Val Venosta
        self.assertIn("BZ-PT", zone_ids)   # Val Pusteria

    def test_parse_fixture_risk_levels_from_indice(self) -> None:
        bulletin = self.connector.run()
        by_zone = {e.zone_id: e for e in bulletin.entries}
        self.assertEqual(by_zone["BZ-BZ"].risk_level, "BASSO")
        self.assertEqual(by_zone["BZ-ME"].risk_level, "MEDIO")
        self.assertEqual(by_zone["BZ-BX"].risk_level, "ALTO")
        self.assertEqual(by_zone["BZ-VV"].risk_level, "MOLTO ALTO")

    def test_parse_fixture_fwi_decimal_with_comma(self) -> None:
        bulletin = self.connector.run()
        by_zone = {e.zone_id: e for e in bulletin.entries}
        self.assertAlmostEqual(by_zone["BZ-BZ"].fwi, 6.1)
        self.assertAlmostEqual(by_zone["BZ-VV"].fwi, 27.3)

    def test_parse_fixture_skips_empty_zone_rows(self) -> None:
        bulletin = self.connector.run()
        zone_names = [e.zone_name for e in bulletin.entries]
        self.assertNotIn("", zone_names)

    def test_parse_without_table_returns_empty_entries(self) -> None:
        bulletin = self.connector.parse_bulletin("<html><body>Nessuna tabella</body></html>")
        self.assertEqual(bulletin.entries, [])
        self.assertEqual(len(bulletin.days), 1)
        self.assertIsNone(bulletin.days[0].day)

    def test_normalize_zone_id_known_it(self) -> None:
        self.assertEqual(self.connector._normalize_zone_id("Merano"), "BZ-ME")

    def test_normalize_zone_id_known_de(self) -> None:
        self.assertEqual(self.connector._normalize_zone_id("Bruneck"), "BZ-BK")

    def test_normalize_zone_id_unknown(self) -> None:
        zone_id = self.connector._normalize_zone_id("Zona Sconosciuta 99")
        self.assertTrue(zone_id.startswith("BZ-UNK-"))

    def test_normalize_risk_level_italian_label(self) -> None:
        self.assertEqual(self.connector._normalize_risk_level("moderato", None), "MEDIO")
        self.assertEqual(self.connector._normalize_risk_level("Molto Alto", None), "MOLTO ALTO")

    def test_normalize_risk_level_german_label(self) -> None:
        self.assertEqual(self.connector._normalize_risk_level("Hoch", None), "ALTO")
        self.assertEqual(self.connector._normalize_risk_level("Sehr Hoch", None), "MOLTO ALTO")
        self.assertEqual(self.connector._normalize_risk_level("Niedrig", None), "BASSO")

    def test_normalize_risk_level_none_returns_nd(self) -> None:
        self.assertEqual(self.connector._normalize_risk_level(None, None), "ND")

    def test_extract_published_at_it_format(self) -> None:
        result = self.connector._extract_published_at("Bollettino del 12/05/2026 ore 08:00")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.strftime("%Y-%m-%d"), "2026-05-12")

    def test_extract_published_at_de_format(self) -> None:
        result = self.connector._extract_published_at("Aktualisiert: 12.05.2026")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.strftime("%Y-%m-%d"), "2026-05-12")

    def test_extract_published_at_iso_format(self) -> None:
        result = self.connector._extract_published_at("Updated 2026-05-12T08:00:00Z")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result.strftime("%Y-%m-%d"), "2026-05-12")

    def test_extract_published_at_missing_returns_none(self) -> None:
        self.assertIsNone(self.connector._extract_published_at("Nessuna data disponibile"))

    def test_bulletin_compatibility_properties(self) -> None:
        bulletin = self.connector.run()
        # published_at e entries sono alias di retrocompatibilità
        self.assertEqual(bulletin.published_at, bulletin.days[0].day)
        self.assertEqual(bulletin.entries, bulletin.days[0].zones)

    def test_orchestrator_persists_fixture_run_output(self) -> None:
        orchestrator = ConnectorOrchestrator(self.output_root)
        result = orchestrator.run_connector(self.connector, run_label="bolzano-fixture")

        self.assertTrue(result.raw_path.exists())
        self.assertTrue(result.parsed_path.exists())
        self.assertEqual(result.source_id, "alto_adige_bolzano")


if __name__ == "__main__":
    unittest.main()
