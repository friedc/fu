#!/bin/sh
# -*- coding: utf-8
#
#-----------
# script: draw-cube-data.py
# ----------
# function: draws cube data
# usage: This script is executed in PyShell
#        >>> fum.ExecuteAddOnScript('draw-cube-data.py')
# note: the script is a part of "fuplot" script
# change history
# the first version: 19Sep2015

# ----------
import cube
import lib
#------

"""  This script is a programming tutorial to use the DrawCubeData_Frm class in cube module.
"""
print 'Opened DrawCubeDataPanel(draw-cube-data.py): ',lib.DateTimeText()
mode=0 # with menu mode
model=fum
mdlwin=fum.mdlwin
#
winsize=lib.MiniWinSize([100,365]) #([100,355])
ctrlflag=None
mdlwinpos=mdlwin.GetPosition()
mdlwinsize=mdlwin.GetSize()
winpos=[mdlwinpos[0]+mdlwinsize[0],mdlwinpos[1]+40]
if mode == 1: winsize[1] -= 25 # no menu in the case of mode=1
#
cubewin=cube.DrawCubeData_Frm(mdlwin,-1,winpos,winsize,model,None,mode) # mode=1
cubewin.Show()
