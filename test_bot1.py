from common import (Position,strConnection2,Order,coins,CoinOrderbookInfo,Moneda)
import pyodbc
from datetime import(datetime)
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from order_book_strategy import getPointsInfo
import logging
import exchange_info
import powerfull_pattern_strategy


key = ""
secret = ""

timeframe = '3m'

um_futures_client = UMFutures(key=key, secret=secret)

def closePositionDB(position = Position(),closePrice = 0,positionSide =0):
    pnL = 0
    maker_commission = 0.04
    net_entry_price = (float(position.price) * float(position.pos_size))-(float(maker_commission) *(float(position.price) * float(position.pos_size)))
    current_value = float(closePrice) * float(position.pos_size)
    net_price = float(current_value) -(float(maker_commission) *float(current_value))
    if(float(positionSide) == 0):
        PnL = float(net_price) - float(net_entry_price)
    else:
        PnL = float(net_entry_price) - float(net_price)

    
    try:
        cursor = connection.cursor()
        sql =  cursor.execute("UPDATE POSITIONS SET pos_status = 1, PnL = "+str(PnL)+", close_date='"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"', close_price = "+str(closePrice)+" WHERE id = "+str(position.id))
        connection.commit()
        
    except Exception as ex:
        print(ex)

def openPositionDB(order = Order()):
    try:
        cursor = connection.cursor()
        sql =  cursor.execute("INSERT INTO POSITIONS (symbol,pos_type,pos_size,price,open_date,order_id,open_status,pos_status)values('"+str(order.symbol)+"',"+str(order.order_type)+","+str(order.order_size)+","+str(order.price)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"',"+str(order.id)+",1,0)")
        connection.commit()
        

        sql =  cursor.execute("UPDATE ORDERS SET order_status = 1 WHERE id = "+str(order.id))
        connection.commit()
        
    except Exception as ex:
        print(ex)

def cancelOrder(order = Order()):
    try:
        sql =  cursor.execute("UPDATE ORDERS SET order_status = 2 WHERE id = "+str(order.id))
        connection.commit()
        
    except Exception as ex:
        print(ex)

try:
    connection = pyodbc.connect(strConnection2)
    
    cursor = connection.cursor()
    positions =  cursor.execute("SELECT p.*, o.timeframe FROM POSITIONS p LEFT JOIN ORDERS o ON p.order_id = o.id WHERE p.pos_status = 0 AND o.timeframe = "+timeframe.split('m')[0])
    rows = cursor.fetchall()
    
    position = Position()
    order = Order()
    positionsList=[]
    active_symbols = []
    last_price = 0

    for r in rows:
        
        take_profit=0
        stop_loss=0
        position.id = r[0]
        position.symbol = r[1]
        active_symbols.append(position.symbol)
        
        response = um_futures_client.mark_price(position.symbol)
        last_price = float(response['indexPrice']) 


    filterd_coins = []
    monedas = coins
    active_coin = False
    for m in monedas:
        for ac in active_symbols:
            if(m.simbolo == ac):
                active_coin = True
        
        if (active_coin == True):
            active_coin = False
        else:
            filterd_coins.append(m)
    
    powerfull_pattern_strategy.calculate_powerfull_pattern(timeframe,False,filterd_coins)

except Exception as ex:
    print("Exception: ")
    print(ex)
finally:
    cursor.close()
    connection.close()
    print('Conexión finalizada')