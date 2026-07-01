import logging
from telegram import Update
from telegram.error import BadRequest
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
from keyboards import (
    BTN_APPROVE,
    Q2_STATUSES,
    awaiting_id_menu,
    main_menu_keyboard,
    q2_action_menu,
    q2_status_menu,
    service_menu,
)

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


async def show(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    reply_markup=None,
    **kwargs,
) -> None:
    """
    Edit the tracked bot message in-place; falls back to send_message when
    there is no tracked message, the edit fails, or content is unchanged.
    Editing keeps the message at its original position — no scroll jumping.
    """
    chat_id = update.effective_chat.id
    old_id = context.user_data.get("bot_msg_id")
    if old_id:
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=old_id,
                text=text,
                reply_markup=reply_markup,
                **kwargs,
            )
            return  # message_id unchanged — no need to update user_data
        except BadRequest as e:
            if "is not modified" in str(e):
                return  # same content — no-op, not an error
        except Exception:
            pass  # too old / already deleted — fall through to send

    msg = await context.bot.send_message(
        chat_id, text, reply_markup=reply_markup, **kwargs
    )
    context.user_data["bot_msg_id"] = msg.message_id


async def show_service_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Send (or replace) the service menu and return SELECTING_SERVICE."""
    if update.callback_query:
        await update.callback_query.answer()
    await show(update, context, "👇 Xizmatni tanlang:", reply_markup=service_menu())
    context.user_data["fsm_state"] = SELECTING_SERVICE
    return SELECTING_SERVICE


def _reset_flow(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear per-flow state but preserve bot_msg_id for in-place editing continuity."""
    bot_msg_id = context.user_data.get("bot_msg_id")
    context.user_data.clear()
    if bot_msg_id:
        context.user_data["bot_msg_id"] = bot_msg_id


async def _send_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str,
    **kwargs,
) -> None:
    """
    Delete the flow-prompt message, then send a fresh result.
    Results are intentionally new messages — not edited in-place — so each
    completed update leaves a distinct, permanent record in the chat history.
    """
    chat_id = update.effective_chat.id
    old_id = context.user_data.pop("bot_msg_id", None)
    if old_id:
        try:
            await context.bot.delete_message(chat_id, old_id)
        except Exception:
            pass
    msg = await context.bot.send_message(chat_id, text, **kwargs)
    context.user_data["bot_msg_id"] = msg.message_id


# ── /start — entry point ───────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_allowed(update.effective_user.id):
        await update.effective_message.reply_text("⛔ Ruxsatingiz yo'q.")
        return ConversationHandler.END

    if update.callback_query:
        await update.callback_query.answer()

    context.user_data.clear()

    # Send welcome with the persistent reply keyboard; the inline service menu
    # is opened separately when the user taps the button.
    await update.effective_message.reply_text(
        "👋 Salom! Quyidagi tugmani bosing:",
        reply_markup=main_menu_keyboard(),
    )
    return SELECTING_SERVICE


# ── Persistent button → open the approval flow ────────────────────────────

