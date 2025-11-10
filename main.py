from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, \
    ContextTypes, ConversationHandler
import logging
import uuid
import json
import os
from cryptography.fernet import Fernet
import base64
import hashlib
import math
import random
import string

# Налаштування логування
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Константи для станів розмови
CHOOSING_ACTION, ADDING_SERVICE, CHOOSING_CAESAR, ADDING_PASSWORD, SEARCHING, DELETING, SETTING_SHIFT, GENERATING_PASSWORD = range(8)

# Зсув для шифру Цезаря (за замовчуванням 3)
CAESAR_SHIFT = 3

# Тут вкажіть ваш UUID
ALLOWED_UUID = "f7e94a9f-347c-5090-affa-418526e99a29"  # Замініть на ваш UUID

# Файл для зберігання зашифрованих паролів
PASSWORDS_FILE = 'passwords.json'

# Кількість паролів на сторінці
PASSWORDS_PER_PAGE = 10

# Генерація ключа шифрування на основі UUID
def generate_key_from_uuid(uuid_str):
    return base64.urlsafe_b64encode(hashlib.sha256(uuid_str.encode()).digest())

# Функція для перевірки доступу
def check_access(user_id):
    user_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, str(user_id)))
    return user_uuid == ALLOWED_UUID or str(user_id) == ALLOWED_UUID

# Збереження паролів у файл
def save_passwords(passwords, user_id):
    try:
        cipher_key = generate_key_from_uuid(ALLOWED_UUID)
        cipher = Fernet(cipher_key)
        encrypted_data = cipher.encrypt(json.dumps(passwords).encode()).decode()
        with open(PASSWORDS_FILE, 'w') as f:
            json.dump(encrypted_data, f)
        return True
    except Exception as e:
        logging.error(f"Помилка при збереженні паролів: {e}")
        return False

# Функція шифру Цезаря
def caesar_encrypt(text, shift=3):
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        elif char.isdigit():
            result += str((int(char) + shift) % 10)
        else:
            result += char
    return result

# Генерація пароля в стилі Apple
def generate_apple_style_password():
    # Дозволені символи (без 0, O, I, l для уникнення плутанини)
    letters = [c for c in string.ascii_letters if c not in 'OIl']
    digits = [d for d in string.digits if d != '0']
    allowed_chars = letters + digits
    # Генеруємо 5 груп по 4 символи
    groups = []
    for _ in range(5):
        group = ''.join(random.choice(allowed_chars) for _ in range(6))
        groups.append(group)
    # Об'єднуємо групи дефісами
    return '-'.join(groups)

# Вибір застосування шифру Цезаря
async def choose_caesar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    choice = update.message.text
    if choice not in ["Так", "Ні"]:
        await update.message.reply_text("Будь ласка, оберіть 'Так' або 'Ні' з клавіатури.")
        return CHOOSING_CAESAR

    context.user_data['use_caesar'] = (choice == "Так")
    if context.user_data.get('generated_password'):
        # Якщо пароль згенерований, переходимо до збереження
        password = context.user_data['generated_password']
        service = context.user_data['service']
        use_caesar = context.user_data['use_caesar']
        final_password = caesar_encrypt(password) if use_caesar else password

        passwords = load_passwords(user_id)
        passwords[service] = final_password

        if save_passwords(passwords, user_id):
            if use_caesar:
                await update.message.reply_text(
                    f"Пароль для {service} успішно зашифровано і збережено!\n\n"
                    f"Оригінальний пароль: {password}\n"
                    f"Зашифрований пароль (використовуйте цей): {final_password}\n\n"
                    f"Зсув Цезаря: {CAESAR_SHIFT}",
                    reply_markup=ReplyKeyboardRemove()
                )
            else:
                await update.message.reply_text(
                    f"Пароль для {service} успішно збережено без шифрування Цезаря!\n\n"
                    f"Пароль: {final_password}",
                    reply_markup=ReplyKeyboardRemove()
                )
        else:
            await update.message.reply_text("Виникла помилка при збереженні пароля. Спробуйте ще раз.",
                                            reply_markup=ReplyKeyboardRemove())

        # Очищення тимчасових даних
        context.user_data.pop('service', None)
        context.user_data.pop('use_caesar', None)
        context.user_data.pop('generated_password', None)
        return await start(update, context)
    else:
        # Якщо пароль не згенерований, просимо ввести пароль
        await update.message.reply_text(f"Тепер введіть пароль для {context.user_data['service']}:",
                                        reply_markup=ReplyKeyboardRemove())
        return ADDING_PASSWORD

