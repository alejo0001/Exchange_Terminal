from asyncio import sleep
import asyncio
import logging
import math
from typing import List
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import pandas as pd

import numpy as np
#import matplotlib.pyplot as plt
import smtplib
import yagmail
import threading

import time
from Klines import getBybitKlines
import order_book_strategy
import orders
import sys

import exchange_info
#import TDB
from common import (CreateOrder, Order,CandleStick, SetTakeprofit, calculateRelativePercentageDiff, getUsdtOrderSize, qty_precission, telegramAPIKey,SendTelegramMessage,obtener_datos_historicos,CalculateMovingAverage)
import ATR
from pybit.unified_trading import (WebSocket,HTTP)

from config import (bybit_api_key,bybit_secret_key)
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR

symbol='GRIFFAINUSDT'
interval='1'

currentMAValue = 0
avgDistanceFromMA = 1 #%
distanceMultiplier = 2 #%
openedPosition = False


tp_percent = 1
sl_percent = 1
tickSize = 0
priceScale = 0
qty = 0

takeProfit = False
isEvaluating = False
usdt = 6
marginPercentage = 15 #porcentaje a utilizar para entrar en las operaciones

ws = WebSocket(
    testnet=False,
    channel_type="linear",
)


client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)

def CalculateValues(wsMessage):
    global currentMAValue
    global symbol

    if(wsMessage['data'][0]['confirm']== True):
        # posiciones=client.get_positions(category="linear",symbol=symbol)
        # if float(posiciones['result']['list'][0]['size']) == 0:
        #     on_message(message)

        data= obtener_datos_historicos(symbol,interval)
        data = CalculateMovingAverage(data)
        currentMAValue = data['MA']
        print("Actualización de valores: ")
        print(wsMessage)

def ValidateEntry(wsMessage):

    global currentMAValue
    global symbol
    global openedPosition
    global tickSize
    global priceScale
    global qty
    global takeProfit 
    global isEvaluating
    global marginPercentage

    if(not isEvaluating):
        isEvaluating = True
        if(not openedPosition):
            posiciones=client.get_positions(category="linear",symbol=symbol)
            if float(posiciones['result']['list'][0]['size']) != 0:
                isEvaluating = False
                openedPosition = True
                print('posición abierta...')
                return
            last_trade = wsMessage["data"][-1]
            last_price = float(last_trade['p'])
            if(currentMAValue > 0 ):
                percentageDistance = abs(calculateRelativePercentageDiff(currentMAValue,last_price))

                if(percentageDistance >= (avgDistanceFromMA*distanceMultiplier)):
                    side = 'Buy' if currentMAValue > last_price else 'Sell'

                    step = client.get_instruments_info(category="linear",symbol=symbol)
                    tickSize = float(step['result']['list'][0]['priceFilter']['tickSize'])
                    priceScale = int(step['result']['list'][0]['priceScale'])
                    step_precission = float(step['result']['list'][0]['lotSizeFilter']["qtyStep"])
                    #qty = float(step['result']['list'][0]['lotSizeFilter']["minOrderQty"])
                    precission = step_precission
                    qty = usdt/last_price
                    qty = getUsdtOrderSize(marginPercentage)/last_price
                    qty = qty_precission(qty,precission)
                    if qty.is_integer():
                        qty = int(qty)

                    stop_loss_price = last_price*(1+sl_percent/100) if side == 'Sell' else last_price*(1-sl_percent/100)
                    take_profit_price = last_price*(1-tp_percent/100)  if side == 'Sell' else last_price*(1+tp_percent/100)

                    CreateOrder(symbol,side,'Market',qty,stop_loss_price,take_profit_price)
                    openedPosition = True
                    takeProfit = False
        
        else:
            isEvaluating = False
            print('posición abierta')
            return
        isEvaluating = False
    else:
        print('Evaluando...')

        

    print("Actualización en tiempo real: ")
    print(wsMessage["data"][-1]['p'])


def start_kline_stream():
    ws.kline_stream(
        interval=int(interval),
        symbol=symbol,
        callback=CalculateValues
    )

# Iniciar kline_stream en un hilo normal (no daemon)
kline_thread = threading.Thread(target=start_kline_stream)
kline_thread.start()

ws.trade_stream(
                symbol=symbol,
                callback=ValidateEntry
            )
kline_thread.join()

def enviar_mensaje_telegram(mensaje):
    asyncio.run(SendTelegramMessage(mensaje))



while True:
    # This while loop is required for the program to run. You may execute
    # additional code for your trading logic here.

    try:
        posiciones=client.get_positions(category="linear",symbol=symbol)
        if float(posiciones['result']['list'][0]['size']) != 0:
            print("Hay una posición abierta en: "+symbol)
            openedPosition = True
            if not takeProfit:
                precio_de_entrada = float(posiciones['result']['list'][0]['avgPrice'])
                if posiciones['result']['list'][0]['side'] == 'Buy':
                    stop_loss_price = precio_de_entrada*(1-sl_percent/100)
                    take_profit_price = precio_de_entrada*(1+tp_percent/100)
                    #establecer_stop_loss(symbol=symbol,sl=stop_loss_price,side="Buy")
                    #SetTakeprofit(symbol,take_profit_price,"Sell",qty,priceScale,tickSize)
                    print("Take profit activado")
                    takeProfit = True
                else:
                    stop_loss_price = precio_de_entrada*(1+sl_percent/100)
                    take_profit_price = precio_de_entrada*(1-tp_percent/100)
                    #establecer_stop_loss(symbol=symbol,sl=stop_loss_price,side="Sell")
                    #SetTakeprofit(symbol,take_profit_price,"Buy",qty,priceScale,tickSize)
                    print("Take profit activado")
                    takeProfit = True
       
        
        else:
            openedPosition = False
            

    except Exception as e:
        print(f"Error en el bot: {e}")
        mensaje = f"Reiniciar bot: {e}. "
        threading.Thread(target=enviar_mensaje_telegram, args=(mensaje,)).start()
        time.sleep(60)

    time.sleep(1)
