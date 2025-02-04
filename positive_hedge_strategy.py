from pybit.unified_trading import (WebSocket,HTTP)
from time import sleep
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
from os import system

ws = WebSocket(
    testnet=True,
    channel_type="private",
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)


stop = False
s = "1000TURBOUSDT"
def handle_message(message):
    print(message)
ws.position_stream(callback=handle_message)
while True:

    pos = session.get_positions(
        category="linear",
        symbol=s      
    )

    if(len(pos['result']['list']) >0):

        system('cls') 
            

        side = pos['result']['list'][0]['side']
        qty = float(pos['result']['list'][0]['size'])
        price = float(pos['result']['list'][0]['avgPrice'])
        op = ""
        hedge_pos = 0
        discharge_order_pos = 0
        discharge_order_type = ""
        discharge_order_percentage_distance = 0.002 ## 0.2%
        discharge_order_trigger_Direction = 0
        discharge_order_position_Idx = 0
        orders_per_side_quantity = 3
        precision_round = 6
        percentage_distance_between_orders = 0.01 ## 1%
        buyback_size = 2 ##Tamaño de las recompras, no se recompra la misma cantidad como en un martingala, se recompra el doble
        charged_pos = 0
        trigger_Direction = 0
        position_Idx= 0 ##necesario para identificar el modo cobertura

        print("posición 1: ")
        print(pos['result']['list'][0])


        ##Buscar si hay dos posiciones simultáneas en la moneda:
        if(len(pos['result']['list']) >=2):
            side2 = pos['result']['list'][1]['side']
            qty2 = float(pos['result']['list'][1]['size'])
            price2 = float(pos['result']['list'][1]['avgPrice'])
            op2 = ""
            hedge_pos2 = 0
            trigger_Direction2 = 0
            position_Idx2= 0 ##necesario para identificar el modo cobertura

            print("posición 2: ")
            print(pos['result']['list'][1])


            ##Validar que las posiciones estén equilibradas:
            posicionesIguales = False
            if(qty == qty2):
                posicionesIguales = True


            ##Si están desequlibradas, se valida primero que exista una orden para descargar dicha posición:
            if(posicionesIguales != True):

                ##Deducir la diferencia de monedas entre juntas posiciones:
                orderSizeToSearch = round(abs(float(qty) - float(qty2)),precision_round)

                ##Identificar cuál es la posición sobrecargada:
                biggerSide = "Buy"

                if(float(qty) > float(qty2)):
                    biggerSide = side
                    charged_pos = price
                else:   
                    biggerSide = side2
                    charged_pos = price2

                ##Se procede a buscar una orden límite que coincida con estas condiciones:
                if(orderSizeToSearch > 0):
                    
                    orders = session.get_open_orders(
                        category="linear",
                        symbol=s,
                    )
                    
                    if(len(orders['result']['list']) >0):
                        print('discharge orders section: ')
                        print(orders)
                        ##Las órdenes de take profit parcial se identificarán si están marcadas con reduce-only == True:
                        discharge_order_exists = False
                        for o in orders['result']['list']:
                            print('order discharge section (for loop): ')
                            print(o)
                            if(o['reduceOnly'] == True):
                                print('order discharge section (for loop-reduceOnly): ')
                                print(o['reduceOnly'])
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

                                    ##Se configura la nueva orden:
                                    if(biggerSide =="Buy"):
                                        discharge_order_pos = round(charged_pos + (charged_pos * discharge_order_percentage_distance),precision_round)
                                        discharge_order_type="Sell"
                                        discharge_order_trigger_Direction = 2
                                        discharge_order_position_Idx = 1
                                    else:
                                        discharge_order_pos = round(charged_pos - (charged_pos * discharge_order_percentage_distance),precision_round)
                                        discharge_order_type="Buy"
                                        discharge_order_trigger_Direction = 1
                                        discharge_order_position_Idx = 2

                                    response = session.place_order(
                                        category="linear",
                                        symbol=s,
                                        side=discharge_order_type,
                                        orderType="Limit",
                                        qty=round(orderSizeToSearch,precision_round),
                                        price = discharge_order_pos,
                                        positionIdx = discharge_order_position_Idx,
                                        reduceOnly = True

                                    )




                                print("órden take profit parcial: ")
                                print(o)

                        if(discharge_order_exists == False):
                        #Se configura la nueva orden:
                            if(biggerSide =="Buy"):
                                discharge_order_pos = round(charged_pos + (charged_pos * discharge_order_percentage_distance),precision_round)
                                discharge_order_type="Sell"
                                discharge_order_trigger_Direction = 2
                                discharge_order_position_Idx = 1
                            else:
                                discharge_order_pos = round(charged_pos - (charged_pos * discharge_order_percentage_distance),precision_round)
                                discharge_order_type="Buy"
                                discharge_order_trigger_Direction = 1
                                discharge_order_position_Idx = 2 

                            response = session.place_order(
                                category="linear",
                                symbol=s,
                                side=discharge_order_type,
                                orderType="Limit",
                                qty=round(orderSizeToSearch,precision_round),
                                price = discharge_order_pos,
                                positionIdx = discharge_order_position_Idx,
                                reduceOnly = True
                            )


            else:
                ##Si las posiciones son iguales, se valida que cada posición tenga sus respectivas recompras y cobertura
                print("posiciones iguales")

                allOrders = session.get_open_orders(
                    category="linear",
                    symbol=s,
                )

               
                
                buyPrice = 0
                sellPrice = 0
                if(side == "Buy"):                   
                    buyPrice = price
                    sellPrice = price2
                else:
                    buyPrice = price2
                    sellPrice = price

                # Primero se debe validar de que no se trate de una cobertura negativa. Si es así, deben cancelarse todas las órdenes para gestionar la cobertura manualmente:
                if(buyPrice > sellPrice):
                    for o in allOrders['result']['list']:
                        session.cancel_order(
                                        category="linear",
                                        symbol=o["symbol"],
                                        orderId=o["orderId"]
                                    )
                else:
                    
                    hedge_buy_pos = {}
                    hedge_sell_pos ={}
                    buy_orders = []
                    sell_orders = []
                    for ord in allOrders['result']['list']:
                    
                        if(ord['reduceOnly'] == False):

                            if(ord['triggerDirection'] == 0):
                                print('triggerDirection: ')
                                print(ord)
                                if(ord['side'] == 'Sell'):
                                    print('se agrega orden: ')
                                    print(ord)
                                    sell_orders.append(ord)
                                else:
                                    buy_orders.append(ord)
                            elif(ord['triggerDirection'] == 1):
                                hedge_buy_pos = ord
                            else:                            
                                hedge_sell_pos = ord

                    ##Si no existe la cantidad de recompras establecidas, se asume que la posición se descargó
                    ##y deben recalcularse las órdenes: 

                    ## se valida de nuevo el tamaño de las posiciones
                    if(qty == qty2):
                        print('qty: '+str(qty)+' qty2: '+str(qty2))
                        sell_pos = {}
                        buy_pos = {}
                        ##Órdenes short:
                        if(len(sell_orders) < orders_per_side_quantity):
                            print('sell orders: ')
                            print(sell_orders)
                            ##primero se cancelan las recompras restantes:
                            for so in sell_orders:
                                session.cancel_order(
                                                category="linear",
                                                symbol=so["symbol"],
                                                orderId=so["orderId"]
                                            )
                                
                            ##Se cancela también la orden condicional de cobertura:
                            if(hedge_buy_pos != {}):
                                session.cancel_order(
                                                category="linear",
                                                symbol=hedge_buy_pos["symbol"],
                                                orderId=hedge_buy_pos["orderId"]
                                            )
                            
                            ##Se recalculan las órdenes:
                            quantity_sum = 0
                            if(side == "Sell"):
                                sell_pos = pos['result']['list'][0]
                            else:
                                sell_pos = pos['result']['list'][1]

                            
                            last_sell_order_price = 0
                            last_sell_order_quantity = 0
                            
                            for i in range(orders_per_side_quantity):
                                quantity = 0
                                p = 0
                                if(i == 0):
                                    quantity = float(sell_pos['size']) * buyback_size
                                    p = round(float(sell_pos['avgPrice']) + (float(sell_pos['avgPrice']) * percentage_distance_between_orders),precision_round)
                                    last_sell_order_quantity = quantity + float(sell_pos['size'])
                                    last_sell_order_price = p
                                    quantity_sum = last_sell_order_quantity
                                else:
                                    quantity = last_sell_order_quantity * buyback_size
                                    p = round(last_sell_order_price+ (last_sell_order_price * percentage_distance_between_orders),precision_round)
                                    last_sell_order_quantity = quantity+last_sell_order_quantity
                                    last_sell_order_price = p
                                    quantity_sum = quantity_sum + quantity


                                re = session.place_order(
                                                category="linear",
                                                symbol=s,
                                                side="Sell",
                                                orderType="Limit",
                                                qty=round(quantity,precision_round),
                                                price = p,
                                                positionIdx = 2
                                            )
                            
                            ## se crea la orden de cobertura:
                            res = session.place_order(
                                            category="linear",
                                            symbol=s,
                                            side="Buy",
                                            orderType="Market",
                                            qty=round(quantity_sum -float(sell_pos['size']),precision_round),
                                            triggerPrice = round(last_sell_order_price +(last_sell_order_price * percentage_distance_between_orders),precision_round),
                                            triggerDirection = 1,
                                            positionIdx = 1
                                        )
                        ##Órdenes long:
                        elif(len(buy_orders) < orders_per_side_quantity):
                            print('buy orders: ')
                            print(buy_orders)
                            ##primero se cancelan las recompras restantes: 
                            for so in buy_orders:
                                session.cancel_order(
                                                category="linear",
                                                symbol=so["symbol"],
                                                orderId=so["orderId"]
                                            )
                                
                            ##Se cancela también la orden condicional de cobertura:
                            if(hedge_sell_pos != {}):
                                session.cancel_order(
                                                category="linear",
                                                symbol=hedge_sell_pos["symbol"],
                                                orderId=hedge_sell_pos["orderId"]
                                            )
                            
                            ##Se recalculan las órdenes:
                            quantity_sum = 0
                            if(side == "Buy"):
                                buy_pos = pos['result']['list'][0]
                            else:
                                buy_pos = pos['result']['list'][1]

                            
                            last_buy_order_price = 0
                            last_buy_order_quantity = 0
                            
                            for i in range(orders_per_side_quantity):
                                quantity = 0
                                p = 0
                                if(i == 0):
                                    quantity = float(buy_pos['size']) * buyback_size
                                    p = round(float(buy_pos['avgPrice']) - (float(buy_pos['avgPrice']) * percentage_distance_between_orders),precision_round)
                                    last_buy_order_quantity = quantity + float(buy_pos['size'])
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
                                                symbol=s,
                                                side="Buy",
                                                orderType="Limit",
                                                qty=round(quantity,precision_round),
                                                price = p,
                                                positionIdx = 1
                                            )
                            
                            ## se crea la orden de cobertura:
                            res = session.place_order(
                                            category="linear",
                                            symbol=s,
                                            side="Sell",
                                            orderType="Market",
                                            qty=round(quantity_sum -float(buy_pos['size']),precision_round),
                                            triggerPrice = round(last_buy_order_price -(last_buy_order_price * percentage_distance_between_orders),precision_round),
                                            triggerDirection = 2,
                                            positionIdx = 2
                                        )
                





    sleep(1)