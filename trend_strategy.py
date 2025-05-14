from asyncio import sleep
import asyncio
import logging
import math
from typing import List
# from binance.um_futures import UMFutures
# from binance.lib.utils import config_logging
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
from common import (CalculateExponentialMovingAverage, CreateOrder, Order,CandleStick, SetTakeprofit, calculateRelativePercentageDiff, getUsdtOrderSize, is_in_range, qty_precission, telegramAPIKey,SendTelegramMessage,obtener_datos_historicos,CalculateMovingAverage)
# import ATR
from pybit.unified_trading import (WebSocket,HTTP)

from config import (bybit_api_key,bybit_secret_key)
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR
import os
import sys

symbol='1000PEPEUSDT'
interval='1'
fastWindow = 50
slowWindow = 200

currentEMAValue = 0
currentSlowMAValue = 0
avgDistanceFromMA =1 #%
distanceMultiplier = 1 #%
openedPosition = False


tp_percent = 4
sl_percent = 2
tickSize = 0
priceScale = 0
qty = 0

takeProfit = False
isEvaluating = False
usdt = 6
marginPercentage =10 #porcentaje a utilizar para entrar en las operaciones
useSlowMA = True

mode = 0 #0 ambas, 1 long, 2 short
prevPrice = 0
# Variables para monitorear el estado de los websockets
last_kline_time = time.time()
last_ticker_time = time.time()

inRange = False
lastData = []

ws = WebSocket(
    testnet=False,
    channel_type="linear",
)

ws_kline : WebSocket

client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)

def CalculateValues(wsMessage):
    global currentEMAValue
    global currentSlowMAValue
    global symbol
    global useSlowMA
    global inRange
    global lastData

    if(wsMessage['data'][0]['confirm']== True):
        # posiciones=client.get_positions(category="linear",symbol=symbol)
        # if float(posiciones['result']['list'][0]['size']) == 0:
        #     on_message(message)

        data= obtener_datos_historicos(symbol,interval)
        lastData = data[2:]
        print('data histórica:')
        print(lastData)
        data = CalculateExponentialMovingAverage(data,fastWindow)
        currentEMAValue = float(data['EMA'])

      
       
        print("Actualización de valores: ")
        print(wsMessage)

        ValidateEntry({
            "data": {
                "lastPrice": float(wsMessage['data'][0]['close'])
            }
        })

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
    global prevPrice
    global inRange
    global lastData

    if float(wsMessage["data"]['lastPrice']) == prevPrice:
        return
    else:
        prevPrice = float(wsMessage["data"]['lastPrice'])

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
            if(currentEMAValue > 0 ):
                print('EMA: ',currentEMAValue)
                #percentageDistance = abs(calculateRelativePercentageDiff(currentEMAValue,last_price))

                entryCondition = False

                # if(useSlowMA == True):
                #     entryCondition = percentageDistance >= (avgDistanceFromMA*distanceMultiplier) and ((last_price > currentMAValue and last_price < currentSlowMAValue) or (last_price < currentMAValue and last_price > currentSlowMAValue))
                # else:
                #entryCondition = percentageDistance >= (avgDistanceFromMA*distanceMultiplier)

                #if(entryCondition == True):

                if len(lastData) > 0:
                    if is_in_range(lastData,last_price) == True:
                        print("precio en rango, no se opera")
                        isEvaluating = False
                        return
                
                side = 'Buy' if currentEMAValue < last_price else 'Sell'

                response = client.get_tickers(category="linear", symbol=symbol)

                # Extraer el funding rate
                funding_rate = float(response["result"]["list"][0]["fundingRate"])

                # if funding_rate >= 0.1:
                #     mode = 2
                # elif funding_rate >= -0.1:
                #     mode = 1
                # else:
                #     mode = 0


                if(side == 'Buy' and (mode == 0  or mode == 1)) or (side == 'Sell' and (mode == 0  or mode == 2)):

                    step = client.get_instruments_info(category="linear",symbol=symbol)
                    tickSize = float(step['result']['list'][0]['priceFilter']['tickSize'])
                    priceScale = int(step['result']['list'][0]['priceScale'])
                    step_precission = float(step['result']['list'][0]['lotSizeFilter']["qtyStep"])

                    precission = step_precission
                    qty = usdt/last_price
                    qty = getUsdtOrderSize(marginPercentage)/last_price
                    qty = qty_precission(qty,precission)
                    if qty.is_integer():
                        qty = int(qty)

                    stop_loss_price = last_price*(1+sl_percent/100) if side == 'Sell' else last_price*(1-sl_percent/100)
                    take_profit_price = last_price*(1-tp_percent/100)  if side == 'Sell' else last_price*(1+tp_percent/100)
                    print(f'Creando orden...: side={side} currenEMA: {currentEMAValue} lastPrice: {last_price}')
                    CreateOrder(symbol,side,'Market',qty,stop_loss_price,take_profit_price,True,priceScale,tickSize)
                    print('Orden creada con éxito...')
                    openedPosition = True
                    takeProfit = False

            
            isEvaluating = False
        else:
            isEvaluating = False
            print('posición abierta')
            return
        isEvaluating = False
    else:
        print('Evaluando...')

        

    print("Actualización en tiempo real: ", wsMessage["data"]['lastPrice'])
    #print(wsMessage["data"][-1]['p'])
    




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
            break  # Salir del bucle si la conexión fue exitosa

        except Exception as e:
            print(f"Error en WebSocket de Kline: {e}")
            print("Reiniciando WebSocket de Kline...")

            try:
                if ws_kline:
                    ws_kline.exit()  # Cierra la conexión si existe
                    print("WebSocket cerrado.")
            except:
                pass  # Ignora errores al cerrar

            time.sleep(5)  # Espera antes de reconectar

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
            print("Reiniciando WebSocket de Ticker...")
            
            time.sleep(5)  # Esperar antes de reintentar
            start_ticker_ws()

# Función para monitorear desconexiones
def monitor_websockets():
    global last_kline_time, last_ticker_time
    while True:
        #if time.time() - last_kline_time > 120:
            # print("Reiniciando WebSocket de Kline...")
            # start_kline_ws()

        #if time.time() - last_ticker_time > 60:
            # print("Reiniciando WebSocket de Ticker...")
            # start_ticker_ws()

        time.sleep(5)  # Revisar cada 5 segundos

# Iniciar ambos WebSockets en hilos separados
kline_thread = threading.Thread(target=start_kline_ws)
# ticker_thread = threading.Thread(target=start_ticker_ws)
# monitor_thread = threading.Thread(target=monitor_websockets, daemon=True)

kline_thread.start()
# ticker_thread.start()
# monitor_thread.start()

# Esperar a que los hilos terminen
kline_thread.join()
#ticker_thread.join()

def restart_script():
    print("Reiniciando el script automáticamente...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)

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
     
       
        
        else:
            openedPosition = False
            

    except Exception as e:
        print(f"Error en el bot: {e}")
        mensaje = f"Reiniciar bot: {e}. "
        threading.Thread(target=enviar_mensaje_telegram, args=(mensaje,)).start()
        restart_script()
            
        time.sleep(60)

    time.sleep(1)
