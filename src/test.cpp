#include <iostream>
#include <sstream>
#include <string>
#include <cmath>
namespace myns{
struct SubType{
    typedef std::string Strtype;    //类型属性，类型字段，相当于类静态字段，只是不用显示初始化，类型也是一种属性
    static std::string field1;      //类静态字段，需要在全局作用域显式初始化
};
std::string SubType::field1("aloha");   //名字空间不算作用域，全局作用域的名字空间仍然是全局作用域，只是对名字访问加名字空间约束
typedef SubType MyType;
}
// std::string myns::MyType::field1("haha");
int main(int argc,char *argv[]){

    std::stringstream ss;
    ss<<"heihei"<<9;
    std::cout<<ss.str()<<"\n";

    ::myns::MyType::Strtype str("heihei");      //访问类的类型属性
    std::cout<<str<<"\n";
    std::cout<<::myns::MyType::field1<<"\n";    //访问类静态字段

    std::cout<<sizeof(-5.9)<<std::endl;    //将输出8，也就是8字节的double
    std::cout<<sizeof(float(-5.9))<<"\n";   //4
    std::cout<<sizeof(double(-5.9))<<"\n";  //8

    std::cout<<std::isnan(3.14)<<"\n";  //0

    long long t(-1);
    std::cout<<sizeof(t)<<"\n"; //8
    double d = *(double*)&t;
    std::cout<<d<<"\n";     //-nan
    long long t2(1);
    double d2 = *(double*)&t2;
    std::cout<<d2<<"\n";    //4.94066e-324
}