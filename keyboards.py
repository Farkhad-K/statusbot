from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ── Reply-keyboard button labels ────────────────────────────────────────────
# Visible text that the keyboard button sends as a plain text message.
# Used as both the button label and the message filter in bot.py.
BTN_APPROVE = "So'rovnoma/Shartnoma tasdiqlash"
# Future: BTN_SQL = "🧪 SQL Sandbox"  (add as a second row when ready)


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Persistent reply keyboard pinned to the input area.
    is_persistent=True keeps it visible between messages.
    Add new feature buttons here as extra rows when each feature is built.
    """
    return ReplyKeyboardMarkup(
        [[KeyboardButton(BTN_APPROVE)]],
        resize_keyboard=True,
        is_persistent=True,
    )


# ── Inline navigation row (reused across menus) ─────────────────────────────
# nav:home   → re-show service menu  (SELECTING_SERVICE)
# nav:back   → one step back         (state-specific)
# nav:cancel → abort the whole flow  (ConversationHandler.END)

_NAV_HOME_CANCEL = [
    InlineKeyboardButton("⬅ Orqaga", callback_data="nav:home"),
    InlineKeyboardButton("✖ Bekor qilish", callback_data="nav:cancel"),
]

_NAV_BACK_CANCEL = [
    InlineKeyboardButton("⬅ Orqaga", callback_data="nav:back"),
    InlineKeyboardButton("✖ Bekor qilish", callback_data="nav:cancel"),
]


# ── Q2 status code → human-readable label ───────────────────────────────────
Q2_STATUSES: dict[int, str] = {
    3: "Elma Success",
    5: "Pending Expert Approve",
    6: "Approve For Contract",
    7: "Cancelled",
}


# ── Inline keyboards ─────────────────────────────────────────────────────────

def service_menu() -> InlineKeyboardMarkup:
    """Main service selector — shown after the persistent button is tapped."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋  Q1 · Questionary v1",   callback_data="svc:q1")],
        [InlineKeyboardButton("📋  Q2 · Questionary v2",   callback_data="svc:q2")],
        [InlineKeyboardButton("🤝  K2 · Collaboration v2", callback_data="svc:k2")],
        [InlineKeyboardButton("✖ Bekor qilish",            callback_data="nav:cancel")],
    ])


def awaiting_id_menu() -> InlineKeyboardMarkup:
    """Inline buttons attached to the 'send me an ID' prompt."""
    return InlineKeyboardMarkup([_NAV_HOME_CANCEL])


def q2_action_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅  Tasdiqlash  →  6 – Approve For Contract", callback_data="q2:approve")],
        [InlineKeyboardButton("🔢  Status tanlash",                        callback_data="q2:choose")],
        _NAV_HOME_CANCEL,
    ])


def q2_status_menu() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(f"{code} – {label}", callback_data=f"q2:status:{code}")]
        for code, label in Q2_STATUSES.items()
    ]
    rows.append(_NAV_BACK_CANCEL)
    return InlineKeyboardMarkup(rows)
