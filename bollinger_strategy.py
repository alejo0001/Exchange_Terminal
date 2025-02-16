import asyncio
from pybit.unified_trading import HTTP
import time
import pandas as pd
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR
import math
from common import SendTelegramMessage
from config import (bybit_api_key,bybit_secret_key)
import threading

symbol= "SWARMSUSDT"
timeframe="3"
usdt = 10
marginPercentage = 33 #porcentaje a utilizar para entrar en las operaciones

tp_percent = 2
sl_percent = 1

client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)

#Datos de la moneda, precuio y pasos:
step = client.get_instruments_info(category="linear",symbol=symbol)
ticksize = float(step['result']['list'][0]['priceFilter']['tickSize'])
price_scale = int(step['result']['list'][0]['priceScale'])
step_precission = float(step['result']['list'][0]['lotSizeFilter']["qtyStep"])

def obtener_datos_historicos(symbol,interval,limite=200):
    response= client.get_kline(symbol=symbol,interval=interval,limite=limite)
    if "result" in response:
        data = pd.DataFrame(response['result']['list']).astype(float)
        data[0] = pd.to_datetime(data[0],unit='ms')
        data.set_index(0,inplace=True)
        data= data[::-1].reset_index(drop=True)
        return data
    else:
        raise Exception("Error al obtener datos históricos: "+ str(response))
    
def calcular_bandas_bollinger(data,ventana=20,desviacion=2):
    data['MA'] = data[4].rolling(window=ventana).mean()
    data['UpperBand'] = data['MA'] + (data[4].rolling(window=ventana).std() * desviacion)
    data['LowerBand'] = data['MA'] - (data[4].rolling(window=ventana).std() * desviacion)
    return data.iloc[-1]

def qty_precission(qty,precission):
    qty = math.floor(qty/precission) * precission
    return qty

def qty_step(price):
    precission = Decimal(f"{10** price_scale}")
    tickdec=Decimal(f"{ticksize}")
    precio_final = (Decimal(f"{price}")*precission)/precission
    precide = precio_final.quantize(Decimal(f"{1/precission}"),rounding=ROUND_FLOOR)
    operaciondec=(precide/tickdec).quantize(Decimal('1'),rounding=ROUND_FLOOR)*tickdec
    result = float(operaciondec)

    return result

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
        #stopLoss=stop_loss
        )
    print("orden creada con éxito")

def establecer_stop_loss(symbol,sl,side):
    sl = qty_step(sl)
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    order = client.set_trading_stop(category="linear",symbol=symbol,stopLoss=sl,slTriggerB="LastPrice",positionIdx=pIdx)
    return order

def establecer_take_profit(symbol,tp,side,qty):
    price = qty_step(tp)
    pIdx = 0
    if side == "Sell":
        pIdx=1
    else:
        pIdx=2
    order=client.place_order(category="linear",symbol=symbol,side=side,orderType="Limit",reduceOnly=True,qty=qty,price=price,positionIdx=pIdx)
    return order

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

def enviar_mensaje_telegram(mensaje):
    asyncio.run(SendTelegramMessage(mensaje))

stop = False
tipo='long'
qty=0

while True:
    try:
        posiciones=client.get_positions(category="linear",symbol=symbol)
        if float(posiciones['result']['list'][0]['size']) != 0:
            print("Hay una posición abierta en: "+symbol)
            if not stop:
                precio_de_entrada = float(posiciones['result']['list'][0]['avgPrice'])
                if posiciones['result']['list'][0]['side'] == 'Buy':
                    stop_loss_price = precio_de_entrada*(1-sl_percent/100)
                    take_profit_price = precio_de_entrada*(1+tp_percent/100)
                    establecer_stop_loss(symbol=symbol,sl=stop_loss_price,side="Buy")
                    establecer_take_profit(symbol,take_profit_price,"Sell",qty)
                    print("Stop loss y take profit activado")
                    stop = True
                else:
                    stop_loss_price = precio_de_entrada*(1+sl_percent/100)
                    take_profit_price = precio_de_entrada*(1-tp_percent/100)
                    establecer_stop_loss(symbol=symbol,sl=stop_loss_price,side="Sell")
                    establecer_take_profit(symbol,take_profit_price,"Buy",qty)
                    print("Stop loss y take profit activado")
                    stop = True

        else:
            stop = False
            qty= 0
            data= obtener_datos_historicos(symbol,timeframe)
            data = calcular_bandas_bollinger(data)
            precio=client.get_tickers(category="linear", symbol=symbol)
            precio = float(precio['result']['list'][0]['lastPrice'])

            if precio >= data['UpperBand']:
                precission = step_precission
                qty = getUsdtOrderSize(marginPercentage)/precio
                qty = qty_precission(qty,precission)
                if qty.is_integer():
                    qty = int(qty)
                print("Cantidad de monedas: "+str(qty))
                stop_loss_price = precio*(1+sl_percent/100)
                take_profit_price = precio*(1-tp_percent/100)
                if tipo =="long" or tipo == "":
                    crear_orden(symbol,"Sell","Market",qty,stop_loss_price,take_profit_price)
                    tipo = "short"
            
            if precio <=data['LowerBand']:
                precission = step_precission                
                qty = getUsdtOrderSize(marginPercentage)/precio
                qty = qty_precission(qty,precission)
                if qty.is_integer():
                    qty = int(qty)
                print("Cantidad de monedas: "+str(qty))
                stop_loss_price = precio*(1-sl_percent/100)
                take_profit_price = precio*(1+tp_percent/100)
                if tipo =="short" or tipo == "":
                    crear_orden(symbol,"Buy","Market",qty,stop_loss_price,take_profit_price)
                    tipo = "long"
            
    except Exception as e:
        print(f"Error en el bot: {e}")
        mensaje = f"Reiniciar bot: {e}. Última operación: {tipo}"
        threading.Thread(target=enviar_mensaje_telegram, args=(mensaje,)).start()
        #asyncio.run(SendTelegramMessage(mensaje))
        time.sleep(60)