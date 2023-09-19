import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from common import(order_book_strategy_coins,Moneda,CoinOrderbookInfo)
import exchange_info

key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)

def make_order(symbol='BTCUSDT',side='SELL',type='LIMIT',quantity = 0,price=0,stopPrice = 0,takeProfitPrice=0,leverage=20):
    try:
        final_quantity = 0
        precision = exchange_info.get_precision_info(symbol)
        final_quantity = round(quantity/price,precision)
  

        response = um_futures_client.new_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            timeInForce="GTC",
            price=price,
            leverage =leverage
        )
     
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def make_position_order(symbol='BTCUSDT',side='SELL',type='LIMIT',quantity = 0,price=0,stopPrice = 0,takeProfitPrice=0,leverage=20):
    try:
        final_quantity = 0
        precision = exchange_info.get_precision_info(symbol)
        final_quantity = round(quantity/price,precision)

        response = um_futures_client.new_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=final_quantity,
            stopPrice=price,
            closePosition =True,
            leverage =leverage
        )
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

#make_order('BTCUSDT','SELL','LIMIT',0.001,28000,28100,27800,50)