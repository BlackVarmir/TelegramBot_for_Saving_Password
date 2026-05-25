"""
handlers/settings.py — Налаштування шифру Цезаря, /whoami, /strengthen.
"""
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from deps import vault
from handlers.common import start
from security.access import require_access, has_access
from security.caesar import caesar_encrypt
from states import State

logger = logging.getLogger(__name__)


@require_access
async def set_caesar_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        new_shift = int(update.message.text)
    except ValueError:
        await update.message.reply_text(
            "Будь ласка, введіть ціле число!", reply_markup=ReplyKeyboardRemove()
        )
        return State.SETTING_SHIFT

    if new_shift < 1 or new_shift > 25:
        await update.message.reply_text(
            "Зсув має бути числом від 1 до 25. Спробуйте ще раз:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.SETTING_SHIFT

    old_shift = vault.get_caesar_shift()
    vault.set_caesar_shift(new_shift)
    await update.message.reply_text(
        f"Зсув для шифру Цезаря змінено з {old_shift} на {new_shift}.\n\n"
        f"ВАЖЛИВО: Нові паролі шифруватимуться зі зсувом {new_shift}, "
        f"але старі паролі залишаються зашифрованими зі старим зсувом {old_shift}.",
        reply_markup=ReplyKeyboardRemove(),
    )
    return await start(update, context)


# ── Команди поза розмовою ────────────────────────────────────────────────────
async def whoami(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показує користувачу його Telegram ID. НЕ розкриває секретів."""
    user = update.effective_user
    status = "✅ маєте доступ" if has_access(user.id) else "⛔ немає доступу"
    await update.message.reply_text(
        f"Ваш Telegram ID: {user.id}\n"
        f"Статус: {status}\n\n"
        "Щоб надати доступ, додайте цей ID у змінну ALLOWED_USER_IDS "
        "у файлі .env і перезапустіть бота."
    )


@require_access
async def strengthen_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Використання: /strengthen пароль\n\n"
            "Команда застосує до пароля просту трансформацію (шифр Цезаря). "
            "Зверніть увагу: це НЕ криптографічний захист."
        )
        return

    original = " ".join(context.args)
    shift = vault.get_caesar_shift()
    transformed = caesar_encrypt(original, shift)
    await update.message.reply_text(
        f"Оригінальний пароль: {original}\n"
        f"Перетворений пароль: {transformed}\n\n"
        f"Зсув Цезаря: {shift}"
    )
