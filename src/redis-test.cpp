#include<iostream>
#include<vector>
#include<string>
#include<chrono>
#include<initializer_list>
#include<unordered_map>
#include<unordered_set>

#include <sw/redis++/redis++.h>

using namespace sw::redis;

int main(int argc,char* argv[]){
   try {
      
      // Create an Redis object, which is movable but NOT copyable.
      //Redis客户端对象，可移动std::move()但不可拷贝，移动语义auto redis3 = std::move(redis1);
      auto redis = Redis("tcp://127.0.0.1:6378");
      /**
       * Redis类维护一个到Redis服务端的连接。如果连接被中断，Redis自动重连到Redis服务。
      构造1：
      explicit Redis(const ConnectionOptions &connection_opts,
         const ConnectionPoolOptions &pool_opts = {}) :
               _pool(std::make_shared<ConnectionPool>(pool_opts, connection_opts)) {}
         你可以使用ConnectionOptions和ConnectionPoolOptions初始化一个Redis实例。
         前者指定连接到Redis服务的选项，后者指定连接池的选项。后者是可选的。如果不指定，Redis维持
         一个单一的连接到Redis服务。
      
      连接选项ConnectionOptions：
      *  ConnectionOptions connection_options;

         connection_options.host = "127.0.0.1";  // Required.  主机名
         connection_options.port = 6666; // Optional. The default port is 6379.  端口号
         connection_options.password = "auth";   // Optional. No password by default.  密码
         connection_options.db = 1;  // Optional. Use the 0th database by default.  数据库号

         // Optional. Timeout before we successfully send request to or receive response from redis.
         // By default, the timeout is 0ms, i.e. never timeout and block until we send or receive successfuly.
         // NOTE: if any command is timed out, we throw a TimeoutError exception.
         可选地参数socket_timeout：在成功发送请求到服务端或者从服务端接收响应之前的超时时间。默认地
         ，超时是0ms也就是说从不超时，一直阻塞直到成功发送或接收。如果命令超时超过timeout
         connection_options.socket_timeout = std::chrono::milliseconds(200);
         //如果设置了连接选项的socket_timeout，并且尝试执行阻塞命令，比如Redis::brpop()、Redis::blpop()、Redis::bzpopmax()
         、Redis::bzpopmin()，那你必须确保连接选项的socket_timeout大于这些阻塞命令所指定的超时时间。否则可能得到TimeoutError并丢失信息    

         // Connect to Redis server with a single connection.
         Redis redis1(connection_options);   //一个连接就用一个连接池
         
         //redis++也支持连接到Unix Domain Socket的Redis服务端
         enum class ConnectionType {
            TCP = 0,
            UNIX
         };
         ConnectionOptions options;
         options.type = ConnectionType::UNIX;
         options.path = "/path/to/socket";   //socket可以在本机不同端口间通信，也可以在网络内不同主机间通信
         Redis redis(options);    //，这里/path/to/socket应该有指定本机某端口号，默认TCP    

      连接池选项ConnectionPoolOptions：
      *  ConnectionPoolOptions pool_options;

         pool_options.size = 3;  // Pool size, i.e. max number of connections.   一个连接池允许的最大连接数

         // Optional. Max time to wait for a connection. 0ms by default, which means wait forever.
         // Say, the pool size is 3, while 4 threds try to fetch the connection, one of them will be blocked.
         也就是说，当连接池大小为3,则当第4条线尝试取得连接时，其中的一条线将被阻塞
         pool_options.wait_timeout = std::chrono::milliseconds(100);

         // Optional. Max lifetime of a connection. 0ms by default, which means never expire the connection.
         // If the connection has been created for a long time, i.e. more than `connection_lifetime`,
         // it will be expired and reconnected. 连接的寿命
         pool_options.connection_lifetime = std::chrono::minutes(10);

         // Connect to Redis server with a connection pool.
         Redis redis2(connection_options, pool_options); 指定连接池对象，从该连接池创建的连接受连接池的约束

      构造2：
       explicit Redis(const std::string &uri); 
         也可以通过URI连接到Redis服务器：
         tcp://[[username:]password@]host[:port][/db]                   最后一项是数据库号用于分表
         unix://[[username:]password@]path-to-unix-domain-socket[/db]

         策略和主机部分是必需的，其他是可选的。如果连接到Unix Domain Socket，你应该使用unix策略，
         否则，你应该使用tcp策略。可选部分的默认值是：
            username: default
            password: empty string, i.e. no password
            port: 6379
            db: 0
         NOTE:如果密码或用户名包含'@'，或者用户名包含':'，你不能使用URI构造Redis对象。因为redis++不能正确
         解析URI。此时，你需要使用ConnectionOptions构造Redis对象。
         NOTE:Redis6.0支持ACL，因此你可以为连接指定用户名username。

         也可以使用URI的查询字符串来指定连接选项：
         tcp://127.0.0.1?keep_alive=true&socket_timeout=100ms&connect_timeout=100ms:
         NOTE:在查询字符串中指定的选项是大小写敏感的，所有键值对必须小写

         不能在URI的Redis构造函数中指定连接池选项。

         // Single connection to the given host and port.
         Redis redis1("tcp://127.0.0.1:6666");

         // Use default port, i.e. 6379.
         Redis redis2("tcp://127.0.0.1");

         // Connect to Redis with password, and default port.
         Redis redis3("tcp://pass@127.0.0.1");

         // Connect to Redis and select the 2nd (db number starts from 0) database.
         Redis redis4("tcp://127.0.0.1:6379/2");

         // Set keep_alive option to true with query string.
         Redis redis5("tcp://127.0.0.1:6379/2?keep_alive=true");

         // Set socket_timeout to 50 milliseconds, and connect_timeout to 1 second with query string.
         Redis redis6("tcp://127.0.0.1?socket_timeout=50ms&connect_timeout=1s");

         // Connect to Unix Domain Socket.
         Redis redis7("unix://path/to/socket");

         懒惰的创建连接
         连接池中的连接是懒惰创建的。当连接池被初始化，比如被Redis的构造函数初始化，
         Redis redis2(connection_options, pool_options); 指定连接池对象，从该连接池创建的连接受连接池的约束
         Redis还不会连接到服务端。而是，只当你尝试发送命令时才连接到服务端。如此，可以避免不必要的连接。因此如果池子
         大小是5,但最大并发连接数是3，则连接池中只会有3个连接。
         断开连接的命令？

         连接失败
         你不必检查Redis连接对象是否成功连接到服务端。如果Redis尝试连接到Redis服务端失败，或连接在某时断掉，在你尝试
         使用Redis连接对象发送命令时，它将抛出一个类型为Error的异常。既使当你收到一个异常，比如连接中断，你也不必创建
         一个新的Redis连接对象。你仍然可以重用之前的Redis连接对象发送命令，Redis连接对象将自动尝试重连到服务端。如果
         它重连成功了，它就发送命令到服务端。否则，它继续抛出一个异常。
         Redis redis("tcp://127.0.0.1:6378");
         bool bSuc(false);
         while(!bSuc){
            try{
               std::cout<<redis.get("key");
               bSuc=true;
            }catch(Error &e){
               //不必理会异常，也不用创建新的Redis连接对象发布命令，仍然可以重用之前的Redis连接对象发送命令
               std::cout<<redis.get("key");
            }
         }

         尽可能多的重用一个Redis连接对象(而不是频繁的创建新的连接对象)
         一个节点进程使用一个Redis连接对象？那就在类内维护一个连接对象得了？
         rospy也是一样？类内维护一个连接对象？对，就这么搞
         创建一个Redis连接对象并不廉价，因为它将创建一个新的连接到Redis服务端。因此你最好尽可能地重用Redis对象。
         并且，使用同一Redis连接对象在多线程环境(线程共享该Redis对象)调用Redis成员方法也是安全的（因为通过同一
         连接发送的命令总是被连接排序到单线程后与Redis服务端通信，而如果多个连接多线程地访问服务就存在同步问题）

         // This is GOOD practice.
         auto redis = Redis("tcp://127.0.0.1");
         for (auto idx = 0; idx < 100; ++idx) {
            // Reuse the Redis object in the loop.
            redis.set("key", "val");
         }

         // This is VERY BAD! It's very inefficient.
         // NEVER DO IT!!!
         for (auto idx = 0; idx < 100; ++idx) {
            // Create a new Redis object for each iteration.
            auto redis = Redis("tcp://127.0.0.1");
            redis.set("key", "val");
         }

         TLS/SSL支持

         Redis连接对象可移动不可拷贝：
         特别的，Redis连接实例不可拷贝只能移动，因而禁用拷贝构造函数、赋值运算符，使用合成的移动构造函数、移动赋值函数
         /// @brief `Redis` is not copyable.
         Redis(const Redis &) = delete;
         /// @brief `Redis` is not copyable.
         Redis& operator=(const Redis &) = delete;
         /// @brief `Redis` is movable.
         Redis(Redis &&) = default;
         /// @brief `Redis` is movable.
         Redis& operator=(Redis &&) = default;


      */


      /**
       * 
      发送命令到Redis服务端
         你可以通过Redis连接对象发送Redis命令。每个Redis命令有一或多个重载方法。例如，DEL key [key...]命令
         有三个重载的方法：

         // Delete a single key.
         long long Redis::del(const StringView &key); //删除单个键，

         // Delete a batch of keys: [first, last).
         template <typename Input>
         long long Redis::del(Input first, Input last);  //删除一批键，迭代器

         // Delete keys in the initializer_list.
         template <typename T>
         long long Redis::del(std::initializer_list<T> il); //删除一批键，std初始化列表

         使用输入参数，这些方法将基于Redis协议构建一个Redis命令，并发送命令到Redis服务端。然后
         同步地(redis++基本命令是线程安全的，除了publiser/subscriber)接收回复，解析回复
         ，返回给调用者。

      参数类型
         大多数方法的对应命令有相同的参数。以下是参数类型的列表：
      
       */ 
      // ***** STRING commands *****   字符串命令

      redis.set("key", "val");
      auto val = redis.get("key");    // val is of type OptionalString. See 'API Reference' section for details.
      if (val) {
         // Dereference val to get the returned value of std::string type.
         std::cout << *val << std::endl;
      }   // else key doesn't exist.
      redis.set("key2","val2");
      redis.set("key3","val3");

      redis.del("key");                      //删除单个键
      std::cout<<redis.exists("key")<<"\n";

      std::vector<std::string>names{"key2","key3"};   //删除一批键，迭代器
      // redis.del(names.begin(),names.end());
      std::cout<<redis.exists("key2")<<"\t"<<redis.exists("key3")<<"\n";

      std::initializer_list<std::string> inilist{"key2","key3"};  //删除一批键，初始化列表
      redis.del(inilist);
      std::cout<<redis.exists("key2")<<"\t"<<redis.exists("key3")<<"\n";

      std::cout<<redis.ping()<<"\n";
      // std::cout<<redis.info()<<"\n";
      // ***** LIST commands *****     
      redis.del("list");

      // std::vector<std::string> to Redis LIST.
      std::vector<std::string> vec = {"a", "b", "c"};
      redis.rpush("list", vec.begin(), vec.end());

      // std::initializer_list to Redis LIST.
      redis.rpush("list", {"a", "b", "c"});

      // Redis LIST to std::vector<std::string>.
      vec.clear();
      redis.lrange("list", 0, -1, std::back_inserter(vec));

      std::cout<<vec.size()<<"\n";
      for (auto &istr:vec){
         std::cout<<istr<<" ";
      }
      std::cout<<"\n";

      std::cout<<"************_\n";
      redis.set("key2","value2");
      OptionalString resstr=redis.get("key2");    //redis.get(StringView)必须访问值是字符串的键
      if(resstr){
         std::cout<<*resstr<<"\n";  //value2
         std::cout<<resstr.operator bool()<<" "<<resstr.value()<<"\n";  //1 value2
      }else
         std::cout<<"key not exist\n";

      std::pair<std::string,std::string> str2;
      while(redis.llen("list")>0){
         auto str2 = redis.blpop("list",1);
         std::cout<<str2.value().first<<"\t"<<str2.value().second<<"\n";
      }
      std::cout<<"*********_2\n";
      // auto str2 = redis.blpop("list",1);
      // std::cout<<str2.value().first<<"\t"<<str2.value().second<<"\n";

      //实验一下连接中断的场景：
      try{
         redis.set("key3","value3");
         std::chrono::seconds dur(1);
         redis.del("key4");
         std::cout<<redis.expire("key4",dur)<<"\n";
      }catch(const Error& e){    //总是断在外层catch??
         redis.set("key3","value3");
         OptionalString resstr = redis.get("key3");
         if(resstr){
            std::cout<<resstr.operator bool()<<" "<<resstr.value()<<"\n";
         }
      }

      // using Var = Variant<double,long long,std::unordered_map<std::string,long long>>;
      /**cmake编译源文件为libredis++.a、libredis++.so时如果指定了-DREDIS_PLUS_PLUS_CXX_STANDARD=17
      //会在编译时定义REDIS_PLUS_PLUS_HAS_VARIANT宏变量，然后定义类Variant封装std::variant

      #if defined REDIS_PLUS_PLUS_HAS_VARIANT
      template <typename ...Args>
      using Variant = std::variant<Args...>;
      using Monostate = std::monostate;
      #endif
      */

      auto v = redis.command<std::unordered_map<std::string,std::string>>("config","get","*");
      for(auto &item:v){
         // std::cout<<item.first<<" "<<item.second<<"\n";
      }

      redis.hincrbyfloat("hashEle","field1",3.14);
      // ***** HASH commands *****     哈希命令

      redis.hset("hash", "field", "val");

      // Another way to do the same job.
      redis.hset("hash", std::make_pair("field", "val"));

      // std::unordered_map<std::string, std::string> to Redis HASH.
      std::unordered_map<std::string, std::string> m = {
         {"field1", "val1"},
         {"field2", "val2"}
      };
      redis.hmset("hash", m.begin(), m.end());

      // Redis HASH to std::unordered_map<std::string, std::string>.
      m.clear();
      redis.hgetall("hash", std::inserter(m, m.begin()));

      // Get value only.
      // NOTE: since field might NOT exist, so we need to parse it to OptionalString.
      std::vector<OptionalString> vals;
      redis.hmget("hash", {"field1", "field2"}, std::back_inserter(vals));

      // ***** SET commands *****      集合命令

      redis.sadd("set", "m1");

      // std::unordered_set<std::string> to Redis SET.
      std::unordered_set<std::string> set = {"m2", "m3"};
      redis.sadd("set", set.begin(), set.end());

      // std::initializer_list to Redis SET.
      redis.sadd("set", {"m2", "m3"});

      // Redis SET to std::unordered_set<std::string>.
      set.clear();
      redis.smembers("set", std::inserter(set, set.begin()));

      if (redis.sismember("set", "m1")) {
         std::cout << "m1 exists" << std::endl;
      }   // else NOT exist.

      // ***** SORTED SET commands *****  有序集合命令

      redis.zadd("sorted_set", "m1", 1.3);

      // std::unordered_map<std::string, double> to Redis SORTED SET.
      std::unordered_map<std::string, double> scores = {
         {"m2", 2.3},
         {"m3", 4.5}
      };
      redis.zadd("sorted_set", scores.begin(), scores.end());

      // Redis SORTED SET to std::unordered_map<std::string, double>.
      scores.clear();
      redis.zrangebyscore("sorted_set",
               UnboundedInterval<double>{},            // (-inf, +inf)
               std::inserter(scores, scores.begin()));

      // Only get member names:
      // pass an inserter of std::vector<std::string> type as output parameter.
      std::vector<std::string> without_score;
      redis.zrangebyscore("sorted_set",
               BoundedInterval<double>(1.5, 3.4, BoundType::CLOSED),   // [1.5, 3.4]
               std::back_inserter(without_score));

      // Get both member names and scores:
      // pass an inserter of std::unordered_map<std::string, double> as output parameter.
      std::unordered_map<std::string, double> with_score;
      redis.zrangebyscore("sorted_set",
               BoundedInterval<double>(1.5, 3.4, BoundType::LEFT_OPEN),    // (1.5, 3.4]
               std::inserter(with_score, with_score.end()));

      // ***** SCRIPTING commands *****
      /* 20210412：脚本命令这里有Bug，就不用了
      // Script returns a single element.
      auto num = redis.eval<long long>("return 1", {}, {});

      // Script returns an array of elements.
      std::vector<long long> nums;
      redis.eval("return {ARGV[1], ARGV[2]}", {}, {"1", "2"}, std::back_inserter(nums));

      // mset with TTL
      auto mset_with_ttl_script = R"(
         local len = #KEYS
         if (len == 0 or len + 1 ~= #ARGV) then return 0 end
         local ttl = tonumber(ARGV[len + 1])
         if (not ttl or ttl <= 0) then return 0 end
         for i = 1, len do redis.call("SET", KEYS[i], ARGV[i], "EX", ttl) end
         return 1
      )";

      // Set multiple key-value pairs with TTL of 60 seconds.
      auto keys = {"key1", "key2", "key3"};
      std::vector<std::string> args = {"val1", "val2", "val3", "60"};
      redis.eval<long long>(mset_with_ttl_script, keys.begin(), keys.end(), vals.begin(), vals.end());
      */
      // ***** Pipeline *****

      // Create a pipeline.
      auto pipe = redis.pipeline();

      // Send mulitple commands and get all replies.
      auto pipe_replies = pipe.set("key", "value")
                              .get("key")
                              .rename("key", "new-key")
                              .rpush("list", {"a", "b", "c"})
                              .lrange("list", 0, -1)
                              .exec();

      // Parse reply with reply type and index.
      auto set_cmd_result = pipe_replies.get<bool>(0);

      auto get_cmd_result = pipe_replies.get<OptionalString>(1);

      // rename command result
      pipe_replies.get<void>(2);

      auto rpush_cmd_result = pipe_replies.get<long long>(3);

      std::vector<std::string> lrange_cmd_result;
      pipe_replies.get(4, back_inserter(lrange_cmd_result));

      // ***** Transaction *****

      // Create a transaction.
      auto tx = redis.transaction();

      // Run multiple commands in a transaction, and get all replies.
      auto tx_replies = tx.incr("num0")
                           .incr("num1")
                           .mget({"num0", "num1"})
                           .exec();

      // Parse reply with reply type and index.
      auto incr_result0 = tx_replies.get<long long>(0);

      auto incr_result1 = tx_replies.get<long long>(1);

      std::vector<OptionalString> mget_cmd_result;
      tx_replies.get(2, back_inserter(mget_cmd_result));

      // ***** Generic Command Interface *****

      // There's no *Redis::client_getname* interface.
      // But you can use *Redis::command* to get the client name.
      val = redis.command<OptionalString>("client", "getname");
      if (val) {
         std::cout << *val << std::endl;
      }

      // Same as above.
      auto getname_cmd_str = {"client", "getname"};
      val = redis.command<OptionalString>(getname_cmd_str.begin(), getname_cmd_str.end());

      // There's no *Redis::sort* interface.
      // But you can use *Redis::command* to send sort the list.
      std::vector<std::string> sorted_list;
      redis.command("sort", "list", "ALPHA", std::back_inserter(sorted_list));

      // Another *Redis::command* to do the same work.
      auto sort_cmd_str = {"sort", "list", "ALPHA"};
      redis.command(sort_cmd_str.begin(), sort_cmd_str.end(), std::back_inserter(sorted_list));

      // ***** Redis Cluster *****
      /* 20210412：集群就不测了
      // Create a RedisCluster object, which is movable but NOT copyable.
      auto redis_cluster = RedisCluster("tcp://127.0.0.1:7000");

      // RedisCluster has similar interfaces as Redis.
      redis_cluster.set("key", "value");
      val = redis_cluster.get("key");
      if (val) {
         std::cout << *val << std::endl;
      }   // else key doesn't exist.

      // Keys with hash-tag.
      redis_cluster.set("key{tag}1", "val1");
      redis_cluster.set("key{tag}2", "val2");
      redis_cluster.set("key{tag}3", "val3");

      std::vector<OptionalString> hash_tag_res;
      redis_cluster.mget({"key{tag}1", "key{tag}2", "key{tag}3"},
               std::back_inserter(hash_tag_res));
      */

   } catch (const Error &e) {
      /**
       * 1、Redis连接对象连接到服务端失败时抛出Error
       * 2、
       */ 
      // Error handling.
      std::cout<<"outer exception occur!\n";
   }
}