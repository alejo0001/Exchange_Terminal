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
from common import (Order,CandleStick,telegramAPIKey,SendTelegramMessage)
import ATR

key=""
secret=""

clavecorreo = ""
email = ""

um_futures_client = UMFutures(key=key, secret=secret)

logging.basicConfig(filename='powerfull_pattern.txt', level=logging.ERROR,filemode='a')
sys.stderr = open('error.txt', 'w')


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
    #yag = yagmail.SMTP(user=email,password=clavecorreo)
    destinatarios = ['']
    asunto = 'rsi '+temporality
    mensaje = 'mensaje de prueba'

   
    if(len(coinsCollection) > 0):
        mensaje = ''
        for c in coinsCollection:
            mensaje += c[0]+" - rsi: "+c[3]+"; precio de cierre : "+c[4]+'\n'
    SendTelegramMessage(asunto+'. '+mensaje)
    #yag.send(destinatarios,asunto,mensaje)
    


def calculate_powerfull_pattern(temporality='15m',limit = True,coinList= coins):
    try:
        simbolo = ''
        coins_info = []
        cs = coinList
        for m in cs:
            coins_info.append(m.simbolo)


            


        coinsCollection = []

        

        for co in coins_info:
            candlesticksList = []
            coin = co
            interval = temporality

            candlesticks = um_futures_client.klines(coin, interval, **{"limit": 20})
            
        
           


            latest_prices = []
            for v in candlesticks:
                candleStick = CandleStick()
                latest_prices.append(float(v[4]))
                 

                candleStick.open = float(v[1])
                candleStick.high = float(v[2])
                candleStick.low = float(v[3])
                candleStick.close = float(v[4])
                candlesticksList.append(candleStick)

            prices = pd.Series(latest_prices)
            rsi = calculate_rsi(prices)
            

            # Ejemplo de uso

            rolling_mean, upper_band, lower_band = calculate_bollinger_bands(prices)

            # Graficar los precios y las bandas de Bollinger

            # fig, ax = plt.subplots(figsize=(12,8))
            # ax.plot(prices.index, prices, label='Precio')
            # ax.plot(rolling_mean.index, rolling_mean, label='Media móvil')
            # ax.plot(upper_band.index, upper_band, label='Banda superior')
            # ax.plot(lower_band.index, lower_band, label='Banda inferior')
            # ax.legend()
            # plt.show()

            
            
            if( (rsi[0] >=70) | (rsi[0] <=30)):
            
                coinsCollection.append([coin,str(upper_band[len(upper_band)-1]),str(lower_band[len(lower_band)-1]),str(rsi[0]),str(latest_prices[-1])])
            else:
                print(coin+" - rsi:"+str(rsi[0]))
                

        print('\n')


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
                            atr = ATR.calculate_ATR(candlesticksList)
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
                            o.timeframe = int(interval.split('m')[0])

                            TDB.create_DB_order(o,True)
                SendEmail(coinsCollection,interval+' test')

                            
    except Exception as e:
    # Registrar el error
        print(str(e))
        logging.error(str(e)+' '+simbolo)


















