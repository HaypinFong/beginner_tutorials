#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
import rospy
from beginner_tutorials.msg import Str

if __name__ == '__main__':
    try:    #嘿嘿
        rospy.init_node('nodeA',anonymous=False)
        pub = rospy.Publisher('~check',Str,queue_size=10)
        rate = rospy.Rate(0.5)
        pubstr = rospy.get_caller_id()+" pub 'check'"
        while not rospy.is_shutdown():
            rospy.loginfo(pubstr)
            pub.publish(pubstr)
            rate.sleep()
    except rospy.ROSInterruptException:
        exceptstr = rospy.get_caller_id()+" check topic exception!"
        rospy.loginfo(excepstr)