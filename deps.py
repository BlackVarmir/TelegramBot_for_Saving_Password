"""
deps.py — Спільні залежності (синглтони), що ін'єктуються у хендлери.
Створюються один раз із конфігу.
"""
from config import config
from security.encryption import Encryptor
from storage.vault import PasswordVault

encryptor = Encryptor(config.fernet_key)
vault = PasswordVault(config.vault_file, encryptor, config.default_caesar_shift)
