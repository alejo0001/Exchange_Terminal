from datetime import datetime, timezone
import threading
import queue
import time
from pybit.unified_trading import WebSocket, HTTP
from common import SetHedgeOrder, SetLimitOrder, SetStopLoss, SetTakeprofit, safe_float
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)


# Configuración global
lock = threading.Lock()
event_queue = queue.Queue()
previousentryPrice = None

distanciaTP_SL = 0.01  # Ejemplo: 1%
cantidadOrdenes = 3
porcentajePnL = 5  # Ejemplo: 5%
capital_total = 25  # Debe actualizarse dinámicamente

precission_round = 4
conditionalOrderDistanceMultiplier = 2
SYMBOL ="MOVEUSDT"
# Conexión a Bybit
session = HTTP(testnet= False,api_key=bybit_api_key, api_secret=bybit_secret_key)
ws = WebSocket(testnet=False, channel_type="private",api_key=bybit_api_key, api_secret=bybit_secret_key)

step = session.get_instruments_info(category="linear",symbol=SYMBOL)
tickSize = float(step['result']['list'][0]['priceFilter']['tickSize'])
price_scale = int(step['result']['list'][0]['priceScale'])

def ws_callback(msg):
    """ Manejo de eventos del WebSocket."""
    if lock.locked():
        print('mensaje en cola')
        event_queue.put(msg)
    else:
        print('ejecutando método')
        manage_position(msg)

def manage_position(msg):
    """ Gestión de órdenes y posiciones."""
    try: 
        with lock:
            global previousentryPrice
            
            # Obtener posiciones abiertas
            positions = session.get_positions(category='linear',symbol = SYMBOL)['result']['list']

            position = next((p for p in positions if float(p['size']) > 0), None)
            print('positions: ',positions)
            if position:
                print('pos: ',position)
                if position['symbol'] == 'PROSUSDT':
                    print('no se validará este ticker: ',position['symbol'])
                    return
                entry_price = float(position['avgPrice'])
                previousentryPrice = entry_price
                size = float(position['size'])
                side = position['side']  # "Buy" o "Sell"

                # validar primero, que existan las 4 órdenes correspondientes (Tp, SL, orden limite inferior y superior),  de lo contrario, cancelar y recalcular:
                orders = session.get_open_orders(category='linear',symbol = SYMBOL)['result']['list']

                tp_price = entry_price * (1 + distanciaTP_SL) if side == "Buy" else entry_price * (1 - distanciaTP_SL)
                tp_side = "Sell" if side == "Buy" else "Buy"
                sl_price = safe_float(entry_price)*(1-(distanciaTP_SL))+tickSize if side == "Buy" else safe_float(entry_price)*(1+(distanciaTP_SL))-tickSize
                newPosOrderPrice = safe_float(entry_price)*(1-(distanciaTP_SL)) if side == "Buy" else safe_float(entry_price)*(1+(distanciaTP_SL))
                condOrderPrice = entry_price * (1 + (distanciaTP_SL * conditionalOrderDistanceMultiplier)) if side == "Buy" else entry_price * (1 - (distanciaTP_SL * conditionalOrderDistanceMultiplier))
                if not orders:        
                    print('no hay órdenes, calculando ...')
                    
                    

                    SetTakeprofit(SYMBOL,tp_price,tp_side,float(position['size']),price_scale,tickSize)
                    SetStopLoss(SYMBOL,sl_price,side,price_scale,tickSize)
                    #session.place_order(category='linear', symbol = SYMBOL,side=side, price=newPosOrderPrice, positionIdx = 1 if side == "Buy" else 2,orderType= 'Limit',qty= float(position['size']))
                    SetLimitOrder(SYMBOL,newPosOrderPrice,side,float(position['size']),price_scale,tickSize)
                    SetHedgeOrder(SYMBOL,condOrderPrice,side,float(position['size']),price_scale,tickSize)
                    # Validar TP y SL
                    #validate_tp_sl(position, entry_price, side)
                elif len(orders) < 4:
                    print('hay menos de 4 órdenes, cancelando y recalculando ...')
                    for o in orders:
                        session.cancel_order(
                                        category="linear",
                                        symbol=o["symbol"],
                                        orderId=o["orderId"]
                                    )
                        
                    SetTakeprofit(SYMBOL,tp_price,tp_side,float(position['size']),price_scale,tickSize)
                    SetStopLoss(SYMBOL,sl_price,side,price_scale,tickSize)
                    
                    SetLimitOrder(SYMBOL,newPosOrderPrice,side,float(position['size']),price_scale,tickSize)
                    SetHedgeOrder(SYMBOL,condOrderPrice,side,float(position['size']),price_scale,tickSize)
                # Colocar órdenes de recompra si no existen
                #place_dca_orders(position,entry_price, side)
                
                # Orden condicional a 2 * distanciaTP_SL
                #place_conditional_order(position,entry_price, side)
            else:
                print ('no hay posiciones abiertas')
                # Si no hay posiciones abiertas, validar órdenes límite
                #manage_limit_orders()
            
            # Validar PnL diario
            validate_pnl()
            
            # Procesar eventos en cola
            while not event_queue.empty():
                manage_position(event_queue.get())
    except Exception as e:
        print('Error: ',e)
