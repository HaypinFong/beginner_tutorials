#include "sw/redis++/redis++.h"
#include "nlohmann/json.hpp"
using namespace sw::redis;
using json = nlohmann::json;
class redis_wraper{
    public:
        //同rospy，在类内维护一个连接，活动在进程的全局作用域
        static ConnectionOptions connection_options;    //连接选项
        static ConnectionPoolOptions pool_options;      //连接池选项
        static Redis redis;                             //连接对象

};