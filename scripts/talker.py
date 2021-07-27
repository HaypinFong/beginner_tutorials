#!/usr/bin/env python
# -*- coding: UTF-8 -*-


## Simple talker demo that published std_msgs/Strings messages
## to the 'chatter' topic

import rospy    
from std_msgs.msg import String      
#std_msgs.msg的导入为了使我们能重用std_msgs/String消息类型来发布
#在source setup.bash终端环境下环境变量$PYTHONPATH 已经是/opt/ros/kinetic/lib/python2.7/dist-packages
#当你source the devel or install space in which the package was build or installed to时
#将自动地将要安装的包增加到PYTHONPATH

from redis_wraper import redis_wraper

def talker():
    rospy.init_node('talker', anonymous=False)
    redis_cli = redis_wraper()
    #初始化该进程的ROS节点,一个rospy进程中只能有一个节点,因此只能调用rospy.init_node()一次
    #把该节点的名称告诉了rospy，只要rospy掌握了这一信息后，才会开始与ROS主节点进行通信
    #在本例中，该节点将使用"talker"名称，anonymous=True让名称末尾添加随机数，确保节点
    #具有唯一的名称
    #http://wiki.ros.org/rospy/Overview/Initialization%20and%20Shutdown#Initializing_your_ROS_Node
    
    pub = rospy.Publisher('~chatter', String, queue_size=10)
    #定义了talker与其他ROS部分的接口。声明该节点正在使用String消息类型发布到chatter话题
    #queue_size参数用于在订阅者接收消息的速度不够快的情况下，限制排队的消息数量为10,
    #订阅者慢，那当前排队的消息只要能满足订阅者即可，多出排队的消息就丢弃了？丢弃旧的消息
    
    rate = rospy.Rate(0.5) # 10hz
    #此行创建一个Rate对象rate,借助其方法sleep(),它提供了一种方便的方法,来以你想要的速率循环,
    #10hz表示希望它每秒循环10次
    while not rospy.is_shutdown():
        #在rospy中测试关机的最常见模式,或rospy.spin(),该rospy.spin()简单休眠,直到is_shutdown()
        #标志为真。它主要用于防止当前Python Main线程退出
        #节点可以通过多种方式接收关闭请求，因此使用while not rospy.is_shutdown()或rospy.spin()
        #两种方法之一以确保程序正确终止很重要
        hello_str = "hello world %s" % rospy.get_time()
        rospy.loginfo(hello_str)    #往rospy节点记录信息
        redis_cli.setkv('param1',hello_str)
        #rospy.loginfo(str)有3各任务:打印消息到屏幕上(当前节点?);把消息写入节点的日志文件;
        #写入rosout(其他节点),rosout是一个方便的调试工具
        pub.publish(hello_str)        #发布话题
        rate.sleep()            #开始休眠10Hz,在循环中用适当的睡眠时间维持期望的速率
    '''这个循环是一个相当标准的rospy结构,检查rospy.is_shutdown()标志,然后执行代码逻辑.
    你必须查看is_shutdown()以检查程序是否应该退出(例如有ctrl+c或其他).在此例中,代码
    逻辑即对pub.publish(hello_str)的调用,它将一个字符串发布到chatter话题.
    '''

if __name__ == '__main__':
    try:
        talker()
    except rospy.ROSInterruptException:    
    #当按下ctrl+c或节点因其他原因关闭时,这一异常会被rospy.sleep()和rospy.Rate.sleep()抛出
        pass


'''
注册关闭钩子函数:rospy进程开始关闭时要调用rospy.on_shutdown(h),h是一个不带参数的函数,当你的节点即将
被关闭时，你可以使用rospy.on_shutdown()来请求一个回调。这将在事实上关闭发生前被调用，因此你可以安全
地执行服务和参数服务调用。消息不保证能被发布
def myhook():
    print "shutdown time!"

rospy.on_shutdown(myhook)
手动关闭(高级):
如果你要覆盖rospy的信号处理(rospy.init_node()函数的disable_signals选项),你需要手动调用正确的shutdown
函数来适当地清理:
rospy.signal_shutdown(reason)
开始节点关闭。reason是一个人类可读的字符串,描述了为什么一个节点被关闭
rospy.init_node(name,anonymous=False,log_level=rospy.INFO,disable_signals=False)
    disable_signals=False
    默认地,rospy注册信号处理函数从而可以在ctrl+c时退出,然而在一些代码中你可能希望禁用它
'''
