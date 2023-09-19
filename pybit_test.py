"""
To see which WebSocket topics are available, check the Bybit API documentation:
https://bybit-exchange.github.io/docs/v5/websocket/public/orderbook
"""

from time import sleep
import yagmail
# Import WebSocket from the unified_trading module.
from pybit.unified_trading import (WebSocket,HTTP)
from os import system
from common import SendTelegramMessage
# Set up logging (optional)
import logging
logging.basicConfig(filename="pybit.log", level=logging.DEBUG,
                    format="%(asctime)s %(levelname)s %(message)s")

clavecorreo = ""
email = ""
def SendEmail(symbol = 'BTCUSDT',temporality = '15m',message=''):
    yag = yagmail.SMTP(user=email,password=clavecorreo)
    destinatarios = ['']
    asunto = 'posible mecha '+temporality+' '+symbol+': '
    mensaje = message

   
    
    SendTelegramMessage(asunto+'. '+mensaje)
    #yag.send(destinatarios,asunto,mensaje)
    


# Connect with authentication!
# Here, we are connecting to the "linear" WebSocket, which will deliver public
# market data for the linear (USDT) perpetuals.
# The available channel types are, for public market data:
#    inverse – Inverse Contracts;
#    linear  – USDT Perpetual, USDC Contracts;
#    spot    – Spot Trading;
#    option  – USDC Options;
# and for private data:
#    private – Private account data for all markets.

ws = WebSocket(
    testnet=True,
    channel_type="linear",
)

ws_private = WebSocket(
    testnet=False,
    channel_type="private",
    api_key="",
    api_secret=""
)

session = HTTP(
    testnet=False,
    api_key="",
    api_secret="",
)

# Let's fetch the orderbook for BTCUSDT. First, we'll define a function.
# def handle_orderbook(message):
#     # I will be called every time there is new orderbook data!
#     print(message)
#     orderbook_data = message["data"]

# # Now, we can subscribe to the orderbook stream and pass our arguments:
# # our depth, symbol, and callback function.
# ws.orderbook_stream(50, "MATICUSDT", handle_orderbook)


# To subscribe to private data, the process is the same:
def handle_position(message):
    # I will be called every time there is new position data!
    print("posición: ")
    print(message)
    


# ws_private.order_stream(callback=handle_position)
ws_private.position_stream(callback=handle_position)
while True:
       
    pos = session.get_positions(
        category="linear",
        symbol="THETAUSDT",
    )

    pnl1 = float(pos['result']['list'][0]['unrealisedPnl'])
    pnl2 = float(pos['result']['list'][1]['unrealisedPnl'])
    mayor = pnl1
    menor = pnl2
    if(abs(pnl2) > abs(pnl1)):
        mayor = pnl2
        menor = pnl1

    if(float(pos['result']['list'][0]['markPrice']) <= 0.6048):
        SendEmail('THETAUSDT','15m','precio menor a  0.6048')
    if(float(pos['result']['list'][0]['markPrice']) >= 0.6114):
        SendEmail('THETAUSDT','15m','precio mayor a  0.6114')
    system('cls') 
    print(pos)
    print('Pnl menor: '+ str(menor)+'. Pnl Mayor: '+ str(mayor))
    print('porcentaje a quemar: '+ str(round(abs(menor/mayor)*100,2)))
    
    print('dólares a quemar: '+ str(abs(menor/mayor)*float(pos['result']['list'][0]['positionValue'])))
    print('monedas a quemar: '+ str(abs(menor/mayor)*float(pos['result']['list'][0]['size'])))
    # This while loop is required for the program to run. You may execute
    # additional code for your trading logic here.
    sleep(0.5)