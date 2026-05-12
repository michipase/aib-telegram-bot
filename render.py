from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import imgkit

from transform import RenderPayload


@dataclass(frozen=True)
class RenderedMedia:
    map_path: Path
    table_path: Path


def render_bulletin_images(payload: RenderPayload, *, output_day: str, media_dir: str | Path) -> RenderedMedia:
    target_dir = Path(media_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    table_path = target_dir / f"{output_day}_table.jpg"
    map_path = target_dir / f"{output_day}_map.jpg"

    imgkit.from_string(
        payload.styled_html,
        str(table_path),
        options={"width": 600},
        css="style/df_style.css",
    )
    imgkit.from_string(
        payload.map_svg,
        str(map_path),
        options={"width": 600},
    )

    return RenderedMedia(map_path=map_path, table_path=table_path)
