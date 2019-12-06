#!/bin/sh
# -*- coding: utf-8 -*- 

#
#-----------
# module name: change-atom-order-in-wat.py
# ----------
# function: Change atom order from H1-O-H2 to O-H1-H2
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('change-atom-order-in-HOH.py',False)
# ----------
#
import copy

wrk=fum.wrk
natm=len(wrk.mol); i=0; nchange=0
while i <= natm-3:
    if wrk.mol[i].resnam == 'HOH' or 'WAT' or 'H2O':
        o=-1; h1=-1; h2=-1
        for j in range(i,i+3): 
            if wrk.mol[j].elm == ' O' and o < 0: o=j
            elif wrk.mol[j].elm == ' H' and h1 < 0: h1=j
            elif wrk.mol[j].elm == ' H' and h2 < 0: h2=j
        if o > 0 and o != i:
            nchange += 1
            atomo=copy.deepcopy(wrk.mol[o])
            atomh1=copy.deepcopy(wrk.mol[h1])
            atomh2=copy.deepcopy(wrk.mol[h2])
            #
            wrk.mol[i]=atomo; wrk.mol[i].seqnmb=i
            wrk.mol[i+1]=atomh1; wrk.mol[i+1].seqnmb=i+1
            wrk.mol[i+2]=atomh2; wrk.mol[i+2].seqnmb=i+2
            
        i += 3
    else: i += 1
print 'nchange',nchange