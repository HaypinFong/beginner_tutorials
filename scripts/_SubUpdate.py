#!/usr/bin/env python2
#-*- coding:UTF-8 -*-
import rospy
import re
from beginner_tutorials.msg import Str

def callback(Strobj):
    rexEle = re.compile("tacticChanged")
    logstr = rospy.get_caller_id()
    if rexEle.search(Strobj.str):
        logstr += "got know tacticChanged, will tack act"
    else:
        logstr += "will do nothing"
    rospy.loginfo(logstr)

if __name__ == '__main__':
    rospy.init_node('nodeC',anonymous=False)
    rospy.Subscriber('/nodeB/updateTactic',Str,callback)
    rospy.spin()