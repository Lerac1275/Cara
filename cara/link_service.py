import logging

logger = logging.getLogger(__name__)


async def convert_link(original_url: str) -> str | None:
    """Convert a link through the external service.

    This is a stub — replace with the actual service integration
    once the external API is available.
    """
    # TODO: Replace with real external service call
    logger.info("Converting link: %s", original_url)
    converted = f"{original_url}?converted=true"
    return converted
