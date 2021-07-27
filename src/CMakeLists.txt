project(redis_json_wraper)
include_directories( "/usr/local/include")

set(CMAKE_CXX_STANDARD 11)              #20210414fhp：指定C++版本
set(CMAKE_CXX_STANDARD_REQUIRED True)
set(HREDIS_DYNAMIC_LIBS "/usr/local/lib/libhiredis.so")             #手动指定动态库
set(REDIS_PLUS_PLUS_DYNAMIC_LIBS "/usr/local/lib/libredis++.so")

add_library(redis_json_wraper redis_json_wraper.cpp)
target_link_libraries(redis_json_wraper ${HREDIS_DYNAMIC_LIBS} 
    ${REDIS_PLUS_PLUS_DYNAMIC_LIBS})
# target_include_directories(redis_json_wraper  #设置包含目录的使用要求不如把头文件安装到/usr/local/include
#     INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})    #把库安装到/usr/local/lib
                                                #把可执行程序安装到/usr/local/bin