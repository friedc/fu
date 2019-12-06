#!/bin/sh
# -*- coding: utf-8
#
#-----------
# scripyt: rms-fit.py
# ----------
# function: rms fits two structures
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('rms-fit.py',False)
# note: RMS fit between target(molecule read by "File"-"Open") and reference 
#       molecule 
# ----------
# change history
# modified for fu ver.0.4.0 06Feb2016
# the first version for fu ver.0.0.0 23Del2015
# -----------
import build
#import rwfile
norun=False
                            
# main program
rmswin=build.RMSFitting_Frm(fum.mdlwin,-1)
if norun: rmswin.Destroy()
else: 
    try: rmswin.Show()
    except: pass
