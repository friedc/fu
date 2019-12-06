#!/bin/sh
# -*- coding: utf-8


import os
#import sys
import wxversion
wxversion.select("2.8")
import wx
import wx.grid

import copy
#import shutil 
#import copy
import numpy
#import numpy
#import datetime
import fumodel
import molec
import const
import lib
import subwin
import rwfile
try: import fortlib
except: pass


class Geometry(object):
    def __init__(self,parent,pltwinpos=[],pltwinsize=[]):
        self.title='Geometry'
        if len(pltwinpos) <= 0: pltwinpos=lib.WinPos(parent)
        if len(pltwinsize) <= 0: pltwinsize=[640,250]
        self.pltwinpos=pltwinpos; self.pltwinsize=pltwinsize
        #
        self.mdlwin=parent
        self.model=self.mdlwin.model #self.parent.model
        #
        self.gparamlst=['Bond length','Bond angle','Hydrogen bond',
                        'Peptide angle']
        self.gparamnmb=-1
        self.gparam=''
        self.graphtype='bar'
        self.graphcolor='b'
        self.ylabel=['Angstroms','Degrees','Angstroms','Degrees']
        self.xlst=[]; self.ylst=[]; self.xvarlst=[]
        
    def SetParamName(self,gparam):
        self.gparam=gparam
        try: self.gparamnmb=self.gparamlst.index(self.gparam)
        except: self.gpramnmb=-1
        
    def SetPlotData(self,xlst,ylst,varlst):
        self.xlst=xlst
        self.ylst=ylst
        self.varlst=varlst

    def SetGraphType(self,graphtype):
        self.graphtype
    
    def SetGraphColor(self,graphcolor):
        self.graphcolor=graphcolor
            
    def Plot(self,gparam):
        self.gparam=gparam
        try: self.gparamnmb=self.gparamlst.index(self.gparam)
        except: pass
        menulst=['by element(s)']
        if gparam == 'Bond length':
            self.xlst,self.ylst,self.xvarlst=self.ComputeBondLength()
        elif gparam == 'Bond angle':
            self.xlst,self.ylst,self.xvarlst=self.ComputeBondAngle()
        elif gparam == 'Hydrogen bond':
            self.xlst,self.ylst,self.xvarlst=self.ComputeHydrogenBond()
        elif gparam == 'Peptide angle':
            self.xlst,self.ylst,self.xvarlst=self.ComputePeptideAngle()
        else:
            mess='Program error: Not supported gparam='+gparam
            lib.model.Message(mess,'GeometryInspection(Plot)')        
            return
        if len(self.xlst) <= 0 or len(self.ylst) <= 0:
            mess='No data to plot.'
            lib.MessageBoxOK(mess,'GeometryInspection(Plot)')
            return
        #
        self.pltwin=subwin.PlotAndSelectAtoms(self.mdlwin,-1,self.model,
                         self.title,"other",button=True,onmolview=True,
                         resetmethod=None) #self.OnReset)
        self.pltwin.SetGraphType(self.graphtype)
        self.pltwin.SetColor(self.graphcolor)
        #
        self.pltwin.NewPlot()
        self.pltwin.PlotTitle(self.gparamlst[self.gparamnmb])
        self.pltwin.PlotXY(self.xlst,self.ylst)
        self.pltwin.PlotXLabel('Data Number')
        self.pltwin.PlotYLabel(self.ylabel[self.gparamnmb])
        self.pltwin.SetXVarData(self.xvarlst)
        if len(menulst) > 0: self.pltwin.AddExtractMenu(menulst,self.OnExtract)
    
    def ComputeBondAngle(self):
        def MakeIndex(i,j,k):
            minik=min(i,k); maxik=max(i,k)
            idx=str(minik)+'-'+str(j)+'-'+str(maxik)
            return idx,minik,j,maxik
        
        todeg=const.PysCon['rd2dg']
        xvalue=[]; yvalue=[]; xvarlst=[]
        natm=0; atmlst=[]; donedic={}
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue # skip TER
            natm += 1; atmlst.append(atom.seqnmb)
        if natm <= 2: return xvalue,yvalue,xvarlst
        count=-1
        for i in atmlst:
            atom=self.model.mol.atm[i]
            if len(atom.conect) < 2: continue
            for j in range(len(atom.conect)-1):
                for k in range(j+1,len(atom.conect)):
                    ja=atom.conect[j]; ka=atom.conect[k]
                    idx,jj,ii,kk=MakeIndex(ja,i,ka) # i: center atom
                    if donedic.has_key(idx): continue
                    count += 1
                    xvalue.append(count)
                    cci=atom.cc[:]; ccj=self.model.mol.atm[ja].cc[:]
                    cck=self.model.mol.atm[ka].cc[:]
                    ang=lib.BendingAngle(ccj,cci,cck); ang=ang*todeg
                    yvalue.append(ang)
                    xvarlst.append([jj,ii,kk])
                    donedic[idx]=True
        return xvalue,yvalue,xvarlst
    
    def ComputeHydrogenBond(self):
        xvalue=[]; yvalue=[]; xvarlst=[]
        nhbnd,bnddic=self.model.mol.MakeHydrogenBond([])
        xvalue=range(nhbnd)
        for i in range(nhbnd): 
            yvalue.append(bnddic[i][2])
            xvarlst.append([bnddic[i][0],bnddic[i][1]])
        return xvalue,yvalue,xvarlst
        
    def ComputePeptideAngle(self):
        pass
    
    def ComputeBondLength(self,rmin=-1,rmax=-1):
        def BondIdx(i,j):
            minij=min(i,j); maxij=max(i,j)
            idx=str(minij)+':'+str(maxij)
            return idx
                
        xvalue=[]; yvalue=[]; xvarlst=[]
        natm=len(self.model.mol.atm); npair=0; donedic={}
        # fortran code
        try:
            if rmin < 0: rmin=0.5
            if rmax < 0: rmax=3.0
            cc=[]; iopt=0
            for i in xrange(natm): cc.append(self.model.mol.atm[i].cc[:])
            cc=numpy.array(cc)
            npair,iatm,jatm,rij=fortlib.find_contact_atoms2(cc,rmin,rmax,iopt)
            count=-1
            for k in xrange(npair):
                i=iatm[k]; j=jatm[k]; r=rij[k]
                if self.model.mol.atm[i].elm == 'XX': continue
                if self.model.mol.atm[j].elm == 'XX': continue
                if not j in self.model.mol.atm[i].conect: continue
                idx=BondIdx(i,j)
                if donedic.has_key(idx): continue
                count += 1
                xvalue.append(count)
                yvalue.append(r)
                xvarlst.append([i,j])
                donedic[idx]=True
        except:
            mess='Model:ComputeBondDistance: running python code'
            self.model.ConsoleMessage(mess)
            count=-1
            for i in xrange(natm):
                if self.model.mol.atm[i].elm == 'XX': continue
                cci=self.model.mol.atm[i].cc[:]
                for j in self.model.mol.atm[i].conect:
                    idx=BondIdx(i,j)
                    if donedic.has_key(idx): continue
                    #itemj=AtomItem(j); 
                    ccj=self.model.mol.atm[j].cc[:]
                    r=lib.Distance(cci,ccj)                
                    count += 1
                    xvalue.append(count)
                    yvalue.append(r)
                    xvarlst.append([i,j])
                    donedic[idx]=True  
        return xvalue,yvalue,xvarlst

    def OnExtract(self,item,xvarlst):
        extracted=[]
        if item == 'by element(s)':
            tiptext='Input element(s), e.g., "C","H",...'
            text=wx.GetTextFromUser(tiptext,'GeometryInspect(OnEctract)')
            text=text.strip()
            if len(text) <= 0: return
            items=lib.SplitStringAtSpacesOrCommas(text)
            elmlst=[]; sellst=[]
            for s in items:
                elm=lib.ElementNameFromString(s)
                elmlst.append(elm)
            #if len(elmlst) > 0:
            if self.gparam == 'Bond length' or self.gparam == 'Hydrogen bond':
                for i in range(len(xvarlst)):
                    j=xvarlst[i][0]; k=xvarlst[i][1]
                    elmj=self.model.mol.atm[j].elm
                    elmk=self.model.mol.atm[k].elm
                    if len(elmlst) == 1:
                        if elmj == elmlst[0] or elmk == elmlst[0]:
                            extracted.append(i)
                    elif len(elmlst) >= 2:
                        if (elmj == elmlst[0] and elmk == elmlst[1]) or \
                                (elmj == elmlst[1] and elmk == elmlst[0]): 
                            extracted.append(i)
            elif self.gparam == 'Bond angle':
                for i in range(len(xvarlst)):
                    j=xvarlst[i][0]; k=xvarlst[i][1]; l=xvarlst[i][2]
                    elmj=self.model.mol.atm[j].elm
                    elmk=self.model.mol.atm[k].elm
                    elml=self.model.mol.atm[l].elm
                    if len(elmlst) == 1:
                        if elmj == elmlst[0] or elmk == elmlst[0] or \
                                   elml == elmlst[0]:
                            extracted.append(i)
                    elif len(elmlst) >= 2:
                        elmtmp=elmlst[:]
                        if elmj in elmtmp:
                            elmtmp.remove(elmj)
                            if elmk in elmtmp:
                                elmtmp.remove(elmk)
                            if len(elmlst) == 2:
                                extracted.append(i); continue
                            if elml in elmtmp: extracted.append(i)                        
            return extracted
        else:
            mess='Wrong menu item='+item
            lib.MessageBoxOK(mess,'GeometryInspection(OnExtract)')
            return []
        
    def OnReset(self,event):
        const.CONSOLEMESSAGE('OnReset')

