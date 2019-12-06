#!/bin/sh
# -*- coding: utf-8


import os
import sys
import wxversion
wxversion.select("2.8")
import wx
#import wx.grid
import numpy
import networkx
#
import fumodel
import molec
import const
import lib
import subwin
import rwfile
#try: import fortlib
#except: pass

class Fragment(object):
    """ Setting of fragments """
    def __init__(self,parent):
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.setctrl=self.model.setctrl
        #
        self.name=None    # name of molecules
        self.frgnamlst=[] # [frgnam1,frgnam2,...]
        self.frgatmdic={} # {frgnam:atmlst,...}
        self.frgbdadic={}
        self.frgattribdic={} # {frgname:[chg,spin,...],...}
        # res data
        self.filelst=[]
        self.resattribdic={} 
        
        self.resfrgdic={} # {resnam:[bdadic,frgnamlst,frgatmdic,frgattribdic],
        
        self.frgauto=None
        self.frgpan=None
        self.attrwin=None
        self.bdapan=None
        self.view=None
        self.attrwin=None
        # default min size
        self.frgminsize=10
        # attribute
        self.attriblst=['charge','layer','spin'] #'active',
        self.valdic={}
        self.valdic['charge']=['0','-2','-1','1','2']
        self.valdic['layer']=['1','2','3'] 
        self.valdic['active']=['0','1'] 
        self.valdic['spin']=['1','2','3','4','5']
        self.frglst0=['selected','non-peptide','all']
        #
        self.savlayer=[]

    def SetName(self,name):
        """ Set molecule name
        
        :param str name: molecule name
        """
        if self.model.mol.CountTer([]) > 0:
            mess='The molecule has "TER(s)". Please delete them '
            mess=mess+'("Modeling"-"Delete"-"TER in PDB data") and try again.'
            lib.MessageBoxOK(mess,'Fragment(SetName)')
            return
        self.name=name
        
    def ClearResidueBDAFiles(self):
        """ Clear residue BDA files """
        self.filelst=[]
        try: self.bdapan.SetItems(self.filelst)
        except: pass
        
    def ClearBDA(self,resknd,drw=True):
        """ Clear BDA/BAA
        
        :param str resknd: 'aa','chm','wat', 'all' or 'selected'
        """
        resknddic={'aa':0,'chm':1,'wat':2}
        ndel=0
        if resknd == 'selected':
            frglst=self.ListSelectedFragment()
            if len(frglst) <= 0: 
                mess='No selected fragments.'
                self.model.ConsoleMessage(mess)
                return
            for i in range(len(self.model.mol.atm)):
                atom=self.model.mol.atm[i]
                if atom.frgnam in frglst:
                    if atom.frgbaa >= 0:
                        atom.frgbaa=-1; atom.frgknd=-1; ndel += 1
        elif resknd == 'all':
            for atom in self.model.mol.atm:
                if atom.frgbaa >= 0: 
                    atom.frgbaa=-1; atom.frgknd=-1; ndel += 1
        else:
            for atom in self.model.mol.atm:
                frgknd=atom.frgknd
                if frgknd != resknddic[resknd]:
                    continue
                if atom.frgbaa >= 0: 
                    atom.frgbaa=-1; atom.frgknd=-1; ndel += 1
        
        self.MakeFragmentName()
        #
        mess="Clear BDA in "+resknd+". Number of removed BDA(s)="+str(ndel)
        self.model.ConsoleMessage(mess)
        #
        self.RemoveDrawFragAndBDA(drw=False)
        if drw: self.DrawBDAPoint(True)
    
    def RemoveDrawFragAndBDA(self,drw=True):
        drwlabel="Paint fragment"
        if self.model.ctrlflag.Get(drwlabel): 
            self.DrawFragmentByColor(False,drw=drw)
        drwlabel="BDA points"
        if self.model.ctrlflag.Get(drwlabel): 
            self.DrawBDAPoint(False,drw=drw)
        
    def ClearFragmentName(self,resknd):
        """ Clear fragment name
        
        :param str resknd: 'aa','chm','wat', or 'all'
        """
        for atom in self.model.mol.atm:
            frgknd=atom.frgknd
            if resknd != 'all' and frgknd != resknd: continue
            atom.frgnam=''
        #
        self.RemoveDrawFragAndBDA()
    
    def DrawFragmentByColor(self,on,drw=True):
        """ Rainbow coloring of fragments
        
        :param bool on: True for coloring, False for restore 
        """
        drwlabel='Paint fragment' # for 'ctrlflag'
        if on:     
            self.model.SetDrawItemsAndCheckMenu(drwlabel,True)
            self.model.SaveAtomColor(True)
            nchg=self.SetFragmentColor()
        else:  
            self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
            self.model.SaveAtomColor(False)      
        
        self.model.mol.SetDrawItem(drwlabel,on)       
        if drw: self.model.DrawMol(True)
    
    def SetFragmentColor(self):
        """ Set fragment colors for draw """
        frgdic={}; nf=-1
        frgnamlst=self.ListFragmentName('all')
        
        for frgnam in frgnamlst:
            if frgdic.has_key(frgnam): continue
            nf += 1; icol=numpy.mod(nf,7)
            frgdic[frgnam]=icol
        
        trgatmlst=self.model.ListTargetAtoms()
        for frgnam in frgnamlst:
            if frgnam == '': continue
            for atom in self.model.mol.atm:
                #atom=self.model.mol.atm[i]
                if atom.elm == 'XX': continue
                if atom.envflag: continue
                if not atom.seqnmb in trgatmlst: continue
                #if not atom.select: continue
                if atom.frgnam == frgnam:
                    icol=frgdic[frgnam]; col=const.FragmentCol[icol]
                    atom.color=col[:]
        #mess='Number of fragment='+str(len(self.frgnamlst))
        #self.model.Message2(mess)

    def RemoveAllFragmentDrawItems(self):
        """
        Remove all fragemnt related draw items, 'BDA points','Paint fragment','
        Formal charge', and 'Fragment name'.
        """
        drwlabels=['BDA points','Paint fragment','Formal charge','Fragment name']
        for drwlabel in drwlabels:
            self.model.mdlwin.draw.DelDrawObj(drwlabel)
            self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
        self.model.SaveAtomColor(False)
        #self.mol.SetDrawItem(drwlabel,on) #Paint fragment'
        self.model.DrawMol(True)
      
    def ListNoneChargeFragment(self):
        frglst=[]; done={}
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam
            if done.has_key(frgnam): continue
            if atom.frgchg is None: frglst.append(frgnam)
            done[frgnam]=True
        """
        try: frgattribdic=self.model.mol.frgattribdic
        except: return frglst
        for frgnam,attriblst in frgattribdic.iteritems():
            if attriblst[0] is None: frglst.append(frgnam)
       """
        return frglst
        
    def DrawFragmentCharge(self,on,drw=True):
        drwlabel='Fragment charge'
        self.model.ctrlflag.Set(drwlabel,False)
        if on:
            nchg,drwdat=self.MakeDrawFragmentChargeData()
            if nchg > 0:
                mess='Number of non-zero fragment charges='+str(nchg)+'.'
                self.model.Message(mess,0,'black')
                #label self.draw.SetLabelList(label,True,drwdat)
                self.model.mdlwin.draw.SetDrawData(drwlabel,'LABEL',drwdat)
                self.model.SetDrawItemsAndCheckMenu(drwlabel,True)       
                self.model.ctrlflag.Set(drwlabel,True)
            else:
                mess='No non-zero fragment charges.'
                self.model.Message(mess,0,'black')
                self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
                self.model.ctrlflag.Set(drwlabel,False)
        else:
            self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
            #label self.draw.SetLabelList(label,False,[])
            self.model.mdlwin.draw.DelDrawObj(drwlabel) #,'LABEL',[])
            self.model.ctrlflag.Set(drwlabel,False)
        if drw: self.model.DrawMol(True)

    def MakeDrawFragmentChargeData(self):
        frgattribdic=self.model.mol.frgattribdic
        myname='Fragment(MakeDrawFragmentChargeData)'
        if frgattribdic is None:
            mess='Fragment charges are not set.'
            lib.MessageBoxOK(mess,myname)
            return
        frglst=self.ListSelectedFragment()
        if len(frglst) <= 0: frglst=self.frgnamlst
        nchg=0; drwdat=[]; nonchgfrg=[]
        # drawlabeldata:label=drawlabel[i][0],pos=drawlabel[i][1];;color=drawlabel[i][2]  
        for frgnam in frglst:
            first=self.frgatmdic[frgnam][0]
            if not self.model.mol.atm[first].show: continue
            if not frgattribdic.has_key(frgnam):
                chg=0; nonchglst.append(frgnam)
                continue
            if len(frgattribdic[frgnam]) <= 0:
                chg=0; nonchgfrg.append(frgnam)
                continue   
            if frgattribdic[frgnam][0] is None:
                chg=0; nonchgfrg.append(frgnam)
            else: chg=self.model.mol.frgattribdic[frgnam][0]
            if abs(chg) < 0.001: continue 
            schg='%5.2f' % chg; schg=schg.strip()
            if chg >= 0: color=[1.0,1.0,0.0,1.0]
            else: color=[0.0,1.0,0.0,1.0]
            pos=numpy.array(self.model.mol.atm[first].cc)
            lab=schg
            drwdat.append([lab,None,pos,color])
            nchg += 1
        if len(nonchgfrg) > 0:
            mess=str(len(nonchgfrg))+'/'+str(len(self.frgnamlst))
            mess=mess+' fragments are not assigned charges'
            #lib.MessageBoxOK(mess,myname)
            self.model.ConsoleMessage(mess)
        
        return nchg,drwdat
        
    def DrawLabelFrgNam(self,on,drw=True):
        drwlabel='Fragment name'
        self.model.ctrlflag.Set(drwlabel,False)
        if on:
            nfrg,drwlst=self.MakeDrawLabelFrgNamData()
            if nfrg > 0:
                self.model.SetDrawItemsAndCheckMenu(drwlabel,True)
                #label self.draw.SetLabelList(label,True,drwlst)
                self.model.mdlwin.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.model.ctrlflag.Set(drwlabel,True)
                self.drawlabelfrg=True
            else: return
        else:
            self.drawlabelfrg=False
            self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
            #label self.draw.SetLabelList(label,False,[])
            self.model.mdlwin.draw.DelDrawObj(drwlabel) #,'LABEL',[])
        
        if drw: self.model.DrawMol(True)
    
    def MakeDrawLabelFrgNamData(self,trglst=[]):
        if len(trglst) <= 0: trglst=self.model.ListTargetAtoms()
        nfrg=0; drwdat=[]; donedic={}
        color=self.model.setctrl.GetParam('label-color') #self.mol.labelcolor #[0.0,1.0,0.0]
        for i in trglst:
            atom=self.model.mol.atm[i]
            frg=atom.frgnam
            if frg == '': continue
            if not atom.show: continue
            if donedic.has_key(frg): continue
            donedic[frg]=i
            sfrg=frg.strip(); sfrg=sfrg.lower()
            posa=numpy.array(atom.cc)
            pos=posa+[0.1,-0.2,0.1]
            lab=sfrg
            drwdat.append([lab,None,pos,color])
            nfrg += 1
        return nfrg,drwdat

    def MakeDrawBDAData(self):   
        #nsel,lst=self.ListSelectedAtom()
        lst=self.model.ListTargetAtoms()
        nbda=0; drwdat=[]; nslice=3
        for i in lst:
            atom=self.model.mol.atm[i]
            if not atom.show: continue
            if atom.frgbaa >= 0: 
                tmp=[] #draw.DrawBDAPointData()
                rad=0.2
                posa=numpy.array(atom.cc)
                atomib=self.model.mol.atm[atom.frgbaa]
                posb=numpy.array(atomib.cc)
                pos=posa+(posb-posa)*0.2 #+[-0.1,-0.1,0.0] # should be half of font size
                color=[0.0,1.0,0.0]
                drwdat.append([rad,pos,color,nslice])
                nbda += 1
        return drwdat
    
    def IsCaAtCterminal(self,ia):
        ans=False
        count=0
        for ib in self.model.mol.atm[ia].conect:
            atomib=self.model.mol.atm[ib]
            atm=atomib.atmnam 
            elm=atomib.elm
            if elm == ' O': count += 1
            if atm == ' OXT': ans=True
        if count == 2: ans=True
        return ans
        
    def SetBDAInAAResidue(self,trglst=[]):
        """ Set BAA to BDA atom to 'Atom' attribute
        
        :param lst trglst: target atom list (sequential numbers)
        """
        if len(trglst) <= 0: trglst=self.model.ListTargetAtoms()
        #
        nbda=0
        for ia in trglst:
            atomia=self.model.mol.atm[ia]
            res=atomia.resnam
            if not const.AmiRes3.has_key(res): continue
            if atomia.atmnam == ' CA ':
                for ib in atomia.conect:
                    atomib=self.model.mol.atm[ib]
                    if atomib.atmnam == ' C  ':
                        if self.IsCaAtCterminal(ib): continue
                        self.model.mol.atm[ia].frgbaa=ib
                        nbda += 1
        return nbda

    def NumberOfAtomsInFragment(self,messout=True):
        """ Return number of atoms in fragment """
        nfrg=len(self.frgnamlst)
        frgnmb=[]; natm=[]
        text='Numnber of atoms in framgent:\n'
        for i in range(nfrg):
            frgnam=self.frgnamlst[i]; natmi=len(self.frgatmdic[frgnam])
            frgnmb.append(i+1); natm.append(natmi)
            text=text+'fragment='+str(i+1)+', number of atoms='
            text=text+str(natmi)+'\n'
        text=text+'Total number of atoms='+str(len(self.model.mol.atm))+'\n'
        if messout: self.model.ConsoleMessage(text)
        
        return frgnmb,natm
            
    def PlotFragmentSize(self):
        """ Plot fragment size """
        x,y=self.NumberOfAtomsInFragment(messout=False)
        molnam=self.model.mol.name
        title='Fragment size'
        winpos=lib.WinPos(self.model.mdlwin)
        pltobj=subwin.PlotAndSelectAtoms(self.model.mdlwin,-1,self.model,
                                         title,'fragment',winpos=winpos) 
        #
        pltobj.NewPlot()
        pltobj.SetGraphType('bar') # 'bar' or 'line'
        pltobj.PlotTitle('Fragment size')
        pltobj.PlotXLabel('Fragment number')
        pltobj.PlotYLabel('Number of atoms')
        pltobj.PlotXY(x, y)

    def ListFragmentAtoms(self):
        """ Return list of fragment atoms """
        frgatmlst=[]
        for frgnam in self.frgnamlst:
            frgatmlst.append(self.frgatmdic[frgnam])
        return frgatmlst
            
    def ListAtomsInFragment(self,frgnam):
        atmlst=[]
        for atom in self.model.mol.atm:
            if atom.frgnam != frgnam: continue
            atmlst.append(atom.seqnmb)
        return atmlst
    
    def DictFragmentAtoms(self):
        """ Return list of fragment atoms """
        frgatmdic={}
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam
            if not frgatmdic.has_key(frgnam): frgatmdic[frgnam]=[]
            frgatmdic[frgnam].append(atom.seqnmb)
        return frgatmdic
            
    def FragmentSizeDistribution(self,binwidth=5,messout=True):
        """ Return fragment size distribution """
        frgatm=self.ListFragmentAtoms()
        nfrg=len(frgatm); size=[]
        for i in range(nfrg): size.append(len(frgatm[i]))
        minsize=min(size); minsize=minsize/binwidth+1
        maxsize=max(size); maxsize=maxsize/binwidth+1
        rank=range(binwidth*(minsize-1),binwidth*(maxsize+1),binwidth)
        x=rank; freq=len(rank)*[0]
        for i in size: freq[(i-rank[0])/binwidth] += 1
        text='Fragment size distribution:\n'
        for i in range(len(x)):
            if freq[i] > 0: 
                text=text+'rank='+str(i)+', number of atoms>='
                text=text+str(x[i])+', frequency='+str(freq[i])+'\n'
        text=text+'Total number of fragments='+str(nfrg)+'\n'
        if messout: self.model.ConsoleMessage(text)
        return x,freq
        
    def PlotFragmentSizeDistribution(self,binwidth=5):
        """ Plot fragment size distribution """
        x,y=self.FragmentSizeDistribution(binwidth=binwidth,messout=True)
        #        
        molnam=self.model.mol.name
        title='Fragment size distribution'
        winpos=lib.WinPos(self.model.mdlwin)
        pltobj=subwin.PlotAndSelectAtoms(self.model.mdlwin,-1,self.model,
                                         title,'',winpos=winpos) 
        #
        pltobj.NewPlot()
        pltobj.SetGraphType('bar') # 'bar' or 'line'
        pltobj.PlotTitle('Fragment size distribution')
        pltobj.PlotXLabel('Number of atoms')
        pltobj.PlotYLabel('Frequency')
        
        pltobj.SetWidth(binwidth)
        pltobj.PlotXY(x,y)

    def AssignLayer(self,layer):
        drwlabel='Layer by color'
        self.SaveLayerData(True)
        nsel,lst=self.model.ListSelectedAtom()
        if nsel <= 0:
            mess='No selected atoms for layer. Nothing done.'
            self.model.Message(mess,0,'black')
            return
        for i in lst: self.model.mol.atm[i].layer=layer
        if self.model.ctrlflag.Get(drwlabel): 
            self.model.DrawMol(True)

    def AssignLayerUndo(self,drw=True):
        for i in xrange(len(self.model.mol.atm)):
            layer=self.model.mol.atm[i].layer
            if layer != self.savlayer[i]:
                self.model.mol.atm[i].color=self.savatmcol[i]
        self.SaveLayerData(False)
        if self.model.ctrlflag.Get('drawlayer') and drw: 
            self.model.DrawMol(True)        
                        
    def SaveLayerData(self,save):
        if self.model.mol is None: return
        if save:
            self.savlayer=[]
            for atom in self.model.mol.atm:
                self.savlayer.append(atom.layer)
        else:
            for i in xrange(len(self.model.mol.atm)):
                self.model.mol.atm[i].layer=self.savlayer[i]
    
    def ViewFragmentData(self):
        """ Open TextViewer and display fragment data """
        # open text viewer
        try: self.view.SetFocus()
        except:
            text=self.ViewText()
            if len(text) > 0:
                title='Fragment data'
                self.view=subwin.TextViewer_Frm(self.model.mdlwin,
                                           title=title,text=text)
        
    def ViewText(self):
        """ View fragment data """
        frgnamlst=self.ListFragmentName('all')
        if len(frgnamlst) <= 0:
            mess='No fragments.'
            lib.MessageBoxOK(mess,'Fragment(ViewFragmentData)')
            return ''
        frgatrribdic={}
        try: frgattribdic=self.model.mol.frgattribdic
        except: frgattribdic=None
        """ needs rewrite"""
        frgatmdic=self.DictFragmentAtoms()
        
        frgnatm=self.CountAtomsInFragment()
        frgnatm=frgnatm.values()
        maxfrg=max(frgnatm); minfrg=min(frgnatm)
        nochgfrg=self.ListNoneChargeFragment()
        #
        text='Fragment data of '+self.model.mol.name+'\n'
        text=text+'Number of atoms='+str(len(self.model.mol.atm))+'\n\n'
        text=text+'Number of fragments='+str(len(frgnamlst))+'\n'
        text=text+'Max. size='+str(maxfrg)+', Min. size='+str(minfrg)+'\n'
        if len(nochgfrg) > 0:
            text=text+'Number of unassigned charge fragments='
            text=text+str(len(nochgfrg))+'\n'
            text=text+'Unassigned charge fragments='+str(nochgfrg)
            text=text+'\n'
        #text=text+'seq#,fragment name,number of atoms,charge,layer,active,'
        #text=text+'spin\n'
        text=text+'seq#,fragment name,number of atoms,charge,layer,'
        text=text+'spin\n'
        if frgattribdic is not None:
            for i in range(len(frgnamlst)):
                frgnam=frgnamlst[i]
                text=text+('%6d' % (i+1)) +' '+frgnam+' '
                text=text+('%6d' % len(frgatmdic[frgnam]))+2*' '
                if frgattribdic[frgnam][0] == None:
                   text=text+str(frgattribdic[frgnam][0])
                else:    
                   text=text+('%4d' % frgattribdic[frgnam][0])
                text=text+('%4d' % frgattribdic[frgnam][1])
                #text=text+('%4d' % frgattribdic[frgnam][2])  # active
                text=text+('%4d' % frgattribdic[frgnam][3])+'\n'
        return text

    def SetSelectFrg(self,frgnam,selflg):
        if frgnam == '': return
        nsel=0
        for atom in self.model.mol.atm:
            i=atom.seqnmb
            frg=atom.frgnam
            if frg == frgnam:
                nsel += 1; atom.select=selflg
        return nsel

    def ListAtomLayer(self):
        layerlst=[]
        for atom in self.model.mol.atm:
            layerlst.append(atom.layer)
        nlayer=max(layerlst)
        return nlayer,layerlst
    
    def ListFragmentLayer1(self):    
        frgdic={}; frglst=[]
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam
            if not frgdic.has_key(frgnam): frglst.append([frgnam,atom.layer])
            frgdic[frgnam]=True
        return frglst
    
    def ClearLayer(self,layer,drw=True):
        drwlabel='Layer by color'
        self.SaveLayerData(True)
        if layer == 999:
            for i in xrange(len(self.model.mol.atm)):
                self.model.mol.atm[i].layer=1
                self.model.mol.atm[i].color=self.savatmcol[i]
        else:    
            lst=self.model.ListTargetAtoms()
            for i in lst:
                if self.model.mol.atm[i].layer == layer:
                    self.model.mol.atm[i].layer=1
                    self.model.mol.atm[i].color=self.savatmcol[i]
        if self.model.ctrlflag.Get(drwlabel) and drw: 
            self.model.DrawMol(True)
    
    def DrawLayer(self,on):
        drwlabel='Layer by color'
        # set from menu
        self.model.SaveAtomColor(on)
        self.model.SetDrawItemsAndCheckMenu(drwlabel,on)
        if on:
            self.model.SaveAtomColor(True)
            self.SetLayerColor()
        else: self.model.SaveAtomColor(False)

        self.model.DrawMol(True)

    def SetLayerColor(self):
        
        for atom in self.model.mol.atm:
            if const.LayerCol.has_key(atom.layer):
                atom.color=const.LayerCol[atom.layer]
    
    def SelectBDAs(self,drw=True):
        self.model.SetSelectAll(False)
        for atom in self.model.mol.atm:
            if atom.frgbaa >= 0: atom.select=True
        if drw: self.model.DrawMol(True)
    
    def SelectFragmentByNmb(self,frgnmb,on,drw=True):
        sellst=[]
        for atom in self.model.mol.atm:
            if atom.frgnmb == frgnmb: atom.select=True
        if drw: self.model.DrawMol(True)
    
    def SelectFragmentByName(self,frglst,drw=True):
        for atom in self.model.mol.atm:
            if atom.frgnam in frglst: atom.select=True
        if drw: self.model.DrawMol(True)
                
    def SelectFragmentWithSize(self,sml):
        # sml: True for smaller, False for larger selection
        self.model.SetSelectAll(False)
        text1='larger'; text2='min.'; default=30
        if sml:
            text1='smaller'; text2='max.'; default=5
        natfrg=wx.GetNumberFromUser('Select '+text1+' fragment',
                                    'Enter '+text2+' number to select',
                           'Input numeric data',default,parent=self.mdlwin)
        if natfrg <= 0:
            mess='Wrong input. Should be an integer. Try again.'
            self.model.Message(mess,0,'black')
            return        
        frgdic=self.CountAtomsInFragment()
        tmp={}; nsel=0
        for name in frgdic:
            if sml:
                if frgdic[name] <= natfrg: tmp[name]=frgdic[name]
            else:
                if frgdic[name] > natfrg: tmp[name]=frgdic[name]
        for atom in self.model.mol.atm:
            if tmp.has_key(atom.frgnam):
                atom.select=True; nsel += 1
                for j in atom.conect:
                    self.model.mol.atm[j].select=True; nsel += 1
        if nsel <=0:
            self.model.Message("No atom is selected.",0,'black')
            return
        self.model.DrawMol(True)
        mess='Number of selected fragment='+str(len(tmp))+', atoms='+str(nsel)
        self.model.Message(mess,0,'')

    def CountAtomsInFragment(self):
        frgdic={}
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam
            if atom.elm == 'XX': continue
            if frgdic.has_key(frgnam): frgdic[frgnam] += 1
            else: frgdic[frgnam]=1
        return frgdic

    def MakeBDAList(self):
        bdalst=[]
        for atom in self.model.mol.atm:
            if atom.frgbaa >= 0:
                bda=atom.seqnmb; baa=atom.frgbaa
                baaatom=self.model.mol.atm[baa]
                bdanam=atom.atmnam; baanam=baaatom.atmnam
                bdares=lib.ResDat(atom); baares=lib.ResDat(baaatom)
                
                bdalst.append([bda,baa,bdanam,baanam,bdares,baares])
        return bdalst
    
    def RenumberIndexForFrg(self):
        # 2013.2 KK
        idx=[]
        seq=0
        for i in xrange(len(self.atm)):
            if self.atm[i].elm == 'XX': idx.append(-1)
            else:
                seq += 1; idx.append(seq)
        return idx
    
    def XXMakeFrgDatForWrite(self):
        # 2013.2 KK
        molnam=self.name
        idx=self.RenumberIndexForFrg()
    
        bdalst=self.MakeBDAList(idx)
        blk=' '
        con=self.MakeFrgConDat(idx)
        ssblst=self.FindSSBond(idx)
        con=Molecule.DelFrgBDABond(bdalst,ssblst,con)
        #
        grplst=Molecule.BondAtmGrp(con,ssblst)
        #
        resnam,frglst=self.MakeFrgAtmLst1(grplst,idx)
        if resnam == '': return

        frgtbl=self.MakeFrgTable(frglst)
        
        return molnam,resnam,bdalst,frgtbl,frglst
    
    def MakeFragAttribFromAtomAttrib(self):
        frgnamlst=self.ListFragmentName()
        #self.mol.ClearFragmentAttribute()
        #if not self.mol.fragattribdic.has_key('FRGNAM'):
        #if not self.parobj.IsAttribute('FRGNAM'):
        #fgnamlst=self.parobj.ListFragmentName()
        #if len(frgnamlsyt) > 0:
        #    self.mol.SetFragmentAttributeList('FRGNAM',frgnamlst)
        #if not self.mol.fragattribdic.has_key('ICHARG'):
        if self.IsAttribute('charge'):
            frgchglst=self.ListFragmentCharge()
            #self.mol.SetFragmentAttributeList('ICHARG',frgchglst)
        

    def MakeFrgTable(self,frglst):
        # 2013.2 KK
        # return frgtbl: [0]frgnam, [1]number of atoms and [2]frgchg
        frgtbl=[]
        prvnam=frglst[0][0]; natm=0; chg=0
        for i in xrange(len(frglst)):
            frgnam=frglst[i][0]
            natm += 1
            #chg += frglst[i][6]; chgnxt=frglst[i][6]
            chg += frglst[i][7]; chgnxt=frglst[i][7]
            if frgnam != prvnam:
                tmp=[]
                chg -= chgnxt; chg=round(chg,0)
                tmp.append(prvnam); tmp.append(natm-1); tmp.append(chg)
                frgtbl.append(tmp)
                natm=1; chg=chgnxt; prvnam=frgnam
        if natm > 0:
            tmp=[]; chg=round(chg,0)
            tmp.append(frgnam); tmp.append(natm); tmp.append(chg)        
            frgtbl.append(tmp)   

        return frgtbl
    
    def FragmentByBDAFiles(self,filelst,messout=True):
        """ Created framents by BDA files 
        
        :param lst filelst: [bdafile1,bdafile2,...]
        """
        self.filelst=filelst
        if len(self.filelst) <= 0: return
        #
        if messout:
            mess='FragmentByBDAFiles:\n'
            mess=mess+'BDA file list='+str(filelst)
            self.model.ConsoleMessage(mess)
        #
        self.MakeResBDADicFromFile(filelst,messout=messout)
        self.SetResidueBDAs(messout=messout)
        
        self.UpdateViewText()
        
    def FragmentPolypeptide(self,case,trglst=[],drw=True,messout=True):
        """ Fragment polypeptide """
        self.CheckTers()

        if len(trglst) <= 0: trglst=self.model.ListTargetAtoms()
        nbda=self.SetBDAInAAResidue(trglst)
        ndel=0  
        if case == 1: # combine GLY to neighbour
            ndel=self.MergeGlyFrg()
        elif case == 2: # combine two residues
            ndel=self.MergeTwoAAResFrgs()
        nbda -= ndel
        #
        if nbda > 0: 
            self.MakeFragmentName()
            #self.SetFragmentCharge()
        #
        if messout:
            mess='Created number of BDA points in Polypeptide='
            mess=mess+str(nbda)+'.'
            self.model.ConsoleMessage(mess)
                
        if drw and nbda > 0: self.DrawBDAPoint(True)
        #self.SetFragmentName()

    def MergeGlyFrg(self):
        ndel=0
        for atom in self.model.mol.atm:
            res=atom.resnam; atm=atom.atmnam
            if res == 'GLY' and atm == ' CA ': 
                atom.frgbaa=-1; ndel += 1
        return ndel
    
    def MergeTwoAAResFrgs(self):
        ndel=0
        ic=0; prvres='   '; prvnmb=-1
        for atom in self.model.mol.atm:
            i=atom.seqnmb; res=atom.resnam; nmb=atom.resnmb 
            if res in const.CysRes:
                ic=0; prevres='   '; prvnmb=-1; continue
            if res != prvres or nmb != prvnmb:
                ic += 1; prvres=res; prvnmb=nmb 
            if ic <= 0: continue
            atm=atom.atmnam
            if atm == ' CA ':
                atom.frgbaa=-1; ndel += 1; ic=-1
        return ndel
    
    def RemoveAllFragmentShowItems(self):
        """
        Remove all fragemnt related draw items, 'BDA points','Paint fragment','
        Formal charge', and 'Fragment name'.
        """
        drwlabels=['BDA points','Paint fragment','Formal charge','Fragment name']
        for drwlabel in drwlabels:
            self.draw.DelDrawObj(drwlabel)
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
        self.SaveAtomColor(False)
        #self.mol.SetDrawItem(drwlabel,on) #Paint fragment'
        self.DrawMol(True)
    
    def CheckTers(self):
        """ Check if 'TER' exists """
        nter=0
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': nter += 1
        if nter > 0:
            mess='There are "TER" in the molecule. Would you like to delete '
            mess=mess+'them?'
            ans=lib.MessageBoxYesNo(mess,'Fragment(CheckTER)')
            if ans: self.model.DeleteAllTers(drw=False)
   
    def FragmentIntoMonomers(self):
        """
        mess='This command is assumed to be executed at the first'
        mess=mess+' fragmentation. So, all BDAs will be removed.\n'
        mess=mess+'Would you like to execute?'
        ans=lib.MessageBoxYesNo(mess,'Fragment(FrgamnetIntoMonomers)')
        if not ans: return
        """
        #
        self.MakeFragmentName()
    
    def FragmentAuto(self,polypepcase=0,trgsize=10,drw=True,messout=True):
        """ Polypeptide Fragment at Csp3 """
        
        self.CheckTers()
        #
        if IsPolypeptide():
            self.FragmentPolypeptide(polypepcase,trglst=[],drw=drw,
                                     messout=messout)
        if IsNonPeptide():
            self.FragmentNonPeptideAuto(trgsize=trgsize,drw=drw,messout=messout)
        if IsWater():
            pass
    
    def FragmentNonPeptideAuto(self):
        self.splittxt=['Csp3-Csp3','Csp3-Csp2','Csp3-O','Csp3-N']
        mess='Enter minimum fragment size(default:10)\n and split option at'   
        mess=mess+' Csp3-X\n(0:X=Csp3,1:Csp2,2:O,3:N,default:[0,1]).\n'
        mess=mess+'If minsize=-1, only splits at Csp3.'
        text=wx.GetTextFromUser(mess,caption='Fragment size option',
                                default_value='10, [0, 1]')       
        if len(text.strip()) <= 0: return
        #
        self.CheckTers()
        #
        splitopt=[]
        if len(text.strip()) > 0:
            test=True
            try: 
                items=text.split(',',1)
                minsize=int(items[0])
                items=items[1].split('['); text=items[1][:-1]
                items=lib.SplitStringAtSpacesOrCommas(text)
                splitopt=[int(x) for x in items]
            except: 
                mess='Wrong input data. text='+text+'.'
                lib.MessageBoxOK(mess,'Fragment(FragmentNonPeptideAuto)')
                return      
        if splitopt is None: 
            splitopt=self.model.setctrl.GetParam('split-option')
        opttxt=''
        for i in splitopt: opttxt=opttxt+self.splittxt[i]+','
        mess='FragmentNonPeptideAuto:\n'; opttxt=opttxt[:-1]
        mess=mess+'split option=['+opttxt+'], '
        mess=mess+'minsize='+str(minsize)
        self.model.ConsoleMessage(mess)
        
        self.FragmentAtCsp3(minsize,option=splitopt)
    
    def FragmentAtCsp3(self,minsize=10,option=[],drw=True):
        """ Auto fragment non-peptide molecule
        
        :param int minsize: minimum fragment size
        :param lst option: option to split at Csp3(BDA)-X(BAA),
                            elements:0:Csp3,1:Csp2,2:O,3:N
                            [0,1] allows Csp3(BDA)-Csp3 and Csp2.
        :param bool drw: True for redraw molecule, False do not 
        """
        self.CheckTers()
        
        self.model.mdlwin.BusyIndicator('On','FragmentNonPeptide...')
        if len(option) <= 0: option=[0,1]
        trgatmlst=range(len(self.model.mol.atm))
        ringatmlst=self.MakeRingAtomList(trgatmlst)
        grpdic=self.model.FindConnectedGroup()
        for ig, atmlst in grpdic.iteritems():
            if len(atmlst) < minsize: continue
            nodelst,conlst=self.MakeConnectList(atmlst)
            for i,j in conlst:
                if i in ringatmlst or j in ringatmlst: continue        
                self.SetBDAAtSP3Carbon(atmlst,option,[])
        #  make minimum sized fragments
        self.MakeFragmentName(messout=False)
        if len(self.frgnamlst) <= 1:
            mess='Unable to fragment. There are no specified BDA-BAA.'
            lib.MessageBoxOK(mess,'Fragment(FragmentNonPeptide)')
            self.model.mdlwin.BusyIndicator('Off')
            return
        #
        self.RemoveBDAWithinFragment()
        #
        if minsize > 0:
            nmerg=self.MergeSmallFragments(minsize)
            if nmerg > 0: 
                self.RemoveDrawFragAndBDA()
                self.MakeFragmentName(messout=True)
                self.RemoveBDAWithinFragment()
        #
        mess='Number of fragments='+str(len(self.frgnamlst))
        self.model.Message2(mess)
        if drw: self.DrawBDAPoint(True)
        self.model.mdlwin.BusyIndicator('Off')
    
    def SetBDAAtSP3Carbon(self,trgatmlst,option=[0,1],ringlst=[]):
        """ Set BDA at SP3-SP3(optional SP3-SP2) carbons except in ring """
        done={}; bdaelm=' C'; elmopt=[' C',' C',' O',' N']; baaelm=[]
        for i in option: baaelm.append(elmopt[i])
        #
        for i in trgatmlst:
            atomi=self.model.mol.atm[i]
            if atomi.resnam in const.AmiRes3: continue
            if done.has_key(i): continue
            if atomi.elm == ' H': 
                done[i]=True; continue
            if atomi.elm != bdaelm or len(atomi.conect) != 4: continue
            for j in atomi.conect:
                atomj=self.model.mol.atm[j]
                if atomj.elm == ' H': 
                    done[j]=True; continue
                if atomj.resnam in const.AmiRes3: continue
                if i in ringlst or j in ringlst: continue
                if done.has_key(j): continue
                if not atomj.elm in baaelm: continue
                ok=False; ncon=len(atomj.conect)
                if 0 in option and ncon == 4: ok=True
                if 1 in option and ncon == 3: ok=True
                else: ok=True
                if ok: 
                    atomi.frgbaa=j; done[i]=True; done[j]=True

    def FragmentAtBDA(self,minsize=10,bdaatmlst=[],baaatmlst=[],aares=False,
                                                              drw=True):
        """ Auto fragment non-peptide molecule
        
        :param int minsize: minimum fragment size
        :param lst bdaatmlst: [atom1,atm2,..], atom:"Xsp3","Xsp2"," X",
                              where X is element(upper case).
        :parma lst baaatmlst: BAA atom list. The data form is the same as BDA
        :param bool drw: True for redraw molecule, False do not 
        :param bool aares: True for including amino acid residues
        """
        self.CheckTers()
        
        self.model.mdlwin.BusyIndicator('On','FragmentAtBDA...')
        if len(bdaatmlst) <= 0 or len(baaatmlst) <= 0:
            mess='No bdaatmlst/baaatmlst.'
            lib.MessageBoxOK(mess,'Fragment(FragmentAtBDA)')
            return
        mess='Fragmentation:\n'
        mess=mess+'BDA atom types='+str(bdaatmlst)+'\n'
        mess=mess+'BAA atom types='+str(baaatmlst)+'\n'
        mess=mess+'Minimum fragment size='+str(minsize)
        self.model.ConsoleMessage(mess)
        # process BDA and BAA type
        bdatyp,bdaelm,bdavale=self.CovertAtomTypeToElmAtmNam(bdaatmlst)
        baatyp,baaelm,baavale=self.CovertAtomTypeToElmAtmNam(baaatmlst) 
        if len(bdatyp) <= 0 or len(baatyp) <= 0:
            mess='Wrong BDA/BAA atom type'
            lib.MessageBoxOK(mess,'Fragment(FragmentAtBDA)')
            return

        trgatmlst=range(len(self.model.mol.atm))
        ringatmlst=self.MakeRingAtomList(trgatmlst)
        grpdic=self.model.FindConnectedGroup()
        for ig, atmlst in grpdic.iteritems():
            if len(atmlst) < minsize: continue
            nodelst,conlst=self.MakeConnectList(atmlst)
            for i,j in conlst:
                if i in ringatmlst or j in ringatmlst: continue        
                self.SetBDAAtAtom(atmlst,bdatyp,bdaelm,bdavale,
                                         baatyp,baaelm,baavale,aares=aares)
        #  make minimum sized fragments
        self.MakeFragmentName(messout=False)
        if len(self.frgnamlst) <= 1:
            mess='Unable to fragment. There are no specified BDA-BAA.'
            lib.MessageBoxOK(mess,'Fragment(FragmentNonPeptide)')
            self.model.ConsoleMessage(mess)
            self.model.mdlwin.BusyIndicator('Off')
            return
        #
        self.RemoveBDAWithinFragment()
        #
        if minsize > 0:
            nmerg=self.MergeSmallFragments(minsize)
            if nmerg > 0: 
                self.RemoveDrawFragAndBDA()
                self.MakeFragmentName(messout=True)
                self.RemoveBDAWithinFragment()
        #
        mess='Number of fragments='+str(len(self.frgnamlst))
        self.model.Message2(mess)
        if drw: self.DrawBDAPoint(True)
        self.model.mdlwin.BusyIndicator('Off')
    
    def SetBDAAtAtom(self,trgatmlst,bdatyp,bdaelm,bdavale,
                             baatyp,baaelm,baavale,aares=False,ringlst=[]):
        """ Set BDA at BDA atoms in in ringlst """
        done={}
        #
        for i in trgatmlst:
            atomi=self.model.mol.atm[i]
            if not aares and atomi.resnam in const.AmiRes3: continue
            if done.has_key(i): continue
            if atomi.elm == ' H': 
                done[i]=True; continue
            if not aares and atomi.resnam in const.AmiRes3: continue
            if not self.IsAtomInBDABAA(atomi,bdatyp,bdaelm,bdavale):
                continue            
            for j in atomi.conect:
                atomj=self.model.mol.atm[j]
                if atomj.elm == ' H': 
                    done[j]=True; continue
                if done.has_key(j): continue
                if not aares and atomj.resnam in const.AmiRes3: continue
                if i in ringlst or j in ringlst: continue
                if not self.IsAtomInBDABAA(atomj,baatyp,baaelm,baavale):
                    continue
                atomi.frgbaa=j; done[i]=True; done[j]=True

    def CovertAtomTypeToElmAtmNam(self,atmtyplst):
        """ Convert BDA/BAA atom type to elm or atmnam """
        def AppenData(type,name,vale,typelst,elmatmlst,valelst):
            typelst.append(type); elmatmlst.append(name); valelst.append(vale)     
        
        typelst=[] # 0:elm without valence, 2:elm with valence,2:atmnam
        elmatmlst=[]; valelst=[]
        for atmtyp in atmtyplst:
            if len(atmtyp) <= 2: # type1, element without valence
                elm=lib.ElementNameFromString(atmtyp)
                AppenData(0,elm,None,typelst,elmatmlst,valelst)
            elif len(atmtyp) == 4:
                nc=atmtyp.find('sp')
                if nc > 0: # type=1,elm with valence
                    try: 
                        elm=lib.ElementNameFromString(atmtyp[:1])
                        vale=int(atmtyp[-1])+1
                        AppenData(1,elm,vale,typelst,elmatmlst,valelst)
                    except: return None,None,None
                else: # type=2, atom name
                    type=2
                    AppenData(2,atmtyp,None,typelst,elmatmlst,valelst)
        return typelst,elmatmlst,valelst

    def IsAtomInBDABAA(self,atom,typelst,elmatmlst,valelst):
        """ Return True if atom ('Atom' instance) is in bad/baa type
        
        :param obj atom: 'Atom' instance
        :param lst typelst: Converted data from BDA/BAA atom type
        :param lst elmatmlst: list of elm or atom name
        :param lst valelst: lits of valence of elm
         """
        for i in range(len(typelst)):
            type=typelst[i]
            if type == 0: # elm without valence
                if atom.elm == elmatmlst[i]: return True
            elif type == 1: # elm with valence
                if atom.elm == elmatmlst[i] and len(atom.conect) == valelst[i]:
                    return True
            elif type == 2: # atom name
                if atom.atmnam == elmatmlst[i]: return True
        return False
    
    def MergeSmallFragments(self,minsize=10):
        """  Merge fragments whose size is smaller than 'minsize' """
        def FindNext(nfrg,done):
            i=-1
            for j in range(nfrg):
                if not done.has_key(j):
                    i=j; break
            return i
        
        def FindConnectedFragment(nfrg,ifg,done):
            can0=-1; can1=-1
            ifgatmlst=self.frgatmdic[self.frgnamlst[ifg]]
            for i in ifgatmlst:
                baa=self.model.mol.atm[i].frgbaa
                if baa < 0: continue
                jfg=self.model.mol.atm[baa].frgnmb
                can1=jfg
            for i in range(nfrg):
                if i == ifg: continue
                atmlst=self.frgatmdic[self.frgnamlst[i]]
                for j in atmlst:
                    atomj=self.model.mol.atm[j]
                    baa=atomj.frgbaa
                    if baa >= 0 and baa in ifgatmlst:
                        bda=atomj.seqnmb
                        can0=self.model.mol.atm[bda].frgnmb      
            fg=can1
            if fg < 0: fg=can0
            return fg
        
        if len(self.model.mol.atm) < minsize:
            mess='The molecular size is smaller than fragment minsize='
            mess=mess+str(minsize)
            lib.MessageBoxOK(mess,'Fragment(MergeSmallFragments')
            return
        # merge loop
        done={}; nmerg=0; nfrg=len(self.frgnamlst); nfrg2=nfrg-2
        while True:
            i=FindNext(nfrg,done)
            if i < 0: break
            atmlst=self.frgatmdic[self.frgnamlst[i]][:]
            done[i]=True
            while len(atmlst) < minsize:
                jfg=FindConnectedFragment(nfrg,i,done)
                if jfg < 0: break
                frgatmlst1=self.frgatmdic[self.frgnamlst[jfg]]
                done[jfg]=True; atmlst=atmlst+frgatmlst1[:]
                self.RemoveBDAInAtomGroup(atmlst)
                nmerg += 1
                if len(atmlst) < minsize:
                    i=FindNext(nfrg,done)
                    if i < 0: break
        # check the last fragment size 
        if not done.has_key(nfrg-1):
            frgnam=self.frgnamlst[-1]
            if len(self.frgatmdic[frgnam]) < minsize:
                jfg=FindConnectedFragment(nfrg,nfrg-2,{})
                if jfg >= 0:
                    frgnam1=self.frgnamlst[jfg]
                    atmlst=self.frgatmdic[frgnam]+self.frgatmdic[frgnam1]
                    self.RemoveBDAInAtomGroup(atmlst)
                    nmerg += 1
        return nmerg
                
    def RemoveBDAInAtomGroup(self,atmlst,messout=False):
        """ Remove BDA/BAA in atoms in 'atmlst' """
        count=0; natm=len(atmlst)
        for i in atmlst:
            bda=i
            baa=self.model.mol.atm[i].frgbaa            
            if baa >= 0:
                if bda in atmlst and baa in atmlst:
                    self.model.mol.atm[i].frgbaa=-1; count += 1
        if messout:
            mess='Number of removed BDA(s)='+str(count)
            self.model.ConsoleMessage(mess)
            
    def RemoveBDAWithinFragment(self):
        """ Remove BDA/BAA in each fragment """
        for frgnam in self.frgnamlst:
            atmlst=self.frgatmdic[frgnam]
            self.RemoveBDAInAtomGroup(atmlst)
        
    def MakeConnectList(self,trgatmlst):
        """ Return connected group list in 'trgatmlst' """
        conlst=[]; nodelst=[]; done={}
        for i in trgatmlst:
            nodelst.append(i)
            for j in self.model.mol.atm[i].conect:
                minij=min([i,j]); maxij=max([i,j])
                ij=str(minij)+':'+str(maxij) 
                if done.has_key(ij): continue
                conlst.append([minij,maxij])
                done[ij]=True
        return nodelst,conlst
    
    def MakeRingAtomList(self,trgatmlst,maxatm=6):
        """ Retrun ring atom list in 'targetatmlst'.
            (ring size is smaller than 'maxatm')
        """
        ringatmlst=[]
        nodelst,conlst=self.MakeConnectList(trgatmlst)
        # find k-components
        G=networkx.Graph()
        G.add_nodes_from(nodelst)
        G.add_edges_from(conlst)
        klst=networkx.k_components(G)
        ringatmlst=[]; ringlst=[]
        try: 
            ringlst=[list(x) for x in klst[2]]
            for lst in ringlst: 
                if len(lst) <= maxatm: ringatmlst=ringatmlst+lst            
        except: pass
        return ringatmlst
            
    def ListSelectedFragment(self):
        """ Return selected fragment names in list """
        nsel,selatm=self.model.ListSelectedAtom()
        if len(selatm) <= 0:
            selatm=range(len(self.model.mol.atm))
        #
        frglst=[]; donedic={}
        for ia in selatm:
            frgnam=self.model.mol.atm[ia].frgnam
            if donedic.has_key(frgnam): continue
            frglst.append(frgnam)
            donedic[frgnam]=True
        return frglst
    
    def JoinTwoFragments(self,drw=True,messout=True):
        """ Join selected two fragmenst """
        frgnamlst=self.ListSelectedFragment()
        if len(frgnamlst) != 2:
            mess='Please select two fragments.'
            lib.MessageBoxOK(mess,'Fragment(JoinTwoFragments')
            return
        if not frgnamlst[0] in self.frgnamlst or \
                         not frgnamlst[1] in self.frgnamlst:
            mess='Program error? Selected fragment is not in frgmant list.'
            lib.MessageBoxOK(mess,'Fragment(JointTwoFragments)')
            return
        atmlst=self.frgatmdic[frgnamlst[0]]+self.frgatmdic[frgnamlst[1]]
        self.RemoveBDAInAtomGroup(atmlst)
        if messout:
            mess='Jointed fragments: '+frgnamlst[0]+' and '+frgnamlst[1]
            self.model.ConsoleMessage(mess)
        self.MakeFragmentName(messout=True)
        #
        if drw: self.DrawBDAPoint(True)
        
    def JoinSelectedToNeighbor(self,trglst=[],drw=True,messout=True):
        """ Need rewite --- Merge selected fragments
        
        :param lst trglst: list of selected atoms
        """
        if len(trglst) <= 0: nsel,trglst=self.model.ListSelectedAtom()
        if len(trglst) <= 0:
            mess='No selected fragments.'
            lib.MessageBoxOK(mess,'Fragment(MergeFragment')
            return
        ndel=0; mrgfrg=[]
        selfrglst=self.ListSelectedFragment()
        for i in trglst:
            atom=self.model.mol.atm[i]
            nami=atom.frgnam; baa=atom.frgbaa
            namj=self.model.mol.atm[baa].frgnam
            if baa > 0 and namj in selfrglst: 
                atom.frgbaa=-1; mrgfrg=mrgfrg+[nami,namj]; ndel += 1
        #
        self.MakeFragmentName()
        #
        if messout:
            mess="Number of deleted BDA's="+str(ndel)+"\n"
            mess=mess+"Merged fragments: "+str(mrgfrg)
            self.model.ConsoleMessage(mess)
        if drw and ndel > 0: self.DrawBDAPoint(True)
    

    def MergeSelectedFragments(self,trglst=[],drw=True,messout=True):
        """ Need rewite --- Merge selected fragments
        
        :param lst trglst: list of selected atoms
        """
        if len(trglst) <= 0: nsel,trglst=self.model.ListSelectedAtom()
        if len(trglst) <= 0:
            mess='No selected fragments.'
            lib.MessageBoxOK(mess,'Fragment(MergeFragment')
            return
        ndel=0; mrgfrg=[]
        selfrglst=self.ListSelectedFragment()
        for i in trglst:
            atom=self.model.mol.atm[i]
            nami=atom.frgnam; baa=atom.frgbaa
            namj=self.model.mol.atm[baa].frgnam
            if baa > 0 and namj in selfrglst: 
                atom.frgbaa=-1; mrgfrg=mrgfrg+[nami,namj]; ndel += 1
        #
        self.MakeFragmentName()
        #
        if messout:
            mess="Number of deleted BDA's="+str(ndel)+"\n"
            mess=mess+"Merged fragments: "+str(mrgfrg)
            self.model.ConsoleMessage(mess)
        if drw and ndel > 0: self.DrawBDAPoint(True)
    
    def InputBDABAA(self,bda,baa):
        """ manual bda/baa setting """
        if baa < 0: return
        self.model.Message('BDA setting...',1,'black')
        natm=len(self.model.mol.atm)
        ia=bda; ib=baa
        mess='bda: '+self.model.MakeAtomLabel(bda,False)
        mess=mess+', baa: '+self.model.MakeAtomLabel(baa,False)
        self.model.Message(mess,1,'black')
        findb=False
        for j in range(len(self.model.mol.atm[ia].conect)):
            if self.model.mol.atm[ia].conect[j] == ib: findb=True #la
        finda=False
        for j in range(len(self.model.mol.atm[ib].conect)):
            if self.model.mol.atm[ib].conect[j] == ia: finda=True #lb
        if self.model.mol.atm[ia].elm == ' H': finda=False
        if self.model.mol.atm[ib].elm == ' H': findb=False
        if not finda or not findb:
            mess='Wrong BDA setting between atoms '+str(ia)+' and '+str(ib)
            mess=mess+'. Skipped.'
            self.model.Message(mess,0,'blue')
            #?self.mousectrl.SetPointedAtomHis([])
            self.model.mousectrl.pntatmhis.Clear()
            self.model.SetSelectAll(False) #ClearSelFlg()
            self.model.DrawMol(True)
            return
        
        dup=self.model.mol.atm[ia].frgbaa == ib
        if dup: self.model.mol.atm[ia].frgbaa=-1
        else: self.model.mol.atm[ia].frgbaa=ib
        #
        self.MakeFragmentName(messout=False)
        #       
        mess='Number of fragment='+str(len(self.frgnamlst))
        #mess='Number of fragment='+str(len(self.frgnamlst))+'['
        #for frgnam in self.frgnamlst:
        #    natmi=len(self.frgatmdic[frgnam]); mess=mess+str(natmi)+','
        #mess=mess[:-1]+']'
        self.model.ConsoleMessage(mess) #Message(mess,0,'')

        self.model.SetSelectAll(False)

        if self.model.ctrlflag.Get('Paint fragment'):
            self.model.ChangeAtomColor("by fragment") #,[])        
        self.DrawBDAPoint(True)
        
    def ManualBDASetting(self,on):
        # on(bool): True for turn on BDA mode, False for turn off
        selmod=self.model.mousectrl.GetSelMode()
        selobj=self.model.mousectrl.GetSelObj()
        if on: 
            mess='Manual BDA setting starts'
            self.model.ConsoleMessage(mess)
            self.model.Message('BDA setting...',1,'black')
            self.MakeFragmentName()
            self.model.mousectrl.SetBDAMode(True)
            # clear pointed atom history
            self.model.mousectrl.pntatmhis.Clear()
            self.model.ctrlflag.Set('pntatmhis',[])
            self.model.SaveMouseSelMode()
            self.model.SetMouseSelModeForTwo()
            self.model.SetDrawItemsAndCheckMenu('BDA points',True)          
            self.model.TextMessage('[FMO:Manual BDA Setting]','yellow')
        else:
            self.model.mousectrl.SetBDAMode(False)
            self.model.RecoverMouseSelMode()
            self.model.Message('',1,'black')
            mess='Manual BDA setting ends'
            self.model.ConsoleMessage(mess)
            self.model.TextMessage('','')

    def XXGetFragObjNameDic(self,ifg):
        fg=self.frg[ifg]
        objdic={'name':fg.frgnam,'atom':fg.frgatm,'charge':fg.frgchg,
                'multip':fg.frgmulti,'active':fg.active,'layer':fg.layer,
                'wave fn':fg.frgwfn,'basis set':fg.frgbas,
                'BDA':fg.frgbda,'BAA':fg.frgbaa}
        return objdic        
    
    def FragmentNonAAResByBDA(self):
        def SetBDA(bdalst,resdat,donedic):
            atmlst=self.model.ListResDatAtoms(resdat)
            nbda=0
            for lst in bdalst:
                bda=lst[0]; baa=lst[1]; nbda += 1
                self.model.mol.atm[atmlst[bda]].frgbaa=baa
            donedic[resdat]=True 
            return nbda
        
        self.CheckTers()
        
        messtitle='Fragment(FragmentNonAAResByBDA)'
        if len(self.bdadic) <= 0:
            mess='No BDA data. Please read BDA files.'
            lib.MessageBoxOK(mess,messtitle)
            return
        lst=self.model.ListTargetAtoms()
        molnam,ext=os.path.splitext(self.model.mol.name)
        alldone=False
        # bda of the molecule
        if self.bdadic.has_key(molnam):
            if self.bdanatmdic[molnam] != len(self.model.mol.atm):
                mess='Number of atoms are not the same in BDA data and "mol".\n'
                mess=mess+'Whould you like to continue?'
                ans=lib.MessageBoxYesNo(mess,messtitle)
                if not ans: return
            bdalst=self.bdadic[molnam]; nbda=0
            for bda,baa,bdaatm,baaatm,bdares,baares in bdalst:
                self.model.mol.atm[bda].frgbaa=baa; nbda += 1
            alldone=True
        if not alldone:
            # BDA for specific residue
            donedic={}
            nonaaresdatlst=self.model.ListResidue3('non-aa')
            for resdat in nonaaresdatlst: 
                atmlst=self.model.ListResDatAtoms(resdat)
                if self.bdadic.has_key(resdat):
                    nbda=SetBDA(self.bdadic[resdat],resdat,donedic)
            if len(donedic) < len(nonaaresdatlst):
                for resdat in nonaaresdatlst:
                    if donedic.has_key(resdat): continue
                    resnam,resnmb,chain=lib.UnpackResDat(resdat)
                    if self.bdadic.has_key(resnam):
                        nbda=SetBDA(self.bdadic[resdat],resdat,donedic)
        nbda=self.model.mol.GetNumberOfBDA()
        self.model.mol.SetFragmentName()
        frgnam=self.model.mol.ListFragmentName()
        mess="Created number of fragments="+str(len(frgnam))
        mess=mess+". Number of BDA points="+str(nbda)
        self.model.Message2(mess)
        if nbda > 0: self.model.DrawBDAPoint(True)
        
    def DrawBDAPoint(self,on,drw=True):
        #
        drwlabel='BDA points'
        if on:
            drwdat=self.MakeDrawBDAData()
            nbda=len(drwdat)
            if nbda > 0:
                self.model.mdlwin.draw.SetDrawData(drwlabel,'BDAPOINT',drwdat)
                mess='Number of BDA points='+str(nbda)
                self.model.Message(mess,0,'')
                self.model.SetDrawItemsAndCheckMenu(drwlabel,True)
            else:
                mess='No FMO/BDA points.'
                self.model.Message(mess,0,'black')
                self.model.mdlwin.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
                self.model.SetDrawItemsAndCheckMenu(drwlabel,False)   
        else:
            self.model.mdlwin.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
            self.model.SetDrawItemsAndCheckMenu(drwlabel,False)
            
        if drw: self.model.DrawMol(True)

    def ListFragmentName(self,kind='all'):
        # return fragment name list. 'frgnamlst'
        resknddic={'aa':0,'chm':1,'wat':2}
        frgnamlst=[]; done={}
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam; frgknd=atom.frgknd
            if frgnam == '': continue
            if done.has_key(frgnam): continue
            if kind != 'all' and frgknd != resknddic[kind]: continue
            frgnamlst.append(frgnam); done[frgnam]=True
        return frgnamlst
    
    def DictFragmentName(self,form):
        # return fragment name dictionary, 'frgnamdic'
        # 'form' is the value of item, could be 0, [],...
        frgnamdic={}
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam; frgnamdic[frgnam]=form
        return frgnamdic

    def GetFragmentAttribute(self,attrib):
        myname='Fragment(GetFragmentAtttribute)'
        attribdic={'charge':0,'layer':1,'active':2,'spin':3}
        if not attribdic.has_key(attrib):
            mess='Program error: wrong attribute='+attrib
            lib.MessageBoxOK(mess,myname)
            return []
        attriblst=[]; iatr=attribdic[attrib]
        if self.model.mol.frgattribdic is None:
            mess='Fragment attributes are not set.'
            lib.MessageBoxOK(mess,myname)
            return attriblst
        else:    
            frgnamlst=self.ListFragmentName()
            for frgnam in frgnamlst:
                if self.model.mol.frgattribdic.has_key(frgnam): 
                    attriblst.append(self.model.mol.frgattribdic[frgnam][iatr])
                else: 
                    mess='attribute "'+attrib+'" is not set for fragment='
                    mess=mess+frgnam
                    lib.MessageBoxOK(mess,myname)
                    return []
        return attriblst
    
    def DeleteAllFragmentAttributes(self):
        self.model.mol.frgattribdic={}
        
    def DeleteAllFragmentNames(self):
        """ Delete all fragment names and fragment atom lists """
        self.frgnamlst=[]; frgatmdic={}
        
    def XXMakeFragAttribFromAtomAttrib(self):
        
        return
        
        frgnamlst=self.ListFragmentName()
        #self.mol.ClearFragmentAttribute()
        #if not self.mol.frgattribdic.has_key('FRGNAM'):
        if not self.IsAttribute('FRGNAM'):
            self.SetFragmentAttributeList('FRGNAM',frgnamlst)
        #if not self.mol.frgattribdic.has_key('ICHARG'):
        if not self.IsAttribute('ICHARG'):
            frgchglst=self.ListFragmentCharge()
            self.SetFragmentAttributeList('ICHARG',frgchglst)
        
    def IsAttribute(self,attrib):
        ans=False
        if self.model.mol.frgattribdic is None: pass
        else:
            if self.model.mol.frgattribdic.has_key(attrib): ans=True
        return ans
    
    def SetAllFragmentCharges(self,frgchg):
        # Atom object
        for atom  in self.model.mol.atm: atom.frgchg=0
        frgnamlst=self.ListFragmentName('all')
        for i in range(len(frgnamlst)):
            frgnam=self.frgnamlst[i]
            self.model.mol.frgattribdic[frgnam][0]=frgchg
    
    def SetFragmentCharge(self,messout=True):
        # AA residue and water charge
        frgchg=self.ListFragmentCharge()
        for i in range(len(frgchg)):
            frgnam=self.frgnamlst[i]
            self.model.mol.frgattribdic[frgnam][0]=frgchg[i]
            if frgnam[:3] in const.WaterRes: # water
                self.model.mol.frgattribdic[frgnam][0]=0
                
    def ListFragmentCharge(self,aareschg=True):
        
        if aareschg: self.model.mol.AssignAAResAtmChg()
        # frgchg:[0,1,2,...]
        frgchg=[]; frgdic={}
        #
        prvnam='dummy'; nfrg=-1
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            i=atom.seqnmb
            frg=atom.frgnam
            if frg == '': 
                continue
            if frg == prvnam: continue
            if frgdic.has_key(frg): continue
            else:
                nfrg += 1; frgdic[frg]=nfrg; prvnam=frg
                frgchg.append(0)
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            if atom.frgnam == '': continue
            ifrg=frgdic[atom.frgnam]
            if atom.frgchg is None: frgchg[ifrg]=None
            else:
                frgchg[ifrg] += atom.frgchg # polypeptide charge
                ###frgchg[ifrg] += atom.charge # ion charge
        for i in xrange(len(frgchg)):
            if frgchg[i] is not None: frgchg[i]=int(frgchg[i]) 

        return frgchg
    
    def SetFragmentAttributeList(self,attrib,attriblst):
        self.model.mol.frgattribdic[attrib]=attriblst
            
    def XXDeleteFragAttribute(self,attrib):
        if self.model.mol.frgattribdic.has_key(attrib):
            del self.model.mol.frgattribdic[attrib] 
    
    def MakeFragmentAtomGroup(self,atmlst,bdalst):
        """ Return connect list of atoms excluding bda-baa bonds """
        edgelst=[]; done={}
        for i in atmlst:
            for j in self.model.mol.atm[i].conect:
                ij=[i,j]; ji=[j,i]
                if ij in bdalst or ji in bdalst: continue
                ijmax=max([i,j]); ijmin=min([i,j])
                idx=str(ijmax)+':'+str(ijmin)
                if done.has_key(idx): continue
                edgelst.append(ij); done[idx]=True
        G=networkx.Graph()
        G.add_edges_from(edgelst)
        congrp=networkx.connected_components(G)
        frgatmlst=[list(x) for x in congrp]
        
        return frgatmlst
        
    def MakeFragmentName(self,messout=True):
        if self.model.mol is None: return False
        self.DeleteAllFragmentNames()
        # find connected groups in 'mol'
        netx,G=lib.NetXGraphObject(self.model.mol)
        congrp=netx.connected_components(G)
        grpatmlst=[x for x in congrp]
        #
        ifg=0
        for i in range(len(grpatmlst)):
            atmlst=list(grpatmlst[i])
            if len(atmlst) == 1:
                ifg += 1 #; atmlst=list(atmlst)
                nmb=atmlst[0]
                resnam=self.model.mol.atm[nmb].resnam
                fnam=resnam+'%03d' % ifg
                self.frgnamlst.append(fnam)
                self.frgatmdic[fnam]=[nmb]
            else:
                bdalst=self.ListBDA(atmlst)
                atmgrplst=self.MakeFragmentAtomGroup(atmlst,bdalst)
                for j in range(len(atmgrplst)):
                    ifg += 1; atm0=atmgrplst[j][0]
                    resnam=self.model.mol.atm[atm0].resnam
                    if len(resnam) <= 0: 
                        mess='Program error in MakeFragmentName. resnam=""'
                        lib.MessageBoxOK(mess,'Fragment(MakeFragmentName)')
                        continue
                    fnam=resnam+'%03d' % ifg
                    self.frgnamlst.append(fnam)
                    self.frgatmdic[fnam]=atmgrplst[j][:]
                #self.RemoveBAAInAtomGroup(atmgrplst[j])
        if messout:
            mess='Number of fragments='+str(ifg)
            self.model.ConsoleMessage(mess)
        #
        self.SetFragmentNameToAtomObj()
        #
        self.InitFragmentAttrib()
        
        self.SetFragmentCharge()
        self.UpdateViewText()
        
    def UpdateViewText(self):
        try:
            self.view.ClearText()
            text=self.ViewText()
            self.view.SetText(text)
        except: pass
          
    def InitFragmentAttrib(self):
        """ Initialize fragment attriute values in 'mol' object """
        frgattribdic={}
        for frgnam in self.frgnamlst:
            frgattribdic[frgnam]=[None,1,0,1] # [charge,layer,active,spin
        self.model.mol.frgattribdic=frgattribdic
        
    def SetFragmentNameToAtomObj(self):
        """ Set frgnam and frgnmb of 'Atom' object """
        nonpepfrg=[]; done={}
        for i in range(len(self.frgnamlst)):    
            frgnam=self.frgnamlst[i]
            atmlst=self.frgatmdic[frgnam]
            for j in atmlst:
                self.model.mol.atm[j].frgnam=frgnam
                self.model.mol.atm[j].frgnmb=i
                resnam=self.model.mol.atm[j].resnam
                if resnam in const.AmiRes3: frgknd=0
                elif resnam in const.WaterRes: frgknd=2
                else: 
                    frgknd=1
                    if not done.has_key(frgnam):
                        nonpepfrg.append(frgnam); done[frgnam]=True
                self.model.mol.atm[j].frgknd=frgknd
        
        self.ResetTargetItemInChild(nonpepfrg)
        
        #if self.frgpan is not None: 
        #    self.frgpan.SetTargetFragment(nonpepfrg)
        #if self.frgauto is not None: 
        #    self.frgauto.SetTargetFragment(nonpepfrg)
        
    def ResetTargetItemInChild(self,nonpepfrg):
        if self.frgpan is not None: 
            self.frgpan.SetTargetFragment(nonpepfrg)
        if self.frgauto is not None: 
            self.frgauto.SetTargetFragment(nonpepfrg)
        #if self.attrwin is not None: 
        #    self.attrwin.SetTargetFragment(nonpepfrg)
        
    def GetNumberOfBDA(self):
        nbda=0
        for atom in self.model.mol.atm:
            if atom.frgbaa >= 0: nbda += 1 
        return nbda

    def OpenFragmentFilePanel(self):
        winpos=lib.WinPos(self.model.mdlwin)
        try: self.bdapan.SetFocus()
        except: self.bdapan=FragMolByBDA_Frm(self.model,-1,self,winpos=winpos)
        
    def OpenBDAFiles(self,mol=False,messout=True):
        """ Open BDA file 
        
        :param bool mol: True for entire molecule BDA, False for residue
        """
        # Check if 'mol' object is availabel 
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return

        wcard='BDA/BAA file(*.bda)|*.bda'
        default=''
        if mol: 
            default,ext=os.path.splitext(self.model.mol.name)
            default=default+'.bda'
        filelst=lib.GetFileNames(self.mdlwin,wcard,'r',True,
                                 defaultname=default)
        if len(filelst) <= 0: return
        
        if mol:
            ans=lib.AreSameBaseNames(filelst[0],self.model.mol.name)
            if not ans:
                mess='The base name of BDA file should be the same as '
                mess=mess+'molecule name.'
                lib.MessageBoxOK(mess,'Fragment(OpenBDAFile')
                return   
        self.AppendFiles(filelst)
        
        self.MakeResBDADicFromFile(filelst,messout=messout)
        
        ###self.SetResidueBDAs(messout=messout)

    def AppendFiles(self,filenames):
        """ Append 'filenames' to 'filelst' """
        for file in filenames:
            if file in self.filelst:
                mess=file+' is alredy stored. Ignored.'
                lib.MessageBoxOK(mess,'Fragment(AppendFiles)')
                #self.SetFocus()
            else: self.filelst.append(file)
                            
    def MakeResBDADicFromFile(self,bdafilelst,messout=True):
        """ Make residue BDA dictionary """
        bdareslst=[]; bdamollst=[]; natmlst=[]
        for file in bdafilelst:
            molnam,resnam,natm,frgdat=rwfile.ReadBDAFile(file)
            if len(frgdat) <= 0:
                mess='Read error ocuured in file='+file
                self.model.ConsoleMessage(mess)
                return
            bdalst=frgdat[0]; frgnamlst=frgdat[1] 
            frgatmdic=frgdat[2]; frgattribdic=frgdat[3]
            # decide frgdat type from file name
            # is frgdat of molecule or residue(generic residue or specific) 
            if lib.AreSameBaseNames(file,self.model.mol.name):
                resnam=self.model.mol.name.upper()            
            #
            self.resfrgdic[resnam]=frgdat
            # Set frgattribdic to 'mol' object
            #####self.model.mol.frgattribdic=frgattribdic
            #
            if messout:
                #self.model.ConsoleMessage('\n')
                mess='Read bda file='+file+'\n'
                mess=mess+'molnam='+molnam+', resnam='+resnam
                mess=mess+', nbda='+str(len(bdalst))
                mess=mess+', nfrg='+str(len(frgnamlst))
                self.model.ConsoleMessage(mess)

    def ListBDA(self,trglst=[]):
        """ Return list of BDA/BAA """
        
        if len(trglst) <= 0: trglst=self.model.ListTargetAtoms()
        bdalst=[]
        for i in trglst:
            atom=self.model.mol.atm[i]
            #for atom in self.model.mol.atm:
            if atom.frgbaa >= 0:
                bda=atom.seqnmb; baa=atom.frgbaa
                #baaatom=self.model.mol.atm[baa]
                #bdanam=atom.atmnam; baanam=baaatom.atmnam
                #bdares=lib.ResDat(atom); baares=lib.ResDat(baaatom)
                bdalst.append([bda,baa])
        return bdalst
    
    def SetFragmentFiles(self,filelst):
        self.filelst=filelst
        self.MakeBDADicFromFile(self.filelst)
        self.FragmentAtCsp3()
        
    def DefaultBDAFileName(self):
        molnam=self.model.mol.name
        nres=self.model.CountNumberOfResidues()
        if nres == 1: 
            resdat=lib.ResDat(self.model.mol.atm[0])
            default=lib.MakeFileNameFromResDat(resdat)
            default=default
        else: 
            base,ext=os.path.splitext(molnam)
            default=base
        default=default+'.bda'
        return default
    
    def GetBDAFileNameForSave(self,default):
        wcard='BDA file(*.bda)|*.bda'
        filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                 defaultname=default)
        if len(filename) <= 0: return None
        return filename
    
    def XXSaveBDAs(self,filename=''):
        """ Save fragment data on BDA file """
        if filename == '': filename=self.GetBDAFileNameForSave()            
        
        default=self.DefaultBDAFileName()
        ###self.SetBDAByBDAFile(filename)    
        molnam=self.model.mol.name
        resnam=lib.ResDat(self.model.mol.atm[0])
        nres=self.model.CountNumberOfResidues()
        if nres == 1 and filename != default:
            head,tail=os.path.split(filename)
            resnam,ext=os.path.splitext(tail)
            resnam=resnam.upper()
        natm=len(self.model.mol.atm)
        inpfile=self.model.mol.inpfile
        bdalst=self.MakeBDAList()
        frgattribdic=self.model.mol.frgattribdic
        frgdat=[bdalst,self.frgnamlst,self.frgatmdic,frgattribdic]
        #
        rwfile.WriteBDAFile(filename,frgdat,molnam,resnam,natm,inpfile)
        mess='created bda file='+filename+'\n'
        mess=mess+'nbda='+str(len(bdalst))
        self.model.ConsoleMessage(mess)
    
    def SaveBDAOnFile(self,filetype='entire'):
        """ Save fragment data of entire system on BDA file """
        nochgfrg=self.ListNoneChargeFragment()
        if len(nochgfrg) > 0:
            mess='There are '+str(len(nochgfrg))+' unassigned charges in '
            mess=mess+'fragments.\n'
            mess=mess+'Are they all zeros?'
            ans=lib.MessageBoxYesNo(mess,'Fragment(SaveBDA')
            if ans: self.SetAllFragmentCharges(0)
            else: return
        default=self.model.mol.inpfile
        head,default=os.path.split(default)
        default,ext=os.path.splitext(default)
        default=default+'.bda'
        filename=self.GetBDAFileNameForSave(default)    
        if filename is None: return
        if len(filename) <= 0: return
        self.SaveBDA(filename,filetype=filetype)

    def SaveBDA(self,filename,filetype='specificl'):
        """ Save fragment data on BDA file
        
        :param str filename: file name
        :paramstr filetype: if 'specific', residue name will be resnam
                            else, resdat
         """
        if len(filename) == '': return
        molnam=self.model.mol.name
        resnam=lib.ResDat(self.model.mol.atm[0])
        if filetype == 'specific': resnam=self.model.mol.atm[0].resnam
        natm=len(self.model.mol.atm)
        inpfile=self.model.mol.inpfile
        bdalst=self.MakeBDAList()
        
        frgattribdic=self.model.mol.frgattribdic
        frgnamlst=self.frgnamlst
        frgatmdic=self.frgatmdic

        frgdat=[bdalst,frgnamlst,frgatmdic,frgattribdic]
        #
        rwfile.WriteBDAFile(filename,frgdat,molnam,resnam,natm,inpfile)
        mess='created bda file='+filename+'\n'
        mess=mess+'nbda='+str(len(bdalst))
        self.model.ConsoleMessage(mess)
        
    def MolNameToFragResName(self):
        resnam=self.model.mol.name
        ok=False
        namu=resnam.upper(); naml=resnam.lower()
        if self.resfrgdic.has_key(namu):
            resnam=namu; ok=True
        elif self.resfrgdic.has_key(naml):
            resnam=naml; ok=True
        if not ok: resnam=None
        return resnam
    
    def SetBDAInFile(self,bdafilelst):
        self.MakeResBDADicFromFile(bdafilelst)
        self.SetResidueBDAs()
    
    def OpenBDAFileAndSetBDA(self,mol=True):
        self.OpenBDAFiles(mol)
        self.SetResidueBDAs()
        
    def SetResidueBDAs(self,drw=True,messout=True):
        """ Set residue fragment data in 'resfrgdic' """
        # Search frgdat of molecule
        resnam=self.model.mol.name.upper()
        
        if self.resfrgdic.has_key(resnam):
            bdalst=self.resfrgdic[resnam][0]
            self.frgnamlst=self.resfrgdic[resnam][1]
            self.frgatmdic=self.resfrgdic[resnam][2]
            self.model.mol.frgattribdic=self.resfrgdic[resnam][3]
            #bdalst=bdadic[resnam]
            for lst in bdalst: self.model.mol.atm[lst[0]].frgbaa=lst[1]
            count=-1
            for frgnam in self.frgnamlst:
                atmlst=self.frgatmdic[frgnam]; count += 1
                for i in atmlst:
                    self.model.mol.atm[i].frgnam=frgnam
                    self.model.mol.atm[i].frgnmb=count
            if messout:
                mess='Fragment data were set:\n'
                mess=mess+'Number of BDAs='+str(len(bdalst))
                mess=mess+', Number of fragmens='+str(len(self.frgnamlst))
                self.model.ConsoleMessage(mess)
        else: # set fragment data residu by residue
            self.SetFrgDatOfResidue(messout=messout)
        #             
        if drw:
            self.model.menuctrl.OnFMO("BDA points",True)
    
    def UpdateFrgAtmDic(self):            
        frgatmdic={}
        #frgnamlst=self.ListFragmentName(kind='all')
        for atom in self.model.mol.atm:
            frgnam=atom.frgnam
            if not frgatmdic.has_key(frgnam): frgatmdic[frgnam]=[]
            frgatmdic[frgnam].append(atom.seqnmb)
        self.frgatmdic.update(frgatmdic)
    
    def SetFrgDatOfResidue(self,messout=True):
        """ Set fragment data for each non-aa resdiue """
        done={}
        resdatlst=self.model.ListResidue3('non-aa')
        if len(resdatlst) <= 0:
            #mess='No non-peptide residues.'
            #lib.MessageBoxOK(mess,'Fragment(SetFrgDatOfResidue)')
            return
        # specific residue
        for frgresnam,frgdat in self.resfrgdic.iteritems():
            if frgresnam in resdatlst:
                self.SetFrgDatToAtomObj(frgresnam,0,frgresnam,messout=messout)
                done[frgresnam]=True 
        # generic bda data
        resdatdic={}
        for resdat in resdatlst:
            if done.has_key(resdat): continue
            res,nmb,chain=lib.UnpackResDat(resdat)
            if not resdatdic.has_key(res): resdatdic[res]=[]
            resdatdic[res].append(resdat)
        resnamlst=resdatdic.keys()
        #
        newfrgnamlst=[]
        for frgresnam,frgdat in self.resfrgdic.iteritems():
            # delete frgresnam attribute
            try:
                dellst=[]
                for name,lst in self.model.mol.frgattribdic.iteritems():
                    if name[:3] == frgresnam: dellst.append(name)
                if len(dellst) > 0:
                    for name in dellst:
                         del self.model.mol.frgattribdic[name]
            except: pass
            #
            if frgresnam in resnamlst:
                reslst=resdatdic[frgresnam]
                rescount=-1
                for resdat in reslst:
                    rescount += 1
                    newfrglst=self.SetFrgDatToAtomObj(resdat,rescount,frgresnam,messout=messout)
                    #self.UpdateFrgAtmDic()
                    newfrgnamlst=newfrgnamlst+newfrglst

        self.frgnamlst=self.ListFragmentName(kind='all')
        self.frgatmdic=self.DictFragmentAtoms()
        
        self.UpdateViewText()
        
        self.ResetTargetItemInChild(newfrgnamlst)
        #if self.frgpan is not None: 
        #    self.frgpan.SetTargetFragment(newfrgnamlst)
        #if self.frgauto is not None: 
        #    self.frgauto.SetTargetFragment(newfrgnamlst)
                
    def SetFrgDatToAtomObj(self,resdat,rescount,frgresnam,messout=True):
        """ Set fragment data to 'Atom' attributes
        
        :param str resdat: resdat, resnam:resnmb:chain
        :param str frgresnam: name in residue fragment data, 'resfrgdic' 
        """
        newfrglst=[]
        sellst=self.model.ListTargetAtoms()
        resatmlst=self.model.ListResDatAtoms(resdat)
        idxdic={}
        for i in range(len(resatmlst)): idxdic[i]=resatmlst[i]+1
        #
        bdalst=self.resfrgdic[frgresnam][0]
        frgnamlst=self.resfrgdic[frgresnam][1]
        frgatmdic=self.resfrgdic[frgresnam][2]
        frgattribdic=self.resfrgdic[frgresnam][3]
        #
        found=True
        for lst in bdalst:
            bda=idxdic[lst[0]-1]; baa=idxdic[lst[1]-1]
            ####if bda not in sellst: found=False
            self.model.mol.atm[bda].frgbaa=baa
        if len(frgnamlst) <= 0: 
            self.MakeFragmentName()
            return []
        
        if not found:
            mess='Residue fragment "'+frgresnam+'" atoms are not in selected '
            mess=mess+'atoms. Skpped.'
            self.model.ConsoleMessage(mess)
            return
        #
        count=-1; ok=False
        charlbl=['a','b','c','d','e','f','g','h','i','j','k','l','m','n']
        #newbase=self.NewFragmentBaseName(frgnamlst[0],rescount) #,rescount,count)
        newbase=frgnamlst[0][:3]+charlbl[rescount]
        for frgnam in frgnamlst:
            resknd=1
            if frgnam[:3] in const.AmiRes3: resknd=0
            count += 1; ok=True
            attrib=frgattribdic[frgnam]
            newfrgnam=newbase+frgnam[4:]
            newfrglst.append(newfrgnam)
            atmlst=frgatmdic[frgnam]
            if len(atmlst) <= 0: continue
            for i in atmlst:
                ii=idxdic[i]-1
                self.model.mol.atm[ii].frgnam=newfrgnam
                self.model.mol.atm[ii].frgnmb=count
                self.model.mol.atm[ii].frgknd=resknd
            # remove resfrgnams in ftgattribdic of mol    
            try: self.model.mol.frgattribdic[newfrgnam]=attrib
            except: pass
        
        if not ok:
            mess='BDA file does not have fragment name data. '
            mess=mess+'and the fragment data was created.'
            self.model.ConsoleMessage(mess)
            self.MakeFragmentName(messout=True)
            frgnamlst=self.frgnamlst
        
        if messout:
            mess='Residue fragment data "'+frgresnam+'" was set to '
            mess=mess+'"'+resdat+'"\n'
            mess=mess+'Number of BDAs='+str(len(bdalst))
            mess=mess+', Number of fragments='+str(len(frgnamlst))
            self.model.ConsoleMessage(mess)
        return newfrglst
    
    def NewFragmentBaseName(self,frgnam,rescount): #,rescount,ifrg):
        charlbl=['a','b','c','d','e','f','g','h','i','j','k','l','m','n']
        maxnmb=0; minvalue=97; maxvalue=110 # 'ord('a',, ord('n')
        for atom in self.model.mol.atm:
            if atom.resnam == frgnam[:3]:
                nmb=ord(atom.frgnam[3:4])
                if nmb > maxnmb: maxnmb=nmb       
        if maxnmb < minvalue or maxnmb > maxvalue: maxnmb=0 
        else: maxnmb=maxnmb-minvalue
        #
        if maxnmb+rescount > len(charlbl)-1:
            mess='Program error: increase charlbl list.'
            lib.MessageBoxOK(mess,'Fragment(NewFragmentName)')
            return
        basename=frgnam[:3]+charlbl[maxnmb+rescount]
        return basename

    def RenumberFragmentNumber(self):
        frgnamlst=self.ListFragmentName()
        if len(frgnamlst) <= 0: return 0
        frgnmblst=range(len(frgnamlst))
        ind=-1
        for atom in self.model.mol.atm:
            if atom.frgnam == '': continue
            ind=-1
            ind=self.frgnamlst.index(atom.frgnam)
            #except: pass
            atom.frgnmb=ind
        return ind
    
    def Get(self,frgnam='all',frgnmb=0):
        pass    
            
    def GetFrgNamList(self):
        return self.frgnamlst
    
    def ClearAllFragments(self):
        self.frg=[]
            
    def GetFragAttribFromMolObj(self):
        frgnamlst=self.model.ListFragmentName()
        if not self.model.mol.IsAttribute('FRGNAM'):
            self.model.mol.SetFragmentAttributeList('FRGNAM',frgnamlst)
        if not self.model.mol.IsAttribute('ICHARG'):
            frgchglst=self.model.ListFragmentCharge()
            self.model.mol.SetFragmentAttributeList('ICHARG',frgchglst)
        frgnamlst=[] # list of fragment names
        frgattribdic={}
        
        return frgnamlst,frgattribdic
        
    def GetFragAttrib(self):
        return self.frgnamlst,self.frgattribdic
    
    def SetFragAttrib(self,frgnamlst,frgattribdic,tomol=True):
        self.frgnamlst=frgnamlst
        self.frgattribdic=frgattribdic
        if tomol: self.SetFragAttribsToMol(self.frgnamlst,self.frgattribdic)
    
    def SetFragAttribToMolObj(self,frgnamlst,attrib,value,select=True,
                              messout=True):
        """ Set fragment attribute """
        attribdic={'charge':0,'layer':1,'active':2,'spin':3}
        # select target fragments
        if select: 
            self.model.SelectAll(False,drw=False)
            self.SelectFragmentByName(frgnamlst,drw=True)
        # set attrib
        for frgnam in frgnamlst:
            if not self.model.mol.frgattribdic[frgnam]:
                mess='Fragment "'+frgnam+'" is not found. Skipped.'
                lib.MessageBoxOK(mess,'Fragment(SetFragAttribToMolObj)')
            self.model.mol.frgattribdic[frgnam][attribdic[attrib]]=value
            # set to Atom object
            atmlst=self.ListAtomsInFragment(frgnam)
            if attrib == 'charge':
                for i in atmlst: self.model.mol.atm[i].frgchg=0
                self.model.mol.atm[atmlst[0]].frgchg=value
            elif attrib == 'layer':
                for i in atmlst: self.model.mol.atm[i].layer=value
            elif attrib == 'active':
                for i in atmlst: self.model.mol.atm[i].active=value
            elif attrib == 'spin':
                for i in atmlst: self.model.mol.atm[i].frgmulti=1
                self.model.mol.atm[atmlst[0]].frgmulti=value
        #
        if messout:
            mess='Attribute:"'+attrib+'='+str(value)+'" were set to '
            mess=mess+str(len(frgnamlst))+' fragments.'
            self.model.Message2(mess)
        #
        self.UpdateViewText()
            
    def EditAttribute(self):
        pass

    def OpenAutoFragmentPanel(self):
        try: self.frgauto.SetFocus()
        except: self.frgauto=FragMolResidue_Frm(self.model.mdlwin,-1,parobj=self)

    def OpenFragmentationPanel(self):
        try:  self.frgpan.SetFocus()
        except: self.frgpan=FragMolAllInOne_Frm(self.model.mdlwin,-1,parobj=self)
        
    def OpenAttribPanel(self):
        self.attrwin=FragMolAttrib_Frm(self.model.mdlwin,-1,self)
        self.attrwin.Show()
        self.model.winctrl.openwindic['FragAttribWin']=self.attrwin
        try: self.model.SaveAtomColor(True)
        except: pass

    def OutlineDocument(self):
        """ Open document of the menu """
        helpname='FragmentOutline'
        self.model.helpctrl.Help(helpname)
                
