# encoding: UTF-8
from datetime import datetime, date, time, timedelta
import time
from func import *
from vnpy.trader.app.ctaStrategy.ctaTemplate import BarGenerator
from vnpy.trader.vtObject import VtBarData, VtTickData
########################################################################
class testStrategy():
    # 策略参数
    fixedSize = 0
    k1 = 0.6
    k2 = 0.4

    initDays = 0
    longPos = 0.0
    shortPos = 0.0
    matchPrice = True
    # 策略变量
    barList = []                # K线对象的列表
    dayOpen = 0.0
    dayHigh = 0.0
    dayLow = 0.0

    range = 0.0
    longEntry = 0.0
    shortEntry = 0.0
    apiKey = ""
    secretKey = ""

    # 参数列表，保存了参数的名称
    paramList = ['apiKey',
                 'secretKey',
                 'logFile',
                 'author',
                 'vtSymbol',
                 'okSymbol',
                 'k1',
                 'k2',
                 'initDays',
                 'fixedSize']

    # 变量列表，保存了变量的名称
    varList = ['inited',
               'trading',
               'pos',
               'range',
               'longEntry',
               'shortEntry']
    
    # 同步列表，保存了需要保存到数据库的变量名称
    syncList = ['pos']    

    #----------------------------------------------------------------------
    def __init__(self, setting):
        """Constructor"""
        self.bg = BarGenerator(self.onBar)
        self.barList = []
        if setting:
            d = self.__dict__
            for key in self.paramList:
                if key in setting:
                    d[key] = setting[key]
        print(u'策略初始化')
        self.okApi = okApi(self.apiKey, self.secretKey, self.logFile)
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        self.initPrice()
        #self.putEvent()
    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        #self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    def initPrice(self):
        self.updatePos()
        try:
            yyd = (datetime.now() - timedelta(2)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            yd = (datetime.now() - timedelta(1)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            td = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
            klinesY = self.okApi.get_okex("/api/futures/v3/instruments/" + self.okSymbol + "/candles", {'start': yyd, 'end': yd, 'granularity': '86400'})
            klinesT = self.okApi.get_okex("/api/futures/v3/instruments/" + self.okSymbol + "/candles", {'start': yd, 'end': td, 'granularity': '86400'})
            print("%s yesterday kline"%(self.__dict__['okSymbol']))
            print(klinesY)
            print("%s today kline"%(self.__dict__['okSymbol']))
            print(klinesT)
            self.dayOpen = float(klinesT[0][1])
            self.dayHigh = float(klinesT[0][2])
            self.dayLow = float(klinesT[0][3])
            self.dayClose = float(klinesT[0][4])
            self.range = float(klinesY[0][2]) - float(klinesY[0][3])
            self.longEntry = float(klinesT[0][1]) + self.k1 * self.range
            self.shortEntry = float(klinesT[0][1]) - self.k2 * self.range
        except KeyError:
            print("%s get kline error"%(self.__dict__['okSymbol']))
            return 0.0 
        return 0.0        

    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单
        bar.open = float(bar.open); bar.close = float(bar.close); bar.high = float(bar.high); bar.low = float(bar.low)
        print("--------------")
        self.cancelAll()
        self.updatePos()
        self.barList.append(bar)
        if len(self.barList) < 2:
            return
        lastBar = self.barList[-2]
        self.barList.pop(0)

        if lastBar.datetime.date() != bar.datetime.date():
            # 如果已经初始化
            if self.dayHigh:
                self.range = self.dayHigh - self.dayLow
                print("bo %f k1 %f k2 %f range %f" % (bar.open, self.k1, self.k2, self.range))
                self.longEntry = bar.open + self.k1 * self.range
                self.shortEntry = bar.open - self.k2 * self.range
            self.dayOpen = bar.open
            self.dayHigh = bar.high
            self.dayLow = bar.low
        else:
            self.dayHigh = max(self.dayHigh, bar.high)
            self.dayLow = min(self.dayLow, bar.low)

        print("%s %s h: %f, l: %f, o: %f, c: %f" % (str(bar.datetime), self.__dict__['okSymbol'], bar.high, bar.low, bar.open, bar.close))
        print("%s long entry: %f, short entry: %f, range: %f" % (self.__dict__['okSymbol'], self.longEntry, self.shortEntry, self.range))

        if self.longPos == 0.0 and self.shortPos == 0.0:
            if bar.close > self.dayOpen and bar.close >= self.longEntry:
                self.order(self.longEntry, self.fixedSize, BUY)
            elif bar.close <= self.shortEntry:
                self.order(self.shortEntry, self.fixedSize, SHORT)

        # 持有多头仓位
        elif self.longPos > 0.0:
            # 多头止损单
            if bar.close <= self.shortEntry:
                self.order(self.longEntry, int(self.longPos), SELL)
                self.order(self.shortEntry, self.fixedSize, SHORT)
        # 持有空头仓位
        elif self.shortPos > 0.0:
            # 空头止损单
            if bar.close >= self.longEntry:
                self.order(self.longEntry, int(self.shortPos), COVER)
                self.order(self.shortEntry, self.fixedSize, BUY)
      # 发出状态更新事件
        #self.putEvent()

    def updatePos(self):
        try:
            balance = self.okApi.get_okex("/api/futures/v3/" + self.okSymbol + "/position");
            self.longPos =  float(balance['holding'][0]['long_avail_qty'])
            self.shortPos = float(balance['holding'][0]['short_avail_qty'])
        except IndexError:
            print("%s get pos error"%(self.__dict__['okSymbol']))
            self.longPos = 0.0
            self.shortPos = 0.0
        print("%s long pos: %f short pos %f"%(self.okSymbol, self.longPos, self.shortPos))

    def cancelAll(self):
        res = self.okApi.get_okex("/api/futures/v3/orders/" + self.okSymbol)['order_info']
        orderIds = [x['order_id'] for x in res]
        print('order ids: %s' % str(orderIds))
        self.okApi.post_okex("/api/futures/v3/cancel_batch_orders/" + self.okSymbol, {"order_ids": orderIds})

    def order(self, price, size, orderType, matchPrice='1'):
        self.okApi.post_okex("/api/futures/v3/order", {"instrument_id": self.okSymbol, "type": orderType, "price": str(price),"size": str(size),"match_price": matchPrice,"leverage":"10"})
