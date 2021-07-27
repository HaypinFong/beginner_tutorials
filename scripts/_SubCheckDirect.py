#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import rospy
import re
from beginner_tutorials.msg import Str  #为自定义消息Str.msg自动生成的类型,类名Str,字段名str

def callback(Strobj):
    rexEle = re.compile("check")
    if rexEle.search(Strobj.str):
        rospy.loginfo(rospy.get_caller_id()+" got know check, will take act")
    else:
        rospy.loginfo(rospy.get_caller_id()+" will do nothing")

def Subscriber():
    rospy.init_node('nodeD',anonymous=True)
    rospy.Subscriber('/nodeA/check',Str,callback)
    rospy.spin()

if __name__=="__main__":
    Subscriber()
