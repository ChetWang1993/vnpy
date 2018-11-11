# encoding: UTF-8
from HttpMD5Util import signature, get_header
import time
import json
from constants import *
import math
import requests
from datetime import datetime, timedelta

class okApi():
    def __init__(self, apiKey, secretKey):
        self.apiKey = str(apiKey)
        self.secretKey = str(secretKey)
    def get_okex(self, requestPath, params = {}):
        paramStr = ''
        if params != {}:
            paramStr += '?'
            for key in params:
                paramStr += (key + '=' + params[key] + '&')
            paramStr = paramStr[:-1]
        timestamp = requests.get(base_url + '/api/general/v3/time').json()['iso']
        header = get_header(self.apiKey, signature(self.secretKey, timestamp, 'GET', requestPath), timestamp, passphrase)
        res = requests.get(base_url + requestPath + paramStr, headers=header).json()
        #print(res)
        return res

    def post_okex(self, requestPath, params = {}):
        timestamp = requests.get(base_url + '/api/general/v3/time').json()['iso']
        body = json.dumps(params)
        header = get_header(self.apiKey, signature(self.secretKey, timestamp, 'POST', requestPath, body), timestamp, passphrase)
        res = requests.post(base_url + requestPath, headers=header, data=body).json()
        print(res)
        return res

startTime = (datetime.now() - timedelta(1)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
endTime = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
params = {'start': startTime, 'end': endTime, 'granularity': '86400'}
#okApi = okApi('f4437433-0378-4535-8ba6-1fdffce6cea5', '589CCC3715DE217F935343DD2F4EE06E')
#okApi.get_okex("/api/futures/v3/instruments/" + 'BTC-USD-181116' + "/candles", params)
#okApi.get_okex("/api/futures/v3/" + 'BTC-USD-181116' + "/position")
#post_okex("/api/futures/v3/order", {"instrument_id":"EOS-USD-181116", "type":"1","price":"432.11","size":"10","match_price":"1","leverage":"10"})
#get_okex("/api/futures/v3/orders/BTC-USD-181116")
