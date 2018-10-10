# encoding: UTF-8
from HttpMD5Util import buildMySign,httpGet,httpPost
import logging
import time
import hashlib
import json
from constants import *
import socket
import math
def getAmount(sym):
    qs = getSpotPrice(sym)
    print(qs)
    spotBid1 = qs["bids"][0][0]
    spotAsk1 = qs["asks"][-1][0]
    midPrice = (spotBid1 + spotAsk1) / 2
    futureInfo = getFutureUserInfo(sym)
    marginInUSD = midPrice * futureInfo['balance']
    totalShares = 3 * marginInUSD / 10 if sym != 'btc' else marginInUSD / 100
    return str(totalShares / 2)


def fundDevolve(sym, transType, amount):
    post_data={"api_key": apiKey, 'symbol': sym, 'amount': amount,'type': transType }
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = {}
    res = json.loads(httpPost("www.okex.com","/api/v1/future_devolve.do", post_data))
    return res

def getSpotUserInfo():
    post_data={"api_key": apiKey }
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = {}
    res = json.loads(httpPost("www.okex.com","/api/v1/userinfo.do", post_data))
    return res

def getFutureKline(symbol, startTime):
    params = 'symbol=%s&type=1day&since=%d&contract_type=this_week'%(symbol, startTime)
    return httpGet("www.okex.com","/api/v1/future_kline.do", params)

def getSpotCurrency(sym):
    res = getSpotUserInfo()
    return res['info']['funds']['free']['eos']

def getFutureUserInfo(sym):
    post_data={"api_key": apiKey }
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = {}
    res = json.loads(httpPost("www.okex.com","/api/v1/future_userinfo_4fix.do", post_data))
    return res['info'][sym]

def getSpotPrice(sym):
    return httpGet("www.okex.com", "/api/v1/depth.do", 'symbol='+ sym + '_usdt&size=5')

def getFuturePrice(sym, contractType):
    return httpGet("www.okex.com", "/api/v1/future_depth.do", 'symbol='+ sym + '_usd&contract_type=' + contractType + '&size=5')

def getFuturePosition(sym, contractType):
    post_data={'symbol': sym, 'contract_type': contractType, 'api_key': apiKey}
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = json.loads(httpPost("www.okex.com","/api/v1/future_position", post_data))
    return res

def getFutureOrderInfo(sym, contractType, orderId):
    post_data={'symbol': sym, 'contract_type': contractType, 'api_key': apiKey, 'order_id': orderId}
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = json.loads(httpPost("www.okex.com","/api/v1/future_order_info", post_data))
    return res['orders']  

def tradeSpread(logger, sym, amount, isLong):
    if not isLong:
        res1 = futureTrade(logger, sym, "next_week", amount, '1', '1')
        res2 = futureTrade(logger, sym, "quarter", amount, '2', '1')
    else:
        res1 = futureTrade(logger, sym, "next_week", amount, '2','1')
        res2 = futureTrade(logger, sym, "quarter", amount, '1', '1')
    return True

def clearPosition(logger, sym):
    res1 = getFuturePosition(sym, 'next_week')
    res2 = getFuturePosition(sym, 'quarter')
    if len(res1['holding']) > 0 and res1['holding'][0]['buy_available'] > 0:
        futureTrade(logger, sym, 'next_week', res1['holding'][0]['buy_available'], '3', '1')
    if len(res1['holding']) > 0 and res1['holding'][0]['sell_available'] > 0:
        futureTrade(logger, sym, 'next_week', res1['holding'][0]['sell_available'], '4', '1')
    if len(res2['holding']) > 0 and res2['holding'][0]['buy_available'] > 0:
        futureTrade(logger, sym, 'quarter', res2['holding'][0]['buy_available'], '3', '1')
    if len(res2['holding']) > 0 and res2['holding'][0]['sell_available'] > 0:
        futureTrade(logger, sym, 'quarter', res2['holding'][0]['sell_available'], '4', '1')
    
def futureCancel(params):
    params['api_key'] = apiKey
    params['sign'] = buildMySign(params, secretKey)
    return json.loads(httpPost("www.okex.com","/api/v1/future_cancel", params))

def futureTrade(params):
    #buildMySign是生成签名的函数，交易所通常会要求提供
    #remainingAmount = math.floor(float(amount))
    
    #futurePrice =getFuturePrice(sym, contractType)
    #price = 0
    #if tradeType == '1' or tradeType == '3':
    #    price = futurePrice['asks'][-1][0]
    #if tradeType == '2' or tradeType == '4':
    #    price = futurePrice['bids'][0][0]
    params['api_key'] = apiKey
    params['sign'] = buildMySign(params, secretKey)
    res=json.loads(httpPost("www.okex.com","/api/v1/future_trade.do", params))
    #print(res)

    #order = getFutureOrderInfo(sym, contractType, res['order_id'])
    #print(remainingAmount)
    #print(float(order[0]['deal_amount']))
    #remainingAmount = remainingAmount - float(order[0]['deal_amount'])
    #if remainingAmount != 0:
    #futureCancel(sym, contractType, res['order_id'])
    return res