async def open_approve_flow(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Triggered when the user taps the reply-keyboard 'BTN_APPROVE' button."""
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ Ruxsatingiz yo'q.")
        return ConversationHandler.END

    context.user_data.clear()  # full clear — each button tap starts a fresh message
    return await show_service_menu(update, context)


# ── Service button tapped ──────────────────────────────────────────────────

async def service_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not is_allowed(query.from_user.id):
        await query.message.reply_text("⛔ Ruxsatingiz yo'q.")
        return ConversationHandler.END

    labels = {
        "svc:q1": "Q1 · Questionary v1",
        "svc:q2": "Q2 · Questionary v2",
        "svc:k2": "K2 · Collaboration v2",
    }
    service = query.data.split(":")[1]   # "q1" | "q2" | "k2"
    context.user_data["service"] = service

    label = labels[query.data]
    await show(
        update, context,
        f"<b>{label}</b>\n\nYozuvning ID-sini yuboring:",
        reply_markup=awaiting_id_menu(),
        parse_mode="HTML",
    )
    context.user_data["fsm_state"] = AWAITING_ID
    return AWAITING_ID


# ── ID received ────────────────────────────────────────────────────────────

async def handle_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_allowed(update.effective_user.id):
        await update.message.reply_text("⛔ Ruxsatingiz yo'q.")
        return ConversationHandler.END

    try:
        record_id = int(update.message.text.strip())
    except ValueError:
        await show(
            update, context,
            "⚠️ Iltimos, to'g'ri raqamli ID yuboring.",
            reply_markup=awaiting_id_menu(),
        )
        return AWAITING_ID

    service = context.user_data.get("service")

    # Q2: save ID, show action buttons
    if service == "q2":
        context.user_data["pending_id"] = record_id
        await show(
            update, context,
            f"Yozuv <b>{record_id}</b> — nima qilmoqchisiz?",
            parse_mode="HTML",
            reply_markup=q2_action_menu(),
        )
        context.user_data["fsm_state"] = Q2_ACTION
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
    await show(
        update, context,
        "Maqsad statusni tanlang:",
        reply_markup=q2_status_menu(),
    )
    context.user_data["fsm_state"] = Q2_STATUS
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
        await _send_result(
            update, context,
            "🛑 Ma'lumotlar bazasi xatosi — loglarga qarang.",
            reply_markup=service_menu(),
        )
        _reset_flow(context)
        context.user_data["fsm_state"] = SELECTING_SERVICE
        return SELECTING_SERVICE

    display = label if label is not None else str(value)
    text = (
        f"✅ Bajarildi — yozuv <b>{record_id}</b> → <b>{display}</b>."
        if found
        else f"❌ Yozuv <b>{record_id}</b> jadvalda topilmadi: <i>{svc_cfg.table}</i>."
    )
    await _send_result(update, context, text, parse_mode="HTML", reply_markup=service_menu())
    _reset_flow(context)
    context.user_data["fsm_state"] = SELECTING_SERVICE
    return SELECTING_SERVICE


# ── Navigation: home / back / cancel ──────────────────────────────────────

async def nav_home(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Any 'Orqaga' that leads to the service menu."""
    return await show_service_menu(update, context)


async def nav_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Context-aware back: from Q2_STATUS → Q2 action menu;
    from anywhere else → service menu.
    """
    await update.callback_query.answer()
    if context.user_data.get("fsm_state") == Q2_STATUS:
        record_id = context.user_data.get("pending_id", "?")
        await show(
            update, context,
            f"Yozuv <b>{record_id}</b> — nima qilmoqchisiz?",
            parse_mode="HTML",
            reply_markup=q2_action_menu(),
        )
        context.user_data["fsm_state"] = Q2_ACTION
        return Q2_ACTION
    return await show_service_menu(update, context)


async def nav_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Abort the flow — remove the inline prompt and re-pin the main-menu button.
    edit_message_text can't carry a reply keyboard, so this must send a fresh
    message (not use show()) or the persistent button never comes back after
    the user has typed something and collapsed the keyboard.
    """
    if update.callback_query:
        await update.callback_query.answer()

    chat_id = update.effective_chat.id
    old_id = context.user_data.get("bot_msg_id")
    if old_id:
        try:
            await context.bot.delete_message(chat_id, old_id)
        except Exception:
            pass  # already gone / too old — ignore

    context.user_data.clear()
    await context.bot.send_message(
        chat_id,
        "✖ Bekor qilindi.",
        reply_markup=main_menu_keyboard(),
    )
    return ConversationHandler.END


# ── Wiring ─────────────────────────────────────────────────────────────────

def main() -> None:
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    app = Application.builder().token(config.token).request(request).build()

    # nav:home fires from AWAITING_ID / Q2_ACTION
    # nav:back fires from Q2_STATUS (returns to action menu)
    # nav:cancel fires from any state
    nav_handlers = [
        CallbackQueryHandler(nav_home,   pattern=r"^nav:home$"),
        CallbackQueryHandler(nav_back,   pattern=r"^nav:back$"),
        CallbackQueryHandler(nav_cancel, pattern=r"^nav:cancel$"),
    ]

    # AWAITING_ID text filter: exclude commands AND the reply-keyboard button
    # text so that tapping the button mid-flow re-triggers the entry point.
    awaiting_id_filter = (
        filters.TEXT
        & ~filters.COMMAND
        & ~filters.Text([BTN_APPROVE])
    )

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            MessageHandler(filters.Text([BTN_APPROVE]), open_approve_flow),
        ],
        states={
            SELECTING_SERVICE: [
                CallbackQueryHandler(service_selected, pattern=r"^svc:"),
                *nav_handlers,
            ],
            AWAITING_ID: [
                MessageHandler(awaiting_id_filter, handle_id),
                *nav_handlers,
            ],
            Q2_ACTION: [
                CallbackQueryHandler(q2_approve, pattern=r"^q2:approve$"),
                CallbackQueryHandler(q2_choose,  pattern=r"^q2:choose$"),
                *nav_handlers,
            ],
            Q2_STATUS: [
                CallbackQueryHandler(q2_status_chosen, pattern=r"^q2:status:"),
                *nav_handlers,
            ],
        },
        fallbacks=[
            CommandHandler("start", start),
            MessageHandler(filters.Text([BTN_APPROVE]), open_approve_flow),
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    logger.info("Bot is starting — polling for updates.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
