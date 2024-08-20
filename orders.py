import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from common import(BybitOrdersResponse, BybitOrdersResponseResult, BybitOrdersResponseResultItem, order_book_strategy_coins,Moneda,CoinOrderbookInfo)
import exchange_info
from typing import List
from pybit.unified_trading import HTTP
from common import BybitPositionsResponse, BybitPositionsResponseResult, BybitPositionsResponseResultItem
from config import(bybit_api_key,bybit_secret_key)

key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)

def make_order(symbol='BTCUSDT',side='SELL',type='LIMIT',quantity = 0,price=0,stopPrice = 0,takeProfitPrice=0,leverage=20):
    try:
        final_quantity = 0
        precision = exchange_info.get_precision_info(symbol)
        final_quantity = round(quantity/price,precision)
  

        response = um_futures_client.new_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=quantity,
            timeInForce="GTC",
            price=price,
            leverage =leverage
        )
     
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

def make_position_order(symbol='BTCUSDT',side='SELL',type='LIMIT',quantity = 0,price=0,stopPrice = 0,takeProfitPrice=0,leverage=20):
    try:
        final_quantity = 0
        precision = exchange_info.get_precision_info(symbol)
        final_quantity = round(quantity/price,precision)

        response = um_futures_client.new_order(
            symbol=symbol,
            side=side,
            type=type,
            quantity=final_quantity,
            stopPrice=price,
            closePosition =True,
            leverage =leverage
        )
    except ClientError as error:
        logging.error(
            "Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )

#make_order('BTCUSDT','SELL','LIMIT',0.001,28000,28100,27800,50)



session = HTTP(
    testnet=False,
    api_key=bybit_api_key,
    api_secret=bybit_secret_key
)

def getBybitOrders(symbol:str=''):
    bybitOrdersResponse: BybitOrdersResponse
    bybitOrdersResponseResult : BybitOrdersResponseResult
    bybitOrdersResultList: List[BybitOrdersResponseResultItem] = []
    if(symbol == ''):
        orders = session.get_open_orders(
                        category="linear",
                        limit= 50
                    )
    
    else:
        orders = session.get_open_orders(
                        category="linear",
                        symbol=symbol,
                        limit= 50
                    )
    for item in orders['result']['list']:
        if(float(item['qty'])> 0 ):
            bybitOrdersResponseResultItem = BybitOrdersResponseResultItem(
                order_id = item["orderId"],
                order_link_id = item["orderLinkId"],
                block_trade_id = item["blockTradeId"],
                symbol = item["symbol"],
                price = item["price"],
                qty = item["qty"],
                side = item["side"],
                is_leverage = item["isLeverage"],
                position_idx = item["positionIdx"],
                order_status = item["orderStatus"],
                cancel_type = item["cancelType"],
                reject_reason = item["rejectReason"],
                avg_price = item["avgPrice"],
                leaves_qty = item["leavesQty"],
                leaves_value = item["leavesValue"],
                cum_exec_qty = item["cumExecQty"],
                cum_exec_value = item["cumExecValue"],
                cum_exec_fee = item["cumExecFee"],
                time_in_force = item["timeInForce"],
                order_type = item["orderType"],
                stop_order_type = item["stopOrderType"],
                order_iv = item["orderIv"],
                trigger_price = item["triggerPrice"],
                take_profit = item["takeProfit"],
                stop_loss = item["stopLoss"],
                tp_trigger_by = item["tpTriggerBy"],
                sl_trigger_by = item["slTriggerBy"],
                trigger_direction = item["triggerDirection"],
                trigger_by = item["triggerBy"],
                last_price_on_created = item["lastPriceOnCreated"],
                reduce_only = item["reduceOnly"],
                close_on_trigger = item["closeOnTrigger"],
                smp_type = item["smpType"],
                smp_group = item["smpGroup"],
                smp_order_id = item["smpOrderId"],
                tpsl_mode = item["tpslMode"],
                tp_limit_price = item["tpLimitPrice"],
                sl_limit_price = item["slLimitPrice"],
                place_type = item["placeType"],
                created_time = item["createdTime"],
                updated_time = item["updatedTime"],
            )
            bybitOrdersResultList.append(bybitOrdersResponseResultItem)
    bybitOrdersResponseResult = BybitOrdersResponseResult(
        list = bybitOrdersResultList,
        nextPageCursor = orders['result']['nextPageCursor'],
        category=orders['result']['category']
        )
    bybitOrdersResponse = BybitOrdersResponse(
        ret_code= int(orders['retCode']),
        ret_msg = orders['retMsg'],
        result = bybitOrdersResponseResult,
        ret_ext_info = orders['retExtInfo'],
        time = orders['time'])

    return bybitOrdersResponse