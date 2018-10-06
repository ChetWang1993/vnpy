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

def getKline(symbol, startTime):
    params = 'symbol=%s&type=1day&since=%d'%(symbol, startTime)
    return httpGet("www.okex.com","/api/v1/kline.do", params)

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
    post_data={'symbol': sym+'_usd', 'contract_type': contractType, 'api_key': apiKey}
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = json.loads(httpPost("www.okex.com","/api/v1/future_position_4fix", post_data))
    return res

def getFutureOrderInfo(sym, contractType, orderId):
    post_data={'symbol': sym, 'contract_type': contractType, 'api_key': apiKey, 'order_id': orderId}
    post_data['sign'] = buildMySign(post_data, secretKey)
    res = json.loads(httpPost("www.okex.com","/api/v1/future_order_info", post_data))
    return res['orders']

def futureCancel(sym, contractType, orderId):
    post_data={'symbol': sym, 'contract_type': contractType, 'api_key': apiKey, 'order_id': orderId}
    post_data['sign'] = buildMySign(post_data, secretKey)
    return json.loads(httpPost("www.okex.com","/api/v1/future_cancel", post_data))
    

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
    

def futureTrade(logger, sym, contractType, amount, tradeType, matchPrice):
    #buildMySign是生成签名的函数，交易所通常会要求提供
    remainingAmount = math.floor(float(amount))
    
    while remainingAmount != 0:
        futurePrice =getFuturePrice(sym, contractType)
        price = 0
        if tradeType == '1' or tradeType == '3':
            price = futurePrice['asks'][-1][0]
        if tradeType == '2' or tradeType == '4':
            price = futurePrice['bids'][0][0]
        post_data={"api_key": apiKey, "symbol" : sym, "contract_type" : contractType, "price" : price, "amount" : float(remainingAmount), "type": tradeType, "match_price" : matchPrice }
        post_data['sign'] = buildMySign(post_data, secretKey)
        res=json.loads(httpPost("www.okex.com","/api/v1/future_trade.do", post_data))
        print(res)
        if res['result'] == False:
            logger.error("Fail to place order " + str(res['error_code']), extra={'executionPrice': price, 'amount': float(remaingAmount), 'tradeType': tradeType, 'contract': contractType, 'sym': sym})
            continue
        time.sleep(5)
        order = getFutureOrderInfo(sym, contractType, res['order_id'])
        print(remainingAmount)
        print(float(order[0]['deal_amount']))
        remainingAmount = remainingAmount - float(order[0]['deal_amount'])
        if remainingAmount != 0:
            futureCancel(sym, contractType, res['order_id'])
        logger.info("Successfully place order " + str(res['order_id']), extra={'executionPrice': price, 'amount': order[0]['deal_amount'], 'tradeType': tradeType, 'contract': contractType, 'sym': sym})
    return res

