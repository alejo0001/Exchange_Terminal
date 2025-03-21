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

symbol='VIDTUSDT'
interval='1'
fastWindow = 10
slowWindow = 200

currentMAValue = 0
currentSlowMAValue = 0
avgDistanceFromMA =1 #%
distanceMultiplier = 1 #%
openedPosition = False


tp_percent = 1
sl_percent = 1
tickSize = 0
priceScale = 0
qty = 0

takeProfit = False
isEvaluating = False
usdt = 6
marginPercentage = 25 #porcentaje a utilizar para entrar en las operaciones
useSlowMA = True

mode = 0 #0 ambas, 1 long, 2 short
# Variables para monitorear el estado de los websockets
last_kline_time = time.time()
last_ticker_time = time.time()

ws = WebSocket(
    testnet=False,
    channel_type="linear",
)


client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)

def CalculateValues(wsMessage):
    global currentMAValue
    global currentSlowMAValue
    global symbol
    global useSlowMA

    if(wsMessage['data'][0]['confirm']== True):
        # posiciones=client.get_positions(category="linear",symbol=symbol)
        # if float(posiciones['result']['list'][0]['size']) == 0:
        #     on_message(message)

        data= obtener_datos_historicos(symbol,interval)
        if(useSlowMA == True):
            currentSlowMAValue = CalculateMovingAverage(data,slowWindow)['MA']
        data = CalculateMovingAverage(data,fastWindow)
        currentMAValue = data['MA']
        print("Actualización de valores: ")
        print(wsMessage)

def ValidateEntry(wsMessage):

    global currentMAValue
    global currentSlowMAValue
    global useSlowMA
    global symbol
    global openedPosition
    global tickSize
    global priceScale
    global qty
    global takeProfit 
    global isEvaluating
    global marginPercentage
    global mode

    if(not isEvaluating):
        isEvaluating = True
        if(not openedPosition):
            posiciones=client.get_positions(category="linear",symbol=symbol)
            if float(posiciones['result']['list'][0]['size']) != 0:
                isEvaluating = False
                openedPosition = True
                print('posición abierta...')
                return
            #last_trade = wsMessage["data"][-1]
            last_trade = wsMessage["data"]
            #last_price = float(last_trade['p'])
            last_price = float(last_trade['lastPrice'])
            if(currentMAValue > 0 ):
                percentageDistance = abs(calculateRelativePercentageDiff(currentMAValue,last_price))

                entryCondition = False

                if(useSlowMA == True):
                    entryCondition = percentageDistance >= (avgDistanceFromMA*distanceMultiplier) and ((last_price > currentMAValue and last_price < currentSlowMAValue) or (last_price < currentMAValue and last_price > currentSlowMAValue))
                else:
                    entryCondition = percentageDistance >= (avgDistanceFromMA*distanceMultiplier)

                if(entryCondition == True):
                    side = 'Buy' if currentMAValue > last_price else 'Sell'

                    response = client.get_tickers(category="linear", symbol=symbol)

                    # Extraer el funding rate
                    funding_rate = float(response["result"]["list"][0]["fundingRate"])

                    if funding_rate >= 0.1:
                        mode = 2
                    elif funding_rate >= -0.1:
                        mode = 1


                    if(side == 'Buy' and (mode == 0  or mode == 1)) or (side == 'Sell' and (mode == 0  or mode == 2)):

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

        

    print("Actualización en tiempo real: ", wsMessage["data"]['lastPrice'])
    #print(wsMessage["data"][-1]['p'])
    


# def start_kline_stream():
#     ws.kline_stream(
#         interval=int(interval),
#         symbol=symbol,
#         callback=CalculateValues
#     )

# # Iniciar kline_stream en un hilo normal (no daemon)
# kline_thread = threading.Thread(target=start_kline_stream)
# kline_thread.start()

# ws.ticker_stream(
#                 symbol=symbol,
#                 callback=ValidateEntry
#             )
# kline_thread.join()

def enviar_mensaje_telegram(mensaje):
    asyncio.run(SendTelegramMessage(mensaje))


# Función para iniciar WebSocket de Kline
def start_kline_ws():
    global ws_kline
    while True:
        try:
            print("Conectando WebSocket de Kline...")
            ws_kline = WebSocket(testnet=False, channel_type="linear")

            ws_kline.kline_stream(
                interval=int(interval),
                symbol=symbol,
                callback=CalculateValues
            )
            print("WebSocket de Kline conectado.")
            break  # Salir del bucle si la conexión es exitosa

        except Exception as e:
            print(f"Error en WebSocket de Kline: {e}")
            time.sleep(5)  # Esperar antes de reintentar

# Función para iniciar WebSocket de Ticker
def start_ticker_ws():
    global ws_ticker
    while True:
        try:
            print("Conectando WebSocket de Ticker...")
            ws_ticker = WebSocket(testnet=False, channel_type="linear")

            ws_ticker.ticker_stream(
                symbol=symbol,
                callback=ValidateEntry
            )
            print("WebSocket de Ticker conectado.")
            break  # Salir del bucle si la conexión es exitosa

        except Exception as e:
            print(f"Error en WebSocket de Ticker: {e}")
            time.sleep(5)  # Esperar antes de reintentar

# Función para monitorear desconexiones
def monitor_websockets():
    global last_kline_time, last_ticker_time
    while True:
        if time.time() - last_kline_time > 120:
            print("Reiniciando WebSocket de Kline...")
            start_kline_ws()

        if time.time() - last_ticker_time > 60:
            print("Reiniciando WebSocket de Ticker...")
            start_ticker_ws()

        time.sleep(5)  # Revisar cada 5 segundos

# Iniciar ambos WebSockets en hilos separados
kline_thread = threading.Thread(target=start_kline_ws)
ticker_thread = threading.Thread(target=start_ticker_ws)
monitor_thread = threading.Thread(target=monitor_websockets, daemon=True)

kline_thread.start()
ticker_thread.start()
monitor_thread.start()

# Esperar a que los hilos terminen
kline_thread.join()
ticker_thread.join()

while True:
    # This while loop is required for the program to run. You may execute
    # additional code for your trading logic here.

    try:
        posiciones=client.get_positions(category="linear",symbol=symbol)
        oP = 0
        for p in posiciones['result']['list']:
            if float(p['size']) != 0:
                oP = oP +1

        if oP > 0:
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
