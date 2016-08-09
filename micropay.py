#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A simple python Wechat MicroPay API

Doc: https://pay.weixin.qq.com/wiki/doc/api/micropay.php?chapter=9_10&index=1
'''

__author__ = 'Anthony Fu'

import os
import json
import requests
import hashlib
import string
import time
import re
import datetime
import random
from   common_pay import Commonpay, CommonResult

urls = {
    'micropay' 		: 'https://api.mch.weixin.qq.com/pay/micropay',
    'orderquery' 	: 'https://api.mch.weixin.qq.com/pay/orderquery',
    'reverse' 		: 'https://api.mch.weixin.qq.com/secapi/pay/reverse',
    'refund'  		: 'https://api.mch.weixin.qq.com/secapi/pay/refund',
    'refundquery' 	: 'https://api.mch.weixin.qq.com/pay/refundquery',
    'downloadbill' 	: 'https://api.mch.weixin.qq.com/pay/downloadbill'
}

class Micropay(Commonpay):
    def __init__(self,appid,mch_id,key,cert_path,cert_key_path):
        self.appid = appid
        self.mch_id = mch_id
        self.key = key
        self.cert_path = cert_path
        self.cert_key_path = cert_key_path

    def yuan_to_cent(self, fee_in_yuan):
        return int(float(fee_in_yuan) * 100)

    def get_state(self, raw):
        result_code = raw.get('result_code',None)
        if   result_code == "SUCCESS":
            return "success"
        else:
            return "fail"

    def get_order_state(self, raw):
        state = raw.get('trade_state', None)
        if   state == "SUCCESS":
            return "success"
        elif state == "USERPAYING":
            return "paying"
        elif state == "REFUND":
            return "refund"
        elif state == "CLOSED":
            return "closed"
        else:
            return self.get_state(raw)

    def get_fee_in_yuan(self, raw):
        fee = int(raw.get('total_fee', 0))
        return str(fee / 100)


    def basic_result_parse(self, raw):
        result = CommonResult(method='micropay',
                            out_trade_no=raw.get('out_trade_no',None),
                            state=self.get_state(raw),
                            order_state=self.get_order_state(raw),
                            total_fee=self.get_fee_in_yuan(raw),
                            orginal_fee=self.get_fee_in_yuan(raw),
                            raw = raw)
        if result.data['order_state'] == 'refund':
            raw_refund = self.raw_refundquery(result.data['out_trade_no'])
            result.data['raw']['refund_query'] = raw_refund
            refund_fee = int(raw_refund.get('refund_fee', 0))
            result.data['refund_fee'] = str(refund_fee / 100)
            result.data['total_fee'] = str((int(raw.get('total_fee', 0)) - refund_fee) / 100)
        return result

    def common_pay(self, fee_in_yuan, auth_code, out_trade_no = None, subject = None):
        fee_in_cent = self.yuan_to_cent(fee_in_yuan)
        raw = self.raw_pay(fee_in_cent, auth_code, out_trade_no, subject)
        return self.basic_result_parse(raw).set_create_time()

    def common_query(self, out_trade_no):
        raw = self.raw_query(out_trade_no)
        return self.basic_result_parse(raw)

    def common_refund(self, out_trade_no, refund_fee_in_yuan, total_fee_in_yuan):
        refund_fee_in_cent = self.yuan_to_cent(refund_fee_in_yuan)
        total_fee_in_cent  = self.yuan_to_cent(total_fee_in_yuan)
        raw = self.raw_refund(refund_fee_in_cent, total_fee_in_cent, out_trade_no)
        return self.basic_result_parse(raw)

    def common_cancel(self, out_trade_no):
        raw = self.raw_cancel(out_trade_no)
        return self.basic_result_parse(raw)

    # ----------- Raw ------------------
    @property
    def base_data(self):
        return dict(appid=self.appid,mch_id=self.mch_id)

    def generate_trado_no(self):
        return 'wx' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '0' + str(random.randint(10, 99))

    def generate_refund_no(self):
        return 'wx' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '0' + str(random.randint(10, 99))

    def raw_pay(self, total_fee, auth_code, out_trade_no=None, body=''):
        if out_trade_no is None:
            out_trade_no = self.generate_trado_no()
        data = self.base_data
        data['body']            = body
        data['out_trade_no']    = out_trade_no
        data['total_fee']       = total_fee
        data['auth_code']       = auth_code
        return self._post_request('micropay',data)

    def raw_query(self,out_trade_no=None,transaction_id=None):
        data = self.base_data
        if out_trade_no:        data['out_trade_no'] = out_trade_no
        elif transaction_id:    data['transaction_id'] = transaction_id
        else:
            return {'error':'trade number required'}
        return self._post_request('orderquery', data)


    def raw_cancel(self,out_trade_no=None,transaction_id=None):
        data = self.base_data
        if out_trade_no:        data['out_trade_no'] = out_trade_no
        elif transaction_id:    data['transaction_id'] = transaction_id
        else:
            return {'error':'trade number required'}
        return self._post_request_with_cert('reverse',data)

    def raw_refund(self,refund_fee,total_fee,out_trade_no=None,transaction_id=None,op_user_id=None):
        data = self.base_data
        if out_trade_no:        data['out_trade_no'] = out_trade_no
        elif transaction_id:    data['transaction_id'] = transaction_id
        else:
            return {'error':'trade number required'}

        out_refund_no = self.generate_refund_no()
        data['out_trade_no']    = out_trade_no
        data['total_fee']       = total_fee
        data['refund_fee']      = refund_fee
        data['op_user_id']      = op_user_id or self.mch_id
        data['out_refund_no']   = out_refund_no
        return self._post_request_with_cert('refund',data)

    def raw_refundquery(self,out_trade_no=None,transaction_id=None,out_refund_no=None,refund_id=None):
        data = self.base_data
        if out_trade_no:        data['out_trade_no'] = out_trade_no
        elif transaction_id:    data['transaction_id'] = transaction_id
        elif out_refund_no:     data['out_refund_no'] = out_refund_no
        elif refund_id:         data['refund_id'] = refund_id
        else:
            return {'error':'refund number required'}
        return self._post_request('refundquery', data)

    def _post_request(self, url_key, data, cert = False):
        url = urls[url_key]
        data['nonce_str'] = generate_nonce_str()
        data = self._hash_sign(data)

        if cert:    cert_path = (self.cert_path,self.cert_key_path)
        else:       cert_path = None

        respone = requests.post(url, dict_to_xml(data).encode("utf-8"), cert = cert_path)
        respone_data = xml_to_dict(respone.content.decode())
        return respone_data

    def _post_request_with_cert(self, url_key, data):
        return self._post_request(url_key, data, True)

    def _hash_sign(self,data):
        sign = hashlib.md5(('&'.join(sorted(['{}={}'.format(k, v) for k, v in data.items()])
                   + ['key='+self.key])).encode()).hexdigest().upper()
        data['sign'] = sign
        return data

def generate_nonce_str():
    chars = string.digits + string.ascii_letters
    return ''.join(random.choice(chars) for x in range(32))

def dict_to_xml(dict_data):
    return '<xml>{}</xml>'.format(''.join('<{k}>{v}</{k}>'.format(k = k, v = v)
                                          for k, v in dict_data.items()))

def xml_to_dict(xml_data):
    xml_data = re.sub(r'<xml>|</xml>|<!\[CDATA\[|\]\]>', '', xml_data)  # Remove the CDATA tag in return xml
    pairs = re.findall(r'<(\w+)>(.+)</(\w+)>', xml_data)
    data = {p[0]:p[1] for p in pairs}
    return data
