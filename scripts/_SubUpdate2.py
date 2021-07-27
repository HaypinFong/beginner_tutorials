#!/usr/bin/env python2
#-*- coding:UTF-8 -*-
import rospy
# from beginner_tutorials.msg import String
from std_msgs.msg import String

def callback(Strobj):
    logstr = rospy.get_caller_id()+" sub topicB"
    rospy.loginfo(logstr)

if __name__ == '__main__':
    rospy.init_node('nodeC',anonymous=False)
    rospy.Subscriber('/nodeB/topicB',String,callback)
    rospy.spin()