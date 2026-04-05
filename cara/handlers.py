import logging
import re

from telethon import TelegramClient, events

from cara.config import settings
from cara.link_service import convert_link
from cara.state import bot_state

logger = logging.getLogger(__name__)

URL_PATTERN = re.compile(r"https?://\S+")


def register_handlers(client: TelegramClient):
    @client.on(events.NewMessage(chats=settings.channel_id))
    async def handle_channel_message(event: events.NewMessage.Event):
        urls = URL_PATTERN.findall(event.raw_text)
        if not urls:
            return

        sender = await event.get_sender()
        sender_id = sender.id
        logger.info("Link detected from user %s in channel.", sender_id)

        for url in urls:
            converted = await convert_link(url)
            if converted is None:
                logger.warning("Link conversion failed for: %s", url)
                continue

            # Always notify the owner
            await client.send_message(
                settings.owner_id,
                f"Link from user {sender_id}:\n"
                f"Original: {url}\n"
                f"Converted: {converted}",
            )

            # Only DM the member when active
            if bot_state.is_active:
                await client.send_message(
                    sender_id,
                    f"Here's your converted link:\n{converted}",
                )

    @client.on(events.NewMessage(chats=settings.owner_id, pattern=r"^/(on|off)$"))
    async def handle_owner_command(event: events.NewMessage.Event):
        command = event.raw_text.strip().lower()
        if command == "/off":
            bot_state.is_active = False
            await event.reply("Cara paused — I'll still track links and notify you, but won't DM members.")
            logger.info("Owner toggled Cara OFF.")
        elif command == "/on":
            bot_state.is_active = True
            await event.reply("Cara resumed — members will receive converted links again.")
            logger.info("Owner toggled Cara ON.")
