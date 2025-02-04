from typing import List,Tuple
import websocket
import json
import hashlib
import hmac
import time
from volatility import calculateVolatility
from common import  (BybitOrders_Response, BybitOrders_Response_Result_Item,BybitPositionsWSResponseResult, BybitPositionsWSResponseResultItem, SendTelegramMessage)
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
from pybit.unified_trading import (WebSocket,HTTP)
import asyncio
# Credenciales API
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key

discharge_order_percentage_distance = 0.002 ## 0.2%
precision_round = 6
marginMultiplier = 3
orders_per_side = 4
buyback_size = 2 #Tamaño de las recompras, no se recompra la misma cantidad como en un martingala, se recompra el doble

percentage_distance_between_orders = 0.011 ## 1%
is_updating_orders = False


# Configurar conexión al WebSocket
asyncio.run(SendTelegramMessage('Bot iniciado'))
print("Intentando conectar al WebSocket...")
ws = WebSocket(
    testnet=False,                # Cambiar a False si usas Mainnet
    api_key=API_KEY,
    api_secret=API_SECRET,
    channel_type="private"       # Tipo de canal: 'private' para datos autenticados
)

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)


def placeDischargeOrder(biggerSide,biggerSidePrice, orderSize, symbol):
    ##Se configura la nueva orden:
    if(biggerSide =="Buy"):
        discharge_order_pos = round(biggerSidePrice + (biggerSidePrice * discharge_order_percentage_distance),precision_round)
        discharge_order_type="Sell"
        discharge_order_trigger_Direction = 2
        discharge_order_position_Idx = 1
    else:
        discharge_order_pos = round(biggerSidePrice - (biggerSidePrice * discharge_order_percentage_distance),precision_round)
        discharge_order_type="Buy"
        discharge_order_trigger_Direction = 1
        discharge_order_position_Idx = 2

    response = session.place_order(
        category="linear",
        symbol=symbol,
        side=discharge_order_type,
        orderType="Limit",
        qty=round(orderSize,precision_round),
        price = discharge_order_pos,
        positionIdx = discharge_order_position_Idx,
        reduceOnly = True

    )
    print("orden de descarga creada: ")
    print(response)

def closePositions(buySide:BybitPositionsWSResponseResultItem,sellSide:BybitPositionsWSResponseResultItem):
    response = session.place_order(
        category="linear",
        symbol=buySide.symbol,
        side="Sell",
        orderType="Market",
        qty=buySide.size,
        positionIdx = 1,
        reduceOnly = True

    )

    print("posición cerrada: ")
    print(response)

    response = session.place_order(
        category="linear",
        symbol=sellSide.symbol,
        side="Buy",
        orderType="Market",
        qty=sellSide.size,
        positionIdx = 2,
        reduceOnly = True

    )
    
