"""Shopee Affiliate API client.

Supports:
- ``generate_short_link`` mutation — convert a product URL to an affiliate link.
- ``conversion_report`` query    — retrieve click/conversion/commission data.
"""
import json
from enum import StrEnum

import requests

from .auth import Authentication
from .countries import Country
from .errors import ShopeeAPIError

_API_URL_TEMPLATE = "https://open-api.affiliate.shopee.{country}/graphql"


# ---------------------------------------------------------------------------
# ConversionReport field enums
# ---------------------------------------------------------------------------

class ConversionReportNode(StrEnum):
    purchaseTime = "purchaseTime"
    clickTime = "clickTime"
    conversionId = "conversionId"
    shopeeCommissionCapped = "shopeeCommissionCapped"
    sellerCommission = "sellerCommission"
    totalCommission = "totalCommission"
    buyerType = "buyerType"
    utmContent = "utmContent"
    device = "device"
    referrer = "referrer"
    orders = "orders"
    linkedMcnName = "linkedMcnName"
    mcnContractId = "mcnContractId"
    mcnManagementFeeRate = "mcnManagementFeeRate"
    mcnManagementFee = "mcnManagementFee"
    netCommission = "netCommission"
    campaignType = "campaignType"


class ConversionReportPageInfo(StrEnum):
    limit = "limit"
    hasNextPage = "hasNextPage"
    scrollId = "scrollId"


class ConversionReportOrderStatus(StrEnum):
    ALL = "ALL"
    UNPAID = "UNPAID"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ConversionReportBuyerType(StrEnum):
    ALL = "ALL"
    NEW = "NEW"
    EXISTING = "EXISTING"


class ConversionReportDevice(StrEnum):
    ALL = "ALL"
    APP = "APP"
    WEB = "WEB"


class ConversionReportFraudStatus(StrEnum):
    ALL = "ALL"
    UNVERIFIED = "UNVERIFIED"
    VERIFIED = "VERIFIED"
    FRAUD = "FRAUD"


class ConversionReportCampaignType(StrEnum):
    ALL = "ALL"
    SELLER_OPEN_CAMPAIGN = "Seller Open Campaign"
    SELLER_TARGET_CAMPAIGN = "Seller Target Campaign"
    MCN_CAMPAIGN = "MCN Campaign"
    NON_SELLER_CAMPAIGN = "Non-Seller Campaign"


class ConversionReportShopType(StrEnum):
    ALL = "ALL"
    SHOPEE_MALL_CB = "SHOPEE_MALL_CB"
    SHOPEE_MALL_NON_CB = "SHOPEE_MALL_NON_CB"
    C2C_CB = "C2C_CB"
    C2C_NON_CB = "C2C_NON_CB"
    PREFERRED_CB = "PREFERRED_CB"
    PREFERRED_NON_CB = "PREFERRED_NON_CB"


# ---------------------------------------------------------------------------
# GraphQL helpers
# ---------------------------------------------------------------------------

def _q(value) -> str:
    """Wrap strings in quotes; pass integers/floats through bare."""
    return f'"{value}"' if isinstance(value, str) else str(value)


def _build_args(pairs: list[tuple[str, object]]) -> str:
    """Render a flat list of (key, value) pairs as GraphQL arguments."""
    return ", ".join(f"{k}: {_q(v)}" for k, v in pairs if v is not None)


