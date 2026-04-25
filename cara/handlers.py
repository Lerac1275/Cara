import logging

from telethon import TelegramClient, events
from telethon.tl.types import PeerUser

from cara.config import settings
from cara.link_service import (
    URL_RE,
    generate_affiliate_link,
    is_shopee_link,
    is_shopee_video_link,
)
from cara.state import bot_state

logger = logging.getLogger(__name__)


NOT_A_PRODUCT_LINK = "Need product link to convert!"


def _format_sender(sender) -> str:
    username = getattr(sender, "username", None)
    handle = f"@{username}" if username else "(no username)"
    return f"{handle} (id={sender.id})"


async def broadcast_admins(client: TelegramClient, message: str) -> None:
    for admin_id in settings.admin_list:
        try:
            await client.send_message(admin_id, message)
        except Exception as exc:
            logger.warning("Failed to notify admin %s: %r", admin_id, exc)


def register_handlers(client: TelegramClient):
    @client.on(events.NewMessage(chats=settings.discussion_group_id))
    async def handle_discussion_message(event: events.NewMessage.Event):
        # Auto-forwarded channel broadcasts land in the discussion group with
        # from_id = PeerChannel(linked_channel). Only act on real user messages.
        if not isinstance(event.message.from_id, PeerUser):
            return

        sender = await event.get_sender()
        if sender is None:
            return
        if sender.id in settings.admin_list or sender.id in settings.ignore_list:
            return

        urls = URL_RE.findall(event.raw_text or "")
        shopee_urls = [u for u in urls if is_shopee_link(u)]
        if not shopee_urls:
            return

        logger.info(
            "Detected %d Shopee URL(s) from user %s (of %d total).",
            len(shopee_urls), sender.id, len(urls),
        )

        entries: list[str] = []
        for url in shopee_urls:
            if is_shopee_video_link(url):
                logger.info("Shopee video link %s — marking as non-product.", url)
                entries.append(NOT_A_PRODUCT_LINK)
                continue
            try:
                result = generate_affiliate_link(url)
                entries.append(result["shortLink"])
            except Exception as exc:
                logger.info("Shopee link %s failed conversion: %r", url, exc)
                entries.append(NOT_A_PRODUCT_LINK)

        if not bot_state.is_active:
            return

        if len(entries) == 1:
            reply_text = entries[0]
        else:
            reply_text = "\n".join(f"{i}. {entry}" for i, entry in enumerate(entries, 1))

        try:
            await event.reply(reply_text, link_preview=False)
        except Exception as exc:
            logger.warning("Failed to reply in-thread: %r", exc)
            await broadcast_admins(
                client,
                f"Failed to post reply to {_format_sender(sender)}: {exc!r}\n"
                f"Reply was:\n{reply_text}",
            )

    @client.on(events.NewMessage(pattern=r"^/(on|off)$", incoming=True))
    async def handle_admin_command(event: events.NewMessage.Event):
        if not event.is_private:
            return
        sender = await event.get_sender()
        if sender is None or sender.id not in settings.admin_list:
            return

        command = event.raw_text.strip().lower()
        if command == "/off":
            bot_state.is_active = False
            logger.info("Admin %s toggled Cara OFF.", sender.id)
            await broadcast_admins(
                client,
                f"Cara paused by {_format_sender(sender)} — link tracking continues, "
                f"but no in-thread replies.",
            )
        elif command == "/on":
            bot_state.is_active = True
            logger.info("Admin %s toggled Cara ON.", sender.id)
            await broadcast_admins(
                client,
                f"Cara resumed by {_format_sender(sender)} — members will receive "
                f"converted links again.",
            )
