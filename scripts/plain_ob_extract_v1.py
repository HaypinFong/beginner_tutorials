#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import rospy
import numpy
import math
import time
import threading
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool
import numpy as np
from scipy import optimize
import copy
import random
from geometry_msgs.msg import PoseStamped, TransformStamped, PoseArray, Pose
from tf.transformations import quaternion_matrix, translation_matrix
import tf
import angles

# import matplotlib.pyplot as plt     #for debug
DEBUG = True


class segment():
    def __init__(self, s, e):
        self.s = s
        self.e = e
        self.length = 0
        self.cx = None
        self.cy = None

    def centroid(self, xs, ys):
        self.cx = np.array(xs[self.s:self.e+1]).mean()
        self.cy = np.array(ys[self.s:self.e+1]).mean()

    def rectify(self, xs, ys, yaw):     #片段
        linex = [math.cos(yaw), math.sin(yaw)]
        liney = [math.cos(yaw + math.pi/2), math.sin(yaw + math.pi/2)]
        #use the first point as a base point
        base = [xs[self.s], ys[self.s]] #片段的起点
        coords = [[0.,0., self.s]]
        for i in range(self.s+1, self.e+1):             #片段内第二个点到最后扩充一个点
            pair = [xs[i] - base[0], ys[i] - base[1]]   #每个点到片段起点
            dx = linex[0]*pair[0] + linex[1]*pair[1]
            dy = liney[0]*pair[0] + liney[1]*pair[1]
            coords.append([dx, dy, i])
        coords = np.array(coords)
        self.flen = coords[:,1].max() - coords[:,1].min()       #当前片段起点
        self.thickness = coords[:,0].max() - coords[:,0].min()
        csed = coords[coords[:,0].argsort()]
        # calculate center
        mx = csed[:csed.shape[0]*2/3, 0].mean()
        my = self.flen/2 + coords[:,1].min()
        self.fcx = base[0] + my*liney[0] + mx * linex[0]        #当前片段的中心
        self.fcy = base[1] + my*liney[1] + mx * linex[1]


