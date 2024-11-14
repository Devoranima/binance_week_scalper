import json
import requests
import time
from datetime import datetime
from typing import TypedDict

API_BASE_URL = "https://api.binance.com"
START_DATE = datetime(2024, 9, 1)

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

KlineTime = TypedDict('KlineTime', {'open': datetime, 'close': datetime})


class Kline:
    def __init__(self, array):
        self.time: dict[str, datetime] = {'open': None, 'close': None}
        self.price = {'open': None, 'close': None, 'high': None, 'low': None}
        self.time['open'] = datetime.fromtimestamp(float(array[0])/1000)
        self.time['close'] = datetime.fromtimestamp(float(array[6])/1000)
        self.price['open'] = float(array[1])
        self.price['high'] = float(array[2])
        self.price['low'] = float(array[3])
        self.price['close'] = float(array[4])

    def __str__(self):
        return f"{self.time['open'].strftime('%Y-%m-%d')}\tHigh:{self.price['high']}\tLow:{self.price['low']}"
    
class FileController:
    def __init__(self, filename = "klines.json"):
        self.filename = filename
        self.klines = {}
        try:
            with open(filename, "r+") as file:
                self.klines : dict[str, list[Kline]] = json.load(file)
        except FileNotFoundError:
            pass
    
    def __writeKlinesToFile__(self, pair, klines):
        self.klines[pair] = klines
        with open(self.filename, "w") as file:
            json.dump(self.klines, file)
        
    def __getNewKlines__(self, pair, klines: list[Kline]):
        new_klines : list[Kline] = sorted(klines, key = lambda x : x.time['open'])
        if pair in self.klines:
            old_klines : list[Kline] = sorted(self.klines[pair], key = lambda x : x.time['open'])
            if old_klines[-1].time['open'] < new_klines[0].time['open']:
                return new_klines
            if old_klines[0].time['open'] > new_klines[0].time['open']:
                return new_klines
            i = 0
            while(old_klines[i].time['open'] < new_klines[0].time['open']): i+=1
            return old_klines[0:i]+new_klines
            
        return new_klines

    def updateKlines(self, pair, klines: list[Kline]):
        new_klines = self.__getNewKlines__(pair, klines)
        self.__writeKlinesToFile__(pair, new_klines)

class TimeoutError(Exception):
    default_message = 'Too many api requests'
    def __init__(self, timeout: int, message = None):
        super().__init__(message or TimeoutError.default_message)
        self.timeout = timeout


def processResponse(klinesarr):
    klines = []
    for klinedata in klinesarr:
        newkline = Kline(klinedata)
        if newkline.time['open'] < START_DATE:
            continue
        klines.append(newkline)
        
    return klines
    



def requestKlines(pair: str):
    response = requests.get('/'.join([API_BASE_URL, "api/v3/klines"]),
                            params={'timeZone': 1, 'interval': '1w',
                                    'limit': 20, 'symbol': pair}
                            )
    match response.status_code:
        case 200:
            return processResponse(json.loads(response.content))
        case 429:
            # ? limit
            raise TimeoutError(
                timeout=response.headers["Retry-After"])
        case 418:
            # ? autoban
            raise TimeoutError(timeout=response.headers["Retry-After"])
        case _:
            raise BrokenPipeError(error=response.content)


def main():  
    try:
        f = open("assets.json", "r")
    except FileNotFoundError as e:
        print("File not found assets.json")
    else:
        with f:
            file_controller = FileController()
            pairs = json.load(f)
            for pair in pairs:
                loaded = False
                while loaded==False:
                    try:
                        klines = requestKlines(pair=pair)
                        file_controller.updateKlines(pair=pair, klines=klines)
                        loaded = True
                    except TimeoutError as err:
                        print(err)
                        time.sleep(err.timeout)
                
        


if __name__ == "__main__":
    main()
