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
from mean_reversion_strategy import getMeanReversionAverage
from Klines import getBybitKlines
import order_book_strategy
import orders
import sys

import exchange_info
#import TDB
from common import (CalculateDistancePercentage, CalculateExponentialMovingAverage, CreateOrder, GetConfirmationByEngulfingCandle,  Order,CandleStick, SetTakeprofit,  calculateRelativePercentageDiff, getUsdtOrderSize, is_in_range, qty_precission, telegramAPIKey,SendTelegramMessage,obtener_datos_historicos,CalculateMovingAverage)
# import ATR
from pybit.unified_trading import (WebSocket,HTTP)

from config import (bybit_api_key,bybit_secret_key)
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR
import os
import sys

symbol='WCTUSDT'
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
marginPercentage =5 #porcentaje a utilizar para entrar en las operaciones
useSlowMA = True

mode = 0 #0 ambas, 1 long, 2 short
prevPrice = 0
# Variables para monitorear el estado de los websockets
last_kline_time = time.time()
last_ticker_time = time.time()

inRange = False
lastData = []
trendThreshold = 1 #%
meanReversionThreshold = 5 #%
longReversionThresholdMultiplier = 2 #%
meanReversionAvgShort = 0
meanReversionAvgLong = 0

# ws = WebSocket(
#     testnet=False,
#     channel_type="linear",
# )

ws_kline : WebSocket

client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)



def is_in_trading_zone(data,lastPrice,currentEMAValue):

    global trendThreshold
    global meanReversionThreshold 
    isInTradingZone = False
    tradeSide="Buy"
    tradeType=0 #0 = tendencia, 1= contra tendencia
    

    distanceFromEMA = (abs(lastPrice - currentEMAValue)/currentEMAValue)*100

    if distanceFromEMA < trendThreshold:
        tradeType = 0
        isInTradingZone = True
    elif distanceFromEMA > meanReversionThreshold:
        tradeType = 1
        isInTradingZone = True

    #last_price*(1-tp_percent/100)
    if (currentEMAValue < lastPrice and tradeType == 0) or (currentEMAValue > lastPrice and tradeType == 1):
        tradeSide="Buy"
    else:
        tradeSide = "Sell"

    return isInTradingZone,tradeSide,tradeType

def validateConfirmation(data,lastPrice,side, tradeType,currentEMAValue):
    global trendThreshold 
    global meanReversionThreshold 
    global fastWindow
    global meanReversionAvgShort
    global meanReversionAvgLong

    openPos = False
    if tradeType == 1:
        if side == "Buy":
            meanReversionAvgLong = getMeanReversionAverage(data,side,meanReversionThreshold *longReversionThresholdMultiplier,fastWindow) if meanReversionAvgLong == 0 else meanReversionAvgLong
            if distanceFromEMA >= meanReversionAvgLong:
                openPos = True
        else:
            meanReversionAvgShort = getMeanReversionAverage(data,side,meanReversionThreshold,fastWindow) if meanReversionAvgShort == 0 else meanReversionAvgShort
            if distanceFromEMA >= meanReversionAvgShort:
                openPos = True
        distanceFromEMA = abs(CalculateDistancePercentage(currentEMAValue,lastPrice))
        
    elif tradeType == 0:
        openPos = GetConfirmationByEngulfingCandle(side,data.iloc[-2],data.iloc[-3]) # se toma penúltima y antepenúltima por que "GetKline" siempre retorna hasta la vela actual que aún esta sin cerrar

    return openPos



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

        data= obtener_datos_historicos(symbol,interval,1000)
        
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
                    isInTradingZone, tradeSide, tradeType = is_in_trading_zone(lastData, last_price, currentEMAValue)
                    side = tradeSide
                    if isInTradingZone == True:
                        print(f"precio en zona de trade. trade: {tradeSide}, tipo: {'tendencia' if tradeType == 0 else 'contra tendencia'}. Validando confirmación...")

                        openPos = validateConfirmation(lastData,last_price,tradeSide, tradeType,currentEMAValue)

                        if openPos == True:

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
                                #CreateOrder(symbol,side,'Market',qty,stop_loss_price,take_profit_price,True,priceScale,tickSize)
                                if side == "Sell":
                                    pIdx=2
                                else:
                                    pIdx=1
                                try:

                                    response = client.place_order(
                                        category="linear",
                                        symbol=symbol,
                                        side=side,
                                        order_type='Market',
                                        qty=qty,
                                        timeInForce="GoodTillCancel",
                                        positionIdx=pIdx,
                                    )
                                    print('Orden creada con éxito...')
                                    openedPosition = True
                                    takeProfit = False
                                except Exception as e:
                                    print(f'error al crear orden: {e}. Reiniciando script ...')
                                    restart_script()

            
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

def UpdateMeanReversionValues(callback):
    global meanReversionThreshold 
    global fastWindow
    global meanReversionAvgShort
    global meanReversionAvgLong
    global lastData
    global longReversionThresholdMultiplier
 
    meanReversionAvgLong = getMeanReversionAverage(lastData,"Buy",meanReversionThreshold *longReversionThresholdMultiplier,fastWindow) 
    meanReversionAvgShort = getMeanReversionAverage(lastData,"Sell",meanReversionThreshold,fastWindow)
     
        
   



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
def start_klineValues_ws():
    global ws_klineUpdate
    while True:
        try:
            print("Conectando WebSocket de KlineValues...")
            ws_klineUpdate = WebSocket(testnet=False, channel_type="linear")

            ws_klineUpdate.kline_stream(
                interval=60,
                symbol=symbol,
                callback=UpdateMeanReversionValues
            )
            print("WebSocket de KlineValues conectado.")
            break  # Salir del bucle si la conexión fue exitosa

        except Exception as e:
            print(f"Error en WebSocket de KlineValues: {e}")
            print("Reiniciando WebSocket de KlineValues...")

            try:
                if ws_klineUpdate:
                    ws_klineUpdate.exit()  # Cierra la conexión si existe
                    print("WebSocket cerrado.")
            except:
                pass  # Ignora errores al cerrar

            time.sleep(5)  # Espera antes de reconectar


# Iniciar ambos WebSockets en hilos separados
kline_thread = threading.Thread(target=start_kline_ws)
klineValues_thread = threading.Thread(target=start_klineValues_ws)

kline_thread.start()
klineValues_thread.start()

# Esperar a que los hilos terminen
kline_thread.join()
klineValues_thread.join()

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
