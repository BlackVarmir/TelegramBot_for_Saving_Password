"""
database/repository.py — CRUD-операції з БД.
Шифрування/дешифрування відбувається тут, на межі зі сховищем.
Працює як з PostgreSQL (asyncpg), так і з SQLite (aiosqlite) — через DATABASE_URL.
"""
import logging
from typing import Optional, Dict

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import (
    AsyncSession, create_async_engine, async_sessionmaker,
)

from database.models import Base, PasswordEntry, UserSetting
from security.encryption import Encryptor

logger = logging.getLogger(__name__)


class PasswordRepository:
    """Низькорівневі операції в межах однієї сесії."""

    def __init__(self, session: AsyncSession, encryptor: Encryptor, default_shift: int = 3):
        self._s = session
        self._enc = encryptor
        self._default_shift = default_shift

    async def list_passwords(self, telegram_id: int) -> Dict[str, str]:
        rows = (
            await self._s.execute(
                select(PasswordEntry).where(PasswordEntry.telegram_id == telegram_id)
            )
        ).scalars().all()
        return {r.service: self._enc.decrypt(r.password_enc) for r in rows}

    async def get_password(self, telegram_id: int, service: str) -> Optional[str]:
        row = await self._get_entry(telegram_id, service)
        return self._enc.decrypt(row.password_enc) if row else None

    async def set_password(self, telegram_id: int, service: str, value: str) -> None:
        row = await self._get_entry(telegram_id, service)
        if row:
            row.password_enc = self._enc.encrypt(value)
        else:
            self._s.add(
                PasswordEntry(
                    telegram_id=telegram_id,
                    service=service,
                    password_enc=self._enc.encrypt(value),
                )
            )
        await self._s.commit()

    async def delete_password(self, telegram_id: int, service: str) -> bool:
        row = await self._get_entry(telegram_id, service)
        if not row:
            return False
        await self._s.delete(row)
        await self._s.commit()
        return True

    async def get_caesar_shift(self, telegram_id: int) -> int:
        setting = await self._s.get(UserSetting, telegram_id)
        return setting.caesar_shift if setting else self._default_shift

    async def set_caesar_shift(self, telegram_id: int, shift: int) -> None:
        setting = await self._s.get(UserSetting, telegram_id)
        if setting:
            setting.caesar_shift = shift
        else:
            self._s.add(UserSetting(telegram_id=telegram_id, caesar_shift=shift))
        await self._s.commit()

    async def _get_entry(self, telegram_id: int, service: str) -> Optional[PasswordEntry]:
        return (
            await self._s.execute(
                select(PasswordEntry).where(
                    PasswordEntry.telegram_id == telegram_id,
                    PasswordEntry.service == service,
                )
            )
        ).scalar_one_or_none()


class DatabaseManager:
    """
    Менеджер підключень + зручні високорівневі методи, що самі відкривають сесію.
    Використання у хендлерах:  await db.set_password(uid, service, value)
    """

    def __init__(self, database_url: str, encryptor: Encryptor, default_shift: int = 3):
        self._engine = create_async_engine(database_url, pool_pre_ping=True)
        self._session_factory = async_sessionmaker(
            self._engine, expire_on_commit=False, class_=AsyncSession,
        )
        self._enc = encryptor
        self._default_shift = default_shift

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ База даних ініціалізована.")

    async def close(self) -> None:
        await self._engine.dispose()

    def session(self) -> AsyncSession:
        return self._session_factory()

    def get_repository(self, session: AsyncSession) -> PasswordRepository:
        return PasswordRepository(session, self._enc, self._default_shift)

    # ── Високорівневі обгортки (сесія на операцію) ───────────────────────────
    async def list_passwords(self, telegram_id: int) -> Dict[str, str]:
        async with self.session() as s:
            return await self.get_repository(s).list_passwords(telegram_id)

    async def get_password(self, telegram_id: int, service: str) -> Optional[str]:
        async with self.session() as s:
            return await self.get_repository(s).get_password(telegram_id, service)

    async def set_password(self, telegram_id: int, service: str, value: str) -> None:
        async with self.session() as s:
            await self.get_repository(s).set_password(telegram_id, service, value)

    async def delete_password(self, telegram_id: int, service: str) -> bool:
        async with self.session() as s:
            return await self.get_repository(s).delete_password(telegram_id, service)

    async def get_caesar_shift(self, telegram_id: int) -> int:
        async with self.session() as s:
            return await self.get_repository(s).get_caesar_shift(telegram_id)

    async def set_caesar_shift(self, telegram_id: int, shift: int) -> None:
        async with self.session() as s:
            await self.get_repository(s).set_caesar_shift(telegram_id, shift)
