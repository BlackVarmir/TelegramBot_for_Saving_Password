"""
handlers/menu.py — Маршрутизація головного меню + список паролів з пагінацією.
"""
import logging
import math

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ContextTypes

from config import config
from deps import vault
from handlers import add
from handlers.common import start
from keyboards import (
    main_menu, pagination,
    BTN_ADD, BTN_FIND, BTN_DELETE, BTN_LIST, BTN_GENERATE, BTN_CAESAR,
)
from security.access import require_access
from states import State

logger = logging.getLogger(__name__)


@require_access
async def action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == BTN_ADD:
        await update.message.reply_text(
            "Введіть назву сервісу або сайту для якого потрібно зберегти пароль:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.ADDING_SERVICE

    if choice == BTN_FIND:
        await update.message.reply_text(
            "Введіть назву сервісу, пароль якого ви шукаєте:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.SEARCHING

    if choice == BTN_DELETE:
        await update.message.reply_text(
            "Введіть назву сервісу, пароль якого потрібно видалити:",
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.DELETING

    if choice == BTN_CAESAR:
        await update.message.reply_text(
            f"Поточне значення зсуву для шифру Цезаря: {vault.get_caesar_shift()}\n"
            "Введіть нове значення зсуву (ціле число 1-25):",
            reply_markup=ReplyKeyboardRemove(),
        )
        return State.SETTING_SHIFT

    if choice == BTN_LIST:
        return await show_passwords_page(update, context, context.user_data.get("passwords_page", 0))

    if choice == BTN_GENERATE:
        return await add.generate_password(update, context)

    await update.message.reply_text("Будь ласка, оберіть дію з клавіатури.")
    return State.CHOOSING_ACTION


async def show_passwords_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    passwords = vault.get_passwords()

    if not passwords:
        text = "У вас ще немає збережених паролів."
        if update.callback_query:
            await update.callback_query.message.edit_text(text, reply_markup=None)
            await update.callback_query.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=main_menu(),
            )
        else:
            await update.message.reply_text(text, reply_markup=ReplyKeyboardRemove())
            await update.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=main_menu(),
            )
        return State.CHOOSING_ACTION

    per_page = config.passwords_per_page
    sorted_passwords = sorted(passwords.items(), key=lambda x: x[0].lower())
    total = len(sorted_passwords)
    total_pages = math.ceil(total / per_page)

    page = max(0, min(page, total_pages - 1))
    start_idx = page * per_page
    page_items = sorted_passwords[start_idx:start_idx + per_page]

    body = "\n".join(f"• {service}: {pwd}" for service, pwd in page_items)
    message = f"Список паролів (Сторінка {page + 1} з {total_pages}):\n\n{body}"

    if update.callback_query:
        await update.callback_query.message.edit_text(message, reply_markup=pagination(page, total_pages))
    else:
        await update.message.reply_text(message, reply_markup=pagination(page, total_pages))

    context.user_data["passwords_page"] = page
    return State.CHOOSING_ACTION


@require_access
async def handle_page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back_to_menu":
        await query.message.edit_text(query.message.text, reply_markup=None)
        return await start(update, context)

    if data.startswith("page_"):
        try:
            page = int(data.split("_")[1])
        except ValueError:
            await query.message.edit_text("Помилка навігації. Спробуйте ще раз.")
            return State.CHOOSING_ACTION
        return await show_passwords_page(update, context, page)

    return State.CHOOSING_ACTION
