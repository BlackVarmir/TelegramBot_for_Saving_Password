# Telegram Password Manager Bot

A secure Telegram bot for storing and managing passwords with encryption capabilities. This bot provides a convenient way to save, retrieve, and organize your passwords directly through Telegram.

## Features

- 🔐 **Secure Password Storage** - Passwords are encrypted using Fernet encryption (AES 128-bit CBC with HMAC authentication)
- 🔑 **Caesar Cipher Enhancement** - Optional additional encryption layer using Caesar cipher
- 🎲 **Password Generator** - Generate strong Apple-style passwords (30 characters with hyphens)
- 🔍 **Password Search** - Quickly find saved passwords by service name
- 📋 **Password List** - View all saved passwords with pagination (10 passwords per page)
- ✏️ **Password Management** - Add, search, and delete passwords
- ⚙️ **Customizable Caesar Shift** - Adjust the Caesar cipher shift value (1-25)
- 🔒 **UUID-based Access Control** - Only authorized users can access the bot
- 🇺🇦 **Ukrainian Language Interface** - User interface in Ukrainian

## Security Features

1. **Fernet Encryption**: All passwords are encrypted using Fernet (symmetric encryption) before being stored in `passwords.json`
2. **UUID-based Authentication**: Access is restricted to authorized users based on their UUID
3. **Caesar Cipher**: Optional additional encryption layer for enhanced password security
4. **Key Generation**: Encryption keys are generated from UUID using SHA-256 hashing
5. **Secure Password Generation**: Generated passwords exclude easily confused characters (O, 0, I, l)

## Requirements

- Python 3.8+
- python-telegram-bot
- cryptography
- uuid (built-in)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/BlackVarmir/TelegramBot_for_Saving_Password.git
cd TelegramBot_for_Saving_Password
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the bot:
   - Open `main.py`
   - Replace `ALLOWED_UUID` with your UUID (you can get it by running the bot and using `/my_uuid` command)
   - Replace `bot_token` with your Telegram bot token from [@BotFather](https://t.me/BotFather)

4. Run the bot:
```bash
python main.py
```

## Configuration

### Getting Your UUID

1. Temporarily set `ALLOWED_UUID` in `main.py` to your Telegram user ID (you can find it by messaging [@userinfobot](https://t.me/userinfobot))
2. Start the bot
3. Send `/my_uuid` command to the bot
4. Copy your generated UUID from the bot's response
5. Update the `ALLOWED_UUID` constant in `main.py` with your UUID
6. Restart the bot

### Getting Bot Token

1. Open [@BotFather](https://t.me/BotFather) in Telegram
2. Send `/newbot` command
3. Follow the instructions to create a new bot
4. Copy the bot token
5. Replace `bot_token` in `main.py` with your token

## Usage

### Available Commands

- `/start` - Start the bot and show the main menu
- `/my_uuid` - Display your Telegram ID and UUID
- `/strengthen [password]` - Encrypt a password using Caesar cipher
- `/cancel` - Cancel the current operation

### Main Menu Options

1. **Додати пароль (Add Password)** - Save a new password for a service
2. **Знайти пароль (Find Password)** - Search for a saved password
3. **Видалити пароль (Delete Password)** - Remove a saved password
4. **Список всіх паролів (List All Passwords)** - View all saved passwords with pagination
5. **Згенерувати пароль (Generate Password)** - Create a strong random password
6. **Налаштувати шифр Цезаря (Configure Caesar Cipher)** - Change the Caesar shift value

### Adding a Password

1. Select "Додати пароль" from the main menu
2. Enter the service name (e.g., "Gmail", "Facebook")
3. Choose whether to apply Caesar cipher encryption
4. Enter or use the generated password
5. The password will be encrypted and saved

### Generating a Password

1. Select "Згенерувати пароль" from the main menu
2. The bot generates a strong 30-character password (format: XXXXXX-XXXXXX-XXXXXX-XXXXXX-XXXXXX)
3. Enter the service name to save this password
4. Choose whether to apply additional Caesar cipher encryption

### Caesar Cipher

The Caesar cipher adds an additional layer of security by shifting characters:
- Letters are shifted in the alphabet
- Digits are shifted in the numeric range (0-9)
- Default shift value is 3, but can be customized (1-25)

**Important**: If you change the Caesar shift, new passwords will use the new shift, but old passwords remain encrypted with the old shift value.

## File Structure

```
TelegramBot_for_Saving_Password/
├── main.py              # Main bot application
├── passwords.json       # Encrypted passwords storage (auto-generated)
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Data Storage

Passwords are stored in `passwords.json` file:
- The entire file is encrypted using Fernet encryption
- Each password entry consists of a service name (key) and encrypted password (value)
- If Caesar cipher is applied, passwords are double-encrypted

## Security Considerations

⚠️ **Important Security Notes:**

1. **Bot Token**: Keep your bot token secret. Never commit it to version control.
2. **UUID**: Keep your UUID private to prevent unauthorized access.
3. **Passwords File**: The `passwords.json` file should be kept secure and backed up regularly.
4. **Telegram Security**: Messages are encrypted in transit but stored on Telegram's servers. Use the bot only in private chats, not in groups.
5. **Local Security**: Ensure your server/computer running the bot is secure.
6. **Backup**: Regularly backup your `passwords.json` file.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Author

BlackVarmir

## Disclaimer

This bot is for personal use. While it implements encryption, it's not a replacement for professional password managers. Use at your own risk and ensure you maintain secure backups of your passwords.
