"""
config.py — Завантаження конфігурації з .env файлу.
Усі секрети (токен бота, ключ шифрування) зберігаються у змінних середовища,
а НЕ у вихідному коді.
"""
import os
import sys
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

# Завантажуємо .env якщо він існує
if not load_dotenv():
    print("⚠️  Файл .env не знайдено! Переконайтеся, що він існує або змінні середовища задані вручну.")

logger = logging.getLogger(__name__)


def _parse_user_ids(raw: str) -> tuple[int, ...]:
    """Розбирає рядок '111,222 333' у кортеж числових Telegram-ID."""
    if not raw:
        return ()
    ids = []
    for part in raw.replace(",", " ").split():
        try:
            ids.append(int(part))
        except ValueError:
            logger.warning(f"Ігнорую некоректний ID у ALLOWED_USER_IDS: {part!r}")
    return tuple(ids)


@dataclass
class Config:
    # Telegram
    bot_token: str

    # Fernet-ключ для шифрування сховища паролів
    fernet_key: str

    # Хто має доступ до бота (числові Telegram-ID)
    allowed_user_ids: tuple[int, ...]

    # Підключення до БД (PostgreSQL у проді, SQLite локально)
    database_url: str = "sqlite+aiosqlite:///passwords.db"

    # Стандартний зсув шифру Цезаря
    default_caesar_shift: int = 3

    # Скільки паролів показувати на одній сторінці
    passwords_per_page: int = 10


def load_config() -> Config:
    """Завантажує конфіг і перевіряє обов'язкові поля."""
    required = {
        "BOT_TOKEN": os.getenv("BOT_TOKEN"),
        "FERNET_KEY": os.getenv("FERNET_KEY"),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.critical(f"❌ Відсутні обов'язкові змінні середовища: {', '.join(missing)}")
        print(
            f"❌ Відсутні обов'язкові змінні середовища: {', '.join(missing)}\n"
            "   Скопіюйте .env.example у .env і заповніть значення."
        )
        sys.exit(1)

    allowed = _parse_user_ids(os.getenv("ALLOWED_USER_IDS", ""))
    if not allowed:
        logger.warning(
            "⚠️  ALLOWED_USER_IDS не задано — доступ заборонено всім. "
            "Надішліть боту /whoami, щоб дізнатись свій ID, додайте його у .env і перезапустіть."
        )

    try:
        shift = int(os.getenv("DEFAULT_CAESAR_SHIFT", "3"))
    except ValueError:
        shift = 3
    shift = max(1, min(shift, 25))

    return Config(
        bot_token=required["BOT_TOKEN"],
        fernet_key=required["FERNET_KEY"],
        allowed_user_ids=allowed,
        database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///passwords.db"),
        default_caesar_shift=shift,
    )


# Глобальний інстанс конфігу
config = load_config()
