from common import (strConnection2,Order)
import pyodbc
from datetime import(datetime)

try:
    connection = pyodbc.connect(strConnection2)    
    cursor = connection.cursor()
except Exception as e:
    print("TDB Exception: ")
    print(e)

def openPositionDB(order = Order()):
    try:
        cursor = connection.cursor()
        sql =  cursor.execute("INSERT INTO POSITIONS (symbol,pos_type,pos_size,price,open_date,order_id,open_status,pos_status)values('"+str(order.symbol)+"',"+str(order.order_type)+","+str(order.order_size)+","+str(order.price)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"',"+str(order.id)+",1,0)")
        connection.commit()
        

        # sql =  cursor.execute("UPDATE ORDERS SET order_status = 1 WHERE id = "+str(order.id))
        # connection.commit()
        
    except Exception as ex:
        print(ex)
        
def create_DB_order(order = Order(),market = True):
    orders_status = 0
    if(market == True):
        orders_status = 1 
        sql =  cursor.execute("INSERT INTO ORDERS (symbol,order_type,order_size,price,order_status,take_profit,stop_loss,creation_date,order_message,timeframe)values('"+order.symbol+"',"+str(order.order_type)+","+str(order.order_size)+","+str(order.price)+","+str(orders_status)+","+str(order.take_profit)+","+str(order.stop_loss)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"','"+order.order_message+"',"+str(order.timeframe)+")")
        sql =  cursor.execute("SELECT @@IDENTITY")        
        order.id = int(cursor.fetchone()[0])     
        connection.commit()   
        openPositionDB(order)
        

    else:

        sql =  cursor.execute("INSERT INTO ORDERS (symbol,order_type,order_size,price,order_status,take_profit,stop_loss,creation_date,order_message,timeframe)values('"+order.symbol+"',"+str(order.order_type)+","+str(order.order_size)+","+str(order.price)+","+str(orders_status)+","+str(order.take_profit)+","+str(order.stop_loss)+",'"+str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))+"','"+order.order_message+"',"+str(order.timeframe)+")")
        connection.commit()