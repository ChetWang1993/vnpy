# encoding: UTF-8

"""
展示如何执行参数优化。
"""

from __future__ import division
from __future__ import print_function
import sys

from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, OptimizationSetting
from vnpy.trader.app.ctaStrategy.strategy.strategyDualThrust import DualThrustStrategy
import Constant

if __name__ == '__main__':
    symbol = sys.argv[1]
    #symbol = 'EOS'
    
    # 创建回测引擎
    engine = BacktestingEngine()
    
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)

    # 设置回测用的数据起始日期
    engine.setStartDate('20180717')
    
    # 设置产品相关参数
    engine.setSlippage(2 * Constant.tick[symbol])     # 股指1跳
    engine.setRate(Constant.rate)   # 万3
    engine.setSize(1)         # 股指合约大小
    engine.setPriceTick(Constant.tick[symbol])    # 股指最小价格变动
    engine.setCapital(Constant.currentPrice[symbol] * Constant.fixedSize[symbol])
    
    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, Constant.dbname%symbol)
    
    # 跑优化
    setting = OptimizationSetting()                 # 新建一个优化任务设置对象
    setting.setOptimizeTarget('annualizedReturn')            # 设置优化排序的目标是策略净盈利
    setting.addParameter('k1', 0.3, 0.9, 0.05)    # 增加第一个优化参数atrLength，起始0.3，结束0.9，步进0.05
    setting.addParameter('k2', 0.3, 0.9, 0.05)        # 增加第二个优化参数atrMa，起始0.3, 结束0.9，步进0.05
    setting.addParameter('fixedSize', Constant.fixedSize[symbol])
    # 性能测试环境：I7-3770，主频3.4G, 8核心，内存16G，Windows 7 专业版
    # 测试时还跑着一堆其他的程序，性能仅供参考
    import time    
    start = time.time()
    
    # 运行单进程优化函数，自动输出结果，耗时：359秒
    #engine.runOptimization(AtrRsiStrategy, setting)            
    
    # 多进程优化，耗时：89秒
    engine.runParallelOptimization(DualThrustStrategy, setting)
    
    print(u'耗时：%s' %(time.time()-start))