def validate_tp_sl(position, entry_price, side):
    """ Asegura que la posición tenga TP y SL."""
    print('validando tp-sl...')
    tp_price = round(entry_price * (1 + distanciaTP_SL) if side == "Buy" else entry_price * (1 - distanciaTP_SL),precission_round)
    sl_price = round(entry_price * (1 - distanciaTP_SL) if side == "Buy" else entry_price * (1 + distanciaTP_SL),precission_round)
    
    # Verificar si existen órdenes TP
    orders = session.get_open_orders(category='linear',symbol = SYMBOL)['result']['list']
    has_tp = any(o['reduceOnly'] and float(o['price']) == tp_price for o in orders)
    print('tp_price: ',str(tp_price))
    print('sl_price: ',str(sl_price))
    print('has_tp: ',has_tp)
    if not has_tp:
        session.place_order(category='linear', symbol = SYMBOL,side='Sell' if side == 'Buy' else 'Buy', price=tp_price, reduce_only=True, positionIdx = 1 if side == "Buy" else 2,orderType= 'Limit',qty= float(position['size']))
    
        # Establecer stop loss con "set_trading_stop"
        session.set_trading_stop(category='linear',symbol = SYMBOL, stop_loss=sl_price,slTriggerB="LastPrice",positionIdx = 1 if side =="Buy" else 2)

def place_dca_orders(position,entry_price, side):
    """ Coloca órdenes de recompra si no existen."""
    print('validando órdenes de recompra...')
    orders = session.get_open_orders(category='linear',symbol = SYMBOL)['result']['list']
    dca_prices = [round(entry_price * (1 - distanciaTP_SL * (i + 1)) if side == "Buy" else entry_price * (1 + distanciaTP_SL * (i + 1)),precission_round) for i in range(cantidadOrdenes)]
    
    print('orders: ',orders)
    print('dca_prices: ',str(dca_prices))
    for price in dca_prices:
        if not any(float(o['reduceOnly']) == False for o in orders):
            session.place_order(category='linear',symbol = SYMBOL, side=side, price=price, qty=float(position['size']),positionIdx = 1 if side =="Buy" else 2,orderType= 'Limit')

def place_conditional_order(position,entry_price, side):
    """ Coloca una orden condicional por encima de la posición."""
    print('validando orden condicional...')
    orders = session.get_open_orders(category='linear',symbol=SYMBOL)['result']['list']
    has_cond_pos = any(o['triggerDirection']  == 1 if side == "Buy" else o['triggerDirection']  == 2  for o in orders)
    print('orders: ',orders)
    print('has_cond_pos: ',has_cond_pos)
    if not has_cond_pos: 
        cond_price = round(entry_price * (1 + 2 * distanciaTP_SL) if side == "Buy" else entry_price * (1 - 2 * distanciaTP_SL),precission_round)
        posIdx = 1 if side == "Buy" else 2
        triggerDirection = 1 if side == "Buy" else 2
        session.place_order(category='linear', symbol = SYMBOL, side=side, price=cond_price, qty=float(position['size']), order_type="Market",triggerDirection = triggerDirection, positionIdx = posIdx,orderType= 'Market')

def manage_limit_orders():
    """ Maneja órdenes límite si no hay posiciones abiertas."""
    print('sin posiciones abiertas, validando órdenes límite...')
    orders = session.get_open_orders(category='linear',symbol = SYMBOL)['result']['list']
    price_actual = float(session.get_tickers(category='linear',symbol=SYMBOL)['result']['list'][0]['lastPrice'])
    print('orders: ',orders)
    print('price_actual: ',str(price_actual))
    for order in orders:
        if (abs(price_actual - safe_float(order['price'])) / price_actual) > distanciaTP_SL:
            session.place_order(category='linear',symbol = SYMBOL, side=order['side'], price=order['price'], qty=float(order['qty']),positionIdx = 1 if order['side'] == "Buy" else 2,orderType= 'Limit')

def get_daily_pnl():
    """Obtiene el PnL total de todas las operaciones cerradas hoy."""
    closed_pnl = session.get_closed_pnl(category='linear', symbol=SYMBOL)['result']['list']
    
    pnl_total = 0.0
    for trade in closed_pnl:
        if trade['symbol'] == SYMBOL:
            pnl_total += float(trade['closedPnl'])
        else:
            break  # Detiene la suma al encontrar un símbolo diferente
    
    print(f"PnL total del día en {SYMBOL}: {pnl_total}")
    return pnl_total

def validate_pnl():
    """ Valida si el PnL diario ha superado el límite y cierra todo."""
    print('validando pnl...')
    
    pnl_total = get_daily_pnl()  # Ahora se usa el PnL real del día

    print('pnl_total:', str(pnl_total))
    
    if (pnl_total / capital_total) * 100 >= porcentajePnL:
        positions = session.get_positions(category='linear', symbol=SYMBOL)['result']['list']
        for pos in positions:
            session.place_order(
                category='linear', 
                symbol=SYMBOL, 
                side='Sell' if pos['side'] == 'Buy' else 'Buy', 
                orderType='Market', 
                qty=float(pos['size']), 
                reduceOnly=True, 
                positionIdx=1 if pos['side'] == 'Buy' else 2
            )
        session.cancel_all_orders(category='linear', symbol=SYMBOL)


# Conectar WebSocket
ws.position_stream(ws_callback)


while True:
    time.sleep(1)