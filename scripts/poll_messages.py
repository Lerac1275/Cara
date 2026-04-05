"""
Poll all messages from the configured channel in the last 48 hours,
structured as:
  - Top-level channel announcements (posts)
  - Each announcement's thread/comment replies
"""

import asyncio
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient
from telethon.tl.types import MessageService

from telethon.tl.types import PeerChannel

from cara.config import settings


async def poll_channel(hours: int = 48):
    client = TelegramClient(
        settings.session_name,
        settings.api_id,
        settings.api_hash,
    )
    await client.start()

    # Telegram channel IDs in the -100... format need the -100 prefix stripped
    # to get the bare channel ID for PeerChannel.
    print(f"DEBUG channel_id raw: {repr(settings.channel_id)}")
    channel_id_str = settings.channel_id.lstrip("-")
    if channel_id_str.startswith("100"):
        channel_id_str = channel_id_str[3:]
    print(f"DEBUG channel_id_str after strip: {repr(channel_id_str)}")
    channel = await client.get_entity(PeerChannel(int(channel_id_str)))
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    print(f"Polling channel: {getattr(channel, 'title', channel.id)}")
    print(f"Cutoff: {cutoff.isoformat()}")
    print("=" * 80)

    # Fetch top-level channel posts from the last 48 hours
    async for message in client.iter_messages(channel, offset_date=None, reverse=False):
        # Stop once we've gone past the cutoff
        if message.date < cutoff:
            break

        # Skip service messages (user joined, pinned message, etc.)
        if isinstance(message, MessageService):
            continue

        sender = await message.get_sender()
        sender_name = getattr(sender, "first_name", None) or getattr(sender, "title", "Unknown")

        print(f"\n[POST #{message.id}] {message.date.isoformat()}")
        print(f"  From: {sender_name}")
        text = (message.text or "(media/no text)").replace("\n", "\n  ")
        print(f"  {text}")

        # Fetch thread replies (comments) for this post
        reply_count = 0
        try:
            async for reply in client.iter_messages(channel, reply_to=message.id):
                if reply.date < cutoff:
                    continue
                reply_sender = await reply.get_sender()
                reply_name = getattr(reply_sender, "first_name", None) or getattr(reply_sender, "title", "Unknown")
                reply_text = (reply.text or "(media/no text)").replace("\n", "\n    ")
                print(f"    [{reply.date.isoformat()}] {reply_name}: {reply_text}")
                reply_count += 1
        except Exception as e:
            print(f"    (Could not fetch thread: {e})")

        if reply_count == 0:
            print("    (no comments)")

    print("\n" + "=" * 80)
    print("Done.")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(poll_channel())
