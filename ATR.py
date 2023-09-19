import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
import smtplib
import yagmail
import threading
import time
from common import(coins,CandleStick)
import order_book_strategy
import orders
import sys
import exchange_info

key=""
secret=""


um_futures_client = UMFutures(key=key, secret=secret)

candlesticks = um_futures_client.klines('BTCUSDT', '1h', **{"limit": 20})        

candlesticksList = []
            
# for v in candlesticks:
#     candleStick = CandleStick()

#     candleStick.open = float(v[1])
#     candleStick.high = float(v[2])
#     candleStick.low = float(v[3])
#     candleStick.close = float(v[4])
#     candlesticksList.append(candleStick)

def calculate_ATR(prices=[],periods = 14):
    atr = 0
    tr = 0
    trList = []
    candleStick = CandleStick()
    prevCandleStick = CandleStick()
    for i in range(1,len(prices)):
        candleStick = prices[i]
        prevCandleStick = prices[i-1]

        high_low = candleStick.high - candleStick.low
        high_close = abs(candleStick.high - prevCandleStick.close)
        low_close = abs(candleStick.low - prevCandleStick.close)

        tr = max(high_low, high_close, low_close)
        trList.append(tr)
        trSeries = pd.Series(trList)
        atr = trSeries.rolling(periods).mean()

    return atr.mean()

#print(calculate_ATR(candlesticksList))