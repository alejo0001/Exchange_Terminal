from BybitWebsocket import BybitWebsocket
import logging
from time import sleep
from os import system

API_KEY = ""
API_SECRET = ""

def setup_logger():
    # Prints logger info to terminal
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Change this to DEBUG if you want a lot more info
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


if __name__ == "__main__":
    logger = setup_logger()

    #inverse perpetual
    
    # ws = BybitWebsocket(wsURL="wss://stream.bytick.com/realtime",
    #                      api_key=API_KEY, api_secret=API_SECRET
    #                     )

    # ws.subscribe_orderBookL2("BTCUSD")
    # ws.subscribe_orderBookL2("BTCUSD", 200)# only support 200
    # # ws.subscribe_kline("BTCUSD", '1')
    # # ws.subscribe_instrument_info('BTCUSD')
    # # ws.subscribe_trade("BTCUSD")
    # # ws.subscribe_insurance() # only support inverse perpetual
    # # ws.subscribe_order()
    # # ws.subscribe_stop_order()
    # # ws.subscribe_execution()
    # #ws.subscribe_position()
    # while(1):
    #     logger.info(ws.get_orderBookL2("BTCUSD"))
    #     logger.info(ws.get_orderBookL2("BTCUSD", 200))
    #     # logger.info(ws.get_kline('BTCUSD', '1'))
    #     # logger.info(ws.get_instrument_info("BTCUSD"))
    #     # logger.info(ws.get_trade("BTCUSD"))
    #     # logger.info(ws.get_insurance("BTC"))
    #     # logger.info(ws.get_insurance("ETH"))
    #     # logger.info(ws.get_order())
    #     # logger.info(ws.get_stop_order())
    #     # logger.info(ws.get_execution())
    #     # logger.info(ws.get_position())
    #     sleep(1)


    # usdt perpetual

    ws_public = BybitWebsocket(wsURL="wss://stream.bytick.com/realtime_public",
                         api_key=API_KEY, api_secret=API_SECRET
                        )
    ws_private = BybitWebsocket(wsURL="wss://stream.bytick.com/realtime_private",
                         api_key=API_KEY, api_secret=API_SECRET
                        )

    ws_public.subscribe_orderBookL2("MATICUSDT")
    ws_public.subscribe_orderBookL2("MATICUSDT", 200)
    ws_public.subscribe_kline("MATICUSDT", '1')
    ws_public.subscribe_instrument_info('MATICUSDT')
    ws_public.subscribe_trade("MATICUSDT")
    ws_private.subscribe_order()
    ws_private.subscribe_stop_order()
    ws_private.subscribe_execution()
    ws_private.subscribe_position()
    ws_private.subscribe_wallet() # only support USDT perpetual
    
    # ws_public.subscribe_orderBookL2("MATICUSDT")
    # ws_public.subscribe_kline("MATICUSDT", '1m')
    # ws_public.subscribe_trade("MATICUSDT")
    # ws_private.subscribe_instrument_info('MATICUSDT')
    # ws_private.subscribe_order()
    # ws_private.subscribe_execution()
    # ws_private.subscribe_position()    
    # ws_private.subscribe_insurance()

    while(1):
        system('cls')
        logger.info(ws_public.get_orderBookL2("MATICUSDT"))
        logger.info(ws_public.get_orderBookL2("MATICUSDT", 200))
        logger.info(ws_public.get_kline('MATICUSDT', '1'))
        logger.info(ws_public.get_instrument_info("MATICUSDT"))
        logger.info(ws_public.get_trade("MATICUSDT"))
        logger.info(ws_private.get_order())
        logger.info(ws_private.get_stop_order())
        logger.info(ws_private.get_execution())
        logger.info("Posición:")
        logger.info(ws_private.get_position())
        logger.info(ws_private.get_wallet())

        # logger.info(ws_public.get_data("orderBookL2_25.MATICUSDT"))
        # logger.info(ws_private.get_data("instrument_info.100ms.MATICUSDT"))
        # #logger.info(ws_public.get_data('kline.MATICUSDT.1m'))
        # # logger.info(ws_private.get_data('order'))
        # # logger.info(ws_private.get_data("execution"))
        # logger.info("Posición:")
        # logger.info(ws_private.get_data("position"))
        # logger.info(ws_private.get_position())

        # logger.info(ws_private.get_data("instrument_info.100ms.BTCUSD"))
        # logger.info(ws_private.get_data('insurance.BTC'))
        # logger.info(ws_private.get_data('insurance.EOS'))
        sleep(1)