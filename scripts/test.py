#!/usr/bin/env python2
#-*- coding:utf-8 -*-
import math
import numpy as np

class SubType:
    def meth1(self,str):
        print(str)
    def meth2(self,arg1):
        return func1(self.meth1,arg1)   #引用self.meth1已经隐式绑定了self实例,表示

def func1(handle,*args):
    return handle(args)

def linefit(x , y):
    # ax + by + c = 0
    #y=ax+b
    reverse = False
    th = math.atan2(y[-1]-y[0], x[-1]-x[0])
    if abs(th - math.pi/2) < math.pi/6:
        reverse = True
        x,y = y,x
    N = float(len(x))
    sx,sy,sxx,syy,sxy=0,0,0,0,0
    x,y = np.array(x), np.array(y)
    sx = x.sum()
    sy = y.sum()
    sxx = (x*x).sum()
    syy = (y*y).sum()
    sxy = (x*y).sum()
    a = (sy*sx/N -sxy)/( sx*sx/N -sxx)
    b = (sy - a*sx)/N
    return (a,b)
if __name__ == "__main__":
    ins = SubType()
    ins.meth2("heihei")
    x=[1,2,3,4,5]
    y=[3,5,7,9,11]
    print(linefit(x,y))
    