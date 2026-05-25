"""
deps.py — Спільні залежності (синглтони), що ін'єктуються у хендлери.
Створюються один раз із конфігу. init_db() викликається у main.py при старті.
"""
from config import config
from security.encryption import Encryptor
from database.repository import DatabaseManager

encryptor = Encryptor(config.fernet_key)
db = DatabaseManager(config.database_url, encryptor, config.default_caesar_shift)
