import logging
import re

from cara.config import settings
from cara.shopeeAPI import ShopeeAffiliate
from cara.shopeeAPI import Country

logger = logging.getLogger(__name__)

_client: ShopeeAffiliate | None = None


def _get_client() -> ShopeeAffiliate:
    global _client
    if _client is None:
        _client = ShopeeAffiliate(
            app_id=settings.shopee_api_id,
            secret=settings.shopee_api_key,
            country=Country.SINGAPORE
        )
    return _client


URL_RE = re.compile(r"https?://\S+")

SHOPEE_DOMAIN_RE = re.compile(r"://(?:[\w-]+\.)*(?:shopee\.sg|shp\.ee)/", re.IGNORECASE)
SHOPEE_VIDEO_RE = re.compile(r"[?&]smtt=", re.IGNORECASE)


def is_shopee_link(url: str) -> bool:
    return SHOPEE_DOMAIN_RE.search(url) is not None


def is_shopee_video_link(url: str) -> bool:
    return is_shopee_link(url) and SHOPEE_VIDEO_RE.search(url) is not None


def generate_affiliate_link(
    product_url: str, sub_ids: list[str] | None = None
) -> dict:
    """Generate a Shopee affiliate link from a product URL.

    Parameters
    ----------
    product_url:
        Any Shopee product URL (e.g. ``https://shopee.sg/product/123``).
    sub_ids:
        Optional tracking identifiers attached to the generated link.

    Returns
    -------
    dict
        ``{"shortLink": "https://s.shopee.sg/abc123"}``
    """
    result = _get_client().generate_short_link(product_url, sub_ids)
    logger.info("Generated affiliate link for %s → %s", product_url, result)
    return result
