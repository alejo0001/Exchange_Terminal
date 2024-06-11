
import asyncio
import websockets

async def websocket_handler(websocket, path):
    while True:
        # Espera a recibir mensajes desde el cliente
        mensaje = await websocket.recv()
        print(f"Mensaje recibido: {mensaje}")

        # Responde al cliente
        respuesta = f"Recibido: {mensaje}"
        await websocket.send(respuesta)

# Configura el servidor WebSocket
async def main():
    server = await websockets.serve(websocket_handler, "localhost", 8765)
    print("Servidor WebSocket iniciado en ws://localhost:8765")

    await server.wait_closed()

# Inicia el bucle de eventos
asyncio.get_event_loop().run_until_complete(main())





# import asyncio 
# import websockets
# import ssl

# all_clients=[]

# ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
# ssl_context.load_cert_chain(certfile="certificate.pem", keyfile="private_key.pem")

# async def send_message(message:str):
#     for client in all_clients:
#         await client.send(message)

# async def new_client_connected(client_socket,path):
#     print("New client connected")
#     all_clients.append(client_socket)

#     while True:
#         new_message = await client_socket.recv()
#         print("Client send: ",new_message)
#         await send_message(new_message)

# async def start_server():
#     try:
#        print("server started")
#        await websockets.serve(new_client_connected,'localhost',8080, ssl=ssl_context)
          
#     except Exception as e:
#         print("sadsadad1"+str(e))

# if __name__ == "__main__":
#     # event_loop = asyncio.get_event_loop()
#     # event_loop.run_until_complete(start_server())
#     # event_loop.run_forever()

#     # loop = asyncio.new_event_loop()
#     # asyncio.set_event_loop(loop)
#     # try:
#     #     asyncio.run(start_server())
#     #     loop.run_forever()
#     # except Exception:
#     #     print("sadsadad")
#     loop = asyncio.new_event_loop()
#     asyncio.set_event_loop(loop)
#     try:
#         asyncio.run(start_server())
#         loop.run_forever()
#     except Exception:
#         print("sadsadad")
#     except Exception as e:
#         print("sadsadad2"+str(e))

