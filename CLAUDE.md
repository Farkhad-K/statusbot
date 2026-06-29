# StatusBot — CLAUDE.md

## What This Is

Telegram bot that updates record statuses in remote PostgreSQL databases via a persistent reply-keyboard menu. No web layer, no ORM. Three services, each hitting a different table with a single `UPDATE` call per interaction.

## File Map

| File | Purpose |
|---|---|
| `bot.py` | Entry point — FSM conversation handler, all Telegram logic, nav handlers |
| `config.py` | Reads `.env`, returns typed `Config` dataclass |
| `db.py` | Single `update_status()` async function — one `asyncpg` call per invocation |
| `keyboards.py` | Reply-keyboard and inline keyboard builders; `BTN_APPROVE` constant; nav rows |

## Services & DB Operations

| Key | Field changed | Target value | Table config var |
|---|---|---|---|
| `q1` | `status` (text) | `"confirmed"` | `Q1_DSN` / `Q1_TABLE` |
| `q2` | `status` (int) | 3, 5, 6, or 7 | `Q2_DSN` / `Q2_TABLE` |
| `k` (K2) | `status_id` (int) | `8` | `K_DSN` / `K_TABLE` |

## FSM States

```text
/start | tap [So'rovnoma/Shartnoma tasdiqlash]  (persistent reply keyboard)
       ↓
SELECTING_SERVICE  ←──────────── nav:home from any state
       ↓ svc:q1 / svc:k2 / svc:q2
AWAITING_ID  [⬅ Orqaga → home][✖ Bekor qilish → END]
  Q1/K2: ↓ numeric ID → UPDATE → result → SELECTING_SERVICE
  Q2:    ↓ numeric ID → Q2_ACTION  [⬅ home][✖]
                ↓ approve → UPDATE (status=6) → result
                ↓ choose  → Q2_STATUS  [⬅ back → Q2_ACTION][✖]
                                ↓ pick status → UPDATE → result
```

## Auth

`ALLOWED_IDS` in `.env` — comma-separated Telegram user IDs. Empty = allow everyone.

## Running

```sh
source .venv/bin/activate && python bot.py
```

## Key Constraints

- Table and column names are validated with `^[A-Za-z_][A-Za-z0-9_]*$` before SQL interpolation — never bypass or skip this check.
- `show()` stores the active message ID in `user_data["bot_msg_id"]` — never clear `user_data` before calling `show()` or the old message is orphaned.
- `BTN_APPROVE` in `keyboards.py` is used as both the keyboard label and the FSM text filter — changing one without the other silently breaks the flow entry point.
- Every state handler must write `context.user_data["fsm_state"]` before transitioning — `nav_back` reads this to decide its destination.
- DB connections open and close per call (no pool) — intentional for low traffic; do not introduce pooling.
- `allow_reentry=True` on `ConversationHandler` is required — removing it prevents the menu button from restarting the flow mid-conversation.
