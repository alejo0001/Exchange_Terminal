from typing import List
from pybit.unified_trading import HTTP
from common import BybitInstrumentsInfoResponse, BybitInstrumentsInfoResponseResult, BybitInstrumentsInfoResponseResultListItem, BybitTickersResponse, BybitTickersResponseResult,BybitTickersResultTicker, LeverageFilter, LotSizeFilter, PriceFilter
from config import(bybit_api_key,bybit_secret_key)
session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)

def getBybitTickers(symbol : str = ''):
    bybitTickersResponse : BybitTickersResponse 
    bybitTickersResponseResult : BybitTickersResponseResult
    bybitTickersResultList: List[BybitTickersResultTicker] = []
    bybitTickersResultTicker : BybitTickersResultTicker
    if(symbol == ''):
        response = session.get_tickers(
            category="linear")
    else:
        response = session.get_tickers(
        category="linear",
        symbol = symbol
        )
    
    for item in response['result']['list']:
        bybitTickersResultTicker = BybitTickersResultTicker(
            symbol= item["symbol"],
            last_price= item["lastPrice"],
            index_price= item["indexPrice"],
            mark_price= item["markPrice"],
            prev_price24_h= item["prevPrice24h"],
            price24_h_pcnt= item["price24hPcnt"],
            high_price24_h= item["highPrice24h"],
            low_price24_h= item["lowPrice24h"],
            prev_price1_h= item["prevPrice1h"],
            open_interest= item["openInterest"],
            open_interest_value= item["openInterestValue"],
            turnover24_h= item["turnover24h"],
            volume24_h= item["volume24h"],
            funding_rate= item["fundingRate"],
            next_funding_time= item["nextFundingTime"],
            predicted_delivery_price= item["predictedDeliveryPrice"],
            basis_rate= item["basisRate"],
            delivery_fee_rate= item["deliveryFeeRate"],
            delivery_time= item["deliveryTime"],
            ask1_size= item["ask1Size"],
            bid1_price= item["bid1Price"],
            ask1_price= item["ask1Price"],
            bid1_size= item["bid1Size"],
            basis= item["basis"]

        )
        bybitTickersResultList.append(bybitTickersResultTicker)


    
    bybitTickersResponseResult = BybitTickersResponseResult(response['result']['category'],bybitTickersResultList)

    bybitTickersResponse = BybitTickersResponse(response['retCode'],response['retMsg'],bybitTickersResponseResult,response['retExtInfo'],response['time'])
    #print(bybitTickersResponse.result.list[0].volume24_h)
    return bybitTickersResponse

def getBybitInstrumentsInfo(symbol:str=''):
    bybitInstrumentsInfoResponse : BybitInstrumentsInfoResponse
    bybitInstrumentsInfoResponseResult : BybitInstrumentsInfoResponseResult
    bybitInstrumentsInfoResponseResultList :List[BybitInstrumentsInfoResponseResultListItem] = []
    if(symbol == ''):
        response = session.get_instruments_info(
            category="linear"
        )
    else:
        response = session.get_instruments_info(
            category="linear",
            symbol = symbol
        )
    print('instrument response: '+str(response))
    for item in response['result']['list']:
        leverage_filter_data = item['leverageFilter']
        priceFilter_data = item['priceFilter']
        lotSizeFilter_data = item['lotSizeFilter']
        leverageFilter = LeverageFilter(
            min_leverage = int(leverage_filter_data['minLeverage']),
            max_leverage = float(leverage_filter_data['maxLeverage']),
            leverage_step = float(leverage_filter_data['leverageStep'])
        )

        priceFilter = PriceFilter(
            min_price = float(priceFilter_data['minPrice']),
            max_price = float(priceFilter_data['maxPrice']),
            tick_size = float(priceFilter_data['tickSize']),
        )
        lotSizeFilter = LotSizeFilter(
            max_order_qty = float(lotSizeFilter_data["maxOrderQty"]),
            min_order_qty = float(lotSizeFilter_data["minOrderQty"]),
            qty_step = float(lotSizeFilter_data["qtyStep"]),
            post_only_max_order_qty = float(lotSizeFilter_data["postOnlyMaxOrderQty"]),
            max_mkt_order_qty = float(lotSizeFilter_data["maxMktOrderQty"]),
            min_notional_value = float(lotSizeFilter_data["minNotionalValue"]),
        )
        bybitInstrumentsInfoResponseResultListItem = BybitInstrumentsInfoResponseResultListItem(
            symbol= item["symbol"],
            contract_type= item["contractType"],
            status= item["status"],
            base_coin= item["baseCoin"],
            quote_coin= item["quoteCoin"],
            launch_time= item["launchTime"],
            delivery_time= item["deliveryTime"],
            delivery_fee_rate= item["deliveryFeeRate"],
            price_scale= item["priceScale"],
            leverage_filter= leverageFilter,
            price_filter= priceFilter,
            lot_size_filter= lotSizeFilter,
            unified_margin_trade= item["unifiedMarginTrade"],
            funding_interval= item["fundingInterval"],
            settle_coin= item["settleCoin"],
            copy_trading= item["copyTrading"],
            upper_funding_rate= item["upperFundingRate"],
            lower_funding_rate= item["lowerFundingRate"],
            is_pre_listing = item['isPreListing'],
            pre_listing_info = item['preListingInfo']
        )
        bybitInstrumentsInfoResponseResultList.append(bybitInstrumentsInfoResponseResultListItem)
    bybitInstrumentsInfoResponseResult = BybitInstrumentsInfoResponseResult(
        category= response['result']['category'],
        list=bybitInstrumentsInfoResponseResultList,
        next_page_cursor = response['result']['nextPageCursor']
        )
    bybitInstrumentsInfoResponse = BybitInstrumentsInfoResponse(
        ret_code= int(response['retCode']),
        ret_msg = response['retMsg'],
        result = bybitInstrumentsInfoResponseResult,
        ret_ext_info = response['retExtInfo'],
        time = int(response['time'])
        )

    return bybitInstrumentsInfoResponse

