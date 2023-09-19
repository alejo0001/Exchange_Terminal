
def calculate_bollinger_bands(prices, window=20, num_std=2):
    rolling_mean = prices.rolling(window).mean()
    rolling_std = prices.rolling(window).std()
    upper_band = rolling_mean + (num_std * rolling_std)
    lower_band = rolling_mean - (num_std * rolling_std)
    return rolling_mean, upper_band, lower_band

def calculate_bollinger_bands_with(upperband=0,lowerband=0,moving_average=20):
    return ((upperband-lowerband)/(moving_average))
