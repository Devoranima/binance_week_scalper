import threading
from bot.bot import startBot
from bot.control_bot import startControlBot


def startBots():
    bot_thread = threading.Thread(target=startBot)
    bot_thread.start()
    startControlBot()
    