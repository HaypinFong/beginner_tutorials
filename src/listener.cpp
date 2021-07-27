#include "ros/ros.h"
#include "std_msgs/String.h"
/**
 * This tutorial demonstrates simple receipt of messages over the ROS system.
 * 这个教程展示了通过ROS系统的简单的消息接收
 */
#include "redis_json_wraper.h"
ConnectionOptions redis_wraper::connection_options("tcp://127.0.0.1:6378");

ConnectionPoolOptions redis_wraper::pool_options;   //连接池最多连接数默认1，每个roscpp进程就用一个连接对象吧
Redis redis_wraper::redis=Redis(redis_wraper::connection_options,redis_wraper::pool_options);   //进程全局的Redis连接，既使多线程共享也是安全的

void chatterCallback(const std_msgs::String::ConstPtr& msg)
{
    //typedef boost::shared_ptr< ::std_msgs::String_<ContainerAllocator> const> ConstPtr;
    ROS_INFO("I heard: %s", msg->data.c_str());
    Redis   &redis_cli=redis_wraper::redis;
    std::string resstr( redis_cli.get("param1").value() );
    ROS_INFO("  and param1 is: %s", resstr.c_str());
    /**
     * 回调函数用boost shared_ptr智能指针引用消息而不是值拷贝，
     * 这是一个回调函数，当有新消息到达chatter话题时他就会被调用。该消息是用boost::shared_ptr智能
     * 指针传递的，这意味着你可以根据需要存储他，既不用担心它在下面被删除，又不必复制底层数据
     */ 
}

