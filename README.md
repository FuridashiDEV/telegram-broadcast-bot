# Telegram Broadcast Bot

A Telegram bot to collect user data and send personalized broadcast messages with optional images, while avoiding duplicate messages and controlling similarity between texts.

## Features

- Stores user data (username, user ID, chat link) in a text file.
- Broadcast messages to users with optional image attachments.
- Limits messages per hour to avoid spam.
- Prevents sending duplicate messages.
- Ensures new broadcast text is not too similar to the previous one.
- Securely loads sensitive credentials from an encrypted `.env` file.

## Installation

1. Clone the repository:

git clone https://github.com/FuridashiDEV/telegram-broadcast-bot.git
cd telegram-broadcast-bot

2. Install dependencies:

pip install telethon cryptography python-dotenv


Setup

1. Place your encrypted `.env.encrypted` and `key.key` files in the project folder.
2. The `.env` file should contain:

API_ID=<your Telegram API ID>
API_HASH=<your Telegram API hash>
OWNER_ID=<your Telegram user ID>


3. The script will decrypt the `.env` automatically when run.

Usage
1. Run the bot:

python bot.py

2. Send a message to the bot in Telegram. It will store your data.
3. As the owner, send `/broadcast` to start sending messages.
4. Follow prompts to provide message text and optional images.


* Messages are limited to 30 per hour.
* The bot avoids sending repeated texts to users.
* Users with OWNER_ID are skipped from storage.

## License
MIT

