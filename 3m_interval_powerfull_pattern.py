import logging
import sys
import powerfull_pattern_strategy
from common import(coins)


logging.basicConfig(filename='3m_interval_powerfull_pattern.txt', level=logging.ERROR,filemode='a')

sys.stderr = open('3merror.txt', 'w')
try:
   powerfull_pattern_strategy.calculate_powerfull_pattern('3m',True,coins)
except Exception as e:
    print(str(e))
                













