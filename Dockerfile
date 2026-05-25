# ══════════════════════════════════════════════════════════════
#  Dockerfile — Мінімальний образ для продакшн
# ══════════════════════════════════════════════════════════════
FROM python:3.12-slim

LABEL description="Telegram Password Manager Bot"

WORKDIR /app

# Залежності першими (кешування шарів)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Решта коду
COPY . .

# Не запускаємо від root
RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Директорія для локальної SQLite БД (якщо не використовується Postgres)
RUN mkdir -p /app/data
ENV DATABASE_URL=sqlite+aiosqlite:///data/passwords.db

CMD ["python", "main.py"]
