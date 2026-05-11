from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collectors import ConnectorOrchestrator, VenetoConnector


def main() -> None:
    connector = VenetoConnector(
        "zone.json",
        verify_ssl=False,
    )
    orchestrator = ConnectorOrchestrator(".dev-output/connectors")
    result = orchestrator.run_connector(connector, run_label="latest")

    print(f"source={result.source_id}")
    print(f"raw={result.raw_path}")
    print(f"parsed={result.parsed_path}")


if __name__ == "__main__":
    main()