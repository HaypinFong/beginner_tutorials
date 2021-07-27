#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from __future__ import print_function

import sys
import rospy
from beginner_tutorials.srv import *
# source devel/setup.bash后Shell环境中$PYTHONPATH为
#/home/haypin/catkin_ws/devel/lib/python2.7/dist-packages:/opt/ros/kinetic/lib/python2.7/dist-packages 
#而/home/haypin/catkin_ws/devel/lib/python2.7/dist-packages中:
'''
haypin@ubt:~/catkin_ws/src/beginner_tutorials/srv$ cat AddTwoInts.srv 
int64 a
int64 b
---
int64 sum
haypin@ubt:~/catkin_ws/src/beginner_tutorials/srv$

haypin@ubt:~/catkin_ws/devel/lib/python2.7/dist-packages/beginner_tutorials/srv$ ls
_AddTwoInts.py  __init__.py

haypin@ubt:~/catkin_ws/devel/lib/python2.7/dist-packages/beginner_tutorials/srv$ cat __init__.py
from ._AddTwoInts import *

haypin@ubt:~/catkin_ws/devel/lib/python2.7/dist-packages/beginner_tutorials/srv$ cat _AddTwoInts.py 
	#用户只定义了描述服务的AddTwoInts.srv文件,_AddTwoInts.py文件自动生成
# This Python file uses the following encoding: utf-8
"""autogenerated by genpy from beginner_tutorials/AddTwoIntsRequest.msg. Do not edit."""
import codecs
import sys
python3 = True if sys.hexversion > 0x03000000 else False
import genpy
import struct


class AddTwoIntsRequest(genpy.Message):
  #AddTwoInts服务请求封装在AddTwoIntsRequest类中
  _md5sum = "36d09b846be0b371c5f190354dd3153e"
  _type = "beginner_tutorials/AddTwoIntsRequest"
  _has_header = False  # flag to mark the presence of a Header object
  _full_text = """int64 a
int64 b
"""
  __slots__ = ['a','b']
  _slot_types = ['int64','int64']

  def __init__(self, *args, **kwds):

    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.

    The available fields are:
       a,b

    :param args: complete set of field values, in .msg order
    :param kwds: use keyword arguments corresponding to message field names
    to set specific fields.

    if args or kwds:
      super(AddTwoIntsRequest, self).__init__(*args, **kwds)
      # message fields cannot be None, assign default values for those that are
      if self.a is None:
        self.a = 0
      if self.b is None:
        self.b = 0
    else:
      self.a = 0
      self.b = 0


class AddTwoIntsResponse(genpy.Message):
  #AddTwoInts服务响应封装在AddTwoIntsResponse类中
  _md5sum = "b88405221c77b1878a3cbbfff53428d7"
  _type = "beginner_tutorials/AddTwoIntsResponse"
  _has_header = False  # flag to mark the presence of a Header object
  _full_text = """int64 sum

  __slots__ = ['sum']
  _slot_types = ['int64']

  def __init__(self, *args, **kwds):

    Constructor. Any message fields that are implicitly/explicitly
    set to None will be assigned a default value. The recommend
    use is keyword arguments as this is more robust to future message
    changes.  You cannot mix in-order arguments and keyword arguments.

    The available fields are:
       sum

    :param args: complete set of field values, in .msg order
    :param kwds: use keyword arguments corresponding to message field names
    to set specific fields.

    if args or kwds:
      super(AddTwoIntsResponse, self).__init__(*args, **kwds)
      # message fields cannot be None, assign default values for those that are
      if self.sum is None:
        self.sum = 0
    else:
      self.sum = 0
class AddTwoInts(object):  
  #AddTwoInts服务类型封装在AddTwoInts类中
  #AddTwoInts服务的名字和字段来自于~/catkin_ws/src/beginner_tutorials/srv/AddTwoInts.srv
  _type          = 'beginner_tutorials/AddTwoInts'
  _md5sum = '6a2e34150c00229791cc89ff309fff21'
  _request_class  = AddTwoIntsRequest
  _response_class = AddTwoIntsResponse

#根据服务定义文件AddTwoInts.srv自动生成的封装服务的类为AddTwoInts
#,也自动生成了AddTwoIntsRequest服务响应类
'''


def add_two_ints_client(x, y):
    #客户端不需要调用init_node()初始化进程节点
    rospy.wait_for_service('add_two_ints')
    #让客户端进程在add_two_ints服务可用之前一直阻塞
    try:
        add_two_ints = rospy.ServiceProxy('add_two_ints', AddTwoInts)
	#rospy.ServiceProxy类,服务的名称"add_two_ints",服务的类型AddTwoInts,返回一个实例,
	#还是个可调用对象,调用时传入一个服务请求类AddTwoIntsRequest实例或直接传入字段构造
	#一个服务请求类AddTwoIntsRequest实例,返回服务响应类AddTwoIntsResponse实例
	'''
	|  __init__(self, name, service_class, persistent=False, headers=None)
	|      ctor.
	|      @param name: name of service to call
	|      @type  name: str
	|      @param service_class: auto-generated service class
	|      @type  service_class: Service class
	|      @param persistent: (optional) if True, proxy maintains a persistent
	|      connection to service. While this results in better call
	|      performance, persistent connections are discouraged as they are
	|      less resistent to network issues and service restarts.
	|      @type  persistent: bool
	|      @param headers: (optional) arbitrary headers 
	|      @type  headers: dict
	'''
        resp1 = add_two_ints(x, y)
	#返回服务响应类AddTwoIntsResponse实例
	'''
	|  __call__(self, *args, **kwds)
	|      Callable-style version of the service API. This accepts either a request message instance,
	|      or you can call directly with arguments to create a new request instance. e.g.::
	|      
	|        add_two_ints(AddTwoIntsRequest(1, 2))
	|        add_two_ints(1, 2)
	|        add_two_ints(a=1, b=2)          
	|      
	|      @param args: arguments to remote service
	|      @param kwds: message keyword arguments
	|      @raise ROSSerializationException: If unable to serialize
	|      message. This is usually a type error with one of the fields.
	'''
        return resp1.sum
    except rospy.ServiceException as e:
        print("Service call failed: %s"%e)

def usage():
    return "%s [x y]"%sys.argv[0]   #命令行接收参数

if __name__ == "__main__":
    if len(sys.argv) == 3:    #客户端进程可执行文件add_two_ints_client.py调用时传入的参数
        x = int(sys.argv[1])
        y = int(sys.argv[2])
    else:
        print(usage())	      #打印提示信息,退出客户端进程
        sys.exit(1)
    print("Requesting %s+%s"%(x, y))
    print("%s + %s = %s"%(x, y, add_two_ints_client(x, y)))