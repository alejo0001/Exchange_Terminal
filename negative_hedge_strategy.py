import math
from typing import List
from pybit.unified_trading import (WebSocket,HTTP)
from time import sleep
from Positions import getBybitPositions
from common import BybitOrdersResponse, BybitOrdersResponseResultItem, BybitPositionsResponse, BybitPositionsResponseResultItem
from orders import getBybitOrders
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)
from os import system



session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)

def handleNegativeHedge(symbol:str):    
    buySide : BybitPositionsResponseResultItem
    sellSide : BybitPositionsResponseResultItem
    orders : BybitOrdersResponse
    takeProfitOrdersPerSide = 10
    longTakeProfitOrders : List[BybitOrdersResponseResultItem]= []
    shortTakeProfitOrders : List[BybitOrdersResponseResultItem] = []
    longLossClosingOrders : List[BybitOrdersResponseResultItem]= []
    shortLossClosingOrders : List[BybitOrdersResponseResultItem]= []
    precision_round = 6
    longOrderDistance = 0
    shortOrderDistance = 0
    test = True

    inverseTradeRiskBenefitRelation = 2


    while True:
        bybitPositionsResponse : BybitPositionsResponse = getBybitPositions(symbol)

        
        #inverse trade strategy:
        if(bybitPositionsResponse.result.list[0].side == "Sell"):
            sellSide = bybitPositionsResponse.result.list[0]
            buySide = bybitPositionsResponse.result.list[1]
        else:
            sellSide = bybitPositionsResponse.result.list[1]
            buySide = bybitPositionsResponse.result.list[0]

        longOrderDistance = (abs(float(buySide.avgPrice) - float(sellSide.avgPrice)))/float(sellSide.avgPrice)
        shortOrderDistance = (abs(float(sellSide.avgPrice) - float(buySide.avgPrice)))/float(buySide.avgPrice)

        orders = getBybitOrders(symbol)
        for order in orders.result.list:
            if(order.side == "Buy" and order.position_idx == 2):
                if( float(order.price) < float(sellSide.avgPrice)):
                    shortTakeProfitOrders.append(order)
                else:
                    shortLossClosingOrders.append(order)
                shortTakeProfitOrders.sort(key = lambda order:order.price)
                shortLossClosingOrders.sort(key = lambda order:order.price)
            elif(order.side == "Sell" and order.position_idx == 1):
                if( float(order.price) > float(buySide.avgPrice)):
                    longTakeProfitOrders.append(order)
                else:
                    longLossClosingOrders.append(order)
                longTakeProfitOrders.sort(key = lambda order:order.price)
                longLossClosingOrders.sort(key = lambda order:order.price)
        
        if(sellSide.size == buySide.size):
            #long take profit orders:
            if(len(longTakeProfitOrders) ==0):
                #orderSize = math.floor(buySide.size / takeProfitOrdersPerSide)
                orderSize = 1 if buySide.size <= 100 else  math.floor(buySide.size /100)
                orderPos = round(float(buySide.avgPrice) +(float(buySide.avgPrice)*longOrderDistance),precision_round)
                sizeSum = 0
                for i in range(takeProfitOrdersPerSide):
                    if(sizeSum + orderSize > buySide.size):
                        break
                    
                    else:
                        sizeSum = sizeSum + orderSize
                        if(test):
                            print(' long take profit Order: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:

                   
                            response = session.place_order(
                                        category="linear",
                                        symbol=symbol,
                                        side="Sell",
                                        orderType="Limit",
                                        qty=orderSize,
                                        price = orderPos,
                                        positionIdx = 1,
                                        reduceOnly = True
                                    )
                        orderPos = round(orderPos +(orderPos*longOrderDistance),precision_round)

            elif(len(longTakeProfitOrders) < takeProfitOrdersPerSide):
                orderSize =  1 if buySide.size <= 100 else  math.floor(buySide.size /100)
                orderPos = round(float(longTakeProfitOrders[len(longTakeProfitOrders)-1]) +(float(longTakeProfitOrders[len(longTakeProfitOrders)-1])*longOrderDistance),precision_round)
                if(test):
                    print(' long take profit Order: ')
                    print(orderPos)
                    print(orderSize)
                    print('-------------------')
                else:
                    profitOrdersSum = 0
                    for o in longTakeProfitOrders:
                        profitOrdersSum = profitOrdersSum +  float(o.qty)

                    if(profitOrdersSum < buySide.size):
                        response = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side="Sell",
                                    orderType="Limit",
                                    qty=orderSize,
                                    price = orderPos,
                                    positionIdx = 1,
                                    reduceOnly = True
                                )
            #short take profit orders:
            if(len(shortTakeProfitOrders) ==0):
                orderSize =  1 if sellSide.size <= 100 else  math.floor(sellSide.size /100)
                orderPos = round(float(sellSide.avgPrice) -(float(sellSide.avgPrice)*shortOrderDistance),precision_round)
                sizeSum = 0
                for i in range(takeProfitOrdersPerSide):
                    if(sizeSum + orderSize > sellSide.size):
                        break
                    else:
                        sizeSum = sizeSum + orderSize
                        if(test):
                            print(' short take profit Order1: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:
                            response = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side="Buy",
                                    orderType="Limit",
                                    qty=orderSize,
                                    price = orderPos,
                                    positionIdx = 2,
                                    reduceOnly = True
                                )
                        orderPos = round(orderPos -(orderPos*shortOrderDistance),precision_round)

            elif(len(shortTakeProfitOrders) < takeProfitOrdersPerSide):
                orderSize = 1 if sellSide.size <= 100 else  math.floor(sellSide.size /100)
                orderPos = round(float(shortTakeProfitOrders[0]) -(float(shortTakeProfitOrders[0])*shortOrderDistance),precision_round)
                if(test):
                    print(' short take profit Order2: ')
                    print(orderPos)
                    print(orderSize)
                    print('-------------------')
                else:
                    profitOrdersSum = 0
                    for o in shortTakeProfitOrders:
                        profitOrdersSum = profitOrdersSum +  float(o.qty)
                    if(profitOrdersSum < sellSide.size):
                        response = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side="Buy",
                                    orderType="Limit",
                                    qty=orderSize,
                                    price = orderPos,
                                    positionIdx = 2,
                                    reduceOnly = True
                                )
        else:
            sizeDiff =  float(buySide.size) -  float(sellSide.size)

            overloadedPosition ="Buy"
            if(sizeDiff < 0):
                overloadedPosition ="Sell"
            
            if(overloadedPosition == "Buy"):
                closingOrdersSum = 0
                for o in longLossClosingOrders:
                    closingOrdersSum = closingOrdersSum +  float(o.qty)

                if(closingOrdersSum < abs(sizeDiff)):
                    if(len(longLossClosingOrders) == 0):
                        orderSize = float(shortTakeProfitOrders[0].qty)
                        orderPos = round(float(sellSide.avgPrice) -(float(sellSide.avgPrice)*shortOrderDistance),precision_round) +round(round(float(sellSide.avgPrice) -(float(sellSide.avgPrice)*shortOrderDistance),precision_round) * (longOrderDistance * inverseTradeRiskBenefitRelation),precision_round)
                        if(test):
                            print(' long closing Order: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:
                            response = session.place_order(
                                category="linear",
                                symbol=symbol,
                                side="Sell",
                                orderType="Limit",
                                qty=orderSize,
                                price = orderPos,
                                positionIdx = 1,
                                reduceOnly = True
                            )
                    elif(len(longLossClosingOrders) > 0):
                        orderSize = float(longLossClosingOrders[len(longLossClosingOrders)-1].qty)
                        orderPos = round(float(longLossClosingOrders[0].price) -(float(longLossClosingOrders[0].price)*longOrderDistance),precision_round) 
                        if(test):
                            print(' long closing Order: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:
                            closingOrdersSum = 0
                            for o in longLossClosingOrders:
                                closingOrdersSum = closingOrdersSum +  float(o.qty)
                            if(closingOrdersSum < buySide.size):
                                response = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side="Sell",
                                    orderType="Limit",
                                    qty=orderSize,
                                    price = orderPos,
                                    positionIdx = 1,
                                    reduceOnly = True
                                )
                        
                else:
                    #short Take Profit orders:
                    if(len(shortTakeProfitOrders) < takeProfitOrdersPerSide):
                        takeProfitSum = 0
                        for order in shortTakeProfitOrders:
                            takeProfitSum = takeProfitSum + float(order.qty)
                        
                        if(takeProfitSum <  float(sellSide.size)):

                            for o in shortTakeProfitOrders:
                                session.cancel_order(
                                            category="linear",
                                            symbol=o.symbol,
                                            orderId=o.order_id
                                        )
                                
                            orderSize =  1 if  float(sellSide.size) <= 100 else  math.floor( float(sellSide.size) /100)
                            orderPos = round(float(sellSide.avgPrice) -(float(sellSide.avgPrice)*shortOrderDistance),precision_round)
                            if(len(longLossClosingOrders) > 0):
                                 orderPos = round(float(longLossClosingOrders[0].price) -(float(longLossClosingOrders[0].price)*(shortOrderDistance*3)),precision_round)
                            sizeSum = 0
                            for i in range(takeProfitOrdersPerSide):
                                if(sizeSum + orderSize >  float(sellSide.size)):
                                    break
                                else:
                                    sizeSum = sizeSum + orderSize
                                    if(test):
                                        print('short take profit Order3: ')
                                        print(orderPos)
                                        print(orderSize)
                                        print('-------------------')
                                    else:
                                        response = session.place_order(
                                                category="linear",
                                                symbol=symbol,
                                                side="Buy",
                                                orderType="Limit",
                                                qty=orderSize,
                                                price = orderPos,
                                                positionIdx = 2,
                                                reduceOnly = True
                                            )
                                    orderPos = round(orderPos -(orderPos*shortOrderDistance),precision_round)
                    
                  

            else:

                closingOrdersSum = 0
                for o in shortLossClosingOrders:
                    closingOrdersSum = closingOrdersSum + float(o.qty)

                if(closingOrdersSum < abs(sizeDiff)):
                    if(len(shortLossClosingOrders) == 0):
                        orderSize = float(longTakeProfitOrders[0].qty)
                        orderPos = round(float(buySide.avgPrice) +(float(buySide.avgPrice)*longOrderDistance),precision_round) -round(round(float(buySide.avgPrice) +(float(buySide.avgPrice)*longOrderDistance),precision_round) * (shortOrderDistance * inverseTradeRiskBenefitRelation),precision_round)
                        if(test):
                            print(' short closing Order: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:
                            response = session.place_order(
                                category="linear",
                                symbol=symbol,
                                side="Buy",
                                orderType="Limit",
                                qty=orderSize,
                                price = orderPos,
                                positionIdx = 2,
                                reduceOnly = True
                            )
                    elif(len(shortLossClosingOrders) > 0):
                        orderSize = float(shortLossClosingOrders[len(shortLossClosingOrders)-1].qty)
                        orderPos = round(float(shortLossClosingOrders[len(shortLossClosingOrders)-1].price) +(float(shortLossClosingOrders[len(shortLossClosingOrders)-1].price)*longOrderDistance),precision_round) 
                        if(test):
                            print(' short closing Order: ')
                            print(orderPos)
                            print(orderSize)
                            print('-------------------')
                        else:
                            closingOrdersSum = 0
                            for o in shortLossClosingOrders:
                                closingOrdersSum = closingOrdersSum +  float(o.qty)
                            if(closingOrdersSum < sellSide.size):
                                response = session.place_order(
                                    category="linear",
                                    symbol=symbol,
                                    side="Buy",
                                    orderType="Limit",
                                    qty=orderSize,
                                    price = orderPos,
                                    positionIdx = 2,
                                    reduceOnly = True
                                )
                        
                else:                   
                    
                    #long Take Profit orders:
                    if(len(longTakeProfitOrders) < takeProfitOrdersPerSide):
                        takeProfitSum = 0
                        for order in longTakeProfitOrders:
                            takeProfitSum = takeProfitSum + float(order.qty)
                        
                        if(takeProfitSum <  float(buySide.size)):

                            for o in longTakeProfitOrders:
                                session.cancel_order(
                                            category="linear",
                                            symbol=o.symbol,
                                            orderId=o.order_id
                                        )
                                
                            orderSize =  1 if  float(buySide.size) <= 100 else  math.floor( float(buySide.size) /100)
                            orderPos = round(float(buySide.avgPrice) +(float(buySide.avgPrice)*longOrderDistance),precision_round)
                            if(len(shortLossClosingOrders) > 0):
                                orderPos = round(float(shortLossClosingOrders[len(shortLossClosingOrders)-1].price) +(float(shortLossClosingOrders[len(shortLossClosingOrders)-1].price)*(longOrderDistance*3)),precision_round)
                            sizeSum = 0
                            for i in range(takeProfitOrdersPerSide):
                                if(sizeSum + orderSize >  float(buySide.size)):
                                    break
                                else:
                                    sizeSum = sizeSum + orderSize
                                    if(test):
                                        print(' long take profit Order: ')
                                        print(orderPos)
                                        print(orderSize)
                                        print('-------------------')
                                    else:
                                        response = session.place_order(
                                                category="linear",
                                                symbol=symbol,
                                                side="Sell",
                                                orderType="Limit",
                                                qty=orderSize,
                                                price = orderPos,
                                                positionIdx = 1,
                                                reduceOnly = True
                                            )
                                    orderPos = round(orderPos +(orderPos*longOrderDistance),precision_round)


        sleep(1)

# orders = getBybitOrders('POPCATUSDT')
# for order in orders.result.list:
#     print('orden:')
#     print(order.side)
#     print(order.position_idx)
#     print(order.qty)

bybitPositionsResponse : BybitPositionsResponse = getBybitPositions()
lstSymbols : List[str]=[]
lstExcludedTickers : List[str]=['1000TURBOUSDT']

for pos in bybitPositionsResponse.result.list:
    if(len(lstSymbols) == 0):
        lstSymbols.append(pos.symbol)
    else:
        exists = False
        for s in lstSymbols:
            if(s == pos.symbol):
                exists = True
        
        if(exists == False):
            lstSymbols.append(pos.symbol)

for symbol in lstSymbols:
    if symbol not in lstExcludedTickers:
        print(symbol)
        handleNegativeHedge(symbol)

