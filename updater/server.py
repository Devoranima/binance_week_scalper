from updater.api import binance
from updater.db import crud
from updater.config import BOT_SERVER_URL

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


from flask import Flask, jsonify, request, Response
import requests

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
    
def processSwings(tradepair_name: str, timeframe: str):
    """
    Process candles to detect new swing formations and add them if necessary.
    A swing is identified by a 5-candle pattern where the middle one has a local extremum.
    """
    candles = crud.selectCandles(tradepair_name, timeframe)
    if len(candles) < 5:
        return

    added_swings = []
    for i in range(2, len(candles) - 2):
        c1, c2, c3, c4, c5 = candles[i - 2:i + 3]
        
        added_swing = None
        
        # Detect local high (swing high)
        if c3['high'] > c1['high'] and c3['high'] > c2['high'] and c3['high'] > c4['high'] and c3['high'] > c5['high']:
            added_swing = crud.addSwing(tradepair_name, timeframe, candles, orientation_up=True)

        # Detect local low (swing low)
        if c3['low'] < c1['low'] and c3['low'] < c2['low'] and c3['low'] < c4['low'] and c3['low'] < c5['low']:
            added_swing = crud.addSwing(tradepair_name, timeframe, candles, orientation_up=False)

        if added_swing:
            added_swings.append(added_swing)
            
    logger.info(f"Added {len(added_swings)} new swings for {tradepair_name} ({timeframe})")
    return added_swings

def update():
    """
    Fetch new candles, process swings, and send swing updates to the bot.
    """
    logger.info("Starting update process...")

    # Step 1: Fetch new candles
    fetch_new_candles()

    # Step 2: Process swings for each tradepair and timeframe
    tradepairs = crud.selectTradepairs(True)
    tradepair_names = [tp['name'] for tp in tradepairs]

    new_swings = []  # Store newly detected swings

    for tradepair_name in tradepair_names:
        swings = processSwings(tradepair_name, '1w')
        new_swings.extend(swings)

    # Step 3: Send new swing data to bot
    if new_swings:
        send_swings_to_bot(new_swings)

    logger.info("Update process completed.")

def send_swings_to_bot(swings):
    """
    Send newly detected swing specifications to the bot.
    """
    payload = [{"tradepair": s.tradepair_name, "timeframe": s.timeframe_name, "swing_type": "high" if s.orientation_up else "low"}
               for s in swings]

    try:
        response = requests.post(f"http://{BOT_SERVER_URL}/swing-updates", json=payload)
        if response.status_code == 200:
            logger.info("Bot successfully updated with new swings.")
        else:
            logger.error(f"Failed to update bot: {response.text}")
    except Exception as e:
        logger.error(f"Error sending swing update to bot: {e}")


def schedule_update():
    """
    Schedule `update()` to run periodically.
    """
    schedule.every().monday.at("05:00", 'Europe/London').do(update)

    while True:
        schedule.run_pending()
        time.sleep(60)  # Wait a minute before checking again
        

def startServer():
    """
    Start the Flask server and schedule background tasks.
    """
    logger.info("Starting Updater server...")
    threading.Thread(target=schedule_update, daemon=True).start()  # Run scheduler in a background thread
    app.run(host='127.0.0.1', port=7669, debug=True, use_reloader=False)
    

class Swing():
    def __init__(self, tradepair_name, timeframe_name, orientation_up):
        self.tradepair_name = tradepair_name
        self.timeframe_name = timeframe_name
        self.orientation_up = orientation_up
    

def debug():
    swing1 = Swing('BTCUSDT', '1w', True)
    swing2 = Swing('ALTUSDT', '1s', False)
    swing3 = Swing('ETHUSDT', '1h', True)
    
    
    swings = [
        swing1, swing2, swing3
    ]
    send_swings_to_bot(swings)
    #print(BOT_SERVER_URL)
    #requests.get(f"http://{BOT_SERVER_URL}/debug")
    