class FragMolByBDA_Frm(wx.Frame):
    """ Fragment by data in BDA/FRG file """
    def __init__(self,parent,id,parobj=None,winpos=[],winsize=[]): #,filelst=[]):
        """ 
        :param obj parent: model instance
        :param int id: id of the object
        :param lst winpos: position of this window
        :param lst winsize: size of this window
        """
        self.title='FragMolByBDA'
        if len(winpos) <= 0: winpos=lib.WinPos(parent)
        if len(winsize) <= 0: self.winsize=lib.WinSize([320,250])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=self.winsize,
                style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.RESIZE_BORDER)
        # 
        self.parent=parent # assume 'mdlwin'
        self.parobj=parobj
        if parobj == None:
            mess="Need parent object!"
            lib.MessageBoxOK(mess,'FragMolByBDA_Frm')
            self.OnClose(1)
        self.model=self.parobj.model
        self.mdlwin=self.model.mdlwin
        #
        self.winlabel='FragMolByBDA'
        self.model.winctrl.SetWin(self.winlabel,self)
        self.helpname=self.winlabel
        # Check if 'mol' object is availabel 
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: self.OnClose(1)
        # attach FU icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # display molecule name on window title
        self.SetTitle(self.title+'['+self.model.mol.name+']')
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.filelst=self.parobj.filelst
        ###self.filelst=self.model.frag.filelst
        self.savbda=[]
        # create panel
        self.CreatePanel()
        if len(self.filelst) > 0: self.SetItems(self.filelst)
        
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
        
        self.Show()
        
    def CreatePanel(self):
        """ Create panel """
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=(0,0),size=(w,h))
        self.panel.SetBackgroundColour("light gray")

        hbtn=25; hcb=const.HCBOX
        xpos=0; ypos=0
        yloc=5
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        btnrset.Hide()
        yloc += 5
        wx.StaticText(self.panel,-1,"Open:",pos=(10,yloc),
                      size=(50,18)) 
        self.rbtfil=wx.RadioButton(self.panel,-1,"File",pos=(60,yloc),
                                   size=(50,18),style=wx.RB_GROUP)
        self.rbtdir=wx.RadioButton(self.panel,-1,"Directory",pos=(110,yloc),
                                   size=(70,18))
        self.rbtfil.SetValue(True)
        xloc=190
        btnbrws=wx.Button(self.panel,-1,"Browse",pos=(xloc,yloc),size=(60,20))
        btnbrws.Bind(wx.EVT_BUTTON,self.OnBrowse)
        yloc += 25
        lin0=wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        # checkbox panel
        width=w-20; height=h-yloc-70 #40
        self.scrpan=subwin.CheckBoxPanel(self.panel,-1,pos=[10,yloc],
                                  size=[width,height])

        yloc += height+10;  xloc=w/2-100
        btnclr=wx.Button(self.panel,-1,"Clear",pos=(xloc,yloc),size=(50,20))
        btnclr.Bind(wx.EVT_BUTTON,self.OnClear)
        btnrmv=wx.Button(self.panel,-1,"Remove",pos=(xloc+70,yloc),
                         size=(60,20))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove) 
        self.btnchk=wx.ToggleButton(self.panel,-1,"Check",pos=(xloc+150,yloc),
                                    size=(50,20))
        self.btnchk.Bind(wx.EVT_TOGGLEBUTTON,self.OnCheck)
        yloc=h-35
        lin1=wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 8; xloc=w/2-100
        # buttons
        self.btnview=wx.Button(self.panel,-1,"View",pos=(xloc,yloc),
                              size=(50,20))
        self.btnview.Bind(wx.EVT_BUTTON,self.OnView)
        self.btnclear=wx.Button(self.panel,-1,"ClearBDA",pos=(xloc+70,yloc),
                              size=(60,20))
        self.btnclear.Bind(wx.EVT_BUTTON,self.OnClearBDA)
        btnaply=wx.Button(self.panel,-1,"Apply",pos=(xloc+150,yloc),
                              size=(50,20))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        
    def SetItems(self,itemlst):
        """ Set items on panel """
        self.scrpan.SetItemList(itemlst)
    
    def ErrorMessage(self,mess):
        """ Display error message """
        lib.MessageBoxOK(mess,'FragmentByBDAFile_Frm(OnUndo)')
            
    def OnView(self,event):
        """ View content of checked(the first file) file  """
        checked=self.scrpan.GetCheckedItems()
        if len(checked) <= 0:
            self.ErrorMessage('No item is checked.')
            return
        file=checked[0]
        viewer=subwin.TextViewer_Frm(self,textfile=file)
        viewer.Refresh()
    
    def OnClearBDA(self,event):
        """ Delete all BDAs """
        self.parobj.ClearBDA('all')
    
    def OnApply(self,event):
        """ Fragment molecule using stored fragment file data """
        filelst=self.scrpan.GetCheckedItems()
        if len(filelst) <= 0:
            mess='No items is checked.'
            lib.MessageBoxOK(mess,'FragmentByFile(OnApply)')
            return
        
        messout=True
        self.parobj.MakeResBDADicFromFile(filelst,messout=messout)
        
        self.parobj.SetResidueBDAs(messout=messout)
    
    def SaveBDAForUndo(self,on):
        """ Save/recover BDA data for undo """
        if on: 
            bdalst=self.model.mol.frgobj.ListBDA()
            self.savbda=bdalst[:]
        else: self.model.mol.frgobj.SetBDAs(self.savbda)
            
    def OnBrowse(self,event):
        """ Get file names(.bad and *.frg) and set them to panel """
        wcard='Fragment file(*.bda;*.frg)|*.bda;*.frg|All(*.*)|*.*'
        extlst=['.bda','*.frg']
        if self.rbtfil.GetValue():
            filenames=lib.GetFileNames(self,wcard=wcard,rw='r')
        elif self.rbtdir.GetValue():
            dirname=lib.GetDirectoryName()
            if dirname == '': filenames=[]
            else: filenames=lib.GetFilesInDirectory(dirname,extlst)   
        if len(filenames) <= 0: return            
        #
        self.model.frag.AppendFiles(filenames)
        self.scrpan.SetItemList(self.model.frag.filelst) #filenames)
        self.scrpan.CheckAllItems(True)
        self.btnchk.SetValue(True)
                    
    def AppendFiles(self,filenames):
        """ Append 'filenames' to 'filelst' """
        for file in filenames:
            if file in self.parobj.filelst:
                mess=file+' is alredy stored. Ignored.'
                lib.MessageBoxOK(mess,'Fragment(AppendFiles)')
                self.SetFocus()
            else: self.parobj.filelst.append(file)
        
    def OnClear(self,event):
        """ Clear filelst """
        self.parobj.filelst=[]
        self.scrpan.SetItemList(self.parobj.filelst)
    
    def OnCheck(self,event):
        """ Get checked items """
        obj=event.GetEventObject()
        value=obj.GetValue()
        self.scrpan.CheckAllItems(value)
    
    def OnRemove(self,enevt):
        """ Remove checked items """
        checked=self.scrpan.GetCheckedItems()
        for file in checked:
            if file in self.parobj.filelst: self.parobj.filelst.remove(file)
        self.scrpan.SetItemList(self.parobj.filelst) #filenames)
        self.scrpan.CheckAllItems(True)
        
    def OnResize(self,event):
        """ Resize wondow """
        itemlst=self.scrpan.GetItemList()
        checklst=self.scrpan.GetCheckedItems()
        #
        self.panel.Destroy()
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])                
        self.CreatePanel()
        #
        self.scrpan.SetItemList(itemlst)
        self.CheckItems(checklst,True)
    
    def CheckItems(self,checklst,on):
        """ Check/uncheck items in 'checklst' """
        self.scrpan.CheckItemsByList(checklst,on) 
        
    def OnNotify(self,event):
        """ Not used. 21Feb2016 """
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles': self.OnReset(1)
        
    def OnReset(self,event):
        """ Reset molecule """
        self.SetTitle(self.title+'['+self.model.mol.name+']')
       
    def OnClose(self,event):
        """ Close the panel """
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        self.Destroy()
        
    def HelpDocument(self):
        """ Open help document """
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        """ Open tutorial """
        self.model.helpctrl.Tutorial(self.helpname)
             
    def MenuItems(self):
        """ Menu items """
        menubar=wx.MenuBar()
         # Help menu
        submenu=wx.Menu()
        submenu.Append(-1,"Document","Open help message")
        submenu.Append(-1,"Tutorial","Open help message")
        menubar.Append(submenu,'Help')
        return menubar

    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        # File
        if item == "Open script files": self.OpenScripts()
        #elif item == "Open log files": self.OpenLogFiles()
        elif item == "Clear script files": self.ClearScripts()
        elif item == "Save .pypy as": self.SavePypyFileAs()
        elif item == "Close": self.OnClose(1)
        # Help menu items
        elif item == "Document": self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()   
            
    
