#!/usr/bin/env python
#-*- coding:utf-8 -*-
import rospy
import math
# from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import PoseArray
import tf
total_count = 0
success_count = 0
sec_start = -1
yaw_list = []        #只统计成功找到pose的yaw的方差
time_list = []
def objective_pose_callback(data):
    global total_count
    global success_count
    global sec_start
    global yaw_list
    global time_list
    total_count += 1
    # if data.pose.position.x != 0.0 and data.pose.position.y != 0.0:
    #这里只统计只有一个pose的yaw的随时间的方差
    if sec_start == -1:
            sec_start = data.header.stamp.secs
    for ipose in data.poses:    #期望只有一个值
        if not math.isnan(ipose.position.x):
            success_count += 1
            quater = [ipose.orientation.x,ipose.orientation.y,ipose.orientation.z,ipose.orientation.w]
            euler = tf.transformations.euler_from_quaternion(quater,axes='sxyz')
            euler = [iv/3.14*180 for iv in euler]
            yaw_list.append(euler[2])
            time_list.append(data.header.stamp.secs-sec_start)
            # print(data.header.stamp.secs-sec_start ,euler)
        if total_count % 20 == 0:
            print "result:(%d/%d)" % (success_count, total_count)
            EX = sum(yaw_list)/len(yaw_list)
            t1 = [(x-EX)**2 for x in yaw_list]
            DX = math.sqrt( sum(t1)/( len(yaw_list)-1 ) )
            print("up to now EX,DX of yaw are: %f,\t%s"%(EX,DX))
        

def listener():
    rospy.init_node("objective_pose_listener")
    rospy.Subscriber("/objective_pose_array", PoseArray, objective_pose_callback)
    rospy.spin()
    

if __name__ == '__main__':
    listener()


