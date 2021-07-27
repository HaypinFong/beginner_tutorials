#!/usr/bin/env python
# -*- coding: UTF-8 -*-


## Simple talker demo that listens to std_msgs/Strings published 
## to the 'chatter' topic

import rospy
from std_msgs.msg import String
from redis_wraper import redis_wraper

redis_cli = redis_wraper()
def callback(data):
    rospy.loginfo(rospy.get_caller_id() + 'I heard %s', data.data)
    rospy.loginfo("listener.py get 'name' form redis: %s"%redis_cli.getv("param1"))

def listener():

    # In ROS, nodes are uniquely named. If two nodes with the same
    # name are launched, the previous one is kicked off. The
    # anonymous=True flag means that rospy will choose a unique
    # name for our 'listener' node so that multiple listeners can
    # run simultaneously.
    #在ROS中,节点是惟一命名的,如果有相同名字的两个节点被启动,前面一个节点
    #将被踢开.anonymous=True从而可以有多个listener.py的节点进程一起运行
    rospy.init_node('listener', anonymous=False)
    rospy.loginfo("listner started")

    rospy.Subscriber('/talker/chatter', String, callback)
    #声明当前订阅者节点订阅chatter话题,类型是std_msgs.msgs.String.当接收到
    #新消息时,callback函数被调用,消息作为第一个参数

    # spin() simply keeps python from exiting until this node is stopped
    rospy.spin()
    #rospy.spin()只是不让你的节点退出,直到节点被明确关闭.与roscpp不同,
    #rospy.spin()不影响订阅者回调函数,因为它们有自己的线程

if __name__ == '__main__':
    listener()
