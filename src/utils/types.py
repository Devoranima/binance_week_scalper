from datetime import datetime


class Kline:
    def __init__(self, array): 
        self.timeframe = '1w'
        self.datetime_open = datetime.fromtimestamp(float(array[0])/1000)
        self.datetime_close = datetime.fromtimestamp(float(array[6])/1000)
        self.value_open = float(array[1])
        self.value_max = float(array[2])
        self.value_min = float(array[3])
        self.value_close = float(array[4])

    def __str__(self):
        return f"{self.datetime_open.strftime('%Y-%m-%d')}\tHigh:{self.value_max}\tLow:{self.value_min}"