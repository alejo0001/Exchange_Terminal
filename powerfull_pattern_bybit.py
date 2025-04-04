import time
import datetime
import importlib
from pybit.unified_trading import HTTP
from powerfull_pattern_strategy import on_message
from config import bybit_api_key, bybit_secret_key

# Configuración de la API
API_KEY = bybit_api_key
API_SECRET = bybit_secret_key

# Configuración
interval = 3  # Temporalidad en minutos
minMarketCap = 20  # En millones de dólares

# Inicializar cliente de Bybit
session = HTTP(testnet=False, api_key=API_KEY, api_secret=API_SECRET)

# Función para obtener tickers de futuros
def get_tickers():
    response = session.get_tickers(category="linear")
    return response.get('result', {}).get('list', [])  # Evitar errores si la API no responde correctamente

# Función para validar si es momento de ejecutar
def is_valid_time(interval):
    current_minute = datetime.datetime.utcnow().minute
    return current_minute % interval == 0

def wait_for_valid_time(interval):
    while True:
        now = datetime.datetime.utcnow()
        current_minute = now.minute
        seconds_to_next_check = 60 - now.second  # Calcular segundos restantes para el próximo minuto

        if current_minute % interval == 0:
            return  # Salimos de la función cuando el tiempo es válido
        
        print(f"Esperando... Próxima validación en {seconds_to_next_check} segundos")
        time.sleep(seconds_to_next_check)  # Dormimos hasta el siguiente minuto

# Función principal
def validarTickers():
    print('Validando...')
    while True:
        try:
            current_time = datetime.datetime.utcnow()
            print(f"Hora actual UTC: {current_time.strftime('%H:%M:%S')}")
            wait_for_valid_time(interval)  # Esperar hasta el minuto correcto
            tickers = get_tickers()
            
            if not tickers:
                print("No se recibieron tickers, posible error en la API.")
                time.sleep(10)
                continue
            
            print(f"Tickers obtenidos: {len(tickers)}")
            
            filtered_tickers = [t for t in tickers if float(t.get('turnover24h', 0)) >= minMarketCap * 1_000_000]
            print(f"Tickers después del filtro: {len(filtered_tickers)}")
            
            for ticker in filtered_tickers:
                symbol = ticker['symbol']
                message = {'data': [{'close': ticker['lastPrice']}]}  # Simulación de la estructura esperada
                
            
                on_message(message,symbol,str(interval))
                
                print(f"Procesado {symbol} con precio {message['data'][0]['close']} ... ")

                
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)  # Esperar antes de reintentar

# Ejecutar la función
validarTickers()
