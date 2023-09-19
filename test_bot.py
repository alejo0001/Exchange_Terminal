#from src.sqlServer_connection import connection
from common import (Position,strConnection,Order,order_book_strategy_coins,CoinOrderbookInfo,Moneda)
import pyodbc
from datetime import(datetime)
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
from order_book_strategy import getPointsInfo
import logging
import exchange_info
# import sys

# # Add the directory to the search path
# sys.path.append('/src/sqlServer_connection')
# import sqlServer_connection


key = ""
secret = ""

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

    #print(str(PnL)+", close_date='"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"', close_price = "+str(closePrice)+" WHERE id = "+str(position.id))
    try:
        cursor = connection.cursor()
        sql =  cursor.execute("UPDATE POSITIONS SET pos_status = 1, PnL = "+str(PnL)+", close_date='"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"', close_price = "+str(closePrice)+" WHERE id = "+str(position.id))
        connection.commit()
        #cursor.close()
    except Exception as ex:
        print(ex)

def openPositionDB(order = Order()):
    try:
        cursor = connection.cursor()
        sql =  cursor.execute("INSERT INTO POSITIONS (symbol,pos_type,pos_size,price,open_date,order_id,open_status,pos_status)values('"+str(order.symbol)+"',"+str(order.order_type)+","+str(order.order_size)+","+str(order.price)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"',"+str(order.id)+",1,0)")
        connection.commit()
        #cursor.close()

        sql =  cursor.execute("UPDATE ORDERS SET order_status = 1 WHERE id = "+str(order.id))
        connection.commit()
        #cursor.close()
    except Exception as ex:
        print(ex)

def cancelOrder(order = Order()):
    try:
        sql =  cursor.execute("UPDATE ORDERS SET order_status = 2 WHERE id = "+str(order.id))
        connection.commit()
        #cursor.close()
    except Exception as ex:
        print(ex)

try:
    connection = pyodbc.connect(strConnection)
    #print(os.getcwd())
    cursor = connection.cursor()
    positions =  cursor.execute("SELECT * FROM POSITIONS WHERE pos_status = 0")
    rows = cursor.fetchall()
    #cursor.close()
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
        position.pos_type =r[2]
        position.pos_size=float(r[3])
        position.price=r[4]
        position.close_price=r[5]
        position.open_date=r[6]
        position.close_date=r[7]
        position.PnL=r[8]
        position.order_id=r[9]
        position.close_status=r[10]
        position.open_status=r[11]
        position.pos_status=r[12]
        positionsList.append(position)
        active_symbols.append(position.symbol)
        
        response = um_futures_client.mark_price(position.symbol)
        last_price = float(response['indexPrice'])

        
        
        orderSQL = cursor.execute("SELECT * FROM ORDERS WHERE id ="+str(position.order_id))
        row = cursor.fetchone()
        if(orderSQL != ''):
            order.id = position.order_id 
            order.symbol=row[1]
            order.order_type=row[2]
            order.order_size=float(row[3])
            order.price=float(row[4])
            order.order_status=row[5]
            order.take_profit=float(row[6])
            order.stop_loss=float(row[7])        
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

    pending_orders =  cursor.execute("SELECT * FROM ORDERS WHERE order_status = 0")
    order_rows = cursor.fetchall()
    #cursor.close()
    print('hora actual: '+str(datetime.today()).split(' ')[1].split(':')[0])
    for oR in order_rows:
        order.id = oR[0]
        order.symbol=oR[1]
        order.order_type=oR[2]
        order.order_size=float(oR[3])
        order.price=float(oR[4])
        order.order_status=oR[5]
        order.take_profit=float(oR[6])
        order.stop_loss=float(oR[7])
        order.creation_date=oR[8]
        active_symbols.append(order.symbol)

        if(int(str(datetime.today() - order.creation_date).split(':')[0]) >= 1):
            cancelOrder(order)
        # print(order.symbol+': ')
        # print(str(datetime.today() - order.creation_date).split(':')[0])
        

        response = um_futures_client.mark_price(order.symbol)
        last_price = float(response['indexPrice'])

        if(order.order_type == 0):
            if(last_price <= order.price):
                    openPositionDB(oR)
        elif(order.order_type == 1):
            if(last_price >= order.price):
                    openPositionDB(oR)

    filterd_coins = []
    monedas = order_book_strategy_coins
    active_coin = False
    for m in monedas:
        for ac in active_symbols:
            if(m.simbolo == ac):
                active_coin = True
        
        if (active_coin == True):
            active_coin = False
        else:
            filterd_coins.append(m)
    
    for x in filterd_coins:
        current_coin=x.simbolo
        min_value = exchange_info.get_min_value_info(current_coin)
        try:
            try:
                info = getPointsInfo(x)
                print("info: "+current_coin)
            except:
                print("error: "+current_coin)

            #1 para short, 0 para long:
            operacion_sugerida = 0

            if(info.shortDistance <= info.longDistance):
                operacion_sugerida = 1

            if(((operacion_sugerida == 1) &  (info.shortRiskBenefitRatio>= 2)) & (info.longDistance >= info.shortDistance)| ((operacion_sugerida == 0) &  (info.longRiskBenefitRatio >= 2)&(info.longDistance <= info.shortDistance))):
                try:
                    entry_price = 0
                    stop_loss_price = 0
                    take_profit_price = 0
                    if(operacion_sugerida == 1):
                        entry_price = info.shortEntry
                        stop_loss_price = info.shortStopLoss
                        take_profit_price = info.longEntry
                    else:
                        entry_price = info.longEntry
                        stop_loss_price = info.longStopLoss
                        take_profit_price = info.shortEntry

                    #cursor = connection.cursor()                
                    sql =  cursor.execute("INSERT INTO ORDERS (symbol,order_type,order_size,price,order_status,take_profit,stop_loss,creation_date)values('"+str(current_coin)+"',"+str(operacion_sugerida)+","+str(min_value)+","+str(entry_price)+",0,"+str(take_profit_price)+","+str(stop_loss_price)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"')")
                    connection.commit()
                    print("'"+str(current_coin)+"',"+str(operacion_sugerida)+","+str(min_value)+","+str(entry_price)+",0,"+str(take_profit_price)+","+str(stop_loss_price)+", '"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"'")
                    #cursor.close()
                except Exception as ex:
                    print("Ex: ")
                    print(ex)
                    print("'"+str(current_coin)+"',"+str(operacion_sugerida)+","+str(min_value)+","+str(entry_price)+",0,"+str(take_profit_price)+","+str(stop_loss_price)+", '"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"'")
            else:
                print(current_coin)


        except ClientError as error:
            logging.error(
                current_coin+": Found error. status: {}, error code: {}, error message: {}".format(
                    error.status_code, error.error_code, error.error_message
                )
            )


except Exception as ex:
    print("Exception: ")
    print(ex)
finally:
    cursor.close()
    connection.close()
    print('Conexión finalizada')