int main(int argc, char **argv)
{
    /**
     * The ros::init() function needs to see argc and argv so that it can perform
     * any ROS arguments and name remapping that were provided at the command line.
     * For programmatic remappings you can use a different version of init() which takes
     * remappings directly, but for most command-line programs, passing argc and argv is
     * the easiest way to do it.  The third argument to init() is the name of the node.
     *
     * You must call one of the versions of ros::init() before using any other
     * part of the ROS system.
     */
    ros::init(argc, argv, "listener");
    /**
     * NodeHandle is the main access point to communications with the ROS system.
     * The first NodeHandle constructed will fully initialize this node, and the last
     * NodeHandle destructed will close down the node.
     */
    ros::NodeHandle n;

    /**
     * The subscribe() call is how you tell ROS that you want to receive messages
     * on a given topic.  This invokes a call to the ROS
     * master node, which keeps a registry of who is publishing and who
     * is subscribing.  Messages are passed to a callback function, here
     * called chatterCallback.  subscribe() returns a Subscriber object that you
     * must hold on to until you want to unsubscribe.  When all copies of the Subscriber
     * object go out of scope, this callback will automatically be unsubscribed from
     * this topic.
     * 使用subscribe()调用告诉ROS你想在一个给定topic上接收消息。这导致对ROS master节点的调用，
     * master节点维护谁在发布、以及谁在订阅的一个注册表。消息被传递给回调函数，这里是chatterCallback()，
     * ros::NodeHandle::subscribe()方法返回一个订阅者对象，你必须维持它直到你想解除订阅。
     * 当订阅者对象的所有拷贝超出作用域被析构，这个回调将自动从这个topic解除订阅。
     * 
     * 当给定topic的所有订阅者都超出作用域被析构，该topic将被解除订阅unsubscribed。
     *
     * The second parameter to the subscribe() function is the size of the message
     * queue.  If messages are arriving faster than they are being processed, this
     * is the number of messages that will be buffered up before beginning to throw
     * away the oldest ones.
     * 如果消息比能被处理的速度更快到达，这是在开始丢弃旧消息之前被缓存的消息的数量
     */
    ros::Subscriber sub = n.subscribe("/talker/nodeHandle/chatter", 1000, chatterCallback);
    Redis   &redis_cli=redis_wraper::redis;
    std::string resstr( redis_cli.get("jsonMap").value() );
    json j(json::parse(resstr));    //使用json::parse()全局函数显式使用std::string构造json对象
    // json j(resstr);     //std::string隐式构造json对象，会报错"what():  [json.exception.type_error.302] type must be object, but is string"
    auto jsonMap = j.get<std::unordered_map<std::string,std::string>>();    //反序列化需要给出类型的模板参数，不像Python的json库那样可以自行推断类型
    ROS_INFO("jsonMap[\"fiedl1\"] is: %s", jsonMap["field1"].c_str());
    /**
     * 
     * 通过master节点订阅chatter话题，当有新消息到达所订阅的chatter话题时会调用回调函数。队列大小，
     * 如果队列达到1000条，再有新消息到达时旧消息会被丢弃(队列，先进先出)
     * 
     * ros::NodeHandle::subscribe()返回一个ros::Subscriber订阅者对象，你必须保持它，除非想
     * 取消订阅。当Subscriber对象被析构，它将自动从chatter话题取消订阅。
     * 
     * 其他回调函数签名：
     *    void callback(boost::shared_ptr<std_msgs::String const>);   //底层const指针
     *    void callback(std_msgs::StringConstPtr);        //底层const指针
     *    void callback(std_msgs::String::ConstPtr);      //底层const指针
     *    void callback(const std_msgs::String&);         //顶层const引用
     *    void callback(std_msgs::String);                //
     *    void callback(const ros::MessageEvent<std_msgs::String const>&);
     * 
     *    void callback(const boost::shared_ptr<std_msgs::String>&);  //顶层const引用，不可以改指向但可以改内容
     *    void callback(boost::shared_ptr<std_msgs::String>); //拷贝指针，增加引用计数
     *    void callback(const std_msgs::StringPtr&);      //顶层const引用，不可以改指向但可以改内容
     *    void callback(std_msgs::StringPtr);             //拷贝指针，增加引用计数
     *    void callback(std_msgs::String::Ptr);           //拷贝指针
     *    void callback(const ros::MessageEvent<std_msgs::String>&);
     * 
     *    MessageEvent类允许你在订阅回调函数中检索一个消息的元数据：
     *    void callback(const ros::MessageEvent<std_msgs::String const>& event)
     *    {
     *        const std::string& publisher_name = event.getPublisherName();
     *        const ros::M_string& header = event.getConnectionHeader();
     *        ros::Time receipt_time = event.getReceiptTime();
     * 
     *        const std_msgs::StringConstPtr& msg = event.getMessage();
     *        //使用顶层const引用+底层const指针的msg，不改指向，不改内容，不增加引用计数
     *    }
     * 
     * 还有另一些版本的ros::NodeHandle::subscribe()函数，可以让你指定为类的成员函数，甚至可以
     * 是被Boost.Function对象调用的任何函数：
     * 1、一般函数
     *    void callback(const std_msgs::StringConstPtr& str)
     *    ros::Subscriber sub = nh.subscribe("my_topic", 1, callback);
     * 2、实例方法：
     *    void Foo::callback(const std_msgs::StringConstPtr& message)
     *    Foo foo_object;
     *    ros::Subscriber sub = nh.subscribe("my_topic", 1, &Foo::callback, &foo_object);
     * 3、可调用对象(与Lambda表达式)
     *    class Foo
     *    {
     *    public:
     *    void operator()(const std_msgs::StringConstPtr& message)    
     *        //顶层const指针的引用，不增加引用计数也保护了实参指针指向
     *        {
     *        }
     *    };
     *    ros::Subscriber sub = nh.subscribe<std_msgs::String>("my_topic", 1, Foo());
     *    注意：当使用可调用对象(比如boost::bind)时你必须以模板参数的形式显式指定消息类型，
     *    因为在这种情况下编译器不能推断出消息类型
     */   
    ros::spin();
    /**
     * ros::spin() will enter a loop, pumping callbacks.  With this version, all
     * callbacks will be called from within this thread (the main one).  ros::spin()
     * will exit when Ctrl-C is pressed, or the node is shutdown by the master.
     * ros::spin()将进入一个循环，泵送回调函数。在当前版本中，所有回调函数将被从当前主线程调用。
     * ros:spin()在Ctrl-C被按下是推出，或节点被住节点关闭。
     * 
     * ros::spin()启动了一个自循环，它会尽可能快地调用消息回调函数(当有发布到订阅的话题)
     * 。不过不要担心，如果没有什么事情，它不会占用太多CPU。另外，一旦ros::ok()返回false，
     * ros::spin()就会退出，这意味着ros::shutdown()被调用了，主节点让我们关闭（或是因为
     * 按下Ctrl+C，ros::shutdown()被手动调用）
     */ 

    return 0;
}
