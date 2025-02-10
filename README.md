# 🚀 Telegram Google Drive Uploader Bot

A fully asynchronous Telegram bot that allows users to upload files to their Google Drive. This bot securely stores user credentials in a MongoDB database and supports multiple users simultaneously.

## 📌 Features
- ✅ **Secure user authentication** with Google Drive API.
- 📂 **Uploads documents, images, and videos** to user-specified Google Drive folders.
- ⚡ **Asynchronous and scalable** (built with Aiogram 3.x and Motor for MongoDB).
- 🔒 **User-specific credentials and folders** stored securely.
- 🏗 **Easy to deploy** on any server or cloud instance.

## 🔧 Prerequisites
Before running the bot, make sure you have the following:
1. **Python 3.10+** installed.
2. A **Telegram Bot Token** from [BotFather](https://t.me/BotFather).
3. A **MongoDB Database** (e.g., MongoDB Atlas or a local instance).
4. A **Google Cloud Project** with a Service Account and Drive API enabled.

## 📂 Setup Guide
### 1️⃣ Clone the Repository
```sh
git clone https://github.com/yourusername/telegram-drive-bot.git
cd telegram-drive-bot
```

### 2️⃣ Install Dependencies
```sh
pip install -r requirements.txt
```

### 3️⃣ Create a `.env` File
Create a `.env` file in the project root directory and add the following:
```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
MONGO_URI=your_mongodb_connection_string
```

### 4️⃣ Setup Google Drive API
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Google Drive API** for the project.
4. Create a **Service Account** and download the JSON credentials file.
5. Share the **Google Drive folder** where files will be uploaded with the service account email (`xxx@developer.gserviceaccount.com`).

### 5️⃣ Run the Bot
```sh
python main.py
```

## 🛠 Usage Instructions
### **Step 1: Start the Bot**
Send `/start` to the bot. If it's your first time, it will ask for your **Google Drive JSON credentials file**.

### **Step 2: Upload Google Drive Credentials**
To obtain your **Service Account JSON file**, follow these steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Select your project and navigate to **IAM & Admin > Service Accounts**.
3. Click **Create Service Account**, fill in the required details, and create it.
4. Once created, go to the **Keys** section and generate a new JSON key.
5. Download the JSON key file and keep it secure.

Next, you need to grant access to your Google Drive folder:
1. Go to [Google Drive](https://drive.google.com/).
2. Right-click the folder where you want to upload files and select **Share**.
3. Enter the **service account email** (found in the JSON file) and grant it **Editor** access.

Finally, upload the JSON file to the bot.

### **Step 3: Set a Google Drive Folder**
Use the following command to set the folder where files will be uploaded:
```sh
/setfolder FOLDER_ID
```
Replace `FOLDER_ID` with the actual **Google Drive Folder ID**.

### **Step 4: Upload Files**
Simply send a document, image, or video to the bot. It will:
- Download the file from Telegram.
- Upload it to your specified Google Drive folder.
- Return a link to the uploaded file.

## 🎯 Deployment Options
### Deploy on a VPS (Linux)
```sh
nohup python main.py &
```
This will run the bot in the background.

### Deploy Using Docker
1. Build the Docker image:
   ```sh
   docker build -t telegram-drive-bot .
   ```
2. Run the container:
   ```sh
   docker run -d --env-file .env telegram-drive-bot
   ```

## 🚨 Troubleshooting
- **Bot doesn't respond?** Check if the **Telegram bot token** is correct.
- **File upload fails?** Ensure the **service account has access** to the Google Drive folder.
- **MongoDB connection error?** Verify the **MongoDB URI** in the `.env` file.

## 🤝 Contributing
Feel free to fork the repository and submit pull requests to improve the bot!

## 📜 License
This project is licensed under the MIT License.

---
🚀 **Built with Aiogram, MongoDB, and Google Drive API**

