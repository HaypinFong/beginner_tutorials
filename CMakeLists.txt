cmake_minimum_required(VERSION 3.0.2)
project(beginner_tutorials)

## Compile as C++11, supported in ROS Kinetic and newer
# add_compile_options(-std=c++11)

## Find catkin macros and libraries
## if COMPONENTS list like find_package(catkin REQUIRED COMPONENTS xyz)
## is used, also find other catkin packages
#获取这个包的构建时buildtime依赖的信息
find_package(catkin REQUIRED COMPONENTS     #生成${catkin_INCLUDE_DIRS}、${catkin_LIBRARIES}
  roscpp            #将找到/opt/ros/kinetic/share/roscpp/rosbuild/roscpp.cmake，这些文件里写明了这些包的导出包含目录和导出库目录
  rospy              
  std_msgs           #20210330,添加message_generation依赖项，才能生成消息
  message_generation	#20210407,都是/opt/ros/kinetic/share/的软件包
  genmsg
)

## System dependencies are found with CMake's conventions
# find_package(Boost REQUIRED COMPONENTS system)

## Uncomment this if the package has a setup.py. This macro ensures
## modules and global scripts declared therein get installed
## See http://ros.org/doc/api/catkin/html/user_guide/setup_dot_py.html
# catkin_python_setup()

################################################
## Declare ROS messages, services and actions ##
################################################

## To declare and build messages, services or actions from within this
## package, follow these steps:
## * Let MSG_DEP_SET be the set of packages whose message types you use in
##   your messages/services/actions (e.g. std_msgs, actionlib_msgs, ...).
## * In the file package.xml:
##   * add a build_depend tag for "message_generation"
##   * add a build_depend and a exec_depend tag for each package in MSG_DEP_SET
##   * If MSG_DEP_SET isn't empty the following dependency has been pulled in
##     but can be declared for certainty nonetheless:
##     * add a exec_depend tag for "message_runtime"
## * In this file (CMakeLists.txt):
##   * add "message_generation" and every package in MSG_DEP_SET to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * add "message_runtime" and every package in MSG_DEP_SET to
##     catkin_package(CATKIN_DEPENDS ...)
##   * uncomment the add_*_files sections below as needed
##     and list every .msg/.srv/.action file to be processed
##   * uncomment the generate_messages entry below
##   * add every package in MSG_DEP_SET to generate_messages(DEPENDENCIES ...)

## Generate messages in the 'msg' folder  #当前软件包的msg目录内定义的**.msg文件
add_message_files(
   FILES
#   Message1.msg
#   Message2.msg
   Num.msg 		#20210330fhp,手动添加.msg文件
   Str.msg		#20210401fhp，自定义字符串类型
)

## Generate services in the 'srv' folder
add_service_files(
   FILES
#   Service1.srv
#   Service2.srv
   AddTwoInts.srv	#20210330fhp
)

## Generate actions in the 'action' folder
# add_action_files(
#   FILES
#   Action1.action
#   Action2.action
# )

## Generate added messages and services with any dependencies listed here
#事实上生成语言特定的消息和服务文件
generate_messages(  #20210330fhp,确保generate_messages()函数被调用
  DEPENDENCIES
  std_msgs   	    #取消注释，添加任意你的消息用到的包含.msg文件的软件包std_msgs
)		    #调用generate_messages()生成所有消息、服务和action动作

################################################
## Declare ROS dynamic reconfigure parameters ##
################################################

## To declare and build dynamic reconfigure parameters within this
## package, follow these steps:
## * In the file package.xml:
##   * add a build_depend and a exec_depend tag for "dynamic_reconfigure"
## * In this file (CMakeLists.txt):
##   * add "dynamic_reconfigure" to
##     find_package(catkin REQUIRED COMPONENTS ...)
##   * uncomment the "generate_dynamic_reconfigure_options" section below
##     and list every .cfg file to be processed

## Generate dynamic reconfigure parameters in the 'cfg' folder
# generate_dynamic_reconfigure_options(
#   cfg/DynReconf1.cfg
#   cfg/DynReconf2.cfg
# )

###################################
## catkin specific configuration ##
###################################
## The catkin_package macro generates cmake config files for your package
## Declare things to be passed to dependent projects  声明要传递给依赖当前包的那些包的东西
## INCLUDE_DIRS: uncomment this if your package contains header files
## LIBRARIES: libraries you create in this project that dependent projects also need
## CATKIN_DEPENDS: catkin_packages dependent projects also need
## DEPENDS: system dependencies of this project that dependent projects also need
#声明当前catkin包的运行时依赖
catkin_package(		#确保该catkin_package()命令声明了其他软件包的消息、服务和行为依赖
#  INCLUDE_DIRS include
#  LIBRARIES beginner_tutorials
  CATKIN_DEPENDS roscpp rospy std_msgs message_runtime  #20210330,确保导出消息的运行时依赖关系
#  DEPENDS system_lib
)

###########
## Build ##
###########

## Specify additional locations of header files
## Your package locations should be listed before other locations
set(REDIS_INCLUDE_PATH "/usr/local/include")    
include_directories(                            #20210414：增加包含目录
   include ${catkin_INCLUDE_DIRS}
   include ${REDIS_INCLUDE_PATH}
)

