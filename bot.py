import os
import logging
import asyncio
import aiohttp
import requests  # FIXED: Added missing import
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup
from flask import Flask
from threading import Thread

# Configuration
DOWNLOAD_WEBSITE = "https://theteradownloader.com"  # Change if needed
TOKEN = os.environ.get("TOKEN")  # Ensure this is set in Render

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== Telegram Bot Functions ==========

async def start(update: Update, context):
    """Handles the /start command."""
    await update.message.reply_text(
        "🚀 Welcome to Video Downloader Bot!\n"
        "Send me a video link (YouTube, Instagram, etc.) and I'll download it for you!"
    )

async def download_video(update: Update, context):
    """Handles video download requests."""
    url = update.message.text
    chat_id = update.message.chat_id

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Please send a valid URL starting with http:// or https://")
        return

    try:
        await update.message.reply_text("⏳ Processing your request...")

        # Fetch the download link using a separate thread
        download_link = await asyncio.to_thread(get_download_link, url)

        if not download_link:
            await update.message.reply_text("❌ Could not find a download link. Please try another URL.")
            return

        await update.message.reply_text("⬇️ Downloading video... Please wait.")

        video_path = await download_and_save_video(download_link)

        if not video_path:
            await update.message.reply_text("❌ Error downloading video.")
            return

        await update.message.reply_text("📤 Uploading video...")

        with open(video_path, "rb") as video_file:
            await context.bot.send_video(
                chat_id=chat_id,
                video=video_file,
                supports_streaming=True
            )

        os.remove(video_path)  # Cleanup after sending

    except Exception as e:
        logger.exception(f"An error occurred: {e}")
        await update.message.reply_text("❌ An unexpected error occurred. Please try again later.")

def get_download_link(video_url):
    """Scrapes the website to get the actual download link for the video."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        payload = {"url": video_url}
        response = requests.post(DOWNLOAD_WEBSITE, data=payload, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes

        soup = BeautifulSoup(response.text, "html.parser")

        # Find the first <a> tag with a download link
        for link in soup.find_all("a"):
            if "download" in link.get_text(strip=True).lower() or "href" in link.attrs:
                return link["href"]

        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {e}")
        return None
    except Exception as e:
        logger.exception(f"Scraping error: {e}")
        return None

async def download_and_save_video(url):
    """Downloads a video from the URL and saves it locally."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    video_path = "downloaded_video.mp4"
                    with open(video_path, "wb") as file:
                        file.write(await response.read())
                    return video_path
    except Exception as e:
        logger.exception(f"Video download failed: {e}")
    return None

# ========== Flask Server ==========
@app.route('/')
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ========== Main Execution ==========
if __name__ == "__main__":
    if not TOKEN:
        raise ValueError("Missing Telegram token! Set the 'TOKEN' environment variable.")

    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Build Telegram Bot
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))

    logger.info("Bot is running...")
    application.run_polling()
    def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


