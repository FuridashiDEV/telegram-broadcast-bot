import os
import re
import random
import asyncio
import difflib
from telethon import TelegramClient, events
from cryptography.fernet import Fernet

# === Расшифровка и загрузка переменных окружения ===
def decrypt_env_file():
    # Загрузка ключа для расшифровки
    with open("key.key", "rb") as key_file:
        key = key_file.read()

    cipher_suite = Fernet(key)

    # Расшифровка данных
    with open(".env.encrypted", "rb") as encrypted_file:
        decrypted_data = cipher_suite.decrypt(encrypted_file.read())

    # Создание временного файла .env
    with open(".env", "wb") as env_file:
        env_file.write(decrypted_data)

    # Загрузка переменных окружения из временного файла
    from dotenv import load_dotenv
    load_dotenv(".env")

    # Удаление временного файла после загрузки
    os.remove(".env")


# === Основной код ===
# Расшифровка .env и загрузка переменных
decrypt_env_file()

# Чтение значений из .env
api_id = os.getenv('API_ID')
api_hash = os.getenv('API_HASH')
OWNER_ID = int(os.getenv('OWNER_ID'))  # Telegram ID владельца бота

# Путь к текстовым файлам
TEXT_FILE = "users_data.txt"
SENT_USERS_FILE = "sent_users.txt"

# Лимиты сообщений
MAX_MESSAGES_PER_HOUR = 30
MESSAGES_BEFORE_TEXT_UPDATE = 15
SIMILARITY_THRESHOLD = 0.8  # Порог схожести 80%

# Проверка наличия user_id в файле
def is_user_in_file(user_id, filename):
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                if f"User ID: {user_id}" in line:
                    return True
    return False

# Функция для записи данных о пользователе в текстовый файл
def save_user_data(filename, username, user_id):
    if user_id == OWNER_ID:
        print(f"Пропуск записи для OWNER_ID {OWNER_ID}")
        return

    if not is_user_in_file(user_id, filename):
        chat_link = f"https://t.me/{username}" if username else f"https://t.me/user?id={user_id}"
        with open(filename, "a") as file:
            file.write(f"Username: {username or 'N/A'}, User ID: {user_id}, Chat Link: {chat_link}\n")
        print(f"Сохранены данные: {username or 'N/A'} ({user_id})")
    else:
        print(f"Пользователь с ID {user_id} уже записан.")

# Функция для чтения пользователей из файла и получения их ID
def get_user_ids_from_file(filename):
    user_ids = []
    if os.path.exists(filename):
        with open(filename, "r") as file:
            for line in file:
                match = re.search(r"User ID: (\d+)", line)
                if match:
                    user_ids.append(int(match.group(1)))
    return user_ids

# Функция для записи ID пользователя, которому было отправлено сообщение
def mark_user_as_sent(user_id):
    with open(SENT_USERS_FILE, "a") as file:
        file.write(f"User ID: {user_id}\n")

# Функция для проверки схожести текста
def is_text_similar(text1, text2, threshold=SIMILARITY_THRESHOLD):
    similarity = difflib.SequenceMatcher(None, text1, text2).ratio()
    return similarity >= threshold

# Функция для рассылки сообщений
async def broadcast_message(client):
    all_user_ids = get_user_ids_from_file(TEXT_FILE)
    sent_user_ids = get_user_ids_from_file(SENT_USERS_FILE)
    pending_user_ids = [user_id for user_id in all_user_ids if user_id not in sent_user_ids]

    messages_sent = 0
    previous_text = ""
    photo_path = None  # Путь к изображению для рассылки

    for i, user_id in enumerate(pending_user_ids):
        if messages_sent >= MAX_MESSAGES_PER_HOUR:
            print("Достигнут лимит сообщений в час. Ожидание...")
            await asyncio.sleep(3600)
            messages_sent = 0

        # Запрос нового текста каждые MESSAGES_BEFORE_TEXT_UPDATE сообщений
        if i % MESSAGES_BEFORE_TEXT_UPDATE == 0:
            await client.send_message(OWNER_ID, "Введите новый текст для рассылки:")
            response = await client.wait_for(events.NewMessage(from_user=OWNER_ID))
            message_text = response.text

            # Проверка схожести текста
            if is_text_similar(message_text, previous_text):
                await client.send_message(OWNER_ID, "Ошибка: текст слишком похож на предыдущий. Введите другой текст.")
                continue

            previous_text = message_text

            # Запрос изображения для рассылки
            await client.send_message(OWNER_ID, "Прикрепите изображение (или напишите 'нет'):")
            photo_response = await client.wait_for(events.NewMessage(from_user=OWNER_ID))
            if photo_response.text.lower() == 'нет':
                photo_path = None
            else:
                if photo_response.photo:
                    photo_path = await client.download_media(photo_response.photo)
                else:
                    await client.send_message(OWNER_ID, "Ошибка: отправьте изображение или напишите 'нет'.")

        # Отправка сообщения
        try:
            if photo_path:
                await client.send_file(user_id, photo_path, caption=previous_text)
            else:
                await client.send_message(user_id, previous_text)

            print(f"Сообщение отправлено пользователю ID {user_id}")
            mark_user_as_sent(user_id)
            messages_sent += 1

            # Случайная задержка
            await asyncio.sleep(random.uniform(2, 5))

        except Exception as e:
            print(f"Ошибка при отправке пользователю ID {user_id}: {e}")

# Инициализация клиента
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage)
async def handler(event):
    sender = await event.get_sender()
    username = sender.username
    user_id = sender.id

    if event.is_private:
        save_user_data(TEXT_FILE, username, user_id)

        if event.text == "/broadcast" and user_id == OWNER_ID:
            await event.reply("Начинаем рассылку...")
            await broadcast_message(client)
            await event.reply("Рассылка завершена.")

if __name__ == "__main__":
    client.start()
    client.run_until_disconnected()
