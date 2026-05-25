"""
tests/test_encryption.py — Unit-тести модуля шифрування.
Запуск: pytest tests/
"""
import pytest
from cryptography.fernet import Fernet

from security.encryption import Encryptor


@pytest.fixture
def encryptor():
    key = Fernet.generate_key().decode()
    return Encryptor(key)


def test_encrypt_decrypt_roundtrip(encryptor):
    plaintext = "S3cr3t-пароль"
    ciphertext = encryptor.encrypt(plaintext)
    assert ciphertext != plaintext
    assert encryptor.decrypt(ciphertext) == plaintext


def test_encrypt_empty_string(encryptor):
    assert encryptor.encrypt("") == ""
    assert encryptor.decrypt("") == ""


def test_different_ciphertexts(encryptor):
    text = "Gmail"
    ct1 = encryptor.encrypt(text)
    ct2 = encryptor.encrypt(text)
    assert ct1 != ct2  # різні IV
    assert encryptor.decrypt(ct1) == encryptor.decrypt(ct2) == text


def test_invalid_key_raises():
    with pytest.raises(Exception):
        Encryptor("не_валідний_ключ")


def test_tampered_ciphertext_returns_empty(encryptor):
    ct = encryptor.encrypt("secret")
    tampered = ct[:-10] + "XXXXXXXXXX"
    assert encryptor.decrypt(tampered) == ""


def test_generate_key():
    key = Encryptor.generate_key()
    enc = Encryptor(key)
    assert enc.decrypt(enc.encrypt("test")) == "test"


def test_unicode_support(encryptor):
    for text in ["Привіт 🌍", "пароль_123", "АБВ-абв"]:
        assert encryptor.decrypt(encryptor.encrypt(text)) == text
