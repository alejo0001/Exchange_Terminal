import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import pandas as pd
from common import(coins)
import bollinger_bands


key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)

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