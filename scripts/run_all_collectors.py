from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collectors import ConnectorOrchestrator, EmiliaRomagnaConnector, ToscanaConnector, VenetoConnector


ROOT = Path(__file__).resolve().parents[1]


class FixtureVenetoConnector(VenetoConnector):
    def __init__(self) -> None:
        super().__init__(ROOT / "zone.json", verify_ssl=False)
        self.fixture_path = ROOT / "tests/fixtures/veneto_fwi_sample.json"

    def fetch_source(self) -> dict:
        return json.loads(self.fixture_path.read_text(encoding="utf-8"))


class FixtureEmiliaRomagnaConnector(EmiliaRomagnaConnector):
    def __init__(self) -> None:
        super().__init__(verify_ssl=False)
        self.fixture_path = ROOT / "tests/fixtures/emilia_romagna_bulletin_sample.html"

    def fetch_source(self) -> str:
        return self.fixture_path.read_text(encoding="utf-8")


class FixtureToscanaConnector(ToscanaConnector):
    def __init__(self) -> None:
        super().__init__(verify_ssl=False)
        self.html_fixture_path = ROOT / "tests/fixtures/toscana_bulletin_sample.html"
        self.pdf_fixture_path = ROOT / "tests/fixtures/toscana_bulletin_sample.pdf"

    def fetch_source(self) -> dict[str, object]:
        return {
            "html": self.html_fixture_path.read_text(encoding="utf-8"),
            "pdf_bytes": self.pdf_fixture_path.read_bytes(),
        }


def build_live_connectors(*, verify_ssl: bool) -> list:
    return [
        VenetoConnector(ROOT / "zone.json", verify_ssl=verify_ssl),
        EmiliaRomagnaConnector(verify_ssl=verify_ssl),
        ToscanaConnector(verify_ssl=verify_ssl),
    ]


def build_fixture_connectors() -> list:
    return [
        FixtureVenetoConnector(),
        FixtureEmiliaRomagnaConnector(),
        FixtureToscanaConnector(),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run all available collectors and persist their outputs.")
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Run against checked-in fixtures instead of live sources.",
    )
    parser.add_argument(
        "--output-root",
        default=str(ROOT / ".dev-output/connectors"),
        help="Directory where raw/parsed/aggregate JSON files are written.",
    )
    parser.add_argument(
        "--run-label",
        default="latest",
        help="Subdirectory label used for each connector run.",
    )
    parser.add_argument(
        "--no-aggregate",
        action="store_true",
        help="Skip the daily aggregate JSON generation step.",
    )
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Enable SSL verification for live sources.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    orchestrator = ConnectorOrchestrator(args.output_root)
    connectors = build_fixture_connectors() if args.fixtures else build_live_connectors(verify_ssl=args.verify_ssl)

    successful_connectors = []
    for connector in connectors:
        try:
            result = orchestrator.run_connector(connector, run_label=args.run_label)
        except Exception as exc:
            print(f"[ERROR] {connector.source_id}: {exc}")
            continue

        successful_connectors.append(connector)
        print(f"[OK] {result.source_id}")
        print(f"  raw:    {result.raw_path}")
        print(f"  parsed: {result.parsed_path}")

    if not successful_connectors:
        print("No collector completed successfully.")
        return 1

    if args.no_aggregate:
        return 0

    aggregate = orchestrator.run_daily_aggregation(successful_connectors, latest_label="latest")
    print("[AGGREGATE]")
    print(f"  day:     {aggregate.day}")
    print(f"  output:  {aggregate.output_path}")
    print(f"  latest:  {aggregate.latest_path}")
    print(f"  sources: {aggregate.sources_count}")
    print(f"  zones:   {aggregate.zones_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())