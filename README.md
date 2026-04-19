# Cara

Helpful Telegram assistant that lives in a channel's discussion group, automatically converting Shopee product links shared by members into affiliate links.

## Features

- **Affiliate link conversion** — When a non-admin, non-ignored member posts a Shopee link (domain contains `shopee.sg` or `shp.ee`) in the channel's linked discussion group, Cara converts it to an affiliate link via the Shopee Affiliate API and replies in-thread. Single links are returned as a bare URL; multiple links are returned as a numbered list in the order they were received.
- **Channel broadcasts ignored** — Auto-forwarded channel posts that appear as thread headers in the discussion group are skipped; Cara only acts on messages whose `from_id` is a real user.
- **Non-Shopee links ignored** — URLs that aren't on a Shopee domain are silently skipped. If a message contains no Shopee links at all, Cara does not reply.
- **Non-product Shopee links** — Shopee video links (URLs containing an `smtt` query parameter) and Shopee links that the API can't convert are replaced inline with `Need product link to convert!` at their position in the numbered reply.
- **Admin controls** — Any user in `ADMIN_LIST` can DM Cara `/off` to pause in-thread replies and `/on` to resume. Every state change is broadcast to all admins. Admins' own messages in the discussion group are ignored.
- **Ignore list** — Users in `IGNORE_LIST` are silently skipped entirely.
- **User account mode** — Cara operates as a Telegram user account via [Telethon](https://docs.telethon.dev/en/stable/), not a bot.

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))
- Shopee Affiliate API credentials

### Installation

```bash
git clone <repo-url> && cd Cara
uv sync

cp .env.example .env
# Edit .env with your credentials and IDs
```

### Environment variables

| Variable | Description |
|---|---|
| `TELEGRAM_API_ID` | Telegram API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | Telegram API hash from my.telegram.org |
| `SESSION_NAME` | Telethon session file name (default: `cara_session`) |
| `CHANNEL_ID` | Target Telegram channel ID (e.g. `-1003714961233`) |
| `DISCUSSION_GROUP_ID` | Linked discussion group ID where Cara listens for member messages |
| `ADMIN_LIST` | Comma-separated user IDs allowed to toggle Cara on/off and receive failure alerts |
| `IGNORE_LIST` | Comma-separated user IDs whose messages are silently ignored |
| `SHOPEE_API_id` | Shopee Affiliate app ID |
| `SHOPEE_API_key` | Shopee Affiliate secret key |

### Running

```bash
uv run python -m cara.main
```

### First-time authentication

On first run, Telethon will prompt for your phone number and a verification code sent via Telegram. After authenticating, a session file is saved locally so subsequent runs connect automatically.

## Scripts

### Poll channel messages

Fetch all messages from the last 48 hours, structured by top-level announcements and their thread replies:

```bash
PYTHONPATH=. uv run python scripts/poll_messages.py
```

## Project structure

```
cara/
├── main.py          # Entry point — client setup and startup
├── config.py        # Environment-based settings (loads .env from project root)
├── handlers.py      # Telegram event handlers (link conversion, /on /off, admin broadcasts)
├── link_service.py  # URL extraction and Shopee affiliate link generation
├── state.py         # Runtime state (active/paused toggle)
└── shopeeAPI/       # Shopee Affiliate API client (no third-party wrapper)
    ├── __init__.py  # Public exports
    ├── auth.py      # SHA256 request signing
    ├── client.py    # ShopeeAffiliate — generate_short_link, conversion_report
    ├── countries.py # Country enum for regional API endpoints
    └── errors.py    # ShopeeAPIError and ShopeeErrorCode

scripts/
└── poll_messages.py  # Polls channel posts + thread replies from last 48h
```

## Telegram channel architecture

Cara interacts with a channel that has a linked discussion group:

- **Channel posts** — Top-level announcements broadcast to the channel. Cara does not act on these.
- **Discussion group** — Each channel post auto-forwards into a linked supergroup where members can reply. Cara listens for `NewMessage` events on this group (`DISCUSSION_GROUP_ID`) and responds to members' messages. The auto-forwarded post itself arrives with `from_id` set to the linked channel (a `PeerChannel`), so Cara filters those out and only processes messages whose `from_id` is a `PeerUser`. Replying via `event.reply(...)` threads the response under the original message.
- **Direct messages** — Admins DM Cara with `/on` and `/off` to control the reply state.

Channel IDs in `-100...` format are used as-is with Telethon.

## Link handling behavior

URLs in a member's message are processed as follows:

1. **Shopee filter** — only URLs whose domain contains `shopee.sg` or `shp.ee` are considered. Everything else is silently dropped. If no Shopee links remain, Cara doesn't reply.
2. **Per-link processing** (preserving original order):
   - **Shopee video links** (`smtt=` query parameter) → `Need product link to convert!`
   - **Other Shopee URLs** → submitted to the Shopee Affiliate API; success yields the short link, any exception yields `Need product link to convert!`.
3. **Reply composition:**
   - Exactly one entry → returned bare (link or placeholder).
   - Multiple entries → numbered list in the original order, mixing affiliate links and placeholders.

Admins are only notified when Cara fails to *send* a reply (genuine Telegram-side errors), not on per-link conversion failures.

## TODO

- [ ] Add TOON format support for structured LLM objects (awaiting `toon-format` PyPI package — currently a namespace reservation only, v0.1.0)
- [ ] Build out LLM functionality with LangChain / LangGraph
- [ ] Add persistence for bot state (survives restarts)
- [ ] Add retry logic for transient link conversion failures
- [ ] Add logging configuration (file output, log levels)
- [ ] Write tests
