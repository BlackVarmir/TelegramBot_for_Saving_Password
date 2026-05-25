"""
storage/vault.py — Зашифроване сховище паролів на диску.

Весь файл сховища шифрується одним Fernet-токеном. Структура у відкритому
вигляді (всередині токена):

    {
        "caesar_shift": 3,
        "passwords": {"Gmail": "...", "GitHub": "..."}
    }
"""
import json
import logging
import os
from typing import Dict

from security.encryption import Encryptor

logger = logging.getLogger(__name__)


class PasswordVault:
    """Працює з єдиним зашифрованим файлом сховища."""

    def __init__(self, path: str, encryptor: Encryptor, default_shift: int = 3):
        self._path = path
        self._enc = encryptor
        self._default_shift = default_shift

    # ── Внутрішні операції з файлом ──────────────────────────────────────────
    def _empty(self) -> dict:
        return {"caesar_shift": self._default_shift, "passwords": {}}

    def _read(self) -> dict:
        if not os.path.exists(self._path):
            return self._empty()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                token = json.load(f)
            raw = self._enc.decrypt(token)
            if not raw:
                logger.warning("Сховище порожнє або не вдалося розшифрувати (невірний ключ?).")
                return self._empty()
            data = json.loads(raw)
            # Сумісність зі старим форматом {service: password}
            if not isinstance(data, dict) or "passwords" not in data:
                data = {"caesar_shift": self._default_shift, "passwords": data if isinstance(data, dict) else {}}
            data.setdefault("caesar_shift", self._default_shift)
            data.setdefault("passwords", {})
            return data
        except Exception as e:
            logger.error(f"Помилка читання сховища: {e}")
            return self._empty()

    def _write(self, data: dict) -> None:
        token = self._enc.encrypt(json.dumps(data, ensure_ascii=False))
        tmp = f"{self._path}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(token, f)
        os.replace(tmp, self._path)  # атомарна заміна

    # ── Публічний API ────────────────────────────────────────────────────────
    def get_passwords(self) -> Dict[str, str]:
        return self._read()["passwords"]

    def has_password(self, service: str) -> bool:
        return service in self._read()["passwords"]

    def get_password(self, service: str) -> str | None:
        return self._read()["passwords"].get(service)

    def set_password(self, service: str, value: str) -> None:
        data = self._read()
        data["passwords"][service] = value
        self._write(data)

    def delete_password(self, service: str) -> bool:
        data = self._read()
        if service in data["passwords"]:
            del data["passwords"][service]
            self._write(data)
            return True
        return False

    def get_caesar_shift(self) -> int:
        return self._read()["caesar_shift"]

    def set_caesar_shift(self, shift: int) -> None:
        data = self._read()
        data["caesar_shift"] = shift
        self._write(data)
