import os
from dotenv import load_dotenv

load_dotenv() 

BOT_SERVER_URL=os.getenv("BOT_SERVER_URL")

if not BOT_SERVER_URL:
    raise AttributeError("Bot URL not found. Check .env file.")
