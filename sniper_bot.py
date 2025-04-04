import datetime
from pybit.unified_trading import WebSocket, HTTP
import time
import statistics
from config import (bybit_api_key,bybit_secret_key)
# Configuración
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key
SYMBOL = "ALCHUSDT"
MULTIPLICADOR = 10  # Factor por el cual el trade debe ser mayor al promedio
ORDER_QTY = 100  # Cantidad fija para prueba
TRADE_HISTORY = 30  # Número de trades recientes a considerar

# Conexión HTTP y WebSocket
session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
ws = WebSocket(testnet=False, api_key=API_KEY, api_secret=API_SECRET,channel_type="linear")

# Almacén de tamaños de órdenes recientes
trade_sizes = []

# Función para obtener el precio actual
def get_current_price():
    response = session.get_ticker(category="linear", symbol=SYMBOL)
    return float(response['result']['list'][0]['lastPrice'])

# Función para monitorear el Trade Stream
def handle_tradestream(message):
    try:
        #print(message)
        global trade_sizes
        if 'data' not in message:
            return
        
        for trade in message['data']:
            size = float(trade['v'])
            side = trade['S']  # 'Buy' o 'Sell'
            
            # Almacenar el tamaño de la transacción
            trade_sizes.append(size)
            if len(trade_sizes) > TRADE_HISTORY:
                trade_sizes.pop(0)
            
                # Calcular el tamaño promedio de las últimas operaciones
                avg_size = statistics.mean(trade_sizes) if trade_sizes else 1
                
                # Si la orden es al menos 'MULTIPLICADOR' veces mayor que el promedio, ejecutamos un trade
                #if size >= avg_size * MULTIPLICADOR:
                if size >=100000:
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] Trade grande detectado: {side} {size}, ejecutando trade")
                    #place_order(side)
    except Exception as e:
        print(f'Error: {e}')

# Función para ejecutar la orden
def place_order(side):
    order_side = "Buy" if side == "Buy" else "Sell"
    
    response = session.place_order(
        category="linear",
        symbol=SYMBOL,
        side=order_side,
        orderType="Market",
        qty=ORDER_QTY
    )
    print(f"Orden ejecutada: {response}")

# Suscribirse al Trade Stream
ws.trade_stream(symbol=SYMBOL, callback=handle_tradestream)

print("Bot Sniper de Liquidez basado en Trade Stream corriendo...")
while True:
    time.sleep(1)