class FragMolAttrib_Frm(wx.Frame):
    """ Not used. 01Mar2016"""
    def __init__(self,parent,id,parobj=None,winpos=[]):
        self.title='Fragment attribute setting'
        winsize=lib.WinSize((320,110)) #((230,135)) #110)
        if len(winpos) <= 0: winpos=lib.WinPos(parent)
        wx.Frame.__init__(self, parent, id, self.title,size=winsize,pos=winpos,
          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent
        self.parobj=parobj
        if parobj == None:
            mess="Need parent object!"
            lib.MessageBoxOK(mess,'FragmentAuto_Frm')
            self.OnClose(1)
        self.model=parent.model
        #self.mdlwin=self.model.mdlwin
        self.winctrl=self.parobj.model.winctrl
        self.winlabel='FragAttribWin'
        self.helpname=self.winlabel
        #
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: self.OnClose(1)

        #
        self.winlabel='FragMolAttrib'
        self.model.winctrl.SetWin(self.winlabel,self)
        self.helpname=self.winlabel
        
        self.molnam=self.model.mol.name #wrkmolnam
        #self.mol=self.model.mol
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # Create Menu
        #self.menubar=self.MenuItems()
        #self.SetMenuBar(self.menubar)
        #self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.attriblst=self.parobj.attriblst#setctrl.FragmentAttributeList()
        
        #self.attribtipdic=self.model.setctrl.FragmentAttributeTipDic()
        self.attribvaluedic=self.parobj.valdic#self.model.setctrl.FragmentAttributeValueDic()
        #self.defaultdic=self.model.setctrl.FragmentAttributeDefaultDic()
        
        self.valuedic={}        
        # initilalize frgament attributes
        self.parobj.MakeFragAttribFromAtomAttrib()
        frgnam=self.parobj.ListFragmentName()
        if len(frgnam) <= 0: self.Return()
        self.valuedic['FRGNAM']=frgnam
        #
        self.attrib=self.attriblst[0]
        self.value=self.attribvaluedic[self.attrib][0]
        self.colorlst=self.ColorList()
        self.color='default'
        self.savattribdic={} 
        self.savactive=[]
              
        self.layerfile=''
        self.show=False
        self.shwlabel=True
        self.color='default'
        self.openviewwin=False
        #
        self.CreatePanel()

        #
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()
           
    def GetFragAttribsFromAtomAttrib(self):
        frgnamlst=self.ListFragmentName()
        if not self.model.frag.IsAttribute('FRGNAM'):
            self.model.frag.SetFragmentAttributeList('FRGNAM',frgnamlst)
        if not self.model.frag.IsAttribute('ICHARG'):
            frgchglst=self.ListFragmentCharge()
            self.model.frag.SetFragmentAttributeList('ICHARG',frgchglst)
        
    def ColorList(self):
        """ Color choice list
        
        """
        colorlst=['default','red','magenta','yellow','orange','brown','blue',
                  'cyan','green','purple','white','gray','black','palette']
        return colorlst
                
    def CreatePanel(self):
        #w=self.size[0]; h=self.size[1]
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        hcb=const.HCBOX
        self.attribpan=FragmentAttrib_Pan(self.panel,-1,[],[],self.parobj)
        
    def SetTargetFragment(self,appendfrglst):
        frglst=self.parobj.frglst0+appendfrglst
        
        const.CONSOLEMESSAGE('frglst='+str(frglst))
        
        self.cmbfrg.SetItems(frglst)
        if self.target in frglst:
            self.cmbfrg.SetStringSelection(self.target)
        else:
            self.cmbfrg.SetStringSelection(frglst[0])
            
    def OnReset(self,event):
        mess='No codes'
        lib.MessageBoxOK(mess,'OnDelete')
        return
    
        attrib=self.cmbattr.GetValue()
        if attrib == 'IACTAT':
            atmlst=range(len(self.model.mol.atm))
            self.SetActiveAtoms('False',atmlst)
        else:
            self.valuedic={}
            self.model.MakeFragAttribFromAtomAttrib()
            frgnam=self.model.frag.GetFragmentAttribute('FRGNAM')
            self.valuedic['FRGNAM']=frgnam
            frgchg=self.model.frag.GetFragmentAttribute('ICHARG')
            self.valuedic['ICHARG']=frgchg
    
    def OnRightClick(self,event):
        attr=self.cmbattr.GetValue()
        if self.attribtipdic.has_key(attr):
            tip=self.attribtipdic[attr]
            lib.MessageBoxOK(tip,'Tip of '+attr)
        
    def OnUndo(self,event):
        #print 'undo'
        attrib=self.cmbattr.GetValue()
        #print 'undo, attrib',attrib
        if attrib == 'IACTAT':
            if len(self.savactive) <= 0:
                self.model.Message2('Unable to undo')
                return
            value=self.savactive[0]
            if value == 'True': val='False'
            else: val='True'
            selatm=self.savactive[1]
            if len(selatm) > 0:
                self.SetActiveAtoms(val,selatm)
            self.savactive=[]
        else:
            if not self.savattribdic.has_key(attrib):
                self.model.Message2('Unable to undo')
                return
            attriblst=self.savattribdic[attrib]
            self.model.RecoverFragmentAttribute(attrib,attriblst)
            del self.savattribdic[attrib]
            self.model.Message2('fragment "'+attrib+'" has been recovered')
        
    def OnEnterValue(self,event):
        self.attrib=self.cmbattr.GetValue()
        #nmb=self.cmbval.GetSelection() # gives always -1
        try: nmb=self.attribvaluedic[self.attrib].index(self.value)
        except: nmb=-1
        self.value=self.cmbval.GetValue()
        if self.attrib == 'FRGNAM': 
            if nmb >= 0: self.valuedic[self.attrib][nmb]=self.value
        else: self.attribvaluedic[self.attrib].append(self.value)
        self.cmbval.SetItems(self.attribvaluedic[self.attrib])
        self.cmbval.SetValue(self.value)
        self.SetFragmentAttribute()

    def SetFragmentAttribute(self):
        self.frglst=self.model.ListSelectedFragment()
        if len(self.frglst) <= 0:
            self.model.Message('No selected fragments',0,'')
            return
            
        self.model.SetFragmentAttribute(frglst,self.attrib,self.value)
        self.model.frag.SetFragmentAttribute(selfrag,self.attrib,self.value)
        self.savfrglst=self.frglst
        nfrg=str(len(self.frglst))
        mess=self.attrib+'='+self.value+' was set for selected '+nfrg
        mess=mess+' fragments'
        self.model.Message()
        
    def OnShowLabel(self,event):
        self.shwlabel=self.ckblab.GetValue()
        
    def SetValueChoiceList(self):
        self.attrib=self.cmbattr.GetValue()
        choicelst=self.attribvaluedic[self.attrib]
        self.cmbval.SetItems(choicelst)
        self.value=choicelst[0]
        self.cmbval.SetValue(self.value)
        self.cmbval.Refresh()
    
    def OnChoiceAttrib(self,event):
        self.attrib=self.cmbattr.GetValue()
        self.SetValueChoiceList()
        
    def OnChoiceValue(self,event):
        self.value=self.cmbval.GetValue()
            
    def OnShowOn(self,event):
        attrib=self.cmbattr.GetValue()
        value=self.cmbval.GetValue()
        withlabel=self.ckblab.GetValue()
        if value.isdigit(): val=int(value)
        else: val=value
        self.model.RemoveDrawFragmentAttribute()
        self.model.DrawFragmentAttribute(attrib,val,withlabel,True)

    def OnShowOff(self,event):
        self.model.RemoveDrawFragmentAttribute()
            
    def OnClear(self,event):
        self.model.ClearLayer(999)
        
    def OnDelete(self,even):
        mess='No codes'
        lib.MessageBoxOK(mess,'OnDelete')
        return
    
    
        attrib=self.cmbattr.GetValue()        
        self.savattribdic[attrib]=self.model.GetFragmentAttribute(attrib)
        self.model.DeleteFragmentAttribute(attrib)

    def SetActiveAtoms(self,value,atmlst):
        if value == 'False': val=False
        elif value == 'True': val=True
        for i in atmlst: self.model.mol.atm[i].active=val
        if value == 'True':
            act='Active'
            nat,lst=self.model.ListActiveAtoms()
        else:
            act='Inactive'
            nat,lst=self.model.ListInactiveAtoms()
        mess='Number of '+act+' atoms='+str(nat)
        self.model.ConsoleMessage(mess)         
        
    def OnAssign(self,event):
        attrib=self.cmbattr.GetValue()
        value=self.cmbval.GetValue()
        value=value.strip()
        if attrib == 'IACTAT':
            nsel,selatm=self.model.ListSelectedAtom()

            if nsel <= 0:
                mess='No atom is selected'
                self.model.Message2(mess)
                return
            self.SetActiveAtoms(value,selatm)
            self.savactive=[value,selatm]
        else:
            value=self.cmbval.GetValue()      
            if value.isdigit(): value=int(value)
            frgnamlst=self.model.frag.ListFragmentName()
            if len(frgnamlst) <= 0:
                mess='No fragment is defined'
                self.model.Message2(mess)
                self.OnClose(1)
            frglst=self.model.frag.ListSelectedFragment()
            if len(frglst) <= 0:
                mess='No fragment is selected'
                self.model.Message2(mess)
                return
            attriblst=self.model.frag.GetFragmentAttribute(attrib)
            if len(attriblst) <= 0:
                default=self.defaultdic[attrib]
                self.model.frag,SetFragmentAttribute(frgnamlst,attrib,default)
            self.model.frag.SetFragmentAttribute(frglst,attrib,value)
        #
        if attrib == 'LAYER':
            target=self.model.frag.ListTargetAtoms()
            for i in target: self.model.mol.atm[i].layer=int(value)
        #
        self.NotifyToViewWin('FragAttribSetting')
            
    def ViewAttributes(self):
        if self.openviewwin:
            self.viewwin.SetFocus(); return
        # open edit attrtibute panel
        molnam=self.model.mol.name     
        
        self.frgnamlst=self.model.frag.frgnamlst       
        self.mode0lst=['!seq#','!name','!atom','!charge','!active','!layer',
                       '!BDA','!BAA']
        self.mode1lst=['!seq#','!name','!atom','!charge','!multip','!active',
                       '!layer','!wavefn','!basis set','!BDA','!BAA']
        self.widthdic={'seq#':45,'name':60,'#atom':55,'charge':55,'multip':50,
                       'active':50,'layer':50,'wave fn':60,'basis set':65,
                       'BDA':50,'BAA':50}

        labels=self.mode0lst
        widthlst=[45,60,55,55,50,50,50,50]
        frgdat=self.model.frag.MakeFragAttribData()
        selobjlst=[]
        for i in range(len(self.frg.frg)):
            selobjlst.append(self.frg.frg[i].frgatm)
        if len(frgdat) <= 0:
            mess='No fragment data.'
            lib.MessageBoxOK(mess,'FragAttribSettin(ViewAttributes)')
            return
        self.viewwin=subwin.GetInputFromUser_Frm(self,-1,
                   'View fragment attribs',model=self.model,
                   labels=labels,values=frgdat,cellwidth=widthlst,
                   retmethod=self.RetFromViewAttrib,selobj=selobjlst)

        self.openviewwin=True
        
    def RetFromViewAttrib(self,retmess,frgdat):
        if retmess == 'OnApply':
            for i in range(len(frgdat)):
                #fg=self.frg.frg[i]
                fgattr=self.mode.frag.GetFragObjNameDic(i)
                for j in range(1,len(frgdat[i])):
                    name=self.itemlst[j]; value=frgdat[i][j]
                    if name == 'atom': continue
                    fgattr[name]=value
                    #self.SetFragItem(name,value)
        elif retmess == 'OnClose': self.openviewwin=False

    def XXSetFragItem(self,fg,name,value):
        objdic={'name':fg.frgnam,'atom':fg.frgatm,'charge':fg.frgchg,
                'multip':fg.frgmulti,'active':fg.active,'layer':fg.layer,
                'wave fn':fg.frgwfn,'basis set':fg.frgbas,
                'BDA':fg.frgbda,'BAA':fg.frgbaa}
        
        self.frg.GetFragObjNameDic()
        objdic[name]=value

    def XXGetFragItemObj(self,fg,item):
        objdic={'name':fg.frgnam,'atom':fg.frgatm,'charge':fg.frgchg,
                'multip':fg.frgmulti,'active':fg.active,'layer':fg.layer,
                'wave fn':fg.frgwfn,'basis set':fg.frgbas,
                'BDA':fg.frgbda,'BAA':fg.frgbaa}
        strdat=str(objdic[item])
        if item == 'atom': strdat=str(len(objdic[item]))
        return strdat

    def MakeFragAttribData(self):
        
        frgdat=[]
        self.itemlst=[]
        for item in self.mode0lst:
            if item[:1] == '!': self.itemlst.append(item[1:])
            else: self.itemlst.append(item)
        nfrg=len(self.frg.frg)
        for i in range(nfrg):
            #fg=self.frg.frg[i]; 
            temp=[]
            objdic=self.frg.GetFragObjNameDic(i)

            temp.append(i+1)
            for j in range(1,len(self.itemlst)):
                item=self.itemlst[j]
                if item == 'atom': temp.append(len(objdic[item]))
                else: temp.append(objdic[item]) #self.GetFragItemObj(fg,item))
            frgdat.append(temp)
        return frgdat
        
    def OnPaint(self,event):
        event.Skip()

    def Return(self):
        mess='No fragment is defined.'
        lib.MessageBoxOK(mess,self.title)
        self.OnClose(1)
        #raise StandardError("No fragment is defined")
        
    def OnClose(self,event):      
        try: self.model.DrawLayer(False)
        except: pass
        try: self.winctrl.Close(self.winlabel)
        except: pass
        self.openviewwin=False
        self.Destroy()

    def XXReadLayer(self,layerfile):
        if len(layerfile) <= 0: return
        f=open(layerfile,"r")
        dat=[]
        for s in f.readlines():
            s=s.replace(',',''); d=s.split()
            for i in d:
                dat.append(int(i))
        f.close() 
        nd=len(dat)
        i=-1
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            i += 1; atom.layer=dat[i]
        err=0
        if i+1 != nd: err=1
        if err:
            mess='Error (ReadLayer): the number of layer data is inconsistent'
            mess=mess+' with atoms.'
            lib.MessageBoxOK(mess,"")   
        else:
            if self.winctrl.Get('drawlayer'): self.model.DrawMol(True)
            mess='read layer data from file='+layerfile
            self.model.ConsoleMessage(mess)

    def XXWriteLayer(self,layerfile):
        if len(layerfile) <= 0: return
        dat=[]
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            dat.append(atom.layer)
        mess='write layer data on file='+layerfile
        self.model.ConsoleMessage(mess)
        rwfile.WriteIntDat(layerfile,"",dat,20,5,10)
    
    def NotifyToViewWin(self,myname,destwindic={}):
        winlabel='FragAttibView'
        winobj=self.viewwin
        wx.PostEvent(winobj,subwin.ThreadEvent(winlabel,myname,''))

    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
        
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
        
    def MenuItems(self):
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        submenu.Append(-1,"Read fmo xyz file","Open FMO xyz file")
        submenu.AppendSeparator() 
        submenu.Append(-1,"Save attribute as","Save attribute data")
        submenu.AppendSeparator() 
        submenu.Append(-1,"Close","Close the panel")
        menubar.Append(submenu,'File')
        # View
        submenu=wx.Menu()
        submenu.Append(-1,"Fragment attributes","view attributes")
        menubar.Append(submenu,'View')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,"Document","Help document")
        submenu.Append(-1,"Tutorial","Tutorial")
        menubar.Append(submenu,'Help')
        #
        return menubar        

    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        
        if item == "Close":
            self.OnClose(1)
            
        elif item == "Read layer file":
            wildcard='xyz file(*.xyz)|*.xyz|All(*.*)|*.*'
            name=self.model.mol.name+".lay"
            filename=lib.GetFileName(self,wildcard,"r",True,name)
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                layerdat=rwfile.ReadLayer(filename)
                for i in xrange(len(self.model.mol.atm)):
                    if self.model.mol.atm[i].elm == "XX": continue
                    self.model.mol.atm[i].layer=layerdat[i]
                #???if self.drawitems.Get('DrawLayer'): self.model.DrawMol(True)
                self.model.DrawMol(True)
                mess='read layer data from file='+filename
                self.model.ConsoleMessage(mess)
                self.layerfile=filename
        
        elif item == "Save attribte as":
            wildcard='layer file(*.lay)|*.lay|All(*.*)|*.*'
            name=self.model.mol.name+".lay"
            filename=lib.GetFileName(self,wildcard,"w",True,name)
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                title="# Assinment of atoms in layer. Mol name="
                title=title++self.model.mol.name
                title=title+ ". Number of atoms="+str(len(self.model.mol.atm))
                rwfile.WriteLayerFile(filename,title)
                mess='Write layer data on file='+filename
                self.model.ConsoleMessage(mess)
                self.layerfile=filename
        
        elif item == "Fragment attributes": self.ViewAttributes()
        elif item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()            

