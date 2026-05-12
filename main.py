import asyncio
import json
import logging
import os
import traceback
from datetime import datetime
from dataclasses import dataclass

from dotenv import load_dotenv

from collector import collect_veneto
from notify import send_daily_bulletin, send_failure_alert
from render import render_bulletin_images
from transform import build_render_payload


LOGGER = logging.getLogger("aib-bot")


@dataclass(frozen=True)
class RuntimeConfig:
    bot_token: str
    group_chat_id: str
    alert_chat_id: str
    verify_ssl: bool


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


def _load_config() -> RuntimeConfig:
    load_dotenv()
    bot_token = _get_env("BOT_TOKEN")
    group_chat_id = _get_env("GROUP_CHAT_ID")
    alert_chat_id = os.getenv("ALERT_CHAT_ID") or group_chat_id
    verify_ssl = _get_bool_env("VENETO_SOURCE_VERIFY_SSL", default=True)
    return RuntimeConfig(
        bot_token=bot_token,
        group_chat_id=group_chat_id,
        alert_chat_id=alert_chat_id,
        verify_ssl=verify_ssl,
    )


async def main(config: RuntimeConfig) -> None:
    bot_token = config.bot_token
    group_chat_id = config.group_chat_id
    verify_ssl = config.verify_ssl

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


async def _run_with_alerting(config: RuntimeConfig) -> None:
    try:
        await main(config)
    except Exception as exc:
        _log_event(
            "run_failed",
            error=str(exc),
            trace=traceback.format_exc(limit=5),
            timestamp=datetime.utcnow().isoformat(),
        )
        try:
            await send_failure_alert(
                bot_token=config.bot_token,
                chat_id=config.alert_chat_id,
                error=str(exc),
                occurred_at_utc=datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            )
            _log_event("alert_sent", alert_chat_id=config.alert_chat_id)
        except Exception as alert_exc:
            _log_event("alert_failed", error=str(alert_exc))
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    runtime_config = _load_config()
    asyncio.run(_run_with_alerting(runtime_config))
    
