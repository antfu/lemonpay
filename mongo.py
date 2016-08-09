#/usr/bin/python
# coding: utf-8

__version__ = (0,0,0,1)

from bson.objectid import ObjectId
from bson.dbref import DBRef
from datetime import datetime
import random
import json
import pymongo
import pymongo.database
import pymongo.collection

DBRef.dereference = lambda self, database: database.dereference(self)

class Database:
    def __init__(self,db):
        self.db = db
        self.collections = {}

    def __getitem__(self, collection_name):
        if not collection_name in self.collections.keys():
            self.collections[collection_name] = Collection(self,self.db[collection_name])
        return self.collections[collection_name]

    def dereference(self, data, **kwargs):
        return Document(self[data.collection], self.db.deference(data))


class Collection:
    def __init__(self,database, collection):
        self.database = database
        self.collection = collection
        self.name = self.collection.name

    def __getitem__(self, item):
        return self.find_by_id(item)

    def _gen_doc(self, data):
        if data is None:
            return None
        return Document(self, data)

    def find_by_id(self, obj_id):
        return self.find_one(dict(_id = ObjectId(obj_id)))

    def find_one(self, condition = None):
        return self._gen_doc(self.collection.find_one(condition))

    def find(self, condition = None, **kwargs):
        if kwargs:
            cursor = self.collection.find(**kwargs)
        else:
            cursor = self.collection.find(condition)
        return [self._gen_doc(x) for x in cursor]

    def find_lazy(self, condition = None):
        cursor = self.collection.find(condition)
        for x in cursor:
            yield self._gen_doc(x)

    def insert(self, data, **kwargs):
        if data is None and not kwargs is None:
            data = kwargs
        if not data:
            return
        if '_id' not in data.keys():
            data['_id'] = ObjectId(''.join(random.choice('1234567890abcdef') for x in range(24)))
        return self.collection.insert_one(data)

    def create_ref(self, id):
        objectid = ObjectId(str(id))
        if self.find_one({'_id': objectid}):
            return DBRef(self.name, objectid)
        else:
            return None


class Document(dict):
    def __init__(self, collection, dic):
        super().__init__()
        self.collection = collection
        self._init(dic)

    def __setitem__(self, key, value):
        self.update({key: value})

    def __delitem__(self, key):
        self.unset(key)

    def _init(self, dic):
        self.inited = False
        self.clear()
        for k, v in dic.items():
            super().__setitem__(k, v)

    def _to_dict_inner(self, d):
        result = {}
        for k, v in d.items():
            if isinstance(v, DBRef):
                result[k] = self.collection.database.dereference(v).to_dict()
            elif isinstance(v, dict):
                result[k] = self._to_dict_inner(v)
            elif isinstance(v, ObjectId):
                result[k] = str(v)
            elif isinstance(v, datetime):
                result[k] = datetime_to_stamp(v)
            else:
                result[k] = v
        return result

    def _update_to_db(self, *args, **kwargs):
        self.collection.collection.update_one({'_id': self.get_id()}, *args,
                                              **kwargs)
        self.refresh()

    def get_id(self):
        return self['_id']

    def get_id_str(self):
        return str(self['_id'])

    def get_ref(self, key):
        if isinstance(self.get(key, None), DBRef):
            return self[key].dereference(self.collection.database)

    def update(self, data = None, **kwargs):
        if data is None and not kwargs is None:
            data = kwargs
        if not data:
            return
        self._update_to_db({'$set': data})

    def unset(self, keylist):
        if not keylist:
            return
        if isinstance(keylist, str):
            keylist = [keylist]
        self._update_to_db({'$unset': {k: None for k in keylist}})

    def refresh(self):
        self._init(self.collection.find_by_id(self.get_id()))

    def to_dict(self):
        return self._to_dict_inner(self)

    def to_json(self, **kwargs):
        return json.dumps(self.to_dict(), **kwargs)

    def ref(self):
        return DBRef(self.collection.name, self.get_id())


def connect(mongodb_url = None, database_name = 'test'):
    client = pymongo.MongoClient(mongodb_url)
    return Database(client[database_name])


def datetime_to_stamp(dt):
    if not isinstance(dt, datetime):
        raise TypeError('Unexpected type {}'.format(type(dt)))
    return int(dt.timestamp() * 1e3)


def stamp_to_datetime(ts):
    return datetime.fromtimestamp(ts / 1e3)


if __name__ == '__main__':
    mongo = Database(None, 'coming')