class FragMolResidue_Frm(wx.Frame):
    """ Fragment non-peptide by semi-auto """
    def __init__(self,parent,id,title='',parobj=None,winpos=[],winsize=[]): #,filelst=[]):
        """ 
        :param obj parent: window object
        :param int id: id of the object
        :param obj parobj: parent object
        :param lst winpos: window position
        :param lst winsize: window size
        """
        if len(title) <= 0: self.title='Auto fragment'
        else: self.title=title
        if len(winpos) <= 0: winpos=lib.WinPos(parent)
        if len(winsize) <= 0: self.winsize=lib.WinSize([320,390])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=self.winsize,
                style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.RESIZE_BORDER)
        # 
        self.parent=parent # assume 'mdlwin'
        self.parobj=parobj
        if parobj == None:
            mess="Need parent object!"
            lib.MessageBoxOK(mess,'FragMolResidue_Frm')
            self.OnClose(1)
        self.model=self.parobj.model
        # 
        self.winlabel='FragMolResidue'
        try: self.model.winctrl.SetWin(self.winlabel,self)
        except: pass
        self.helpname=self.winlabel
        # Check if 'mol' object is availabel 
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: self.OnClose(1)
        # attach FU icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # display molecule name on window title
        self.SetTitle(self.title+'['+self.model.mol.name+']')
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        # default BAA
        self.frglst0=self.parobj.frglst0
        self.frgminsize=self.parobj.frgminsize #10
        self.bdaatm='"Csp3"'
        self.baaatm='"Csp3","Csp2"," N"," O"'
        self.bdaatmlst=[]
        self.baaatmlst=[]
        self.savdir=os.getcwd()
        self.filetype=None
        self.attriblst=self.parobj.attriblst
        self.attrib=0 #0:charge,1:layer,2:active; 3:spin
        self.valdic=self.parobj.valdic
        self.vallst=[]       
        self.frgnam='selected'
        # create panel
        self.CreatePanel()
        #
        self.SetValuesToWidgets()
        ###self.SetTargetFragment([])
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()
    
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)         
    
    def CreatePanel(self):
        """ Create panel """
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=(0,0),size=(w,h))
        self.panel.SetBackgroundColour("light gray")

        hbtn=25; hcb=const.HCBOX
        xpos=0; ypos=0
        yloc=5
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc += 5
        wx.StaticText(self.panel,-1,"Fragmentation of non-peptide",pos=(10,yloc),
                      size=(200,18)) 
        yloc += 20
        self.ckbres=wx.CheckBox(self.panel,-1,"Include peptide residues",
                                pos=(20,yloc),size=(150,20))
        self.ckbres.Bind(wx.EVT_CHECKBOX,self.OnIncludeAARes)
        yloc += 25
        wx.StaticText(self.panel,-1,"Fragment min. size:",pos=(20,yloc),
                      size=(120,18)) 
        self.tclmin=wx.TextCtrl(self.panel,-1,pos=(150,yloc),
                                size=(50,20),style=wx.TE_PROCESS_ENTER)
        yloc += 25
        wx.StaticText(self.panel,-1,"BDA atoms:",pos=(20,yloc),size=(80,18)) 
        xloc=90
        self.tclbda=wx.TextCtrl(self.panel,-1,pos=(100,yloc),
                        size=(170,20),style=wx.TE_PROCESS_ENTER)
        yloc += 25
        wx.StaticText(self.panel,-1,"BAA atoms:",pos=(20,yloc),size=(80,18)) 
        xloc=90
        self.tclbaa=wx.TextCtrl(self.panel,-1,pos=(100,yloc),
                        size=(170,20),style=wx.TE_PROCESS_ENTER)
        yloc += 30
        xloc=60
        # buttons
        self.btnview=wx.Button(self.panel,-1,"Clear BDA",pos=(xloc,yloc),
                              size=(80,20))
        self.btnview.Bind(wx.EVT_BUTTON,self.OnClearBDA)
        #self.btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        btnaply=wx.Button(self.panel,-1,"Apply",pos=(xloc+100,yloc),
                              size=(80,20))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        ###
        hcmb=25
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        winpos=[0,yloc]
        self.attribpan=FragmentAttrib_Pan(self.panel,-1,winpos,[],self.parobj)
        """
        wx.StaticText(self.panel,-1,"Fragment attribute setting",pos=(10,yloc),
                      size=(200,18)) 
        yloc += 20
        wx.StaticText(self.panel,-1,"Attribute:",pos=(20,yloc),
                      size=(70,18)) 
        xloc=90
        self.cmbattrib=wx.ComboBox(self.panel,-1,'',choices=[], \
                       pos=(xloc,yloc-2),size=(70,hcmb),style=wx.CB_READONLY)                      
        self.cmbattrib.Bind(wx.EVT_COMBOBOX,self.OnAttrib)

        wx.StaticText(self.panel,-1,"value=",pos=(xloc+80,yloc),
                      size=(45,18)) 

        self.cmbvalue=wx.ComboBox(self.panel,-1,'',choices=[], \
                               pos=(xloc+130,yloc-2),size=(60,hcmb))
        yloc += 25
        xloc=40
        wx.StaticText(self.panel,-1,"Target fragment:",pos=(xloc,yloc),
                      size=(95,18)) 
        frglst=['all','selected','---']#+self.frgnamlst[polypep,or non-pep]
        self.cmbfrg=wx.ComboBox(self.panel,-1,'',choices=[], \
                    pos=(xloc+100,yloc-2),size=(70,hcmb),style=wx.CB_READONLY)                      
        btnattrib=wx.Button(self.panel,-1,"Apply",pos=(240,yloc),
                       size=(50,20))
        btnattrib.Bind(wx.EVT_BUTTON,self.OnApplyAttrib)        
        ###
        """
        yloc += 75 #+= 28
        lin1=wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10        
        wx.StaticText(self.panel,-1,"Save BDA as",pos=(10,yloc),
                      size=(80,18)) 
        xloc=90
        self.rbtgenbda=wx.RadioButton(self.panel,-1,"General",
                       pos=(xloc,yloc-2),size=(60,18),style=wx.RB_GROUP)
        self.rbtspcbda=wx.RadioButton(self.panel,-1,"Specific",
                                      pos=(xloc+70,yloc-2),size=(60,18))
        self.rbtgenbda.Bind(wx.EVT_RADIOBUTTON,self.OnGenBDAFile)
        self.rbtspcbda.Bind(wx.EVT_RADIOBUTTON,self.OnGenBDAFile)
        btnsav=wx.Button(self.panel,-1,"Save",pos=(xloc+150,yloc),
                         size=(50,20))
        btnsav.Bind(wx.EVT_BUTTON,self.OnSaveBDA)

        yloc += 25
        wx.StaticText(self.panel,-1,"Directry:",pos=(20,yloc),
                      size=(70,18)) 

        self.tcldir=wx.TextCtrl(self.panel,-1,pos=[90,yloc],
                        size=[140,20],style=wx.TE_PROCESS_ENTER)
        btndir=wx.Button(self.panel,-1,"Browse",pos=(240,yloc),
                         size=(50,20))
        btndir.Bind(wx.EVT_BUTTON,self.OnBrowseDir)
        yloc += 25
        wx.StaticText(self.panel,-1,"File name:",pos=(20,yloc),
                      size=(70,18)) 
        self.tclfile=wx.TextCtrl(self.panel,-1,pos=[90,yloc],
                        size=[140,20],style=wx.TE_PROCESS_ENTER)
        btnfile=wx.Button(self.panel,-1,"Browse",pos=(240,yloc),
                              size=(50,20))
        btnfile.Bind(wx.EVT_BUTTON,self.OnBrowseFile)
        
    def SetValuesToWidgets(self):
        self.tcldir.SetValue(self.savdir)
        self.tclmin.SetValue(str(self.frgminsize))
        self.tclbda.SetValue(self.bdaatm)
        self.tclbaa.SetValue(self.baaatm)
        # attribute
        """
        self.cmbattrib.SetItems(self.attriblst)
        self.cmbattrib.SetStringSelection(self.attriblst[self.attrib])
        self.vallst=self.valdic[self.attriblst[self.attrib]]
        self.cmbvalue.SetItems(self.vallst)
        self.cmbvalue.SetStringSelection(self.vallst[0])
        """
    
    def SetTargetFragment(self,frglst):
        self.attribpan.SetTargetFragment(frglst)
        
        
        """
        self.frglst=self.frglst0+frglst
        self.cmbfrg.SetItems(self.frglst)
        if self.frgnam in self.frglst:
            self.cmbfrg.SetStringSelection(self.frgnam)
        else:
            self.cmbfrg.SetStringSelection(self.frglst[0])
        """
    def OnApply(self,event):
        minsize=self.tclmin.GetValue()
        try: minsize=int(minsize)
        except:
            mess='Wrong frament min size data.'
            lib.MessageBoxOK(mess,'FragmentAuto_Frm(OnFragment)')
            return
        bdaatm=self.tclbda.GetValue().strip()
        baaatm=self.tclbaa.GetValue().strip()
        if len(bdaatm) <= 0 or len(baaatm) <= 0:
            mess='Please input BDA/BAA atoms.'
            lib.MessageBoxOK(mess,'FragmentAuto_Frm(OnFragment)')
            return
        self.bdaatmlst=lib.GetStringBetweenQuotation(bdaatm)
        self.baaatmlst=lib.GetStringBetweenQuotation(baaatm)        
        #
        aares=self.ckbres.GetValue()
        self.parobj.FragmentAtBDA(minsize=minsize,bdaatmlst=self.bdaatmlst,
                                baaatmlst=self.baaatmlst,aares=aares,drw=True)
        #
        self.SetDefaultFileName()
    
    def OnApplyAttrib(self,event):
        value=self.cmbvalue.GetStringSelection()
        target=self.cmbfrg.GetStringSelection()
        # attrib
        attrib=self.cmbattrib.GetStringSelection()
        # value
        value=int(value)
        # target fragments
        if target == 'all':
            frglst=self.parobj.ListFragmentName('all')
        elif target == 'selected':
            frglst=self.parobj.ListSelectedFragment()
        elif target == 'non-peptide':
            frglst=self.parobj.ListFragmentName(kind='chm')
            
        else: # a fragment
            frglst=[target]
            
        if len(frglst) <= 0:
            mess='No target fragments.'
            lib.MessageBoxOK(mess,'Fragmentation_Frm(OnApplyAtrib)')
            return            

        self.parobj.SetFragAttribToMolObj(frglst,attrib,value)
        
    def OnAttrib(self,event):
        """ Set attribute values """
        attrib=self.cmbattrib.GetStringSelection()
        idx=self.attriblst.index(attrib)
        vallst=self.valdic[attrib]
        self.cmbvalue.SetItems(vallst)
        self.cmbvalue.SetStringSelection(vallst[0])

    def XXSetTargetFragment(self,frglst):
        self.frglst=self.frglst0+frglst
        self.cmbfrg.SetItems(self.frglst)
        if self.frgnam in self.frglst:
            self.cmbfrg.SetStringSelection(self.frgnam)
        else:
            self.cmbfrg.SetStringSelection(self.frglst[0])
                        
    def SetDefaultFileName(self):
        if self.rbtgenbda.GetValue(): # general res BDA file
            default=self.model.mol.atm[0].resnam; self.filetype='general'
        else: # specific
            resdat=lib.ResDat(self.model.mol.atm[0])
            default=lib.MakeFileNameFromResDat(resdat)
            self.filetype='specific'
        #
        default=default+'.bda'
        head,default=os.path.split(default)
        self.tclfile.SetValue(default)
    
    def OnGenBDAFile(self,event):
        self.SetDefaultFileName()
        
    def OnInputBDA(self,event):
        pass
    
    def OnInputBAA(self,event):
        pass
    
    def OnIncludeAARes(self,event):
        obj=event.GetEventObject()
        if obj.GetValue():
            mess='Warning: May take a very long time for a molecule with '
            mess=mess+'several hundreds atoms.\n'
            mess=mess+'Use fragment polypeptide menu and manual BDA setting.'
            lib.MessageBoxOK(mess,'FragmentAuto')
        
    def OnClearBDA(self,event):
        self.parobj.ClearBDA('all')
        self.tclfile.SetValue('')
    
    def OnReset(self,event):
        mess='Reset molecule object.'
        lib.MessageBoxOK(mess,'FragmentAuto_Frm')
        self.Reset()    
    
    def Reset(self):
        self.SetTitle(self.title+' ['+self.model.mol.name+']')
        self.SetValuesToWidgets()
        
    def OnBrowseDir(self,event):
        dirname=lib.GetDirectoryName()
        if len(dirname) <= 0: return
        self.tcldir.SetValue(dirname)
        
    def OnBrowseFile(self,event):
        """ Open filer """
        default=self.parobj.DefaultBDAFileName()
        filename=self.parobj.GetBDAFileNameForSave(default)
        if len(filename) is None: return            
        head,filename=os.path.split(filename)
        self.tclfile.SetValue(filename)
        
    def OnSaveBDA(self,event):
        nochgfrg=self.parobj.ListNoneChargeFragment()
        if len(nochgfrg) > 0:
            mess='There are '+str(len(nochgfrg))+' unassigned charges in '
            mess=mess+'fragments.\n'
            mess=mess+'Are they all zeros?'
            ans=lib.MessageBoxYesNo(mess,'Fragment(SaveBDA')
            if ans: self.SetAllFragmentCharges(0)
            else: return
        filename=self.tclfile.GetValue()
        if filename.strip() == '':
            mess='Please enter file name.'
            lib.MessageBoxOK('FragmentAuto_Frm(OnSaveBAD)')
            return
        dirname=self.tcldir.GetValue()
        filename=os.path.join(dirname,filename)
        self.parobj.SaveBDA(filename=filename,filetype=self.filetype)
        self.tclfile.SetValue('')

    def OnNotify(self,event):
        """ Not used. 21Feb2016 """
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles': self.Reset()
        
    def OnClose(self,event):
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        try: self.parobj.frgauto=None
        except: pass
        self.Destroy()
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
        
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
        
    def MenuItems(self):
        """ Menu items """
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        submenu.Append(-1,"View fragment data","View data")
        submenu.AppendSeparator()
        submenu.Append(-1,"Clear residue BDA files","Remove residue files")
        submenu.AppendSeparator()
        submenu.Append(-1,"Close","Close")
        menubar.Append(submenu,'File')
        # Help menu
        submenu=wx.Menu()
        submenu.Append(-1,"Document","Open help message")
        submenu.Append(-1,"Tutorial","Open help message")
        menubar.Append(submenu,'Help')
        return menubar

    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        # File
        if item == "Save BDA": self.SaveBDA()
        #elif item == "Open log files": self.OpenLogFiles()
        elif item == "View fragment data": self.parobj.ViewFragmentData()
        elif item == "Clear residue BDA files": 
            self.parobj.ClearResidueBDAFiles()
        elif item == "Close": self.OnClose(1)
        # Help menu items
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()   
            

