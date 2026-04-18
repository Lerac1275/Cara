"""
Poll all messages from the configured channel in the last 48 hours,
structured as:
  - Top-level channel announcements (posts)
  - Each announcement's thread/comment replies
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone, tzinfo
from pathlib import Path
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.tl.types import MessageService, PeerChannel

from cara.config import settings

# ── Configuration ─────────────────────────────────────────────────────────────

WRITE_TO_FILE = True  # Set True to save output to scripts/output/<timestamp>.txt
HOURS=24 # How far back to look

# ──────────────────────────────────────────────────────────────────────────────

SGT = ZoneInfo("Asia/Singapore")
OUTPUT_DIR = Path(__file__).parent / "output"


def to_sgt(dt: datetime) -> datetime:
    return dt.astimezone(SGT)


def fmt(dt: datetime) -> str:
    return to_sgt(dt).strftime("%Y-%m-%d %H:%M:%S SGT")


async def poll_channel(hours: int = 48):
    client = TelegramClient(
        settings.session_name,
        settings.api_id,
        settings.api_hash,
    )
    await client.start()

    # Telegram channel IDs in the -100... format need the -100 prefix stripped
    # to get the bare channel ID for PeerChannel.
    channel_id_str = settings.channel_id.lstrip("-")
    if channel_id_str.startswith("100"):
        channel_id_str = channel_id_str[3:]
    channel = await client.get_entity(PeerChannel(int(channel_id_str)))

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    lines = []

    def emit(text: str = ""):
        print(text)
        lines.append(text)

    emit(f"Polling channel: {getattr(channel, 'title', channel.id)}")
    emit(f"Cutoff: {fmt(cutoff)}")
    emit("=" * 80)

    async for message in client.iter_messages(channel, offset_date=None, reverse=False):
        if message.date < cutoff:
            break
        if isinstance(message, MessageService):
            continue

        sender = await message.get_sender()
        sender_name = getattr(sender, "first_name", None) or getattr(sender, "title", "Unknown")

        emit()
        emit(f"[POST #{message.id}] {fmt(message.date)}")
        emit(f"  From: {sender_name}")
        text = (message.text or "(media/no text)").replace("\n", "\n  ")
        emit(f"  {text}")

        reply_count = 0
        try:
            async for reply in client.iter_messages(channel, reply_to=message.id):
                if reply.date < cutoff:
                    continue
                reply_sender = await reply.get_sender()
                reply_name = getattr(reply_sender, "first_name", None) or getattr(reply_sender, "title", "Unknown")
                reply_text = (reply.text or "(media/no text)").replace("\n", "\n    ")
                emit(f"    [{fmt(reply.date)}] {reply_name}: {reply_text}")
                reply_count += 1
        except Exception as e:
            emit(f"    (Could not fetch thread: {e})")

        if reply_count == 0:
            emit("    (no comments)")

    emit()
    emit("=" * 80)
    emit("Done.")
    await client.disconnect()

    if WRITE_TO_FILE:
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now(SGT).strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"{timestamp}.txt"
        out_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"\nOutput saved to {out_path}")


if __name__ == "__main__":
    asyncio.run(poll_channel(hours=HOURS))
