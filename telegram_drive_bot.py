import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.filters import Command
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram import Router, F

# Suppress OAuth warning
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Load environment variables
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Ensure credentials file exists
GOOGLE_CREDENTIALS_FILE = os.path.join(os.getcwd(), "ambient-depth-450117-t2-817e247adf33.json")

# Google Drive API Scopes
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot with session
session = AiohttpSession()
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
dp = Dispatcher()

# Authenticate Google Drive
def authenticate_drive():
    creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

drive_service = authenticate_drive()

# Google Drive folder
FOLDER_ID = "1-3tmMJ0ivSRpEAXdOE6zeqzlR27HU9oB"  # Replace with actual folder ID

# Upload function
def upload_to_drive(file_path, file_name):
    media = MediaFileUpload(file_path, resumable=True)
    file_metadata = {"name": file_name, "parents": [FOLDER_ID]}  # Uploads to the folder
    file = drive_service.files().create(body=file_metadata, media_body=media, fields="id").execute()
    return f"https://drive.google.com/file/d/{file['id']}/view"

# ✅ Fixed registration
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.reply("Send me any file (photo, video, document), and I'll upload it to Google Drive!")

router = Router()

# ✅ Universal Handler for ALL FILE TYPES
@router.message(F.content_type.in_({types.ContentType.DOCUMENT, types.ContentType.PHOTO, types.ContentType.VIDEO}))
async def handle_files(message: Message):
    # Determine file type
    if message.document:
        file = message.document
        file_name = message.document.file_name
    elif message.photo:
        file = message.photo[-1]  # Get highest resolution
        file_name = f"photo_{message.message_id}.jpg"
    elif message.video:
        file = message.video
        file_name = message.video.file_name or f"video_{message.message_id}.mp4"
    else:
        await message.reply("Unsupported file type!")
        return

    # Download file
    file_path = f"downloads/{file_name}"
    os.makedirs("downloads", exist_ok=True)
    file_info = await bot.get_file(file.file_id)
    await bot.download_file(file_info.file_path, file_path)

    # Upload to Google Drive
    drive_link = upload_to_drive(file_path, file_name)

    # Send confirmation
    await message.reply(f"✅ File uploaded successfully!\n[View File]({drive_link})", parse_mode="Markdown")

    # Delete local file
    os.remove(file_path)

# Start bot
async def main():
    dp.include_router(router)  # Register router
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
