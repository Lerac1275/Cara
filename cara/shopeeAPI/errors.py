from enum import IntEnum


class ShopeeErrorCode(IntEnum):
    SYSTEM_ERROR = 10_000
    REQUEST_PARSING_ERROR = 10_010
    IDENTITY_AUTHENTICATION_ERROR = 10_020
    TRIGGER_TRAFFIC_LIMITING = 10_030
    ACCESS_DENY = 10_031
    INVALID_AFFILIATE_ID = 10_032
    ACCOUNT_IS_FROZEN = 10_033
    AFFILIATE_ID_BLACK_LIST = 10_034
    UNAUTHORIZED_ERROR = 10_035
    BUSINESS_PROCESSING_ERROR = 11_000
    PARAMS_ERROR = 11_001
    BIND_ACCOUNT_ERROR = 11_002


class ShopeeAPIError(Exception):
    """Raised when the Shopee Affiliate API returns an error response."""

    def __init__(self, message: str, extensions: dict, locations=None) -> None:
        super().__init__(message)
        self.message = message
        self.locations = locations
        self.code = ShopeeErrorCode(extensions["code"])
        self.api_message = extensions["message"]

    def __repr__(self) -> str:
        return f"ShopeeAPIError(code={self.code.name}, message={self.api_message!r})"
