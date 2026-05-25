"""
handlers/common.py — Спільні хендлери: /start, головне меню, /cancel.
Не імпортує інші модулі хендлерів (щоб уникнути циклічних імпортів).
"""
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from keyboards import main_menu
from security.access import require_access
from states import State

logger = logging.getLogger(__name__)

WELCOME = "Вітаю у вашому особистому менеджері паролів! Оберіть дію:"


async def _send_menu(update: Update, text: str = WELCOME) -> None:
    """Показує головне меню (працює і для message, і для callback)."""
    if update.callback_query:
        await update.callback_query.message.reply_text(text, reply_markup=main_menu())
    else:
        await update.message.reply_text(text, reply_markup=main_menu())


@require_access
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_menu(update)
    return State.CHOOSING_ACTION


@require_access
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for key in ("service", "use_caesar", "generated_password", "passwords_page"):
        context.user_data.pop(key, None)
    await update.message.reply_text("Операцію скасовано.", reply_markup=ReplyKeyboardRemove())
    return await start(update, context)
