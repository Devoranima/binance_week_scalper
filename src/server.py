from .controllers import api, bot, db
import schedule
import time
import threading
import logging
from .utils import logging as lg


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler() 
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter(
  "{asctime} - {levelname} - {message}",
  style="{",
  datefmt="%Y-%m-%d %H:%M",
)

console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def updateTradepairs():
    """Update tradepairs list"""
    print("Starting tradepairs list update...")
    try:
        tradepairs = api.getTradepairs()
    except ConnectionError as e:
        print(e)
    else:
        print("Finished fetching tradepairs from Binance")
        print("Uploading tradepairs to the database")
        values = db.updateTradepairs(tradepairs=tradepairs)
        print("Update complete, exiting...")
    
def getTradepairs(filter: str):
    if (filter == "none-filter"):
        tradepairs = db.selectAllTradepairs()    
    else:
        tradepairs = db.selectFilteredTradepairs(filter == "tracking")
    
    print(tradepairs)
    
def udpateCandles():
    logger.info("Starting candles update")
    tradepairs = db.selectFilteredTradepairs(True)
    try:
        candles = api.getCandles(tradepairs) 
    except RuntimeError as err:
        logger.error(err)
    else:
        logger.info("Adding candles to the DB")
        db.addCandles(candles)
    
def switchTradepairsTrakingStatus(track:bool, selected_tradepairs: list[str]):
    tradepairs = db.switchTradepairsTrackingStatus(track, selected_tradepairs)
    print(tradepairs)


def startUpdater():
    def run():
        schedule.every().monday.at("03:00").do(udpateCandles)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    updater_thread = threading.Thread(target = run)
    
    try:
        updater_thread.start()
    except Exception as e:
        logger.error("Failed to start the Updater")
        logger.exception(e)
    else:
        logger.info("Updater started\nJob scheduled for every Monday at 3am 0tmz")


def startBot():
    tgBot = bot.BotController()
    try:
        logger.info("Bot started polling")
        tgBot.run()
    except Exception as e:
        logger.error("Failed to start the Bot")
        logger.exception(e)
        
    
def startRoutine(option):
    match option:
        case 'bot':
            startBot()
        case 'updater':
            startUpdater()
        case _:
            startUpdater()
            startBot()