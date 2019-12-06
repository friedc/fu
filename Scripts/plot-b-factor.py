#!/bin/sh
# -*- coding: utf-8 -*- 
#
#-----------
# module name: plot-b-factor.py
# ----------
# function: Open MatPlotLib_Frm, plot B factors in PDB data and select atoms with large value
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('plot_b_factor.py',False)
#        Click "Select" button on toolbar to select atoms having a large B-factor value 
#        When a peak is clicked in the graph, the corresponding atom is selected in molecular model.
# note: execute this script before hydrogen additions (before any change in pdb structure data)
# ----------
#

import sys
sys.path.insert(0,'.//Scripts') #h://workspace//fu-v0.20-Jun')
import subwin
import molec
import rwfile

global atmnmb,bfc
    
def MakeBFC():
    # read pdb file; does not work since atmnmb is changed in FU.
    pdbfile=fum.mol.inpfile
    pdbmol,fuoptdic=rwfile.ReadPDBMol(pdbfile)
    atmnam=pdbmol[2]; atmnmb=pdbmol[3]; bfc=pdbmol[10]
    pdbatmdic={}
    for i in range(len(atmnam)):
        if atmnam[i] == "    ": continue
        try:
            atm=atmnam[i]+':'+str(atmnmb[i])
        except:
            print 'i,atmnam[i],atmnmb[i]',i,atmnam[i],atmnmb[i]
            continue
        pdbatmdic[atm]=bfc[i]
    #print 'pdbatmdic',pdbatmdic
    
    for atom in fum.mol.atm:
        wrkatm=atom.atmnam+':'+str(atom.atmnmb)
        if pdbatmdic.has_key(wrkatm): atom.bfc=pdbatmdic[wrkatm]
        else: atom.bfc=0.0

def SetAtmPrp():
    for atom in fum.mol.atm:
        atom.atmprp=atom.bfc    

def PlotData():
    atmnmb=[]; bfc=[]
    for atom in fum.mol.atm:
        atmnmb.append(atom.seqnmb+1) 
        bfc.append(atom.bfc)
    #
    pltbfc.SetGraphType("bar")
    pltbfc.SetColor("r")
    #
    pltbfc.NewPlot()
    pltbfc.PlotXY(atmnmb,bfc)
    pltbfc.PlotXLabel('Sequence number of atom')
    pltbfc.PlotYLabel('Arbitary unit')

pltbfc=subwin.PlotAndSelectAtoms(fum.mdlwin,-1,fum,"plot-b-factor","atom")
pltbfc.SetInput(">20")
SetAtmPrp()
MakeBFC()
PlotData()