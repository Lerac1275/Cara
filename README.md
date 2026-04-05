# Cara

Helpful Telegram assistant that lives in your channel, automatically converting member-shared links through an external service.

## Features

- **Link conversion** — When a member posts a link in the channel, Cara runs it through an external service and returns the converted link via private message. The channel owner also receives a copy.
- **Owner controls** — The channel owner can DM Cara `/off` to pause member notifications (Cara still tracks and converts links, forwarding them to the owner) and `/on` to resume.
- **User account mode** — Cara operates as a Telegram user account via [Telethon](https://docs.telethon.dev/en/stable/), not a bot.

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) package manager
- Telegram API credentials ([my.telegram.org](https://my.telegram.org))

### Installation

```bash
# Clone and install
git clone <repo-url> && cd Cara
uv sync

# Configure environment
cp .env.example .env
# Edit .env with your Telegram API credentials
```

### Environment variables

| Variable | Description |
|---|---|
| `TELEGRAM_API_ID` | Telegram API ID from my.telegram.org |
| `TELEGRAM_API_HASH` | Telegram API hash from my.telegram.org |
| `SESSION_NAME` | Telethon session file name (default: `cara_session`) |
| `CHANNEL_ID` | Target Telegram channel ID (e.g. `-1003714961233`) |
| `OWNER_ID` | Channel owner's Telegram user ID |

### Running

```bash
uv run cara
```

### First-time authentication

On first run, Telethon will prompt for your phone number and a verification code sent via Telegram. After authenticating, a session file is saved locally so subsequent runs connect automatically.

## Scripts

### Poll channel messages

Fetch all messages from the last 48 hours, structured by top-level announcements and their thread replies:

```bash
PYTHONPATH=. uv run python scripts/poll_messages.py
```

## Project Structure

```
cara/
├── main.py          # Entry point — client setup and startup
├── config.py        # Environment-based settings (loads .env from project root)
├── handlers.py      # Telegram event handlers (link detection, /on /off)
├── link_service.py  # External link conversion (stub)
└── state.py         # Runtime state (active/paused toggle)

scripts/
└── poll_messages.py  # Polls channel posts + thread replies from last 48h
```

## Telegram Channel Architecture

Cara interacts with a channel that has a linked discussion group:

- **Channel posts** — Top-level announcements broadcast to the channel.
- **Comment threads** — Each post can have a discussion thread. Under the hood, these are messages in a linked supergroup, tied to the channel post via `reply_to`. Telethon fetches them with `iter_messages(channel, reply_to=msg_id)`.
- **Direct messages** — Members can also message the channel directly (separate from thread comments).

Channel IDs in `-100...` format include a prefix that must be stripped to get the bare channel ID for Telethon's `PeerChannel`.

## TODO

- [ ] Integrate real external link conversion service (replace stub in `link_service.py`)
- [ ] Add TOON format support for structured LLM objects (awaiting `toon-format` PyPI package — currently a namespace reservation only, v0.1.0)
- [ ] Build out LLM functionality with LangChain / LangGraph
- [ ] Add persistence for bot state (survives restarts)
- [ ] Add error handling and retry logic for link conversion failures
- [ ] Add logging configuration (file output, log levels)
- [ ] Write tests
