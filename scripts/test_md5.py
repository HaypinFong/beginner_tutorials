#!/usr/bin/env python
#-*- coding: utf-8 -*-
import hashlib
if __name__ == '__main__':
    with open('./PubYamlOrderC2.py','rb') as fh:
        data = fh.read()
        MD = hashlib.md5(data).hexdigest()
        print(MD)