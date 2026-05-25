"""
tests/test_caesar.py — Unit-тести шифру Цезаря та генератора паролів.
"""
import pytest

from security.caesar import (
    caesar_encrypt, caesar_decrypt, generate_apple_style_password,
)


@pytest.mark.parametrize("shift", [1, 3, 7, 13, 25])
@pytest.mark.parametrize("text", ["password", "Hello123", "AbC-xyz_9", ""])
def test_roundtrip(text, shift):
    assert caesar_decrypt(caesar_encrypt(text, shift), shift) == text


def test_letter_wrap():
    assert caesar_encrypt("z", 1) == "a"
    assert caesar_encrypt("Z", 1) == "A"
    assert caesar_encrypt("a", 25) == "z"


def test_digit_wrap():
    assert caesar_encrypt("9", 1) == "0"
    assert caesar_encrypt("0", 9) == "9"


def test_non_alphanumeric_unchanged():
    assert caesar_encrypt("a-b c!", 3) == "d-e f!"


def test_unicode_unchanged():
    # Кирилиця не входить у [a-zA-Z0-9], тож лишається без змін
    assert caesar_encrypt("пароль", 3) == "пароль"


def test_generator_format():
    pwd = generate_apple_style_password()
    groups = pwd.split("-")
    assert len(groups) == 5
    assert all(len(g) == 6 for g in groups)
    assert len(pwd) == 5 * 6 + 4


def test_generator_excludes_ambiguous():
    for _ in range(50):
        pwd = generate_apple_style_password().replace("-", "")
        assert not (set(pwd) & set("OIl0"))
        assert pwd.isalnum()


def test_generator_randomness():
    assert generate_apple_style_password() != generate_apple_style_password()
