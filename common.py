from dataclasses import dataclass
from datetime import (date,datetime,timedelta)
from enum import Enum
from pydantic import BaseModel
from telegram import *

from telegram import (Update,Bot)
import asyncio
from config import(chat_id,telegramAPIKey,strConnection,strConnection2)
import re
from typing import Any, ForwardRef, List, Optional

from config import (bybit_api_key,bybit_secret_key)
from pybit.unified_trading import HTTP
import pandas as pd
from decimal import Decimal, ROUND_DOWN,ROUND_FLOOR
import math

client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,testnet = False)

class AnalyzeResponse:
    source: str
    author:str
    newsItemLink:str
    newsItemDate:datetime
    date: datetime
    analysis:str
    score:int
    pairs:List[str]

    def __init__(self, source: str, author: str,newsItemLink: str,newsItemDate: datetime,analysis: str,score: int,pairs: List[str]):
        self.source = source
        self.author= author
        self.newsItemLink= newsItemLink
        self.newsItemDate= newsItemDate
        self.date= date
        self.analysis = analysis
        self.score = score
        self.pairs = pairs

class Moneda:
    simbolo = ''
    intervalos = []

    def __init__(self, simbolo, intervalos):
        self.simbolo = simbolo
        self.intervalos = intervalos

class CoinOrderbookInfo:
    longStopLoss=0
    shortStopLoss=0
    longEntry=0
    shortEntry=0
    longRiskBenefitRatio=0
    shortRiskBenefitRatio=0
    longDistance=0
    shortDistance=0
    latestPrice = 0

class Order:
    id=0
    symbol=''
    order_type=0
    order_size=0
    price=0
    order_status=0
    take_profit=0
    stop_loss=0
    creation_date=datetime.today()
    order_message = ''
    timeframe = 0

class Position:
    id =0
    symbol =''
    pos_type =0
    pos_size=0
    price=0
    close_price=0
    open_date=datetime.today()
    close_date=datetime.today()
    PnL=0
    order_id=0
    close_status=0
    open_status=0
    pos_status=0

class CandleStick:
    open = 0
    high=0
    low=0
    close=0

