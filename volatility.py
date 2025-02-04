import logging
from typing import List
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import pandas as pd
import Klines
from common import(BybitKlinesResponse, coins)
import bollinger_bands
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
import numpy as np

key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)#binance


temporality=15

def calculateVolatility(symbol:str='BTCUSDT'):

    bybitKlinesResponse : BybitKlinesResponse = Klines.getBybitKlines(symbol,100,temporality)
    closePrices :List[int] = []
    for kline in bybitKlinesResponse.result.list:
        closePrices.append(float(kline.closePrice))
    # Datos de precios de cierre (últimas 10 velas de 15m)
    #precios = [30000, 30050, 30100, 30070, 30120, 30080, 30060, 30110, 30090, 30130]
    precios = closePrices

    # Crear DataFrame
    df = pd.DataFrame(precios, columns=["close"])

    # Calcular retornos logarítmicos
    df["retornos"] = np.log(df["close"] / df["close"].shift(1))

    # Calcular la volatilidad (desviación estándar de retornos)
    volatilidad = df["retornos"].std()

    # Convertir volatilidad a porcentaje del precio promedio
    precio_promedio = df["close"].mean()
    distancia_promedio = volatilidad * precio_promedio * 1.5  # Factor ajustable (1.5x, 2x, etc.)

    print(f"Volatilidad: {volatilidad:.2%}")
    print(f"Distancia promedio sugerida entre órdenes: {distancia_promedio:.6f}")
    print(round(volatilidad,4))
    return round(volatilidad,4)

#calculateVolatility('USUALUSDT')

def calculateVolatilityFromBB():
    coins_info = []
    for m in coins:
        coins_info.append(m.simbolo)

    for c in coins_info:
        rolling_mean = 0
        upper_band = 0
        lower_band = 0
        candlesticks = um_futures_client.klines(c, "15m", **{"limit": 20})

        latest_prices = []
        for v in candlesticks:
            latest_prices.append(float(v[4]))

        prices = pd.Series(latest_prices)

        rolling_mean, upper_band, lower_band = bollinger_bands.calculate_bollinger_bands(prices)

        bbw = bollinger_bands.calculate_bollinger_bands_with(upper_band,lower_band,rolling_mean)

        if(bbw[len(bbw)-1] >= 0.02):       
            print(c+': '+str(bbw[len(bbw)-1]))
        else:
            print(c+': sin volatilidad')