import logging
import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import BotCommand
from dotenv import load_dotenv

# Load .env variables
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
DATA_FILE = os.getenv("DATA_FILE", "data.json")

# File system
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    # Default config if no file exists
    return {"admins": [], "users": {}}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# Data
data = load_data()
ADMINS = set(data["admins"])
users = data["users"]  # dict: user_id -> {username, first_name}

# Logging
logging.basicConfig(level=logging.INFO)

# Create bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Function
def add_user(user: types.User):
    users[str(user.id)] = {
        "username": user.username or "",
        "first_name": user.first_name or "",
    }
    save_data()


# Commands
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    add_user(message.from_user)
    await message.answer("Привет! Ты добавлен в список ✅")


@dp.message(Command("get_my_id"))
async def cmd_get_my_id(message: types.Message):
    await message.answer(f"Твой Telegram ID: {message.from_user.id}")


@dp.message(Command("addadmin"))
async def cmd_addadmin(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("❌ У вас нет прав")

    try:
        new_admin = int(message.text.split()[1])
        ADMINS.add(new_admin)
        data["admins"] = list(ADMINS)
        save_data()
        await message.answer(f"Пользователь {new_admin} теперь админ ✅")
    except:
        await message.answer("Используй: /addadmin user_id")


@dp.message(Command("send_by_id"))
async def cmd_send_by_id(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("❌ У вас нет прав")

    try:
        args = message.text.split(" ", 2)
        user_id = int(args[1])
        text = args[2]
        await bot.send_message(user_id, f"Сообщение от админа:\n{text}")
        await message.answer("✅ Сообщение отправлено")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


@dp.message(Command("send_by_username"))
async def cmd_send_by_username(message: types.Message):
    if message.from_user.id not in ADMINS:
        return await message.answer("❌ У вас нет прав")

    try:
        args = message.text.split(" ", 2)
        username = args[1].lstrip("@")
        text = args[2]

        # Search by username
        for uid, info in users.items():
            if info["username"] and info["username"].lower() == username.lower():
                await bot.send_message(int(uid), f"Сообщение от админа:\n{text}")
                return await message.answer("✅ Сообщение отправлено")

        await message.answer("❌ Пользователь не найден")
    except Exception as e:
        await message.answer(f"Ошибка: {e}")


# Bot command list
async def set_commands():
    commands = [
        BotCommand(command="start", description="Начать работу"),
        BotCommand(command="get_my_id", description="Узнать свой ID"),
        BotCommand(command="send_by_id", description="Отправить сообщение по ID (админ)"),
        BotCommand(command="send_by_username", description="Отправить сообщение по username (админ)"),
        BotCommand(command="addadmin", description="Добавить нового админа (админ)"),
    ]
    await bot.set_my_commands(commands)


# Start bot
async def main():
    await set_commands()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
