# encoding: UTF-8

"""
展示如何执行策略回测。
"""

from __future__ import division

from vnpy.trader.app.ctaStrategy.ctaBacktesting import BacktestingEngine, MINUTE_DB_NAME, formatNumber, copy, TradingResult
from vnpy.trader.vtConstant import *
from vnpy.trader.app.ctaStrategy.strategy.strategyDualThrustC import DualThrustStrategyC
import sys
import Constant
import pandas as pd

#dbname = sys.argv[1]
symbol = sys.argv[1]
#resFile = sys.argv[3]
#dbname = 'BTCUSDT'
#dbname = 'EOSUSDT'
#symbol = 'EOS'
#resFile = 'res/EOS.csv'
#pnlFile = 'res/EOSpnl.csv'
startDate = '20180717'
capital = 10000
ratio = 0.5

def displayResult(engine, capital):
    d = engine.calculateBacktestingResult()
    # 输出
    engine.output('-' * 30)
    engine.output(u'第一笔交易：\t%s' % d['timeList'][0])
    engine.output(u'最后一笔交易：\t%s' % d['timeList'][-1])
    
    engine.output(u'总交易次数：\t%s' % formatNumber(d['totalResult']))        
    engine.output(u'总盈亏：\t%s' % formatNumber(d['capital']))
    engine.output(u'最大回撤: \t%s' % formatNumber(min(d['drawdownList'])))                
    
    engine.output(u'平均每笔盈利：\t%s' %formatNumber(d['capital']/d['totalResult']))
    engine.output(u'平均每笔滑点：\t%s' %formatNumber(d['totalSlippage']/d['totalResult']))
    engine.output(u'平均每笔佣金：\t%s' %formatNumber(d['totalCommission']/d['totalResult']))
    
    engine.output(u'胜率\t\t%s%%' %formatNumber(d['winningRate']))
    engine.output(u'盈利交易平均值\t%s' %formatNumber(d['averageWinning']))
    engine.output(u'亏损交易平均值\t%s' %formatNumber(d['averageLosing']))
    engine.output(u'盈亏比：\t%s' %formatNumber(d['profitLossRatio']))
    engine.output(u'percentage：\t%s' %formatNumber((d['capital'] + capital) / capital * 100))

def getResultList(engine, param):
    """
    计算回测结果
    """
    engine.output(u'计算回测结果')
    
    # 首先基于回测后的成交记录，计算每笔交易的盈亏
    resultList = []             # 交易结果列表
    
    longTrade = []              # 未平仓的多头交易
    shortTrade = []             # 未平仓的空头交易
    
    tradeTimeList = []          # 每笔成交时间戳
    posList = [0]               # 每笔成交后的持仓情况        

    for trade in engine.tradeDict.values():
        # 复制成交对象，因为下面的开平仓交易配对涉及到对成交数量的修改
        # 若不进行复制直接操作，则计算完后所有成交的数量会变成0
        trade = copy.copy(trade)
        
        # 多头交易
        if trade.direction == DIRECTION_LONG:
            # 如果尚无空头交易
            if not shortTrade:
                longTrade.append(trade)
            # 当前多头交易为平空
            else:
                while True:
                    entryTrade = shortTrade[0]
                    exitTrade = trade
                    
                    # 清算开平仓交易
                    closedVolume = min(exitTrade.volume, entryTrade.volume)
                    result = TradingResult(entryTrade.price, entryTrade.dt, 
                                           exitTrade.price, exitTrade.dt,
                                           -closedVolume, engine.rate, engine.slippage, engine.size)
                    resultList.append(result)
                    
                    posList.extend([-1,0])
                    tradeTimeList.extend([result.entryDt, result.exitDt])
                    
                    # 计算未清算部分
                    entryTrade.volume -= closedVolume
                    exitTrade.volume -= closedVolume
                    
                    # 如果开仓交易已经全部清算，则从列表中移除
                    if not entryTrade.volume:
                        shortTrade.pop(0)
                    
                    # 如果平仓交易已经全部清算，则退出循环
                    if not exitTrade.volume:
                        break
                    
                    # 如果平仓交易未全部清算，
                    if exitTrade.volume:
                        # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                        # 等于新的反向开仓交易，添加到队列中
                        if not shortTrade:
                            longTrade.append(exitTrade)
                            break
                        # 如果开仓交易还有剩余，则进入下一轮循环
                        else:
                            pass
                    
        # 空头交易        
        else:
            # 如果尚无多头交易
            if not longTrade:
                shortTrade.append(trade)
            # 当前空头交易为平多
            else:                    
                while True:
                    entryTrade = longTrade[0]
                    exitTrade = trade
                    
                    # 清算开平仓交易
                    closedVolume = min(exitTrade.volume, entryTrade.volume)
                    result = TradingResult(entryTrade.price, entryTrade.dt, 
                                           exitTrade.price, exitTrade.dt,
                                           closedVolume, engine.rate, engine.slippage, engine.size)
                    resultList.append(result)
                    
                    posList.extend([1,0])
                    tradeTimeList.extend([result.entryDt, result.exitDt])

                    # 计算未清算部分
                    entryTrade.volume -= closedVolume
                    exitTrade.volume -= closedVolume
                    
                    # 如果开仓交易已经全部清算，则从列表中移除
                    if not entryTrade.volume:
                        longTrade.pop(0)
                    
                    # 如果平仓交易已经全部清算，则退出循环
                    if not exitTrade.volume:
                        break
                    
                    # 如果平仓交易未全部清算，
                    if exitTrade.volume:
                        # 且开仓交易已经全部清算完，则平仓交易剩余的部分
                        # 等于新的反向开仓交易，添加到队列中
                        if not longTrade:
                            shortTrade.append(exitTrade)
                            break
                        # 如果开仓交易还有剩余，则进入下一轮循环
                        else:
                            pass                    
    
    # 到最后交易日尚未平仓的交易，则以最后价格平仓
    if engine.mode == engine.BAR_MODE:
        endPrice = engine.bar.close
    else:
        endPrice = engine.tick.lastPrice
        
    for trade in longTrade:
        result = TradingResult(trade.price, trade.dt, endPrice, engine.dt, 
                               trade.volume, engine.rate, engine.slippage, engine.size)
        resultList.append(result)
        
    for trade in shortTrade:
        result = TradingResult(trade.price, trade.dt, endPrice, engine.dt, 
                               -trade.volume, engine.rate, engine.slippage, engine.size)
        resultList.append(result)            

    df = pd.DataFrame([{'entryPrice': x.entryPrice, 'exitPrice': x.exitPrice, 'entryDt': x.entryDt, 'exitDt': x.exitDt, 'volume': x.volume, 'turnover': x.turnover, 'commission': x.commission, 'slippage': x.slippage, 'pnl': x.pnl } for x in resultList])
    df['size'] = capital * ratio / 100.0 / Constant.currentPrice[param['symbol']]
    df.to_csv(Constant.pnlFile[param['symbol']])

