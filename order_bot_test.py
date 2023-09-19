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
    positions =  cursor.execute("SELECT * FROM POSITIONS WHERE pos_status = 0")
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
        position.pos_type =float(r[2])
        position.pos_size=float(r[3])
        position.price=float(r[4])
        position.open_date=r[6]
        position.order_id=float(r[9])
        position.open_status=float(r[11])
        position.pos_status=float(r[12])
        positionsList.append(position)
        active_symbols.append(position.symbol)
        
        response = um_futures_client.mark_price(position.symbol)
        last_price = float(response['indexPrice'])

        
        
        orderSQL = cursor.execute("SELECT * FROM ORDERS WHERE id ="+str(position.order_id))
        row = cursor.fetchone()
        if(orderSQL != ''):
            order.id = position.order_id 
            order.symbol=row[1]
            order.order_type=float(row[2])
            order.order_size=float(row[3])
            order.price=float(row[4])
            order.order_status=float(row[5])
            order.take_profit=float(row[6])
            order.stop_loss=float(row[7])  
            order.timeframe=float(row[10])

            take_profit = order.take_profit
            stop_loss = order.stop_loss

            #print(position.symbol+': '+str(take_profit)+'; '+str(stop_loss)+'entry: '+str(position.price)+'; last_price: '+str(last_price))

            #0 = long, 1= short
            if(position.pos_type == 0):
                if(last_price >= take_profit):
                    closePositionDB(position,take_profit,position.pos_type)
                elif(last_price <= stop_loss):
                    closePositionDB(position,stop_loss,position.pos_type)
            elif(position.pos_type == 1):
                if(last_price <= take_profit):
                    closePositionDB(position,take_profit,position.pos_type)
                elif(last_price >= stop_loss):
                    closePositionDB(position,stop_loss,position.pos_type)

   

except Exception as ex:
    print("Exception: ")
    print(ex)
finally:
    cursor.close()
    connection.close()
    print('Conexión finalizada')