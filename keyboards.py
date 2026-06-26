from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Q2 status code → human-readable label
Q2_STATUSES: dict[int, str] = {
    3: "Elma Success",
    5: "Pending Expert Approve",
    6: "Approve For Contract",
    7: "Cancelled",
}


def service_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋  Q1 · Questionary v1",   callback_data="svc:q1")],
        [InlineKeyboardButton("📋  Q2 · Questionary v2",   callback_data="svc:q2")],
        [InlineKeyboardButton("🤝  K2 · Collaboration v2", callback_data="svc:k2")],
    ])


def q2_action_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅  Approve  →  6 Approve For Contract", callback_data="q2:approve")],
        [InlineKeyboardButton("🔢  Choose status",                      callback_data="q2:choose")],
    ])


def q2_status_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{code} – {label}", callback_data=f"q2:status:{code}")]
        for code, label in Q2_STATUSES.items()
    ])