# Callback para manejar los mensajes
def handle_message(message):
    global percentage_distance_between_orders
    global is_updating_orders
    try:
       

    # Si se están colocando órdenes, no procesar el mensaje.
        if is_updating_orders:
            print("Actualización en progreso. Mensaje ignorado.")
            return
        # print("Mensaje recibido:")
        # print(message)
        positions = BybitPositionsWSResponseResult.from_dict(message)

        if(len(positions.data) <2):
            print('Sólo existe una posición, esperando la otra posición para gestionar')
            return

        # validar si juntas posiciones tienen el mismo tamaño:
        size1 = float(positions.data[0].size)
        size2 = float(positions.data[1].size)
        if(size1 != size2):
            print("posiciones desequilibradas en "+str(positions.data[0].symbol))
            #se valida si existe orden de descarga:
            biggerSide = "Buy"
            biggerSidePrice = 0

            if(size1 > size2):
                biggerSide = positions.data[0].side
                biggerSidePrice = float(positions.data[0].entryPrice)
                if((size1/3) > size2):
                    asyncio.run(SendTelegramMessage('más de dos recompras sin descargar en '+str(positions.data[0].symbol)+', revisar'))
            else:
                biggerSide = positions.data[1].side
                biggerSidePrice = float(positions.data[1].entryPrice)
                if((size2/3) > size1):
                    asyncio.run(SendTelegramMessage('más de dos recompras sin descargar en '+str(positions.data[0].symbol)+', revisar'))

            #se procede a buscar una orden que tenga marcado el flag "reduce-only" true:
            orders = session.get_open_orders(
                        category="linear",
                        symbol=positions.data[0].symbol,
                    )
            ordersResponse = BybitOrders_Response.from_dict(orders)
            print("ordersObject: ")
            print(ordersResponse.result.list[0].createdTime)
            if(len(orders['result']['list']) >0):
                # print('discharge orders section: ')
                # print(orders)
                ##Las órdenes de take profit parcial se identificarán si están marcadas con reduce-only == True:
                discharge_order_exists = False
                orderSizeToSearch = round(abs(size1 - size2),4)
                for o in orders['result']['list']:
                    # print('order discharge section (for loop): ')
                    # print(o)
                    if(o['reduceOnly'] == True):
                        # print('order discharge section (for loop-reduceOnly): ')
                        # print(o['reduceOnly'])
                        discharge_order_exists = True

                        ##Se puede dar el caso de que se haya tomado otra recompra antes de descargarse,
                        ##si es así, debe cancelarse dicha orden y crear una nueva,
                        ##para esto, se compara el tamaño de esa orden con el tamaño que debería tener:

                        

                        if(float(o['qty']) != orderSizeToSearch):
                            print('orderSizeToSearch: '+str(orderSizeToSearch))
                            session.cancel_order(
                                category="linear",
                                symbol=o["symbol"],
                                orderId=o["orderId"]
                            )
                            placeDischargeOrder(biggerSide,biggerSidePrice,orderSizeToSearch,positions.data[0].symbol)

                        print("órden take profit parcial: ")
                        print(o)

                if(discharge_order_exists == False):
                    print("no existe orden de descarga, creando")

                    placeDischargeOrder(biggerSide,biggerSidePrice,orderSizeToSearch,positions.data[0].symbol)

                   
        else:
            print("posiciones equilibradas en "+str(positions.data[0].symbol))
            shortSide = {}
            buySide ={}
            if(positions.data[0].side == "Buy"):
                buySide = positions.data[0]
                shortSide = positions.data[1]
            else:
                buySide = positions.data[1]
                shortSide = positions.data[0]
            differencePercentage = ((float(shortSide.entryPrice) - float(buySide.entryPrice))/float(buySide.entryPrice))*100
            if(differencePercentage > 1):
                is_updating_orders = True
               
                closePositions(buySide,shortSide)

                ordrs = session.get_open_orders(
                        category="linear",
                        symbol=positions.data[0].symbol,
                    )
                if(len(ordrs['result']['list']) >0):
                    for o in ordrs['result']['list']:
                        session.cancel_order(
                                    category="linear",
                                    symbol=o["symbol"],
                                    orderId=o["orderId"]
                                )
                is_updating_orders = False
                asyncio.run(SendTelegramMessage('ganancia mayor al 1 porciento en '+str(positions.data[0].symbol)+', posiciones cerradas'))
                return
            margenTotal = 0
            try:
                response = session.get_wallet_balance(accountType="UNIFIED",coin = "USDT")
                if response["retCode"] == 0:
                    margin_balance = response["result"]["list"]
                # print("Saldo de margen por moneda:")
                # print(response)
                
                moneda=margin_balance[0]['coin'][0]['coin']
                margenTotal = float(margin_balance[0]['totalEquity'])
                print(f"Moneda: {moneda}, Total: {margenTotal}")
         

                if(margenTotal > 0):
                    #validar si el tamaño de las posiciones es mayor al tamaño del margen por el multiplicador indicado, esto, para saber si se pueden colocar más recompras:
                    tamanhoPosicion = float(positions.data[0].size) * float(positions.data[0].entryPrice)
                    tamanhoMaximoPermitidoPosicion = margenTotal*marginMultiplier
                    sell_pos = {}
                    buy_pos = {}
                    if(tamanhoPosicion<tamanhoMaximoPermitidoPosicion):
                        hedge_buy_pos = {}
                        hedge_sell_pos ={}
                        buy_orders :List[BybitOrders_Response_Result_Item] = []
                        sell_orders :List[BybitOrders_Response_Result_Item] = []
                        orders = session.get_open_orders(
                        category="linear",
                        symbol=positions.data[0].symbol,
                        )
                        ordersResponse = BybitOrders_Response.from_dict(orders)
                        if(len(ordersResponse.result.list)>0):
                            print("ordersObject: ")
                            print(ordersResponse.result.list[0].createdTime)
                        for ord in ordersResponse.result.list:
                            if(ord.reduceOnly == False):
                                if(ord.triggerDirection == 0):
                                    if(ord.side == "Sell"):
                                        sell_orders.append(ord)
                                    else:
                                        buy_orders.append(ord)
                                elif(ord.triggerDirection == 1):
                                    hedge_buy_pos = ord
                                else:                            
                                    hedge_sell_pos = ord
                        
                        if(len(buy_orders)<orders_per_side):
                            is_updating_orders = True
                             ##primero se cancelan las recompras restantes: 
                            for so in buy_orders:
                                session.cancel_order(
                                                category="linear",
                                                symbol=so.symbol,
                                                orderId=so.orderId
                                            )
                                
                            ##Se cancela también la orden condicional de cobertura:
                            if(hedge_sell_pos != {}):
                                session.cancel_order(
                                                category="linear",
                                                symbol=hedge_sell_pos.symbol,
                                                orderId=hedge_sell_pos.orderId
                                            )
                            
                            if(positions.data[0].side == "Buy"):
                                buy_pos = positions.data[0]
                            else:
                                buy_pos = positions.data[1]


                            #Se recalculan las órdenes:
                            last_buy_order_price = 0
                            last_buy_order_quantity = 0
                            buyPlacedOrders : List[Tuple[float,float]] = []
                            mode = 1
                            print('orders_per_side: '+str(orders_per_side))
                            volatilityPercentage = calculateVolatility(positions.data[0].symbol)
                            if(volatilityPercentage > percentage_distance_between_orders):
                                percentage_distance_between_orders = volatilityPercentage
                            if(len(positions.data)>1):
                                for i in range(orders_per_side):
                                    quantity = 0
                                    p = 0
                                    if(mode==1):
                                        if(i == 0):
                                            quantity = float(buy_pos.size) 
                                            p = round(float(buy_pos.entryPrice) - (float(buy_pos.entryPrice) * percentage_distance_between_orders),precision_round)
                                            buyPlacedOrders.append((quantity,p))
                                        elif( i%2 == 0):
                                            quantity = sum(order[0] for order in buyPlacedOrders)+float(buy_pos.size)
                                            p = round(buyPlacedOrders[len(buyPlacedOrders)-1][1] - (buyPlacedOrders[len(buyPlacedOrders)-1][1] * percentage_distance_between_orders),precision_round)
                                            buyPlacedOrders.append((quantity,p))
                                        else:
                                            quantity = buyPlacedOrders[len(buyPlacedOrders)-1][0]
                                            p = round(buyPlacedOrders[len(buyPlacedOrders)-1][1] - (buyPlacedOrders[len(buyPlacedOrders)-1][1] * percentage_distance_between_orders),precision_round)
                                            buyPlacedOrders.append((quantity,p))

                                        re = session.place_order(
                                                        category="linear",
                                                        symbol=buy_pos.symbol,
                                                        side="Buy",
                                                        orderType="Limit",
                                                        qty=round(quantity,precision_round),
                                                        price = p,
                                                        positionIdx = 1
                                                    )
                                    else:
                                        if(i == 0):
                                            quantity = float(buy_pos.size) * buyback_size
                                            p = round(float(buy_pos.entryPrice) - (float(buy_pos.entryPrice) * percentage_distance_between_orders),precision_round)
                                            last_buy_order_quantity = quantity + float(buy_pos.size)
                                            last_buy_order_price = p
                                            quantity_sum = last_buy_order_quantity
                                        else:
                                            quantity = last_buy_order_quantity * buyback_size
                                            p = round(last_buy_order_price - (last_buy_order_price * percentage_distance_between_orders),precision_round)
                                            last_buy_order_quantity = quantity + last_buy_order_quantity 
                                            last_buy_order_price = p
                                            quantity_sum = quantity_sum + quantity

                                        re = session.place_order(
                                                        category="linear",
                                                        symbol=buy_pos.symbol,
                                                        side="Buy",
                                                        orderType="Limit",
                                                        qty=round(quantity,precision_round),
                                                        price = p,
                                                        positionIdx = 1
                                                    )
                                
                            

                        if(len(sell_orders)<orders_per_side):
                            is_updating_orders = True
                             ##primero se cancelan las recompras restantes: 
                            for so in sell_orders:
                                session.cancel_order(
                                                category="linear",
                                                symbol=so.symbol,
                                                orderId=so.orderId
                                            )
                                
                            ##Se cancela también la orden condicional de cobertura:
                            if(hedge_buy_pos != {}):
                                session.cancel_order(
                                                category="linear",
                                                symbol=hedge_buy_pos.symbol,
                                                orderId=hedge_buy_pos.orderId
                                            )
                            
                            if(positions.data[0].side == "Sell"):
                                sell_pos = positions.data[0]
                            else:
                                sell_pos = positions.data[1]


                            #Se recalculan las órdenes:
                            sellPlacedOrders : List[Tuple[float,float]] = []
                            mode = 1
                            print('orders_per_side_sell: '+str(orders_per_side))
                            volatilityPercentage = calculateVolatility(positions.data[0].symbol)
                            if(volatilityPercentage > percentage_distance_between_orders):
                                percentage_distance_between_orders = volatilityPercentage
                            if(len(positions.data)>1):
                                for i in range(orders_per_side):
                                    quantity = 0
                                    p = 0
                                    if(mode==1):
                                        if(i == 0):
                                            quantity = float(sell_pos.size) 
                                            p = round(float(sell_pos.entryPrice) + (float(sell_pos.entryPrice) * percentage_distance_between_orders),precision_round)
                                            sellPlacedOrders.append((quantity,p))
                                        elif( i%2 == 0):
                                            quantity = sum(order[0] for order in sellPlacedOrders)+float(sell_pos.size)
                                            p = round(sellPlacedOrders[len(sellPlacedOrders)-1][1] + (sellPlacedOrders[len(sellPlacedOrders)-1][1] * percentage_distance_between_orders),precision_round)
                                            sellPlacedOrders.append((quantity,p))
                                        else:
                                            quantity = sellPlacedOrders[len(sellPlacedOrders)-1][0]
                                            p = round(sellPlacedOrders[len(sellPlacedOrders)-1][1] + (sellPlacedOrders[len(sellPlacedOrders)-1][1] * percentage_distance_between_orders),precision_round)
                                            sellPlacedOrders.append((quantity,p))

                                        re = session.place_order(
                                                        category="linear",
                                                        symbol=sell_pos.symbol,
                                                        side="Sell",
                                                        orderType="Limit",
                                                        qty=round(quantity,precision_round),
                                                        price = p,
                                                        positionIdx = 2
                                                    )
                                    else:
                                        last_sell_order_quantity = 0
                                        last_sell_order_price = 0
                                        if(i == 0):
                                            quantity = float(sell_pos.size) * buyback_size
                                            p = round(float(sell_pos.entryPrice) + (float(sell_pos.entryPrice) * percentage_distance_between_orders),precision_round)
                                            last_sell_order_quantity = quantity + float(sell_pos.size)
                                            last_sell_order_price = p
                                            quantity_sum = last_sell_order_quantity
                                        else:
                                            quantity = last_sell_order_quantity * buyback_size
                                            p = round(last_sell_order_price + (last_sell_order_price * percentage_distance_between_orders),precision_round)
                                            last_sell_order_quantity = quantity + last_sell_order_quantity 
                                            last_sell_order_price = p
                                            quantity_sum = quantity_sum + quantity

                                        re = session.place_order(
                                                        category="linear",
                                                        symbol=sell_pos.symbol,
                                                        side="Sell",
                                                        orderType="Limit",
                                                        qty=round(quantity,precision_round),
                                                        price = p,
                                                        positionIdx = 2
                                                    )
                                
                        is_updating_orders = False
                        print('Escuchando de nuevo')

            except Exception as e:
                print(f"Error al conectar con la API: {str(e)}")
            
    except websocket._exceptions.WebSocketConnectionClosedException:
        print("Conexión WebSocket cerrada. Reconectando...")
        connect_to_websocket()
    except Exception as e:
        print(f"Error procesando mensaje: {e}")

def connect_to_websocket():
    # global ws
    # global session
    while True:
        try:

        
            # Suscribirse al canal de posiciones con el callback

            ws.subscribe("position", callback=handle_message)
            print("Conectado al WebSocket.")
            return
                
        except Exception as e:
            print(f"Error conectando al WebSocket: {e}")
            print("Reintentando en 5 segundos...")
            time.sleep(5)

connect_to_websocket()
# Mantener la conexión activa
try:
    print("Escuchando actualizaciones...")
    while True:
        time.sleep(1)  # Mantener el script activo y evitar consumir recursos en exceso
except KeyboardInterrupt:
    print("Conexión cerrada.")