#!/bin/sh
# -*- coding: utf-8


import os
#import sys
import wx
import wx.grid

import copy
from operator import itemgetter
#import shutil 
#import copy
import numpy
import scipy
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

class RotateBond_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos=[],winsize=[],
                 winlabel='RotateBond'):
        self.title='Bond Rotator'
        self.winsize=winsize
        self.winpos=winpos
        if len(self.winsize) <= 0: self.winsize=lib.MiniWinSize([280,300])
            #pltfrm=lib.GetPlatform()
            #if pltfrm == 'WINDOWS': self.winsize=lib.WinSize((230,230)) #([260,270]) #((260,240)) #400) #366) #(155,330) #(155,312)
            #else: self.winsize=lib.WinSize((260,270))
            
        if len(self.winpos) <= 0: self.winpos=lib.WinPos(parent.mdlwin)
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=self.winpos,
               size=self.winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER) #|wx.FRAME_FLOAT_ON_PARENT)      
 
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.winctrl=self.model.winctrl
        self.setctrl=self.model.setctrl
        self.draw=self.mdlwin.draw
        self.ctrlflag=self.model.ctrlflag

        self.winlabel=winlabel
        self.helpname='BondRotator'
        #self.model.winctrl.SetWin(self.winlabel,self)
        
        molnam=self.model.mol.name
        #
        self.Initialize()
        self.curmolnam=self.model.mol.name
        self.curmolnatm=len(self.model.mol.atm)
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        #
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        
        #
        self.SetTitle(self.title+' ['+molnam+']')
        #
        self.savselnmb=self.model.mousectrl.GetSelMode()
        self.savselobj=self.model.mousectrl.GetSelObj()
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)
        #        
        self.maxchangehis=self.setctrl.GetParam('max-undo-zmt') #'self.model.maxzmchangehis # maximum number of change history
        self.changehis=[] # change history.
        # mouse
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)
        # create panel and set widget state
        self.CreatePanel()
        #        
        self.Show()

        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
        
    def CreatePanel(self):
        # popup control panel
        [xsize,ysize]=self.GetClientSize()
        xpos=0; ypos=0
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        [w,h]=self.panel.GetSize()
        hbtn=22; hcmd=35 #40
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc=10; xloc=5
        wx.StaticText(self.panel,-1,"Rotation axis:",pos=(xloc,yloc),
                      size=(80,18)) 
        self.tclpnts=wx.TextCtrl(self.panel,-1,self.curname,
                                 pos=(xloc+85,yloc),size=(70,18),
                                 style=wx.TE_PROCESS_ENTER)
        self.tclpnts.Bind(wx.EVT_TEXT_ENTER,self.OnInput)
        mess='Input two atom numbers(ex. 1-2) and hit "ENTER"'
        self.tclpnts.SetToolTipString(mess)
        btninv=wx.Button(self.panel,wx.ID_ANY,"Invert",pos=(xloc+170,yloc),
                         size=(45,hbtn))        
        btninv.Bind(wx.EVT_BUTTON,self.OnInvert)    
        btninv.SetToolTipString('Invert movable atom group')
        yloc += 25
        wx.StaticText(self.panel,-1,"1)Set selected atoms:",pos=(xloc+10,yloc),
                      size=(130,18)) 
        btnget=wx.Button(self.panel,-1,"Set",pos=(xloc+150,yloc),size=(70,hbtn))        
        btnget.Bind(wx.EVT_BUTTON,self.OnSetAxis)
        btnget.SetToolTipString('Set selected two atoms to the rotation axis')
        # input two points
        yloc += 25
        st2=wx.StaticText(self.panel,-1,"2)Select from list:",
                          pos=(xloc+10,yloc),size=(120,18)) 
        mess='Check a data in the list to set to the rotation axis'
        st2.SetToolTipString(mess)
        self.btnnext=wx.Button(self.panel,-1,">",pos=(xloc+160,yloc),
                               size=(20,hbtn))        
        self.btnnext.Bind(wx.EVT_BUTTON,self.OnNextPrev)
        mess='Set next data in the list to the rotation axis'
        self.btnnext.SetToolTipString(mess)
        self.btnprev=wx.Button(self.panel,-1,"<",pos=(xloc+130,yloc),
                               size=(20,hbtn))        
        self.btnprev.Bind(wx.EVT_BUTTON,self.OnNextPrev)
        mess='Set previous data in the list to the rotation axis'
        self.btnprev.SetToolTipString(mess)
        self.number=wx.StaticText(self.panel,-1,"",pos=(xloc+200,yloc+2),
                                  size=(40,18)) 
        yloc += 30
        #
        wpan=130; hpan=h-yloc-hcmd-30
        self.pntpan=wx.ScrolledWindow(self.panel,-1,pos=[xloc+30,yloc],
                                      size=[wpan,hpan]) #,
        self.pntpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
        self.pntpan.SetBackgroundColour('white')
        self.SetAxisCheckBoxes()
        self.pntpan.SetScrollRate(5,20)
        xloc1=xloc+wpan+45
        btnauto=wx.Button(self.panel,wx.ID_ANY,"Auto set",pos=(xloc1,yloc),
                          size=(60,hbtn))        
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnauto.SetToolTipString(mess)
        btnauto.Bind(wx.EVT_BUTTON,self.OnAutoSet)
        yloc += 25
        btnrmv=wx.Button(self.panel,wx.ID_ANY,"Remove",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove)
        btnrmv.SetToolTipString('Remove checked data from the list')
        yloc += 25
        btnclr=wx.Button(self.panel,wx.ID_ANY,"ClearAll",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearAll)
        btnclr.SetToolTipString('Clear the list')
        #yloc=h-hpan
        #yloc += 10; xloc=5
        yloc=h-hcmd-20; xloc=5
        self.ckbsel=wx.CheckBox(self.panel,-1,
                      'Automatic selection of movable atoms',pos=(xloc,yloc))
        self.ckbsel.Bind(wx.EVT_CHECKBOX,self.OnAutoSelection)
        self.ckbsel.SetToolTipString('Select movable atoms automatically')
        self.ckbsel.SetValue(self.autosel)
        #
        #yloc=h-hcmd+5
        yloc += 20
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(xsize,2),
                      style=wx.LI_HORIZONTAL)
        #       
        yloc += 8; xloc2=30
        btnundo=wx.Button(self.panel,wx.ID_ANY,"Undo",
                          pos=(xloc2,yloc),size=(45,hbtn))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)       
        btnundo.SetToolTipString('Undo')
        wx.StaticText(self.panel,-1,"Bond Rotation:",
                      pos=(xloc2+70,yloc+2),size=(85,18)) 
        label='Off'
        if self.buildmode: label='On'
        btnbld=wx.ToggleButton(self.panel,-1,label,pos=(xloc2+165,yloc),
                               size=(45,hbtn))
        btnbld.Bind(wx.EVT_TOGGLEBUTTON,self.OnBuildMode)
        if label == 'Off': btnbld.SetValue(True)
        else: btnbld.SetValue(False)
        btnbld.SetToolTipString('Toggle between build(On) and view(Off) mode')

    def OnUndo(self,event):
        #self.model.mol.atm=self.savemolatm
        self.model.RecoverAtomCC()
        if self.buildmode: self.model.SaveAtomCC()
        
    def OnAutoSet(self,event):
        bondlst=self.model.FindRotatableBonds(self.singlebondonly)
        self.AutoSet(bondlst)

    def AutoSet(self,bondlst):
        if len(bondlst) >= 0:
            self.axislst=bondlst
            self.ClearCheckBoxPanel()
            self.SetAxisCheckBoxes()
            self.p1=self.axislst[0][0]; self.p2=self.axislst[0][1]
            name=self.PackName(self.p1,self.p2)
            self.curname=name
            self.CheckName(self.curname,True)
            self.tclpnts.SetValue(name)
        pntlst=[]; pntlst.append([self.p1,self.p2])
        
        self.model.SelectAll(False,drw=False)
        self.DrawRotationAxis(pntlst)
        
        self.SetNumber()
    
    def SetNumber(self):
        nmb=len(self.axischkboxdic)
        self.number.SetLabel(str(nmb))
    
    def OnAutoSelection(self,event):
        obj=event.GetEventObject()
        self.autosel=obj.GetValue()
        
    def OnInput(self,event):
        p1,p2=self.GetPoints()
        if p1 >= 0 and p2 >= 0:
            self.p1=p1; self.p2=p2
            self.SetAxis(self.p1,self.p2)
        else: return
            
    def OnInvert(self,event):
        p1,p2=self.GetPoints()
        if [p1,p2] in self.axislst: self.axislst.remove([p1,p2])      
        p1s=p1; self.p1=p2; self.p2=p1s
        self.SetAxis(self.p1,self.p2)
        self.model.SelectMovableAtoms(self.p1,self.p2,autosel=False,drw=True)
        
    def UnpackName(self,name):
        p1=-1; p2=-1
        items=lib.SplitStringAtSeparator(name,':')
        try:
            p1=int(items[0])-1
            p2=int(items[1])-1
        except: pass  
        return p1,p2
    
    def PackName(self,p1,p2):
        return str(p1+1)+':'+str(p2+1)    
    
    def PackName3(self,p1,p2,p3):
        return str(p1+1)+':'+str(p2+1)+':'+str(p3+1)
    
    def UnpackName3(self,name):
        p1=-1; p2=-1; p3=-1
        items=lib.SplitStringAtSeparator(name,':')
        try: p1=int(items[0])-1
        except: pass
        try: p2=int(items[1])-1
        except: pass
        try: p3=int(items[2])-1
        except: pass  
        return p1,p2,p3
        
    def GetPoints(self):
        p1=-1; p2=-1
        name=self.tclpnts.GetValue()
        p1,p2=self.UnpackName(name)
        if p1 < 0 or p2 < 0:            
            mess='Error in input text. Please input two numbers separated by "-"'
            lib.MessageBoxOK(mess,'BondRotate(GetPoints)')
        return p1,p2
    
    def OnSetAxis(self,event):
        nsel,lst=self.model.ListSelectedAtom()
        if nsel < 2:
            mess='Please select two/three atoms defining rotation axis.'
            lib.MessageBoxOK(mess,'Bond Rotation(OnSetPoints)')
            return
        elif nsel == 2:
            p1=lst[0]; p2=lst[1]
            name=self.PackName(p1,p2)
            if [p1,p2] in self.axislst: self.CheckName(name,True)
            if [p2,p1] in self.axislst: self.CheckName(name,True)

            self.SetAxis(p1,p2)
            
        
    def SetAxis(self,p1,p2,arrow=True):
        if p1 < 0 or p2 < 0:
            mess='Axis is not defined.'
            lib.MessageBoxOK(mess,'Bond Rotation(AppendPoints)')
            return
        self.p1=p1; self.p2=p2
        name=self.PackName(self.p1,self.p2)
        self.tclpnts.SetValue(name)
        #
        if not [p1,p2] in self.axislst and not [p2,p1] in self.axislst:
            self.axislst.append([self.p1,self.p2])
            self.ClearCheckBoxPanel()
            self.SetAxisCheckBoxes()
        #
        self.curname=name
        self.CheckName(self.curname,True)
        nmove,invertp=self.model.SelectMovableAtoms(self.p1,self.p2,drw=False)
        if self.buildmode: 
            self.SetRotationAxis(self.p1,self.p2)
            self.model.mousectrl.SetMouseMode(7,delarrow=False)
            # select movable atoms
            nmove,invertp=self.model.SelectMovableAtoms(self.p1,self.p2,drw=False)
            if invertp: self.OnInvert(1)
            if nmove <= 0: return
            if self.shwtorsion:
                # draw torsion angle and elemnt names
                pnts14=self.model.Find14Atoms(self.p1,self.p2)
                if len(pnts14) > 0:
                    self.model.ctrlflag.Set('draw-torsion-angle',pnts14)
                    ###self.model.DrawLabelElm(True,-1,atmlst=[p11,self.p1,self.p2,p22],drw=False)
                else:
                    self.model.ctrlflag.Del('draw-torsion-angle')
                    #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
                    self.model.DrawLabelAtm(False,-1,drw=False)
        # beep when short contact occurs
        if self.beep: self.ctrlflag.Set('beep-short-contact',self.shortdistance)
        else: self.ctrlflag.Del('beep-short-contact')            
        pntlst=[]; pntlst.append([self.p1,self.p2])
        if arrow: self.DrawRotationAxis(pntlst)
        
        self.SetNumber()
        
    def DrawRotationAxis(self,pntlst):
        self.model.DrawAxisArrow(False,[])
        bndpnts=[]
        for p1,p2 in pntlst:
            cc1=self.model.mol.atm[p1].cc
            cc2=self.model.mol.atm[p2].cc
            bndpnts.append([cc1,cc2])    
        self.model.DrawAxisArrow(True,bndpnts)
        # self.model.DrawMol(True)   
  
    def SetAxisCheckBoxes(self):
        if len(self.axischkboxdic) > 0: self.ClearCheckBoxPanel()
        yloc=8
        for p1,p2 in self.axislst:
            name=self.PackName(p1,p2) #str(p1+1)+':'+str(p2+1)
            chkbox=wx.CheckBox(self.pntpan,-1,name,pos=[10,yloc])
            self.axischkboxdic[name]=chkbox
            chkbox.Bind(wx.EVT_CHECKBOX,self.OnCheckBox)
            yloc += 20
        self.CheckName(self.curname,True)
        self.pntpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
    
    def ClearCheckBoxPanel(self):
        for name,obj in self.axischkboxdic.iteritems(): obj.Destroy()
        self.axischkboxdic={}
        self.curname=''
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)
 
    def OnRemove(self,event):
        dellst=self.GetCheckedList()
        self.Remove(dellst)

    def Remove(self,dellst):
        for name in dellst:
            #del self.axischkboxdic[name]
            items=lib.SplitStringAtSeparator(name,':')            
            p1=int(items[0])-1
            p2=int(items[1])-1
            self.axislst.remove([p1,p2])
        self.SetAxisCheckBoxes()
        self.model.DrawAxisArrow(False,[])
        self.tclpnts.SetValue('')
        self.curname=''

    def GetCheckedList(self):
        checkedlst=[]
        for name,obj in self.axischkboxdic.iteritems():
            if obj.GetValue(): checkedlst.append(name)
        return checkedlst

    def OnClearAll(self,event):
        self.ClearCheckBoxPanel()
        self.axislst=[]
        self.tclpnts.SetValue('')
        self.curname=''
        self.model.DrawAxisArrow(False,[])
        
    def OnCheckAll(self,event):
        # ToggleButton
        self.btnchk.GetValue()
        value=False
        if self.btnchk.GetValue(): 
            value=True; self.curname=self.axislst[0] # #Check all, else uncheck all
        else: self.curname=''
        for name,obj in self.axischkboxdic.iteritems(): obj.SetValue(value)
    
    def CheckName(self,name,on):
        if name == '': return
        if on: value=True
        else: value=False
        for pntnam,obj in self.axischkboxdic.iteritems():
            if pntnam == name: obj.SetValue(value)

    def OnCheckOne(self,event):
        return
        #self.checkone=self.ckbone.GetValue()
        #self.SetSelectButtonStatus()
    
    def SetSelectButtonStatus(self):
        return
    
        #if self.checkone:
        #    self.ckbone.SetValue(True)
        #    self.btnnext.Enable(); self.btnprev.Enable()
        #else:
        #    self.ckbone.SetValue(False)
        #    self.btnnext.Disable(); self.btnprev.Disable()

    def OnNextPrev(self,event):
        obj=event.GetEventObject()
        label=obj.GetLabel() 
        lst=self.GetCheckedList()
        if len(lst) <= 0: 
            mess='No check item in "Bond(axis) list". Please check one.'
            lib.MessageBoxOK(mess,'Bond Rotation(OnNextPrev)')
            return
        name=lst[0]
        p1,p2=self.UnpackName(name)
        try: idx=self.axislst.index([p1,p2])
        except: return
        #        
        self.CheckName(name,False)
        npnts=len(self.axislst)
        if label == '>':
            if idx < npnts-1: next=idx+1
            else: next=0
        else:
            if idx == 0: next=npnts-1
            else: next=idx-1
        pnts=self.axislst[next]
        self.SetAxis(pnts[0],pnts[1])

    def OnCheckBox(self,event):
        if len(self.axislst) <= 1:
            self.CheckName(self.curname,True)
            self.SetAxis(self.p1,self.p2)
            return
        checkedlst=self.GetCheckedList()
        if len(checkedlst) <= 0: 
            return
        
        if self.checkone:
            if self.curname != '': self.CheckName(self.curname,False)
            name=''
            for pntnam in checkedlst:
                if pntnam != self.curname:
                    name=pntnam; break
            if name == '': return
            p1,p2=self.UnpackName(name)
            if p1 < 0 or p2 < 0: return            
            self.SetAxis(p1,p2)
        else: pass
                        
    def UpdateHistry(self):
        current=[]
        #atm.append([self.p1,self.p2,self.p3,self.p4])
        nsel,lst=self.model.ListSelectedAtom()
        if nsel <= 0: return
        #
        for atom in self.model.mol.atm:
            if atom.select:
                tmp=[]
                tmp.append(atom.seqnmb)
                tmp.append(copy.deepcopy(atom.cc))
                current.append(tmp)
        #current.append(atm)    
        nhis=len(self.changehis)
        if nhis > self.maxchangehis: del self.changehis[1]
        self.changehis.append(current)

    def OnBuildMode(self,event):
        obj=event.GetEventObject()
        value=obj.GetValue()
        if value: 
            obj.SetLabel('Off'); self.buildmode=False
            self.mdlmode=0
            self.buildmode=False
            self.mdlmode=0
            #self.SwitchMdlMode(self.mdlmode)
            self.model.mousectrl.SetMdlMode(self.mdlmode)
            ###self.SetCenterOfRotation(True)
            self.model.menuctrl.OnSelect("Atom",True)
            self.model.mousectrl.SetMouseMode(0,delarrow=True) 
            self.model.mousectrl.SetMouseModeSelection(0)
            ###self.model.mousectrl.SetRotationAxisPnts(False,[])
            ###self.mdlwin.ChangeMouseModeWinBGColor('light gray')
            self.ctrlflag.Del('draw-torsion-angle')
            #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
            self.model.DrawLabelElm(False,-1,drw=False)
            self.model.TextMessage('')
    

        else:
            obj.SetLabel('On'); self.buildmode=True
            self.mdlmode=5
            #
            #self.SwitchMdlMode(self.mdlmode)
            self.model.mousectrl.SetMdlMode(self.mdlmode)
            ###self.SetCenterOfRotation(True)
            self.savmusmod=self.model.mousectrl.GetMouseMode()
            p1,p2=self.UnpackName(self.curname)
            self.SetRotationAxis(p1,p2)
            self.model.mousectrl.SetMouseMode(7,delarrow=False) # axis rotation
            self.model.mousectrl.SetMouseModeSelection(7)
            self.SetAxis(p1,p2)
            self.model.SaveAtomCC()
        
    def SetRotationAxis(self,p1,p2):
        p1cc=self.model.mol.atm[p1].cc
        p2cc=self.model.mol.atm[p2].cc
        self.model.mousectrl.SetRotationAxisPnts(True,pnts=[p1cc,p2cc])

    def OnViewMode(self,event):
        self.buildmode=False
        self.mdlmode=0
        #self.SwitchMdlMode(self.mdlmode)
        self.model.mousectrl.SetMdlMode(self.mdlmode)
        ###self.SetCenterOfRotation(True)
        self.model.menuctrl.OnSelect("Atom",True)
        self.model.mousectrl.SetMouseMode(0,delarrow=True) 
        self.model.mousectrl.SetMouseModeSelection(0)
        ###self.model.mousectrl.SetRotationAxisPnts(False,[])
        ###self.mdlwin.ChangeMouseModeWinBGColor('light gray')
        self.ctrlflag.Del('draw-torsion-angle')
        #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
        self.model.DrawLabelAtm(False,-1,drw=False)
        self.model.TextMessage('')

    def SwitchMdlMode(self,mdlmod): # arg=True,False
        try: self.model.mousectrl.ResetModelMode()
        except: pass
        self.model.mousectrl.SetMdlMode(mdlmod) # build mode
    
    def SetCenterOfRotation(self,argval):
        on=argval
        sellst=self.model.ListTargetAtoms()
        if len(sellst) > 0:
            self.model.CenterOfRotation(sellst)
        else: pass
        
    def OnPaint(self,event):
        event.Skip()
    
    def OnResize(self,event):
        self.panel.Destroy()
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])        
        self.axischkboxdic={}
        self.CreatePanel()

    def Initialize(self):
        #
        #self.savselnmb=self.model.mousectrl.GetSelMode()
        #self.savselobj=self.model.mousectrl.GetSelObj()
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)
        #
        self.shwtorsion=True
        self.beep=True
        self.shortdistance=1.5
        self.singlebondonly=False
        #
        self.axischkboxdic={}
        self.axislst=[]
        self.p1=-1; self.p2=-1
        self.p11=-1; self.p22=-1
        self.curname=''
        self.checkone=True
        self.buildmode=False # mouse mode for moving selected atom(s)
        self.autosel=True
        self.mdlmode=0
        self.SwitchMdlMode(self.mdlmode)
        self.sensitive=0.5 # mouse sensitivity
        self.model.mousectrl.SetSensitive(self.sensitive)

    def MakeFileName(self,molnam):
        fudir=self.model.setctrl.GetDir('Scratch')
        base,ext=os.path.splitext(molnam)
        filename=os.path.join(fudir,base+'.rotbnd')
        return filename
        
    def SaveBondDataInScratch(self):
        natm=self.curmolnatm
        molnam=self.curmolnam
        filename=self.MakeFileName(molnam)
        bondlst=self.GetBondData()
        self.WriteRotBondFile(filename,bondlst,molnam,natm)
        
    def GetBondDataFilesInScratch(self,molnam):
        curfile=''
        fudir=self.model.setctrl.GetDir('Scratch')
        filenames=lib.GetFilesInDirectory(fudir,['.rotbnd'])
        nc=molnam.find('.')
        if nc >= 0: molnam=molnam[:nc]+'.rotbnd'
        else: molnam=molnam+'.rotbnd'
        for file in filenames:
            head,tail=os.path.split(file)
            if tail == molnam:
                curfile=file; break
        return curfile
        
    def OnNotify(self,event):
        try: item=event.message
        except: return
        #
        if item == 'SwitchMol': self.OnReset(1)
        elif item == 'ReadFiles': self.OnReset(1)      
    
    def OnReset(self,event):
        # clear all, clear rotation angle, SelectAll(False)        
        self.SaveBondDataInScratch()
        self.Initialize()
        self.OnClearAll(1)
        self.OnResize(1)
        #
        self.curmolnam=self.model.mol.name
        self.curmolnatm=len(self.model.mol.atm)
        filename=self.GetBondDataFilesInScratch(self.curmolnam)
        if len(filename) > 0:
            retmess,bondlst=self.ReadRotBondFile(filename)
            if len(bondlst) > 0: self.AutoSet(bondlst)
        #
        try: self.SetTitle(self.title+' ['+self.curmolname+']')
        except: pass
        
        self.ctrlflag.Del('draw-torsion-angle')
        #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
        self.model.DrawLabelAtm(False,-1,drw=False)
        #
        self.model.mousectrl.SetMdlMode(self.mdlmode)
        self.model.mousectrl.SetMouseMode(0,delarrow=True)
        #
        self.model.SelectAll(False,drw=True)
            
    def OnClose(self,event):
        # recover mouse and sel mode
        self.model.mousectrl.SetMdlMode(0)
        self.model.mousectrl.SetSelMode(self.savselnmb)
        self.model.mousectrl.SetSelModeSelection(self.savselnmb)
        self.model.mousectrl.SetSelObj(self.savselobj)
        self.model.mousectrl.SetSelObjSelection(self.savselobj)
        # remove draw data
        self.model.DrawAxisArrow(False,[])
        self.model.TextMessage('')
        self.ctrlflag.Del('draw-torsion-angle')
        #self.model.DrawLabelElm(False,-1,atmlst=[],drw=True)
        self.model.DrawLabelAtm(False,-1,drw=True)
        #
        self.winctrl.Close(self.winlabel) #'ZmatWin'
        self.Destroy()

    def SetSensitive(self):
        text=wx.GetTextFromUser('Enter mouse sensitivity(default:0.5).',
                                caption='Rotate Bond',default_value=str(self.sensitive))
        if len(text) > 0:
            try: sensitive=float(text)
            except: return
        else: return
        mess='Mouse sensitivity has changed from '+str(self.sensitive)+' to '+str(sensitive)
        self.model.ConsoleMessage(mess)
        self.sensitive=sensitive
        self.model.mousectrl.SetSensitive(self.sensitive)
    
    def ShortContactDistance(self):
        #self.model.ConsoleMessage('entered in ShrotContact')
        text=wx.GetTextFromUser('Enter short contact distance(default:1.5A).',
                                caption='Rotate Bond',default_value=str(self.shortdistance))
        if len(text) > 0:
            try: distance=float(text)
            except: return
        else: return
        mess='Short contact distance has changed from '+str(self.shortdistance)+' to '+str(distance)
        self.model.ConsoleMessage(mess)
        self.shortdistance=distance
        
    def OpenRotFile(self):
        wcard='Rotate bond file(*.rotbnd)|*.rotbnd'
        filename=lib.GetFileName(self.model.mdlwin,wcard,'r',True)
        if len(filename) <= 0: return
        retmess,bondlst=self.ReadRotBondFile(filename)
        if int(retmess['NATM']) != len(self.model.mol.atm):
            mess='The number of atoms is not the same as that of "mol".'
            lib.MessageBoxOK(mess,'RotateBond_Frm(OpenRotFile)')
            return
        mess='Read rotatable bond file='+filename
        self.model.ConsoleMessage(mess)
        #
        self.AutoSet(bondlst)
        
    def SaveRotFile(self):
        wcard='Rotate bond file(*.rotbnd)|*.rotbnd'
        filename=lib.GetFileName(self.model.mdlwin,wcard,'w',True)
        if len(filename) <= 0: return
        
        natm=len(self.model.mol.atm)
        molname=self.model.mol.name
        bondlst=self.GetBondData()
        self.WriteRotBondFile(filename,bondlst,molnam,natm)
        #
        mess='Write rotatable bond file='+filename
        self.model.ConsoleMessage(mess)
        
    def GetBondData(self):     
        # get bondlst in 
        bondlst=[]
        for name,obj in self.axischkboxdic.iteritems():
            items=name.split(':')
            i=int(items[0]); j=int(items[1])
            bondlst.append([i,j])        
        #
        molnam=self.model.mol.name
        natm=len(self.model.mol.atm)
        bondlst=sorted(bondlst, key=lambda atmpair: atmpair[0])
        return bondlst
    
    def ReadRotBondFile(self,filename):
        retmess={}; bondlst=[]
        molnam=''; natm=-1; line=0
        f=open(filename,'r')
        for s in f.readlines():
            line += 1 
            s=rwfile.CommentFilter(s)
            if s is None: continue
            if s.startswith('MOLNAM',0,6):
                key,value=lib.GetKeyAndValue(s)
                molnam=value
                retmess['MOLNAM']=molnam
            elif s.startswith('NATM',0,4):
                key,value=lib.GetKeyAndValue(s)
                natm=value
                retmess['NATM']=str(natm)
            else:
                items=lib.SplitStringAtSpacesOrCommas(s)
                if len(items) <= 2:
                    retmess['ERROR']='missing atom line '+str(line)
                    return retmess,bondlst
                else:
                    atmi=int(items[1])-1; atmj=int(items[2])-1
                    bondlst.append([atmi,atmj])
        
        f.close()
        bondlst=sorted(bondlst, key=lambda atmpair: atmpair[0])
        return retmess,bondlst
    
    def WriteRotBondFile(self,filename,bondlst,molname,natm):
        fi6='%6d'
        text='# rotatable bond file ... '+lib.DateTimeText()+'\n'
        text=text+'MOLNAME='+molname+'\n'
        text=text+'NATM='+str(natm)+'\n'
        text=text+'#\n'
        text=text+'# format:\n'
        text=text+'# seq number, atomi,atomj\n'
        text=text+'#\n'
        count=0
        for i,j in bondlst:
            count += 1
            text=text+(fi6 % count)+' '+(fi6 % i)+' '
            text=text+(fi6 % j)+'\n'
        f=open(filename,'w')
        f.write(text)
        f.close()
    
    def HelpDocument(self):
        const.CONSOLEMESSAGE('helpname='+self.helpname)
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname,expand=True)
    
    def Beep(self,on):
        self.beep=on
    
    def SetSingleBondOnly(self,on):
        self.singlebondonly=on
            
    def OpenZmtViewer(self):
        win=ZMatrixEditor_Frm(self.mdlwin,-1)
    
    def ExecTinker(self):
        self.model.ExecuteAddOnScript('tinker-optimize.py',False)
    
    def ExecGAMESS(self):
        self.model.ExecuteAddOnScript('gamess-user.py',False)
            
    def MenuItems(self):
        #menuhelpdic={} 
        menubar=wx.MenuBar()
        # File
        submenu1=wx.Menu()
        submenu1.Append(-1,'Open .rotbnd file','Open rotatable bond file.')
        submenu1.Append(-1,'Save .rotbnd file','Save rotatable bond file.')
        submenu1.AppendSeparator()
        submenu1.Append(-1,'Close','Close the panel')
        menubar.Append(submenu1,'File')
        # Option
        submenu1=wx.Menu()
        iid=wx.NewId()
        submenu1.Append(iid,'Show torsion angle','Show torsion angle.',
                        kind=wx.ITEM_CHECK)
        submenu1.Check(iid,self.shwtorsion)

        #submenu.AppendSeparator()
        submenu1.Append(-1,'Mouse sensitivity','Set mouse sensitivity.')
        
        iid=wx.NewId()
        submenu1.Append(iid,'Beep when short contact occured','Beep when short contact ocurrs.',kind=wx.ITEM_CHECK)
        submenu1.Check(iid,self.beep)
        
        
        submenu1.Append(-1,'Short contact distance','Input short contact distance.',kind=wx.ITEM_CHECK)
        
        
        #iid=wx.NewId()
        
        #submenu1.Append(iid,"Single bond only for rotatable bonds","",kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.singlebondonly)
        menubar.Append(submenu1,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Open document.')
        helpname=self.winlabel
        submenu.Append(-1,'Tutorial','Open tutorial panel.')
        # related functions
        #submenu.AppendSeparator()
        #subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"ZmtViewer","View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,'Help')

        """ test """
        #menubar.Bind(wx.EVT_HELP,self.OnMenuHelp)
        
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # File
        if item == 'Open .rotbnd file': self.OpenRotFile()
        elif item == 'Save .rotbnd file': self.SaveRotFile()
        elif item == 'Close': self.OnClose()
        # Option
        elif item == "Show torsion angle": self.shwtorsion=bChecked
        elif item == "Mouse sensitivity": self.SetSensitive()
        elif item == "Single bond only for rotatable bonds": self.SetSingleBondOnly()
        elif item == "Beep when short contact occured": self.Beep(bChecked)
        elif item == "Short contact distance": self.ShortContactDistance()
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == "ZmtViewer": self.OpenZmtViewer()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()
        # Help
        elif item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()

class ModelBuilder_Frm(wx.MiniFrame):
    """ Model builder """
    def __init__(self,parent,id,winpos=[],winsize=[],winlabel='ModelBuilder',
                 column=2):
        self.column=column
        winwidth=40*self.column+45 #20
        if len(winsize) == 0:
            if lib.GetPlatform() == 'WINDOWS':
                winsize=[winwidth,400]
                self.winsize=lib.MiniWinSize(winsize)
            else: self.winsize=[winwidth,400]
        if len(winpos) == 0:
            #pos=parent.GetPosition()
            #winpos=[pos[0]-self.winsize[0],pos[1]+40]            
            winpos=lib.WinPos(parent.mdlwin)
        self.title='Model builder'
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,\
                          size=self.winsize,\
                          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|\
                          wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)
        #
        self.parent=parent
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.setctrl=self.model.setctrl
        self.winctrl=self.model.winctrl
        self.winlabel=winlabel
        self.winctrl.SetOpened(self.winlabel,self)
        #
        self.bgcolor='light gray' #'gray'
        self.SetBackgroundColour(self.bgcolor)
        #
        if self.model.molctrl.GetCurrentMolName() == '': 
            self.model.NewMolecule()
        #
        self.savmenuobj=self.model.ctrlflag.Get('popupmenu')
        self.model.ctrlflag.Set('popupmenu',self.PopUpMenu)
        self.Initialize()
        # set "reset" button ico       
        self.resetbmp=self.model.setctrl.GetIconBmp('reset')
        self.ctrlbmp=self.model.setctrl.GetIconBmp('mode')
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.CreatePanel()
        #
        self.Show()
        # event handlers
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnResize)
                
    def CreatePanel(self):
        [w,h]=self.GetClientSize(); hp=60 # height of move panel
        self.column=(w-22)/40
        if self.column < 1: self.column=1
        if self.column == 1: hp=70
        # mode panel
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=[w,hp]) #,style=wx.BORDER) #,size=(xsize,yupper)) #ysize))
        self.panel.SetBackgroundColour("light gray") 
        # Buttons
        hbtn=22
        btnwidth=50
        if self.column <= 1:
            yloc1=h-65; yloc2=yloc1+30; xloc1=int((w/2)-25)
            xloc2=int((w/2)-25)
            btnheight=70
        else: 
            xloc1=20; xloc2=xloc1+60; yloc1=h-30; yloc2=yloc1
            btnheight=35
        if self.column == 2: xloc1=5; xloc2=xloc1+45; btnwidth=40
        self.btnundo=wx.Button(self,-1,"Undo",pos=(xloc1,yloc1),
                               size=(btnwidth,25))
        self.btnundo.Bind(wx.EVT_BUTTON,self.OnUndo) 
        self.btncone=wx.Button(self,-1,"Connect",pos=(xloc2,yloc2),
                               size=(55,25))
        self.btncone.Bind(wx.EVT_BUTTON,self.OnConnect) 
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        yloc=5
        # mode panel radio buttons
        yloc += 20 #30
        # icon panel (scrolled panel)
        self.scrollpanel=wx.ScrolledWindow(self,-1,pos=[0,yloc],
                                           size=[w,h-yloc-btnheight],
                                           style=wx.VSCROLL|wx.SUNKEN_BORDER) #,
        self.scrollpanel.SetBackgroundColour('light gray')
        self.scrollpanel.SetScrollRate(0,30)
        bmpwidth=35; bmpheight=35; bmpsize=[bmpwidth,bmpheight]
        yloc=5
        for i in range(0,len(self.molnamelst),self.column):
            xloc=5
            for j in range(self.column):
                try: name=self.molnamelst[i+j]
                except: break
                xloc=j*40+5
                bmpfile=self.iconfiledic[name]
                if os.path.exists(bmpfile):
                    bmp=wx.Bitmap(bmpfile,wx.BITMAP_TYPE_ANY)
                    btnobj=wx.BitmapButton(self.scrollpanel,-1,bitmap=bmp,
                                           pos=(xloc,yloc),size=bmpsize)
                else: 
                    label=self.resnamedic[name]
                    btnobj=wx.Button(self.scrollpanel,-1,label,pos=(xloc,yloc),
                                     size=bmpsize)
                btnobj.Bind(wx.EVT_BUTTON,self.OnChooseMol)
                self.objdic[btnobj]=name
            yloc += bmpheight+5
        self.scrollpanel.SetScrollbars(0,1,0,yloc+10)

    def Initialize(self):
        self.objdic={}
        self.mdlmode=0 ### 5
        self.molfiledic=[]
        self.iconfiledic=[]
        self.molnamelst=[]
        self.resnamedic={}
        self.moldir=self.setctrl.GetDir('Molecules')
        self.SetMolFiles(self.moldir)
        #
        self.buildmol=None
        self.savemolatm=[]; self.saveatmcc=[]
        #self.model.ClearSaveAtomCC()
        if len(self.model.mol.atm) > 0: 
            self.savemolatm=self.model.mol.CopyAtom() #self.SaveMol()
            self.CopyAtomCC()
            #self.model.SaveAtomCC(True)
        self.setrotaxis=True
        self.model.ctrlflag.Del('draw-torsion-angle')
        self.connectatm1=-1; self.connectatm2=-1
        self.showdistance=False
        # set mouse mode
        self.SwitchMdlMode(6)
        self.model.menuctrl.OnSelect("Unlimited",True) #"2-objects",True)
        #self.model.mousectrl.pntatmhis.Clear()
        self.model.menuctrl.OnSelect("Atom",True)
        
        self.model.ready=True
        
    def CopyAtomCC(self):
        self.saveatmcc=[]
        for i in range(len(self.model.mol.atm)):
            cc=self.model.mol.atm[i].cc
            self.saveatmcc.append([cc[0],cc[1],cc[2]])
                 
    def OnConnect(self,event):
        self.ConnectMols()        
    
    def OnLeftDown(self,event):
        pass
    
    def OnChooseMol(self,event):
        obj=event.GetEventObject()
        molname=self.objdic[obj]
        if molname == 'ion': self.OpenIonMenu()
        else:
            molfile=self.molfiledic[molname]
            moldat=rwfile.ReadMolFile(molfile)
            moldat=moldat[0]
            #
            title=moldat[0]; comment=moldat[1]; resnam=moldat[2]
            molatm=moldat[3]
            mol=molec.Molecule(self.model) 
            mol.SetMolAtoms(molatm,resnam=resnam)
            self.SetBuildMol(mol) #.atm)
            # mdlmo -> put mol mode
            self.SwitchMdlMode(6)
    
    def OpenIonMenu(self):    
        menulst=['NA','MG','CL','---','Other']
        tiplst=[]
        retmethod=self.OnIonSelect
        width=50
        self.ionmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,menulst,
                                            tiplst,winwidth=width)
        
    def OnIonSelect(self,item,label):
        if item == '---': return
        if item == 'Other':
            input=wx.GetTextFromUser('Enter element symbol.')
            input=input.strip()
            if len(input) <= 0: return
            elm=input.upper()
        else:
            item=item.strip()
            if len(item) == 1: item=' '+item
            elif len(item) > 2: item=item[:2]
            elm=item.upper()
        # make mol data
        self.MakeIonData(elm)    
        self.model.ConsoleMessage('Input ion='+elm)
        
    def MakeIonData(self,elm):
        molname=elm
        mol=molec.Molecule(self.model)
        molatm=[[elm],[[0.0,0.0,0.0]],[],[]]
        #moldat=['ion','ion',elm,]
        title='ion'; comment='ion'; resnam=elm
        mol.SetMolAtoms(molatm,resnam=resnam)
        self.SetBuildMol(mol) #.atm)
        # mdlmo -> put mol mode. PutBuildingMol method in Model class calls PutMol method
        self.SwitchMdlMode(6)
        
    def OnChangeMode(self,event):
        if self.mdlmode == 5: self.mdlmode=0
        elif self.mdlmode == 0: 
            self.mdlmode=5
            self.savemolatm=self.model.mol.CopyAtom()
            self.CopyAtomCC()
            #self.model.ClearSaveAtomCC()
            #self.model.SaveAtomCC(True)
        self.SwitchMdlMode(self.mdlmode)
        self.SetCenterOfRotation(True)
        
    def GetMdlMode(self):
        return self.mdlmode
    
    def SetMolFiles(self,moldir):
        #self.molnamelst=[]; self.molfilelst=[]; iconfilelst=[]
        self.inifile=os.path.join(moldir,'moleculepanel.index')
        # mol files
        if not os.path.exists(self.inifile):
            molfilelst=lib.GetFilesInDirectory(moldir,extlst=['.mol'])
            if len(self.molfilelst) <= 0:
                mess='No molecule files(.mol) in directory='+moldir
                lib.MessageBoxOK(mess,'MoleculePanel(SetMolFiles')
                return
        else: molfilelst,labellst=self.ReadIndexFile(moldir,self.inifile)
        # mol nmaes
        self.molnamelst,self.resnamedic,\
                self.molfiledic=self.MolNameAndLabel(molfilelst,labellst)
        # icon files
        self.iconfiledic=self.IconFileList(moldir,self.molnamelst,
                                           self.resnamedic)
    
    def ReadIndexFile(self,moldir,inifile):
        molfilelst=[]; labellst=[]
        f=open(inifile,'r')
        for s in f.readlines():
            s=s.strip()
            if len(s) <= 0: continue
            if s[:1] == '#': continue
            ns=s.find('#')
            if ns >= 0: s=s[:ns].strip()
            items=lib.SplitStringAtSpacesOrCommas(s)
            file=os.path.join(moldir,items[0])
            try: label=items[1]
            except: label='icon'
            if os.path.exists(file): molfilelst.append(file)
            else: molfilelst.append('')
            labellst.append(label)
        f.close()
        #
        return molfilelst,labellst
    
    def MolNameAndLabel(self,molfilelst,labellst):
        resnamedic={}; molnamelst=[]; molfiledic={}
        for i in range(len(molfilelst)):
            fil=molfilelst[i]
            label=labellst[i]
            head,tail=os.path.split(fil); base,ext=os.path.splitext(tail)
            molnamelst.append(base)
            if label != 'icon': resnamedic[base]=label
            molfiledic[base]=fil
        return molnamelst,resnamedic,molfiledic
            
    def IconFileList(self,moldir,molnamelst,resnamedic):
        icondir=os.path.join(moldir,'icons')
        iconfiledic={}
        for name in molnamelst:
            if resnamedic.has_key(name):
                iconfiledic[name]=''
            else:
                iconfile=name+'.png'
                iconfile=os.path.join(icondir,iconfile)
                if os.path.exists(iconfile): iconfiledic[name]=iconfile
                else: iconfiledic[name]=''
        
        return iconfiledic

    def SwitchMdlMode(self,mdlmode): # arg=True,False
        #mdlmod=argval
        ###try: self.model.mousectrl.ResetModelMode()
        ###except: pass
        self.model.mousectrl.SetMdlMode(mdlmode) # build mode

    def SetBuildMol(self,argval): # arg=molatm
        molatm=argval
        self.buildmol=molatm

    def IsBuildingMol(self,argval): # no arg
        ans=True
        if self.buildmol == None: ans=False
        return ans
        
    def SetCenterOfRotation(self,argval):
        on=argval
        sellst=self.model.ListTargetAtoms()
        if len(sellst) > 0:
            self.model.CenterOfRotation(sellst)
        else: pass
            
    def SetModeButton(self,argval):
        mdlmod=argval
        try: 
            obj=self.model.winctrl.GetWin(self.winlabel)
            obj.SetMdlModeButton(mdlmod)
        except: pass            
 
    def OnUndo(self,event):
        natm0=len(self.model.mol.atm)
        self.Undo()
        natm1=len(self.model.mol.atm)
        if natm0 != natm1:
            self.model.DrawAxisArrow(False,[])
            self.model.mousectrl.SetRotationAxisPnts(False,[])
            self.model.menuctrl.OnShow("Element",False)
        if self.mdlmode == 5: 
            self.model.menuctrl.OnShow("Element",True)
        self.RemoveDistance()
    
    def Undo(self):
        if len(self.savemolatm) > 0:   
            self.model.mol.atm=self.savemolatm
            for i in range(len(self.model.mol.atm)):
                self.model.mol.atm[i].cc[0]=self.saveatmcc[i][0]
                self.model.mol.atm[i].cc[1]=self.saveatmcc[i][1]
                self.model.mol.atm[i].cc[2]=self.saveatmcc[i][2]
            self.model.DrawMol(True)

            if self.mdlmode != 5: 
                self.savemolatm=[]
        else:
            mess='Failed to undo. No saved data'
            lib.MessageBoxOK(mess,'model-builder.py(Undo)')
    
    def ConnectMols(self,drw=True):
        atatmlst=[]
        ###nsel,lst=self.model.ListSelectedAtom()
        pntslst=self.model.mousectrl.pntatmhis.GetSaved()
        self.model.mousectrl.pntatmhis.Clear()
        pntslst.reverse()
        if len(pntslst) >= 2:
            self.savemolatm=self.model.mol.CopyAtom()
            self.CopyAtomCC()
            atm1=pntslst[0]; atm2=pntslst[1]
            self.connectedlst,case=self.model.ConnectGroups(atm1,atm2,
                                                            select=True)
            self.model.menuctrl.OnShow("Element",False)
            if case != 3:
                if self.setrotaxis and len(self.connectedlst) == 1:
                    #self.model.DrawAxisArrow(False,[])
                    #self.model.SetRotationAxis(self.connectedlst[0])                                      
                    
                    self.SetRotationAxis(self.connectedlst[0])
                    """
                    pnts14=self.model.Find14Atoms(self.connectedlst[0][0],self.connectedlst[0][1])
                    if len(pnts14) > 0:
                        self.model.ctrlflag.Set('draw-torsion-angle',pnts14)
                        self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
                    else:
                        self.model.ctrlflag.Del('draw-torsion-angle')
                        self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
                    """
        else:
            mess='Please select two atoms, one in parent group and the other in attaching group.'    
            lib.MessageBoxOK(mess,'model-builder.py(ConnectMols)')
        
        #self.model.DrawMol(True)

    def PutMol(self,pos): # argval=pos
        if self.buildmol is None: return
        self.savemolatm=self.model.mol.CopyAtom()
        self.CopyAtomCC()
        # merge mols
        [x,y]=self.model.mdlwin.draw.GetCoordinateAt('left',pos[0],'top',
                                                     pos[1])

        for atom in self.buildmol.atm:
            atom.cc[0] += x; atom.cc[1] += y   
        self.model.MergeMolecule(self.buildmol.atm,True,drw=True)
        self.buildmol=None
        mdlmod=0
        self.model.mousectrl.SetMdlMode(mdlmod)
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)
        self.model.menuctrl.OnShow("Element",True)

    def SetRotateBondMode(self,on):
        rotaxispnts=[]
        if on:
            if self.connectatm1 < 0 or self.connectatm2 < 0:
                return
            self.savemousemode=self.model.mousectrl.GetMouseMode()
            rotaxispnts=[self.connectatm1,self.connectatm2]
            self.model.mousectrl.SetMouseMode(9) # axisrot
        else:
            self.model.mousectrl.SetMouseMode(self.savemousemode)        
        self.model.SetRotationAxis(rotaxispnts)
        self.model.DrawAxisArrow(False,[rotaxispnts])
    
    def OnResize(self,event):
        try: self.panel.Destroy()
        except: pass
        try: self.scrollpanel.Destroy()
        except: pass
        try: self.btnundo.Destroy()
        except: pass
        try: self.btncone.Destroy()
        except: pass
        self.CreatePanel()
    
    def OnReset(self,event):
        self.Initialize()
        self.OnResize(1)
        #lib.MessageBoxOK('Restored molecule data in mdlwin','')
        self.model.Message('Restored molecule object',0,'')
            
    def OnClose(self,event):        
        self.model.ctrlflag.Set('popupmenu',self.savmenuobj)
        self.SwitchMdlMode(0)
        self.model.mousectrl.SetRotationAxisPnts(False,[])
        self.model.DrawAxisArrow(False,[])
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        self.model.ctrlflag.Del('draw-torsion-angle')
        self.model.ctrlflag.Del('beep-short-contact')
        self.model.DrawLabelRemoveAll(True)
        #
        self.model.ClearSaveMol()
        #
        try: self.Destroy()
        except: pass
    
    def SetRotationAxisFlag(self,on):
        self.setrotaxis=on

    def SetRotationAxis(self,pnts=[]):
        if len(pnts) > 0:
            nselsav,selsav=self.model.ListSelectedAtom()
            self.model.SetSelectAtom0(pnts,True)
            try: selsav.remove(pnts[0])
            except: pass
            try: selsav.remove(pnts[1])
            except: pass 
            #
            self.model.SetRotationAxis(pnts)
            #
            self.model.SetSelectAll(False)
            self.model.SetSelectAtom0(selsav,True)

    def RemoveRotationAxis(self):
        self.model.mousectrl.SetRotationAxisPnts(False,[])
        self.model.DrawAxisArrow(False,[])      
        self.model.ctrlflag.Del('draw-torsion-angle')
        self.model.TextMessage([])
        self.model.DrawMol(True)
    
    def XXRemoveDistance(self,drw=True):
        drwlabel='draw-distance'
        self.mdlwin.draw.DelDrawObj(drwlabel)
        self.model.ctrlflag.Del(drwlabel)
        if drw: self.model.DrawMol(True)
        
    def SetSelectedAtomPair(self,drw=True):
        drwlabel='draw-distance'
        nsel,atmpair=self.model.ListSelectedAtom()
        if nsel != 2:
            mess='Please select two atoms'
            lib.MessageBoxOK(mess,'ModelBuilder(SetSelectedAtomPair)')
            return
        self.model.ctrlflag.Set(drwlabel,[atmpair])
        if drw: self.model.DrawMol(True) 
   
    def SetAtomPairs(self):
        
        mess='Sorry. not inplemented yet'
        lib.MessageBoxOK(mess,'ModelBuilder(SteAtomPairs')
        return
        
        drwlabel='draw-distance'
        atmpairlst=[]

        self.model.ctrlflag.Set(drwlabel,atmpairlst)   
    
    def DelDummyAtoms(self):
        dellst=[]    
        for atom in self.model.mol.atm:
            if atom.elm == ' X': dellst.append()
        if len(dellst) > 0: self.model.DelAtoms(dellst)
        self.model.DrawMol(True)
        
    def RemoveLabel(self,drw=True):
        self.model.DrawLabelRemoveAll(drw=drw)
        
    def HelpDocument(self):
        helpname='ModelBuilder'
        self.model.helpctrl.Help(helpname)
    
    def Tutorial(self):
        helpname='ModelBuilder'
        self.model.helpctrl.Tutorial(helpname)
    
    def RelatedFunctions(self):

        menulst=["CloseMe","","ZmtViewer","RotCnfEditor","ZmtCnfEditor",
                 "TINKER",'GAMESS']
        relwin=subwin.RelatedFunctions(self,-1,self.model,menulst) #,tipslst)
    
    
    def PopUpMenu(self):
        menulst=['close me','---','Undo','---',
                 'Show atmnmb label','Show element','Remove labels',
                 ]
        axispnts=self.model.mousectrl.GetRotationAxisPnts()
        if len(axispnts) > 0:
            menulst.append('---')
            menulst.append('Remove rotation axis')
        nsel,lst=self.model.ListSelectedAtom()
        if nsel == 1:
            menulst.append('---')
            menulst.append('Change element')
            menulst.append('---')
            menulst.append('Del atom')
        elif nsel == 2:
            menulst.append('---')
            menulst.append('Set rotation axis')
            menulst.append('---')
            menulst.append('Change length')
            menulst.append('---')
            menulst.append('Make bond')
            menulst.append('Del bond')
            menulst.append('Set bond multiplicity')
        elif nsel == 3:
            menulst.append('---')
            menulst.append('Set rotation axis')
            
        tiplst=[]
        # pop up menu
        retmethod=self.OnPopUpMenu
        lbmenu=subwin.ListBoxMenu_Frm(self.model.mdlwin.canvas,-1,[],[],
                            retmethod,menulst,tiplst)

    def OnPopUpMenu(self,item,label):
        self.ExecMenuCommand(item,False)            

    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        # Option
        iid=wx.NewId()
        submenu.Append(iid,'Rotation axis flag',
                       'Set rotation axis to connected atoms',
                       kind=wx.ITEM_CHECK)
        submenu.Check(iid,self.setrotaxis)
        submenu.Append(-1,'Remove rotation axis','Remove rotation axis')
        submenu.AppendSeparator()
        submenu.Append(-1,'Remove labels','Remove labels')
        submenu.AppendSeparator()
        submenu.Append(-1,'Del dummy atoms(X)','Delete dummy atoms')
        submenu.AppendSeparator()
        submenu.Append(-1,'Close','Close the window')        
        menubar.Append(submenu,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        #submenu.AppendSeparator()
        #submenu.Append(-1,'Related functions','Execute related functions')
        
        menubar.Append(submenu,'Help')
        #
        return menubar

    def OnMenu(self,event):
        """ Menu event handler
        
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        self.ExecMenuCommand(item,bChecked)

    def ExecMenuCommand(self,item,bChecked):    
        # File menu items
        if item == 'Open':
            pass

        elif item == 'Save ini file':
            pass
        elif item == 'Undo': self.OnUndo(1)
        elif item == 'Rotation axis flag': self.SetRotationAxisFlag(bChecked)
        elif item == 'Remove rotation axis': self.RemoveRotationAxis()
        elif item == 'Selected two atoms': self.SetSelectedAtomPair()
        elif item == 'Set atom pairs': self.SetAtomPairs()
        elif item == 'Remove distance': self.RemoveDistance()
        elif item == 'Remove labels': self.RemoveLabel()
        elif item == 'Del dummy atom(X)': self.DelDummyAtoms()
        elif item == "Close": self.OnClose(1)
        # popup menu
        elif item == 'Show atmnmb label': 
            self.RemoveLabel()
            self.model.menuctrl.OnShow("Atom number",True)
        elif item == 'Show element': 
            self.RemoveLabel()
            self.model.menuctrl.OnShow("Element",True)
        elif item == 'Set rotation axis': self.SetRotationAxis()
        elif item == 'Change element': self.model.ChangeElementAndLength()
        elif item == 'Connect': self.ConnectMols()
        elif item == 'Draw distance': self.model.SetDrawDistance(True)
        elif item == 'Remove distance':
            self.model.SetDrawDistance(False)
            self.model.ClearDrawDistance()
        elif item == 'Change length': 
            self.model.menuctrl.OnChange("Change bond length",False)
        elif item == 'Set bond multiplicity':
            mess='Press 1,2,3,4 key to make multiple bond'
            lib.MessageBoxOK(mess,'OnChange: Change bond multiplicity')
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == 'Related functions': self.RelatedFunctions()

class MutateAAResudes_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos=[],winlabel='MutateResidue'):
        self.title='Mutate amino acid resudues'
        winsize=lib.MiniWinSize((250,250)) #(235,220)
        if len(winpos) <= 0:
            pos=parent.GetPosition()
            size=parent.GetSize()
            winpos=lib.WinPos(parent.mdlwin) #[pos[0]+size[0],pos[1]+20]
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,
               size=winsize,style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        #
        self.winlabel='Mutate AA residue'
        self.SetBackgroundColour('light gray')
        #
        self.parent=parent
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.mol=self.model.mol
        self.winlabel=winlabel
        # ctrlflag
        self.ctrlflag=self.model.ctrlflag

        if self.ctrlflag.Get('mutateresiduewin'):
            mess='"mutate-residue.py" is already running.'
            lib.MessageBoxOK(mess,"")
            global norun
            norun=True; return
        self.ctrlflag.Set('mutateresiduewin',True)
        # icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #               
        self.model.mousectrl.SetSelObj(1)
        self.model.mousectrl.SetSelObjSelection(1)
        #
        self.respanel=None
        self.chirality="L" # "L" or "D"
        self.resnam=''
        self.model.ClearSaveMol()
        #
        self.resnamlst=["ALA","ARG","ASN","ASP","CYS",
                     "GLN","GLU","GLY","ILE",
                     "LEU","LYS","MET","PHE","PRO",
                     "SER","THR","TRP","TYR","VAL",
                     "HIS","HID","HIE"]

        self.CreatePanel()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Show()
    
    def CreatePanel(self):
        pansize=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=[0,0],size=pansize)
        w=pansize[0]; h=pansize[1]
        hbtn=22
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc=5 #+=5
        wx.StaticText(self.panel,-1,'Mutate selected residues to:',
                      pos=(10,yloc),size=(200,18))
        yloc += 20
        winpos=(0,yloc) # winsize=(245,180)
        self.respanel=AAResiduePicker(self.panel,-1,winpos,self.ReturnMethod,
                                          self.model,resnamlst=self.resnamlst)
        yloc=pansize[1]-40 # += 130

        wx.StaticLine(self.panel,pos=(0,yloc),size=(pansize[0],2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        btnundo=wx.Button(self.panel,-1,"Undo",pos=(70,yloc),size=(50,22))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        #btnapl=wx.Button(self.panel,-1,"Apply",pos=(140,yloc),size=(50,22))
        #btnapl.Bind(wx.EVT_BUTTON,self.OnApply)
        btncls=wx.Button(self.panel,-1,"Close",pos=(140,yloc),size=(50,22))
        btncls.Bind(wx.EVT_BUTTON,self.OnClose)

    def OnReset(self):       
        pass
        
    def OnUndo(self,event):
        #self.resnam=''; self.charality='L'
        #mess='Not implemented'
        #mess=lib.MessageBoxOK(mess,'Mutate.Undo')
        self.model.RecoverMol()
    
    def OnApply(self,event):
        if self.resnam == '':
            mess='Residue is not specified. Push one in the panel.'
            lib.MessageBoxOK(mess,'Model.MutateAAResidue') 
            return
        self.Apply()
        
    def Apply(self):
        self.mol=self.model.mol
        self.molobjlst=self.SplitMolIntoResidues(con=False)
        #
        self.MutateResidue([],self.resnam,self.chirality,addh=True)
   
    def ReturnMethod(self,resnam,chirality):
        if resnam == '': return
        self.resnam=resnam
        self.chirality=chirality
        self.Apply()
           
    def UndoMutate(self):
        self.SaveMolForMutateUndo(False)
        
    def OnClose(self,event):
        #self.ctrlflag.Set('peptidewin',False)
        self.model.mousectrl.SetSelObj(0)
        self.model.mousectrl.SetSelObjSelection(0)
        self.model.ClearSaveMol()
        try: self.model.winctrl.Close(self.winlabel)
        except: self.Destroy()
        self.Destroy()
        self.ctrlflag.Set('mutateresiduewin',False)

    def HelpDocument(self):
        helpname='MutateResidue'
        #self.model.helpctrl.Help(helpname)
    
    def Tutorial(self):
        helpname='MutateResidue'
        #self.model.helpctrl.Tutorial(helpname)
    def OpenZmtEditor(self):
        win=ZMatrixEditor_Frm(self.mdlwin,-1)
    
    def ExecTinker(self):
        self.model.ExecuteAddOnScript('tinker-optimize.py',False)
    
    def ExecGAMESS(self):
        self.model.ExecuteAddOnScript('gamess-user.py',False)

    def OpenRotCnfEditor(self):
        win=RotateBond_Frm(self.mdlwin,-1,self.model,[50,150])
    
    def OpenZmtCnfEditor(self):
        pass
    
    def MenuItems(self):
        # Menu items
        menubar=wx.MenuBar()
        # Close
        submenu=wx.Menu()
        #submenu.Append(-1,'Reset selected residues','Gte seelcted residues from model')
        submenu.Append(-1,'Close','Close the panel')
        menubar.Append(submenu,'File')
        # Help        
        submenu=wx.Menu()
        submenu.Append(-1,'Help','Help')
        submenu.AppendSeparator()
        #submenu.Append(-1,'Setting','Setting')
        # related functions
        #subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"ZMatrixEditor",
        #                  "View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"RotCnfEditor",
        #                  "Open Rotate bond conformation editor")
        #subsubmenu.Append(-1,"ZmtCnfEditor",
        #                  "Open Z-matrix conformation editor")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,'Help')
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        #if item == 'Reset selected residues': self.GetSelectedResidues()
        if item == "Close": self.OnClose(1)
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == "ZMatrixEditor": self.OpenZmtEditor()
        elif item == "RotCnfEditor": self.OpenRotCnfEditor()
        elif item == "ZmtCnfEditor": self.OpenZmtcnfEditor()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()

    def MutateResidue(self,targetreslst,mutresnam,chirality,addh=True):
        if len(targetreslst) <= 0: 
            targetreslst=self.model.ListSelectedResidues()
        #
        if len(targetreslst) <= 0:
            mess='No selected residues. Please select residue(s) to be '
            mess=mess+'mutated.'
            lib.MessageBoxOK(mess,'Model(MutateResidue)')
            return
        if targetreslst[0] == mutresnam:
            mess='Current and mutate residue are the same.'
            self.model.ConsoleMessage(mess,'mutate-residue.py(MutateResidue)')
            return
        # save view param
        eyepos,center,upward,ratio=self.model.mdlwin.draw.GetViewParams()
        # make mutate resmol
        # make mutate residue molecule instance
        rescacc,rescbcc,resccc,mutresmol=self.GetSideChainAtoms(mutresnam,
                                                                chirality,addh)
        
        if len(mutresmol.atm) <= 0:
            mess='No atoms in mutate residue name="'+mutresnam+'"'
            lib.MessageBoxOK(mess,'Model(MutateResidue)')
            return
        
        # check CA, CB and C
        if len(rescacc) < 0 or len(rescbcc) < 0 or len(resccc) < 0:
            mess='Missing CA, CB or O(CO) in residue data='+mutresnam
            mess=mess+'. Check the pdbfile in FUDATASET//FUdata.'
            lib.MessageBoxOK(mess,'mutate-residue.py(MutateResidue)')
            return
        # save atmcc for undo
        self.model.SaveMol()
        # make new molecule
        self.model.NewMolecule()
        self.mol=self.model.mol
        #selatmlst=[]
        #keepatmlst=[' N  ',' H  ',' CA ',' HA ',' CB ',' C  ', ' O  ']
        #nres=len(self.molobjlst)
        resdatlst=[]; count=0
        for molobj in self.molobjlst:
            #dellst=[]
            if molobj.name in targetreslst:
                res,nmb,chain=lib.UnpackResDat(molobj.name)
                if not const.AmiRes3.has_key(res):
                    self.model.MergeMolecule(molobj.atm,True,False)
                    continue
                if mutresnam == 'GLY':
                    cacc,cbcc,ccc,molobj=self.ExtractCACBC(molobj)
                    for atom in molobj.atm:
                        if atom.atmnam == ' HA ': atom.atmnam=' HA2'
                        if atom.atmnam == ' CB ': 
                            atom.atmnam=' HA3'
                            atom.cc=lib.CalcPositionWithNewBL(cacc,cbcc,1.09)
                        atom.resnam=mutresnam
                        atom.resnmb=nmb
                        atom.chainam=chain
                elif mutresnam == molobj.name[:3]:
                    pass
                else:
                    resmol=mutresmol.CopyMolecule()
                    #    """ just replace HA and CB with HA" and HA3 """
                    cacc,cbcc,ccc,molobj=self.ExtractCACBC(molobj)
                    for atom in molobj.atm: atom.resnam=mutresnam
                    # move resmol CB atoms at CB
                    resmolcc=self.CoordsAlignedCACB(cacc,cbcc,ccc,rescacc,
                                                    rescbcc,resccc,resmol)
                    resmolcc=self.CoordsAlignedCACBC(cacc,cbcc,ccc,resmolcc)               
                    # append side chain atoms
                    seq=len(molobj.atm)-1
                    for j in range(len(resmol.atm)):
                        seq += 1
                        molobj.atm.append(resmol.atm[j])
                        molobj.atm[seq].seqnmb=seq
                        molobj.atm[seq].cc=resmolcc[j]
                        molobj.atm[seq].resnam=mutresnam
                        molobj.atm[seq].resnmb=nmb
                        molobj.atm[seq].chainnam=chain
                resdat=lib.PackResDat(mutresnam,nmb,chain)
                resdatlst.append(resdat)
                count += 1
            # merge 
            warn=True
            if count > 1: warn=False
            self.model.MergeMolecule(molobj.atm,warn,False)
        # make bonds
        self.model.mol.AddBondUseBL([])
        self.model.SetSelectAll(False)
        self.model.SelectResidue(resdatlst,True)
        # recover view
        self.model.mdlwin.draw.SetViewParams(eyepos,center,upward,ratio)
        #self.model.FitToScreen(True,True)
        self.model.DrawMol(True)
        #
        mess='The residues '+lib.ListToText(targetreslst,',')
        mess=mess+' were mutated by '+mutresnam+'(chirality='+chirality+')'
        self.model.ConsoleMessage(mess)
        mess=self.model.mol.name+': Number of atoms='
        mess=mess+str(len(self.model.mol.atm))
        self.model.ConsoleMessage(mess)

        self.model.mousectrl.SetSelObj(1)
        self.model.mousectrl.SetSelObjSelection(1)

    def GetSideChainAtoms(self,mutresnam,chirality,addh):
        resdatdir=self.model.setctrl.GetDir('FUdata')
        resobj=lib.AAResidueAtoms(self,resdatdir,hydrogens=addh)
        mutresatmlst=resobj.GetResidueAtomData(mutresnam,chirality)
        resmol=molec.Molecule(self.model)
        delatmlst=[' N  ',' H1 ',' H2 ',' H3 ',' CA ',' HA ',' CB ',' C  ',
                   ' O  ', ' OXT']
        seqnmb=-1; resmolca=-1; resmolcb=-1; resmolc=-1
        cclst=[]
        """ GLY CA, HA2,HA3 """
        for i in range(len(mutresatmlst)): # elm,atmnam,cc
            """ except gly, and pro: need special codes for them """
            atmnam=mutresatmlst[i][1]; atomcc=mutresatmlst[i][2][:]
            if atmnam == ' CA ': 
                resmolca=i; rescacc=numpy.array(atomcc[:])
            if atmnam == ' CB ': 
                resmolcb=i; rescbcc=numpy.array(atomcc[:])
            if atmnam == ' C  ': 
                resmolc=i; resccc=numpy.array(atomcc[:])
            # special code for GLY
            if mutresnam == 'GLY' and atmnam == ' HA3':
                resmolcb=i; rescbcc=numpy.array(atomcc[:])
            if mutresnam == 'GLY' and atmnam == ' HA2':
                mutresatmlst[i][1]=' HA '
            if mutresatmlst[i][1] in delatmlst: continue
            seqnmb += 1
            atom=molec.Atom(resmol)
            atom.seqnmb=seqnmb
            atom.elm=mutresatmlst[i][0]
            atom.atmnam=mutresatmlst[i][1]
            atom.cc=atomcc[:]
            cclst.append(atomcc[:])
            atom.resnam=mutresnam
            atom.SetAtomParams(atom.elm)
            resmol.atm.append(atom)
        return  rescacc,rescbcc,resccc,resmol

    def CoordsAlignedCACB(self,cacc,cbcc,ccc,rescacc,rescbcc,resccc,resmol):
        dcc=rescbcc-cbcc
        resmolcc=[]
        for atom in resmol.atm:
            cc0=atom.cc[0]-dcc[0]; cc1=atom.cc[1]-dcc[1]; cc2=atom.cc[2]-dcc[2] 
            atom.cc=[cc0,cc1,cc2]
            resmolcc.append([cc0,cc1,cc2])
        rescacc=numpy.array(rescacc-dcc); rescbcc=numpy.array(rescbcc-dcc)
        resccc=numpy.array(resccc-dcc)
        resmolcc.append(rescacc); resmolcc.append(rescbcc)
        resmolcc.append(resccc)
        # rotate resmol to alline CA-CB
        vec12=cacc-cbcc
        vec34=rescacc-rescbcc
        da=lib.AngleT(vec34,vec12)
        ax=lib.NormalVector(rescacc,cbcc,cacc) #(cacc,cbcc,rescacc)
        u=lib.RotMatAxis(ax,da)
        resmolcc=lib.RotMol(u,cbcc,resmolcc)
        #
        return resmolcc        
   
    def CoordsAlignedCACBC(self,cacc,cbcc,ccc,resmolcc):
        """ rescacc,rescbcc,resccc are in resmolcc """
        rescacc=numpy.array(resmolcc[-3])
        rescbcc=numpy.array(resmolcc[-2])
        resccc=numpy.array(resmolcc[-1])
        vec12=ccc-cacc
        vec23=resccc-rescacc
        da=lib.AngleT(vec23,vec12)
        ax=cbcc-cacc
        u=lib.RotMatAxis(ax,da) 
        resmolcc=lib.RotMol(u,cacc,resmolcc)
        return resmolcc
        
    def ExtractCACBC(self,molobj):
        keepatmlst=[' N  ',' H  ',' CA ',' HA ',' CB ',' C  ', ' O  ']
        rcacb=1.54
        # glycine
        if molobj.name[:3] == 'GLY':
            for i in range(len(molobj.atm)):
                if molobj.atm[i].atmnam == ' CA ': cacc=molobj.atm[i].cc
                if molobj.atm[i].atmnam == '1HA ' or \
                                               molobj.atm[i].atmnam == ' HA2': 
                    molobj.atm[i].atmnam=' HA '
                if molobj.atm[i].atmnam == '2HA ' or \
                                               molobj.atm[i].atmnam == ' HA3':
                    molobj.atm[i].atmnam=' CB '
                    molobj.atm[i].elm=' C'
                    molobj.atm[i].cc=lib.CalcPositionWithNewBL(cacc,
                                                       molobj.atm[i].cc,rcacb)
        dellst=[]
        for atom in molobj.atm:
            if atom.atmnam == ' CA ': cacc=numpy.array(atom.cc)
            if atom.atmnam == ' CB ': cbcc=numpy.array(atom.cc)
            if atom.atmnam == ' C  ': ccc=numpy.array(atom.cc)
            if not atom.atmnam in keepatmlst: dellst.append(atom.seqnmb) 
        # delete unneeded atoms
        molobj.DelAtoms(dellst)
        #
        return cacc,cbcc,ccc,molobj
        
    def SplitMolIntoResidues(self,con=False):
        """ split molecule into residues
        
        :param bool con: True for keep connect, False fordelet
        :return: molobjlst(lst) - list of residue mol objects
        """
        reslst=self.model.ListResidue3(True) # reslst: [resdat,...]
        if len(reslst) <= 0:
            mess='No residues in '+self.model.mol.Name
            self.model.ConsoleMessage(mess)
            return
        molatm=self.model.mol.CopyAtom()
        molobjlst=[]
        for resdat in reslst:
            mol=molec.Molecule(self.mdlwin)
            mol.name=resdat
            mol.inpfilet=self.model.mol.inpfile
            atmlst=self.model.ListResDatAtoms(resdat)
            seq=-1
            for i in atmlst: 
                seq += 1
                molatm[i].seqnmb=seq
                molatm[i].conect=[]
                molatm[i].show=True
                molatm[i].select=False
                mol.atm.append(molatm[i])
            #if con: mol.AddBondUseBL([])
            molobjlst.append(mol)
        return molobjlst

    def SaveMolForMutateUndo(self,on):
        """
        
        :param bool on: True for save, False for recover
        """
    
        scratchdir=self.setctrl.GetDir('Scratch')
        savefile=os.path.join(scratchdir,'mutateres.tmp')
        self.ConsoleMessage('savefile='+savefile)
        if on:
            #try:
            f=open(savefile,'wb')
            pickel.dump(self.model.mol.atm,f)
            f.close()
            #except: pass
        else:
            if not os.path.exists(savefile):
                mess='No undo data saved on savefile='+savefile
                lib.MessageBoxOK(mess,'MutateAAResidue(SaveMolForUndo)')
                return
            try:
                f=open(savefile,'rb')
                atm=pickel.load(f)
                f.close()
            except: pass
            self.model.mol.atm=atm
            self.DrawMol(True)

class Polypeptide_Frm(wx.Frame):
    def __init__(self,parent,id):
        self.title='Polypeptide Builder'
        winsize=lib.WinSize((260,370)) #320)
        #pos=parent.GetPosition()
        #size=parent.GetSize()
        #winpos=[pos[0]+size[0],pos[1]+20]
        winpos=lib.WinPos(parent.mdlwin)
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        [w,h]=self.GetClientSize()
        self.winxsize=w; self.winymin=h
        self.winlabel='PolypeptideBuilder'
        self.helpname=self.winlabel #'PolypeptideBuilder'
        #self.setfile=parent.model.setfile
        self.parent=parent
        self.model=parent
        self.mdlwin=self.model.mdlwin
        # ctrlflag
        self.ctrlflag=self.model.ctrlflag
        self.mol=self.model.mol
        if not self.model.mol: 
            self.model.read=True
            self.model.NewMolecule()
            self.mol=self.model.mol
        self.molnam=self.model.mol.name
        self.setctrl=self.model.setctrl
        if self.molnam == "": self.model.NewMolecule()
        # check if the script is running
        if self.ctrlflag.Get('peptidewin'):
            """
            mess='"polypeptide.py" is already running.'
            lib.MessageBoxOK(mess,"")
            global norun
            norun=True; return
            """
            polypep.Destroy()
        self.ctrlflag.Set('peptidewin',True)
        # residue data are in FUDATASET/FUdata directory
        self.fudatadir=self.model.setctrl.GetDir('FUdata')
        # icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        self.notepadexe="C:\\Windows\\System32\\notepad.exe"
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #               
        self.chidic={"ALA":1,"ARG":1,"ASN":1,"ASP":1,"CYS":1,
                     "GLN":1,"GLU":1,"GLY":0,"HIS":1,"ILE":1,
                     "LEU":1,"LYS":1,"MET":1,"PHE":1,"PRO":1,
                     "SER":1,"THR":1,"TRP":1,"TYR":1,"VAL":1,
                     "ACE":0,"NME":0}
        self.resnam=self.chidic.keys()
        self.resnam.sort()
        self.resnam.remove("ACE"); self.resnam.remove("NME")
        self.resnam.append("ACE"); self.resnam.append("NME")
        # amino acid sequence file
        self.seqfile=""
        # aa residue object
        self.aaresobj=lib.AAResidueAtoms(self,self.fudatadir,hydrogens=False)
        #
        self.chirality="L" # "L" or "D"
        self.conf=2 # 0:alpjha, 1:beta, 2:stretch
        self.phi="180.0"; self.psi="180.0"; self.omg="180.0"
        self.chi1="180.0"; self.chi2="180.0"; self.chi3="180.0"
        self.chi4="180.0"
        self.chi5="180.0"; self.defchi="180.0"
        self.chivar={"ALA":[1,0,0,0,0],"ALG":[]} # chivariable for each residue, 0:False, 1:True
        self.defangle={"alpha":["-58.0","-47.0","180.0"],
                       "beta":["-119.0","113.0","180.0"],
                       "stretch":["180.0","180.0","180.0"]}
        self.defchi1="180.0"; self.defchi2="180.0"
        self.defchi3="180.0"; self.defchi4="180.0"; 
        # make new mol
        self.nres=0
        self.existres=False
        self.resnmb=0
        self.atmnmb=0
        self.amiresseqlst=[] # [["ALA",phi,psi,omega,chi1,...],...]
        if self.model.mol == None:
            self.model.NewMolecule()
            #self.mol=self.model.mol
        #
        self.CreatePanel()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnSize)
    
        self.Show()

    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        ysize=h
        xsize=self.winxsize
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        #
        #btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc=5
        self.rbtalp=wx.RadioButton(self.panel,-1,"alpha-helix",pos=(5,yloc),
                                   style=wx.RB_GROUP) #size=(60,18))
        self.rbtalp.Bind(wx.EVT_RADIOBUTTON,self.OnAlpha)
        self.rbtbet=wx.RadioButton(self.panel,-1,"beta-strand",pos=(90,yloc)) #,size=(60,18))
        self.rbtbet.Bind(wx.EVT_RADIOBUTTON,self.OnBeta)
        self.rbtoth=wx.RadioButton(self.panel,-1,"other",pos=(180,yloc)) #,size=(60,18))
        self.rbtoth.Bind(wx.EVT_RADIOBUTTON,self.OnOther)
        self.SetConformation()
        yloc += 22; ws=40
        wx.StaticText(self.panel,-1,"phi",pos=(10,yloc),size=(20,18)) 
        self.tclphi=wx.TextCtrl(self.panel,-1,self.phi,pos=(35,yloc),
                                size=(ws,18))
        self.tclphi.Bind(wx.EVT_TEXT,self.OnAngle)
        wx.StaticText(self.panel,-1,"psi",pos=(80,yloc),size=(20,18)) 
        self.tclpsi=wx.TextCtrl(self.panel,-1,self.psi,pos=(105,yloc),
                                size=(ws,18))
        self.tclpsi.Bind(wx.EVT_TEXT,self.OnAngle)
        wx.StaticText(self.panel,-1,"omg",pos=(150,yloc),size=(25,18)) 
        self.tclomg=wx.TextCtrl(self.panel,-1,self.omg,pos=(175,yloc),
                                size=(ws,18))
        self.tclomg.Bind(wx.EVT_TEXT,self.OnAngle)
        yloc += 25
        wx.StaticText(self.panel,-1,"chi1",pos=(10,yloc),size=(22,18)) 
        self.tclchi1=wx.TextCtrl(self.panel,-1,self.chi1,pos=(35,yloc),
                                 size=(ws,18))
        self.tclchi1.Bind(wx.EVT_TEXT,self.OnAngle)
        self.tclchi1.Disable() # not supported yet       
        wx.StaticText(self.panel,-1,"chi2",pos=(80,yloc),size=(22,18)) 
        self.tclchi2=wx.TextCtrl(self.panel,-1,self.chi2,pos=(105,yloc),
                                 size=(ws,18))
        self.tclchi2.Bind(wx.EVT_TEXT,self.OnAngle)
        self.tclchi2.Disable() # not supported yet
        wx.StaticText(self.panel,-1,"chi3",pos=(150,yloc),size=(22,18)) 
        self.tclchi3=wx.TextCtrl(self.panel,-1,self.chi3,pos=(175,yloc),
                                 size=(ws,18))
        self.tclchi3.Bind(wx.EVT_TEXT,self.OnAngle)
        self.tclchi3.Disable() # not supported yet
        yloc += 25
        wx.StaticText(self.panel,-1,"chi4",pos=(10,yloc),size=(22,18)) 
        self.tclchi4=wx.TextCtrl(self.panel,-1,self.chi4,pos=(35,yloc),
                                 size=(ws,18))
        self.tclchi4.Bind(wx.EVT_TEXT,self.OnAngle)
        self.tclchi4.Disable() # not supported yet
        self.SetAngle()
        #
        btncls=wx.Button(self.panel,wx.ID_ANY,"Reset chi",pos=(155,yloc-2),
                         size=(60,22))
        btncls.Bind(wx.EVT_BUTTON,self.OnReset)
        btncls.Disable() # not supported yet
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        # residue button panel
        winpos=(0,yloc)
        self.respanel=AAResiduePicker(self.panel,-1,winpos,self.ReturnMethod,
                                      self.model)
        winsize=self.respanel.GetSize()
        yloc += winsize[1]+5 #50
        #wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8; hsiz=ysize-yloc-40
        self.tcldsp=wx.TextCtrl(self.panel,pos=(10,yloc),size=(w-20,hsiz),
                                style=wx.TE_MULTILINE)
        self.DispSequence()
        #yloc += 35
        yloc=ysize-30
        btnreset=wx.Button(self.panel,wx.ID_ANY,"New",pos=(30,yloc),
                           size=(40,22))
        btnreset.Bind(wx.EVT_BUTTON,self.OnNew)
        btnund=wx.Button(self.panel,wx.ID_ANY,"Del last",pos=(90,yloc),
                         size=(55,22))
        btnund.Bind(wx.EVT_BUTTON,self.OnDelLast)
        btncls=wx.Button(self.panel,wx.ID_ANY,"Close",pos=(165,yloc),
                         size=(45,22))
        btncls.Bind(wx.EVT_BUTTON,self.OnClose)

    def SetExistingResidue(self):
        # amiresseqlst: [["ALA",resnumber,phi,psi,omega,chi1,...],...]    
        self.resseqlst=[]
        reslst=self.model.ListResidue(True)
        #print 'reslst',reslst
        nchain=len(reslst)
        nres=len(reslst[nchain-1])
        if nres > 0:
            nam=reslst[nchain-1][nres-1][0]; nmb=reslst[nchain-1][nres-1][1]
            if not const.AmiRes3.has_key(nam):
                mess='The last residue '+nam
                mess=mess+' is not amino acid. Unable to continue.'
                lib.MessageBoxOK(mess,"")
                self.OnClose(1)
            phi,psi,omg=self.CalcPhiPsiOmega(nam,nmb)
            chi1,chi2,chi3,chi4=self.CalcChi(nam,nmb)
            self.resseqlst.append([nam,nmb,phi,psi,omg,chi1,chi2,chi3,chi4,
                                   'L'])
        self.nres=1
        self.resnmb=nmb
        lastatm=len(self.model.mol.atm)
        self.atmnmb=self.model.mol.atm[lastatm-1].seqnmb+1
        self.existres=True
    
    def CalcChi(self,resnam,resnmb):
        # res: amini acid residue name, i.e. 'ALA'.
        chi1=180.0; chi2=180.0; chi3=180.0; chi4=180.0
        return chi1,chi2,chi3,chi4
    
    def OnNew(self,event):
        self.mol=self.model.mol
        if self.mol == None:
            self.model.NewMolecule()
            self.mol=self.model.mol
        #
        self.DelAll()
        self.model.DrawMol(True)

    def DelAll(self):
        self.nres=0
        self.existres=False
        self.resnmb=0
        self.atmnmb=0
        self.amiresseqlst=[] # [["ALA",phi,psi,omega,chi1,...],...]
        self.model.mol.atm=[]
        #
        try: self.tcldsp.SetValue("")
        except: pass
        
    def OnAlpha(self,event):
        self.conf=0
        try: 
            self.tclphi.SetValue(self.defangle["alpha"][0])
            self.tclpsi.SetValue(self.defangle["alpha"][1])
            self.tclomg.SetValue(self.defangle["alpha"][2])
            self.GetAngle()
        except: pass
        
    def OnBeta(self,event):
        self.conf=1
        try:
            self.tclphi.SetValue(self.defangle["beta"][0])
            self.tclpsi.SetValue(self.defangle["beta"][1])
            self.tclomg.SetValue(self.defangle["beta"][2])
            self.GetAngle()
        except: pass
    
    def OnOther(self,event):
        self.conf=2
        try:
            self.tclphi.SetValue(self.defangle["stretch"][0])
            self.tclpsi.SetValue(self.defangle["stretch"][1])
            self.tclomg.SetValue(self.defangle["stretch"][2])
            self.GetAngle()
        except: pass
        
    def SetConformation(self):
        if self.conf == 0: self.rbtalp.SetValue(True)
        if self.conf == 1: self.rbtbet.SetValue(True)
        if self.conf == 2: self.rbtoth.SetValue(True)
        
    def OnReset(self,event):
        self.tclchi1.SetValue(self.defchi1) 
        self.tclchi2.SetValue(self.defchi2)
        self.tclchi3.SetValue(self.defchi3) 
        self.tclchi4.SetValue(self.defchi4)        

    def OnAngle(self,event):
        self.GetAngle()
   
    def GetAngle(self):
        self.phi=self.tclphi.GetValue()
        self.psi=self.tclpsi.GetValue()
        self.omg=self.tclomg.GetValue()
        self.chi1=self.tclchi1.GetValue()
        self.chi2=self.tclchi2.GetValue()
        self.chi3=self.tclchi3.GetValue()
        self.chi4=self.tclchi4.GetValue()
        
    def SetAngle(self):
        self.tclphi.SetValue(self.phi)
        self.tclpsi.SetValue(self.psi)
        self.tclomg.SetValue(self.omg)
        self.tclchi1.SetValue(self.chi1)
        self.tclchi1.SetValue(self.chi2)
        self.tclchi1.SetValue(self.chi3)
        self.tclchi1.SetValue(self.chi4)

    def OnLChirality(self,event):
        self.chirality="L"

    def OnDChirality(self,event):
        self.chirality="D"
        
    def SetChirality(self):
        if self.chirality == "L": self.rbtlll.SetValue(True) 
        if self.chirality == "D": self.rbtddd.SetValue(True) 
        
    def GetChirality(self):
        if self.rbtlll.GetValue(): chirality="L"
        if self.rbtddd.GetValue(): chirality="D"
        return chirality
    
    def DispSequence(self):
        if len(self.amiresseqlst) <= 0: return
        text=""; first=0
        if self.existres: first=1
        for i in range(first,len(self.amiresseqlst)):
            res=self.amiresseqlst[i][0]; chiral=""
            if self.chirality == "D":
                if res != "ACE" and res!= "NME": chiral="D-"
            text=text+str(i+1)+":"+chiral+res+","
        text=text[:len(text)-1]
        self.tcldsp.SetValue(text)
    
    def ReturnMethod(self,res,chirality):
        if res == "NME" and self.resnmb == 0:
            mess='Unable to put "NME" at the first position'
            lib.MessageBoxOK(mess,"")
            return
        self.chirality=chirality
        self.resnmb += 1
        resdat=[res,self.resnmb,self.phi,self.psi,self.omg,self.chi1,
                self.chi2,self.chi3,self.chi4,self.chirality]
        self.amiresseqlst.append(resdat)
        self.DispSequence()
        #
        self.AddAARes()

    def MakePolypeptide(self):
        for i in range(len(self.amiresseqlst)):
            self.resnmb += 1; self.AddAARes()
            
    def AddAARes(self):
        tmp=molec.Molecule(self.model)
        nres=len(self.amiresseqlst)
        resdat=self.amiresseqlst[self.resnmb-1]
        #
        res=resdat[0]; nmb=resdat[1]; cc=[]; oxtseq=-1; oxtcc=[]
        aacclst=self.aaresobj.GetResidueAtomData(res,self.chirality)
        if len(self.model.mol.atm) <= 0: # == None:
            for elm,atm,coord in aacclst: cc.append(coord)
        else:
            natm=len(self.model.mol.atm)
            lastnam=self.model.mol.atm[natm-1].resnam
            lastnmb=self.model.mol.atm[natm-1].resnmb
            ncc,cacc,ccc,occ,oxtcc,oxtseq=self.GetBackboneCC(lastnam,lastnmb)        
            if  resdat[0] != 'NME' and (len(ccc) <= 0 or len(oxtcc) <= 0):
                mess='Failed to find "C" or "OXT" in the last residue '+ \
                      lastnam+':'+str(lastnmb)+'. Unable to continue.'
                lib.MessageBoxOK(mess,"")
                del self.amiresseqlst[self.resnmb-1]
                return
            cc=self.CalcResidueCC(aacclst,resdat,ncc,cacc,ccc,occ,oxtcc)
        #
        if len(self.model.mol.atm) > 0: self.model.DeleteBonds('all',False)
        if oxtseq > 0: del self.model.mol.atm[oxtseq]
        
        tmp.atm=self.MakeTempMol(tmp,res,aacclst,cc)

        self.model.MergeMolecule(tmp.atm,False) #ecule(tmp.mol,False) 
        # renumner seqnmb
        for i in range(len(self.model.mol.atm)): self.model.mol.atm[i].seqnmb=i

        self.model.mol.AddBondUseBL([])
        self.model.SetUpDraw(True)
        
        self.model.Message(res+":"+str(nmb)+" residue is added.",0,"")

    def MakeTempMol(self,tmp,res,aacclst,cc):
        seqnmb=len(self.model.mol.atm)
        for i in range(len(cc)):
            self.atmnmb += 1
            atom=molec.Atom(self)
            atom.seqnmb=i+seqnmb
            atom.atmnmb=self.atmnmb
            atom.cc=cc[i][:]
            atom.conect=[]
            atom.atmnam=aacclst[i][1]
            atom.resnam=res
            atom.resnmb=self.resnmb
            atom.elm=aacclst[i][0]
            #
            elm=atom.elm
            atom.SetAtomParams(elm)
            #
            tmp.atm.append(atom)
         
        return tmp.atm 

    def CalcResidueCC(self,aacclst,resdat,pncc,pcacc,pccc,pocc,poxtcc):
        # cseq,ccc: seqnmber of "C" atom and it coordinates of previous residue
        # oseq,occ: seqnmber of "OXT" atom and it coordinates of previous residue
        # return transformed coordinates of orgcc
        orgcc=[]     
        for elm,atm,coord in aacclst: orgcc.append(coord[:])
        cc=[]
        # translate "N" to "OXT" of previos residue 1.250
        rnc=1.335 
        if resdat[0] == 'NME': rnc=1.48
        ncc=lib.CalcPositionWithNewBL(pccc,poxtcc,rnc)
        # assuming that the first atom is "N" in orgcc
        ncc0,cacc0,ccc0,occ0,oxtcc0=self.GetCCInResDic(aacclst,orgcc)
        dx=ncc[0]-ncc0[0]; dy=ncc[1]-ncc0[1]; dz=ncc[2]-ncc0[2]
        
        for i in range(len(orgcc)):
            cc.append([orgcc[i][0]+dx,orgcc[i][1]+dy,orgcc[i][2]+dz])
             
        if self.resnmb == 1: return cc
        # set angle C-N-CA,pccc-ncc0, cacc0-ncc0
        ra=numpy.subtract(pccc,cc[0]); rb=numpy.subtract(cc[1],cc[0])
        ang0=lib.AngleT(ra,rb)
        # 122.0 deg
        ang=122.0*(3.141529/180.0)
        ang=ang-ang0
        axi=numpy.cross(ra,rb)
        axi=axi/numpy.dot(axi,axi)
        u=lib.RotMatAxis(axi,ang)
        cc1=[]
        for i in range(1,len(cc)): cc1.append(cc[i][:])
        cct=lib.RotMol(u,cc[0],cc1)
        for i in range(1,len(cc)): cc[i]=cct[i-1][:]
 
        if resdat[0] == 'NME': return cc        
        
        if resdat[0] == 'PRO':
            phi=-75.0*(3.1415/180.0) # right hand-side helix        
            psi=160.0*(3.1415/180.0) # right hand-side helix
            omg=0.0
        omg=3.1415*(float(resdat[4])/180.0)
        phi=3.1415*(float(resdat[2])/180.0)
        psi=3.1415*(float(resdat[3])/180.0)
        # assume N-CA-C-O sequence in resdat
        # Omega
        resnam=resdat[0]; resnmb=resdat[1]
        ncc,cacc,ccc,occ,oxtcc=self.GetCCInResDic(aacclst,cc)
        omg0=lib.TorsionAngle(cacc,ncc,pccc,pocc) #pcacc,pccc,ncc,cacc)
        rotang=-omg0-omg-3.1415
        #rotang=-comg+3.141519
        # omega
        """ Ca(i-1)-C(i-1)=N(i)-Ca(i) """
        """  pccc is C(i-1), ncc is N(i)  """
        v=numpy.subtract(pccc,ncc)
        #v=[pccc[0]-ncc[0],pccc[1]-ncc[1],pccc[2]-ncc[2]]
        u=lib.RotMatAxis(v,-rotang)
        cc1=[]
        for i in range(1,len(cc)): cc1.append(cc[i][:])
        cct=lib.RotMol(u,ncc,cc1)
        for i in range(1,len(cc)): cc[i]=cct[i-1][:]
        # phi
        """ C(i-1)-N(i)=Ca(i)-C(i) """
        ncc1,cacc1,ccc1,occ1,oxtcc1=self.GetCCInResDic(aacclst,cc)
        phi0=lib.TorsionAngle(ccc1,cacc1,ncc1,pccc) #pccc,ncc1,cacc1,ccc1)       
        rotang=phi-phi0
        #rotang=-cphi+3.141519
        v=numpy.subtract(cacc1,ncc1)
        #v=[cacc[0]-ncc[0],cacc[1]-ncc[1],cacc[2]-ncc[2]]
        u=lib.RotMatAxis(v,rotang)
        cc1=[]
        for i in range(2,len(cc)): cc1.append(cc[i][:])
        #del cc1[0]; del cc1[1]
        cct=lib.RotMol(u,cacc1,cc1) 
        for i in range(2,len(cc)): cc[i]=cct[i-2][:]
        # psi
        """ N(i)-Ca(i)=C(i)-N(i+1) N(i+1) is OXT """
        ncc2,cacc2,ccc2,occ2,oxtcc2=self.GetCCInResDic(aacclst,cc)
        psi0=lib.TorsionAngle(oxtcc2,ccc2,cacc2,ncc2) #ncc2,cacc2,ccc2,oxtcc2)
        #print 'cpsi',psi0*(180.0/3.1415)
        rotang=psi-psi0
        #rotang=-cpsi+3.141519
        v=numpy.subtract(ccc2,cacc2)
        #v=[ccc[0]-cacc[0],ccc[1]-cacc[1],ccc[2]-cacc[2]]
        u=lib.RotMatAxis(v,rotang)
        cc1=[]
        #for i in range(4,len(cc)): cc1.append(cc[i][:])
        na=len(cc)
        print 
        cc1.append(cc[3][:]); cc1.append(cc[na-1][:])
        cct=lib.RotMol(u,ccc2,cc1)        
        cc[3]=cct[0][:]; cc[na-1]=cct[1][:]

        return cc

    def GetBackboneCC(self,resnam,resnmb):
        ncc=[]; cacc=[]; ccc=[]; occ=[]; oxtcc=[]; oxtseq=-1
        i=-1
        for atom in self.model.mol.atm:
            i += 1
            if atom.elm == "XX": continue
            if atom.resnam != resnam or atom.resnmb != resnmb: continue
            if atom.atmnam == " N  ": ncc=atom.cc[:]
            if atom.atmnam == " CA ": cacc=atom.cc[:]
            if atom.atmnam == " C  ": ccc=atom.cc[:]
            if atom.atmnam == " O  ": occ=atom.cc[:]
            if atom.atmnam == " OXT":
                oxtcc=atom.cc[:]; oxtseq=i #atom.seqnmb
        return ncc,cacc,ccc,occ,oxtcc,oxtseq

    def GetCCInResDic(self,aacclst,cc):
        ncc=[]; cacc=[]; ccc=[]; occ=[]; oxtcc=[]
        #for elm,atm,coord in aaccdic:
        for i in range(len(aacclst)):
            atm=aacclst[i][1]
            if atm == " N  ": ncc=cc[i][:]
            if atm == " CA ": cacc=cc[i][:]
            if atm == " C  ": ccc=cc[i][:]
            if atm == " O  ": occ=cc[i][:]
            if atm == " OXT": oxtcc=cc[i][:]
        return ncc,cacc,ccc,occ,oxtcc
                
    def CalcPhiPsiOmega(self,resnam,resnmb):
        """ not comleted yet. 04, Dec 2013 """
        """
        # dihedral test
        reslst=self.model.ListResidue(True)
        print 'reslst',reslst
        if len(reslst) > 0:
            for i in range(len(reslst)):
                for j in range(1,len(reslst[i])-1):
                    nam=reslst[i][j][0]; nmb=reslst[i][j][1]
                    phi,psi,omg=self.CalcPhiPsiOmega(nam,nmb)
                    #print 'phi,psi,omg',phi,psi,omg
        """
        # res: given as resnam+":"+str(resnmb)
        resn=resnam+":"+str(resnmb)

        reslst=self.model.ListResidue(True)
        resseqdic={}
        for atom in self.model.mol.atm:
            restmp=atom.resnam+":"+str(atom.resnmb)
            if not resseqdic.has_key(restmp): resseqdic[restmp]=[]
            resseqdic[restmp].append(atom.seqnmb)
        
        for i in range(len(reslst)): # chain loop
            nres=len(reslst[i])
            for j in range(len(reslst[i])):
                nam=reslst[i][j][0]; nmb=reslst[i][j][1]
                res=nam+":"+str(nmb)
                if res == resn:
                    if j == 0: prev=-1
                    else:
                        prev=j-1
                        prevres=reslst[i][j-1][0]+":"+str(reslst[i][j-1][1])
                    if j == nres-1: next=-1
                    else:
                        next=j+1 
                        nextres=reslst[i][j+1][0]+":"+str(reslst[i][j+1][1])
                    #break
        # phi is the dihedral angle of C(i-1)-N(i)-Ca(i)-C(i),
        # psi is the dihedral angle of N(i)-Ca(i)-C(i)-N(i+1),
        # omega is the dihedral angle of Ca(i)-C(i)-N(i+1)-Ca(i+1)
        phi=99.9; psi=99.9; omg=99.9; atm=[]; cc=[]
        if prev >= 0:
            for i in resseqdic[prevres]:
                if self.model.mol.atm[i].atmnam == " C  ":
                    pccc=self.model.mol.atm[i].cc
                    #print ' C1  found'
                    atm.append(i); break 
        for i in resseqdic[resn]:
            if self.model.mol.atm[i].atmnam == " N  ":
                #print ' N2  found'
                ncc=self.model.mol.atm[i].cc
                atm.append(i); break
        for i in resseqdic[resn]:
            if self.model.mol.atm[i].atmnam == " CA ":
                #print ' CA3  found'
                cacc=self.model.mol.atm[i].cc
                atm.append(i); break
        for i in resseqdic[resn]:
            if self.model.mol.atm[i].atmnam == " C  ":
                #print ' C4  found'
                ccc=self.model.mol.atm[i].cc
                atm.append(i); break
        if next > 0:
            for i in resseqdic[nextres]:
                if self.model.mol.atm[i].atmnam == " N  ":
                    #print ' N5  found'
                    nncc=self.model.mol.atm[i].cc
                    atm.append(i); break 
            for i in resseqdic[nextres]:
                if self.model.mol.atm[i].atmnam == " CA ":
                    #print ' CA6  found'
                    ncacc=self.model.mol.atm[i].cc
                    atm.append(i); break 
        #print 'atm',atm
        
        for i in atm:
            cc.append(self.model.mol.atm[i].cc)
        #print 'cc',cc
        
        i=0
        if prev >= 0:
            #phi=lib.TorsionAngle(cc[i],cc[i+1],cc[i+2],cc[i+3])
            #phi=lib.TorsionAngle(cc[0],cc[1],cc[2],cc[3])
            phi=lib.TorsionAngle(pccc,ncc,cacc,ccc)
            i=1         
        if next >= 0:
            #psi=lib.TorsionAngle(cc[i],cc[i+1],cc[i+2],cc[i+3])
            #omg=lib.TorsionAngle(cc[i+1],cc[i+2],cc[i+3],cc[i+4])               
            #psi=lib.TorsionAngle(cc[1],cc[2],cc[3],cc[4])
            psi=lib.TorsionAngle(ncc,cacc,ccc,nncc)
            omg=lib.TorsionAngle(pccc,ncc,cacc,ccc)               

        deg=180.0/3.14159
        print 'phi,psi,omg',phi*deg,psi*deg,omg*deg
        
        return phi,psi,omg
        
    def RemunberResSeq(self):
        nres=len(self.amiresseqlst)
        for i in range(nres):
            self.amiresseqlst[i][1]=i+1
        
    def OnDelLast(self,event):
        nres=len(self.amiresseqlst)
        if nres <= 1:
            lib.MessageBoxOK("No residues.","")
            return 
        res=self.amiresseqlst[nres-1][0]; nmb=self.amiresseqlst[nres-1][1]
        res1=self.amiresseqlst[nres-2][0]; nmb1=self.amiresseqlst[nres-2][1]
        #
        lst=[]; cc=[]; roxt=1.25
        for atom in self.model.mol.atm:
            if atom.resnam == res1 and atom.resnmb == nmb1:
                if atom.atmnam == " C  ": cc0=atom.cc[:]
            if atom.resnam == res and atom.resnmb == nmb:
                if atom.atmnam != " N  ": lst.append(atom.seqnmb)
                else:
                    atom.atmnam=" OXT"; atom.elm=" O"
                    atom.resnam=res1; atom.resnmb=nmb1
                    cc1=atom.cc[:]
                    if len(cc0) > 0: 
                        cc=lib.CalcPositionWithNewBL(cc0,cc1,roxt)
                    else: cc=atom.cc[:]
                    atom.cc=cc
                    atom.SetAtomParams(atom.elm)
                    #atom.SetDefaultColor()
                    #atom.SetDefaultAtmRad()
                    #atom.SetDefaultBondThick()
                    #atom.SetDefaultVdwRad()
        #        
        if len(lst) > 0:
            self.model.mol.DelAtoms(lst)
            del self.amiresseqlst[nres-1]
            self.resnmb -= 1
            self.model.DrawMol(True)
            self.model.Message(res+":"+str(nmb)+" residue is deleted.",0,"")
            self.DispSequence()
    
    def DihedralAngleText(self):
        text="Peptide dihedral angles, phi and psi\n"
        text=text+"right-hand alpha helix:    -57   -47\n"
        text=text+"parallel beta strand:      -119  113\n"
        text=text+"anti-parallel beta strand: -139  135\n"
        text=text+"right-hand 3(10) helix:     -49  -26\n"
        text=text+"right-hand pi helix:        -57  -70\n"
        text=text+"2.2(7) ribon:               -78   59\n"
        text=text+"left-hand alpha helix:       57   47\n"  
        return text
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
    
    def OpenZmtViewer(self):
        win=ZMatrixViewer_Frm(self.mdlwin,-1)
    
    def ExecTinker(self):
        pass
    
    def ExecGAMESS(self):
        pass

    def OpenRotCnfEditor(self):
        win=RotateBond_Frm(self.mdlwin,-1,self.model,[50,150])
    
    def OpenZmtCnfEditor(self):
        pass
    
        
    def XXOpenNotePad(self,filename):
        if not os.path.exists(filename):
            lib.MessageBoxOK("File not found. file= "+filename,"")
            return

        os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+" "+filename])     
    
    def SaveFile(self,savefile):
        if not os.path.exists(savefile):
            lib.MessageBoxOK("File not found. file= "+savefile,"")
            return 
        base,ext=os.path.splitext(savefile)
        
        filename=""; wildcard=savefile+'|*'+ext
        dlg = wx.FileDialog(self, "Save as...", os.getcwd(),
                            style=wx.SAVE, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath()
        dlg.Destroy()        
        if len(filename) < 0: return
        #
        #shutil.copyfile(savefile,filename)

    def ReadSequenceFile(self,filename):
        amiresseqlst=[]
        f=open(filename,"r")
        f.readline() # skip the first comment line
        for s in f.readlines():
            s=s.strip(); item=s.split()
            if len(item) <= 0: break
            print 'item[0]',item[0]
            if item[0][0:1] == "#": continue
            nam=item[0]; nmb=int(item[1])
            phi=float(item[2]); psi=float(item[3]); omg=float(item[4])
            chi1=float(item[5]); chi2=float(item[6])
            chi3=float(item[7]); chi4=float(item[8])
            chiral=item[9]
            amiresseqlst.append([nam,nmb,phi,psi,omg,chi1,chi2,chi3,chi4,
                                 chiral])
        f.close()
        
        return amiresseqlst
    
    def WriteSequenceFile(self,filename):
        if len(self.amiresseqlst) <= 0:
            lib.MessageBoxOK("No polypeptide data.","")
            return            
        f=open(filename,"w")    
        s='# Created by fu. DateTime='+lib.DateTimeText()+'\n'
        f.write(s)
        for nam,nmb,phi,psi,omg,chi1,chi2,chi3,chi4,chiral in \
                                                            self.amiresseqlst:
            s=nam+" "+str(nmb)+" "+str(phi)+" "+str(phi)+" "+str(omg)+" "
            s=s+str(chi1)+" "+str(chi2)+" "+str(chi3)+" "+str(chi4)+" "+chiral
            f.write(s+"\n")
        f.write("\n")
        f.close()

    def MenuItems(self):
        menubar=wx.MenuBar()
        # Menu items
        submenu=wx.Menu()
        submenu.Append(-1,"Open sequence file","Read sequence file")
        submenu.Append(-1,"Merge sequence file",
                       "merge residues in sequence file")
        submenu.AppendSeparator()
        submenu.Append(-1,"Save sequence file","Save sequence file")
        submenu.Append(-1,"Save sequence file as","Save sequence file as")
        submenu.AppendSeparator()
        submenu.Append(-1,"Quit","Close peptid epanel")     
        menubar.Append(submenu,"File")
        # Edit
        submenu=wx.Menu()
        submenu.Append(-1,"Sequence file","sequence file")
        menubar.Append(submenu,"Edit")
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        submenu.AppendSeparator()
        submenu.Append(-1,"Peptide dihedral angles","Help")
        submenu.AppendSeparator()
        # related functions
        #subsubmenu=wx.Menu()        
        #subsubmenu.Append(-1,"ZmtViewer",
        #                  "View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"RotCnfEditor",
        #                  "Open Rotate bond conformation editor")
        #subsubmenu.Append(-1,"ZmtCnfEditor",
        #                  "Open Z-matrix conformation editor")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,"Help")

        return menubar
    
    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        # File menu
        if item == "Open sequence file" or item == "Merge sequence file":
            filename=""
            wildcard='sequence(*.seq)|*.seq|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"r",True,"")
            if len(filename) > 0: 
                if item == "Merge sequence file": amires=self.amiresseqlst[:]
                self.DelAll()
                
                root,ext=os.path.splitext(filename)
                self.amiresseqlst=self.ReadSequenceFile(filename)
                self.seqfile=filename
                if item == "Merge sequence file":
                    self.amiresseqlst=amires+self.amiresseqlst
                self.RemunberResSeq()
                #self.resnmb=0
                self.MakePolypeptide()
                mess="Polypeptide is created according to sequence file= "
                mess=mess+self.seqfile
                self.model.Message(mess,0,"")
                self.DispSequence()
            return
            
        if item == "Save sequence file": #xxx.ffp (force field parameter
            filename=self.seqfile
            if len(filename) > 0:
                self.WriteSequenceFile(filename)
            else:
                lib.MessageBoxOK("No sequence file","")
                return
            return
        if item == "Save sequence file as":
            filename=""
            wildcard='sequence file(*.seq)|*.seq|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"w",True,"")
            if len(filename) > 0: 
                self.WriteSequenceFile(filename)
                self.seqfile=filename
            return
        if item == 'Quit':
            self.OnClose(1)
            return
        # Edit menu
        if item == "Sequence file":
            if os.path.exists(self.seqfile):
                #self.OpenNotePad(self.seqfile)
                lib.Editor(self.seqfile)
            else:
                mess="Sequence file: "+self.seqfile+" not found."
                lib.MessageBoxOK(mess,"")
                return                    
            return
        # Help menu        
        if item == "Peptide dihedral angles":
            helptext=self.DihedralAngleText()
            lib.MessageBoxOK(helptext,"")
            return
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        
        elif item == "Tutorial": self.Tutorial()
        elif item == "ZmtEditor": self.OpenZmtViewer()
        elif item == "RotCnfEditor": self.OpenRotCnfEditor()
        elif item == "ZmtCnfEditor": self.OpenZmtcnfEditor()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()
    
    def HelpMessage(self):
        mess='Needs residues pdb files in FUDATASET/FUdata/'
        lib.MessageBoxOK(mess,'Polypeptide.py')
            
    def OnSize(self,event):
        self.panel.Destroy()
        self.CreatePanel()
        
    def OnClose(self,event):
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        self.ctrlflag.Set('peptidewin',False)
        self.Destroy()

class TorsionEditor_Frm(wx.Frame):
    def __init__(self,parent,id,model,winpos,winlabel='Open Torsion Editor'):
        self.title='Torsion Editor'
        #pltfrm=lib.GetPlatform()
        #if pltfrm == 'WINDOWS': winsize=lib.WinSize([230,210]) #((260,240)) #400) #366) #(155,330) #(155,312)
        #else: winsize=(260,240)
        #if const.SYSTEM == const.MACOSX: winsize=(260,210)
        winsize=lib.WinSize([270,270])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|\
               wx.FRAME_FLOAT_ON_PARENT)      
 
        self.parent=parent
        self.winctrl=model.winctrl
        self.mdlwin=parent
        self.setctrl=model.setctrl
        self.draw=self.mdlwin.draw
        #xxself.ctrlflag=model.ctrlflag
        self.model=model                 
        self.winlabel=winlabel
        self.helpname='TorsionEditor'
        molnam=model.mol.name #wrkmolnam
        # Menu
        self.stepmenuid=wx.NewId()
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        #
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_MENU,self.OnMenu)#
        #
        self.SetTitle(self.title+' ['+molnam+']')
        self.size=self.GetClientSize()
        # initialize variables
        self.p1=-1; self.p2=-1; self.p3=-1; self.p4=-1
        self.zmpntlst=[] # list for keeping change history
        self.lengthvar=True; self.anglevar=False; self.torsionvar=False
        # angle is in degrees in this routie
        self.todeg=const.PysCon['todeg']
        # initial values of geometrical parameters in input window
        self.length=0.0; self.angle=0.0; self.torsion=0.0
        # initial values of increment values in input window
        self.lengthini=0.0; self.angleini=0.0; self.torsionini=0.0
        # mouse/non-mouse mode
        self.mousemode=True # mouse mode for moving selected atom(s)
        self.mousemovfactor=0.5 # mouse sensitivity
        #
        self.maxchangehis=self.setctrl.GetParam('max-undo-zmt') #'self.model.maxzmchangehis # maximum number of change history
        self.changehis=[] # change history.
        # create panel and set widget state
        self.CreateZmatrixPanel()
        self.SetWidgetState()
        
        self.Show()

    def CreateZmatrixPanel(self):
        # popup control panel
        xpos=0; ypos=0; xsize=self.size[0]; ysize=self.size[1]
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        # Menu
        yloc=5
        wx.StaticText(self.panel,-1,"Mode:",pos=(5,yloc),size=(35,18)) 
        self.rbtmus=wx.RadioButton(self.panel,wx.ID_ANY,'mouse',pos=(50,yloc), \
                                    style=wx.RB_GROUP)
        self.rbtnon=wx.RadioButton(self.panel,wx.ID_ANY,'non-mouse',
                                   pos=(120,yloc))
        self.rbtmus.Bind(wx.EVT_RADIOBUTTON,self.OnMode)
        self.rbtnon.Bind(wx.EVT_RADIOBUTTON,self.OnMode)
        if self.mousemode:
            self.rbtmus.SetValue(True)
        else:
            self.rbtnon.SetValue(True)
        wx.StaticLine(self.panel,pos=(-1,yloc+20),size=(xsize,2),
                      style=wx.LI_HORIZONTAL)
        yloc=yloc+30 #25
        # zmt points textctrl
        wx.StaticText(self.panel,-1,"p1:",pos=(5,yloc+2),size=(22,18)) 
        self.tclpnt1=wx.TextCtrl(self.panel,-1,'-1',pos=(28,yloc),size=(35,18))
        self.tclpnt1.Bind(wx.EVT_TEXT,self.OnP1Input)
        wx.StaticText(self.panel,-1,"p2:",pos=(67,yloc+2),size=(22,18)) 
        self.tclpnt2=wx.TextCtrl(self.panel,-1,'-1',pos=(90,yloc),size=(35,18))
        self.tclpnt2.Bind(wx.EVT_TEXT,self.OnP2Input)
        wx.StaticText(self.panel,-1,"p3:",pos=(130,yloc+2),size=(22,18)) 
        self.tclpnt3=wx.TextCtrl(self.panel,-1,'-1',pos=(152,yloc),
                                 size=(35,18))
        self.tclpnt3.Bind(wx.EVT_TEXT,self.OnP3Input)
        wx.StaticText(self.panel,-1,"p4:",pos=(192,yloc+2),size=(22,18)) 
        self.tclpnt4=wx.TextCtrl(self.panel,-1,'-1',pos=(215,yloc),
                                 size=(35,18))
        self.tclpnt4.Bind(wx.EVT_TEXT,self.OnP4Input)
        yloc=yloc+25      
        # reset selected atoms for move
        btnsel=wx.Button(self.panel,wx.ID_ANY,"Reset",pos=(20,yloc),
                         size=(50,20))        
        btnsel.Bind(wx.EVT_BUTTON,self.OnResetSel)
        wx.StaticText(self.panel,-1,"selected atoms for move",pos=(75,yloc),
                      size=(150,18)) 
        wx.StaticLine(self.panel,pos=(-1,yloc+25),size=(xsize,2),
                      style=wx.LI_HORIZONTAL)
        # zmt parameters, length, angle, torsion
        yloc=yloc+35
        # length input
        self.rbtlen=wx.RadioButton(self.panel,wx.ID_ANY,'length(p1-p2)',
                                   pos=(5,yloc),style=wx.RB_GROUP)
        self.rbtlen.Bind(wx.EVT_RADIOBUTTON,self.OnLength)
        self.tcllen=wx.TextCtrl(self.panel,-1,'0.0',pos=(150,yloc),
                                size=(55,18))
        #self.tcllen.Bind(wx.EVT_TEXT,self.OnLengthValue)
        self.tclleni=wx.TextCtrl(self.panel,-1,'0.01',pos=(210,yloc),
                                 size=(40,18))

        yloc=yloc+20
        # angle input
        self.rbtang=wx.RadioButton(self.panel,wx.ID_ANY,'angle(p1-p2-p3)',
                                   pos=(5,yloc))
        self.rbtang.Bind(wx.EVT_RADIOBUTTON,self.OnAngle)
        self.tclang=wx.TextCtrl(self.panel,-1,'0.0',pos=(150,yloc),
                                size=(55,18))
        #self.tclang.Bind(wx.EVT_TEXT,self.OnAngleValue)
        self.tclangi=wx.TextCtrl(self.panel,-1,'2.00',pos=(210,yloc),
                                 size=(40,18))

        yloc=yloc+20
        # torsion angle input
        self.rbttor=wx.RadioButton(self.panel,wx.ID_ANY,'torsion(p1-p2-p3-p4)',
                                   pos=(5,yloc))        
        self.rbttor.Bind(wx.EVT_RADIOBUTTON,self.OnTorsion)
        self.tcltor=wx.TextCtrl(self.panel,-1,'0.0',pos=(150,yloc),
                                size=(55,18))
        #self.tcltor.Bind(wx.EVT_TEXT,self.OnTorsionValue)
        self.tcltori=wx.TextCtrl(self.panel,-1,'2.00',pos=(210,yloc),
                                 size=(40,18))
        
        yloc=yloc+25
        # increment,decrementmreset button
        self.btnrst=wx.Button(self.panel,wx.ID_ANY,"reset",pos=(55,yloc),
                              size=(45,20))        
        self.btnrst.Bind(wx.EVT_BUTTON,self.OnResetParam)
        self.btninc=wx.Button(self.panel,wx.ID_ANY,"inc",pos=(120,yloc),
                              size=(35,20))        
        self.btninc.Bind(wx.EVT_BUTTON,self.OnIncParam)
        self.btndec=wx.Button(self.panel,wx.ID_ANY,"dec",pos=(170,yloc),
                              size=(35,20))        
        self.btndec.Bind(wx.EVT_BUTTON,self.OnDecParam)
        wx.StaticLine(self.panel,pos=(-1,yloc+25),size=(xsize,2),
                      style=wx.LI_HORIZONTAL)        
        yloc=yloc+32
        # OK, Cancel button       
        btnundo=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(30,yloc),
                          size=(45,20))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        btnapl=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(95,yloc),
                         size=(45,20))
        btnapl.Bind(wx.EVT_BUTTON,self.OnApply)
        btnok=wx.Button(self.panel,wx.ID_ANY,"OK",pos=(175,yloc),size=(45,20))
        btnok.Bind(wx.EVT_BUTTON,self.OnOK)
    
    def SetZMPoints(self,atm0,atm1,atm2,atm3):
        print 'SetZMTPoint',atm0,atm1,atm2,atm3
        self.p1=atm0
        self.p2=atm1
        self.p3=atm2
        self.p4=atm3
        self.tclpnt1.SetValue(str(self.p1+1))
        self.tclpnt2.SetValue(str(self.p2+1))
        self.tclpnt3.SetValue(str(self.p3+1))
        self.tclpnt4.SetValue(str(self.p4+1))
        #
        self.length=self.model.AtomDistance(self.p1,self.p2)
        self.angle=self.model.AtomAngle(self.p1,self.p2,self.p3)*self.todeg  
        self.torsion=self.model.TorsionAngle(self.p1,self.p2,self.p3,
                                             self.p4)*self.todeg
        # keep initial values for undo
        self.lengthini=self.length
        self.angleini=self.angle
        self.torsionini=self.torsion
        # 
        self.tcllen.SetValue(str(self.length))
        self.tclang.SetValue(str(self.angle))
        self.tcltor.SetValue(str(self.torsion))
        #
        self.ChangeZMPoints()
        
        self.UpdateHistry()

    def SetSelectAtomForMove(self):
        # set movable atoms be selected
        move,grplst=self.FindMoveAtomGroup()
        self.model.SetSelectAll(False)
        if not move:
            self.parent.Message('No movable atoms',0,'black')
        else:
            for i in grplst:
                self.model.SetSelectedAtom(i,True)
        
        self.model.DrawMol(True)

    def FindMoveAtomGroup(self):
        # make list of covalent bonded atom group including p1.
        move=True
        condat=[]
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            condat.append(atom.conect[:])
        #
        grpdic={}; grplst=[]
        conp1=condat[self.p1]
        for i in conp1:
            if i == self.p2: continue
            if grpdic.has_key(i): continue
            else: grpdic[i]=0                
        # if p1 is a terminal atom, search connected atoms to p2
        p1term=False
        if len(conp1) == 1: p1term=True
        if p1term:
            conp2=condat[self.p2]
            for i in conp2:
                if i == self.p1: continue
                if i == self.p3: continue
                if grpdic.has_key(i): continue
                else: grpdic[i]=1
        
        condat[self.p2]=[]
        #
        na=1
        while na > 0:
            grplst=grpdic.keys()
            na=0
            for i in grplst:
                for j in condat[i]:
                    if j == self.p1: continue
                    if j == self.p2: continue
                    if grpdic.has_key(j): continue
                    else:
                        grpdic[j]=1; na += 1
        if grpdic.has_key(self.p2): move=False
        if grpdic.has_key(self.p3): move=False
        if grpdic.has_key(self.p4): move=False
        grpdic[self.p1]=1
        grplst=grpdic.keys()
        grplst.sort()
        #
        return move,grplst
    
    def ChangeGeometry(self,dif):
        print 'zamtrix dif',dif
        if not self.mousemode: return
        if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
        if abs(dif[0]) < 0.01: return
        mov=dif[0]*self.draw.ratio*self.mousemovfactor
        atm1=self.model.mol.atm[self.p1]
        atm2=self.model.mol.atm[self.p2]
        atm3=self.model.mol.atm[self.p3]
        cc1=atm1.cc; cc2=atm2.cc; cc3=atm3.cc
        if self.lengthvar:
            leng0=self.model.AtomDistance(self.p1,self.p2)
            leng=leng0+mov
            self.ChangeLength(leng0,mov)
            self.length=self.model.AtomDistance(self.p1,self.p2)
            self.tcllen.SetValue(str(self.length))
        elif self.anglevar:
            ax=numpy.cross(numpy.subtract(cc3,cc2),numpy.subtract(cc1,cc2))
            cnt=cc2
            self.ChangeAngle(ax,cnt,mov)
            self.angle=self.model.AtomAngle(self.p1,self.p2,self.p3)*self.todeg  
            self.tclang.SetValue(str(self.angle))
        elif self.torsionvar:
            ax=numpy.subtract(cc3,cc2)
            cnt=cc2
            self.ChangeAngle(ax,cnt,mov)
            self.torsion=self.model.TorsionAngle(self.p1,self.p2,self.p3,
                                                 self.p4)*self.todeg
            self.tcltor.SetValue(str(self.torsion))

        self.model.DrawMol(True)    
               
    def ChangeLength(self,leng0,dl):
        # change length p1-p2
        if self.p1 < 0 or self.p2 < 0: return
        atm1=self.model.mol.atm[self.p1]
        atm2=self.model.mol.atm[self.p2]
        dx=(atm1.cc[0]-atm2.cc[0])/leng0
        dy=(atm1.cc[1]-atm2.cc[1])/leng0
        dz=(atm1.cc[2]-atm2.cc[2])/leng0
        leng=leng0+dl
        if leng < 0.5: return
        dx *= dl; dy *= dl; dz *= dl
        for atom in self.model.mol.atm:
            if not atom.select: continue
            atom.cc[0] += dx
            atom.cc[1] += dy
            atom.cc[2] += dz

    def ChangeAngle(self,ax,cnt,da):
        # for angle (p1-p2-p3) and torsion (p1-p2-p3-p4) change
        if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
        u=lib.RotMatAxis(ax,da)
        coord=[]
        for atom in self.model.mol.atm:
            if not atom.select: continue
            coord.append(copy.deepcopy(atom.cc))
        xyz=lib.RotMol(u,cnt,coord)
        k=-1
        for i in xrange(len(self.model.mol.atm)):

            if not self.model.mol.atm[i].select: continue
            k += 1
            self.model.mol.atm[i].cc[0]=xyz[k][0]
            self.model.mol.atm[i].cc[1]=xyz[k][1]
            self.model.mol.atm[i].cc[2]=xyz[k][2]

    def OnUndo(self,event):
        nhis=len(self.changehis)
        if nhis <= 0:
            self.parent.Message('No change history',0,'black')
            return
        elif nhis == 1:
            self.parent.Message('Undo buffer is empty.',0,'black')
        #
        dat=self.changehis[nhis-1]
        self.model.SetSelectAll(False)

        for i in xrange(len(dat)):
            atmseq=dat[i][0]
            atmcc=dat[i][1]
            self.model.mol.atm[atmseq].cc=copy.deepcopy(atmcc)
            self.model.SetSelectedAtom(atmseq,True)
        # set current values in textctrl
        self.length=self.model.AtomDistance(self.p1,self.p2)
        self.tcllen.SetValue(str(self.length))
        self.angle=self.model.AtomAngle(self.p1,self.p2,self.p3)*self.todeg  
        self.tclang.SetValue(str(self.angle))
        self.torsion=self.model.TorsionAngle(self.p1,self.p2,self.p3,
                                             self.p4)*self.todeg
        self.tcltor.SetValue(str(self.torsion))
        
        if nhis > 1: del self.changehis[nhis-1]
        # draw molecue
        self.model.DrawMol(True)
        
    def OnApply(self,event):
        atm1=self.model.mol.atm[self.p1]
        atm2=self.model.mol.atm[self.p2]
        atm3=self.model.mol.atm[self.p3]
        cc1=atm1.cc; cc2=atm2.cc; cc3=atm3.cc

        if not self.mousemode:
            if self.lengthvar:
                leng=float(self.tcllen.GetValue())
                leng0=self.model.AtomDistance(self.p1,self.p2)
                dl=leng-leng0
                self.ChangeLength(leng0,dl) 
                self.length=self.model.AtomDistance(self.p1,self.p2)
                self.tcllen.SetValue(str(self.length))
                             
            elif self.anglevar:
                ax=numpy.cross(numpy.subtract(cc3,cc2),numpy.subtract(cc1,cc2))
                ang=float(self.tclang.GetValue())  
                ang0=self.model.AtomAngle(self.p1,self.p2,self.p3)  
                cnt=cc2
                self.angle=ang
                ang /= self.todeg
                da=ang-ang0
                self.ChangeAngle(ax,cnt,da)
                self.angle=self.model.AtomAngle(self.p1,self.p2,
                                                self.p3)*self.todeg  
                self.tclang.SetValue(str(self.angle))

            elif self.torsionvar:
                tors=float(self.tcltor.GetValue())            
                self.torsion=tors
                tors0=self.model.TorsionAngle(self.p1,self.p2,self.p3,self.p4)
                tors /= self.todeg
                da=tors-tors0
                ax=numpy.subtract(cc2,cc3)
                cnt=cc2
                self.ChangeAngle(ax,cnt,da)
                self.torsion=self.model.TorsionAngle(self.p1,self.p2,
                                                    self.p3,self.p4)*self.todeg
                self.tcltor.SetValue(str(self.torsion))
            
            self.model.DrawMol(True)

        self.UpdateHistry()

    def OnOK(self,event):
        self.OnApply(0)
        self.OnClose(0)

    def ResetLength(self):
        self.length=self.lengthini
        self.tcllen.SetValue(str(self.length))
        
    def ResetAngle(self):
        self.angle=self.angleini
        self.tclang.SetValue(str(self.angle))
        
    def ResetTorsion(self):
        self.torsion=self.torsionini
        self.tcltor.SetValue(str(self.torsion))
        
    def OnResetParam(self,event):
        if self.lengthvar: # length
            self.ResetLength()
        if self.anglevar: # angle
            self.ResetAngle()
        if self.torsionvar: # trotion
            self.ResetTorsion()

    def OnIncParam(self,event):
        if self.lengthvar:
            val=self.tclleni.GetValue()
            self.length=float(self.tcllen.GetValue())
        if self.anglevar:
            val=self.tclangi.GetValue()
            self.angle=float(self.tclang.GetValue())
        if self.torsionvar:
            val=self.tcltori.GetValue()
            self.torsion=float(self.tcltor.GetValue())
        if not val.replace('.','').isdigit():
            mess='Wrong input. Should be float.'
            self.parent.Message(mess,0,'black')
            return
        inc=float(val)
        if self.lengthvar: # length
            self.length += inc
            self.tcllen.SetValue(str(self.length))
        if self.anglevar: # angle
            self.angle += inc
            self.tclang.SetValue(str(self.angle))
        if self.torsionvar: # torsion
            self.torsion += inc
            self.tcltor.SetValue(str(self.torsion))

    def OnDecParam(self,event):
        if self.lengthvar:
            val=self.tclleni.GetValue()
            self.length=float(self.tcllen.GetValue())
        if self.anglevar:
            val=self.tclangi.GetValue()
            self.angle=float(self.tclang.GetValue())
        if self.torsionvar:
            val=self.tcltori.GetValue()
            self.torsion=float(self.tcltor.GetValue())
        if not val.replace('.','').isdigit():
            mess='Wrong input. Should be float.'
            self.parent.Message(mess,0,'black')
            return
        inc=float(val)
        if self.lengthvar: # length
            self.length -= inc
            if self.length <= 0.5: self.length=0.5
            self.tcllen.SetValue(str(self.length))
        if self.anglevar: # angle
            self.angle -= inc
            if self.angle <= 0.0: self.angle=0.01
            self.tclang.SetValue(str(self.angle))
        if self.torsionvar: # torsion
            self.torsion -= inc
            self.tcltor.SetValue(str(self.torsion))
               
    def OnLength(self,event):
        self.lengthvar=True
        self.anglevar=False; self.tclang.Disable()
        self.torsionvar=False; self.tcltor.Disable()
        if not self.mousemode:
            self.tcllen.Enable()
            self.tclleni.Enable()
            self.btnrst.Enable()
            self.btninc.Enable()
            self.btndec.Enable()
             
    def OnAngle(self,event):
        self.lengthvar=False; self.tcllen.Disable()
        self.anglevar=True
        self.torsionvar=False; self.tcltor.Disable()
        if not self.mousemode:
            self.tclang.Enable()
            self.tclangi.Enable()
            self.btnrst.Enable()
            self.btninc.Enable()
            self.btndec.Enable()
    
    def OnTorsion(self,event):
        self.lengthvar=False; self.tcllen.Disable()
        self.anglevar=False; self.tclang.Disable()
        self.torsionvar=True
        if not self.mousemode:
            self.tcltor.Enable()
            self.tcltori.Enable()
            self.btnrst.Enable()
            self.btninc.Enable()
            self.btndec.Enable()
    
    def OnGetParam(self,event):
        if self.lengthvar: val=self.tcllen.GetValue()
        if self.anglevar: val=self.tclang.GetValue()
        if self.torsionvar: val=self.tcltor.GetValue()
        if not val.replace('.','').isdigit():
            print 'Wrong input. Should be float.'
            return
        val=float(val)
        if self.lengthvar: # length
            self.length=val
            if self.length < 0:
                self.parent.Message("Wrong input, negative length.",0,"black")
                return
            self.tcllen.SetValue(str(self.length))
        if self.anglevar: # angle
            self.angle=val
            if self.angle < 0:
                self.parent.Message("Wrong input, negative angle.",0,"black")
                return
            self.tclang.SetValue(str(self.angle))
        if self.torsionvar: # torsion
            self.trotion=val
            self.tcltor.SetValue(str(self.torsion))
            
    def OnResetSel(self,event):
        self.SetSelectAtomForMove()
    
    def OnP1Input(self,event):
        try:
            self.p1=int(self.tclpnt1.GetValue())-1
            if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
            self.ChangeZMPoints()
        except: pass
    
    def OnP2Input(self,event):
        try:
            self.p2=int(self.tclpnt2.GetValue())-1
            if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
            self.ChangeZMPoints()
        except: pass
        
    def OnP3Input(self,event):
        try:
            self.p3=int(self.tclpnt3.GetValue())-1
            if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
            self.ChangeZMPoints()
        except: pass
             
    def OnP4Input(self,event):
        try:
            self.p4=int(self.tclpnt4.GetValue())-1        
            if self.p1 < 0 or self.p2 < 0 or self.p3 < 0 or self.p4 < 0: return
            self.ChangeZMPoints()
        except: pass

    def ChangeZMPoints(self):
        #self.model.mol.SetExtraBond(self.zmpntlst,False)
        #self.zmpntlst=[[self.p1,self.p2],[self.p2,self.p3],[self.p3,self.p4]]
        #self.model.mol.SetExtraBond(self.zmpntlst,True)
        self.model.DrawAxisArrow(False,[])
        cc1=self.model.mol.atm[self.p1].cc
        cc2=self.model.mol.atm[self.p2].cc
        cc3=self.model.mol.atm[self.p3].cc
        cc4=self.model.mol.atm[self.p4].cc
        zmtpnts=[[cc1,cc2],[cc2,cc3],[cc3,cc4]]
        self.model.DrawAxisArrow(True,zmtpnts)
        # set select atoms for move
        self.SetSelectAtomForMove()
        # add current coordinates of selected atoms to change history
        self.UpdateHistry()
        # draw molecule
        self.model.DrawMol(True)
        
    def UpdateHistry(self):
        current=[]
        #atm.append([self.p1,self.p2,self.p3,self.p4])
        nsel,lst=self.model.ListSelectedAtom()
        if nsel <= 0: return
        #
        for atom in self.model.mol.atm:
            if atom.select:
                tmp=[]
                tmp.append(atom.seqnmb)
                tmp.append(copy.deepcopy(atom.cc))
                current.append(tmp)
        #current.append(atm)    
        nhis=len(self.changehis)
        if nhis > self.maxchangehis: del self.changehis[1]
        self.changehis.append(current)

    def OnMode(self,event):
        self.mousemode=self.rbtmus.GetValue()
        self.SetWidgetState()
        
    def SetWidgetState(self):
        if self.mousemode:
            # textctrl
            self.tcllen.Disable()
            self.tclleni.Disable()
            self.tclang.Disable()
            self.tclangi.Disable()
            self.tcltor.Disable()
            self.tcltori.Disable()
            # button
            self.btnrst.Disable()
            self.btninc.Disable()
            self.btndec.Disable()
        else:
            # textctrl
            self.tcllen.Enable()
            self.tclleni.Enable()
            self.tclang.Enable()
            self.tclangi.Enable()
            self.tcltor.Enable()
            self.tcltori.Enable()
            # button
            self.btnrst.Enable()
            self.btninc.Enable()
            self.btndec.Enable()
    
    def DelArrows(self):    
        self.model.mousectrl.SetRotationAxisPnts(False,[]) 
        self.model.DrawAxisArrow(False,[])
        self.model.DrawMol(True)

    def OnPaint(self,event):
        event.Skip()

    def OnClose(self,event):
        self.model.DrawAxisArrow(False,[])
        self.winctrl.Close(self.winlabel) #'ZmatWin'
        #try:
        #    self.model.mol.SetExtraBond(self.zmpntlst,False) 
        #    self.model.DrawMol(True)
        #except: pass
        self.Destroy()

    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
    
    def MenuItems(self):
        helpname=self.helpname
        
        menubar=wx.MenuBar()
        #
        submenu=wx.Menu()
        submenu.Append(-1,'Del arrows','Option')
        menubar.Append(submenu,'Option')
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Open document.')
        if self.model.helpctrl.IsTutorial(helpname):
            submenu.Append(-1,'Tutorial','Open tutorial panel.')
        #
        menubar.Append(submenu,'Help')
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        if item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == 'Del arrows': self.DelArrows()
    
class ZMatrixEditor_Frm(wx.Frame):
    def __init__(self,parent,id,winpos=[],winsize=[],winlabel='ZmatrixEditor'): #winsize=[510,350]): #winsize=[300,400]):
        """ 
        
        :param int mode: 0 for input and 1 for manual mode
        :param lst gmsdoc: gamess inputdoc data. 
        :seealso: ReadGMSInputDocText() static method for gmsdoc
        """
        #mdlwin=parent
        self.title='Z-Matrix Editor'
        self.winlabel=winlabel # = helpname
        winpos=winpos
        if len(winpos) <= 0:
            #[x,y]=mdlwin.GetPosition()
            #[w,h]=mdlwin.GetSize()
            #winpos=[x+w,y+20]
            winpos=lib.WinPos(parent.mdlwin)
        if len(winsize) <= 0: winsize=lib.WinSize([580,350])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
                          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|\
                          wx.RESIZE_BORDER) #|wx.FRAME_FLOAT_ON_PARENT)        #
        #
        self.model=parent
        self.mdlwin=self.model.mdlwin
        ###self.curmol,self.mol=self.model.molctrl.GetCurrentMol()
        self.winsize=winsize
        # set title
        try: self.SetTitle(self.title+' ['+self.model.mol.name+']')
        except: self.SetTitle(self.title+' [No name]')
        # attach icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass        
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #self.Bind(wx.EVT_MENU_OPEN,self.OnMenuOpen)
        #self.Bind(wx.EVT_MENU_HIGHLIGHT,self.OnMenuHelp)
        #
        try: self.model.winctrl.SetWin(self.winlabel,self)
        except: pass
        # help icon
        #self.helpbmp=self.model.setctrl.GetIconBmp('help')
        self.deselectbmp=self.model.setctrl.GetIconBmp('deselect')
        self.command1bmp=self.model.setctrl.GetIconBmp('command1')
        self.command2bmp=self.model.setctrl.GetIconBmp('command2')
        self.executebmp=self.model.setctrl.GetIconBmp('execute')
        self.get1bmp=self.model.setctrl.GetIconBmp('get1')
        #self.compubmp=self.model.setctrl.GetIconBmp('compute')
        self.listbmp=self.model.setctrl.GetIconBmp('list')
        #
        self.SetBackgroundColour('light gray')
        # Undo atom by atom
        self.PopupMenuItems()
        self.maxundo=5
        self.textcolor=wx.BLACK
        self.changecolor=(165, 40, 40) # wx.BLACK, wx.RED
        self.freezecolor=wx.BLACK
        self.activecolor=(255,128,190) #'MAGENTA' #wx.CYAN
        self.dualcolor=(0,128,128) #(0,255,128) #'CYAN'
        self.inputcolor=(255,0,0)
        #
        self.vsbl=['R','A','T'] # head charater of variables 
        self.prmform=['%8.3f','%8.2f','%8.2f']
        self.nullkeynam=['0:0','0:1','0:2','1:1','1:2','2:2']
        
        self.pntmapdic={}
        self.addseqnmb=False
        self.symboliczmt=False
        self.synconebyone=False
        self.dispitem='all'
        self.disptext=''
        self.trymol=None # mol object
        self.trymolgrpnam=''
        self.savmol=None
        self.savatmcc=[]
        self.selectedrow=-1; self.selectedcol=-1
        #self.changedic={}
        self.ClearParams()
        #
        self.MakeZMData()
        self.displst=range(len(self.zelm))
        #
        self.CreatePanel()
        self.CreateGrid()
        self.SetDataToGridTable()
        #
        self.Show()
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        #
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
    
        self.Show()
        
    def ClearParams(self,all=True):
        self.changeprmdic={}
        self.changepntdic={}
        self.changeatmnam={}
        self.changeresdat={}
        self.changeelm={}
        self.inputdic={}
        self.zvardic={}; self.acrivedic={}; self.zmtpnt=[]
        self.activedic={}
        if all:
            self.tryzmt=False
            self.zelm=[]; self.zpnt=[]; self.zprm=[]
            self.atmnam=[]; self.resdat=[]
      
    def OnNotify(self,event):
        if event.jobid != 'ZMatrixEditor': return
        try: item=event.message
        except: return
        #
        if item == 'SwitchMol': # method name
            self.model.ConsoleMessage('mess from SwitchMol')
            self.OnReset(1)
        elif item == 'ReadFiles': self.OnReset(1)      
        elif item == 'One-by-One': # winlabel
            self.model.ConsoleMessage('mess from One-by-One')
            if self.synconebyone: 
                self.displst,needinput=self.Extract('show atoms','')
                self.Resize()

    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=[0,0],size=[w,h])
        self.panel.SetBackgroundColour('light gray')
        hbtn=25; hcb=const.HCBOX
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        btnrset.SetLabel('Reset')
        #btnrset.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        #
        yloc=5
        txtext=wx.StaticText(self.panel,-1,'Extract:',pos=(10,yloc+2),
                             size=(50,20)) 
        txtext.SetToolTipString('Extract atoms by item and its value')
        self.cmbsel=wx.ComboBox(self.panel,-1,'',choices=self.extractmenu, \
                           pos=(60,yloc), size=(120,hcb),style=wx.CB_READONLY)
        self.cmbsel.Bind(wx.EVT_COMBOBOX,self.OnExtract) #ControlPanMdl)
        self.cmbsel.SetValue(self.dispitem)
        mess='Choose item. Some items require value(input it in text '
        mess=mess+'window and hit "ENTER")'
        self.cmbsel.SetToolTipString(mess)
        wx.StaticText(self.panel,-1,'=',pos=(185,yloc+2),size=(15,20)) 
        self.tclsel=wx.TextCtrl(self.panel,-1,'',pos=(205,yloc),size=(300,20),
                           style=wx.TE_PROCESS_ENTER)
        mess='Input value for choosen item and hit "ENTER"'      
        self.tclsel.SetToolTipString(mess)
        self.tclsel.Bind(wx.EVT_TEXT_ENTER,self.OnExtract)
        self.tclsel.SetValue(self.disptext)
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        label='atmnam'+4*' '; label=label+'resdat'+5*' '
        label=label+' seq.#'+4*' '
        label=label+'elm'+5*' '; label=label+'p1'+7*' '
        label=label+'length'+8*' '
        label=label+'p2'+7*' '; label=label+'angle'+9*' '
        label=label+'p3'+7*' '
        label=label+'torsion'
        self.stlabl=wx.StaticText(self.panel,-1,label,pos=(10,yloc),
                                  size=(w-40,20)) 
        self.stlabl.Bind(wx.EVT_RIGHT_DOWN,self.OnColCommand)
        self.stlabl.Bind(wx.EVT_LEFT_DOWN,self.OnColCommand)
        #
        btnclrsel=wx.BitmapButton(self.panel,-1,bitmap=self.deselectbmp,
                                  pos=(w-32,yloc-5),size=(hbtn,hbtn))
        btnclrsel.Bind(wx.EVT_BUTTON,self.OnClearSelection)
        btnclrsel.SetToolTipString('Reset cell selection')
        btnclrsel.SetLabel('DeselectCell')
        btnclrsel.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        yloc += 20   
        pansize=[w-20,h-yloc-45]
        self.grid=wx.grid.Grid(self.panel,-1,pos=[10,yloc],size=pansize)
        self.grid.EnableGridLines(True)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelSize(0)
        try: self.grid.ShowScrollbars(wx.SHOW_SB_DEFAULT,wx.SHOW_SB_NEVER)
        except: pass
        
        self.grid.DisableDragCell()
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnCellLeftClick)
        #self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,self.OnGridRightClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE,self.OnGridCellChange)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,self.OnCellRightClick)
        self.grid.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)  
        # cmd buttons
        yloc=h-35; ylocs=yloc
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        btncmd1=wx.BitmapButton(self.panel,-1,bitmap=self.command1bmp,
                                pos=(20,yloc-2),size=(40,hbtn))
        btncmd1.Bind(wx.EVT_BUTTON,self.OnCommand) #ControlPanMdl)
        btncmd1.SetToolTipString('Commands for ZM table')
        btncmd1.SetLabel('Command1')
        btncmd1.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        btnlst=wx.BitmapButton(self.panel,-1,bitmap=self.listbmp,
                               pos=(70,yloc-2),size=(hbtn,hbtn))
        btnlst.Bind(wx.EVT_BUTTON,self.OnListVariable) #ControlPanMdl)
        btnlst.SetToolTipString('List variable names')
        btnlst.SetLabel('list')
        btnlst.Bind(wx.EVT_RIGHT_DOWN,self.OnListVariable)

        wx.StaticLine(self.panel,pos=(110,ylocs+8),size=(4,35-12),
                      style=wx.LI_VERTICAL)

        btncmd2=wx.BitmapButton(self.panel,-1,bitmap=self.command2bmp,
                                pos=(130,yloc-2),size=(40,hbtn))
        btncmd2.Bind(wx.EVT_BUTTON,self.OnCommand) #ControlPanMdl)
        btncmd2.SetLabel('Command2')
        btncmd2.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        #                   style=wx.TE_PROCESS_ENTER)        
        btncmd2.SetToolTipString('Commands for mdlwin')
        btnget=wx.BitmapButton(self.panel,-1,bitmap=self.get1bmp,
                               pos=(180,yloc-2),size=(hbtn,hbtn))
        btnget.Bind(wx.EVT_BUTTON,self.OnGetSelectedAtom) #ControlPanMdl)
        btnget.SetLabel('get')
        btnget.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        mess='Get selected atoms in mdlwin and set select in the table'
        btnget.SetToolTipString(mess)
        xloc=320
        wx.StaticLine(self.panel,pos=(xloc,ylocs),size=(2,35),
                      style=wx.LI_VERTICAL)    
        xloc += 10
        self.btnundo=wx.Button(self.panel,-1,"Undo",pos=(xloc+20,yloc),
                               size=(50,20))
        self.btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        self.btnundo.SetToolTipString('Undo "Apply"')
        self.btnaply=wx.Button(self.panel,-1,"Apply",pos=(xloc+90,yloc),
                               size=(50,20))
        self.btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        self.btnaply.SetToolTipString('Apply current coordinates')
        self.EnableApply()
        #wx.StaticLine(self.panel,pos=(xloc+140,ylocs),size=(2,35),style=wx.LI_VERTICAL)    
        self.btntry=wx.ToggleButton(self.panel,-1,"Try",pos=(xloc+160,yloc),
                                    size=(50,20))
        self.btntry.Bind(wx.EVT_TOGGLEBUTTON,self.OnTry)
        mess='Try to apply changes(toggle). "Apply" button is enabled after '
        mess=mess+'"Try"'
        self.btntry.SetToolTipString(mess)
        #self.btntry.Bind(wx.EVT_RIGHT_DOWN,self.OnEnableTry)
    
    def OnKeyDown(self,event):
        # ctrl-c: copy
        colprp={0:self.changeatmnam}
        row=self.selectedrow; col=self.selectedcol
        if event.ControlDown() and event.GetKeyCode() == 67:
            text=self.grid.GetCellValue(row,col)
            lib.CopyTextToClipboard(text)
        # ctrl-v: paste
        if event.ControlDown() and event.GetKeyCode() == 86:
            text=lib.PasteTextFromClipboard()
            sellst=self.ListSelectedRow()
            if len(sellst) <= 0: sellst=[row]
            for row in sellst:
                self.grid.SetCellValue(row,col,text)
                self.CellValueChange(row,col,text)
            self.SetCellColor(sellst,[col])
        event.Skip()
        
    def OnUndo(self,event):
        self.SaveZMTData(False)
        self.SaveChange(False)
        
        self.model.RecoverMol(False)
        self.RenameGroup('base')
        #self.model.molctrl.SetMol(molidx,self.model.mol) 
        self.ResetChange()
        self.SetDataToGridTable()
 
        self.model.FitToScreen(True,True)
        
        self.tryzmt=False
        self.btntry.SetValue(self.tryzmt)
        self.btntry.Enable()
        
        self.btnaply.Disable()
        self.btnundo.Disable()

    def OnApply(self,event):
        if not self.tryzmt:
            mess='Please hit "Try" button before "Apply"' 
            lib.MessageBoxOK(mess,'ZMatrixViewer(OnApply)')
            return
        dellst=[]
        for atom in self.model.mol.atm:
            if atom.grpnam != self.trymolgrpnam: dellst.append(atom.seqnmb)
        self.model.mol.DelAtoms(dellst)
        self.model.SetSelectAll(True)
        self.model.AddBondUseBondLength(False)
        self.model.SetSelectAll(False)
        
        self.model.DrawLabelAtm(False,0)
        self.model.DrawMol(True)

        self.tryzmt=False
        self.btntry.SetValue(self.tryzmt)
        self.btntry.Disable()
        self.btnaply.Disable()
        self.btnundo.Enable()
        
        self.ResetChange()
        ##self.mol=self.model.mol
        """ check 30Nov2015"""
        self.RenameGroup('base')
        """ """
        """
        self.model.mol.zmtpnt=self.zmtpnt
        self.model.mol.zactivedic=self.zactivedic
        self.model.mol.zvardic=self.zvardic
        """
        self.zmtpnt=self.zpnt
        self.zelm,self.zpnt,self.zprm=lib.CCToZM(self.model.mol,
                                                 zmtpnt=self.zmtpnt)
        self.SetDataToGridTable()
    
    def RenameGroup(self,grpnam):
        for i in range(len(self.model.mol.atm)):
            self.model.mol.atm[i].grpnam=grpnam
        
    def SaveZMTData(self,on):
        if on:
            self.zelmsav=copy.deepcopy(self.zelm)
            self.zpntsav=copy.deepcopy(self.zpnt)
            self.zprmsav=copy.deepcopy(self.zprm)
            self.atmnamsav=copy.deepcopy(self.atmnam)
            self.resdatsav=copy.deepcopy(self.resdat)
        else:
            self.zelm=copy.deepcopy(self.zelmsav)
            self.zpnt=copy.deepcopy(self.zpntsav)
            self.zprm=copy.deepcopy(self.zprmsav)
            self.atmnam=copy.deepcopy(self.atmnamsav)
            self.resdat=copy.deepcopy(self.resdatsav)
        
    def ResetChange(self):
        self.changeprmdic={};  self.changepntdic={}; self.changeatmnam={}
        self.changeresdat={}; self.changeelm={}
    
    def SaveChange(self,on):
        if on:
            self.changeprmdicsav=copy.deepcopy(self.changeprmdic)
            self.changepntdicsav=copy.deepcopy(self.changepntdic)
            self.changeatmnamsav=copy.deepcopy(self.changeatmnam)
            self.changeresdatsav=copy.deepcopy(self.changeresdat)
            self.changeelmsav=copy.deepcopy(self.changeelm)
        else:
            self.changeprmdic=copy.deepcopy(self.changeprmdicsav)
            self.changepntdic=copy.deepcopy(self.changepntdicsav)
            self.changeatmnam=copy.deepcopy(self.changeatmnamsav)
            self.changeresdat=copy.deepcopy(self.changeresdatsav)
            self.changeelm=copy.deepcopy(self.changeelmsav)
            
    def EnableApply(self):
        if self.tryzmt:
            self.btnundo.Enable(); self.btnaply.Enable()
        else:
            self.btnundo.Disable(); self.btnaply.Disable()
    
    def OnListVariable(self,event):
        form=['%8.3f','%8.2f','%8.2f']
        conlst=[]; varlst=[]
        textcon='Constants:\n'; textvar='Variables:\n'
        for keynam,varnam in self.zvardic.iteritems():
            iatm,iprm=self.UnPackVarNam(varnam)
            #iatm -= 1
            try: value=self.zprm[iatm][iprm]
            except: continue
            value=varnam+'='+(form[iprm] % value)
            if self.activedic.has_key(keynam):
                if not value in varlst: varlst.append(value)
            else:
                if not value in conlst: conlst.append(value)
        if len(varlst) > 0: 
            varlst.sort()
            for text in varlst: textvar=textvar+text+'\n'
        if len(conlst) > 0:
            conlst.sort()
            for text in conlst: textcon=textcon+text+'\n'
        text=textvar+'\n'+textcon+'\n'
        #
        self.viewprm=subwin.TextViewer_Frm(self,winpos=[-1,-1],
                             winsize=[150,400],title='ZM variables',text=text)
         
    def GetZMParamsInTable(self):
        pntcol=[4,6,8]; prmcol=[5,7,9]
        err=False
        nrow=self.grid.GetNumberRows()
        zelm=[]; zpnt=[]; self.sprm=[]; activedic={}; atmnam=[]; resdat=[]
        for i in range(nrow):
            if i < 3: mprm=i
            else: mprm=3
            # atmnam
            atm=self.grid.GetCellValue(i,0)
            #if atm == '': break
            atm=lib.AtmNamFromString(atm)
            # resdat
            res=self.grid.GetCellValue(i,1)
            # seq #
            seqnmb=self.grid.GetCellValue(i,2)
            # elm
            elm=self.grid.GetCellValue(i,3)
            elm=lib.ElementNameFromString(elm)
            # p1,p2,p3
            pnt=[-1,-1,-1]; prm=['','','']
            if mprm > 0:
                for j in range(mprm):
                    pnt[j]=self.grid.GetCellValue(i,pntcol[j])
                    try: pnt[j]=int(pnt[j])-1
                    except:
                        err=True
                        mess='Wrong point data. row='+str(i+1)+', col='
                        mess=mess+str(j+1)
                        self.model.ConsoleMessage(mess)
                # zparam
                for j in range(mprm):
                    prm[j]=self.grid.GetCellValue(i,prmcol[j])
                # set active
                for j in range(mprm):
                    iprm=prmcol[j]
                    keynam=str(i)+':'+str(j)   
                    if self.grid.GetCellTextColour(i,iprm) == self.activecolor: 
                        activedic[keynam]=True
                    #else: activedic[keynam]=False
            #
            atmnam.append(atm); resdat.append(res); zelm.append(elm)
            zpnt.append(pnt); self.sprm.append(prm)
        
        err,zprm=self.SetZPRMValue(self.sprm)
        ###for varnam, vallst in zmtdic.iteritems():
        ###    if activedic.has_key(varnam) and activedic[varnam]: zmtdic[varnam][1]=True
        # 
        if err: return err
        #
        self.zelm=zelm
        self.atmnam=atmnam
        self.resdat=resdat
        self.zpnt=zpnt
        self.zprm=zprm
        self.activedic=activedic
        
        return err
            
    def SetZPRMValue(self,sprm):
        err=False
        #zprm=len(sprm)*[['','','']]; zvardic={}
        zprm=[]
        
        for i in range(len(sprm)):
            prm=['','','']
            if i == 0:
                zprm.append(prm); continue
            if i < 3: mprm=i
            else: mprm=3 
            for j in range(mprm):
                try: prm[j]=float(sprm[i][j])
                except:
                    value=self.GetVarNamValue(sprm[i][j])
                    if value == None:
                        err=True
                        mess='Wrong variable name. varnam='+sprm[i][j]
                        lib.MessageBoxOK(mess,'ZMatrixViewer(SetZPRMValue)')
                        return err,[] #,{}
                    #zprm[i][j]=zprm[iatm-1,iprm]
                    prm[j]=value
            zprm.append(prm)
        return err,zprm #,zvardic

    def GetVarNamValue(self,varnam):
        value=None
        for keynam,var in self.zvardic.iteritems():
            if var == varnam:
                #iatm,iprm=self.UnPackKeyNam(keynam)
                iatm,iprm=self.UnPackVarNam(var)
                value=self.zprm[iatm][iprm]
        return value

    def OnTry(self,event):
        obj=event.GetEventObject()
        on=obj.GetValue()
        self.tryzmt=on
        self.Try(on)
 
    def Try(self,on):
        if on:
            err=self.GetZMParamsInTable()
            if err: 
                self.tryzmt=False
                self.btntry.SetValue(self.tryzmt)
                self.btnaply.Disable()
                mess='"Try" is Cancelled.'
                lib.MessageBoxOK(mess,'ZMatrixViewer(Try)')
                return
            self.btnaply.Enable()
            self.SaveChange(True)
            self.SaveZMTData(True)
            
            natm=len(self.model.mol.atm)
            self.model.SaveMol()
            
            self.savzprm=copy.deepcopy(self.zprm)
            zmtatm=lib.ZMToCC(self.zelm,self.zpnt,self.zprm)
            if len(self.zelm) == natm:
                cc0=[]; cc1=[]
                for i in range(len(self.zelm)):
                    ###zmtatm[i][0]=str(const.ElmNmb[zmtatm[i][0]])
                    cc0.append(self.model.mol.atm[i].cc[:])
                    cc1.append([zmtatm[i][1],zmtatm[i][2],zmtatm[i][3]])
                rmsd=lib.ComputeRMSD(cc0,cc1)
                mess='(ZMatrixViewer) RMSD='+'%10.6f' % rmsd 
                self.model.ConsoleMessage(mess)
            
            self.trymol=molec.Molecule(self.model)
            self.trymol.SetZMTAtoms(zmtatm)           
            self.trymol.AddBondUseBL([])
            atmlst=range(len(self.trymol.atm))
            self.trymol.RenameResDat(atmlst,self.resdat)
            self.trymol.RenameAtmNam(atmlst,self.atmnam)
            self.SetElement()
            self.model.MergeMolecule(self.trymol.atm,False)
            self.trymolgrpnam=self.model.mol.atm[natm].grpnam
        else:
            self.model.RecoverMol()
            #self.OnReset(1)
            self.model.DrawMol(True)
            
            self.zprm=self.savzprm
            """
            #self.mol=self.model.mol
            self.model.mol.zmtpnt=self.zmtpnt
            self.model.mol.zactivedic=self.zactivedic
            self.model.mol.zvardic=self.zvardic
            """
            self.btnaply.Disable()
    
    def SetElement(self):
        for i in range(len(self.trymol.atm)):
            try: 
                elmnmb=int(self.trymol.atm[i].elm)
                elm=const.ElmSbl[elmnmb]
                self.trymol.atm[i].elm=elm
                self.trymol.atm[i].SetAtomParams(elm)
            except: pass

    def CheckZMParams(self,zelm,zpnt,zprm):
        err=False; err1=False; err2=False
        for i in range(len(zelm)):
            if i == 0: continue
            if i < 3: mprm=i
            else: mprm=3    
            for j in range(mprm):
                if zpnt[i][j] < 0: 
                    mess='Wrong point data for iatm='+str(i+1)+', ipnt='
                    mess=mess+str(j+1)
                    lib.MessageBoxOK(mess,'ZMatrixView(CheckZMParams)')
                    err1=True
                if zprm[i][j] == '': 
                    mess='Wrong param data for iatm='+str(i+1)+', iprm='
                    mess=mess+str(j+1)
                    lib.MessageBoxOK(mess,'ZMatrixView(CheckZMParams)')
                    err2=True
            if err1 and err2: break    
        return err
        
    def UpdateZmtParams(self):
        """ not used """
        return
        
        for keynam,value in self.changeprmdic.iteritems():
            iatm,prm=self.UnPackKeyNam(keynam)
            self.zprm[iatm][prm]=float(value)

    def SaveAtomCC(self):
        self.savatmcc=[]
        for atom in self.model.mol.atm:
            x=atom.cc[0]; y=atom.cc[1]; z=atom.cc[2]
            self.savatmcc.append([x,y,z])
    
    def RecoverAtomCC(self):
        for i in range(len(self.model.mol.atm)):
            x=self.savatmcc[i][0]
            y=self.savatmcc[i][1]
            z=self.savatmcc[i][2]
            self.model.mol.atm[i].cc[0]=x
            self.model.mol.atm[i].cc[1]=y
            self.model.mol.atm[i].cc[2]=z
            
    def OnCommand(self,event): 
        obj=event.GetEventObject()
        cmdlabel=obj.GetLabel() 
        #        
        if cmdlabel == 'Command1':
            menulst=self.cmd1menu; tiplst=self.cmd1tip
            retmethod=self.Command1
            #width=120        
        elif cmdlabel == 'Command2': 
            menulst=self.cmd2menu; tiplst=self.cmd2tip
            retmethod=self.Command2
            #width=150 
        #
        self.lbmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,menulst,
                                           tiplst) #,winwidth=200)
        #        
        event.Skip()
    
    def SetActiveDisp(self,idsp,prm,on,refresh=False):
        prmcoldic={0:5,1:7,2:9}
        iatm=self.displst[idsp]
        keynam=str(iatm)+':'+str(prm)
        col=prmcoldic[prm]
        curcolor=self.grid.GetCellTextColour(idsp,col) 
        if on:
            if idsp >= 0: 
                color=self.activecolor
                if curcolor == self.changecolor: color=self.dualcolor
                self.grid.SetCellTextColour(idsp,col,color) 
            self.activedic[keynam]=True
        else:
            if idsp >= 0: 
                color=self.freezecolor
                if curcolor == self.dualcolor: color=self.changecolor
                self.grid.SetCellTextColour(idsp,col,color)  
            if self.activedic.has_key(keynam): del self.activedic[keynam] 
        if refresh: self.grid.Refresh()
    
    def ResetAllActives(self):
        prmcoldic={0:5,1:7,2:9}
        for i in range(len(self.displst)):
            for j in range(3):
                col=prmcoldic[j]
                self.grid.SetCellTextColour(i,col,self.freezecolor) 
        self.activedic={}
        
        self.grid.Refresh()

    def SetActiveAll(self,prm,on):
        """
        
        :param str prm: 'length','angle',or 'torsion'
        """
        prmcoldic={0:5,1:7,2:9}
        col=prmcoldic[prm]
        for i in range(len(self.displst)): self.SetActiveDisp(i,prm,on)
        self.grid.Refresh()

    def ListSelectedRow(self):
        sellst=[]
        #prmcoldic={0:5,1:7,2:9}
        top=self.grid.GetSelectionBlockTopLeft()
        if len(top) <= 1: return sellst
        bottom=self.grid.GetSelectionBlockBottomRight()    
        trow=top[1][0]; tcol=top[1][1]
        brow=bottom[1][0]; bcol=bottom[1][1]
        for i in range(trow,brow+1): sellst.append(i)
        return sellst

    def ListSelectedRowAtom(self):
        atmlst=[]
        sellst=self.ListSelectedRow()
        for i in sellst: atmlst.append(self.displst[i])
        return atmlst
    
    def SetActiveSelectedCells(self,prm,on):
        sellst=self.ListSelectedRow()
        if len(sellst) <= 0: return
        for i in sellst:
            self.SetActiveDisp(i,prm,on)
        self.grid.Refresh()

    def SetActiveReverseAll(self,prm):
        """
        
        :param str prm: 'length','angle',or 'torsion'
        """
        for i in range(len(self.displst)):
            iatm=self.displst[i]
            keynam=str(iatm)+':'+str(prm)
            if self.activedic.has_key(keynam): on=False
            else: on=True
            self.SetActiveDisp(i,prm,on)
        self.grid.Refresh()

    def ResetParams(self,rowlst,iprm):
        self.SetParamValue(rowlst,[iprm],reset=True,refresh=True)
        
    def ResetAllParams(self):
        self.zprm=copy.deepcopy(self.zprmsav)
        self.zvardic=copy.deepcopy(self.zvardic)
        self.changeprmdic={}
        #self.SetValueToGridCell()
        self.displst=range(len(self.zelm))
        rowlst=range(len(self.zelm)); prmlst=[0,1,2]
        self.SetParamValue(rowlst,prmlst,reset=True,refresh=True)
        
    def ResetSelectedColCells(self,col,sellst):
        itmcol=[0,1,3]; pntcol=[4,6,8]; prmcol=[5,7,9]
        colitmdic={0:0,1:1,3:2}; colprmdic={5:0,7:1,9:2}
        colpntdic={4:0,6:1,8:2}; 
        if len(sellst) <= 0: sellst=self.ListSelectedRow()
        if len(sellst) <= 0: return
        for i in sellst:
            if col in prmcol: 
                self.SetVauleToDispPrmCell(i,colprmdic[col],False)
            elif col in pntcol: 
                self.SetVauleToDispPntCell(i,colpntdic[col],False)
            elif col in itmcol: 
                self.SetVauleToDispItmCell(i,colitmdic[col],False)
        self.grid.Refresh()
        
    def ResetParamSelectedCells(self,prm,sellst):
        if len(sellst) <= 0: sellst=self.ListSelectedRow()
        if len(sellst) <= 0: return
        self.SetParmValue(sellst,[prm],reset=True,refresh=True)
        
    def Command1(self,cmd,label):
        pltcmdlst=['plot length','plot angle','plot torsion']
        if cmd == '---': pass
        elif cmd == 'reset all params': 
            self.ResetAllParams()
        elif cmd == 'reset all actives': 
            self.SetActiveAll(rowlst,collst,reset=True)
            self.activedic={}; rowlst=range(len.self.zelm)
            collst=[5,7,9]
            self.SetCellColor(rowlst,collst)
        
        elif cmd in pltcmdlst: self.PlotGeomParam(cmd)
        
        elif cmd == 'reset all variable names':
            self.ResetVariableName([],[])
    
    def Command2(self,cmd,cmdlabel):
        pltcmdlst=['plot length','plot angle','plot torsion']        
        if cmd == '---': pass
        elif cmd == 'get selected atom': self.GetSelectedAtom()
        elif cmd == 'create new molecule': self.CreateNewMolecule()
        elif cmd == 'set rotation axis': self.SetRotationAxis(True)
        elif cmd == 'del rotation axis': self.SetRotationAxis(False)
        elif cmd == 'select atoms': self.SetSelectAtoms()
        elif cmd == 'show atoms': self.SetShowAtoms(True)
        elif cmd == 'reset show atoms': self.SetShowAtoms(True)                    

    def CreateNewMolecule(self):
        #default='mod-'+self.mol.name
        #text=wx.GetTextFromUser('Enter molecule name',
        #                        default_value=default,parent=self)
        #text=text.strip()
        #if len(text) <= 0: return
        #name=text.strip()
        zmtatm=lib.ZMToCC(self.zelm,self.zpnt,self.zprm) # [elm,x,y,z]
        #
        self.model.NewMolecule()
        #self.model.RenameMolecule(self.mol.name,name)
        self.curmol,self.mol=self.model.molctrl.GetCurrentMol()
        for i in range(len(self.zelm)):
            atom=molec.Atom(self.model.mdlwin)
            atom.seqnmb=i
            elm=zmtatm[i][0]
            atom.elm=elm
            atom.cc=[zmtatm[i][1],zmtatm[i][2],zmtatm[i][3]]
            atom.atmnam=self.atmnam[i]
            resnam,resnmb,chain=lib.UnpackResDat(self.resdat[i])
            atom.resnam=resnam
            atom.resnmb=resnmb
            atom.chainnam=chain
            atom.SetAtomParams(elm)
            self.model.mol.atm.append(atom)
        self.model.mol.AddBondUseBL([])
         #
        self.model.FitToScreen(True,True)

    def SetSelectAtoms(self):
        atmlst=[]
        sellst=self.ListSelectedRow()
        for i in sellst:
            iatm=self.displst[i]
            atmlst.append(iatm)
        self.model.SetSelectAll(False)
        self.model.SetSelectAtom0(atmlst,True)
        self.model.DrawMol(True)
    
    def SetShowAtoms(self,on):
        atmlst=[]
        sellst=self.ListSelectedRow()
        for i in sellst:
            iatm=self.displst[i]
            atmlst.append(iatm)
        if on:
            self.model.SetShowAll(False)
            for i in atmlst: self.model.mol.atm[i].show=True
        else:
            self.model.SetShowAll(True)
        self.model.DrawMol(True)
                        
    def SetRotationAxis(self,on):
        if on:
            default=''
            if self.selectedrow > 0:
                pnt1=self.selectedrow
                try: 
                    default=str(self.zpnt[pnt1][0]+1)+','
                    default=default+str(self.zpnt[pnt1][1]+1)
                except: pass
            mess='Enter numbers of two atoms, e.g. "1,2,..."','Select atoms'
            text=wx.GetTextFromUser(mess,default_value=default,parent=self)
            text=text.strip()
            if len(text) <= 0: return
            text=text.strip()
            items=lib.SplitStringAtSpacesOrCommas(text)
            if len(items) <= 1:
                mess='Wrong input='+text
                lib.MessageBoxOK(mess,'ZMatrixViewer(SetRotationAxis)')
                return
            pnts=[int(items[0])-1,int(items[1])-1]
            self.model.SetRotationAxis(pnts)
        else:
            self.model.mousectrl.SetRotationAxisPnts(False,[]) 
            self.model.DrawAxisArrow(False,[])
        self.model.DrawMol(True)
                
    def PlotGeomParam(self,cmd):
        prmdic={'plot length':0, 'plot angle':1,'plot torsion':2}     
        ylabel=['Length','Angle','Torsion']
        selval=["<0.8","<90.0","<10.0"]
        xlst=[]; ylst=[]
        iprm=prmdic[cmd]
        for i in self.displst:
            if self.zprm[i][iprm] == '': continue
            xlst.append(i+1)
            ylst.append(self.zprm[i][iprm])
        #
        self.pltzmt=subwin.PlotAndSelectAtoms(self,-1,self.model,cmd,"atom")
        self.pltzmt.SetGraphType("bar")
        self.pltzmt.SetColor("b")
        #
        self.pltzmt.NewPlot()
        self.pltzmt.PlotXY(xlst,ylst)
        self.pltzmt.PlotXLabel('Sequence number of atom')
        self.pltzmt.PlotYLabel(ylabel[iprm])
        self.pltzmt.SetInput(selval[iprm])

    def OnExtract(self,event):
        item=self.cmbsel.GetValue()
        text=self.tclsel.GetValue()
        needvarlst=['seqnmb','atmnam','resdat','elm',
                    'length','angle','torsion','variable name']

        if item == '---' or item == '':
            self.cmbsel.SetValue(''); self.tclsel.SetValue('')
            return
        if item in needvarlst and text == '': return
            
        
        displst,needinput=self.Extract(item,text)
        if needinput: return
        
        if not needinput and len(displst) <= 0: 
            mess='No applicable atoms'
            lib.MessageBoxOK(mess,'Extract')
            self.tclsel.SetValue('')
            return
        
        self.dispitem=item
        self.disptext=''
        self.displst=displst
        #self.tclsel.SetValue('')
        self.Resize()
        
        self.tclsel.SetValue('')
            
    def Extract(self,item,text):
        def Message(item,eg='',default=''):
            itemtipdic={'seqnmb':'1,2-5,8','length':'>1.6, <0.9',
                    'angle':'>90.0, <120','torsion':'>170.0, <180',
                    'atmnam':'CA','resdat':'ALA:1:A, resnam:resnmb:chain name',
                    'elm':'H'}
            mess='Enter value and hit [ENTER]'
            if eg == '': eg=itemtipdic[item] 
            mess=mess+' (e.g., "'+eg+'")'
            lib.MessageBoxOK(mess,'Extract items')
            #text=wx.GetTextFromUser(mess,'ZMatrixViewer(MakeDispList)',default)
            #return text
        needinput=False
        displst=[]
        text=text.strip()
        if item == 'all':
            displst=range(len(self.zelm))
        elif item == 'seqnmb':
            if len(text) <= 0: 
                Message(item); return displst,True
            displst=lib.StringToInteger(text)
            for i in range(len(displst)): displst[i] -= 1      
        elif item == 'length' or item == 'angle' or item == 'torsion':
            #messdic={'length':'>1.6, <0.9','angle':'>90.0, <120','torsion':'>170.0, <180'}
            if len(text) <= 0: 
                Message(item); return displst,True
            displst=self.ExtractGeomParam(item,text)
        elif item == 'atmnam':
            if len(text) <= 0: 
                Message(item); return displst,True
            displst,text=self.ExtractAtmNam(text)
        elif item == 'resdat':
            if len(text) <= 0: 
                Message(item); return displst,True
            displst,text=self.ExtractResDat(text)
        elif item == 'elm':
            if len(text) <= 0: 
                Message(item); return displst,True
            displst,text=self.ExtractElm(text)
        elif item == 'selected atoms':
            for i in range(len(self.model.mol.atm)):
                if self.model.mol.atm[i].select: displst.append(i)
        elif item == 'show atoms':
            for i in range(len(self.model.mol.atm)):
                if self.model.mol.atm[i].show: displst.append(i)
        elif item == 'changed': 
            objlst=[self.changepntdic,self.changeprmdic]
            for obj in objlst:
                if len(obj) <= 0: continue
                for keynam,value in obj.iteritems():
                    iatm,iprm=self.UnPackKeyNam(keynam)
                    if not iatm in displst: displst.append(iatm)
        elif item == 'active': 
            for keynam,value in self.activedic.iteritems():
                iatm,iprm=self.UnPackKeyNam(keynam)
                if not iatm in displst: displst.append(iatm)
        elif item == 'variable name': 
            if len(text) <= 0: 
                Message(item); return displst,True
            varlst=self.MakeVarNamListFromText(text)
            for keynam,varnam in self.zvardic.iteritems():
                if varnam in varlst:
                    iatm,iprm=self.UnPackKeyNam(keynam)
                    if not iatm in displst: displst.append(iatm)              
        return displst,needinput

    def GetLargerAndSmaller(self,text):
        def ErrorMessage(text):
            mess='Wrong data. text='+text
            lib.MessageBoxOK(mess,'ZMatrixEditor(GetLargerAndSmalerr)')
        larger=''; smaller=''
        items=text.split(',')
        for i in range(len(items)):
            s=items[i].strip()
            if s[:1] == '>':
                larger=s[1:].strip()
                try: larger=float(larger)
                except: ErrorMessage(text)
            if s[:1] == '<':
                smaller=s[1:].strip()
                try: smaller=float(smaller)
                except: ErrorMessage(text)
        return larger,smaller
    
    def MakeVarNamListFromText(self,text):
        hvar=['R','A','T']
        varlst=[]; rvar=''; avar=''; tvar=''
        items=lib.SplitStringAtSpacesOrCommas(text)
        for s in items:
            if s[:1].upper() == 'R': rvar=rvar+s[1:]+','
            elif s[:1].upper() == 'A': avar=avar+s[1:]+','
            elif s[:1].upper() == 'T': tvar=tvar+s[1:]+','
        objlst=[rvar,avar,tvar]
        for i in range(3):
            obj=objlst[i]
            if len(obj) <= 0: continue
            obj=obj[:-1]
            nmblst=lib.StringToInteger(obj)
            for j in nmblst:
                varnam=hvar[i]+('%04d' % j)
                varlst.append(varnam)
        return varlst
    
    def ExtractElm(self,text):
        displst=[]

        if len(text) <= 0: return displst,text
        elmlst=lib.SplitStringAtSpacesOrCommas(text)
        for i in range(len(elmlst)):
            if len(elmlst[i]) == 1: elmlst[i]=' '+elmlst[i]
            elif len(elmlst[i]) > 2: elmlst[i]=elmlst[i][:2]
            elmlst[i]=elmlst[i].upper()
        for i in range(len(self.zelm)):
            if self.zelm[i] in elmlst: displst.append(i)
        return displst,text
    
    def ExtractResDat(self,text):
        displst=[]
        if len(text) <= 0: return displst,text
        reslst=lib.SplitStringAtSpacesOrCommas(text)
        for i in range(len(self.zelm)):
            res=self.resdat[i].strip()
            if res in reslst: displst.append(i)
        return displst,text
    
    def ExtractAtmNam(self,text):
        displst=[]
        if len(text) <= 0: return displst,text
        namlst=lib.SplitStringAtSpacesOrCommas(text)
        for i in range(len(namlst)):
            namlst[i]=namlst[i].upper()
        for i in range(len(self.atmnam)):
            name=self.atmnam[i].strip()
            if name in namlst: displst.append(i)       
        return displst,text
    
    def ExtractGeomParam(self,item,text):
        displst=[]
        prmdic={'length':0,'angle':1,'torsion':2}
        iprm=prmdic[item]
        larger,smaller=self.GetLargerAndSmaller(text)
        if smaller == '' and larger == '': return
        if iprm == 2:
            if smalle != '': smaller=abs(smaller)
            if larger != '': larger=abs(larger) 
        for i in range(len(self.zelm)):
            if self.zprm[i][iprm] == '': continue
            value=self.zprm[i][iprm]
            if iprm == 2: value=abs(value)
            if smaller == '':
                if value > larger and not i in displst: displst.append(i) 
            elif larger == '':
                if value < smaller and not i in displst: displst.append(i) 
            else:
                if value > larger and value < smaller and not i in displst: 
                    displst.append(i)                        
        return displst
    
    def OnReset(self,event):
        try: self.panel.Destroy()
        except: pass
        self.curmol,self.mol=self.model.molctrl.GetCurrentMol()
        self.MakeZMData()
        self.displst=range(len(self.model.mol.atm))        
        self.CreatePanel()
        self.CreateGrid()
        #self.MakeZMData()
        self.SetDataToGridTable()
        self.SetTitle(self.title+' ['+self.model.mol.name+']')
        #
        #lib.MessageBoxOK('Restored molecule data in mdlwin','')
        self.model.Message('Restored molecule object',0,'')
        try: event.Skip()
        except: pass
        
    def OnClose(self,event):
        try: self.viewprm.Destroy()
        except: pass
        try: self.pltzmt.Destroy()
        except: pass
        self.model.winctrl.Close(self.winlabel)
        self.Destroy()
    
    def OnResize(self,event):
        self.Resize()
        
    def Resize(self):
        self.panel.Destroy()
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])        
        self.CreatePanel()
        self.CreateGrid()
        self.SetDataToGridTable()

    def ResetTable(self):
        self.OnReset(1)
         
    def OnClearSelection(self,event):
        self.grid.ClearSelection()
    
    def OnColCommand(self,event):
        pos=self.ScreenToClient(wx.GetMousePosition())

        label=''
        # atnam
        if pos[0] > 15 and pos[0] < 50: label='atmnam'
        # resdat
        elif pos[0] > 70 and pos[0] < 110: label='resdat'
        # lem
        elif pos[0] > 170 and pos[0] < 190: label='elm'
        # p1
        elif pos[0] > 200 and pos[0] < 240: label='p1'
        # length
        elif pos[0] > 250 and pos[0] < 300: label='length'
        # p2
        elif pos[0] > 310 and pos[0] < 350: label='p2'
        # angle
        elif pos[0] > 360 and pos[0] < 410: label='angle'
        #p3
        elif pos[0] > 420 and pos[0] < 460: label='p3'
        # trosion
        elif pos[0] > 470 and pos[0] < 510: label='torsion'
        #
        if label == '': return
        if label == 'p1' or label == 'p2' or label == 'p3':
            menulst=self.colcmdmenu; tiplst=self.colcmdtip
            retmethod=self.CommandCol
            #width=120
        elif label == 'atmnam' or label == 'resdat' or label == 'elm':
            menulst=self.colcmdmenu; tiplst=self.colcmdtip
            retmethod=self.CommandCol
            #width=120
        elif label == 'length':
            menulst=self.prmcolcmdmenu[:]; tiplst=self.prmcolcmdmenu
            retmethod=self.CommandCol
            menulst.append('---')
            menulst.append('set std value in selected cells')        
        else: 
            menulst=self.prmcolcmdmenu; tiplst=self.prmcolcmdmenu
            retmethod=self.CommandCol
        
        self.lbmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,menulst,
                                           tiplst,menulabel=label) 
        
        event.Skip()

    def CommandCol(self,cmd,label):
        prmcmd=['length','angle','torsion']
        pntcmd=['p1','p2','p3']
        if label in prmcmd: 
            if label == 'length': 
                col=5; prm=0
            elif label == 'angle':
                 col=7; prm=1
            elif label == 'torsion': 
                col=9; prm=2
            #
            if cmd == 'set active all': self.SetActiveAll(prm,True)
            elif cmd == 'reset all active': self.SetActiveAll(prm,False)
            #elif cmd == 'reverse active in selected cells': pass
            elif cmd == 'reverse all active': self.SetActiveReverseAll(prm)
            elif cmd == 'set active to selected cells': 
                self.SetActiveSelectedCells(prm,True)
            elif cmd == 'reset active in selected cells': 
                self.SetActiveSelectedCells(prm,False)    
            elif cmd == 'reset params in selected cells': 
                rowlst=self.ListSelectedRow()
                if len(rowlst) > 0: 
                    #self.ResetSelectedColCells(col,[])
                    self.SetParamValue(rowlst,[prm],reset=True,refresh=True)
            elif cmd == 'rest all params': 
                rowlst=range(len(self.zelm))
                self.SetParamValue(rowlst,[prm],reset=True,refresh=True)
            elif cmd == 'replace variable name in selected cells': pass
            elif cmd == 'replace all variable names': pass
            elif cmd == 'set std value in selected cells': 
                self.SetStandardLength([])
        elif label in pntcmd:
            pnt=-1
            if label == 'p1': pnt=0
            elif label == 'p2': pnt=1
            elif label == 'p3': pnt=2
            #
            if cmd == 'reset selected cells': self.ResetPnts(pnt,True)
            elif cmd == 'reset all': self.ResetPnts(pnt,False)
            elif cmd == 'replace selected cells':
                self.Replace(label,selected=True)
            elif cmd == 'replace all':
                self.Replace(label,selected=False)
        else:
            #def CommandColItem(self,cmd,label,selected=True):
            if cmd == 'reset selected cells': self.ResetItem(label,'selected')
            elif cmd == 'reset all': self.ResetItem(label,'all')
            elif cmd == 'replace selected cells':
                self.Replace(label,selected=True)
            elif cmd == 'replace all':
                self.Replace(label,selected=False)
            
    def SetStandardLength(self,atmlst,selected=True):
        if len(atmlst) <= 0:
            if selected: atmlst=self.ListSelectedRowAtom()
            else: atmlst=range(len(self.zelm))
        for i in atmlst:
            j=self.zpnt[i][0]
            ielm=self.zelm[i]; jelm=self.zelm[j]
            length=const.ElmCov[ielm]+const.ElmCov[jelm]
            self.zprm[i][0]=length
            
        self.SetDataToGridTable()
            
    def Replace(self,label,selected=True):
        mess='Enter varnam=value, e.g., wat:1:=HOH:1: for resdat).'
        text=wx.GetTextFromUser(mess,caption='Replace '+label)
        if len(text) <= 0: return
        
        oldval,newval=lib.SplitVariableAndValue(text)
        if selected: sellst=self.ListSelectedRow()
        else: sellst=range(len(self.zelm)) # all
        pntlabel={'p1':0,'p2':1,'p3':2}
        itmcol={'atmnam':0,'resdat':1,'p1':4,'p2':6,'p3':8}
        if pntlabel.has_key(label):
            ipnt=pntlabel[label]
            oldval=int(oldval); newval=int(newval)
            for idsp in sellst:
                iatm=idsp
                if select: iatm=self.displst[idsp]
                if self.zpnt[iatm][ipnt] == oldval:
                    self.zpnt[iatm][ipnt]=newval
                    keynam=str(iatm)+':'+str(ipnt)
                    self.changepntdic[keynam]=newval
        else:
            if label == 'atmnam': 
                obj=self.atmnam; obj1=self.changeatmnam
            elif label == 'resdat': 
                obj=self.resdat; obj1=self.changeresdat
            col=itmcol[label]
            for idsp in sellst:
                iatm=idsp
                if selected: iatm=self.displst[idsp]
                if obj[iatm].strip() == oldval: 
                    obj[iatm]=newval; obj1[iatm]=True
        self.SetDataToGridTable()
        
    def ResetItem(self,item,cells='current'):
        """ 
        
        :param bool selected: True for selected only, False for all
        """
        atmlst=[]
        if cells == 'current': atmlst=[self.selectedrow]
        elif cells == 'selected': 
            sellst=self.ListSelectedRow()
            for i in sellst: atmlst.append(self.displst[i]) 
        else: atmlst=range(len(self.zelm)) # all
        for i in atmlst:
            if item == 'atmnam':
                self.changeatmnam[i]=False
                value=self.atmnamsav[i]; col=0
            elif item == 'resdat':
                self.changeresdat[i]=False
                value=self.resdatsav[i]; col=1
            elif item == 'elm':
                self.changeelm[i]=False
                value=self.zelmsav[i]; col=3
            if i in self.displst:        
                idsp=self.displst.index(i)
                idsp=self.displst.index(i)
                self.grid.SetCellValue(idsp,col,value)
                self.grid.SetCellTextColour(idsp,col,self.textcolor)  

    def ResetPnts(self,pnt,selected=True):
        """ 
        
        params bool selcted: True for selected only, False for all displaied
        """
        atmlst=[]; prmcol={0:5,1:7,2:9}
        if selected: 
            sellst=self.ListSelectedRow()
            for i in sellst: atmlst.append(self.displst[i]) 
        else: atmlst=range(len(self.zelm))
        for i in atmlst:
            if pnt == 'p1': prm=0
            elif pnt == 'p2': prm=1
            elif pnt == 'p3': prm=2
            keynam=str(i)+':'+str(prm)
            col=prmcol[prm]
            self.changeprm[keynam]=False
            if i in self.displst:
                idsp=self.displst.index(i)
                value=str(self.zprm[i][prm])
                self.grid.SetCellValue(idsp,col,value)
                self.grid.SetCellTextColour(idsp,col,self.textcolor)  
    
    def OnCellRightClick(self,event):
        #self.grid.ClearSelection()
        prmlst=[5,7,9]; pntlst=[4,6,8]; itmlst=[0,1,3]
        itmnam=['atmnam','resdat','elm']
        # cell in seq.# column
        if self.selectedcol == 2:
            menulst=self.rowcmdmenu
            tiplst=self.rowcmdtip
            retmethod=self.CommandRow
            label='seq'
        # prams column cell
        elif self.selectedcol in prmlst:
            menulst=self.cellprmmenu
            tiplst=self.cellprmtip #[]
            retmethod=self.CommandCell
            label='prm'
        # point column cell
        elif self.selectedcol in pntlst:
            menulst=self.cellpntmenu
            tiplst=self.cellpnttip #[]
            retmethod=self.CommandCell
            label='pnt'
        
        elif self.selectedcol in itmlst: # atmnam,resdat,elm
            menulst=self.cellitmmenu 
            tiplst=self.cellitmtip #[]
            retmethod=self.CommandCell
            idx=itmlst.index(self.selectedcol)
            label=itmnam[idx]
            
        try: self.lbmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,
                                               menulst,tiplst,menulabel=label)
        except: pass
        event.Skip()
            
    def CommandRow(self,item,label):
        iatm=self.displst[self.selectedrow]
        if item == 'close me': 
            self.lbmenu.OnClose(1)
            return
        insert=True
        if item == 'insert upper': 
            self.insertatm=self.InsertAtom(iatm,True)
        elif item == 'insert lower': 
            self.insertatm=self.InsertAtom(iatm,False)
        elif item == 'delete': 
            self.deleteatm=self.DeleteAtoms(iatm)
            insert=False
        #
        self.RenumberVarNam(insert)
        self.RenumberChange(insert)
        self.insertatm=-1; self.deleteatm=-1
            
        # reset grid table
        self.displst=range(len(self.zelm))
        self.Resize()
            
    def DeleteAtoms(self,iatm):
        del self.zelm[iatm]
        del self.zpnt[iatm]
        del self.zprm[iatm]
        del self.atmnam[iatm]
        del self.resdat[iatm]
        zpnt=copy.deepcopy(self.zpnt)
        for i in range(len(self.zelm)):
            for j in range(3):
                if i == iatm:
                    keynam=str(i)+':'+str(j)
                    self.inputdic[keynam]=True
                    continue
                if i > iatm:
                    if zpnt[i][j] >= 0: 
                        self.zpnt[i][j]=zpnt[i][j]-1             
                    if self.zpnt[i][j] < 0: 
                        self.zpnt[i][j]=-2; self.zprm[i][j]=''
                else: self.zpnt[i][j]=zpnt[i][j]
        return iatm
    
    def InsertAtom(self,iatm,upper=True):
        apd=False
        if upper: 
            iatm1=iatm; inc=1
        else: 
            iatm1=iatm+1; inc=2
        if upper or iatm1 < len(self.model.mol.atm)-1: 
            #cc=self.model.mol.atm[iatm].cc[:]
            self.zelm.insert(iatm1,' X')
            self.atmnam.insert(iatm1,'X')
            self.resdat.insert(iatm1,'')
            self.zpnt.insert(iatm1,[-2,-2,-2])
            self.zprm.insert(iatm1,['','',''])
        else:
            self.zelm.append(' X')
            self.atmnam.append('X')
            self.resdat.append('')
            self.zpnt.append([-2,-2,-2])
            self.zprm.append(['','',''])
            iatm1=len(self.zelm)-1; apd=True
        #self.atmnam[iatm1]='X'
        self.resdat[iatm1]=self.resdat[iatm1-1]
        # renumber point data
        zpnt=copy.deepcopy(self.zpnt)
        if not apd:
            for i in range(len(self.zelm)):
                for j in range(3):
                    if i > iatm+inc: 
                        if zpnt[i][j] >= 0: self.zpnt[i][j]=zpnt[i][j]+inc
                        else: self.zpnt[i][j]=-1
                    else: self.zpnt[i][j]=zpnt[i][j]
        return iatm1

    def RenumberVarNam(self,insert):
        if insert:
            atatm=self.insertatm+1; inc=1
        else: 
            atatm=self.deleteatm; inc=-1
            #delprmval=self.zvardic[atatm]
        if atatm < 0:
            mess='No insert/delete atom data. Unable to continue'
            lib.MessageBoxOK(mess,'ZMatrixViewer(RenumberVarNam')
            return
        # vardic
        zvardic=copy.deepcopy(self.zvardic); self.zvardic={}
        zvarkeylst=zvardic.keys()
        if len(zvarkeylst) > 0:
            for jkey in zvarkeylst:
                jatm,jprm=self.UnPackKeyNam(jkey)
                jvar=zvardic[jkey]
                if not insert and jatm == atatm: 
                    continue
                vatm,vprm=self.UnPackVarNam(jvar)
                if not insert and vatm == atatm:                    
                    continue      
                if jatm >= atatm:
                    if vatm == 0: continue
                    if vatm == 1 and vprm == 1: continue
                    if vatm == 1 and vprm == 2: continue
                    if vatm == 2 and vprm == 2: continue   
                        
                    newkey=str(jatm+inc)+':'+str(jprm)
                    newvar=self.vsbl[vprm]+'%04d' % (vatm+inc+1)
                    self.zvardic[newkey]=newvar
                else: self.zvardic[jkey]=zvardic[jkey]
        # check parent varnam exists
        if len(self.zvardic) > 0:
            zvardic=copy.deepcopy(self.zvardic); self.zvardic={}
            zvarkeylst=zvardic.keys(); self.parvarlst=[]
            for keynam in zvarkeylst:
                jatm,jprm=self.UnPackKeyNam(keynam)
                varnam=zvardic[keynam]
                vatm,vprm=self.UnPackVarNam(varnam)
                if jatm == vatm: self.parvarlst.append(varnam)        
            for keynam in zvarkeylst:
                varnam=zvardic[keynam]
                if varnam in self.parvarlst: 
                    self.zvardic[keynam]=zvardic[keynam]
   
    def RenumberChange(self,insert):
        if insert:
            atatm=self.insertatm+1; inc=1
        else:
            atatm=self.deleteatm; inc=-1
            #delprmval=self.zvardic[atatm]
        if atatm < 0:
            mess='No insert/delete atom data. Unable to continue'
            lib.MessageBoxOK(mess,'ZMatrixViewer(RenumberChange')
            return
        # changeprmdic and changepntdic
        nmblst=[0,1,2]
        changepntdic=copy.deepcopy(self.changepntdic)
        changeprmdic=copy.deepcopy(self.changeprmdic)
        changeelm=copy.deepcopy(self.changeelm)
        changeatmnam=copy.deepcopy(self.changeatmnam)
        changeresdat=copy.deepcopy(self.changeresdat)  
        newobjlst=[self.changepntdic,self.changeprmdic,
                   self.changeelm,self.changeatmnam,self.changeresdat]
        oldobjlst=[changepntdic,changeprmdic,
                   changeelm,changeatmnam,changeresdat]
        for i in range(len(oldobjlst)):
            oldobj=oldobjlst[i]; objkeylst=oldobjlst[i].keys()
            newobj=newobjlst[i]
            for jkey in objkeylst:
                jatm,jprm=self.UnPackKeyNam(jkey)
                if not insert and jatm == atatm: continue
                
                
                
                if self.zprm[jatm][jprm] == '': continue
                
                
                vatm,vprm=self.UnPackVarNam(obj[jkey])
                if jatm > atatm:
                    newobj[jatm+inc]=oldobj[jatm]      
        
    def SetChangeFlag(self,atmlst,collst,on,select=False):
        def SetValue(obj,keynam,on):
            if on: obj[keynam]=True
            else:
                if obj.has_key(keynam): del obj[keynam]
                
        if len(collst) <= 0: collst=range(10)
        if len(atmlst) <= 0: atmlst=range(len(self.zelm))            
        colprm=[5,7,9]; colpnt=[4,6,8]
        colprmdic={5:0,7:1,9:2}; colpntdic={4:0,6:1,8:2}
        for iatm in atmlst:
            idsp=iatm
            if select:
                if iatm in self.displst: idsp=self.displst.index(iatm)
                else: continue
            SetValue(self.changeelm,idsp,on)
            SetValue(self.changeatmnam,idsp,on)
            SetValue(self.changeresdat,idsp,on)
            for j in collst:
                if j in colpnt:
                    pnt=colpntdic[j]
                    keynam=str(idsp)+':'+str(pnt)
                    SetValue(self.changepntdic,keynam,on)
                elif j in colprm:
                    keynam=str(idsp)+':'+str(pnt)
                    SetValue(self.changeprmdic,keynam,on)
                    if not self.IsIndependentVar(keynam,self.zvardic):
                        for key,varnam in self.zvardic.iteritems():
                            SetValue(self.changeprmdic,key,on)
                    
            self.SetCellColor([iatm],[])

    def ResetVariableName(self,atmlst,prmlst,resetdata=True):
        """
        
        :param 
        """
        if len(atmlst) <= 0: atmlst=range(len(self.zelm))
        if len(prmlst) <= 0: prmlst=range(3)
        #
        for iatm in atmlst:
            for iprm in prmlst:
                keynam=str(iatm)+':'+str(iprm)
                if self.zvardic.has_key(keynam): del self.zvardic[keynam]
        
        if resetdata: self.SetDataToGridTable()
        
    def ResetBond(self):
        self.model.mol.DelAllKindBonds([])
        self.model.mol.AddBondUseBL([])
        
    def Reorder(self,iatm,dicobj,add=True):
        if len(dicobj) <= 0: return
        tmpdic={}
        if add: inc=1
        else: inc=-1
        for keynam,val in dicobj.iteritems():
            ia,ip=self.UnPackKeyNam(keynam)
            if ia > iatm:
                if ip > 0: newkey=str(ia+1)+':'+str(ip)
                else: newkey=ia+inc
                tmpdic[newkey]=val
            else: tmpdic[keynam]=val
        dicobj=copy.deepcopy(tmpdic) 
              
    def CommandCell(self,item,label):

        colprmdic={5:0,7:1,9:2}; colpntdic={4:0,6:1,8:2}
        colitmdic={0:0,1:1,3:2}
        idsp=self.selectedrow; col=self.selectedcol

        idsp=self.selectedrow; col=self.selectedcol
        
        if label == 'prm':
            prm=-1
            try: prm=colprmdic[col]
            except: pass
            if prm < 0: return
            if item == 'close me': self.lbmenu.OnClose(1)
            elif item == 'set freeze':
                self.SetActiveDisp(idsp,prm,False,refresh=True)
            elif item== 'set active':
                self.SetActiveDisp(idsp,prm,True,refresh=True)
            elif item == 'reset value':
                self.SetParamValue([idsp],[prm],reset=True,refresh=True)
            elif item == 'reset variable name':
                iatm=self.displst[idsp]              
                self.ResetVariableName([iatm],[prm])
            else:
                mess='Program error: not defined menu item='+item
                lib.MessageBoxOK(mess,'ZMatrixViewer(CellMenu)')
        elif label == 'pnt':
            pnt=-1
            try: prm=colpntdic[col]
            except: pass
            if pnt < 0: return
            if item == 'close me': self.lbmenu.OnClose(1)
            elif item == 'reset value':
                self.ResetSelectedColCells(col,[])
            else:
                mess='Program error: not defined menu item='+item
                lib.MessageBoxOK(mess,'ZMatrixViewer(CellMenu)')
        elif label == 'atmnam' or label == 'resdat' or label == 'elm':
            #itm=-1
            #try: itm=colitmdic[col]
            #except: pass
            #if itm < 0: return
            if item == 'close me': self.lbmenu.OnClose(1)
            elif item == 'reset value':
                #self.ResetItemSelectedCells(itm,idsp)
                self.ResetItem(label,'current')
            else:
                mess='Program error: not defined menu item='+item
                lib.MessageBoxOK(mess,'ZMatrixViewer(CellMenu)')
    
    def SetActiveColor(self):
        prmcol=[5,7,9]
        for i in range(len(self.displst)):
            iatm=self.displst[i]
            for j in range(3):
                keynam=str(iatm)+':'+str(j)
                col=prmcol[j]
                if self.activedic.has_key(keynam) and self.activedic[keynam]: 
                    color=self.activecolor
                else: color=self.freezecolor     
                self.grid.SetCellTextColour(i,col,color)

    def SetParamColor(self,refresh=False):
        prmcoldic={0:5,1:7,2:9}
        for idsp in range(len(self.displst)):
            iatm=self.displst[idsp]
            for prm in range(3):
                keynam=str(iatm)+':'+str(prm)
                col=prmcoldic[prm]
                if self.changeprmdic.has_key(keynam):
                    keynamlst=self.ListDependentVar(keynam,self.zvardic)
                    for ikey in keynamlst:
                        iat,ipr=self.UnPackKeyNam(ikey)
                        if iat in self.displst:
                            idx=self.displst.index(iat)
                            self.grid.SetCellTextColour(idx,col,
                                                        self.changecolor) 
                else:
                    self.grid.SetCellTextColour(idsp,col,self.textcolor) 
        #
        if refresh: self.grid.Refresh()
                
    def UnPackVarNam(self,varnam):
        vsbl=varnam[:1]; vsbl=vsbl.upper()
        if vsbl == 'R': iprm=0
        elif vsbl == 'A': iprm=1
        elif vsbl == 'T': iprm=2
        #elif vsbl == 'D': iprm=2
        else: iprm=-1
        iatm=int(varnam[1:])-1
        return iatm,iprm
        
    def UnPackKeyNam(self,keynam):
        iatm=-1; prm=-1
        items=lib.SplitStringAtSeparator(keynam,':')
        if len(items) >= 1: iatm=int(items[0])
        if len(items) >= 2: prm=int(items[1])
        return iatm,prm
                
    def OnGridCellChange(self,event):
        row=self.selectedrow=event.GetRow()
        col=self.selectedcol=event.GetCol()
        value=self.grid.GetCellValue(row,col)
        value=value.strip()
        
        self.CellValueChange(row,col,value)
        self.SetCellColor([row],[col])

        self.EnableTry()
        #self.grid.SelectBlock(row,col+1,row,col+1)
        
    def CellValueChange(self,row,col,value):    
        """ for debug"""
        def PointError(pnt,iatm,newpnt):
            mess='Wrong point data. new point='+str(newpnt)
            lib.MessageBoxOK(mess,'ZMatrixViewer_Frm(OnGridCellChanged)')                
            if iatm in self.displst:
                value=self.zpnt[iatm][pnt]
                value=self.grid.SetCellValue(self.selectedrow,self.selectedcol,
                                             str(value))
            
        colprmdic={5:0,7:1,9:2}; prmcollst=[5,7,9]
        colpntdic={4:0,6:1,8:2}; pntcollst=[4,6,8]
        idsp=row
        iatm=self.displst[idsp]
        #
        if col in prmcollst: # prms   
            self.changed=True
            prm=colprmdic[col]
            keynam=str(iatm)+':'+str(prm)
            try: 
                value=float(value)
                self.zprm[iatm][prm]=value
            except:
                vatm,vprm=self.UnPackVarNam(value.upper())
                if vprm < 0 or vatm > iatm:
                    mess='Wrong varoable name input. The variable number '
                    mess=mess+'should be smaller than '+str(iatm+1)
                    lib.MessageBoxOK(mess,'ZMatrixViewer(OnGridCellChange)')
                    return                  
                varnam=self.vsbl[vprm]+'%04d' % (vatm+1)
                self.zvardic[keynam]=varnam
                if vatm != iatm:
                    parkey=str(vatm)+':'+str(vprm)           
                    if not self.zvardic.has_key(parkey):
                        self.zvardic[parkey]=varnam 
                #self.zprm[iatm][prm]=value
                self.grid.SetCellValue(idsp,col,varnam)
                #value=self.zprm[iat][iprm] 
            self.changeprmdic[keynam]=value
            
            self.SetDataToGridTable()
            return
            
            #self.SetParamColor()
            #self.SetParamDisp(idsp,prm,True,refresh=True)
            
        elif col in pntcollst: # pnts
            pnt=colpntdic[col]
            newpnt=int(value)-1  
            if newpnt >= iatm:
                mess='Wrong point data. new point='+str(newpnt)
                mess=mess+'. The point number should be smaller than '+str(iatm)
                lib.MessageBoxOK(mess,'ZMatrixViewer_Frm(OnGridCellChanged)')
                return   
            keynam=str(iatm)+':'+str(pnt)
            self.changepntdic[keynam]=int(value)-1
            self.zpnt[iatm][pnt]=int(value)-1
            if iatm in self.displst:
                value=self.zpnt[iatm][pnt]+1
                self.grid.SetCellValue(self.selectedrow,self.selectedcol,
                                       str(value))                       
            self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,
                                        self.changecolor)
        elif col == 0: 
            self.changeatmnam[iatm]=value
            self.atmnam[iatm]=lib.AtmNamFromString(value)
            self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,
                                        self.changecolor)
        elif col == 1: 
            self.changeresdat[iatm]=value
            self.resdat[iatm]=value
            self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,
                                        self.changecolor)
        elif col == 3: 
            self.changeelm[iatm]=value
            self.zelm[iatm]=lib.ElementNameFromString(value)
            self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,
                                        self.changecolor)
        else: return
        #
        curnmb=self.grid.GetCellValue(self.selectedrow,2)
        self.curnmb=curnmb
        
        """
        curcolor=self.grid.GetCellTextColour(self.selectedrow,self.selectedcol)
        color=self.changecolor
        if curcolor == self.activecolor: color=self.dualcolor
        self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,color)
        #
        """
        self.EnableTry()
        self.grid.Refresh()
       
    def SetCellColor(self,rowlst,collst):
        if len(rowlst) <= 0: rowlst=range(len(self.displst))
        if len(collst) <= 0: collst=range(10)
        colprmdic={5:0,7:1,9:2}; prmcollst=[5,7,9]
        colpntdic={4:0,6:1,8:2}; pntcollst=[4,6,8]
        for idsp in rowlst:
            iatm=self.displst[idsp]
            for col in collst:
                color=self.textcolor
                if col in prmcollst: # param
                    color=self.textcolor
                    iprm=colprmdic[col]
                    keynam=str(iatm)+':'+str(iprm)  
                    if self.IsIndependentVar(keynam,self.zvardic):
                        chgprm=False; chgact=False
                        if self.changeprmdic.has_key(keynam): chgprm=True
                        if self.activedic.has_key(keynam): 
                            chgact=self.activedic[keynam]
                        if chgprm and chgact: color=self.dualcolor
                        elif chgprm and not chgact: color=self.changecolor
                        elif not chgprm and chgact: color=self.activecolor
                        keynamlst=self.ListDependentVar(keynam,self.zvardic)
                        for ikey in keynamlst:
                            jatm,jprm=self.UnPackKeyNam(ikey)
                            if jatm in self.displst:
                                jdsp=self.displst.index(jatm)
                                self.grid.SetCellTextColour(jdsp,col,color)
                elif col in pntcollst: # pnts
                    color=self.textcolor
                    ipnt=colpntdic[col]
                    keynam=str(iatm)+':'+str(ipnt)
                    if self.changepntdic.has_key(keynam): 
                        color=self.changecolor
                    if self.zpnt[iatm][ipnt] < 0: color=self.inputcolor
                    self.grid.SetCellTextColour(idsp,col,color)
                else:
                    if col == 0: # atmnam
                        if self.changeatmnam.has_key(iatm): 
                            color=self.changecolor
                    elif col == 1: # resdat
                        if self.changeresdat.has_key(iatm): 
                            color=self.changecolor
                    elif col == 2: continue
                    elif col == 3: # elm
                        if self.changeelm.has_key(iatm): color=self.changecolor               
                    self.grid.SetCellTextColour(idsp,col,color)
        
        self.grid.Refresh()
        
    def ListDependentVar(self,keynam,zvardic):
        keynamlst=[]
        if keynam in self.nullkeynam: return keynamlst
        iatm,iprm=self.UnPackKeyNam(keynam)
        if not zvardic.has_key(keynam): 
            keynamlst.append(keynam)
        else:
            varnam=zvardic[keynam]
            for key,var in zvardic.iteritems():
                if var != varnam: continue
                if key in self.nullkeynam: continue
                iat,ipr=self.UnPackKeyNam(key)
                if iat in self.displst and ipr == iprm:
                    idx=self.displst.index(iat)
                    keynamlst.append(key)
        return keynamlst

    def IsIndependentVar(self,keynam,zvardic):
        ans=True
        if not zvardic.has_key(keynam): ans=True
        else:
            varnam=zvardic[keynam]
            iatm,iprm=self.UnPackKeyNam(keynam)
            jatm,jprm=self.UnPackVarNam(varnam)
            if jatm == iatm and jprm == iprm: ans=True
            else: ans=False
        return ans

    def SetParamValue(self,rowlst,prmlst,reset=False,refresh=False):
        
        if len(rowlst) <= 0: rowlst=range(len(self.zelm))
        if len(prmlst) <= 0: prmlst=range(3)
        #
        prmcoldic={0:5,1:7,2:9}; form=['%8.3f','%8.2f','%8.2f']
        #
        for row in rowlst:
            if not row in self.displst: continue
            iatm=self.displst.index(row)
            for iprm in prmlst:
                keynam=str(iatm)+':'+str(iprm)
                if keynam in self.nullkeynam: continue
                col=prmcoldic[iprm]
                if reset:
                    self.zprm[iatm][iprm]=self.zprmsav[iatm][iprm]
                    value=self.prmform[iprm] % self.zprm[iatm][iprm] 
                    if self.changeprmdic.has_key(keynam): 
                        del self.changeprmdic[keynam]
                    if self.zvardic.has_key(keynam):
                        if self.zvardicsav.has_key(keynam):
                            self.zvardic[keynam]=self.zvardicsav[keynam]
                        else: del self.zvardic[keynam]
                        if self.IsIndependentVar(keynam,self.zvardic): 
                            value=form[iprm] % self.zprm[iatm][iprm]
                        else: value=self.zvardic[keynam]
                        self.grid.SetCellValue(row,col,value)
                        self.SetCellColor([row],[col])
                else:
                    if self.changeprmdic.has_key(keynam):
                        value=self.prmform[iprm] % self.zprm[iatm][oprm]
                        if not self.IsIndependentVar(keynam,self.zvardic):
                            value=self.zvardic[keynam] 
                        self.grid.SetCellValue(row,col,value)
                        self.SetCellColor([row],[col])
        #
        if refresh: self.grid.Refresh()
    
    def OnEnableTry(self,event):
        self.EnableTry()
        
    def EnableTry(self):
        self.tryzmt=False
        self.btntry.Enable()
        self.btntry.SetValue(self.tryzmt)
        self.EnableApply()
                
    def OnGetSelectedAtom(self,event):
        self.GetSelectedAtom()
                 
    def GetSelectedAtom(self):
        nsel,atmlst=self.model.ListSelectedAtom()
        if len(atmlst) <= 0:
            mess='No atom is selected'
            lib.MessageBoxOK(mess,'ZMatrixViewer(GetSelectedAtom)')
            return
        if len(atmlst) == 1:           
            iatm=atmlst[0]           
            atmlst=[iatm]
            if iatm >= 1: atmlst.append(self.zpnt[iatm][0]-1)
            if iatm >= 2: atmlst.append(self.zpnt[iatm][1]-1)
            if iatm >= 3: atmlst.append(self.zpnt[iatm][2]-1)
            try: idsp=self.displst.index(iatm)
            except:
                mess='Not displayed in table. iatm='+str(iatm)
                lib.MessageBoxOK(mess,'ZMatrixViewer(SetGetSelectedAtom)')
                return
            self.grid.ClearSelection()
            self.grid.SelectBlock(idsp,2,idsp,2)
            if len(atmlst) > 0:
                self.model.SetSelectAll(False)
                self.model.SetSelectAtom0(atmlst,True)
                self.model.DrawLabelAtm(True,0)
                self.model.DrawMol(True)
                
        else:
            self.grid.ClearSelection()
            for iatm in atmlst:
                try: idsp=self.displst.index(iatm)
                except: continue
                self.grid.SelectBlock(idsp,2,idsp,2,addToSelected=True)

        self.grid.MakeCellVisible(idsp,0)
    
    def OnCellLeftClick(self,event):
        selectedrow=event.GetRow()
        if selectedrow >= len(self.displst): return
        
        self.selectedrow=selectedrow        
        self.selectedcol=event.GetCol()
        self.grid.SelectBlock(self.selectedrow,2,self.selectedrow,2)
        self.grid.SetGridCursor(self.selectedrow,self.selectedcol)
        #
        atmlst=[]
        iatm=self.grid.GetCellValue(self.selectedrow,2)
        iatm=int(iatm); atmlst.append(iatm-1)
        #        
        if iatm == 1: cols=[]
        elif iatm == 2: cols=[4]
        elif iatm == 3: cols=[4,6]
        else: cols=[4,6,8]
        if len(cols) > 0:
            for i in cols:
                atmi=self.grid.GetCellValue(self.selectedrow,i)
                atmlst.append(int(atmi)-1)
        # select atoms in mdlwin
        #if len(atmlst) > 0:
        self.model.SetSelectAll(False)
        self.model.SetSelectAtom0(atmlst,True)
        self.model.DrawLabelAtm(True,0)
        self.model.DrawMol(True)
    
    def ConvertZVarDic(self,zvardic,messout=False):
        mess='Z-matrix variable names were changed'
        if messout: self.model.ConsoleMessage(mess)
        vardic={}
        for keynam,varnam in zvardic.iteritems(): 
            if vardic.has_key(varnam):
                keyvar=vardic[varnam]
                iatm1,iprm1=self.UnPackKeyNam(keynam)
                iatm2,iprm2=self.UnPackKeyNam(keyvar)
                if iatm1 < iatm2: vardic[varnam]=keynam
            else: vardic[varnam]=keynam
        for keynam,varnam in zvardic.iteritems():
            oldvarnam=varnam
            keyvar=vardic[varnam]
            iatm,iprm=self.UnPackKeyNam(keyvar)
            newvarnam=self.vsbl[iprm]+('%04d' % (iatm+1)) 
            zvardic[keynam]=newvarnam
            if messout: 
                self.model.ConsoleMessage('   '+oldvarnam+' -> '+newvarnam)
        return zvardic
    
    def MakeZMData(self):
        if self.model.mol == None:
            mess='No molecule data. Created a new molecule.'
            lib.MessageBoxOK(mess,'ZMatrixEditor(MakeZMData)')
            self.NewTable(False)
            return
        else:
            self.changeprmdic={}; self.activedic={}; self.chnagepntdic={}            
            self.changeatmnam={}
            self.changeresdat={}
            self.changeelm={}

            self.zmtpnt=self.model.mol.zmtpnt
            
            self.activedic=copy.deepcopy(self.model.mol.zactivedic)
            self.zvardic=copy.deepcopy(self.model.mol.zvardic)
            # rename variables
            if len(self.zvardic) > 0:
                self.zvardic=self.ConvertZVarDic(self.zvardic)
            #
            self.zelm,self.zpnt,self.zprm=lib.CCToZM(self.model.mol,
                                                     zmtpnt=self.zmtpnt)
            self.natm=len(self.zelm)
            self.resdat=[]; self.atmnam=[]
            for atom in self.model.mol.atm:
                if atom.elm == 'XX': continue
                atmnam=atom.atmnam #.replace(' ','_',4)
                self.atmnam.append(atmnam)
                self.resdat.append(lib.ResDat(atom))
            self.RenameGroup('base')
            #self.zmtdic=self.mol.zmtdic
            self.zelmsav=copy.deepcopy(self.zelm)
            self.zpntsav=copy.deepcopy(self.zpnt)
            self.zprmsav=copy.deepcopy(self.zprm)
            self.atmnamsav=copy.deepcopy(self.atmnam)
            self.resdatsav=copy.deepcopy(self.resdat)
            self.activedicsav=copy.deepcopy(self.activedic)
            self.zvardicsav=copy.deepcopy(self.zvardic)
            #self.savzmtdic=copy.deepcopy(self.zmtdic)
            # activedic
            #for keynam, val in self.zmtdic.iteritems():
            #    if val[1]: self.activedic[keynam]=True
            #
            self.model.FitToScreen(True,True)
            
    def SetDataToGridTable(self):
        #
        if len(self.zelm) == 0:
            self.grid.SetCellValue(0,2,'1')
            self.EnabelCellChange()
            return
        #
        self.grid.ClearGrid()
        nrow=len(self.displst)
        #
        ncol=10; prmcoldic={0:5,1:7,2:9}
        ff83='%8.3f'; ff82='%8.2f'
        for i in range(len(self.displst)): #range(nrow):
            iatm=self.displst[i]
            items=[]
            items.append(self.atmnam[iatm])
            items.append(self.resdat[iatm])
            items.append(str(iatm+1))
            items.append(self.zelm[iatm])
            # p1,prm1,p2,prm2,p3,prm3
            for j in range(3):
                items.append(str(self.zpnt[iatm][j]+1))
                keynam=str(iatm)+':'+str(j)
                if self.IsIndependentVar(keynam,self.zvardic):
                    if self.zpnt[iatm][j] >= 0:
                        items.append(ff83 % (self.zprm[iatm][j]))
                    else: items.append('')
                else: items.append(self.zvardic[keynam])
            if iatm == 0: mcol=4
            elif iatm == 1: mcol=6
            elif iatm == 2: mcol=8
            else: mcol=ncol
            for k in range(mcol): self.grid.SetCellValue(i,k,items[k])
        # cell text color
        self.SetCellColor([],[])   
        # enable cell change
        self.EnabelCellChange()
        
        self.grid.Refresh()
    
    def EnabelCellChange(self):
        nrow=len(self.zelm) #len(self.model.mol.atm)
        ndisp=len(self.displst)
        if ndisp == 0: ndisp=1

        for i in range(ndisp):
            for j in range(10): self.grid.SetReadOnly(i,j,isReadOnly=False)
        # disable columns 2-3
        for i in range(ndisp):
            self.grid.SetReadOnly(i,2,isReadOnly=True)
                
    def CreateGrid(self):
        #
        #self.grid.ClearGrid()
        nrow=len(self.zelm)
        if nrow == 0: nrow=1
        ncol=10
        self.grid.CreateGrid(nrow,ncol)
        self.grid.SetColSize(0,40) # atmnam
        self.grid.SetColSize(1,70) # resdat
        self.grid.SetColSize(2,50) # seq number
        self.grid.SetColSize(3,30) # elm
        width1=50; width2=60
        self.grid.SetColSize(4,width1) # p0
        self.grid.SetColSize(5,width2) # length
        self.grid.SetColSize(6,width1) # p1
        self.grid.SetColSize(7,width2) # bond angle
        self.grid.SetColSize(8,width1) # p2
        self.grid.SetColSize(9,width2) # torsion
        for i in range(nrow): self.grid.SetRowSize(i,22)
     
    def NewTable(self,panel=False):
        self.ClearParams()
        #
        self.model.NewMolecule()
        atom=molec.Atom(self.model.mdlwin)
        atom.seqnmb=0; atom.elm=' X'; atom.cc=[0.0,0.0,0.0]
        atom.SetAtomParams(atom.elm)
        self.model.mol.atm.append(atom)
        #
        self.zelm.append(' X')
        self.zpnt.append([-1,-1,-1])
        self.zprm.append(['','',''])
        self.atmnam.append('')
        self.resdat.append('')
        self.displst=range(len(self.zelm))
        if panel:
            try: self.grid.ClearGrid()
            except: pass
            try: self.panel.Destroy()
            except: pass
            self.CreatePanel()
            self.CreateGrid()
            self.SetDataToGridTable()
            self.EnabelCellChange()

        self.model.DrawMol(True)
     
    def SaveZMTFile(self):
        name=self.model.mol.name
        wcard='zmt file(*.zmt)|*.zmt;all(*.*)|*.*'
        filename=lib.GetFileName(None,wcard,'w',True) #,defname)
        if len(filename) <= 0: return
        title=name+' ... Created by FU at '+lib.DateTimeText()
        #const.CONSOLEMESSAGE('SaveZMTFile. filename='+filename)
        if self.symboliczmt: # and len(self.zvardic) <= 0:
            for i in range(len(self.zelm)):
                if i == 0: continue
                if i == 1: mcol=1
                elif i == 2: mcol=2
                else: mcol=3
                for j in range(mcol):
                    keynam=str(i)+':'+str(j)
                    if self.zvardic.has_key(keynam):    
                        self.zvardic[keynam]=self.vsbl[j]+'%04d' % (i+1)      
        # write
        rwfile.WriteZMTFile(filename,title,self.zelm,self.zpnt,self.zprm,
                               zvardic=self.zvardic,activedic=self.activedic,
                               seqnmb=self.addseqnmb)
                            
    def HelpDocument(self):
        helpname=self.winlabel
        self.model.helpctrl.Help(helpname)
    
    def Tutorial(self):
        helpname=self.winlabel
        self.model.helpctrl.Tutorial(helpname)
    
    def RelatedFunctions(self):
        menulst=["CloseMe","","RotCnfEditor","ZmtCnfEditor",
                 "TINKER",'GAMESS','OneByOneViewer']
        relwin=subwin.RelatedFunctions(self,-1,self.model,menulst) #,tipslst)

    def OnTipString(self,event):
        tipdic={'Reset':'Reset mol object to the current one in mdlwin',
                'Deselect':'Reset selection: restore all atom data',
                'DeselectCell':'Deselect cells'}
        obj=event.GetEventObject()
        label=obj.GetLabel() #GetName()
        if tipdic.has_key(label): mess=tipdic[label]
        else: mess='No description'
        tipstr=subwin.TipString(obj,mess)

    def PopupMenuItems(self):
        self.extractmenu=['','all',
                          '---',
                          'seqnmb','atmnam','resdat','elm',
                          '---',
                          'length','angle','torsion',
                          '---',
                          'selected atoms','show atoms',
                          '---',
                          'changed','active',
                          '---',
                          'variable name'
                          ]
        self.extracttip=['','restore all atoms','',
                         'extract atoms by sequence number of atoms(need input)',
                         'extract atoms by atom name(need input)',
                         'extract atoms by resudue data(resdue name:residure number:chain name, need input)',
                         'extrac atoms by element name(need input)',
                         '',
                         'extract atoms by bond length range(need input)',
                         'extract atoms by bond angle range(need input)',
                         'extract atoms by torsion angle range(need input)',
                         '',
                         'extract atoms selected in mdlwin',
                         'extract atoms with "show" attribute in mdlwin',
                         '',
                         'extract atoms which have changed attribute',
                         'extract atoms which have active attribute',
                         '',
                         'extract atoms having "variable name"(need input)'
                         ]
        self.cmd1menu=['close me',
                      '---',
                      'reset all params',
                      'reset all actives',
                      '---',
                      'reset all variable names',
                      '---',
                      'plot length','plot angle','plot torsion',
                     ]
        self.cmd1tip=[]
        self.cmd2menu=['close me',
                      '---',
                      'get selected atom',
                      '---',
                      'create new molecule',
                      '---',
                      'select atoms','show atoms','reset show atoms',
                      '---',
                      'set rotation axis','del rotation axis',
                      ]
        self.cmd2tip=[]
        #
        self.cellprmmenu=['close me',
                          '---','set active','set freeze',
                          '---','reset value','reset variable name']
        self.cellprmtip=[]

        self.cellpntmenu=['close me','---','reset value']
        self.cellpnttip=[]
        #
        self.cellitmmenu=['close me','---','reset value']
        self.cellitmtip=[]
        #
        self.prmcolcmdmenu=['close me',
                '---',
                'set active to selected cells',
                'reset active in selected cells',
                'reverse active in selected cells',
                 '---',
                'set active all',
                 'reset all active',
                 'reverse all active',
                 '---',
                 'reset params in selected cells',
                 'rest all params',
                 #'---',
                 #'replace variable name in selected cells',
                 #'replace all variable names',
                 #'---',
                 #'set std value in selected cells'
                 ]
        self.prmcolcmdtip=[]
        # apply to pnts, atmnam,resdat,elm
        self.colcmdmenu=['close me',
                '---',
                 'reset selected cells',
                 'reset all',
                 '---','replace selected cells','replace all'
                 ]
        self.colcmdtip=['',
                        '',
                        ]        
        #
        self.rowcmdmenu=['close me','--',
                         'insert upper',
                         'insert lower',
                         '---',
                         'delete']
        self.rowcmdtip=[]
        
    def MenuTip(self,event):
        self.model.ConsoleMessage('Test of MenuTip')
            
    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        #iid=wx.NewId()
        #menuitem=wx.MenuItem(submenu,-1,text='SAVE ZMTFILE')
        submenu.Append(-1,'New table','Create a new grid table')
        submenu.AppendSeparator()
        submenu.Append(-1,'Save zmtfile','Save z-matrix file')
        #submenu.AppendItem(menuitem)
        #menuitem=submenu.GetMenuItems()
        #menuitem[0].SetHelp('Help message of save zmtfile')
        #menuitem.Bind(wx.EVT_RIGHT_DOWN,self.MenuTip)
        submenu.Append(-1,'Add sequence number in zmtfile','',
                       kind=wx.ITEM_CHECK)
        ###submenu.Append(-1,'Symbolic Z-Matrix','',kind=wx.ITEM_CHECK)
        submenu.AppendSeparator()
        submenu.Append(-1,'Sync with one-by-one selector','',
                       kind=wx.ITEM_CHECK)
        submenu.AppendSeparator()
        submenu.Append(-1,'Reset table','Reset grid table')        
        submenu.AppendSeparator()
        submenu.Append(-1,'Close','Close the window')        
        menubar.Append(submenu,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        #submenu.AppendSeparator()
        #submenu.Append(-1,'Related functions','Execute related functions')        
        menubar.Append(submenu,'Help')
        #
        return menubar
    
    def AddSequenceNumber(self,on):
        self.addseqnmb=on
        
    def SymbolicZMTFlag(self,on):
        self.symboliczmt=on
    
    def SyncWithOneByOne(self,on):
        self.synconebyone=on
        if not on:
            self.displst=range(len(self.zelm))
            self.Resize()
             
    def OnMenu(self,event):
        """ Menu event handler
        
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        self.ExecMenuCommand(item,bChecked)

    def ExecMenuCommand(self,item,bChecked):
        # File menu items
        if item == 'New table': self.NewTable(True)
        elif item == 'Save zmtfile': self.SaveZMTFile()
        elif item == 'Add sequence number in zmtfile': 
            self.AddSequenceNumber(bChecked)
        elif item == 'Symbolic Z-Matrix': self.SymbolicZMTFlag(bChecked)
        elif item == 'Sync with one-by-one selector': 
            self.SyncWithOneByOne(bChecked)
        elif item == 'Reset table': self.ResetTable()
        elif item == "Close": self.OnClose(1)
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == 'Related functions': self.RelatedFunctions()

class AddHydrogen_Frm(wx.Frame):
    def __init__(self,parent,id,model,winpos,scrdir='',winlabel=''):
        self.title='Hydrogen addition'
        #pltfrm=lib.GetPlatform()
        #if pltfrm == 'WINDOWS': winsize=lib.WinSize((290,220)) #400) #366) #(155,330) #(155,312)
        #else: winsize=(320,250)
        winsize=lib.WinSize([320,295])
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)      
        #
        self.parent=parent
        self.mdlwin=parent
        self.model=model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.winlabel=winlabel
        self.helpname='AddHydrogen'
        self.scrdir=scrdir
        if len(self.scrdir) <= 0: self.scrdir=self.setctrl.GetDir('Scratch')
        if len(self.winlabel) <= 0: self.winlabel='AddHydrogen'
        self.winctrl.SetWin(self.winlabel,self)
        #xxself.ctrlflag=model.ctrlflag
        # attach fu icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.Initialize()
        #
        self.CreatePanel()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
        
    def Initialize(self):
        self.molnam=self.model.mol.name #wrkmolnam
        self.SetTitle(self.title+' ['+self.molnam+']')
        #        
        self.pdbfile=self.model.mol.inpfile
        self.sav=self.model.mol.CopyAtom()
        self.tmpfile=''
        pid=self.model.pid
        self.tmpfile='fmopdb-addh'+str(pid)+'.pdb'
        self.tmpfile=os.path.join(self.scrdir,self.tmpfile)
        self.model.mol.WritePDBMol(self.tmpfile,"","",True) # True: save conect data
        self.model.mol.inpfile=self.tmpfile
        self.model.mol=molec.Molecule(self.model)
        self.model.mol.BuildFromPDBFile(self.tmpfile)
        self.model.mol.name=self.molnam
        #
        self.applied=False
        #
        self.RecoverAtomData()
        self.pdbfile=self.tmpfile
    
    def CreatePanel(self):
        # popup control panel
        self.size=self.GetClientSize()
        hbtn=25; hcb=const.HCBOX
        xpos=0; ypos=0; xsize=self.size[0]; ysize=self.size[1]
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        w=self.size[0]; h=self.size[1]
         # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        yloc=10

        wx.StaticText(self.panel,-1,"Keep existing hydrogens?",pos=(10,yloc),
                      size=(150,18)) 
        self.rbtkep=wx.RadioButton(self.panel,-1,"Yes",pos=(160,yloc),
                                   size=(40,18),
                                   style=wx.RB_GROUP)
        self.rbtrmv=wx.RadioButton(self.panel,-1,"No",pos=(210,yloc),
                                   size=(40,18))
        self.rbtrmv.SetValue(True)
        """
        self.ckbkep=wx.CheckBox(self.panel,-1,'Keep existing hydrogens',pos=(10,yloc))
        self.ckbkep.SetToolTipString('Keep existing hydrogens')
        self.ckbkep.SetValue(False)
        self.ckbmis=wx.CheckBox(self.panel,-1,'List missing atoms',pos=(200,yloc))
        self.ckbmis.SetToolTipString('List missing atoms (PDB data only)')
        self.ckbmis.SetValue(False)
        """
        
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        self.ckbpep=wx.CheckBox(self.panel,-1,'Polypeptides',pos=(10,yloc))
        self.ckbpep.SetValue(True)
        yloc += 25; xloc=10
        wx.StaticText(self.panel,-1,"N-terminus:",pos=(xloc+10,yloc),
                      size=(70,18)) 
        self.rbtntr=wx.RadioButton(self.panel,-1,"leave as is",
                             pos=(xloc+85,yloc),size=(80,18),style=wx.RB_GROUP)
        self.rbtnh3=wx.RadioButton(self.panel,-1,"NH3+",pos=(xloc+175,yloc),
                                   size=(50,18))
        self.rbtnh2=wx.RadioButton(self.panel,-1,"NH2",pos=(xloc+235,yloc),
                                   size=(50,18))
        #self.rbtnme=wx.RadioButton(self.panel,-1,"NME",pos=(xloc+295,yloc),size=(50,18))
        self.rbtnh3.SetValue(True)
        
        yloc += 25
        wx.StaticText(self.panel,-1,"C-terminus:",pos=(xloc+10,yloc),
                      size=(70,18)) 
        self.rbtctr=wx.RadioButton(self.panel,-1,"leave as is",
                             pos=(xloc+85,yloc),size=(80,18),style=wx.RB_GROUP)
        self.rbtcoo=wx.RadioButton(self.panel,-1,"COO-",pos=(xloc+175,yloc),
                                   size=(50,18))
        #self.rbtcoh=wx.RadioButton(self.panel,-1,"COH",pos=(235,yloc),size=(50,18))
        self.rbtcooh=wx.RadioButton(self.panel,-1,"COOH",pos=(xloc+235,yloc),
                                    size=(55,18))
        #self.rbtace=wx.RadioButton(self.panel,-1,"ACE",pos=(xloc+295,yloc),size=(50,18))
        self.rbtcoo.SetValue(True)
        yloc += 25
        wx.StaticText(self.panel,-1,"HIS residue:",pos=(xloc+10,yloc),
                      size=(70,18))
        self.rbthe1=wx.RadioButton(self.panel,-1,"HIE",pos=(xloc+85,yloc),
                                   size=(40,18),
                                   style=wx.RB_GROUP)
        self.rbthe1.SetToolTipString('Attach at epsilon N')
        self.rbthd1=wx.RadioButton(self.panel,-1,"HID",pos=(xloc+135,yloc),
                                   size=(40,18))
        self.rbthd1.SetToolTipString('Attach at delta N')
        self.rbthpr=wx.RadioButton(self.panel,-1,"HIP",pos=(xloc+185,yloc),
                                   size=(40,18))
        mess='Attach at delta N and epsilon N (protonated form)'
        self.rbthpr.SetToolTipString(mess)
        #self.rbtauto=wx.RadioButton(self.panel,-1,"auto",pos=(xloc+235,yloc),size=(40,18))
        #self.rbtauto.SetToolTipString('Determine appropriate form base-on hydrogen bonds')
        self.rbthpr.SetValue(True)
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        #wx.StaticText(self.panel,-1,"Waters:",pos=(10,yloc+8),size=(70,18))
        yloc += 8
        self.ckbwat=wx.CheckBox(self.panel,-1,'Waters:',pos=(10,yloc))
        self.ckbwat.SetValue(True)

        self.rbtwdel=wx.RadioButton(self.panel,-1,"delete",pos=(95,yloc),
                                    size=(60,18),style=wx.RB_GROUP)
        self.rbtwadd=wx.RadioButton(self.panel,-1,"add hydrogens",
                                    pos=(165,yloc),size=(100,18))
        self.rbtwadd.SetValue(True)

        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
                
        yloc += 8
        self.ckbrest=wx.CheckBox(self.panel,-1,'Others:    use',pos=(10,yloc))
        self.ckbrest.SetValue(True)

        self.rbtrstfrm=wx.CheckBox(self.panel,-1,"frame data",pos=(115,yloc),
                                   size=(80,18))
        self.rbtrstfrm.SetToolTipString('Use frame data')
        self.rbtrstlen=wx.CheckBox(self.panel,-1,"bond length",pos=(205,yloc),
                                   size=(90,18))
        #self.rbtrstlen.SetValue(False)
        mess='Attach hydrogens based-on bond length'
        self.rbtrstlen.SetToolTipString(mess)
        self.rbtrstlen.SetValue(False)
        self.rbtrstfrm.SetValue(True)
        
        yloc += 25
        # Apply, OK, Cancel buttons       
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        btnundo=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(70,yloc),
                          size=(50,20))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        btnaply=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(140,yloc),
                          size=(50,20))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        btncls=wx.Button(self.panel,wx.ID_ANY,"Close",pos=(210,yloc),
                         size=(50,20))
        btncls.Bind(wx.EVT_BUTTON,self.OnClose)

    def RecoverAtomData(self):
        for i in xrange(len(self.model.mol.atm)):
            self.model.mol.atm[i]=self.sav[i]
    
    def OnReset(self,event):
        self.Initialize()
        try: 
            self.panel.Destroy()
            self.CreatePanel()
        except: pass
            
    def Apply(self):
        def StartMessage(mess):
            mess=mess+' at '+lib.DateTimeText()
            self.model.Message2(mess)

        # save mol.atm for undo
        self.model.SaveMol()  
        # keep existing hydrogens
        if self.rbtkep.GetValue(): keep=True
        elif self.rbtrmv.GetValue(): keep=False
        else: keep=False
        # polypeptide
        polypep=self.ckbpep.GetValue()
        # n-term
        if self.rbtntr.GetValue(): nterm=2 # leave as is
        if self.rbtnh3.GetValue(): nterm=0 # NH3+
        if self.rbtnh2.GetValue(): nterm=1 # NH2
        #if self.rbtnme.GetValue(): nterm=-1 # NME
        # c-term
        if self.rbtctr.GetValue(): cterm=3 # leave as is
        if self.rbtcoo.GetValue(): cterm=1 # COO-
        #if self.rbtcoh.GetValue(): cterm=2 # COH
        if self.rbtcooh.GetValue(): cterm=2 # COOH
        #if self.rbtace.GetValue(): cterm=-1 # ACE
        # his
        if self.rbthe1.GetValue(): his=2 # E2
        if self.rbthd1.GetValue(): his=1 # D1
        if self.rbthpr.GetValue(): his=0 # protonate
        #if self.rbtauto.GetValue(): his=-1 # Auto
        # water
        water=self.ckbwat.GetValue()
        if self.rbtwdel.GetValue(): wat=0 # delete
        if self.rbtwadd.GetValue(): wat=1 # add hydrogens
        # the others
        others=self.ckbrest.GetValue()
        if self.rbtrstfrm.GetValue(): frm=1 # use frame data
        else: frm=0
        if self.rbtrstlen.GetValue(): bln=1 # use bond length
        else: bln=0
        #
        atmlst=range(len(self.model.mol.atm)) #self.model.ListTargetAtoms()
        if not keep: self.model.DeleteHydrogens(atmlst)
        fmoutil=False
        #
        StartMessage('AddHydrogen starts')
        #
        try: 
            #self.model.mdlwin.ResetBusyIndicator(1)
            self.model.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass

        if polypep:
            StartMessage('AddHydrogen to polypeptides starts')
            atmlst=range(len(self.model.mol.atm))
            
            const.CONSOLEMESSAGE('len(atmlst)='+str(len(atmlst)))
            atmlst=self.model.ListAAResidueAtoms(atmlst)
            const.CONSOLEMESSAGE('len(atmlst)='+str(len(atmlst)))
            self.model.AddHydrogenToAAResidue(atmlst=atmlst,drw=True)
            """
            if self.model.setctrl.GetParam('use-fmoutil'):
                test=True
                #try:
                if test:
                    natm=self.model.AddHydrogenToAAByFMOPDB(self.pdbfile,
                                            keep,nterm,cterm,his,wat,drw=True)
                    fmoutil=True
                else:
                #except:
                    mess='Trying python code ...'
                    self.model.ConsoleMessage(mess)
                    self.AddHydrogenToAAResidue(atmlst=atmlst,drw=True)
                    #nhtotal,nhchainlst=\
                    #                self.model.mol.AddHydrogenToProtein(atmlst)   
            else: 
                self.AddHydrogenToAAResidue(atmlst=atmlst,drw=True)
                #nhtotal,nhchainlst=\
                #                    self.model.mol.AddHydrogenToProtein(atmlst)
            """
            StartMessage('AddHydrogen to polypeptides ends')        
        #
        if water:
            StartMessage('AddHydrogen to waters starts')
            self.model.Message('AddH to waters',1,'')
            atmlst=range(len(self.model.mol.atm))
            #atmlst=self.model.ListWaterAtoms(atmlst)
            nwat=self.model.mol.CountWater([])
            #try: self.model.mdlwin.BusyIndicator('On','Adding hydrogens...')
            #except: pass
            if water and wat == 1 and nwat > 0:
                self.model.mol.AddHydrogenToWaterMol(atmlst)
            elif water and wat == 0: self.model.mol.DelWater(atmlst)
            StartMessage('AddHydrogen to waters ends')
        if others:
            atmlst=range(len(self.model.mol.atm))
            atmlst=self.model.ListNonAAResidueAtoms(wat=False,atmlst=atmlst)
            nres=len(atmlst) #self.model.mol.CountNonAARes(False)
            #try: self.model.mdlwin.BusyIndicator('On','Adding hydrogens...')
            #except: pass
            if nres > 0:
                self.model.Message('AddH to non-peptide',1,'')
                if frm == 1:
                    StartMessage('AddHydrogens use frame starts')
                    self.model.AddHydrogenUseFrameData(atmlst=atmlst,drw=True)
                    StartMessage('AddHydrogens use frame starts')
                if bln == 1:
                    StartMessage('AddHydrogens use bond length starts')
                    atmlst=range(len(self.model.mol.atm))
                    atmlst=self.model.ListNonAAResidueAtoms(wat=False,
                                                            atmlst=atmlst)
                    self.model.AddHydrogenUseBondLength(drw=True,
                                                        atmlst=atmlst)
                    StartMessage('AddHydrogens use bond length ends')
                #elif frm == 1 and bln == 1:
                #    atmlst=self.model.ListNonAAResidueAtoms(wat=False)
                #    self.model.AddHydrogenUseBondLength(drw=False,
                #                                        atmlst=atmlst)
        #        
        self.model.DrawMol(True)
        self.model.ConsoleMessage('\n')
        # !!! mol object has changed !!!
        self.model.molctrl.ResetMol(self.model.mol)
        #
        try: self.model.mdlwin.BusyIndicator('Off')
        except: pass
        StartMessage('AddHydrogen ends')
        
    def OnApply(self,event):
        self.Apply()
        self.applied=True
                   
    def OnUndo(self,event):
        self.model.mol.atm=self.sav #copy.deepcopy(self.sav)        
        self.model.RecoverMol()
        self.applied=False
        self.model.DrawMol(True)
        
    def OnClose(self,event):
        try: self.winctrl.Close(self.winlabel)
        except: pass
        try: os.remove(self.tmpfile)
        except: pass
        self.Destroy()
    
    def OnNotify(self,event):
        #if event.jobid != self.winlabel: return
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles': self.OnReset(1)
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
    
    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        submenu.Append(-1,'View summary','View message log')
        submenu.Append(-1,'View message log','View message log')
        submenu.AppendSeparator()
        submenu.Append(-1,'Close','Close the panel')
        menubar.Append(submenu,'File')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        #submenu.AppendSeparator()
        #submenu.Append(-1,'Related functions','Execute related functions')
        menubar.Append(submenu,'Help')
        #
        return menubar

    def OnMenu(self,event):
        """ Menu event handler
        
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # File
        if item == 'View summary': self.model.SummaryOfAddHydrogens()         
        elif item == 'View message log': self.model.ViewMessageLog()
        elif item == 'Close': self.OnClose(1)
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
         

class WaterBox_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos=[],winlabel='BoxWter'):
        self.title='Water box'
        #if lib.GetPlatform() == 'WINDOWS': winsize=(290,320)
        #else: winsize=(270,310)
        winsize=lib.MiniWinSize([290,340])
        if len(winpos) <= 0:
            #mdlwinpos=parent.GetPosition()
            #mdlwinsize=parent.GetSize()
            #winpos=[mdlwinpos[0]+mdlwinsize[0],mdlwinpos[1]+50]
            winpos=lib.WinPos(parent.mdlwin)
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,
                    size=winsize,style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        #
        self.parent=parent
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.winctrl=self.model.winctrl
        self.setctrl=self.model.setctrl
        self.winlabel=winlabel
        self.winlabel=winlabel
        self.winctrl.SetWin(self.winlabel,self)
        self.helpname='BoxWater'

        #xxself.ctrlflag=model.ctrlflag
        #molnam=model.mol.name #wrkmolnam
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.watnam='WAT'
        #self.watfile=self.model.exedir+'/data/water-box.pdb'
        self.watfile=self.setctrl.GetFile('FUdata','water-box.pdb')
        if not os.path.exists(self.watfile):
            mess='WaterBox(init):"water-box.pdb" file is not found in '
            mess=mess+'FUDATASET/FUdata/\n'
            mess=mess+'Unable to continue.'
            lib.MessageBoxOK(mess,"WaterBox_Frm")
            self.OnClose(1)
        #
        self.Initialize()
        #
        self.CreatePanel()
         #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
        
        self.Show()
        
    def Initialize(self):
        molnam=self.model.mol.name #wrkmolnam
        self.SetTitle(self.title+' ['+molnam+']')
        self.sav=self.model.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        #
        # default values
        self.xsize=0.0; self.ysize=0.0; self.zsize=0.0
        self.xdis0=6.0; self.ydis0=6.0; self.zdis0=6.0; self.cdis0=2.5
        #
        self.xdis=self.xdis0; self.ydis=self.ydis0; self.zdis=self.zdis0
        self.cdis=self.cdis0        # create panel and set widget state
        self.thick0=6.0
        self.thick=self.thick0
        self.nna=0; self.ncl=0
        self.solutechg=0
        #
        self.xsize=0; self.ysize=0; self.zsize=0
        self.wat=None
        self.xwat=0; self.ywat=0; self.zwat=0
        self.pdbwat=[]; self.watelmcc=[]
        #
        self.rot=[]; self.com=[]
        self.GetSoluteSize()
        #
        self.xbox=self.xsize+2.0*self.xdis
        self.ybox=self.ysize+2.0*self.ydis
        self.zbox=self.zsize+2.0*self.zdis      
        box=[self.xbox,self.ybox,self.zbox]
        self.xyzbox=max(box)
        #
        self.applied=False
    
    def CreatePanel(self):
        self.size=self.GetClientSize()
        hbtn=25; hcb=const.HCBOX
        # popup control panel
        xpos=0; ypos=0; xsize=self.size[0]; ysize=self.size[1]
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        w=self.size[0]; h=self.size[1]
        self.dispxloc=5; self.dispyloc=5
        self.DispSoluteSize()
        self.DispSoluteCharge()
        if self.solutechg > 0: self.ncl=self.solutechg
        elif self.solutechg < 0: self.nna=-self.solutechg
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc=44 #22
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 5
        self.rbtbox=wx.RadioButton(self.panel,wx.ID_ANY,'Box waters',
                                   pos=(5,yloc),style=wx.RB_GROUP)
        self.rbtbox.Bind(wx.EVT_RADIOBUTTON,self.OnRadioButton)
        ylocx=yloc+108
        self.rbtshl=wx.RadioButton(self.panel,-1,
                                 'Shell waters.  thickness (A):',pos=(5,ylocx))
        self.rbtshl.Bind(wx.EVT_RADIOBUTTON,self.OnRadioButton)
        self.rbtshl.SetValue(True)
        # box sizes
        yloc += 20
        self.rbtbox1=wx.RadioButton(self.panel,-1,"cubic box length (A),",
                                    pos=(25,yloc),style=wx.RB_GROUP)
        self.rbtbox1.Bind(wx.EVT_RADIOBUTTON,self.OnRadioButton)
        yloc += 20
        wx.StaticText(self.panel,-1,"x:",pos=(50,yloc+2),size=(10,18)) 
        self.tcldx1=wx.TextCtrl(self.panel,-1,str(self.xyzbox),pos=(65,yloc),
                                size=(40,18))
        wx.StaticText(self.panel,-1,"y:",pos=(120,yloc+2),size=(10,18)) 
        self.tcldy1=wx.TextCtrl(self.panel,-1,str(self.xyzbox),pos=(135,yloc),
                                size=(40,18))
        wx.StaticText(self.panel,-1,"z:",pos=(190,yloc+2),size=(10,18)) 
        self.tcldz1=wx.TextCtrl(self.panel,-1,str(self.xyzbox),pos=(205,yloc),
                                size=(40,18))
        yloc += 22
        self.rbtbox2=wx.RadioButton(self.panel,-1,
                    "distance between solute and box wall (A),",pos=(25,yloc))
        self.rbtbox2.Bind(wx.EVT_RADIOBUTTON,self.OnRadioButton)
        yloc += 20
        wx.StaticText(self.panel,-1,"x:",pos=(50,yloc+2),size=(10,18)) 
        self.tcldx2=wx.TextCtrl(self.panel,-1,str(self.xdis),pos=(65,yloc),
                                size=(40,18))
        #self.tclpnt1.Bind(wx.EVT_TEXT,self.OnP1Input)
        wx.StaticText(self.panel,-1,"y:",pos=(120,yloc+2),size=(10,18)) 
        self.tcldy2=wx.TextCtrl(self.panel,-1,str(self.ydis),pos=(135,yloc),
                                size=(40,18))
        #self.tclpnt2.Bind(wx.EVT_TEXT,self.OnP2Input)
        wx.StaticText(self.panel,-1,"z:",pos=(190,yloc+2),size=(10,18)) 
        self.tcldz2=wx.TextCtrl(self.panel,-1,str(self.zdis),pos=(205,yloc),
                                size=(40,18))
        # shell thickness
        yloc += 25
        self.tclshl=wx.TextCtrl(self.panel,-1,str(self.thick),pos=(200,yloc-2),
                                size=(40,18))
        yloc += 22
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 5
        wx.StaticText(self.panel,-1,"Minimum heavy atom distance between",
                      pos=(5,yloc),size=(250,18))
        yloc=yloc+22
        wx.StaticText(self.panel,-1,"solute and water molecule (A):",
                      pos=(30,yloc),size=(190,18)) 
        self.tcldc=wx.TextCtrl(self.panel,-1,str(self.cdis),pos=(230,yloc-2),
                               size=(40,18))
        yloc += 22
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"Add ions:    Na+",pos=(5,yloc),
                      size=(95,18))
        self.tclpos=wx.TextCtrl(self.panel,-1,str(self.nna),pos=(100,yloc-2),
                                size=(40,18))
        wx.StaticText(self.panel,-1,"Cl-",pos=(155,yloc),size=(20,18))
        self.tclneg=wx.TextCtrl(self.panel,-1,str(self.ncl),pos=(180,yloc-2),
                                size=(40,18))
        yloc += 20; xloc=50
        # Apply, OK, Cancel buttons       
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        btnundo=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(xloc,yloc),
                          size=(45,20))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        btnapl=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(xloc+65,yloc),
                         size=(45,20))
        btnapl.Bind(wx.EVT_BUTTON,self.OnApply)
        ###btnok=wx.Button(self.panel,wx.ID_ANY,"OK",pos=(160,yloc),size=(45,20))
        ###btnok.Bind(wx.EVT_BUTTON,self.OnOK)
        btncl=wx.Button(self.panel,wx.ID_ANY,"Close",pos=(xloc+130,yloc),
                        size=(45,20))
        btncl.Bind(wx.EVT_BUTTON,self.OnClose)
        self.OnRadioButton(1)

    def OnRadioButton(self,event):
        if self.rbtbox.GetValue():
            self.SetRBTShlWater(False); self.SetRBTBoxWater(True)
        else:
            self.SetRBTShlWater(True); self.SetRBTBoxWater(False)

    def SetRBTBoxWater(self,on):
        if on:
            self.rbtbox1.Enable(); self.rbtbox2.Enable()
            if self.rbtbox1.GetValue():
                self.tcldx1.Enable(); self.tcldy1.Enable()
                self.tcldz1.Enable()
                #self.rbtbox2.Disable()
                self.tcldx2.Disable(); self.tcldy2.Disable()
                self.tcldz2.Disable()
            else:
                self.tcldx2.Enable(); self.tcldy2.Enable()
                self.tcldz2.Enable()
                #self.rbtbox1.Disable()
                self.tcldx1.Disable(); self.tcldy1.Disable()
                self.tcldz1.Disable()
        else:
            self.rbtbox1.Disable()
            self.tcldx1.Disable(); self.tcldy1.Disable(); self.tcldz1.Disable()
            self.rbtbox2.Disable()
            self.tcldx2.Disable(); self.tcldy2.Disable(); self.tcldz2.Disable()
            
    def SetRBTShlWater(self,on):
        if on:
            self.tclshl.Enable()
            self.SetRBTBoxWater(False)
        else:
            self.tclshl.Disable()
            self.SetRBTBoxWater(True)
           
    def DispSoluteSize(self):
        x= "%8.2f" % self.xsize; y="%8.2f" % self.ysize; z="%8.2f" %self.zsize
        x=x.strip(); y=y.strip(); z=z.strip()
        mess="Solute size: x="+x+", y="+y+", z="+z
        xloc=self.dispxloc; yloc=self.dispyloc
        wx.StaticText(self.panel,-1,mess,pos=(xloc,yloc),
                      size=(self.size[0]-xloc-10,18)) 

    def DispSoluteCharge(self):
        self.model.mol.AssignAAResAtmChg()
        self.solutechg=self.model.mol.CountChargeOfAARes([])
        ionchg=self.model.mol.CountIonCharge([])
        self.solutechg += ionchg
        chg= "%4d" % self.solutechg
        mess="Solute charge: "+chg
        xloc=self.dispxloc; yloc=self.dispyloc+20
        wx.StaticText(self.panel,-1,mess,pos=(xloc,yloc),
                      size=(self.size[0]-xloc-10,18)) 
    
    def Apply(self):
        def BusyInd(on):
            try: 
                if on: 
                    self.model.mdlwin.BusyIndicator('On','Water box...')
                else: self.model.mdlwin.BusyIndicator('Off')
            except: pass
        
        if len(self.model.mol.atm) <= 0:
           mess='No solute atoms. Please read a molecule file.' 
           lib.MessageBoxOK(mess,'Water box(Apply)')
           return
        #
        boxwat=0
        BusyInd(True)
        
        if self.rbtbox1.GetValue():
            boxwat=0
            self.xdis=self.tcldx1.GetValue()
            self.ydis=self.tcldy1.GetValue()
            self.zdis=self.tcldz1.GetValue()
        if self.rbtbox2.GetValue():
            boxwat=1
            self.xdis=self.tcldx2.GetValue()
            self.ydis=self.tcldy2.GetValue()
            self.zdis=self.tcldz2.GetValue()
        if self.rbtshl.GetValue():
            boxwat=2
            self.thick=self.tclshl.GetValue()
            self.xdis=self.thick; self.ydis=self.thick
            self.zdis=self.thick
        if boxwat !=2 : self.thick="1000000.0"
        self.cdis=self.tcldc.GetValue()
        # check data
        if not self.xdis.replace('.','').isdigit():
            lib.MessageBoxOK("Wrong data in x distance.","")
            BusyInd(False)
            return          
        if not self.xdis.replace('.','').isdigit():
            lib.MessageBoxOK("Wrong data in y distance.","")
            BusyInd(False)
            return          
        if not self.xdis.replace('.','').isdigit():
            lib.MessageBoxOK("Wrong data in z distance.","")
            BusyInd(False)
            return          
        if not self.cdis.replace('.','').isdigit():
            lib.MessageBoxOK("Wrong data in cavity distance.","")
            BusyInd(False)
            return          
        if self.rbtshl.GetValue():
            if not self.thick.replace('.','').isdigit():
                lib.MessageBoxOK("Wrong data in shell thickness.","")
                BusyInd(False)
                return
            
        self.xdis=float(self.xdis)
        self.ydis=float(self.ydis)
        self.zdis=float(self.zdis)
        self.cdis=float(self.cdis)
        self.thick=float(self.thick)
        #
        if boxwat == 0:
            self.xbox=self.xdis; self.ybox=self.ydis
            self.zbox=self.zdis
        else:
            self.xbox=2.0*self.xdis+self.xsize
            self.ybox=2.0*self.ydis+self.ysize
            self.zbox=2.0*self.zdis+self.zsize
        #???#25Mar2016#self.model.SetWaterBoxDist(self.xdis,self.ydis,self.zdis,self.cdis,
        #                            self.thick)
        if self.cdis >= self.thick or self.cdis >= self.xbox or \
                self.cdis >= self.ybox or self.cdis >= self.zbox:
            mess="Wrong data in cavity radius.\n"
            mess=mess+""
            lib.MessageBoxOK(mess,"")
            BusyInd(False)
            return
        #
        self.nna=int(self.tclpos.GetValue())
        self.ncl=int(self.tclneg.GetValue())
        #
        self.MakeBoxWater()
    
        BusyInd(False)
        
    def OnApply(self,event):
        self.Apply()
        self.applied=True
            
    def XXOnOK(self,event):
        if not self.applied: self.Apply()
        self.OnClose(1)
    
    def OnUndo(self,event):
        self.model.mol.atm=self.sav #copy.deepcopy(self.sav)        
        self.model.FitToScreen(False,True)
        #self.model.DrawMol(True)
        self.applied=False
        
    def OnClose(self,event):
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        #self.MakeModal(False)
        self.Destroy()
    
    def ReplaceWithIons(self):
        nwat=len(self.wat.atm)/3
        nion=max(self.nna, self.ncl)
        lst=[]; ccion=[]; atmdic={}
        if self.nna > 0:
            elm='NA'; atmnam=' NA+'; resnam='NA+'
        elif self.ncl > 0:
            elm='CL'; atmnam=' CL-'; resnam='CL-'
        if nion > 0: 
            for i in xrange(nion):
                ii=int(nwat*numpy.random.random())
                if ii > nwat: ii=nwat-1
                lst.append(3*ii)
                lst.append(3*ii+1)
                lst.append(3*ii+2)
                ccion.append(self.wat.atm[3*ii].cc)
            self.wat.DelAtoms(lst)
            natm=len(self.wat.atm)
            seqnmb=natm
            for i in xrange(nion):
                ion=molec.Atom(self)
                ion.seqnmb=seqnmb+i
                ion.elm=elm; ion.cc=ccion[i]
                ion.atmnam=atmnam; ion.resnam=resnam
                ion.resnmb=i+1
                ion.SetAtomParams(ion.elm)
                #
                self.wat.atm.append(ion)

    def MakeBoxWater(self):
        ###self.RotateMolecule(True) # rotate solute
        mess="Running Add box waters ..."
        self.model.Message(mess,0,'black')
        #
        self.ReadWaterBox()
        self.ExpandWaterBox()
        self.MakeCavityInWater()
        # rotate waters
        self.RotateWaterBox()
        # merge solute and waters
        nwat=len(self.wat.atm)/3
        # replace water molecule(s) with ion(s)
        self.ReplaceWithIons()
         
        #self.RenumberWater()
         
        self.model.MergeMolecule(self.wat.atm,False)
        
        natm=len(self.model.mol.atm)
        mess="Number of water molecules added = "+str(nwat)
        mess=mess+" and total number of atoms in system = "+str(natm)
        self.model.Message(mess,0,'black')
        self.model.ConsoleMessage(mess)
        # check short contact
        # for debuggin
        debug=False
        if debug:
            rmax=0.5
            npair,iatm,jatm,rij=self.model.CheckShortContact(rmax)
            if npair > 0:
                mess='There are '+str(npair)+' short contact (< 0.5A) atoms.'
                lib.MessageBoxOK(mess,"")
            print 'npair',npair
        # draw new molecule
        #self.model.FitToScreen(False)
        self.model.DrawMol(True)
        #self.model.Message("",0,"")
        self.model.MsgNumberOfAtoms(0)

    def RenumberWater(self):
        reslst=self.model.ListResidue(True)
        maxwat=0
        for i in xrange(len(reslst)):
            nwat=0
            for j in xrange(len(reslst[i])):
                if reslst[i][0] == 'HOH' or reslst[i][0] == 'WAT': nwat += 1
            if nwat > maxwat: maxwat=nwat
        nwat=maxwat
        for i in xrange(0,len(self.wat.atm),3):
            nwat += 1; 
            self.wat.atm[i].resnmb=nwat
            self.wat.atm[i+1].resnmb=nwat
            self.wat.atm[i+2].resnmb=nwat
                
    def GetSoluteSize(self):
        if len(self.model.mol.atm) <= 0: return
        
        mass=[]; coord=[]
        for atom in self.model.mol.atm:
            if atom.elm == 'XX': continue
            mass.append(1.0); coord.append(atom.cc[:])
        com,eig,vec=lib.CenterOfMassAndPMI(mass,coord)
        #self.com=com[:]
        pp1=vec[0]; pp2=vec[1]; pp3=vec[2]
        for i in xrange(len(coord)):
            coord[i][0] -= com[0]; coord[i][1] -= com[1]; coord[i][2] -= com[2]
        # rotarion matrix, rot
        ze=[0.0,0.0,0.0]; p1=[ze,pp3]
        zaxis=[0.0,0.0,1.0]; p2=[ze,zaxis]
        u=lib.RotMatPnts(p1,p2)
        pp2=numpy.dot(u,pp2)
        xaxis=numpy.array([1.0,0.0,0.0])
        t=lib.AngleT(pp2,xaxis)
        v=lib.RotMatZ(-t)
        self.rot=numpy.dot(v,u)
        # rotate molecule
        ctr=[0.0,0.0,0.0]
        coord=lib.RotMol(self.rot,ctr,coord)
        #
        self.cc1=copy.deepcopy(coord)
        self.com=com
        #
        x=[]; y=[]; z=[]
        for i in xrange(len(coord)):
            x.append(coord[i][0]); y.append(coord[i][1]); z.append(coord[i][2])
        xmin=min(x); xmax=max(x); ymin=min(y); ymax=max(y); zmin=min(z)
        zmax=max(z) 
        self.xsize=xmax-xmin; self.ysize=ymax-ymin; self.zsize=zmax-zmin
            
    def RotateWaterBox(self):
        invrot=numpy.linalg.inv(self.rot)
        coord=[]; ctr=[0.0,0.0,0.0]
        for atom in self.wat.atm: coord.append(atom.cc[:])
        coord=lib.RotMol(invrot,ctr,coord)
        for i in xrange(len(self.wat.atm)):
            atom=self.wat.atm[i]
            atom.cc[0]=coord[i][0]+self.com[0]
            atom.cc[1]=coord[i][1]+self.com[1]
            atom.cc[2]=coord[i][2]+self.com[2]
    
    def MakeCavityInWater(self):
        # remove waters overlapping with solute
        cc1=self.cc1; natm=len(cc1)
        messnowat=''
        if natm <= 0:
            lib.MessageBoxOK('No heavy atoms in current molecule.',"")
            return
        # copy water coordinates        
        cc2=[]; nwat=0; index=[]; i=-1 #; mass=[]
        for atom in self.wat.atm:
            i += 1
            if atom.elm == ' H': continue
            #if atom.elm == " O": nwat += 1
            cc2.append(atom.cc); index.append(i); nwat += 1
        if nwat <= 0:
            messnowat='No water molecules in required distance range.'
            lib.MessageBoxOK(messnowat,"")
            return
        # pickup water molecules
        try: # fortran code
            dim=3; natm1=natm; natm2=nwat; rmin=self.cdis; rmax=self.thick
            nwat,iatm=fortlib.find_contact_atoms(cc1,cc2,rmin,rmax)
        except:
            mess='WaterBox(MakeCavityInWater): Fortran routine is not '
            mess=mess+'available!'
            self.model.ConsoleMessage(mess)
            atmdic={}; excldic={}
            for j in xrange(len(cc2)):
                for i in xrange(len(cc1)):
                    r=lib.Distance(cc2[j],cc1[i])
                    if r < self.cdis: excldic[j]=True
                    if r < self.thick: atmdic[j]=True 
            jatm=atmdic.keys(); jatm.sort(); iatm=[]
            for i in jatm:
                if excldic.has_key(i): continue
                iatm.append(i)
            nwat=len(iatm)

        if nwat <= 0:
            #mess='No water molecules in required distance range.'
            lib.MessageBoxOK(messnowat,"")
            return
        # remove overlappinng waters with solute
        wsol=molec.Molecule(self.model); wsol.atm=[]
        for i in xrange(nwat):
            ii=iatm[i]; iii=index[ii]
            wsol.atm.append(self.wat.atm[iii])
            wsol.atm.append(self.wat.atm[iii+1])
            wsol.atm.append(self.wat.atm[iii+2])
        n=len(wsol.atm)
        # renumber atoms
        for i in xrange(0,n,3):
            wsol.atm[i].seqnmb=i; wsol.atm[i].conect=[i+1,i+2]
            wsol.atm[i+1].seqnmb=i+1; wsol.atm[i+1].conect=[i]
            wsol.atm[i+2].seqnmb=i+2; wsol.atm[i+2].conect=[i]
        #
        self.wat=wsol
         
    def MakeWaterMolData(self):
        # pdbdata format
        # [i][0]: cc
        # [i][1]: icon
        # [i][2]label=[atmnam,atmnmb,resnam,resnmb,chain,alt] #atmnmb,alt]
        # [i][3]rest=[elm,focc,fbfc,chg]
        pdbmol=[]
        lo=[' O  ',-1,self.watnam,-1,' ',' '] # label
        lh1=[' H1 ',-1,self.watnam,-1,' ',' '] 
        lh2=[' H2 ',-1,self.watnam,-1,' ',' ']
        ro=[' O',0.0,0.0,0.0] # rest
        rh=[' H',0.0,0.0,0.0]
        k=0 # counter for residues 
        coord=[]; connect=[]; atmname=[]; atmnumber=[]; resname=[];resnumber=[]
        chaname=[]; altnate=[]; element=[]; occupation=[]; bfactor=[];charge=[]

        for i in xrange(0,len(self.watelmcc),3):
            k += 1
            # O
            coord.append(self.watelmcc[i][0])
            #icon=[i,i+1,i+2]; connect.append(icon)
            icon=[i+1,i+2]; connect.append(icon)
            lo[1]=i+1; lo[3]=k
            atmname.append(lo[0]); atmnumber.append(lo[1])
            resname.append(lo[2]); resnumber.append(lo[3])
            chaname.append(lo[4]); altnate.append(lo[5])
            element.append(ro[0]); occupation.append(ro[1])
            bfactor.append(ro[2]); charge.append(ro[3])
            # H1
            coord.append(self.watelmcc[i+1][0])
            #icon=[i+1,i]; connect.append(icon)
            icon=[i]; connect.append(icon)
            lh1[1]=i+2; lh1[3]=k
            atmname.append(lh1[0]); atmnumber.append(lh1[1])
            resname.append(lh1[2]); resnumber.append(lh1[3])
            chaname.append(lh1[4]); altnate.append(lh1[5])
            element.append(rh[0]); occupation.append(rh[1])
            bfactor.append(rh[2]); charge.append(rh[3])
            # H2
            coord.append(self.watelmcc[i+2][0])
            #icon=[i+2,i]; connect.append(icon)
            icon=[i]; connect.append(icon)
            lh2[1]=i+3; lh2[3]=k
            atmname.append(lh2[0]); atmnumber.append(lh2[1])
            resname.append(lh2[2]); resnumber.append(lh2[3])
            chaname.append(lh2[4]); altnate.append(lh2[5])
            element.append(rh[0]); occupation.append(rh[1])
            bfactor.append(rh[2]); charge.append(rh[3])

        pdbmol=[coord,connect,atmname,atmnumber,resname,resnumber,  \
                chaname,altnate,element,occupation,bfactor,charge]
        # make mol data
        self.wat=molec.Molecule(self.model)
        self.wat.SetPDBMol(pdbmol) #Atoms(pdbmol)
    
    def CopyPDBWater(self):
        xh=self.xwat/2.0; yh=self.ywat/2.0; zh=self.zwat/2.0
        watcc=[]
        coord=self.pdbwat[0]; elm=self.pdbwat[8]
        for i in xrange(len(coord)):
            tmp=[]
            cc=copy.deepcopy(coord[i])
            cc[0] += xh; cc[1] += yh; cc[2] += zh
            tmp.append(cc)
            tmp.append(elm[i])
            watcc.append(tmp)
        return watcc
                   
    def ExpandWaterBox(self):
        self.watelmcc=self.CopyPDBWater() # set initial box water in self.watcc
        kshift=[self.xwat,self.ywat,self.zwat]
        delta=0.1
        kbox=[self.xbox+delta,self.ybox+delta,self.zbox+delta]
        mbox=[self.xbox,self.ybox,self.zbox]
        for k in range(3): 
            shift=kshift[k]; maxbox=mbox[k]
            if shift < maxbox:
                boxcc=copy.deepcopy(self.watelmcc)
                sft=shift; ndup=1
                while sft < maxbox:
                    ndup += 1
                    nadd=0
                    tmp=copy.deepcopy(boxcc)
                    for i in xrange(0,len(tmp),3):
                        tmp[i][0][k] += sft
                        tmp[i+1][0][k] += sft
                        tmp[i+2][0][k] += sft
                        if tmp[i][0][k] > maxbox: continue
                        nadd += 3
                        self.watelmcc.append(tmp[i])
                        self.watelmcc.append(tmp[i+1])
                        self.watelmcc.append(tmp[i+2])
                    sft=shift*ndup
            else:
                tmp=[]
                for i in xrange(0,len(self.watelmcc),3):
                    if self.watelmcc[i][0][k] > maxbox: continue
                    tmp.append(self.watelmcc[i])
                    tmp.append(self.watelmcc[i+1])
                    tmp.append(self.watelmcc[i+2])
                self.watelmcc=copy.deepcopy(tmp)
        #
        xctr=self.xbox/2.0; yctr=self.ybox/2.0; zctr=self.zbox/2.0
        for i in xrange(len(self.watelmcc)):
            self.watelmcc[i][0][0] -= xctr
            self.watelmcc[i][0][1] -= yctr
            self.watelmcc[i][0][2] -= zctr    
        
        self.MakeWaterMolData()
        
    def ReadWaterBox(self):
        # read file of water box
        filename=self.watfile
        if not os.path.exists(filename):
            mess='File not found. file='+filename
            lib.MessageBoxOK(mess,"")
            #
            return
        # read water box coordinate file to get box size
        try:
            f=open(filename,'r')
            text=f.readline()
            item=text.split()
            self.xwat=float(item[3]); self.ywat=float(item[4])
            self.zwat=float(item[5])
        except:
            mess="Failed to get water box size in file="+filename
            lib.MessageBoxOK(mess,"")
            return
        # create mol instance of water molecules    
        self.pdbwat,fuoptdic=rwfile.ReadPDBMol(filename)
    
    def OnNotify(self,event):
        #if event.jobid != self.winlabel: return
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles':
            self.model.ConsoleMessage('mess from '+item)
            self.OnReset(1)

    def OnReset(self,event):
        self.Initialize()
        try: 
            self.panel.Destroy()
            self.CreatePanel()
        except: pass
        self.model.Message('Restored molecule object',0,'')
        #lib.MessageBoxOK('Restored molecule data in mdlwin','')

    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
    
    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        # Option
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        #submenu.AppendSeparator()
        #submenu.Append(-1,'Related functions','Execute related functions')
        menubar.Append(submenu,'Help')
        #
        return menubar

    def OnMenu(self,event):
        """ Menu event handler
        
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # Help
        if item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
         
class AAResiduePicker(wx.Panel):
    def __init__(self,parent,id,winpos,retmethod,model,resnamlst=[]):
        title='Amino acid resudue picker'
        winsize=(245,125)
        wx.Panel.__init__(self,parent,id,pos=winpos,size=winsize)
        #self.setfile=parent.model.setfile
        self.model=model
        self.retmethod=retmethod
        #               
        self.SetBackgroundColour("light gray")
        #
        self.resnamlst=resnamlst
        if len(resnamlst) <= 0:
            self.resnamlst=["ALA","ARG","ASN","ASP","CYS",
                         "GLN","GLU","GLY","HIS","ILE",
                         "LEU","LYS","MET","PHE","PRO",
                         "SER","THR","TRP","TYR","VAL",
                         "ACE","NME"]
        self.resnam=''
        self.chirality="L" # "L" or "D"
        #
        self.CreateResButtons()
        #
    def CreateResButtons(self):
        yloc=5
        #x1=12; wbtn=42; x2=x1+wbtn; x3=x2+wbtn; x4=x3+wbtn; x5=x4+wbtn
        x1=15; wbtn=45; x2=x1+wbtn; x3=x2+wbtn; x4=x3+wbtn; x5=x4+wbtn
        xloc=[x1,x2,x3,x4,x5]
        #
        for i in range(4):
            ii=5*i; ie=ii+5; jj=-1
            for j in range(ii,ie):
                res=self.resnamlst[j]; jj += 1
                btnres=wx.Button(self,wx.ID_ANY,res,pos=(xloc[jj],yloc),
                                 size=(38,22))
                btnres.Bind(wx.EVT_BUTTON,self.OnButton)
            yloc += 25        
        #
        ace=self.resnamlst[20]
        btnace=wx.Button(self,wx.ID_ANY,ace,pos=(x1,yloc),size=(38,22))
        btnace.Bind(wx.EVT_BUTTON,self.OnButton)
        #self.buttondic[btnace.Id]=ace
        nme=self.resnamlst[21]
        btnnme=wx.Button(self,wx.ID_ANY,nme,pos=(x2,yloc),size=(38,22))
        btnnme.Bind(wx.EVT_BUTTON,self.OnButton)
        #self.buttondic[btnnme.Id]=nme
        wx.StaticText(self,-1,"chirality:",pos=(115,yloc+6),size=(50,18)) 
        self.rbtlll=wx.RadioButton(self,-1,"L",pos=(170,yloc+6),
                                   style=wx.RB_GROUP) #size=(60,18))
        self.rbtlll.Bind(wx.EVT_RADIOBUTTON,self.OnLChirality)
        self.rbtddd=wx.RadioButton(self,-1,"D",pos=(200,yloc+6)) #,size=(60,18))
        self.rbtddd.Bind(wx.EVT_RADIOBUTTON,self.OnDChirality)
        self.SetChirality()

    def OnLChirality(self,event):
        self.chirality="L"

    def OnDChirality(self,event):
        self.chirality="D"
        
    def SetChirality(self):
        if self.chirality == "L": self.rbtlll.SetValue(True) 
        if self.chirality == "D": self.rbtddd.SetValue(True) 
        
    def GetChirality(self):
        if self.rbtlll.GetValue(): chirality="L"
        else: chirality="D"
        return chirality
    
    def GetCurrentRes(self):
        return self.res,self.chirality
        
    def OnButton(self,event):
        obj=event.GetEventObject()
        self.resnam=obj.GetLabel()
        self.chirality=self.GetChirality()
        self.retmethod(self.resnam,self.chirality)

class RigidBodyOptimizer_Frm(wx.Frame):
    def __init__(self,parent,id,model,winpos=[]):
        #if lib.GetPlatform() == 'WINDOWS':self.winsize=(310,420)
        #else: self.winsize=(300,390)
        self.winsize=lib.WinSize([310,420])
        if len(winpos) <= 0: winpos=lib.WinPos(parent)
        self.title='Rigid-Body Optmizer'
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,
                          size=self.winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)      
        # ctrlflag
        #self.fum=fum
        self.mdlwin=parent
        self.model=model
        self.ctrlflag=parent.model.ctrlflag
        #if self.ctrlflag.GetCtrlFlag('tinoptwin'):
        #    self.Destroy()
        #    return
        #if self.ctrlflag.GetCtrlFlag('tinoptwin'): 
        #    self.OnClose(0)
        #self.ctrlflag.SetCtrlFlag('tinoptwin',True)
                
        #self.setfile=parent.model.setfile
        self.model=parent.model
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: 
            self.OnClose(1); return
                
        scriptdir=self.model.setctrl.GetDir('Scripts')

        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        self.helpname='rigidbody-optimizer'
        self.winlabel='RigidBodyOptimizer'
        self.model.winctrl.SetOpenWin(self.winlabel,self)
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.vdwlst=['Internal','File']
        self.chglst=['None','QEq','EHT','File']
        #
        self.Initialize()
        #
        self.CreatePanel()
        self.ResetVariableButtons()
        
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        # Event handler to receive message when child thread ends
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)

        self.Show()
    
    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        xsize=w; ysize=h
        hbtn=22; hcmd=200
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        hcb=const.HCBOX
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset) 
        yloc=10
        wx.StaticText(self.panel,-1,"Variable definition:",pos=(10,yloc),
                      size=(100,18)) 
        #btnviewvar=wx.Button(self.panel,-1,"View Variables",pos=(100,yloc-2),size=(100,hbtn)) 
        yloc += 20
        self.rbtvargrp=wx.RadioButton(self.panel,-1,
                     "Selected atoms define rigid-body",
                     pos=(20,yloc),style=wx.RB_GROUP)
        self.rbtvargrp.Bind(wx.EVT_RADIOBUTTON,self.OnVariableGroup)
        self.btngrpset=wx.Button(self.panel,-1,"Set",pos=(240,yloc-2),
                                 size=(40,22))
        self.btngrpset.Bind(wx.EVT_BUTTON,self.OnSetGroup)
        yloc += 20; xloc=30
        wx.StaticText(self.panel,-1,"optimize:",pos=(xloc+10,yloc),
                      size=(50,18)) 
        self.ckbcntr=wx.CheckBox(self.panel,-1,"Center",pos=(xloc+80,yloc),
                                 size=(60,18))
        self.ckbcntr.Bind(wx.EVT_CHECKBOX,self.OnOptCenter)
        self.ckborie=wx.CheckBox(self.panel,-1,"Orientation",
                                 pos=(xloc+150,yloc),size=(100,18))
        self.ckborie.Bind(wx.EVT_CHECKBOX,self.OnOptOrientation)
        yloc += 25
        self.rbtvarrot=wx.RadioButton(self.panel,-1,
                            "Rotate around bond(select 2 atoms)",pos=(20,yloc))
        self.rbtvarrot.Bind(wx.EVT_RADIOBUTTON,self.OnVariableRot)
        mess='Rotation angle around axis defined by two selected atoms.'
        self.rbtvarrot.SetToolTipString(mess)
        self.btnbndset=wx.Button(self.panel,-1,"Set",pos=(250,yloc-2),
                                 size=(40,22))
        self.btnbndset.Bind(wx.EVT_BUTTON,self.OnSetBond)

        yloc += 25
        self.rbtvarset=wx.RadioButton(self.panel,-1,
                                   "Multiple rigid-bodies/bonds",pos=(20,yloc)) #,size=(60,18))
        self.rbtvarset.Bind(wx.EVT_RADIOBUTTON,self.OnVariableSet)
        #self.SetVariableButtonStatus()
        self.btnopn=wx.Button(self.panel,-1,"Open setting",pos=(200,yloc-2),
                              size=(90,22))
        self.btnopn.Bind(wx.EVT_BUTTON,self.OnOpenVariableSetting)
        """
        yloc += 25
        self.rbtvarred=wx.RadioButton(self.panel,-1,"Read variable file",pos=(20,yloc)) #,size=(60,18))
        self.rbtvarred.Bind(wx.EVT_RADIOBUTTON,self.OnVariableRead)
        self.btnred=wx.Button(self.panel,-1,"Read",pos=(200,yloc-2),size=(50,22))
        self.btnred.Bind(wx.EVT_BUTTON,self.OnReadVariableFile)
        """
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 10
        
        wx.StaticText(self.panel,-1,"Non-bond parameters:",pos=(10,yloc),
                      size=(150,18)) 
        """
        btnviewprm=wx.Button(self.panel,-1,"View params",pos=(150,yloc-2),size=(90,hbtn)) 
        """
        yloc += 25
        wx.StaticText(self.panel,-1,"vdW:",pos=(20,yloc),size=(35,18))
        self.cmbvdw=wx.ComboBox(self.panel,-1,'',choices=self.vdwlst, \
                          pos=(55,yloc-2), size=(70,hcb),style=wx.CB_READONLY) # 28<-22                             
        self.cmbvdw.Bind(wx.EVT_COMBOBOX,self.OnvdWParam)
        self.cmbvdw.SetStringSelection(self.vdwoptn)
        """
        rbtambvdw=wx.RadioButton(self.panel,-1,"Internal",pos=(120,yloc),style=wx.RB_GROUP) #size=(60,18))
        #rbtredchg.SetValue(self.ambcharge)
        rbtredvdw=wx.RadioButton(self.panel,-1,"Read",pos=(200,yloc)) #,size=(60,18))
        """
        #yloc += 20 
        wx.StaticText(self.panel,-1,"Atom charges:",pos=(140,yloc),
                      size=(80,18))
        self.cmbchg=wx.ComboBox(self.panel,-1,'',choices=self.chglst, \
                               pos=(230,yloc-2), size=(60,hcb),\
                               style=wx.CB_READONLY) # 28<-22                             
        self.cmbchg.Bind(wx.EVT_COMBOBOX,self.OnAtomCharge)
        self.cmbchg.SetStringSelection(self.chgoptn)

        """
        rbtambchg=wx.RadioButton(self.panel,-1,"AMBER",pos=(120,yloc),style=wx.RB_GROUP) #size=(60,18))
        #rbtredchg.SetValue(self.ambcharge)
        rbtredchg=wx.RadioButton(self.panel,-1,"Read",pos=(200,yloc)) #,size=(60,18))
        """
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)                
        yloc += 10
        wx.StaticText(self.panel,-1,"Optimization method:",pos=(10,yloc),
                      size=(120,18)) 
        self.cmbmet=wx.ComboBox(self.panel,-1,'',choices=self.methodlst, \
                         pos=(140,yloc-2),size=(100,hcb),style=wx.CB_READONLY)                      
        #self.cmbmet.Bind(wx.EVT_COMBOBOX,self.OnMethod)
        self.SetMethod()
        self.cmbmet.SetStringSelection(self.method)
        # threshold, maxcycle, 
        yloc += 25
        strms=wx.StaticText(self.panel,-1,"RMS gradient convergence:",
                            pos=(25,yloc),size=(160,18))  
        strms.SetToolTipString('Convergence criteria in kcal per Angstrom')
        self.tclgrd=wx.TextCtrl(self.panel,-1,str(self.rmsgrd),pos=(185,yloc),
                                size=(50,18))
        #self.tclitr.Bind(wx.EVT_TEXT,self.OnMaxCycleInput)
        yloc += 25
        wx.StaticText(self.panel,-1,"maximum cycles:",pos=(25,yloc),
                      size=(100,18)) 
        self.tclitr=wx.TextCtrl(self.panel,-1,str(self.maxiter),pos=(130,yloc),
                                size=(50,18))
        #wx.StaticText(self.panel,-1,"RMS gradient (kcal/A/mol):",pos=(25,yloc),size=(150,18))
        #self.tclgrd.Bind(wx.EVT_TEXT,self.OnGradientInput)
        #        
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"Plot:",pos=(10,yloc),size=(40,18)) 
        self.rbtene=wx.RadioButton(self.panel,-1,"energy",pos=(50,yloc),
                                   style=wx.RB_GROUP) #size=(60,18))
        self.rbtene.SetValue(self.pltene)
        self.rbtgrd=wx.RadioButton(self.panel,-1,"gradient",pos=(120,yloc)) #,size=(60,18))
        self.rbtgrd.SetValue(self.pltgrd)
        self.rbtnoplt=wx.RadioButton(self.panel,-1,"none",pos=(200,yloc)) #,size=(60,18))
        self.rbtnoplt.SetValue(self.pltnon)
        #btnopt.Bind(wx.EVT_BUTTON,self.OnPltOptions)
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,4),
                      style=wx.LI_HORIZONTAL)
        yloc += 12
        self.btnexec=wx.Button(self.panel,-1,"ExecOpt",pos=(20,yloc-2),
                               size=(60,22))
        self.btnexec.Bind(wx.EVT_BUTTON,self.OnExecOpt)
        self.rbtexeall=wx.RadioButton(self.panel,-1,"simultaneous",
                                      pos=(90,yloc),style=wx.RB_GROUP) #size=(60,18))
        #self.rbtene.SetValue(self.pltene)
        self.rbtexestep=wx.RadioButton(self.panel,-1,"step-by-step",
                                       pos=(190,yloc)) #,size=(60,18))
        #self.rbtgrd.SetValue(self.pltgrd)
        #wx.StaticLine(self.panel,pos=(100,yloc-8),size=(4,h-yloc+12),style=wx.LI_VERTICAL)
        yloc += 25
        xloc=60
        self.btnundo=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(xloc,yloc),
                               size=(40,22))
        self.btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        #self.btnundo.Disable()
        self.btnaply=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(xloc+60,yloc),
                               size=(40,22))
        self.btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        #self.btnaply.Disable()
        self.btntry=wx.Button(self.panel,wx.ID_ANY,"Try",pos=(xloc+120,yloc-2),
                              size=(40,22))
        self.btntry.Bind(wx.EVT_TOGGLEBUTTON,self.OnTry)
        #self.btntry.Disable()
        #
        #self.SetVariableButtonStatus()
    
    def Initialize(self):
        try: self.SetTitle(self.title+' ['+self.model.mol.name+']')
        except: pass
        #
        self.setbond=True
        #
        self.vdwoptn='Internal'
        self.chgoptn='None'
        self.varoptn=0 # 0: group opt,1:zaxis rotation,2:set variables, 3:read file
        self.gcharge=0
        self.ngroup=0
        #self.varoptnlst=["selected atoms","set variables"]
        self.optcenter=True
        self.optorient=True
        #self.varbuttondic={"rotation angles":'Set axis',"rigid body":'Set group'}
        #
        self.methodlst=['CG','Powell','L-BFGS-B','Newton-CG','TNC']
        self.method="CG"
        self.optndic={} # option for optimizer
        
        self.p1=-1; self.p2=-1
        self.grplst=[]
        self.grpchkboxdic={}
        #
        self.rmsgrd=0.1 # for rough optimization!
        self.maxiter=1000
        self.updatesteps=1
        self.overlay=False
        self.multichain=False
        if len(self.model.ListChainName()) > 1: self.multichain=True
        #
        self.savmol=self.model.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        #
        self.pltene=False; self.pltgrd=False; self.pltnon=True
        self.pltgeo=False

        self.discongrpdic=self.model.FindConnectedGroup()
        if len(self.discongrpdic) <= 0:
            mess='No disconnected groups in '+self.model.mol.name
            self.model.ConsoleMessage(mess)        
        self.grplst=[] #['fkbp','k506'] # group name list
        self.grpatmlstdic={} # {grpnam:atmidxlst,...}
        self.grpchgfiledic={} #['c2h5oh']='E://FUDATASET//FUdocs//data//ethanol.chg'
        self.grpvardic={} # {grpnam:[True(center),True(orientation),[atmi,atmj,[movelst](rotaxis),..],...]
        self.rotatmlstdic={} # {rotnam('p1-p2':[movable atmlst],...}
        
        self.vdwprmdic=const.LJParams
        self.atmchglst=[]
        
    def ResetVariableButtons(self):
        self.rbtvargrp.SetValue(True)
        self.ckbcntr.Enable()
        self.ckborie.Enable()
        self.ckbcntr.SetValue(self.optcenter)
        self.ckborie.SetValue(self.optorient)
        self.rbtexeall.Disable()
        self.rbtexestep.Disable()
   
    def OnVariableGroup(self,event):
        self.model.mousectrl.SetRotationAxisPnts(False,[])
        self.model.DrawAxisArrow(False,[],drw=True)
        
        self.varoptn=0
        self.rbtexestep.Disable(); self.rbtexeall.Disable()
        self.ckbcntr.Enable(); self.ckborie.Enable()

        #self.SetVariableButtonStatus()
        
        self.model.menuctrl.OnSelect("1-object",True)   
    
    def OnSetGroup(self,event):
        nsel,sellst=self.model.ListSelectedAtom()
        if nsel <= 0:
            mess='Please select atoms to define rigid-bod group'
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnSetGroup)')    
            return
        self.ngroup += 1
        grpnam='Group'+'%03d' % self.ngroup
        self.grplst.append(grpnam)
        self.grpatmlstdic[grpnam]=sellst
        center=self.ckbcntr.GetValue()
        orient=self.ckborie.GetValue()
        self.grpvardic[grpnam]=[center,orient,[]]
        
        self.model.ConsoleMessage(grpnam+': Number of group atoms='+str(nsel))

    def OnSetBond(self,event):
        if self.setbond:
            nsel,sellst=self.model.ListSelectedAtom()
            if nsel <= 0:
                mess='Please select two atoms to define rotatable bond'
                lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnSetBond)')    
                return
            self.ngroup += 1
            grpnam='AllAtoms'
            self.grplst.append(grpnam)
            self.grpatmlstdic[grpnam]=range(len(self.model.mol.atm))
            center=False; orient=False
            self.p1=sellst[0]; self.p2=sellst[1]
            self.grpvardic[grpnam]=[center,orient,[self.p1,self.p2]]
            self.DrawRotationAxis([[self.p1,self.p2]])
            self.model.mousectrl.SetRotationAxisPnts(True,[self.p1,self.p2]) 
            nmove=self.model.SelectMovableAtoms(self.p1,self.p2,drw=True,
                                                messout=False)
            mess='Please select movable atoms' # and push "Set" button'
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnSetBond)')    
            self.setbond=False
            if nmove <= 0:
                mess='No movable atoms around this bond.'
                lib.MessageBoxOK(mess,'RigidBody-optimiser(OnSetBond)')
        else:
            nsel,sellst=self.model.ListSelectedAtom()
            rotnam=str(str(self.p1)+':'+str(self.p2))
            self.rotatmlstdic[rotnam]=sellst
            #mess='Rigid-boy group='+self.grplst[self.ngroup-1]+'\n'
            mess='Number of movable atoms around bond '+str(self.p1)+'-'
            mess=mess+str(self.p2)+'='+str(nsel)
            self.model.ConsoleMessage(mess)
            self.setbond=True
            self.p1=-1; self.p2=-1
  
    def DrawRotationAxis(self,pntlst):
        self.model.DrawAxisArrow(False,[],drw=False)
        if len(pntlst) <= 0: return
        bndpnts=[]
        for p1,p2 in pntlst:
            cc1=self.model.mol.atm[p1].cc
            cc2=self.model.mol.atm[p2].cc
            bndpnts.append([cc1,cc2])    
        self.model.DrawAxisArrow(True,bndpnts)
   
    def OnVariableRot(self,event):
        self.cmbvdw.Enable(); self.cmbchg.Enable()
        self.ckbcntr.Disable(); self.ckborie.Disable()
        self.rbtexestep.Disable(); self.rbtexeall.Disable()
        self.varoptn=1
        #self.SetVariableButtonStatus()
        
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)

    
    def OnVariableSet(self,event):
        self.model.mousectrl.SetRotationAxisPnts(False,[])
        self.model.DrawAxisArrow(False,[],drw=True)

        self.cmbvdw.Enable(); self.cmbchg.Enable()
        self.ckbcntr.Disable(); self.ckborie.Disable()
        self.rbtexestep.Enable(); self.rbtexeall.Enable()
        self.varoptn=2
        #self.SetVariableButtonStatus()
        self.model.menuctrl.OnSelect("1-object",True)
        self.cmbvdw.Disable(); self.cmbchg.Disable()
  
    def OnOpenVariableSetting(self,event):
        self.varsetwin=VariableDefinition_Frm(self,-1,self.model)
        self.OnVariableSet(1)
    
    def XXOnVariableRead(self,event):   
        self.varoptn=3
        #self.SetVariableButtonStatus()
        self.model.menuctrl.OnSelect("1-object",True)
        
    def OnReadVariableFile(self,event):
        const.CONSOLEMESSAGE('OnReadVariableFile')   
        self.OnVariableRead(1)
        self.ReadVriableFile()
        
    def ReadVariableFile(self):
        const.CONSOLEMESSAGE('RaedVariableFile')    
    
    def OnOptCenter(self,event):
        self.optcenter=self.ckbcntr.GetValue()
            
    def OnOptOrientation(self,event):
        self.optorient=self.ckborie.GetValue()
            
    def OnThreadJobEnded(self,event):
        pass
    
    def XXOnMethod(self,event):
        self.method=self.cmbmet.GetStringSelection()
        
        
    def SetMethod(self):
        self.cmbmet.SetStringSelection(self.method) 
                 
    def SetOptMethod(self,method):
        self.method=method
        self.cmbmet.SetStringSelection(self.method)    
    
    def OnvdWParam(self,event):
        obj=event.GetEventObject()
        value=obj.GetStringSelection()
        if value == 'Internal': self.vdwprmdic=const.LJParams
        elif value == 'File':
            self.vdwprmfile=''
            wcard='vdW (*.vdw)|*.vdw'
            mess='vdW parameter file'
            filenam=lib.GetFileName(wcard=wcard,rw='r',message=mess)
            if len(filenam) <= 0: return
            self.vdwprmdic=rwfile.ReadvdWParams(filename)
        const.CONSOLEMESSAGE('vdwprmdic in OnvdWParam='+str(self.vdwprmdic))
    
    def XXReadvdWParams(self,vdwfile):
        vdwprmdic={}
        if not os.path.exists(vdwfile):
            mess='Not found vdwfile='+vdwfile
            const.CONSOLEMESSAGE(mess)
            return vdwprmdic
        line=0
        f=open(vdwfile,'r')
        for s in f.readlines():
            line += 1
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                mess='Wrong data in line='+str(line)
                lib.MessageBoxOK(mess,'RigidBodyOptimizer(ReadvdWParams')
                return vdwprmdic
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # params
            vdwprmdic[elm]=[float(items[1]),float(items[2])]
        f.close()
        
        return vdwprmdic
        
    def OnAtomCharge(self,event):
        obj=event.GetEventObject()
        value=obj.GetStringSelection()
        const.CONSOLEMESSAGE('OnAtomCharge. value='+value)
        if value == 'None': pass
        elif value == 'QEq': 
            self.atmchglst=self.ComputeQEqChareg()
        elif value == 'File':
            const.CONSOLEMESSAGE('In File')
            wcard='charge(*.chg)|*.chg'
            base,ext=os.path.splitext(self.model.mol.name)
            defnam=base+'.chg'
            mess='Open charge file'
            const.CONSOLEMESSAGE('In File #1')
            filename=lib.GetFileName(wcard=wcard,rw='r',defaultname=defnam,
                                     message=mess)
            const.CONSOLEMESSAGE('filename='+filename)
            if len(filename) <= 0: return
            retmess,chglst=rwfile.ReadAtomCharges(filename)
            const.CONSOLEMESSAGE('File #2')
            for chg in chglst: 
                self.atmchglst.append(chg)
            nchg=len(self.atmchglst) 
            if nchg != len(self.model.mol.atm):
                mess='Wrong atom charge file.\n'
                mess=mess+'Number of charges read='+str(nchg)+'\n'
                mess=mess+'Number of atoms in '+self.model.mol.name+'='
                mess=mess+str(len(self.model.mol.atm))
                lib.MessageBoxOK(mess,'RiidBodyOptimizer(OnAtomCharge)')

        elif value == 'EHT':
            pass    

    def ComputeQEqCharge(self):
        TIP3PO=-0.400; TIP3PH=0.200
        self.atmchglst=[]
        const.CONSOLEMESSAGE('Entered in ComputeQEqCharge')
        self.grpchgdic={}
        for grpnam in self.grplst:
            text=wx.GetTextFromUser('Enter total charge for group='+grpnam,
                                    '','0.0')
            try: 
                self.grpchgdic[grpnam]=float(text)
            except:
                mess='Wrong input for total charge'            
                lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnAtomCharge')
                return

        
        if value == 'None':
            pass # do not use charge-charge interaction
        elif value == 'QEq':

            
            self.grpchgdic={}
            for grpnam in self.grplst:
                text=wx.GetTextFromUser('Enter total charge for group='+grpnam,
                                        '','0.0')
                try: 
                    self.grpchgdic[grpnam]=float(text)
                except:
                    mess='Wrong input for total charge'            
                    lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnAtomCharge')
                    return
        elif value == 'File':
            self.grpchgfiledic={}; count=0
            for i,lst in self.discongrpdic.iteritems():
                const.CONSOLEMESSAGE('group number='+str(i))
                fst=self.model.mol.atm[lst[0]]
                resnam=fst.resnam #; elm=fst.elm
                const.CONSOLEMESSAGE('resnam='+resnam)
                if resnam in const.WaterRes:
                    const.CONSOLEMESSAGE('In Water. lst='+str(lst))
                    for j in lst:
                        elm=self.model.mol.atm[j].elm
                        const.CONSOLEMESSAGE('In Water. elm='+elm)
                        if elm == ' O': 
                            count += 1; self.atmchglst.append(TIP3PO)
                        elif elm == ' H': 
                            count += 1; self.atmchglst.append(TIP3PH)
                else:
                    const.CONSOLEMESSAGE('In File')
                    wcard='charge(*.chg)|*.chg'
                    defnam='Group'+str(i)+'.chg'
                    mess='Open charge file'
                    const.CONSOLEMESSAGE('In File #1')
                    filename=lib.GetFileName(wcard=wcard,rw='r',
                                             defaultname=defnam,message=mess)
                    const.CONSOLEMESSAGE('filename='+filename)
                    if len(filename) <= 0: return
                    #self.grpchgfiledic[grpnam]=filename
                    const.CONSOLEMESSAGE('File #1')
                    retmess,chglst=rwfile.ReadAtomCharges(filename)
                    const.CONSOLEMESSAGE('File #2')
                    for chg in chglst: 
                        self.atmchglst.append(chg); count += 1
            if count != len(self.model.mol.atm):
                mess='Failed to read atom charges.\n'
                mess=mess+'Number of charges read='+str(count)+'\n'
                mess=mess+'Number of atoms in '+self.model.mol.name+'='
                mess=mess+str(len(self.model.mol.atm))
                lib.MessageBoxOK(mess,'RiidBodyOptimizer(OnAtomCharge)')
                
                #self.atmchglst=[]
        const.CONSOLEMESSAGE('atmchglst in OnAtomCharge='+str(self.atmchglst))        
                    
    def XXReadAtomCharges(self,chgfile):
        def ErrorMessage(line,filename):
            mess='Wrong data in line='+str(line)+' in '+filename
            lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')

        def FileExist(filename):
            mess=''
            if not os.path.exists(filename):
                mess='Not found file='+filename
                lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')
            return mess
        # check file    
        err=FileExist(chgfile)
        if len(err) > 0: return []
        #
        mess='atom charge file='+chgfile+'\n'
        atmchglst=[]; scale=1.0
        line=0
        f=open(chgfile,'r')
        for s in f.readlines():
            line += 1
            if s[:1] == '#': continue
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            if s[1:] == '@': #file name
                n=1
                subfile=s[1:].strip()
                items=subfile.split('*')
                if len(items) > 1:
                    subfile=items[0].strip(); n=int(items[1])
                err=FileExist(subfile)
                if len(err) > 0: return []
                for i in range(n):
                    addmess,addlst=ReadAtomCharges(subfile)
                    atmchglst=atmchglst+addlst
                mess=mess+addmess+' *'+str(n)+'\n'
                continue
            if s[:6] == 'RESNAM':
                const.CONSOLEMESSAGE('found RESNAM')
                key,resnam=lib.GetKeyAndValue(s)
                mess=mess+'RESNAM:'+resnam+'\n'
                continue
            if s[:6] == 'CHARGE':
                const.CONSOLEMESSAGE('found CHARGE')
                key,charge=lib.GetKeyAndValue(s); continue
            if s[:5] == 'SCALE':
                const.CONSOLEMESSAGE('found SCALE')
                key,scale=lib.GetKeyAndValue(s); continue
                mess=mess+'SCALE='+str(scale)+'\n'
            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                ErrorMessage(line,chgfile)
                return []
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # atomic charge
            try: chg=float(items[2])
            except:
                ErrorMessage(line,chgfile)
                return []
            # params
            atmchglst.append(chg)
        f.close()
        
        for i in range(len(atmchglst)): atmchglist[i] *= scale
        
        return mess,atmchglst
     
    def SetAtomCharges(self):
        tip3pO=-0.400; tip3pH=0.200
        atmchglst=[]

        return atmchglst
    
    
    def OnUndo(self,event):
        pass
    
    def OnApply(self,event):
        pass
    
    def OnTry(self,event):
        pass
    
    def OnExecOpt(self,event):
        self.method=self.cmbmet.GetStringSelection()
        self.gconv=float(self.tclgrd.GetValue())
        self.maxiter=float(self.tclitr.GetValue())
        const.CONSOLEMESSAGE('Entered in OnExecOpt. maxiter='+str(self.maxiter)) 
        self.ExecOpt()

    def ExecOpt(self):
        const.CONSOLEMESSAGE('Entered in ExecOpt') 
        const.CONSOLEMESSAGE('vdwprmdic in ExecOpt='+str(self.vdwprmdic))
        self.nbie=NonBondIntEnergy(self.model,title='RigidBodyOptimization')
        self.nbie.SetRigidBodyData(self.grplst,self.grpatmlstdic,
                                   self.grpvardic,self.rotatmlstdic)
        self.nbie.SetNonBondParams(self.vdwprmdic,self.atmchglst)
        const.CONSOLEMESSAGE('ExecOpt #1') 
        self.nbie.SetOptMethod(self.method,self.gconv,self.maxiter)
        const.CONSOLEMESSAGE('ExecOpt #2') 
        self.nbie.Optimize()
        const.CONSOLEMESSAGE('ExecOpt #3')
         
    def OnKill(self,event):
        pass
    
    def OnReset(self,event):
        self.Initialize()
        self.panel.Destroy()
        self.CreatePanel()
        self.ResetVariableButtons()
        
    def OnClose(self,event):
        try: self.model.menuctrl.OnSelect("1-object",True)
        except: paee
        try: self.model.DrawAxisArrow(False,[],drw=True)
        except: pass
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        try: self.Destroy()
        except: pass
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
        
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
                
    def MenuItems(self):
        #menuhelpdic={} 
        menubar=wx.MenuBar()
        # Option
        submenu=wx.Menu()
        submenu.Append(-1,'Save output','Save optimization output')
        menubar.Append(submenu,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Open document.')
        helpname=self.winlabel
        submenu.Append(-1,'Tutorial','Open tutorial panel.')
        # related functions
        #submenu.AppendSeparator()
        #subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"ZmtViewer",
        #                  "View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,'Help')

        """ test """
        #menubar.Bind(wx.EVT_HELP,self.OnMenuHelp)
        
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # Option
        if item == "Save output": 
            pass
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        #
        elif item == "ZmtViewer": self.OpenZmtViewer()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()
        
class VariableDefinition_Frm(wx.Frame):
    def __init__(self,parent,id,model,winpos=[]):
        self.title='Variable Definition'
        if len(winpos) <= 0: winpos=[-1,-1]
        self.winsize=lib.WinSize((300,380))
        #if const.SYSTEM == const.MACOSX: winsize=(275,355)
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,\
               size=self.winsize,style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|\
               wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)      
               
        #self.fum=fum
        self.parent=parent
        self.model=model
        self.mdlwin=self.model.mdlwin
        self.ctrlflag=self.model.ctrlflag
        #
        if not self.model.mol:
            mess='No molecule data. Open pdb/xyz file in fumodel.'
            lib.MessageBoxOK(mess,"")
            self.OnClose(1)                       
        self.mol=self.model.mol
        self.molnam=self.mol.name
        self.molnam,ext=os.path.splitext(self.molnam)
        scriptdir=self.model.setctrl.GetDir('Scripts')
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        self.winlabel='VariableDefinitionWin'
        self.model.winctrl.SetOpenWin(self.winlabel,self)
        # Menu
        menud=self.MenuItems()
        self.SetMenuBar(menud) # self.menubar.menuitem)
        self.Bind(wx.EVT_MENU,self.OnMenu)

        #
        self.var="rotation angles"
        self.varlst=["rotation angles","rigid body"]
        self.varbuttondic={"rotation angles":'Set axis',
                           "rigid body":'Set group'}
        #
        self.curgrp=''
        self.groupatmdic={} # {group#:[atm1,atm2,...],...}
        self.axisdic={} # {group#:[[atm1,atm2],...],...}
        self.vardic={} # {group#:[center,orientation],...}
        self.optvarorder=[]
        self.optgrouporder=[]
        
        #
        self.axislst=[]
        self.axischkboxdic={}
        self.curname=''
        self.rotpanheight=120
        self.grouppanheight=120
        self.p1=-1; self.p2=-1
        #
        self.grplst=[]
        self.grpchkboxdic={}
        #
        self.CreatePanel()
        
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Show()
    
    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        xsize=w; ysize=h
        self.grouppanheight=120
        
        hbtn=22; hcmd=200
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        hcb=const.HCBOX
        
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        yloc=10
        self.CreateGroupPanel(yloc,self.grouppanheight)
        yloc += self.grouppanheight+5
        
        wx.StaticLine(self.panel,pos=(20,yloc),size=(w-40,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 10
        
        self.stgrp=wx.StaticText(self.panel,-1,"Variables in "+self.curgrp,
                                 pos=(20,yloc),size=(100,18))                 

        self.rotpanheight=h-self.grouppanheight-90

        yloc += 25

        self.CreateRotAxisPanel(yloc,self.rotpanheight)
        yloc += self.rotpanheight+5
        #if self.rigidbodypan:
        yloc=h-35
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        xloc=40
        btnedit=wx.Button(self.panel,-1,"Edit",pos=(xloc,yloc),size=(50,hbtn))
        btnedit.Bind(wx.EVT_BUTTON,self.OnEdit)
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnedit.SetToolTipString(mess)
        

        btnaply=wx.Button(self.panel,-1,"Apply",pos=(xloc+70,yloc),
                          size=(60,hbtn))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnaply.SetToolTipString(mess)
        
        btncls=wx.Button(self.panel,-1,"Close",pos=(xloc+150,yloc),
                         size=(60,hbtn))
        btncls.Bind(wx.EVT_BUTTON,self.OnClose)
        
    def CreateRotAxisPanel(self,yloc,height):
        hbtn=22
        wx.StaticText(self.panel,-1,"Rotation axis:",pos=(35,yloc),
                      size=(80,18))
        btnset=wx.Button(self.panel,-1,"Set selected atoms",pos=(130,yloc-2),
                         size=(120,hbtn))
        btnset.Bind(wx.EVT_BUTTON,self.OnSetAxis)
        wpan=130; hpan=height-50 #hpan=h-yloc-hcmd-30
        xloc=5
        yloc += 25
        self.rotpan=wx.ScrolledWindow(self.panel,-1,pos=[xloc+30,yloc],
                                      size=[wpan,hpan]) #,
        self.rotpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
        self.rotpan.SetBackgroundColour('white')
        self.SetAxisCheckBoxes()
        self.rotpan.SetScrollRate(5,20)
        xloc1=xloc+wpan+45
        btnauto=wx.Button(self.panel,-1,"Auto set",pos=(xloc1,yloc),
                          size=(60,hbtn))
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnauto.SetToolTipString(mess)
        #btnauto.Bind(wx.EVT_BUTTON,self.OnAutoSet)
        yloc += 25
        btnrmv=wx.Button(self.panel,-1,"Remove",pos=(xloc1,yloc),
                         size=(60,hbtn))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove)
        btnrmv.SetToolTipString('Remove checked data from the list')
        yloc += 25
        btnclr=wx.Button(self.panel,-1,"ClearAll",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearAll)
        btnclr.SetToolTipString('Clear the list')
        yloc += hpan-40
        wx.StaticText(self.panel,-1,"Optimize:",pos=(30,yloc),size=(50,18))                 
        xloc=90

        self.rbtseqrotopt=wx.RadioButton(self.panel,-1,"Sequential",
                                         pos=(xloc,yloc),style=wx.RB_GROUP)
        self.rbtseqrotopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptRotSequential)
       
        self.rbtallrotopt=wx.RadioButton(self.panel,-1,"Simultaneouse",
                                         pos=(xloc+80,yloc))
        self.rbtallrotopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptRotSimultanious)
        mess='Rotation angle around axis defined by two selected atoms.'
        self.rbtallrotopt.SetToolTipString(mess)

    def CreateGroupPanel(self,yloc,height):
        hbtn=22
        wx.StaticText(self.panel,-1,"Group:",pos=(20,yloc),size=(100,18))                 
        btnset=wx.Button(self.panel,-1,"Set selected atoms",pos=(130,yloc-2),
                         size=(120,hbtn))
        wpan=130; hpan=height-50 #hpan=h-yloc-hcmd-30
        xloc=5
        yloc += 25
        self.grppan=wx.ScrolledWindow(self.panel,-1,pos=[xloc+30,yloc],
                                      size=[wpan,hpan]) #,
        self.grppan.SetScrollbars(1,1,0,(len(self.grplst)+1)*20)
        self.grppan.SetBackgroundColour('white')
        self.SetGroupCheckBoxes()
        self.grppan.SetScrollRate(5,20)
        xloc1=xloc+wpan+45
        btnauto=wx.Button(self.panel,-1,"Auto set",pos=(xloc1,yloc),
                          size=(60,hbtn))
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnauto.SetToolTipString(mess)
        #btnauto.Bind(wx.EVT_BUTTON,self.OnAutoSet)
        yloc += 25
        btnrmv=wx.Button(self.panel,-1,"Remove",pos=(xloc1,yloc),
                         size=(60,hbtn))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove)
        btnrmv.SetToolTipString('Remove checked data from the list')
        yloc += 25
        btnclr=wx.Button(self.panel,-1,"ClearAll",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearAll)
        btnclr.SetToolTipString('Clear the list')
        yloc += 30
        wx.StaticText(self.panel,-1,"Optimize:",pos=(30,yloc),size=(50,18))                 
        xloc=90

        self.rbtseqgrpopt=wx.RadioButton(self.panel,-1,"Sequential",
                                         pos=(xloc,yloc),style=wx.RB_GROUP)
        self.rbtseqgrpopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptGroupSequential)
       
        self.rbtallgrpopt=wx.RadioButton(self.panel,-1,"Simultaneouse",
                                         pos=(xloc+80,yloc))
        self.rbtallgrpopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptGroupSimultanious)
        mess='Rotation angle around axis defined by two selected atoms.'
        self.rbtallgrpopt.SetToolTipString(mess)

    def OnOptGroupSequential(self,event):
        pass
    def OnOptGroupSimultanious(self,event):
        pass
    
    def OnOptRotSequential(self,event):
        pass
    def OnOptRotSimultanious(self,event):
        pass
    
    def OnSetAxis(self,event):
        nsel,lst=self.model.ListSelectedAtom()
        if nsel < 2:
            mess='Please select two/three atoms defining rotation axis.'
            lib.MessageBoxOK(mess,'Bond Rotation(OnSetPoints)')
            return
        elif nsel == 2:
            p1=lst[0]; p2=lst[1]
            name=self.PackName(p1,p2)
            if [p1,p2] in self.axislst: self.CheckName(name)
            if [p2,p1] in self.axislst: self.CheckName(name)

            self.SetAxis(p1,p2)
        
    def SetAxis(self,p1,p2,arrow=True):
        if p1 < 0 or p2 < 0:
            mess='Axis is not defined.'
            lib.MessageBoxOK(mess,'Bond Rotation(AppendPoints)')
            return
        self.p1=p1; self.p2=p2
        name=self.PackName(self.p1,self.p2)
        #self.tclpnts.SetValue(name)
        #
        if not [p1,p2] in self.axislst and not [p2,p1] in self.axislst:
            self.axislst.append([self.p1,self.p2])
            self.ClearCheckBoxPanel()
            self.SetAxisCheckBoxes()
        #
        self.curname=name
        self.CheckName(self.curname,True)
        """
        if self.buildmode: 
            self.SetRotationAxis(self.p1,self.p2)
            self.model.mousectrl.SetMouseMode(7,delarrow=False)
            # select movable atoms
            nmove=self.SelectMovableAtoms(self.p1,self.p2,drw=False)
            #if nmove <= 0: return
            if self.shwtorsion:
                # draw torsion angle and elemnt names
                pnts14=self.model.Find14Atoms(self.p1,self.p2)
                if len(pnts14) > 0:
                    self.model.ctrlflag.Set('draw-torsion-angle',pnts14)
                    ###self.model.DrawLabelElm(True,-1,atmlst=[p11,self.p1,self.p2,p22],drw=False)
                else:
                    self.model.ctrlflag.Del('draw-torsion-angle')
                    #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
                    self.model.DrawLabelAtm(False,-1,drw=False)
        # beep when short contact occurs
        if self.beep: self.ctrlflag.Set('beep-short-contact',self.shortdistance)
        else: self.ctrlflag.Del('beep-short-contact')            
        pntlst=[]; pntlst.append([self.p1,self.p2])
        if arrow: self.DrawRotationAxis(pntlst)
        """
        
    def OnRotAxisPanel(self,event):
        obj=event.GetEventObject()
        self.rotaxispan=obj.GetValue()
        self.panel.Destroy()
        self.CreatePanel()
            
    def OnRigidBodyPanel(self,event):
        obj=event.GetEventObject()
        self.rigidbodypan=obj.GetValue()
        self.panel.Destroy()
        self.CreatePanel()
        
    def SetAxisCheckBoxes(self):
        if len(self.axischkboxdic) > 0: self.ClearCheckBoxPanel()
        yloc=8
        for p1,p2 in self.axislst:
            name=self.PackName(p1,p2) #str(p1+1)+':'+str(p2+1)
            chkbox=wx.CheckBox(self.rotpan,-1,name,pos=[10,yloc])
            self.axischkboxdic[name]=chkbox
            chkbox.Bind(wx.EVT_CHECKBOX,self.OnCheckBox)
            yloc += 20
        self.CheckName(self.curname,True)
        self.rotpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
    
    def ClearCheckBoxPanel(self):
        for name,obj in self.axischkboxdic.iteritems(): obj.Destroy()
        self.axischkboxdic={}
        self.curname=''
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)

    def OnSetGroup(self,event):
        nsel,lst=self.model.ListSelectedAtom()
        if nsel < 0:
            mess='Please select atoms for defining rigid-body group.'
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnSetGroup)')
            return
        
        grpnam='group'+'%04d' % len(self.grouplst)
        
        
        self.grplst.append(grpnam)
        p1=lst[0]; p2=lst[1]
        name=self.PackName(p1,p2)
        if [p1,p2] in self.axislst: self.CheckName(name)
        if [p2,p1] in self.axislst: self.CheckName(name)

        self.SetAxis(p1,p2)
 
    def SetGroupCheckBoxes(self):
        if len(self.axischkboxdic) > 0: self.ClearCheckBoxPanel()
        yloc=8
        for p1,p2 in self.axislst:
            name=self.PackName(p1,p2) #str(p1+1)+':'+str(p2+1)
            chkbox=wx.CheckBox(self.pntpan,-1,name,pos=[10,yloc])
            self.axischkboxdic[name]=chkbox
            chkbox.Bind(wx.EVT_CHECKBOX,self.OnCheckBox)
            yloc += 20
        self.CheckName(self.curname,True)
        self.grppan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
    
    def OnRemove(self,event):
        dellst=self.GetCheckedList()
        self.Remove(dellst)

    def Remove(self,dellst):
        for name in dellst:
            #del self.axischkboxdic[name]
            items=lib.SplitStringAtSeparator(name,':')            
            p1=int(items[0])-1
            p2=int(items[1])-1
            self.axislst.remove([p1,p2])
        self.SetAxisCheckBoxes()
        self.model.DrawAxisArrow(False,[])
        self.tclpnts.SetValue('')
        self.curname=''

    def GetCheckedList(self):
        checkedlst=[]
        for name,obj in self.axischkboxdic.iteritems():
            if obj.GetValue(): checkedlst.append(name)
        return checkedlst

    def OnClearAll(self,event):
        self.ClearCheckBoxPanel()
        self.axislst=[]
        self.tclpnts.SetValue('')
        self.curname=''
        self.model.DrawAxisArrow(False,[])
        
    def OnCheckAll(self,event):
        # ToggleButton
        self.btnchk.GetValue()
        value=False
        if self.btnchk.GetValue(): 
            value=True; self.curname=self.axislst[0] # #Check all, else uncheck all
        else: self.curname=''
        for name,obj in self.axischkboxdic.iteritems(): obj.SetValue(value)
    
    def CheckName(self,name,on):
        if name == '': return
        if on: value=True
        else: value=False
        for pntnam,obj in self.axischkboxdic.iteritems():
            if pntnam == name: obj.SetValue(value)

    def OnCheckOne(self,event):
        return
        #self.checkone=self.ckbone.GetValue()
        #self.SetSelectButtonStatus()

    def PackName(self,p1,p2):
        return str(p1+1)+':'+str(p2+1)    
    
    def PackName3(self,p1,p2,p3):
        return str(p1+1)+':'+str(p2+1)+':'+str(p3+1)
    
    def UnpackName3(self,name):
        p1=-1; p2=-1; p3=-1
        items=lib.SplitStringAtSeparator(name,':')
        try: p1=int(items[0])-1
        except: pass
        try: p2=int(items[1])-1
        except: pass
        try: p3=int(items[2])-1
        except: pass  
        return p1,p2,p3
        
    def GetPoints(self):
        p1=-1; p2=-1
        name=self.tclpnts.GetValue()
        p1,p2=self.UnpackName(name)
        if p1 < 0 or p2 < 0:            
            mess='Error in input text. Please input two numbers separated by'
            mess=mess+' "-"'
            lib.MessageBoxOK(mess,'BondRotate(GetPoints)')
        return p1,p2
    
    
    def OnThreadJobEnded(self,event):
        pass
        
    def OnDefRigidBody(self,event):
        pass
    
    def OnOptProgram(self,event):
        pass
    
    def SetOptMethod(self,method):
        self.method=method
        self.cmbmet.SetStringSelection(self.method)    
    
    def OnApply(self,event):
        pass
    
    def OnEdit(self,event):
        pass
    
    def OnClose(self,event):
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        try: self.Destroy()
        except: pass
    
    def OnReset(self,event):
        pass
    
    def OnOverlay(self,event):
        pass
    
    def OnExecute(self,event):
        pass
    
    def OnRMSFit(self,event):
        pass
    
    def SetOptProgram(self):
        pass
    
    def OnVariable(self,event):
        obj=event.GetEventObject()
        self.var=obj.GetStringSelection()
        self.btnset.SetLabel(self.varbuttondic[self.var])
    
    def OnResize(self,event):
        self.panel.Destroy()
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])        
        self.CreatePanel()
        
    def MenuItems(self):
        #menuhelpdic={} 
        menubar=wx.MenuBar()
        # Option
        submenu1=wx.Menu()
        iid=wx.NewId()
        submenu1.Append(iid,'Show torsion angle','Show torsion angle.',
                        kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.shwtorsion)

        #submenu.AppendSeparator()
        submenu1.Append(-1,'Mouse sensitivity','Set mouse sensitivity.')
        
        iid=wx.NewId()
        submenu1.Append(iid,'Beep when short contact occured',
                        'Beep when short contact ocurrs.',kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.beep)
        
        
        submenu1.Append(-1,'Short contact distance',
                        'Input short contact distance.',kind=wx.ITEM_CHECK)
        
        
        iid=wx.NewId()
        
        submenu1.Append(iid,"Single bond only for rotatable bonds","",
                        kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.singlebondonly)
        menubar.Append(submenu1,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Open document.')
        helpname=self.winlabel
        submenu.Append(-1,'Tutorial','Open tutorial panel.')
        # related functions
        #submenu.AppendSeparator()
        #subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"ZmtViewer",
        #                  "View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,'Help')

        """ test """
        #menubar.Bind(wx.EVT_HELP,self.OnMenuHelp)
        
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # Option
        if item == "Show torsion angle": self.shwtorsion=bChecked
        elif item == "Mouse sensitivity": self.SetSensitive()
        elif item == "Single bond only for rotatable bonds": 
            self.SetSingleBondOnly()
        elif item == "Beep when short contact occured": self.Beep(bChecked)
        elif item == "Short contact distance": self.ShortContactDistance()
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == "ZmtViewer": self.OpenZmtViewer()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()
        # Help
        elif item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()
                        
class SetModelingGroup_Frm(wx.Frame):
    def __init__(self,parent,id,model,winpos=[]):
        self.title='Define Groups for Modeling'
        if len(winpos) <= 0: winpos=[-1,-1]
        self.winsize=lib.WinSize((260,340))
        #if const.SYSTEM == const.MACOSX: winsize=(275,355)
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,\
               size=self.winsize,style=wx.SYSTEM_MENU|wx.CAPTION|\
               wx.CLOSE_BOX|wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)      
        #self.fum=fum
        self.parent=parent
        self.model=model
        self.mdlwin=self.model.mdlwin
        self.ctrlflag=self.model.ctrlflag
        #
        if not self.model.mol:
            mess='No molecule data. Open pdb/xyz file in fumodel.'
            lib.MessageBoxOK(mess,"")
            self.OnClose(1)                       
        self.mol=self.model.mol
        self.molnam=self.mol.name
        self.molnam,ext=os.path.splitext(self.molnam)
        scriptdir=self.model.setctrl.GetDir('Scripts')
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        self.winlabel='SetModelingGroupWin'
        self.model.winctrl.SetOpenWin(self.winlabel,self)
        # Menu
        menud=self.MenuItems()
        self.SetMenuBar(menud) # self.menubar.menuitem)
        self.Bind(wx.EVT_MENU,self.OnMenu)

        #
        self.var="rotation angles"
        self.varlst=["rotation angles","rigid body"]
        self.varbuttondic={"rotation angles":'Set axis',
                           "rigid body":'Set group'}
        #
        self.curgrp=''
        self.groupatmdic={} # {group#:[atm1,atm2,...],...}
        self.axisdic={} # {group#:[[atm1,atm2],...],...}
        self.vardic={} # {group#:[center,orientation],...}
        self.optvarorder=[]
        self.optgrouporder=[]
        
        #
        self.axislst=[]
        self.axischkboxdic={}
        self.curname=''
        self.rotpanheight=120
        self.grouppanheight=120
        self.p1=-1; self.p2=-1
        #
        self.grplst=[]
        self.grpchkboxdic={}
        #
        self.CreatePanel()
        
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Show()
    
    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        xsize=w; ysize=h
        self.grouppanheight=120
        
        hbtn=22; hcmd=200
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        hcb=const.HCBOX
        
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        yloc=10
        self.CreateGroupPanel(yloc,self.grouppanheight)
        yloc += self.grouppanheight+5
        
        wx.StaticLine(self.panel,pos=(20,yloc),size=(w-40,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 10
        
        self.stgrp=wx.StaticText(self.panel,-1,"Variables in "+self.curgrp,
                                 pos=(20,yloc),size=(100,18))                 

        self.rotpanheight=h-self.grouppanheight-90

        yloc += 25

        self.CreateRotAxisPanel(yloc,self.rotpanheight)
        yloc += self.rotpanheight+5
        #if self.rigidbodypan:
        yloc=h-35
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        xloc=40
        btnedit=wx.Button(self.panel,-1,"Edit",pos=(xloc,yloc),size=(50,hbtn))
        btnedit.Bind(wx.EVT_BUTTON,self.OnEdit)
        btnedit.SetToolTipString('Set rotatable bonds to the list. Takes time for large molecule!')
        

        btnaply=wx.Button(self.panel,-1,"Apply",pos=(xloc+70,yloc),
                          size=(60,hbtn))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        btnaply.SetToolTipString('Set rotatable bonds to the list. Takes time for large molecule!')
        
        btncls=wx.Button(self.panel,-1,"Close",pos=(xloc+150,yloc),
                         size=(60,hbtn))
        btncls.Bind(wx.EVT_BUTTON,self.OnClose)
        
    def CreateRotAxisPanel(self,yloc,height):
        hbtn=22
        wx.StaticText(self.panel,-1,"Rotation axis:",pos=(35,yloc),
                      size=(80,18))
        btnset=wx.Button(self.panel,-1,"Set selected atoms",pos=(130,yloc-2),
                         size=(120,hbtn))
        btnset.Bind(wx.EVT_BUTTON,self.OnSetAxis)
        wpan=130; hpan=height-50 #hpan=h-yloc-hcmd-30
        xloc=5
        yloc += 25
        self.rotpan=wx.ScrolledWindow(self.panel,-1,pos=[xloc+30,yloc],
                                      size=[wpan,hpan]) #,
        self.rotpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
        self.rotpan.SetBackgroundColour('white')
        self.SetAxisCheckBoxes()
        self.rotpan.SetScrollRate(5,20)
        xloc1=xloc+wpan+45
        btnauto=wx.Button(self.panel,-1,"Auto set",pos=(xloc1,yloc),
                          size=(60,hbtn))
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnauto.SetToolTipString(mess)
        #btnauto.Bind(wx.EVT_BUTTON,self.OnAutoSet)
        yloc += 25
        btnrmv=wx.Button(self.panel,-1,"Remove",pos=(xloc1,yloc),
                         size=(60,hbtn))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove)
        btnrmv.SetToolTipString('Remove checked data from the list')
        yloc += 25
        btnclr=wx.Button(self.panel,-1,"ClearAll",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearAll)
        btnclr.SetToolTipString('Clear the list')
        yloc += hpan-40
        wx.StaticText(self.panel,-1,"Optimize:",pos=(30,yloc),size=(50,18))                 
        xloc=90

        self.rbtseqrotopt=wx.RadioButton(self.panel,-1,"Sequential",
                                         pos=(xloc,yloc),style=wx.RB_GROUP)
        self.rbtseqrotopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptRotSequential)
       
        self.rbtallrotopt=wx.RadioButton(self.panel,-1,"Simultaneouse",
                                         pos=(xloc+80,yloc))
        self.rbtallrotopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptRotSimultanious)
        mess='Rotation angle around axis defined by two selected atoms.'
        self.rbtallrotopt.SetToolTipString(mess)

    def CreateGroupPanel(self,yloc,height):
        hbtn=22
        wx.StaticText(self.panel,-1,"Group:",pos=(20,yloc),size=(100,18))                 
        btnset=wx.Button(self.panel,-1,"Set selected atoms",pos=(130,yloc-2),
                         size=(120,hbtn))
        wpan=130; hpan=height-50 #hpan=h-yloc-hcmd-30
        xloc=5
        yloc += 25
        self.grppan=wx.ScrolledWindow(self.panel,-1,pos=[xloc+30,yloc],
                                      size=[wpan,hpan]) #,
        self.grppan.SetScrollbars(1,1,0,(len(self.grplst)+1)*20)
        self.grppan.SetBackgroundColour('white')
        self.SetGroupCheckBoxes()
        self.grppan.SetScrollRate(5,20)
        xloc1=xloc+wpan+45
        btnauto=wx.Button(self.panel,-1,"Auto set",pos=(xloc1,yloc),
                          size=(60,hbtn))
        mess='Set rotatable bonds to the list. Takes time for large molecule!'
        btnauto.SetToolTipString(mess)
        #btnauto.Bind(wx.EVT_BUTTON,self.OnAutoSet)
        yloc += 25
        btnrmv=wx.Button(self.panel,-1,"Remove",pos=(xloc1,yloc),
                         size=(60,hbtn))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemove)
        btnrmv.SetToolTipString('Remove checked data from the list')
        yloc += 25
        btnclr=wx.Button(self.panel,-1,"ClearAll",pos=(xloc1,yloc),
                         size=(60,hbtn))        
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearAll)
        btnclr.SetToolTipString('Clear the list')
        yloc += 30
        wx.StaticText(self.panel,-1,"Optimize:",pos=(30,yloc),size=(50,18))                 
        xloc=90

        self.rbtseqgrpopt=wx.RadioButton(self.panel,-1,"Sequential",
                                         pos=(xloc,yloc),style=wx.RB_GROUP)
        self.rbtseqgrpopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptGroupSequential)
       
        self.rbtallgrpopt=wx.RadioButton(self.panel,-1,"Simultaneouse",
                                         pos=(xloc+80,yloc))
        self.rbtallgrpopt.Bind(wx.EVT_RADIOBUTTON,self.OnOptGroupSimultanious)
        mess='Rotation angle around axis defined by two selected atoms.'
        self.rbtallgrpopt.SetToolTipString(mess)

    def OnOptGroupSequential(self,event):
        pass
    def OnOptGroupSimultanious(self,event):
        pass
    
    def OnOptRotSequential(self,event):
        pass
    def OnOptRotSimultanious(self,event):
        pass
    
    def OnSetAxis(self,event):
        nsel,lst=self.model.ListSelectedAtom()
        if nsel < 2:
            mess='Please select two/three atoms defining rotation axis.'
            lib.MessageBoxOK(mess,'Bond Rotation(OnSetPoints)')
            return
        elif nsel == 2:
            p1=lst[0]; p2=lst[1]
            name=self.PackName(p1,p2)
            if [p1,p2] in self.axislst: self.CheckName(name)
            if [p2,p1] in self.axislst: self.CheckName(name)

            self.SetAxis(p1,p2)
        
    def SetAxis(self,p1,p2,arrow=True):
        if p1 < 0 or p2 < 0:
            mess='Axis is not defined.'
            lib.MessageBoxOK(mess,'Bond Rotation(AppendPoints)')
            return
        self.p1=p1; self.p2=p2
        name=self.PackName(self.p1,self.p2)
        #self.tclpnts.SetValue(name)
        #
        if not [p1,p2] in self.axislst and not [p2,p1] in self.axislst:
            self.axislst.append([self.p1,self.p2])
            self.ClearCheckBoxPanel()
            self.SetAxisCheckBoxes()
        #
        self.curname=name
        self.CheckName(self.curname,True)
        """
        if self.buildmode: 
            self.SetRotationAxis(self.p1,self.p2)
            self.model.mousectrl.SetMouseMode(7,delarrow=False)
            # select movable atoms
            nmove=self.SelectMovableAtoms(self.p1,self.p2,drw=False)
            #if nmove <= 0: return
            if self.shwtorsion:
                # draw torsion angle and elemnt names
                pnts14=self.model.Find14Atoms(self.p1,self.p2)
                if len(pnts14) > 0:
                    self.model.ctrlflag.Set('draw-torsion-angle',pnts14)
                    ###self.model.DrawLabelElm(True,-1,atmlst=[p11,self.p1,self.p2,p22],drw=False)
                else:
                    self.model.ctrlflag.Del('draw-torsion-angle')
                    #self.model.DrawLabelElm(False,-1,atmlst=[],drw=False)
                    self.model.DrawLabelAtm(False,-1,drw=False)
        # beep when short contact occurs
        if self.beep: self.ctrlflag.Set('beep-short-contact',self.shortdistance)
        else: self.ctrlflag.Del('beep-short-contact')            
        pntlst=[]; pntlst.append([self.p1,self.p2])
        if arrow: self.DrawRotationAxis(pntlst)
        """
        
    def OnRotAxisPanel(self,event):
        obj=event.GetEventObject()
        self.rotaxispan=obj.GetValue()
        self.panel.Destroy()
        self.CreatePanel()
            
    def OnRigidBodyPanel(self,event):
        obj=event.GetEventObject()
        self.rigidbodypan=obj.GetValue()
        self.panel.Destroy()
        self.CreatePanel()
        
    def SetAxisCheckBoxes(self):
        if len(self.axischkboxdic) > 0: self.ClearCheckBoxPanel()
        yloc=8
        for p1,p2 in self.axislst:
            name=self.PackName(p1,p2) #str(p1+1)+':'+str(p2+1)
            chkbox=wx.CheckBox(self.rotpan,-1,name,pos=[10,yloc])
            self.axischkboxdic[name]=chkbox
            chkbox.Bind(wx.EVT_CHECKBOX,self.OnCheckBox)
            yloc += 20
        self.CheckName(self.curname,True)
        self.rotpan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
    
    def ClearCheckBoxPanel(self):
        for name,obj in self.axischkboxdic.iteritems(): obj.Destroy()
        self.axischkboxdic={}
        self.curname=''
        self.model.menuctrl.OnSelect("2-objects",True)
        self.model.menuctrl.OnSelect("Atom",True)

    def OnSetGroup(self,event):
        nsel,lst=self.model.ListSelectedAtom()
        if nsel < 0:
            mess='Please select atoms for defining rigid-body group.'
            lib.MessageBoxOK(mess,'RigidBodyOptimizer(OnSetGroup)')
            return
        
        grpnam='group'+'%04d' % len(self.grouplst)
        
        
        self.grplst.append(grpnam)
        p1=lst[0]; p2=lst[1]
        name=self.PackName(p1,p2)
        if [p1,p2] in self.axislst: self.CheckName(name)
        if [p2,p1] in self.axislst: self.CheckName(name)

        self.SetAxis(p1,p2)
 
    def SetGroupCheckBoxes(self):
        if len(self.axischkboxdic) > 0: self.ClearCheckBoxPanel()
        yloc=8
        for p1,p2 in self.axislst:
            name=self.PackName(p1,p2) #str(p1+1)+':'+str(p2+1)
            chkbox=wx.CheckBox(self.pntpan,-1,name,pos=[10,yloc])
            self.axischkboxdic[name]=chkbox
            chkbox.Bind(wx.EVT_CHECKBOX,self.OnCheckBox)
            yloc += 20
        self.CheckName(self.curname,True)
        self.grppan.SetScrollbars(1,1,0,(len(self.axislst)+1)*20)
    
    def OnRemove(self,event):
        dellst=self.GetCheckedList()
        self.Remove(dellst)

    def Remove(self,dellst):
        for name in dellst:
            #del self.axischkboxdic[name]
            items=lib.SplitStringAtSeparator(name,':')            
            p1=int(items[0])-1
            p2=int(items[1])-1
            self.axislst.remove([p1,p2])
        self.SetAxisCheckBoxes()
        self.model.DrawAxisArrow(False,[])
        self.tclpnts.SetValue('')
        self.curname=''

    def GetCheckedList(self):
        checkedlst=[]
        for name,obj in self.axischkboxdic.iteritems():
            if obj.GetValue(): checkedlst.append(name)
        return checkedlst

    def OnClearAll(self,event):
        self.ClearCheckBoxPanel()
        self.axislst=[]
        self.tclpnts.SetValue('')
        self.curname=''
        self.model.DrawAxisArrow(False,[])
        
    def OnCheckAll(self,event):
        # ToggleButton
        self.btnchk.GetValue()
        value=False
        if self.btnchk.GetValue(): 
            value=True; self.curname=self.axislst[0] # #Check all, else uncheck all
        else: self.curname=''
        for name,obj in self.axischkboxdic.iteritems(): obj.SetValue(value)
    
    def CheckName(self,name,on):
        if name == '': return
        if on: value=True
        else: value=False
        for pntnam,obj in self.axischkboxdic.iteritems():
            if pntnam == name: obj.SetValue(value)

    def OnCheckOne(self,event):
        return
        #self.checkone=self.ckbone.GetValue()
        #self.SetSelectButtonStatus()

    def PackName(self,p1,p2):
        return str(p1+1)+':'+str(p2+1)    
    
    def PackName3(self,p1,p2,p3):
        return str(p1+1)+':'+str(p2+1)+':'+str(p3+1)
    
    def UnpackName3(self,name):
        p1=-1; p2=-1; p3=-1
        items=lib.SplitStringAtSeparator(name,':')
        try: p1=int(items[0])-1
        except: pass
        try: p2=int(items[1])-1
        except: pass
        try: p3=int(items[2])-1
        except: pass  
        return p1,p2,p3
        
    def GetPoints(self):
        p1=-1; p2=-1
        name=self.tclpnts.GetValue()
        p1,p2=self.UnpackName(name)
        if p1 < 0 or p2 < 0:            
            mess='Error in input text. Please input two numbers separated by '
            mess=mess+'"-"'
            lib.MessageBoxOK(mess,'BondRotate(GetPoints)')
        return p1,p2
    
    
    def OnThreadJobEnded(self,event):
        pass
        
    def OnDefRigidBody(self,event):
        pass
    
    def OnOptProgram(self,event):
        pass
    
    def SetOptMethod(self,method):
        self.method=method
        self.cmbmet.SetStringSelection(self.method)    
    
    def OnApply(self,event):
        pass
    
    def OnEdit(self,event):
        pass
    
    def OnClose(self,event):
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        try: self.Destroy()
        except: pass
    
    def OnReset(self,event):
        pass
    
    def OnOverlay(self,event):
        pass
    
    def OnExecute(self,event):
        pass
    
    def OnRMSFit(self,event):
        pass
    
    def SetOptProgram(self):
        pass
    
    def OnVariable(self,event):
        obj=event.GetEventObject()
        self.var=obj.GetStringSelection()
        self.btnset.SetLabel(self.varbuttondic[self.var])
    
    def OnResize(self,event):
        self.panel.Destroy()
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])        
        self.CreatePanel()
        
    def MenuItems(self):
        #menuhelpdic={} 
        menubar=wx.MenuBar()
        # Option
        submenu1=wx.Menu()
        iid=wx.NewId()
        submenu1.Append(iid,'Show torsion angle','Show torsion angle.',
                        kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.shwtorsion)

        #submenu.AppendSeparator()
        submenu1.Append(-1,'Mouse sensitivity','Set mouse sensitivity.')
        
        iid=wx.NewId()
        submenu1.Append(iid,'Beep when short contact occured',
                        'Beep when short contact ocurrs.',kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.beep)
        
        
        submenu1.Append(-1,'Short contact distance',
                        'Input short contact distance.',kind=wx.ITEM_CHECK)
        
        
        iid=wx.NewId()
        
        submenu1.Append(iid,"Single bond only for rotatable bonds","",
                        kind=wx.ITEM_CHECK)
        #submenu1.Check(iid,self.singlebondonly)
        menubar.Append(submenu1,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Open document.')
        helpname=self.winlabel
        submenu.Append(-1,'Tutorial','Open tutorial panel.')
        # related functions
        #submenu.AppendSeparator()
        #subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"ZmtViewer",
        #                  "View geometrical paramters in z-matrix form")
        #subsubmenu.AppendSeparator()
        #subsubmenu.Append(-1,"TINKER","Minimization with TINKER")
        #subsubmenu.Append(-1,"GAMESS","Minimization with GAMESS")
        #submenu.AppendMenu(-1,'Related functions',subsubmenu)
        menubar.Append(submenu,'Help')

        """ test """
        #menubar.Bind(wx.EVT_HELP,self.OnMenuHelp)
        
        return menubar
    
    def OnMenu(self,event):
        """ Menu handler
        """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # Option
        if item == "Show torsion angle": self.shwtorsion=bChecked
        elif item == "Mouse sensitivity": self.SetSensitive()
        elif item == "Single bond only for rotatable bonds": 
            self.SetSingleBondOnly()
        elif item == "Beep when short contact occured": self.Beep(bChecked)
        elif item == "Short contact distance": self.ShortContactDistance()
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()
        elif item == "ZmtViewer": self.OpenZmtViewer()
        elif item == "TINKER": self.ExecTinker()
        elif item == 'GAMESS': self.ExecGAMESS()
        # Help
        elif item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()
        
class XXNonBondIntE():
    def __init__(self,model,title=''):
        """ Charge equilibration method:
            A. K. Pappe and W. A. Goddard III, J.Phys.Chem.,3358(1991).   
            modified to use NM-gamma for electron-electron repulsion:
            T.Nakano,T.Kaminuma,M.Uebayasi,Y.Nakata, Chem-Bio Info.J.,1,35(2001).
       
        :param str title: title
        :param float charge: total charge of molecule
        :param lst xyzatm: [[elm(str*2),x(float),y(float),z(float)],...]
        """
        const.CONSOLEMESSAGE('Entered in NonBondIntE') 
        
        self.prgnam='nonbond-inte ver. 0.1'
        self.model=model
        #
        fudir=self.model.setctrl.GetDir('FUdata')
        self.ljprmfile=os.path.join(fudir,'lj.prm')
        #         
        self.atmchg=[]
        # should move in Initialize     
        self.ljprmdic=self.ReadLJParams(self.ljprmfile)
        const.CONSOLEMESSAGE('ljprmdic='+str(self.ljprmdic))
        # add tip3p params('OW' and 'HW')
        vdwprmdic={}
        vdwprmdic['OW']=[1.7683,0.1520]
        vdwprmdic['HW']=[0.0,0.0]
        
        
        chgfile='E://FUDATASET//FUdocs//data//ethanol-h2o.chg'
        #chgfilelst=[ethanolchgfile] # <--- isolated groups
        
        self.Initialize()
        
        self.vdwprmdic=self.ljprmdic 
        #for chgfile in chgfilelst:
        resnam,charge,scale,self.atmchglst=self.ReadAtomCharges(chgfile)
        #    atmchgdic[resnam]=[charge,scale,chglst]
        # append tip3p charge (assume the atom orderto be  O-H-H)
        #atmchgdic['TIP3P']=[0.0,1.0,[-0.400,0.200,0.200]]          
        const.CONSOLEMESSAGE('atmchglst='+str(self.atmchglst))
        
        
        const.CONSOLEMESSAGE('vdwprmdic='+str(self.vdwprmdic))
        
        #
                
        self.active=[]
        nsel,self.active=self.model.ListSelectedAtom()
        const.CONSOLEMESSAGE('active='+str(self.active))
        ###self.vdwprmdic=self.SetvdWParams()
        
        ###self.xyzatm,bonds,resfrg=rwfile.ReadXYZMol(xyzfile)
        ###self.natm=len(self.xyzatm)
        
        #self.vdwprm=self.AssignLJParamToAtom()
        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        const.CONSOLEMESSAGE('etot='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele))
        const.CONSOLEMESSAGE('evdw='+str(evdw))
        const.CONSOLEMESSAGE('gtot='+str(gtot))
        const.CONSOLEMESSAGE('gtot='+str(gele))
        const.CONSOLEMESSAGE('gvdw='+str(gvdw))
        
        self.x0=len(self.active)*[0.0]
        self.Optimize()
        """
        self.an=self.CheckParams()       
        """
        """
        self.time1=time.clock()
        #self.distlst=self.ComputeDistance()
        #self.q=self.SolveQEqEq()
        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele))
        const.CONSOLEMESSAGE('evdw='+str(evdw))
        #const.CONSOLEMESSAGE('gtot='+str(gtot))
        #const.CONSOLEMESSAGE('gele='+str(gele))
        #const.CONSOLEMESSAGE('gvdw='+str(gvdw))
        x0=[]
        self.Optimize(x0,method='',epslst=[],optndic={})
        
        self.time2=time.clock()
        
        etime=self.time2-self.time1
        const.CONSOLEMESSAGE('etime(sec.)='+str(etime))
        ###self.WritevdWParams(outfile)
        """
        
    def Initialize(self):
        const.CONSOLEMESSAGE('Entered in Initialize') 
        # temp mol object
        self.opt=self.model.mol.CopyMolecule()
        const.CONSOLEMESSAGE('Initialize #1') 
        self.natm=len(self.opt.atm)
        # set variables
        self.grplst=[] #['c2h5oh','h2o'] #['fkbp','k506'] # group name list
        self.grpatmlstdic={} # {grpnam:atmidxlst,...}
        self.grpchgfiledic={}
        self.grpvardic={} #{'h2o':[True,True,[]]} # {grpnam:[True(center),True(orientation),[atmi,atmj,[movelst](rotaxis),..],...]
        self.grpvarvaldic={} # {grpnam:[center:cc, orient:alpha,,beta,gamma],[angle1,...]],...}
        self.rotatmlstdic={}
        #self.active=[]; 
        self.activeatmlst=[]; self.inactiveatmlst=[]
        #self.ljprmdic={}
        #self.vdwprmdic={}
        #self.atmchglst=[]
        self.method='CG'
        self.optndic={}
        self.optndic['maxiter']=1000
        self.optndic['gtol']=0.1 # 1e-2
        self.optndic['disp']=True
        const.CONSOLEMESSAGE('Initialize #2') 
    
    def SetRigidBodyData(self,grplst,grpatmlstdic,grpvardic,rotatmlstdic):
        const.CONSOLEMESSAGE('Entered SetRigidBodyData') 
        self.grplst=grplst #['fkbp','k506'] # group name list
        self.grpatmlstdic=grpatmlstdic # {grpnam:atmidxlst,...}
        self.grpvardic=grpvardic # {grpnam:[True(center),True(orientation),[atmi,atmj,[movelst](rotaxis),..],...]
        self.rotatmlstdic=rotatmlstdic # {rotnam('p1-p2':[movable atmlst],...}
        #
        const.CONSOLEMESSAGE('SetRigidBodyData #1') 
        
        self.SetVariables()
        
        const.CONSOLEMESSAGE('SetRigidBodyData #3') 
    
    def SetNonBondParams(self,ljprmdic,atmchglst):
        self.atmchglst=atmchglst #['c2h5oh']='E://FUDATASET//FUdocs//data//ethanol.chg'
        self.ljprmdic=ljprmdic
        self.SetElement()
        self.vdwprmdic=self.SetvdWParams(self.ljprmdic)

        const.CONSOLEMESSAGE('SetNonBondParams atmchglst='+str(self.atmchglst))         
        
    def SetOptMethod(self,method,gconv,maxiter):
        self.method=method
        self.optndic['gtol']=gconv
        self.optndic['maxiter']=maxiter
        
    def SetVariables(self):
        #self.varnamlst=[]; self.varvallst=[]
        self.x0=[]; epslst=[]; self.activeatmlst=[]; self.inactiveatmlst=[]
        for grpnam in self.grplst:
            const.CONSOLEMESSAGE('SetVariables # 1 grpnam='+grpnam)
            center=False
            if self.grpvardic.has_key(grpnam):
                if self.grpvardic[grpnam][0]: # center-of-mass            
                    #self.varnamlst.append(grpnam+':center')
                    self.x0=self.x0+[0.0,0.0,0.0]
                    epslst=epslst+[0.1,0.1,0.1]
                    const.CONSOLEMESSAGE('grpnam='+str(self.grpatmlstdic.keys()))
                    self.activeatmlst=\
                                    self.activeatmlst+self.grpatmlstdic[grpnam]         
                const.CONSOLEMESSAGE('SetVariables # 2')
                if self.grpvardic[grpnam][1]: # orientation   
                    #self.varnamlst.append(grpnam+':orientation')
                    #abg=self.ComputeEulerAngles(grpnam,comcc)
                    #self.varvallst.append(abg)
                    
                    self.x0=self.x0+[0.0,0.0,0.0]
                    epslst=epslst+[0.01,0.01,0.01]
                    if not center: self.acriveatmlst=\
                                    self.activeatmlst+self.grpatmlstdic[grpnam]         
                const.CONSOLEMESSAGE('SetVariables # 3')    
                if len(self.grpvardic[grpnam][2]) > 0:
                    for i,j,movatmlst in self.grpvardic[grpnam][2]:
                        if len(movatmlst) <= 0: continue
                        varnam=str(i)+':'+str(j)
                        #self.varnamlst.append(varnam) # rot-axsis variable
                        #self.rotmovatmlstdic[varnam]=moveatmlst
                        #angle=self.ComputeRotAngle(grpnam,i,j,movatmlst)
                        angle=0.0
                        #self.varvallst.append(angle)
                        self.x0=self.x0+[0.0]
                        epslst=epslst+[0.01]                       
        
        self.nactive=len(self.activeatmlst)
        for i in range(len(self.model.mol.atm)):
            if not i in self.activeatmlst: self.inactiveatmlst.append(i)
        self.ninactive=len(self.inactiveatmlst)
        
        const.CONSOLEMESSAGE('SetVariables # 4')
        #self.x0=x0
        self.optndic['eps']=epslst
        #               
        const.CONSOLEMESSAGE('x0='+str(self.x0))        
        # set initial value of variable
        
    def ComputeEulerAngles(self,grpnam,comcc):
        xyz=[]
        
        
        
        return xyz
    
    def ComputeRotAngle(self,grpnam,atmi,atmj):
        angle=0.0
        
        
        return angle
     
    def SetElement(self):
        self.elm=[]
        for atom in self.model.mol.atm:
            elm=atom.elm; res=atom.resnam
            if res in const.WaterRes:
                if elm == ' O': self.elm.append('OW')
                elif elm == ' H': self.elm.append('HW')
            else: self.elm.append(elm)
    
    def SetAtomCharges(self):
        atmchglst=[]
        if resnam in const.WaterRes:
            pass # water
        
    
        return atmchglst
    

    def SetvdWParams(self,ljprmdic,vdwgeom=True):
        # geometric combination rule
        #    [rad]  radij=2.0*(sqrt(radi*sqrt(radj)
        #    [epsilon] epsij=sqrt(epsi)*sqrt(epsj)
        # 'arithmeric' combination rule
        #    [rad] radij=radi+radj
        #    [epsi lon] radij=0.5*(epsi+epsj)

        # add tip3p params('OW' and 'HW')
        ljprmdic['OW']=[1.7683,0.1520]
        ljprmdic['HW']=[0.0,0.0]
        const.CONSOLEMESSAGE('SetvdWParams. ljprmdic='+str(ljprmdic))
        # check params
        missprm=[]
        #elmlst=self.model.ListElement()
        for elm in self.elm:
            if not elm in ljprmdic: misselm.append(elm)        
        if len(missprm) > 0:
            mess='vdW paramtere is not found for element(s): '+misselm+'\n'
            mess=mess+'Define the paramter(s) in ".prm" file.'
            lib.MessageBoxOK(mess,'NonBondIntE(SetvdWParams)')
            return
        #
        vdwprmdic={}; sq2=numpy.sqrt(2.0); pt5=0.5; twosq6=1.122462048309372981
        for elm, prm in ljprmdic.iteritems():
            f=twosq6
            if not vdwgeom: f=0.5
            rad=f*ljprmdic[elm][0]
            eps=ljprmdic[elm][1]
            if vdwgeom: vdwprmdic[elm]=[numpy.sqrt(rad),numpy.sqrt(eps)]
            else: vdwprmdic[elm]=[rad,pt5*eps]         
        return vdwprmdic
    
    def ComputeDistance2(self):
        const.CONSOLEMESSAGE('ComputeDistance2 self.nactive='+str(self.nactive))
        #const.CONSOLEMESSAGE('ComputeDistance2 self.innactive='+str(self.ninactive))

        r2lst=[]; lst=self.natm*[0.0]
        for i in range(self.nactive): r2lst.append(lst[:])
        """
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
        """
        const.CONSOLEMESSAGE('Running Python code ...')
        self.activeatmlst=self.active
        self.inactiveatmlst=[]
        for atom in self.model.mol.atm:
            if not atom.select: self.inactiveatmlst.append(atom.seqnmb)
        self.ninactive=len(self.inactiveatmlst)
        
        
        for i in range(self.nactive):
            ii=self.activeatmlst[i]
            #xi=self.xyzatm[ii][1]; yi=self.xyzatm[ii][2]; zi=self.xyzatm[ii][3]
            atmi=self.opt.atm[ii]
            xi=atmi.cc[0]; yi=atmi.cc[1]; zi=atmi.cc[2]
            for j in range(self.ninactive):
                #xj=self.xyzatm[j][1]; yj=self.xyzatm[j][2]; zj=self.xyzatm[j][3]
                jj=self.inactiveatmlst[j]
                atmj=self.opt.atm[jj]
                xj=atmj.cc[0]; yj=atmj.cc[1]; zj=atmj.cc[2]
                r2=(xi-xj)**2+(yi-yj)**2+(zi-zj)**2
                r2lst[i][j]=r2
        
        const.CONSOLEMESSAGE('Exit from ComputeDistance2')
        return r2lst

    #def Optimize(self,x0,method='L-BFGS-B',epslst=[],optndic={}):
    def Optimize(self):
        """
        :param str methdd: 'Nelder-Mead','Powell','CG','BFGS','Newton-CG',
        'Anneal','L-BFGS-B','TNC', 'COBYLA', 'SLSQP'] 
        # scipy.Optimoze.Minimize in scipy ver0.16?
        """
        const.CONSOLEMESSAGE('Entered in Optimize')
        method=self.method
        optndic=self.optndic
        const.CONSOLEMESSAGE('Optimize. method='+method)
        x0=self.x0[:] #[0.0,0.0,0.0,0.0,0.0,0.0]
        #nvar=len(x0)
        """
        if len(epslst) > 0: optndic['eps']=epslst
        else:
            if not optndic.has_key('eps'):
                epslst=nvar*[0.1] #,0.01,0.01,0.01]
                optndic['eps']=epslst
        if len(method) <= 0: method='CG' #'L-BFGS-B' 
        
        optndic['maxiter']=1000
        optndic['gtol']=0.1 # 1e-2
        optndic['disp']=True
        
        optns = {'maxiter' : False,    # default value.
                'disp' : True, #True,    # non-default value.
                'gtol' :1e-2, #1e-5,    # default value.
                'eps' : epslst }#1.4901161193847656e-08}  # default value.
        """
        self.count=0
        #time1=time.clock()
        const.CONSOLEMESSAGE('Optimize # 1')
        result=lib.Optimizer(self.Efunc,x0,method=method,optns=optndic)
        const.CONSOLEMESSAGE('Optimize # 2')
        #time2=time.clock()
        #x = x0
        if int(scipy.__version__.split('.')[1]) >= 11: # for Scipy 0.11.x or later
            x = result.x
        else: # for Scipy 0.10.x
            x = result.xopt
        
        etot=self.Efunc(x)
        
        const.CONSOLEMESSAGE('final etot='+str(etot))

    def Efunc(self,x):    
        self.count += 1
        const.CONSOLEMESSAGE('optprm in Efunc='+str(x)+', count='+str(self.count))
        ivar=-1; atmlst=[]
        for grpnam in self.grplst:
            const.CONSOLEMESSAGE('Efunc # 1 grpnam='+grpnam)
            if self.grpvardic.has_key(grpnam):
                atmlst=self.grpatmlstdic[grpnam]
                const.CONSOLEMESSAGE('atmlst='+str(atmlst))
                for i in atmlst: self.opt.atm[i].cc=self.model.mol.atm[i].cc[:]
                
                mass=range(len(atmlst))
                if self.grpvardic[grpnam][0]: # var:center-of-mass          
                    for j in range(3):
                        ivar += 1
                        const.CONSOLEMESSAGE('ivar='+str(ivar))
                        for i in atmlst: 
                            self.opt.atm[i].cc[j]=\
                                            self.model.mol.atm[i].cc[j]+x[ivar]
                const.CONSOLEMESSAGE('Efunc  # 2')
                if self.grpvardic[grpnam][1]: # var:orientation   
                    cc=[]
                    for i in atmlst: cc.append(self.opt.atm[i].cc[:])
                    #const.CONSOLEMESSAGE('Efunc  cc='+str(cc))
                    ivar += 1; a=x[ivar]; ivar += 1; b=x[ivar]; ivar += 1
                    c=x[ivar]
                    u=lib.RotMatEul(a,b,c)
                    #const.CONSOLEMESSAGE('Efunc  u='+str(u))
                    cntr,eig,vec=lib.CenterOfMassAndPMI(mass,cc)
                    #const.CONSOLEMESSAGE('Efunc  cntr='+str(cntr))
                    #cntr=numpy.array(cntr); u=numpy.array(u)
                    cct=lib.RotMol(u,cntr,cc)
                    #const.CONSOLEMESSAGE('Efunc  cct='+str(cct))
                    for i in range(len(atmlst)):
                        #const.CONSOLEMESSAGE('i='+str(i))
                        self.opt.atm[atmlst[i]].cc=cct[i][:]
                const.CONSOLEMESSAGE('Efunc  # 3')    
                if len(self.grpvardic[grpnam][2]) > 0:
                    for atmi,atmj,movatmlst in self.grpvardic[grpnam][2]:
                        if len(movatmlst) <= 0: continue
                        ivar += 1; rota=x[ivar]
                        cc=[]
                        for i in movatmlst: cc.append(self.opt.atm[i].cc[:])
                        # rot atoms in movatmlst around atmi-atmj axis by x[iva]       
                        pnti=numpy.array(self.opt.atm[atmi].cc)
                        pntj=numpy.array(self.opt.atm[atmj].cc)
                        axis=pnti-pntj
                        u=RotMatAxis(axis,rota)
                        cct=lib.RotMol(u,pntj,cc)
                        for i in movatmlst:
                            for j in range(3):
                                self.opt.atm[i].cc[j]=cct[i][j]
                        
                        varnam=str(i)+':'+str(j)
                        

        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot in Efunc='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele)+', evdw='+str(evdw))
        
        gx=0.0; gy=0.0; gz=0.0
        for i in range(len(atmlst)):
            gx += gtot[i][0]
            gy += gtot[i][1]
            gz += gtot[i][2]
        gnorm=numpy.sqrt(gx*gx+gy*gy+gz*gz)
        const.CONSOLEMESSAGE('gnorm='+str(gnorm)+', gx='+str(gx)+', gy='+str(gy)+', gz='+str(gz))
        
        
        return etot

    
    def XXEfunc(self,p):
        atmlst=self.grpatmlstdic['h2o'] #grpnam]
        cc1=[]
        for i in atmlst: cc1.append(self.model.mol.atm[i].cc[:])
        mass=len(atmlst)*[1.0]
        comcc,eig,vec=lib.CenterOfMassAndPMI(mass,cc1)
        #cntr=[-comcc[0],-comcc[1],-comcc[2]]
        
        xc=p[0]; yc=p[1]; zc=p[2] # translation vector
        a=p[3]; b=p[4]; c=p[5] # euler angles
        
        ###a=0.0; b=0.0; c=0.0

        
        
        u=lib.RotMatEul(a,b,c)
        #cnt=numpy.array(self.comcc)
        #cnt=[xc,yc,zc]
        #cnt=[xc,yc,zc]
        
        const.CONSOLEMESSAGE('optprm in Efunc='+str(p)+', count='+str(self.count))
        self.count += 1
        cntr=[0.0,0.0,0.0]
        cct=lib.RotMol(u,comcc,cc1)
        cc=[]
        for i in range(len(atmlst)):
            cc.append([cct[i][0]+xc,
                       cct[i][1]+yc,
                       cct[i][2]+zc])
            

        for i in range(len(atmlst)):
            self.opt.atm[atmlst[i]].cc=cc[i][:]

        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot in Efunc='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele)+', evdw='+str(evdw))
        
        gx=0.0; gy=0.0; gz=0.0
        for i in range(len(atmlst)):
            gx += gtot[i][0]
            gy += gtot[i][1]
            gz += gtot[i][2]
        gnorm=numpy.sqrt(gx*gx+gy*gy+gz*gz)
        const.CONSOLEMESSAGE('gnorm='+str(gnorm)+', gx='+str(gx)+', gy='+str(gy)+', gz='+str(gz))
        
        
        return etot
    
    def Gfunc(self):
        gtot=[]
        
        
        return gtot
                
    def EnergyAndGradient(self,vdw=True,ele=True,grad=True,vdwgeom=True,
                          dielec=1.0):
        const.CONSOLEMESSAGE('Entered in EnergyAndGradinet')
        uele=332.063714/dielec
        etot=0.0; gtot=[]
        eele=0.0; gele=[] 
        evdw=0.0; gvdw=[] 

        self.activeatmlst=self.active
        self.inactiveatmlst=[]
        for atom in self.model.mol.atm:
            if not atom.select: self.inactiveatmlst.append(atom.seqnmb)
        self.ninactive=len(self.inactiveatmlst)

        self.nactive=len(self.active)
        
        for i in range(self.nactive):
            gele.append([0.0,0.0,0.0]); gvdw.append([0.0,0.0,0.0])
            gtot.append([0.0,0.0,0.0])
        #
        const.CONSOLEMESSAGE('EnergyAndGradinet #1')
        
        r2lst=self.ComputeDistance2()
        # energy and gradients of cgarge-charge interactions
        const.CONSOLEMESSAGE('EnergyAndGradinet #2')
        #const.CONSOLEMESSAGE('EnergyAndGradinet atmchglst='+str(self.atmchglst))
        if ele and len(self.atmchglst) <= 0:
            mess='Skipped "ele", since no atom charges'
            self.model.ConsoleMessage(mess)    
            ele=False
        if ele:
            for i in range(self.nactive):
                ii=self.activeatmlst[i]
                for j in range(self.ninactive):
                    jj=self.inactiveatmlst[j]
                    if jj == ii: continue
                    r2=r2lst[i][j]
                    #const.CONSOLEMESSAGE('EnergyAndGradinet ii='+str(ii)+', jj='+str(jj)+', r2='+str(r2))
                    riv=1.0/numpy.sqrt(r2)
                    qij=uele*self.atmchglst[ii]*self.atmchglst[jj]
                    eele += qij*riv
                    const.CONSOLEMESSAGE('eele='+str(eele))
                    if grad:
                        d=-qij*riv/r2
                        dx=self.opt.atm[ii].cc[0]-self.opt.atm[jj].cc[0]
                        dy=self.opt.atm[ii].cc[1]-self.opt.atm[jj].cc[1]
                        dz=self.opt.atm[ii].cc[2]-self.opt.atm[jj].cc[2]
                        gele[i][0] += d*dx
                        gele[i][1] += d*dy
                        gele[i][2] += d*dz
        const.CONSOLEMESSAGE('EnergyAndGradinet #3')
        # energy and gradients of vdw interactions                             
        if vdw and len(self.ljprmdic) <= 0:
            mess='Skipped "vdw", since no lj params'
            self.model.ConsoleMessage(mess)    
            vdw=False
        if vdw:
            for i in range(self.nactive):
                ii=self.activeatmlst[i]; elmii=self.model.mol.atm[ii].elm #opt.atm[ii].elm
                const.CONSOLEMESSAGE('elmii='+str(elmii))
                
                radii=self.ljprmdic[elmii][0]; epsii=self.ljprmdic[elmii][1]
                for j in range(self.ninactive):
                    jj=self.inactiveatmlst[j]
                    if jj == ii: continue
                    elmj=self.model.mol.atm[jj].elm #self.opt.atm[jj].elm
                    radj=self.ljprmdic[elmj][0]; epsj=self.ljprmdic[elmj][1]
                    if vdwgeom: 
                        radij=radii*radj; epsij=epsii*epsj
                    else:
                        radij=radii+radj; epsij=epsii+epsj
                    r2=r2lst[i][j]
                    c6=radij**6/r2**3; c12=c6*c6
                    evdw += epsij*(c12-2.0*c6)
                    if grad:
                        r3iv=1.0/(r2*numpy.sqrt(r2))
                        d=-12.0*r3iv*epsij*(c12-c6)
                        dx=self.opt.atm[ii].cc[0]-self.opt.atm[jj].cc[0]
                        dy=self.opt.atm[ii].cc[1]-self.opt.atm[jj].cc[1]
                        dz=self.opt.atm[ii].cc[2]-self.opt.atm[jj].cc[2]
                        gvdw[i][0] += d*dx
                        gvdw[i][1] += d*dy
                        gvdw[i][2] += d*dz                                
        const.CONSOLEMESSAGE('EnergyAndGradinet #4')
        # total energy and gradients
        etot=eele+evdw
        for i in range(self.nactive):
            gtot[i][0]=gele[i][0]+gvdw[i][0]
            gtot[i][1]=gele[i][1]+gvdw[i][1]
            gtot[i][2]=gele[i][2]+gvdw[i][2]
        
        """ debug """
        gx=0.0; gy=0.0; gz=0.0
        for i in range(self.nactive):
            gx += gele[i][0]
            gy += gele[i][1]
            gz += gele[i][2]
        #const.CONSOLEMESSAGE('gele sumx='+str(gx)+', sumy='+str(gy)+', sumz='+str(gz))
        gx=0.0; gy=0.0; gz=0.0
        for i in range(self.nactive):
            gx += gvdw[i][0]
            gy += gvdw[i][1]
            gz += gvdw[i][2]
        #const.CONSOLEMESSAGE('gvdw sumx='+str(gx)+', sumy='+str(gy)+', sumz='+str(gz))
        
        #const.CONSOLEMESSAGE('gradinet of first atom='+str(gtot[0]))
        """ end debug """
        return etot,eele,evdw,gtot,gele,gvdw
        
        """
        coulomb=332.063714; dielec = 1.0
        math.i:c     twosix   numerical value of the sixth root of two
        math.i:      real*8 sqrttwo,twosix
        math.i:      parameter (twosix=1.122462048309372981d0)
        
        rad(i) = twosix * rad(i)
        eps(i) = abs(eps(i))
        seps(i) = sqrt(eps(i))
        
        else if (radrule(1:10) .eq. 'ARITHMETIC') then
          rd = rad(i) + rad(k)
        else if (radrule(1:9) .eq. 'GEOMETRIC') then
          rd = 2.0d0 * (srad(i) * srad(k))
        radmin(i,k) = rd
        radmin(k,i) = rd
        eps
            else if (epsrule(1:10) .eq. 'ARITHMETIC') then
              ep = 0.5d0 * (eps(i) + eps(k))
           else if (epsrule(1:9) .eq. 'GEOMETRIC') then
              ep = seps(i) * seps(k)             
           epsilon(i,k) = ep
           epsilon(k,i) = ep
           
           
           elj1.f elj and the first derivative
           echarge1.f for charge-charge int
               rik2=rik**2
               if (rik2 .le. off2) then
                  rv = radmin(kt,it)
                  eps = epsilon(kt,it)
                  if (iv14(k) .eq. i) then
                     rv = radmin4(kt,it)
                     eps = epsilon4(kt,it)
                  end if
                  eps = eps * vscale(k)
                  p6 = rv**6 / rik2**3
                  p12 = p6 * p6
                  e = eps * (p12 - 2.0d0*p6)
        """
            
    def ReadAtomCharges(self,chgfile):
        def ErrorMessage(line,file):
            mess='Wrong data in line='+str(line)+' in '+file
            lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')
        #    
        atmchglst=[]; resnam=''; charge=0.0; scale=1.0
        if not os.path.exists(chgfile):
            mess='Not found chgfile='+chgfile
            const.CONSOLEMESSAGE(mess)
            return resnam,charge,scale,atmchglst
        line=0
        f=open(chgfile,'r')
        for s in f.readlines():
            line += 1
            s=s.strip()
            if s[:1] == '#': continue
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            if s[:6] == 'RESNAM':
                const.CONSOLEMESSAGE('found RESNAM')
                key,resnam=lib.GetKeyAndValue(s); continue
            if s[:6] == 'CHARGE':
                const.CONSOLEMESSAGE('found RESNAM')
                key,charge=lib.GetKeyAndValue(s); continue
            if s[:5] == 'SCALE':
                const.CONSOLEMESSAGE('found RESNAM')
                key,scale=lib.GetKeyAndValue(s); continue

            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                ErrorMessage(line,chgfile)
                return resnam,charge,scale,atmchglst
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # atomic charge
            try: chg=float(items[2])
            except:
                ErrorMessage(line,chgfile)
                return resnam,charge,scale,atmchglst
            # params
            atmchglst.append(chg)
        f.close()
        
        return resnam,charge,scale,atmchglst
    
    def ReadLJParams(self,ljfile):
        vdwprmdic={}
        if not os.path.exists(ljfile):
            mess='Not found ljfile='+ljfile
            const.CONSOLEMESSAGE(mess)
            return vdwprmdic
        line=0
        f=open(ljfile,'r')
        for s in f.readlines():
            line += 1
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                mess='Wrong data in line='+str(line)
                lib.MessageBoxOK(mess,'nonbond-int(ReadLJParams')
                return vdwprmdic
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # params
            vdwprmdic[elm]=[float(items[1]),float(items[2])]
        f.close()
        
        return vdwprmdic
    
    def TranslationGrad(self):
        pass
    
    def RotationGrad(self):
        pass
            
    def XYZDer(self):
        """
        XYZDER:: derivatives of x,y, and z with respect to euler angles.
        """
        """
          implicit real*8(a-h,o-z)
          common/molgeo/xmol(maxa,maxk),ymol(maxa,maxk),zmol(maxa,maxk)
          common/asminf/nmol,mol(maxm),natm(maxm),nbas(maxm),norb(maxm)
          common/asmgeo/x(maxm),y(maxm),z(maxm),a(maxm),b(maxm),c(maxm)
          common/dxyz/  dx(3,maxa,maxm),dy(3,maxa,maxm),dz(3,maxa,maxm)
          dimension     du(3,3,3)
    
          do 50 ith=1,nmol
          ki=mol(ith)
          nati=natm(ith)
          derivatives of euler angles
          call deuler(a(ith),b(ith),c(ith),du)
          do 20 ig=1,3
          do 20 ia=1,nati
          dx(ig,ia,ith)=xmol(ia,ki)*du(1,1,ig)+ymol(ia,ki)*du(1,2,ig)
                      +zmol(ia,ki)*du(1,3,ig)
          dy(ig,ia,ith)=xmol(ia,ki)*du(2,1,ig)+ymol(ia,ki)*du(2,2,ig)
                      +zmol(ia,ki)*du(2,3,ig)
          dz(ig,ia,ith)=xmol(ia,ki)*du(3,1,ig)+ymol(ia,ki)*du(3,2,ig)
                      +zmol(ia,ki)*du(3,3,ig)
          20 continue
          50 continue
        """
          
    def XXDerXYZEuler(self,alpha,beta,gamma):
        """ derivatives of transformation matrix with respect to Euler angle
        
        :param float alpha: euler angle alpha (radians)
        :param float beta: euler angle beta  (radians)
        :param float gamma: euler angle gamma (radians)
        :return: - du:lst(3*3*3)  derivatives of transformation matrix.
                      u(1,1,1)=ddu(1,1)/d(alpha), u(1,1,2)=ddu(1,1)/d(beta), etc.    
        Note: transformation matrix of Eular angles
        u(1,1)= cb*cc-ca*sb*sc, u(1,2)=-sc*cb-ca*sb*cc, u(1,3)= sa*sb
        u(2,1)= sb*cc+ca*cb*sc, u(2,2)=-sc*sb+ca*cb*cc, u(2,3)=-sa*cb
        u(3,1)= sa*sc,          u(3,2)= sa*cc,          u(3,3)= ca
        """
        zero=0.0
        du=numpy.zeros((3,3,3))
        sa=numpy.sin(alpha); ca=numpy.cos(alpha)
        sb=numpy.sin(beta);  cb=numpy.cos(beta)
        sc=numpy.sin(gamma); cc=numpy.cos(gamma)
        # derivatives of transformation matrix with respect to alpha.
        du[1][1][1]= sa*sb*sc; du[1][2][1]= sa*sb*cc; du[1][3][1]= ca*sb
        du[2][1][1]=-sa*cb*sc; du[2][2][1]=-sa*cb*cc; du[2][3][1]=-ca*cb
        du[3][1][1]= ca*sc;    du[3][2][1]= ca*cc;    du[3][3][1]=-sa
        # derivatives of transformation matrix with respect to beta.
        du[1][1][2]=-sb*cc-ca*cb*sc
        du[1][2][2]= sc*sb-ca*cb*cc; du[1][3][2]= sa*cb
        du[2][1][2]= cb*cc-ca*sb*sc
        du[2][2][2]=-sc*cb-ca*sb*cc; du[2][3][2]= sa*sb
        du[3][1][2]= zero; du[3][2][2]= zero; du[3][3][2]= zero
        # derivatives of transformation matrix with respect to gamma.
        du[1][1][3]=-cb*sc-ca*sb*cc; du[1][2][3]=-cc*cb+ca*sb*sc
        du[1][3][3]= zero
        du[2][1][3]=-sb*sc+ca*cb*cc; du[2][2][3]=-cc*sb-ca*cb*sc
        du[2][3][3]= zero
        du[3][1][3]= sa*cc; du[3][2][3]=-sa*sc; du[3][3][3]= zero
        return du
       
    def XXTorque(self,cc1,cc2,ccp,g,mass=1.0):
        """
        cc1: origin of axis, cc2 head of axis
        ccp: point
        g: Gradients in Cartasian coordinate, [dx,dy,dz]
        """
        torque=0.0
        x21=cc2[0]-cc1[0]; y21=cc2[1]-cc1[1]; z21=cc2[2]-cc1[2]
        xp1=ccp[0]-cc1[0]; yp1=ccp[1]-cc1[1]; zp1=ccp[2]-cc1[2]
        dnom=x21**2+y21**2+z21**2
        t=(x21*xp1+y21*yp1+z21*zp1)/(x21**2+y21**2+z21**2)
        x=x21*t+cc1[0]; y=y21*t+cc1[1]; z=z21*t+cc1[2]
        
        r=numpy.sqrt((x-ccp[0])**2+(y-ccp[1])**2+(z-ccp[2])**2)
        
        const.CONSOLEMESSAGE('r='+str(r))
        
        xp=ccp[0]-x; yp=ccp[1]-y; zp=ccp[2]-z
        
        const.CONSOLEMESSAGE('xyz='+str([x,y,z]))
        
        v21=numpy.array([x21,y21,z21])
        vpp=numpy.array([xp,yp,zp])
        
        const.CONSOLEMESSAGE('orth v21,vpp?'+str(numpy.dot(v21,vpp)))

        
        r=numpy.sqrt(xp**2+yp**2+zp**2)
        if r > 0:
            vec1=numpy.array([x21,y21,z21])
            vec2=numpy.array([xp,yp,zp])
            
            vec=numpy.cross(vec1,vec2)
            vnorm=numpy.linalg.norm(vec)
            if vnorm > 0: vec=vec/vnorm
        
            const.CONSOLEMESSAGE('vec='+str(vec)) 
            
            const.CONSOLEMESSAGE('orth vec and vec2?'+str(numpy.dot(vec,vec2)))
            g=numpy.array(g)
            torque=mass*r*numpy.dot(vec,g)
            
            const.CONSOLEMESSAGE('torque='+str(torque))
            
        else: pass # p is on rotation axis, r=0
        
        return torque
    
        
    def Quit(self):
        self.Destroy()

class NonBondIntEnergy(wx.Object):
    """ Non-bonding interaction energy (vdw and partial charge interaction)
        and rigid-body geometry optimization calculations """
    def __init__(self,model,title=''):
        """ Charge equilibration method:
            A. K. Pappe and W. A. Goddard III, J.Phys.Chem.,3358(1991).   
            modified to use NM-gamma for electron-electron repulsion:
            T.Nakano,T.Kaminuma,M.Uebayasi,Y.Nakata, Chem-Bio Info.J.,1,35(2001).
        
        :param obj model: an instance of the 'Model' class
        :param str title: title
        """
        const.CONSOLEMESSAGE('Entered in NonBondIntE') 
        
        self.prgnam='nonbond-inte ver. 0.1'
        self.model=model
        #
        """
        fudir=self.model.GetDir('FUdata')
        self.ljprmfile=os.path.join(fudir,'lj.prm')
        #
         
        self.atmchg=[]
        # should move in Initialize     
        self.ljprmdic=self.ReadLJParams(self.ljfile)
        # add tip3p params('OW' and 'HW')
        vdwprmdic['OW']=[1.7683,0.1520]
        vdwprmdic['HW']=[0.0,0.0]
        #
        chgfilelst=[ethanolchgfile] # <--- isolated groups
        atmchgdic={}
        for chgfile in chgfilelst:
            resnam,charge,scale,chglst=self.ReadAtomCharges(chgfile)
            atmchgdic[resnam]=[charge,scale,chglst]
        # append tip3p charge (assume the atom orderto be  O-H-H)
        atmchgdic['TIP3P']=[0.0,1.0,[-0.400,0.200,0.200]]          
        self.atmchglst=self.SetAtomCharges()
        """
        
        
        
        self.Initialize()
        #
        ###self.vdwprmdic=self.SetvdWParams()
        
        ###self.xyzatm,bonds,resfrg=rwfile.ReadXYZMol(xyzfile)
        ###self.natm=len(self.xyzatm)
        
        #self.vdwprm=self.AssignLJParamToAtom()
        
        """
        self.an=self.CheckParams()       
        """
        """
        self.time1=time.clock()
        #self.distlst=self.ComputeDistance()
        #self.q=self.SolveQEqEq()
        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele))
        const.CONSOLEMESSAGE('evdw='+str(evdw))
        #const.CONSOLEMESSAGE('gtot='+str(gtot))
        #const.CONSOLEMESSAGE('gele='+str(gele))
        #const.CONSOLEMESSAGE('gvdw='+str(gvdw))
        x0=[]
        self.Optimize(x0,method='',epslst=[],optndic={})
        
        self.time2=time.clock()
        
        etime=self.time2-self.time1
        const.CONSOLEMESSAGE('etime(sec.)='+str(etime))
        ###self.WritevdWParams(outfile)
        """
        
    def Initialize(self):
        const.CONSOLEMESSAGE('Entered in Initialize') 
        # temp mol object
        self.opt=self.model.mol.CopyMolecule()
        const.CONSOLEMESSAGE('Initialize #1') 
        self.natm=len(self.opt.atm)
        # set variables
        self.grplst=[] #['c2h5oh','h2o'] #['fkbp','k506'] # group name list
        self.grpatmlstdic={} # {grpnam:atmidxlst,...}
        self.grpchgfiledic={}
        self.grpvardic={} #{'h2o':[True,True,[]]} # {grpnam:[True(center),True(orientation),[atmi,atmj,[movelst](rotaxis),..],...]
        self.grpvarvaldic={} # {grpnam:[center:cc, orient:alpha,,beta,gamma],[angle1,...]],...}
        self.rotatmlstdic={}
        self.active=[]; 
        self.activeatmlst=[]; self.inactiveatmlst=[]
        self.ljprmdic={}
        self.vdwprmdic={}
        self.atmchglst=[]
        self.method='CG'
        self.optndic={}
        self.optndic['maxiter']=1000
        self.optndic['gtol']=0.1 # 1e-2
        self.optndic['disp']=True
        const.CONSOLEMESSAGE('Initialize #2') 
    
    def SetRigidBodyData(self,grplst,grpatmlstdic,grpvardic,rotatmlstdic):
        const.CONSOLEMESSAGE('Entered SetRigidBodyData') 
        self.grplst=grplst #['fkbp','k506'] # group name list
        self.grpatmlstdic=grpatmlstdic # {grpnam:atmidxlst,...}
        self.grpvardic=grpvardic # {grpnam:[True(center),True(orientation),[atmi,atmj,[movelst](rotaxis),..],...]
        self.rotatmlstdic=rotatmlstdic # {rotnam('p1-p2':[movable atmlst],...}
        #
        const.CONSOLEMESSAGE('SetRigidBodyData #1') 
        
        self.SetVariables()
        
        const.CONSOLEMESSAGE('SetRigidBodyData #3') 
    
    def SetNonBondParams(self,ljprmdic,atmchglst):
        self.atmchglst=atmchglst #['c2h5oh']='E://FUDATASET//FUdocs//data//ethanol.chg'
        self.ljprmdic=ljprmdic
        self.SetElement()
        self.vdwprmdic=self.SetvdWParams(self.ljprmdic)

        const.CONSOLEMESSAGE('SetNonBondParams atmchglst='+str(self.atmchglst))         
        
    def SetOptMethod(self,method,gconv,maxiter):
        self.method=method
        self.optndic['gtol']=gconv
        self.optndic['maxiter']=maxiter
        
    def SetVariables(self):
        #self.varnamlst=[]; self.varvallst=[]
        self.x0=[]; epslst=[]; self.activeatmlst=[]; self.inactiveatmlst=[]
        for grpnam in self.grplst:
            const.CONSOLEMESSAGE('SetVariables # 1 grpnam='+grpnam)
            center=False
            if self.grpvardic.has_key(grpnam):
                if self.grpvardic[grpnam][0]: # center-of-mass            
                    #self.varnamlst.append(grpnam+':center')
                    self.x0=self.x0+[0.0,0.0,0.0]
                    epslst=epslst+[0.1,0.1,0.1]
                    const.CONSOLEMESSAGE('grpnam='+str(self.grpatmlstdic.keys()))
                    self.activeatmlst=\
                                    self.activeatmlst+self.grpatmlstdic[grpnam]         
                const.CONSOLEMESSAGE('SetVariables # 2')
                if self.grpvardic[grpnam][1]: # orientation   
                    #self.varnamlst.append(grpnam+':orientation')
                    #abg=self.ComputeEulerAngles(grpnam,comcc)
                    #self.varvallst.append(abg)
                    
                    self.x0=self.x0+[0.0,0.0,0.0]
                    epslst=epslst+[0.01,0.01,0.01]
                    if not center: 
                        self.acriveatmlst=self.activeatmlst+\
                                                      self.grpatmlstdic[grpnam]         
                const.CONSOLEMESSAGE('SetVariables # 3')
                const.CONSOLEMESSAGE('grpvardic[grpnam][2]='+str(self.grpvardic[grpnam][2]))    
                if len(self.grpvardic[grpnam][2]) > 0:
                    [i,j]=self.grpvardic[grpnam][2]
                    #const.CONSOLEMESSAGE('movatmlst='+str(movatmlst))
                    #if len(movatmlst) <= 0: continue
                    #i=movatmlst[0]; j=movatmlst[1]
                    varnam=str(i)+':'+str(j)
                    #self.varnamlst.append(varnam) # rot-axsis variable
                    #self.rotmovatmlstdic[varnam]=moveatmlst
                    #angle=self.ComputeRotAngle(grpnam,i,j,movatmlst)
                    angle=0.0
                    #self.varvallst.append(angle)
                    self.x0=self.x0+[0.0]
                    epslst=epslst+[0.01]                       
        
        self.nactive=len(self.activeatmlst)
        for i in range(len(self.model.mol.atm)):
            if not i in self.activeatmlst: self.inactiveatmlst.append(i)
        self.ninactive=len(self.inactiveatmlst)
        
        const.CONSOLEMESSAGE('SetVariables # 4')
        #self.x0=x0
        self.optndic['eps']=epslst
        #               
        const.CONSOLEMESSAGE('x0='+str(self.x0))        
        # set initial value of variable
        
    def ComputeEulerAngles(self,grpnam,comcc):
        xyz=[]
        
        
        
        return xyz
    
    def ComputeRotAngle(self,grpnam,atmi,atmj):
        angle=0.0
        
        
        return angle
     
    def SetElement(self):
        self.elm=[]
        for atom in self.model.mol.atm:
            elm=atom.elm; res=atom.resnam
            if res in const.WaterRes:
                if elm == ' O': self.elm.append('OW')
                elif elm == ' H': self.elm.append('HW')
            else: self.elm.append(elm)
    
    def SetvdWParams(self,ljprmdic,vdwgeom=True):
        # geometric combination rule
        #    [rad]  radij=2.0*(sqrt(radi*sqrt(radj)
        #    [epsilon] epsij=sqrt(epsi)*sqrt(epsj)
        # 'arithmeric' combination rule
        #    [rad] radij=radi+radj
        #    [epsi lon] radij=0.5*(epsi+epsj)

        # add tip3p params('OW' and 'HW')
        ljprmdic['OW']=[1.7683,0.1520]
        ljprmdic['HW']=[0.0,0.0]
        const.CONSOLEMESSAGE('SetvdWParams. ljprmdic='+str(ljprmdic))
        # check params
        missprm=[]
        #elmlst=self.model.ListElement()
        for elm in self.elm:
            if not elm in ljprmdic: misselm.append(elm)        
        if len(missprm) > 0:
            mess='vdW paramtere is not found for element(s): '+misselm+'\n'
            mess=mess+'Define the paramter(s) in ".prm" file.'
            lib.MessageBoxOK(mess,'NonBondIntE(SetvdWParams)')
            return
        #
        vdwprmdic={}; sq2=numpy.sqrt(2.0); pt5=0.5; twosq6=1.122462048309372981 # 2**(1/6)
        for elm, prm in ljprmdic.iteritems():
            f=twosq6
            if not vdwgeom: f=0.5
            rad=f*ljprmdic[elm][0]
            eps=ljprmdic[elm][1]
            if vdwgeom: vdwprmdic[elm]=[numpy.sqrt(rad),numpy.sqrt(eps)]
            else: vdwprmdic[elm]=[rad,pt5*eps]         
        return vdwprmdic
    
    def ComputeDistance2(self):
        const.CONSOLEMESSAGE('ComputeDistance2 self.nactive='+str(self.nactive))
        const.CONSOLEMESSAGE('ComputeDistance2 self.innactive='+str(self.ninactive))

        r2lst=[]; lst=self.natm*[0.0]
        for i in range(self.nactive): r2lst.append(lst[:])
        """
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
        """
        const.CONSOLEMESSAGE('Running Python code ...')
        
        
        for i in range(self.nactive):
            ii=self.activeatmlst[i]
            #xi=self.xyzatm[ii][1]; yi=self.xyzatm[ii][2]; zi=self.xyzatm[ii][3]
            atmi=self.opt.atm[ii]
            xi=atmi.cc[0]; yi=atmi.cc[1]; zi=atmi.cc[2]
            for j in range(self.ninactive):
                #xj=self.xyzatm[j][1]; yj=self.xyzatm[j][2]; zj=self.xyzatm[j][3]
                jj=self.inactiveatmlst[j]
                atmj=self.opt.atm[jj]
                xj=atmj.cc[0]; yj=atmj.cc[1]; zj=atmj.cc[2]
                r2=(xi-xj)**2+(yi-yj)**2+(zi-zj)**2
                r2lst[i][j]=r2
        
        const.CONSOLEMESSAGE('Exit from ComputeDistance2')
        return r2lst

    #def Optimize(self,x0,method='L-BFGS-B',epslst=[],optndic={}):
    def Optimize(self):
        """
        :param str methdd: 'Nelder-Mead','Powell','CG','BFGS','Newton-CG',
                           'Anneal','L-BFGS-B','TNC', 'COBYLA', 'SLSQP']
                            # scipy.Optimoze.Minimize in scipy ver0.16?
        """
        const.CONSOLEMESSAGE('Entered in Optimize')
        method=self.method
        optndic=self.optndic
        const.CONSOLEMESSAGE('Optimize. method='+method)
        x0=self.x0[:] #[0.0,0.0,0.0,0.0,0.0,0.0]
        #nvar=len(x0)
        """
        if len(epslst) > 0: optndic['eps']=epslst
        else:
            if not optndic.has_key('eps'):
                epslst=nvar*[0.1] #,0.01,0.01,0.01]
                optndic['eps']=epslst
        if len(method) <= 0: method='CG' #'L-BFGS-B' 
        
        optndic['maxiter']=1000
        optndic['gtol']=0.1 # 1e-2
        optndic['disp']=True
        
        optns = {'maxiter' : False,    # default value.
                'disp' : True, #True,    # non-default value.
                'gtol' :1e-2, #1e-5,    # default value.
                'eps' : epslst }#1.4901161193847656e-08}  # default value.
        """
        self.count=0
        #time1=time.clock()
        const.CONSOLEMESSAGE('Optimize # 1')
        result=lib.Optimizer(self.Efunc,x0,method=method,optns=optndic)
        const.CONSOLEMESSAGE('Optimize # 2')
        #time2=time.clock()
        #x = x0
        if int(scipy.__version__.split('.')[1]) >= 11: # for Scipy 0.11.x or later
            x = result.x
        else: # for Scipy 0.10.x
            x = result.xopt
        
        etot=self.Efunc(x)
        
        const.CONSOLEMESSAGE('final etot='+str(etot))

    def Efunc(self,x):    
        self.count += 1
        const.CONSOLEMESSAGE('optprm in Efunc='+str(x)+', count='+str(self.count))
        ivar=-1
        for grpnam in self.grplst:
            const.CONSOLEMESSAGE('Efunc # 1 grpnam='+grpnam)
            if self.grpvardic.has_key(grpnam):
                atmlst=self.grpatmlstdic[grpnam]

                for i in atmlst: self.opt.atm[i].cc=self.model.mol.atm[i].cc[:]
                
                mass=range(len(atmlst))
                if self.grpvardic[grpnam][0]: # var:center-of-mass          
                    for j in range(3):
                        ivar += 1
                        const.CONSOLEMESSAGE('ivar='+str(ivar))
                        for i in atmlst: 
                            self.opt.atm[i].cc[j]=\
                                            self.model.mol.atm[i].cc[j]+x[ivar]
                const.CONSOLEMESSAGE('Efunc  # 2')
                if self.grpvardic[grpnam][1]: # var:orientation   
                    cc=[]
                    for i in atmlst: cc.append(self.opt.atm[i].cc[:])
                    #const.CONSOLEMESSAGE('Efunc  cc='+str(cc))
                    ivar += 1; a=x[ivar]; ivar += 1; b=x[ivar]; ivar += 1
                    c=x[ivar]
                    u=lib.RotMatEul(a,b,c)
                    #const.CONSOLEMESSAGE('Efunc  u='+str(u))
                    cntr,eig,vec=lib.CenterOfMassAndPMI(mass,cc)
                    #const.CONSOLEMESSAGE('Efunc  cntr='+str(cntr))
                    #cntr=numpy.array(cntr); u=numpy.array(u)
                    cct=lib.RotMol(u,cntr,cc)
                    #const.CONSOLEMESSAGE('Efunc  cct='+str(cct))
                    for i in range(len(atmlst)):
                        #const.CONSOLEMESSAGE('i='+str(i))
                        self.opt.atm[atmlst[i]].cc=cct[i][:]
                const.CONSOLEMESSAGE('Efunc  # 3')    
                const.CONSOLEMESSAGE('grpvardic='+str(self.grpvardic)) 
                
                if len(self.grpvardic[grpnam][2]) > 0:
                    #for atmi,atmj,movatmlst in self.grpvardic[grpnam][2]:
                    const.CONSOLEMESSAGE('grvvardic[grpnam]='+str(self.grpvardic[grpnam]))
                    atmi=self.grpvardic[grpnam][2][0]
                    atmj=self.grpvardic[grpnam][2][1]
                    #movatmlst=self.grpvardic[grpnam][2]
                    #if len(movatmlst) <= 0: continue
                    ivar += 1; rota=x[ivar]
                    cc=[]
                    for i in movatmlst: cc.append(self.opt.atm[i].cc[:])
                    # rot atoms in movatmlst around atmi-atmj axis by x[iva]       
                    pnti=numpy.array(self.opt.atm[atmi].cc)
                    pntj=numpy.array(self.opt.atm[atmj].cc)
                    axis=pnti-pntj
                    u=lib.RotMatAxis(axis,rota)
                    cct=lib.RotMol(u,pntj,cc)
                    for i in movatmlst:
                        for j in range(3):
                            self.opt.atm[i].cc[j]=cct[i][j]
                    
                    varnam=str(i)+':'+str(j)
                        

        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot in Efunc='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele)+', evdw='+str(evdw))
        
        gx=0.0; gy=0.0; gz=0.0
        for i in range(len(atmlst)):
            gx += gtot[i][0]
            gy += gtot[i][1]
            gz += gtot[i][2]
        gnorm=numpy.sqrt(gx*gx+gy*gy+gz*gz)
        const.CONSOLEMESSAGE('gnorm='+str(gnorm)+', gx='+str(gx)+', gy='+str(gy)+', gz='+str(gz))
        
        
        return etot

    
    def XXEfunc(self,p):
        atmlst=self.grpatmlstdic['h2o'] #grpnam]
        cc1=[]
        for i in atmlst: cc1.append(self.model.mol.atm[i].cc[:])
        mass=len(atmlst)*[1.0]
        comcc,eig,vec=lib.CenterOfMassAndPMI(mass,cc1)
        #cntr=[-comcc[0],-comcc[1],-comcc[2]]
        
        xc=p[0]; yc=p[1]; zc=p[2] # translation vector
        a=p[3]; b=p[4]; c=p[5] # euler angles
        
        ###a=0.0; b=0.0; c=0.0

        
        
        u=lib.RotMatEul(a,b,c)
        #cnt=numpy.array(self.comcc)
        #cnt=[xc,yc,zc]
        #cnt=[xc,yc,zc]
        
        const.CONSOLEMESSAGE('optprm in Efunc='+str(p)+', count='+str(self.count))
        self.count += 1
        cntr=[0.0,0.0,0.0]
        cct=lib.RotMol(u,comcc,cc1)
        cc=[]
        for i in range(len(atmlst)):
            cc.append([cct[i][0]+xc,
                       cct[i][1]+yc,
                       cct[i][2]+zc])
            

        for i in range(len(atmlst)):
            self.opt.atm[atmlst[i]].cc=cc[i][:]

        etot,eele,evdw,gtot,gele,gvdw=self.EnergyAndGradient()
        
        const.CONSOLEMESSAGE('etot in Efunc='+str(etot))
        const.CONSOLEMESSAGE('eele='+str(eele)+', evdw='+str(evdw))
        
        gx=0.0; gy=0.0; gz=0.0
        for i in range(len(atmlst)):
            gx += gtot[i][0]
            gy += gtot[i][1]
            gz += gtot[i][2]
        gnorm=numpy.sqrt(gx*gx+gy*gy+gz*gz)
        const.CONSOLEMESSAGE('gnorm='+str(gnorm)+', gx='+str(gx)+', gy='+str(gy)+', gz='+str(gz))
        
        
        return etot
    
    def Gfunc(self):
        gtot=[]
        
        
        return gtot
                
    def EnergyAndGradient(self,vdw=True,ele=True,grad=True,vdwgeom=True,
                          dielec=1.0):
        const.CONSOLEMESSAGE('Entered in EnergyAndGradinet')
        uele=332.063714/dielec
        etot=0.0; gtot=[]
        eele=0.0; gele=[] 
        evdw=0.0; gvdw=[] 
        for i in range(self.nactive):
            gele.append([0.0,0.0,0.0]); gvdw.append([0.0,0.0,0.0])
            gtot.append([0.0,0.0,0.0])
        #
        const.CONSOLEMESSAGE('EnergyAndGradinet #1')
        r2lst=self.ComputeDistance2()
        # energy and gradients of cgarge-charge interactions
        const.CONSOLEMESSAGE('EnergyAndGradinet #2')
        #const.CONSOLEMESSAGE('EnergyAndGradinet atmchglst='+str(self.atmchglst))
        if ele and len(self.atmchglst) <= 0:
            mess='Skipped "ele", since no atom charges'
            self.model.ConsoleMessage(mess)    
            ele=False
        if ele:
            for i in range(self.nactive):
                ii=self.activeatmlst[i]
                for j in range(self.ninactive):
                    jj=self.inactiveatmlst[j]
                    if jj == ii: continue
                    r2=r2lst[i][j]
                    #const.CONSOLEMESSAGE('EnergyAndGradinet ii='+str(ii)+', jj='+str(jj)+', r2='+str(r2))
                    riv=1.0/numpy.sqrt(r2)
                    qij=uele*self.atmchglst[ii]*self.atmchglst[jj]
                    eele += qij*riv
                    if grad:
                        d=-qij*riv/r2
                        dx=self.opt.atm[ii].cc[0]-self.opt.atm[jj].cc[0]
                        dy=self.opt.atm[ii].cc[1]-self.opt.atm[jj].cc[1]
                        dz=self.opt.atm[ii].cc[2]-self.opt.atm[jj].cc[2]
                        gele[i][0] += d*dx
                        gele[i][1] += d*dy
                        gele[i][2] += d*dz
        const.CONSOLEMESSAGE('EnergyAndGradinet #3')
        # energy and gradients of vdw interactions                             
        if vdw and len(self.vdwprmdic) <= 0:
            mess='Skipped "vdw", since no vdw params'
            self.model.ConsoleMessage(mess)    
            vdw=False
        if vdw:
            for i in range(self.nactive):
                ii=self.activeatmlst[i]; elmii=self.elm[ii] #opt.atm[ii].elm
                radii=self.vdwprmdic[elmii][0]; epsii=self.vdwprmdic[elmii][1]
                for j in range(self.ninactive):
                    jj=self.inactiveatmlst[j]
                    if jj == ii: continue
                    elmj=self.elm[jj] #self.opt.atm[jj].elm
                    radj=self.vdwprmdic[elmj][0]; epsj=self.vdwprmdic[elmj][1]
                    if vdwgeom: 
                        radij=radii*radj; epsij=epsii*epsj
                    else:
                        radij=radii+radj; epsij=epsii+epsj
                    r2=r2lst[i][j]
                    c6=radij**6/r2**3; c12=c6*c6
                    evdw += epsij*(c12-2.0*c6)
                    if grad:
                        r3iv=1.0/(r2*numpy.sqrt(r2))
                        d=-12.0*r3iv*epsij*(c12-c6)
                        dx=self.opt.atm[ii].cc[0]-self.opt.atm[jj].cc[0]
                        dy=self.opt.atm[ii].cc[1]-self.opt.atm[jj].cc[1]
                        dz=self.opt.atm[ii].cc[2]-self.opt.atm[jj].cc[2]
                        gvdw[i][0] += d*dx
                        gvdw[i][1] += d*dy
                        gvdw[i][2] += d*dz                                
        const.CONSOLEMESSAGE('EnergyAndGradinet #4')
        # total energy and gradients
        etot=eele+evdw
        for i in range(self.nactive):
            gtot[i][0]=gele[i][0]+gvdw[i][0]
            gtot[i][1]=gele[i][1]+gvdw[i][1]
            gtot[i][2]=gele[i][2]+gvdw[i][2]
        
        """ debug """
        gx=0.0; gy=0.0; gz=0.0
        for i in range(self.nactive):
            gx += gele[i][0]
            gy += gele[i][1]
            gz += gele[i][2]
        #const.CONSOLEMESSAGE('gele sumx='+str(gx)+', sumy='+str(gy)+', sumz='+str(gz))
        gx=0.0; gy=0.0; gz=0.0
        for i in range(self.nactive):
            gx += gvdw[i][0]
            gy += gvdw[i][1]
            gz += gvdw[i][2]
        #const.CONSOLEMESSAGE('gvdw sumx='+str(gx)+', sumy='+str(gy)+', sumz='+str(gz))
        
        #const.CONSOLEMESSAGE('gradinet of first atom='+str(gtot[0]))
        """ end debug """
        return etot,eele,evdw,gtot,gele,gvdw
        
        """
        coulomb=332.063714; dielec = 1.0
        math.i:c     twosix   numerical value of the sixth root of two
        math.i:      real*8 sqrttwo,twosix
        math.i:      parameter (twosix=1.122462048309372981d0)
        
        rad(i) = twosix * rad(i)
        eps(i) = abs(eps(i))
        seps(i) = sqrt(eps(i))
        
        else if (radrule(1:10) .eq. 'ARITHMETIC') then
          rd = rad(i) + rad(k)
        else if (radrule(1:9) .eq. 'GEOMETRIC') then
          rd = 2.0d0 * (srad(i) * srad(k))
        radmin(i,k) = rd
        radmin(k,i) = rd
        eps
            else if (epsrule(1:10) .eq. 'ARITHMETIC') then
              ep = 0.5d0 * (eps(i) + eps(k))
           else if (epsrule(1:9) .eq. 'GEOMETRIC') then
              ep = seps(i) * seps(k)             
           epsilon(i,k) = ep
           epsilon(k,i) = ep
           
           
           elj1.f elj and the first derivative
           echarge1.f for charge-charge int
               rik2=rik**2
               if (rik2 .le. off2) then
                  rv = radmin(kt,it)
                  eps = epsilon(kt,it)
                  if (iv14(k) .eq. i) then
                     rv = radmin4(kt,it)
                     eps = epsilon4(kt,it)
                  end if
                  eps = eps * vscale(k)
                  p6 = rv**6 / rik2**3
                  p12 = p6 * p6
                  e = eps * (p12 - 2.0d0*p6)
        """
            
    def ReadAtomCharges(self,chgfile):
        def ErrorMessage(line,file):
            mess='Wrong data in line='+str(line)+' in '+file
            lib.MessageBoxOK(mess,'nonbond-int(ReadAtomCharges')
        #    
        atmchglst=[]; resnam=''; charge=0.0; scale=1.0
        if not os.path.exists(chgfile):
            mess='Not found chgfile='+chgfile
            const.CONSOLEMESSAGE(mess)
            return atmchgdic
        line=0
        f=open(chgfile,'r')
        for s in f.readlines():
            line += 1
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            if s == 'RESNAM':
                const.CONSOLEMESSAGE('found RESNAM')
                key,resnam=lib.GetKeyAndValue(s); continue
            if s == 'CHARGE':
                const.CONSOLEMESSAGE('found RESNAM')
                key,charge=lib.GetKeyAndValue(s); continue
            if s == 'SCALE':
                const.CONSOLEMESSAGE('found RESNAM')
                key,scale=lib.GetKeyAndValue(s); continue

            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                ErrorMessage(line,chgfile)
                return atmchglst
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # atomic charge
            try: chg=float(items[2])
            except:
                ErrorMessage(line,chgfile)
                return atmchglst
            # params
            atmchglst.append(chg)
        f.close()
        
        return resnam,charge,scale,atmchglst
    
    def XXReadLJParams(self,ljfile):
        vdwprmdic={}
        if not os.path.exists(ljfile):
            mess='Not found ljfile='+ljfile
            const.CONSOLEMESSAGE(mess)
            return vdwprmdic
        line=0
        f=open(ljfile,'r')
        for s in f.readlines():
            line += 1
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if len(s) <= 0: continue
            items=lib.SplitStringAtSpacesOrCommas(s)
            if len(items) < 3:
                mess='Wrong data in line='+str(line)
                lib.MessageBoxOK(mess,'nonbond-int(ReadLJParams')
                return vdwprmdic
            # element
            try: 
                elm=int(items[0])
                elm=const.ElmSbl[elm]
            except:
                elm=items[0].upper()
                if len(elm) <= 1: elm=' '+elm
            # params
            vdwprmdic[elm]=[float(items[1]),float(items[2])]
        f.close()
        
        return vdwprmdic
    
    def TranslationGrad(self):
        pass
    
    def RotationGrad(self):
        pass
            
    def XYZDer(self):
        """
        XYZDER:: derivatives of x,y, and z with respect to euler angles.
        """
        """
          implicit real*8(a-h,o-z)
          common/molgeo/xmol(maxa,maxk),ymol(maxa,maxk),zmol(maxa,maxk)
          common/asminf/nmol,mol(maxm),natm(maxm),nbas(maxm),norb(maxm)
          common/asmgeo/x(maxm),y(maxm),z(maxm),a(maxm),b(maxm),c(maxm)
          common/dxyz/  dx(3,maxa,maxm),dy(3,maxa,maxm),dz(3,maxa,maxm)
          dimension     du(3,3,3)
    
          do 50 ith=1,nmol
          ki=mol(ith)
          nati=natm(ith)
          derivatives of euler angles
          call deuler(a(ith),b(ith),c(ith),du)
          do 20 ig=1,3
          do 20 ia=1,nati
          dx(ig,ia,ith)=xmol(ia,ki)*du(1,1,ig)+ymol(ia,ki)*du(1,2,ig)
                      +zmol(ia,ki)*du(1,3,ig)
          dy(ig,ia,ith)=xmol(ia,ki)*du(2,1,ig)+ymol(ia,ki)*du(2,2,ig)
                      +zmol(ia,ki)*du(2,3,ig)
          dz(ig,ia,ith)=xmol(ia,ki)*du(3,1,ig)+ymol(ia,ki)*du(3,2,ig)
                      +zmol(ia,ki)*du(3,3,ig)
          20 continue
          50 continue
        """
          
    def XXDerXYZEuler(self,alpha,beta,gamma):
        """ derivatives of transformation matrix with respect to Euler angle
        
        :param float alpha: euler angle alpha (radians)
        :param float beta: euler angle beta  (radians)
        :param float gamma: euler angle gamma (radians)
        :return: - du:lst(3*3*3)  derivatives of transformation matrix.
                      u(1,1,1)=ddu(1,1)/d(alpha), u(1,1,2)=ddu(1,1)/d(beta), etc.    
        Note: transformation matrix of Eular angles
        u(1,1)= cb*cc-ca*sb*sc, u(1,2)=-sc*cb-ca*sb*cc, u(1,3)= sa*sb
        u(2,1)= sb*cc+ca*cb*sc, u(2,2)=-sc*sb+ca*cb*cc, u(2,3)=-sa*cb
        u(3,1)= sa*sc,          u(3,2)= sa*cc,          u(3,3)= ca
        """
        zero=0.0
        du=numpy.zeros((3,3,3))
        sa=numpy.sin(alpha); ca=numpy.cos(alpha)
        sb=numpy.sin(beta);  cb=numpy.cos(beta)
        sc=numpy.sin(gamma); cc=numpy.cos(gamma)
        # derivatives of transformation matrix with respect to alpha.
        du[1][1][1]= sa*sb*sc; du[1][2][1]= sa*sb*cc; du[1][3][1]= ca*sb
        du[2][1][1]=-sa*cb*sc; du[2][2][1]=-sa*cb*cc; du[2][3][1]=-ca*cb
        du[3][1][1]= ca*sc;    du[3][2][1]= ca*cc;    du[3][3][1]=-sa
        # derivatives of transformation matrix with respect to beta.
        du[1][1][2]=-sb*cc-ca*cb*sc; du[1][2][2]= sc*sb-ca*cb*cc
        du[1][3][2]= sa*cb
        du[2][1][2]= cb*cc-ca*sb*sc; du[2][2][2]=-sc*cb-ca*sb*cc
        du[2][3][2]= sa*sb
        du[3][1][2]= zero; du[3][2][2]= zero; du[3][3][2]= zero
        # derivatives of transformation matrix with respect to gamma.
        du[1][1][3]=-cb*sc-ca*sb*cc; du[1][2][3]=-cc*cb+ca*sb*sc
        du[1][3][3]= zero
        du[2][1][3]=-sb*sc+ca*cb*cc; du[2][2][3]=-cc*sb-ca*cb*sc
        du[2][3][3]= zero
        du[3][1][3]= sa*cc; du[3][2][3]=-sa*sc; du[3][3][3]= zero
        return du
       
    def XXTorque(self,cc1,cc2,ccp,g,mass=1.0):
        """
        cc1: origin of axis, cc2 head of axis
        ccp: point
        g: Gradients in Cartasian coordinate, [dx,dy,dz]
        """
        torque=0.0
        x21=cc2[0]-cc1[0]; y21=cc2[1]-cc1[1]; z21=cc2[2]-cc1[2]
        xp1=ccp[0]-cc1[0]; yp1=ccp[1]-cc1[1]; zp1=ccp[2]-cc1[2]
        dnom=x21**2+y21**2+z21**2
        t=(x21*xp1+y21*yp1+z21*zp1)/(x21**2+y21**2+z21**2)
        x=x21*t+cc1[0]; y=y21*t+cc1[1]; z=z21*t+cc1[2]
        
        r=numpy.sqrt((x-ccp[0])**2+(y-ccp[1])**2+(z-ccp[2])**2)
        
        const.CONSOLEMESSAGE('r='+str(r))
        
        xp=ccp[0]-x; yp=ccp[1]-y; zp=ccp[2]-z
        
        const.CONSOLEMESSAGE('xyz='+str([x,y,z]))
        
        v21=numpy.array([x21,y21,z21])
        vpp=numpy.array([xp,yp,zp])
        
        const.CONSOLEMESSAGE('orth v21,vpp?'+str(numpy.dot(v21,vpp)))

        
        r=numpy.sqrt(xp**2+yp**2+zp**2)
        if r > 0:
            vec1=numpy.array([x21,y21,z21])
            vec2=numpy.array([xp,yp,zp])
            
            vec=numpy.cross(vec1,vec2)
            vnorm=numpy.linalg.norm(vec)
            if vnorm > 0: vec=vec/vnorm
        
            const.CONSOLEMESSAGE('vec='+str(vec)) 
            
            const.CONSOLEMESSAGE('orth vec and vec2?'+str(numpy.dot(vec,vec2)))
            g=numpy.array(g)
            torque=mass*r*numpy.dot(vec,g)
        else: pass # p is on rotation axis, r=0
        
        return torque
    
                
class SplitAndJoinPDBFile_Frm(wx.Frame):
    def __init__(self,parent,id,winpos=[],winlabel='SplitJoin'): #,model,ctrlflag,molnam):
        self.title='Split/Join PDB Data'
        #pltfrm=lib.GetPlatform()
        #if pltfrm == 'WINDOWS': winsize=lib.WinSize((220,185)) #((168,330))
        #else: winsize=(220,185)
        winsize=lib.WinSize([260,240])
        if len(winpos) <= 0:
            #pos=parent.GetPosition()
            #size=parent.GetSize()
            #winpos=[pos[0]+size[0],pos[1]+50]
            winpos=lib.WinPos(parent.mdlwin)
        #
        wx.Frame.__init__(self, parent, id, self.title,pos=winpos,size=winsize,
                style=wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        #self.Bind(wx.EVT_SIZE,self.OnSize)
        self.model=parent
        self.winlabel=winlabel
        if len(self.winlabel) <= 0: self.winlabel='SplitAndJoinWin'
        self.helpname='SplitAndJoinWin'
        self.parent=parent
        self.winctrl=self.model.winctrl
        self.mdlwin=self.model.mdlwin
        #xxself.ctrlflag=model.ctrlflag
        #self.model=self.mdlwin.model #parent.model
        self.winlabel=winlabel
        if self.model.mol is None:
            self.Destroy()
            return
        #
        self.molnam=self.model.mol.name #wrkmolnam
        #
        self.SetTitle(self.title+' ['+self.molnam+']')   
        # icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.funclst=['Split','Join','Extract']
        self.funcmode='Split'
        self.dirname=''
        self.splitcase=0 # 0:ter,1:chain,2:waters,3:pro-chemn-wat
        self.applied=False
        self.splfile=''
        self.pdbfile=''
        self.extrestxt=''
        self.extdir=''
        self.joinfile=''
        self.joinfilelst=[]
        self.mrgfile=''
        #
        self.CreatePanel()
        #
        self.Show()
        #
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify) 
        
    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        xsize=w; ysize=h; wnmb=95; wtxt=140-wnmb; xtcl0=155; xtcl1=260; htcl=22
        #
        hckb=24; hcmb=const.HCBOX; wtxt=60; wcmb=80; xcmb=75
        hcb=const.HCBOX
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)

        yloc=5
        wx.StaticText(self.panel,-1,"Choose function:",
                      pos=(5,yloc+2),size=(120,20)) 
        self.cmbfunc=wx.ComboBox(self.panel,-1,'',choices=self.funclst,
                             pos=(130,yloc),size=(80,hcb),style=wx.CB_READONLY)                      
        self.cmbfunc.Bind(wx.EVT_COMBOBOX,self.OnFunction)
        self.cmbfunc.SetValue(self.funcmode)
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)         

        yloc += 10

        if self.funcmode == 'Split': self.CreateSplitPanel(yloc)
        elif self.funcmode == 'Join': self.CreateJoinPanel(yloc)
        else: self.CreateExtractPanel(yloc)

    def CreateSplitPanel(self,yloc):
        [w,h]=self.GetClientSize()
        ###yloc=5
        wx.StaticText(self.panel,-1,"Split into:",pos=(5,yloc),size=(60,20)) 
        self.rbtter=wx.RadioButton(self.panel,-1,"at TER's",pos=(70,yloc),
                                   style=wx.RB_GROUP)
        self.rbtter.Bind(wx.EVT_RADIOBUTTON,self.OnSplitCase)
        self.rbtter.SetToolTipString('split at TER')
        self.rbtcha=wx.RadioButton(self.panel,-1,'chains',pos=(150,yloc))
        self.rbtcha.Bind(wx.EVT_RADIOBUTTON,self.OnSplitCase)
        self.rbtcha.SetToolTipString('split into chains')
        yloc += 20
        self.rbtwat=wx.RadioButton(self.panel,-1,'water and rest',
                                   pos=(30,yloc))
        self.rbtwat.Bind(wx.EVT_RADIOBUTTON,self.OnSplitCase)
        self.rbtwat.SetToolTipString('split into waters and the rest')
        
        self.rbtpcw=wx.RadioButton(self.panel,-1,'pro-chem-wat',
                                   pos=(140,yloc))
        self.rbtpcw.Bind(wx.EVT_RADIOBUTTON,self.OnSplitCase)
        mess='split into polypeptides,non-polypeptides,and waters'
        self.rbtpcw.SetToolTipString(mess)
        #self.rbtmul.Bind(wx.EVT_RADIOBUTTON,self.SelMulti)
        self.rbtcha.SetValue(True)
        yloc += 22
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)         
        yloc += 8
        savtxt=wx.StaticText(self.panel,-1,"Save directory:",
                      pos=(5,yloc),size=(100,20)) 
        savtxt.SetToolTipString('Directoy to save PDB files')
        btnbrw=wx.Button(self.panel,-1,"Browse",pos=(w-60,yloc),size=(50,20))
        btnbrw.Bind(wx.EVT_BUTTON,self.OnBrowseSplit)
        yloc += 25
        htcl=h-yloc-40
        self.tcldir=wx.TextCtrl(self.panel,-1,"",pos=(10,yloc),
                    size=(w-20,htcl),style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE)        
        self.tcldir.SetValue(self.dirname)
        self.tcldir.Bind(wx.EVT_TEXT_ENTER,self.OnInputDirectory)
        # buttons
        yloc=h-35
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)         
        wx.StaticLine(self.panel,pos=(170,yloc),size=(2,35),
                      style=wx.LI_VERTICAL)         
        yloc += 8
        self.btnload=wx.Button(self.panel,-1,"Load files",pos=(10,yloc),
                               size=(70,20))
        self.btnload.Bind(wx.EVT_BUTTON,self.OnLoadSplitFiles)
        #btnview=wx.Button(self.panel,-1,"Edit",pos=(53,yloc),size=(45,20))
        self.btnview=wx.Button(self.panel,-1,"View result",pos=(90,yloc),
                               size=(70,20))
        self.btnview.Bind(wx.EVT_BUTTON,self.OnViewResult)
        apbt=wx.Button(self.panel,-1,"Apply",pos=(185,yloc),size=(45,20))
        apbt.Bind(wx.EVT_BUTTON,self.OnApplySplit) # 10,105,53
        #
        self.SetSplitCase()
        self.EnableSplitButton()
        
    def CreateJoinPanel(self,yloc):
        [w,h]=self.GetClientSize()
        ##yloc=5
        wx.StaticText(self.panel,-1,"Open split/merge file(*.spl):",pos=(5,yloc),
                      size=(160,20)) 
        btnedit=wx.Button(self.panel,-1,"Edit",pos=(170,yloc),size=(50,20))  
        btnedit.Bind(wx.EVT_BUTTON,self.OnEditJoinFile)
        yloc += 25
        htcl=(h-yloc-65)/2
        self.tcljoin=wx.TextCtrl(self.panel,-1,"",pos=(10,yloc),
                    size=(w-80,htcl),style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE)        
        self.tcljoin.SetValue(self.joinfile)
        self.tcljoin.Bind(wx.EVT_TEXT_ENTER,self.OnInputJoinFile)
        btnbrw=wx.Button(self.panel,-1,"Browse",pos=(w-60,yloc),size=(50,20))
        btnbrw.Bind(wx.EVT_BUTTON,self.OnBrowseJoinFile)

        yloc += (htcl+5)
        ###wx.StaticText(self.panel,-1,"Join file name(*.mrg):",
        ###              pos=(5,yloc),size=(160,20)) 
        ###self.btnsave=wx.Button(self.panel,-1,"Save",pos=(170,yloc),size=(50,20))  
        ###self.btnsave.Bind(wx.EVT_BUTTON,self.OnSaveMergeFile)
        ###self.btnsave.Disable()
        yloc += 20
        ###self.tclmrg=wx.TextCtrl(self.panel,-1,"",pos=(10,yloc),
        ###            size=(w-80,htcl),style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE)          
        ###self.tclmrg.Bind(wx.EVT_TEXT_ENTER,self.OnInputMergeFile)
        #self.tclmrg.SetValue(self.mrgfile)
        ###btnmrg=wx.Button(self.panel,-1,"Browse",pos=(w-60,yloc+2),size=(50,20))
        ###btnmrg.Bind(wx.EVT_BUTTON,self.OnBrowseMergeFile)
        # buttons
        yloc=h-35
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)         
        wx.StaticLine(self.panel,pos=(170,yloc),size=(2,35),
                      style=wx.LI_VERTICAL)         
        yloc += 8
        ###self.btnview=wx.Button(self.panel,-1,"View merge file list",
        ###                       pos=(20,yloc),size=(120,20))
        ###self.btnview.Bind(wx.EVT_BUTTON,self.OnLoadPDBFile)
        #btnview=wx.Button(self.panel,-1,"Edit",pos=(53,yloc),size=(45,20))
        apbt=wx.Button(self.panel,-1,"Apply",pos=(185,yloc),size=(45,20))
        apbt.Bind(wx.EVT_BUTTON,self.OnApplyJoin) # 10,105,53
        #
        self.EnableJoinButton()
        
    def CreateExtractPanel(self,yloc):
        [w,h]=self.GetClientSize()
        ##yloc=5
        exttxt=wx.StaticText(self.panel,-1,
                "Input residue name(s) to be extracted:",
                pos=(5,yloc),size=(250,20)) 
        mess='Residue name(s) like "ALA:3:A,..." (res name:number:chain name)'
        exttxt.SetToolTipString(mess)
        yloc += 25
        htcl=(h-yloc-65)/2
        self.tclres=wx.TextCtrl(self.panel,-1,"",pos=(10,yloc),
                    size=(w-20,htcl),style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE)        
        self.tclres.Bind(wx.EVT_TEXT_ENTER,self.OnInputExtRes)
        self.tclres.SetValue(self.extrestxt)
        yloc += (htcl+5)
        wx.StaticText(self.panel,-1,"Directory name for save extracted files:",
                      pos=(5,yloc),size=(220,20)) 
        yloc += 20
        self.tclextdir=wx.TextCtrl(self.panel,-1,"",pos=(10,yloc),
                    size=(w-80,htcl),style=wx.TE_PROCESS_ENTER|wx.TE_MULTILINE)          
        self.tclextdir.Bind(wx.EVT_TEXT_ENTER,self.OnInputExtDir)
        self.tclextdir.SetValue(self.extdir)
        btnpdb=wx.Button(self.panel,-1,"Browse",pos=(w-60,yloc),size=(50,20))
        btnpdb.Bind(wx.EVT_BUTTON,self.OnBrowseExtract)
        # buttons
        yloc=h-35
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)         
        wx.StaticLine(self.panel,pos=(170,yloc),size=(2,35),
                      style=wx.LI_VERTICAL)         
        yloc += 8
        self.btnloadext=wx.Button(self.panel,-1,"Load extracted files",
                               pos=(20,yloc),size=(120,20))
        self.btnloadext.Bind(wx.EVT_BUTTON,self.OnLoadExtFile)
        #btnview=wx.Button(self.panel,-1,"Edit",pos=(53,yloc),size=(45,20))
        apbt=wx.Button(self.panel,-1,"Apply",pos=(185,yloc),size=(45,20))
        apbt.Bind(wx.EVT_BUTTON,self.OnApplyExtract) # 10,105,53
        #
        self.EnableExtButton()
        
    def EnableExtButton(self):
        if self.applied: 
            try: self.btnloadext.Enable()
            except: pass
        else: 
            try: self.btnloadext.Disable()
            except: pass  
        
    def EnableJoinButton(self):
        if self.applied: 
            try: self.btnload.Enable()
            except: pass
        else: 
            try: self.btnload.Disable()
            except: pass  
    
    def EnableSplitButton(self):
        if self.applied:
            try: 
                self.btnload.Enable(); self.btnview.Enable()
            except: pass
        else:
            try: 
                self.btnload.Disable(); self.btnview.Disable()    
            except: pass
            
    def OnSplitCase(self,event):
        objlabel=["at TER's",'chains','water and rest','pro-chem-wat']
        obj=event.GetEventObject()
        label=obj.GetLabel()
        self.splitcase=objlabel.index(label)
        self.applied=False
        self.EnableSplitButton()
        
    def SetSplitCase(self):
        caseobj=[self.rbtter,self.rbtcha,self.rbtwat,self.rbtpcw]
        caseobj[self.splitcase].SetValue(True)
    
    def InitExtract(self):
        self.extrestxt=''
        self.extdir=''
        self.applied=False
    
    def InitSplit(self):        
        self.dirname=''
        self.applied=False
    
    def InitJoin(self):
        self.applied=False
        self.splfile=''
        self.pdbfile=''
        self.joinmolobj=None
        
    def OnLoadSplitFiles(self,event):
        if not os.path.exists(self.splfile):
            mess='not found splfile='+self.splfile
            lib.MessageBoxOK(mess,'Split/Join(OnLoadSpltFile')
            return
        self.model.ReadFiles(self.splfile,True)
        self.applied=False
        self.EnableSplitButton()
    
    def OnLoadExtFile(self,event):
        if len(self.extfilelst) <= 0:
            mess='No extracte dfiles'
            lib.MessageBoxOK(mess,'Split and join(OnLoadExtFile)')
            return
        
        for file in self.extfilelst: self.model.ReadFiles(file,True)
        
        self.applied=False
        self.EnableExtButton()
        
    def OnLoadPDBFile(self,event):
        if not os.path.exists(self.pdbfile):
            mess='not found pdbfile='+self.pdbfile
            lib.MessageBoxOK(mess,'Split/Join(OnLoadPDBFile')
            return
        self.model.ReadFiles(self.pdbfile,True)
        self.applied=False
        self.EnableJoinButton()
            
    def OnViewResult(self,event):
        pass
    
    def OnFunction(self,event):
        self.funcmode=self.cmbfunc.GetStringSelection()
        self.panel.Destroy()
        if self.funcmode == 'Split': self.InitSplit()
        elif self.funcmode == 'Join': self.InitJoin()
        elif self.funcmode == 'Extract': self.InitExtract()
        self.CreatePanel()      
        
    def OnInputDirectory(self,event):
        dirname=self.tcldir.GetValue().strip()        
        if not os.path.isdir(self.dirname):
            mess='Not exits dir='+dirname+'.\n'
            mess=mess+'Whould you like to create it?\n'
            ans=lib.MessageBoxYesNo(mess,'SplitAndJoin(OndirectoryName)')
            if not ans:
                self.tcldir.SetValue('')
                return
        os.mkdir(dirname)
        self.dirname=dirname
        tcldir.SetValue(self.dirname)
        self.applied=False
        self.EnableSplitButton()
    
    def OnInputExtDir(self,event):
        pass
    
    def OnInputExtRes(self,event):
        pass
            
    def OnInputSplitFile(self,event):
        splfile=self.tclspl.GetValue().strip()
        if not os.path.exists(splfile):
            mess='Not exits splfile='+splfile+'.\n'
            lib.MessageBoxOK(mess,'Split/Join(OnInputSplitFile)')
            return
        self.splfile=splfile
        self.tclspl.SetValue(self.splfile)
    
    def OnInputJoinFile(self,event):
        joinfile=self.tcljoin.GetValue().strip()
        if not os.path.exists(splfile):
            mess='Not exits splfile='+splfile+'.\n'
            lib.MessageBoxOK(mess,'Split/Join(OnInputJointFile)')
            return
        self.joinfile=joinfile
        self.tcljoin.SetValue(self.joinfile)
        #
        self.joinfilelst=[]
        f=open(self.joinfile,'r')
        for s in f.readlines(): self.joinfilelst.append(s.strip())
        f.close()
     
    def OnInputMergeFile(self,event):
        mrgfile=self.tclmrg.GetValue().strip()
        if len(mrgfile) <= 0: return
        self.tclmrg.SetValue(mrgfile)
        self.btnsave.Enable()
             
    def OnInputPDBFile(self,event):
        self.pdbfile=self.tclpdb.GetValue().strip()        
        self.tclpdb.SetValue(self.pdbfile)
        self.applied=False
        self.EnableJoinButton()
    
    def OnEditJoinFile(self,event):
        if not os.path.exists(self.joinfile):
            mess='Not fount joinfile='+self.joinfile
            lib.MessageBoxOK(mess,'Split/Join(OnEditJoinFile)')
            return
        title='Edit join file +['+self.joinfile+']'
        retmeth=self.ReturnFromEditor
        winpos=[0,0]; winsize=[600,200]
        parpos=self.GetPosition(); parsize=self.GetSize()
        winpos[0]=parpos[0]+parsize[0]; winpos[1]=parpos[1]+50
        text=''
        f=open(self.joinfile,'r')
        for s in f.readlines(): text=text+s+'\n'
        f.close()
        txtedt=subwin.TextEditor_Frm(self.mdlwin,-1,winpos,winsize,
                                     title,text,retmethod=retmeth)
        self.applied=False
        #self.EnableJoinButton()
        
    def ReturnFromEditor(self,title,text,cancel):
        if cancel: return
        self.joinfilelst=[]
        items=text.split('\n')
        for s in items:
            file=s.strip()
            if file[:1] == '#': continue
            if len(file) > 0: self.joinfilelst.append(file)
        ###self.btnsave.Enable()
    
    def OnApplyExtract(self,event):
        self.resdatlst=[]; self.extfilelst=[]
        self.extrestxt=self.tclres.GetValue().strip()
        if len(self.extrestxt) <= 0:
            mess='Please input residues.'
            lib.MessageBoxOK(mess,'Split/Join(OnapplyExtract)')
            return
        self.extdir=self.tclextdir.GetValue().strip()
        if len(self.extdir) <= 0:
            mess=mess+'Please enter directory name\n'
            lib.MessageBoxOK(mess,'Split/Join(OnapplyExtract)')
            return
        # residues
        self.resdatlst=lib.SplitStringAtSpacesOrCommas(self.extrestxt)
        self.extfilelst,failedlst=\
                    self.model.ExtractResiduesInMol(self.resdatlst,self.extdir)
        mess='Created residue files='+str(self.extfilelst)                                           
        self.model.ConsoleMessage(mess)
        if len(failedlst) > 0:
            mess='Failed extract residues='+str(failedlst)
            self.model.ConsoleMessage(mess)
        self.applied=True
        self.EnableExtButton()
        
    def XXOnApplyJoin(self,event):
        mess=''
        self.splfile=self.tclspl.GetValue().strip()
        if len(self.splfile) <= 0:
            mess=mess+'Please enter split file name(*.spl)\n'
        self.pdbfile=self.tclpdb.GetValue().strip()
        if len(self.pdbfile) <= 0:
            mess=mess+'Please enter PDB filename.\n'
        if len(mess) > 0:
            lib.MessageBoxOK(mess,'Split/Join(OnapplyJoin)')
            return
        # join
        self.joinmolobj=self.model.JoinPDBFiles(self.pdbfile,self.splfile)
        
        self.applied=True
        self.EnableJoinButton()
        
    def OnApplyJoin(self,event):
        if len(self.joinfilelst) <= 0:
            self.joinfile=self.tcljoin.GetValue()
            if not os.path.exists(self.joinfile):
                mess='Not found join file='+self.joinfile
                lib.MessageBoxOK('(SplitAndJoinOnApplyJoin)')
                return
            self.joinfilelst=[]
            f=open(self.joinfile,'r')
            for file in f.readlines(): self.joinfilelst.appned(s.strip()) 
            f.close()
        if len(self.joinfilelst) <= 0:
            mess='Please input split(join) file.'
            lib.MessageBoxOK(mess,'SplitAndJojn(OnApply)')
            return
        # join
        self.model.MergeByFiles(self.joinfilelst)
        
        self.applied=True
        #self.EnableJoinButton()
        
    def OnApplySplit(self,event):
        self.dirname=self.tcldir.GetValue()
        self.dirname=self.dirname.strip()
        if len(self.dirname) <= 0: 
            mess='Diretory name is empty.'
            lib.MessageBoxOK(mess,'Split/Join(OnApplySplit)')
            return
        if not os.path.isdir(self.dirname):
            mess='Not found directrory name='+self.dirname+'\n'
            mess=mess+' Would you like to create it?'
            ans=lib.MessageBoxYesNo(mess,'SplitPDBData')
            if not ans: return
            else: os.mkdir(self.dirname)
        #
        if self.rbtter.GetValue(): 
            self.model.SplitMolAtTER(self.dirname,load=False)
        if self.rbtcha.GetValue(): 
            self.model.SplitMolIntoChains(self.dirname,load=False)
        if self.rbtpcw.GetValue(): 
            self.model.SplitMolIntoProChemWat(self.dirname,load=False)
        if self.rbtwat.GetValue(): 
            self.model.SplitMolIntoWatAndRest(self.dirname,load=False)
        #
        self.applied=True
        self.EnableSplitButton()
        
    def OnBrowseSplit(self,event):
        self.dirname=lib.GetDirectoryName()
        if len(self.dirname) <= 0: return
        self.dirname=lib.ReplaceBackslash(self.dirname)
        self.tcldir.SetValue(self.dirname)
        
    def OnBrowseSplFile(self,event):
        wcard='Split file(*.spl)|*.spl'
        self.splfile=lib.GetFileName(wcard=wcard,rw='r',check=True)
        if len(self.splfile) <= 0: return
        self.splfile=lib.ReplaceBackslash(self.splfile)
        self.tclspl.SetValue(self.splfile)
        if not os.path.exists(self.splfile):
            mess='Not found file='+self.splfile+'\n'
            mess='Re-enter.'
            lib.MessageBoxOK(mess,'Join(OnBrowseSpl)')
            self.tclspl=''; self.tclsel.SetValue('')
        self.applied=False
        self.EnableSplitButton()
       
    def OnBrowseJoinFile(self,event):
        wcard='Split file(*.spl,*.mrg)|*.spl;*.mrg'
        self.joinfile=lib.GetFileName(wcard=wcard,rw='r',check=True)
        if len(self.joinfile) <= 0: return
        self.joinfile=lib.ReplaceBackslash(self.joinfile)
        self.tcljoin.SetValue(self.joinfile)
        if not os.path.exists(self.joinfile):
            mess='Not found file='+self.joinfile+'\n'
            mess='Re-enter.'
            lib.MessageBoxOK(mess,'Join(OnBrowseJoinFile)')
            self.tcljoin=''
        self.applied=False
       
    def OnBrowseMergeFile(self,event):
        wcard='Split file(*.spl,*.mrg)|*.spl;*.mrg'
        self.jmrgfile=lib.GetFileName(wcard=wcard,rw='r',check=True)
        if len(self.mrgfile) <= 0: return
        self.joinfile=lib.ReplaceBackslash(self.mrgfile)
        self.tclmrg.SetValue(self.mrgfile)
       
    def OnSaveMergeFile(self,event):
        mrgfile=self.tclmrg.GetValue()
        mrgfile=mrgfile.strip()
        if len(mrgfile) <=0: return
        self.mrgfile=mrgfile
        
    def OnBrowseJoin(self,event):
        wcard='PDB file(*.pdb)|*.pdb'
        self.pdbfile=lib.GetFileName(wcard=wcard,rw='w',check=True)
        if len(self.pdbfile) <= 0: retunr
        self.pdbfile=lib.ReplaceBackslash(self.pdbfile)
        self.tclpdb.SetValue(self.pdbfile)
        self.applied=False
        self.EnableJoinButton()
    
    def OnBrowseExtract(self,event):
        self.extdir=lib.GetDirectoryName()
        if len(self.extdir) <= 0: return
        self.extdir=lib.ReplaceBackslash(self.extdir)
        self.tclextdir.SetValue(self.extdir)
            
    def OnResize(self,event):
        self.OnMove(1)

    def OnMove(self,event):
        w,h=self.GetSize()
        self.panel.Destroy()
        self.SetMinSize([w,120])
        self.SetMaxSize([w,2000])        
        self.CreatePanel()
        
    def OnNotify(self,event):
        #if event.jobid != self.winlabel: return
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles':
            mess='Reset mol object in "'+self.winlabel+'"'
            self.model.ConsoleMessage(mess)
            self.OnReset(1)

    def OnReset(self,event):
        self.panel.Destroy()

        self.CreatePanel()
        self.model.Message('Restored molecule object',0,'')
        #lib.MessageBoxOK('Restored molecule data in mdlwin','')
    
    def OnClose(self,event):
        
        try: self.model.winctrl.Close(self.winlabel)
        except: pass
        self.Destroy()
        
        try: item=event.message
        except: return
        if item == 'SwitchMol' or item == 'ReadFiles':
            self.model.ConsoleMessage('Reset mol object in "NameSelector"')
            self.OnReset(1)

    def HelpDocument(self):
        pass
    
    def Tutorial(self):
        pass
    
    def Related(self):
        pass
        
    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        #submenu.AppendSeparator()
        #submenu.Append(-1,'Related functions','Execute related functions')
        menubar.Append(submenu,'Help')
        #
        return menubar

    def OnMenu(self,event):
        """ Menu event handler
        
        """
        menuid=event.GetId()
        label=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        # Help
        if label == 'Document': self.HelpDocument()
        elif label == 'Tutorial': self.Tutorial()
        elif label == 'Related functions': self.Related()

class RMSFitting_Frm(wx.Frame):
    def __init__(self,parent,id,winpos=[],winsize=[]): #,model,ctrlflag,molnam,winpos):
        self.title='RMS Fitting'
        if len(winpos) <= 0:
            parpos=parent.GetPosition(); parsize=parent.GetSize()
            winpos=[parpos[0]+parsize[0],parpos[1]+40]            
        if len(winsize) <= 0: winsize=lib.WinSize((340,280)) #270) # 335)
        self.winsize=winsize
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)      
        #
        self.mdlwin=parent
        self.model=self.mdlwin.model
        ###self.mol=fum.mol
        self.helpname='rms-fit'
        self.ctrlflag=self.model.ctrlflag
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass        
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: 
            self.OnClose(1); return  
            
        molnam1=self.model.mol.name
        molnam2=self.model.mol.mergedmolname
        self.trgfile=self.model.mol.inpfile
        self.SetTitle(self.title+' ['+molnam1+','+molnam2+']')
        #self.size=self.GetClientSize()
        #
        self.batch=False
        #
        self.reffile=""
        self.savtrs=[]
        self.refbndthic=1
        self.rmsdval=0.5
        self.donermsfit=False
        self.applied=False
        self.ntrg=0; self.nref=0
        self.trgdic={}; self.refdic={}
        self.totdic0={}; self.totdic1={}
        self.messout=True
        self.messpos0=[]; self.messpos1=[]; self.messpos2=[]
        self.trgdic={}; self.refdic={}; self.totdic0={}; self.totdic1={}
        self.matdic={}
        self.case=2
        self.chainnam=False; self.resnam=True; self.resnmb=True#; self.atmnam=True
        self.backbone=False #True this is removed KK
        self.trsr2t=True
        self.transatm=[]
        self.matchlst0=[]; self.nonmatchlst0=[]
        self.matchlst1=[]; self.nonmatchlst1=[]
        self.dcnt=[]; self.cnt=[]; self.rot=[]
        self.savcon=[]; self.seqnew2old=[]; self.seqold2new=[]
        self.savmol=[]
        self.input='>1.0'
        self.devatom=[]
        self.readref=False
        ntrg,nref=self.CountAtomsInTrgAndRef()
        if nref > 0:
            self.readref=True
            self.savrms=self.model.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        #
        self.rmsfit=False
        self.panel=None; self.hpanel=-1
        self.CreatePanel()
        #
        self.ChangeBondThickness()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()

    def CreatePanel(self):
        xpos=0; ypos=0; [w,h]=self.GetClientSize()
        #
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        #
        yloc=10
        wx.StaticText(self.panel,-1,"Reference molecule:",pos=(10,yloc),
                      size=(115,18))
        self.btnmatdel=wx.Button(self.panel,wx.ID_ANY,"Del",pos=(200,yloc-3),
                            size=(50,20))
        self.btnmatdel.Bind(wx.EVT_BUTTON,self.OnDelReference)
        btnmatred=wx.Button(self.panel,wx.ID_ANY,"Read",pos=(275,yloc-3),
                            size=(45,20))
        btnmatred.Bind(wx.EVT_BUTTON,self.OnReadReference)
        btnmatred.SetFocus()
        yloc += 20
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,4),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"1)Matching atoms:",pos=(10,yloc),
                      size=(115,18))
        btnmatapl=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(270,yloc),
                            size=(45,20))
        btnmatapl.Bind(wx.EVT_BUTTON,self.OnMatchingApply)
        #self.ckbback=wx.CheckBox(self.panel,-1,"backbone only",pos=(135,yloc), \
        #                         size=(120,18))
        #self.ckbback.SetValue(self.backbone)
        yloc += 20
        self.rbtsel=wx.RadioButton(self.panel,-1,"selected pairs",
                                 pos=(25,yloc),size=(120,18),style=wx.RB_GROUP)
        self.rbtseq=wx.RadioButton(self.panel,-1,"sequence number order",
                                   pos=(145,yloc),size=(150,18))
        yloc += 20
        self.rbtnam=wx.RadioButton(self.panel,-1,"atom names with,",
                                   pos=(25,yloc),size=(120,18))
        self.rbtnam.SetValue(True)
        yloc += 20
        self.ckbresnam=wx.CheckBox(self.panel,-1,"resnam",pos=(40,yloc),
                                   size=(60,18))
        self.ckbresnmb=wx.CheckBox(self.panel,-1,"resnmb",pos=(110,yloc),
                                   size=(60,18))
        self.ckbchainnam=wx.CheckBox(self.panel,-1,"chainnam",pos=(180,yloc),
                                     size=(70,18))
        self.SetNameOptions()
        yloc += 20; tclh=45
        mess="# of matched, nonmatched[target,refrence] atoms:"
        wx.StaticText(self.panel,-1,mess,pos=(20,yloc),size=(w-40,18)) 
        yloc += 20
        self.messpos0=[60,yloc]
        self.txt=wx.StaticText(self.panel,-1,"0[0,0]",pos=self.messpos0,
                               size=(200,18)) 
        #
        yloc += 22
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"2)RMS fit with:",pos=(10,yloc),
                      size=(90,18))
        self.rbtcg=wx.RadioButton(self.panel,-1,"CG",pos=(110,yloc),
                                  size=(40,18),style=wx.RB_GROUP)
        self.rbtpow=wx.RadioButton(self.panel,-1,"Powell",pos=(155,yloc),
                                   size=(55,18))
        self.rbtpow.SetValue(True)
        self.btnfitundo=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(230,yloc),
                                  size=(45,20))
        self.btnfitundo.Bind(wx.EVT_BUTTON,self.OnRMSFitUndo)
        self.btnfitdo=wx.Button(self.panel,wx.ID_ANY,"Fit",pos=(285,yloc),
                                size=(35,20))
        self.btnfitdo.Bind(wx.EVT_BUTTON,self.OnRMSFitDo)
        #
        yloc += 22
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)                
        yloc += 8
        wx.StaticText(self.panel,-1,"3)Show atoms displaced larger than:",
                      pos=(10,yloc),size=(210,18))
        #self.rbtrms.Bind(wx.EVT_RADIOBUTTON,self.OnRBTNonMatching)
        self.tclval=wx.TextCtrl(self.panel,-1,str(self.rmsdval),pos=(225,yloc),
                                size=(40,18)) # size x 28 <-30
        btnshwapl=wx.Button(self.panel,wx.ID_ANY,"Plot",pos=(280,yloc),
                            size=(45,20))
        btnshwapl.Bind(wx.EVT_BUTTON,self.OnPlotDeviation)
        self.hpanel=yloc+20

    def ChangeBondThickness(self):
        for atom in self.model.mol.atm:
            if atom.elm == "XX": continue
            if atom.grpnam == "mrg2": atom.thick=self.refbndthic  
        if not self.batch: self.model.DrawMol(True)
    
    def SetCKBName(self):
        val=self.rbtnam.GetValue()
        if val:
            self.ckbresnam.Enable(); self.ckbresnmb.Enable()
            self.ckbchainnam.Enable()
        else:
            self.ckbresnam.Disable(); self.ckbresnmb.Disable()
            self.ckbchainnam.Disable()
    
    def CountAtomsInTrgAndRef(self):
        ntrg=0; nref=0
        for atom in self.model.mol.atm:
            if atom.grpnam == "base": ntrg += 1
            if atom.grpnam == "mrg2": nref += 1
        return ntrg,nref
            
    def MakeCase2AtomNameDic(self,sellst,fullname):
        self.trgdic={}; self.refdic={}
        if len(sellst) <= 0:
            sellst=[]
            for i in range(len(self.model.mol.atm)):
                if self.model.mol.atm[i].elm == "XX": continue
                sellst.append(i)
        #
        self.resnam=self.ckbresnam.GetValue()
        self.resnmb=self.ckbresnmb.GetValue()
        #self.atmnam=self.ckbatmnam.GetValue()
        self.chainnam=self.ckbchainnam.GetValue()
        #
        dupdic0={}; dupdic1={}
        for i in sellst:
            if self.backbone and not self.model.mol.IsBackBoneAtom(i): continue
            atom=self.model.mol.atm[i]
            if fullname: name=self.model.mol.MakeFullAtomName(i,True,True,True)
            else: name=self.model.mol.MakeFullAtomName(i,self.chainnam,
                                                       self.resnam,self.resnmb)
            if atom.grpnam == "base": self.trgdic[name]=i
            if atom.grpnam == "mrg2": self.refdic[name]=i
        
        self.matdic={}
        for i in range(len(self.model.mol.atm)):
            if fullname: name=self.model.mol.MakeFullAtomName(i,True,True,True)
            else: name=self.model.mol.MakeFullAtomName(i,self.chainnam,
                                                       self.resnam,self.resnmb)
            if self.trgdic.has_key(name) and self.refdic.has_key(name):
                self.matdic[name]=True            

        self.difdic0={}
        for i in self.trgdic:
            if not self.refdic.has_key(i): self.difdic0[i]=self.trgdic[i]

        self.difdic1={}
        for i in self.refdic:
            if not self.trgdic.has_key(i): self.difdic1[i]=self.refdic[i]
            
    def MakeCase1AtomNameDic(self,selected):
        self.trgdic={}; self.refdic={}; sellst=[]
        
        if selected: nsel,sellst=self.model.ListSelectedAtom()
        else: sellst=self.model.ListAtomSequence(True)
        #
        for i in sellst:
            atom=self.model.mol.atm[i]
            #if fullname: self.mol.MakeFullAtomName(i,True,True,True)
            #else: name=self.mol.MakeFullAtomName(i,self.chainnam,self.resnam,self.resnmb)
            if atom.grpnam == "base": self.trgdic[i]=i
            if atom.grpnam == "mrg2": self.refdic[i-self.ntrg]=i
        
        self.matdic={}
        for i in range(len(self.model.mol.atm)):
            atom=self.model.mol.atm[i]
            ii=i
            if atom.grpnam == "mrg2": ii=i-self.ntrg
            if self.trgdic.has_key(ii) and self.refdic.has_key(ii):
                self.matdic[ii]=True            

        self.difdic0={}
        for i in self.trgdic:
            if not self.refdic.has_key(i): self.difdic0[i]=self.trgdic[i]

        self.difdic1={}
        for i in self.refdic:
            if not self.trgdic.has_key(i): self.difdic1[i]=self.refdic[i]

    def ListMatchingAtoms(self):
        # case:  =0 for selected order, =1 for sequence order, =2 for names
        err=0; nref=0; ntrg=0
        self.matchlst0=[]; self.nonmatchlst0=[]
        self.matchlst1=[]; self.nonmatchlst1=[]
        #
        nsel,sellst=self.model.ListSelectedAtom()
        #
        self.case=1
        if self.rbtsel.GetValue(): self.case=0 
        if self.rbtseq.GetValue(): self.case=1
        if self.rbtnam.GetValue(): self.case=2        
        #
        if self.case == 0: # selected order
            pass
            
        elif self.case == 1: # sequence order
            self.MakeCase1AtomNameDic(True) # selected only

            for i in sellst:
                atom=self.model.mol.atm[i]
                if atom.elm == "XX": continue
                if self.backbone and not self.model.mol.IsBackBoneAtom(i): 
                    continue
                #name=self.mol.MakeFullAtomName(i,self.chainnam,self.resnam,self.resnmb)
                if atom.grpnam == "base":
                    if self.refdic.has_key(i+self.ntrg): 
                        self.matchlst0.append(i)
                    else: self.nonmatchlst0.append(i)
                if atom.grpnam == "mrg2":
                    if self.trgdic.has_key(i-self.ntrg): 
                        self.matchlst1.append(i)
                    else: self.nonmatchlst1.append(i)
        elif self.case == 2: # for name matching
            self.MakeCase2AtomNameDic(sellst,False) # selected and not fullname
            atmlst=self.matdic.keys()
            for i in atmlst:
                ii=self.trgdic[i]; self.matchlst0.append(ii)
                ii=self.refdic[i]; self.matchlst1.append(ii)
            
            for i in self.difdic0:
                self.nonmatchlst0.append(self.difdic0[i])
            for i in self.difdic1:
                self.nonmatchlst1.append(self.difdic1[i])
        #
        return err
    
    def MakeMatchingdAtomCC(self):
        err=0
        cc0=[]; cc1=[]; cct=[]
        for i in self.matchlst0: #self.fitatmlst0:
            atom=self.model.mol.atm[i]; cc0.append(atom.cc[:])
        for i in self.matchlst1: #self.fitatmlst1:
            atom=self.model.mol.atm[i]; cc1.append(atom.cc[:])
        if len(cc0) != len(cc1):
            mess="Number of atoms in reference and target group is different."
            lib.MessageBoxOK(mess,"")
            err=1
        
        return err,cc0,cc1

    def SetNameOptions(self):
        self.ckbresnam.SetValue(self.resnam)
        self.ckbresnmb.SetValue(self.resnmb)
        #self.ckbatmnam.SetValue(self.atmnam)
        self.ckbchainnam.SetValue(self.chainnam)
    
    def OnReadReference(self,event):
        if self.readref:
            mess="Reference molecule is already read. filename="+self.reffile
            self.model.Message(mess,0,"")
            return
        wcard='pdb file(*.pdb;*.ent)|*.pdb;*.ent'
        #
        name=self.model.setctrl.GetParam('defaultfilename')
        self.model.setctrl.SetParam('defaultfilename','')
        #
        filename=lib.GetFileName(self,wcard,"r",True,defaultname=name)
        self.reffile=filename
        self.model.MergeToCurrent(filename) 
        mess="Read reference molecule, filename="+filename
        #self.model.Message(mess,0,"")
        self.model.ConsoleMessage(mess)
        self.ntrg,self.nref=self.CountAtomsInTrgAndRef() 
        mess="Numbers of target atoms= "+str(self.ntrg)
        mess=mess+ " and reference atoms= "+str(self.nref)
        self.model.ConsoleMessage(mess)

        self.savrms=self.model.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        self.readref=True
    
    def OnDelReference(self,event):
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return
        dellst=[]
        for i in range(len(self.model.mol.atm)):
            if self.model.mol.atm[i].grpnam == "mrg2": dellst.append(i)
        if len(dellst) > 0:
            self.model.mol.DelAtoms(dellst)
            self.model.DrawMol(True)
            mess="rms_fit.py: Reference molecule was deleted."
            self.model.Message(mess,0,"")
        self.readref=False
        
    def DeviatedAtoms(self,rmin):
        matdic={}
        for i in range(len(self.model.mol.atm)):
            if self.model.mol.atm[i].grpnam != "base": continue
            res=self.model.mol.atm[i].resnmb
            atm=self.model.mol.atm[i].atmnmb
            name=self.model.mol.MakeFullAtomName(i,self.chainnam,self.resnam,
                                                 self.resnmb)
            if self.trgdic.has_key(name) and self.refdic.has_key(name): 
                matdic[name]=[i,res,atm]
        #        
        matitem=self.SortNameByResNmbAtmNmb(matdic)
        trglst=[]; reflst=[]
        for i in matitem:
            ii=self.trgdic[i]; jj=self.refdic[i]
            trglst.append(ii); reflst.append(jj)
        if len(trglst) <= 0: return
        if len(trglst) != len(reflst):
            print "error: ntrg != nref ",len(trglst),len(reflst)
            #return
        # compute distance
        cc0=[]; cc1=[]; npair=0 #; iatm=[]; jatm=[]; rij=[]
        self.devatom=[]
        for i in range(len(trglst)):
            cc0=self.model.mol.atm[trglst[i]].cc
            cc1=self.model.mol.atm[reflst[i]].cc
            r=lib.Distance(cc0,cc1)
            if r > rmin:
                npair += 1
                self.devatom.append([trglst[i],reflst[i],r])

    def PrintDeviatedAtoms(self,rmin):
        devlst=self.ListDeviatedAtoms(rmin,False)
        self.model.ConsoleMessage(str(devlst))

    def ListDeviatedAtoms(self,rmin,setprp):
        # setprp: True for set atmprp in Atom instance
        x=[]; y=[]; xlab=[]; devlst=[]
        npair=len(self.devatom)
        x=numpy.arange(0,npair)
        if setprp:
            for atom in self.model.mol.atm: atom.atmprp=0.0
        for i in range(npair):
            ii=self.devatom[i][0] #jatm[i]
            jj=self.devatom[i][1]
            rij=self.devatom[i][2]
            if setprp: self.model.mol.atm[ii].atmprp=rij #rij[i]
            if rij < rmin: continue
            y.append(rij)
            xlab.append(str(ii)+'-'+str(jj))
            devlst.append([ii,jj,rij])
        return devlst

    def OnPlotDeviation(self,event):   
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return

        rmin=float(self.tclval.GetValue()) 
        self.DeviatedAtoms(rmin)
        devlst=self.ListDeviatedAtoms(rmin,True)
        #
        x=[]; y=[]; xlab=[]
        npair=len(devlst) # len(self.devatom)
        x=numpy.arange(0,npair)
        #for atom in self.mol.atm: atom.atmprp=0.0
        for i in range(npair):
            ii=devlst[i][0] #jatm[i]
            jj=devlst[i][1]
            rij=devlst[i][2]
            #self.mol.atm[ii].atmprp=rij #rij[i]
            y.append(rij)
            xlab.append(str(ii)+'-'+str(jj))
            devlst.append([ii,jj,rij])

        molnam='dummy'; ctrlflag=self.ctrlflag
        self.pltdev=subwin.PlotAndSelectAtoms(self.panel,-1,self.model,
                                    "Displaced atoms",molnam,"atom",ctrlflag)
        self.pltdev.SetInput(self.input)
        self.pltdev.NewPlot()
        self.pltdev.PlotXY(x,y)
        self.pltdev.PlotXLabel('Atom pair')
        self.pltdev.PlotYLabel('Distance(A)')
        self.pltdev.XTicks(xlab) # set after width setting
        
    def OnRMSFitDo(self,event):
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return

        method="CG"
        if self.rbtpow.GetValue(): method="Powell"
        #
        err,cc0,cc1=self.MakeMatchingdAtomCC()
        if err: return
        #
        if not self.batch: self.model.Message("Running RMS fit ...",0,"")
        # busy on
        self.model.mdlwin.BusyIndicator('On','rms-fit.py')
        #
        err=self.RMSFitOfTrgAndRef(method,cc0,cc1)
        if err: return 1
        
        self.OverlayReferenceWithTarget(True)
        #
        self.model.Message("",0,"")
        #
        self.model.DrawMol(True)
        
        self.model.Message("Done RMS fit.",0,"")
        # busy off
        self.model.mdlwin.BusyIndicator('Off')
        self.rmsfit=True
        return 0
    
    def OnRMSFitUndo(self,event):         
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return

        #self.mol.atm=copy.deepcopy(self.savrms)
        self.model.mol.atm=self.savrms  
        #self.applied=False
        #
        if not self.batch: self.model.DrawMol(True)       
                       
    def XXOnSelectApply(self,event):
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return

        # select atoms
        self.model.SetSelectAll(False)
        
        nsel0=0; nsel1=0
        if self.rbtmat.GetValue():
            for i in self.matchlst0:
                nsel0 += 1; self.model.mol.atm[i].select=True
            for i in self.matchlst1:
                nsel1 += 1; self.model.mol.atm[i].select=True
        elif self.rbtnon.GetValue():
            for i in self.nonmatchlst0:
                nsel0 += 1; self.model.mol.atm[i].select=True
            for i in self.nonmatchlst1:
                nsel1 += 1; self.model.mol.atm[i].select=True

        if not self.batch: self.model.DrawMol(True)        
        #
        mess="Number of selected atoms in target and reference: "
        mess=mess+str(nsel0)+","+str(nsel1)
        if not self.batch: self.model.Message(mess,0,"")
        #        
    def OnMatchingApply(self,event):
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return
        #self.backbone=self.ckbback.GetValue()
        #
        err=self.ListMatchingAtoms()        

        ntrg=len(self.matchlst0); nref=len(self.matchlst1)

        if err:
            print 'Error in listmatchingatoms, case=',self.case
            return        
        if ntrg <= 0 or nref <= 0:
            lib.MessageBoxOK("No target/reference atoms are selected.","")
            err=1
        if err: return err
        #
        non0=len(self.nonmatchlst0); non1=len(self.nonmatchlst1)
        text=str(ntrg)+" ["+str(non0)+", "+str(non1)+"]"
        self.txt=wx.StaticText(self.panel,-1,text,pos=self.messpos0,
                               size=(300,18))         
        if not self.batch: self.model.Message("Done Matching.",0,"")
        return 0

    def RMSFitOfTrgAndRef(self,method,cc0,cc1):
        #
        self.SaveMol()
        #
        rmsfit=lib.RMSFitCC(self)
        rmsfit.SetCCAndMass(cc0,cc1)
        rmsfit.SetMethod(method)
        if self.messout:
            messmethod=self.model.ConsoleMessage
        else: messmethod=None
        err,etime,ndat,rmsd,chisq,dcnt,cnt,rot=rmsfit.PerformRMSFit(messmethod)
        if err: return 1           
        #
        """
        emin=etime/60.0; semin='%6.2f' % emin 
        mess="Elasped time in RMS fit: "+str(etime)+" sec ("+semin
        mess=mess+" min) by method= "+method+"\n"
        srmsd="%6.3f" % rmsd; schisq='%6.3f' % chisq
        mess=mess+"RMSD(A),ndata: "+srmsd+","+str(len(cc1))
        self.model.ConsoleMessage(mess)
        """
        self.donermsfit=True
        self.dcnt=dcnt; self.cnt=cnt; self.rot=rot
        self.rmsd=rmsd
        return 0
    
    def SaveMol(self):
        # trg True, ref True for save
        #self.savmol=[]
        #for atom in self.mol.atm: self.savmol.append(copy.deepcopy(atom))
        self.savmol=self.model.mol.CopyAtom()
        
    def RecoverMol(self):
        #self.mol.atm=[]
        #for atom in self.savmol: self.mol.atm.append(atom)
        self.model.mol.atm=self.savmol
             
    def SortNameByResNmbAtmNmb(self,namedic):
        sortedkey=[]; sortedval=[]; tmpdic={}
        tmplst=[]; item=[]; sortedname=[]
        for k in namedic:
            tmplst.append([k,namedic[k][1],namedic[k][2]])
        item=sorted(tmplst,key=itemgetter(1,2))
        for i,j,k in item: sortedname.append(i)
        #
        return sortedname
        
    def MoveAtom(self,cc0,r2t):
        dcnt=self.dcnt; cnt=self.cnt; rot=self.rot
        cc=[cc0[:]]
        if r2t:
            cc[0][0] += dcnt[0]; cc[0][1] += dcnt[1]; cc[0][2] += dcnt[2]
            a=rot[0]; b=rot[1]; c=rot[2]
            u=lib.RotMatEul(a,b,c)
            cct=lib.RotMol(u,cnt,cc)
        else:
            a=rot[0]; b=rot[1]; c=rot[2]
            u=lib.RotMatEul(a,b,c)
            u=numpy.linalg.inv(u)
            cct=lib.RotMol(u,cnt,cc)
            cct[0][0] -= dcnt[0]; cct[0][1] -= dcnt[1]; cct[0][2] -= dcnt[2]        
        #
        cct=cct[0][:]    

        return cct         
        
    def OverlayReferenceWithTarget(self,r2t):
        # overlay target and reference molecules at position of reference molecule
        # r2t: =True for reference to target, =False for target to reference
        # dcnt[x,y,z]: movement vector of reference to center of mass position of target
        # cnt[x,y,z] : tarnaslation vector of reference to rms fit to target
        # rot[a,b,c]: rotation angle vector of reference to rms fit to parent
        dcnt=self.dcnt; cnt=self.cnt; rot=self.rot
        if len(dcnt) <= 0: return
        cc1=[]
        if r2t:
            for atom in self.model.mol.atm:
                #if atom.elm == "XX": continue
                if atom.grpnam == "mrg2":
                    cc=atom.cc[:]; cc[0] += dcnt[0]; cc[1] += dcnt[1]
                    cc[2] += dcnt[2]
                    cc1.append(cc)
            a=rot[0]; b=rot[1]; c=rot[2]
            #cnt=[xc,yc,zc]
            u=lib.RotMatEul(a,b,c)
            cct=lib.RotMol(u,cnt,cc1)
            # change coordinates of reference group
            k=-1
            for atom in self.model.mol.atm:
                atom.select=False
                #if atom.elm == "XX": continue
                if atom.grpnam == "mrg2":
                    k += 1; atom.cc=cct[k]; atom.select=True
        else:
            for atom in self.model.mol.atm:
                #if atom.elm == "XX": continue
                if atom.grpnam == "base":
                    cc=atom.cc[:]; cc1.append(cc)
            a=rot[0]; b=rot[1]; c=rot[2]
            #cnt=[xc,yc,zc]
            u=lib.RotMatEul(a,b,c)
            u=numpy.linalg.inv(u)
            cct=lib.RotMol(u,cnt,cc1)
            print 'translation (A): ', cnt
            print 'euler angles (rad): ',[a,b,c]
            # change coordinates of target group
            k=-1
            for atom in self.model.mol.atm:
                atom.select=False
                #if atom.elm == "XX": continue
                if atom.grpnam == "base":
                    k += 1; atom.select=True
                    atom.cc[0]=cct[k][0]-dcnt[0]
                    atom.cc[1]=cct[k][1]-dcnt[1]
                    atom.cc[2]=cct[k][2]-dcnt[2]

    def WriteMoveData(self,filnam):
        # see OverlayReferenceWithTarget()
        ff10='%10.6f'
        f=open(filnam,"w")
        text='title= transformation from '+self.reffile+" to "+self.trgfile
        text=text+"\n"
        f.write(text)
        f.write('comment= RMSD(A)='+str(self.rmsd)+'\n')
        s='center-of-mass translation vector(A)= '
        for i in range(3): s=s+(ff10 % self.dcnt[i])+','
        s=s[:len(s)-1]
        f.write(s+'\n')
        s='translation vector(A)= '
        for i in range(3): s=s+(ff10 % self.cnt[i])+','
        s=s[:len(s)-1]
        f.write(s+'\n')
        s='rotation angle(rad)= '
        for i in range(3): s=s+(ff10 % self.rot[i])+','
        s=s[:len(s)-1]
        f.write(s+'\n') 
        #    
        f.close()
        
    def PrintDisplacementVectors(self):
        mess="Translation vector of center fitting of reference: "
        mess=mess+'['+str(self.dcnt[0])+','+str(self.dcnt[1])+','
        mess=mess+str(self.dcnt[2])+']'
        self.model.ConsoleMessage(mess)
        mess="Translation vector of reference to fit target: "
        mess=mess+'['+str(self.cnt[0])+','+str(self.cnt[1])+','
        mess=mess+str(self.cnt[2])+']'
        self.model.ConsoleMessage(mess)
        mess="Rotation angles of reference to fit target: "
        mess=mess+'['+str(self.rot[0])+','+str(self.rot[1])+','
        mess=mess+str(self.rot[2])+']'
        self.model.ConsoleMessage(mess)
    
    def OnClose(self,event):
        #self.ctrlflag.SetCtrlFlag('comparestructure',False)
        try: self.OnDelReference(1)
        except: pass
        self.Destroy()
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
       
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
            
    def MenuItems(self):
        # Menu items
        menubar=wx.MenuBar()
        submenu=wx.Menu()
        # File menu
        submenu.Append(-1,"Open matching data", "read miatching file")
        submenu.AppendSeparator()
        submenu.Append(-1,"Save matching data","Save matching data")
        submenu.Append(-1,"Save log","Save log file")
        submenu.AppendSeparator()
        id1=wx.NewId()
        submenu.Append(id1,"Output RMS fit result",kind=wx.ITEM_CHECK)
        submenu.AppendSeparator()
        submenu.Append(-1,"Close", "Close the panel")
        menubar.Append(submenu,'File')
        # edit
        submenu=wx.Menu()
        submenu.Append(-1,"Matching data","view/edit matching file")
        submenu.Append(-1,"Log data","view/edit log file")
        menubar.Append(submenu,'Edit')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,"Document","Open help document")
        submenu.Append(-1,"Tutorial","Open tutorial panel")
        menubar.Append(submenu,'Help')
        #
        menubar.Check(id1,True)
        return menubar

    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        # File submenu
        if item == "Open matching data":
            wildcard='matching file(*.mat)|*.mat|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"r",True,"")
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                self.ReadFile(filename)
        elif item == "Save matching data":
            wildcard='mathing file(*.mat)|*.mat|All(*.*)|*.*'
            self.savefile=lib.GetFileName(self,wildcard,"w",True,"")

        elif item == "Save log":
            wildcard='log file(*.log)|*.log|All(*.*)|*.*'
            self.savefile=lib.GetFileName(self,wildcard,"w",True,"")

        elif item == "Output RMS fit result":
            self.messout=self.menubar.IsChecked(menuid)
            
        elif item == "Close":
            self.OnClose(1)
        # Edit submenu            
        elif item == "Matching data":
            pass
        elif item == "Log data":
            wildcard='Log file(*.log)|*.log|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"r",True,"")
            lib.OpenEditor(filename)            
        # Help
        elif item == "Document":
            self.HelpDocument()
        elif item == "Tutorial":
            self.Tutorial()

class TransferAtoms_Frm(RMSFitting_Frm):
    def __init__(self,parent,id,winpos=[]): #,model,ctrlflag,molnam,winpos):
        self.title='Transfer atoms'
        self.winsize=lib.WinSize((340,360))
        self.mdlwin=parent
        self.model=self.mdlwin.model
        #
        self.helpname='transfer-atoms'
        #
        #self.reffile=""
        self.readref=False
        self.apply=False
        #self.matching=False
        #self.rmsfit=False
        self.select=False
        self.savmol=self.model.mol.CopyMolecule()
        #        
        self.rmswin=None
        self.CreateButtons()
        self.rmswin.SetTitle(self.title)
        self.rmswin.helpname=self.helpname
        
    def CreateButtons(self):    
        self.rmswin=RMSFitting_Frm(self.mdlwin,-1,winsize=self.winsize)
        self.rmswin.btnmatdel.Disable()
        [w,h]=self.rmswin.winsize
        xpos=0; ypos=h+5; wp=w; hp=self.winsize[1]-ypos
        h=self.rmswin.hpanel # h=220
        self.panel=self.rmswin.panel
        yloc=h+5
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)                
        yloc += 8
        wx.StaticText(self.panel,-1,"4)Select atoms:",pos=(10,yloc),
                      size=(90,18))
        self.rbtnon=wx.RadioButton(self.panel,-1,"nonmatched",pos=(105,yloc),
                                   size=(85,18),style=wx.RB_GROUP)
        self.rbtmat=wx.RadioButton(self.panel,-1,"matched",pos=(195,yloc),
                                   size=(75,18))
        self.rbtnon.SetValue(True)
        btnselapl=wx.Button(self.panel,-1,"Apply",pos=(270,yloc),
                            size=(45,20))
        btnselapl.Bind(wx.EVT_BUTTON,self.OnSelectApply)
        #        
        yloc += 22
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)        
        yloc += 8
        wx.StaticText(self.panel,-1,"5)Transfer selected reference atoms:",
                      pos=(10,yloc),size=(210,18))
        yloc += 22
        self.btntrsundo=wx.Button(self.panel,-1,"Undo",pos=(50,yloc),
                                  size=(45,20))
        self.btntrsundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        self.btnapl=wx.Button(self.panel,-1,"Apply",pos=(110,yloc),
                              size=(45,20))
        self.btnapl.Bind(wx.EVT_BUTTON,self.OnApply)
        self.btnok=wx.Button(self.panel,-1,"OK",pos=(170,yloc),
                             size=(35,20))
        self.btnok.Bind(wx.EVT_BUTTON,self.OnOK)
        self.btncls=wx.Button(self.panel,-1,"Close",pos=(230,yloc),
                              size=(45,20))
        self.btncls.Bind(wx.EVT_BUTTON,self.OnClose)
        
    def CheckChainNam(self):
        chaindic={}
        for i in range(len(self.model.mol.atm)):
            name=self.model.mol.atm[i].chainnam
            chaindic[name]=True
        namlst=chaindic.keys()
        namlst.sort()
        namtxt=""
        for s in namlst: namtxt=namtxt+s+","
        ns=len(namtxt); namtxt=namtxt[:ns-1]
        if len(namlst) > 1:
            mess="Tere are several chains: "+namtxt
            self.model.ConsoleMessage(mess+" in target molecule")
            mess="Tere are several chains: "+namtxt
            mess=mess+"\n Do you want to change them?"
            dlg=lib.MessageBoxYesNo(mess,"")
            if dlg == wx.NO: return        
            else: self.ChangeChainNam()
    
    def ChangeChainNam(self):
        mess='Enter data (ex. "A","C","B","C",... for "A" to "C" and "B"'
        mess=mess+' to "C",...)'
        chaintxt=wx.GetTextFromUser(mess,'Input data')
        item=chaintxt.split(",")
        if len(item) <= 1:
            lib.MessageBoxOK("Wrong data. Try again!","")
            return
        changedic={}
        for i in range(0,len(item),2):
            nam1=lib.GetStringBetweenQuotation(item[i])[0]
            nam2=lib.GetStringBetweenQuotation(item[i+1])[0]
            changedic[nam1]=nam2
        mess=[]; nchan=0
        if len(changedic) > 0:
            for atom in self.model.mol.atm:
                nam=atom.chainnam; seq=atom.seqnmb+1
                if changedic.has_key(nam):
                    atom.chainnam=changedic[nam]; nchan += 1   
                    tmp="atom "+str(seq)+": chain name "+nam+" was changed to "
                    tmp=tmp+changedic[nam]
                    mess.append([tmp])
        if len(mess) > 0: 
            mess="Chain names of "+str(nchan)+" atoms has changed"
            self.model.ConsoleMessage(mess)
            #self.model.ConsoleMessage(mess)
    
    def SaveConectData(self):
        self.savcon=[]
        for atom in self.model.mol.atm:
            self.savcon.append([atom.seqnmb,atom.conect,atom.bndmulti])
    
    def RecoverConectData(self):
        for i in range(len(self.model.mol.atm)):
            ii=self.rmswin.seqnew2old[i]
            if ii <= 0: continue
            con=self.savcon[ii][1]
            newcon=[]
            for j in con:
                if self.rmswin.seqold2new[j] < 0: continue
                newcon.append(self.rmswin.seqold2new[j])
            self.model.mol.atm[i].conect=newcon
            self.model.mol.atm[i].bndmulti=self.savcon[ii][2]
                                 
    def Transfer(self):
        if not self.rmswin.rmsfit:
            lib.MessageBoxOK("Perform RMS fit before this command.","")                
            return
        #
        self.trsr2t=True; self.trst2r=False
        savbackbone=self.rmswin.backbone
        self.rmswin.backbone=False
        savmol=self.model.mol.CopyMolecule()

        self.rmswin.MakeCase2AtomNameDic([],False)

        if self.trsr2t:    
            self.TransferAtoms(True)
        if self.trst2r:
            self.TransferAtoms(False)       

        self.rmswin.backbone=savbackbone

        #if not self.batch: self.model.DrawMol(True)

        ntrn=len(self.transatm)
        mess=str(ntrn)+" atoms were transfered from reference to target "
        mess=mess+"molecule."
        if not self.rmswin.batch: self.model.Message(mess,0,"")

    def TransferAtoms(self,r2t):
        # r2t: True for transfer from reference to target, False for oppsit        
        nsel,sellst=self.model.ListSelectedAtom()
        #
        self.rmswin.RecoverMol()
        #
        newmol=molec.Molecule(self.model)
        #trgitem=[]; trgnmb=[]
        natm=len(self.model.mol.atm)
        # sort self.totdic
        # shuld sort with resnmb
        if len(sellst) <= 0:
            lib.MessageBoxOK("No transfer atoms are selected.","")            
            return
        nref=0
        for i in sellst:
            if self.model.mol.atm[i].grpnam == "mrg2": nref += 1
        if nref <= 0:
            lib.MessageBoxOK("No transferable atoms in reference.","")            
            return
        #
        self.SaveConectData()
        self.model.DeleteBonds("all",False)
        savsellst=sellst
        if r2t:
            sellst=savsellst
            newmol=self.TransferAtomsToTarget(newmol,sellst)
        else:
            sellst=savsellst
            newmol=self.TransferAtomsToReference(newmol,sellst)
        
        ntrn=len(self.transatm)
        mess=str(ntrn)+" atoms were transfered from reference to target "
        mess=mess+"molecule."
        self.model.ConsoleMessage(mess)
        # prit transfered atoms
        mess=""; resdic={}
        for i in range(len(self.transatm)):
            seq=str(self.transatm[i][0]); atm=self.transatm[i][1]
            res=self.transatm[i][2]+":"+str(self.transatm[i][3])
            chain=self.transatm[i][4]
            resdic[res]=[self.transatm[i][2],self.transatm[i][3]]
            mess=mess+'seqnmb='+seq+',atmnam='+atm+',res='+res
            mess=mess+',chain='+chain+'\n'
        self.model.ConsoleMessage(mess)
        # print transfered residues
        reslst=resdic.values()
        mess=str(len(reslst))+" residues were transfered from reference to "
        mess=mess+"target molecule."
        self.model.ConsoleMessage(mess)
        if len(reslst) > 0:
            reslst.sort(key=lambda x:x[1])
            mess=""
            for res,nmb in reslst:  mess=mess+res+":"+str(nmb)+","
            ns=len(mess); mess=mess[:ns-1]
            self.model.ConsoleMessage(mess)
        #
        self.model.mol.atm=[]
        for atom in newmol.atm: self.model.mol.atm.append(atom)
        
        self.model.mol.DeleteAllTers()
        #
        self.RecoverConectData()
        
    def TransferAtomsToTarget(self,newmol,sellst):
        # transfer selected atoms from refrence to target molecule
        trgitem=[]; trgnmb=[]
        natm=len(self.model.mol.atm)
        #
        self.totdic0={}; self.seqdic={}
        for i in range(len(self.model.mol.atm)):
            if self.model.mol.atm[i].grpnam != "base": continue
            thick=self.model.mol.atm[i].thick
            res=self.model.mol.atm[i].resnmb
            atm=self.model.mol.atm[i].atmnmb
            name=self.model.mol.MakeFullAtomName(i,self.rmswin.chainnam,
                                         self.rmswin.resnam,self.rmswin.resnmb)
            self.totdic0[name]=[i,res,atm]
        #
        for i in sellst:
            if self.model.mol.atm[i].grpnam == "base": continue
            name=self.model.mol.MakeFullAtomName(i,self.rmswin.chainnam,
                                         self.rmswin.resnam,self.rmswin.resnmb)
            if self.rmswin.trgdic.has_key(name): continue
            res=self.model.mol.atm[i].resnmb
            atm=self.model.mol.atm[i].atmnmb
            self.totdic0[name]=[i,res,atm]
        #        
        trgitem=self.rmswin.SortNameByResNmbAtmNmb(self.totdic0)
        #
        natm0=0; cc1=[]; add0=[]; nadd=0
        self.transatm=[] 
        self.rmswin.seqold2new=len(self.model.mol.atm)*[-1]
        for i in trgitem:
            ii=self.totdic0[i][0]
            atom=self.model.mol.CopyIthAtom(ii) #copy.deepcopy(self.mol.atm[ii])
            name=self.model.mol.MakeFullAtomName(ii,self.rmswin.chainnam,
                                         self.rmswin.resnam,self.rmswin.resnmb)
            if self.rmswin.trgdic.has_key(name):
                
                self.rmswin.seqnew2old.append(atom.seqnmb)
                self.rmswin.seqold2new[atom.seqnmb]=natm0
                
                atom.select=False
                atom.seqnmb=natm0
                newmol.atm.append(atom)
                natm0 += 1
            elif self.rmswin.refdic.has_key(name):
                jj=self.totdic0[name][0] #self.refdic[i]
                atomj=self.model.mol.atm[jj]
                if atomj.select:
                    self.rmswin.seqnew2old.append(-1)
                    atomx=self.model.mol.CopyIthAtom(jj) #copy.deepcopy(atomj)
                    atomx.grpnam="base"
                    cc1=atomx.cc[:]
                    #print 'atomj.seqnmb,cc1',atomj.seqnmb,cc1
                    cc1=self.rmswin.MoveAtom(cc1,True)
                    atomx.thick=thick
                    atomx.cc=cc1
                    atomx.conect=[]; atomx.bndmulti=[]
                    atomx.seqnmb=natm0
                    atomx.select=True
                    newmol.atm.append(atomx)
                    add0.append(jj)
                    natm0 += 1; nadd += 1
                    self.transatm.append([jj,atomj.atmnam,atomj.resnam,
                                          atomj.resnmb,atomj.chainnam])
            else:
                print str(i)+":"+name+" was not found."
        natm1=natm0 
        for atom in self.model.mol.atm:
            if atom.grpnam == "base": continue

            self.rmswin.seqnew2old.append(atom.seqnmb)
            self.rmswin.seqold2new[atom.seqnmb]=natm1

            atom.select=False
            atom.seqnmb=natm1
            
            newmol.atm.append(atom)
            natm1 += 1

        return newmol

    def TransferAtomsToReference(self,newmol,sellst):
        #!# not wroking!!! 25 Oct 2013, KK
        natm=len(self.model.mol.atm)
 
        natm0=0 
        self.rmswin.seqold2new=len(self.model.mol.atm)*[-1]
        self.rmswin.seqnew2old=[]
        #
        for atom in self.model.mol.atm:
            if atom.grpnam == "mrg2": continue
            
            self.rmswin.seqnew2old.append(atom.seqnmb)
            self.rmswin.seqold2new[atom.seqnmb]=natm0

            atom.select=False
            atom.seqnmb=natm0
            
            newmol.atm.append(atom)
            natm0 += 1
        
        self.totdic0={}; self.seqdic={}
        for i in range(len(self.model.mol.atm)):
            if self.model.mol.atm[i].grpnam != "mrg2": continue
            res=self.model.mol.atm[i].resnmb
            atm=self.model.mol.atm[i].atmnmb
            name=self.model.mol.MakeFullAtomName(i,self.rmswin.chainnam,
                                     self.rmswin.resnam,self.rmswin.resnmb)
            self.totdic0[name]=[i,res,atm]

        print 'len-totdic0 before trg add',len(self.totdic0)   
        for i in sellst:
            if self.model.mol.atm[i].grpnam == "mrg2": continue
            name=self.model.mol.MakeFullAtomName(i,self.rmswin.chainnam,
                                     self.rmswin.resnam,self.rmswin.resnmb)
            if self.rmswin.refdic.has_key(name): continue
            res=self.model.mol.atm[i].resnmb
            atm=self.model.mol.atm[i].atmnmb
            self.totdic0[name]=[i,res,atm]
        print 'len-totdic0 after trg add',len(self.totdic0)
        
        refitem=self.SortNameByResNmbAtmNmb(self.totdic0)
        
        print 'len-sorted key',len(refitem)
        self.transatm=[]     
        natm1=natm0; cc0=[]; add1=[]; nadd=0
        for i in refitem:
            ii=self.totdic0[i][0]
            atom=self.model.mol.CopyIthAtom(ii) #copy.deepcopy(self.mol.atm[ii])
            name=self.model.mol.MakeFullAtomName(ii,self.rmswin.chainnam,
                                     self.rmswin.resnam,self.rmswin.resnmb)
            if self.rmswin.refdic.has_key(name):
                
                self.rmswin.seqnew2old.append(atom.seqnmb)
                self.rmswin.seqold2new[atom.seqnmb]=natm1
                
                atom.select=False
                atom.seqnmb=natm1
                newmol.atm.append(atom)
                natm1 += 1
            elif self.rmswin.trgdic.has_key(name):
                jj=self.totdic0[name][0] #self.refdic[i]
                atomj=self.model.mol.atm[jj]
                if atomj.select:
                    self.rmswin.seqnew2old.append(-1)
                    atomx=self.model.mol.CopyIthAtom(jj) #copy.deepcopy(atomj)
                    atomx.grpnam="base"
                    cc0=atomx.cc[:]
                    #print 'atomj.seqnmb,cc1',atomj.seqnmb,cc1
                    cc0=self.rmswin.MoveAtom(cc0,False) # False=ref, True=trg 
                    atomx.thick=self.refbndthic
                    atomx.cc=cc0
                    atomx.seqnmb=natm1
                    atomx.select=True
                    newmol.atm.append(atomx)
                    add1.append(jj)
                    natm1 += 1; nadd += 1
            else:
                print str(i)+":"+name+" was not found."
        
        return newmol
    
    def OnSelectApply(self,event):
        if not self.readref:
            self.model.Message("No reference atoms.",0,"")
            return
        # select atoms
        self.model.SetSelectAll(False)
        
        nsel0=0; nsel1=0
        if self.rbtmat.GetValue():
            for i in self.matchlst0:
                nsel0 += 1; self.model.mol.atm[i].select=True
            for i in self.matchlst1:
                nsel1 += 1; self.model.mol.atm[i].select=True
        elif self.rbtnon.GetValue():
            for i in self.nonmatchlst0:
                nsel0 += 1; self.model.mol.atm[i].select=True
            for i in self.nonmatchlst1:
                nsel1 += 1; self.model.mol.atm[i].select=True

        if not self.batch: self.model.DrawMol(True)        
        #
        mess="Number of selected atoms in target and reference: "
        mess=mess+str(nsel0)+","+str(nsel1)
        if not self.batch: self.model.Message(mess,0,"")
        #
        self.select=True
                          
    def OnUndo(self,event):
        #self.model.mol.atm=self.sav
        self.model.mol=self.savmol
        self.model.DrawMol(True)
        self.apply=False
        self.rmswin.rmsfit=False
        self.select=False
    
    def OnApply(self,event):
        if not self.rmswin.rmsfit:
            lib.MessageBoxOK("rms fit was not performed.","")            
            return
        """
        if not self.select:
            lib.MessageBoxOK("No atoms are selected for transfere.","")            
            return
        """
        self.apply=True
        self.Transfer()
        self.rmswin.OnDelReference(1)
        #
        #self.CheckResNmb()        
        self.CheckChainNam()
        
        
        self.select=False

    def OnOK(self,event):
        if not self.apply: self.OnApply(1)
        self.OnClose(1)

    def OnClose(self,event):
        self.rmswin.OnClose(event)
        event.Skip()
 
def RepalceResdiue(model):
    """ Repalce residues 
    
    :param obj model: 'Model' instance
    """
    if model.mol is None: return
    nsel,sellst=self.ListSelectedAtom()
    if nsel <= 2:
        mess='Select more than three atoms.'
        lib.MessageBoxOK(mess,self.classnam+'(ReplaceWithSameResidue)')
        return
    resnam0=self.mol.atm[0].resnam
    resnmb0=self.mol.atm[0].resnmb
    chainnam0=self.mol.atm[0].chainnam
    atmnam0=[]; cc0=[]
    for i in sellst: 
        atmnam0.append(self.mol.atm[i].atmnam)
        cc0.append(self.mol.atm[i].cc[:])
    natm0=len(sellst)
    if len(pdbfile) == 0:
        wcard='PDB file(*.pdb)|*.pdb'
        mess='Open PDB file for '+resnam0
        pdbfile=lib.GetFileName(wcard=wcard,rw='r',message=mess)    
        if len(pdbfile) <= 0: return
    if not lib.CheckFileExists(pdbfile): return
    # molobj and zmt of refrence molecule
    molobj=molec.Molecule(self)
    molobj.BuildFromPDBFile(pdbfile)
    resdat1=lib.ResDat(molobj.atm[0])
    resnam1=molobj.atm[0].resnam
    if resnam1 != resnam0:
        mess='Residues are not the same between selected "'+resnam1+'"'
        mess=mess+' and in PDB file "'+resnam1+'"\n'
        mess=mess+'Would you like to continue?'
        ans=lib.MessageBoxYesNo(mess,'Model(ReplaceWithSameResidue)')
        if not ans: return
    atmnam1=[]
    for atom in molobj.atm: atmnam1.append(atom.atmnam)
    atmnam1=atmnam1[:natm0]
    if atmnam1 != atmnam0:
        mess='Atom names are not the same between selected '+str(atmnam0)
        mess=mess+' and in PDB file '+str(atmnam1)+'\n'
        mess=mess+'Would you like to continue?'
        ans=lib.MessageBoxYesNo(mess,'Model(ReplaceWithSameResidue)')
        if not ans: return
    natm1=len(molobj.atm)
    #pnts1=[molobj.atm[0].cc[:],molobj.atm[1].cc[:],molobj.atm[2].cc[:]]
    zelm,zpnt,zprm=lib.CCToZM(molobj)
    # change the conformation
    pnts0=[self.mol.atm[sellst[0]].cc[:],self.mol.atm[sellst[1]].cc[:],
           self.mol.atm[sellst[2]].cc[:]]
    curobj=molec.Molecule(self)
    for i in sellst: curobj.atm.append(self.mol.atm[i])
    zelm0,zpnt0,zprm0=lib.CCToZM(curobj)
    for i in range(len(zelm0)-1):
        zpnt[i]=zpnt0[i]; zprm[i]=zprm0[i]
    zmtatm=lib.ZMToCC(zelm,zpnt,zprm)
    #
    for i in range(len(zmtatm)):
        cc=[zmtatm[i][1],zmtatm[i][2],zmtatm[i][3]]
        molobj.atm[i].cc=cc[:]
    pnts1=[molobj.atm[0].cc[:],molobj.atm[1].cc[:],molobj.atm[2].cc[:]]
    delta=[pnts0[0][0]-pnts1[0][0],pnts0[0][1]-pnts1[0][1],
           pnts0[0][2]-pnts1[0][2]]
    # rotate molobj
    u=lib.RotMatPnts(pnts1,pnts0)
    cc=[]; cntr=[pnts1[0][0],pnts1[0][1],pnts1[0][2]]
    for i in range(len(molobj.atm)): cc.append(molobj.atm[i].cc[:])
    cc=lib.RotMol(u,cntr,cc)
    for i in range(len(molobj.atm)): molobj.atm[i].cc=cc[i][:]
    # match th eposition
    for i in range(len(molobj.atm)):
        for j in range(3): 
            molobj.atm[i].cc[j] += delta[j]
        molobj.atm[i].resnam=resnam0
        molobj.atm[i].resnmb=resnmb0
        molobj.atm[i].chainnam=chainnam0
    cc1=[]
    for i in range(natm0): cc1.append(molobj.atm[i].cc[:])
    rmsd=lib.ComputeRMSD(cc0,cc1)
    # molobj of selected residue
    resdat=lib.ResDat(self.mol.atm[sellst[0]])
    resatmlst=self.ListResDatAtoms(resdat)
    part1obj,partobj,part2obj=self.SplitMolObject(resatmlst,self.mol)
    self.mol.atm=[]
    # merge parts
    molobjs=[part1obj,molobj,part2obj]
    for obj in molobjs:
        if obj is None: continue
        self.MergeMolecule(obj.atm,True,drw=False)
    self.SetSelectResidue(resdat,True)
    # reset current molobject
    idx=self.molctrl.GetCurrentMolIndex()
    self.molctrl.SetMol(idx,self.mol)
    #
    mess='"'+resdat+'" was replaced with the residue "'+resdat1
    mess=mess+'" in pdbfile='+pdbfile+'\n'
    mess=mess+'Number of replaced atoms(old,new)='
    mess=mess+str(natm0)+', '+str(natm1)+'\n'
    mess=mess+'rmsd='+str(rmsd)
    self.ConsoleMessage(mess)
    self.MsgNumberOfAtoms(1)
    #
    if drw: self.FitToScreen(True,True)

def ReplaceLigandInComplex(model,envrad=4.0,optmethod='Powell',addbond=True):
    """ Replace lignad in a complex with that in the other complex of
     the same protein
    
    :param obj model: an instance of 'Model' class
    :param float envrad: distance of environment residues  from ligand
                         to be used in rms-fit betwee the current and 
                         reference proteins in the complexes
    :param str optmethod: optimization method to be used in rms-fit
    :param bool addbond: True for add bonds to ligand, False for do not.
    """
    def FindSeqNmbOfAtomNam(molobj,atmnam,resnam,resnmb):
        seqnmb=-1
        for i in xrange(len(molobj.atm)):
            atom=molobj.atm[i]
            if atom.atmnam == atmnam and atom.resnam == resnam and \
                         atom.resnmb == resnmb:
                seqnmb=i; break
        return seqnmb
    
    def MoveAtom(cc,dcnt,cnt,rot):
        newcc=cc[:]
        newcc[0] += dcnt[0]; newcc[1] += dcnt[1]; newcc[2] += dcnt[2]
        a=rot[0]; b=rot[1]; c=rot[2]
        #cnt=[xc,yc,zc]
        u=lib.RotMatEul(a,b,c)
        cct=lib.RotMol(u,cnt,[newcc])
        return cct[0]
    # model: an instance of 'Model' class
    fum=model
    # read reference protein complex
    wcard='PDB file(*.pdb)|*.pdb'
    filename=lib.GetFileName(fum.mdlwin,wcard,'r',True)
    if len(filename) <= 0: return # canceled
    mess='replace-ligand.py: ligand pdb file='+filename
    fum.ConsoleMessage(mess)
    #
    mol=molec.Molecule(fum) 
    mol.BuildFromPDBFile(filename)
    # read radius for env atoms
    mess='Please enter distance from ligand atoms(default=4.0).\n'
    mess=mess+' for using atoms in RMS fit'
    text=wx.GetTextFromUser(mess,caption='ReplaceLigand',default_value='4.0')
    if len(text) <= 0: renv=envrad
    else:
        try: renv=float(text.strip())
        except:
            mess='Wrong data.'
            lib.MessageBoxOK(mess,'ReplaceLigand')
            return
    # check residue sequence
    ans,diflst=fum.CompareAAResidueSequence(mol,filename)
    if not ans: 
        mess='The residue sequences are not the same between the current mol'
        mess=mess+' and refrence mol.\n'
        mess=mess+'Whould you like to continue?'
        yesno=lib.MessageBoxYesNo(mess)
        if not yesno: return
    # make heavy atom list
    atmlst=fum.ListHeavyAtoms()
    nenv,envatmlst=fum.FindRadiusAtoms(renv,atmlst=atmlst)
    if nenv < 3:
        mess='Number of env atoms within '+str(envrad)+' is less than'
        mess=mess+' '+str(nadd)+'. Can not perform RMS fit.'
        lib.MessageBoxOK(mess,'Model(ReplaceLigandInComplex')
        return
    #
    cc0=[]; cc1=[]
    for i in envatmlst:
        atom=fum.mol.atm[i]; atmnam=atom.atmnam; resnam=atom.resnam
        resnmb=atom.resnmb
        seqnmb=FindSeqNmbOfAtomNam(mol,atmnam,resnam,resnmb)
        if seqnmb > 0:
            ccmol=mol.atm[seqnmb].cc
            cc0.append(atom.cc[:]); cc1.append(ccmol[:])
    nfit=len(cc0)
    if len(cc0) <= 0:
        mess='Number of matiched atoms is zero. Can not perform rms fit.'
        lib.MessageBoxOK(mess,'Model(ReplaceLigandInComplex')
        return  
    # busy on
    fum.mdlwin.BusyIndicator('Open')
    fum.mdlwin.BusyIndicator('On','running rms-fit.py')
    # perform rms-fit    
    rmsfit=lib.RMSFitCC(fum)
    rmsfit.SetCCAndMass(cc0,cc1)
    rmsfit.SetMethod(optmethod)
    err,etime,ndat,rmsd,chisq,dcnt,cnt,rot= \
             rmsfit.PerformRMSFit(messmethod=fum.ConsoleMessage)
    fum.mdlwin.BusyIndicator('Off','')
    if err:
        mess='Failed to rms fit'
        lib.MessageBoxOK(mess,'Model(ReplaceLigandInComplex')
        return        
    # replace ligands
    newligmol=molec.Molecule(fum)
    seq=-1
    for i in xrange(len(mol.atm)):
        atom=mol.atm[i]; res=atom.resnam
        if const.AmiRes3.has_key(res): continue
        if res in const.WaterRes: continue
        seq += 1; atom.seqnmb=seq; atom.conect=[]; cc=atom.cc[:]
        newlig=res
        newcc=MoveAtom(cc,dcnt,cnt,rot)
        atom.cc=newcc[:]
        newligmol.atm.append(atom)
    #
    if len(newligmol.atm) > 0:
        fum.SaveMol() # save mol for undo
        ligatm=[]
        ligatm=fum.ListNonAAResidueAtoms(wat=True)
        oldlig=fum.mol.atm[ligatm[0]].resnam
        fum.mol.DelAtoms(ligatm)
        #
        fum.MergeMolecule(newligmol.atm,True,drw=False)
        for i in range(len(fum.mol.atm)): fum.mol.atm[i].seqnmb=i
        if addbond:
            nsel,sellst=fum.ListSelectedAtom()
            if nsel > 1: fum.mol.AddBondUseBL(sellst)
        #
        fum.DrawMol(True)
        # message
        mess='replace-ligand.py:\n'
        mess=mess+'The ligand '+oldlig+' in '+fum.mol.inpfile+' was replaced '
        mess=mess+'with '+newlig+' in '+filename+'\n'
        mess=mess+'Number of environment atoms='+str(len(envatmlst))+'\n'
        mess=mess+'Number of atoms(heavy) used to rms-fit='+str(nfit)+'\n'
        fum.ConsoleMessage(mess)
    else:
        mess='No ligand atoms in ligand file='+filename
        lib.MessageBoxOK(mess,'replace-ligand.py')

def TruncateProtein(cap=0,model=None):
    """ Make reduced model of protein/protein complex
    
    :param int cap: 0 for Ace/Nme caps, 1 for hydrogen caps
    :param obj model: 'Model' instance
    """
    def KeepResidues(fum,dellst):
        lst=[]   
        if len(dellst) > 0:
            keepres=[]; conresdat=[]
            parmol=fum.mol.CopyMolecule()
            #if cap == 0:
            acednglst=FindDanglingBond(parmol,dellst,' N  ')
            nmednglst=FindDanglingBond(parmol,dellst,' C  ')
            for i in acednglst:
                atmi=parmol.atm[i]
                for j in atmi.conect:
                    if parmol.atm[j].atmnam == ' C  ':
                        resdat=lib.ResDat(parmol.atm[j])
                        conresdat.append(resdat)
            if len(conresdat) > 0:
                for i in nmednglst:
                    atmi=parmol.atm[i]
                    for j in atmi.conect:
                        if parmol.atm[j].atmnam == ' N  ':
                            resdat=lib.ResDat(parmol.atm[j])
                            if resdat in conresdat: keepres.append(resdat)
            if len(keepres) > 0:
                lst=[]
                for i in dellst:
                    atom=parmol.atm[i]; resdat=lib.ResDat(atom)
                    if not resdat in keepres: lst.append(i)
            else: lst=dellst[:]
        return lst,parmol

    def FindDanglingBond(parmol,dellst,at):
        """
        
        :param str at: atmnam, ' N  ' or ' C  '
        """
        # find -NH, or -CO in polypeptide
        dngatmlst=[]
        for i in xrange(len(parmol.atm)):
            atom=parmol.atm[i]
            if not atom.select: continue
            resnam=atom.resnam
            if not const.AmiRes3.has_key(resnam): continue
            if atom.atmnam != at: continue
            for j in atom.conect:
                if j in dellst:
                    dngatmlst.append(i); break
        return dngatmlst
    
    def MakeBondsOfCaps(fum,acebnddic,nmebnddic):
        trglst=[]
        names=['ACE','NME']; atmnams=[' N  ',' C  ']
        for i in range(2):
            for atom in fum.mol.atm:
                if atom.resnam == names[i]: trglst.append(atom.seqnmb)
        for atom in fum.mol.atm:
            resdat=lib.ResDat(atom)
            if acebnddic.has_key(resdat): 
                if acebnddic[resdat] == atom.atmnam: 
                    trglst.append(atom.seqnmb)
            if nmebnddic.has_key(resdat): 
                if nmebnddic[resdat] == atom.atmnam: 
                    trglst.append(atom.seqnmb)
        if len(trglst) > 0: fum.mol.AddBondUseBL(trglst)
        return trglst
    
    def MakeAceForNterm(fum,parmol,dellst):
        dngatmlst=FindDanglingBond(parmol,dellst,' N  ')
        aceatm=[]; seq=-1; resnmb=0; resdatlst=[]; bnddic={}
        for i in dngatmlst:
            atom=parmol.atm[i]
            atmnam=atom.atmnam
            resdat=lib.ResDat(atom)
            seq,resnmb,atms,resdati,bnddici=MakeACE(resdat,parmol,seq,
                                                         resnmb)
            aceatm=aceatm+atms; bnddic.update(bnddici)
            resdatlst=resdatlst+resdati
        return aceatm,resdatlst,bnddic

    def MakeNmeForCterm(fum,parmol,dellst,skipreslst):
        dngatmlst=FindDanglingBond(parmol,dellst,' C  ')
        nmeatm=[]; seq=-1; resnmb=0; bnddic={}
        for i in dngatmlst:
            atom=parmol.atm[i]
            atmnam=atom.atmnam
            resdat=lib.ResDat(atom)
            seq,resnmb,atms,bnddici=MakeNME(resdat,parmol,seq,resnmb,
                                                skipreslst)
            nmeatm=nmeatm+atms; bnddic.update(bnddici)
        return nmeatm,bnddic
    
    def MakeACE(resdat,parmol,seq,resnmb):
        def SetAtomAttrib(seq,parmol,iatm,conatm,resnmb):
            atom=parmol.CopyIthAtom(iatm)
            atomcon=atom.conect[:]
            seq += 1; atom.seqnmb=seq
            atom.resnam='ACE'; atom.resnmb=resnmb
            #atom.conect=[conatm]; atom.bndmulti=[1]
            atom.conect=[]; atom.bndmulti=[]
            return seq,atom,atomcon
        
        rch=1.09; hnam=[' H1 ',' H2 ',' H3 ']
        resdic={}; atmlst=[]; resdatlst=[]; bnddic={}
        for i in xrange(len(parmol.atm)):
            atom=parmol.atm[i]; atmnam=atom.atmnam
            res=lib.ResDat(atom)
            if res == resdat and atmnam == ' N  ':
                for j in atom.conect:
                    if parmol.atm[j].atmnam == ' C  ':
                        resnmb += 1; resdatj=lib.ResDat(parmol.atm[j])
                        seq,atmj,conj=SetAtomAttrib(seq,parmol,j,i,resnmb)
                        cseq=seq; resdatlst.append(resdatj)
                        aceresdat=lib.ResDat(atmj); bnddic[res]=atmnam
                        atmlst.append(atmj)
                        for k in conj:
                            if parmol.atm[k].atmnam == ' O  ':
                                seq,atmk,con=SetAtomAttrib(seq,parmol,k,cseq,
                                                           resnmb)
                                atmlst.append(atmk)
                        for k in conj:
                            if parmol.atm[k].atmnam == ' CA ':
                                seq,atmk,conk=SetAtomAttrib(seq,parmol,k,cseq,
                                                            resnmb)
                                caseq=seq; cc0=atmk.cc
                                atmlst.append(atmk)
                                for l in conk:
                                    if l == k: continue
                                    if l == j: continue
                                    if parmol.atm[l].atmnam == ' HA ':
                                        seq,atml,con=SetAtomAttrib(seq,parmol,
                                                                l,caseq,resnmb)
                                        atmlst.append(atml)
                                count=-1
                                for l in conk:
                                    if l == k: continue
                                    if l == j: continue
                                    if parmol.atm[l].atmnam != ' N'and \
                                              parmol.atm[l].atmnam != ' HA ':
                                        count += 1
                                        seq,atml,con=SetAtomAttrib(seq,parmol,
                                                                l,caseq,resnmb)
                                        atml.atmnam=hnam[count]; atml.elm=' H'
                                        atml.SetAtomParams(' H')
                                        cc=lib.ChangeLength(cc0,atml.cc,rch)
                                        atml.cc=cc[:]
                                        atmlst.append(atml)
                break                     
        return seq,resnmb,atmlst,resdatlst,bnddic
    
    def MakeNME(resdat,parmol,seq,resnmb,skipreslst):
        def SetAtomAttrib(seq,parmol,iatm,conatm,resnmb):
            atom=parmol.CopyIthAtom(iatm)
            atomcon=atom.conect[:]
            seq += 1; atom.seqnmb=seq
            atom.resnam='NME'; atom.resnmb=resnmb
            #atom.conect=[conatm]; atom.bndmulti=[1]
            atom.conect=[]; atom.bndmulti=[]
            return seq,atom,atomcon
        #
        rch=1.09; rnh=1.01; hnam=[' H1 ',' H2 ',' H3 ']
        resdic={}; atmlst=[]; bnddic={}
        for i in xrange(len(parmol.atm)):
            atmi=parmol.CopyIthAtom(i) #parmol.atm[i]
            atmnam=atmi.atmnam
            res=lib.ResDat(atmi)
            if res == resdat and atmnam == ' C  ':
                for j in atmi.conect:
                    if parmol.atm[j].atmnam == ' N  ':
                        resdatj=lib.ResDat(parmol.atm[j])
                        if resdatj in skipreslst: break
                        resnmb += 1
                        seq,atmj,conj=SetAtomAttrib(seq,parmol,j,i,resnmb)
                        nseq=seq
                        atmlst.append(atmj); bnddic[res]=atmnam
                        for k in conj:
                            resk=parmol.atm[k].resnam
                            if resk == 'PRO':
                                if parmol.atm[k].atmnam == ' CD ':
                                    seq,atmk,con=SetAtomAttrib(seq,parmol,k,
                                                               nseq,resnmb)
                                    atmk.atmnam=' H  '; atmk.elm=' H'
                                    cc0=atmj.cc[:]
                                    cc=lib.ChangeLength(cc0,atmk.cc,rnh)
                                    atmk.cc=cc[:]; atmk.SetAtomParams(' H')
                                    atmlst.append(atmk)
                            else:
                                if parmol.atm[k].atmnam == ' H  ':
                                    seq,atmk,con=SetAtomAttrib(seq,parmol,k,
                                                               nseq,resnmb)
                                    atmlst.append(atmk)
                        for k in conj:
                            if parmol.atm[k].atmnam == ' CA ':
                                seq,atmk,conk=SetAtomAttrib(seq,parmol,k,nseq,
                                                           resnmb)
                                caseq=seq
                                cc0=atmk.cc[:]
                                atmlst.append(atmk)
                                count=-1
                                for l in conk:
                                    if l == k: continue
                                    if l == j: continue
                                    count += 1
                                    seq,atml,con=SetAtomAttrib(seq,parmol,l,
                                                               caseq,resnmb)
                                    if atml.elm != ' H':
                                        cc=lib.ChangeLength(cc0,atml.cc,rch)
                                        atml.cc=cc[:]
                                    atml.atmnam=hnam[count]; atml.elm=' H'
                                    atml.SetAtomParams(' H')
                                    atmlst.append(atml)    
                break
        return seq,resnmb,atmlst,bnddic

    if model is None:
        mess='Needs "Model" instance'
        lib.MessageBoxOK(mess,'buidl.TruncateProtein')
        return
    #
    fum=model
    #
    natm0=len(fum.mol.atm)
    dellst=[]; nsel=0; bndlst=[]
    for atom in fum.mol.atm:
        if not atom.resnam in const.AmiRes3: continue
        if not atom.select: dellst.append(atom.seqnmb)
        else: nsel += 1
    if nsel <= 0:
        mess='Please select residues to be kept'
        lib.MessageBoxOK(mess,'TruncateProtein(OnApply)')
        return
        if len(dellst) <= 0: return
    #
    if cap == 0:
        # delete selected atoms except keep resdiues
        dellst,parmol=KeepResidues(fum,dellst)
        fum.mol.DelAtoms(dellst)
        # ACE
        aceatms,resdatlst,acebnddic=MakeAceForNterm(fum,parmol,dellst)
        fum.MergeMolecule(aceatms,False,drw=False)
        # NME
        nmeatms,nmebnddic=MakeNmeForCterm(fum,parmol,dellst,resdatlst)
        fum.MergeMolecule(nmeatms,False,drw=False)
        # make bonds
        trglst=MakeBondsOfCaps(fum,acebnddic,nmebnddic)
        # select caps 
        for atom in fum.mol.atm:
            if atom.seqnmb in trglst: atom.select=True
            else: atom.select=False    
    elif cap == 1: 
        # delete selected atoms
        fum.mol.DelAtoms(dellst)
        fum.CapNCtermsWithHydrogens(drw=False)
    
    fum.DrawMol(True)
    #self.CapDanglingBonds()       
    mess='TruncatProtein:\n'
    mess=mess+'Number of atoms was reduced from '+str(natm0)
    mess=mess+' to '+str(len(fum.mol.atm))
    fum.ConsoleMessage(mess)
    if cap == 0:
        nace=len(aceatms)/6; nnme=len(nmeatms)/6
        mess='Number of ACE and NME are '+str(nace)+' and '+str(nnme)
        mess=mess+', respectively'
        fum.ConsoleMessage(mess)

class TruncateProtein_Frm(wx.MiniFrame):
    """ Not completed 21May2016 
    
    note: if you create an instance of this class with 'parent=None',
    you have to execte 'del instance-name' to remove! 
    """
    def __init__(self,parent,id,winpos=[],savfile=None):
        self.title='Truncate Protein'
        self.model=parent
        if self.model is None: return # need del xxx for delete
        winsize=lib.WinSize((230,300)) #400) #366) #(155,330) #(155,312)
        if len(winpos) <= 0: winpos=lib.WinPos(self.model.mdlwin)
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,\
                   size=winsize,style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|\
                                                      wx.FRAME_FLOAT_ON_PARENT)      
        #
        self.parent=parent
        self.winctrl=self.model.winctrl
        pid=self.model.pid
        self.winlabel='TruncateProtein'
        self.model.winctrl.SetWin(self.winlabel,self)
        self.mol=self.model.mol
        #
        self.helpname=self.winlabel
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        #
        scrdir='H://Test'
        #
        self.Initialize()
        self.reslst=['Ligand']
        self.distance=4.0
        self.filename=''
        #
        self.CreatePanel()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.Show()
        #
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnNotify)    
    
    def CreatePanel(self):
        [w,h]=self.GetClientSize(); hcb=22
        #xpos=0; ypos=0; xsize=self.size[0]; ysize=self.size[1]
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(0,0),size=(w,h)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        #w=self.size[0]; 
        # Reset button
        btnrset=subwin.Reset_Button(self.panel,-1,self.OnReset)
        #
        yloc=10
        
        wx.StaticText(self.panel,-1,"Select core residue:",
                      pos=(10,yloc+2),size=(120,18))
        self.cmbres=wx.ComboBox(self.panel,-1,'',choices=self.reslst,
                             pos=(130,yloc),size=(60,hcb),style=wx.CB_READONLY)                      
        self.cmbres.Bind(wx.EVT_COMBOBOX,self.OnSelectResidue)
        yloc += 25
        wx.StaticText(self.panel,-1,"Truncate distance(A):",
                      pos=(10,yloc),size=(140,18))
        self.tcldis=wx.TextCtrl(self.panel,-1,str(self.distance),
                         pos=(150,yloc),size=(35,18),style=wx.TE_PROCESS_ENTER)
        self.tcldis.Bind(wx.EVT_TEXT_ENTER,self.OnDistance)
        yloc += 25
        wx.StaticText(self.panel,-1,"Cap dungling bonds with",
                      pos=(10,yloc),size=(160,18))
        yloc += 20
        self.rbtace=wx.RadioButton(self.panel,-1,"ACE/NME",pos=(20,yloc),
                                   size=(70,18),style=wx.RB_GROUP)
        self.rbtace.SetValue(True)
        self.rbthyd=wx.RadioButton(self.panel,-1,"Hydrogens",pos=(100,yloc),
                                   size=(90,18))
        yloc += 25
        self.ckbsav=wx.CheckBox(self.panel,-1,'Save file',pos=(10,yloc))
        self.ckbsav.SetValue(True)
        yloc += 20
        wx.StaticText(self.panel,-1,"Path:",
                      pos=(20,yloc),size=(30,18))
        self.tcldir=wx.TextCtrl(self.panel,-1,str(self.distance),
                         pos=(60,yloc),size=(80,18),style=wx.TE_PROCESS_ENTER)
        self.tcldir.Bind(wx.EVT_TEXT_ENTER,self.OnDirectory)
        btnbrw=wx.Button(self.panel,wx.ID_ANY,"Browse",pos=(150,yloc),
                          size=(60,20))
        btnbrw.Bind(wx.EVT_BUTTON,self.OnBrowse)
        yloc += 25
        st=wx.StaticText(self.panel,-1,"File name postfix:",
                      pos=(20,yloc),size=(100,18))
        st.SetToolTipString('Leave empty to appliy default name')
        self.tclfil=wx.TextCtrl(self.panel,-1,self.filename,
                         pos=(120,yloc),size=(90,18),style=wx.TE_PROCESS_ENTER)
        self.tclfil.Bind(wx.EVT_TEXT_ENTER,self.OnFileName)
        
        
        
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),
                      style=wx.LI_HORIZONTAL)
        yloc += 8
        btnundo=wx.Button(self.panel,-1,"Undo",pos=(60,yloc),
                         size=(45,20))
        btnundo.Bind(wx.EVT_BUTTON,self.OnUndo)
        btnaply=wx.Button(self.panel,-1,"Apply",pos=(130,yloc),
                          size=(45,20))
        btnaply.Bind(wx.EVT_BUTTON,self.OnApply)
        #btnsave=wx.Button(self.panel,-1,"Save",pos=(160,yloc),size=(45,20))
        #btnsave.Bind(wx.EVT_BUTTON,self.OnSave)

    def Initialize(self):
        self.sav=self.model.mol.CopyAtom() #copy.deepcopy(self.mol.atm)        
        #
        molnam=self.model.mol.name
        self.SetTitle(self.title+' ['+molnam+']')
        
        self.keepreslst=[]
        self.applied=False
    
    def OnSelectResidue(self,event):
        self.selres=self.cmbres.GetStringSelection()
        const.CONSOLEMESSAGE('selres='+self.selres)
        
    def OnDistance(self,event):
        self.distance=self.tcldis.GetValue()
        const.CONSOLEMESSAGE('distance='+self.distance)
        
    def OnBrowse(self,event):
        pass
        
    def OnDirectory(self,event):
        self.directory=self.tcldir.GetValue()
        if os.path.isdir(self.directory):
            pass
    
    def OnFileName(self,event):
        self.filename=self.tclfil.GetValue()
        
    def RecoverAtomData(self):
        for i in xrange(len(self.model.mol.atm)):
            self.model.mol.atm[i]=self.sav[i]
    
    
    def OnApply(self,event):
        # N-term cap
        self.rbtnace.GetValue()
        self.rbtnh.GetValue()
        # C-term cap
        self.rbtcnme.GetValue()
        self.rbtch.GetValue()
        #
        self.Truncate()
        
    def Truncate(self,cap=0):
        pass
    def OnUndo(self,event):
        self.model.mol.atm=self.sav #copy.deepcopy(self.sav)        
        self.applied=False
        self.model.DrawMol(True)
        
    def OnSave(self,event):
        filename=''
        self.SaveFile(filename)
    
    def SaveFile(self,filename):
        pass
    
    def OnReset(self,event):
        self.Initialize()
        self.mol=self.model.mol
    
    def OnNotify(self,event):
        try: item=event.message
        except: return        
        if item == 'SwitchMol' or item == 'ReadFiles': self.OnReset(1)
    
    def OnClose(self,event):
        try: self.model.winctrl.CloseWin(self.winlabel)
        except: pass
        self.Destroy()
    
    def HelpDocument(self):
        self.model.helpctrl.Help(self.helpname)
        
    def Tutorial(self):
        self.model.helpctrl.Tutorial(self.helpname)
        
    def MenuItems(self):
        """ Menu and menuBar data
        
        """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        # Option
        iid=wx.NewId()
        submenu.Append(iid,'Rotation axis flag',
                       'Set rotation axis to connected atoms',
                       kind=wx.ITEM_CHECK)
        #submenu.Check(iid,self.setrotaxis)
        submenu.Append(-1,'Remove rotation axis','Remove rotation axis')
        submenu.AppendSeparator()
        submenu.Append(-1,'Remove labels','Remove labels')
        submenu.AppendSeparator()
        submenu.Append(-1,'Del dummy atoms(X)','Delete dummy atoms')
        submenu.AppendSeparator()
        submenu.Append(-1,'Close','Close the window')        
        menubar.Append(submenu,'Option')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        
        menubar.Append(submenu,'Help')
        #
        return menubar

    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)
        if item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()
            