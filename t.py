from os import system
import TDB
from common import (Order)
from common import (Order,CandleStick,telegramAPIKey,SendTelegramMessage)
import ATR
from telegram.ext import *
from telegram import (Update,Bot)
import asyncio
import requests
import yagmail
import websocket
import websockets
import json
import hashlib
import hmac
import time
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)

API_KEY = ""
API_SECRET = ""
interval= 15
connected_clients = set()
loop = asyncio.get_event_loop()

from pybit.unified_trading import WebSocket
from time import sleep

async def websocket_handler(websocket, path):
    connected_clients.add(websocket)
    while True:
        # Espera a recibir mensajes desde el cliente
        mensaje = await websocket.recv()
        print(f"Mensaje recibido: {mensaje}")

        # Responde al cliente
        respuesta = f"Recibido: {mensaje}"
        await websocket.send(respuesta)

async def send_websocket_message(message, custom_websocket):
    #await custom_websocket.send(json.dumps(message))

    for client in connected_clients:
       
        try:
            await custom_websocket.send(json.dumps(message))
        except websockets.exceptions.ConnectionClosedError:
            # Manejar casos donde la conexión está cerrada
            print(f"Conexión cerrada: {custom_websocket}")

def SendEmail(symbol = 'BTCUSDT',temporality = '15m',message=''):
    yag = yagmail.SMTP(user=email,password=clavecorreo)
    asunto = 'posible mecha '+temporality+' '+symbol+': '
    mensaje = message

   
    
    SendTelegramMessage(asunto+'. '+mensaje)
    #yag.send(destinatarios,asunto,mensaje)
    

ws = WebSocket(
    testnet=True,
    channel_type="linear",
)

async def enviarMensaje(message,ws):
    #print(message)
    print("sddddd")
    #await ws.send("dsdsdsd")

    for client in connected_clients:
       
        try:
            await client.send("ssdsdsddd")
        except websockets.exceptions.ConnectionClosedError:
            # Manejar casos donde la conexión está cerrada
            print(f"Conexión cerrada: {client}")
async def handle_message(message,custom_websocket):
    
    #
    open = float(message['data'][0]['open'])
    close = float(message['data'][0]['close'])
    porcentaje = 0
    if(open > close):
        porcentaje = abs(round(close/open,5)-1) * 100
    else:
        porcentaje = abs(round(close/open,5)-1) *100
    
    if(porcentaje >=1):
        SendEmail(message['topic'].split('.')[2],str(interval)+'m',str(round(porcentaje,4))+'%')

    system('cls')
    print(message)
    print('Porcentaje última vela temporalidad '+str(interval)+'m: '+str(round(porcentaje,4))+'%')
    
    # await send_websocket_message({
    #     'symbol': message['topic'].split('.')[2],
    #     'temporality': str(interval)+'m',
    #     'percentage': str(round(porcentaje, 4))+'%'
    # }, custom_websocket)

    for client in connected_clients:
       
        try:
            await client.send(json.dumps({
                'symbol': message['topic'].split('.')[2],
                'temporality': str(interval)+'m',
                'percentage': str(round(porcentaje,4))+'%'
            }))
        except websockets.exceptions.ConnectionClosedError:
            # Manejar casos donde la conexión está cerrada
            print(f"Conexión cerrada: {client}")

    #await send_websocket_message("dsddsdsd", custom_websocket)
    

async def start_websocket_server():
    try:
        server = await websockets.serve(websocket_handler, "localhost", 8765)
        print("Servidor WebSocket iniciado en ws://localhost:8765")

        await server.wait_closed()
    except Exception as e:
        print(f"Error en start_websocket_server: {e}")
    
# Función principal
async def main():
    try:
        # Configura el servidor WebSocket y espera a que esté listo
        # server_task = asyncio.create_task(start_websocket_server())
        # await asyncio.sleep(1)  # Espera un segundo para asegurarse de que el servidor esté listo
        server = await websockets.serve(websocket_handler, "localhost", 8765)
        
        print("Servidor WebSocket iniciado en ws://localhost:8765")

        

        # Inicia la conexión al WebSocket personalizado después de iniciar el servidor
        custom_websocket = await websockets.connect("ws://localhost:8765")

        # Configura el cliente WebSocket para recibir mensajes
        ws = WebSocket(
            testnet=True,
            channel_type="linear",
        )
        # Configura el cliente WebSocket para recibir mensajes
        #asyncio.new_event_loop()
        ws.kline_stream(
            interval=interval,
            symbol="1000BONKUSDT",
            #callback=lambda message:asyncio.create_task(handle_message(message, custom_websocket,server))
            callback = lambda message: loop.create_task(handle_message(message,custom_websocket))
        )
        #ws.subscribe_candle("1m")
        await server.wait_closed()
        while True:
            # data = ws.recv()
            # if data != "":
            #     ws.send("xssx")
            
            
            # Puedes realizar otras tareas aquí si es necesario
            sleep(0.5)


    except Exception as e:
        print(f"Error en main: {e}")

loop = asyncio.get_event_loop()
try:
    # Configura y ejecuta el bucle de eventos automáticamente
    loop.run_until_complete(main())
except KeyboardInterrupt:
    print("Saliendo...")
finally:
    loop.close()
