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
import sys
import exchange_info
import TDB
from common import (Order,CandleStick)
import ATR

key=""
secret=""

clavecorreo = ""
email = ""

um_futures_client = UMFutures(key=key, secret=secret)

# logging.basicConfig(filename='powerfull_pattern.txt', level=logging.ERROR,filemode='a')
# sys.stderr = open('error.txt', 'w')


def calculate_rsi(prices, n=14):
    deltas = prices.diff()
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = pd.Series(100 - (100/(1 + rs)), index=prices.index)
    return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()
    upper_band = rolling_mean + (num_std * rolling_std)
    lower_band = rolling_mean - (num_std * rolling_std)
    return rolling_mean, upper_band, lower_band

def SendEmail(coinsCollection=[],temporality = '15m'):
    yag = yagmail.SMTP(user=email,password=clavecorreo)
    destinatarios = ['']
    asunto = 'patrón poderoso '+temporality
    mensaje = 'mensaje de prueba'

    if(len(coinsCollection) > 0):
        mensaje = ''
        for c in coinsCollection:
            mensaje += c[0]+': banda superior: '+c[1]+"; banda inferior: "+c[2]+"; rsi: "+c[3]+"; precio de cierre : "+c[4]+'\n'

    yag.send(destinatarios,asunto,mensaje)

def calculate_powerfull_pattern(temporality='15m',limit = True,coinList= coins):
    
    try:
        


            

        
        coinsCollection = []

       
         
        coinsCollection.append(['CFXUSDT','0.24379791325318323','0.24034208674681679','84','85'])
          


        if(len(coinsCollection) > 0):
            if(limit == True):
                
                for c in coinsCollection:
                    simbolo = c[0]
                    for m in coins:
                        if((c[0] != 'BTCUSDT')& (c[0] != 'ETHUSDT') & (c[0]!= 'XMRUSDT') & (c[0]!= 'QNTUSDT') & (c[0]!= 'BNBUSDT')& (c[0]!= 'MKRUSDT')):
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
                                max_leverage = exchange_info.get_max_leverage(m.simbolo)
                                #orders.make_order(m.simbolo,side,'LIMIT',min_value,entryPrice,0,0,max_leverage)
                SendEmail(coinsCollection,temporality)
            else:
                
                order_type = 0
                for c in coinsCollection:
                    simbolo = c[0]
                    for m in coins:                        
                        if(c[0]==m.simbolo):
                            #currentCoin =order_book_strategy.getPointsInfo(m)
                            side=''
                            entryPrice=0
                            atr = 0.02
                            response = um_futures_client.mark_price(simbolo)
                            lp = float(response['indexPrice'])
                            tp = 0
                            sl=0

                            if(float(c[3])>=80):
                                side='SELL'
                                order_type = 1
                                tp = lp - (atr*2)
                                sl = lp + atr
                            else:
                                side='BUY'
                                order_type = 0
                                tp = lp + (atr*2)
                                sl = lp - atr
                            
                            min_value = exchange_info.get_min_value_info(simbolo)
                            max_leverage = exchange_info.get_max_leverage(simbolo)

                            

                            o = Order()

                            o.symbol=m.simbolo
                            o.order_type=order_type
                            o.order_size=min_value
                            o.price=lp
                            o.take_profit=tp
                            o.stop_loss=sl
                            o.order_message = simbolo+': banda superior: '+c[1]+"; banda inferior: "+c[2]+"; rsi: "+c[3]+"; precio de cierre : "+c[4]
                            o.timeframe = int(temporality.split('m')[0])

                            #TDB.create_DB_order(o,True)
                SendEmail(coinsCollection,temporality+' test')
                print('funciona')
                            
    except Exception as e:
    # Registrar el error
        print(str(e))
        logging.error(str(e)+' '+simbolo)

calculate_powerfull_pattern('3m',False)
    
















