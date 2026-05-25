"""
migrate_legacy.py — Одноразова міграція зі старого формату сховища.

Старе сховище (passwords.json) шифрувалося ключем, що виводився з відомого
(тепер відкликаного) UUID, вписаного просто в код, — тобто фактично без
захисту. Цей скрипт читає старі дані і перешифровує їх новим FERNET_KEY
у нове сховище.

Запуск (після налаштування .env з FERNET_KEY та VAULT_FILE):
    python migrate_legacy.py [шлях_до_старого_passwords.json]

⚠️ Паролі зі старого сховища слід вважати скомпрометованими — після міграції
   рекомендуємо змінити їх у відповідних сервісах.
"""
import base64
import hashlib
import json
import sys

from cryptography.fernet import Fernet

from config import config
from deps import vault

# Старий (відкликаний) UUID, з якого виводився ключ у попередній версії коду.
LEGACY_UUID = "f7e94a9f-347c-5090-affa-418526e99a29"
LEGACY_FILE = "passwords.json"


def _legacy_key(uuid_str: str) -> bytes:
    return base64.urlsafe_b64encode(hashlib.sha256(uuid_str.encode()).digest())


def main() -> None:
    path = sys.argv[1] if len(sys.argv) > 1 else LEGACY_FILE
    try:
        with open(path, "r", encoding="utf-8") as f:
            token = json.load(f)
    except FileNotFoundError:
        print(f"Файл {path} не знайдено — нічого мігрувати.")
        return

    cipher = Fernet(_legacy_key(LEGACY_UUID))
    try:
        decrypted = cipher.decrypt(token.encode()).decode()
        old_passwords = json.loads(decrypted)
    except Exception as e:
        print(f"Не вдалося розшифрувати {path}: {e}")
        sys.exit(1)

    if not isinstance(old_passwords, dict) or not old_passwords:
        print("Старе сховище порожнє — нічого мігрувати.")
        return

    for service, password in old_passwords.items():
        vault.set_password(service, password)

    print(f"✅ Перенесено {len(old_passwords)} записів у {config.vault_file}.")
    print("⚠️  Рекомендуємо змінити ці паролі у відповідних сервісах.")


if __name__ == "__main__":
    main()
