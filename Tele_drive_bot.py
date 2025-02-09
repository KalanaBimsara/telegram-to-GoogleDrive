import os
import logging
import json
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from motor.motor_asyncio import AsyncIOMotorClient
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from aiogram import F 
from aiogram.types import Message

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "tele_drive_bot"
COLLECTION_NAME = "users"

# Logging setup
logging.basicConfig(level=logging.INFO)

# ✅ Correct Aiogram 3.x Bot & Dispatcher Setup
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
router = Router()  # Use a separate router

# ✅ MongoDB Connection
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client[DB_NAME]
users_collection = db[COLLECTION_NAME]

# ✅ Start Command
@router.message(Command("start"))
async def start_command(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})

    if not user:
        await users_collection.insert_one({"user_id": message.from_user.id, "username": message.from_user.username})
        await message.answer("👋 Welcome! Please send your **Google Drive JSON credentials file**.")
    else:
        if "credentials_json" not in user:
            await message.answer("📂 Please upload your Google Drive JSON credentials file to proceed.")
        elif "folder_id" not in user:
            await message.answer("🔹 Now, set your Google Drive folder using:\n\n<b>/setfolder [FOLDER_ID]</b>")
        else:
            await message.answer("✅ You’re all set! Send me a file, and I'll upload it to your Google Drive.")

# ✅ Handle Google Drive JSON File Upload
@router.message(lambda msg: msg.document and msg.document.file_name.endswith(".json"))
async def handle_json_upload(message: Message):
    # Get user ID
    user_id = message.from_user.id
    file = message.document

    # Download the JSON file
    file_info = await bot.get_file(file.file_id)
    local_path = f"downloads/{file.file_name}"
    os.makedirs("downloads", exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}") as response:
            with open(local_path, "wb") as f:
                f.write(await response.read())

    # Read JSON content
    with open(local_path, "r") as json_file:
        credentials_json = json.load(json_file)

    # Store in MongoDB
    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"credentials_json": credentials_json}},
        upsert=True
    )

    # Delete local file
    os.remove(local_path)

    await message.answer("✅ Google Drive credentials saved! Now, set your Google Drive folder with:\n\n<b>/setfolder [FOLDER_ID]</b>")

# ✅ Set Google Drive Folder ID
@router.message(Command("setfolder"))
async def set_folder(message: Message):
    folder_id = message.text.split(" ", 1)[-1].strip()

    if len(folder_id) < 20:  # Folder IDs are usually long
        await message.answer("❌ Invalid folder ID. Please check and try again.")
        return

    user = await users_collection.find_one({"user_id": message.from_user.id})
    if not user or "credentials_json" not in user:
        await message.answer("⚠ Please upload your Google Drive JSON credentials file first.")
        return

    await users_collection.update_one(
        {"user_id": message.from_user.id},
        {"$set": {"folder_id": folder_id}},
        upsert=True
    )
    await message.answer("✅ Folder ID updated successfully! You can now send files.")

# ✅ Handle Document Upload
@router.message(lambda msg: msg.content_type in {types.ContentType.DOCUMENT, types.ContentType.PHOTO, types.ContentType.VIDEO})
async def handle_files(message: Message):
    user = await users_collection.find_one({"user_id": message.from_user.id})

    # ✅ Check if JSON credentials exist
    if not user or "credentials_json" not in user:
        await message.answer("⚠ Please upload your Google Drive JSON credentials file first.")
        return
    if "folder_id" not in user:
        await message.answer("⚠ Please set your Google Drive folder using:\n\n<b>/setfolder [FOLDER_ID]</b>")
        return

    # Determine file type
    if message.document:
        file = message.document
        file_name = file.file_name
    elif message.photo:
        file = message.photo[-1]  # Highest resolution
        file_name = f"photo_{message.message_id}.jpg"
    elif message.video:
        file = message.video
        file_name = file.file_name or f"video_{message.message_id}.mp4"
    else:
        await message.reply("❌ Unsupported file type!")
        return

    # Download file from Telegram
    file_info = await bot.get_file(file.file_id)
    local_file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)

    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}") as response:
            with open(local_file_path, "wb") as f:
                f.write(await response.read())

    # Upload to Google Drive
    drive_link = await upload_to_drive(local_file_path, file_name, user)

    if drive_link:
        await message.answer(f"✅ File uploaded successfully!\n📂 <a href='{drive_link}'>View File</a>")
        os.remove(local_file_path)
    else:
        await message.answer("❌ Upload failed. Please try again.")

async def upload_to_drive(local_file_path, file_name, user):
    # Load credentials from user data
    credentials_json = user["credentials_json"]
    creds = Credentials.from_service_account_info(credentials_json)
    drive_service = build('drive', 'v3', credentials=creds)

    # Upload file to Google Drive
    file_metadata = {
        "name": file_name,
        "parents": [user["folder_id"]]
    }
    media = MediaFileUpload(local_file_path, resumable=True)
    uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()

    # Return the link to the uploaded file
    file_link = f"https://drive.google.com/file/d/{uploaded_file['id']}/view"
    return file_link

# ✅ Run the Bot
async def main():
    logging.info("Starting bot...")
    dp.include_router(router)  # Include the router in the dispatcher
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())