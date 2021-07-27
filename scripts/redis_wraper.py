#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import redis
import json
class redis_wraper:
    #在类内维护一个连接供同一rospy进程内全局使用，避免每次建立、释放redis-cli连接的开销，从一个连接池
    #加上decode_response=True，写入的键值中的value为str类型，不加这个参数写入的是字节数组类型
    #连接池除了限定从连接池返回的连接数量外，起到统一在连接池内指定连接参数的作用。
    pool = redis.ConnectionPool(host='localhost',port=6378,decode_responses=True)
    redis_cli = redis.Redis(connection_pool=pool,encoding='utf-8')
    def setkv(self,key,map_list_tuple):
        self.redis_cli.set(key,json.dumps(map_list_tuple))
    def getv(self,key):
        j = self.redis_cli.get(key)
        map_list_tuple = json.loads(j)
        return map_list_tuple
    def __del__(self):
        self.redis_cli.close()
    # def deletek(self,key):
    #     return self.redis_cli.delete(key)
    # def exists(slef,keys):
    #     return self.redis_cli.exists(keys)
    #其他函数如无必要可以直接self.redis_cli.func()执行，