class FragMolAllInOne_Frm(wx.Frame):
    """ All-in-one Fragment panel """
    def __init__(self,parent,id,title='',parobj=None,winpos=[],winsize=[]): #,filelst=[]):
        """ 
        :param obj parent: window object
        :param int id: id of the object
        :param obj parobj: parent object
        :param lst winpos: window position
        :param lst winsize: window size
        """
        if len(title) <= 0: self.title='FragMolAllInOne'
        else: self.title=title
        if len(winpos) <= 0: winpos=lib.WinPos(parent)
        if len(winsize) <= 0: self.winsize=lib.WinSize([310,410])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,
                size=self.winsize,style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        # 
        self.parent=parent # assume 'mdlwin'
        self.parobj=parobj
        if parobj == None:
            mess="Need parent object!"
            lib.MessageBoxOK(mess,'FragMolAllInOne_Frm')
            self.OnClose(1)
        self.model=self.parobj.model
        # 
        self.winlabel='FragMolAllInOne'
        self.helpname=self.winlabel
        try: self.model.winctrl.SetWin(self.winlabel,self)
        except: pass
        self.helpname=self.winlabel
        # Check if 'mol' object is availabel 
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: self.OnClose(1)
        # attach FU icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # display molecule name on window title
        self.SetTitle(self.title+'['+self.model.mol.name+']')
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        #self.frglst=self.frglst0+self.parobj.frgnamlst
        self.frglst0=['selected','non-peptide','all']
        self.frgnam='all'
        # default BAA
        self.frgminsize=self.parobj.frgminsize #10
        self.baaopt=['Csp3','Csp2','N','O']
        self.baalst=[1,1,0,0]
        self.baabtn=[]
        self.pepfrgsize=0 # peptide res size, 0:1res,1:1resxGly,2:2res
        self.frgminsize=self.parobj.frgminsize # non-peptide size
        self.bdafiletype=1 # 0:entire,1:resbda
        self.attriblst=parobj.attriblst
        self.attrib=0 #0:charge,1:layer,2:active; 3:spin
        self.valdic=parobj.valdic #{}
        self.vallst=[]       
        self.frgnam='selected'
        self.bdamode=False
        # create panel
        self.CreatePanel()
        #
        self.SetValueToWidgets()
        ##self.SetTargetFragment([])
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()
    
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)         
    
    def CreatePanel(self):
        """ Create panel """
        
        def Buttons(name,xloc,yloc):
            btnclear=wx.Button(self.panel,-1,"Clear BDA",pos=(xloc,yloc-2),
                                  size=(80,20))
            btnclear.Bind(wx.EVT_BUTTON,self.OnClearBDA)
            btnclear.SetName(name)
            #self.btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
            btnapply=wx.Button(self.panel,-1,"Apply",pos=(xloc+100,yloc-2),
                                  size=(60,20))
            btnapply.Bind(wx.EVT_BUTTON,self.OnApply)
            btnapply.SetName(name)
            #btndic[name]=[btnaplly,btnclear]
        
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=(0,0),size=(w,h))
        self.panel.SetBackgroundColour("light gray")

        hbtn=25; hcb=const.HCBOX
        wcmb=80; hcmb=25
        xpos=0; ypos=0
        yloc=5
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #btnrset.Hide()
        yloc += 5
        wx.StaticText(self.panel,-1,"Fragmentation",pos=(10,yloc),
                      size=(120,18)) 
        yloc += 25
        wx.StaticText(self.panel,-1,"Polypeptide:",pos=(20,yloc),
                      size=(100,18)) 
        xloc=120
        Buttons('polypeptide',xloc,yloc)

        yloc += 20
        xloc=40
        wx.StaticText(self.panel,-1,"fragment into(per fragment),",pos=(xloc,yloc),
                              size=(200,18))         

        yloc += 20; xloc=60
        self.rbtres0=wx.RadioButton(self.panel,-1,'1 res',pos=(xloc,yloc),
                                    style=wx.RB_GROUP)
        self.rbtres1=wx.RadioButton(self.panel,-1,'1 res except GLY',
                                    pos=(xloc+50,yloc))
        self.rbtres2=wx.RadioButton(self.panel,-1,'2 res',
                                    pos=(xloc+170,yloc))
        yloc += 20
        wx.StaticLine(self.panel,pos=(40,yloc),size=(w-80,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        wx.StaticText(self.panel,-1,"Non-peptide:",pos=(20,yloc),
                      size=(100,18)) 
        xloc=120
        Buttons('non-peptide',xloc,yloc)
        yloc += 25; xloc=40
        wx.StaticText(self.panel,-1,"Fragment min. size(number of atoms):",pos=(xloc,yloc),
                      size=(210,18)) 
        self.tclmin=wx.TextCtrl(self.panel,-1,pos=(xloc+220,yloc-2),
                                size=(30,20),style=wx.TE_PROCESS_ENTER)
        yloc += 25; xloc=40
        wx.StaticText(self.panel,-1,"BAA atoms:",pos=(xloc,yloc),size=(80,18)) 
        xloc=110
        ckbsp3=wx.CheckBox(self.panel,-1,"Csp3",pos=[xloc,yloc-2],
                                size=[50,20])
        self.baabtn.append(ckbsp3)
        ckbsp2=wx.CheckBox(self.panel,-1,"Csp2",pos=[xloc+55,yloc-2],
                                size=[50,20])
        self.baabtn.append(ckbsp2)
        ckbn=wx.CheckBox(self.panel,-1,"N",pos=[xloc+110,yloc-2],
                                size=[40,20])
        self.baabtn.append(ckbn)
        ckbo=wx.CheckBox(self.panel,-1,"O",pos=[xloc+150,yloc-2],
                                size=[40,20])
        self.baabtn.append(ckbo)
        yloc += 25
        wx.StaticLine(self.panel,pos=(40,yloc),size=(w-80,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        wx.StaticText(self.panel,-1,"By BDA file:",pos=(20,yloc),
                      size=(100,18)) 
        xloc=120
        Buttons('byBDA',xloc,yloc)
        yloc += 25; xloc=40
        btnopen=wx.Button(self.panel,-1,"Open",pos=(xloc,yloc-2),
                                  size=(50,20))
        btnopen.Bind(wx.EVT_BUTTON,self.OnOpenFile)

        #wx.StaticText(self.panel,-1,"Open file of",pos=(xloc,yloc-2),
        #              size=(70,20))
        self.rbtmolbda=wx.RadioButton(self.panel,-1,'Entire BDA',
                                      pos=(xloc+60,yloc),style=wx.RB_GROUP)
        self.rbtresbda=wx.RadioButton(self.panel,-1,'residue BDA file',
                                    pos=(xloc+150,yloc))
        yloc += 25
        wx.StaticLine(self.panel,pos=(40,yloc),size=(w-80,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        wx.StaticText(self.panel,-1,"By hand: BDA setting mode",pos=(20,yloc),
                      size=(180,18)) 
        xloc=200
        self.btnmode=wx.ToggleButton(self.panel,-1,"On/Off",pos=(xloc,yloc-2),
                              size=(70,20))
        self.btnmode.Bind(wx.EVT_TOGGLEBUTTON,self.OnBDAMode)
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                           style=wx.LI_HORIZONTAL)
        yloc += 10
        winpos=[0,yloc]
        self.attribpan=FragmentAttrib_Pan(self.panel,-1,winpos,[],self.parobj)
        """
        wx.StaticText(self.panel,-1,"Fragment attribute setting",pos=(10,yloc),
                      size=(200,18)) 
        yloc += 20
        wx.StaticText(self.panel,-1,"Attribute:",pos=(20,yloc),
                      size=(70,18)) 
        xloc=90
        self.cmbattrib=wx.ComboBox(self.panel,-1,'',choices=[], \
                       pos=(xloc,yloc-2),size=(70,hcmb),style=wx.CB_READONLY)                      
        self.cmbattrib.Bind(wx.EVT_COMBOBOX,self.OnAttrib)
        wx.StaticText(self.panel,-1,"value=",pos=(xloc+80,yloc),
                      size=(45,18)) 

        self.cmbvalue=wx.ComboBox(self.panel,-1,'',choices=[], \
                               pos=(xloc+130,yloc-2),size=(60,hcmb))
        yloc += 25
        xloc=40
        wx.StaticText(self.panel,-1,"Target fragment:",pos=(xloc,yloc+2),
                      size=(95,18)) 
        self.cmbfrg=wx.ComboBox(self.panel,-1,'',choices=[], \
                    pos=(xloc+100,yloc),size=(80,hcmb),style=wx.CB_READONLY)                      
        btnattrib=wx.Button(self.panel,-1,"Apply",pos=(240,yloc),
                       size=(50,20))
        btnattrib.Bind(wx.EVT_BUTTON,self.OnApplyAttrib)
        """
    def SetValueToWidgets(self):
        # frgmant names
        # non-peptide minimum fragment size
        self.tclmin.SetValue(str(self.frgminsize))
        # BAA type option
        for i in range(len(self.baabtn)):
            obj=self.baabtn[i]
            if self.baalst[i] == 1: obj.SetValue(True)
            else: obj.SetValue(False)
        # polypeptide fragment size
        if self.pepfrgsize == 0: self.rbtres0.SetValue(True)
        elif self.pepfrgsize == 1: self.rbtres1.SetValue(True)
        elif self.pepfrgsize == 2: self.rbtres2.SetValue(True)
        # BDA file type
        if self.bdafiletype == 0: self.rbtmolbda.SetValue(True)
        else: self.rbtresbda.SetValue(True)
        # attribute
        """
        self.cmbattrib.SetItems(self.attriblst)
        self.cmbattrib.SetStringSelection(self.attriblst[self.attrib])
        self.vallst=self.valdic[self.attriblst[self.attrib]]
        self.cmbvalue.SetItems(self.vallst)
        self.cmbvalue.SetStringSelection(self.vallst[0])
        """
        # bda setting mode
        self.btnmode.SetValue(self.bdamode)
        
    def SetTargetFragment(self,frglst):
        self.attribpan.SetTargetFragment(frglst)
        """
        self.frglst=self.frglst0+frglst
        self.cmbfrg.SetItems(self.frglst)
        if self.frgnam in self.frglst:
            self.cmbfrg.SetStringSelection(self.frgnam)
        else:
            self.cmbfrg.SetStringSelection(self.frglst[0])
        """    
    def OnApply(self,event):
        obj=event.GetEventObject()
        name=obj.GetName()
        if name == 'polypeptide':
            if self.rbtres0.GetValue(): resopt=0
            elif self.rbtres1.GetValue(): resopt=1
            elif self.rbtres2.GetValue(): resopt=3
            self.parobj.FragmentPolypeptide(resopt)
        elif name == 'non-peptide':
            baadic={'Csp3':0,'Csp2':1,'N':2,'O':3}; baaopt=[0,0,0,0]
            for ckbobj in self.baabtn:
                if ckbobj.GetValue(): 
                    baa=ckbobj.GetLabel();  baaopt[baadic[baa]]=1
            minsize=int(self.tclmin.GetValue())
            self.parobj.FragmentAtCsp3(minsize,baaopt)
        elif name == 'byBDA': 
            
            if self.rbtmolbda.GetValue(): self.bdafiletype=0
            if self.rbtresbda.GetValue(): self.bdafiletype=1
            self.parobj.SetResidueBDAs()

    def OnOpenFile(self,event):    
        if self.rbtmolbda.GetValue(): self.parobj.OpenBDAFiles(mol=True)
        elif self.rbtresbda.GetValue(): self.parobj.OpenBDAFiles(mol=False)
    
    def OnBDAMode(self,event):
        bChecked=self.btnmode.GetValue()
        self.model.menuctrl.OnFMO("Manual BDA setting",bChecked)       
        
    def OnClearBDA(self,event):
        obj=event.GetEventObject()
        name=obj.GetName()
        if name == 'polypeptide': self.parobj.ClearBDA('aa')
        elif name == 'non-peptide': self.parobj.ClearBDA('chm')
        elif name == 'byBDA': self.parobj.ClearBDA('selected')
        
    def OnApplyAttrib(self,event):
        value=self.cmbvalue.GetStringSelection()
        target=self.cmbfrg.GetStringSelection()
        # attrib
        attrib=self.cmbattrib.GetStringSelection()
        # value
        value=int(value)
        # target fragments
        if target == 'all':
            frglst=self.parobj.ListFragmentName()
        elif target == 'selected':
            frglst=self.parobj.ListSelectedFragment()
        elif target == 'non-peptide':
            frglst=self.parobj.ListFragmentName(kind='chm')
            
        else: # a fragment
            frglst=[target]
            
        if len(frglst) <= 0:
            mess='No target fragments.'
            lib.MessageBoxOK(mess,'Fragmentation_Frm(OnApplyAtrib)')
            return            

        self.parobj.SetFragAttribToMolObj(frglst,attrib,value)
        
    def OnAttrib(self,event):
        """ Set attribute values """
        attrib=self.cmbattrib.GetStringSelection()
        idx=self.attriblst.index(attrib)
        vallst=self.valdic[attrib]
        self.cmbvalue.SetItems(vallst)
        self.cmbvalue.SetStringSelection(vallst[0])
            
    def OnNotify(self,event):
        pass
        
    def OnReset(self,event):
        pass
        
    def OnClose(self,event):
        try: self.parobj.frgpan=None
        except: pass
        self.Destroy()

    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)

    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
        
    def MenuItems(self):
        """ Menu items """
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        submenu.Append(-1,"View fragment data","View BDA/Fragment data")
        submenu.Append(-1,"Save BDA","Save BDA")
        submenu.AppendSeparator()
        submenu.Append(-1,"Clear residue BDA files","Clear resdiue BDA files")
        submenu.AppendSeparator()
        submenu.Append(-1,"Close","Close")
        menubar.Append(submenu,'File')
        # Help menu
        submenu=wx.Menu()
        submenu.Append(-1,"Document","Open help message")
        submenu.Append(-1,"Tutorial","Open help message")
        menubar.Append(submenu,'Help')
        return menubar

    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        # File
        if item == "View fragment data": self.parobj.ViewFragmentData()
        elif item == "Save BDA": self.SaveBDA()
        #elif item == "Open log files": self.OpenLogFiles()
        elif item == "Clear residue BDA files": 
            self.parobj.ClearResidueBDAFiles()
        elif item == "Close": self.OnClose(1)
        # Help menu items
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()   
            
class FragmentAttrib_Pan(wx.Panel):
    def __init__(self,parent,id,winpos,winsize,parobj) : #,resnamlst=[]):
        title='Fragment attrib panel'
        if len(winpos) <= 0: winpos=[0,5]
        winsize=list(winsize)
        if len(winsize) <=0: winsize=[310,75]
        if winsize[0] < 310: winsize[0]=310
        if winsize[1] < 70: winsize[1]=70
        wx.Panel.__init__(self,parent,id,pos=winpos,size=winsize)
        #self.setfile=parent.model.setfile
        self.panel=parent # parent window object
        self.parobj=parobj # "Fragment" instance
        #               
        self.SetBackgroundColour("light gray")
        #
        self.attrib=None
        self.target=self.parobj.frglst0[0]
        # 
        nonchg=self.parobj.ListNoneChargeFragment()
        self.CreateButtons()
        
        self.SetTargetFragment(nonchg)
        
        
    def CreateButtons(self):    
        hcmb=25
        yloc=0
        wx.StaticText(self,-1,"Fragment attribute setting",pos=(10,yloc),
                      size=(200,18)) 
        yloc += 20
        wx.StaticText(self,-1,"Attribute:",pos=(20,yloc),
                      size=(70,18)) 
        xloc=90
        self.cmbattrib=wx.ComboBox(self,-1,'',choices=[], \
                       pos=(xloc,yloc-2),size=(70,hcmb),style=wx.CB_READONLY)                      
        self.cmbattrib.Bind(wx.EVT_COMBOBOX,self.OnAttrib)
        wx.StaticText(self,-1,"value=",pos=(xloc+80,yloc),
                      size=(45,18)) 
        self.cmbvalue=wx.ComboBox(self,-1,'',choices=[], \
                               pos=(xloc+130,yloc-2),size=(60,hcmb))
        yloc += 25; xloc=40
        wx.StaticText(self,-1,"Target fragment:",pos=(xloc,yloc+2),
                      size=(95,18)) 
        self.cmbfrg=wx.ComboBox(self,-1,'',choices=[], \
                    pos=(xloc+100,yloc),size=(80,hcmb),style=wx.CB_READONLY)                      
        btnattrib=wx.Button(self,-1,"Apply",pos=(240,yloc),
                       size=(50,20))
        btnattrib.Bind(wx.EVT_BUTTON,self.OnApplyAttrib)
        # Set parmas
        self.SetWidgetItems()

    def SetWidgetItems(self):
        # items from parobj
        attriblst=self.parobj.attriblst
        self.attrib=attriblst[0]
        self.cmbattrib.SetItems(attriblst)
        self.cmbattrib.SetStringSelection(self.attrib)
        vallst=self.parobj.valdic[self.attrib]
        self.cmbvalue.SetItems(vallst)
        self.cmbvalue.SetStringSelection(vallst[0])
        # fragment items
        self.SetTargetFragment([])
        
    def SetTargetFragment(self,appendfrglst):
        self.attrib=self.cmbattrib.GetStringSelection()
        if self.attrib == 'charge': frglst=self.parobj.frglst0+appendfrglst
        else: frglst=self.parobj.frglst0
        self.cmbfrg.SetItems(frglst)
        if self.target in frglst:
            self.cmbfrg.SetStringSelection(self.target)
        else:
            self.cmbfrg.SetStringSelection(frglst[0])
    
    def OnAttrib(self,event):
        """ Set attribute values """
        self.attrib=self.cmbattrib.GetStringSelection()
        idx=self.parobj.attriblst.index(self.attrib)
        vallst=self.parobj.valdic[self.attrib]
        self.cmbvalue.SetItems(vallst)
        self.cmbvalue.SetStringSelection(vallst[0])
        if self.attrib == 'charge':
            nonchg=self.parobj.ListNoneChargeFragment()
        else: nonchg=[]
        self.SetTargetFragment(nonchg)
        
    def OnApplyAttrib(self,event):
        value=self.cmbvalue.GetStringSelection()
        target=self.cmbfrg.GetStringSelection()
        # attrib
        self.attrib=self.cmbattrib.GetStringSelection()
        # value
        value=int(value)
        # target fragments
        if target == 'all':
            frglst=self.parobj.ListFragmentName('all')
        elif target == 'selected':
            frglst=self.parobj.ListSelectedFragment()
        elif target == 'non-peptide':
            frglst=self.parobj.ListFragmentName(kind='chm')
        else: # a fragment
            frglst=[target]
            
        if len(frglst) <= 0:
            mess='No target fragments.'
            lib.MessageBoxOK(mess,'Fragmentation_Frm(OnApplyAtrib)')
            return            
        #
        self.parobj.SetFragAttribToMolObj(frglst,self.attrib,value)
        
