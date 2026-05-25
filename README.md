# Telegram Password Manager Bot

Телеграм-бот для збереження паролів із шифруванням сховища. Дозволяє зберігати,
шукати, видаляти та генерувати паролі прямо в Telegram.

> ⚠️ **Це навчальний проєкт, а не заміна професійним менеджерам паролів.**
> Шифр Цезаря — НЕ криптографічний захист. Реальну конфіденційність забезпечує
> Fernet-шифрування паролів перед записом у базу даних.

## Можливості

- 🔐 Паролі зберігаються в БД зашифрованими (Fernet, AES-128-CBC + HMAC)
- 🗄 PostgreSQL у проді або SQLite локально (через `DATABASE_URL`)
- 🎲 Генератор надійних паролів у стилі Apple
- 🔍 Пошук, 📋 перегляд (з пагінацією), ✏️ додавання та видалення паролів
- 🔁 Опційний шифр Цезаря з налаштовуваним зсувом (1–25)
- 🔒 Контроль доступу за числовим Telegram ID; дані прив'язані до власника

## Структура проєкту

```
TelegramBot_for_Saving_Password/
├── main.py                 # точка входу: ConversationHandler і запуск polling
├── config.py               # завантаження конфігу з .env
├── deps.py                 # спільні синглтони (encryptor, db)
├── states.py               # стани розмови
├── keyboards.py            # клавіатури
├── security/
│   ├── encryption.py       # Fernet-шифрування значень
│   ├── caesar.py           # шифр Цезаря + генератор паролів
│   └── access.py           # контроль доступу
├── database/
│   ├── models.py           # SQLAlchemy-моделі (passwords, user_settings)
│   └── repository.py       # async CRUD + DatabaseManager
├── handlers/
│   ├── common.py           # /start, /cancel, головне меню
│   ├── menu.py             # маршрутизація меню + список з пагінацією
│   ├── add.py              # додавання/генерація пароля
│   ├── manage.py           # пошук і видалення
│   └── settings.py         # шифр Цезаря, /whoami, /strengthen
├── tests/                  # pytest
├── migrate_legacy.py       # одноразова міграція зі старого формату
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── requirements.txt
```

## Встановлення

1. Клонувати репозиторій і встановити залежності:
   ```bash
   pip install -r requirements.txt
   ```

2. Створити файл `.env` з прикладу:
   ```bash
   cp .env.example .env
   ```

3. Згенерувати ключ шифрування і вписати його у `FERNET_KEY`:
   ```bash
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. Вписати `BOT_TOKEN` (від [@BotFather](https://t.me/BotFather)).

5. Налаштувати `DATABASE_URL`:
   - PostgreSQL: `postgresql+asyncpg://user:pass@host:5432/dbname`
   - SQLite (локально): `sqlite+aiosqlite:///passwords.db`

   Таблиці створюються автоматично при першому запуску.

6. Дізнатися свій Telegram ID і додати у `ALLOWED_USER_IDS`:
   запустіть бота, надішліть `/whoami`, скопіюйте показаний ID у `.env`,
   перезапустіть бота.

7. Запуск:
   ```bash
   python main.py
   ```

### Docker (бот + PostgreSQL)

```bash
docker compose up -d --build
```
Піднімає сервіс `postgres` і бот; дані БД зберігаються у volume `postgres_data`
між перезапусками. Логін/пароль/назву БД задайте у `.env`
(`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`).

## Команди

- `/start` — головне меню
- `/whoami` — показати ваш Telegram ID (для налаштування доступу)
- `/strengthen <пароль>` — застосувати шифр Цезаря до тексту
- `/cancel` — скасувати поточну операцію

## Тести

```bash
pytest tests/
```

## Міграція зі старої версії

Раніше дані лежали у файлі `passwords.json`, зашифрованому ключем, що виводився
з відкритого UUID у коді, — тобто фактично без захисту. Щоб перенести старі
записи в базу даних під новим `FERNET_KEY` (вкажіть Telegram ID власника):

```bash
python migrate_legacy.py <telegram_id> [passwords.json]
```

⚠️ Паролі зі старого `passwords.json` слід вважати скомпрометованими — після
міграції рекомендуємо змінити їх у відповідних сервісах.

## Безпека

- Токен бота і ключ шифрування зберігаються лише в `.env` (він у `.gitignore`).
- Паролі шифруються (Fernet) перед записом у БД; у БД немає відкритого тексту.
- Без `FERNET_KEY` дані з БД не розшифрувати — зберігайте його надійно й окремо
  від резервних копій БД.
- Використовуйте бота лише в приватних чатах, не в групах.

## Ліцензія

MIT.
