#!/bin/sh
# -*- coding: utf-8
#
#-----------
# module name: flatten_mol.py
# ----------
# function: Project molecular structure on nearly a plane
# usage: This script is executed in PyCrust shell.
#        >>> fum.ExecuteScript('flatten_mol.py',False)
#        to recover the original coordinates, execute 
#        "Change"-"Recover coordinates" menu or
#        >>> fum.RecoverCC()
#        in PyCrust console.
# note: this is an example to use sciypy.optimize/minimize method
# ----------
import numpy
import lib
import fortlib
#from scipy.optimize import fmin_bfgs, fmin_cg, check_grad
from scipy.optimize import minimize
import time

def Func2DProj(x):
    #print 'x',x
    cclst=[]
    for i in range(0,len(x),3):
        cclst.append([x[i],x[i+1],x[i+2]])
    
    global ibnd,jbnd,rbnd,ifix,ccfix,kb,kn,kl,kz,kf
    val=fortlib.flatten_func(cclst,ibnd,jbnd,rbnd,ifix,ccfix,
                                kb,kn,kl,kz,kf)    
    return val

def DerFunc2DProj(x):
    cclst=[]
    for i in range(0,len(x),3):
        cclst.append([x[i],x[i+1],x[i+2]])
    global ibnd,jbnd,rbnd,ifix,ccfix,kb,kn,kl,kz,kf
    val,g=fortlib.flatten_func_grad(cclst,ibnd,jbnd,rbnd,ifix,ccfix,
                                kb,kn,kl,kz,kf)        
    de=[]
    for i in range(len(cclst)):
        de.append(g[i][0]); de.append(g[i][1]); de.append(g[i][2])
    return numpy.array(de)
    
def PotFunc2DProj(cclst,bnddic,kb,kn,kl,kz):
    g=[]#; kb=50.0; kz=0.1; kn=5.0
    kb2=2.0*kb; kz2=2.0*kz; kn12=12.0*kn
    e=0.0; er=0.0

    n=len(cclst)
    for i in range(n): g.append([0.0,0.0,0.0])
    
    for i in range(n):
        xi=cclst[i][0]; yi=cclst[i][1]; zi=cclst[i][2]

        e += kz*zi**2 # kz*(z-z0)**2, z0=0.0
        for j in range(i+1,n):
            ij=i*10000+j
            r=lib.Distance(cclst[i],cclst[j])   

            if bnddic.has_key(ij):
                r0=bnddic[ij]; dr=r-r0
                e += kb*dr**2
            else:        
                
                e += kn/r**4
                e += kl/r**2
                er += kn/r**4
                er += kl/r**2
    return e,g

def DerPotFunc2DProj(cclst,bnddic,kb,kn,kl,kz):
    #e=0.0; g=[]; kb=5000.0; kz=100.0; kn=100.0
    g=[]#; kb=50.0; kz=0.1; kn=5.0
    kb2=2.0*kb; kz2=2.0*kz; kn12=12.0*kn
    e=0.0; er=0.0
    
    n=len(cclst)
    for i in range(n): g.append([0.0,0.0,0.0])
    
    for i in range(n):
        xi=cclst[i][0]; yi=cclst[i][1]; zi=cclst[i][2]
        e += kz*zi**2 # kz*(z-z0)**2, z0=0.0
        gz=kz2*zi
        g[i][2] += gz
        for j in range(i+1,n):
            ij=i*10000+j
            r=lib.Distance(cclst[i],cclst[j])   
            dx=(xi-cclst[j][0])/r; dy=(yi-cclst[j][1])/r; dz=(zi-cclst[j][2])/r
            
            if bnddic.has_key(ij):
                dr=r-bnddic[ij] # r-r0
                e += kb*dr**2
                fc=kb2*dr
                gx=fc*dx; gy=fc*dy; gz=fc*dz
            else:        
                #gx=0.0; gy=0.0; gz=0.0
                rm4=1.0/r**4          
                e += kn*rm4
                e += kl/r**2                
                fc4=-4.0*kn*rm4/r
                fc1=-2.0*kl/r**3
                fc=fc4+fc1
                gx=fc*dx; gy=fc*dy; gz=fc*dz

            g[i][0] += gx; g[i][1] += gy; g[i][2] += gz
            g[j][0] -= gx; g[j][1] -= gy; g[j][2] -= gz 
    de=[]
    for i in range(len(cclst)):
        de.append(g[i][0]); de.append(g[i][1]); de.append(g[i][2])
    
    return e,g
    
