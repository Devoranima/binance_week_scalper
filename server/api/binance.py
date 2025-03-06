import requests
import time
from typing import List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
  "{asctime} - {levelname} - {message}",
  style="{",
  datefmt="%Y-%m-%d %H:%M",
)

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
CANDLES_ENDPOINT = "klines"




class ApiOverflowError(Exception):
    default_message = 'Too many api requests'

    def __init__(self, timeout: int, message=None):
        super().__init__(message or ApiOverflowError.default_message)
        self.timeout = timeout


def getTradepairs() -> list[str]:
    try:
        response = requests.get('/'.join([API_BASE_URL, EXCHANGE_BASE_ENDPOINT]))
        symbols = json.loads(response.content)["symbols"]
        assets = sorted(set(filter(lambda x: str(x).endswith(
            "USDT"), list(map(lambda x: x["symbol"], symbols)))))
        return assets
    except:
        raise ConnectionError("Network connection error, try again later")

def parseCandleFromResponse(array, symbol):
    candle = dict()
    candle["timeframe"] = '1w'
    candle["datetime_open"] = datetime.fromtimestamp(float(array[0])/1000)
    candle["datetime_close"] = datetime.fromtimestamp(float(array[6])/1000)
    candle["open"] = float(array[1])
    candle["high"] = float(array[2])
    candle["low"] = float(array[3])
    candle["close"] = float(array[4])
    candle["tradepair_name"] = symbol
    return candle

def requestTradepairCandles(symbol: str, limit: int = 5, interval: str = '1w') -> list[dict]:
    response = requests.get('/'.join([API_BASE_URL, CANDLES_ENDPOINT]),
                            params={'timeZone': 1, 'interval': interval ,
                                    'limit': limit, 'symbol': symbol}
                            )
    match response.status_code:
        case 200:
            klines = json.loads(response.content)
            return [parseCandleFromResponse(kline, symbol) for kline in klines]
        case 429:
            # ? limit
            raise ApiOverflowError(timeout=response.headers["Retry-After"])
        case 418:
            # ? autoban
            raise ApiOverflowError(timeout=response.headers["Retry-After"])
        case _:
            raise BrokenPipeError(response)


def getCandles(tradepairs: list[str])->list[dict]:
    candles = list()

    #tradepairs = tradepairs[:11]
    for tradepair_name in tradepairs:
        logger.info("Loading cabdles for %s"%tradepair_name)
        loaded = False
        while loaded == False:
            try:
                tradepair_candles = requestTradepairCandles(symbol=tradepair_name)
                candles.append(tradepair_candles)
                loaded = True
            except ApiOverflowError as err:
                logger.warning("Api overflown, waiting %d seconds"%err.timeout)
                #? make it with logger
                time.sleep(err.timeout)
            except Exception as e:
                logger.critical(e)
                raise RuntimeError(e)
                
    return candles

#? silly billy
def gCandles(tradepairs: list[str]):
    loaded_candles = list()
    for tradepair in tradepairs:
        loaded = False
        while loaded == False:
            try:
                candles = requestTradepairCandles(pair=tradepair)
                for candle in candles:
                    candle['tradepair_name'] = tradepair
                    loaded_candles.append(candle)
                loaded = True
                yield candles
            except ApiOverflowError as err:
                logger.warning("Api overflown, waiting %d seconds"%err.timeout)
                    #? make it with logger
                time.sleep(err.timeout)
            except Exception as e:
                logger.critical(e)
                raise RuntimeError(e)
    return loaded_candles


def getTradepairCandles(symbol: str):
    loaded = False
    while loaded == False:
        try:
            candles = requestTradepairCandles(symbol=symbol)
            loaded=True
            return candles
        except ApiOverflowError as err:
            logger.warning("Api overflown, waiting %d seconds"%err.timeout)
            time.sleep(err.timeout)
        except Exception as e:
            logger.critical(e)
            raise RuntimeError(e)