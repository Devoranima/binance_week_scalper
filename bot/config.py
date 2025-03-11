import os
import logging
from dotenv import load_dotenv

load_dotenv() 

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CONTROL_BOT_TOKEN = os.getenv("CONTROL_BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")
UPDATER_SERVER_URL=os.getenv("UPDATER_SERVER_URL")

if not TELEGRAM_BOT_TOKEN:
    raise AttributeError("Telegram bot token not found. Check .env file.")
if not CONTROL_BOT_TOKEN:
    raise AttributeError("Control bot token not found. Check .env file.")
if not ADMIN_ID:
    raise AttributeError("Admin ID not found. Check .env file.")
if not UPDATER_SERVER_URL:
    raise AttributeError("Updater URL not found. Check .env file.")

SPECIAL_USERS = [int(ADMIN_ID)]
CHAT_ID = ADMIN_ID

logger = logging.getLogger()

def setupLogging():

    main_log_handler = logging.FileHandler("logs/bot.log")
    main_log_handler.setLevel(logging.INFO)
    main_log_formatter = logging.Formatter()
    main_log_handler.setFormatter(main_log_formatter)

    naughty_kids_handler = logging.FileHandler("logs/naughty_kids.log")
    naughty_kids_handler.setLevel(logging.WARN)
    naughty_kids_formatter = logging.Formatter(
        "{asctime} | {message}",
        style="{",
        datefmt="%y:%m:%d %H:%M"
    )
    naughty_kids_filter = logging.Filter()
    naughty_kids_filter.filter = lambda x: x.message.startswith(
        "Unauthorized request from:")
    naughty_kids_handler.setFormatter(naughty_kids_formatter)
    naughty_kids_handler.addFilter(naughty_kids_filter)

    logger.addHandler(main_log_handler)
    logger.addHandler(naughty_kids_handler)