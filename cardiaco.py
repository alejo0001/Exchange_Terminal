import os
import sys
from pybit.unified_trading import WebSocket, HTTP
import time
from ATR import calculate_ATR
from common import CalculateDistancePercentage, CandleStick, SetHedgeOrder, safe_float
from config import(bybit_api_key,bybit_secret_key)
import math
import threading

lock = threading.Lock()
# Configuración de la API
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key
SYMBOL = "1000PEPEUSDT"
MAX_RECOMPRAS = 3
DISTANCIA_RECOMPRA = 0.01  # 0.01 = 1% de distancia
MULTIPLICADOR = 2
RIESGO_CUENTA = 0.01  # 0.02 = 2% de la cuenta
TAKE_PROFIT_DISTANCIA = 0.01  # 2% desde la posición actual
PRECISION_ROUND = 7
ATR_MULTIPLIER = 2
INTERVAL = 1 #minutos
MIN_PERCENTAGE_DISTANCE = 1 # %

is_updating_orders = False
calculateByATR = True
hedgeInsteadStop = True

# Conectar a Bybit
http = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)
#ws = WebSocket(testnet=False,channel_type="private", api_key=API_KEY, api_secret=API_SECRET)

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
    stop_loss = abs (entry_price * (1- (riesgo_maximo / (position_size*entry_price)))) if side == "Buy" else abs(entry_price * (1 +(riesgo_maximo / (position_size*entry_price))))
    print('stopLoss: ',round(stop_loss, PRECISION_ROUND))
    if stop_loss < 0:
        stop_loss = 0
    return round(stop_loss, PRECISION_ROUND)

