import requests
import time
from typing import List
import json
import logging
from ..utils.types import Kline
from ..utils.logging import adaptiveFormatter

logger = logging.getLogger(__name__)

formatter = adaptiveFormatter()

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler("logs/api.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

'''
  #? Single Kline is represented as an array with the following layout 
  [
    1499040000000,      // Kline open time
    "0.01634790",       // Open price
    "0.80000000",       // High price
    "0.01575800",       // Low price
    "0.01577100",       // Close price
    "148976.11427815",  // Volume
    1499644799999,      // Kline Close time
    "2434.19055334",    // Quote asset volume
    308,                // Number of trades
    "1756.87402397",    // Taker buy base asset volume
    "28.46694368",      // Taker buy quote asset volume
    "0"                 // Unused field, ignore.
  ]
'''


API_BASE_URL = "https://data-api.binance.vision/api/v3"
EXCHANGE_BASE_ENDPOINT = "exchangeInfo"
PING_ENDPOINT = "ping"
CANDLES_ENDPOINT = "api/v3/klines"




class ApiOverflowError(Exception):
    default_message = 'Too many api requests'

    def __init__(self, timeout: int, message=None):
        super().__init__(message or ApiOverflowError.default_message)
        self.timeout = timeout


def getTradepairs():
    try:
        response = requests.get('/'.join([API_BASE_URL, EXCHANGE_BASE_ENDPOINT]))
        symbols = json.loads(response.content)["symbols"]
        assets = sorted(set(filter(lambda x: str(x).endswith(
            "USDT"), list(map(lambda x: x["symbol"], symbols)))))
        return assets
    except:
        return ConnectionError("Network connection error, try again later")


def requestTradepairCandles(pair: str, limit: int = 5, interval: str = '1w'):
    response = requests.get('/'.join([API_BASE_URL, CANDLES_ENDPOINT]),
                            params={'timeZone': 1, 'interval': interval ,
                                    'limit': limit, 'symbol': pair}
                            )
    match response.status_code:
        case 200:
            klines = []
            for klinedata in json.loads(response.content):
                newkline = Kline(klinedata)
                klines.append(newkline)
            return klines
        case 429:
            # ? limit
            raise ApiOverflowError(timeout=response.headers["Retry-After"])
        case 418:
            # ? autoban
            raise ApiOverflowError(timeout=response.headers["Retry-After"])
        case _:
            raise BrokenPipeError(error=response.content)


def getCandles(pairs: List[str])->dict:
    candles = dict()
    for pair in pairs:
        logger.info("Loading cabdles for %s"%pair)
        loaded = False
        while loaded == False:
            try:
                tradepair_candles = requestTradepairCandles(pair=pair)
                candles[pair] = tradepair_candles
                loaded = True
            except ApiOverflowError as err:
                logger.warning("Api overflown, waiting %d seconds"%err.timeout)
                #? make it with logger
                time.sleep(err.timeout)
            except Exception as e:
                logger.critical(e)
                raise RuntimeError(e)
                
    return candles

