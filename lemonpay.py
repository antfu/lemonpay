#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.websocket
import urllib.parse
from   alipay           import Alipay
from   micropay         import Micropay
from   history          import History
from   configs.config   import configs

payment_methods = {
    'alipay':    Alipay(configs.alipay.app_id,configs.alipay.cert_path,configs.alipay.default_subject),
    'mircopay':  Micropay(configs.mircopay.app_id,configs.mircopay.mch_id,configs.mircopay.key,configs.mircopay.cert_path,configs.mircopay.cert_key_path)
}

history = History('lemonpay')

class root_handler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')

class payment_handler(tornado.web.RequestHandler):
    def post(self, input):
        request = json.loads(self.request.body.decode("utf-8"))
        _common_pay = payment_methods[request['method']]
        device_name = self.get_cookie('device_name')
        if device_name:
            device_name = urllib.parse.unquote(device_name)
        if input == 'pay':
            result = _common_pay.common_pay(request['fee_in_yuan'], request['auth_code'], request['out_trade_no'])
            if device_name:
                result.data['pay_device_name'] = device_name
        elif input == 'query':
            result = _common_pay.common_query(request['out_trade_no'])
        elif input == 'refund':
            result = _common_pay.common_refund(request['out_trade_no'], request['refund_fee_in_yuan'], request['total_fee_in_yuan'])
            if device_name:
                result.data['refund_device_name'] = device_name
        elif input == 'cancel':
            result = _common_pay.common_cancel(request['out_trade_no'])

        if result.data['state'] != 'fail':
            history.update(result)
        if not result.data.get('create_time',None):
            history.get_create_time(result)
        self.write(result.to_json())

class history_handler(tornado.web.RequestHandler):
    def post(self):
        request = json.loads(self.request.body.decode("utf-8"))
        from_time = request.get('from_time',int(time.time()) - 432000) # 60*60*24*5 5day
        to_time = request.get('to_time',int(time.time()))
        histories = history.get(from_time,to_time)
        self.write('['+','.join([x.to_json() for x in histories])+']')

if not os.path.exists('logs'):
    os.mkdir('logs')
args = sys.argv
args.append("--log_file_prefix=logs/web.log")
tornado.options.parse_command_line()
app = tornado.web.Application(
    handlers=[
        (r'/',root_handler),
        (r'/api/payment/(\w+)', payment_handler),
        (r'/api/history',history_handler)
    ],
    template_path='template',
    static_path='static',
    debug=True
)
http_server = tornado.httpserver.HTTPServer(app)
http_server.listen(configs.port)
tornado.ioloop.IOLoop.instance().start()
