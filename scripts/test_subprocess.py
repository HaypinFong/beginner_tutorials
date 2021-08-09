#!/usr/bin/env python
#-*- coding:utf-8 -*-
import subprocess
if __name__ == '__main__':
    subp = subprocess.run(args='cd /heihei')
    if subp.wait()!=0:
        print('heiehi')