def _post(url: str, auth: Authentication, query: str) -> dict:
    payload = json.dumps({"query": query})
    headers = auth.get_headers(payload)
    response = requests.post(url, data=payload, headers=headers)
    body = response.json()
    if response.status_code == 200 and "data" in body:
        return body["data"]
    errors = body.get("errors", [{}])
    raise ShopeeAPIError(**errors[0])


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class ShopeeAffiliate:
    """Shopee Affiliate API client.

    Parameters
    ----------
    app_id:
        Affiliate app ID (``SHOPEE_API_id`` in .env).
    secret:
        Affiliate secret key (``SHOPEE_API_key`` in .env).
    country:
        Target Shopee region. Defaults to ``Country.SINGAPORE``.
    """

    def __init__(
        self,
        app_id: str,
        secret: str,
        country: Country = Country.SINGAPORE,
    ) -> None:
        self._auth = Authentication(app_id, secret)
        self._url = _API_URL_TEMPLATE.format(country=country)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def generate_short_link(
        self,
        origin_url: str,
        sub_ids: list[str] | None = None,
    ) -> dict:
        """Generate a Shopee affiliate short link.

        Parameters
        ----------
        origin_url:
            Any Shopee product URL, e.g. ``https://shopee.sg/product/123``.
        sub_ids:
            Optional tracking identifiers (up to 5 strings).

        Returns
        -------
        dict
            ``{"shortLink": "https://s.shopee.sg/..."}``

        Raises
        ------
        ShopeeAPIError
            On API-level errors (auth failure, bad URL, rate limit, …).
        """
        sub_ids_gql = (
            " subIds: [" + ", ".join(f'"{s}"' for s in sub_ids) + "]"
            if sub_ids else ""
        )
        query = (
            f'mutation {{ generateShortLink (input: {{'
            f' originUrl: "{origin_url}"{sub_ids_gql}'
            f' }}) {{ shortLink }} }}'
        )
        return _post(self._url, self._auth, query)["generateShortLink"]

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def conversion_report(
        self,
        *,
        # Time filters (Unix timestamps)
        purchase_time_start: int | None = None,
        purchase_time_end: int | None = None,
        complete_time_start: int | None = None,
        complete_time_end: int | None = None,
        # Entity filters
        shop_name: str | None = None,
        shop_id: int | None = None,
        shop_type: ConversionReportShopType | None = None,
        conversion_id: int | None = None,
        order_id: str | None = None,
        product_name: str | None = None,
        product_id: int | None = None,
        category_lv1_id: int | None = None,
        category_lv2_id: int | None = None,
        category_lv3_id: int | None = None,
        # Enum filters
        order_status: ConversionReportOrderStatus = ConversionReportOrderStatus.ALL,
        buyer_type: ConversionReportBuyerType = ConversionReportBuyerType.ALL,
        device: ConversionReportDevice = ConversionReportDevice.ALL,
        fraud_status: ConversionReportFraudStatus | None = None,
        campaign_type: ConversionReportCampaignType = ConversionReportCampaignType.ALL,
        campaign_partner_name: str | None = None,
        attribution_type: str | None = None,
        # Pagination
        limit: int = 20,
        scroll_id: str | None = None,
        # Response fields
        nodes: list[ConversionReportNode] | None = None,
        page_info: list[ConversionReportPageInfo] | None = None,
    ) -> dict:
        """Query the conversion report.

        Returns click, order, and commission data for affiliate links.
        All parameters are keyword-only.

        Parameters
        ----------
        purchase_time_start / purchase_time_end:
            Unix timestamps bounding the purchase window.
        complete_time_start / complete_time_end:
            Unix timestamps bounding the completion window.
        order_status:
            Filter by order state (default ``ALL``).
        buyer_type:
            Filter by buyer history (default ``ALL``).
        device:
            Filter by device (default ``ALL``).
        fraud_status:
            Filter by fraud verification state.
        campaign_type:
            Filter by campaign type (default ``ALL``).
        limit:
            Page size (default 20).
        scroll_id:
            Cursor for the next page, taken from a previous response's
            ``pageInfo.scrollId``.
        nodes:
            Response fields to include on each record.
            Defaults to all ``ConversionReportNode`` values.
        page_info:
            Pagination fields to include.
            Defaults to all ``ConversionReportPageInfo`` values.

        Returns
        -------
        dict
            ``{"nodes": [...], "pageInfo": {...}}``
        """
        if nodes is None:
            nodes = list(ConversionReportNode)
        if page_info is None:
            page_info = list(ConversionReportPageInfo)

        args = _build_args([
            ("purchaseTimeStart", purchase_time_start),
            ("purchaseTimeEnd", purchase_time_end),
            ("completeTimeStart", complete_time_start),
            ("completeTimeEnd", complete_time_end),
            ("shopName", shop_name),
            ("shopId", shop_id),
            ("shopType", shop_type),
            ("conversionId", conversion_id),
            ("orderId", order_id),
            ("productName", product_name),
            ("productId", product_id),
            ("categoryLv1Id", category_lv1_id),
            ("categoryLv2Id", category_lv2_id),
            ("categoryLv3Id", category_lv3_id),
            ("orderStatus", order_status),
            ("buyerType", buyer_type),
            ("attributionType", attribution_type),
            ("device", device),
            ("limit", limit),
            ("fraudStatus", fraud_status),
            ("scrollId", scroll_id),
            ("campaignPartnerName", campaign_partner_name),
            ("campaignType", campaign_type),
        ])

        nodes_gql = "\n            ".join(nodes)
        page_info_gql = "\n            ".join(page_info)

        query = f"""{{
    conversionReport ({args}) {{
        nodes {{
            {nodes_gql}
        }}
        pageInfo {{
            {page_info_gql}
        }}
    }}
}}"""
        return _post(self._url, self._auth, query)["conversionReport"]
