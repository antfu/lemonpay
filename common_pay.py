# -*- coding: utf-8 -*-
# @Author: Anthony
# @Date:   2016-04-08 18:42:53
# @Last Modified by:   Anthony
# @Last Modified time: 2016-04-08 19:03:40

import json
import time

class Commonpay:
    def common_pay(self, fee_in_yuan, auth_code, out_trade_no = None, subject = None):
        pass

    def common_query(self, out_trade_no):
        pass

    def common_refund(self, out_trade_no, refund_fee_in_yuan, total_fee_in_yuan):
        pass

    def common_cancel(self, out_trade_no):
        pass

    def common_refundquery(self, out_trade_no):
        pass

class CommonResult:
    def __init__(self, method, out_trade_no, state, order_state, raw, **addtion):
        self.data = {}
        self.data['out_trade_no'] = out_trade_no
        self.data['method'] = method
        self.data['state'] = state
        self.data['order_state'] = order_state
        self.data['raw'] = raw
        self.data['time'] = int(time.time())
        self.data.update(addtion)

    def set_create_time(self):
        self.data['create_time'] = int(time.time())
        return self

    def to_json(self):
        return json.dumps(self.data)