def MakeBnddicAndCClst():
    #tgt=fum.ListTargetAtom()
    bnddic={}; cclst=[]; idxlst=[]

    for atom in fum.mol.atm:
        i=atom.seqnmb
        cc=[atom.cc[0],atom.cc[1],atom.cc[2]]
        cclst.append(cc)
        idxlst.append(atom.seqnmb)
        # covalent bonds
        for j in atom.conect:
            if j > i:
                atomj=fum.mol.atm[j]
                ij=i*10000+j
                ccj=atomj.cc #fum.wrk.mol[j].cc  
                rij=lib.Distance(cc,ccj)
                bnddic[ij]=rij 
                """ #1-3 distance constraint. this prevents to make fallten!
                if atomj.elm == ' H': continue
                for k in atomj.conect:
                    if k == j: continue
                    atomk=fum.wrk.mol[k]
                    if atomk.elm == ' H': continue
                    jk=j*10000+k
                    if bnddic.has_key(jk): continue
                    cck=atomk.cc  
                    rjk=fufortlib.Distance(ccj,cck)
                    bnddic[jk]=rjk
                """ 
        # extrabonds
        for j in atom.extraconect:
            if j > i:
                #print 'i,j',i,j
                ij=i*10000+j
                ccj=fum.mol.atm[j].cc  
                rij=lib.Distance(cc,ccj)
                bnddic[ij]=rij 

    return bnddic,cclst

# copy wrk.mol for recovery
ans=lib.IsMoleculeObj(fum.mol)
if not ans: exit()

fum.SaveMol()

time1=time.clock()

bnddic,cclst=MakeBnddicAndCClst()
cclst=numpy.array(cclst)
#
ibnd=[]; jbnd=[]; rbnd=[]
for ij in bnddic:
    i=ij/10000; j=ij-i*10000; rij=bnddic[ij]
    ibnd.append(i+1); jbnd.append(j+1); rbnd.append(rij)
rbnd=numpy.array(rbnd)

x0=[]
for i in range(len(cclst)):
    for j in range(len(cclst[i])):
        x0.append(cclst[i][j])
#
x0=numpy.array(x0)
#var=minimize(Func,x0,method='BFGS',fprime=DerFunc,options={'disp':True})
#var=minimize(Func,x0,method='nelder-mead',
#!!scipy.optimize.fmin_bfgs(f, x0, fprime=None, args=(), gtol=1e-05, norm=inf, epsilon=1.4901161193847656e-08, maxiter=None, full_output=0, disp=1, retall=0, callback=None)
#http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.fmin_bfgs.html
kb=50.0; kn=10.0; kl=50.0; kz=0.0; kf=0.0
ifix=[0]; ccfix=[[0.0,0.0,0.0]]; nfix=1; kf=5000.0

nvar=30*len(cclst)
#result=fmin_bfgs(Func2DProj,x0,fprime=DerFunc2DProj,gtol=1e-05,maxiter=nvar)
# minimize method=
# http://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
#'Nelder-Mead', 'Powell', 'CG', 'BFGS', 'Newton-CG', 'Anneal', 'L-BFGS-B'
#'TNC', 'COBYLA', 'SLSQP'
#jac : bool or callable, optional
#Only for CG, BFGS, Newton-CG
method='L-BFGS-B'
opts = {'maxiter' : nvar, #None,    # default value.
        'disp' : False, #True,    # non-default value.
        'gtol' : 1e-2,    # default value.
        #'norm' : numpy.inf,  # default value.
        'eps' : 1.4901161193847656e-08}  # default value.
result=minimize(Func2DProj,x0,jac=DerFunc2DProj,method=method,options=opts)

# timming for fk506(126 atoms)
# CG: 8 sec, 1crn: 435 sec(7.25min), (1,642 fix): 606 sec(10.1min)
# BFGS: 13 sec
# Newton-CG: too slow!
# L=BFGS-B: 1 sec. firstest! 1crn(642 atom2): 30 sec, fkbp(1666 atoms:878 sec, 14.6 min
# 1crn 1,642 fix 228 sec(4.8min)
#
#res=fmin_cg(Func2DProj,x0,fprime=DerFunc2DProj,gtol=1e-05,maxiter=nvar)  

nc=-1
for i in range(0,len(result.x),3):
    nc += 1
    fum.mol.atm[nc].cc[0]=result.x[i]
    fum.mol.atm[nc].cc[1]=result.x[i+1]
    fum.mol.atm[nc].cc[2]=result.x[i+2]
fum.DrawMol(True)

time2=time.clock()
dtime=time2-time1
dtime=int(dtime)
print 'elasped time (sec): ',method,dtime
print ' time in min.',dtime/60.0

