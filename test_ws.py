
from pybit.unified_trading import (WebSocket,HTTP)
from time import sleep
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
from os import system

ws = WebSocket(
    testnet=False,
    channel_type="private",
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)
def handle_message(message):
    print(message)

ws.position_stream(callback=handle_message)
while True:
    sleep(1)