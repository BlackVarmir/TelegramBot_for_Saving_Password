"""
security/caesar.py — Шифр Цезаря та генератор паролів.

Увага: шифр Цезаря — НЕ криптографічний захист. Це лише проста оборотна
трансформація. Реальна конфіденційність забезпечується Fernet-шифруванням
сховища (security/encryption.py).
"""
import random
import string

# Символи, які легко сплутати, виключаємо з генератора
_AMBIGUOUS = set("OIl0")
_LETTERS = [c for c in string.ascii_letters if c not in _AMBIGUOUS]
_DIGITS = [d for d in string.digits if d not in _AMBIGUOUS]
_GEN_ALPHABET = _LETTERS + _DIGITS

_GROUPS = 5
_GROUP_LEN = 6


def _shift_char(ch: str, shift: int) -> str:
    """
    Зсуває ASCII-літеру (mod 26) або ASCII-цифру (mod 10); решту лишає як є.

    Навмисно обмежено ASCII: str.isalpha()/isdigit() вважають літерами й кирилицю
    та інші Unicode-символи, через що зсув ставав необоротним. Тут такі символи
    залишаються без змін, тож трансформація завжди оборотна.
    """
    if "a" <= ch <= "z":
        return chr((ord(ch) - ord("a") + shift) % 26 + ord("a"))
    if "A" <= ch <= "Z":
        return chr((ord(ch) - ord("A") + shift) % 26 + ord("A"))
    if "0" <= ch <= "9":
        return str((ord(ch) - ord("0") + shift) % 10)
    return ch


def caesar_encrypt(text: str, shift: int = 3) -> str:
    """Застосовує прямий зсув Цезаря до тексту."""
    return "".join(_shift_char(c, shift) for c in text)


def caesar_decrypt(text: str, shift: int = 3) -> str:
    """Зворотна операція до caesar_encrypt з тим самим зсувом."""
    return "".join(_shift_char(c, -shift) for c in text)


def generate_apple_style_password() -> str:
    """
    Генерує надійний пароль у стилі Apple:
    5 груп по 6 символів, з'єднаних дефісами (наприклад, Ab3kPq-...).
    Виключає символи, які легко сплутати (O, I, l, 0).
    """
    rng = random.SystemRandom()
    groups = [
        "".join(rng.choice(_GEN_ALPHABET) for _ in range(_GROUP_LEN))
        for _ in range(_GROUPS)
    ]
    return "-".join(groups)
