#!/usr/bin/env python
import rospy
import math
from geometry_msgs.msg import PoseStamped
total_count = 0
success_count = 0

def objective_pose_callback(data):
    global total_count
    global success_count
    total_count += 1
    # if data.pose.position.x != 0.0 and data.pose.position.y != 0.0:
    if not math.isnan(data.pose.position.x):
        success_count += 1
    if total_count % 20 == 0:
        print "result:(%d/%d)" % (success_count, total_count)

def listener():
    rospy.init_node("objective_pose_listener")
    rospy.Subscriber("/objective_pose", PoseStamped, objective_pose_callback)
    rospy.spin()
    

if __name__ == '__main__':
    listener()