# Отримання пароля з урахуванням вибору шифру Цезаря
async def add_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    password = update.message.text
    service = context.user_data['service']
    use_caesar = context.user_data.get('use_caesar', True)
    final_password = caesar_encrypt(password) if use_caesar else password

    passwords = load_passwords(user_id)
    passwords[service] = final_password

    if save_passwords(passwords, user_id):
        if use_caesar:
            await update.message.reply_text(
                f"Пароль для {service} успішно зашифровано і збережено!\n\n"
                f"Оригінальний пароль: {password}\n"
                f"Зашифрований пароль (використовуйте цей): {final_password}\n\n"
                f"Зсув Цезаря: {CAESAR_SHIFT}",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                f"Пароль для {service} успішно збережено без шифрування Цезаря!\n\n"
                f"Пароль: {final_password}",
                reply_markup=ReplyKeyboardRemove()
            )
    else:
        await update.message.reply_text("Виникла помилка при збереженні пароля. Спробуйте ще раз.",
                                        reply_markup=ReplyKeyboardRemove())

    # Очищення тимчасових даних
    context.user_data.pop('service', None)
    context.user_data.pop('use_caesar', None)
    return await start(update, context)

# Обробка генерації пароля
async def generate_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Генеруємо пароль
    generated_password = generate_apple_style_password()
    context.user_data['generated_password'] = generated_password

    await update.message.reply_text(
        f"Згенерований пароль: {generated_password}\n\n"
        "Введіть назву сервісу для збереження цього пароля:",
        reply_markup=ReplyKeyboardRemove()
    )
    return ADDING_SERVICE

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if check_access(user_id):
        keyboard = [
            ["Додати пароль", "Знайти пароль"],
            ["Видалити пароль", "Список всіх паролів"],
            ["Згенерувати пароль", "Налаштувати шифр Цезаря"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
        # Для callback-запитів надсилаємо нове повідомлення
        if update.callback_query:
            await update.callback_query.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=reply_markup
            )
        return CHOOSING_ACTION
    else:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "Вибачте, у вас немає доступу до цього бота.",
                reply_markup=None
            )
        else:
            await update.message.reply_text(
                "Вибачте, у вас немає доступу до цього бота.",
                reply_markup=ReplyKeyboardRemove()
            )
        return ConversationHandler.END

# Виведення сторінки зі списком паролів
async def show_passwords_page(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int):
    user_id = update.effective_user.id
    if not check_access(user_id):
        if update.callback_query:
            await update.callback_query.message.edit_text("Вибачте, у вас немає доступу до цього бота.")
        else:
            await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                            reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    passwords = load_passwords(user_id)
    if not passwords:
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "У вас ще немає збережених паролів.",
                reply_markup=None
            )
            await update.callback_query.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=ReplyKeyboardMarkup([
                    ["Додати пароль", "Знайти пароль"],
                    ["Видалити пароль", "Список всіх паролів"],
                    ["Згенерувати пароль", "Налаштувати шифр Цезаря"]
                ], resize_keyboard=True, one_time_keyboard=False)
            )
        else:
            await update.message.reply_text(
                "У вас ще немає збережених паролів.",
                reply_markup=ReplyKeyboardRemove()
            )
            await update.message.reply_text(
                "Вітаю у вашому особистому менеджері паролів! Оберіть дію:",
                reply_markup=ReplyKeyboardMarkup([
                    ["Додати пароль", "Знайти пароль"],
                    ["Видалити пароль", "Список всіх паролів"],
                    ["Згенерувати пароль", "Налаштувати шифр Цезаря"]
                ], resize_keyboard=True, one_time_keyboard=False)
            )
        return CHOOSING_ACTION

    try:
        # Сортуємо паролі за назвою сервісу
        sorted_passwords = sorted(passwords.items(), key=lambda x: x[0].lower())
        total_passwords = len(sorted_passwords)
        total_pages = math.ceil(total_passwords / PASSWORDS_PER_PAGE)

        # Перевірка коректності сторінки
        page = max(0, min(page, total_pages - 1))

        # Обчислення діапазону паролів для поточної сторінки
        start_idx = page * PASSWORDS_PER_PAGE
        end_idx = min(start_idx + PASSWORDS_PER_PAGE, total_passwords)
        page_passwords = sorted_passwords[start_idx:end_idx]

        # Формування тексту повідомлення
        passwords_text = "\n".join([f"• {service}: {password}" for service, password in page_passwords])
        message = f"Список паролів (Сторінка {page + 1} з {total_pages}):\n\n{passwords_text}"

        # Створення клавіатури зі стрілками
        keyboard = []
        if total_pages > 1:
            nav_buttons = []
            if page > 0:
                nav_buttons.append(InlineKeyboardButton("⬅ Назад", callback_data=f"page_{page - 1}"))
            if page < total_pages - 1:
                nav_buttons.append(InlineKeyboardButton("Вперед ➡", callback_data=f"page_{page + 1}"))
            keyboard.append(nav_buttons)
        keyboard.append([InlineKeyboardButton("Повернутися до меню", callback_data="back_to_menu")])
        reply_markup = InlineKeyboardMarkup(keyboard)

        # Виведення повідомлення
        if update.callback_query:
            await update.callback_query.message.edit_text(message, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message, reply_markup=reply_markup)

        # Збереження поточної сторінки
        context.user_data['passwords_page'] = page
        return CHOOSING_ACTION

    except Exception as e:
        logging.error(f"Помилка при виведенні списку паролів: {e}")
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "Виникла помилка при виведенні списку паролів. Спробуйте ще раз."
            )
        else:
            await update.message.reply_text(
                "Виникла помилка при виведенні списку паролів. Спробуйте ще раз.",
                reply_markup=ReplyKeyboardRemove()
            )
        return await start(update, context)

