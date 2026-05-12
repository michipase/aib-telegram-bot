from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from bs4 import BeautifulSoup

from collectors import VenetoBulletin


DEFAULT_FILL = "#cccccc"
RISK_COLORS = {
    "BASSO": "#00ff00",
    "MEDIO": "#ffff00",
    "ALTO": "#ffaa00",
    "MOLTO ALTO": "#ff0000",
}


@dataclass(frozen=True)
class RenderPayload:
    formatted_table: pd.DataFrame
    styled_html: str
    map_svg: str
    display_date: str


def build_render_payload(bulletin: VenetoBulletin, map_svg_raw: str) -> RenderPayload:
    date_label = bulletin.valid_for_date.strftime("%d/%m/%y")
    frame = pd.DataFrame([entry.to_dict() for entry in bulletin.entries])
    frame = frame.rename(
        columns={
            "zone_id": "id",
            "zone_name": "name",
            "fwi": "FWI",
            "indice": "INDICE",
            "risk_level": "RISCHIO",
        }
    )

    map_svg = _apply_map_fill(map_svg_raw, frame)
    formatted_table = frame.sort_values("name", ignore_index=True)[["name", "FWI", "INDICE", "RISCHIO"]]

    styled_table = (
        formatted_table.style.apply(_color_row, axis=1)
        .format(precision=2, thousands=".", decimal=",")
        .set_caption(f"Rischio incendio 🔥🌲</br>Aggiornamento: <b>{date_label}</b>")
    )

    return RenderPayload(
        formatted_table=formatted_table,
        styled_html=styled_table.to_html(index=False, classes="df_style.css"),
        map_svg=map_svg,
        display_date=date_label,
    )


def _apply_map_fill(map_svg_raw: str, frame: pd.DataFrame) -> str:
    soup = BeautifulSoup(map_svg_raw, "lxml")
    groups = soup.find_all(name="g", id=lambda value: value and value.startswith("GI_"))
    for group in groups:
        zone_id = group.get("id", "")[3:]
        group["fill"] = _zone_fill_color(zone_id, frame)
    return soup.prettify()


def _zone_fill_color(zone_id: str, frame: pd.DataFrame) -> str:
    row = frame.loc[frame["id"] == zone_id, "RISCHIO"]
    if row.empty:
        return DEFAULT_FILL
    risk_level = str(row.iloc[0]).strip().upper()
    return RISK_COLORS.get(risk_level, DEFAULT_FILL)


def _color_row(row: pd.Series) -> list[str]:
    color = RISK_COLORS.get(str(row.get("RISCHIO", "")).strip().upper(), DEFAULT_FILL)
    return [f"background-color: {color}"] * len(row)
