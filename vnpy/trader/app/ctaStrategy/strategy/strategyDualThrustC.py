# encoding: UTF-8

"""
DualThrust交易策略
"""

from datetime import datetime, date, time, timedelta
import datetime
from vnpy.trader.vtObject import VtBarData
from vnpy.trader.vtConstant import EMPTY_STRING
from vnpy.trader.app.ctaStrategy.ctaTemplate import CtaTemplate, BarGenerator
#from binance.client import Client
from vnpy.api.okex.func import *
from vnpy.trader.app.ctaStrategy.ctaBase import *
########################################################################
class DualThrustCStrategy(CtaTemplate):
    """DualThrust交易策略"""
    className = 'DualThrustStrategyC'
    author = u'用Python的交易员'

    # 策略参数
    fixedSize = 100
    k1 = 0.6
    k2 = 0.4

    initDays = 0
    longPos = 0.0
    shortPos = 0.0
    isStop = False
    # 策略变量
    barList = []                # K线对象的列表

    dayOpen = 0.0
    dayHigh = 0.0
    dayLow = 0.0
    
    range = 0.0
    longEntry = 0.0
    shortEntry = 0.0

    longEntered = False
    shortEntered = False

    # 参数列表，保存了参数的名称
    paramList = ['name',
                 'className',
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
    def __init__(self, ctaEngine, setting):
        """Constructor"""
        super(DualThrustCStrategy, self).__init__(ctaEngine, setting) 
        
        self.bg = BarGenerator(self.onBar)
        self.barList = []

    #----------------------------------------------------------------------
    def onInit(self):
        """初始化策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略初始化' %self.name)
    
        # 载入历史数据，并采用回放计算的方式初始化策略数值
        #initData = self.loadBar(self.initDays)
        #for bar in initData:
        #    self.onBarInit(bar)
        self.initPrice()
        self.putEvent()

    #----------------------------------------------------------------------
    def onStart(self):
        """启动策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略启动' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onStop(self):
        """停止策略（必须由用户继承实现）"""
        self.writeCtaLog(u'%s策略停止' %self.name)
        self.putEvent()

    #----------------------------------------------------------------------
    def onTick(self, tick):
        """收到行情TICK推送（必须由用户继承实现）"""
        self.bg.updateTick(tick)

    def initPrice(self):
        try:
            apiKey = 'R0546VwwTnhBNXdxi9a9Z7dkRHnCP8DyY0ah8KTDClxZqEOBaFkKgYLTLF8Acow8'
            secretKey = 'J72JCQIxm3RRFDIwFXNWnSlmgKadEqaz184j2sjSeBGLBu9dDZ7kB7ImPR6Jdgqx'
            today = datetime.datetime.now() - timedelta(1)
            yesterday = datetime.datetime.now() - timedelta(2)
            klinesY = getFutureKline(self.__dict__['vtSymbol'], time.mktime(yesterday.timetuple()) * 1000)
            klinesT = getFutureKline(self.__dict__['vtSymbol'], time.mktime(today.timetuple()) * 1000)
            print("%s yesterday kline"%(self.__dict__['okSymbol']))
            print(klinesY)
            print("%s today kline"%(self.__dict__['okSymbol']))
            print(klinesT)
            self.dayHigh = float(klinesT[0][2])
            self.dayLow = float(klinesT[0][3])
            self.dayOpen = float(klinesT[0][1])
            self.dayClose = float(klinesT[0][4])
            self.range = float(klinesY[0][2]) - float(klinesY[0][3])
            self.longEntry = float(klinesT[0][1]) + self.k1 * self.range
            self.shortEntry = float(klinesT[0][1]) - self.k2 * self.range
        except KeyError:
            print("%s get kline error"%(self.__dict__['okSymbol']))
            return 0.0        

    #----------------------------------------------------------------------
    def onBarInit(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 计算指标数值
        self.barList.append(bar)
        
        if len(self.barList) <= 2:
            return
        else:
            self.barList.pop(0)
        lastBar = self.barList[-2]
        
        # 新的一天
        if lastBar.datetime.date() != bar.datetime.date():
            # 如果已经初始化
            if self.dayHigh:
                self.range = self.dayHigh - self.dayLow
                self.longEntry = bar.open + self.k1 * self.range
                self.shortEntry = bar.open - self.k2 * self.range           
                
            self.dayOpen = bar.open
            self.dayHigh = bar.high
            self.dayLow = bar.low

            self.longEntered = False
            self.shortEntered = False
        else:
            self.dayHigh = max(self.dayHigh, bar.high)
            self.dayLow = min(self.dayLow, bar.low)

        self.putEvent()
        
    #----------------------------------------------------------------------
    def onBar(self, bar):
        """收到Bar推送（必须由用户继承实现）"""
        # 撤销之前发出的尚未成交的委托（包括限价单和停止单）
        self.cancelAll()
        self.updatePos()
        #if self.longPos == 0:
        #    self.buy(self.longEntry, self.fixedSize, stop=self.isStop)
            #if self.longPos > 0:
        #    self.sell(self.longEntry, self.longPos, stop=self.isStop)
        print("%s long pos: %f short pos: %f"%(self.__dict__['okSymbol'], self.longPos, self.shortPos))
        # 计算指标数值
        self.barList.append(bar)
        if len(self.barList) <= 2:
            return
        else:
            self.barList.pop(0)
        lastBar = self.barList[-2]
        
        # 新的一天
        if lastBar.datetime.date() != bar.datetime.date():
            # 如果已经初始化
            if self.dayHigh:
                self.range = self.dayHigh - self.dayLow
                self.longEntry = bar.open + self.k1 * self.range
                self.shortEntry = bar.open - self.k2 * self.range           
                
            self.dayOpen = bar.open
            self.dayHigh = bar.high
            self.dayLow = bar.low

            self.longEntered = False
            self.shortEntered = False
        else:
            self.dayHigh = max(self.dayHigh, bar.high)
            self.dayLow = min(self.dayLow, bar.low)

        print("%s h: %f, l: %f, o: %f, c: %f, range: %f, dh: %f, dl: %f, do: %f, dc: %f"\
            %(self.__dict__['okSymbol'], self.dayHigh, self.dayLow, bar.open, bar.close, self.range, self.dayHigh, self.dayLow, self.dayOpen, self.dayClose))
        print("%s long entry: %f, short entry: %f, lp: %f, sp: %f" % (self.__dict__['okSymbol'], self.longEntry, self.shortEntry, self.longPos, self.shortPos))

        if not self.range:
            return

        if self.longPos == 0.0 and self.shortPos == 0.0:
            if bar.close > self.dayOpen:
                if not self.longEntered and bar.close >= self.longEntry:
                    print("%s buy, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.longEntry, self.fixedSize))
                    self.buy(self.longEntry, self.fixedSize, stop=self.isStop)
            else:
                if not self.shortEntered and bar.close <= self.shortEntry:
                    print("%s short, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.shortEntry, self.fixedSize))
                    self.short(self.shortEntry, self.fixedSize, stop=self.isStop)

        # 持有多头仓位
        elif self.longPos > 0.0:
            self.longEntered = True

            # 多头止损单
            if bar.close <= self.shortEntry:
                print("%s sell, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.shortEntry, self.longPos))
                self.sell(self.shortEntry, self.longPos, stop=self.isStop)
            
            # 空头开仓单
                if not self.shortEntered:
                    print("%s short, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.shortEntry, self.fixedSize))
                    self.short(self.shortEntry, self.fixedSize, stop=self.isStop)
            
        # 持有空头仓位
        elif self.shortPos > 0.0:
            self.shortEntered = True

            # 空头止损单
            if bar.close >= self.longEntry:
                print("%s cover, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.longEntry, self.shortPos))
                self.cover(self.longEntry, self.shortPos, stop=self.isStop)
                
                # 多头开仓单
                if not self.longEntered:
                    print("%s long, price: %f, pos: %f"%(self.__dict__['okSymbol'], self.longEntry, self.fixedSize))
                    self.buy(self.longEntry, self.fixedSize, stop=self.isStop)
 
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onOrder(self, order):
        """收到委托变化推送（必须由用户继承实现）"""
        pass

    #----------------------------------------------------------------------
    def onTrade(self, trade):
        # 发出状态更新事件
        self.putEvent()

    #----------------------------------------------------------------------
    def onStopOrder(self, so):
        """停止单推送"""
        pass

    def updatePos(self):
        try:
            balance = getFuturePosition(self.__dict__['okSymbol'], 'this_week');
            self.longPos =  balance['holding'][0]['buy_amount']
            self.shortPos = balance['holding'][0]['sell_amount']
        except IndexError:
            print("%s get pos error"%(self.__dict__['okSymbol']))
            self.longPos = 0.0
            self.shortPos = 0.0

    def coverAll(self, price, stop=False):
        """买平"""
	self.updatePos()
        return self.sendOrder(CTAORDER_COVER, price, self.longPos, stop)