coins = [
    Moneda('TRXUSDT',['0.001','0.0001','0.00001']),
    Moneda('MATICUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('XRPUSDT',['0.01','0.001','0.0001']),
    Moneda('LTCUSDT',['1','0.1','0.01']),
    Moneda('VETUSDT',['0.001','0.0001','0.00001']),
    Moneda('AVAXUSDT',['1','0.1','0.01','0.001']),
    Moneda('NEARUSDT',['0.1','0.01','0.001']),
    Moneda('DOTUSDT',['0.1','0.01','0.001']),
    Moneda('ADAUSDT',['0.1','0.01','0.001']),
    Moneda('THETAUSDT',['0.1','0.01','0.001']),
    Moneda('OPUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('OCEANUSDT',['0.01','0.001','0.0001','0.00001']),
    Moneda('AAVEUSDT',['1','0.1','0.01']),
    Moneda('GMTUSDT',['0.01','0.001','0.0001']),
    Moneda('GALUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('C98USDT',['0.01','0.001','0.0001']),
    Moneda('ALPHAUSDT',['0.01','0.001','0.0001','0.00001']),
    Moneda('CRVUSDT',['0.01','0.001']),
    Moneda('SOLUSDT',['1','0.1','0.01','0.001']),
    Moneda('ROSEUSDT',['0.001','0.0001','0.00001']),
    Moneda('KAVAUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('DOGEUSDT',['0.001','0.0001','0.00001']),
    Moneda('LINKUSDT',['0.1','0.01','0.001']),
    Moneda('APTUSDT',['1','0.1','0.01','0.001']),
    Moneda('BNBUSDT',['10','1','0.1','0.01']),
    Moneda('BTCUSDT',['100','50','10','1','0.1']),
    Moneda('ETHUSDT',['100','50','10','1','0.1','0.01']),
    Moneda('MINAUSDT',['0.01','0.001','0.0001']),
    Moneda('EOSUSDT',['0.1','0.01','0.001']),
    Moneda('FETUSDT',['0.01','0.001','0.0001']),
    Moneda('AGIXUSDT',['0.01','0.001','0.0001']),
    Moneda('OMGUSDT',['0.1','0.01','0.001']),
    Moneda('UNIUSDT',['0.1','0.01','0.001']),
    Moneda('IOSTUSDT',['0.001','0.0001','0.00001','0.000001']),
    Moneda('ATOMUSDT',['1','0.1','0.01','0.001']),
    Moneda('XMRUSDT',['10','1','0.1','0.01']),
    Moneda('QNTUSDT',['10','1','0.1','0.01']),
    Moneda('ALGOUSDT',['0.01','0.001','0.0001']),
    Moneda('CKBUSDT',['0.0001','0.00001','0.000001']),
    Moneda('EGLDUSDT',['1','0.1','0.01']),
    Moneda('MASKUSDT',['0.1','0.01','0.001']),
    Moneda('TRUUSDT',['0.001','0.0001','0.00001']),
    Moneda('RLCUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('IMXUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('BNXUSDT',['0.01','0.001']),
    Moneda('BLZUSDT',['0.001','0.0001','0.00001']),
    Moneda('BAKEUSDT',['0.01','0.001','0.0001']),
    Moneda('SKLUSDT',['0.001','0.0001','0.00001']),
    Moneda('ARBUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('HOOKUSDT',['1','0.1','0.01','0.001']),
    Moneda('ZENUSDT',['1','0.1','0.01','0.001']),
    Moneda('NEOUSDT',['1','0.1','0.01','0.001']),
    Moneda('SUSHIUSDT',['0.1','0.01','0.001']),
    Moneda('IOTXUSDT',['0.001','0.0001','0.00001']),
    Moneda('QTUMUSDT',['0.1','0.01','0.001']),
    Moneda('MAGICUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('LITUSDT',['0.01','0.001']),
    Moneda('DYDXUSDT',['0.1','0.01','0.001']),
    Moneda('STXUSDT',['0.01','0.001','0.0001']),
    #Moneda('COCOSUSDT',['0.1','0.01','0.001']),
    Moneda('SSVUSDT',['1','0.1','0.01']),
    Moneda('FTMUSDT',['0.01','0.001','0.0001']),
    Moneda('SXPUSDT',['0.01','0.001','0.0001']),
    Moneda('FXSUSDT',['0.1','0.01','0.001']),
    Moneda('STGUSDT',['0.01','0.001','0.0001']),
    Moneda('XEMUSDT',['0.001','0.0001']),
    Moneda('LDOUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('ONTUSDT',['0.01','0.001','0.0001']),
    Moneda('IDUSDT',['0.01','0.001','0.0001']),
    Moneda('AMBUSDT',['0.001','0.0001','0.00001']),
    Moneda('MKRUSDT',['50','10','1','0.1']),
    Moneda('ICXUSDT',['0.01','0.001','0.0001']),
    Moneda('CFXUSDT',['0.1','0.01','0.001','0.0001'])
    ]

class BybitTickersResultTicker:
    symbol: str
    last_price: str
    index_price: str
    mark_price: str
    prev_price24_h: str
    price24_h_pcnt: str
    high_price24_h: str
    low_price24_h: str
    prev_price1_h: str
    open_interest: int
    open_interest_value: str
    turnover24_h: str
    volume24_h: int
    funding_rate: str
    next_funding_time: str
    predicted_delivery_price: str
    basis_rate: str
    delivery_fee_rate: str
    delivery_time: int
    ask1_size: int
    bid1_price: str
    ask1_price: str
    bid1_size: int
    basis: str

    def __init__(self, symbol: str, last_price: str, index_price: str, mark_price: str, prev_price24_h: str, price24_h_pcnt: str, high_price24_h: str, low_price24_h: str, prev_price1_h: str, open_interest: int, open_interest_value: str, turnover24_h: str, volume24_h: int, funding_rate: str, next_funding_time: str, predicted_delivery_price: str, basis_rate: str, delivery_fee_rate: str, delivery_time: int, ask1_size: int, bid1_price: str, ask1_price: str, bid1_size: int, basis: str) -> None:
        self.symbol = symbol
        self.last_price = last_price
        self.index_price = index_price
        self.mark_price = mark_price
        self.prev_price24_h = prev_price24_h
        self.price24_h_pcnt = price24_h_pcnt
        self.high_price24_h = high_price24_h
        self.low_price24_h = low_price24_h
        self.prev_price1_h = prev_price1_h
        self.open_interest = open_interest
        self.open_interest_value = open_interest_value
        self.turnover24_h = turnover24_h
        self.volume24_h = volume24_h
        self.funding_rate = funding_rate
        self.next_funding_time = next_funding_time
        self.predicted_delivery_price = predicted_delivery_price
        self.basis_rate = basis_rate
        self.delivery_fee_rate = delivery_fee_rate
        self.delivery_time = delivery_time
        self.ask1_size = ask1_size
        self.bid1_price = bid1_price
        self.ask1_price = ask1_price
        self.bid1_size = bid1_size
        self.basis = basis

class BybitKlinesResultKline:
    startTime:str
    openPrice:str
    highPrice:str
    lowPrice:str
    closePrice:str
    volume:str
    turnover:str

    def __init__(self,startTime,openPrice,highPrice,lowPrice,closePrice,volume,turnover):
        self.startTime = startTime
        self.openPrice =openPrice
        self.highPrice =highPrice
        self.lowPrice = lowPrice
        self.closePrice = closePrice
        self.volume = volume
        self.turnover = turnover

class BybitKlinesResponseResult:
    category : str
    symbol : str
    list : List[BybitKlinesResultKline]

    def __init__(self,category:str,symbol:str, list: List[BybitKlinesResultKline]):
        self.category = category
        self.symbol = symbol
        self.list = list



class BybitTickersResponseResult:
    category: str
    list: List[BybitTickersResultTicker]

    def __init__(self, category: str, list: List[BybitTickersResultTicker]) -> None:
        self.category = category
        self.list = list


class RetEXTInfo(BaseModel):
    pass

    


class BybitTickersResponse:
    ret_code: int
    ret_msg: str
    result: BybitTickersResponseResult
    ret_ext_info: RetEXTInfo
    time: int

    def __init__(self, ret_code: int, ret_msg: str, result: BybitTickersResponseResult, ret_ext_info: RetEXTInfo, time: int) -> None:
        self.ret_code = ret_code
        self.ret_msg = ret_msg
        self.result = result
        self.ret_ext_info = ret_ext_info
        self.time = time


class BybitKlinesResponse:
    ret_code: int
    ret_msg: str
    result: BybitKlinesResponseResult
    ret_ext_info: RetEXTInfo
    time: int

    def __init__(self, ret_code: int, ret_msg: str, result: BybitKlinesResponseResult, ret_ext_info: RetEXTInfo, time: int) -> None:
        self.ret_code = ret_code
        self.ret_msg = ret_msg
        self.result = result
        self.ret_ext_info = ret_ext_info
        self.time = time

EntranceZone = ForwardRef('EntranceZone')
class PriceGroup(BaseModel):
    rangeValue: float
    prices: List[float]
    minPrice : float
    maxPrice : float    
    sellZone : Optional[EntranceZone] = None
    buyZone : Optional[EntranceZone] = None

    # def __init__(self, rangeValue: float, prices: List[float]) -> None:
    #     self.rangeValue = rangeValue
    #     self.prices = prices

class EntranceZone(BaseModel):    
    minPrice : float
    maxPrice : float
    zoneType: int
    # priceGroup: PriceGroup | None
    # def __init__(self, minPrice: float, maxPrice: float, zoneType:int,priceGroup : PriceGroup) -> None:
    #     self.minPrice = minPrice
    #     self.maxPrice = maxPrice
    #     self.zoneType = zoneType
    #     self.priceGroup = priceGroup

class zoneType(Enum):
    buy = 0
    sell = 1

class CalculationMode(Enum):
    percentage = 0
    divisor = 1

class Strategies(Enum):
    bollingerAndRSI = 0
    priceAction = 1

class PriceActionCalibrationDto(BaseModel):
    rangeDivisor: float
    precision: int
    temporality: str
    minBouncesAmount:int
    calculationMode : int
    percentage: float
    depth: int

    # def __init__(self, divisor: float, precision:int,temporality : int) -> None:
    #     self.divisor = divisor
    #     self.precision = precision
    #     self.temporality = temporality

class BybitPositionsResponseResultItem(BaseModel):
    positionIdx: int
    riskId: int
    riskLimitValue: str
    symbol: str
    side: str
    size: str
    avgPrice: str
    positionValue: str
    tradeMode: int
    positionStatus: str
    autoAddMargin: int
    adlRankIndicator: int
    leverage: str
    positionBalance: str
    markPrice: str
    liqPrice: str
    bustPrice: str
    positionMM: str
    positionIM: str
    tpslMode: str
    takeProfit: str
    stopLoss: str
    trailingStop: str
    unrealisedPnl: str
    curRealisedPnl: str
    cumRealisedPnl: str
    seq: float
    isReduceOnly: bool
    mmrSysUpdateTime: str
    leverageSysUpdatedTime: str
    sessionAvgPrice: str
    createdTime: str
    updatedTime: str

class BybitPositionsResponseResult(BaseModel):
    list : List[BybitPositionsResponseResultItem]
    nextPageCursor: str
    category: str

class BybitPositionsResponse(BaseModel):
    ret_code: int
    ret_msg: str
    result: BybitPositionsResponseResult
    ret_ext_info: RetEXTInfo | None
    time: int

class BybitOrdersResponseResultItem(BaseModel):
    order_id: str
    order_link_id: str
    block_trade_id: str
    symbol: str
    price: str
    qty: str
    side: str
    is_leverage: str
    position_idx: int
    order_status: str
    cancel_type: str
    reject_reason: str
    avg_price: str
    leaves_qty: str
    leaves_value: str
    cum_exec_qty: str
    cum_exec_value: int
    cum_exec_fee: int
    time_in_force: str
    order_type: str
    stop_order_type: str
    order_iv: str
    trigger_price: str
    take_profit: str
    stop_loss: str
    tp_trigger_by: str
    sl_trigger_by: str
    trigger_direction: int
    trigger_by: str
    last_price_on_created: str
    reduce_only: bool
    close_on_trigger: bool
    smp_type: str
    smp_group: int
    smp_order_id: str
    tpsl_mode: str
    tp_limit_price: str
    sl_limit_price: str
    place_type: str
    created_time: str
    updated_time: str

class BybitOrdersResponseResult(BaseModel):
    list : List[BybitOrdersResponseResultItem]
    nextPageCursor: str
    category: str

class BybitOrdersResponse(BaseModel):
    ret_code: int
    ret_msg: str
    result: BybitOrdersResponseResult
    ret_ext_info: RetEXTInfo | None
    time: int

class LeverageFilter(BaseModel):
    min_leverage: int
    max_leverage: float
    leverage_step: float
class LotSizeFilter(BaseModel):
    max_order_qty: float
    min_order_qty: float
    qty_step: float
    post_only_max_order_qty: float
    max_mkt_order_qty: float
    min_notional_value: float
class PriceFilter(BaseModel):
    min_price: float
    max_price: float
    tick_size: float
class BybitInstrumentsInfoResponseResultListItem(BaseModel):
    symbol: str
    contract_type: str
    status: str
    base_coin: str
    quote_coin: str
    launch_time: str
    delivery_time: int
    delivery_fee_rate: str
    price_scale: int
    leverage_filter: LeverageFilter
    price_filter: PriceFilter
    lot_size_filter: LotSizeFilter
    unified_margin_trade: bool
    funding_interval: int
    settle_coin: str
    copy_trading: str
    upper_funding_rate: str
    lower_funding_rate: str
    is_pre_listing: bool
    pre_listing_info: None


class BybitInstrumentsInfoResponseResult(BaseModel):
    category: str
    list: List[BybitInstrumentsInfoResponseResultListItem]
    next_page_cursor: str


class BybitInstrumentsInfoResponse(BaseModel):
    ret_code: int
    ret_msg: str
    result: BybitInstrumentsInfoResponseResult
    ret_ext_info: RetEXTInfo | None
    time: int


class BybitPositionsWSResponseResultItem:

    def __init__(self, positionIdx=None, tradeMode=None, riskId=None, riskLimitValue=None,
                 symbol=None, side=None, size=None, entryPrice=None, sessionAvgPrice=None,
                 leverage=None, positionValue=None, positionBalance=None, markPrice=None,
                 positionIM=None, positionMM=None, takeProfit=None, stopLoss=None,
                 trailingStop=None, unrealisedPnl=None, cumRealisedPnl=None,
                 curRealisedPnl=None, createdTime=None, updatedTime=None, tpslMode=None,
                 liqPrice=None, bustPrice=None, category=None, positionStatus=None,
                 adlRankIndicator=None, autoAddMargin=None, leverageSysUpdatedTime=None,
                 mmrSysUpdatedTime=None, seq=None, isReduceOnly=None):
                self.positionIdx = positionIdx
                self.tradeMode = tradeMode
                self.riskId = riskId
                self.riskLimitValue = riskLimitValue
                self.symbol = symbol
                self.side = side
                self.size = size
                self.entryPrice = entryPrice
                self.sessionAvgPrice = sessionAvgPrice
                self.leverage = leverage
                self.positionValue = positionValue
                self.positionBalance = positionBalance
                self.markPrice = markPrice
                self.positionIM = positionIM
                self.positionMM = positionMM
                self.takeProfit = takeProfit
                self.stopLoss = stopLoss
                self.trailingStop = trailingStop
                self.unrealisedPnl = unrealisedPnl
                self.cumRealisedPnl = cumRealisedPnl
                self.curRealisedPnl = curRealisedPnl
                self.createdTime = createdTime
                self.updatedTime = updatedTime
                self.tpslMode = tpslMode
                self.liqPrice = liqPrice
                self.bustPrice = bustPrice
                self.category = category
                self.positionStatus = positionStatus
                self.adlRankIndicator = adlRankIndicator
                self.autoAddMargin = autoAddMargin
                self.leverageSysUpdatedTime = leverageSysUpdatedTime
                self.mmrSysUpdatedTime = mmrSysUpdatedTime
                self.seq = seq
                self.isReduceOnly = isReduceOnly

   
    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)
class BybitPositionsWSResponseResult:
    def __init__(self, id=None, topic=None, creationTime=None, data=None):
        self.id = id
        self.topic = topic
        self.creationTime = creationTime
        self.data = [BybitPositionsWSResponseResultItem.from_dict(item) for item in data] if data else []

    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)
    


class BybitOrders_Response_Result_Item:

    def __init__(self
        ,symbol= None
        ,orderType= None
        ,orderLinkId= None
        ,slLimitPrice= None
        ,orderId= None
        ,cancelType= None
        ,avgPrice= None
        ,stopOrderType= None
        ,lastPriceOnCreated= None
        ,orderStatus= None
        ,createType= None
        ,takeProfit= None
        ,cumExecValue= None
        ,tpslMode = None
        ,smpType = None
        ,triggerDirection = None
        ,blockTradeId = None
        ,isLeverage = None
        ,rejectReason = None
        ,price = None
        ,orderIv = None
        ,createdTime = None
        ,tpTriggerBy = None
        ,positionIdx = None
        ,timeInForce = None
        ,leavesValue = None
        ,updatedTime = None
        ,side = None
        ,smpGroup = None
        ,triggerPrice = None
        ,tpLimitPrice = None
        ,cumExecFee = None
        ,leavesQty = None
        ,slTriggerBy = None
        ,closeOnTrigger = None
        ,placeType = None
        ,cumExecQty = None
        ,reduceOnly = None
        ,qty = None
        ,stopLoss = None
        ,marketUnit = None
        ,smpOrderId = None
        ,triggerBy = None
    ):
        self.symbol= symbol
        self.orderType= orderType
        self.orderLinkId= orderLinkId
        self.slLimitPrice= slLimitPrice
        self.orderId= orderId
        self.cancelType= cancelType
        self.avgPrice= avgPrice
        self.stopOrderType= stopOrderType
        self.lastPriceOnCreated= lastPriceOnCreated
        self.orderStatus= orderStatus
        self.createType= createType
        self.takeProfit= takeProfit
        self.cumExecValue= cumExecValue
        self.tpslMode = tpslMode
        self.smpType=smpType
        self.triggerDirection=triggerDirection
        self.blockTradeId=blockTradeId
        self.isLeverage=isLeverage
        self.rejectReason=rejectReason
        self.price=price
        self.orderIv=orderIv
        self.createdTime=createdTime
        self.tpTriggerBy=tpTriggerBy
        self.positionIdx=positionIdx
        self.timeInForce=timeInForce
        self.leavesValue=leavesValue
        self.updatedTime=updatedTime
        self.side=side
        self.smpGroup=smpGroup
        self.triggerPrice=triggerPrice
        self.tpLimitPrice=tpLimitPrice
        self.cumExecFee=cumExecFee
        self.leavesQty=leavesQty
        self.slTriggerBy=slTriggerBy
        self.closeOnTrigger=closeOnTrigger
        self.placeType=placeType
        self.cumExecQty=cumExecQty
        self.reduceOnly=reduceOnly
        self.qty=qty
        self.stopLoss=stopLoss
        self.marketUnit=marketUnit
        self.smpOrderId=smpOrderId
        self.triggerBy=triggerBy


    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)

class BybitOrdersResponse_Result:

    def __init__(self, list=None, nextPageCursor=None, category=None):
        self.list = [BybitOrders_Response_Result_Item.from_dict(item) for item in list] if list else []
        self.nextPageCursor = nextPageCursor
        self.category = category

    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)

class BybitOrders_Response:
    def __init__(self, retCode=None, retMsg=None, result=None, retExtInfo=None,time=None):
        self.retCode = retCode
        self.retMsg = retMsg
        self.result = BybitOrdersResponse_Result.from_dict(result)
        self.retExtInfo = retExtInfo
        self.time = time

    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)
    
class simpleCandleStick:
    def __init__(self,open,close,high,low):
        self.open = open
        self.close = close
        self.high = high
        self.low  = low
  
    @classmethod
    def from_dict(cls, obj):
        return cls(**obj)
coin = [
    Moneda('NEOUSDT',['1','0.1','0.01','0.001'])
    ]


def get_order_book_strategy_coins():
    monedas = []
    x = Moneda('BTCUSDT',['0.1'])
    for m in coins:
        x= m
        if((x.simbolo != 'BTCUSDT')& (x.simbolo != 'ETHUSDT') & (x.simbolo!= 'XMRUSDT') & (x.simbolo!= 'QNTUSDT') & (x.simbolo!= 'BNBUSDT')& (x.simbolo!= 'MKRUSDT')):
            monedas.append(x)
        
    return monedas

order_book_strategy_coins = get_order_book_strategy_coins()

async def enviar_mensaje(chat_id, mensaje):
    bot = Bot(token=telegramAPIKey)
    await bot.send_message(chat_id=chat_id, text=mensaje)


async def SendTelegramMessage(message):
    mensaje = "Hola, esto es un mensaje enviado desde mi bot de Telegram."
    await enviar_mensaje(chat_id, message)




def subtratcFromCurrentDate(*args):
    currentDate = datetime.now()

    for arg in args:

        quantity,unity = re.match(r"(\d+)([smhdw])",arg).groups()

        if unity == "s":
            currentDate -= timedelta(seconds= int(quantity))
        elif unity == "m":
            currentDate -= timedelta(minutes= int(quantity))
        elif unity == "h":
            currentDate -= timedelta(hours= int(quantity))
        elif unity == "d":
            currentDate -= timedelta(days= int(quantity))
        elif unity == "w":
            currentDate -= timedelta(weeks= int(quantity))

    return currentDate

def CreateOrder(symbol,side,order_type,qty,stop_loss,take_profit):
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    response = client.place_order(
        category="linear",
        symbol=symbol,
        side=side,
        order_type=order_type,
        qty=qty,
        timeInForce="GoodTillCancel",
        positionIdx=pIdx,
        #takeProfit=take_profit,
        #stopLoss=stop_loss
        )
    print("orden creada con éxito")

def qty_step(price,priceScale,tickSize):
    precission = Decimal(f"{10** priceScale}")
    tickdec=Decimal(f"{tickSize}")
    precio_final = (Decimal(f"{price}")*precission)/precission
    precide = precio_final.quantize(Decimal(f"{1/precission}"),rounding=ROUND_FLOOR)
    operaciondec=(precide/tickdec).quantize(Decimal('1'),rounding=ROUND_FLOOR)*tickdec
    result = float(operaciondec)

    return result

def SetStopLoss(symbol,sl,side,priceScale,tickSize):
    sl = qty_step(sl,priceScale,tickSize)
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    order = client.set_trading_stop(category="linear",symbol=symbol,stopLoss=sl,slTriggerB="LastPrice",positionIdx=pIdx)
    return order

def SetTakeprofit(symbol,tp,side,qty,priceScale,tickSize):
    price = qty_step(tp,priceScale,tickSize)
    pIdx = 0
    if side == "Sell":
        pIdx=1
    else:
        pIdx=2
    order=client.place_order(category="linear",symbol=symbol,side=side,orderType="Limit",reduceOnly=True,qty=qty,price=price,positionIdx=pIdx)
    return order

def SetLimitOrder(symbol,tp,side,qty,priceScale,tickSize):
    price = qty_step(tp,priceScale,tickSize)
    pIdx = 0
    if side == "Sell":
        pIdx=2
    else:
        pIdx=1
    order=client.place_order(category="linear",symbol=symbol,side=side,orderType="Limit",qty=qty,price=price,positionIdx=pIdx)
    return order

def SetHedgeOrder(symbol,tp,side,qty,priceScale,tickSize):
    price = qty_step(tp,priceScale,tickSize)
    pIdx = 0
    triggerDirection = 1
    if side == "Sell":
        pIdx=2
        triggerDirection = 2
    else:
        pIdx=1
        triggerDirection = 1
    order=client.place_order(category="linear",symbol=symbol,side=side,orderType="Market",qty=qty,positionIdx=pIdx,triggerPrice = price,triggerDirection = triggerDirection)
    return order

def qty_precission(qty,precission):
    qty = math.floor(qty/precission) * precission
    return qty

def getMarginBalance():
    response = client.get_wallet_balance(accountType="UNIFIED",coin = "USDT")
    if response["retCode"] == 0:
        margin_balance = response["result"]["list"]
    # print("Saldo de margen por moneda:")
    # print(response)
    
    moneda=margin_balance[0]['coin'][0]['coin']
    margenTotal = float(margin_balance[0]['totalEquity'])
    print(f"Moneda: {moneda}, Total: {margenTotal}")
    return margenTotal

def getUsdtOrderSize(marginPercentage=33):
    balance = getMarginBalance()
    orderSize = balance * (marginPercentage/100)
    return round(orderSize)

def obtener_datos_historicos(symbol,interval,limite=200):
    response= client.get_kline(symbol=symbol,interval=interval,limite=limite)
    if "result" in response:
        data = pd.DataFrame(response['result']['list']).astype(float)
        data[0] = pd.to_datetime(data[0],unit='ms')
        data.set_index(0,inplace=True)
        data= data[::-1].reset_index(drop=True)
        return data
    else:
        raise Exception("Error al obtener datos históricos: "+ str(response))
    
def calculateRelativePercentageDiff(initial, final):
    return ((final - initial)/initial) * 100
    
def CalculateMovingAverage(data,window=20):
    data['MA'] = data[4].rolling(window=window).mean()
    return data.iloc[-1]
    
def calcular_bandas_bollinger(data,ventana=20,desviacion=2):
    data['MA'] = data[4].rolling(window=ventana).mean()
    data['UpperBand'] = data['MA'] + (data[4].rolling(window=ventana).std() * desviacion)
    data['LowerBand'] = data['MA'] - (data[4].rolling(window=ventana).std() * desviacion)
    return data.iloc[-1]

def calculate_rsiV2(data):

    n = 14

    deltas = data[4].diff()
    gain = deltas.where(deltas > 0, 0)
    loss = -deltas.where(deltas < 0, 0)

    avg_gain = gain.rolling(window=n, min_periods=n).mean()
    avg_loss = loss.rolling(window=n, min_periods=n).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

def safe_float(value):
    return float(value) if value and value != '' else 0.0

