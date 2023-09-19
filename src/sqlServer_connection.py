import pyodbc

# try:
connection = pyodbc.connect('DRIVER={SQL Server};SERVER=;DATABASE=;UID=;PWD=')
cursor = connection.cursor()

    # cursor.execute("INSERT INTO ORDERS(symbol,order_type,order_size,price,order_status)values('BTCUSDT',1,0.001,27800,0)")
    # connection.commit()

    # cursor.execute("UPDATE ORDERS SET order_status = 1 where id = 4")
    # connection.commit()

    # # cursor.execute("SELECT * FROM ORDERS")
    # # row = cursor.fetchone()

cursor.execute("SELECT * FROM ORDERS")
rows = cursor.fetchall()
for r in rows:
    print(r)
    #print(row)

    # print('Conexión exitosa')
# except Exception as ex:
#     print(ex)
# finally:
#     connection.close()
#     print('Conexión finalizada')