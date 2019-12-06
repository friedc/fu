#!/bin/sh
# -*- coding: utf-8

Version="FU ver.0.4.0"
Copyright="Copyright (c) 2013-15, FU User Group. All rights reserved."
License="The BSD 2-Clause License" # http://opensource.org/licenses/BSD-2-Clause).
Contributors="FU User Group"
Acknowledgement="The development of this software is partially supported by CMSI (2013-14)"

import sys
sys.path.insert(0,'.')
sys.path.insert(0,'./Source')
import os
import wx

import fumodel

def start():
    app=wx.App(False)
    global fum # Create Model instance
    srcpath=os.getcwd() # source path
    #
    parent=None; mode=0
    fum=fumodel.Model_Frm(parent,srcpath,mode)
    parent=fum
    fum.OpenMdlWin(parent)
    #
    app.MainLoop()

#----------------------------------------    
if __name__ == '__main__':
    start()
    
