import time
from pybit.unified_trading import WebSocket, HTTP
import threading
import queue
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)

# Configuración
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key
SYMBOL = "BTCUSDT"
distanciaTakeProfit = 0.035  # 3%
distanciaProfitNegativo = 0.01  # 1%
orderSize = 0.01  # Tamaño de orden

# Conexión HTTP y WebSocket
session = HTTP(api_key=API_KEY, api_secret=API_SECRET, testnet=False)
ws = WebSocket(api_key=API_KEY, api_secret=API_SECRET, testnet=False)

lock = threading.Lock()
# Cola para eventos en espera
event_queue = queue.Queue()

def get_positions():
    """Obtiene las posiciones abiertas en el símbolo."""
    positions = session.get_positions(category='linear')
    return [p for p in positions["result"]["list"] if p["symbol"] == SYMBOL]

def get_open_orders():
    """Obtiene las órdenes abiertas en el símbolo."""
    orders = session.get_open_orders(category='linear', symbol=SYMBOL)
    return orders["result"]["list"]

def place_order(side, qty, price, positionIdx):
    """Coloca una orden límite con reduceOnly=True."""
    session.place_order(
        category='linear',
        symbol=SYMBOL,
        side=side,
        orderType='Limit',
        qty=qty,
        price=price,
        reduceOnly=True,
        positionIdx=positionIdx
    )

def manage_hedging(event):
    global SYMBOL
    global distanciaTakeProfit 
    global distanciaProfitNegativo 
    global orderSize
    global lock 
    global event_queue 
    
    with lock:
        try:
            positions = get_positions()
            if len(positions) != 2:
                print('menos de dos posiciones')
                return
            
            long_pos = next((p for p in positions if p["side"] == "Buy"), None)
            short_pos = next((p for p in positions if p["side"] == "Sell"), None)
            
            if not long_pos or not short_pos:
                print('no hay posiciones')
                return
            
            long_size = float(long_pos["size"])
            short_size = float(short_pos["size"])
            long_entry = float(long_pos["entryPrice"])
            short_entry = float(short_pos["entryPrice"])
            
            open_orders = get_open_orders()
            reduce_orders_long = sorted([o for o in open_orders if o["reduceOnly"] == True and int(o["positionIdx"]) == 1], key=lambda x: int(x["createdTime"]))
            reduce_orders_short =  sorted([o for o in open_orders if o["reduceOnly"] == True and int(o["positionIdx"]) == 2], key=lambda x: int(x["createdTime"]))
            
            if long_size == short_size:
                print('posiciones iguales')
                # Asegurar que hay TP en ambos lados
                tp_long = long_entry * (1 + distanciaTakeProfit)
                tp_short = short_entry * (1 - distanciaTakeProfit)
                if not reduce_orders_long:
                    place_order("Sell", min(orderSize, long_size), tp_long, 1)
                if not reduce_orders_short:
                    place_order("Buy", min(orderSize, short_size), tp_short, 2)
            else:
                print('posiciones desiguales')
                # Cancelar órdenes incorrectas
                if len(reduce_orders_long) + len(reduce_orders_short) == 1:
                    print('cancelando TP posición más grande')
                    for order in open_orders:
                        if order["reduceOnly"]:
                            session.cancel_order(category='linear', orderId=order["orderId"],symbol = SYMBOL)
                            
                # Identificar el lado más débil y compensar
                if long_size > short_size:
                    print('Long más grande que short')
                    deficit = long_size - short_size
                    weaker_size = short_size
                    stronger_size = long_size
                    weaker_price = short_entry
                    stronger_price = long_entry
                    weaker_side = "Sell"
                    stronger_side = "Buy"
                    positionIdx_weaker = 2
                    positionIdx_stronger = 1
                else:
                    print('short más grande que long')
                    deficit = short_size - long_size
                    weaker_size = long_size
                    stronger_size = short_size
                    weaker_price = long_entry
                    stronger_price = short_entry
                    weaker_side = "Buy"
                    stronger_side = "Sell"
                    positionIdx_weaker = 1
                    positionIdx_stronger = 2
                    
                sum_reduce_weaker = sum(float(o["qty"]) for o in open_orders if o["positionIdx"] == positionIdx_weaker)

                if not sum_reduce_weaker:
                    print('no exiten órdenes que compensen la desigualdad entre las posiciones')
                    sum_reduce_weaker = 0
                
                if sum_reduce_weaker != deficit:
                    print('deficit: ',str(deficit))
                    print('sum_reduce_weaker: ',str(sum_reduce_weaker))
                    lastStrongerSideOrderPrice = float(reduce_orders_short[-1]['price']) if weaker_side == "Buy" else float(reduce_orders_long[-1]['price']) 

                    if sum_reduce_weaker == 0:
                        price_stronger = stronger_price * (1 + (distanciaProfitNegativo+ distancia_porcentaje)) if weaker_side == "Buy" else stronger_price * (1 - (distanciaProfitNegativo+ distancia_porcentaje))
                    else:
                        price_stronger = lastStrongerSideOrderPrice * (1 + distanciaTakeProfit) if weaker_side == "Buy" else lastStrongerSideOrderPrice * (1 - distanciaTakeProfit)
                    place_order(weaker_side, min(orderSize, deficit), price_stronger, positionIdx_stronger)

                else:
                    print('órdenes compensan desigualdad')
                    strongerSideOrders = reduce_orders_long if weaker_side == "Sell" else reduce_orders_short
                    weakerSideOrders = reduce_orders_long if weaker_side == "Buy" else reduce_orders_short

                    s = "Sell" if weaker_side == "Buy" else "Sell"
                    qty = min(orderSize, weaker_size)

                    # Calculamos la distancia porcentual entre las posiciones
                    precio_promedio = (long_entry + short_entry) / 2
                    distancia_porcentaje = (abs(long_entry - short_entry) / precio_promedio) 

                    p = float(strongerSideOrders[-1]['price']) *(1 + (distanciaTakeProfit + distanciaProfitNegativo+ distancia_porcentaje)) if weaker_side == "Buy" else float(strongerSideOrders[-1]['price']) *(1 - (distanciaTakeProfit + distanciaProfitNegativo+ distancia_porcentaje))
                    if weakerSideOrders :
                        print('weakSideOrders: ',str(weakerSideOrders))
                        if len(weakerSideOrders) > 1:
                            for o in weakerSideOrders:

                                session.cancel_order(category='linear', orderId=o["orderId"],symbol = SYMBOL)   

                            place_order(s, qty, p, positionIdx_weaker)
                        
                    else:
                        print('colocando orden TP weakerSide')
                        place_order(s, qty, p, positionIdx_weaker)

                    # Procesar eventos en cola si hay pendientes
            while not event_queue.empty():
                next_event = event_queue.get()
                print(f"Procesando evento en cola: {next_event}")
                manage_hedging(next_event)  # Procesa el siguiente evento en cola
        except Exception as e :
            print("Error en el bot: ")
            print(e)
        # finally:
        #     lock.release()

# Callback del WebSocket
def websocket_callback(event):
    """Maneja eventos entrantes del WebSocket."""
    if lock.locked():
        print("Ejecución en proceso, mensaje en cola")
        event_queue.put(event)  # Agregar evento a la cola si el proceso está en ejecución
        return

    # Procesar inmediatamente si no hay bloqueo
    manage_hedging(event)

# Suscribir al stream de posiciones
ws.position_stream(callback=websocket_callback)


while True:
    time.sleep(1)