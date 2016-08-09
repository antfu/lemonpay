#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-

import json
import mongo
import time
import datetime

class History:
    def __init__(self,name):
        self.db = mongo.connect(None, 'lemonpay')
        self.collection = self.db[name]

    def append(self,result):
        self.collection.insert(dict(result.data))

    def update(self,result):
        orginal = self.collection.find_one(dict(out_trade_no=result.data['out_trade_no']))
        if not orginal:
            self.append(result)
        else:
            for k,v in result.data.items():
                orginal[k] = v

    def get_create_time(self,result):
        orginal = self.collection.find_one(dict(out_trade_no=result.data['out_trade_no']))
        if not orginal:
            return
        try:
            test = orginal['create_time']
        except KeyError:
            orginal['create_time'] = time.time()
        result.data['create_time'] = orginal['create_time']

    def get_day(self,day=None):
        if day is None:
            date = datetime.date.today()
        elif isinstance(day,datetime.date):
            date = day
        elif isinstance(day,datetime.datetime):
            date = day.date()
        elif isinstance(day,int):
            date = datetime.date.today() + datetime.timedelta(day)
        elif isinstance(day,tuple):
            date = datetime.date(day[0],day[1],day[2])
        timestamp = int(datetime.datetime(date.year,date.month,date.day).timestamp())
        return self.get(timestamp,timestamp+86400)

    def get(self,from_time,to_time):
        return sorted(self.collection.find({'create_time':{'$gt':from_time,'$lt':to_time}}),key=lambda x: x['create_time'])