## Declare a C++ library
# add_library(${PROJECT_NAME}
#   src/${PROJECT_NAME}/beginner_tutorials.cpp
# )

## Add cmake target dependencies of the library
## as an example, code may need to be generated before libraries
## either from message generation or dynamic reconfigure重新配置
# add_dependencies(${PROJECT_NAME} ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Declare a C++ executable
## With catkin_make all packages are built within a single CMake context
## The recommended prefix ensures that target names across packages don't collide
# add_executable(${PROJECT_NAME}_node src/beginner_tutorials_node.cpp)

## Rename C++ executable without prefix
## The above recommended prefix causes long target names, the following renames the
## target back to the shorter version for ease of user use
## e.g. "rosrun someones_pkg node" instead of "rosrun someones_pkg someones_pkg_node"
# set_target_properties(${PROJECT_NAME}_node PROPERTIES OUTPUT_NAME node PREFIX "")

## Add cmake target dependencies of the executable
## same as for the library above
# add_dependencies(${PROJECT_NAME}_node ${${PROJECT_NAME}_EXPORTED_TARGETS} ${catkin_EXPORTED_TARGETS})

## Specify libraries to link a library or executable target against
# target_link_libraries(${PROJECT_NAME}_node
#   ${catkin_LIBRARIES}
# )

#############
## Install ##
#############

# all install targets should use catkin DESTINATION variables
# See http://ros.org/doc/api/catkin/html/adv_user_guide/variables.html

## Mark executable scripts (Python etc.) for installation
## in contrast to setup.py, you can choose the destination
catkin_install_python(PROGRAMS	  #确保正确安装python脚本
   scripts/talker.py		  #含发布话题的节点
   scripts/listener.py		  #含订阅话题的节点
   scripts/add_two_ints_server.py #服务节点
   scripts/add_two_ints_client.py #客户端节点

   scripts/plain_ob_extract_v1.py
   scripts/plain_ob_extract_front.py
#   scripts/my_python_script
   DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

## Mark executables for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_executables.html
# install(TARGETS ${PROJECT_NAME}_node
#   RUNTIME DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
# )

## Mark libraries for installation
## See http://docs.ros.org/melodic/api/catkin/html/howto/format1/building_libraries.html
# install(TARGETS ${PROJECT_NAME}
#   ARCHIVE DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   LIBRARY DESTINATION ${CATKIN_PACKAGE_LIB_DESTINATION}
#   RUNTIME DESTINATION ${CATKIN_GLOBAL_BIN_DESTINATION}
# )

## Mark cpp header files for installation
# install(DIRECTORY include/${PROJECT_NAME}/
#   DESTINATION ${CATKIN_PACKAGE_INCLUDE_DESTINATION}
#   FILES_MATCHING PATTERN "*.h"
#   PATTERN ".svn" EXCLUDE
# )

## Mark other files for installation (e.g. launch and bag files, etc.)
# install(FILES
#   # myfile1
#   # myfile2
#   DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
# )

#############
## Testing ##
#############

## Add gtest based cpp test target and link libraries
# catkin_add_gtest(${PROJECT_NAME}-test test/test_beginner_tutorials.cpp)
# if(TARGET ${PROJECT_NAME}-test)
#   target_link_libraries(${PROJECT_NAME}-test ${PROJECT_NAME})
# endif()

## Add folders to be run by python nosetests
# catkin_add_nosetests(test)
set(CMAKE_CXX_STANDARD 11)              #20210414fhp：指定C++版本
set(CMAKE_CXX_STANDARD_REQUIRED True)
SET(CMAKE_BUILD_TYPE "RelWithDebInfo")
set(HREDIS_DYNAMIC_LIBS "/usr/local/lib/libhiredis.so")             #手动指定动态库
set(REDIS_PLUS_PLUS_DYNAMIC_LIBS "/usr/local/lib/libredis++.so")
# add_library(libredis++ SHARED IMPORTED)
# add_library(libhiredis SHARED IMPORTED)
#20210407fhp:
#定义使用了msg/Str.msg等的可执行程序
add_executable(talker   src/talker.cpp)     
target_link_libraries(talker ${catkin_LIBRARIES} ${HREDIS_DYNAMIC_LIBS} ${REDIS_PLUS_PLUS_DYNAMIC_LIBS})     #20210414：设置库目录
add_dependencies(talker beginner_tutorials_generate_messages_cpp) 
#必须为可执行目标添加依赖项到消息生成目标，这确保了在使用此包之前生成了该包的
#消息头。如果使用来自你catkin工作空间中的其他包中的消息，则还需要将依赖项添加
#到各自的生成目标中，因为catkin将所有项目并行构建。在ROS Groovy(2012)及
#更新版本中(kinetic 2016)，还可以使用
#target_link_libraries(talker ${catkin_LIBRARIES})来依赖所有必须的目标

add_executable(listener src/listener.cpp)
target_link_libraries(listener ${catkin_LIBRARIES} ${HREDIS_DYNAMIC_LIBS} ${REDIS_PLUS_PLUS_DYNAMIC_LIBS})   #设置库目录
add_dependencies(listener beginner_tutorials_generate_messages_cpp)

#把依赖的库安装到catkin_install的话就是个/usr/local/lib/libhiredis.so与libredis++.so，
#以及生成的两个可执行程序放到
