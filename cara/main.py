import asyncio
import logging

from telethon import TelegramClient

from cara.config import settings
from cara.handlers import register_handlers

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

    register_handlers(client)

    await client.run_until_disconnected()


def main():
    asyncio.run(start())


if __name__ == "__main__":
    main()