# Manejo de posiciones abiertas
def manejar_posicion(msg):
    
    global SYMBOL
    global PRECISION_ROUND
    global MULTIPLICADOR
    global MAX_RECOMPRAS
    global DISTANCIA_RECOMPRA
    global TAKE_PROFIT_DISTANCIA
    global is_updating_orders
    print('is_updating_orders: ',is_updating_orders)
    if not lock.acquire(blocking=False):
        print("Actualización en progreso. Mensaje ignorado.")
        return 
        
    
    try:

        is_updating_orders = True

        if 'data' in msg:
            cantPos = True
            #print('msg: ',msg)

            if msg['data'][0]["symbol"] == 'PROSUSDT':
                return
            if(len(msg['data'])> 1):
                
                if safe_float(msg['data'][0]["size"]) == 0 and  float(msg['data'][1]["size"]) ==0:
                    cantPos = False                

            else:
                safe_float(msg['data'][0]["size"]) == 0
                cantPos = False

            # if cantPos == False:
                        
            #     return

            for pos in msg['data']:
                SYMBOL =  pos['symbol']
                if float(pos['size']) > 0:
                    #print('posición: ',pos)
                    position_size = float(pos['size'])
                    entry_price = float(pos['entryPrice'])
                    side = pos['side']
                    position_idx = pos['positionIdx']
                    
                    # Validar órdenes abiertas
                    
                    ordenes = http.get_open_orders(category="linear", symbol=SYMBOL)
                    posiciones = http.get_positions(category="linear", symbol=SYMBOL)
                    if len(posiciones['result']['list'])>= 2:
                        if float(posiciones['result']['list'][0]['size']) > 0 and float(posiciones['result']['list'][1]['size']) > 0:
                            print(f'cobertura detectada en {SYMBOL}, cancelando órdenes pendientes... ')
                            #print(posiciones['result']['list'])
                            for order in ordenes['result']['list']:                                
                                http.cancel_order(symbol=SYMBOL,category="linear", order_id=order["orderId"])
                            print('órdenes canceladas con éxito, gestionar cobertura manualmente')
                            is_updating_orders = False
                            return
                                        
                    #print('órdenes: ',ordenes)
                    ordenes_abiertas = [o for o in ordenes['result']['list'] if o['side'] == side]

                    # Configurar Take Profit
                    createOrder = True
                    if ordenes:
                        
                        tp_orders = [order for order in ordenes['result']['list'] if order["reduceOnly"] == True and order["side"] != side]
                        #print('tp_orders: ',tp_orders)
                        if tp_orders:
                            print('validando órdenes TP...')
                            for order in tp_orders:
                                if safe_float(order['qty']) != position_size:
                                    http.cancel_order(symbol=SYMBOL,category="linear", order_id=order["orderId"])
                                    print('createOrder: ',createOrder)
                                else:
                                    createOrder = False
                                    print('createOrder2: ',createOrder)
                            print('órdenes TP actualizadas con éxito')
                        
                    if createOrder == True: 
                        take_profit = entry_price * (1 + TAKE_PROFIT_DISTANCIA) if side == "Buy" else entry_price * (1 - TAKE_PROFIT_DISTANCIA)
                        print ('takeProfit: ',take_profit)
                        print('entry_price: ',entry_price)
                        print('side: ',side)
                        # 4️⃣ Crear nueva orden límite para el TP
                        response = http.place_order(
                            category="linear",
                            symbol=SYMBOL,
                            side="Sell" if side == "Buy" else "Buy",  # Si estamos en Long, el TP es una venta; en Short, una compra
                            order_type="Limit",
                            qty=position_size,  # Tamaño actualizado
                            price=round(take_profit,PRECISION_ROUND),  # Precio de TP calculado
                            #time_in_force="GoodTillCancel",
                            reduce_only=True,  # Asegura que solo cierre la posición
                            position_idx=int(position_idx)  # Para modo cobertura
                        )

                        #print('response TP: ',response)

                        # Calcular y actualizar stop loss
                        stop_loss = calcular_stop_loss(entry_price, position_size,side)
                        if stop_loss > 0:
                            if hedgeInsteadStop == False:
                                http.set_trading_stop(
                                    category="linear",
                                    symbol=SYMBOL,
                                    side=side,
                                    stopLoss=stop_loss,
                                    position_idx = int(position_idx) 
                                )
                            else:

                                #Validar si existe ya una cobertura con el tamaño de posición correspondiente:
                                print('Validando orden de cobertura...')
                                hedgeSide = "Sell" if side == "Buy" else "Buy"
                                hedgeOrder = [o for o in ordenes['result']['list'] if o['side'] == hedgeSide]
                                placeHedge = False

                                if not hedgeOrder:
                                    placeHedge = True
                                elif safe_float(hedgeOrder[0]['qty']) != position_size:
                                    http.cancel_order(
                                            category="linear",
                                            symbol=hedgeOrder[0]["symbol"],
                                            orderId=hedgeOrder[0]["orderId"]
                                        )
                                    
                                    placeHedge = True

                                
                                if placeHedge == True:
                                    step = http.get_instruments_info(category="linear",symbol=SYMBOL)
                                    tickSize = float(step['result']['list'][0]['priceFilter']['tickSize'])
                                    price_scale = int(step['result']['list'][0]['priceScale'])

                                    # se evalúa si la orden de cobertura que dentro del rango de las recompras, si es así, se ajusta su valor:
                                    if ordenes_abiertas:
                                        last_DCA_Order = max(ordenes_abiertas, key=lambda x: float(x["price"])) if side == "Sell" else  min(ordenes_abiertas, key=lambda x: float(x["price"]))
                                        if side == "Buy":
                                            if stop_loss > float(last_DCA_Order['price']):
                                                stop_loss = float(last_DCA_Order['price']) * (1 - DISTANCIA_RECOMPRA)
                                        else:
                                            if stop_loss < float(last_DCA_Order['price']):
                                                stop_loss = float(last_DCA_Order['price']) * (1 + DISTANCIA_RECOMPRA)
                                    elif hedgeOrder:
                                        stop_loss = float (hedgeOrder[0]['price'])

                                    SetHedgeOrder(SYMBOL,stop_loss,"Sell" if side == "Buy" else "Buy",position_size,price_scale,tickSize)
                                    print('Orden de cobertura colocada con éxito')
                    
                    
                    if not ordenes_abiertas:
                        print('Sin recompras. Validando orden de cobertura...')
                        hedgeSide = "Sell" if side == "Buy" else "Buy"
                        hedgeOrder = [o for o in ordenes['result']['list'] if o['side'] == hedgeSide]

                        if not hedgeOrder:
                            distancia_Recompra_ATR = 0
                            if calculateByATR : 
                                print('recompras por porcentaje según ATR...')
                                prices = http.get_kline(
                                        category="linear",
                                        symbol=SYMBOL,
                                        interval=str(INTERVAL),
                                        limit = 20
                                    )
                                candlesticksList = []
                                for v in prices['result']['list']:
                                    candleStick = CandleStick()                                    

                                    candleStick.open = float(v[1])
                                    candleStick.high = float(v[2])
                                    candleStick.low = float(v[3])
                                    candleStick.close = float(v[4])
                                    candlesticksList.append(candleStick)
                                    
                                ATR = calculate_ATR(candlesticksList)
                                print(f'ATR: {ATR}...')
                                ATR_price = entry_price - ATR if side == "Buy" else entry_price + ATR
                                ATR_percentage_distance = abs(CalculateDistancePercentage(entry_price,ATR_price))/100
                                print(f'Porcentaje ATR: {ATR_percentage_distance}...')
                                if ATR_percentage_distance < MIN_PERCENTAGE_DISTANCE:
                                    ATR_percentage_distance = 1

                                distancia_Recompra_ATR = (ATR_percentage_distance * ATR_MULTIPLIER)/100

                            else:
                                print(f'recompras por porcentaje Fijo({DISTANCIA_RECOMPRA}%)...')
                            # Crear órdenes de recompra
                            for i in range(MAX_RECOMPRAS):
                                tamaño_recompra = position_size * (MULTIPLICADOR ** i) if i > 0 else position_size 
                                precio_recompra = 0

                                if calculateByATR == False:

                                    precio_recompra = entry_price * (1 - DISTANCIA_RECOMPRA * (i + 1)) if side == "Buy" else entry_price * (1 + DISTANCIA_RECOMPRA * (i + 1))
                                else:                               
                                    precio_recompra = entry_price * (1 - distancia_Recompra_ATR * (i + 1)) if side == "Buy" else entry_price * (1 + distancia_Recompra_ATR * (i + 1))
                                
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
                                ##time.sleep(0.5)  # Pausa entre órdenes para evitar saturación
                        else:
                            print('existe orden de cobertura, no se colocan mas recompras...')
                            is_updating_orders = False
                            return
                else:
                    posiciones=http.get_positions(category="linear",symbol=SYMBOL)
                    oP = 0
                    for p in posiciones['result']['list']:
                        if safe_float(p['size']) != 0:
                            oP = oP +1

                    if oP == 0:
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

                        
                    

            #time.sleep(5) #evitar que las ordenes recién colocadas/canceladas 
                            #vuelvan a llamar al método causando un bucle
            is_updating_orders = False
        else:
            print('sin información: ',msg)
        is_updating_orders = False
    except Exception as e:
        is_updating_orders = False
        print(f"Error en el bot: {e}")
    finally:
        lock.release()  # Liberar el lock al finalizar
        
def restart_script():
    print("Reiniciando el script automáticamente...")
    python = sys.executable
    os.execv(python, [python] + sys.argv)
# Suscribirse al stream de posiciones
def iniciar_websocket():
    global ws
    while True:
        try:
            print("Conectando al WebSocket...")
            ws = WebSocket(testnet=False, channel_type="private", api_key=API_KEY, api_secret=API_SECRET)
            ws.subscribe("position", callback=manejar_posicion)
            print("WebSocket conectado con éxito.")
            
            while True:
                time.sleep(1)  # Mantener el WebSocket vivo
            
        except Exception as e:
            print(f"⚠️ Error en WebSocket: {e}")
            print("Reiniciando script...")
            restart_script()
            time.sleep(60)  # Espera 1 minuto antes de reconectar

# 🔥 Iniciar WebSocket en un hilo separado
threading.Thread(target=iniciar_websocket, daemon=True).start()
            


# Mantener la conexión abierta
while True:
    time.sleep(1)
