"""
main.py — Головна точка входу бота-менеджера паролів.
Збирає ConversationHandler, реєструє команди, запускає polling.

Секрети (токен, ключ шифрування) беруться з .env через config.py.
"""
import logging
import sys

from telegram.ext import (
    ApplicationBuilder, Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
)

from config import config
from states import State
from handlers import common, menu, add, manage, settings

# ── Логування ────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def build_application() -> Application:
    """Створює та конфігурує Application з усіма хендлерами."""
    application = ApplicationBuilder().token(config.bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", common.start)],
        states={
            State.CHOOSING_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, menu.action_choice),
                CallbackQueryHandler(menu.handle_page_navigation),
            ],
            State.ADDING_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add.add_service)],
            State.CHOOSING_CAESAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, add.choose_caesar)],
            State.ADDING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add.add_password)],
            State.SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage.search_password)],
            State.DELETING: [MessageHandler(filters.TEXT & ~filters.COMMAND, manage.delete_password)],
            State.SETTING_SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings.set_caesar_shift)],
        },
        fallbacks=[CommandHandler("cancel", common.cancel)],
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("whoami", settings.whoami))
    application.add_handler(CommandHandler("strengthen", settings.strengthen_password))
    return application


def main() -> None:
    logger.info("🚀 Запуск бота...")
    if not config.allowed_user_ids:
        logger.warning("Список дозволених користувачів порожній — спершу налаштуйте ALLOWED_USER_IDS.")
    application = build_application()
    logger.info("✅ Бот запущено. Очікування повідомлень...")
    application.run_polling()


if __name__ == "__main__":
    main()
