"""
keyboards.py — Клавіатури бота.
"""
from telegram import (
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

# Підписи кнопок головного меню (також використовуються як маршрути в menu.py)
BTN_ADD = "Додати пароль"
BTN_FIND = "Знайти пароль"
BTN_DELETE = "Видалити пароль"
BTN_LIST = "Список всіх паролів"
BTN_GENERATE = "Згенерувати пароль"
BTN_CAESAR = "Налаштувати шифр Цезаря"

YES = "Так"
NO = "Ні"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            [BTN_ADD, BTN_FIND],
            [BTN_DELETE, BTN_LIST],
            [BTN_GENERATE, BTN_CAESAR],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def yes_no() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [[YES, NO]], resize_keyboard=True, one_time_keyboard=True
    )


def pagination(page: int, total_pages: int) -> InlineKeyboardMarkup:
    keyboard = []
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton("⬅ Назад", callback_data=f"page_{page - 1}"))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton("Вперед ➡", callback_data=f"page_{page + 1}"))
        if nav:
            keyboard.append(nav)
    keyboard.append([InlineKeyboardButton("Повернутися до меню", callback_data="back_to_menu")])
    return InlineKeyboardMarkup(keyboard)
