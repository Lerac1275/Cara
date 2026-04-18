import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Always load .env from the project root, regardless of CWD.
# cara/config.py is one level deep, so parent = cara/, parent.parent = project root.
_here = Path(__file__).resolve()
_project_root = _here.parent.parent
load_dotenv(_project_root / ".env", override=True)


def _csv_ints(name: str) -> list[int]:
    raw = os.getenv(name, "")
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


@dataclass
class Settings:
    api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    session_name: str = os.getenv("SESSION_NAME", "cara_session")
    channel_id: int = int(os.getenv("CHANNEL_ID", "0"))
    discussion_group_id: int = int(os.getenv("DISCUSSION_GROUP_ID", "0"))
    admin_list: list[int] = field(default_factory=lambda: _csv_ints("ADMIN_LIST"))
    ignore_list: list[int] = field(default_factory=lambda: _csv_ints("IGNORE_LIST"))
    shopee_api_id: str = os.getenv("SHOPEE_API_id", "")
    shopee_api_key: str = os.getenv("SHOPEE_API_key", "")


settings = Settings()
