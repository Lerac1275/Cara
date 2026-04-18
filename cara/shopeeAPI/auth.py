import hashlib
import time


class Authentication:
    """Signs requests with SHA256 using the affiliate app credentials."""

    def __init__(self, app_id: str, secret: str) -> None:
        self.app_id = app_id
        self.secret = secret

    def get_headers(self, payload: str) -> dict[str, str]:
        timestamp = int(time.time())
        sign_factor = f"{self.app_id}{timestamp}{payload}{self.secret}"
        signature = hashlib.sha256(sign_factor.encode()).hexdigest()
        return {
            "Content-Type": "application/json",
            "Authorization": (
                f"SHA256 Credential={self.app_id},"
                f" Timestamp={timestamp},"
                f" Signature={signature}"
            ),
        }
