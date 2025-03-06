from server.api import binance
from server.db import crud
import schedule
import time
import threading
import logging
import json

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


def parseNewTradepairs():
    """Parse new tradepairs"""
    
    logger.info("Fetching tradepairs...")
    tradepairs = binance.getTradepairs()
    logger.debug(f"Fetched {len(tradepairs)} tradepairs")
    logger.info("Uploading tradepairs to db...")
    added_tradepairs = crud.addTradepairs(tradepairs=tradepairs)
    logger.debug(f"Added {len(added_tradepairs)} tradepairs")
    return jsonify({'added_tradepairs': added_tradepairs})
    
def getTradepairs(tracking: bool = None):
    tradepairs = crud.selectTradepairs(tracking)
    
    print(list(map(lambda x: x.name, tradepairs)))
    print(f"{len(tradepairs)} Tradepairs found")

def getCandles(tradepair_name: str, timeframe: str):
    candles = crud.selectCandles(tradepair_name, timeframe)
    
    print(candles)
    print(f"{len(candles)} Candles found")
    
def parseNewCandles():
    logger.info("Loading tradepairs...")
    tradepairs = crud.selectTradepairs(tracking=True)
    tradepairs = list(map(lambda x: x['name'], tradepairs))
    print(f"{len(tradepairs)} tradepairs loaded. Fetching candles...")
    
    try:
        candles = binance.getCandles(tradepairs)
    except RuntimeError as err:
        logger.error(err)
    else:
        logger.info("Adding candles to the DB")
        added_candles = crud.addCandles(candles)
        if (len(added_candles) != 0):
            logger.info(f"Added {len(added_candles)} candles")
        else:
            logger.info("No new candles")

def parse(table: str):
    if table == "candles":
        parseNewCandles()
    elif table == "tradepairs":
        parseNewTradepairs()

def switchTradepairsTrakingStatus(track:bool, selected_tradepairs: list[str]):
    tradepairs = crud.switchTradepairsTrackingStatus(track, selected_tradepairs)
    print(tradepairs)

def startUpdater():
    def run():
        schedule.every().monday.at("03:00").do(parseNewCandles)
        
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
        
        


from flask import Flask, jsonify, request, Response

app = Flask(__name__)

@app.route('/tradepairs', methods=['GET'])
def get_tradepairs():
    tracking = request.args.get('tracking', type = bool)
    tradepairs = crud.selectTradepairs(tracking)
    return jsonify({'tradepairs': tradepairs})

@app.route('/candles', methods=["GET"])
def get_candles():
    tradepair_name = request.args.get('tradepair_name', type=str)
    timeframe = request.args.get('timeframe', type=str)
    if timeframe and tradepair_name:
        candles = crud.selectCandles(tradepair_name, timeframe)
        return jsonify({'candles': candles})
    return Response('Invalid parameters', status=422)

@app.route('/tradepairs/status', methods=["PUT"])
def switch_tradepairs_status():
    data = json.loads(request.data)
    tradepairs = data['tradepairs']
    tracking = data['tracking']

    if tradepairs and tracking != None:
        updated_tradepairs = crud.switchTradepairsTrackingStatus(tracking, tradepairs)
        if updated_tradepairs:
            return jsonify({'updated_tradepairs': updated_tradepairs})
    
    return Response('Invalid parameters', status=422)

@app.route('/tradepairs/update', methods=['POST'])
def fetch_new_tradepairs():
    logger.info("Fetching tradepairs...")
    tradepairs = binance.getTradepairs()
    logger.debug(f"Fetched {len(tradepairs)} tradepairs")
    logger.info("Uploading tradepairs to db...")
    added_tradepairs = crud.addTradepairs(tradepairs=tradepairs)
    logger.debug(f"Added {len(added_tradepairs)} tradepairs")
    return jsonify({'added_tradepairs': added_tradepairs})


@app.route('/candles/update', methods=['POST'])
def fetch_new_candles():
    logger.info("Loading tradepairs...")
    tradepairs = crud.selectTradepairs(True)
    
    #! just for debugging
    tradepairs = tradepairs[:60]
    
    logger.debug(f"{len(tradepairs)} tradepairs loaded")
    logger.info("Fetching candles...")
    tradepair_names = list(map(lambda x: x['name'], tradepairs))
    new_candles = []
    for tradepair_name in tradepair_names:
        try:
            candles = binance.getTradepairCandles(tradepair_name)
            new_candles.append(candles)
            logger.debug(f"Fetched {len(candles)} candles for {tradepair_name}")
        except Exception as e:
            logger.error(e)
            return Response(f'Some error occured while loading candles for {tradepair_name}. Check logs for more info', status=500)
    logger.info("Uploading candles to db...")
    added_candles = crud.addCandles(new_candles)
    return jsonify({'added_candles_number': len(added_candles)})



def startServer():
    app.run(debug=True, use_reloader=False)
    
def debug():
    tradepairs = crud.switchTradepairsTrackingStatus(False, ['BTCUSDT'])

    for tradepair in tradepairs:
        print(tradepair)
