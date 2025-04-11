import math
import threading
import queue
import time
from pybit.unified_trading import WebSocket, HTTP
from datetime import datetime
from config import bybit_api_key, bybit_secret_key
import websocket

# Configuración general
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key
SYMBOL = "VINEUSDT"

INTERVAL = 1  # Minuto
test = False  # Modo prueba
position_queue = queue.Queue()
lock = threading.Lock()

# Cliente HTTP y WebSocket
session = HTTP(api_key=API_KEY, api_secret=API_SECRET)
ws = WebSocket(testnet=False,
                api_key=bybit_api_key,
                api_secret=bybit_secret_key,
                channel_type="private"    )   # Tipo de canal: 'private' para datos autenticados)

def get_account_balance():
    balance_info = session.get_wallet_balance(accountType="UNIFIED")
    usdt_balance = float(balance_info['result']['list'][0]['totalEquity'])
    return usdt_balance

def get_last_candle(symbol, interval):
    klines = session.get_kline(
        category="linear",
        symbol=symbol,
        interval=str(interval),
        limit=1
    )
    last = klines['result']['list'][0]
    return float(last[1]), float(last[4])  # open, close

def get_open_positions(symbol):
    response = session.get_positions(category="linear", symbol=symbol)
    positions = [pos for pos in response['result']['list'] if float(pos['size']) > 0]
    return positions

def place_order(symbol, side, qty, positionIdx):
    if test:
        print(f"[TEST] Colocando orden: {side}, cantidad: {qty}, símbolo: {symbol}")
    else:
        session.place_order(
            category="linear",
            symbol=symbol,
            side=side,
            order_type="Market",
            qty=qty,
            position_idx=positionIdx
        )

def handle_event(event=None):
    try:
        with lock:
            print(f"[{datetime.now()}] Ejecutando evento del WebSocket...")

            positions = get_open_positions(SYMBOL)

            if not positions:
                balance = get_account_balance()
                order_value = balance * 0.05

                open_price, close_price = get_last_candle(SYMBOL, INTERVAL)
                direction = "Sell" if close_price > open_price else "Buy"
                positionIdx = 1 if direction == "Buy" else 2

                last_price = float(session.get_tickers(category="linear", symbol=SYMBOL)['result']['list'][0]['lastPrice'])
                qty = round(order_value / last_price, 3)  # ajusta según qtyStep de Bybit

                place_order(SYMBOL, direction, math.ceil(qty), positionIdx)
            else:
                for pos in positions:
                    print(f"Posición abierta en: {pos['symbol']}, cantidad: {pos['size']}")

            # Manejar cola de eventos
            while not position_queue.empty():
                _ = position_queue.get()
                print(f"[{datetime.now()}] Procesando evento en cola...")
                handle_event()
    except websocket._exceptions.WebSocketConnectionClosedException:
        print("Conexión WebSocket cerrada. Reconectando...")
        
    except Exception as e:
        
        print(f"Error procesando mensaje: {e}")
def on_position_update(message):
    if not lock.locked():
        handle_event(message)
    else:
        print(f"[{datetime.now()}] Evento en cola.")
        position_queue.put(message)

# Escuchar WebSocket de posiciones
# ws.position_stream(callback=on_position_update)

# # Mantener vivo el script
# print("Bot iniciado. Esperando eventos...")
# while True:
#     time.sleep(1)