def backTesting(st, param):
    # 创建回测引擎
    engine = BacktestingEngine()
    # 设置引擎的回测模式为K线
    engine.setBacktestingMode(engine.BAR_MODE)
    # 设置回测用的数据起始日期
    engine.setStartDate(param['sd'])
    # 设置产品相关参数
    engine.setSlippage(2 * Constant.tick[symbol])     # 股指1跳
    engine.setRate(10/10000)   # 万10
    #engine.setSize(1)         # 股指合约大小 
    size = capital / Constant.currentPrice[param['symbol']]
    print(size)
    engine.setSize(11)         # 股指合约大小 
    #print("size: " + str( capital / 10.0 / param['currentPrice']))
    engine.setPriceTick(Constant.tick[symbol])    # 股指最小价格变动
    engine.setCapital(param['capital'])
    # 设置使用的历史数据库
    engine.setDatabase(MINUTE_DB_NAME, Constant.dbname[param['symbol']])
    
    # 在引擎中创建策略对象
    #d = {'rsiEntry': 30, 'atrLength': 20, 'artMaLength': 10, 'rsiLength': 40, 'fixedSize': 100, 'trailingPercent': 5, 'initDays': 20 }          # 初始化数据所用的天数}
    #d = {'initDays': 10, 'slMultiplier': 8, 'fixedSize': 1, 'bollDev': 6, 'bollWindow': 20}
    d = {'k1': Constant.dualThrustK1[param['symbol']], 'k2': Constant.dualThrustK2[param['symbol']], 'fixedSize': 10.0}
    print(d)
    engine.initStrategy(DualThrustStrategy, d)
    
    # 开始跑回测
    engine.runBacktesting()
    d = engine.tradeDict
    res = pd.DataFrame([d[k].__dict__ for k in d.keys()])
    res['direction'] = pd.Series([ 1 if x == u'\u7a7a' else -1 for x in res['direction']])
    res['offset'] = pd.Series(['open' if x == u'\u5f00\u4ed3' else 'close' for x in res['offset']])
    res.to_csv(Constant.resFile[param['symbol']])
    displayResult(engine, param['capital'])
    getResultList(engine, param)
    #engine.showResultNoDraw()
    # 显示回测结果
    #engine.showBacktestingResult()
    return engine

if __name__ == '__main__':
    param = {'sd': startDate, 'symbol': symbol, 'capital': Constant.currentPrice[symbol] * 11}
    engine = backTesting(DualThrustStrategy, param)
    # 在引擎中创建策略对象
    #d = {'rsiEntry': 30, 'atrLength': 20, 'artMaLength': 10, 'rsiLength': 40, 'fixedSize': 100, 'trailingPercent': 5, 'initDays': 20 }          # 初始化数据所用的天数}
    #d = {'initDays': 10, 'slMultiplier': 8, 'fixedSize': 1, 'bollDev': 6, 'bollWindow': 20}
    #d = {'k1': 0.8, 'k2': 0.4, 'fixedSize': 100}