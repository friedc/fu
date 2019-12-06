#!/bin/sh
# -*- coding: utf-8
#
#-----------
# module name: draw_pmi_vector.py
# ----------
# function: Draw principal moment inertia vectors
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('draw_pmi_vector.py',True)
#        For removing the arrows,
#        >>> fum.frame.view.SetDrawArrowList(False,[])
#        >>> fum.DrawMol(True)
# Note: This script describes how to draw arrows in molecular model view canvas.
# ----------
#
natm=0
try: natm=len(fum.mol.atm)
except: pass
sc=2.0 # scale factor for vector length
thick=2 # stick thickness
label='pmi-vector'
if natm > 0:
    if fum.scriptcheck:
        com,eig,vec=fum.mol.CenterOfMass() #fulib.CenterOfMassAndPMI(atmmas,coord)
        p1=vec[0]; p2=vec[1]; p3=vec[2]
        print 'Principal moment of inertia: eigenvalues and eigenvectors'
        print '[0](red)    ',eig[0],p1
        print '[1](yellow) ',eig[1],p2
        print '[2](cyan)   ',eig[2],p3
        maxv=max(eig)
        fc=sc/maxv; fc1=fc*eig[0]; fc2=fc*eig[1]; fc3=fc*eig[2]
        p0=com; p1=fc1*p1+p0; p2=fc2*p2+p0; p3=fc3*p3+p0 
        color1=[1.0,0.0,0.0,1.0] # red
        color2=[1.0,1.0,0.0,1.0] # yellow
        color3=[0.0,1.0,1.0,1.0] # cyan
        head=0.3
        #
        fum.mdlwin.draw.arrowhead=0.3 # arrow head length ratio (default=0.25)
        arrow=[[p0,p1,color1,thick,0.3],[p0,p2,color2,thick,0.3],[p0,p3,color3,thick,0.3]]
        fum.mdlwin.draw.SetDrawData(label,'ARROW',arrow)
    else:
        fum.mdlwin.draw.DelDrawData(label)
    
    fum.DrawMol(True)
