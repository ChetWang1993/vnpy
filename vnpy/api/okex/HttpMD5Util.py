#!/usr/bin/python
# -*- coding: utf-8 -*-
#用于进行http请求，以及MD5加密，生成签名的工具类

import http.client
import urllib
import json
import hashlib
import time
import socket
from constants import *

def sendRequest(self, channel, params=None):
    """发送请求"""
    # 生成请求
    d = {}
    d['event'] = 'addChannel'
    d['channel'] = channel

    # 如果有参数，在参数字典中加上api_key和签名字段
    if params is not None:
        params['api_key'] = apiKey
        params['sign'] = buildMySign(params, secreteKey)
        d['parameters'] = params

    # 使用json打包并发送
    j = json.dumps(d)

    # 若触发异常则重连
    try:
        self.ws.send(j)
        return True
    except websocket.WebSocketConnectionClosedException:
        self.reconnect()
        return False


def buildMySign(params,secretKey):
    sign = ''
    for key in sorted(params.keys()):
        sign += key + '=' + str(params[key]) +'&'
    data = sign+'secret_key='+secretKey
    return  hashlib.md5(data.encode("utf8")).hexdigest().upper()

def httpGet(url,resource,params=''):
    data = {}
    while(True):
        try:
            conn = http.client.HTTPSConnection(url, timeout=10)
            conn.request("GET",resource + '?' + params)
            response = conn.getresponse()
            data = response.read().decode('utf-8')            
            break
        except socket.timeout:
            continue
    return json.loads(data)

def httpPost(url,resource,params):
    headers = {
           "Content-type" : "application/x-www-form-urlencoded",
    }
    data = {}
    while(True):
        try:
            conn = http.client.HTTPSConnection(url, timeout=10)
            #temp_params = urllib.parse.urlencode(params)
            temp_params = urllib.urlencode(params)
            conn.request("POST", resource, temp_params, headers)
            response = conn.getresponse()
            data = response.read().decode('utf-8')
            params.clear()
            conn.close()
            break
        except socket.timeout:
            continue
    
    return data
