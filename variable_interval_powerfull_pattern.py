import logging
import sys
import powerfull_pattern_strategy
from common import(coins)




logging.basicConfig(filename='variable_interval_powerfull_pattern.txt', level=logging.ERROR,filemode='a')
sys.stderr = open('error.txt', 'w')
try:
   powerfull_pattern_strategy.calculate_powerfull_pattern('5m',True,coins)
except Exception as e:
    print(str(e))
                

















