from binance.um_futures import UMFutures


key=""
secret=""

um_futures_client = UMFutures(key=key, secret=secret)



response = um_futures_client.klines('BTCUSDT', '5m', **{"limit": 1000})


# Obtener los precios de cierre y calcular los niveles de soporte y resistencia
close_prices = [float(entry[4]) for entry in response]
max_price = max(close_prices)
min_price = min(close_prices)
range_price = max_price - min_price
resistance_level = max_price - (range_price * 0.382)
support_level = min_price + (range_price * 0.382)

print('Resistance level:', resistance_level)
print('Support level:', support_level)