class ExtractObjectivepose:
    def __init__(self):
        self.enabled = False 
        self.tf_l2b = None
        self.tf_listener = tf.TransformListener()
        #TransformListner<——TransformerRos<——Transformer
        #TransformListner是tf.TransformerROS的订阅"/tf"消息topic子类，并对每个输入的转换消息调用
        # tf.Transformer.setTransform()。这种方式下一个TransformerListner对象自动对所有当前转换
        #保持最新。
        # self.laser_topic = rospy.get_param("~laser_topic", "/rear_laser_test/scan_original") 
        scan_topic = rospy.get_param("~scan_topic","/scan")
        self.laser_topic = scan_topic
        rospy.loginfo("Got scan_topic :%s "%(scan_topic))
        self.intensity_thr = rospy.get_param("~intensity_thr", 50)     #230
        self.laser_topic_pub = rospy.get_param("~laser_topic_pub", self.laser_topic + "_ev")

        self.board_adjacent_dis_min = rospy.get_param("~ob_extract/board/adjacent_dis_min",0.1)
        self.board_len_min = rospy.get_param("~ob_extract/board/len/min",0.5)
        self.board_len_max = rospy.get_param("~ob_extract/board/len/max",0.6)
        self.board_interval_min = rospy.get_param("~ob_extract/board/interval_min",0.03)
        self.board_mid_len_max = rospy.get_param("~ob_extract/board/mid_len_max",0.05)
        self.board_LR_len_min = rospy.get_param("~ob_extract/board/LR_len/Min",0.15)
        self.board_LR_len_max = rospy.get_param("~ob_extract/board/LR_len/Max",0.25)
        self.board_LR_len_total_min = rospy.get_param("~ob_extract/board/LR_len/total_min",0.35)


        #pub/subs
        self.laser_pub = rospy.Publisher(self.laser_topic_pub, LaserScan, queue_size=10)
        self.pub_pt_start = rospy.Publisher("/test_pt_start",PoseStamped,queue_size=20)            #调试，同一时刻只维持、显示最多4个可能片段头尾点
        self.pub_pt_end = rospy.Publisher("/test_pt_end",PoseStamped,queue_size=20)                #调试
        self.pub_pt_mid = rospy.Publisher("/test_pt_mid",PoseStamped,queue_size=20)

        self.ob_pub = rospy.Publisher("/objective_pose_array", PoseArray, queue_size = 15)  #发布pose的数组?
        rospy.Subscriber(self.laser_topic, LaserScan, self.scan_callback, queue_size=1)
        # rospy.Subscriber("/plain_laser_feature_capture", Bool, self.open_callback)        #/laser_feature_capture
        rospy.Subscriber("/laser_feature_capture", Bool, self.open_callback)

    def open_callback(self, data):
        if self.enabled != data.data:
            self.enabled = data.data
            rospy.loginfo("plain OB detection switched %s" % ( "on" if data.data else "off"))

    # ax + by + c = 0
    def linefit(self, x , y):
        reverse = False
        th = math.atan2(y[-1]-y[0], x[-1]-x[0])
        if abs(th - math.pi/2) < math.pi/6:
            reverse = True
            x,y = y,x
        N = float(len(x))
        sx,sy,sxx,syy,sxy=0,0,0,0,0
        x,y = np.array(x), np.array(y)
        sx = x.sum()
        sy = y.sum()
        sxx = (x*x).sum()
        syy = (y*y).sum()
        sxy = (x*y).sum()
        a = (sy*sx/N -sxy)/( sx*sx/N -sxx)
        b = (sy - a*sx)/N
        #r = abs(sy*sx/N-sxy)/math.sqrt((sxx-sx*sx/N)*(syy-sy*sy/N))
        if reverse:
            return -1.0, a, b
        else:
            return a, -1.0, b

    def optimize_fit(self, XX, YY, z):
        def huber_loss(res, delta):
            return (res<delta)*res**2/2 + (res>delta)*delta*(res-delta/2)
        def total_huber_loss(K, x=np.array(XX), y=np.array(YY), delta=0.02):
            return huber_loss(abs(K[0]*x + K[1]*y + K[2]) / np.sqrt(K[0]**2 + K[1]**2), delta).sum()
        z1 = optimize.fmin(total_huber_loss, z, disp=False)
        return math.atan2(z1[1], z1[0])

    def scan_callback(self, data):  #LaserScan
        print("---")
        if self.tf_l2b == None:     #只进行一次转换关系的计算
            try:
                rt = self.tf_listener.getLatestCommonTime("/base_link", data.header.frame_id)
                #tf.Transformer能在两个给定帧之间计算转换的最近时间，返回rospy.Time，计算/base_link与/rear_laser当前最近的共同时间
                # ，就是当前最近的两两坐标帧，可用来转换当前LaserScan帧激光点到base_link
                (trans,rot) = self.tf_listener.lookupTransform('base_link', data.header.frame_id, rt)   
                #激光帧在base_link帧中的坐标trans、转角rot，最近时刻
                #返回rt时刻从LaserScan帧到base_link帧的转换(translation(x,y,z),quaternion(x,y,z,w))，一组值
            except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException):
                #http://docs.ros.org/en/kinetic/api/tf/html/python/tf_python.html，所有的异常类型
                print("tf.***Exception!\n")
                return

            self.tf_l2b = tf.TransformerROS(True, rospy.Duration(10.0))     #转换lasertobase_link
            #TransformListner<——TransformerRos<——Transformer
            #tf.TransformerROS类拓展tf.Transformer基类，增加了处理ROS消息的方法
            #tf.Transformer类，interpolating——是否篡改转换。cache_time——tf应该保留多久之前的转换信息.
            #是tf的核心，它维护转换的一个时变图形(tf树?)，允许同步的图形修改和查询
            m = TransformStamped()
            m.header.frame_id = 'base_link'
            m.child_frame_id = data.header.frame_id     #激光帧相对于base_link帧，rear_laser
            m.transform.translation.x = trans[0]        #trans现在是LaserScan帧相对于base_link
            m.transform.translation.y = trans[1]
            m.transform.translation.z = trans[2]
            m.transform.rotation.x = rot[0]
            m.transform.rotation.y = rot[1]
            m.transform.rotation.z = rot[2]
            m.transform.rotation.w = rot[3]
            self.tf_l2b.setTransform(m)
            '''
            tf.Transformer.setTransform(transform,authority="")
            参数：。transform对象
                 。给于这个转换的权限的字符串
            增加一个新的转换到Transformer树。transform实例，就是一个TransformStamped实例
            '''
            print self.tf_l2b.lookupTransform('base_link', data.header.frame_id, rospy.Time(0))     #从最近开始转换  
            #上面rt时刻的转换结果(trans,rot)与这里rospy.Time(0)最近时刻的转换结果相同，rospy.Time(0)表示最近共同时间的转换
            self.tf_listener = None             #释放tf.TransformListener()
        if not self.enabled:
            rospy.loginfo("topic /laser_feature_capture not pub True, ob_extract skipped!")
            return

        # forward
        msg = copy.deepcopy(data)
        msg.ranges = list(data.ranges)      #构造列表
        angle = data.angle_min
        xs, ys, rs = [], [], []
        xs_debug, ys_debug = [], []
        for i, r in enumerate(data.ranges):
            if math.isinf(r) or math.isnan(r) or data.intensities[i] < self.intensity_thr:  #不行的点
                r = 0
            if r > 0:
                xs.append(r*math.cos(angle))    #xs[]坐标列表只收集距离有效、强度足够的点，坐标当然是准的
                ys.append(r*math.sin(angle))    #激光帧相对于laser的坐标 列表
                rs.append(i)                    #对应帧中点下标
            msg.ranges[i] = r                   #不行的点将距离置零，正常的点距离不变
            xs_debug.append(r*math.cos(angle))  #调试用
            ys_debug.append(r*math.sin(angle))  #调试用
            angle += data.angle_increment
        self.laser_pub.publish(msg)             #self.laser_topic + "_ev"，处理了无用点后的当前帧的LaserScan

        # if DEBUG:
            # fig,axes = plt.subplots(nrows=2,ncols=1)
            # axes[0,0].set(title="whole pts")
            # axes[1,0].set(title="valid pts")
            # axes.flat[0].set(xtickes=xs_debug,yticks=ys_debug)
            # axes.flat[1].set(xtickes=xs,yticks=ys)

            # plt.scatter(xs,ys)
            # plt.xlabel("X")
            # plt.ylabel("Y")
            # plt.title("X-Y of valid pts")
            # plt.savefig(r"/home/haypin/catkin_ws/src/beginner_tutorials/pics/laser_valid_pts.jpg",dpi=520)

        ob = PoseArray()
        ob.header = data.header                 #目标pose数组的标头，就是LaserScan的标头
        ob.header.frame_id = "base_link"        #将是相对于base_link的，而不是相对于Laser的
        # print("len(xs) is %d"%(len(xs)))        #Debug
        if len(xs) > 20:
            segs = []
            pre_i, s = 0, 0
            for i in range(len(xs)):
                if math.hypot(xs[i] - xs[pre_i], ys[i] - ys[pre_i]) > self.board_adjacent_dis_min:      #参数2，相邻反光条板子间距
                    if i - s > 2:   #首先要前后前段之间空当距离大于0.1m，然后需要一片段上点数多于2个，激光发出频率一定的话岂不是取决于照射到的物体的角度、距离激光的远近，频率很快时可以忽略角度影响，密布
                        segs.append(segment(s, pre_i))  #segs存储点集片段首尾下标，前后片段之间相邻两点距离要大于0.1，且当前片段内要有三个以上点，
                    s = i                               #开始分段
                if i == len(xs) - 1 and i - s > 2:      #已经遍历到最后一个点，存储最后一段
                    segs.append(segment(s, i))
                pre_i = i

            backboards = []
            for seg in segs:            
                seg.length = math.hypot(xs[seg.s] - xs[seg.e], ys[seg.s] - ys[seg.e])   #片段长度
                print(seg.s, seg.e, seg.length)
                # if DEBUG:
                #     pt_start = PoseStamped()                       #调试
                #     pt_start.header.frame_id = msg.header.frame_id
                #     pt_start.pose.position.x = xs[seg.s]
                #     pt_start.pose.position.y = ys[seg.s]
                #     yaw_start = math.atan2(ys[seg.s],xs[seg.s])
                #     pt_start.pose.orientation.w = math.cos(yaw_start/2)
                #     pt_start.pose.orientation.z = math.sin(yaw_start/2)
                #     self.pub_pt_start.publish(pt_start)

                #     pt_end = PoseStamped()                         #调试
                #     pt_end.header.frame_id = msg.header.frame_id
                #     pt_end.pose.position.x = xs[seg.e]
                #     pt_end.pose.position.y = ys[seg.e]
                #     yaw_end = math.atan2(ys[seg.e],xs[seg.e])
                #     pt_end.pose.orientation.w = math.cos(yaw_end/2)
                #     pt_end.pose.orientation.z = math.sin(yaw_end/2)
                #     self.pub_pt_end.publish(pt_end)
                #     #--------------------------------------
                if seg.length > self.board_len_min and seg.length < self.board_len_max: #参数3，反光条板子总长区间
                    seg.centroid(xs, ys)        #计算seg片段的中心(cx,cy)
                    backboards.append(seg)      #认为该片段可能是在板子上的片段
            if DEBUG:
                param_ob_extract = rospy.get_param("~ob_extract")  #~替代/node_name/，不用再加/
                # print(type(param_ob_extract))             #dict
                # print(param_ob_extract)
                # print(self.intensity_thr)
            print("-------------->", len(segs), len(backboards))    #10、9个片段里有2个片段可能在板子上

            for board in backboards:
                
                dist = math.hypot(board.cx, board.cy)   #板子中点在LaserScan坐标系中距离原点的距离
                # too far away
                if dist > 1.5:
                    rospy.loginfo("dist: %s, too far away!"%(dist))
                    continue
                if DEBUG:
                    pt_start = PoseStamped()                       #调试
                    pt_start.header.frame_id = msg.header.frame_id
                    pt_start.pose.position.x = xs[board.s]
                    pt_start.pose.position.y = ys[board.s]
                    yaw_start = math.atan2(ys[board.s],xs[board.s])
                    pt_start.pose.orientation.w = math.cos(yaw_start/2)
                    pt_start.pose.orientation.z = math.sin(yaw_start/2)
                    self.pub_pt_start.publish(pt_start)

                    pt_end = PoseStamped()                         #调试
                    pt_end.header.frame_id = msg.header.frame_id
                    pt_end.pose.position.x = xs[board.e]
                    pt_end.pose.position.y = ys[board.e]
                    yaw_end = math.atan2(ys[board.e],xs[board.e])
                    pt_end.pose.orientation.w = math.cos(yaw_end/2)
                    pt_end.pose.orientation.z = math.sin(yaw_end/2)
                    self.pub_pt_end.publish(pt_end)
                    #--------------------------------------
                XX, YY = [], []
                XX.extend(xs[board.s+2 : board.e-1])
                YY.extend(ys[board.s+2 : board.e-1])
                #print(XX, YY)
                z1 = self.linefit(XX, YY)
                yaw = self.optimize_fit(XX, YY, z1)         #板子拟合直线的角度，LaserScan坐标系
                th_b2l = math.atan2(board.cy, board.cx)     #板子中点到LaserScan的角度，LaserScan坐标系，borad2laser
                if abs(angles.shortest_angular_distance(th_b2l, yaw)) > math.pi/2:  #???
                    yaw = yaw + math.pi
                print(len(xs), yaw)     #xs[]坐标列表只收集距离有效、强度有效的点
                
                # expect 3 sub-segments
                segs = []
                pre_i, s = board.s, board.s
                line = [math.cos(yaw + math.pi/2), math.sin(yaw + math.pi/2)]   #板子切向cos,sin
                for i in range(board.s, board.e+1):
                    pair = [xs[i] - xs[pre_i], ys[i] - ys[pre_i]]
                    dist = math.fabs(line[0]*pair[0] + line[1]*pair[1])     #板子中相邻两点距离在板子切向上的映射距离(减少距离的误差)
                    if dist > self.board_interval_min:                      #参数4，反光条板子上空当长度阈值下限
                        if i - s > 2:
                            segs.append(segment(s, pre_i))  #前后片段之间相邻两点距离大于0.016且当前片段内要有3个以上点
                            if DEBUG:
                                pt_mid = PoseStamped()                         #调试
                                pt_mid.header.frame_id = msg.header.frame_id
                                pt_mid.pose.position.x = xs[pre_i]
                                pt_mid.pose.position.y = ys[pre_i]
                                yaw_end = math.atan2(ys[pre_i],xs[pre_i])
                                pt_mid.pose.orientation.w = math.cos(yaw_end/2)
                                pt_mid.pose.orientation.z = math.sin(yaw_end/2)
                                self.pub_pt_mid.publish(pt_mid)
                        # if i-s > 2: 
                        #     if i-s ==1:
                        #         segs.append(segment(s,s))
                        #     else:
                        #         segs.append(segment(s,i))
                        s = i   #更新片段起始点下标s
                    if i == board.e and s < pre_i:          #板子上最后一部分也要存一个片段，并检查s<pre_i，i不要了?
                        segs.append(segment(s, pre_i))
                    pre_i = i

                if len(segs) != 3:
                    print("len(segs) is: %d"%(len(segs)))
                    continue

                for seg in segs:
                    seg.length = math.hypot(xs[seg.s] - xs[seg.e], ys[seg.s] - ys[seg.e])       #片段长度
                    seg.centroid(xs, ys)        #计算片段均值中心cx,cy
                    seg.rectify(xs, ys, yaw)    #计算片段中心fcx,fcy
                    print("--> ", seg.s, seg.e, seg.flen)

                if segs[1].flen < self.board_mid_len_max \
                        and ((self.board_LR_len_min < segs[0].flen < self.board_LR_len_max) \
                          or (self.board_LR_len_min < segs[2].flen < self.board_LR_len_max)) \
                        and (segs[0].flen + segs[2].flen > self.board_LR_len_total_min):       #参数5，中间反光条长度阈值上限；参数6，两边反光条长度阈值区间；参数7，两边反光条长度累加和阈值下限
                    pose = PoseStamped()
                    pose.header.stamp.secs = 0
                    pose.header.stamp.nsecs = 0
                    pose.header.frame_id = msg.header.frame_id              #LaserScan
                    pose.pose.position.x = segs[1].fcx
                    pose.pose.position.y = segs[1].fcy
                    #yaw  = yaw + math.pi/2
                    pose.pose.orientation.z = math.sin(yaw/2)
                    pose.pose.orientation.w = math.cos(yaw/2)
                    pose = self.tf_l2b.transformPose("base_link", pose)
                    ob.poses.append(pose.pose)          #允许存在多个合格板子，都放到ob.poses，供base_link节点选择最近的
                    print("~~~~~~~~~~~~~~~~~~~~~~~~")
        self.ob_pub.publish(ob)


if __name__ == '__main__':
    rospy.init_node('extract_objectivepose')
    rospy.loginfo("node started")
    obj = ExtractObjectivepose()
    rospy.spin()

