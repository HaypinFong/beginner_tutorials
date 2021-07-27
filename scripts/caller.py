#!/usr/bin/env python2
#-*- coding:utf-8 -*-
'''
1、输入行分隔的编号；
2、访问url，提取version和level字段值
3、输出"编号——version——紧急"行分隔结果
'''
import sys
import re
import requests
import json
import os
def ReadTXT(infile):
    '''
    读取文本返回行分隔编号
    '''
    numlist=[]
    # path = os.path.abspath(infile)
    # reg = re.compile  #不用过滤文本了，直接空格分隔
    nline = 0
    if os.path.isfile(infile):
        with open(infile,"r") as fileh:
            lines = fileh.readlines()
        for iline in lines:
            nline+=1
            strlist = iline.split(' ')
            if len(strlist)<=0:
                print("输入文件的第%s行文本无效，将跳过".format(nline))
                continue
            #是否检测strlist[0]是否有效，正则表达式?
            numlist.append(strlist[0])
            
        return numlist
    else:
        print("输入txt文件名不正确或不存在!\n")
        return

def CallURL(url):
    '''
    request爬取url的HTML文本，提取"version"和"level"字段值返回
    '''
    version=''
    level=''
    res = requests.get(url)
    ele = json.loads(res.text)
    version = ele['data']['version']
    level = ele['data']['level']
    return (version,level)

    
    return (version,level)
def WriteRes(outfile,outlines):
    with open(outfile,'w') as fileh:
        # fileh.
        pass
    with open(outfile,'a') as fileh:
        for iline in outlines:
            fileh.write(iline)
    return

if __name__ == "__main__":
    # if len(sys.argv)<=1:
    #     print("请输入包含编号的txt文件名！\n")
    #     sys.exit(1)
    infile = sys.argv[1]

    reload(sys)
    sys.setdefaultencoding( "utf-8" )
    
    numlist = ReadTXT(infile)
    outlines=[]
    pre = 'https://api.yunjichina.com.cn/api/v2/robot/update/version?productId='
    for inum in numlist:
        version,level = CallURL(pre+str(inum))
        # url = pre+str(inum)
        # version=''
        # level=''
        # res = requests.get(url)
        # ele = json.loads(res.text)
        # version = ele['data']['version']
        # level = ele['data']['level']
        outlines.append('%s %s %s\n'%(inum,version,level))
    WriteRes("./out.txt",outlines)
    print("来自%s的所有编号都已爬取完毕并输出至当前目录的%s"%(infile,"out.txt"))
