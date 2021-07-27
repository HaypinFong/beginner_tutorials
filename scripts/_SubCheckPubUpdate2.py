#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
import rospy    #导入其他节点，python节点自身就是一个包，
# from beginner_tutorials.msg import String	#自定义消息类型
from std_msgs.msg import String

def callback(Strobj):
    try:
        pub = rospy.Publisher('~topicB',String)   #定义发布者
        strmsg = rospy.get_caller_id()+" sub topicA then pub topicB"
        rospy.loginfo(strmsg) #往rospy节点记录信息
        #rospy.get_caller_id()返回当前节点的完整解析的节点名
        pub.publish(strmsg) #发布话题,已经在rospy.spin()订阅循环中了
        #，不用再加循环rospy.Rate().sleep()了
    except rospy.ROSInterruptException:
        pass

if __name__=="__main__":
    '''yamlpath、launchpath存储在参数服务器中由roscore或其他先启节点
    以话题的方式发布到当前节点？
    '''
    rospy.init_node('nodeB',anonymous=False)
    rospy.Subscriber('/nodeA/topicA',String,callback)   #定义订阅者
    rospy.spin()