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
from common import(coin)


key=""
secret=""

clavecorreo = ""
email = ""

um_futures_client = UMFutures(key=key, secret=secret)

#coins_info = ["BTCUSDT"]
coins_info = []
cs = coin
for m in cs:
    coins_info.append(m.simbolo)


    


coinsCollection = []

def calculate_rsi(prices, n=14):
    list = prices
    list.pop(19)
    list.pop(18)
    list.pop(17)
    list.pop(16)
    list.pop(15)
    list.pop(14)
    deltas = prices.diff()
    seed = deltas[:n+1]
    up = seed[seed>=0].sum()/n
    down = -seed[seed<0].sum()/n
    rs = up/down
    rsi = pd.Series(100 - (100/(1 + rs)), index=prices.index)
    return rsi

def calculate_rsi2(prices, n=14):
    list = prices
    up = []
    down = []
    upsum = 0
    downsum=0
    upavg=0
    downavg=0
    rs = 0
    rsi = 0
    list.pop()
    list.pop()
    list.pop()
    list.pop()
    list.pop()
    list.pop()
    
    for p in list:
        if(float(p[1]) < float(p[4])):
            up.append(float(p[4]))
        else:
            down.append(float(p[4]))
        
    for u in up:
        upsum+=u
    
    for d in down:
        downsum+=d

    upavg = upsum/n
    downavg = downsum/n

    rs = upavg/downavg
    rsi = 100 -(100/(1+rs))
    return [rsi]




# def calculate_rsi(prices, n=14):
#     # 1. Calcula la lista de cambios de precios
#     deltas = []
#     for i in range(1, len(prices)):
#         deltas.append(prices[i] - prices[i-1])

#     # 2. Inicializa las variables de up y down para el primer cálculo de RSI
#     seed_up = 0
#     seed_down = 0
#     for i in range(n):
#         if deltas[i] >= 0:
#             seed_up += deltas[i]
#         else:
#             seed_down += abs(deltas[i])
#     up = seed_up / n
#     down = seed_down / n
#     rs = up / down
#     rsi = 100 - (100 / (1 + rs))
#     return rsi

def calculate_bollinger_bands(prices, window=20, num_std=2):
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()
    upper_band = rolling_mean + (num_std * rolling_std)
    lower_band = rolling_mean - (num_std * rolling_std)
    return rolling_mean, upper_band, lower_band

def SendEmail(coinsCollection=[]):
    yag = yagmail.SMTP(user=email,password=clavecorreo)
    destinatarios = ['alejandroes_92@hotmail.com']
    asunto = 'powerfull pattern'
    mensaje = 'mensaje de prueba'

    if(len(coinsCollection) > 0):
        mensaje = ''
        for c in coinsCollection:
            mensaje += c[0]+': banda superior: '+c[1]+"; banda inferior: "+c[2]+"; rsi: "+c[3]+"; precio de cierre : "+c[4]+'\n'

    yag.send(destinatarios,asunto,mensaje)

  # def calculate_rsi(prices,n=14):
    #     delta = prices.diff()
    #     delta = delta[1:]

    #     up,down = delta.copy(), delta.copy()

    #     up[up<0] = 0
    #     down[down>0]=0

    #     #calculating average up and down
    #     average_up = up.rolling(n).mean()
    #     average_down = down.abs().rolling(n).mean()

    #     #relative strength
    #     rs = average_up/average_down

    #     #index
    #     rsi = 100 -(100/(1+rs))
    #     return rsi

for co in coins_info:
    coin = co
    interval = "15m"

    #candlesticks = um_futures_client.index_price_klines("BTCUSDT", interval, **{"limit": 14})
    #candlesticks = um_futures_client.mark_price_klines("BTCUSDT", interval, **{"limit": 14})
    candlesticks = um_futures_client.klines(coin, interval, **{"limit": 20})

    


    latest_prices = []
    for v in candlesticks:
        latest_prices.append(float(v[4]))

    prices = pd.Series(latest_prices)
    rsi = calculate_rsi(prices)
    # print("intervalo: "+interval)
    # print(rsi[0])

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

    
    #mensaje = coin +": banda superior: "+str(upper_band[len(upper_band)-1])+"; banda inferior: "+str(lower_band[len(lower_band)-1])+"; rsi: "+str(rsi[0])+"; precio de cierre : "+str(latest_prices[-1])
    if(((latest_prices[-1]> upper_band[len(upper_band)-1] ) & (rsi[0] >=80)) | ((latest_prices[-1]< lower_band[len(lower_band)-1] ) & (rsi[0] <=20))):
        #print("patrón poderoso: "+mensaje)
        #SendEmail()
        coinsCollection.append([coin,str(upper_band[len(upper_band)-1]),str(lower_band[len(lower_band)-1]),str(rsi[0]),str(latest_prices[-1])])
    else:
        print("sin patrón poderoso: "+coin+": banda superior: "+str(upper_band[len(upper_band)-1])+"; banda inferior: "+str(lower_band[len(lower_band)-1])+"; rsi: "+str(rsi[0])+"; precio de cierre : "+str(latest_prices[-1]))
        #print('rsi: '+str(rsi[0])+'lateest pricces:'+str(latest_prices))
        #SendEmail()
        #coinsCollection.append([coin,str(upper_band[len(upper_band)-1]),str(lower_band[len(lower_band)-1]),str(rsi[0]),str(latest_prices[-1])])

print('\n')

if(len(coinsCollection) > 0):
    SendEmail(coinsCollection)

    





















