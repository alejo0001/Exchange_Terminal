from datetime import datetime, timedelta
from typing import List
from common import BybitKlinesResponse, EntranceZone, PriceGroup,zoneType
import Klines

# rangeDivisor : float = 2
# rangePrecision :int =3
minPricesAmount = 4
entranceZonePercentage = 0.0025
filterGroups = True

def getMarketZones(temporality : int = 15, rangeDivisor : float =2, rangePrecision:int = 2, minBouncesAmount : int = 2):
    minPricesAmount = minBouncesAmount
    bybitKlinesResponse : BybitKlinesResponse = Klines.getBybitKlines('1000TURBOUSDT',200,temporality)

    priceGroups: List[PriceGroup]=[]
    epoch = datetime(1970, 1, 1)
    #se crean zonas de soportes y resistencias:
    for index, kline in enumerate(bybitKlinesResponse.result.list):
        #print('kline: '+str(kline.closePrice)+', index: '+str(index)+', fecha: '+str(epoch +timedelta(seconds=int(kline.startTime)/1000)))
        rangeValueExists = False
        maximum = False
        minimum = False

        if(index == 0):
            if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index +1].closePrice)):
                minimum = True
            if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index +1].closePrice)):
                maximum = True
        elif(index == len(bybitKlinesResponse.result.list)-1):
            if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index -1].closePrice)):
                minimum = True
            if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index -1].closePrice)):
                maximum = True
        else:
            if(float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index -1].closePrice) and float(kline.closePrice) <= float(bybitKlinesResponse.result.list[index +1].closePrice)):
                minimum = True
            if(float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index -1].closePrice) and float(kline.closePrice) >= float(bybitKlinesResponse.result.list[index +1].closePrice)):
                maximum = True
        if(maximum | minimum):
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
    

def getEntranceZones():
    priceGroups: List[PriceGroup]=[]
    priceGroups = getMarketZones()

    lstEntranceZones : List[EntranceZone]=[]


    for priceGroup in priceGroups:
        #se establece zona de entrada a compra:
        buyEntranceZone = EntranceZone(
            minPrice = priceGroup.minPrice,
            maxPrice = priceGroup.minPrice + (priceGroup.minPrice * entranceZonePercentage),
            zoneType = zoneType.buy,
            priceGroup=priceGroup)      

        #se establece zona de entrada a venta:
        sellEntranceZone= EntranceZone(
            minPrice = priceGroup.maxPrice - (priceGroup.maxPrice * entranceZonePercentage),
            maxPrice = priceGroup.maxPrice ,
            zoneType = zoneType.sell,
            priceGroup=priceGroup)    


        priceGroup.sellZone = sellEntranceZone
        priceGroup.buyZone = buyEntranceZone


        lstEntranceZones.append(buyEntranceZone)  
        lstEntranceZones.append(sellEntranceZone)  

    for eZone in lstEntranceZones:
        print(f'''rango: {str(eZone.priceGroup.rangeValue)}
            precio mínimo: {str(eZone.priceGroup.minPrice)}
            precio máximo: {str(eZone.priceGroup.maxPrice)}
            máximo compra: {str(eZone.priceGroup.buyZone.maxPrice)}
            mínimo venta: {str(eZone.priceGroup.sellZone.minPrice)}''')

    #return lstEntranceZones


#getEntranceZones()

