import requests
import time
import asyncio
from telegram import Bot
from asyncio import sleep
import asyncio
import threading

from common import SendTelegramMessage

COPminAmount = 500000

# 📤 Función para enviar mensaje a Telegram
def enviar_mensaje_telegram(mensaje):
    asyncio.run(SendTelegramMessage(mensaje))


# 📈 Consulta el mejor precio de compra o venta
def obtener_mejor_precio(trade_type, metodo_pago="Nequi"):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "asset": "USDT",
        "fiat": "COP",
        "merchantCheck": False,
        "page": 1,
        "rows": 1,
        "transAmount": COPminAmount,
        "tradeType": trade_type,
        "payTypes": [metodo_pago]
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    # Imprimir la respuesta completa para verificar la estructura
    #print(data)
    if data["data"]:
        adv = data["data"][0]["adv"]
        precio = float(data["data"][0]["adv"]["price"])
        vendedor = data["data"][0]["advertiser"]["nickName"] 
        monto_minimo = float(adv["minSingleTransAmount"])
        return precio, vendedor, monto_minimo
    else:
        return None

# 🔁 Monitorea oportunidades y alerta
def monitorear_oportunidades():
    print("Monitoreando Binance P2P USDT/COP (Nequi)...\n")
    while True:
        try:
            precio_compra, vendedor_compra, monto_minimo_compra = obtener_mejor_precio("BUY")
            precio_venta, vendedor_venta, monto_minimo_venta = obtener_mejor_precio("SELL")

            if precio_compra and precio_venta:
                diferencia = precio_venta - precio_compra
                print(f"[{time.strftime('%H:%M:%S')}]")
                print(f"🟢 Mejor precio de COMPRA (tú compras): {precio_compra:.2f} COP")
                print(f"🔴 Mejor precio de VENTA (tú vendes): {precio_venta:.2f} COP")
                print(f"💰 Diferencia: {diferencia:.2f} COP")
                print(f"👤 Vendedor COMPRA: {vendedor_compra} (Monto mínimo: {monto_minimo_compra} COP)")
                print(f"👤 Vendedor VENTA: {vendedor_venta} (Monto mínimo: {monto_minimo_venta} COP)")

                mensaje = None
                if diferencia >= 200:
                    mensaje = f"🚨 Alta oportunidad en P2P Binance:\nCompra: {precio_venta:.2f}\nVenta: {precio_compra:.2f}\nSpread: {diferencia:.2f} COP"
                elif diferencia >= 150:
                    mensaje = f"✅ Buena oportunidad:\nCompra: {precio_venta:.2f}\nVenta: {precio_compra:.2f}\nSpread: {diferencia:.2f} COP"
                elif diferencia >= 100:
                    mensaje = f"⚠️ Oportunidad básica:\nCompra: {precio_venta:.2f}\nVenta: {precio_compra:.2f}\nSpread: {diferencia:.2f} COP"

                if mensaje:
                    #enviar_mensaje_telegram(mensaje)
                    print(mensaje)
                    if monto_minimo_compra <= COPminAmount and monto_minimo_venta <= COPminAmount :
                        threading.Thread(target=enviar_mensaje_telegram, args=(mensaje,)).start()

                print("-" * 40)

            time.sleep(30)

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(10)

# ▶️ Ejecutar
monitorear_oportunidades()