from datetime import datetime, timedelta
import enum
import math
from typing import List
from Positions import getBybitPositions
from common import BybitInstrumentsInfoResponse, BybitKlinesResponse, BybitKlinesResultKline, BybitPositionsResponse, BybitTickersResponse, BybitTickersResultTicker, CalculationMode, EntranceZone, PriceGroup,zoneType
import Klines
from getTickers import getBybitInstrumentsInfo, getBybitTickers
from pybit.unified_trading import (HTTP)
from config import(bybit_api_key,bybit_secret_key)
# rangeDivisor : float = 2
# rangePrecision :int =3
minPricesAmount = 4
entranceZonePercentage = 0.0025
filterGroups = True
symbol = 'MAVIAUSDT'
lstGlobalEntranceZones : List[EntranceZone]=[]
accountMargin= 50
marginPercentage = 0.15
firstEntry = 0

session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key,
)

def setTicker(s:str):
    global symbol
    symbol = s

def setFirstEntry(type:int):
    global firstEntry
    firstEntry = type
    return firstEntry

def _getZonesByPercentage(kline : BybitKlinesResultKline, index: int, klinesList: List[BybitKlinesResultKline],priceGroups: List[PriceGroup],percentage:float):
    
    rangeValueExists = False
    if(len(priceGroups)== 0):  
            
        priceGroups.append(PriceGroup(
            rangeValue = 0,
            prices=[float(kline.closePrice)],
            minPrice = float(kline.closePrice) - (float(kline.closePrice) * percentage),
            maxPrice = float(kline.closePrice) + (float(kline.closePrice) * percentage),
            sellZone = None,
            buyZone = None
            ))
    elif(len(priceGroups) > 0):
        
        for pGroup in priceGroups:
            if(float(kline.closePrice) >= pGroup.minPrice and float(kline.closePrice) <= pGroup.maxPrice ):
                pGroup.prices.append(float(kline.closePrice))
                rangeValueExists = True
                break
        if(rangeValueExists == False):
            priceGroups.append(PriceGroup(
            rangeValue = 0,
            prices=[float(kline.closePrice)],
            minPrice = float(kline.closePrice) - (float(kline.closePrice) * percentage),
            maxPrice = float(kline.closePrice) + (float(kline.closePrice) * percentage),
            sellZone = None,
            buyZone = None
        ))
    
    # if(len(priceGroups) > 0):
    #     for pGroup in priceGroups:
    #         pGroup.minPrice = min(pGroup.prices)
    #         pGroup.maxPrice = max(pGroup.prices)
    return priceGroups

