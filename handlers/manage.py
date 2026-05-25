"""
handlers/manage.py — Пошук і видалення паролів.
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from deps import vault
from handlers.common import start
from security.access import require_access

logger = logging.getLogger(__name__)


@require_access
async def search_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    password = vault.get_password(service)
    if password is not None:
        await update.message.reply_text(f"Сервіс: {service}\nПароль: {password}")
    else:
        await update.message.reply_text(f"Пароль для {service} не знайдено.")
    return await start(update, context)


@require_access
async def delete_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = update.message.text
    if vault.delete_password(service):
        await update.message.reply_text(f"Пароль для {service} успішно видалено!")
    else:
        await update.message.reply_text(f"Пароль для {service} не знайдено.")
    return await start(update, context)
