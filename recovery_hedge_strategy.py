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
from common import (BybitPositionsWSResponseResult, CreateOrder, Order,CandleStick, SetStopLoss, SetTakeprofit, calculateRelativePercentageDiff, getMarginBalance, getUsdtOrderSize, qty_precission, qty_step, safe_float, telegramAPIKey,SendTelegramMessage,obtener_datos_historicos,CalculateMovingAverage)
import ATR
from pybit.unified_trading import (WebSocket,HTTP)

from config import (bybit_api_key,bybit_secret_key)
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR
import websocket


is_updating_orders = False
recoveryMultiplier = 1.5
recoveryPercentageDistance = 0.5
totalMargin = getMarginBalance()
symbol = ''

takeProfit = 2 #%
takeProfitFirstPos = 1
prevBuySize = 0
prevSellSize = 0


ws = WebSocket(
    testnet=False,                # Cambiar a False si usas Mainnet
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
    channel_type="private"       # Tipo de canal: 'private' para datos autenticados
)

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)

def handle_message(message):

    global recoveryMultiplier
    global recoveryPercentageDistance
    global takeProfit
    global totalMargin
    global symbol
    global is_updating_orders
    global prevBuySize 
    global prevSellSize 
    global takeProfitFirstPos

    try:       

    # Si hay un ciclo for cancelando o colocando órdenes, no procesar el mensaje.
        if is_updating_orders:
            print("Actualización en progreso. Mensaje ignorado.")
            return
        
        print ('raw positions: ',str(message))

        positions = BybitPositionsWSResponseResult.from_dict(message)
        #print(str(positions))
        symbol =  positions.data[0].symbol

        step = session.get_instruments_info(category="linear",symbol=symbol)
        tickSize = float(step['result']['list'][0]['priceFilter']['tickSize'])
        priceScale = int(step['result']['list'][0]['priceScale'])
        step_precission = float(step['result']['list'][0]['lotSizeFilter']["qtyStep"])        
        
        if(len(positions.data)>1):
            changes = False

            print('prevSellSize: ')
            print(prevSellSize)
            print('prevBuySize: ')
            print(prevBuySize)

            if(positions.data[0].side == 'Buy'):
                if(safe_float(positions.data[0].size) > prevBuySize):
                    prevBuySize = safe_float(positions.data[0].size)
                    changes = True
            elif(positions.data[0].side == 'Sell'):
                if(safe_float(positions.data[0].size) > prevSellSize):
                    prevSellSize = safe_float(positions.data[0].size)
                    changes = True
            if(positions.data[1].side == 'Buy'):
                if(safe_float(positions.data[1].size) > prevBuySize):
                    prevBuySize = safe_float(positions.data[1].size)
                    changes = True
            elif(positions.data[1].side == 'Sell'):
                if(safe_float(positions.data[1].size) > prevSellSize):
                    prevSellSize = safe_float(positions.data[1].size)
                    changes = True
            elif(safe_float(positions.data[0].size) == 0 and safe_float(positions.data[1].size) == 0 and (prevBuySize > 0 or prevSellSize > 0)):
                    prevSellSize = safe_float(positions.data[0].size) if positions.data[0].positionIdx == 2 else safe_float(positions.data[1].size)
                    prevBuySize = safe_float(positions.data[0].size) if positions.data[0].positionIdx == 1 else safe_float(positions.data[1].size)
                    changes = True

            print('NewprevSellSize: ')
            print(prevSellSize)
            print('NewprevBuySize: ')
            print(prevBuySize)
            print('changes: ')
            print(changes)

            if(changes == True):
                if((safe_float(positions.data[0].size) > 0 and safe_float(positions.data[1].size) == 0) or (safe_float(positions.data[0].size) == 0 and safe_float(positions.data[1].size) > 0)):      
                    is_updating_orders = True
                    openedPos = positions.data[0] if safe_float(positions.data[0].size) > 0 else positions.data[1]
                    print('Sólo existe una posición, validando orden de cobertura...')

                    side = openedPos.side
                    recoverySide = 'Sell' if side == 'Buy' else 'Buy'
                    recoveryOrderSide = 1 if side == 'Sell' else 2

                    orders = session.get_open_orders(
                                category="linear",
                                symbol= symbol,
                            )
                            
                    recoveryExists = False       
                    tPExists = False   
                    for o in orders['result']['list']:
                        if(o.get('reduceOnly', False) == False and o.get('triggerDirection')== recoveryOrderSide):
                            recoveryExists = True
                        if(o.get('reduceOnly', False) == True ): 
                            tPExists = True
                    
                    if(not recoveryExists):

                        
                
                        qty = safe_float(openedPos.size) * recoveryMultiplier
                        price = safe_float(openedPos.entryPrice)
                        triggerPrice = price*(1-recoveryPercentageDistance/100) if side == 'Buy' else price*(1+recoveryPercentageDistance/100)
                        recoveryPrice = qty_step(triggerPrice,priceScale,tickSize)
                        
                        recoveryTriggerDirection = 2 if side == 'Buy' else 1
                        recoveryPositionIdx = 2 if side == 'Buy' else 1

                        res = session.place_order(
                                            category="linear",
                                            symbol=symbol,
                                            side=recoverySide,
                                            orderType="Market",
                                            qty=math.ceil(qty),
                                            triggerPrice = recoveryPrice,
                                            triggerDirection =recoveryTriggerDirection,
                                            positionIdx = recoveryPositionIdx
                                        )

                        
                        print('Orden de cobertura creada con éxito.')

                    if(not tPExists):
                        #Crear takeProfit de la posición existente:
                        takeProfitPrice = safe_float(price)*(1+takeProfitFirstPos/100) if side == 'Buy' else safe_float(price)*(1-takeProfitFirstPos/100)
                        tpSide = 'Buy' if side == 'Sell' else 'Sell'
                        SetTakeprofit(symbol,takeProfitPrice,tpSide,safe_float(openedPos.size),priceScale,tickSize)
                    
                elif(safe_float(positions.data[0].size) <= 0 and safe_float(positions.data[1].size) <= 0):
                    is_updating_orders = True
                    print('sin posiciones, validando órdenes abiertas...')
                    orders = session.get_open_orders(
                                category="linear",
                                symbol= symbol,
                            )
                            
                    if(len(orders['result']['list']) >0):
                        print('Cancelando órdenes abiertas...')
                        for o in orders['result']['list']:
                            session.cancel_order(
                                            category="linear",
                                            symbol=o["symbol"],
                                            orderId=o["orderId"]
                                        )
                            
                        print('Órdenes canceladas con éxito.')
                    else:
                        print('no hay órdenes abiertas para cancelar.')

                    totalMargin = getMarginBalance()
                    
                elif(safe_float(positions.data[0].size) == safe_float(positions.data[1].size) and safe_float(positions.data[0].size) > 0 and safe_float(positions.data[1].size) > 0):
                        print('Posiciones igualadas')                
                        is_updating_orders = True
                        orders = session.get_open_orders(
                                    category="linear",
                                    symbol= symbol,
                                )
                            
                        if(len(orders['result']['list']) >0):
                            print('Cancelando órdenes abiertas...')
                            for o in orders['result']['list']:
                                session.cancel_order(
                                                category="linear",
                                                symbol=o["symbol"],
                                                orderId=o["orderId"]
                                            )
                                
                            print('Órdenes canceladas con éxito, gestionar manualmente.')

                else:
                    print('Posiciones desequilibradas, validando órdenes...')
                    is_updating_orders = True
                    orders = session.get_open_orders(
                                category="linear",
                                symbol= symbol,
                            )
                    #mientras existan 5 órdenes abiertas(tp long, tp short, sl long, sl short y orden de cobertura, no hace falta validar nada)
                    if(len(orders['result']['list'])<5):
                        buySide = positions.data[0] if positions.data[0].side == 'Buy' else positions.data[1]
                        sellSide = positions.data[0] if positions.data[0].side == 'Sell' else positions.data[1]
                        biggerSide = 'Buy' if safe_float(buySide.size) > safe_float(sellSide.size) else 'Sell'
                        recoveryOrderSide = 1 if biggerSide == 'Sell' else 2


                        #Validar que la orden recovery exista, de acuerdo a la posición más pequeña:
                        recoveryExists = False
                        longTPExists = False
                        shortTPExists = False
                        longSLExists = False
                        shortSLExists = False
                        longTPOrder = None
                        shortTPOrder = None


                        for o in orders['result']['list']:
                            if(o.get('reduceOnly', False) == False and o.get('triggerDirection')== recoveryOrderSide):                        
                                recoveryExists = True
                                print('Existe orden recovery')
                            if(o.get('reduceOnly', False) == True and o.get('positionIdx')== 1): #1. afecta long
                                longTPExists = True
                                longTPOrder = o
                                print('Existe TP Long')
                            if(o.get('reduceOnly', False) == True and o.get('positionIdx')== 2): #2. afecta short
                                shortTPExists = True
                                shortTPOrder = o
                                print('Existe TP short')
                            if(o.get('reduceOnly', False) == False and o.get('stopOrderType')== "StopLoss" and o.get('positionIdx')== 1):
                                longSLExists = True
                                print('Existe SL Long')
                            if(o.get('reduceOnly', False) == False and o.get('stopOrderType')== "StopLoss" and o.get('positionIdx')== 2):                        
                                shortSLExists = True
                                print('Existe SL short')


                        if not recoveryExists:
                            print('No existe orden recovery')
                            biggerPos = buySide if biggerSide == 'Buy' else sellSide
                            smallerPos = sellSide if biggerSide == 'Buy' else buySide
                            nextRecoveryQty = safe_float(biggerPos.size) * recoveryMultiplier
                            
                            print ('nextRecoveryQty: ')
                            print(nextRecoveryQty)
                            print('totalMargin: ')
                            print(totalMargin)

                            nextRecoveryQtyAvaliable = ((nextRecoveryQty)*safe_float(biggerPos.entryPrice)) <= (totalMargin*10)

                            print('nextRecoveryQtyAvaliable:')
                            print(nextRecoveryQtyAvaliable)

                            qtyR = nextRecoveryQty - safe_float(smallerPos.size) if nextRecoveryQtyAvaliable else safe_float(biggerPos.size) - safe_float(smallerPos.size)
                            price = safe_float(biggerPos.entryPrice)
                            triggerPrice = price*(1-recoveryPercentageDistance/100) if biggerSide == 'Buy' else price*(1+recoveryPercentageDistance/100)
                            recoveryPrice = qty_step(triggerPrice,priceScale,tickSize)
                            recoverySide = 'Sell' if biggerSide == 'Buy' else 'Buy'
                            recoveryTriggerDirection = 2 if biggerSide == 'Buy' else 1
                            recoveryPositionIdx = 2 if biggerSide == 'Buy' else 1

                            res = session.place_order(
                                        category="linear",
                                        symbol=symbol,
                                        side=recoverySide,
                                        orderType="Market",
                                        qty=math.ceil(qtyR),
                                        triggerPrice = recoveryPrice,
                                        triggerDirection =recoveryTriggerDirection,
                                        positionIdx = recoveryPositionIdx
                                    )
                            print('Órden recovery creada con éxito.')

                        #Validar que existan las órdenes de take profit y stop loss:
                        if not longTPExists:
                            print('No existe TP Long')
                            takeProfitPrice = safe_float(buySide.entryPrice)*(1+takeProfit/100)
                            SetTakeprofit(symbol,takeProfitPrice,"Sell",safe_float(buySide.size),priceScale,tickSize)
                            
                            

                        elif safe_float(longTPOrder['qty']) < safe_float(buySide.size):
                            
                            session.cancel_order(
                                        category="linear",
                                        symbol=longTPOrder["symbol"],
                                        orderId=longTPOrder["orderId"]
                                    )
                            
                            takeProfitPrice = safe_float(buySide.entryPrice)*(1+takeProfit/100)
                            SetTakeprofit(symbol,takeProfitPrice,"Sell",safe_float(buySide.size),priceScale,tickSize)

                        if not shortTPExists:
                            print('No existe TP short')
                            takeProfitPrice = safe_float(sellSide.entryPrice)*(1-takeProfit/100)
                            SetTakeprofit(symbol,takeProfitPrice,"Buy",safe_float(sellSide.size),priceScale,tickSize)
                            
                            

                        elif safe_float(shortTPOrder['qty']) < safe_float(sellSide.size):
                            
                            session.cancel_order(
                                        category="linear",
                                        symbol=shortTPOrder["symbol"],
                                        orderId=shortTPOrder["orderId"]
                                    )
                            
                            takeProfitPrice = safe_float(sellSide.entryPrice)*(1-takeProfit/100)
                            SetTakeprofit(symbol,takeProfitPrice,"Buy",safe_float(sellSide.size),priceScale,tickSize)

                        if not longSLExists:
                            print('No existe SL Long')
                            stopLossPrice = safe_float(buySide.entryPrice)*(1-(recoveryPercentageDistance + takeProfit)/100)-tickSize
                            SetStopLoss(symbol,stopLossPrice,"Buy",priceScale,tickSize)
                        if not shortSLExists:
                            print('No existe SL Short')
                            stopLossPrice = safe_float(sellSide.entryPrice)*(1+(recoveryPercentageDistance + takeProfit)/100)+tickSize
                            SetStopLoss(symbol,stopLossPrice,"Sell",priceScale,tickSize)

                        
                            
                            


            is_updating_orders = False
        else:
            print('respuesta: ')

        print(message)
        return
    except websocket._exceptions.WebSocketConnectionClosedException:
        print("Conexión WebSocket cerrada. Reconectando...")
        connect_to_websocket()
    except Exception as e:
        is_updating_orders = False
        print(f"Error procesando mensaje: {e}")
        
def connect_to_websocket():
    # global ws
    # global session
    while True:
        try:

        
            # Suscribirse al canal de posiciones con el callback

            ws.subscribe("position", callback=handle_message)
            print("Conectado al WebSocket.")
            return
                
        except Exception as e:
            print(f"Error conectando al WebSocket: {e}")
            print("Reintentando en 5 segundos...")
            time.sleep(5)

connect_to_websocket()

try:
    print("Escuchando actualizaciones...")
    while True:
        time.sleep(1) 
except KeyboardInterrupt:
    print("Conexión cerrada.")
    time.sleep(60)