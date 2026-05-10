"""
Find a channel announcement by matching the start of its text against a regex,
then collect usernames of everyone who replied in the linked discussion thread
before a cutoff datetime. Output as CSV: user_id, username, n_msgs.
"""

import asyncio
import csv
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from telethon import TelegramClient
from telethon.tl.types import MessageService, PeerChannel, PeerUser

from cara.config import settings

# ── Configuration ─────────────────────────────────────────────────────────────

CHANNEL_ID = "-1001952812326"  # Channel to search
MESSAGE_ID = 337  # Set to the known message ID to skip the regex search; None to search
MESSAGE_START = r"^happy sat friends!!! been thinking of doing a giveaway and since it’s my birthday month, now feels like the right time! 🤍"  # Regex; matched against message.text (ignored when MESSAGE_ID is set)
CUTOFF_SGT = datetime(2026, 5, 11, 0, 0, 0)  # Replies strictly before this (SGT)
OUTPUT_DIR = Path(__file__).parent / "output"

# ──────────────────────────────────────────────────────────────────────────────

SGT = ZoneInfo("Asia/Singapore")
CUTOFF_UTC = CUTOFF_SGT.replace(tzinfo=SGT)


def resolve_sender(sender) -> tuple[str, str, str]:
    """Returns (username, first_name, last_name). username is '' if not set."""
    if sender is None:
        return "", "", ""
    username = getattr(sender, "username", None) or ""
    if username:
        username = f"@{username}"
    first = getattr(sender, "first_name", "") or ""
    last = getattr(sender, "last_name", "") or ""
    return username, first, last


async def main():
    client = TelegramClient(
        settings.session_name,
        settings.api_id,
        settings.api_hash,
    )
    await client.start()

    channel_id_str = CHANNEL_ID.lstrip("-")
    if channel_id_str.startswith("100"):
        channel_id_str = channel_id_str[3:]
    channel = await client.get_entity(PeerChannel(int(channel_id_str)))

    print(f"Channel: {getattr(channel, 'title', channel.id)}")

    if MESSAGE_ID is not None:
        target = await client.get_messages(channel, ids=MESSAGE_ID)
        if target is None:
            print(f"Message #{MESSAGE_ID} not found.")
            await client.disconnect()
            return
        print(f"Using message #{target.id}  {target.date.astimezone(SGT)}")
    else:
        pattern = re.compile(MESSAGE_START, re.IGNORECASE)
        print(f"Searching for pattern: {MESSAGE_START!r}")

        matches = []
        async for message in client.iter_messages(channel, limit=None):
            if isinstance(message, MessageService):
                continue
            text = message.text or ""
            if pattern.search(text):
                matches.append(message)

        if not matches:
            print("No matching announcement found.")
            await client.disconnect()
            return

        matches.sort(key=lambda m: m.date, reverse=True)
        target = matches[0]

        if len(matches) > 1:
            print(f"Found {len(matches)} matches; using most recent:")
            for m in matches:
                preview = (m.text or "").splitlines()[0][:80]
                print(f"  #{m.id}  {m.date.astimezone(SGT)}  {preview!r}")
        print(f"\nTarget message: #{target.id}  {target.date.astimezone(SGT)}")
        print(f"Message ID for future lookups: {target.id}")

    # Collect repliers
    counts: dict[int, int] = defaultdict(int)
    usernames: dict[int, str] = {}
    first_names: dict[int, str] = {}
    last_names: dict[int, str] = {}
    first_sent: dict[int, datetime] = {}
    last_sent: dict[int, datetime] = {}

    async for reply in client.iter_messages(channel, reply_to=target.id):
        if isinstance(reply, MessageService):
            continue
        if reply.date >= CUTOFF_UTC:
            continue
        from_id = reply.from_id
        if not isinstance(from_id, PeerUser):
            continue
        user_id = from_id.user_id
        counts[user_id] += 1
        if user_id not in usernames:
            sender = await reply.get_sender()
            username, first, last = resolve_sender(sender)
            usernames[user_id] = username
            first_names[user_id] = first
            last_names[user_id] = last
        sent_sgt = reply.date.astimezone(SGT)
        if user_id not in first_sent or sent_sgt < first_sent[user_id]:
            first_sent[user_id] = sent_sgt
        if user_id not in last_sent or sent_sgt > last_sent[user_id]:
            last_sent[user_id] = sent_sgt

    print(f"\nFound {len(counts)} unique repliers before {CUTOFF_SGT} SGT")

    OUTPUT_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now(SGT).strftime("%Y%m%d_%H%M%S")
    out_path = OUTPUT_DIR / f"usernames_{target.id}_{timestamp}.csv"

    fmt = "%Y-%m-%d %H:%M:%S"
    rows = sorted(
        (
            (
                uid,
                usernames[uid],
                first_names[uid],
                last_names[uid],
                counts[uid],
                first_sent[uid].strftime(fmt),
                last_sent[uid].strftime(fmt),
            )
            for uid in counts
        ),
        key=lambda r: (r[4], r[6]),
        reverse=True,
    )

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_id", "username", "first_name", "last_name", "n_msgs", "first_sent", "last_sent"])
        writer.writerows(rows)

    print(f"Wrote {out_path}")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
