# StatusBot — CLAUDE.md

## What This Is

Telegram bot that updates record statuses in remote PostgreSQL databases. No web layer. No ORM. Three operations, each hitting a different DB table.

## File Map

| File | Purpose |
|---|---|
| `bot.py` | Entry point. FSM conversation handler, all Telegram logic |
| `config.py` | Reads `.env`, returns typed `Config` dataclass |
| `db.py` | Single `update_status()` async function — one `asyncpg` call |
| `keyboards.py` | Inline keyboard builders + `Q2_STATUSES` dict |
| `.env` | Secrets (git-ignored). Template: `.env.example` |
| `requirements.txt` | `python-telegram-bot`, `asyncpg`, `python-dotenv` |

## Services & DB Operations

| Key | Field changed | Target value | Table config var |
|---|---|---|---|
| `q1` | `status` (text) | `"confirmed"` | `Q1_DSN` / `Q1_TABLE` |
| `q2` | `status` (int) | 3, 5, 6, or 7 | `Q2_DSN` / `Q2_TABLE` |
| `k` (K2) | `status_id` (int) | `8` | `K_DSN` / `K_TABLE` |

## FSM States

```
SELECTING_SERVICE → AWAITING_ID → (Q2 only) Q2_ACTION → Q2_STATUS
                                                       ↘ (approve shortcut → done)
```

- `Q1` / `K2`: ID received → update immediately → back to `SELECTING_SERVICE`
- `Q2`: ID received → show action menu → either approve (status=6) or pick from status menu

## Auth

`ALLOWED_IDS` in `.env` — comma-separated Telegram user IDs. Empty = allow everyone.

## Running

```sh
source .venv/bin/activate && python bot.py
```

Systemd service: see `README.md`.

## Key Constraints

- Table and column names are validated with `^[A-Za-z_][A-Za-z0-9_]*$` before interpolation — never bypass this.
- `db.py` opens and closes a connection per call (no pool) — intentional for low-traffic use.
- All Telegram responses return to `SELECTING_SERVICE` after any terminal action (success, not-found, or error).
