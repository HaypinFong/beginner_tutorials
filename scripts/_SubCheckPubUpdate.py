#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
import rospy
from beginner_tutorials.msg import Str	#自定义消息类型
import os
import re


def updateTactic(yamlpathstr,launchpathstr):
    yamlpath=os.path.abspath(yamlpathstr)
    recordFileName=yamlpath+"/MD5_orders.txt"
    launchpath=os.path.abspath(launchpathstr)
    launchFileName=launchpath+"/load.launch"
    # print(yamlpath)
    #如果更新了load.launch则需要发布一个"load.launch_update"的话题，
    #由其它节点订阅后决定重启ROS
    yamls=[]
    # temp=os.listdir(yamlpath)
    rexEle=re.compile("\d{3}.*\.yaml")
    for ifile in os.listdir(yamlpath):
        if ifile.endswith(".yaml") and rexEle.match(ifile):    #正则表达式确定yaml文件名样式[::num::][A-Z]\.yaml
            yamls.append(ifile)
    if len(yamls)<=0:   #yaml目录下没有有效.yaml文件
        return False
    # for iyaml in yamls:
    #     print(iyaml+"\t")
    # print("\n")

    #将001file1.yaml、002file2.yaml、003file3.yaml配置文件的MD5记录到MD5.txt
    #内容是:    其中配置文件的顺序由003C.yaml的前面"003"确定，
    #当文件名"00xfile3.yaml"前缀"00x"改变不会改变file3.yaml文件的MD5，但会改变顺序
    #确认文件内容不会改变，那只用记录文件顺序就好了
    '''
    file1
    file2
    file3
    '''
    #对yamls列表中文件名按[::num::]字符串部分转数字后排序
    def SortByNamePrefix(filename1,filename2):
        regexEle=re.compile("\d{3}")
        numstr1=regexEle.search(filename1)
        numstr2=regexEle.search(filename2)
        if numstr1==None:
            print("warning:策略配置文件"+filename1+"没有以'003'样式指定覆盖顺序，将当作最低优先级处理！\n")
        if numstr2==None:
            print("warning:策略配置文件"+filename2+"没有以'003'样式指定覆盖顺序，将当作最低优先级处理！\n")
        if numstr1!=None and numstr2!=None:
            num1=int(numstr1.group(),base=10)
            num2=int(numstr2.group(),base=10)
            return num1-num2
        elif numstr1!=None and numstr2==None:
            return 1
        elif numstr1==None and numstr2!=None:
            return -1
        else:
            return 1


    def WriteOrders(recordFilename,fileOrderCur,mapFullName,launchpathstr):
        with open(recordFileName,"w") as fileh:
            fileh.writelines("")
        with open(launchFileName,"w") as fileh2:
            fileh2.writelines("")
        with open(recordFileName,"a") as fileh:
            #重生成load.launch的include行，不是替换
            with open(launchpathstr,"a") as fileh2:
                fileh2.write("<launch>\n")
                #写orders，
                for iline in fileOrderCur:
                    fileh.write(iline+"\n")
                    fileh2.write("     <include file=\""+launchpathstr+"/"+mapFullName[iline]+"\"/>\n")
                fileh2.write("</launch>\n")
        return


    yamls.sort(cmp=SortByNamePrefix)
    fileOrderCur=[]     #精简文件名"011file3.yaml"为"file3.yaml"，精简后的文件名不变，
    mapFullName={"filenamePart":"filenameFull"} #精简文件名file1.yaml映射实际文件名0xxfile1.yaml
    regexEle=re.compile("\d{3}")
    for ifile in yamls:
        numstr=regexEle.search(ifile)
        if numstr==None:
            fileOrderCur.append(ifile)
            mapFullName[ifile]=ifile
        else:
            strprefix=numstr.group()
            istart=ifile.find(strprefix)
            strremain=ifile[istart+len(strprefix):]
            fileOrderCur.append(strremain)
            mapFullName[strremain]=ifile

    
    if os.path.isfile(recordFileName):
        #比较MD5_orders.txt中各配置文件的MD5与实际目录下文件的MD5,不要了

        #读取记录文件中记录的filex.yaml顺序
        fileOrderOld=[]
        with open(recordFileName,"r") as fileh:
            fileOrderOld=fileh.readlines()
        fileOrderOld2=[]
        for iline in fileOrderOld:
            stripNL=iline.replace("\n","")  #换行
            fileOrderOld2.append(stripNL)
        fileOrderOld=fileOrderOld2
            
        #比较MD5_orders.txt中有效文件名部分的顺序与fileorder列表顺序
        #若一致则退出，否则覆盖MD5_orders.txt中顺序并重生成load.launch
        if len(fileOrderOld)<=0 or len(fileOrderCur)<=0 or len(fileOrderOld)!=len(fileOrderCur):
            #增加或减少yaml配置文件？按当前yaml配置文件及顺序
            WriteOrders(recordFileName,fileOrderCur,mapFullName,launchFileName)
            return True
        bChanged=False
        for i in range(len(fileOrderOld)):
            if(fileOrderOld[i]!=fileOrderCur[i]):
                bChanged=True
                break
        if bChanged:
            WriteOrders(recordFileName,fileOrderCur,mapFullName,launchFileName)
            return True	#表示xxxfilex.yaml顺序确有发生改变,更新了策略
    else:
        WriteOrders(recordFileName,fileOrderCur,mapFullName,launchFileName)
	return False	#表示初始化


def callback(Strobj):
    rexEle = re.compile('check')
    if rexEle.search(Strobj.str):
        # rospy.loginfo("subApubB sub check topic, will check filename")
        try:
            pub = rospy.Publisher('~updateTactic',Str)   #定义发布者
            #'updateTactic'话题
            # rospy.init_node('tacticPub',anonymous=True)
            #rate = rospy.Rate(0.003)	#3次1000秒，1次300秒合5分钟
            yamlpath = "/home/haypin/pytest/yamldir"
            launchpath = "/home/haypin/pytest/launchdir"
            strmsg = rospy.get_caller_id()+" check and compute "
            if updateTactic(yamlpath,launchpath):
                strmsg += "tacticChanged"
            else:
                strmsg += "stay former load.launch"
            rospy.loginfo(strmsg) #往rospy节点记录信息
            #rospy.get_caller_id()返回当前节点的完整解析的节点名
            pub.publish(strmsg) #发布话题，一次
        except rospy.ROSInterruptException:
            pass
    else:
        rospy.loginfo(rospy.get_caller_id()+"will do nothing")

if __name__=="__main__":
    '''yamlpath、launchpath存储在参数服务器中由roscore或其他先启节点
    以话题的方式发布到当前节点？
    '''
    rospy.init_node('nodeB',anonymous=False)
    rospy.Subscriber('/nodeA/check',Str,callback)   #定义订阅者
    rospy.spin()