# Обробка навігації сторінок
async def handle_page_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not check_access(user_id):
        await query.message.edit_text("Вибачте, у вас немає доступу до цього бота.")
        return ConversationHandler.END

    data = query.data
    if data == "back_to_menu":
        # Видаляємо inline-клавіатуру перед поверненням до меню
        await query.message.edit_text(query.message.text, reply_markup=None)
        return await start(update, context)

    if data.startswith("page_"):
        try:
            page = int(data.split("_")[1])
            return await show_passwords_page(update, context, page)
        except ValueError:
            await query.message.edit_text("Помилка навігації. Спробуйте ще раз.")
            return CHOOSING_ACTION

# Обробка вибору дії
async def action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    choice = update.message.text
    if choice == "Додати пароль":
        await update.message.reply_text("Введіть назву сервісу або сайту для якого потрібно зберегти пароль:",
                                        reply_markup=ReplyKeyboardRemove())
        return ADDING_SERVICE
    elif choice == "Знайти пароль":
        await update.message.reply_text("Введіть назву сервісу, пароль якого ви шукаєте:",
                                        reply_markup=ReplyKeyboardRemove())
        return SEARCHING
    elif choice == "Видалити пароль":
        await update.message.reply_text("Введіть назву сервісу, пароль якого потрібно видалити:",
                                        reply_markup=ReplyKeyboardRemove())
        return DELETING
    elif choice == "Налаштувати шифр Цезаря":
        await update.message.reply_text(
            f"Поточне значення зсуву для шифру Цезаря: {CAESAR_SHIFT}\n"
            "Введіть нове значення зсуву (ціле число):",
            reply_markup=ReplyKeyboardRemove()
        )
        return SETTING_SHIFT
    elif choice == "Список всіх паролів":
        return await show_passwords_page(update, context, context.user_data.get('passwords_page', 0))
    elif choice == "Згенерувати пароль":
        return await generate_password(update, context)
    else:
        await update.message.reply_text("Будь ласка, оберіть дію з клавіатури.")
        return CHOOSING_ACTION

