import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
EMAIL_USER = os.getenv("SMTP_EMAIL")
EMAIL_PASS = os.getenv("SMTP_PASSWORD")
EMAIL_HOST = os.getenv("SMTP_SERVER")
EMAIL_PORT = int(os.getenv("SMTP_PORT", 465))