import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import exchange_info
import math
from config import(bybit_api_key,bybit_secret_key)
from pybit.unified_trading import HTTP

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)

#print(session.get_orderbook(category="linear", symbol="BTCUSDT"))

print(session.place_order(
    category="linear",
    symbol="THETAUSDT",
    side="Buy",
    orderType="Limit",
    qty=2,
    price=0.5778,
    isLeverage=1, #necesario para futuros
    positionIdx=1 #necesario para futuros
))



# D:\Apps\Exchange_Terminal\Exchange_Terminal>py pruebas.py
# {'retCode': 0, 'retMsg': 'OK', 'result': {'orderId': 'a6416a18-7f2b-490e-8824-92bcd8a5d51c', 'orderLinkId': ''}, 'retExtInfo': {}, 'time': 1695255288114}