# Отримання назви сервісу для додавання
async def add_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    service = update.message.text
    context.user_data['service'] = service
    keyboard = [["Так", "Ні"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text(
        f"Застосувати шифр Цезаря до пароля для {service}? (Це посилить пароль)",
        reply_markup=reply_markup
    )
    return CHOOSING_CAESAR

# Завантаження паролів з файлу
def load_passwords(user_id):
    if not os.path.exists(PASSWORDS_FILE):
        return {}
    try:
        with open(PASSWORDS_FILE, 'r') as f:
            encrypted_data = json.load(f)
        cipher_key = generate_key_from_uuid(ALLOWED_UUID)
        cipher = Fernet(cipher_key)
        decrypted_data = cipher.decrypt(encrypted_data.encode()).decode()
        return json.loads(decrypted_data)
    except Exception as e:
        logging.error(f"Помилка при завантаженні паролів: {e}")
        return {}

# Пошук пароля
async def search_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    service = update.message.text
    passwords = load_passwords(user_id)
    if service in passwords:
        await update.message.reply_text(f"Сервіс: {service}\nПароль: {passwords[service]}")
    else:
        await update.message.reply_text(f"Пароль для {service} не знайдено.")
    return await start(update, context)

# Видалення пароля
async def delete_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    service = update.message.text
    passwords = load_passwords(user_id)
    if service in passwords:
        del passwords[service]
        if save_passwords(passwords, user_id):
            await update.message.reply_text(f"Пароль для {service} успішно видалено!")
        else:
            await update.message.reply_text("Виникла помилка при видаленні пароля. Спробуйте ще раз.")
    else:
        await update.message.reply_text(f"Пароль для {service} не знайдено.")
    return await start(update, context)

# Отримання UUID
async def my_uuid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_uuid = str(uuid.uuid5(uuid.NAMESPACE_OID, str(user_id)))
    await update.message.reply_text(
        f"Ваш Telegram ID: {user_id}\n"
        f"Ваш згенерований UUID: {user_uuid}\n\n"
        f"Для доступу до бота використовується UUID: {ALLOWED_UUID}\n"
        f"Поточний зсув для шифру Цезаря: {CAESAR_SHIFT}"
    )

# Встановлення зсуву для шифру Цезаря
async def set_caesar_shift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CAESAR_SHIFT
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    try:
        new_shift = int(update.message.text)
        if new_shift < 1 or new_shift > 25:
            await update.message.reply_text("Зсув має бути числом від 1 до 25. Спробуйте ще раз:",
                                            reply_markup=ReplyKeyboardRemove())
            return SETTING_SHIFT
        old_shift = CAESAR_SHIFT
        CAESAR_SHIFT = new_shift
        await update.message.reply_text(
            f"Зсув для шифру Цезаря змінено з {old_shift} на {new_shift}.\n\n"
            f"ВАЖЛИВО: Нові паролі будуть шифруватися з новим зсувом {new_shift}, "
            f"але старі паролі залишаються зашифрованими зі старим зсувом {old_shift}.",
            reply_markup=ReplyKeyboardRemove()
        )
    except ValueError:
        await update.message.reply_text("Будь ласка, введіть ціле число!", reply_markup=ReplyKeyboardRemove())
        return SETTING_SHIFT
    return await start(update, context)

# Команда для генерації покращеного пароля
async def strengthen_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return

    if not context.args:
        await update.message.reply_text(
            "Використання: /strengthen пароль\n\n"
            "Ця команда зашифрує ваш пароль методом Цезаря для підвищення безпеки. "
            "Використовуйте отриманий зашифрований пароль як свій новий пароль."
        )
        return

    original_password = ' '.join(context.args)
    strengthened_password = caesar_encrypt(original_password)
    await update.message.reply_text(
        f"Оригінальний пароль: {original_password}\n"
        f"Покращений пароль (використовуйте цей): {strengthened_password}\n\n"
        f"Зсув Цезаря: {CAESAR_SHIFT}"
    )

# Команда скасування
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("Вибачте, у вас немає доступу до цього бота.",
                                        reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Очищення тимчасових даних
    context.user_data.pop('service', None)
    context.user_data.pop('use_caesar', None)
    context.user_data.pop('passwords_page', None)
    context.user_data.pop('generated_password', None)

    await update.message.reply_text("Операцію скасовано.", reply_markup=ReplyKeyboardRemove())
    return await start(update, context)

def main():
    global CAESAR_SHIFT
    if not os.path.exists(PASSWORDS_FILE):
        empty_passwords = {}
        save_passwords(empty_passwords, "init")

    bot_token = "7924702097:AAES2tfYHW2GnQvuRKBSIOMiVuUyIBSuzzQ"  # Замініть на ваш токен
    application = ApplicationBuilder().token(bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING_ACTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, action_choice),
                CallbackQueryHandler(handle_page_navigation)
            ],
            ADDING_SERVICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service)],
            CHOOSING_CAESAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_caesar)],
            ADDING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_password)],
            SEARCHING: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_password)],
            DELETING: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_password)],
            SETTING_SHIFT: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_caesar_shift)],
            GENERATING_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_service)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("my_uuid", my_uuid))
    application.add_handler(CommandHandler("strengthen", strengthen_password))
    application.run_polling()

if __name__ == "__main__":
    main()