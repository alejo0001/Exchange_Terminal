import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import smtplib
import yagmail
import threading
import time
from common import(coins)
import order_book_strategy
import orders
import exchange_info
import sys

key=""
secret=""

clavecorreo = ""
email = ""

um_futures_client = UMFutures(key=key, secret=secret)

logging.basicConfig(filename='test.txt', level=logging.ERROR,filemode='a')
sys.stderr = open('errortest.txt', 'w')
simbolo = ''
mv = ''
try:
    coins_info = []
    cs = coins
    for m in cs:
        coins_info.append(m.simbolo)


        


    coinsCollection = []

    #coinsCollection.append(['UNIUSDT','5.89','5.734','80.01','5.794'])
    coinsCollection.append(['QTUMUSDT','5.89','5.734','80.01','5.794'])
    if(len(coinsCollection) > 0):
    # SendEmail(coinsCollection)
        for c in coinsCollection:
            simbolo = c[0]
            for m in coins:
                if((c[0] != 'BTCUSDT')& (c[0] != 'ETHUSDT') & (c[0]!= 'XMRUSDT') & (c[0]!= 'QNTUSDT') & (c[0]!= 'BNBUSDT')):
                    if(c[0]==m.simbolo):
                        currentCoin =order_book_strategy.getPointsInfo(m)
                        side=''
                        entryPrice=0
                        if(float(c[3])>=80):
                            side='SELL'
                            entryPrice = currentCoin.shortEntry
                        else:
                            side='BUY'
                            entryPrice = currentCoin.longEntry
                        
                        min_value = exchange_info.get_min_value_info(m.simbolo)
                        mv = min_value
                        max_leverage = exchange_info.get_max_leverage(m.simbolo)
                        orders.make_order(m.simbolo,side,'LIMIT',min_value,entryPrice,0,0,max_leverage)
except Exception as e:
    # Registrar el error
    print(str(e))
    logging.error(str(e)+' '+simbolo+', min value: '+mv)
    time.sleep(10)

