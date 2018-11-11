# encoding: UTF-8
import sys
sys.path.append('./strat')
from dtStrat import *
from func import *
import json

settingFileName = sys.argv[1]
setting = json.load(open('conf/' + settingFileName))
strat = testStrategy(setting)
okApi = okApi(setting['apiKey'], setting['secretKey'])
while(True):
    tick = okApi.get_okex("/api/futures/v3/instruments/" + setting['okSymbol'] + "/ticker")
    t = VtTickData()   
    # 成交数据
    t.lastPrice = tick['last']           # 最新成交价
    t.volume = 0                 # 今天总成交量
    t.openInterest = 0           # 持仓量
    try:
        t.datetime = datetime.strptime(tick['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')                    # python的datetime时间对象    
        strat.onTick(t)
    except ValueError:
        continue
    time.sleep(1)