"""
tests/test_repository.py — Тести БД-репозиторію.
Використовують тимчасову SQLite-БД (aiosqlite), тож реальний PostgreSQL не потрібен.
Сама логіка ідентична для обох СУБД.
"""
import pytest
import pytest_asyncio
from cryptography.fernet import Fernet
from sqlalchemy import select

from security.encryption import Encryptor
from database.repository import DatabaseManager
from database.models import PasswordEntry


@pytest_asyncio.fixture
async def db(tmp_path):
    key = Fernet.generate_key().decode()
    url = f"sqlite+aiosqlite:///{tmp_path / 'test.db'}"
    manager = DatabaseManager(url, Encryptor(key), default_shift=3)
    await manager.init_db()
    yield manager
    await manager.close()


async def test_empty_by_default(db):
    assert await db.list_passwords(123) == {}
    assert await db.get_caesar_shift(123) == 3


async def test_set_get_password(db):
    await db.set_password(123, "Gmail", "abc123")
    assert await db.get_password(123, "Gmail") == "abc123"
    assert await db.list_passwords(123) == {"Gmail": "abc123"}


async def test_update_existing_password(db):
    await db.set_password(123, "Gmail", "old")
    await db.set_password(123, "Gmail", "new")
    assert await db.get_password(123, "Gmail") == "new"
    assert len(await db.list_passwords(123)) == 1


async def test_delete_password(db):
    await db.set_password(123, "GitHub", "token")
    assert await db.delete_password(123, "GitHub") is True
    assert await db.delete_password(123, "GitHub") is False
    assert await db.get_password(123, "GitHub") is None


async def test_passwords_are_per_user(db):
    await db.set_password(111, "Service", "secret-111")
    await db.set_password(222, "Service", "secret-222")
    assert await db.get_password(111, "Service") == "secret-111"
    assert await db.get_password(222, "Service") == "secret-222"
    assert "Service" not in (await db.list_passwords(333))


async def test_caesar_shift_per_user(db):
    await db.set_caesar_shift(111, 7)
    assert await db.get_caesar_shift(111) == 7
    assert await db.get_caesar_shift(222) == 3  # дефолт


async def test_password_encrypted_at_rest(db):
    await db.set_password(123, "SecretService", "PlainPasswordValue")
    async with db.session() as s:
        row = (await s.execute(select(PasswordEntry))).scalar_one()
    assert row.password_enc != "PlainPasswordValue"
    assert "PlainPasswordValue" not in row.password_enc
