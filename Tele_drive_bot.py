import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from motor.motor_asyncio import AsyncIOMotorClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from aiogram.client.bot import Bot, DefaultBotProperties

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "tele_drive_bot"
COLLECTION_NAME = "users"
GOOGLE_CREDENTIALS_FILE = "credentials.json"  # Path to Google service account JSON file

# Logging setup
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Connect to MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_collection = db[COLLECTION_NAME]

# Authenticate Google Drive API
creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE)
drive_service = build('drive', 'v3', credentials=creds)


# ✅ Start Command
@dp.message(Command("start"))
async def start_command(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})

    if not user:
        await users_collection.insert_one({"user_id": message.from_user.id, "username": message.from_user.username})
        await message.answer("👋 Welcome! Please send your Google Drive Folder ID using:\n\n<b>/setfolder [FOLDER_ID]</b>")
    else:
        folder_id = user.get("folder_id")
        if folder_id:
            await message.answer("✅ You’re all set! Send me a file, and I'll upload it to your Google Drive.")
        else:
            await message.answer("🔹 You haven't set a folder yet. Send your Google Drive Folder ID using:\n\n<b>/setfolder [FOLDER_ID]</b>")


# ✅ Set Google Drive Folder ID
@dp.message(Command("setfolder"))
async def set_folder(message: Message):
    folder_id = message.text.split(" ", 1)[-1].strip()

    if len(folder_id) < 20:  # Folder IDs are usually long
        await message.answer("❌ Invalid folder ID. Please check and try again.")
        return

    await users_collection.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"folder_id": folder_id}},
        upsert=True
    )
    await message.answer(f"✅ Folder ID updated successfully!\nYou can now send files to be uploaded.")


# ✅ Handle Document Upload
@dp.message(lambda msg: msg.document)
async def handle_document(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})

    if not user or "folder_id" not in user:
        await message.answer("⚠ You haven't set a Google Drive Folder ID.\nUse:\n\n<b>/setfolder [FOLDER_ID]</b>")
        return

    folder_id = user["folder_id"]
    document = message.document

    # Get file info
    file_info = await bot.get_file(document.file_id)
    file_path = file_info.file_path
    file_name = document.file_name

    # Download file from Telegram
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    local_file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)

    async with bot.session.get(file_url) as response:
        with open(local_file_path, "wb") as f:
            f.write(await response.read())

    # Upload to Google Drive
    file_metadata = {
        "name": file_name,
        "parents": [folder_id]
    }
    media = MediaFileUpload(local_file_path, resumable=True)
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    # Send confirmation to user
    file_link = f"https://drive.google.com/file/d/{uploaded_file['id']}/view"
    await message.answer(f"✅ File uploaded successfully!\n📂 <a href='{file_link}'>View File</a>")


# ✅ Run the Bot
async def main():
    logging.info("Starting bot...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
