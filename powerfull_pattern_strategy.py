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
from common import(BybitKlinesResponse, calcular_bandas_bollinger, coins)
import order_book_strategy
import orders
import sys

import exchange_info
import TDB
from common import (Order,CandleStick,telegramAPIKey,SendTelegramMessage,obtener_datos_historicos)
import ATR
from pybit.unified_trading import (WebSocket,HTTP)

from config import (bybit_api_key,bybit_secret_key)
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR

key=""
secret=""

clavecorreo = ""
email = ""

um_futures_client = UMFutures(key=key, secret=secret)

logging.basicConfig(filename='powerfull_pattern.txt', level=logging.ERROR,filemode='a')
sys.stderr = open('error.txt', 'w')

symbol=''
interval='15'
upperRsi = 70
lowerRsi=30
bBPercentageDistance = 3

marginPercentage = 33 #porcentaje a utilizar para entrar en las operaciones
tp_percent = 2
sl_percent = 1

ws = WebSocket(
    testnet=False,
    channel_type="linear",
)

client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)


def crear_orden(symbol,side,order_type,qty,stop_loss,take_profit):
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    response = client.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        order_type=order_type,
        qty=qty,
        timeInForce="GoodTillCancel",
        positionIdx=pIdx,
        #takeProfit=take_profit,
        stopLoss=stop_loss
        )
    print("orden creada con éxito")

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

            
            
            if(((latest_prices[-1]> upper_band[len(upper_band)-1] ) & (rsi[0] >=80)) | ((latest_prices[-1]< lower_band[len(lower_band)-1] ) & (rsi[0] <=20))):
            
                coinsCollection.append([coin,str(upper_band[len(upper_band)-1]),str(lower_band[len(lower_band)-1]),str(rsi[0]),str(latest_prices[-1])])
            else:
                print("sin patrón poderoso: "+coin+": banda superior: "+str(upper_band[len(upper_band)-1])+"; banda inferior: "+str(lower_band[len(lower_band)-1])+"; rsi: "+str(rsi[0])+"; precio de cierre : "+str(latest_prices[-1])+"lista: "+str(latest_prices))
                

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

def qty_step(price):

    step = client.get_instruments_info(category="linear",symbol=symbol)
    ticksize = float(step['result']['list'][0]['priceFilter']['tickSize'])
    price_scale = int(step['result']['list'][0]['priceScale'])
    precission = Decimal(f"{10** price_scale}")
    tickdec=Decimal(f"{ticksize}")
    precio_final = (Decimal(f"{price}")*precission)/precission
    precide = precio_final.quantize(Decimal(f"{1/precission}"),rounding=ROUND_FLOOR)
    operaciondec=(precide/tickdec).quantize(Decimal('1'),rounding=ROUND_FLOOR)*tickdec
    result = float(operaciondec)

    return result

def establecer_take_profit(symbol,tp,side,qty):
    price = qty_step(tp)
    pIdx = 0
    if side == "Sell":
        pIdx=1
    else:
        pIdx=2
    order=client.place_order(category="linear",symbol=symbol,side=side,orderType="Limit",reduceOnly=True,qty=qty,price=price,positionIdx=pIdx)
    return order

def crear_orden(symbol,side,order_type,qty,stop_loss,take_profit):
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    response = client.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        order_type=order_type,
        qty=qty,
        timeInForce="GoodTillCancel",
        positionIdx=pIdx,
        #takeProfit=take_profit,
        stopLoss=stop_loss
        )
    print("orden creada con éxito")

def qty_precission(qty,precission):
    qty = math.floor(qty/precission) * precission
    return qty

def getMarginBalance():
    response = client.get_wallet_balance(accountType="UNIFIED",coin = "USDT")
    if response["retCode"] == 0:
        margin_balance = response["result"]["list"]
    # print("Saldo de margen por moneda:")
    # print(response)
    
    moneda=margin_balance[0]['coin'][0]['coin']
    margenTotal = float(margin_balance[0]['totalEquity'])
    print(f"Moneda: {moneda}, Total: {margenTotal}")
    return margenTotal

def getUsdtOrderSize(marginPercentage=33):
    balance = getMarginBalance()
    orderSize = balance * (marginPercentage/100)
    return round(orderSize)

def on_message(message):
    try:
        global symbol
        global interval
        global upperRsi
        global lowerRsi
        global bBPercentageDistance

        candlesticksDataFrame =  obtener_datos_historicos(symbol,interval)
        data = calcular_bandas_bollinger(candlesticksDataFrame)
        bBKlines : BybitKlinesResponse = getBybitKlines(symbol, 200, int(interval))
        precio = float(message['data'][0]['close'])
        lstLatestPrices = []        

        for v in bBKlines.result.list:            

            lstLatestPrices.append(v.closePrice)

        prices = pd.Series(lstLatestPrices)
        rsi = calculate_rsi(prices)

        step = client.get_instruments_info(category="linear",symbol=symbol)
        ticksize = float(step['result']['list'][0]['priceFilter']['tickSize'])
        price_scale = int(step['result']['list'][0]['priceScale'])
        step_precission = float(step['result']['list'][0]['lotSizeFilter']["qtyStep"])

        currentBBPDistance = (((data['UpperBand'] - data['LowerBand']) / data['MA']) * 100)

        shortCondition = precio >= data['UpperBand'] & (rsi[0] >= upperRsi) & currentBBPDistance >= bBPercentageDistance
        longCondition = precio <= data['LowerBand'] & (rsi[0] <= lowerRsi) & currentBBPDistance >= bBPercentageDistance

        if shortCondition:
            precission = step_precission
            qty = getUsdtOrderSize(marginPercentage)/precio
            qty = qty_precission(qty,precission)
            if qty.is_integer():
                qty = int(qty)
            print("Cantidad de monedas: "+str(qty))
            stop_loss_price = precio*(1+sl_percent/100)
            take_profit_price = precio*(1-tp_percent/100)
            
            crear_orden(symbol,"Sell","Market",qty,stop_loss_price,take_profit_price)
            establecer_take_profit(symbol,take_profit_price,"Buy",qty)

        if longCondition:
            precission = step_precission                
            qty = getUsdtOrderSize(marginPercentage)/precio
            qty = qty_precission(qty,precission)
            if qty.is_integer():
                qty = int(qty)
            print("Cantidad de monedas: "+str(qty))
            stop_loss_price = precio*(1-sl_percent/100)
            take_profit_price = precio*(1+tp_percent/100)
            
            crear_orden(symbol,"Buy","Market",qty,stop_loss_price,take_profit_price)
            establecer_take_profit(symbol,take_profit_price,"Sell",qty)
                
    except Exception as e:
    # Registrar el error
        print("Error onMessage: "+str(e))


def handle_message(message):
    if(message['data'][0]['confirm']== True):
        #on_message(message)
        print(message)

def calculate_powerfull_patternV2(temporality = "1",coinList : List[str]= [],maxRsi=70,minRsi=30,minBBPercentageDistance=3):

    try:
        global symbol
        global interval
        global upperRsi
        global lowerRsi
        global bBPercentageDistance 
        
        interval= temporality
        upperRsi = maxRsi
        lowerRsi = minRsi
        bBPercentageDistance = minBBPercentageDistance

        for co in coinList:
            symbol = co
            
            ws.kline_stream(
                interval=int(temporality),
                symbol=symbol,
                callback=handle_message
            )

        
    except Exception as e:
    # Registrar el error
        print("Error: "+str(e))
        logging.error(str(e)+' '+symbol)


calculate_powerfull_patternV2("1",['SWARMSUSDT'])

















