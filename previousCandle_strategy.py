from pybit.unified_trading import (WebSocket,HTTP)
import time
from config import(email,clavecorreo,destinatarios,bybit_api_key,bybit_secret_key)


endpoint = "https://api.bybit.com"  # Cambiar a "https://api-testnet.bybit.com" para la testnet

# Crear cliente HTTP
client = HTTP(api_key=bybit_api_key, api_secret=bybit_secret_key,  testnet = False)

# Parámetros de estrategia
STOP_LOSS_PERCENT = 0.2  # 0.2%
TAKE_PROFIT_FACTOR = 2.0  # Multiplicador de TP
SYMBOL = "ARCUSDT"  # Cambia al par que desees operar
#LEVERAGE = 5  # Leverage para la operación
TIMEFRAME = "3m"  # Intervalo de tiempo (1 minuto en este ejemplo)
roundDecimals = 5

def get_last_candles(symbol, timeframe, limit=2):
    """
    Obtiene las últimas velas del mercado.
    """
    candles = client.get_kline(category="linear", symbol=symbol, interval=timeframe, limit=limit)
    print("c:",candles )
    return candles["result"]["list"]

def calculate_levels(open_price, prev_open_price):
    """
    Calcula los niveles de Stop Loss y Take Profit basados en la apertura de la vela anterior.
    """
    long_stop_loss = round(prev_open_price - (prev_open_price * STOP_LOSS_PERCENT / 100),roundDecimals)
    long_take_profit = round(open_price + (open_price *((abs(long_stop_loss-open_price)/open_price) * TAKE_PROFIT_FACTOR)),roundDecimals)

    short_stop_loss = round(prev_open_price + (prev_open_price * STOP_LOSS_PERCENT / 100),roundDecimals)
    short_take_profit = round(open_price - (open_price *((abs(short_stop_loss-open_price)/open_price) * TAKE_PROFIT_FACTOR))  ,roundDecimals)

    return long_stop_loss, long_take_profit, short_stop_loss, short_take_profit

def place_order(side, qty, stop_loss, take_profit, position_idx=0):
    """
    Coloca una orden en Bybit.
    """
    order = client.place_order(
        category="linear",
        symbol=SYMBOL,
        side=side,
        orderType="Market",
        qty=qty,
        positionIdx=position_idx,  # 0 para la posición en One-way y 1 para Hedge
        timeInForce="GoodTillCancel",
        takeProfit=take_profit,
        stopLoss=stop_loss
    )
    return order

def get_position_size():
    """
    Obtiene el tamaño de la posición actual.
    """
    positions = client.get_positions(category="linear", symbol=SYMBOL)
    for position in positions["result"]["list"]:
        if position["size"] != 0:
            return position["size"]
    return 0

def get_account_mode():
    """
    Obtiene el modo de la cuenta (One-way o Hedge).
    """
    account = client.get_account()
    return account["result"]["account"]["mode"]

# Bucle principal de la estrategia
def on_message(message):
    try:
        # Obtener el modo de la cuenta (Hedge o One-way)
        account_mode = "Hedge"#get_account_mode()
        print(f"Modo de cuenta: {account_mode}")

        # Obtener las últimas dos velas
        candles = get_last_candles(SYMBOL, TIMEFRAME.split('m')[0], limit=2)
        print(f"candles: {candles}")
        prev_candle = candles[0]
        current_candle = candles[1]
        print(f"prev_candle: {prev_candle}")
        # Datos de la vela anterior
        # prev_open = float(prev_candle[1])
        # prev_close = float(prev_candle[4])
        prev_open = float(message['data'][0]['open'])
        prev_close = float(message['data'][0]['close'])
        # Datos de la vela actual
        #current_open = float(current_candle[1])
        current_open = prev_close
        # Calcular niveles
        long_stop_loss, long_take_profit, short_stop_loss, short_take_profit = calculate_levels(
            current_open, prev_open
        )

        # Comprobar si no hay posiciones abiertas
        print("get_position_size(): ",get_position_size())
        if int(get_position_size()) == 0:
            print("prev_close : ",prev_close)
            print("prev_open : ",prev_open)
            # Condiciones de entrada
            if prev_close > prev_open:
                # Long
                qty = 20  # Tamaño de la posición (ajusta según tu balance)
                if account_mode == "Hedge":
                    # Si el modo es Hedge, colocamos la posición en índice 1 (hedge)
                    place_order("Buy", qty, long_stop_loss, long_take_profit, position_idx=1)
                else:
                    # Si el modo es One-way, colocamos la posición en índice 0
                    place_order("Buy", qty, long_stop_loss, long_take_profit, position_idx=0)
                print("Orden LONG colocada")
            elif prev_close < prev_open:
                # Short
                qty = 20  # Tamaño de la posición
                if account_mode == "Hedge":
                    # Si el modo es Hedge, colocamos la posición en índice 1 (hedge)
                    place_order("Sell", qty, short_stop_loss, short_take_profit, position_idx=2)
                else:
                    # Si el modo es One-way, colocamos la posición en índice 0
                    place_order("Sell", qty, short_stop_loss, short_take_profit, position_idx=0)
                print("Orden SHORT colocada")

        # Esperar 1 minuto antes de la siguiente iteración
    #     time.sleep(180)

    except Exception as e:
        print(f"Error: {e}")
        # time.sleep(10)


def start_websocket():
    """
    Inicia la conexión del WebSocket y maneja la reconexión si se cierra.
    """
    #while True:
    #try:
    ws = WebSocket(
        testnet=False,
        api_key=bybit_api_key,
        api_secret=bybit_secret_key,
        channel_type="linear"
    )
    ws.kline_stream( interval=3, symbol=SYMBOL, callback=on_message)
    while True:
        time.sleep(1)
    #except Exception as e:
        #print(f"WebSocket desconectado. Reconectando... Error: {e}")
        #time.sleep(5)  # Esperar 5 segundos antes de reconectar

# Iniciar WebSocket
#start_websocket()

ws = WebSocket(
    testnet=False,
    channel_type="linear",
)
def handle_message(message):
    if(message['data'][0]['confirm']== True):
        on_message(message)
        print(message)
ws.kline_stream(
    interval=3,
    symbol="ARCUSDT",
    callback=handle_message
)
while True:
    time.sleep(1)