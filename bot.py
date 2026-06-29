import logging
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram.request import HTTPXRequest
from config import load_config
from db import update_status
from keyboards import Q2_STATUSES, q2_action_menu, q2_status_menu, service_menu

logging.basicConfig(
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── FSM states ─────────────────────────────────────────────────────────────
SELECTING_SERVICE, AWAITING_ID, Q2_ACTION, Q2_STATUS = range(4)

config = load_config()


# ── Helpers ────────────────────────────────────────────────────────────────

def is_allowed(user_id: int) -> bool:
    return not config.allowed_ids or user_id in config.allowed_ids


async def send_menu(update: Update, text: str = "👇 Choose a service:") -> None:
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=service_menu())
    else:
        await update.message.reply_text(text, reply_markup=service_menu())


# ── /start — entry point ───────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_allowed(update.effective_user.id):
        await update.effective_message.reply_text("⛔ You are not authorized to use this bot.")
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    context.user_data.clear()
    await send_menu(update)
    return SELECTING_SERVICE


# ── Service button tapped ──────────────────────────────────────────────────

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    labels = {
        "svc:q1": "Q1 · Questionary v1",
        "svc:q2": "Q2 · Questionary v2",
        "svc:k2": "K2 · Collaboration v2",
    }
    service = query.data.split(":")[1]   # "q1" | "q2" | "k2"
    context.user_data["service"] = service

    label = labels[query.data]
    await query.message.reply_text(
        f"<b>{label}</b>\n\nSend the record ID:", parse_mode="HTML"
    )
    return AWAITING_ID


# ── ID received ────────────────────────────────────────────────────────────

async def handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ You are not authorized.")
        return ConversationHandler.END

    try:
        record_id = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("⚠️ Please send a valid numeric ID.")
        return AWAITING_ID

    service = context.user_data.get("service")

    # Q2: save ID, show action buttons
    if service == "q2":
        context.user_data["pending_id"] = record_id
        await update.message.reply_text(
            f"Record <b>{record_id}</b> — what do you want to do?",
            parse_mode="HTML",
            reply_markup=q2_action_menu(),
        )
        return Q2_ACTION

    # Q1 / K2: update immediately
    if service == "q1":
        svc_cfg, col, val = config.q1, "status", "confirmed"
    else:
        svc_cfg, col, val = config.k, "status_id", 8

    return await _execute_update(update, context, svc_cfg, col, val, record_id)


# ── Q2: Approve button ─────────────────────────────────────────────────────

async def q2_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    return await _apply_q2_status(update, context, 6)


# ── Q2: Choose status button ───────────────────────────────────────────────

async def q2_choose(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await update.callback_query.message.reply_text(
        "Choose a target status:", reply_markup=q2_status_menu()
    )
    return Q2_STATUS


# ── Q2: specific status tapped ─────────────────────────────────────────────

async def q2_status_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    status = int(update.callback_query.data.split(":")[-1])
    return await _apply_q2_status(update, context, status)


# ── Internal: execute Q2 status update ────────────────────────────────────

async def _apply_q2_status(
    update: Update, context: ContextTypes.DEFAULT_TYPE, status: int
) -> int:
    record_id = context.user_data.get("pending_id")
    label = Q2_STATUSES.get(status, str(status))
    return await _execute_update(
        update, context,
        svc_cfg=config.q2,
        column="status",
        value=status,
        record_id=record_id,
        label=f"{status} – {label}",
    )


# ── Internal: run UPDATE, send reply, reset state ──────────────────────────

async def _execute_update(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    svc_cfg,
    column: str,
    value,
    record_id: int,
    label: str | None = None,
) -> int:
    try:
        found = await update_status(svc_cfg.dsn, svc_cfg.table, column, value, record_id)
    except Exception as exc:
        logger.error("DB error: %s", exc, exc_info=True)
        await _reply(
            update,
            "🛑 Database error — check the logs.",
            reply_markup=service_menu(),
        )
        context.user_data.clear()
        return SELECTING_SERVICE

    display = label if label is not None else str(value)
    text = (
        f"✅ Done — record <b>{record_id}</b> updated to <b>{display}</b>."
        if found
        else f"❌ Record <b>{record_id}</b> not found in <i>{svc_cfg.table}</i>."
    )
    await _reply(update, text, parse_mode="HTML", reply_markup=service_menu())
    context.user_data.clear()
    return SELECTING_SERVICE


async def _reply(update: Update, text: str, **kwargs) -> None:
    if update.callback_query:
        await update.callback_query.message.reply_text(text, **kwargs)
    else:
        await update.message.reply_text(text, **kwargs)


# ── Wiring ─────────────────────────────────────────────────────────────────

def main() -> None:
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = Application.builder().token(config.token).request(request).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECTING_SERVICE: [
                CallbackQueryHandler(service_selected, pattern=r"^svc:"),
            ],
            AWAITING_ID: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_id),
            ],
            Q2_ACTION: [
                CallbackQueryHandler(q2_approve, pattern=r"^q2:approve$"),
                CallbackQueryHandler(q2_choose,  pattern=r"^q2:choose$"),
            ],
            Q2_STATUS: [
                CallbackQueryHandler(q2_status_chosen, pattern=r"^q2:status:"),
            ],
        },
        fallbacks=[CommandHandler("start", start)],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Bot is starting — polling for updates.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
