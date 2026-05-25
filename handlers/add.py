"""
handlers/add.py — Додавання пароля (ручне введення або генерація).
Тут виправлено баг: шифр Цезаря застосовується з НАЛАШТОВАНИМ зсувом
(зі сховища), а не завжди зі стандартним 3.
"""
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from deps import vault
from handlers.common import start
from keyboards import yes_no, YES, NO
from security.access import require_access
from security.caesar import caesar_encrypt, generate_apple_style_password
from states import State

logger = logging.getLogger(__name__)


async def _save_and_report(update: Update, context: ContextTypes.DEFAULT_TYPE, password: str):
    """Шифрує (за потреби), зберігає пароль і повідомляє користувача."""
    service = context.user_data["service"]
    use_caesar = context.user_data.get("use_caesar", True)
    shift = vault.get_caesar_shift()
    final_password = caesar_encrypt(password, shift) if use_caesar else password

    try:
        vault.set_password(service, final_password)
    except Exception as e:
        logger.error(f"Помилка при збереженні пароля: {e}")
        await update.message.reply_text(
            "Виникла помилка при збереженні пароля. Спробуйте ще раз.",
            reply_markup=ReplyKeyboardRemove(),
        )
        _cleanup(context)
        return await start(update, context)

    if use_caesar:
        await update.message.reply_text(
            f"Пароль для {service} успішно зашифровано і збережено!\n\n"
            f"Оригінальний пароль: {password}\n"
            f"Зашифрований пароль (використовуйте цей): {final_password}\n\n"
            f"Зсув Цезаря: {shift}",
            reply_markup=ReplyKeyboardRemove(),
        )
    else:
        await update.message.reply_text(
            f"Пароль для {service} успішно збережено без шифрування Цезаря!\n\n"
            f"Пароль: {final_password}",
            reply_markup=ReplyKeyboardRemove(),
        )

    _cleanup(context)
    return await start(update, context)


def _cleanup(context: ContextTypes.DEFAULT_TYPE) -> None:
    for key in ("service", "use_caesar", "generated_password"):
        context.user_data.pop(key, None)


# ── Хендлери ────────────────────────────────────────────────────────────────
@require_access
async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    context.user_data["service"] = service
    await update.message.reply_text(
        f"Застосувати шифр Цезаря до пароля для {service}? "
        "(додаткова проста оборотна трансформація)",
        reply_markup=yes_no(),
    )
    return State.CHOOSING_CAESAR


@require_access
async def choose_caesar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text
    if choice not in (YES, NO):
        await update.message.reply_text("Будь ласка, оберіть 'Так' або 'Ні' з клавіатури.")
        return State.CHOOSING_CAESAR

    context.user_data["use_caesar"] = (choice == YES)

    # Якщо пароль вже згенеровано — зберігаємо одразу
    if context.user_data.get("generated_password"):
        return await _save_and_report(update, context, context.user_data["generated_password"])

    await update.message.reply_text(
        f"Тепер введіть пароль для {context.user_data['service']}:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return State.ADDING_PASSWORD


@require_access
async def add_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_report(update, context, update.message.text)


async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Викликається з головного меню; не реєструється напряму."""
    generated = generate_apple_style_password()
    context.user_data["generated_password"] = generated
    await update.message.reply_text(
        f"Згенерований пароль: {generated}\n\n"
        "Введіть назву сервісу для збереження цього пароля:",
        reply_markup=ReplyKeyboardRemove(),
    )
    return State.ADDING_SERVICE
