#include "ros/ros.h"          //  /opt/ros/kinetic/include/ros
//  ros/ros.h包含了使用ROS系统中最常见的公共部分所需的全部头文件
#include "std_msgs/String.h"  //  /opt/ros/kinetic/include/std_msgs
//引用/opt/ros/kinetic/share/std_msgs软件包(只定义了消息)中的msg/String.msg消息
//，自动生成封装类到/opt/ros/kinetic/include/std_msgs，放在名字空间std_msgs内

#include <sstream>
#include <unordered_map>
#include <string>
#include "redis_json_wraper.h"
ConnectionOptions redis_wraper::connection_options("tcp://127.0.0.1:6378");

ConnectionPoolOptions redis_wraper::pool_options;   //连接池最多连接数默认1，每个roscpp进程就用一个连接对象吧
Redis redis_wraper::redis=Redis(redis_wraper::connection_options,redis_wraper::pool_options);   //进程全局的Redis连接，既使多线程共享也是安全的

/**
 * This tutorial demonstrates simple sending of messages over the ROS system.
 * 该教程展示了通过ROS系统简单地发送消息
 */
int main(int argc, char **argv)
{
    /**
     * The ros::init() function needs to see argc and argv so that it can perform
     * any ROS arguments and name remapping that were provided at the command line.
     * For programmatic remappings you can use a different version of init() which takes
     * remappings directly, but for most command-line programs, passing argc and argv is
     * the easiest way to do it.  The third argument to init() is the name of the node.
     * ros::init()函数需要能看见argc和argv从而执行由命令行提供的ROS参数与名字的重映射。
     * 对正式的重映射，你可以使用init()的不同版本从而直接进行重映射，但对大多数命令行程序，传递
     * argc和argv是最简单的方式。init()的第三个参数是节点名字。
     * 
     * You must call one of the versions of ros::init() before using any other
     * part of the ROS system.
     * 在使用ROS系统的任何部分之前你必须调用某个版本的ros::init()方法
     * 
     */

    /** @brief ROS initialization function.
     *
     * This function will parse any ROS arguments (e.g., topic name
     * remappings), and will consume them (i.e., argc and argv may be modified
     * as a result of this call).
     * 该函数将解析所有ROS参数（比如topic名重映射)，并且将使用它们（比如argc和argv可能被修改作为该调用的结果）
     *
     * Use this version if you are using the NodeHandle API
     *
     * \param argc
     * \param argv
     * \param name Name of this node.  The name must be a base name, ie. it cannot contain namespaces.
     * \param options [optional] Options to start the node with (a set of bit flags from \ref ros::init_options)
     * \throws InvalidNodeNameException If the name passed in is not a valid "base" name
     *
     * ROSCPP_DECL void init(int &argc, char **argv, const std::string& name, uint32_t options = 0);
     */
    // %Tag(INIT)%
    ros::init(argc, argv, "talker");    //  /opt/ros/kinetic/include/ros/init.h
    Redis   &redis_cli=redis_wraper::redis;
    //试验nlohmann/json.hpp：
    std::unordered_map<std::string,std::string> jsonMap;
    jsonMap["field1"]="value1";
    jsonMap["field2"]="value2";
    json j(jsonMap);
    redis_cli.set("jsonMap",j.dump());


    // %EndTag(INIT)%

    /**
     * NodeHandle is the main access point to communications with the ROS system.
     * The first NodeHandle constructed will fully initialize this node, and the last
     * NodeHandle destructed will close down the node.
     * NodeHandle是与ROS系统通信的主要接入点。第一个创建的NodeHandle将完全初始化该节点,最后析构
     * 的NodeHandle将关闭该节点
     * 为这个进程的节点创建句柄。创建的第一个NodeHandle实际上将执行节点的初始化，而最后一个被销毁
     * 的NodeHandle将清除节点所使用的任何资源
     */
    // %Tag(NODEHANDLE)%
    ros::NodeHandle n("~nodeHandle");
    // %EndTag(NODEHANDLE)%

    /**
     * The advertise() function is how you tell ROS that you want to
     * publish on a given topic name. This invokes a call to the ROS
     * master node, which keeps a registry of who is publishing and who
     * is subscribing. After this advertise() call is made, the master
     * node will notify anyone who is trying to subscribe to this topic name,
     * and they will in turn negotiate a peer-to-peer connection with this
     * node.  advertise() returns a Publisher object which allows you to
     * publish messages on that topic through a call to publish().  Once
     * all copies of the returned Publisher object are destroyed, the topic
     * will be automatically unadvertised.
     * 用ros::NodeHandle::advertise()方法来告诉ROS你想在一个给定topic名字上发布topic
     * 。这将导致对ROSmaster节点的调用，master节点维护谁在发布以及谁在订阅的一个注册表
     * 。在该advertise()被调用后，master节点将通知所有尝试订阅该topic名字(chatter)的节点
     * ，这些节点将轮流协商一个与该节点端到端的连接。advertise()返回一个发布者Publisher对象
     * ，其允许你通过调用ros::Publisher::publish()在那个topic上发布消息。一旦返回的
     * Publisher对象的所有拷贝被析构，该topic将自动被"未登广告"（ros::Publisher对象中应该
     * 是包含对topic发布者的引用，当最后一个引用被析构后便失去了对该topic发布者的引用从而
     * 该topic发布者被自动被析构"）
     * 
     * NodeHandle::advertise()方法返回一个ros::Publisher对象，它有2个目的：其一，它
     * 包含一个publish()方法，可以将消息发布到创建它的话题上；其二，当超出范围(作用域)时
     * ，它将自动取消这一宣告操作(也就是析构ros::Publisher对象)。
     *
     * The second parameter to advertise() is the size of the message queue
     * used for publishing messages.  If messages are published more quickly
     * than we can send them, the number here specifies how many messages to
     * buffer up before throwing some away.
     * advertise()函数的第二个参数是用于发布消息的消息队列message queue的大小。如果
     * 消息比我们可以发送的速度更快被发布，这里的数字指定了在抛出一些消息之前要缓冲多少消息.
     * 如果发布得太快，它将最多缓存1000条消息，不然就会丢弃旧消息。
     */

    /**
     * 通过进程节点句柄调用ros::NodeHandle::advertise()发起话题发布者，调用
     * ros::NodeHandle::subscribe()发起话题订阅者。一个进程节点可以发起多个
     * 话题发布者、话题订阅者、话题发布者与话题订阅者
     * image_transport::Publisher pub = it.advertise("node_a", 1);
     * image_transport::Subscriber sub = it.subscribe("node_b",1,imageCallback);
     * 
     * ros::NOdeHandle::advertise()方法返回一个ros::Publisher对象，它有2个目的：
     * 其一，它包含一个publish()方法，可以将消息发布到创建它的话题上；其二，当超出范围时，
     * 它将自动取消这一宣告操作。
     */
    // %Tag(PUBLISHER)%
    ros::Publisher chatter_pub = n.advertise<std_msgs::String>("chatter", 1000);
    // %EndTag(PUBLISHER)%

    // %Tag(LOOP_RATE)%
    ros::Rate loop_rate(0.5);    //10Hz，10次每秒
    /**
     * ros::Rate对象能让你指定循环的频率。它会记录从上次调用ros::Rate::sleep()到现在
     * 已经有多长时间，并休眠正确的时间。
     */
    // %EndTag(LOOP_RATE)%

    /**
     * A count of how many messages we have sent. This is used to create
     * a unique string for each message.
     */
    // %Tag(ROS_OK)%
    int count = 0;
    /**
     * 默认情况下，roscpp进程将安装一个SIGINT处理程序，它能够处理Ctrl+C操作，让ros::ok()返回false
     * ros::OK()在以下情况会返回false：
     * 1、收到SIGINT信号(Ctrl+C)
     * 2、被另一个同名节点踢出了网络
     * 3、ros::shutdown()被程序的另一部分调用
     * 4、所有的ros::NodeHandle进程节点句柄都已被销毁(当前进程节点的所有引用句柄被销毁，自然已经
     * 销毁了通过所有进程节点句柄发起的话题发布者、话题订阅者、，当前进程节点作为一个ROS节点没有存
     * 在的必要了)
     * 一旦ros::ok()返回false，所有的ROS调用都会失败
     */
    while (ros::ok()){
        // %EndTag(ROS_OK)%
        /**
         * This is a message object. You stuff it with data, and then publish it.
         */
        // %Tag(FILL_MESSAGE)%
        std_msgs::String msg;   //构造消息对象

        std::stringstream ss;
        ss << "hello world " << count;
        msg.data = ss.str();
        /**
         *我们使用一种消息自适应的类(实例)在ROS上广播消息，该类通常由msg文件生成。更复杂的数据类型
        也可以，不过我们现在将使用标准的std_msgs::String消息，它有一个成员data
        */
        // %EndTag(FILL_MESSAGE)%

        // %Tag(ROSCONSOLE)%
        ROS_INFO("%s", msg.data.c_str());   
        //宏，扩展成ROS_LOG( ::ros::console::levels::Info,ROSCONSOLE_DEFAULT_NAME,"%s",msg.data.c_str() )
        //向ROS控制台/rosout写节点信息，ROS_INFO宏和它的朋友们可用来取代printf/cout，参见http://wiki.ros.org/rosconsole
        //rospy.loginfo(rospy.get_caller_id()+strmsg) #往rospy节点记录信息
        // %EndTag(ROSCONSOLE)%

        /**
         * The publish() function is how you send messages. The parameter
         * is the message object. The type of this object must agree with the type
         * given as a template parameter to the advertise<>() call, as was done
         * in the constructor above.
         * ros::Publisher类实例方法publish用来发送消息。参数是消息对象。消息对象的
         * 类型必须与调用advertise<>()时作为模板参数给出的类型相同，就像在上面构造函数
         * 中那样：n.advertise<std_msgs::String>("chatter", 1000);
         * std_msgs::String msg;
         */
        // %Tag(PUBLISH)%
        chatter_pub.publish(msg);
        redis_cli.set("param1",ss.str());
        /**
         * ros::Publisher::publish()方法把消息广播给所有已连接(连接到master 节点)的节点
         */ 
        // %EndTag(PUBLISH)%

        // %Tag(SPINONCE)%
        ros::spinOnce();
        /**
         * 此处调用ros::spinOnce()对于这个简单程序来说没啥必要，因为我们没有接收任何回调。
         * 然而，如果要在这个程序中添加订阅，但此处没有ros::spinOnce()的话，回调函数将永远
         * 不会被调用。ros::spinOnce()等待让订阅的回调函数被调用
         */
        // %EndTag(SPINONCE)%

        // %Tag(RATE_SLEEP)%
        loop_rate.sleep();    //10Hz，ros::Rate::sleep()
        /**
         * 使用ros::Rate在剩下的时间内睡眠，以让我们达到10Hz的发布速率
         */ 
        // %EndTag(RATE_SLEEP)%
        ++count;
    }


    return 0;
}
// %EndTag(FULLTEXT)%
