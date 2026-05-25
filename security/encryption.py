"""
security/encryption.py — Шифрування/дешифрування сховища паролів.
Використовує Fernet (симетричне шифрування AES-128-CBC + HMAC).
Ключ береться з FERNET_KEY (.env), а не виводиться з відомого значення.
"""
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


class Encryptor:
    """
    Клас для шифрування рядкових даних.
    Fernet гарантує автентифікацію повідомлення (MAC).
    """

    def __init__(self, key: str):
        """
        :param key: Base64-encoded 32-байтний ключ.
                    Генерується командою:
                    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
        """
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.critical(f"Невалідний Fernet-ключ: {e}")
            raise

    def encrypt(self, plaintext: str) -> str:
        """Шифрує рядок і повертає Base64-encoded рядок."""
        if not plaintext:
            return ""
        token = self._fernet.encrypt(plaintext.encode("utf-8"))
        return token.decode("utf-8")

    def decrypt(self, ciphertext: str) -> str:
        """Дешифрує Base64-encoded рядок. Повертає '' якщо токен пошкоджено."""
        if not ciphertext:
            return ""
        try:
            plaintext = self._fernet.decrypt(ciphertext.encode("utf-8"))
            return plaintext.decode("utf-8")
        except InvalidToken:
            logger.warning("Невалідний або пошкоджений токен шифрування.")
            return ""

    @staticmethod
    def generate_key() -> str:
        """Генерує новий Fernet-ключ (для першого налаштування)."""
        return Fernet.generate_key().decode()
