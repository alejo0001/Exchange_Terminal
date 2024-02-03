import logging
import sys
import rsi_strategy
from common import(coins)


logging.basicConfig(filename='15m_interval_rsi.txt', level=logging.ERROR,filemode='a')

sys.stderr = open('15merror.txt', 'w')
try:
   rsi_strategy.calculate_powerfull_pattern('15m',True,coins)
except Exception as e:
    print(str(e))
                
