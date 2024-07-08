from typing import List
from pybit.unified_trading import HTTP
from common import BybitTickersResponse, BybitTickersResponseResult,BybitTickersResultTicker
session = HTTP(testnet=True)

def getBybitTickers():
    bybitTickersResponse : BybitTickersResponse 
    bybitTickersResponseResult : BybitTickersResponseResult
    bybitTickersResultList: List[BybitTickersResultTicker] = []
    bybitTickersResultTicker : BybitTickersResultTicker
    response = session.get_tickers(
        category="linear")
    
    for item in response['result']['list']:
        bybitTickersResultTicker = BybitTickersResultTicker(
            item["symbol"],
            item["lastPrice"],
            item["indexPrice"],
            item["markPrice"],
            item["prevPrice24h"],
            item["price24hPcnt"],
            item["highPrice24h"],
            item["lowPrice24h"],
            item["prevPrice1h"],
            item["openInterest"],
            item["openInterestValue"],
            item["turnover24h"],
            item["volume24h"],
            item["fundingRate"],
            item["nextFundingTime"],
            item["predictedDeliveryPrice"],
            item["basisRate"],
            item["deliveryFeeRate"],
            item["deliveryTime"],
            item["ask1Size"],
            item["bid1Price"],
            item["ask1Price"],
            item["bid1Size"],
            item["basis"]

        )
        bybitTickersResultList.append(bybitTickersResultTicker)


    
    bybitTickersResponseResult = BybitTickersResponseResult(response['result']['category'],bybitTickersResultList)

    bybitTickersResponse = BybitTickersResponse(response['retCode'],response['retMsg'],bybitTickersResponseResult,response['retExtInfo'],response['time'])
    #print(bybitTickersResponse.result.list[0].volume24_h)
    return bybitTickersResponse
