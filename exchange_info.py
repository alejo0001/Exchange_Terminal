import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
import math
from config import (binance_api_key,binance_secret_key)




key=binance_api_key
secret=binance_secret_key

um_futures_client = UMFutures(key=key, secret=secret)

def get_precision_info(symbol='BTCUSDT'):
    info = um_futures_client.exchange_info()
    price_precision = 0
    for s in info['symbols']:
        if(symbol == s['symbol']):
            price_precision = int(s['quantityPrecision'])
    return price_precision

def get_min_value_info(symbol='BTCUSDT'):
    info = um_futures_client.exchange_info()
    price= float(um_futures_client.mark_price(symbol)['indexPrice'])
    min_price = 0
    precision = get_precision_info(symbol)
    for s in info['symbols']:
        if(symbol == s['symbol']):          
            notional = float(s['filters'][5]['notional'])
            factor = float(s['filters'][1]['minQty'])
            num1 = notional/price
            num1_rounded = math.ceil(num1 / factor) * factor
            min_price = round(num1_rounded,precision)
            #print(num1_rounded)
    return min_price

def get_max_leverage(symbol='BTCUSDT'):
    response = um_futures_client.get_position_risk(recvWindow=6000)
    
    leverage=0
    for c in response:
        if(c['symbol'] == symbol):
            leverage = int(c['leverage'])
    return leverage