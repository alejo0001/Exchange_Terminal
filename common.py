from datetime import (date,datetime)
from telegram import *
from telegram import (Update,Bot)
import asyncio
from config import(chat_id,telegramAPIKey,strConnection,strConnection2)




class Moneda:
    simbolo = ''
    intervalos = []

    def __init__(self, simbolo, intervalos):
        self.simbolo = simbolo
        self.intervalos = intervalos

class CoinOrderbookInfo:
    longStopLoss=0
    shortStopLoss=0
    longEntry=0
    shortEntry=0
    longRiskBenefitRatio=0
    shortRiskBenefitRatio=0
    longDistance=0
    shortDistance=0
    latestPrice = 0

class Order:
    id=0
    symbol=''
    order_type=0
    order_size=0
    price=0
    order_status=0
    take_profit=0
    stop_loss=0
    creation_date=datetime.today()
    order_message = ''
    timeframe = 0

class Position:
    id =0
    symbol =''
    pos_type =0
    pos_size=0
    price=0
    close_price=0
    open_date=datetime.today()
    close_date=datetime.today()
    PnL=0
    order_id=0
    close_status=0
    open_status=0
    pos_status=0

class CandleStick:
    open = 0
    high=0
    low=0
    close=0

coins = [
    Moneda('TRXUSDT',['0.001','0.0001','0.00001']),
    Moneda('MATICUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('XRPUSDT',['0.01','0.001','0.0001']),
    Moneda('LTCUSDT',['1','0.1','0.01']),
    Moneda('VETUSDT',['0.001','0.0001','0.00001']),
    Moneda('AVAXUSDT',['1','0.1','0.01','0.001']),
    Moneda('NEARUSDT',['0.1','0.01','0.001']),
    Moneda('DOTUSDT',['0.1','0.01','0.001']),
    Moneda('ADAUSDT',['0.1','0.01','0.001']),
    Moneda('THETAUSDT',['0.1','0.01','0.001']),
    Moneda('OPUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('OCEANUSDT',['0.01','0.001','0.0001','0.00001']),
    Moneda('AAVEUSDT',['1','0.1','0.01']),
    Moneda('GMTUSDT',['0.01','0.001','0.0001']),
    Moneda('GALUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('C98USDT',['0.01','0.001','0.0001']),
    Moneda('ALPHAUSDT',['0.01','0.001','0.0001','0.00001']),
    Moneda('CRVUSDT',['0.01','0.001']),
    Moneda('SOLUSDT',['1','0.1','0.01','0.001']),
    Moneda('ROSEUSDT',['0.001','0.0001','0.00001']),
    Moneda('KAVAUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('DOGEUSDT',['0.001','0.0001','0.00001']),
    Moneda('LINKUSDT',['0.1','0.01','0.001']),
    Moneda('APTUSDT',['1','0.1','0.01','0.001']),
    Moneda('BNBUSDT',['10','1','0.1','0.01']),
    Moneda('BTCUSDT',['100','50','10','1','0.1']),
    Moneda('ETHUSDT',['100','50','10','1','0.1','0.01']),
    Moneda('MINAUSDT',['0.01','0.001','0.0001']),
    Moneda('EOSUSDT',['0.1','0.01','0.001']),
    Moneda('FETUSDT',['0.01','0.001','0.0001']),
    Moneda('AGIXUSDT',['0.01','0.001','0.0001']),
    Moneda('OMGUSDT',['0.1','0.01','0.001']),
    Moneda('UNIUSDT',['0.1','0.01','0.001']),
    Moneda('IOSTUSDT',['0.001','0.0001','0.00001','0.000001']),
    Moneda('ATOMUSDT',['1','0.1','0.01','0.001']),
    Moneda('XMRUSDT',['10','1','0.1','0.01']),
    Moneda('QNTUSDT',['10','1','0.1','0.01']),
    Moneda('ALGOUSDT',['0.01','0.001','0.0001']),
    Moneda('CKBUSDT',['0.0001','0.00001','0.000001']),
    Moneda('EGLDUSDT',['1','0.1','0.01']),
    Moneda('MASKUSDT',['0.1','0.01','0.001']),
    Moneda('TRUUSDT',['0.001','0.0001','0.00001']),
    Moneda('RLCUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('IMXUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('BNXUSDT',['0.01','0.001']),
    Moneda('BLZUSDT',['0.001','0.0001','0.00001']),
    Moneda('BAKEUSDT',['0.01','0.001','0.0001']),
    Moneda('SKLUSDT',['0.001','0.0001','0.00001']),
    Moneda('ARBUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('HOOKUSDT',['1','0.1','0.01','0.001']),
    Moneda('ZENUSDT',['1','0.1','0.01','0.001']),
    Moneda('NEOUSDT',['1','0.1','0.01','0.001']),
    Moneda('SUSHIUSDT',['0.1','0.01','0.001']),
    Moneda('IOTXUSDT',['0.001','0.0001','0.00001']),
    Moneda('QTUMUSDT',['0.1','0.01','0.001']),
    Moneda('MAGICUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('LITUSDT',['0.01','0.001']),
    Moneda('DYDXUSDT',['0.1','0.01','0.001']),
    Moneda('STXUSDT',['0.01','0.001','0.0001']),
    #Moneda('COCOSUSDT',['0.1','0.01','0.001']),
    Moneda('SSVUSDT',['1','0.1','0.01']),
    Moneda('FTMUSDT',['0.01','0.001','0.0001']),
    Moneda('SXPUSDT',['0.01','0.001','0.0001']),
    Moneda('FXSUSDT',['0.1','0.01','0.001']),
    Moneda('STGUSDT',['0.01','0.001','0.0001']),
    Moneda('XEMUSDT',['0.001','0.0001']),
    Moneda('LDOUSDT',['0.1','0.01','0.001','0.0001']),
    Moneda('ONTUSDT',['0.01','0.001','0.0001']),
    Moneda('IDUSDT',['0.01','0.001','0.0001']),
    Moneda('AMBUSDT',['0.001','0.0001','0.00001']),
    Moneda('MKRUSDT',['50','10','1','0.1']),
    Moneda('ICXUSDT',['0.01','0.001','0.0001']),
    Moneda('CFXUSDT',['0.1','0.01','0.001','0.0001'])
    ]


coin = [
    Moneda('NEOUSDT',['1','0.1','0.01','0.001'])
    ]


def get_order_book_strategy_coins():
    monedas = []
    x = Moneda('BTCUSDT',['0.1'])
    for m in coins:
        x= m
        if((x.simbolo != 'BTCUSDT')& (x.simbolo != 'ETHUSDT') & (x.simbolo!= 'XMRUSDT') & (x.simbolo!= 'QNTUSDT') & (x.simbolo!= 'BNBUSDT')& (x.simbolo!= 'MKRUSDT')):
            monedas.append(x)
        
    return monedas

order_book_strategy_coins = get_order_book_strategy_coins()

async def enviar_mensaje(chat_id, mensaje):
    bot = Bot(token=telegramAPIKey)
    await bot.send_message(chat_id=chat_id, text=mensaje)

    

def SendTelegramMessage(message):
    mensaje = "Hola, esto es un mensaje enviado desde mi bot de Telegram."

    asyncio.run(enviar_mensaje(chat_id, message))

