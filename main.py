import asyncio
import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

from collector import collect_veneto
from notify import send_daily_bulletin
from render import render_bulletin_images
from transform import build_render_payload


LOGGER = logging.getLogger("aib-bot")


def _get_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required env var: {name}")
    return value


def _get_bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _log_event(event: str, **payload: object) -> None:
    LOGGER.info(json.dumps({"event": event, **payload}, ensure_ascii=False))


async def main() -> None:
    load_dotenv()
    bot_token = _get_env("BOT_TOKEN")
    group_chat_id = _get_env("GROUP_CHAT_ID")
    verify_ssl = _get_bool_env("VENETO_SOURCE_VERIFY_SSL", default=True)

    _log_event("run_started", verify_ssl=verify_ssl)
    collected = collect_veneto("zone.json", verify_ssl=verify_ssl)
    transformed = build_render_payload(collected.bulletin, collected.map_svg)

    output_day = collected.bulletin.valid_for_date.strftime("%Y%m%d")
    rendered = render_bulletin_images(transformed, output_day=output_day, media_dir="media")

    await send_daily_bulletin(
        bot_token=bot_token,
        chat_id=group_chat_id,
        map_path=rendered.map_path,
        table_path=rendered.table_path,
        bulletin_date=transformed.display_date,
    )
    _log_event("run_completed", output_day=output_day, timestamp=datetime.utcnow().isoformat())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        asyncio.run(main())
    except Exception as exc:
        _log_event("run_failed", error=str(exc))
        raise
    