def getMarketZones(temporality : int = 15, rangeDivisor : float =2, rangePrecision:int = 2, minBouncesAmount : int = 2, calculationMode: int =0, percentage : float = 0,depth:int=2):
    print(symbol)
    minPricesAmount = minBouncesAmount
    bybitKlinesResponse : BybitKlinesResponse = Klines.getBybitKlines(symbol,200,temporality)
    priceGroups: List[PriceGroup]=[]
    epoch = datetime(1970, 1, 1)
    #se crean zonas de soportes y resistencias:
    for index, kline in enumerate(bybitKlinesResponse.result.list):
        #print('kline: '+str(kline.closePrice)+', index: '+str(index)+', fecha: '+str(epoch +timedelta(seconds=int(kline.startTime)/1000)))
        rangeValueExists = False
        maximum = False
        minimum = False

        # if(index == 0):
        #     if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index +1].closePrice)):
        #         minimum = True
        #     if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index +1].closePrice)):
        #         maximum = True
        # elif(index == len(bybitKlinesResponse.result.list)-1):
        #     if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index -1].closePrice)):
        #         minimum = True
        #     if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index -1].closePrice)):
        #         maximum = True
        # else:
        #     if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index -1].closePrice) and float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index +1].closePrice)):
        #         minimum = True
        #     if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index -1].closePrice) and float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index +1].closePrice)):
        #         maximum = True
        is_greater = True
        is_lower = True
        if(index == 0):
            for j in range(1, depth + 1):
                if kline.closePrice <= bybitKlinesResponse.result.list[index + j].closePrice:
                    is_greater = False
                    break
            if(is_greater == False):
                for j in range(1, depth + 1):
                    if kline.closePrice >= bybitKlinesResponse.result.list[index + j].closePrice:
                        is_lower = False
                        break
                if(is_lower== True):
                    minimum = True
            else:
                maximum = True
          
        elif(index == len(bybitKlinesResponse.result.list)-1):
            for j in range(1, depth + 1):
                if kline.closePrice <= bybitKlinesResponse.result.list[index - j].closePrice:
                    is_greater = False
                    break
            if(is_greater == False):
                for j in range(1, depth + 1):
                    if kline.closePrice >= bybitKlinesResponse.result.list[index - j].closePrice:
                        is_lower = False
                        break
                if(is_lower== True):
                    minimum = True
            else:
                maximum = True
        else:
            for j in range(1, depth + 1):
                if((index - j) >= 0 and (index + j) <= len(bybitKlinesResponse.result.list)-1):
                    if kline.closePrice <= bybitKlinesResponse.result.list[index - j].closePrice or kline.closePrice <= bybitKlinesResponse.result.list[index + j].closePrice:
                        is_greater = False
                        break
            if(is_greater == False):
                for j in range(1, depth + 1):
                    if((index - j) >= 0 and (index + j) <= len(bybitKlinesResponse.result.list)-1):
                        if kline.closePrice >= bybitKlinesResponse.result.list[index - j].closePrice or kline.closePrice >= bybitKlinesResponse.result.list[index + j].closePrice:
                            is_lower = False
                            break
                if(is_lower== True):
                    minimum = True
            else:
                maximum = True
       

        if(maximum | minimum):
            
            if(calculationMode == 1):
                
                # se valida precio de apertura:
                #priceRange = round(float(kline.openPrice) / rangeDivisor,rangePrecision)
                priceRange = float(f'{(float(kline.openPrice) / rangeDivisor):.{rangePrecision}f}')  
                if(len(priceGroups)== 0):                
                    priceGroups.append(PriceGroup(
                        rangeValue = priceRange,
                        prices=[float(kline.closePrice)],
                        minPrice = 0,
                        maxPrice = 0,
                        sellZone = None,
                        buyZone = None
                        ))
                elif(len(priceGroups) > 0):
                    for pGroup in priceGroups:
                        if(pGroup.rangeValue == priceRange):
                            pGroup.prices.append(float(kline.closePrice))
                            rangeValueExists = True
                            break
                    if(rangeValueExists == False):
                        priceGroups.append(PriceGroup(
                            rangeValue = priceRange,
                            prices=[float(kline.closePrice)],
                            minPrice = 0,
                            maxPrice = 0,
                            sellZone = None,
                            buyZone = None
                            ))
            elif(calculationMode == 0):
                
                priceGroups = _getZonesByPercentage(kline,index,bybitKlinesResponse.result.list,priceGroups,percentage)
                
    if(filterGroups):
        filteredPriceGroups : List[PriceGroup] = []

        for pG in priceGroups:
            if(len(pG.prices) >= minPricesAmount):
                filteredPriceGroups.append(pG)

        priceGroups = filteredPriceGroups

    for pGroup in priceGroups:
        pGroup.minPrice = min(pGroup.prices)
        pGroup.maxPrice = max(pGroup.prices)
        #print("rango: "+str(pGroup.rangeValue)+", precios: "+str(pGroup.prices))

    return priceGroups
    

def getEntranceZones(pGroups : List[PriceGroup]=[]):
    priceGroups: List[PriceGroup]=[]
    if(len(pGroups)>0):
        priceGroups = pGroups
    else:
        priceGroups = getMarketZones()

    lstEntranceZones : List[EntranceZone]=[]

    print(priceGroups)
    for index, priceGroup in enumerate(priceGroups):
        #se establece zona de entrada a compra:
        # buyEntranceZone = EntranceZone(
        #     minPrice = priceGroup.minPrice,
        #     maxPrice = priceGroup.minPrice + (priceGroup.minPrice * entranceZonePercentage),
        #     zoneType = zoneType.buy,
        #     priceGroup=priceGroup)      
    


        #se establece zona de entrada a venta:
        # sellEntranceZone= EntranceZone(
        #     minPrice = priceGroup.maxPrice - (priceGroup.maxPrice * entranceZonePercentage),
        #     maxPrice = priceGroup.maxPrice ,
        #     zoneType = zoneType.sell,
        #     priceGroup=priceGroup)    

        if(index < len(priceGroups)-2):
            priceDiff = abs(priceGroup.maxPrice - priceGroups[index +1].minPrice )
            distancePercentage = (priceDiff/priceGroup.minPrice) * 100
            

           
            if(distancePercentage > 1):
                zonePercentage = priceDiff * 0.25
                buyEntranceZone = EntranceZone(
                    minPrice = priceGroup.minPrice,
                    maxPrice = priceGroup.minPrice +zonePercentage,
                    zoneType = zoneType.buy)  

                sellEntranceZone= EntranceZone(
                    minPrice = priceGroups[index +1].maxPrice - zonePercentage,
                    maxPrice = priceGroups[index +1].maxPrice ,
                    zoneType = zoneType.sell)  

                priceGroup.sellZone = sellEntranceZone
                priceGroup.buyZone = buyEntranceZone


                lstEntranceZones.append(buyEntranceZone)  
                lstEntranceZones.append(sellEntranceZone)  

    global lstGlobalEntranceZones
    lstGlobalEntranceZones = lstEntranceZones

    return lstEntranceZones

