from typing import List
from pybit.unified_trading import HTTP
from common import BybitPositionsResponse, BybitPositionsResponseResult, BybitPositionsResponseResultItem
from config import(bybit_api_key,bybit_secret_key)
session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)

def getBybitPositions(symbol:str=''):
    bybitPositionsResponse: BybitPositionsResponse
    bybitPositionsResponseResult : BybitPositionsResponseResult
    bybitPositionsResultList: List[BybitPositionsResponseResultItem] = []
    if(symbol == ''):
        pos = session.get_positions(
        category="linear"
    )
    else:
        pos = session.get_positions(
            category="linear",
            symbol=symbol,
        )
    for item in pos['result']['list']:
        if(float(item['size'])> 0 ):
            bybitPositionsResponseResultItem = BybitPositionsResponseResultItem(
                positionIdx = item["positionIdx"],
                riskId = item["riskId"],
                riskLimitValue = item["riskLimitValue"],
                symbol = item["symbol"],
                side = item["side"],
                size = item["size"],
                avgPrice = item["avgPrice"],
                positionValue = item["positionValue"],
                tradeMode = item["tradeMode"],
                positionStatus = item["positionStatus"],
                autoAddMargin = item["autoAddMargin"],
                adlRankIndicator = item["adlRankIndicator"],
                leverage = item["leverage"],
                positionBalance = item["positionBalance"],
                markPrice = item["markPrice"],
                liqPrice = item["liqPrice"],
                bustPrice = item["bustPrice"],
                positionMM = item["positionMM"],
                positionIM = item["positionIM"],
                tpslMode = item["tpslMode"],
                takeProfit = item["takeProfit"],
                stopLoss = item["stopLoss"],
                trailingStop = item["trailingStop"],
                unrealisedPnl = item["unrealisedPnl"],
                curRealisedPnl = item["curRealisedPnl"],
                cumRealisedPnl = item["cumRealisedPnl"],
                seq = item["seq"],
                isReduceOnly = item["isReduceOnly"],
                mmrSysUpdateTime = item["mmrSysUpdatedTime"],
                leverageSysUpdatedTime = item["leverageSysUpdatedTime"],
                sessionAvgPrice = item["sessionAvgPrice"],
                createdTime = item["createdTime"],
                updatedTime = item["updatedTime"],
            )
            bybitPositionsResultList.append(bybitPositionsResponseResultItem)
    bybitPositionsResponseResult = BybitPositionsResponseResult(
        list = bybitPositionsResultList,
        nextPageCursor = pos['result']['nextPageCursor'],
        category=pos['result']['category']
        )
    bybitPositionsResponse = BybitPositionsResponse(
        ret_code= int(pos['retCode']),
        ret_msg = pos['retMsg'],
        result = bybitPositionsResponseResult,
        ret_ext_info = pos['retExtInfo'],
        time = pos['time'])

    return bybitPositionsResponse