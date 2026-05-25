"""
security/access.py — Контроль доступу до бота.
Доступ дозволено лише числовим Telegram-ID зі списку ALLOWED_USER_IDS.
"""
import functools
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from config import config

logger = logging.getLogger(__name__)

DENY_TEXT = "Вибачте, у вас немає доступу до цього бота."


def has_access(user_id: int) -> bool:
    return user_id in config.allowed_user_ids


async def _deny(update: Update) -> None:
    if update.callback_query:
        await update.callback_query.answer()
        try:
            await update.callback_query.message.edit_text(DENY_TEXT, reply_markup=None)
        except Exception:
            await update.callback_query.message.reply_text(DENY_TEXT)
    elif update.message:
        await update.message.reply_text(DENY_TEXT, reply_markup=ReplyKeyboardRemove())


def require_access(handler):
    """
    Декоратор для хендлерів: пропускає лише дозволених користувачів,
    інакше відповідає відмовою і завершує розмову.
    """
    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user or not has_access(user.id):
            if user:
                logger.warning(f"Відмовлено в доступі користувачу {user.id}")
            await _deny(update)
            return ConversationHandler.END
        return await handler(update, context, *args, **kwargs)

    return wrapper
