"""
migrate_legacy.py — Одноразова міграція зі старого файлового сховища у БД.

Старе сховище (passwords.json) шифрувалося ключем, що виводився з відомого
(тепер відкликаного) UUID, вписаного в код, — тобто фактично без захисту.
Цей скрипт читає старі дані і записує їх у базу даних під новим FERNET_KEY,
прив'язавши до вказаного Telegram ID.

Запуск (після налаштування .env):
    python migrate_legacy.py <telegram_id> [шлях_до_passwords.json]

Якщо у ALLOWED_USER_IDS лише один ID, його можна не вказувати:
    python migrate_legacy.py

⚠️ Паролі зі старого сховища слід вважати скомпрометованими — після міграції
   рекомендуємо змінити їх у відповідних сервісах.
"""
import asyncio
import base64
import hashlib
import json
import sys

from cryptography.fernet import Fernet

from config import config
from deps import db

LEGACY_UUID = "f7e94a9f-347c-5090-affa-418526e99a29"
LEGACY_FILE = "passwords.json"


def _legacy_key(uuid_str: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(uuid_str.encode()).digest())


def _read_legacy(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        token = json.load(f)
    cipher = Fernet(_legacy_key(LEGACY_UUID))
    decrypted = cipher.decrypt(token.encode()).decode()
    return json.loads(decrypted)


async def _migrate(telegram_id: int, path: str) -> None:
    try:
        old_passwords = _read_legacy(path)
    except FileNotFoundError:
        print(f"Файл {path} не знайдено — нічого мігрувати.")
        return
    except Exception as e:
        print(f"Не вдалося розшифрувати {path}: {e}")
        sys.exit(1)

    if not isinstance(old_passwords, dict) or not old_passwords:
        print("Старе сховище порожнє — нічого мігрувати.")
        return

    await db.init_db()
    try:
        for service, password in old_passwords.items():
            await db.set_password(telegram_id, service, password)
    finally:
        await db.close()

    print(f"✅ Перенесено {len(old_passwords)} записів для користувача {telegram_id}.")
    print("⚠️  Рекомендуємо змінити ці паролі у відповідних сервісах.")


def main() -> None:
    args = sys.argv[1:]
    telegram_id = None
    path = LEGACY_FILE

    if args and args[0].lstrip("-").isdigit():
        telegram_id = int(args[0])
        if len(args) > 1:
            path = args[1]
    else:
        if len(config.allowed_user_ids) == 1:
            telegram_id = config.allowed_user_ids[0]
        if args:
            path = args[0]

    if telegram_id is None:
        print(
            "Вкажіть Telegram ID власника паролів:\n"
            "    python migrate_legacy.py <telegram_id> [passwords.json]"
        )
        sys.exit(1)

    asyncio.run(_migrate(telegram_id, path))


if __name__ == "__main__":
    main()
