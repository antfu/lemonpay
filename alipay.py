#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
A simple python Alipay Barcode API
'''

__author__ = 'Anthony Fu'

import OpenSSL
import requests
import datetime
import base64
import json
import random
import logging
from   common_pay import Commonpay, CommonResult

class Alipay(Commonpay):
    def __init__(self, app_id, cert_path, default_subject = ''):
        self.appid = app_id
        self.cert = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, open(cert_path).read())
        self.default_subject = default_subject
        self.default_request = {
            'charset': 'utf-8',
            'sign_type': 'RSA',
            'version': '1.0',
            'app_id': app_id
        }
        self.default_bizcontent = {
            'scene': 'bar_code',
            'timeout_express': '10m',
            'subject': default_subject
        }

    def get_state(self, raw):
        code = raw.get('code',None)
        if code.startswith("1"):
            return "success"
        else:
            return "fail"

    def get_order_state(self, raw):
        state = raw.get('trade_status')
        if   state == "WAIT_BUYER_PAY":
            return "paying"
        elif state == "TRADE_SUCCESS":
            return "success"
        elif state == "TRADE_CLOSED":
            return "closed"
        elif raw.get('code',None) == "10003":
            return "paying"
        else:
            return self.get_state(raw)

    def get_total_fee(self, raw):
        return raw.get('total_amount','0')

    def basic_result_parse(self, raw):
        result = CommonResult(method='alipay',
                            out_trade_no=raw.get('out_trade_no',None),
                            state=self.get_state(raw),
                            order_state=self.get_order_state(raw),
                            total_fee=raw.get('invoice_amount',None),
                            orginal_fee=raw.get('total_amount',raw.get('invoice_amount',None)),
                            raw = raw)
        if result.data['order_state'] == 'refund':
            refund_bills = raw.get('fund_bill_list',[])
            refund_fee = 0
            for b in refund_bills:
                refund_fee += float(b.get('amount',0))
            result.data['refund_fee'] = str(refund_fee)
        if result.data['order_state'] == 'closed':
            result.data['refund_fee'] = result.data['orginal_fee']
        return result

    def common_pay(self, fee_in_yuan, auth_code, out_trade_no = None, subject = None):
        raw = self.raw_pay(fee_in_yuan, auth_code, out_trade_no, subject)
        return self.basic_result_parse(raw).set_create_time()

    def common_query(self, out_trade_no):
        raw = self.raw_query(out_trade_no)
        return self.basic_result_parse(raw)

    def common_refund(self, out_trade_no, refund_fee_in_yuan, total_fee_in_yuan = None):
        raw = self.raw_refund_out(out_trade_no, refund_fee_in_yuan)
        result = self.basic_result_parse(raw)
        if result.data['order_state'] == 'success':
            result.data['order_state'] = 'refund'
            result.data['refund_fee'] = raw.get('refund_fee',None)
        return result
        #TODO

    def common_cancel(self, out_trade_no):
        raw = self.raw_cancel(out_trade_no)
        return self.basic_result_parse(raw)

    # ----------- Raw ------------------
    def raw_pay(self, total_amount, auth_code, out_trade_no = None, subject = None, **kwargs):
        if not out_trade_no:
            out_trade_no = self._gen_trade_no()
        content = dict(self.default_bizcontent)
        content.update({
            'out_trade_no': str(out_trade_no),
            'total_amount': str(total_amount),
            'auth_code': str(auth_code),
            'subject': str(subject or self.default_subject)
        })
        content.update(kwargs)
        return self._send('alipay.trade.pay',content)['alipay_trade_pay_response']

    def raw_query(self, out_trade_no, **kwargs):
        content = dict(out_trade_no = str(out_trade_no))
        content.update(kwargs)
        return self._send('alipay.trade.query',content)['alipay_trade_query_response']

    def raw_refund(self, trade_no, refund_amount, **kwargs):
        content = {
            'trade_no': str(trade_no),
            'refund_amount': str(refund_amount)
        }
        content.update(kwargs)
        return self._send('alipay.trade.refund',content)['alipay_trade_refund_response']

    def raw_cancel(self, out_trade_no, **kwargs):
        content = dict(out_trade_no = str(out_trade_no))
        content.update(kwargs)
        return self._send('alipay.trade.cancel',content)['alipay_trade_cancel_response']

    def raw_refund_out(self, out_trade_no, refund_amount, **kwargs):
        r = self.raw_query(out_trade_no)
        return self.raw_refund(r['trade_no'],refund_amount, **kwargs)

    def _join_dict(self,dic):
        return '&'.join('{}={}'.format(k, v) for k, v in sorted(dic.items()))

    def _sign(self, dic):
        data = self._join_dict(dic).encode('utf-8')
        signature = OpenSSL.crypto.sign(self.cert, data, 'sha1')
        return base64.standard_b64encode(signature).decode()

    def _gen_request(self, method, **kw):
        kw.update(self.default_request)
        kw.update({'method': method, 'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        kw.update({'sign': self._sign(kw)})
        return kw

    def _post(self, data):
        return requests.post('https://openapi.alipay.com/gateway.do', data = data)

    def _send(self, method, content):
        r = self._post(self._gen_request(method, biz_content = json.dumps(content)))
        return json.loads(r.text)

    def _gen_trade_no(self, prefix='zfb'):
        return prefix + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '0' + str(random.randint(10, 99))
