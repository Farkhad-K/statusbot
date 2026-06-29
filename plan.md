# StatusBot — Roadmap & Implementation Plan

## Shipped — `feature/main-menu-and-navigation`

### What changed

| File | Change |
|---|---|
| `keyboards.py` | `BTN_APPROVE` constant, `main_menu_keyboard()`, `awaiting_id_menu()`, nav rows on every inline menu |
| `bot.py` | `show()` single-message helper, `open_approve_flow`, nav handlers (`nav_home` / `nav_back` / `nav_cancel`), rewired FSM |

### UX after this branch

```
/start
└─ "Salom!" + [So'rovnoma/Shartnoma tasdiqlash]  ← persistent reply keyboard
        │
        ▼ (tap button)
   Service menu (inline)
   ├─ [Q1] → "send ID" [⬅ Orqaga][✖ Bekor qilish] → update → result
   ├─ [Q2] → "send ID" [⬅ Orqaga][✖ Bekor qilish]
   │            └─ Action menu [Approve→6] [Choose status] [⬅][✖]
   │                      └─ Status menu  3 / 5 / 6 / 7  [⬅ back][✖]
   └─ [K2] → "send ID" [⬅ Orqaga][✖ Bekor qilish] → update → result
```

Key behaviours:
- **One bot message at a time** — previous bot message is deleted before each new one.
- **Back / Cancel everywhere** — no more dead-ends if you tap the wrong service.
- **Button mid-flow** — tapping the reply-keyboard button mid-flow restarts the flow
  cleanly instead of being silently swallowed as a record ID.

---

## Planned — SQL Sandbox

> **Status: designed, not yet implemented.**
> Implement as a separate branch once the main-menu branch is merged.

### Goal

Authorized users can send a raw `SELECT` query and receive the results as a downloadable
file in their chosen format. Useful for quick ad-hoc checks without opening a DB client.

### Auth & config additions

**`.env` additions:**
```
# Comma-separated Telegram user IDs allowed to use SQL Sandbox
# (independent from ALLOWED_IDS — can be a subset or a separate list)
SQL_ALLOWED_IDS=512374891

# DSN for the sandbox database (point at a read-only Postgres role)
SQL_DSN=postgresql://readonly_user:password@host:5432/dbname
```

**`config.py`** gains:
- `sql_allowed_ids: list[int]`
- `sql_dsn: str` (optional — defaults to empty; feature disabled if unset)

### UX flow

```
[🧪 SQL Sandbox]  ← second row added to main_menu_keyboard() for sql_allowed_ids users
        │
        ▼
"Soʻrovingizni yuboring:" [✖ Bekor qilish]
        │  (user sends: SELECT id, name FROM users LIMIT 10)
        ▼
Format inline menu: [CSV] [TXT] [JSON] [Markdown]
        │
        ▼
Bot sends file as document (BytesIO)
For ≤ 20 rows: also sends inline as a code block
```

### New file: `sql_sandbox.py`

```python
# Responsibilities:
#   validate_query(sql: str) -> None  — raises ValueError if unsafe
#   execute_query(dsn: str, sql: str) -> list[dict]
#   format_result(rows, fmt: str) -> bytes  — fmt in ("csv","txt","json","md")
```

**Safety rules (non-negotiable):**
1. Strip comments (`--` and `/* */`), uppercase, check first non-whitespace token is
   `SELECT` or `WITH`.
2. Reject if the stripped SQL contains any of:
   `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`,
   `CREATE`, `COPY`, or a second `;`.
3. Wrap in a transaction and always `ROLLBACK` — even a `SELECT` can have side-effects
   via triggers.
4. `SET LOCAL statement_timeout = '5s'` before executing.
5. Hard cap: 1 000 rows, 50 columns, 2 MB raw output — truncate and warn.

### New FSM states

```python
SQL_AWAITING_QUERY, SQL_CHOOSING_FORMAT = range(4, 6)
# (range starts after existing 0-3)
```

### Files to create / modify

| File | Change |
|---|---|
| `sql_sandbox.py` | New — validate, execute, format |
| `keyboards.py` | `BTN_SQL`, conditional `main_menu_keyboard(user_id)`, `sql_format_menu()` |
| `bot.py` | `open_sql_flow`, `sql_query_received`, `sql_format_chosen`, nav wiring |
| `config.py` | `sql_allowed_ids`, `sql_dsn` |
| `.env.example` | `SQL_ALLOWED_IDS`, `SQL_DSN` |
| `CLAUDE.md` | Update FSM states table |

### Verification checklist (future)

- [ ] Non-`SQL_ALLOWED_IDS` user does NOT see the sandbox button.
- [ ] `DROP TABLE users` is rejected before hitting the DB.
- [ ] A multi-statement `SELECT 1; DROP TABLE users` is rejected.
- [ ] A valid `SELECT` returns a `.csv` file with correct headers.
- [ ] A result > 1 000 rows is capped and the warning is included in the file.
- [ ] Statement timeout fires on a `pg_sleep(10)` query.
- [ ] Cancel works at both the query-input and format-selection steps.
