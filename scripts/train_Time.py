import rospy
if __name__ == "__main__":
    rospy.init_node("time")
    time_now = rospy.get_time()
    time_now = rospy.Time(time_now)
    print(type(time_now))
    print(time_now.to_sec())
    print(time_now.to_nsec())