# def generate_signature(api_secret, data):
#     expires = int(time.time()) + 5
#     signature_payload = f"{data}{expires}"
#     signature = hmac.new(api_secret.encode('utf-8'), signature_payload.encode('utf-8'), hashlib.sha256).hexdigest()
#     return signature, expires

# def on_message(ws, message):
#     data = json.loads(message)
#     if "success" in data and data["success"]:
#         if "request" in data and "op" in data["request"] and data["request"]["op"] == "auth":
#             print("Authenticated successfully.")
#             # Una vez autenticado, puedes suscribirte al canal "position" para obtener la información de la posición
#             position_subscription = {
#                 "op": "subscribe",
#                 "args": ["position"]
#             }
#             ws.send(json.dumps(position_subscription))
#         elif "topic" in data and data["topic"] == "position":
#             print("Position Information:", data["data"])

    

# def on_error(ws, error):
#     print("Error:", error)

# def on_close(ws, close_status_code, close_msg):
#     print("Closed:", close_status_code, close_msg)

# def on_open(ws):
#     # Aquí puedes suscribirte a los canales de WebSocket que desees
#     # subscribe_data = {
#     #     "op": "subscribe",
#     #     "args": ["instrument_info.100ms.MATICUSDT"]
#     # }
#     subscribe_data ={
#         "op": "subscribe",
#         "args": [
#             "position"
#         ]
#     }
#     signature, expires = generate_signature(API_SECRET, json.dumps(subscribe_data))
    
#     auth_data = {
#         "op": "auth",
#         "args": [API_KEY, expires, signature]
#     }

    
    
#     ws.send(json.dumps(auth_data))
#     ws.send(json.dumps(subscribe_data))

# ws_url = "wss://stream.bybit.com/realtime"

# websocket.enableTrace(True)
# ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
# ws.on_open = on_open

# ws.run_forever()


# from pybit.unified_trading import WebSocket
# from time import sleep
# ws = WebSocket(
#     testnet=True,
#     channel_type="private",
#     api_key=API_KEY,
#     api_secret=API_SECRET
# )
# def handle_message(message):
#     print(message)
# ws.position_stream(callback=handle_message)
# while True:
#     sleep(1)

# #if __name__ == "__main__":
# ws_url = "wss://stream.bybit.com/realtime"

# websocket.enableTrace(True)  # Esto activará la traza de depuración de la biblioteca websocket
# ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
# ws.on_open = on_open

# ws.run_forever()




# if __name__ == "__main__":
#     websocket.enableTrace(True)
#     connWS()


#bybit prueba------
# url = "https://api-testnet.bybit.com/v5/position/list"

# payload={}
# headers = {
#   'X-BAPI-API-KEY': '',
#   'X-BAPI-TIMESTAMP': '',
#   'X-BAPI-RECV-WINDOW': '20000',
#   'X-BAPI-SIGN': '4a35d0901e1a6024c35e1e1529514a1a0679e15de2b4f3fd23f40704d04fd7b3'
# }

# response = requests.request("GET", url, headers=headers, data=payload)

# print(response.text)
#bybit prueba-------



# import websocket
# import json

# def on_message(ws, message):
#     data = json.loads(message)
#     print("Received:", data)

# def on_error(ws, error):
#     print("Error:", error)

# def on_close(ws, close_status_code, close_msg):
#     print("Closed:", close_status_code, close_msg)

# def on_open(ws):
#     # Aquí puedes suscribirte a los canales de WebSocket que desees
#     subscribe_data = {
#         "op": "subscribe",
#         "args": ["instrument_info.100ms.BTCUSD"]
#     }
#     ws.send(json.dumps(subscribe_data))

# if __name__ == "__main__":
#     ws_url = "wss://stream.bybit.com/realtime"
    
#     websocket.enableTrace(True)  # Esto activará la traza de depuración de la biblioteca websocket
#     ws = websocket.WebSocketApp(ws_url, on_message=on_message, on_error=on_error, on_close=on_close)
#     ws.on_open = on_open
    
#     ws.run_forever()






# order = Order()

# order.symbol ='ADAUSDT'
# order.order_type = 1
# order.order_size = 14.0
# order.price = 0.37
# order.order_status = 2
# order.take_profit = 0.39
# order.stop_loss = 0.3
# order.order_message= 'test'
# order.timeframe= 3

# TDB.create_DB_order(order,True)
#INSERT INTO ORDERS(symbol,order_type,order_size,price,order_status,take_profit,stop_loss,creation_date,order_message,timeframe)values('ADAUSDT',1,14.0,0.37,2,0.39,0.3, '2023/04/25 00:43:06','test',3) SELECT @@IDENTITY
#updater = Updater(telegramAPIKey, use_context=True)

# up = Update.message.reply_text('qwewq')



# async def enviar_mensaje(chat_id, mensaje):
#     bot = Bot(token=telegramAPIKey)
#     await bot.send_message(chat_id=chat_id, text=mensaje)


# #loop = asyncio.get_event_loop()

# chat_id = '1691938948'
# mensaje = "Hola, esto es un mensaje enviado desde mi bot de Telegram."

# #loop.run_until_complete(enviar_mensaje(chat_id, mensaje))

# asyncio.run(enviar_mensaje(chat_id, mensaje))



#llave api BYbit: 
#clave secreta api bybit 