import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

# Comma-separated list of Telegram user IDs who are admins (e.g. 123456789,987654321)
ADMINS = []
raw_admins = os.getenv("ADMINS", "")
if raw_admins:
    try:
        ADMINS = [int(x.strip()) for x in raw_admins.split(",") if x.strip()]
    except ValueError:
        ADMINS = []

# WhatsApp number for admin contact in international format without + (e.g. 15551234567)
ADMIN_WHATSAPP_NUMBER = os.getenv("ADMIN_WHATSAPP_NUMBER", "")

# Optional base URL for file access if you host uploads somewhere
FILES_BASE_URL = os.getenv("FILES_BASE_URL", "")
