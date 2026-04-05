import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Always load .env from the project root, regardless of CWD.
# cara/config.py is one level deep, so parent = cara/, parent.parent = project root.
_here = Path(__file__).resolve()
_project_root = _here.parent.parent
load_dotenv(_project_root / ".env", override=True)


@dataclass
class Settings:
    api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    session_name: str = os.getenv("SESSION_NAME", "cara_session")
    channel_id: str = os.getenv("CHANNEL_ID", "0")
    owner_id: str = os.getenv("OWNER_ID", "")


settings = Settings()
