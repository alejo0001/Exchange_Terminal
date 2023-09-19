import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import array as arr
from common import(order_book_strategy_coins,Moneda)
import order_book_strategy




monedas = order_book_strategy_coins
current_coin=''

for m in monedas:
    current_coin=m.simbolo
    try:
        #try:
        info = order_book_strategy.getPointsInfo(m)
        # except:
        #     print(current_coin)

        #1 para short, 0 para long:
        operacion_sugerida = 0

        # if(info.shortDistance <= info.longDistance):
        #     operacion_sugerida = 1

        if(((operacion_sugerida == 1) &  (info.shortRiskBenefitRatio>= 2)) & (info.longDistance >= info.shortDistance)| ((operacion_sugerida == 0) &  (info.longRiskBenefitRatio >= 2)&(info.longDistance <= info.shortDistance))):

            print('precio actual '+m.simbolo+': '+ str(info.latestPrice))
            print('stop loss short: '+str(info.shortStopLoss))    
            print('entrada short: '+str(info.shortEntry))
            print('stop loss long: '+str(info.longStopLoss))    
            print('entrada long: '+str(info.longEntry))
            try:
                print('relación riesgo/beneficio long = '+str(info.longRiskBenefitRatio)+' a 1')
            except:
                print('mismo valor que stop loss, recalcular stop loss long')
            
            try:
                print('relación riesgo/beneficio short = '+str(info.shortRiskBenefitRatio)+' a 1')
            except:
                print('mismo valor que stop loss, recalcular stop loss short')

            print('distancia para short = '+str(info.shortDistance))
            print('distancia para long = '+str(info.longDistance))                
            print(' ')
     

    except ClientError as error:
        logging.error(
            current_coin+": Found error. status: {}, error code: {}, error message: {}".format(
                error.status_code, error.error_code, error.error_message
            )
        )