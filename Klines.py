from typing import List
from pybit.unified_trading import HTTP
from config import(bybit_api_key,bybit_secret_key)
from common import BybitKlinesResponse, BybitKlinesResponseResult, BybitKlinesResultKline
session = HTTP( testnet=False,    api_key=bybit_api_key,    api_secret=bybit_secret_key,)

def getBybitKlines(symbol : str, limit : int, interval : int):

    bybitKlinesResponse : BybitKlinesResponse
    bybitKlinesResponseResult : BybitKlinesResponseResult
    bybitKlinesResultKline : BybitKlinesResultKline
    bybitKlinesResultKlines: List[BybitKlinesResultKline] = []
    response = session.get_kline(
        category="linear",
        symbol=symbol,
        interval=interval,
        # start=1670601600000,
        # end=1670608800000,
        limit = limit
    )

    for item in response['result']['list']:
        bybitKlinesResultKline = BybitKlinesResultKline(
            startTime = item[0],
            openPrice = item[1],
            highPrice = item[2],
            lowPrice = item[3],
            closePrice = item[4],
            volume = item[5],
            turnover = item[6]
        )
        #print('kline '+symbol+': '+str(item))
        bybitKlinesResultKlines.append(bybitKlinesResultKline)

    bybitKlinesResponseResult = BybitKlinesResponseResult(
        response['result']['category'],
        response['result']['symbol'],
        bybitKlinesResultKlines
    )
    bybitKlinesResponse = BybitKlinesResponse(
        response['retCode'],
        response['retMsg'],
        bybitKlinesResponseResult,
        response['retExtInfo'],
        response['time']
    )

    return bybitKlinesResponse

