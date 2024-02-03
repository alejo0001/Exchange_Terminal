import logging
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging
from binance.error import ClientError
import array as arr
from common import(order_book_strategy_coins,Moneda,CoinOrderbookInfo)
from config import(binance_api_key,binance_secret_key)


key=binance_api_key
secret=binance_secret_key

um_futures_client = UMFutures(key=key, secret=secret)

depth = 0
cantidad_bloques_intervalo_mas_alto = 10
intervalo_mas_alto = 0.001
intervalo_intermedio = 0.0001
aumento = 0
aumento_intermedio = 0

d_bloques_venta = {}
d_bloques_compra = {}
d_bloques_venta_intermedios = {}
d_bloques_compra_intermedios = {}



monedas = order_book_strategy_coins

def getPointsInfo(m = Moneda('TRXUSDT',['0.001','0.0001','0.00001'])):

    info = CoinOrderbookInfo()
    d_bloques_venta = {}
    d_bloques_compra = {}
    d_bloques_venta_intermedios = {}
    d_bloques_compra_intermedios = {}
    bloque_actual_precio = 0
    aumento = 0
    aumento_intermedio = 0
    response = um_futures_client.mark_price(m.simbolo)
    libro_ordenes = um_futures_client.depth(m.simbolo, **{"limit": 1000})

    parte_decimal = response['indexPrice'].split(".")[1]
    parte_entera =  response['indexPrice'].split(".")[0]

    intervalo_mas_alto = m.intervalos[0]
    intervalo_intermedio = m.intervalos[1]
    decimales_intervalo_mas_alto = ''
    try:
        parte_decimal_intervalo_mas_alto = intervalo_mas_alto.split('.')[1]
    except:
        parte_decimal_intervalo_mas_alto = ''
    decimales_intervalo_intermedio = ''
    parte_decimal_intervalo_intermedio = intervalo_intermedio.split('.')[1]
    cantidad_digitos_intervalo_mas_alto = len(parte_decimal_intervalo_mas_alto)
    cantidad_digitos_intervalo_intermedio = len(parte_decimal_intervalo_intermedio)
    
    for d in range(cantidad_digitos_intervalo_mas_alto):            
        decimales_intervalo_mas_alto = decimales_intervalo_mas_alto+parte_decimal[d]

    for d in range(cantidad_digitos_intervalo_intermedio):
        decimales_intervalo_intermedio = decimales_intervalo_intermedio + parte_decimal[d]


    bloque_actual_precio = float(parte_entera +'.'+decimales_intervalo_mas_alto)
    bloque_actual_precio_intervalo_intermedio = float(parte_entera +'.'+decimales_intervalo_intermedio)
    
    
    
    

    


    #bloques intervalo más alto:
    for i in range(1,cantidad_bloques_intervalo_mas_alto + 1):
        aumento += float(intervalo_mas_alto)
        #print(str(bloque_actual_precio) +'-'+str(aumento)+'-'+intervalo_mas_alto)
        intervalo_venta = str(round(bloque_actual_precio+aumento,cantidad_digitos_intervalo_mas_alto))
        intervalo_compra = str(round(bloque_actual_precio -(aumento-float(intervalo_mas_alto)),cantidad_digitos_intervalo_mas_alto))
        d_bloques_venta[intervalo_venta] = 0
        d_bloques_compra[intervalo_compra] = 0

    #bloques intervalo intermedio:
    for i in range(1,(cantidad_bloques_intervalo_mas_alto*2) + 1):
        aumento_intermedio += float(intervalo_intermedio)

        intervalo_venta = str(round(bloque_actual_precio_intervalo_intermedio+aumento_intermedio,cantidad_digitos_intervalo_intermedio))
        intervalo_compra = str(round(bloque_actual_precio_intervalo_intermedio -(aumento_intermedio-float(intervalo_intermedio)),cantidad_digitos_intervalo_intermedio))
        d_bloques_venta_intermedios[intervalo_venta] = 0
        d_bloques_compra_intermedios[intervalo_compra] = 0

    

    for j in libro_ordenes['bids']:
        siguiente_bloque_mas_alto = 0
        siguiente_bloque_intermedio_mas_alto = 0
        for bc in d_bloques_compra:
            
            if(siguiente_bloque_mas_alto == 0):
                siguiente_bloque_mas_alto = float(bc) +float(intervalo_mas_alto)

            if((float([j][0][0]) >= float(bc) )& (float([j][0][0]) < siguiente_bloque_mas_alto)):
                d_bloques_compra[bc]=str(float(d_bloques_compra[bc])+float(j[1]))
                break

        for bc in d_bloques_compra_intermedios:
            
            if(siguiente_bloque_intermedio_mas_alto == 0):
                siguiente_bloque_intermedio_mas_alto = float(bc) +float(intervalo_intermedio)
                

            if((float([j][0][0]) >= float(bc) )& (float([j][0][0]) < siguiente_bloque_intermedio_mas_alto)):
                d_bloques_compra_intermedios[bc]=str(float(d_bloques_compra_intermedios[bc])+float(j[1]))
                break



    for j in libro_ordenes['asks']:
        siguiente_bloque_mas_bajo = 0
        siguiente_bloque_intermedio_mas_bajo = 0

        for bv in d_bloques_venta:            
            if(siguiente_bloque_mas_bajo == 0):
                siguiente_bloque_mas_bajo = float(bc) -float(intervalo_mas_alto)            

            if((float([j][0][0]) <= float(bv) )& (float([j][0][0]) > siguiente_bloque_mas_bajo)):
                d_bloques_venta[bv]=str(float(d_bloques_venta[bv])+float(j[1]))
                break

        for bv in d_bloques_venta_intermedios:            
            if(siguiente_bloque_intermedio_mas_bajo == 0):
                siguiente_bloque_intermedio_mas_bajo = float(bc) -float(intervalo_intermedio)            

            if((float([j][0][0]) <= float(bv) )& (float([j][0][0]) > siguiente_bloque_intermedio_mas_bajo)):
                d_bloques_venta_intermedios[bv]=str(float(d_bloques_venta_intermedios[bv])+float(j[1]))
                break

    valor_stop_loss_short = 0
    bloque_stop_loss_short = 0
    for b in d_bloques_venta:
        if(float(d_bloques_venta[b]) > float(valor_stop_loss_short)):
            valor_stop_loss_short = d_bloques_venta[b]
            bloque_stop_loss_short = b

    valor_stop_loss_long = 0
    bloque_stop_loss_long = 0
    for b in d_bloques_compra:
        if(float(d_bloques_compra[b]) > float(valor_stop_loss_long)):
            valor_stop_loss_long = d_bloques_compra[b]
            bloque_stop_loss_long = b

    entrada_short_temporal = 0
    bloque_short = 0
    for b in d_bloques_venta_intermedios:
        if(float(b) <= float(bloque_stop_loss_short)):
            if(float(d_bloques_venta_intermedios[b]) > float(entrada_short_temporal)):
                entrada_short_temporal= d_bloques_venta_intermedios[b]
                bloque_short = b

    entrada_long_temporal = 0
    bloque_long = 0
    for b in d_bloques_compra_intermedios:
        if(float(b) >= float(bloque_stop_loss_long)):
            if(float(d_bloques_compra_intermedios[b]) > float(entrada_long_temporal)):
                bloque_long = b
                entrada_long_temporal = d_bloques_compra_intermedios[b]

    recalcular_stop_loss_long = False
    recalcular_stop_loss_short = False
    if(bloque_long ==0):
        bloque_long = bloque_stop_loss_long
        recalcular_stop_loss_long = True
    if(bloque_short ==0):
        bloque_short = bloque_stop_loss_short
        recalcular_stop_loss_short = True
    if(recalcular_stop_loss_long == True):
        porcentaje_nuevo_stop_loss_long = ((float(bloque_short)-float(bloque_long))/float(bloque_long))/2
        bloque_stop_loss_long = float(bloque_long)-(float(bloque_long)*(porcentaje_nuevo_stop_loss_long/100))
    if(recalcular_stop_loss_short== True):
        porcentaje_nuevo_stop_loss_short = (abs(float(bloque_long)-float(bloque_short))/float(bloque_short))/2
        bloque_stop_loss_short = float(bloque_long)-(float(bloque_long)*(porcentaje_nuevo_stop_loss_short/100))

    

    #relación de riesgo:
    #print(d_bloques_compra)
    porcentaje_stop_loss_long = (abs(float(bloque_stop_loss_long) -float(bloque_long))/float(bloque_long))*100
    porcentaje_stop_loss_short = (abs(float(bloque_stop_loss_short) - float(bloque_short))/float(bloque_short))*100

    porcentaje_take_profit_long = (abs(float(bloque_short) - float(bloque_long))/float(bloque_long))*100
    porcentaje_take_profit_short = (abs(float(bloque_long )- float(bloque_short))/float(bloque_short))*100

    try:
        if(porcentaje_stop_loss_long == 0):
            porcentaje_stop_loss_long = porcentaje_take_profit_long/2
        if(porcentaje_stop_loss_short== 0):
            porcentaje_stop_loss_short = porcentaje_take_profit_short/2

        distancia_short = abs(((float(bloque_short) - float(response['indexPrice']))/float(response['indexPrice'])))*100 
        distancia_long = abs(((float(bloque_long) - float(response['indexPrice']))/float(response['indexPrice'])))*100

        rb_long = round(porcentaje_take_profit_long/porcentaje_stop_loss_long,2)
        rb_short = round(porcentaje_take_profit_short/porcentaje_stop_loss_short,2)
    except:
       return 
    
    info.latestPrice = float(response['indexPrice'])
    info.longEntry = float(bloque_long)
    info.shortEntry = float(bloque_short)
    info.shortStopLoss = float(bloque_stop_loss_short)
    info.longStopLoss = float(bloque_stop_loss_long)
    info.longRiskBenefitRatio = rb_long
    info.shortRiskBenefitRatio = rb_short
    info.longDistance = distancia_long
    info.shortDistance = distancia_short
    return info

