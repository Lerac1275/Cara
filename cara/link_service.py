import logging
import re

import requests

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
SHOPEE_SHORT_DOMAIN_RE = re.compile(r"://(?:[\w-]+\.)*(?:shp\.ee|s\.shopee\.sg)/", re.IGNORECASE)
# Final product pages take the form /product/{shopId}/{itemId} or
# /opaanlp/{shopId}/{itemId} (affiliate landing page that JS-redirects to
# /product/...). Both expose the IDs in the path directly, so we can short-circuit.
SHOPEE_PRODUCT_ID_RE = re.compile(r"/(?:product|opaanlp)/(\d+)/(\d+)")
SHOPEE_LIVE_DOMAIN_RE = re.compile(r"://live\.shopee\.", re.IGNORECASE)


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


def _resolve_short_link(url: str) -> str:
    """Follow redirects on Shopee short links to recover the canonical URL."""
    if not SHOPEE_SHORT_DOMAIN_RE.search(url):
        return url
    response = requests.get(url, allow_redirects=True, timeout=5)
    return response.url


def _parse_shop_item_ids(url: str) -> tuple[int, int] | None:
    """Extract ``(shop_id, item_id)`` from a Shopee product/opaanlp URL.

    Returns ``None`` if the URL doesn't match a product page (e.g. a Shopee
    Live share URL on ``live.shopee.*``).
    """
    if SHOPEE_LIVE_DOMAIN_RE.search(url):
        return None
    match = SHOPEE_PRODUCT_ID_RE.search(url)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def estimate_commission(affiliate_short_link: str) -> float | None:
    """Estimate the absolute affiliate commission for a generated short link.

    Resolves the affiliate short link (so we land on the product/opaanlp page,
    not the user's original short link), parses ``shopId`` / ``itemId``, and
    queries ``productOfferV2``. Returns ``priceMax * commissionRate`` (the
    upper-bound payout) or ``None`` if any step fails.
    """
    try:
        resolved = _resolve_short_link(affiliate_short_link)
        ids = _parse_shop_item_ids(resolved)
        if ids is None:
            logger.info(
                "No shop/item IDs in %s (resolved: %s)",
                affiliate_short_link, resolved,
            )
            return None
        shop_id, item_id = ids
        offer = _get_client().product_offer(item_id=item_id, shop_id=shop_id)
        if offer is None:
            logger.info("No productOfferV2 node for shop=%s item=%s", shop_id, item_id)
            return None
        price_max = float(offer.get("priceMax") or 0)
        rate = float(offer.get("commissionRate") or 0)
        return price_max * rate
    except Exception as exc:
        logger.info("Commission estimate failed for %s: %r", affiliate_short_link, exc)
        return None
