#!/bin/sh
# -*- coding: utf-8
#
#-----------
# module name: short-contact-atoms.py
# ----------
# function: Select short contacted atoms
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('short_contact_atoms.py',False)
# ----------
#
import lib
try: import fortlib
except: pass
import numpy

mol=fum.mol
rmin=0.0; rmax=0.85; iopt=1
cc=[]
lst=fum.ListTargetAtoms()
index=[]
for i in lst:
    atom=mol.atm[i]
    if atom.elm == 'XX': continue
    cc.append(atom.cc); index.append(i)
npair,iatm,jatm,rij=fortlib.find_contact_atoms2(cc,rmin,rmax,iopt)

print 'mol=',fum.mol.name
if npair <= 0:
    print 'There is no short contacted atoms.'
else:
    print 'There are '+str(npair)+' short contacted atom pairs.'
    for i in range(npair):
        print str(i+1)+": ",index[iatm[i]]+1,index[jatm[i]]+1,numpy.sqrt(rij[i])
    fum.SetSelectAll(False)
    for i in range(npair):
        ii=index[iatm[i]]
        #fum.SetSelectedAtom(ii,True)
        mol.atm[ii].select=True
    for i in range(npair):
        ii=index[jatm[i]]
        #fum.SetSelectedAtom(ii,True)
        mol.atm[ii].select=True
    fum.DrawMol(True)
    

