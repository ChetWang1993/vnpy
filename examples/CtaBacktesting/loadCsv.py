# encoding: UTF-8

"""
导入MC导出的CSV历史数据到MongoDB中
"""

from vnpy.trader.app.ctaStrategy.ctaBase import MINUTE_DB_NAME
from vnpy.trader.app.ctaStrategy.ctaHistoryData import loadMcCsv
import sys

filename = sys.argv[1]
dbname = sys.argv[2]
if __name__ == '__main__':
    loadMcCsv(filename, MINUTE_DB_NAME, dbname)
    #loadMcCsv('rb0000_1min.csv', MINUTE_DB_NAME, 'rb0000')

