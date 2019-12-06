#!/bin/sh
# -*- coding: utf-8
#
#-----------
# scripyt: transfer-atoms.py
# ----------
# function: transfer atoms from reference molecule
# usage: This script is executed in PyShell window.
#        >>> fum.fum.ExecuteAddOnScript('transfer-atoms.py',False)
# note: RMS fit between target(molecule read by "File"-"Open") and reference 
#       molecule and some atoms in the reference are transfered
#       to target molecule
# ----------
# change history
# modified for fu ver.0.4.0 06Feb2016
# the first version for fu ver.0.0.0 23Del2015
# -----------
import build
#import rwfile
norun=False
                            
# main program
trswin=build.TransferAtoms_Frm(fum.mdlwin,-1)
if norun: trswin.Destroy()
else: 
    try: trswin.Show()
    except: pass
