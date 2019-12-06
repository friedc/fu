#!/bin/sh
# -*- coding: utf-8
#
#-----------
# module name: orientate_h-o-bond.py
# ----------
# function: Orientate OH to make hydrogen bonds with neighbors
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('orientate_h-o-bond.py',False)
# note: this is an example to use scipy.optimize/minimize
# ----------
#
from scipy.optimize import minimize
import time

def FuncHB(x):
    # set coordinates
    cclst=[]
    for i in range(0,len(x),3):
        cclst.append([x[i],x[i+1],x[i+2]])
    cclst=numpy.array(cclst)
    
    global q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx
    e=fuflib.hb_func(cclst,q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx)
    return e

def FuncHBGrad(x):
    # set coordinates
    cclst=[]
    for i in range(0,len(x),3): cclst.append([x[i],x[i+1],x[i+2]])
    cclst=numpy.array(cclst)
    #
    global q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx,natm
    e,g=fuflib.hb_func_grad(cclst,q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx)    
    # set gradients
    de=[]
    for i in range(natm): 
        de.append(g[i][0]); de.append(g[i][1]); de.append(g[i][2]) 
    return numpy.array(de)

# save ccordinate to recover
fum.SaveCC([])
#
wrk=fum.wrk
tgt=fum.ListTargetAtom()
# charge parameters are groundless! 
qhdic={' O':0.2,' N':0.15,' S':0.1}
qdic={' O':-0.4,' N':-0.3,' S':-0.1}
# force constants for bond and fix atoms, respectively.
kb=1000; kx=2000.0

# find polar hydrogens
atmlst=[]; cc=[]; condic={}; bndlst=[]
q=[]; fixdic={}
bnddic={}; atmdic={}
for i in tgt:
    atom=wrk.mol[i]
    elm=atom.elm
    if elm == ' O': # or elm == ' N' or elm == ' S':
        hx=[]
        for j in atom.conect:
            atomj=wrk.mol[j]
            if atomj.elm != ' H': continue    
            if not atmdic.has_key(j):
                atmlst.append(j); atmdic[j]=len(atmlst)-1
                cc.append(atomj.cc)
                condic[j]=i; q.append(qhdic[elm])
                fixdic[j]=False
                hx.append(j)
            bndlst.append([i,j])
            if not atmdic.has_key(i):
                atmlst.append(i); atmdic[i]=len(atmlst)-1
                cc.append(atom.cc)
                q.append(qdic[elm])
                fixdic[i]=True
        # multiple-hydrogens attaches
        if len(hx) <= 1: continue
        for j in range(len(hx)-1):
            jj=hx[j]
            for k in range(j+1,len(hx)):
                kk=hx[k]
                bndlst.append([jj,kk])
# set 1-3 atoms
for i in condic:
    j=condic[i]
    atomj=wrk.mol[j]
    for k in atomj.conect:
        atomk=wrk.mol[k]
        if k == j: continue
        if atomk.elm == ' H': continue
        if not atmdic.has_key(k):
            atmlst.append(k); atmdic[k]=len(atmlst)-1
            cc.append(atomk.cc)
            if qdic.has_key(atomk.elm): q.append(qdic[atomk.elm])
            else: q.append(0.0)
            fixdic[k]=True
        bndlst.append([j,k])
        bndlst.append([i,k])
        break
# find polar atoms around O-H hydrogen
rmin=1.2; rmax=4.0; cch=[]; cca=[]
for i in range(len(atmlst)):
    if wrk.mol[atmlst[i]].elm == ' H': cch.append(cc[i])
for atom in wrk.mol: cca.append(atom.cc)
npair,iatm,jatm,rij=fuflib.find_contact_atoms0(cca,cch,rmin,rmax,1)
for i in range(npair):
    ii=iatm[i]
    atom=wrk.mol[ii]
    if atom.elm == ' O' or atom.elm == ' N' or atom.elm == ' S':
        if not atmdic.has_key(ii):
            atmlst.append(ii); atmdic[ii]=len(atmlst)-1
            cc.append(atom.cc)
            fixdic[ii]=True; q.append(qdic[atom.elm])
# set ifix and thir coordinates
ifix=[]; ccfix=[]; jfix=[]
for i in atmlst:
    if not fixdic.has_key(i): continue
    if fixdic[i]: 
        ifix.append(atmdic[i]); ccfix.append(wrk.mol[i].cc)

# set ibond, jbnd and rbn
nbnd=len(bndlst); rbnd=[]; ibnd=[]; jbnd=[]
bnddic={}
for i,j in bndlst:
    ib=i*10000+j; jb=j*10000+i
    if bnddic.has_key(ib) or bnddic.has_key(jb): continue    
    cci=wrk.mol[i].cc; ccj=wrk.mol[j].cc
    rij=fulib.Distance(cci,ccj)
    rbnd.append(rij)
    bnddic[ib]=1; bnddic[jb]=1
bnddic={}
for i,j in bndlst:
    ib=i*10000+j; jb=j*10000+i
    if bnddic.has_key(ib) or bnddic.has_key(jb): continue    
    ibnd.append(atmdic[i])
    jbnd.append(atmdic[j])
    bnddic[ib]=1; bnddic[jb]=1
#
natm=len(atmlst)
# initial values of variables
x0=[]
for i in range(len(cc)):
    x0.append(cc[i][0]); x0.append(cc[i][1]); x0.append(cc[i][2])
x0=numpy.array(x0)
# initial energy calculations for debugging
#e=fuflib.hb_func(cc,q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx)
#e,g=fuflib.hb_func_grad(cc,q,ibnd,jbnd,rbnd,ifix,ccfix,kb,kx)
time1=time.clock()
# choice of optimization method
#'Nelder-Mead', 'Powell', 'CG', 'BFGS', 'Newton-CG', 'Anneal', 'L-BFGS-B'
#'TNC', 'COBYLA', 'SLSQP'
method='CG' # for this problem, 'CG' seems faster than 'Newton-CG'
# to see options: optimize.show_options('minimize', method='Anneal')
""" I do not know how to use Anneal method """
optcg = {'maxiter' : None,    # default value.
        'disp' : True, #False, #True,    # non-default value.
        'gtol' :1e-2, #1e-5,    # default value.
        #'norm' : numpy.inf,  # default value.
        'eps' : 1.4901161193847656e-08}  # default value.
optan= {'T0': 1000.0, # initial temperature
         'Tf':1e-8, # final temperature
         #'maxfev': 10000, #max # of function evaluations
         #'maxaccept': 1, # max change to accept
         #'lower': [...], # lower on x
         #'upper': [...], # upper on x
         #'dwell':100  # the number of times to search the space at each temperature
         }
opts=optcg
if method == 'Anneal': opts=optan
result=minimize(FuncHB,x0,jac=FuncHBGrad,method=method,options=opts)

nc=-1
for i in range(0,3*natm,3):
    nc += 1
    ii=atmlst[nc]
    if wrk.mol[ii].elm != ' H': continue
    wrk.mol[ii].cc[0]=result.x[i]
    wrk.mol[ii].cc[1]=result.x[i+1]
    wrk.mol[ii].cc[2]=result.x[i+2]
fum.DrawMol(True)

#print result.message
time2=time.clock()
dtime=time2-time1
dtime=int(dtime)
print 'elasped time (sec): ',method,dtime
print ' time in min.',dtime/60.0

