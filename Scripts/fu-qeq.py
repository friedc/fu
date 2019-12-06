#!/bin/sh
# -*- coding: utf-8 -*- 
#
#-----------
# Script: qeq.py
# ----------
# function: charge eqibration method
# usage: This script is executed in fu-PyShell shell.
#        >>> fum.ExecuteAddOnScript('qeq.py',False)
# change history
# Dec2015 - the first version
#
import time
#import numpy
from scipy import linalg
import const
import rwfile
try: import fortlib
except: pass 

class QEq():
    def __init__(self,title,charge=0,xyzfile='',prmfile='',outfile=''):
        """ Charge equilibration method:
            A. K. Pappe and W. A. Goddard III, J.Phys.Chem.,3358(1991).   
            modified to use NM-gamma for electron-electron repulsion:
            T.Nakano,T.Kaminuma,M.Uebayasi,Y.Nakata, Chem-Bio Info.J.,1,35(2001).
       
        :param str title: title
        :param float charge: total charge of molecule
        :param lst xyzatm: [[elm(str*2),x(float),y(float),z(float)],...]
        """
        #
        prmfile='E://FUDATASET//FUdata//qeq.prm'
        #xyzfile='F://winfort//mqeq//1crnhadd.xyz'
        #outfile='F://winfort//mqeq//1crnhadd.chg'
        xyzfile='E://FUDATASET//FUdocs//data//c2h5oh.xyz'
        outfile='E://FUDATASET//FUdocs//data//c2h5oh.chg'
        
        self.prgnam='fu-qeq ver.0.1'
        self.xyzfile=xyzfile
        self.coordfile=xyzfile
        self.outfile=outfile
        
        self.charge=charge
        self.scale=1.0
        self.prmdic=rwfile.ReadQEqParams(prmfile)
        
        self.xyzatm,bonds,resfrg=rwfile.ReadXYZMol(xyzfile)
        self.natm=len(self.xyzatm)
        self.elm=self.CheckParams()       
        self.resnam=lib.MakeMolNamFromFileName(self.coordfile)
        self.resnam=self.resnam.upper()
        
        self.time1=time.clock()
        self.distlst=self.ComputeDistance()
        self.q=self.SolveQEqEq()
        self.time2=time.clock()
        
        self.WriteResults()
        self.WriteFile(self.outfile)
        const.CONSOLEMESSAGE('partial charges were saved on file='+self.outfile)
            
    def CheckParams(self):
        an=[]
        for i in range(self.natm):
            elm=self.xyzatm[i][0]
            if not self.prmdic.has_key(elm):
                mess='Not found QEq parameter for element='+elm+'\n'
                mess=mess+'Define the parameter in the "FUDATASET//FUdata//qeq.prm" file.'
                lib.MessageBoxOK(mess,'QEq(CheckParams')
                self.Quit()
            an.append(elm)
        return an
         
    def SolveQEqEq(self):
        f=0.529917724*27.2113845 # =14.42 bohr*au2ev
        #
        b=self.natm*[0.0]
        b[0]=self.charge
        an0=self.elm[0]
        chi0=self.prmdic[an0][0]
        for i in range(1,self.natm):
            ani=self.elm[i]
            b[i]=self.prmdic[ani][0]-chi0
        #
        a=[]
        a.append(self.natm*[1.0])
        lst=self.natm*[0.0]
        for i in range(1,self.natm): a.append(lst[:])
        j0=self.prmdic[an0][1]
        for i in range(1,self.natm):
            ani=self.elm[i]; ji=self.prmdic[ani][1]
            for j in range(self.natm):
                anj=self.elm[j]
                jj=self.prmdic[anj][1]
                r0j=self.distlst[0][j]
                rij=self.distlst[j][i]
                # g: NM-gamma
                d0j=2.0*f/(j0+jj); g0j=f/(r0j+d0j)
                dij=2.0*f/(ji+jj); gij=f/(rij+dij)
                a[i][j]=g0j-gij
        # solve simultaneous linear equation 
        a=numpy.array(a); b=numpy.array(b)
        #q=numpy.linalg.solve(a,b)
        q=linalg.solve(a,b)
        return q
        
    def ComputeDistance(self):
        distlst=[]; lst=self.natm*[0.0]
        for i in range(self.natm): distlst.append(lst[:])
        #
        try:
            cc=[]; k=-1
            for i in range(self.natm): 
                cc.append([self.xyzatm[i][1],self.xyzatm[i][2],self.xyzatm[i][3]])
            cc=numpy.array(cc)
            rij=fortlib.distance(cc,0)
            for i in range(self.natm-1):
                for j in range(i+1,self.natm):
                    k += 1
                    distlst[i][j]=rij[k]; distlst[j][i]=rij[k]
        except:
            const.CONSOLEMESSAGE('Running Python code ...')
            for i in range(1,self.natm):
                xi=self.xyzatm[i][1]; yi=self.xyzatm[i][2]; zi=self.xyzatm[i][3]
                for j in range(i):
                    xj=self.xyzatm[j][1]; yj=self.xyzatm[j][2]; zj=self.xyzatm[j][3]
                    r=numpy.sqrt((xi-xj)**2+(yi-yj)**2+(zi-zj)**2)
                    distlst[i][j]=r; distlst[j][i]=r
        return distlst
    
    def XXReadQEqParams(self,prmfile):
        if not os.path.exists(prmfile):
            mess='Not found QEq parameter file='+prmfile
            lib.MessageBoxOK(mess,'QEq(ReadQEqParams)')
            self.Quit()
        prmdic={}; resnam=''; charge=0.0; scale=1.0
        f=open(prmfile,'r')
        for s in f.readlines():
            ns=s.find('#')
            if ns >= 0: s=s[:ns]
            s=s.strip()
            if len(s) <= 0: continue
            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3: continue
            ian=int(items[0]); chi=float(items[1]); j=float(items[2])
            prmdic[ian]=[chi,j]
        f.close()
        return prmdic
        
    def DipoleMoment(self):
        debbohr=2.541747761/0.529917724 # debye/bohr
        mu=[0.0,0.0,0.0]
        cntr=[0.0,0.0,0.0]; chg=self.charge
        if self.charge != 0.0:
            for i in range(3):
                for j in range(self.natm):
                    cntr[i] += self.q[j]*self.xyzatm[j][i+1]
            cntr[0]=cntr[0]/chg; cntr[1]=cntr[1]/chg; cntr[2]=cntr[2]/chg
        # dipole moment
        for i in range(3):
            for j in range(self.natm):
                mu[i] += self.q[j]*(self.xyzatm[j][i+1]-cntr[i])
        mu[0]=mu[0]*debbohr; mu[1]=mu[1]*debbohr; mu[2]=mu[2]*debbohr
        d=numpy.sqrt(mu[0]**2+mu[1]**2+mu[2]**2)
        return d,mu

    def WriteResults(self,prtchg=True):
        ff83='%8.3f'
        qt=0.0
        for i in range(self.natm): qt=qt+self.q[i]
        #const.CONSOLEMESSAGE('atom charges='+str(self.q))
        if abs(qt-self.charge) > 0.001:
            mess='QEq calculation failed. input charge='+str(self.charge)+'and computed total charge='+str(qt)
            lib.MessageBoxOK(mess,'Qeq(WriteResults)')
        else:
            if prtchg:
                const.CONSOLEMESSAGE('Partial charges obtained by the modified QEq method(NM-Gamma is used):')
                const.CONSOLEMESSAGE('xyzfile='+self.xyzfile)
                for i in range(self.natm):
                    const.CONSOLEMESSAGE(str(i+1)+', '+self.xyzatm[i][0]+', '+str(self.q[i]))
        const.CONSOLEMESSAGE('Total Charge='+str(qt))

        # compute dipole moment
        d,mu=self.DipoleMoment()
        const.CONSOLEMESSAGE('Dipole moment(Debye)='+ff83 % d+' ('+ff83 % mu[0]+','+ff83 % mu[1]+','+ff83 % mu[2]+')')
        if self.charge != 0.0:
            const.CONSOLEMESSAGE('The molecule is charged! So, the dipole moment is calculated at center-of-charge')
        etime=self.time2-self.time1
        const.CONSOLEMESSAGE('Elapsed time(sec.): '+ff83 % etime)   
    
    def WriteFile(self,outfile,title=''):
        ff8='%10.6f'; fi4='%4d'; fi2='%2d'; blk5=5*' '
        text='# Atomic partial charges created by fu at '+lib.DateTimeText()+'\n'
        text=text+'# Program: '+self.prgnam+'\n'
        if len(title) >= 0: text=text+'# '+title+'\n'
        text=text+'# coordinate file='+self.coordfile+'\n'
        text=text+'# number of atoms='+str(self.natm)+'\n'
        text=text+'RESNAM='+self.resnam+'\n'
        text=text+'CHARGE='+ff8 % self.charge+'\n'
        text=text+'SCALE= '+ff8 % self.scale+'\n'
        text=text+'#\n'
        text=text+'# format: sequence number,element, partial charge\n'
        text=text+'#\n'
        chgtext=''
        for i in range(len(self.xyzatm)):
            chgtext=chgtext+fi4 % (i+1)+blk5
            chgtext=chgtext+self.xyzatm[i][0]+blk5
            chgtext=chgtext+ff8 % self.q[i]+'\n'
        text=text+chgtext
        #
        f=open(outfile,'w')
        f.write(text)
        f.close()
        
    def Quit(self):
        self.Destroy()

qeq=QEq('Title',0)

