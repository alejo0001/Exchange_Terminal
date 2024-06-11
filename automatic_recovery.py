from pybit.unified_trading import (WebSocket,HTTP)
from time import sleep
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
from os import system

ws = WebSocket(
    testnet=True,
    channel_type="private",
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)


stop = False
s = "IDUSDT"
def handle_message(message):
    print(message)
ws.order_stream(callback=handle_message)
while True:

    pos = session.get_open_orders(
        category="linear",
        symbol=s,
    )

    if(len(pos['result']['list']) >0):

        side = pos['result']['list'][0]['side']
        # qty = float(pos['result']['list'][0]['size'])
        # price = float(pos['result']['list'][0]['avgPrice'])
        qty = float(pos['result']['list'][0]['qty'])
        price = float(pos['result']['list'][0]['price'])
        op = ""
        hedge_pos = 0
        trigger_Direction = 0
        position_Idx= 0 ##necesario para identificar el modo cobertura

        if(qty>0):
            

            if(side =="Buy"):
                hedge_pos = round(price - (price * 0.005),4)
                op="Sell"
                trigger_Direction = 2
                position_Idx = 2
            else:
                hedge_pos = round(price + (price * 0.005),4)
                op="Buy"
                trigger_Direction = 1
                position_Idx = 1

            system('cls') 
            print(pos)

            if(stop ==False):
                print(session.place_order(
                category='linear',
                symbol = s,
                orderType = 'Market',
                triggerDirection = trigger_Direction,
                side= op,
                qty= qty *2,
                triggerPrice=hedge_pos,
                positionIdx = position_Idx
                ))

                stop = True

    sleep(1)