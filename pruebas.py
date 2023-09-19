import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import exchange_info
import math
# from binance.client import Client
# from binance.enums import *
# from binance.exceptions import BinanceAPIException




key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)


# info = um_futures_client.exchange_info()
# print(str(info))
   
try:
    # response = um_futures_client.get_position_risk(recvWindow=6000)
    # for c in response:
    #     if(c['symbol'] == "EOSUSDT"):
    #         print(str(c))
    #         info = um_futures_client.exchange_info()
    #         min_price = 0
    #         for s in info['symbols']:
    #             if('EOSUSDT' == s['symbol']):          
    #                 print (str(s))
            

            #print(exchange_info.get_min_value_info(symbol='MAGICUSDT'))

 

    num1 = 4.201680672268908
    factor = 0.1

    num1_rounded = math.ceil(num1 / factor) * factor

    print(num1_rounded)
 

except ClientError as error:
    logging.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )



# Crea una instancia del cliente con tus credenciales de Binance
# client = Client(api_key, api_secret)

# # Símbolo del par que deseas obtener el apalancamiento
# symbol = "BTCUSDT"

# try:
#     # Obtiene la información de la posición en el par
#     position_info = client.futures_position_information(symbol=symbol)

#     # Encuentra la posición con la información de margen
#     for position in position_info:
#         if position['symbol'] == symbol:
#             margin_info = position['margin']
#             break

#     # Obtiene el apalancamiento máximo
#     leverage = margin_info['leverage']

#     print(f"El apalancamiento máximo para el par {symbol} es de {leverage}")
    
# except BinanceAPIException as e:
#     print(f"Ha ocurrido un error: {e}")
