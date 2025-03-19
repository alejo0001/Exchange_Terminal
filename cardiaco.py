from pybit.unified_trading import WebSocket, HTTP
import time
from config import(bybit_api_key,bybit_secret_key)
import math
# Configuración de la API
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key
SYMBOL = ""
MAX_RECOMPRAS = 6
DISTANCIA_RECOMPRA = 0.03  # 1% de distancia
MULTIPLICADOR = 1
RIESGO_CUENTA = 0.3  # 0.02 = 2% de la cuenta
TAKE_PROFIT_DISTANCIA = 0.01  # 2% desde la posición actual
PRECISION_ROUND = 4

is_updating_orders = False

# Conectar a Bybit
http = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
ws = WebSocket(testnet=False,channel_type="private", api_key=API_KEY, api_secret=API_SECRET)

# Obtener saldo de la cuenta
def obtener_saldo():
    saldo = http.get_wallet_balance(accountType="UNIFIED",coin = "USDT")
    return float(saldo['result']['list'][0]['totalEquity'])

# Calcular el stop loss en base al riesgo
def calcular_stop_loss(entry_price, position_size,side):
    global RIESGO_CUENTA
    global PRECISION_ROUND
    saldo = obtener_saldo()
    riesgo_maximo = saldo * RIESGO_CUENTA
    stop_loss = math.abs(entry_price - (riesgo_maximo / (position_size*entry_price))) if side == "Buy" else math.abs(entry_price + (riesgo_maximo / (position_size*entry_price)))
    print('stopLoss: ',round(stop_loss, PRECISION_ROUND))
    return round(stop_loss, PRECISION_ROUND)

# Manejo de posiciones abiertas
def manejar_posicion(msg):
    print('llega: ',msg)
    global SYMBOL
    global PRECISION_ROUND
    global MULTIPLICADOR
    global MAX_RECOMPRAS
    global DISTANCIA_RECOMPRA
    global TAKE_PROFIT_DISTANCIA
    global is_updating_orders

    if is_updating_orders:
        print("Actualización en progreso. Mensaje ignorado.")
        return
    
    is_updating_orders = True

    if 'data' in msg:
        cantPos = True
        print('msg: ',msg)

        if msg['data'][0]["symbol"] == 'PROSUSDT':
            return
        if(len(msg['data'])> 1):
            
            if float(msg['data'][0]["size"]) == 0 and  float(msg['data'][1]["size"]) ==0:
                cantPos = False                

        else:
            float(msg['data'][0]["size"]) == 0
            cantPos = False

        if cantPos == False:
            print('sin posiciones abiertas, validando órdenes pendientes...')
            ordenes = http.get_open_orders(category="linear", symbol=SYMBOL)
            if len(ordenes) > 0:
                for o in ordenes['result']['list']:
                    http.cancel_order(
                                category="linear",
                                symbol=o["symbol"],
                                orderId=o["orderId"]
                            )
                print('órdenes canceladas con éxito')

            is_updating_orders=False            
            return

        for pos in msg['data']:
            SYMBOL =  pos['symbol']
            if float(pos['size']) > 0:
                print('posición: ',pos)
                position_size = float(pos['size'])
                entry_price = float(pos['entryPrice'])
                side = pos['side']
                position_idx = pos['positionIdx']
                
                # Validar órdenes abiertas
                ordenes = http.get_open_orders(category="linear", symbol=SYMBOL)
                ordenes_abiertas = [o for o in ordenes['result']['list'] if o['side'] == side]
                
                if not ordenes_abiertas:
                    # Crear órdenes de recompra
                    for i in range(MAX_RECOMPRAS):
                        tamaño_recompra = position_size * (MULTIPLICADOR ** i) if i > 0 else position_size 
                        precio_recompra = entry_price * (1 - DISTANCIA_RECOMPRA * (i + 1)) if side == "Buy" else entry_price * (1 + DISTANCIA_RECOMPRA * (i + 1))
                        
                        http.place_order(
                            category="linear",
                            symbol=SYMBOL,
                            side=side,
                            orderType="Limit",
                            qty=math.ceil(tamaño_recompra),
                            price=round(precio_recompra, PRECISION_ROUND),
                            positionIdx=int(position_idx),
                            reduceOnly=False,
                            closeOnTrigger=False
                        )
                
                # Calcular y actualizar stop loss
                stop_loss = calcular_stop_loss(entry_price, position_size,side)
                print('stop Loss: ',str(stop_loss))
                http.set_trading_stop(
                    category="linear",
                    symbol=SYMBOL,
                    side=side,
                    stopLoss=stop_loss,
                    position_idx = int(position_idx) 
                )
                

                # Configurar Take Profit
                
                if ordenes_abiertas:
                    tp_orders = [order for order in ordenes if order["reduceOnly"] == True and order["side"] != side]

                    if tp_orders:
                        print('cancelando órdenes TP...')
                        for order in tp_orders:
                            http.cancel_order(symbol=SYMBOL, order_id=order["order_id"])
                        print('órdenes TP canceladas con éxito')
                take_profit = entry_price * (1 + TAKE_PROFIT_DISTANCIA) if side == "Buy" else entry_price * (1 - TAKE_PROFIT_DISTANCIA)
                print ('takeProfit: ',take_profit)
                print('entry_price: ',entry_price)
                print('side: ',side)
                # 4️⃣ Crear nueva orden límite para el TP
                http.place_order(
                    symbol=SYMBOL,
                    side="Sell" if side == "Buy" else "Buy",  # Si estamos en Long, el TP es una venta; en Short, una compra
                    order_type="Limit",
                    qty=position_size,  # Tamaño actualizado
                    price=round(take_profit,PRECISION_ROUND),  # Precio de TP calculado
                    #time_in_force="GoodTillCancel",
                    reduce_only=True,  # Asegura que solo cierre la posición
                    position_idx=int(position_idx)  # Para modo cobertura
                )
              
                # 
                # http.set_trading_stop(
                #     category="linear",
                #     symbol=SYMBOL,
                #     side=side,
                #     takeProfit=round(take_profit, 2)
                # )
            
            #elif pos['symbol'] == SYMBOL and float(pos['size']) == 0:
                # Cancelar órdenes pendientes
                #http.cancel_all_orders(category="linear", symbol=SYMBOL)
    else:
        print('sin información: ',msg)
    is_updating_orders = False

# Suscribirse al stream de posiciones
#ws.position_stream(callback=manejar_posicion)
try:

    
    # Suscribirse al canal de posiciones con el callback

    ws.subscribe("position", callback=manejar_posicion)
    print("Conectado al WebSocket.")
        
            
except Exception as e:
    print(f"Error conectando al WebSocket: {e}")

# Mantener la conexión abierta
while True:
    time.sleep(1)
