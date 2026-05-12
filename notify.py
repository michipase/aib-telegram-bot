from __future__ import annotations

from pathlib import Path

from telegram import Bot, InputMediaPhoto


async def send_daily_bulletin(
    *,
    bot_token: str,
    chat_id: str,
    map_path: str | Path,
    table_path: str | Path,
    bulletin_date: str,
) -> None:
    bot = Bot(token=bot_token)
    caption = (
        f"🔥🌲<b>NUOVO BOLLETTINO {bulletin_date}</b>\n"
        "Ogni giorno un nuovo bollettino di pericolo incendi boschivi.\n"
        "<a href=\"https://www.ambienteveneto.it/incendi/index.html\">Ulteriori informazioni</a>\n"
        "Prossimo bollettino domani pomeriggio!"
    )

    map_file_path = Path(map_path)
    table_file_path = Path(table_path)

    with map_file_path.open("rb") as map_file, table_file_path.open("rb") as table_file:
        media = [
            InputMediaPhoto(media=map_file, parse_mode="HTML", caption=caption),
            InputMediaPhoto(media=table_file),
        ]
        await bot.send_media_group(chat_id=chat_id, media=media)


async def send_failure_alert(
    *,
    bot_token: str,
    chat_id: str,
    error: str,
    occurred_at_utc: str,
) -> None:
    bot = Bot(token=bot_token)
    message = (
        "AIB bot daily run failed.\n"
        f"Time (UTC): {occurred_at_utc}\n"
        f"Error: {error}"
    )
    await bot.send_message(chat_id=chat_id, text=message)
