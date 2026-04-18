import asyncio
import logging

from telethon import TelegramClient

from cara.config import settings
from cara.handlers import broadcast_admins, register_handlers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def start():
    client = TelegramClient(
        settings.session_name,
        settings.api_id,
        settings.api_hash,
    )
    await client.start()
    logger.info("Cara is online.")

    # Warm the entity cache so admin IDs resolve without a prior interaction
    # in this process's lifetime. Without this, send_message(admin_id, ...)
    # raises "Could not find the input entity" on a cold session.
    dialog_count = 0
    async for _ in client.iter_dialogs(limit=500):
        dialog_count += 1
    logger.info("Warmed entity cache from %d dialogs.", dialog_count)

    register_handlers(client)

    await broadcast_admins(client, "Cara is online — link conversion active.")

    try:
        await client.run_until_disconnected()
    finally:
        try:
            await broadcast_admins(client, "Cara is shutting down — link conversion paused.")
        finally:
            await client.disconnect()


def main():
    try:
        asyncio.run(start())
    except KeyboardInterrupt:
        logger.info("Cara stopped by keyboard interrupt.")


if __name__ == "__main__":
    main()
