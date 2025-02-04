from typing import Any, List
import websocket
import json
from binance.um_futures import UMFutures
from common import simpleCandleStick
from config import (binance_api_key,binance_secret_key)
# URL del WebSocket de Binance
socket_url = "wss://stream.binance.com:9443/ws/gusdt@kline_1m"
klinesList : List[simpleCandleStick]=[]


um_futures_client = UMFutures(key=binance_api_key, secret=binance_secret_key)
# Función que se ejecuta al recibir un mensaje desde el WebSocket
def on_message(ws, message):
    data = json.loads(message)
    kline = data['k']  # Datos de la vela (kline)
    
    # Extraer información relevante
    is_candle_closed = kline['x']
    open_price = kline['o']
    close_price = kline['c']
    high_price = kline['h']
    low_price = kline['l']
    
    if is_candle_closed:
        print(f"Candle closed. Open: {open_price}, Close: {close_price}, High: {high_price}, Low: {low_price}")
        #print(kline)

        if len(klinesList) <= 0:
            candlesticks = um_futures_client.klines("gusdt", '1m', **{"limit": 20})
            for c in candlesticks:
                candle : simpleCandleStick = simpleCandleStick(float(c[1]),float(c[4]),float(c[2]),float(c[3]))
                klinesList.append(candle)
            
        else:
            candle : simpleCandleStick = simpleCandleStick(float(open_price),float(close_price),float(high_price),float(low_price))
            del klinesList[0]
            klinesList.append(candle)
    
        for i,c in enumerate(klinesList):

            print(f"vela {str(i+1)}: open={str(c.open)},close={str(c.close)},high={str(c.high)}, low={str(c.low)}")

# Función que se ejecuta al conectar con el WebSocket
def on_open(ws):
    print("WebSocket connected!")

# Función que se ejecuta al cerrarse la conexión del WebSocket
def on_close(ws, close_status_code, close_msg):
    print("WebSocket closed.")

# Función que se ejecuta en caso de error
def on_error(ws, error):
    print(f"Error: {error}")

# Crear la conexión WebSocket
ws = websocket.WebSocketApp(socket_url,
                            on_message=on_message,
                            on_open=on_open,
                            on_close=on_close,
                            on_error=on_error)

# Iniciar la conexión
ws.run_forever()
