import json
import requests
import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, TypeHandler, ApplicationHandlerStop
)

from bot.config import TELEGRAM_BOT_TOKEN, SPECIAL_USERS, UPDATER_SERVER_URL
from bot.config import logger


async def startHandle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    await update.message.reply_text("Welcome! Send me a message and I'll process it.")


async def authorizationHandle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Check if the user is authorized."""
    if update.effective_user.id not in SPECIAL_USERS:
        logger.warning(
            f"Unauthorized request from: {update.effective_chat.id}")
        raise ApplicationHandlerStop

async def getTradepairsHandle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    response = requests.get("http://" + UPDATER_SERVER_URL + "/tradepairs")
    tradepairs = json.loads(response.content)['tradepairs']
    tracking = list(filter(lambda x: x['tracking'], tradepairs))

    msg = """
  %d tradepairs loaded
  %d tracking
  %d untracking
  """ % (len(tradepairs), len(tracking), len(tradepairs) - len(tracking))

    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
application.add_handler(TypeHandler(Update, authorizationHandle), -1)   
application.add_handler(CommandHandler('start', startHandle))
application.add_handler(CommandHandler('tradepairs', getTradepairsHandle))

def startControlBot():
    print("Starting control bot")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.run(application.run_polling())
    
    