import os
from dotenv import load_dotenv
from ..utils.wrappers import singleton
from ..utils.logging import adaptiveFormatter

load_dotenv() 

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TELEGRAM_BOT_TOKEN == None:
  raise AttributeError("Telegram bot token not found. Check if TELEGRAM_BOT_TOKEN is declared in .env")

ADMIN_ID = os.getenv("ADMIN_ID")
if ADMIN_ID == None:
  raise AttributeError("Admin ID not found. Check if ADMIN_ID is declared in .env")


from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, TypeHandler, ApplicationHandlerStop
import asyncio
import logging

logger = logging.getLogger(__name__)

main_log_handler = logging.FileHandler("logs/bot.log")
main_log_handler.setLevel(logging.INFO)
main_log_formatter = adaptiveFormatter()
main_log_handler.setFormatter(main_log_formatter)

naughty_kids_handler = logging.FileHandler("logs/naughty_kids.log")
naughty_kids_handler.setLevel(logging.WARN)
naughty_kids_formatter = logging.Formatter(
  "{asctime} | {message}",
  style="{",
  datefmt="%y:%m:%d %H:%M"
)
naughty_kids_filter = logging.Filter()
naughty_kids_filter.filter = lambda x: x.message.startswith("Unathorized request from:")
naughty_kids_handler.setFormatter(naughty_kids_formatter)
naughty_kids_handler.addFilter(naughty_kids_filter)

logger.addHandler(main_log_handler)
logger.addHandler(naughty_kids_handler)

SPECIAL_USERS = [int(ADMIN_ID)]

@singleton
class BotController():
  def __init__(self, *args, **kwargs):
    self.application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    handler = TypeHandler(Update, authorizationHandle)
    self.application.add_handler(handler, -1)
    
    start_handler = CommandHandler('start', start)
    self.application.add_handler(start_handler)
  
  def run(self):
    asyncio.create_task(self.application.run_polling())
  
  def sendUpdate(self, data):
    raise NotImplementedError("BotCntroller().sendUpdate is not implemented")
    

async def authorizationHandle(update: Update, context: ContextTypes.DEFAULT_TYPE):
  if update.effective_user.id in SPECIAL_USERS:
    pass
  else:
    #await update.effective_message.reply_text("Hey! You are not allowed to use me!")
    logger.warning("Unathorized request from: %s"%update.effective_chat.id)
    
    raise ApplicationHandlerStop  

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
  await context.bot.send_message(chat_id=update.effective_chat.id, text="I'm a bot, please talk to me!")

