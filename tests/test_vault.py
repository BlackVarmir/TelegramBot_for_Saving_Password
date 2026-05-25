"""
tests/test_vault.py — Unit-тести зашифрованого сховища.
"""
import pytest
from cryptography.fernet import Fernet

from security.encryption import Encryptor
from storage.vault import PasswordVault


@pytest.fixture
def vault(tmp_path):
    key = Fernet.generate_key().decode()
    enc = Encryptor(key)
    path = str(tmp_path / "vault.json")
    return PasswordVault(path, enc, default_shift=3)


def test_empty_by_default(vault):
    assert vault.get_passwords() == {}
    assert vault.get_caesar_shift() == 3


def test_set_get_password(vault):
    vault.set_password("Gmail", "abc123")
    assert vault.has_password("Gmail")
    assert vault.get_password("Gmail") == "abc123"
    assert vault.get_passwords() == {"Gmail": "abc123"}


def test_delete_password(vault):
    vault.set_password("GitHub", "token")
    assert vault.delete_password("GitHub") is True
    assert vault.delete_password("GitHub") is False
    assert not vault.has_password("GitHub")


def test_caesar_shift_persists(vault):
    vault.set_caesar_shift(7)
    assert vault.get_caesar_shift() == 7


def test_persistence_across_instances(tmp_path):
    key = Fernet.generate_key().decode()
    path = str(tmp_path / "vault.json")
    v1 = PasswordVault(path, Encryptor(key), default_shift=3)
    v1.set_password("Service", "secret")
    v1.set_caesar_shift(5)

    v2 = PasswordVault(path, Encryptor(key), default_shift=3)
    assert v2.get_password("Service") == "secret"
    assert v2.get_caesar_shift() == 5


def test_file_is_encrypted_on_disk(tmp_path):
    key = Fernet.generate_key().decode()
    path = tmp_path / "vault.json"
    v = PasswordVault(str(path), Encryptor(key), default_shift=3)
    v.set_password("SecretService", "PlainPasswordValue")

    raw = path.read_text(encoding="utf-8")
    assert "SecretService" not in raw
    assert "PlainPasswordValue" not in raw


def test_wrong_key_returns_empty(tmp_path):
    path = str(tmp_path / "vault.json")
    PasswordVault(path, Encryptor(Fernet.generate_key().decode())).set_password("A", "b")

    other = PasswordVault(path, Encryptor(Fernet.generate_key().decode()))
    assert other.get_passwords() == {}
