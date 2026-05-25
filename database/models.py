"""
database/models.py — SQLAlchemy-моделі.
Паролі зберігаються лише в зашифрованому вигляді (стовпець password_enc).
"""
from datetime import datetime

from sqlalchemy import (
    BigInteger, Integer, String, DateTime, UniqueConstraint, Column,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class PasswordEntry(Base):
    """Один збережений пароль, що належить користувачу (telegram_id)."""
    __tablename__ = "passwords"
    __table_args__ = (
        UniqueConstraint("telegram_id", "service", name="uq_user_service"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, index=True)
    service = Column(String(255), nullable=False)
    password_enc = Column(String, nullable=False)  # Fernet-зашифроване значення

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PasswordEntry telegram_id={self.telegram_id} service={self.service!r}>"


class UserSetting(Base):
    """Налаштування користувача (поки що — лише зсув шифру Цезаря)."""
    __tablename__ = "user_settings"

    telegram_id = Column(BigInteger, primary_key=True)
    caesar_shift = Column(Integer, nullable=False, default=3)

    def __repr__(self):
        return f"<UserSetting telegram_id={self.telegram_id} shift={self.caesar_shift}>"
