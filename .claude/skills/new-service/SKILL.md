---
name: new-service
description: Scaffold a new DB service into the bot. Touches all 5 required locations so none are accidentally missed.
---

The user wants to add a new service to StatusBot. Before writing any code, ask the user for:

1. **Service key** — short lowercase identifier (e.g. `q3`, `k3`). Used in callback data and config prefix.
2. **Display label** — shown in the service menu button (e.g. `Q3 · Questionary v3`).
3. **Env prefix** — uppercase prefix for env vars (e.g. `Q3` → `Q3_DSN`, `Q3_TABLE`).
4. **Status column** — the column name to update (e.g. `status`, `status_id`).
5. **Target value** — the value to set (string like `"confirmed"` or int like `8`).
6. **Menu emoji** — one emoji for the service button (e.g. `📋` or `🤝`).

Once you have all six answers, implement ALL FIVE touch-points below. Do not skip any.

---

### Touch-point 1 — `.env.example`

Add a commented block at the end:

```
# ── {display label} ────
{ENV_PREFIX}_DSN=connection_string_here
{ENV_PREFIX}_TABLE=table_name_here
```

---

### Touch-point 2 — `config.py`

Add a `ServiceConfig` field to the `Config` dataclass:

```python
{key}: ServiceConfig  # inside Config dataclass
```

Add a `svc("{ENV_PREFIX}")` call inside `load_config()` and assign it to that field.

---

### Touch-point 3 — `keyboards.py`

Add a new `InlineKeyboardButton` row to `service_menu()`:

```python
[InlineKeyboardButton("{emoji}  {display label}", callback_data="svc:{key}")],
```

---

### Touch-point 4 — `bot.py` → `service_selected()`

Add an entry to the `labels` dict:

```python
"svc:{key}": "{display label}",
```

---

### Touch-point 5 — `bot.py` → `handle_id()`

Add a branch in `handle_id()` before the final `Q1 / K2` block:

```python
if service == "{key}":
    svc_cfg, col, val = config.{key}, "{column}", {value}
    return await _execute_update(update, context, svc_cfg, col, val, record_id)
```

If the value type is `str`, quote it. If `int`, do not quote.

---

After implementing all five, verify:
- `python3 -m py_compile bot.py config.py keyboards.py` passes
- The new button appears in the service menu description in CLAUDE.md (run /update-claude-md)