def EvaluatePriceAction():
    global lstGlobalEntranceZones 
    global symbol
    global accountMargin
    global marginPercentage
    global firstEntry
    print('lstGlobalEntranceZones: '+str(lstGlobalEntranceZones))
    if(len(lstGlobalEntranceZones)>0):
        bybitTickersResponse : BybitTickersResponse = getBybitTickers(symbol)
        tickerInfoResponse : BybitInstrumentsInfoResponse = getBybitInstrumentsInfo(symbol)
        ticker : BybitTickersResultTicker = bybitTickersResponse.result.list[0]
        bybitPositionsResponse : BybitPositionsResponse = getBybitPositions(symbol)
        last_price :float = float(ticker.last_price)
       
        print('bybitPositionsResponse: '+str(bybitPositionsResponse))
        for index,eZ in enumerate(lstGlobalEntranceZones):
            print('eZ: '+str(eZ)+' last_price: '+str(last_price))
            if(last_price > eZ.minPrice and last_price <= eZ.maxPrice):
                print('entró')
                #print('len(bybitPositionsResponse.result.list): '+str(len(bybitPositionsResponse.result.list))+' bybitPositionsResponse.result.list[0].size: '+bybitPositionsResponse.result.list[0].size)
                if(len(bybitPositionsResponse.result.list) == 1 ):
                    print('entró 1')
                    for item in bybitPositionsResponse.result.list:
                        if(item.side == "Sell" and eZ.zoneType == 0):
                            response = session.place_order(
                                        category="linear",
                                        symbol=symbol,
                                        side="Buy",
                                        orderType="Market",
                                        qty=item.size,
                                        positionIdx = 1,
                                        takeProfit= round(lstGlobalEntranceZones[index +1].maxPrice -(lstGlobalEntranceZones[index +1].maxPrice * 0.002),6),
                                        stopLoss = round(last_price -(last_price *0.1),6)
                                    )
                        elif(item.side == "Buy" and eZ.zoneType == 1):
                            response = session.place_order(
                                        category="linear",
                                        symbol=symbol,
                                        side="Sell",
                                        orderType="Market",
                                        qty=item.size,
                                        positionIdx = 2,
                                        takeProfit= round(lstGlobalEntranceZones[index -1].minPrice +(lstGlobalEntranceZones[index -1].minPrice * 0.002),6),
                                        stopLoss = round(last_price +(last_price *0.1),6)
                            )
                elif(len(bybitPositionsResponse.result.list) <2):
                    print('entró2')
                    usdtSizePosition = accountMargin * marginPercentage
                    sizePosition = usdtSizePosition/last_price
                    finalSize : int =0
                    print('sizePosition: '+str(sizePosition))
                    print('tickerInfoResponse.result.list[0].lot_size_filter.min_order_qty: '+str(tickerInfoResponse.result.list[0].lot_size_filter.min_order_qty))
                    if(sizePosition < tickerInfoResponse.result.list[0].lot_size_filter.min_order_qty):
                        finalSize = tickerInfoResponse.result.list[0].lot_size_filter.min_order_qty
                    else:
                        finalSize = math.ceil(sizePosition)
                    if(eZ.zoneType == 0 and (firstEntry == 0 or firstEntry == 1) ):
                        response = session.place_order(
                                                category="linear",
                                                symbol=symbol,
                                                side="Buy",
                                                orderType="Market",
                                                qty=finalSize,
                                                positionIdx = 1,
                                                takeProfit= round(lstGlobalEntranceZones[index +1].maxPrice -(lstGlobalEntranceZones[index +1].maxPrice * 0.002),6),
                                                stopLoss = round(last_price -(last_price *0.1),6)
                                            )

                    elif(eZ.zoneType == 1 and (firstEntry == 0 or firstEntry == 2)):
                        response = session.place_order(
                                                category="linear",
                                                symbol=symbol,
                                                side="Sell",
                                                orderType="Market",
                                                qty=finalSize,
                                                positionIdx = 2,
                                                takeProfit= round(lstGlobalEntranceZones[index -1].minPrice +(lstGlobalEntranceZones[index -1].minPrice * 0.002),6),
                                                stopLoss = round(last_price +(last_price *0.1),6)
                                            )






