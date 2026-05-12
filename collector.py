from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from collectors import VenetoBulletin, VenetoConnector


@dataclass(frozen=True)
class CollectedVenetoPayload:
    bulletin: VenetoBulletin
    map_svg: str


def collect_veneto(zone_metadata_path: str | Path, *, verify_ssl: bool = True) -> CollectedVenetoPayload:
    connector = VenetoConnector(zone_metadata_path, verify_ssl=verify_ssl)
    bulletin = connector.run()
    map_svg = connector.fetch_map_svg()
    return CollectedVenetoPayload(bulletin=bulletin, map_svg=map_svg)
