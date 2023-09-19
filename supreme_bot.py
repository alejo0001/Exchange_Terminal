import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from common import(order_book_strategy_coins,Moneda,CoinOrderbookInfo,coins)
import order_book_strategy
import orders
import exchange_info


key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)
open_positions=[]
orders_response = []
try:
    response = um_futures_client.get_position_risk(recvWindow=6000)
    #logging.info(response)
    for c in response:
        if(float(c['entryPrice']) > 0):
            print(str(c))
            open_positions.append(c)

    for p in open_positions:
        position_orders=[]
        orders_response = um_futures_client.get_all_orders(symbol=p['symbol'], recvWindow=2000)
        print('\n')
        if(len(orders_response)>0):
            for o in orders_response:
                if(o['status']=='NEW'):
                    position_orders.append(o)

            if(len(position_orders)==0):
                #print(str(position_orders))
                side=''
                c=Moneda('BTCUSDT',['100','50','10','1','0.1'])
                for i in coins:
                    if(i.simbolo == p['symbol']):
                        c=i
                points_info=order_book_strategy.getPointsInfo(c)
                take_profit_price=0
                stop_loss_price=0
                
                #for short, set "BUY" side, else "SELL":
                if((float(p['entryPrice']) < float(p['markPrice'])) & (float(p['unRealizedProfit'])<0)):
                    side='BUY'
                elif((float(p['entryPrice']) > float(p['markPrice'])) & (float(p['unRealizedProfit'])<0)):
                    side='SELL'
                elif((float(p['entryPrice']) < float(p['markPrice'])) & (float(p['unRealizedProfit'])>0)):
                    side='SELL'
                elif((float(p['entryPrice']) > float(p['markPrice'])) & (float(p['unRealizedProfit'])>0)):
                    side='BUY'
                if(side=='BUY'):
                    take_profit_price=points_info.longEntry
                    stop_loss_price=points_info.shortStopLoss
                else:
                    take_profit_price=points_info.shortEntry
                    stop_loss_price=points_info.longStopLoss

                max_leverage = exchange_info.get_max_leverage(p['symbol'])
                orders.make_position_order(p['symbol'],side,'STOP_MARKET',float(p['positionAmt']),stop_loss_price,0,0,max_leverage)
                orders.make_position_order(p['symbol'],side,'TAKE_PROFIT_MARKET',float(p['positionAmt']),take_profit_price,0,0,max_leverage)


except ClientError as error:
    logging.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )