#!/bin/sh
# -*- coding:utf-8

#-----------
# script: fuplot.py
# ----------
# function: plot properties of GAMESS and FMO
# usage: This script is executed in PyShell console.
#        >>> fum.fum.ExecuteAddOnScript('fuplot.py',False)
# ----------
# change history
# modified for fu ver.0.2.0 18May2015
# the first version for fu ver.0.0.0 23Del2015
# -----------

import sys
sys.path.insert(0,'.')

import os
import copy
import wxversion
wxversion.select("2.8")
import wx
import wx.py.crust
#import psutil
import time
import math

import numpy
import scipy
if int(scipy.__version__.split('.')[1]) >= 11:
    from scipy.sparse.csgraph import _validation # for pyinstaller
    from scipy.optimize import minimize # need for pyinstaller

import matplotlib # for pyinstaller
matplotlib.interactive( True ) # for pyinstaller
from matplotlib.figure import Figure # for pyinstaller
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas # for pyinstaller
from matplotlib.backends.backend_wxagg import NavigationToolbar2Wx # for pyinstaller

import fumodel
import view
import ctrl
import rwfile
import lib
import subwin
import graph
import const
import cube
try: import fucubelib
except: pass

#class Plot_Frm(wx.Frame):
@lib.CLASSDECORATOR(lib.FUNCCALL)
class Plot(wx.Frame):
    # main program for draw FMO property graphs
    def __init__(self,parent,id): #,winpos,fuplot):
        winsize=lib.WinSize((410,250)) #300))
        #print 'SYSTEM',const.SYSTEM
        #if const.SYSTEM != const.WINDOWS: winsize=(400,300)
        winpos=[0,0]
        if lib.GetPlatform() == "WINDOWS": winsize=lib.WinSize((400,300))
        self.title='fuplot'
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
        #
        """ parent=None, model=None"""
        #self.mdlwin=None
        #self.model=None
        
        self.mdlwin=parent
        #if parent:
        self.model=parent.model
        self.mdlargs=self.model.mdlargs
        
        self.mdlwintitle=self.mdlwin.GetTitle()
        ###self.fuplot=fuplot
        self.pltargs={}
        
        self.draw=None
        #
        self.platform=lib.GetPlatform()        
        self.winsize=winsize
        # set icon
        try: lib.AttachIcon(self,const.FUPLOTICON)
        except: pass
        #
        """
        #self.font=lib.GetFont(4,8)
        self.font=self.GetFont()
        self.font.SetPointSize(8)
        self.pltargs['SetFontToPlot']=self.font
        self.SetFontToPlot() #(self.font)
        """
        lib.SetFrameFont(self)
        """
        try:
            self.addonmenu=self.model.setctrl.GetParam('add-on-fuplot')        # program directory
            if len(self.addonmenu):
                print 'addonmenu',self.addonmenu
        except: pass
        """
        #!!!self.exedir=lib.GetExeDir(self.program)
        # change directory
        #???self.curdir=lib.ChangeToPreviousDir(self.exedir,self.inifile)
        self.curdir=os.getcwd()
        # CtrlFlag instance
        self.ctrlflag=self.model.ctrlflag #ctrl.CtrlFlag()
        #
        self.addmode=True
        self.datadic={}
              
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        self.bgcolor="white"
        self.SetBackgroundColour(self.bgcolor) 
        # Create Menu
        self.menubar=None
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        # accept drop files
        droptarget=lib.DropFileTarget(self)
        self.SetDropTarget(droptarget)
        #
        self.prpobjdic={} # {prpnam:FileReader instance,...}
        self.propertyitems=[] #['Orbital','Orbital energy','PIE/PEDA','CT charge','Mulliken','MEP','Density']    
        self.prpdic={}
        self.plotted=[]
               
        self.infotext=''
        self.datnam=''
        self.pltprp=-1
        #self.molint=False
        self.piedadat=[]
        self.onebody=[]
        self.frgnam=[]
        self.mulcharge=[]
        self.ctcharge=[]
        # files
        self.filterfile=''
        self.filternam=''
        self.openfiles=[]
        self.fileout=[]
        self.fileinp=[]
        self.filepdb=[]
        #
        self.graphnam=[]
        
        
        self.graph={}
        self.idmax=0
        #
        self.fmodatadic={}
        self.drvdatadic={}
        self.drvprpdic={}
        self.drvprpinfo={}
        #
        self.datalist=[]
        self.selected=''
        
        self.opendrvdatpan=False
        self.drvdatpan=None
        self.opendrvprppan=False
        self.drvprppan=None

        self.pltpiedisable=False
        self.pltctchgdisable=True
        self.pltmulchgdisable=True
        self.pltespotdisable=True
        self.pltdendisable=True
        self.pltorbdisable=True

        self.pltpie=0
        self.pltctchg=0
        self.pltmulchg=0
        self.pltespot=0
        self.pltden=0
        self.pltorb=0

        # Create StatusBar
        #self.statusbar=self.CreateStatusBar()
        #self.CreateSplitWindow()
        self.CreatePropertyPanel()
        self.CreateSelectDataPanel()
        #
        self.Bind(wx.EVT_SIZE,self.OnResize)    
        ###self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()

    def SetFontToPlot(self):
        if self.pltargs.has_key('SetFontToPlot'): 
            font=self.pltargs['SetFontToPlot']
            self.SetFont(font)
            del self.pltargs['SetFontToPlot']
        else: pass
        
    def CreatePropertyPanel(self):
        # create property choice panel on right hand side
        [w,h]=self.GetClientSize() #self.GetSize()
        xsize=w/2-20; ysize=h
        #width=w/2-20; height=h
        xpos=w/2; ypos=0
        xloc=10; yloc=5
        self.prppan=wx.Panel(self,-1,pos=(xpos,ypos),size=(w/2,h)) #ysize))
        self.prppan.SetBackgroundColour("light gray")

        wx.StaticText(self.prppan,wx.ID_ANY,'Plot data:',pos=(xloc,yloc),size=(100,20)) 
        self.btngist=wx.Button(self.prppan,-1,"Info",pos=(xloc+135,yloc-2),size=(40,22))
        self.btngist.Bind(wx.EVT_BUTTON,self.OnViewInfo)
        self.btngist.SetToolTipString('View information')
        yloc += 20
        self.tcsel=wx.TextCtrl(self.prppan,-1,"",pos=(xloc,yloc),size=(xsize,20),
                               style=wx.TE_READONLY|wx.TE_MULTILINE) #|wx.HSCROLL) 
        #self.tclsel.Bind(wx.EVT_TEXT_ENTER,self.OnSelected)       
        yloc += 25
        stprp=wx.StaticText(self.prppan,-1,'Plot props:',pos=(xloc,yloc),size=(65,20))
        stprp.SetToolTipString('Select items and push "View" or "Plot"')
        #yloc += tcheight+5
        self.btnview=wx.Button(self.prppan,wx.ID_ANY,"View",pos=(xloc+70,yloc),size=(40,22))
        self.btnview.Bind(wx.EVT_BUTTON,self.OnViewProperty)
        self.btnview.SetToolTipString('View selected property')
        self.btnplt=wx.Button(self.prppan,wx.ID_ANY,"Plot",pos=(xloc+130,yloc),size=(45,22))
        self.btnplt.Bind(wx.EVT_BUTTON,self.OnPlotProperty)
        self.btnplt.SetToolTipString('Plot selected property')
        yloc += 25
        tcheight=h-yloc-8 #50 #8
        self.lcprp=wx.ListCtrl(self.prppan,-1,pos=(xloc,yloc),size=(xsize,tcheight),
                               style=wx.LC_REPORT|wx.LC_NO_HEADER) #|wx.LC_SORT_ASCENDING)
        #self.lcprp.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnSelectPrpItem)
        self.SetPropertyItems()
        self.lcprp.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK,self.OnPropRightClick)
        
        
        
        #yloc += tcheight+10
        #wx.StaticLine(self.prppan,pos=(-1,yloc),size=(w/2,2),style=wx.LI_HORIZONTAL) 
        # button to pop-up derived data creation panel 
        #yloc += 10
        #self.btndrvprp=wx.ToggleButton(self.prppan,-1,label='Make derived prop',
        #                           pos=(40,yloc),size=(120,22)) 
        #self.btndrvprp.SetToolTipString('Open derived property panel (toggle)')
        #self.btndrvprp.Bind(wx.EVT_TOGGLEBUTTON,self.OnDerivedPorpPanel)

        
        """ if recover the following codes, YYxxxxx methods and #YY comments should be recover too
        #yloc += 20
        yloc +=  tcheight+5 #25
        wx.StaticLine(self.prppan,pos=(0,yloc),size=(w/2,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.prppan,-1,'Done list:',pos=(xloc,yloc),size=(100,20))
        yloc += 20; lstheight=h-yloc-40
        lstheight=h-yloc-35
        self.lcplted=wx.ListCtrl(self.prppan,-1,pos=(xloc,yloc),size=(xsize,lstheight),
                               style=wx.LC_REPORT|wx.LC_NO_HEADER) #|wx.LC_SORT_ASCENDING)
        self.lcplted.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnPlotted)
        self.SetPlotted()
        yloc = h-28
        self.btnrmv=wx.Button(self.prppan,-1,"Remove",pos=(40,yloc),size=(50,20))
        self.btnrmv.Bind(wx.EVT_BUTTON,self.OnRemoveProp)
        self.btnrmv.Disable()
        self.btnrmv.SetToolTipString('under construction')
        self.btnsav=wx.Button(self.prppan,-1,"Save",pos=(110,yloc),size=(50,20))
        self.btnsav.Bind(wx.EVT_BUTTON,self.OnSaveProp)
        self.btnsav.Disable()
        self.btnsav.SetToolTipString('under construction')
        """

    def OnViewInfo(self,event):
        self.ViewInfo() #self.selected,self.infotext)
 
    def ViewInfo(self):
        
        text=''; filename=''
        if self.datadic.has_key(self.selected):
            filename=self.datadic[self.selected][0]
            if self.datadic[self.selected][1] == 'cube':
                text='Information of '+self.selected+'\n\n'
                info,natoms,atmcc=rwfile.ReadCubeFile(filename)
                text=text+cube.DrawCubeData_Frm.MakeCubeDataInfoText(filename,'Cube',natoms,info)
            else: text=self.infotext         
        elif self.drvdatadic.has_key(self.selected):
            filename=self.selected
            text='component files='
            for lst in self.drvdatadic[self.selected]:
                text=text+lst[0]+'('+lst[1]+')'+', '
            text=text[:-1]+'\n'
            text=text+self.infotext
        if len(text) > 0:
            title='View '+filename+' information'
            text='Filter file='+self.filterfile+'\n'+text   
            self.OpenTextEditor(title,text,'View')
        
    def OnViewProperty(self,event):
        prplst=self.GetSelectedProperty()
        text=''
        if len(prplst) <= 0:
            dlg=lib.MessageBoxOK("Please select a plotable prop.","")
            return
        prp=prplst[0]
        if prp == 'Opt.Coordinates': 
            optcoordlst=self.MakeOptCoordList(True)
            text=self.TextCoord(optcoordlst)
        elif prp == 'Coordinates':
            coordlst=self.MakeOptCoordList(False)
            text=self.TextCoord(coordlst)
        elif prp == 'Orbital energy': text=self.TextOrbitalEnergy()
        elif prp == 'Orbitals': text=self.TextOrbital()           
        elif prp == 'PIE' or prp =='PIEDA': text=self.TextPIEDA()
        elif prp == 'CTCharge': text=self.TextCTCharge()
        elif prp == 'Mulliken.Q(2)-Q(1)': text=self.TextMullikenQ()
        elif prp == 'Cube': 
            text='file='+self.selected+'\n'
            text=text+'prp='+prp+'\n\n'
        else: text=self.TextProperty(prp)
        #    
        title='View '+prp
        self.OpenTextEditor(title,text,'Edit')
    
    def TextMullikenQ(self):
        text='file='+self.selected+'\n'
        prp='Mulliken.Q(2)-Q(1)'
        text=text+'prp='+prp+'\n\n'
        datlst=self.prpdic['Mulliken.Q(2)-Q(1)']
        j=1; nmb=len(datlst)
        """
        datlst1=self.prpdic['Mulliken.Q(1)']
        datlst2=self.prpdic['Mulliken.Q(2)']
        j=1; nmb=len(datlst1)
        if datlst1.count('end') > 1: text=text+'data number '+str(j)+':\n'
        for i in range(len(datlst1)): 
            value=datlst1[i]
            if value == 'end': 
                j += 1
                text=text[:-1]+'\n'
                if i != nmb-1: text=text+'data number '+str(j)+':\n'
                continue
            value=float(datlst2[i])-float(datlst1[i])
            text=text+str(str(value))+','
        """
        for i in range(len(datlst)): 
            value=datlst[i]
            if value == 'end': 
                j += 1
                text=text[:-1]+'\n'
                if i != nmb-1: text=text+'data number '+str(j)+':\n'
                continue
            text=text+str(str(value))+','

        text=text[:-1]+'\n'      

        return text
        
    def TextOrbitalEnergy(self):
        text='file='+self.selected+'\n'
        text=text+'prp='+prp+'\n\n'
        orbenglst=self.prpdic['Orbitals'][1][4]
        for i in range(len(orbenglst)):
            value=orbenglst[i]
            text=text+str(i+1)+')'+str(value)+','
        text=text[:-1]+'\n'
        return text
    
    def TextCTCharge(self):
        prp='PIEDA'; item='Q(I->J)'
        text='file='+self.selected+'\n'
        text=text+'prp='+'CTCharge'+'\n\n'
        npairs=len(self.prpdic[prp][item])
        text=text+'Number of CTCharge data='+str(npairs)+'\n\n' 
        return text
    
    def TextPIEDA(self):
        prp='PIEDA'
        keylst=self.prpdic[prp].keys()
        text='file='+self.selected+'\n'
        text=text+'prp=PIEDA\n'
        npairs=len(self.prpdic[prp][keylst[0]])
        text=text+'Number of PIEDA data='+str(npairs)+'\n\n'
        #
        text=text+'Items='
        for item in keylst: text=text+item+','
        text=text[:-1]+'\n'
        return text
    
    def TextOrbital(self):
        text='file='+self.selected+'\n'
        text=text+'prp=Orbitals:\n\n'
        orbeng=self.prpdic['Orbitals'][1][4]
        orbsym=self.prpdic['Orbitals'][1][5]
        orbcoeff=self.prpdic['Orbitals'][1][6]
        for j in range(len(orbcoeff)):
            text=text+'No. '+str(j+1)+' ('+orbsym[j]+')'+' E='+str(orbeng[j])+'\n'
            for i in range(len(orbcoeff[j])):
                value=orbcoeff[j][i]
                text=text+str(value)+','
            text=text[:-1]+'\n'
        return text
        
    def TextProperty(self,prp):
        text='file='+self.selected+'\n'
        text=text+'prp='+prp+'\n\n'
        datlst=self.prpdic[prp]
        j=1; nmb=len(datlst)
        if datlst.count('end') > 1: text=text+'data number '+str(j)+':\n'
        for i in range(len(datlst)): 
            value=datlst[i]
            if value == 'end': 
                j += 1
                text=text[:-1]+'\n'
                if i != nmb-1: text=text+'data number '+str(j)+':\n'
                continue
            text=text+str(value)+','
        text=text[:-1]+'\n'      

        return text            

    def MakePropertyList(self,prp):
        prplstlst=[]
        datlst=self.prpdic[prp]
        nmb=len(datlst)
        prplst=[]
        for i in range(len(datlst)): 
            value=datlst[i]
            if value == 'end': 
                if i != nmb-1: 
                    prplstlst.append(prplst); prplst=[]
                continue
            prplst.append(value)
        if len(prplst) > 0: prplstlst.append(prplst)
        return prplstlst

    def OpenTextEditor(self,title,text,mode):
        ##if len(mode) == 0: mode='Edit'
        retmethod=self.ReturnFromTextEditor
        winpos=wx.GetMousePosition()
        winsize=[480,300]
        parent=self

        self.texteditor=True
        self.editor=subwin.TextEditor_Frm(parent,-1,winpos,winsize,title,text,
                                          retmethod,mode=mode)
    
    def ReturnFromTextEditor(self):
        self.texteditor=False
        
    def TextCoord(self,coordlst):
        ff12='%12.6f'; fi4='%4d'; ff3='%3.1f'
        coordtext='file='+self.selected+'\n'
        coordtext=coordtext+'prp=Coordinates\n\n'
        idat=0
        for coordlst in coordlst:
            idat += 1
            coordtext=coordtext+'Data number='+str(idat)+'\n'   #title
            coordtext=coordtext+'\n' # blank
            for label,x,y,z in coordlst:
                if label == 'end': continue
                try: lab=ff3 % label
                except: lab=label
                sx=ff12 % x; sy=ff12 % y; sz=ff12 % z
                coordtext=coordtext+lab+' '+sx+' '+sy+' '+sz+'\n'
            coordtext=coordtext+'\n'
        return coordtext
            
    def MakeOptCoordList(self,opt):
        coordlst=[]
        
        if opt: prpnam='Opt.Coordinates'
        else: prpnam='Coordinates'
        prpdic=self.prpdic[prpnam]
        if len(prpdic) <= 0:
            print 'not found Opt.Coordinates'
            return coordlst
        chg=[]; elm=[]; seq=[]
        if self.prpdic.has_key('NATOMS'): natm=int(self.prpdic['NATOMS'][0])
        else: 
            natm=len(self.model.mol.atm)
        if natm <= 0:
            mess='Number of atoms is zero. Unable to continue'
            leb.MessageBoxOK(mess,'fuplt(MakeOptCoordList)')
            return coordlst
        if prpdic.has_key('NUC.CHARGE'): chg=prpdic['NUC.CHARGE']
        elif prpdic.has_key('ELEMENT'): elm=prpdic['ELEMENT']
        else: 
            seq=range(natm); seq=numpy.array(seq); seq=seq+1
        x=prpdic['X']
        y=prpdic['Y']
        z=prpdic['Z']
        ndata=min([len(x),len(y),len(z)])
        clst=[]; nmb=0; iat=0
        for i in range(ndata):
            if x[i] == 'end' or y[i] == 'end' or z[i] == 'end':
                coordlst.append(clst); clst=[]; nmb += 1; iat=0
                continue
            iat += 1
            if iat <= natm:
                if len(seq) > 0: label=seq[i]
                if len(chg) > 0: label=chg[i]
                if len(elm) > 0: label=elm[i]
                clst.append([label,x[i],y[i],z[i]])
        return coordlst
         
    def YYOnPlotted(self,event):
        """ not completed"""
        selectedlst=[]
        item=-1
        while 1:
            item = self.lcplted.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item != -1: selectedlst.append(item)
            if item == -1: break
        print 'selectedlst',selectedlst
                       
    def YYSetPlotted(self):
        """ make lsit of properties in output file and set them to LC"""
        self.lcplted.DeleteAllItems()
        self.lcplted.InsertColumn(0,'#',width=110,format=wx.LIST_FORMAT_LEFT)
        self.lcplted.InsertColumn(1,'stat',width=15,format=wx.LIST_FORMAT_LEFT)
        #
        for i in range(len(self.plotted)):
            txt=self.plotted[i]
            indx=self.lcplted.InsertStringItem(i,txt) #str(i+1))
            self.lcplted.SetStringItem(indx,1,'')

    def SetPropertyItems(self):
        self.lcprp.DeleteAllItems()
        #self.lcprp.InsertColumn(0,'#',width=80,format=wx.LIST_FORMAT_LEFT)
        self.lcprp.InsertColumn(0,'#',width=15,format=wx.LIST_FORMAT_LEFT)
        self.lcprp.InsertColumn(1,'Item',width=110,format=wx.LIST_FORMAT_LEFT)
        self.lcprp.InsertColumn(2,'numb',width=30,format=wx.LIST_FORMAT_RIGHT)
        #
        for i in range(len(self.propertyitems)):
            txt=self.propertyitems[i]
            if self.prptypdic.has_key(txt): nmb=self.prptypdic[txt][1]
            else: nmb=1 
            indx=self.lcprp.InsertStringItem(i,str(i+1))
            self.lcprp.SetStringItem(indx,1,txt)
            self.lcprp.SetStringItem(indx,2,str(nmb))
            
    def OnRemoveProp(self,event):
        print 'OnremoveProp'
    def OnSaveProp(self,event):
        print 'OnSaveProp'

    def CreateSelectDataPanel(self):
        # create select panel on left hand side
        [w,h]=self.GetClientSize()
        xpos=0; ypos=0
        xsize=w/2; ysize=h
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(w/2,h))
        self.panel.SetBackgroundColour("light gray")
        width=w/2 #-20
        xloc=5; yloc=5
        wx.StaticText(self.panel,wx.ID_ANY,'Loaded file list:',pos=(xloc+5,yloc),size=(100,20)) 
        wclb=w/2-xpos-22; hclb=h-100 #h-125 #140
        yloc += 20
        self.lbdat=wx.ListBox(self.panel,-1,pos=(xloc+5,yloc),size=(wclb,hclb),
                                      style=wx.LB_HSCROLL|wx.LB_SORT) #
        self.lbdat.Bind(wx.EVT_RIGHT_DOWN,self.OnDataRightClick)
        self.lbdat.SetToolTipString('List of data obtained by filer')
        # command button
        #xloc=wclb/2; 
        yloc1=yloc+hclb+10 
        btnclr=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(10,yloc1),size=(45,22))
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearData)
        btnclr.SetToolTipString('Clear all data')
        btnrmv=wx.Button(self.panel,wx.ID_ANY,"Remove",pos=(60,yloc1),size=(55,22))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnRemoveData)
        btnrmv.SetToolTipString('Remove data from the list')
        btnsel=wx.Button(self.panel,-1,label='Set for plot',
                                   pos=(120,yloc1),size=(75,22)) 
        btnsel.SetToolTipString('Set selected data for plot')
        btnsel.Bind(wx.EVT_BUTTON,self.OnSelectForPlot)
        yloc1 += 25
        wx.StaticLine(self.panel,pos=(-1,yloc1),size=(w/2,2),style=wx.LI_HORIZONTAL) 
        # button to pop-up derived data creation panel 
        yloc1 += 10
        self.btndrvdat=wx.ToggleButton(self.panel,-1,label='Make derived data',
                                   pos=(40,yloc1),size=(120,22)) 
        self.btndrvdat.SetToolTipString('Open derived data panel (toggle)')
        self.btndrvdat.Bind(wx.EVT_TOGGLEBUTTON,self.OnDerivedDataPanel)
        #wx.StaticLine(self.panel,pos=(100,yloc1-8),size=(2,40),style=wx.LI_VERTICAL) 
        #yloc1 += 50
        #self.drvpanpos=[60,yloc1]; self.drvpansize=[wclb,80]
        if self.opendrvdatpan: self.OnDerivedDataPanel(0)
        #
        wx.StaticLine(self.panel,pos=(w/2-4,0),size=(2,h),style=wx.LI_VERTICAL) 
    
    def MessageSelect(self):
        mess='Select a item'
        lib.MessageBoxOK("Select a file in loaded file list.","")

    def GetCubeFile(self):
        name=self.tcsel.GetValue()
        filename=self.datadic[name][0]
        #name=name.split(':',1)
        #filename=name[1]
        base,ext=os.path.splitext(filename) 
        if ext == '.mep' or ext == '.den' or ext == '.cub': return filename
        else: return '' 
        
    def OnPlotProperty(self,event):
        prplst=self.GetSelectedProperty()
        if len(prplst) <= 0: return
        prp=prplst[0]
        #plttyp=self.prpdic[prp][0]
        #print 'pltpyp',plttyp
        self.PlotProperty(prp) #,plttyp)
                
    def PlotProperty(self,prp): #,plttyp):
   
        if len(prp) <= 0:
            lib.MessageBoxOK('No property, '+prp,'fuplt(PlotProperty')
            return
        #for prp in prplst:
        """
        prporg=''
        if prp == 'Mulliken.Q(2)-Q(1)': 
            prporg=prp; prp='Mulliken.Q(1)'
        """
        if prp == 'Orbital':
            pass
        
        elif prp == 'Orbital energy':
            orbsetdic=self.prpdic['Orbitals']
            orbitallst=[orbsetdic[1][4]]              
            self.orbengobj=PlotOrbitalEnergy(self,orbitallst)                    
        
        elif prp == 'PIE': self.PlotFragmentProperty(prp)
        elif prp == 'PIEDA': self.PlotFragmentProperty(prp)
        elif prp == 'CTCharge': self.PlotFragmentProperty(prp)
        elif prp == 'Mono.Energies': self.PlotFragmentProperty(prp)
        elif prp == 'Cube': self.OpenDrawCubeWin()
            
        elif prp == 'Opt.Coordinates':
            self.CreateMolecules(True)
        
        elif prp == 'Coordinates': self.CreateMolecules(False)
        else:
            prptyp=self.prptypdic[prp][0]
            items=prptyp.split('-')
            prptyp=items[0].strip()
            atom=''
            if len(items) >= 2: atom=items[1].strip()
            if prptyp == 'bar' or prptyp == 'line':
                #if prporg == "": 
                datlst=self.MakePropertyList(prp)
                if len(datlst) <= 0: return
                winlabel='Plot property'
                if atom == 'atom': self.PlotOnMatPlotLib(prp,datlst[0],'atom')
                else:
                    winlabel='Plot property'
                    winsize=lib.WinSize((600,300))
                    self.mpl=subwin.MatPlotLib_Frm(self,-1,self.model,[0,0],winsize,winlabel)
                    self.mpl.Show()
                    #self.mpl.Clear()
                    self.mpl.SetGraphType(prptyp)
                    self.mpl.PlotTitle(prp)                
                    ndat=len(datlst[0])
                    x=range(ndat); x=numpy.array(x); x=x+1
                    if len(datlst) == 1: self.mpl.PlotXY(x,datlst[0])
                    else:
                        for y in datlst: self.mpl.PlotXY(x,y)

        self.plotted.append(prp)
        #YY self.SetPlotted()
    
    def PlotOnMatPlotLib(self,prp,datlst,selectitem):
        """ atom property """
        molnam=self.model.mol.name; ctrlflag=self.model.ctrlflag
        if selectitem == 'atom':
            natm=len(self.model.mol.atm)
            if natm != len(datlst):
                mess='Unable to plot, since numbers of data and atoms are different.'
                lib.MessageBoxOK(mess,'fuplot(PlotInMatPlotLib)')
                return
        elif selectitem == 'fragment':
            frgnamlst=self.model.frag.ListFragmentName()
            nfrg=len(frgnamlst)
            if nfrg != len(datlst):
                mess='Unable to plot, since numbers of data and fragments are different.'
                lib.MessageBoxOK(mess,'fuplot(PlotInMatPlotLib2)')
                return   
        else: return
        #
        self.mpl=subwin.PlotAndSelectAtoms(self.mdlwin,-1,self.model,prp,selectitem) #,ctrlflag) 
        maxvalue=max(datlst)
        selval=maxvalue*0.5
        self.mpl.SetInput('>'+str(selval))
        if selectitem == 'atom':
            targets=self.model.ListTargetAtoms()
            atmnmb=[]; dat=[]
            for i in targets:
                atmnmb.append(self.model.mol.atm[i].seqnmb+1)
                dat.append(datlst[i])
            xnmb=atmnmb
        elif selectitem == 'fragment':
            frgnamlst=self.model.frag.ListFragmentName()
            frgnmb=[]; dat=[]
            for i in range(len(frgnamlst)): frgnmb.append(i) 
            for i in frgnmb: dat.append(datlst[i-1])
            xnmb=frgnmb
        # setup graph
        self.mpl.SetGraphType("bar")
        self.mpl.SetColor("b")
        self.mpl.NewPlot()
        self.mpl.PlotXY(xnmb,dat) #datlst)
        self.mpl.PlotXLabel('Sequence number of '+selectitem)
        self.mpl.PlotTitle(prp)
        #self.mpl.PlotYLabel('Arbitary unit')
    def CreateMolecules(self,opt):
        # coordlst: [ [ [mol1.atm1 an,cc],..  ], [mol1.atm1cc],... ]
        coordlst=self.MakeOptCoordList(opt)
        file=self.datadic[self.selected][0]
        xyzmollst=[]
        for moldat in coordlst:
            xyzmol=[]
            for atmdat in moldat:
                #if atmdat[0].isdigit():
                try:
                    an=int(float(atmdat[0])+0.01); elm=const.ElmSbl[an]
                except: elm=atmdat[0]
                x=atmdat[1]; y=atmdat[2]; z=atmdat[3]
                xyzmol.append([elm,x,y,z])
            xyzmollst.append(xyzmol)
        self.model.BuildMolFromXYZs(xyzmollst,file)

    def GetSelectedProperty(self):  
        selectedlst=[]
        item=-1
        while 1:
            item = self.lcprp.GetNextItem(item, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
            if item != -1: selectedlst.append(item)
            if item == -1: break
        prplst=[]
        for item in selectedlst: prplst.append(self.propertyitems[item])
        
        return prplst
        
    def OpenDrawCubeWin(self):
        mode=1 # no menu mode
        winsize=lib.MiniWinSize([100,365]) #([100,355])
        mdlwinpos=self.mdlwin.GetPosition()
        mdlwinsize=self.mdlwin.GetClientSize()
        winpos=[mdlwinpos[0]+mdlwinsize[0],mdlwinpos[1]+50]
        #if const.SYSTEM == const.MACOSX: winsize=[85,315]
        if mode == 1: winsize[1] -= 25 # no menu in the case of mode=1
        self.cubewin=cube.DrawCubeData_Frm(self.mdlwin,-1,winpos,winsize,self.model,self,mode) # mode=1
        self.cubewin.Show()
                
    def CloseDrawCubeWin(self):
        self.cubewin.Destroy()
                              
    def OnCloseAll(self,event):
        print 'OnCloseAll'
        
    def OnClearData(self,event):
        self.datadic={}
        self.SetDataList()
        self.tcsel.SetValue('')
        
    def OnSelectForPlot(self,event):

        self.selected=self.lbdat.GetStringSelection()
        if self.selected == '': 
            self.MessageSelect()
            self.prpdic={}
            self.plotted=[]
            return
        else: self.SelectForPlot()

    def SelectForPlot(self):
            # YYself.plotted=[]; self.lcplted.DeleteAllItems()
            self.lcprp.DeleteAllItems()
            self.tcsel.SetValue('')
            # save atom color for recovering later
            try: self.model.SaveAtomColor(True)
            except: pass
            #
            filternam=''
            if self.datadic.has_key(self.selected): filternam=self.datadic[self.selected][1]
            self.propertyitems=[]
            if filternam == 'cube': 
                self.propertyitems=['Cube']
                self.prpdic={}; self.prptypdic={}
            else:
                #self.prpdic,self.prptypdic=self.prpobjdic[filternam].ReadOutputFile(file)
                self.prpdic,self.prptypdic=self.ReadProperties()
                if len(self.prpdic) <= 0:
                    mess='No properties to plot'
                    lib.MessageBoxOK(mess,'OnSelectForPlot')
                    return
                self.infotext='Information of '+self.selected+'\n\n'
                title=''
                for keynam,lst in self.prptypdic.iteritems():     
                    #info=False
                    prptyp=lst[0]
                    if prptyp == 'info':
                        #self.infotext='filename='+self.selected+'\n'
                        self.MakeInfoText(keynam)
                    elif prptyp == 'data': continue
                    elif prptyp == 'orb':
                        if self.prpdic.has_key('Orbitals'):
                            if len(self.prpdic['Orbitals'][1][4]) > 0: 
                                self.propertyitems.append('Orbital energy')
                            if len(self.prpdic['Orbitals'][1][6]) > 0:
                                self.propertyitems.append('Orbitals')
                    elif prptyp == 'pie' or prptyp == 'piedat':
                        self.propertyitems.append('PIEDA')
                        self.propertyitems.append('CTCharge')
                    else: self.propertyitems.append(keynam)
                
                if not self.IsDerivedData(self.selected):
                    # add Mulliken.Q(2)-Q(1)
                    if self.prpdic.has_key('Mulliken.Q(1)') and \
                             self.prpdic.has_key('Mulliken.Q(2)'):
                        self.propertyitems.append('Mulliken.Q(2)-Q(1)')
                        self.AddMullikenQ2M1ToPrpDic()
            #
            mess='Selected file for plot='+self.selected
            self.ConsoleMessage(mess)
            #
            self.tcsel.SetValue(self.selected)
            self.propertyitems.sort()
            self.SetPropertyItems()
    
    def AddMullikenQ2M1ToPrpDic(self):
        q21=[]
        if not self.prpdic.has_key('Mulliken.Q(2)'): return
        if not self.prpdic.has_key('Mulliken.Q(1)'): return
        q2=self.prpdic['Mulliken.Q(2)']
        q1=self.prpdic['Mulliken.Q(1)']
        for i in range(len(q2)):
            if q2[i] == 'end': q21.append('end')
            else: q21.append(q2[i]-q1[i])
        self.prpdic['Mulliken.Q(2)-Q(1)']=q21
        prptyp=self.prptypdic['Mulliken.Q(2)'][0]
        self.prptypdic['Mulliken.Q(2)-Q(1)']=[prptyp,1]
        
    def MakeInfoText(self,keynam):
        dat=''
        if not self.prpdic.has_key(keynam):
            self.infotext=self.infotext+keynam+' no info availabel\n'
            return
        datlst=self.prpdic[keynam]
        for d in datlst: 
            if d == 'end': continue
            d=str(d); dat=dat+d+','
        dat=dat[:-1]
        self.infotext=self.infotext+keynam+' '+dat+'\n'
                            
    def EnableFMOButtons(self,on):
        if on:
            self.btndetail.Enable(); self.btnresult.Enable()
            self.btnviewprop.Enable(); self.cbprop.Enable()
            self.btnplt.Enable(); self.btncls.Enable()
            #self.btnpie.Enable(); self.btnctc.Enable(); self.btnmul.Enable()
            #self.btnmep.Enable(); self.btnden.Enable(); self.btnorb.Enable()
            #self.btnhomo.Enable(); self.btndos.Enable(); self.btnchgc.Enable()
        else:
            self.btndetail.Disable(); self.btnresult.Disable()
            self.btnviewprop.Disable(); self.cbprop.Disable()
            self.btnplt.Disable(); self.btncls.Disable()
            #self.btnpie.Disable(); self.btnctc.Disable(); self.btnmul.Disable()
            #self.btnmep.Disable(); self.btnden.Disable(); self.btnorb.Disable()
            #self.btnhomo.Disable(); self.btndos.Disable(); self.btnchgc.Disable()

    def EditFile(self):
        selected=self.lbdat.GetStringSelection()
        if selected == '': self.MessageSelect()
        else:
            filename=self.datadic[selected][0]
            lib.Editor(filename)

    def SavePropChoice(self,on):
        # save and recover checkbox states 
        # on: True for save, and False for recover
        if on: # save
            if self.ckbpie.GetValue(): self.pltpie=1 
            else: self.pltpie=0
            if self.ckbctc.GetValue(): self.pltctchg=1 
            else: self.pltctchg=0 
            if self.ckbmul.GetValue(): self.pltmulchg=1 
            else: self.pltmulchg=0 
            if self.ckbesp.GetValue(): self.pltespot=1 
            else: self.pltespot=0 
            if self.ckbden.GetValue(): self.pltden=1 
            else:self.pltden=0 
            if self.ckborb.GetValue(): self.pltorb=1
            else: self.pltorb=0         
        else: # recover
            if self.pltpie == 1: self.ckbpie.SetValue(True)
            else: self.ckbpie.SetValue(False)
            if self.pltctchg == 1: self.ckbctc.SetValue(True)
            else: self.ckbctc.SetValue(False)
            if self.pltmulchg == 1: self.ckbmul.SetValue(True)
            else: self.ckbmul.SetValue(False)
            if self.pltespot == 1: self.ckbesp.SetValue(True)
            else: self.ckbesp.SetValue(False)
            if self.pltden == 1: self.ckbden.SetValue(True)
            else: self.ckbden.SetValue(False)
            if self.pltorb == 1: self.ckborb.SetValue(True)
            else: self.ckborb.SetValue(False)          
    
    def PlotFragmentProperty(self,fmoprp):
        # fmoprp: 'PIE,PIEDA','CTCharge', or 'MullikenCharge'
        methnam='fuplot(PlotFragmentProperty)'
        if not self.model.mol:
            mess='Please read molecule data in "fumodel".\n'
            lib.MessageBoxOK(mess,methnam)
            return
        if not self.prpdic.has_key('Fragment.Name'):
            mess='No "Fragment.Name". Unable to plot fragment prpperty.'
            lib.MessageBoxOK(mess,methnam)
            return
        natm=len(self.model.mol.atm)
        frgnam=self.model.frag.ListFragmentName()
        nfrg=len(frgnam)
        indat=self.model.frag.ListFragmentAtoms()
        ifg=natm*[0]
        for i in range(len(indat)): 
            for j in range(len(indat[i])): ifg[indat[i][j]]=i+1
        #
        frgnamout=self.prpdic['Fragment.Name']
        try: 
            frg1=frgnamout[0]; tmpnam=[]
            tmpnam.append(frg1)
            frgnamout.remove('end')
            for i in range(1,len(frgnamout)):
                nam=frgnamout[i]
                if nam == frg1: break
                tmpnam.append(nam)
            frgnamout=tmpnam
        except: pass
        if nfrg != len(frgnamout):
        #if len(frgnam) <= 0:
            frgnam=frgnamout
            nfrg=len(frgnam)
            if nfrg <= 0:
                mess='Number of fragments is <=0. Unable to plot fragment properties.'
                lib.MessageBoxOK(mess,methnam)
                return
            try: 
                ifg=[]
                for i in self.prpdic['IFG']:
                    if  i == 'end': break
                    ifg.append(i)
            except:
                mess='No fragment data, "IFG". Unable to plot PIEDA property.'
                lib.MessageBoxOK(mess,methnam)
                return         
            try: filter(lambda a: a != 'end', ifg)                
            except: pass
            #
            if len(ifg) != natm:
                nter=self.model.mol.CountTer([])
                mess='Mol includes '+str(nter)+'" TERs". Is it OK to delte them?'
                retcode=lib.MessageBoxYesNo(mess,'fuplot(PlotFragmentProperty)')
                if not retcode: return #dlg.ShowModal() == wx.ID_NO: return
                else:
                    self.model.DeleteAllTers()
                #dlg.Destroy()
            # set fragmet data to Mol
            ###funcnam='SetFragmentToMol'
            ###self.mdlargs[funcnam]=[frgnam,ifg]
            ###self.model.SetFragmentToMol(funcnam)
            #self.model.SetFragmentToWrkMol(frgnam,ifg)
            
        if fmoprp == 'PIEDA' or fmoprp == 'PIE' or fmoprp == 'CTCharge':
            if not self.prpdic.has_key('PIEDA'):
                mess='No PIE/PIEDA data. Unable to plot PIEDA prpperty.'
                lib.MessageBoxOK(mess,methnam)
                return     
        if fmoprp == 'Mono.Energies':
            datlst=self.MakePropertyList(fmoprp)
            if len(datlst[0]) == nfrg:
                self.PlotOnMatPlotLib(fmoprp,datlst[0],'fragment')
            return
        natm=len(self.model.mol.atm)
        if len(ifg) != natm:
            mess='Number of atoms is different in Mol and that in output file. Unable to continue.'
            lib.MessageBoxOK(mess,'fuplot(PlotFragmentProperty)')
            return
        molint=self.IsDerivedData(self.selected)
        # interfragment distance
        frgdist=[]
        dat1d=self.prpdic['PIEDA']['R']
        self.pltargs['LinearToSquareArray']=dat1d
        dat2d=self.LinearToSquareArray(nfrg,[],True) #dat1d,True)
        self.pltargs['AddIndexToSquareArray']=dat2d
        
        frgdist=self.AddIndexToSquareArray(nfrg,[]) #dat2d)
        #
        err=False
        #molint=False; datnam=self.selected; piedacmp=[]; mullbody=[]
        datnam=self.selected; pieda=False; corr=False
        if fmoprp == 'CTCharge':
            if not self.prpdic['PIEDA'].has_key('Q(I->J)'):
                mess='No CTCharge data. Unable to plot.'
                lib.MessageBoxOK(mess,methnam)
                err=True
            else:
                #dat1d=self.prpdic['PIEDA']['Q(I->J)']
                #dat2d=self.LinearToSquareArray(nfrg,dat1d)
                #ctcharge=self.AddIndexToSquareArray(nfrg,dat2d)
                prpdat,valrange=self.MakeCTChargePlotData(nfrg)
                pltprp=1

        elif fmoprp == 'PIEDA':
            err,cmplst,prpdat=self.MakePIEDAPlotData(nfrg,molint)
            if err: return
            pieda=False; corr=False
            if 'Ees' in cmplst: pieda=True
            if 'Edisp' in cmplst: corr=True
            #print 'PIEDA prpdat',prpdat
            #pieda=True
            pltprp=0
        # draw graph    
        if err: 
            graphobj.Close()
            return
        #
        pos=(-1,-1); size=(660,360)
        oned=True # 1D graph: yess
        child=False # child mode: no
        pltmode=0 # 0:pieda, 1:ctcharge, 2:muliken
        graphobj=PIEDAGraph_Frm(self,-1,pos,size,oned,pltmode,child)
        #self.ctrlflag.SetCtrlFlag(name,True)
        #pieda=False; corr=False
        molint=False
        piedacmp=[0,0,0,0,0]; mullbody=[0,0,0,0]       
        if pltprp == 0 or pltprp == 1:
            if pieda: piedacmp=[1,1,1,0,0]
            if corr: piedacmp[3]=1
            if molint: piedacmp[4]=1 # one-body
        if pltprp == 2:
            if len(fmoprp[0][0]) == 3: mullbody=[1,1,0,0]
            if len(fmoprp[0][0]) == 4: mullbody=[1,1,1,1] 
        #
        graphobj.SetPIEDAProperty(pltprp,datnam,molint,piedacmp,mullbody)        
        self.pltargs['SetPIEDAData']=[frgnam,prpdat,frgdist]
        graphobj.SetPIEDAData(natm,nfrg) #,frgnam,prpdat,frgdist)
        self.graph[fmoprp]=graphobj
        self.graph[fmoprp].Show()
        if pltprp == 0:
            valrange=50.0
            if self.IsDerivedData(self.selected): valrange=5.0
            self.graph[fmoprp].SetYRange(valrange)
        elif pltprp == 1: 
            self.graph[fmoprp].SetYRange(valrange)
        else: self.graph[fmoprp].DrawGraph(True)
            
    def MakePIEDAPlotData(self,nfrg,molint):
        # make pieda for plot.
        # if molint=True, subtract component energy from those of complex
        piedadat=[]
        tokcal=627.50 # Hartree to kcal/mol, for onbody energy conversion.
        nlayer=1
        err=True
        #
        cmpnamdic={'total':'tot','Ees':'es','Eex':'ex','Ect+mix':'ct',
                   'Edisp':'di','Gsol':'sol'}        
        self.piedacmp=[False,False,False,False,False] # flag: es,ex,ctmix,di,1b
        #
        cmplst,piedadat=self.PIEDAArrayData(nfrg)
        #
        ncmp=len(cmplst)
        if ncmp <= 0:
            mess='No PIEDA components. Unable to plot.'
            lib.MessageBoxOK(mess,'fuplot(MakePIEDAPlotData')
            return err,cmplst,piedadat
        mess='PIEDA components: '
        for s in cmplst: mess=mess+s+','
        mess=mess[:-1]
        self.ConsoleMessage(mess)

        pie=False; pieda=False; corr=False; sol=False
        #if ncmp == 1: pie=True
        if 'Ees' in cmplst: pieda=True
        else: pie=True
        if 'Edisp' in cmplst: corr=True
        if 'Gsol' in cmplst: sol=True
        if not 'total' in cmplst:
            print 'cmpdic does not have "total"'
        #
        #
        return False,cmplst,piedadat
    
    
    
    
        onebody=[]
        onebody=self.prpdic['Mono.Energies']
        try: onebody.remove('end')
        except: pass
        
        pieda=copy.deepcopy(pieda)
        onebody=copy.deepcopy(onebody)
        nlen=len(pieda[0])
        nf=0
        for i in range(1,len(fmodat)):
            datnam=fmodat[i]
            tmppieda=self.fmodatadic[datnam].frgpieda
            tmpone=self.fmodatadic[datnam].onebody 
            tmpnfrg=self.fmodatadic[datnam].nfrg
            for j in range(len(tmpone)):
                onebody[j+nf][1] += cmpsign[i]*tmpone[j][1]
            for j in range(len(tmppieda)):
                if tmpnfrg == 1:
                    nf += 1; break
                for k in range(len(tmppieda[j])):
                    i0=j+nf; 
                    j0=k+nf
                    for l in range(1,len(tmppieda[j][k])):
                        pieda[i0][j0][l] += cmpsign[i]*tmppieda[j][k][l]
            nf += tmpnfrg
        for i in range(len(pieda)):
            obe=tokcal*onebody[i][1]
            for j in range(len(pieda[i])):
                if i == j: pieda[i][j].append(obe)
                else: pieda[i][j].append(0.0)
        return False,cmplst,piedadat
    
    def ReadProperties(self):
        prpdic={}; prptypdic={}
        #if not self.IsDerivedData(self.selected):        #
        if self.datadic.has_key(self.selected):
            file=self.datadic[self.selected][0]
            filternam=self.datadic[self.selected][1] # cube or program name 'gms'         
            prpdic,prptypdic=self.prpobjdic[filternam].ReadOutputFile(file)        
        elif self.drvdatadic.has_key(self.selected):
            self.drvprpinfo={}
            cmpdat=self.drvdatadic[self.selected]
            file=self.datadic[cmpdat[0][0]][0]
            filternam=self.datadic[cmpdat[0][0]][1]
            prpdic,prptypdic=self.prpobjdic[filternam].ReadOutputFile(file)
            try: 
                natm=len(prpdic['IFG'])
                self.drvprpinfo['natm']=[natm]
            except:
                pass
                #natm=len(prpdic['Mulliken.Charge'])
            try: 
                nfrg=len(prpdic['Fragment.Name'])
                self.drvprpinfo['nfrg']=[nfrg]
            except: nfrg=1
            ifrg=0; iatm=0
            for i in range(1,len(cmpdat)):
                datanam=cmpdat[i][0]
                arith=cmpdat[i][1]
                filter=self.datadic[datanam][1]
                #if filter != filternam:
                #    print 'filter is not the same as parent file',filter,filternam
                file=self.datadic[datanam][0]
                tmpprpdic,tmpprptypdic=self.prpobjdic[filternam].ReadOutputFile(file)
                try: 
                    matm=len(tmpprpdic['IFG'])
                    if 'end' in tmpprpdic['IFG']: matm -= 1
                    if self.drvprpinfo.has_key('natm'): self.drvprpinfo['natm'].append(matm)
                except: matm=0
                try: 
                    mfrg=len(tmpprpdic['Fragment.Name'])
                    if 'end' in tmpprpdic['Fragment.Name']: mfrg -= 1
                except: mfrg=1
                if self.drvprpinfo.has_key('nfrg'): self.drvprpinfo['nfrg'].append(mfrg)
                # two-body properties
                prpdic=self.DerivedPIEDAData(nfrg,ifrg,prpdic,mfrg,tmpprpdic,arith)
                # one-body energy
                prpnam='Mono.Energies'
                if prpdic.has_key(prpnam):
                    prpdic=self.DerivedOneBodyProperty(ifrg,prpdic,prpnam,mfrg,tmpprpdic,arith)
                
                ifrg += mfrg
                
                # Mulliken.Q(1)
                prpnam='Mulliken.Q(1)'
                if prpdic.has_key(prpnam):
                    prpdic=self.DerivedMullikenCharge(mfrg,iatm,prpdic,prpnam,matm,tmpprpdic,arith) 
                prpnam='Mulliken.Q(2)'
                if prpdic.has_key(prpnam):
                    prpdic=self.DerivedMullikenCharge(mfrg,iatm,prpdic,prpnam,matm,tmpprpdic,arith)
                #prpnam='Mulliken.Q(2)-Q(1)'
                #if prpdic.has_key(prpnam):
                #    prpdic=self.DerivedMullikenCharge(mfrg,iatm,prpdic,prpnam,matm,tmpprpdic,arith)
                
                iatm += matm
            # deriveddatainfo
            # natm,nfrg,Totalcharge,total charge,,Total.Energy(1),Total.Energy(1)
            ###self.infotext=self.infotext+'Total.Energy(1)'       
            # serived prpperty information
            self.MakeDerivedPropertyInfo()
        return prpdic,prptypdic

    def MakeDerivedPropertyInfo(self):
 
        # CTCharge,PIEDA:cmp,Mulliken.Q(2),Q(1)
        pass


    def DerivedPIEDAData(self,nfrg,ifrg,prpdic,mfrg,tmpprpdic,arith):
        prplst=['CTCharge','PIEDA','Mono.Energies','Mullike.Q(1)','Mulliken.Q(2)']
        # CTCharge
        if tmpprpdic.has_key('PIEDA'):
            if tmpprpdic['PIEDA'].has_key('Q(I->J)') and mfrg > 1:
                ctcharge=prpdic['PIEDA']['Q(I->J)']
                k0=(ifrg+1)*(ifrg)/2+ifrg
                #print 'initial k',k0
                k=-1 
                for i in range(1,mfrg-1):
                    for j in range(i):
                        k += 1
                        k=i*(i-1)/2+j
                        k0=(ifrg+i)*(ifrg+i-1)/2+(ifrg+j)
                        #print 'i,j,k,k0',i,j,k,k0
                        #print 'calk',i*(i-1)/2+j
                        if tmpprpdic['PIEDA']['Q(I->J)'][k] == 'end': 
                            continue
                        if arith == 'sub': ctcharge[k0] -= tmpprpdic['PIEDA']['Q(I->J)'][k]
                        else: ctcharge[k0] += tmpprpdic['PIEDA']['Q(I->J)'][k]
        # pieda data
        cmplst=['total','tot','Ees','Eex','Ect+mix','Edisp','Gsol']        
        if tmpprpdic.has_key('PIEDA') and mfrg > 1:
            for cmp in cmplst:
                if not tmpprpdic['PIEDA'].has_key(cmp): continue
                cmpdat=prpdic['PIEDA'][cmp]
                k0=(ifrg+1)*(ifrg)/2+ifrg
                k=-1
                for i in range(1,mfrg-1):
                    for j in range(i):
                        k += 1
                        k0=(ifrg+i)*(ifrg+i-1)/2+(ifrg+j)
                        if arith == 'sub': cmpdat[k0] -= tmpprpdic['PIEDA'][cmp][k]
                        else: cmpdat[k0] += tmpprpdic['PIEDA'][cmp][k]
        return prpdic
    
    def DerivedOneBodyProperty(self,ifrg,prpdic,prpnam,mfrg,tmpprpdic,arith):
        if tmpprpdic.has_key(prpnam):
            temp=tmpprpdic[prpnam]
            monop=prpdic[prpnam]
            for i in range(mfrg):
                if temp[i] == 'end': continue
                if monop[i+ifrg] == 'end': continue
                if arith == 'sub': monop[i+ifrg] -= tmpprpdic[prpnam][i]
                else: monop[i+ifrg] += tmpprpdic[prpnam][i] 
            prpdic[prpnam]=monop
        return prpdic
    
    def DerivedMullikenCharge(self,mfrg,iatm,prpdic,prpnam,matm,tmpprpdic,arith): 
        if tmpprpdic.has_key(prpnam):
            if mfrg == 1: temp=tmpprpdic['Mulliken.Q(1)']
            else: temp=tmpprpdic[prpnam]
            mchg=prpdic[prpnam]
            for i in range(matm):
                #print 'i,i+iatm',i,i+iatm
                if temp[i] == 'end': continue
                if mchg[i+iatm] == 'end': continue
                if arith == 'sub': mchg[i+iatm] -= temp[i]
                else: mchg[i+iatm] += temp[i] 
            prpdic[prpnam]=mchg
        return prpdic
    
    def PIEDAArrayData(self,nfrg):
        piedadat=[]; cmplst=[]
        skiplst=['dDIJ*VIJ','DL','Q(I->J)','I','J','R','EIJ-EI-EJ','Z']
        pickuplst=['total','tot','Ees','Eex','Ect+mix','Edisp','Gsol'] #,'total']  
        # piedadat array
        for i in range(nfrg): 
            tmp=[]
            for j in range(nfrg): tmp.append([j+1])
            piedadat.append(tmp)
        # componen data
        cmpdic={}; nmb=0
        for item,data in self.prpdic['PIEDA'].iteritems():
            if item in pickuplst:
                cmp=item
                if item == 'tot': cmp='total'
                if cmp == 'total' and 'end' in data: nmb += 1
                cmpdic[cmp]=data
        
        nd=self.CountNumberOfPIEDAData()

        for cmp,data in cmpdic.iteritems():
            self.pltargs['GetIthData']=data
            dt=self.GetIthData(nd,[]) #data)
            cmpdic[cmp]=dt
        if nd > 1:
            mess='The '+str(nd)+'-th PIEDA data out of '+str(nd)+' is plotted.'
            self.ConsoleMessage(mess)
        ndat=len(cmpdic['total'])      
        cmplst=cmpdic.keys()
        ncmp=len(cmplst)
        pieda=False
        if 'Ees' in cmplst: pieda=True
        # frag distance
        rij=self.prpdic['PIEDA']['R']
        ifrg=self.prpdic['PIEDA']['I']
        jfrg=self.prpdic['PIEDA']['J']
        #
        for i in range(1,nfrg):
            for j in range(i):
                if pieda: tmp=[0.0,0.0,0.0,0.0,0.0]
                else: tmp=[0.0]
                piedadat[i][j]=piedadat[i][j]+tmp
                piedadat[j][i]=piedadat[j][i]+tmp       
        #
        for ii in range(ndat):
            if ifrg[ii] == 'end' or jfrg[ii] == 'end': break
            i=ifrg[ii]-1; j=jfrg[ii]-1
            if rij[ii] == 0: continue
            tmp=[]
            if pieda:
                tot=cmpdic['total'][ii]
                es=cmpdic['Ees'][ii]
                ex=cmpdic['Eex'][ii]
                ct=cmpdic['Ect+mix'][ii]
                di=0.0
                if cmpdic.has_key('Edisp'): di=cmpdic['Edisp'][ii]
                tmp.append(tot); tmp.append(es)
                tmp.append(ex); tmp.append(ct); tmp.append(di)
                piedadat[i][j][1]=tot; piedadat[i][j][2]=es
                piedadat[i][j][3]=ex; piedadat[i][j][4]=ct
                piedadat[i][j][5]=di
                piedadat[j][i][1]=tot; piedadat[j][i][2]=es
                piedadat[j][i][3]=ex; piedadat[j][i][4]=ct
                piedadat[j][i][5]=di
            else:
                tot=cmpdic['total'][ii]
                #tmp.append(tot)
                piedadat[i][j][1]=tot
                piedadat[j][i][1]=tot 
        # diagonal element 
        for i in range(nfrg):
            if pieda: piedadat[i][i]=piedadat[i][i]+ncmp*[0.0]
            else: piedadat[i][i]=piedadat[i][i]+[0.0]

        return cmplst,piedadat
    
    def CountNumberOfData(self,data):
        nd=0    
        for value in data:
            if value == 'end': nd += 1
        return nd
    
    def CountNumberOfPIEDAData(self):
        nd=0    
        if not self.prpdic.has_key('PIEDA'): return nd
        tot='total'
        if not self.prpdic['PIEDA'].has_key(tot): tot='tot'
        for value in self.prpdic['PIEDA'][tot]:
            if value == 'end': nd += 1
        return nd

    def GetPltArgs(self,methnam):
        data=None
        if self.pltargs.has_key(methnam): data=self.pltargs[methnam]
        del self.pltargs[methnam]
        return data
        
    def GetIthData(self,ith,data=[]):
        data=self.GetPltArgs('GetIthData')
        
        ithdat=[]; k=1; found=False
        for value in data:
            if value == 'end': 
                k += 1
                if found and k != ith: break
                continue
            if k == ith: 
                ithdat.append(value); found=True
        return ithdat
        
    def ComputeCeilValue(self,value):
        pow=int(math.log10(value))-1
        val=math.ceil(value*10.0**(-pow))*10.0**pow
        return val
    
    def MakeCTChargePlotData(self,nfrg):
        ctcharge=[]
        dat1d=self.prpdic['PIEDA']['Q(I->J)']
        for i in range(nfrg): 
            tmp=[]
            for j in range(nfrg): tmp.append([j+1])
            ctcharge.append(tmp)
        nd=self.CountNumberOfData(dat1d)
        self.pltargs['GetIthData']=dat1d
        data=self.GetIthData(nd,[]) #dat1d)
        ndat=len(data)
        if nd > 1:
            mess='The '+str(nd)+'-th CTCharge data out of '+str(nd)+' is plotted.'
            self.ConsoleMessage(mess)

        ifrg=self.prpdic['PIEDA']['I']
        jfrg=self.prpdic['PIEDA']['J']
        for i in range(nfrg): 
            tmp=[]
            for j in range(nfrg): tmp.append([j+1])
            ctcharge.append(tmp)
        for i in range(1,nfrg):
            for j in range(i):
                ctcharge[i][j]=ctcharge[i][j]+[0.0]
                ctcharge[j][i]=ctcharge[j][i]+[0.0]             
        for ii in range(ndat):
            if ifrg[ii] == 'end' or jfrg[ii] == 'end': break
            i=ifrg[ii]-1; j=jfrg[ii]-1
            chg=data[ii]
            ctcharge[i][j][1]=chg
            ctcharge[j][i][1]=chg 
        # diagonal element 
        for i in range(nfrg):
            ctcharge[i][i]=ctcharge[i][i]+[0.0]
        maxv=max(data); minv=min(data)
        maxabs=max(abs(maxv),abs(minv))
        valrange=self.ComputeCeilValue(maxabs)
        return ctcharge,valrange

    def XXPIEDAItemArray(self,nfrg,item):
        prpdat=[]
        item=self.prpdic['PIEDA'][item]
        tmp=nfrg*[0.0]
        for i in range(nfrg): prpdat.append(tmp)
        #
        ifg=self.prpdic['PIEDA']['I']
        jfg=self.prpdic['PIEDA']['I']
        for ip in range(len(ifg)):
            if item[ip] == 'end': continue
            i=ifg[ip]-1; j=jfg[ip]-1
            prpdat[i][j]=item[ip]
            prpdat[j][i]=item[ip]
        
        print 'item',item
        #print 'prpdat',prpdat
        return prpdat
    
    def LinearToSquareArray(self,ndim,dat1d=[],symmetric=True):
        if self.pltargs.has_key('LinearToSquareArray'):
            dat1d=self.pltargs['LinearToSquareArray']
            del self.pltargs['LinearToSquareArray']
        else: pass
        dat2d=[]
        for i in range(ndim): dat2d.append(ndim*[0.0])
        k=-1
        for i in range(1,ndim):
            for j in range(i):
                k += 1
                if dat1d[k] == 'end': continue
                dat2d[i][j]=dat1d[k]
                if symmetric: dat2d[j][i]=dat1d[k]
                else: dat2d[j][i]=-dat1d[k]
        return dat2d
      
    def AddIndexToSquareArray(self,ndim,dat2d=[]):
        # add numbering
        if self.pltargs.has_key('AddIndexToSquareArray'):
            dat2d=self.pltargs['AddIndexToSquareArray']
            del self.pltargs['AddIndexToSquareArray']
        else: pass
        
        indexeddat2d=[]
        for i in range(ndim):
            tmp=[]
            for j in range(ndim):
                tmp.append([j+1,dat2d[i][j]])
            indexeddat2d.append(tmp)
        #print 'dat2d after numbering',indexeddat2d
        return indexeddat2d
        
    def OnRemoveData(self,event):     
        selected=self.lbdat.GetStringSelection()
        if self.datadic.has_key(selected): del self.datadic[selected]
        if self.drvdatadic.has_key(selected): del self.drvdatadic[selected]
        
        self.SetDataList()
        if selected == self.tcsel.GetValue(): self.tcsel.SetValue('')
        """
        for i in range(len(self.datalist)):
            if self.datalist[i] == self.selected:
                del self.datalist[i]; break
        self.lbdat.Set(self.datalist)
        self.selected=''
        self.tcrmk.Clear()
        self.XXOnPropClear(0)
        """
    def WriteRemark(self):
        if not self.tcrmk: return
        eol='\n'
        self.tcrmk.Clear()
        if self.selected != "":
            self.tcrmk.WriteText('data ... '+self.selected+eol)
        # derived data
        if self.IsDerivedData(self.selected):
            txt=''
            for cmpo in self.drvdatadic[self.selected]: 
                txt=txt+' '+cmpo
            self.tcrmk.WriteText('comp ...'+txt+eol)
            drvnam=self.drvdatadic[self.selected] 
            cmpdat,cmpsign=self.ResolveDerivedData(drvnam)
            #
            for cmpnam in cmpdat:
                id,name=self.GetIDAndName(cmpnam)
                filout=self.fmodatadic[cmpnam].outfile
                filinp=self.fmodatadic[cmpnam].inpfile
                filpdb=self.fmodatadic[cmpnam].pdbfile
                self.tcrmk.WriteText(id+': outfil ...'+filout+eol)
                self.tcrmk.WriteText(id+': inpfil ...'+filinp+eol)
                self.tcrmk.WriteText(id+': pdbfil ...'+filpdb+eol)
        # original fmo data
        if self.IsFMOProperty(self.selected):
            txt=self.fmodatadic[self.selected].outfile
            self.tcrmk.WriteText('outfile ...'+txt+eol)           
            txt=self.fmodatadic[self.selected].inpfile
            self.tcrmk.WriteText('inpfile ...'+txt+eol)           
            txt=self.fmodatadic[self.selected].pdbfile
            self.tcrmk.WriteText('pdbfile ...'+txt+eol)           
    
            txt=str(self.fmodatadic[self.selected].nfrg)
            self.tcrmk.WriteText('nfrg ...'+txt+eol)       
            txt=str(self.fmodatadic[self.selected].natm)
            self.tcrmk.WriteText('natm ...'+txt+eol)       
            txt=str(self.fmodatadic[self.selected].nbas)
            self.tcrmk.WriteText('nbas ...'+txt+eol)       
            txt=str(self.fmodatadic[self.selected].tchg)
            self.tcrmk.WriteText('tchg ...'+txt+eol)       

        self.tcrmk.ShowPosition(0)

    def ResolveDerivedData(self,drvnam):
        #
        fmodat=[]; cmpsign=[]
        for cmpnam in drvnam:    
            id,name=self.GetIDAndName(cmpnam)
            idsgn=1
            if cmpnam[0:1] == '-': idsgn=-1
            datnam=self.GetFMOPropName(self.fmodatadic,id)
            #
            if self.fmodatadic.has_key(datnam):
                fmodat.append(datnam)
                cmpsign.append(idsgn)
            else: 
                idv,namev=self.GetIDAndName(cmpnam)
                drvnamv=self.GetFMOPropName(self.drvdatadic,idv)
                if drvnamv == '': continue
                cmpv=self.drvdatadic[drvnamv]
                #
                for cmpnamv in cmpv:
                    idd,named=self.GetIDAndName(cmpnamv)
                    iddsgn=1
                    if cmpnamv[0:1] == '-': iddsgn=-1
                    datnamd=self.GetFMOPropName(self.fmodatadic,idd)
                    if self.fmodatadic.has_key(datnamd):
                        fmodat.append(datnamd)
                        cmpsign.append(idsgn*iddsgn)
                    else:
                        fmodat=[]; cmpsign=[]
                        dlg=lib.MessageBoxOK("Failed to find components. "+cmpnam,"")
                    
        return fmodat,cmpsign
    
    def GetFMOProp(self,dataname):
        fmodat=None
        if self.fmodatadic.has_key(dataname): fmodat=self.fmodatadic[dataname]
        return fmodat
                
    def GetFMOPropName(self,fmodatadic,id):
        dataname=''
        lst=fmodatadic.keys()
        for name in lst:
            ns=name.find(':')
            iddat=name[:ns]
            if iddat == id:
                dataname=name; break
        return dataname

    def OnDerivedPorpPanel(self,event):
        #if self.opendrvpan: self.drvpanprp.Destroy()
        try: self.drvprppan.Destroy()
        except: pass
        onoff=self.btndrvprp.GetValue()
        if onoff:
            pos=self.GetPosition()
            size=self.GetSize()
            drvpanpos=[pos[0]+size[0]/2,pos[1]+size[1]-20]
            drvpansize=[size[0]/2,95]
            #
            self.opendrvprppan=True
            com="Input, e.g. Delta.Q=8-7, where 8,7 are property numbers."
            winlabel='Derived property'
            #[posx,posy]=self.GetPosition(); [wsize,hsize]=self.GetSize()
            #self.drvpanprppos=[posx+wsize-100,posy+hsize-40]
            self.drvprppan=subwin.TextInput_Frm(self,-1,drvpanpos,drvpansize,
                                             winlabel,com,self.DerivedPropText)
            self.drvprppan.Show()
        else:
            try: self.drvprppan.Destroy()
            except: pass
        
    def OnDerivedDataPanel(self,event):
        #
        #if self.opendrvpan: self.drvpandat.Destroy()
        if len(self.datadic) <= 0: return
        try: self.drvdatpan.Destroy()
        except: pass
        onoff=self.btndrvdat.GetValue()
        if onoff:
            pos=self.GetPosition()
            size=self.GetSize()
            drvpanpos=[pos[0],pos[1]+size[1]-20]
            drvpansize=[size[0]/2,95]
            #
            self.opendrvdatpan=True
            com="Input, e.g. dataname=3-1-2, where 3,1,2 are data numbers."
            winlabel='Derived data'
            #[posx,posy]=self.GetPosition(); [wsize,hsize]=self.GetSize()
            #self.drvpandatpos=[posx+wsize-100,posy+hsize-40]
            self.drvdatpan=subwin.TextInput_Frm(self,-1,drvpanpos,drvpansize,
                                             winlabel,com,self.DerivedDataText)
            self.drvdatpan.Show()
        else:
            try: self.drvdatpan.Destroy()
            except: pass
            
    def OpenPlotOrbitalEnergyWin(self):
        print 'OpenDrawOrbitalWin'
        
        #self.orbwin=cube.DrawOrbital_Frm(self.mdlwin,-1,winpos,winsize,self.model,self,mode) # mode=1
        model=1
    
        orbitallst=[[-20,-10,0,10,20],[-25,-15,0,10,15,25]]
        
        
        self.orbengobj=PlotOrbitalEnergy(self,orbitallst)
        #self.orbengobj.OpenDrawWin()
       
    def OpenDrawOrbitalWin(self):
        print 'OpenDrawOrbitalWin'
        
        #self.orbwin=cube.DrawOrbital_Frm(self.mdlwin,-1,winpos,winsize,self.model,self,mode) # mode=1
        model=1
        self.orbobj=cube.DrawOrbital(self,model,None)
        orbitallst=[['orbital1',[-20,-10,0,10,20]],['orbital2',[-25,-15,0,10,15,25]] ]
        
        #orbitallst=[]
        self.orbobj.OpenDrawWin(orbitallst=orbitallst)
        #self.orbwin=cube.DrawOrbital_Frm(self,-1,self.model,self) # mode=1        

    def GetDataFromUserInput(self,inputtext):    
        #drvtxt=inputtext
        drvcmp=[]
        nc=inputtext.find('=')
        if nc <= 0:
            lib.MessageBoxOK("No name. Try again. %s" % inputtext,"")
            return
        drvnam=inputtext[:nc]
        cmptxt=inputtext[nc+1:]
        #
        cat=False
        nc=cmptxt.find('cat all')
        if nc >= 0: 
            print 'cat all'
            # make drvcmp list
            cat=True
        nc=cmptxt.find('cat selected')
        if nc >= 0:
            print 'cat selected'
            cat=True
            # make drvcmp lst
        if not cat:
            txt=''
            if cmptxt[0] != '-' or cmptxt != '+': cmptxt='+'+cmptxt
            #
            for i in range(len(cmptxt)):
                    
                s=cmptxt[i]
                if s == ' ':continue
                if s == '-' or s == '+':
                    txt=txt+' '+s
                else: txt=txt+s
            #
            cmpo=txt.split(' ')
            for sc in cmpo:
                if sc == '': continue
                sc.strip()        
                drvcmp.append(sc)
            #
            if len(drvcmp) <= 0:
                lib.MessageBoxOK("No components. Try again. %s" % inputtext,"")        
            # check data
            for s in drvcmp:
                try: s=int(s)
                except:
                    lib.MessageBoxOK("Wrong input. %s" % inputtext,"")
                    
                    #drvtxt=''; 
                    drvnam=''; drvcmp=[]
                    break
        # 
        return drvnam,drvcmp
        
    def DerivedDataText(self,winlabel,inputtext):
        inputtext=inputtext.strip()
        if len(inputtext) <= 0: return
        
        drvnam,drvcmp=self.GetDataFromUserInput(inputtext)
        if len(drvnam) <= 0 or len(drvcmp) <= 0: return
        self.AddDerivedDataToDic(drvnam,drvcmp)
    
    def OnPropRightClick(self,event):
        #print 'PropLC Rihjt Clicked'
        return
        # remove selected item    
    def OnDataRightClick(self,event):
        return

        print 'data right clicked'
        #item,flags=self.lbdat.HitTest(event.GetPosition())
        #if flags == wx.NOT_FOUND:
        #    event.Skip()
        #    return
        items=self.lbdat.GetSelections()
        print 'items',items
                    
    def DerivedPropText(self,winlabel,inputtext):
        inputtext=inputtext.strip()
        if len(inputtext) <= 0: return
        
        drvnam,drvcmp=self.GetDataFromUserInput(inputtext)
        if len(drvnam) <= 0 or len(drvcmp) <= 0: return

        print 'drvnam,drvcmp',drvnam,drvcmp
        self.AddDerivedPropToDic(drvnam,drvcmp)
                
    def AddDerivedDataToDic(self,drvnam,drvcmp):

        if drvnam == '': return
        drvnam.strip()
        dup=self.IsDuplicateName(1,drvnam)
        if dup: return
        #find=self.CheckDeriveComp(drvcmp)
        #if not find: return
        drvnam=self.MakeDataName(drvnam)
        if not self.drvdatadic.has_key(drvnam): self.drvdatadic[drvnam]=[]
        for i in range(len(drvcmp)):
            dataid=int(drvcmp[i])
            if dataid > 0: arith='add'
            else: arith='sub'
            dataid=abs(dataid)
            datanam=self.GetDataNameById(dataid)
            if datanam == '': continue
            self.drvdatadic[drvnam].append([datanam,arith])
        #
        lst=self.drvdatadic.keys()
        for drvnam in lst:
            if len(self.drvdatadic[drvnam]) <= 0: del self.drvdatadic[drvnam]
        if len(self.drvdatadic) < 0: return
        #
        self.SetDataListInSelLB()
        self.lbdat.SetStringSelection(drvnam)
        #self.OnSelectData(0)

    def AddDerivedPropToDic(self,drvnam,drvcmp):

        if drvnam == '' or len(drvcmp) <= 0: return
        prpnam=drvnam.strip()
        #dup=self.IsDuplicateName(1,drvnam)
        #if dup: return
        #find=self.CheckDeriveComp(drvcmp)
        #if not find: return
        #
        self.drvprpdic[prpnam]=drvcmp
        prptyp=self.prptypdic[drvcmp[0][0]]
        self.prptypdic[prpnam]=[prptyp,1]
        #
        #self.SetDataListInSelLB()
        self.propertyitems.append(prpnam)
        self.SetPropertyItems()
        #self.lcprp.SetStringSelection(prpnam)
        #self.OnSelectData(0)

    def IsDerivedData(self,dataname):
        if self.drvdatadic.has_key(dataname): return True
        else: return False

    def CheckDeriveComp(self,drvcmp):
        find=False
        for cmpo in drvcmp:
            find=self.IsItemInDataDic(cmpo,self.datadic)
            #
            if not find:
                find=self.IsItemInDataDic(cmpo,self.drvdatadic)
            if not find:
                dlg=lib.MessageBoxOK("No component data. "+cmpo,"fuplot(CheckDerivedComp")
        return find
    
    def IsItemInDataDic(self,item,datadic):
        ret=False
        idc,namec=self.GetIDAndName(item)
        lst=datadic.keys()
        for datnam in lst:
            id,name=self.GetIDAndName(datnam)
            print 'idc,id,name',idc,id,name
            if idc == id:
                ret=True; break
        print 'item,datadic',item,datadic

        return ret

    def GetDataNameById(self,dataid):
        """ dataid(positive int) """
        name=''
        for name,datlst in self.datadic.iteritems():
            items=name.split(':',1)
            id=int(items[0].strip())
            if id == dataid:break
        return name    
        
    def GetIDAndName(self,dataname):
        ns=dataname.find(':')
        if ns < 0:
            id=dataname; name=''
        else:
            id=dataname[:ns]; name=dataname[ns+1:]
        if id[0:1] == '+' or id[0:1] == '-':
            id=id[1:]
        return id,name
    
    def MakeDataName(self,name):
        self.idmax += 1
        dataname=str(self.idmax)+':'+name
        return dataname
        
    def IsDuplicateName(self,dset,name):
        # dset=0 for self.self.fmodatadic, =1: for self.drvdatadic
        dup=False

        if len(self.drvdatadic) <= 0: return
        #    
        if dset == 1: lst=self.drvdatadic.keys()
        else: lst=self.fmodatadic.keys()
        #
        for dataname in lst:
            id,nam=self.GetIDAndName(dataname)
            if nam == name:
                dlg=lib.MessageBoxOK("Duplicate name="+name+". Neglected.","")
                dup=True; break
        return dup

    def GetOpenFiles(self,curdir,files):
        # get current directory and file names from an instance of OpenMultipleFile_Frm class 
        self.curdir=curdir
        # write current directory on inifile
        funame=self.inifile
        funame=os.path.join(self.exedir,funame)

        lib.WriteDirectoryOnFile(curdir,funame)
        self.fmodatadic=self.MakeFMOPropertyDic(curdir,files)

        self.datalist=self.MakeDataList()
        # show names in select data panel
        self.lbdat.Set(self.datalist)
        if len(self.datalist) > 0:
            # select the first name
            self.lbdat.SetSelection(0)
            self.OnSelectData(0)
                
    def SetDataListInSelLB(self):
        self.datalist=self.MakeDataList()    
        self.lbdat.Set(self.datalist)
                    
    def MakeDataList(self):
        datalist=self.datadic.keys()
        if len(self.drvdatadic) > 0:
            drvlist=self.drvdatadic.keys()
            datalist=datalist+drvlist
        datalist.sort()
        #
        return datalist
    
    def GetNameAndExt(self,filename):
        err=True
        #name=''; ext=''
        ext=os.path.splitext(filename)[1]
        name=os.path.splitext(filename)[0]
        if len(ext) <= 0:
            retcode=lib.MessageBoxYesNo('Wrong file name, missing extention. '+filename+". Quit?","")
            if retcode: #wx.YES:
                return err,name,ext       
        err=False

        return err,name,ext
        
    def MenuItems(self):
        # Menu items
        menubar=wx.MenuBar()
        submenu=wx.Menu()
        # Open
        subsubmenu=wx.Menu()
        #subsubmenu.Append(-1,"GAMESS output","GAMESS output file")
        #subsubmenu.Append(-1,"Cube file","Cube file")
        #submenu.AppendSubMenu(subsubmenu,'Open')
        submenu.Append(-1,'Open output file',
                       'Open output files (multiple files can be opened.)')
        submenu.AppendSeparator()
        submenu.Append(-1,'Open cube file','Open cube file')
        submenu.AppendSeparator()
        submenu.Append(-1,'Open filter file','Open filter file')
        # List prpdic
        submenu.AppendSeparator()
        submenu.Append(-1,'List properties','List properties on console window')
        # Quit
        submenu.AppendSeparator()
        submenu.Append(-1,'Quit','Close the window')
        menubar.Append(submenu,'File')
        # Edit
        submenu=wx.Menu()
        submenu.Append(-1,'View file','View file')
        menubar.Append(submenu,'View')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'About','About')
        submenu.AppendSeparator()
        submenu.Append(-1,'Help','Help')
        menubar.Append(submenu,'Help')
        """
        # Add-on
        if len(self.addonmenu) > 0:
            topname=self.addonmenu[0]
            itemlst=self.addonmenu[1]
            for name,tip,checkable in itemlst:
                submenu=wx.Menu()
                submenu.Append(-1,name,tip)
            menubar.Append(submenu,topname)
        """
        return menubar
 
    def OpenDropFiles(self,filenames):
        if len(filenames) <= 0: return
        extlst=['.out','.log','.mep','.den','.cub','.cube']
        filelst=lib.ExpandFilesInDirectory(filenames,extlst)
        #
        for file in filelst:
            base,ext=os.path.splitext(file)
            if ext == '.out' or ext == '.log': case="Open output file"
            elif ext == '.mep' or ext == '.den' or ext == '.cub' or ext == '.cube':
                case='Open cube file'
            #
            self.MakeDataDic([file],case)
            self.SetDataList()
   
    def OpenFiles(self,case):
        # get default name
        name=self.model.setctrl.GetParam('defaultfilename')
        self.model.setctrl.SetParam('defaultfilename','')
        
        if case == "Open output file":
            wcard='Output file(*.out;*.log)|*.out;*.log|All(*.*)|*.*'
        elif case == 'Open cube file':
            wcard='Cube file(*.mep;*.den;*.cub)|*.mep;*.den;*.cub|All(*.*)|*.*'
        
        files=lib.GetFileNames(None,wcard,'r',True,defaultname=name)
        #
        self.MakeDataDic(files,case)
        self.SetDataList()

    
    def OpenFilterFile(self):
        filterfile=''
        self.filterfiledir=self.model.setctrl.GetDir('Filters')
        if os.path.isdir(self.filterfiledir): 
            curdir=os.getcwd()
            os.chdir(self.filterfiledir)
        wcard='filter file(*.filter)|*.filter|all(*,*)|*.*'
        filterfile=lib.GetFileName(self,wcard,'r',False,'',
                message="Open filter file") #,wildcard=wcard,
        os.chdir(curdir)
        if filterfile == '': return''
        if not os.path.exists(filterfile): 
            mess='file not found. filename='+filterfile
            self.ConsoleMessage(mess)        
        return filterfile

    def MakeDataDicOfOutputFiles(self,files,filterfile):
        # alternate of self.MakeDataDic(files,case)
        self.filterfile=filterfile
        if len(files) <= 0: return
        if not self.addmode: 
            self.datadic={}; self.idmax=0
        nmblst=[]; namedic={}
        for name,file in self.datadic.iteritems():
            items=name.split(':')
            nmblst.append(int(items[0]))
            namedic[items[1]]=file
        try: nmb=max(nmblst)
        except: nmb=0
        for fil in files:
            head,tail=os.path.split(fil)
            if namedic.has_key(tail):
                if namedic[tail][0] == fil: continue
            self.idmax += 1; name=str(self.idmax)+':'+tail
            base,ext=os.path.splitext(fil)
            #if case == "Open output file":
            if ext == '.out':
                #self.filterfile=self.GetFilterFile()
                self.filternam,ext=os.path.splitext(self.filterfile)
                self.prpobjdic[self.filternam]=FileReader(self.model,self.filternam,self.filterfile,self) 
                self.datadic[name]=[fil,self.filternam]
                mess='read file='+fil
                self.ConsoleMessage(mess)
                mess='filter file='+self.filterfile
                self.ConsoleMessage(mess)
            #elif case == 'Open cube file':
            else:
                self.datadic[name]=[fil,'cube']
        #
        self.SetDataList()
        
        
    def MakeDataDic(self,files,case):
        if len(files) <= 0: return
        if not self.addmode: 
            self.datadic={}; self.idmax=0
        nmblst=[]; namedic={}
        for name,file in self.datadic.iteritems():
            items=name.split(':')
            nmblst.append(int(items[0]))
            namedic[items[1]]=file
        try: nmb=max(nmblst)
        except: nmb=0
        for fil in files:
            head,tail=os.path.split(fil)
            if namedic.has_key(tail):
                if namedic[tail][0] == fil: continue
            self.idmax += 1; name=str(self.idmax)+':'+tail
            if case == "Open output file":
                self.filterfile=self.GetFilterFile()
                self.filternam,ext=os.path.splitext(self.filterfile)
                self.prpobjdic[self.filternam]=FileReader(self.model,self.filternam,self.filterfile,self) 
                self.datadic[name]=[fil,self.filternam]
                mess='read file='+fil
                self.ConsoleMessage(mess)
                mess='filter file='+self.filterfile
                self.ConsoleMessage(mess)
            elif case == 'Open cube file':
                self.datadic[name]=[fil,'cube']

    def GetFilterFile(self):
        # read property definition file    . xxx-gms.out    
        # get default
        try: 
            filterfile=self.model.setctrl.GetParam('output-filter')
        except: pass
        # previous filter
        if self.filterfile != '': filterfile=self.filterfile
        #
        if not os.path.exists(filterfile): #return filterdesc,filterfile
            mess='Open filter file for the output file.'
            filterfile=self.OpenFilterFile()
        else:
            mess='Is it OK to apply filter file='+filterfile+'?'
            retcode=lib.MessageBoxYesNo(mess,'fuplot(MakeDataDic')
            if not retcode:
            #if dlg.ShowModal() == wx.ID_NO: 
                filterfile=self.OpenFilterFile()
            #dlg.Destroy()
        return filterfile

    def XXBaseNameInFileName(self,filename):
        """ should replace with lib.BaseNameInFileName """
        head,tail=os.path.split(filename)
        base,ext=os.path.splitext(tail)
        return base
    
    def SetDataList(self):
        lst=[]
        for name,fil in self.datadic.iteritems(): lst.append(name)
        """ not completed for derived property """
        self.drvprplst=self.drvdatadic.keys()
        #filternam=self.datadic[self.selected][1]
        #self.drvprplst=self.prpobjdic[filternam].GetDerivedPropertyName()            
    
        if len(self.drvprplst) > 0: lst=lst+self.drvprplst
        self.lbdat.Set(lst)
        self.lbdat.SetSelection(len(lst)-1)

    def ListPropertyDic(self):
        mess='Properties in '+self.selected+':'
        self.ConsoleMessage(mess)
        print self.prpdic
        
    def AboutMessage(self):
        """ Open 'About' message box
        
        :param str title: title
        :note: icon file 'fumodel.png' should be in FUPATH/Icons directory.
        """
        #iconfile=self.setctrl.GetFile('Icons','fumodel.png')
        title='fuplot in FU ver.'
        lib.About(title,const.FUPLOTLOGO)
        
    def HelpMessage(self):
        mess='Filter files for GAMESS(gamess.filter and gamess-fmo.filter) are in FUDATASET/Filters/'
        lib.MessageBoxOK(mess,'fuplot help message')
        
    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        # File menu items
        if item == "Open output file": self.OpenFiles(item)
        elif item == "Open cube file": self.OpenFiles(item)
        elif item == "Open filter file": self.OpenFilterFile()
        elif item == "Save bitmap":
            print 'save bitmap on file'
        
        elif item == "*Print bitmap":
            self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
            dc=wx.BufferedDC(None,self.buffer)
            dc.Clear() 
        elif item == "Quit":
            self.OnClose(0)
        elif item == 'List properties':
            self.ListPropertyDic()
        #Edit
        elif item == 'View file': self.EditFile()
        # help
        elif item == 'About':
            self.AboutMessage()
        
        elif item == 'Help':
            self.HelpMessage()        
        # plot menu items
        elif item == "PIE/PIEDA":
            self.ckbpie.SetValue(True)
            self.ckbctc.SetValue(False)
            self.ckbmul.SetValue(False)
            self.OnPlot(0)
        elif item == "CT charge":
            self.ckbpie.SetValue(False)
            self.ckbctc.SetValue(True)
            self.ckbmul.SetValue(False)
            self.OnPlot(0)
        elif item == "Mulliken charge":
            self.ckbpie.SetValue(False)
            self.ckbctc.SetValue(False)
            self.ckbmul.SetValue(True)
            self.OnPlot(0) 
        # window menu items
        elif item == "PyCrust":
            self.OpenPyCrustFrame()
        elif item == "MatPlotLib":
            self.OpenMatPlotLibFrame()
        elif item == 'About': lib.About('FMOviewer')
        # add-on
        else:
            print 'addon item',item
            bChecked=False
            if item.find('.py') > 0: 
                self.model.ExecuteAddOnScript(item,bChecked)
    
    def RunMethod(self,method):
        self.pycrust.shell.run(method)

    def Message(self):
        self.text='test message'
        print 'message: ',self.text

    def ConsoleMessage(self,mess):
        mess='(fup)'+mess
        self.model.ConsoleMessage(mess)
    
    def PrintMessage(self):
        print self.consolemessage

    def OnClosePyCrust(self,event):
        self.ctrlflag.Set('pycrustwin',False)
        self.pycrust.Destroy()
        
    def OpenPyCrustFrame(self):
        if self.ctrlflag.GetCtrlFlag('pycrustwin'):
            self.pycrust.SetFocus(); return
        
        parentpos=self.GetPosition()
        parentsize=self.GetClientSize()
        winpos=[parentpos[0],parentpos[1]+parentsize[1]+50]
        winsize=lib.WinSize((600,250)); title='PyCrust in FMOViewer'
        self.pycrust=wx.py.crust.CrustFrame(parent=self,pos=winpos,size=winsize,title=title)

        self.pycrust.Bind(wx.EVT_CLOSE,self.OnClosePyCrust)
        self.pycrust.Show()
        self.ctrlflag.Set('pycrustwin',True)

    def OpenMatPlotLibFrame(self):
        if self.ctrlflag.GetCtrlFlag('matplotlibwin'):
            self.mpl.SetFocus(); return
        parentpos=self.GetPosition()
        parentsize=self.GetClientSize()
        winpos=[parentpos[0],parentpos[1]+parentsize[1]+50]
        winsize=lib.WinSize((600,450))
        winlabel='matplotlibwin'
        self.mpl=fupanel.MatPlotLib_Frm(self,-1,self.model,winpos,winsize,winlabel)
        self.mpl.Show()
        self.ctrlflag.Set('matplotlibwin',True)

    def OnFocus(self,event):
        self.SetFocus()
        
    def OnPaint(self,event):
        'print onpaint'        
        event.Skip()

    def OnResize(self,event):
        selected=self.tcsel.GetValue()
        # destroy panels
        self.panel.Destroy()
        self.prppan.Destroy()
        # set window size
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])
        # create panels
        self.CreateSelectDataPanel()
        self.CreatePropertyPanel()
        # set data
        self.tcsel.SetValue(selected)   
        self.SetDataList()
        
        return
                
        self.SavePropChoice(False)
        if self.opendrvdatpan: self.OnDerivedDataPanel(0)
        if self.opendrvprppan: self.OnDerivedPropPanel(0)


    def OnClose(self,event):
        try: self.mdlwin.SetTitle(self.mdlwintitle)
        except: pass    
        try: self.cubewin.Close(1)
        except: pass
        try: # close remarkwin in mdlwin
            for fmoprp,graphobj in self.graph.iteritems():
                if graphobj.openremarkwin: graphobj.MolView(False)
        except: pass
        try: self.Destroy()
        except: pass
        try: self.editor.Destroy()
        except: pass
         
class FileReader(object):
    def __init__(self,parent,name,filterfile,fuplot): #,outfil,inpfil,pdbfil):
        # outfil:FMO output file name
        self.model=parent
        self.fuplot=fuplot
        self.name=name
        #
        self.filterfile=filterfile
        self.constdic={}
        self.prpdefdic={}
        self.vardic={}
        #
        self.constdic,self.prpdefdic,self.vardic,self.drvprpdic= \
                 self.ReadFilterFile(self.filterfile)
       
    def ReadFilterFile(self,filterfile):
        """
        :return dic prpdefdic: {0: {'everylines': [2], 'prptype': ['bar', 'bar'], 'datatype': ['float', 'float'],
        'getitems': [[4, 6], ['MULL.CHARGE', 'LOW.CHARGE'], [' ', ' ', ' ', ' ', ' ']],
        'skiplines': 1, 'endstring': [1, ''], 
        'beginstring': [11, 'TOTAL MULLIKEN AND LOWDIN ATOMIC POPULATIONS']}, 
        1: {,,,},...}
        
        for filterfile,see 'c://fumodel0.2//Programs//gamess//outputprp//gamess.prp'
        """
        prpdefdic={}; constdic={}; vardic={}; drvprpdic={}
        #keystrlst=['$const','priorstring','beginstring','skiplines','getitems','datatype','prptype','endstring']
        
        defno=-1; varno=-1; varnam=''
        f=open(filterfile,'r')
        #
        for s in f.readlines():
            if s[:1] == '#': continue
            nc=s.find('#',1)
            if nc >= 0: s=s[:nc]
            s=s.strip()
            if s[:1] == '$':
                items=s.split('=',1)
                if len(items) < 2: continue
                var=items[0].strip()
                value=float(items[1])
                constdic[var]=value
                continue
            if s[:4] == 'prp ':
                defno += 1
                prpdefdic[defno]={}
                ss=s[4:]
                items=ss.split(',')
                items=self.StripStringList(items) 
                prpdefdic[defno]['property']=items
                continue
            if s[:4] == 'var ': # float constant
                ss=s[4:]; items=ss.split(' ',1); 
                varnam=items[0].strip()
                continue 
            if s[:4] == 'drv ': # derived prpperty. currently '-' or '+' is supported
                ss=s[4:]; items=ss.split('=',1); 
                if items[1].find('-') >= 0: arith='-'
                elif items[1].find('+') >= 0: arith='+'
                else: continue
                vars=items[1].split(arith,1)
                if len(vars) < 2: continue
                var1=vars[0]; var2=vars[1]
                drvprpdic[items[0].strip()]=[var1,var2,arith]
                continue 
            if s.find('varstring') >= 0:
                items=s.split('=',1)
                if len(items) < 2: continue
                keystr=items[0].strip()
                keywrd,colmn=self.GetKeywrdAndColmn(keystr)
                item=items[1][1:]; item=item[:-1]
                vardic[varnam]=[colmn,item]
                continue

            if s.find('beginstring') >= 0 or s.find('endstring') >= 0 \
                   or s.find('searchonstring') >= 0 or s.find('searchoffstring') >= 0:
                items=s.split('=',1)
                if len(items) < 2: continue
                keystr=items[0].strip()
                keywrd,colmn=self.GetKeywrdAndColmn(keystr)
                if keywrd == '': continue
                value=items[1][1:].rstrip()
                value=value[:-1]
                if value == 'blank': value=''
                prpdefdic[defno][keywrd]=[colmn,value]
                continue
            if s.find('skiplines') >= 0 or s.find('everylines') >= 0:
                items=s.split('=')
                keywrd=items[0].strip()
                value=int(items[1].strip())
                prpdefdic[defno][keywrd]=value
                continue
            if s.find('datatyp') >= 0 or s.find('plottype') >= 0:
                items=s.split('=')
                keywrd=items[0].strip()
                values=items[1].split(',')
                values=self.StripStringList(values)
                values=self.ExpandData(values)
                prpdefdic[defno][keywrd]=values    
                continue
            if s.find('getitems') >= 0:
                items=s.split('=',1)
                keywrd=items[0].strip()
                forsep=items[1].split('for')
                varvalsep=forsep[0].strip()
                varsep=forsep[1].strip()
                if varvalsep == 'all':
                    itemnmb=[-1]; seps=[' ']; vars=varsep.split(' ')[0]
                else:
                    itemnmb=self.StripStringList(varvalsep.split(','))
                    itemnmb=self.StringsToIntegers(itemnmb)
                    varsep=varsep.split('sep=')
                    vars=varsep[0].strip().split(',')
                    vars=self.StripStringList(vars)
                    seplst=varsep[1].split(',')
                    seplst=self.StripStringList(seplst)
                    seps=self.ExpandData(seplst)
                prpdefdic[defno][keywrd]=[itemnmb,vars,seps]    
                continue
            if s.find('priorstring') >= 0:
                items=s.split('=')
                keywrd,colmn=self.GetKeywrdAndColmn(items[0])
                value=items[1].strip()
                if value[:1] == "'": value=value[1:]
                if value[-1] == "'": value=value[:-1]   
                value=value.strip()           
                prpdefdic[defno][keywrd]=[colmn,value]  
                    
        f.close()
        return constdic,prpdefdic,vardic,drvprpdic

    def GetKeywrdAndColmn(self,keystr):
        varcolmn=keystr.split('[')
        if len(varcolmn) < 2:
            print 'format error: ',keystr
            return '',0 
        #var=varcolmn[0].strip()
        keywrd=varcolmn[0].strip()
        colmn=varcolmn[1][:-1].strip()
        colmn=int(colmn)
        return keywrd,colmn
    
    def StripStringList(self,strlst):
        lst=[]
        for st in strlst:
            st=st.strip()
            if st[:1] == "'": st=st[1:]
            if st[-1] == "'": st=st[:-1]
            st.strip()
            lst.append(st.strip())
        return strlst 
    
    def StringsToIntegers(self,strlst):
        intlst=[]
        for st in strlst:
            if st[:1] == "'": st=st[1:]
            if st[-1] == "'": st=st[:-1]
            intlst.append(int(st.strip()))
        return intlst

    def ExpandData(self,strlst):
        valuelst=[]
        for st in strlst:
            nc=st.find('*')
            if nc >= 0:
                items=st.split('*')
                if items[0].isdigit():
                    rep=int(items[0].strip())
                    value=items[1].strip()
                    if value[:1] == "'": value=value[1:]
                    if value[-1] == "'": value=value[:-1]
                    tmplst=rep*[value] 
                    valuelst=valuelst+tmplst
                else: 
                    if st[:1] == "'": st=st[1:]
                    if st[-1] == "'": st=st[:-1]
                    valuelst.append(st.strip())
            else: 
                st=st.strip()
                if st[:1] == "'": st=st[1:]
                if st[-1] == "'": st=st[:-1]
                valuelst.append(st)
        return valuelst

    def ReadVarNamList(self,filename,colmn,varstring):
        varnamlst=[]
        n=colmn+len(varstring)+1
        f=open(filename,'r')
        for s in f.readlines():
            if s.startswith(varstring,colmn-1,n):
                s=s.rstrip()
                varnamlst=lib.SplitStringAtSpaces(s)
        return varnamlst
                    
    def ReadOutputFile(self,filename): #,constdic,prpdefdic):
        constdic=self.constdic; prpdefdic=self.prpdefdic; vardic=self.vardic
        prplabeldic={}; prptypdic={}; varnamdic={}
        orbs={}
        #
        for varnam, items in vardic.iteritems():
            colmn=items[0]
            varstring=items[1]
            varnamlst=self.ReadVarNamList(filename,colmn,varstring)
            varnamdic[varnam]=varnamlst
        #
        loop=True
        idat=-1
        while loop:
            idat += 1; nam=''
            if not prpdefdic.has_key(idat): break
            if len(prpdefdic[idat]['getitems'][0]) <= 0: continue
            if prpdefdic[idat]['getitems'][0][0] == -1:
                nam=prpdefdic[idat]['getitems'][1]
                if varnamdic.has_key(nam): namlst=varnamdic[nam]
                else: continue
                prpdefdic[idat]['getitems'][1]=namlst
                sep=prpdefdic[idat]['getitems'][2][0]
                prpdefdic[idat]['getitems'][2]=len(namlst)*[sep]
                nmblst=range(len(namlst))
                for i in range(len(nmblst)): nmblst[i] += 1
                prpdefdic[idat]['getitems'][0]=nmblst
            # special code for readingorbitals
            if nam == 'Orbitals': 
                if not prpdefdic[idat].has_key('beginstring'): continue
                beginstring=prpdefdic[idat]['beginstring']
                skiplines=2
                if prpdefdic.has_key('skiplines'): skiplines=prpdefdic['skiplines']
                orbsetdic=self.ReadOrbitals(filename,beginstring,skiplines)
                if len(orbsetdic) > 0:
                    prplabel=prpdefdic[idat]['property']
                    print 'prplabel for orbs',prplabel[0]
                    prplabeldic[prplabel[0]]=orbsetdic
                    nmb=1; typ=prpdefdic[idat]['plottype'][0]
                    prptypdic[prplabel[0]]=[typ,nmb]
            else:
                prpdic=self.ReadPropertyInOutput(filename,prpdefdic[idat],constdic)
                #
                if len(prpdic) > 0:
                    prplabel=prpdefdic[idat]['property']
                    plttyp=prpdefdic[idat]['plottype']
                    pltitem=prpdefdic[idat]['getitems']
        
                    if len(prplabel) == 1:
                        item=pltitem[1][0]
                        typ=plttyp[0]
                        if typ == 'coord' or typ == 'pie' or typ == 'multi': 
                            prplabeldic[prplabel[0]]=prpdic
                        else: prplabeldic[prplabel[0]]=prpdic[item]
                        
                        nmb=self.CountNumberOfData(prplabel[0],typ,prplabeldic)
                        prptypdic[prplabel[0]]=[plttyp[0],nmb]
                    else:
                        for i in range(len(prplabel)):
                            item=pltitem[1][i]
                            prplabeldic[prplabel[i]]=prpdic[item]
                            typ=plttyp[i]
                            nmb=self.CountNumberOfData(prplabel[i],typ,prplabeldic)
                            prptypdic[prplabel[i]]=[plttyp[i],nmb]

        return prplabeldic,prptypdic
    
    def GetDerivedPropertyName(self):
        drvprplst=[]
        for prpnam,vars in self.drvprpdic.iteritems():
            drvprplst.append(prpnam)
        return drvprplst
    
    def MakeDerivedProperty(self,prpdic,prptypdic):
        drvprpdic=self.drvprpdic
        if len(drvprpdic) <= 0: return prpdic,prptypdic    
        for prpnam,vars in self.drvprpdic.iteritems():
            if prpdic.has_key(vars[0]) and prpdic.has_key(vars[1]):
                value=[]
                values1=prpdic[vars[0]]
                values2=prpdic[vars[1]]
                for val in range(len(values1)):
                    if vars[2] == '+': value.append(value1[i]+value2[i])
                    elif vars[2] == '-': value.append(value1[i]-value2[i])    
                prpdic[prpnam]=value
                plttyp=prpdic[vars[0]][0]
                prptypdic[prpnam]=[plttyp,1]
        return prpdic,prptypdic
        
    def ReadOrbitals(self,filename,beginstring,skiplines):
        """ Read molecular orbitals
        
        :return dic orbsetdic: orbsetdic={setno: orbset,...}
            orbset=[nbas(int),norb(int),center(lst),baslbl(lst),
            orbeng(lst),orbsym(lst),coeff(lst)]
            coeff: [[orb1 coeffs],[orb2 coeffs],..]
        """
        # centers,orbsymbol,symmetry,orbenergy,orbcoeff
        orbs={}; orbnmb=[]; nbas=0; orbeng=[]; norb=0
        center=[]; baslbl=[]; orbsym=[]; coeff=[]; coeffdic={}
        orbsetdic={}; setno=0
        colmn=beginstring[0]-1; string=beginstring[1]
        ncolmn=colmn+len(string)

        f=open(filename,'r')
        found=False; lines=0; readstart=False; readblock=1
        for s in f.readlines():
            s=s.rstrip()
            lines += 1
            #if lines <= 2: print 'lines counter',lines
            if not found:
                if s.startswith(string,colmn,ncolmn):
                    # need clear all for next orbital set
                    found=True; lines=0; norb=0
                    print 'found',s
                    continue
                else: continue
            else:
                if readstart and len(s) <= 0:
                    if readblock == 1: 
                        #nbas=lines-6
                        nbas=len(baslbl)
                        lines=2
                    #     
                    if len(orbnmb) > 0: norb=max(orbnmb)
                    else: norb=0
                    if norb >= nbas:
                        setno += 1 
                        lines=0
                        found=False
                        # store coeff in list
                        coeff=[]
                        for j in range(norb):
                            c=[]
                            for i in range(nbas):
                               idx=str(i+1)+':'+str(j+1)
                               c.append(coeffdic[idx])
                            coeff.append(c)  
                        nbas=len(center); norb=len(orbeng)
                        orbsetdic[setno]=[nbas,norb,center,baslbl, \
                                          orbeng,orbsym,coeff]
                        # need initialize for next orbital set
                        coeffdic={}
                        nbas=0; norb=0; center=[]; baslbl=[]; orbeng=[]; orbnmb=[]
                        continue
                    readblock += 1
                    continue
                if not readstart:
                    if lines < skiplines: 
                        #print 'skiplines. lines',lines
                        continue
                    else: 
                        #print 'readstart True'
                        readstart=True
                        continue
                else:
                    if lines == 3: # orbitalnumber
                        curorb=lib.SplitStringAtSpaces(s)
                        for i in range(len(curorb)): curorb[i]=int(curorb[i])
                        
                        orbnmb=orbnmb+curorb
                        #print 'orbnmb',orbnmb
                        #norb=max(orbnmb)
                    elif lines == 4: # orbital energy
                        items=lib.SplitStringAtSpaces(s)
                        
                        for i in range(len(items)): items[i]=float(items[i])
                        orbeng=orbeng+items
                        #print 'orbeng',orbeng
                    elif lines == 5: # orbital symmetry
                        items=lib.SplitStringAtSpaces(s)
                        orbsym=orbsym+items
                        #print 'orbsym',orbsym
                    else: # lines >= 6: # coefficients  
                        items=lib.SplitStringAtSpaces(s)
                        if readblock == 1:
                            center=center+[int(items[2])]
                            baslbl=baslbl+[items[3]]
                        #print 'aono,items',items[0]
                        aono=int(items[0])
                        iorb=norb
                        
                        for i in range(4,len(items)):
                            val=float(items[i])
                            iorb += 1
                            print 'aono,iorb',aono,iorb
                            idx=str(aono)+':'+str(iorb)
                            coeffdic[idx]=val
        f.close()
        #
        """
        #debug print
        for i in range(setno):
            print 'setno',i+1
            nbas=orbsetdic[i+1][0]
            norb=orbsetdic[i+1][1]
            center=orbsetdic[i+1][2]
            baslbl=orbsetdic[i+1][3]
            orbeng=orbsetdic[i+1][4]
            orbsym=orbsetdic[i+1][5]
            coeff=orbsetdic[i+1][6]
        print 'nbas,norb',nbas,norb
        print 'center',center
        print 'bassbl',baslbl
        print 'orbsym',orbsym
        print 'orbeng',orbeng
        print 'coeff',coeff
        """
        return orbsetdic
        
    def CountNumberOfData(self,prplabel,plttyp,prpdic):
        nmb=1
        if plttyp == 'coord': 
            if prpdic[prplabel].has_key('NUC.CHARGE'):
                nmb=prpdic[prplabel]['NUC.CHARGE'].count('end')
            elif prpdic[prplabel].has_key('ELEMENT'):
                nmb=prpdic[prplabel]['ELEMENT'].count('end')
            else: nmb=1
        elif plttyp == 'pie': nmb=1
        else: nmb=prpdic[prplabel].count('end')
        if nmb <= 0: nmb=1
        return nmb
    
    def ReadPropertyInOutput(self,filename,prpdefdic,constdic):
        prpdic={}
        nulltext='???????'
        search=False; prior=False; begin=False
        searchon=True; searchoff=False
        foundprior=False; foundbegin=False; foundend=False
        searchoncol=0; searchoffcol=0
        searchontext=nulltext; searchofftext=nulltext
        skiplines=0
        if prpdefdic.has_key('searchonstring'):
            search=True
            searchon=False
            searchoff=False
            seachoncol=prpdefdic['searchonstring'][0]-1
            searchontext=prpdefdic['searchonstring'][1]
            if prpdefdic.has_key('searchoffstring'):
                searchoffcol=prpdefdic['searchoffstring'][0]-1
                searchofftext=prpdefdic['searchoffstring'][1]
        else:
            search=False
            searchon=True; searchoff=False
            searchoncol=0; searchontext=nulltext
            searchoffcol=0; searchofext=nulltext
        if prpdefdic.has_key('priorstring'):
            prior=True
            priorcol=prpdefdic['priorstring'][0]-1
            priortext=prpdefdic['priorstring'][1]
            foundprior=False
            foundbegin=True
            foundend=False
        if prpdefdic.has_key('beginstring'):
            begin=True
            foundbegin=False
            foundend=False
            begincol=prpdefdic['beginstring'][0]-1
            begintext=prpdefdic['beginstring'][1]
            if prpdefdic.has_key('endstring'):
                endtext=prpdefdic['endstring'][1]
                endcol=prpdefdic['endstring'][0]-1
            else:
                endtext=nulltext; endcol=0
            if prpdefdic.has_key('skiplines'):
                skiplines=prpdefdic['skiplines']
        #
        line=0
        # read output file  
        f=open(filename,'r')
        found=False
        for s in f.readlines():
            s=s.rstrip()
            if not searchon:
                ss=s[searchoncol:]
                nc=ss.find(searchontext)
                if nc >= 0:
                    searchon=True; continue
            if searchon:
                ss=s[searchoffcol:]
                nc=ss.find(searchofftext)
                if nc >= 0: 
                    searchon=False; continue
            if prior:
                if searchon:
                    ss=s[priorcol:]; nc=ss.find(priortext)
                    if nc < 0: continue
                    ss=ss[len(priortext):]
                    prpdic=self.GetItemsInLine(prpdefdic,constdic,prpdic,ss)
                    continue
            if begin:
                if searchon:
                    if not foundbegin:
                        ss=s[begincol:]; nc=ss.find(begintext)
                        if nc < 0: continue
                        foundbegin=True; line=0
                        namlst=prpdefdic['getitems'][1]
                        continue
                    if foundbegin:
                        line += 1
                        if endtext == '':
                            sss=s.strip(); nc=-len(sss)
                        else:
                            ss=s[endcol:]; nc=ss.find(endtext)
                        if nc >= 0 and line > skiplines:
                            foundbegin=False
                            namlst=prpdefdic['getitems'][1]
                            for i in range(len(namlst)): prpdic[namlst[i]].append('end')
                            continue
                        else:
                            # read items
                            if line <= skiplines: continue
                            prpdic=self.GetItemsInLine(prpdefdic,constdic,prpdic,s)                                              
                            continue
        f.close()
        #        
        return prpdic

    def GetItemsInLine(self,prpdefdic,constdic,prpdic,ss):
        getitems=prpdefdic['getitems']
        dattyp=prpdefdic['datatype']
        sep=getitems[2][0]
        #ss=ss[len(priortext):]
        items=ss.split(sep)
        temp=[]
        for dat in items:
            if dat != '': temp.append(dat)
        items=temp
        nmblst=getitems[0]
        namlst=getitems[1]
        for i in range(len(namlst)):
            if not prpdic.has_key(namlst[i]): prpdic[namlst[i]]=[]
            try:
                val=items[nmblst[i]-1].strip()
            except: 
                #print 'val is missing'
                continue
            val=val.replace(',','')
            if dattyp[0] == 'auto': type=lib.StringType(val)
            else: type=dattyp[i].split('*',1)[0].strip()
            if type == 'float':
                sc=1.0
                if dattyp[0] != 'auto':
                    for name,value in constdic.iteritems():
                        nc=dattyp[i].find(name)
                        if nc >= 0: sc=value
                try: val=sc*float(val)
                except: continue
            elif type == 'int': 
                try: val=int(val)
                except: continue
            prpdic[namlst[i]].append(val)
            #except: pass
        return prpdic
             
class FMOProperty(object):
    def __init__(self,name,outfile): #,outfil,inpfil,pdbfil):
        # outfil:FMO output file name
        self.name=name
        #self.id=-1
        #self.outfile=outfil
        #self.inpfile=inpfil
        #self.pdbfile=pdbfil
        self.outfile=outfile
        
        
        self.nfrg=2
        
        
        
        self.SetProperty(self.outfile,'new')
        # proprtties
        # 'PIE','PIEDA','CT charge','Mulliken','MEP(PTC)','Density','Orbital'
        # 'HOMO-LUMO','DOS','Charge coupling terms',SCF conv','SCC conv','Geometry conv'
        # 'Geometry','Gradients','Vibration'
        self.propdic={} # {prop:data,...}, 'PIEDA':[pieda data]
        # test
        self.graphnamtxt=['PIE','PIEDA','CTcharge','Mulliken','ESPot','Density','Orbital',
                           'HOMO-LUMO(m)','DOS(m)','Charge Coupling','SCF conv.(m)','SCF conv.(d)',
                           'SCC conv.','Geom conv.','Geom change','Vibration']
        for name in self.graphnamtxt: self.propdic[name]=[]        
        # property flags
        self.geom=3 # 0:no, 1:output file, 3:input file
        self.pieda=False # =0:pie, =1:pieda
        self.ctchg=False # =0:no data, 1:yes
        self.mulchg=False # 0:not avilable, 1*yes
        self.espot=False
        self.density=False
        self.orbital=False
        # method
        self.fmo=True
        self.nbody=2 # # 2:fmo2, 3:fmo3
        self.corr=0 # flag 0:hf, 1:corr
        # property value
        self.prpdic={}
        self.etfmo2=0 # fmo2,fmo3
        self.etfmo3=0 
        self.ecfmo2=0 # fmo2,3
        self.ecfmo3=0 #
        
        self.dft=False
        # molecule data
        self.natmfrg=[] # each fragment
        self.natm=0
        self.nbas=0
        self.nfrg=0
        self.tchg=0 # total charge of while system
        self.nbasfrg=[] # each fragment
        self.frgnam=[]
        self.frgchg=[]
        self.indat=[]
        self.bdabaa=[]
        self.jobtitle='' # job comment in output
        self.gamessver=''
        self.fmover=''
        #
        self.frgpieda=[]
        self.frgdist=[]
        self.ctcharge=[]
        self.mulliken=[]
        self.onebody=[]
        #
        self.SetAttributes()
        """
        if self.nfrg >= 1:
            err,ver,self.frgdist=rwfile.ReadFrgDistance(os.path.realpath(self.outfile))                
            #
            err,ver,onebody=rwfile.ReadFMOOneBody(self.outfile)        
            self.onebody=ConvertOneBodyForPlot(onebody,'L1')
            #
            err,ver,frgpieda=rwfile.ReadFMOPIEDA(self.outfile)
            self.frgpieda,self.ctcharge=ConvertPIEDAForPlot(frgpieda)
            if self.nfrg > 1:
                err,ver,mulliken=rwfile.ReadFMOMulliken(self.outfile)
                self.mulliken=ConvertMullikenChargeForPlot(mulliken)
            else:
                err,ver,mulliken=rwfile.ReadGMSMulliken(self.outfile)
                self.mulliken=ConvertGMSMullikenChargeForPlot(mulliken)
            #self.SetMulliken()
            if len(self.inpfile) > 0:
                err,nfrag,self.frgchg,self.frgnam,self.indat,self.bdabaa= \
                    rwfile.ReadFMOInput(self.inpfile)
        """
    def SetProperty(self,filename,mode):
        """
        :param str filename: filename:gamess output '.out' or '.log','fmoinp('.inp'),'pdb ('.pdb' or '.ent')
        :param str mode: 'update','add','new','clear'
        """
        if not os.path.exists(filename):
            print 'file: "'+filename+'" does not exist.'
        base,ext=os.path.splitext(filename)
        self.file=filename
        # mode???
        if ext == '.out' or ext == '.log':
        #if self.nfrg >= 1:
            err,ver,self.frgdist=rwfile.ReadFrgDistance(os.path.realpath(self.file))                
            #
            err,ver,onebody=rwfile.ReadFMOOneBody(self.file)        
            self.onebody=self.ConvertOneBodyForPlot(onebody,'L1')
            #
            err,ver,frgpieda=rwfile.ReadFMOPIEDA(self.file)
            self.frgpieda,self.ctcharge=self.ConvertPIEDAForPlot(frgpieda)
            
            if self.nfrg > 1:
                err,ver,mulliken=rwfile.ReadFMOMulliken(self.file)
                self.mulliken=self.ConvertMullikenChargeForPlot(mulliken)
            else:
                err,ver,mulliken=rwfile.ReadGMSMulliken(self.file)
                self.mulliken=self.ConvertGMSMullikenChargeForPlot(mulliken)
        elif ext == '.inp':
            if len(self.inpfile) > 0:
                err,nfrag,self.frgchg,self.frgnam,self.indat,self.bdabaa= \
                    rwfile.ReadFMOInput(self.file)
        elif ext == '.pdb' or ext == 'ent':
            pass
       
    def GetProperty(self,name): 
        if self.propdic.has_key(name): return self.propdic[name]
        else: return []

    def GetPropertyItems(self):
        itemlst=[]
        for name in self.graphnamtxt:      
            if self.propdic.has_key(name): itemlst.append(name)
        return itemlst
                            
    def SetAttributes(self):
        #self.geom=3 # 0:no, 1:output file, 3:input file
        err,ver,prpdic=rwfile.ReadFMOStatics(os.path.realpath(self.file))
        if err:
            self.fmo=False; return
        self.prpdic=prpdic
        
        #print 'prpdic',prpdic
        #prpdic['nbody']=2
        #prpdic['mplevl']=0
        #prpdic['fmover']=4.3
        try:
            self.nbody=prpdic['nbody'] #2 # # 2:fmo2, 3:fmo3
        except: pass
        if self.nbody > 1:
            if prpdic.has_key('pieda'): self.pieda=prpdic['pieda'] # =0:pie, =1:pieda
            if prpdic.has_key('pieda'): self.ctchg=prpdic['pieda'] # =0:no data, 1:yes
            if prpdic.has_key('mulchg'): self.mulchg=prpdic['mulchg'] # 0:not avilable, 1*yes

        self.espot=False
        self.density=False
        self.orbital=False
        # method
        try:
            self.corr=prpdic['mplevl'] #0 # flag 0:hf, 1:corr
        except: pass
        # property value
        self.etfmo2=0.0
        if self.nbody > 1:
            if prpdic.has_key('escf(2)'): self.etfmo2=prpdic['escf(2)'] #0 # fmo2,fmo3
        else: self.etfmo2=prpdic['etotal']
        self.etfmo3=0 
        self.ecfmo2=0 # fmo2,3
        self.ecfmo3=0 #
        
        self.dft=False
        if prpdic.has_key("dfttyp"): self.dft=True
        # molecule data
        self.natmfrg=[] # each fragment
        if prpdic.has_key('natm'): self.natm=prpdic['natm']
        if prpdic.has_key('nbas'): self.nbas=prpdic['nbas']
        if prpdic.has_key('nfrg'): self.nfrg=prpdic['nfrg']
        if prpdic.has_key('tchg'): self.tchg=prpdic['tchg']
        self.nbasfrg=[] # each fragment
        self.jobtitle='' # job comment in output
        try:
            self.gamessver=prpdic['gmsver']
        except: pass
        try:
            self.fmover=prpdic['fmover']
        except: pass
        
    def GetFMOIterEnergy(self):
        err,ver,jter,de,dd=rwfile.ReadFMOIterEnergy(self.outfile)
        return jter,de,dd
    
    def GetFrgIterEnergy(self):
        err,ver,jter,efmo,de,dd=rwfile.ReadFrgIterEnergy(self.outfile)
        return jter,efmo,de,dd

    @staticmethod
    def ConvertPIEDAForPlot(fmopieda):
        # fmopieda: pieda read by ReadFMOPIEDA(fmo output file)
        # return pieda: [[i,j,tot,(cr)],...](PIE) or [[i,j,tot,es,ex,ct,(cr)],...] (PIEDA)
        # no cr term if uncorr level calculation. 
        pieda=[]; ctchg=[]
        if len(fmopieda) <= 0: return pieda,ctchg
        pie=False; corr=True
        if len(fmopieda[0]) <= 11: pie=True
        if len(fmopieda[0]) <= 12: corr=False
        ndat=len(fmopieda)
        nfrg=fmopieda[ndat-1][0]
        for i in range(nfrg):
            piedai=[]
            for j in range(nfrg):
                tmp=[]
                tmp.append(j+1)
                piedai.append(tmp)
            pieda.append(piedai)
        
        ctchg=copy.deepcopy(pieda)

        for i in range(len(fmopieda)):
            i0=fmopieda[i][0]-1
            j0=fmopieda[i][1]-1
            tmp=[]
            if not pie:
                rij=fmopieda[i][4]
                if rij == 0:
                    tot=0.0; es=0.0; ex=0.0; ct=0.0; di=0.0
                else:
                    tot=fmopieda[i][8]
                    es=fmopieda[i][9]
                    ex=fmopieda[i][10]
                    ct=fmopieda[i][11]
                    di=0.0
                    if corr: di=fmopieda[i][12]
                tmp.append(tot); tmp.append(es)
                tmp.append(ex); tmp.append(ct)
                
                tmp.append(di)
                
                pieda[i0][j0]=pieda[i0][j0]+tmp
                pieda[j0][i0]=pieda[j0][i0]+tmp
            else:
                if len(fmopieda[i]) == 10: tot=fmopieda[i][9]
                elif len(fmopieda[i]) == 11: tot=fmopieda[i][10]
                else:
                    dlg=lib.MessageBoxOK("Failed to get PIE","")
                    return pieda,ctchg
                tmp.append(tot)
                pieda[i0][j0]=pieda[i0][j0]+tmp
                pieda[j0][i0]=pieda[j0][i0]+tmp
            ctc=fmopieda[i][5]
            ctchg[i0][j0].append(-ctc) #=ctchg[i0][j0]+[ctc] # both for pie and pieda
            ctchg[j0][i0].append(ctc) #=ctchg[j0][i0]+[ctc]
        # diagonal element 
        for i in range(nfrg):
            if pie:
                pieda[i][i]=pieda[i][i]+[0.0]
            else:
                pieda[i][i]=pieda[i][i]+[0.0,0.0,0.0,0.0,0.0]
            ctchg[i][i]=ctchg[i][i]+[0.0]
        
        return pieda,ctchg
    
    @staticmethod
    def ConvertOneBodyForPlot(fmoone,layer):
        # fmone: data read by puPlot.ReadOneBody(fmo output file)
        # layer: 1st,2nd or 3rd layer given by an integer
        # retuen onbody: [[i,energy],...], energy in a.u.
        # tokcal=627.52
        layr='L'+str(layer)
        onebody=[]
        nfrg=len(fmoone)
        for i in range(nfrg):
            tmp=[]
            #tmp.append(i+1)
            value=0.0
            if fmoone[i][1] != layer: continue
            value=fmoone[i][2]
            tmp.append(i+1)
            tmp.append(value)
            onebody.append(tmp) 
        #
        return onebody
     
    @staticmethod
    def ConvertCTChargeForPlot(fmoctchg):
        # fmoctchg: ct charge read by puPlot.ReadFMOCTCharge(fmo output file)
        # return ctcharge: [[j,value],...]
        # transfered charge from ith to jth fragment in (i,j) element
        # diagonal elecent store net transfered charge.
        ctcharge=[]
        nfrg=len(fmoctchg)
        if nfrg <= 0: return ctcharge

        for i in range(nfrg):
            tmp=[]
            for j in range(nfrg):
                tmp.append([j+1,0.0]) # [j,val], val=tval for i=J
            for j in range(len(fmoctchg)):
                jj=fmoctchg[j][1]-1
                val=fmoctchg[j][2]
                if jj == i: val=fmoctchg[j][2]
                tmp[jj][1]=val
            ctcharge.append(tmp)
        return ctcharge
    
    @staticmethod
    def ConvertMullikenChargeForPlot(fmomulchg):
        # fmomulchg: data read by puPlot.ReadFMOMulliken(fmo output file)
        # mulliken:[[atom,val],..,[natm-1,val]]
        mulchg=[]; muldic={}
        for i in range(len(fmomulchg)):
            ifrg=fmomulchg[i][1]
            if not muldic.has_key(ifrg): muldic[ifrg]=[]
            tmp=[]
            tmp.append(fmomulchg[i][0])
            for j in range(3,len(fmomulchg[i])):
                tmp.append(fmomulchg[i][j])
            muldic[ifrg].append(tmp)
        lst=muldic.keys()
        nfrg=max(lst)
        for i in range(nfrg):
            tmp=muldic[i+1]
            tmp.sort(key=lambda x:x[0])
            mulchg.append(tmp)
        return mulchg
    
    @staticmethod
    def ConvertGMSMullikenChargeForPlot(mulliken):
        mulchg=[]
        for i in range(len(mulliken)):
            chg=mulliken[i]
            del chg[1]; del chg[1]
            mulchg.append(chg)
        return mulchg

class PlotOrbitalEnergy(object):
    def __init__(self,parent,orbitallst):
    
        self.parent=parent
        self.orbitallst=[]
        self.winpos=[-1,-1]
        self.winsize=[0,0]
        self.orbitallst=orbitallst
        #self.orbitallst=[[-20,-15,-10,5,10,15],[-50,-20,-15,-10,5,10,15],[-15,-10,-5,8,10,12],
        #                 [-15,-10,-5,8,10,12]]
        
        norbpanel=len(self.orbitallst)
        #if norbpanel <= 0: norbpanel=1 
        orbitalpanwidth=10 #115
        self.winwidth=100+8+norbpanel*orbitalpanwidth+10
        if norbpanel <= 0: self.winwidth=110
        self.winheight=self.winsize[1]
        if self.winheight <= 0: self.winheight=340
        self.winsize=[self.winwidth,self.winheight]
        self.drawenergy=OrbitalEnergyGraph_Frm(self.parent,-1,self,winsize=self.winsize,orbitallst=self.orbitallst)        
        
    def SetOrbitalList(self,orbitallst):
        self.orbitallst=orbitallst
 
    def MoveDrawWin(self):
        self.drawenergy.Destroy()
        self.winsize[0]=self.winwidth
        self.drawenergy=OrbitalEnergyGraph_Frm(self.parent,-1,self,
                                              winpos=self.winpos,winsize=self.winsize,orbitallst=self.orbitallst)        
        
class OrbitalEnergyGraph_Frm(wx.MiniFrame):
    def __init__(self,parent,id,parobj,winpos=[-1,-1],winsize=[-1,-1],orbitallst=[]): #,model,ctrlflag,molnam,winpos):
        """
        :param obj parent: parent object
        :param int id: object id
        """       
        self.parent=parent
        self.parobj=parobj
        self.title='Orbital energy plotter'
        self.orbitallst=orbitallst
        self.magnify=False
        if len(winsize) <= 0: winsize=[11,300]
        norbpanel=len(self.orbitallst)
        #if norbpanel <= 0: norbpanel=1 
        orbitalpanwidth=10 #115
        self.winwidth=100+8+norbpanel*orbitalpanwidth+10
        if norbpanel <= 0: self.winwidth=110
        self.winheight=340
        #if winpos[1] <= 0: self.winheight=340
        
        winsize=lib.MiniWinSize(winsize) #([100,355])
        self.norbpanel=norbpanel
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
                          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)
        """ need codes """
        self.erangemin=-15.0
        self.erangemax=5.0
        
        self.orbitaltitle='orbtitle'
        # menu
        self.mode=0
        if self.mode == 0:
            menubar=self.MenuItems() # method of MyModel class
            self.SetMenuBar(self.menubar.menuitem) # method of wxFrame class
            self.Bind(wx.EVT_MENU,self.OnMenu)
        # 
        self.bgcolor='light gray'
        #self.cubedataname=[]
        # create panel
        self.CreatePanel()
        
        ###for i in range(self.norbpanel): self.CreateOrbitalPanel(i)

        ###self.SetParamsToWidgets()
        #
        self.Show()
        # initialize view
        ###self.InitDrawOrbitalWin()
        self.PlotEnergy()
        
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_SIZE,self.OnSize)

    def OnMove(self,event):
        self.parobj.winpos=self.GetPosition() 
        self.parobj.MoveDrawWin()
    
    def OnSize(self,event):
        self.parobj.winsize=self.GetSize()
        self.OnMove(1)

    def OnClose(self,event):
        self.Destroy()

    def PlotEnergy(self):
        self.orbgraph.SetYRange(self.erangemin,self.erangemax)
        self.orbgraph.SetData(self.orbitallst) #[0])
        self.orbgraph.SetYAxisLabel('Energy (ev)')
        self.orbgraph.Plot(True)

    def CreatePanel(self):
        size=self.GetClientSize()
        w=size[0]; h=size[1]
        #w=self.orbitalpanwidth
        #xpanpos=5
        ff='%5.0f'
        # upper panel
        panel=wx.Panel(self,-1,pos=(0,0),size=(w,h)) #ysize))
        panel.SetBackgroundColour(self.bgcolor)
        # cubedata
        yloc=5; xloc=10

        label=wx.StaticText(panel,-1,label=self.orbitaltitle,pos=(xloc,yloc),size=(w-10,18))
        ###label.Bind(wx.EVT_LEFT_DOWN,self.OnOrbTitleLeftClick)
        ##label.SetToolTipString('L-Click to be avtive')
        ##wx.StaticLine(panel,pos=(0,0),size=(4,h),style=wx.LI_VERTICAL)
        #ststit.SetToolTipString('Choose drawing style')
        yloc += 25
        self.wplt=w-20 #self.winwidth-35 #-25 #90; 
        self.hplt=h-70 #self.winheight-120
        self.orbgraph=graph.EnergyGraph(panel,-1,[xloc,yloc],[self.wplt,self.hplt],'white',retobj=self)        #yloc += 25
        self.orbgraph.SetToolTipString('L-Click a bar for select. L-Drag for move plot window')
        #
        #yloc += self.hplt+10
        yloc=h-30
        xloc=w-100

        btnrdc=wx.Button(panel,-1,"<",pos=(xloc,yloc),size=(20,20))
        btnrdc.Bind(wx.EVT_BUTTON,self.OnOrbReduce)
        btnrdc.SetToolTipString('"<" ("<") key press also reduces/magnifies')
        btnrdc.Bind(wx.EVT_KEY_DOWN,self.OnOrbKeyDown)
        btnmag=wx.Button(panel,-1,">",pos=(xloc+25,yloc),size=(20,20))
        btnmag.Bind(wx.EVT_BUTTON,self.OnOrbMagnify)
        btnmag.SetToolTipString('"<" ("<") key press also reduces/magnifies')
        btnmag.Bind(wx.EVT_KEY_DOWN,self.OnOrbKeyDown)
        btnset=wx.Button(panel,-1,"Reset",pos=(xloc+50,yloc),size=(40,20))
        btnset.Bind(wx.EVT_BUTTON,self.OnOrbReset)
        btnset.SetToolTipString('Reset draw size')
        
    def OnOrbKeyDown(self,event):
        # ascii:44:'<',46:'>', unicode: 60:'<',62:'>'
        keycode=event.GetKeyCode()
        if keycode == 46: self.ZoomEnergyGraph(True)
        elif keycode == 44: self.ZoomEnergyGraph(False)

    def ZoomEnergyGraph(self,magnify):
        #graphobj=self.GetGraphObj(idata)
        #
        ymin,ymax=self.orbgraph.GetYRange()
        yinc=1.0
        if magnify: ymin += yinc; ymax -= yinc
        else: ymin -= yinc; ymax += yinc    
        #
        self.orbgraph.SetYRange(ymin,ymax)
        self.orbgraph.Plot(True)
    
    def OnOrbMagnify(self,event):
        self.ZoomEnergyGraph(True)
    
    def OnOrbReduce(self,event):
        #
        self.ZoomEnergyGraph(False)

    def OnOrbReset(self,event):
        # reset energy graph color
        ymin=self.erangemin
        ymax=self.erangemax
        self.orbgraph.SetYRange(ymin,ymax)
        self.orbgraph.Plot(True)


    
    def MenuItems(self):
        # menuitemdata: (top menu item, (submenu item, comment to be displayed in
        #       the first field of statusbar, checkable),..,))
        # Menu items
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        submenu.Append(-1,"Open","Open...")
        submenu.AppendSeparator()
        submenu.Append(-1,"Quit","Quit...")
        menubar.Append(submenu,'File')
        # Edit
        submenu=wx.Menu()
        submenu.Append(-1,"Cube data","Edit/View cube data")
        menubar.Append(submenu,'Edit')

        return menubar

    def OnMenu(self,event):
        # menu event handler
        menuid=event.GetId()
        #item=self.menuitem.GetLabel(menuid)
        #bChecked=self.menubar.IsChecked(menuid) # method of wx.Menu
        #menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()

        # File menu
        if item == "Open": # open file
            wcard="den,mep cube(*.den;*.mep)|*.den;*.mep|all(*.*)|*.*"
            filenames=lib.GetFileName(self,wcard,"r",True,"")
            if not isinstance(filenames,list): filenames=[filenames]
            if len(filenames) > 0:
                ndat=0
                for filename in filenames:
                    if len(filename) > 0:
                        if not os.path.exists(filename):
                            self.ConsoleMessage(mess)(filename+' file not found. skipped.')
                        else:
                            base,ext=os.path.splitext(filename)
                            if ext == '.den' or ext == '.mep':
                                err=self.AddToCubeObjDic(filename)
                                if not err:
                                    self.ConsoleMessage(mess)('Read cube file: '+filename)
                                    ndat += 1
                            else:
                                mess='Can not read file with extention: "'+ext+'"'
                                lib.MessageBoxOK(mess,"OnMenu")
                                continue
                mess=str(ndat)+' '+prop+' cube data were read.'
                self.ConsoleMessage(mess)(mess)

        if item == "Quit":
            self.OnClose(1)
        # Edit menu
        if item == "Cube data":
            self.OpenNotePad()    

@lib.CLASSDECORATOR(lib.FUNCCALL)
class PIEDAGraph_Frm(wx.Frame):
    def __init__(self,parent,id,winpos,winsize,onedmode,prpmode,childmode): #,pltprp,datnam,fmodat,molint): #,molnam,prop):
        #winsize=(660,360) #(680,350) # (520,350)
        wx.Frame.__init__(self,parent,id,pos=winpos,size=winsize,
                          style=wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION|\
                          wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT) 
        self.parent=parent
        self.model=self.parent.model
        #
        self.mdlargs=self.model.mdlargs
        self.pltargs=self.parent.pltargs
        
        
        self.pltprp=prpmode # 0:pieda, 1:ctcharge, 2: mulliken
        self.childmode=childmode
        self.onedmode=onedmode
        if parent:
            self.parent=parent
            self.ctrlflag=parent.ctrlflag
        else: self.ctrlflag=ctrl.CtrlFlag()
        # icon
        try: lib.AttachIcon(self,const.FUPLOTICON)
        except: pass        
        #
        self.bgcolor="white"
        self.SetBackgroundColour(self.bgcolor)
        self.childgraphsize=(500,500)
        self.childgraphstat=False
        self.ready=True
        # Menu
        self.menubarplot=self.MenuGraph()
        self.SetMenuBar(self.menubarplot)
        self.Bind(wx.EVT_MENU,self.OnMenuGraph)
        
        # molview
        self.openremarkwin=False
        self.wcolpan=80  # width of color remark, the same as wpan in CreateDispPanel
        self.hcolpan=200 # hight of color remark, the same as hpan in CreateDispPanel
        self.rankposi=10
        self.ranknega=10
        self.font = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_NORMAL, False, 'Courier 10 Pitch')
        # plot panel and command panel
        self.graphname=['pieda','ctcharge','mulliken']
        # initial values
        self.molint=False
        self.datnam=''
        self.nfrg=0
        self.ifrg=1
        self.iatm=-1
        self.yrange=50.0
        if self.pltprp == 1: self.yrange=0.2
        if self.pltprp == 2: self.yrange=0.5
        self.eachfrg=True
        self.pltdat=[]
        self.sortitem=0
        self.pickeddata=10000.0
        # for pie/pieda specific
        self.ckbcmp=[None,None,None,None,None] # ckeck box: es,ex,ctmix,di,1b
        self.piedacmp=[False,False,False,False,False] # flag: es,ex,ctmix,di,1b
        self.activecmp=[False,False,False,False,False] # ckbcom: enable/disable flag
        # for mulliken charge
        self.rbtmul=[None,None,None,None] # 2, 2-1,3,3-2 body
        self.activemul=[True,False,False,False]
        self.mullbody=[True,False,False,False]
        # graph panel
        self.CreateGraphPanel()
        # event handlers
        self.Bind(wx.EVT_SIZE,self.OnSize)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        ###self.Bind(wx.EVT_SET_FOCUS,self.OnFocus)
        #self.Bind(wx.EVT_PAINT, self.OnPaint)
        #self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)

    def OnKeyDown(self,event):
        keycode=event.GetKeyCode()
        keychar=lib.KeyCodeToASCII(keycode)
        saveimgkey=self.model.setctrl.GetShortcutKeyChar('Save image')
        print 'Onkeydown 1d,savimgkey',event.GetKeyCode(),saveimgkey
        if keychar == saveimgkey: #73: # 'i' in ASCII code
             imgdir=self.model.setctrl.GetDir('Images')
             base='fup-pieda1d-'
             ###ext='.'+self.model.setctrl.GetParam('image-format')
             filename=lib.MakeFileNameWithDateTime(base,'.bmp')
             filename=os.path.join(imgdir,filename)
             lib.SaveBitmapAsFile(filename,self.graph.buffer)
             mess='fuplot(PIEDA1DGraph): Saved image file='+filename
             self.model.ConsoleMessage(mess)
        event.Skip()

    def OnKeyDownChild(self,event):
        print 'Onkeydown chaild',event.GetKeyCode()
        keycode=event.GetKeyCode()
        keychar=lib.KeyCodeToASCII(keycode)
        saveimgkey=self.model.setctrl.GetShortcutKeyCode('Save image')
        if keychar == saveimgkey: #73: # 'i' in ASCII code
             imgdir=self.model.setctrl.GetDir('Images')
             base='fup-pieda2d-'
             ###ext='.'+self.model.setctrl.GetParam('image-format')
             filename=lib.MakeFileNameWithDateTime(base,'.bmp')
             filename=os.path.join(imgdir,filename)
             lib.SaveBitmapAsFile(filename,self.childgraph.buffer)
             mess='fuplot(PIEDA2DGraph): Saved image file='+filename
             self.model.ConsoleMessage(mess)
        event.Skip()

    def OnMouseLeftDown(self,event):
        event.Skip()        
    def OnMouseRightDown(self,event):
        event.Skip()        
    def OnMouseLeftUp(self,event):
        event.Skip()        
    def OnMouseMove(self,event):
        event.Skip()        

    def CreateGraphPanel(self):
        # crate plot panel
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        #
        self.hcmdpanel=60 #50 # hight of command panel
        self.hplt=h-self.hcmdpanel; self.wplt=w
        self.pltpan=wx.Panel(self,wx.ID_ANY,pos=(0,0),size=(w,h)) #self.hplt)) #,style=wx.DOUBLE_BORDER)
        self.pltpan.SetBackgroundColour(self.bgcolor)
        
        if self.childmode: self.hplt=h
        if self.onedmode:
            self.graph=graph.BarGraph(self.pltpan,-1,self,(0,0),(self.wplt,self.hplt),'white')
        else:
            self.graph=graph.TileGraph(self.pltpan,-1,self,(0,0),(self.wplt,self.hplt),'white')
        if self.childmode: return
        if self.pltprp == 0: self.piedacmdpan=self.CreatePIEDACmdPanel()
        if self.pltprp == 1: self.ctchargecmdpan=self.CreateCTChargeCmdPanel()
        if self.pltprp == 2: self.mullikencmdpan=self.CreateMullikenCmdPanel()        
        self.SetWidgetStates()
        
    def CreatePIEDACmdPanel(self):
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]

        yloc=h-self.hcmdpanel
        self.piedacmd1pan=wx.Panel(self.pltpan,wx.ID_ANY,pos=(0,yloc),size=(w,self.hcmdpanel)) #,style=wx.DOUBLE_BORDER)
        self.piedacmd1pan.SetBackgroundColour("light gray")
        # fragment number selector        
        wx.StaticLine(self.piedacmd1pan,pos=(0,0),size=(w,2),style=wx.LI_HORIZONTAL)
        st0=wx.StaticText(self.piedacmd1pan,-1,"Fragment #:",pos=(5,6),size=(70,18))
        self.sclfrg=wx.SpinCtrl(self.piedacmd1pan,-1,value="1",pos=(78,4),size=(60,20),
                    style=wx.SP_ARROW_KEYS) #,min=1,max=self.nfrg)
        #self.sclfrg.Bind(wx.EVT_TEXT,self.OnChangeFragment)
        self.sclfrg.Bind(wx.EVT_SPINCTRL,self.OnChangeFragment)
        # plot energy range
        xloc=5; yloc=35 #30
        wx.StaticText(self.piedacmd1pan,-1,"y.range(+/-):",pos=(xloc,yloc+2),size=(75,18))                  
        self.tclyrng=wx.TextCtrl(self.piedacmd1pan,-1,"50",pos=(xloc+80,yloc),size=(55,18),
                                style=wx.TE_PROCESS_ENTER)        
        self.tclyrng.Bind(wx.EVT_TEXT_ENTER,self.OnChangeYRange)
        # separate line
        xsep=146
        wx.StaticLine(self.piedacmd1pan,pos=(xsep,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)
        # PIEDA component
        xloc=155; yloc=8
        wx.StaticText(self.piedacmd1pan,wx.ID_ANY,'Plot:',pos=(xloc,yloc),size=(30,18))
        xloc=185
        self.rbtech=wx.RadioButton(self.piedacmd1pan,-1,"PIE",pos=(xloc,yloc), \
                                  style=wx.RB_GROUP)
        self.rbtech.Bind(wx.EVT_RADIOBUTTON,self.OnEach)
        #
        self.rbtall=wx.RadioButton(self.piedacmd1pan,-1,"BE",pos=(xloc+45,yloc)) #,size=(40,18))
        self.rbtall.Bind(wx.EVT_RADIOBUTTON,self.OnAll)

        xloc=280
        wx.StaticText(self.piedacmd1pan,wx.ID_ANY,'for',pos=(xloc,yloc),size=(25,18))
        xloc=302
        self.ckbcmp[0]=wx.CheckBox(self.piedacmd1pan,wx.ID_ANY,"es",pos=(xloc,yloc)) #,size=(50,18))
        self.ckbcmp[0].Bind(wx.EVT_CHECKBOX,self.OnPIEDAComponent)

        self.ckbcmp[1]=wx.CheckBox(self.piedacmd1pan,wx.ID_ANY,"ex",pos=(xloc+35,yloc)) #,size=(50,18))
        self.ckbcmp[1].Bind(wx.EVT_CHECKBOX,self.OnPIEDAComponent)

        self.ckbcmp[2]=wx.CheckBox(self.piedacmd1pan,wx.ID_ANY,"ctmix",pos=(xloc+70,yloc)) #,size=(50,18))
        self.ckbcmp[2].Bind(wx.EVT_CHECKBOX,self.OnPIEDAComponent)

        self.ckbcmp[3]=wx.CheckBox(self.piedacmd1pan,wx.ID_ANY,"di",pos=(xloc+120,yloc)) #,size=(50,18))
        self.ckbcmp[3].Bind(wx.EVT_CHECKBOX,self.OnPIEDAComponent)

        self.ckbcmp[4]=wx.CheckBox(self.piedacmd1pan,wx.ID_ANY,"1b",pos=(xloc+152,yloc)) #,size=(50,18))
        self.ckbcmp[4].Bind(wx.EVT_CHECKBOX,self.OnPIEDAComponent)
        #
        wx.StaticText(self.piedacmd1pan,wx.ID_ANY,'<-',pos=(xloc+188,yloc),size=(15,16))
        self.btnall=wx.ToggleButton(self.piedacmd1pan,label='all(on/off)',pos=(xloc+205,yloc),size=(65,16))     
        self.btnall.Bind(wx.EVT_TOGGLEBUTTON,self.OnAllCompOnOff)
        self.btnall.SetValue(True) # default is on (see self.piedacmp)
        # separate line 
        wbtn=68
        wx.StaticLine(self.piedacmd1pan,pos=(0,self.hcmdpanel/2+1),size=(w-wbtn,2),style=wx.LI_HORIZONTAL)
        # sort
        xloc=155; yloc=35 #30
        wx.StaticText(self.piedacmd1pan,wx.ID_ANY,'Sort:',pos=(xloc,yloc+2),size=(30,18))
        self.rbtseq=wx.RadioButton(self.piedacmd1pan,wx.ID_ANY,'fragment #',pos=(xloc+35,yloc+2), \
                               style=wx.RB_GROUP)
        self.rbtseq.Bind(wx.EVT_RADIOBUTTON,self.OnSortFrgNmb)
        # sort button
        self.rbtdst=wx.RadioButton(self.piedacmd1pan,wx.ID_ANY,'distance',pos=(xloc+130,yloc+2)) 
        self.rbtdst.Bind(wx.EVT_RADIOBUTTON,self.OnSortDist)
        self.rbtlrg=wx.RadioButton(self.piedacmd1pan,wx.ID_ANY,'large',pos=(xloc+205,yloc+2))
        self.rbtlrg.Bind(wx.EVT_RADIOBUTTON,self.OnSortLarge)
        self.rbtsml=wx.RadioButton(self.piedacmd1pan,wx.ID_ANY,'small',pos=(xloc+260,yloc+2))
        self.rbtsml.Bind(wx.EVT_RADIOBUTTON,self.OnSortSmall)  
        yloc=8
        # separator line
        wx.StaticLine(self.piedacmd1pan,pos=(w-wbtn,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)        
        # 2d button
        self.tglcld=wx.ToggleButton(self.piedacmd1pan,label='2DGraph',pos=(w-58,yloc),size=(52,18))     
        self.tglcld.Bind(wx.EVT_TOGGLEBUTTON,self.OnOpenChildGraph)
        # molview button
        yloc=35 #30
        self.tglvew=wx.ToggleButton(self.piedacmd1pan,label='MolView',pos=(w-58,yloc),size=(52,18))     
        self.tglvew.Bind(wx.EVT_TOGGLEBUTTON,self.OnMolView)
        self.tglvew.SetValue(self.openremarkwin)
        # set status for Widgets
        self.SetWidgetStates()
        self.SetPIEDAComponentWidget(self.piedacmp)
         
    def CreateCTChargeCmdPanel(self):
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]

        hgraph=h-self.hcmdpanel 
        self.graph1d=graph.BarGraph(self.pltpan,-1,self,(0,0),(w,hgraph),'white')

        yloc=h-self.hcmdpanel       
        #
        self.ctcmd1pan=wx.Panel(self.pltpan,wx.ID_ANY,pos=(0,yloc),size=(w,self.hcmdpanel)) #,style=wx.DOUBLE_BORDER)
        self.ctcmd1pan.SetBackgroundColour("light gray")
        # fragment number selector        
        wx.StaticLine(self.ctcmd1pan,pos=(0,0),size=(w,2),style=wx.LI_HORIZONTAL)
        st0=wx.StaticText(self.ctcmd1pan,-1,"Fragment #:",pos=(5,6),size=(70,18))
        self.sclfrg=wx.SpinCtrl(self.ctcmd1pan,-1,value="1",pos=(78,4),size=(60,20),
                          style=wx.SP_ARROW_KEYS) #,min=1,max=self.nfrg)
        self.sclfrg.Bind(wx.EVT_TEXT,self.OnChangeFragment)
        # plot energy range 
        xloc=5; yloc=35 #30
        wx.StaticText(self.ctcmd1pan,-1,"y.range(+/-):",pos=(xloc,yloc+2),size=(75,18))                  
        self.tclyrng=wx.TextCtrl(self.ctcmd1pan,-1,"0.5",pos=(xloc+80,yloc),size=(55,18),
                                style=wx.TE_PROCESS_ENTER)        
        self.tclyrng.Bind(wx.EVT_TEXT_ENTER,self.OnChangeYRange)
        # separate line
        xsep=146
        wx.StaticLine(self.ctcmd1pan,pos=(xsep,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)
        # PIEDA component
        xloc=155; yloc=8
        wx.StaticText(self.ctcmd1pan,wx.ID_ANY,'Plot:',pos=(xloc,yloc),size=(30,18))
        self.rbtall=wx.RadioButton(self.ctcmd1pan,-1,"all",pos=(xloc+35,yloc), \
                                  style=wx.RB_GROUP)
        #
        self.rbtall.Bind(wx.EVT_RADIOBUTTON,self.OnAll)
        #
        self.rbtech=wx.RadioButton(self.ctcmd1pan,-1,"each",pos=(xloc+75,yloc)) #,size=(40,18))
        self.rbtech.Bind(wx.EVT_RADIOBUTTON,self.OnEach)
        # separate line 
        wbtn=68 # 55
        wx.StaticLine(self.ctcmd1pan,pos=(0,self.hcmdpanel/2+1),size=(w-wbtn,2),style=wx.LI_HORIZONTAL)
        # sort
        xloc=155; yloc=35 #30
        wx.StaticText(self.ctcmd1pan,wx.ID_ANY,'Sort:',pos=(xloc,yloc+2),size=(30,18))
        self.rbtseq=wx.RadioButton(self.ctcmd1pan,wx.ID_ANY,'fragment #',pos=(xloc+35,yloc+2), \
                               style=wx.RB_GROUP)
        self.rbtseq.Bind(wx.EVT_RADIOBUTTON,self.OnSortFrgNmb)
        # sort buttons
        self.rbtdst=wx.RadioButton(self.ctcmd1pan,wx.ID_ANY,'distance',pos=(xloc+130,yloc+2)) 
        self.rbtdst.Bind(wx.EVT_RADIOBUTTON,self.OnSortDist)
        self.rbtlrg=wx.RadioButton(self.ctcmd1pan,wx.ID_ANY,'large',pos=(xloc+210,yloc+2))
        self.rbtlrg.Bind(wx.EVT_RADIOBUTTON,self.OnSortLarge)
        self.rbtsml=wx.RadioButton(self.ctcmd1pan,wx.ID_ANY,'small',pos=(xloc+265,yloc+2))
        self.rbtsml.Bind(wx.EVT_RADIOBUTTON,self.OnSortSmall)
        yloc=8
        # separator line
        wx.StaticLine(self.ctcmd1pan,pos=(w-wbtn,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)        
        yloc=8
        # separator line
        wx.StaticLine(self.ctcmd1pan,pos=(w-wbtn,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)        
        # 2d button
        self.tglcld=wx.ToggleButton(self.ctcmd1pan,label='2DGraph',pos=(w-58,yloc),size=(52,18))     
        self.tglcld.Bind(wx.EVT_TOGGLEBUTTON,self.OnOpenChildGraph)
        # molview button
        yloc=35 #30
        self.tglvew=wx.ToggleButton(self.ctcmd1pan,label='MolView',pos=(w-58,yloc),size=(52,18))     
        self.tglvew.Bind(wx.EVT_TOGGLEBUTTON,self.OnMolView)
        self.tglvew.SetValue(self.openremarkwin)
    
        self.SetWidgetStates()

    def CreateMullikenCmdPanel(self):
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        
        hgraph=h-self.hcmdpanel 
        self.graph1d=graph.BarGraph(self.pltpan,-1,self,(0,0),(w,hgraph),'white')

        yloc=h-self.hcmdpanel
        #
        self.mulchgcmdpan=wx.Panel(self.pltpan,wx.ID_ANY,pos=(0,yloc),size=(w,self.hcmdpanel)) #,style=wx.DOUBLE_BORDER)
        self.mulchgcmdpan.SetBackgroundColour("light gray")
        # fragment number selector        
        wx.StaticLine(self.mulchgcmdpan,pos=(0,0),size=(w,2),style=wx.LI_HORIZONTAL)
        st0=wx.StaticText(self.mulchgcmdpan,-1,"Fragment #:",pos=(5,6),size=(70,18))
        self.sclfrg=wx.SpinCtrl(self.mulchgcmdpan,-1,value="1",pos=(78,4),size=(60,20),
                          style=wx.SP_ARROW_KEYS) #,min=1,max=self.nfrg)
        self.sclfrg.Bind(wx.EVT_TEXT,self.OnChangeFragment)
        # plot energy range
        xloc=5; yloc=35 #30
        wx.StaticText(self.mulchgcmdpan,-1,"y.range(+/-):",pos=(xloc,yloc+2),size=(75,18))                  
        self.tclyrng=wx.TextCtrl(self.mulchgcmdpan,-1,"50",pos=(xloc+80,yloc),size=(55,18),
                                style=wx.TE_PROCESS_ENTER)        
        self.tclyrng.Bind(wx.EVT_TEXT_ENTER,self.OnChangeYRange)
        xsep=146
        wx.StaticLine(self.mulchgcmdpan,pos=(xsep,0),size=(2,self.hcmdpanel),style=wx.LI_VERTICAL)
        # PIEDA component
        xloc=155; yloc=8
        wx.StaticText(self.mulchgcmdpan,wx.ID_ANY,'Plot:',pos=(xloc,yloc),size=(30,18))
        self.rbtall=wx.RadioButton(self.mulchgcmdpan,-1,"all",pos=(xloc+35,yloc),style=wx.RB_GROUP)
        self.rbtall.Bind(wx.EVT_RADIOBUTTON,self.OnAll) #MullikenAll)
        self.rbtech=wx.RadioButton(self.mulchgcmdpan,-1,"fragment",pos=(xloc+75,yloc))
        self.rbtech.Bind(wx.EVT_RADIOBUTTON,self.OnEach) #MullikenFragment)
        # n-body
        xloc=315
        wx.StaticText(self.mulchgcmdpan,wx.ID_ANY,'for',pos=(xloc,yloc),size=(30,18))
        xloc=340
        wx.StaticText(self.mulchgcmdpan,wx.ID_ANY,'n-body=',pos=(xloc,yloc),size=(40,18))
        self.rbtmul[0]=wx.RadioButton(self.mulchgcmdpan,-1,"2",pos=(xloc+50,yloc), \
                                  style=wx.RB_GROUP)
        self.rbtmul[0].Bind(wx.EVT_RADIOBUTTON,self.OnMullikenBody)
        self.rbtmul[1]=wx.RadioButton(self.mulchgcmdpan,-1,"2-1",pos=(xloc+85,yloc)) #,size=(40,18))
        self.rbtmul[1].Bind(wx.EVT_RADIOBUTTON,self.OnMullikenBody)
        self.rbtmul[2]=wx.RadioButton(self.mulchgcmdpan,-1,"3",pos=(xloc+130,yloc)) #,size=(50,18))
        self.rbtmul[2].Bind(wx.EVT_RADIOBUTTON,self.OnMullikenBody)
        self.rbtmul[3]=wx.RadioButton(self.mulchgcmdpan,-1,"3-2",pos=(xloc+165,yloc)) #,size=(40,18))
        self.rbtmul[3].Bind(wx.EVT_RADIOBUTTON,self.OnMullikenBody)        
        # separate line 
        wbtn=68 #55
        wx.StaticLine(self.mulchgcmdpan,pos=(0,self.hcmdpanel/2+1),size=(w,2),style=wx.LI_HORIZONTAL)
        # sort
        xloc=155; yloc=35 #30
        wx.StaticText(self.mulchgcmdpan,wx.ID_ANY,'Sort:',pos=(xloc,yloc+2),size=(30,18))
        self.rbtseq=wx.RadioButton(self.mulchgcmdpan,wx.ID_ANY,'fragment #',pos=(xloc+35,yloc+2), \
                               style=wx.RB_GROUP)
        self.rbtseq.Bind(wx.EVT_RADIOBUTTON,self.OnSortFrgNmb)
        #self.rbtseq.SetValue(True)
        self.rbtlrg=wx.RadioButton(self.mulchgcmdpan,wx.ID_ANY,'large',pos=(xloc+135,yloc+2)) 
        self.rbtlrg.Bind(wx.EVT_RADIOBUTTON,self.OnSortLarge)
        self.rbtsml=wx.RadioButton(self.mulchgcmdpan,wx.ID_ANY,'small',pos=(xloc+190,yloc+2))
        self.rbtsml.Bind(wx.EVT_RADIOBUTTON,self.OnSortSmall)
        # 
        yloc=30
        # separator line
        wx.StaticLine(self.mulchgcmdpan,pos=(w-wbtn,yloc-2),size=(2,30),style=wx.LI_VERTICAL)        
        yloc=35 #30
        # molview button
        self.tglvew=wx.ToggleButton(self.mulchgcmdpan,label='MolView',pos=(w-58,yloc),size=(52,18))     
        #self.tglvew.Bind(wx.EVT_TOGGLEBUTTON,self.OnOpenMolViewWin)
        self.tglvew.Bind(wx.EVT_TOGGLEBUTTON,self.OnMolView)
        self.tglvew.SetValue(self.openremarkwin)

        self.SetWidgetStates()
        self.SetMulliknBodyWidget(self.mullbody)
    
    def CreateChildGraphPanel(self):
        self.childgraphwin=wx.Frame(self,-1,pos=(-1,-1),size=self.childgraphsize,
                          style=wx.RESIZE_BORDER|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)
        # menu
        self.menubarchild=self.MenuGraph()
        self.childgraphwin.SetMenuBar(self.menubarchild)
        self.childgraphwin.Bind(wx.EVT_MENU,self.OnMenuChildGraph)
        self.childgraphwin.Bind(wx.EVT_CLOSE,self.OnCloseChildGraph)
        self.childgraphwin.Bind(wx.EVT_SIZE,self.OnSizeChildGraph)
        self.childgraphwin.Bind(wx.EVT_KEY_DOWN,self.OnKeyDownChild)
        #
        size=self.childgraphwin.GetClientSize()
        wplt=size[0]; hplt=size[1]
        # when current graph is 1D, then create 2D as child
        if not self.onedmode:
            self.childgraph=graph.BarGraph(self.childgraphwin,-1,self,(-1,-1),(wplt,hplt),'white')
        else:
            self.childgraph=graph.TileGraph(self.childgraphwin,-1,self,(-1,-1),(wplt,hplt),'white')

    def OnEach(self,event):
        # plot each fragment property
        self.eachfrg=True
        self.sclfrg.Enable()
        self.sortitem=0
        self.rbtseq.SetValue(True)
        if self.pltprp <= 1: self.rbtdst.Enable()
        #if self.ctrlflag.GetCtrlFlag('molviewwin'):
        if self.parent.mdlwin:
            self.parent.model.SetSelectAll(False) 
            mess='Fragmet: '+self.frgnam[self.ifrg-1]
            self.parent.model.Message(mess,0,'black')
        self.iatm=-1
        self.graph.begindata=0
        self.DrawGraph(True)
    
    def OnAll(self,event):
        # plot all components
        self.eachfrg=False
        self.sclfrg.Disable()
        self.sortitem=0
        self.rbtseq.SetValue(True)
        if self.pltprp <= 1: self.rbtdst.Disable()
        self.iatm=-1
        #if self.ctrlflag.GetCtrlFlag('molviewwin'):
        if self.parent.mdlwin:
            self.parent.model.SetSelectAll(False)
            mess='Fragmet: '+self.frgnam[self.ifrg-1]
            self.parent.model.Message(mess,0,'black')
        self.graph.begindata=0
        self.DrawGraph(True)

    def OnAllCompOnOff(self,event):
        on=self.btnall.GetValue()
        #
        for i in range(len(self.piedacmp)):
            if self.activecmp[i]: self.piedacmp[i]=on
        self.SetPIEDAComponentWidget(self.piedacmp)        
        self.DrawGraph(True)

    def OnMullikenBody(self,event):
        for i in range(len(self.mullbody)):
            if self.activemul[i]:
                self.mullbody[i]=self.rbtmul[i].GetValue()
        self.SetMulliknBodyWidget(self.mullbody)
        self.DrawGraph(True)

    def SetMulliknBodyWidget(self,mullbody):
        # set Widget states
        self.mullbody=mullbody
        for i in range(len(self.mullbody)):
            if not self.activemul[i]: self.rbtmul[i].Disable()
            else: self.rbtmul[i].Enable()
        for i in range(len(self.mullbody)):
            if self.activemul[i]: self.rbtmul[i].SetValue(self.mullbody[i])
    
    def OnChangeYRange(self,event):
        value=self.tclyrng.GetValue()
        if value.replace(".","",1).isdigit(): self.yrange=float(value)
        else:
            mess='Wrong input in y.range. value='+str(value)
            dlg=lib.MessageBoxOK(mess,"")
            return
        self.SetYRange(self.yrange)

    def SetYRange(self,yrange):
        self.yrange=yrange
        self.graph.SetYRange(-self.yrange,self.yrange)
        self.SetRankColor()        
        self.DrawGraph(True)
                
    def SetWidgetStates(self):
        # set wedets except PIEDA components which are set in SetPIEDAComponent Widget
        self.sclfrg.SetRange(1,self.nfrg)
        self.sclfrg.SetValue(self.ifrg)
        # each fragment or all
        if self.eachfrg:
            self.rbtech.SetValue(True)
            self.sclfrg.Enable()
            if self.pltprp <= 1: self.rbtdst.Enable()
        else:
            self.rbtall.SetValue(True)
            self.sclfrg.Disable()
            if self.pltprp <= 1: self.rbtdst.Disable()
        # energy range
        txt=str(self.yrange)
        self.tclyrng.SetValue(txt)
        # recover sort option
        if self.sortitem == 0: # sort by fragment
            self.rbtseq.SetValue(True)
        else: self.rbtseq.SetValue(False)
        if self.sortitem == 2: # low energy
            self.rbtlrg.SetValue(True)
        else: self.rbtlrg.SetValue(False)
        if self.sortitem == 3: # high energy   
            self.rbtsml.SetValue(True)
        else: self.rbtsml.SetValue(False)
        
        if self.pltprp == 2: return
        if self.sortitem == 1: # by distance
            self.rbtdst.SetValue(True)
        else: self.rbtdst.SetValue(False)
            
    def OnMolView(self,event):
        on=self.tglvew.GetValue()
        self.MolView(on)
        
    def MolView(self,on):
        #
        self.openremarkwin=on
        self.mdlwin=self.parent.mdlwin
        self.model=self.parent.model
        if not self.mdlwin: return
        #if on and self.ctrlflag.GetCtrlFlag('molviewwin'):
        #    try: self.molview.mdlwin.SetFocus(); return
        #    except: pass
        natm=len(self.model.mol.atm)
        if on:
            if self.mdlwin.openremwin: self.mdlwin.CloseRemarkWin()         
            self.model.ChangeFUMode(1)
            self.model.SaveAtomColor(True)           
            self.mdlwin.SetTitle('fuPlot model viewer:'+self.datnam)
            pansize=[self.wcolpan,self.hcolpan]
            self.mdlwin.SetRemarkPanelSize(pansize)
            #
            self.mdlwin.OpenRemarkWin()
            self.ctrlflag.Set('molviewwin',True)
            self.SetRankColor()
            self.DrawMolView()
            mess='Fragment: '+self.frgnam[self.ifrg-1]
            self.model.Message(mess,0,'black')
            remarkdata=self.MakeRemarkData()
            self.mdlwin.remarkwin.SetRemarkData(remarkdata)
            self.mdlwin.remarkwin.DrawColorRemark()
        else:
            self.ctrlflag.Set('molviewwin',False)
            self.model.ChangeFUMode(0)
            try: self.parent.mdlwin.CloseRemarkWin()
            except: pass
            #self.model.SetSelectAll(False)
            #self.model.SaveAtomColor(False)
            #self.model.DrawMol(True)

    def SelectFragmetAndDrawMolView(self,ifrg,on):
        if not self.openremarkwin: return
        if on:
            frgnam=self.frgnam[ifrg]     
            self.parent.model.SetSelectAll(False)
            self.parent.model.SelectFragNam(frgnam,True,frgnam)
        else:
            self.parent.model.SetSelectAll(False)
            self.DrawMolView()
            
    def DrawMolView(self):
        #if not self.ctrlflag.GetCtrlFlag('molviewwin'): return
        pltcol=self.MakeRankColorData()
        if self.pltprp == 0 or self.pltprp == 1: # pass fragment color
            #self.frgcol=self.pltcol
            funcnam='DrawPlotData'
            self.mdlargs[funcnam]=[True,False,1,pltcol,-1]
            self.parent.model.DrawPlotData(funcnam) #True,False,1,pltcol,-1)
            #self.parent.model.DrawPlotData(True,False,1,pltcol,-1)
        elif self.pltprp == 2: # pass atom color
            #ifrg=self.ifrg
            #if not self.eachfrg: ifrg=-1
            try:
                funcnam='DrawPlotData'
                self.mdlargs[funcnam]=[True,False,0,pltcol,self.ifrg]
                self.parent.model.DrawPlotData(funcnam) #True,False,0,pltcol,self.ifrg)
            except: pass

    def OnOpenChildGraph(self,event):
        self.OpenChildGraph()
        
    def OpenChildGraph(self):
        if self.childgraphstat:
            self.childgraphwin.SetFocus(); return
        
        self.CreateChildGraphPanel()
        ##self.graph=TileGraph(self.childgraph,-1,pos,size,bgcolor)
        self.childgraphwin.Show()
        self.childgraphstat=True
                
        self.DrawGraph(True)

    def OnSortFrgNmb(self,event):
        self.SetSortFrgNmb()
        
    def SetSortFrgNmb(self):
        self.sortitem=0
        self.xstartfrg1d=0
        #self.SortFrgNmb()
        self.DrawGraph(False) # True
    
    def OnSortDist(self,event):
        self.SetSortDist()
        
    def SetSortDist(self):
        self.sortitem=1
        self.xstartfrg1d=0
        #self.SortDist()
        self.DrawGraph(False) #True)
    
    def OnSortLarge(self,event):
        self.SetSortLarge()
        
    def SetSortLarge(self):
        self.sortitem=2
        self.xstartfrg1d=0
        #self.SortLarge()
        self.DrawGraph(False) #True)
    
    def OnSortSmall(self,event):
        self.SetSortSmall()
    
    def SetSortSmall(self):
        self.sortitem=3
        self.xstartfrg1d=0
        #self.SortSmall()
        self.DrawGraph(False) # True)
    
    def SortData(self,pltdat=[]):
        if self.pltargs.has_key('SortData'):
            pltdat=self.pltargs['SortData']
            del self.pltargs['SortData']
        else: pass
        if self.sortitem == 0: 
            self.pltargs['SortDataNmb']=pltdat
            order=self.SortDataNmb([]) #pltdat)
        if self.sortitem == 1: order=self.SortDist()
        if self.sortitem == 2: 
            self.pltargs['SortLarge']=pltdat
            order=self.SortLarge([]) #pltdat)
        if self.sortitem == 3: 
            self.pltargs['SortSmall']=pltdat
            order=self.SortSmall([]) #pltdat)
        #self.ctrlflag.SetCtrlFlag('sortorder',order)
        return order

    def SortDist(self):
        dist=copy.deepcopy(self.frgdist[self.ifrg-1])
        dist.sort(key=lambda x:x[1])
        order=[]
        ndat=len(dist)
        for i in range(ndat): order.append(dist[i][0]-1)
        return order
    
    def SortDataNmb(self,pltdat=[]):
        if self.pltargs.has_key('SortDataNmb'):
            pltdat=self.pltargs['SortDataNmb']
            del self.pltargs['SortDataNmb']
        else: pass
        ndat=len(pltdat)
        order=[]
        for i in range(ndat): order.append(i)
        return order

    def SortLarge(self,pltdat=[]): #pltdat):
        if self.pltargs.has_key('SortLarge'):
            pltdat=self.pltargs['SortLarge']
            del self.pltargs['SortLarge']
        else: pass
        dat=copy.deepcopy(pltdat)
        ndat=len(dat)
        for i in range(ndat): dat[i][0]=i
        order=[]
        dat.sort(key=lambda x:-x[1])
        for i in range(ndat): order.append(dat[i][0])
        return order
    
    def SortSmall(self,pltdat=[]):
        if self.pltargs.has_key('SortSmall'):
            pltdat=self.pltargs['SortSmall']
            del self.pltargs['SortSmall']
        else: pass

        dat=copy.deepcopy(pltdat)
        ndat=len(dat)
        for i in range(ndat): dat[i][0]=i
        order=[]
        dat.sort(key=lambda x:x[1])
        for i in range(ndat): order.append(dat[i][0])
        return order
    
    def MakePIEDABondingEnergyData(self):
        pltdat=[]; ncmp=0
        ncmp=self.GetNumberOfPIEDAComponents()
        nfrg=len(self.fmoprp[0])
        for i in range(nfrg):
            pie=0.0; ob=0.0; sumv=0.0; tmp=[]
            becmp=[0.0,0.0,0.0,0.0] # es,ex,ct,di
            dat=self.fmoprp[i]
            for j in range(nfrg):
                if ncmp == 0: # pie   
                    pie += dat[j][1]
                elif ncmp == 1:
                    if i == j and self.piedacmp[4]: # 1-body
                        ob += dat[j][6]
                    else:
                        for k in range(4): # es,ex,ct,di
                            if self.piedacmp[k]:
                                icmp=k
                                becmp[k] += dat[j][k+2]
                else:
                    try: 
                        for k in range(4):
                            sumv += dat[j][k+2]
                            becmp[k] += dat[j][k+2]
                        if i == j and self.piedacmp[4]: # 1-body
                            ob += dat[j][6]
                    except: pass
            tmp.append(i+1)
            if ncmp == 0: tmp.append(0.5*pie)
            elif ncmp == 1:
                if self.piedacmp[4]: tmp.append(ob)
                else: tmp.append(0.5*becmp[icmp])
            else:
                sumv *= 0.5
                if self.piedacmp[4]: sumv += ob
                tmp.append(sumv)
                for k in range(4):
                    if self.piedacmp[k]: tmp.append(0.5*becmp[k])
                if self.piedacmp[4]: tmp.append(ob)
            pltdat.append(tmp)
        return pltdat   

    def SetPIEDAComponentWidget(self,piedacmp):
        # set Widget states
        self.piedacmp=piedacmp
        #if self.pltprp == 0:
        for i in range(len(self.piedacmp)):
            if not self.activecmp[i]: self.ckbcmp[i].Disable()
            else: self.ckbcmp[i].Enable()
        for i in range(len(self.piedacmp)):
            if self.activecmp[i]: self.ckbcmp[i].SetValue(self.piedacmp[i])

    def OnPIEDAComponent(self,event):
        for i in range(len(self.piedacmp)):
            if self.activecmp[i]: self.piedacmp[i]=self.ckbcmp[i].GetValue()
        self.SetPIEDAComponentWidget(self.piedacmp)
        self.DrawGraph(True)
         
    def OnMenuGraph(self,event):
        # Menu event handler
        menuid=event.GetId()
        menuitem=self.menubarplot.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        #bChecked=self.plotmenu.IsChecked(menuid)
        if item == "Save bitmap":
            filename=""; wcard='bmp(*.bmp)|*.bmp'
            filename=lib.GetFileName(self,wcard,"w",True,"")
            if len(filename) < 0: return
            lib.SaveBitmapAsFile(filename,self.graph.buffer)
            
        if item == "*Print bitmap":
            self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
            dc=wx.BufferedDC(None,self.buffer)
            dc.Clear()
        
        if item == "Quit":
            self.OnClose(0)
        if item == "Copy bitmap":
            lib.CopyBitmapToClipboad(self.graph.buffer)
            
        if item == "Clear clipboard":
            wx.TheClipboard.Clear()
        # data
        if item == "Extract":
            # >0.3, <-0.5
            value=wx.GetTextFromUser('Enter threshold values',
                        caption='Extract data',parent=self,default_value='>1.0')
            value=value.strip()
            if len(value) <= 0: return
            items=value.split(',',1); lg=False; sm=False
            for i in range(len(items)):
                items[i].strip()
                if items[i][:1] == '>': 
                    self.larger=float(items[i][1:].strip()); lg=True
                elif items[i][:1] == '<': 
                    self.smaller=float(items[i][1:].strip()); sm=True
                    
                else: print 'input error',value
            
            if sm: print 'smaller',self.smaller
            if lg: print 'larger',self.larger
            if self.pltprp == 0: # pieda
                if sm: # smaller value is set
                    pass
                if lg: # larger value is set
                    pass
                pass
            elif self.pltprp == 1: # ctcharge
                """ code not completed. 13Jul2014 (kk)"""
                self.ExtractCTChargeData(sm,lg)
                self.ifrg=1
                self.DrawGraph(True)

        if item == "Restore":
            if len(self.savfmoprp):
                self.fmoprp=self.savfmoprp
    
    def ExtractCTChargeData(self,small,large):
        """ not completed """
        if small:
            pass
            
        if large:
            print 'extract self.larger',self.larger
            nfrg=-1; fmoprp=[]; order=[]; frgdist=[]; ndat=0
            for i in range(nfrg):
                tmp=[]
                for j in range(nfrg):
                    ndat=0
                    for k in range(len(self.fmoprp[i][j])):
                        if self.fmoprp[i][j][k][1] > self.larger:
                            ndat += 1; tmp.append([ndat,self.fmoprp[i][j][k][1]])
                            if i == 0 and j == 0:
                                order.append(self.order[j])
                                frgdist.append(self.frgdist[i][j])
                fmoprp.append(tmp)
            ndat=len(order)
            if ndat <= 0:
                print 'no data after extract. neglected the command.'
                return
            self.nfrg=ndat
            self.order=order
            self.frgdist=frgdist
            self.fmoprp=fmoprp
            
    def SavePIEDAData(self,on):
        if on:
            self.savfmoprp=self.fmoprp
            self.savorder=self.order
            self.savfrgdist=self.frgdist
            self.savnfrg=self.nfrg
            self.savnatm=self.natm
        else:
            if len(self.savfmoprp):
                self.fmoprp=self.savfmoprp; self.savfmoprp=[]
                self.order=self.savorder; self.savorder=[]
                self.frgdist=self.savfrgdist; self.savfrgdist=[]
                self.nfrg=self.savnfrg; self.savnfrg=-1
                self.natm=self.savnatm; self.savnatm=-1
            else:
                print 'no data to recover'
            
                    
    def OnMenuChildGraph(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.childmenu.GetLabel(menuid)
        bChecked=self.childmenu.IsChecked(menuid)
        if item == "Save bitmap":
            filename=""; wcard='bmp(*.bmp)|*.bmp'
            filename=lib.GetFileName(self,wcard,"w",True,"")
            if len(filename) < 0: return
            lib.SaveBitmapAsFile(filename,self.childgraph.buffer)
        
        if item == "*Print bitmap":
            self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
            dc=wx.BufferedDC(None,self.buffer)
            dc.Clear()
        
        if item == "Quit":
            self.OnClose(0)
        
        if item == "Copy bitmap":
            lib.CopyBitmapToClipboad(self.childgraph.buffer)
        
        if item == "Clear clipboard":
            wx.TheClipboard.Clear()

    def SetRankColor(self):
        posicol=const.HSVCol['red'] #red']
        negacol=const.HSVCol['blue'] #blue'] 
        self.extcolorposi=lib.HSVtoRGB(const.HSVCol['magenta'])
        self.extcolornega=lib.HSVtoRGB(const.HSVCol['cyan']) #['cyan'])
        rankposi=self.rankposi; ranknega=self.ranknega
        
        self.rankcolorposi=[]; self.rankcolornega=[]
        # rank color for positive value:  red -> white
        if rankposi > 0: 
            grad=1.0/float(rankposi)
            for i in range(rankposi):
                col=list(posicol)
                col[1]=0.9-grad*(ranknega-i) + 0.1
                self.rankcolorposi.append(lib.HSVtoRGB(col))
        # rank color for negative  value: white -> blue
        if ranknega > 0: 
            grad=1.0/float(ranknega)
            for i in range(ranknega):
                col=list(negacol)
                col[1]=0.9-grad*(ranknega-i) + 0.1       
                self.rankcolornega.append(lib.HSVtoRGB(col))

    def MakeRankColorData(self):
    
        pltcol=[]
        # note: color code in main window is different!
        curcol=const.RGBColor255['yellow']
        concol=const.RGBColor255['darkkhaki']
        # plot data
        self.extposivalue=0.0
        self.extnegavalue=0.0
        maxval=-1000000.0; minval=1000000.0

        if self.pltprp <= 1: # pieda, ctcharge
            for i in range(len(self.pltdat)):
                val=0.0
                val=self.pltdat[i][1]
                if self.eachfrg:
                    if self.ifrg == self.pltdat[i][0]:
                        pltcol.append(curcol); continue
                    elif self.frgdist[i][self.ifrg-1][1] < 0.001:
                        pltcol.append(concol); continue
                col=self.GetRankColor(val)
                pltcol.append(col)
                if val > maxval: maxval=val
                if val < minval: minval=val
        
        if self.pltprp == 2: # mulliken population
            for i in range(self.natm):
                val=0.0
                col=const.RGBColor255['white'] 
                pltcol.append(col)
            for i in range(len(self.pltdat)):
                val=self.pltdat[i][1]
                ii=self.pltdat[i][0]-1
                pltcol[ii]=self.GetRankColor(val)
                if val > maxval: maxval=val
                if val < minval: minval=val
            if self.iatm > 0 : pltcol[self.iatm-1]=const.RGBColor255['green']
        if maxval > self.yrange: self.extposivalue=maxval
        if minval < -self.yrange: self.extnegavalue=minval
        
        return pltcol
                              
    def GetRankColor(self,value):
        # return energy rank color        
        vunit=self.yrange/self.rankposi
        if value >= 0:
            rank=int(value/vunit)
            if rank > self.rankposi-1:
                color=self.extcolorposi
            else: color=self.rankcolorposi[rank]
        else:
            rank=int(abs(value)/vunit)
            if rank < 0 or rank > self.ranknega-1:
                color=self.extcolornega
            else: color=self.rankcolornega[rank]
        
        return color
                   
    def OnChangeFragment(self,event):
        # change fragment event handler
        if self.nfrg <= 0: return
        #
        #if not self.ctrlflag.GetCtrlFlag('busy'): return
        self.ifrg=self.sclfrg.GetValue()      
        if self.ifrg > self.nfrg: self.ifrg=self.nfrg
        if self.ifrg <= 0: self.ifrg=1
        self.ChangeFragment(self.ifrg)
        
    def ChangeFragment(self,ifrg):
        #self.sclfrg.Disable()
        #        
        #if self.ctrlflag.GetCtrlFlag('molviewwin'):
        #    mess='Fragment: '+self.frgnam[self.ifrg-1]
        #    self.molview.Message(mess,0,'black')
        #    self.molview.SetSelectAll(False)        
        if self.nfrg <= 0: return
        self.ifrg=ifrg
        self.sclfrg.SetValue(ifrg)  
        #
        self.iatm=-1
        #self.DrawGraph(True)
        #if self.ctrlflag.GetCtrlFlag('molviewwin'):
        if self.parent.mdlwin:
            frgnam=self.frgnam[self.ifrg-1]
            mess='Fragment: '+frgnam
            self.parent.model.Message(mess,0,'black')
            self.parent.model.SetSelectAll(False) 
            self.parent.model.frag.SelectFragmentByName(frgnam,True)
        self.DrawGraph(True)
        self.sclfrg.Enable()
            
    def SetPIEDAProperty(self,pltprp,datnam,molint,piedacmp,mullbody):
        # 
        self.pltprp=pltprp
        self.molint=molint
        self.datnam=datnam
        self.activecmp=piedacmp[:]
        self.activemul=mullbody
        self.piedacmp=piedacmp
        if self.pltprp == 0: # pie or pieda
            self.yrange=50.0
            if self.molint: self.yrange=5.0
            self.SetPIEDAComponentWidget(self.piedacmp)
        if self.pltprp == 1: # ct charge
            self.yrange=0.5
            if self.molint: self.yrange=0.02
        if self.pltprp == 2: # mulliken charge
            self.yrange=0.5
            if self.molint: self.yrange=0.02
            self.SetMulliknBodyWidget(self.mullbody)
        self.graph.SetYRange(-self.yrange,self.yrange)
        self.tclyrng.SetValue(str(self.yrange))        
        
        self.SetRankColor()
        #if self.pltprp == 0: self.SetPIEDAComponentWidget(self.piedacmp)
        #if self.pltprp == 2: self.SetMulliknBodyWidget(self.mullbody)

    def SetPIEDAData(self,natm,nfrg,frgnam=[],fmoprp=[],frgdist=[]):
        if self.pltargs.has_key('SetPIEDAData'):
            [frgnam,fmoprp,frgdist]=self.pltargs['SetPIEDAData']
            del self.pltargs['SetPIEDAData']
        else: pass
        self.natm=natm
        self.nfrg=nfrg
        self.order=[]
        for i in range(self.nfrg): self.order.append(i)
        self.frgnam=frgnam
        self.fmoprp=fmoprp
        self.frgdist=frgdist
        #self.nfrg=len(self.frgnam)
        self.sclfrg.SetRange(1,self.nfrg)
        self.ifrg=1
        self.sclfrg.SetValue(self.ifrg)
        self.rbtseq.SetValue(True)
                
    def SetMolViewFragmentData(self,pdbfile,indat,bdabaa):
        self.pdbfile=pdbfile
        self.bdabaa=bdabaa
        self.indat=indat
        
    def DrawGraph(self,redrawmol):
        if self.nfrg <= 0: return
        #mac# if self.sclfrg: self.sclfrg.SetValue(self.ifrg)
        self.tclyrng.SetValue(str(self.yrange))
        xlab='fragment number'; xlab1='atom number'
        if self.pltprp == 0:
            ftitle='Plot PIEDA: '; gtitle='PIE/PIEDA: '; ylab='Energy (kcal/mol)'
            childtitle='2D PIE/PIEDA'; rem='kcal/mol'
        if self.pltprp ==1:
            ftitle='Plot CT Charge'; gtitle='CT Charge: '; ylab='Charge (a.u.)'
            ctitle='2D CT Charge'; rem='     a.u.'
        if self.pltprp ==2:
            ftitle='Plot Mullike Charge'; gtitle='Mulliken Charge: '; ylab='Charge (a.u.)'
            ctitle='2D Mulliken Charge'; rem='     a.u.'; xlab=xlab1
        if self.molint: gtitle='[MI] '+gtitle    
        #if self.pltprp <= 2: # pie/pieda and ct charge plot
        #test=True
        #if test:    
        self.SetTitle(ftitle+self.datnam)
        if self.pltprp ==0:
            if self.eachfrg: pltdat=self.MakeFragmentPIEDAData(self.ifrg) #self.MakeFragmentData(self.ifrg)
            else: pltdat=self.MakePIEDABondingEnergyData() #MakeAllPIEDAData()
        if self.pltprp ==1:
            if self.eachfrg: pltdat=self.MakeFragmentCTChargeData(self.ifrg)
            else: pltdat=self.MakeAllCTChergeData()
        if self.pltprp == 2:
            if self.eachfrg: pltdat=self.MakeFragmentMullikenData(self.ifrg)
            else: pltdat=self.MakeAllMullikenData()
        if self.eachfrg and self.pltprp !=2: distinfo=self.MakeDistanceInfo()
        self.pltargs['SortData']=pltdat
        self.order=self.SortData([]) # pltdat)
        order=self.order
        
        self.pltdat=pltdat
        # remarks
        if self.pltprp == 0:
            remarkbox=[8,8]
            self.pltargs['MakePIEDARemarkList']=self.pltdat
            remarklist=self.MakePIEDARemarkList([]) #self.pltdat)
            self.graph.SetRemark(remarkbox,remarklist)
        #order=self.order
        name='All'
        if self.pltprp == 0: name='BE'
        if self.eachfrg: name=self.frgnam[self.ifrg-1] 
        self.graph.SetTitle(gtitle+name) #self.frgnam[self.ifrg-1])
        self.graph.SetAxisLabel(xlab,ylab)
        self.graph.SetYRange(-self.yrange,self.yrange)
        self.graph.SetData(self.pltdat,self.order)
        if self.eachfrg and self.pltprp !=2: self.graph.SetAdditionalInfo(distinfo)
        else: self.graph.SetAdditionalInfo([])

        self.graph.Plot(True)
        
        if self.childgraphstat:    
            self.childgraphwin.SetTitle(ftitle+self.datnam)
            pltdat=self.MakeDataFor2D() #self.MakePIEDAData2D()
            #if self.pltprp == 1: self.MakeCTChargeData2D()
            #order=self.ctrlflag.GetCtrlFlag('sortorder')
            self.childgraph.SetTitle(gtitle)
            xlab='fragment number'; ylab='fragment number'
            self.childgraph.SetAxisLabel(xlab,ylab)
            self.childgraph.SetYRange(-self.yrange,self.yrange)
            self.childgraph.SetData(pltdat,[])
            self.childgraph.SetRemarkTitle(rem)
            self.childgraph.SetFocus(self.ifrg) # draw border with thick line for data "1"
        
            #self.Refresh()
            #self.Update()
            
            self.childgraph.Plot(True)
        # draw molview
        if redrawmol and self.parent.mdlwin.remarkwin: #self.ctrlflag.GetCtrlFlag('molviewwin'):
            self.ctrlflag.Set('busy',True)
            self.DrawMolView() 
            #if const.SYSTEM == const.WINDOWS:
            remarkdata=self.MakeRemarkData()
            self.parent.mdlwin.remarkwin.SetRemarkData(remarkdata)
            self.parent.mdlwin.remarkwin.DrawColorRemark()
            self.ctrlflag.Set('busy',False)
            
    def MakeRemarkData(self):
        textcol='yellow'
        rem='PIEDA'
        if self.pltprp == 1: rem='CT charge'
        if self.pltprp == 2: rem='Mulliken'
        wcolorbox=10
        hcolorbox=8
        remarkdata=[rem,0,0,self.wcolpan,self.hcolpan,
                    self.font,textcol,"black",wcolorbox,hcolorbox,
                    self.rankposi,self.ranknega,self.yrange,self.extposivalue,self.extnegavalue,
                    self.rankcolorposi,self.rankcolornega,self.extcolorposi,self.extcolornega]
        return remarkdata

    def MakeGraphValueMess(self,idat):
        mess='Fragmet: '+self.frgnam[self.ifrg-1]
        if idat < 0: return mess
        if self.pltprp == 2: # mulliken
            if not self.eachfrg:
                selfrg=self.parent.model.mol.atm[idat-1].frgnam
                mess='Fragmet: '+selfrg            
            atmseq=self.pltdat[idat][0]
            mess=mess+", selected atom="+str(atmseq)+', charge='+('%6.3f' % self.pltdat[idat][1])
        else: # pieda and ctcharge
            selfrg=self.frgnam[idat]
            if self.eachfrg:
                mess=mess+", selected="+selfrg+', value=['
            else: mess='Fragment: '+selfrg+', data['
            fmt='%6.2f'
            if self.pltprp == 1: fmt='%7.3f'
            for j in range(1,len(self.pltdat[idat])):
                mess=mess+fmt % self.pltdat[idat][j]
            mess=mess+']'
            if self.eachfrg: mess=mess+', r='+'%6.2f' % self.frgdist[self.ifrg-1][idat][1]
        return mess
    
    def MakeDistanceInfo(self):
        distinfo=[]
        for i in range(len(self.frgdist[self.ifrg-1])):
            info=', r='+'%6.2f' % self.frgdist[self.ifrg-1][i][1]
            distinfo.append(info)
        return distinfo
    
    def MakePIEDARemarkList(self,pltdat):
        if self.pltargs.has_key('MakePIEDARemarkList'):
            pltdat=self.pltargs['MakePIEDARemarkList']
            del self.pltargs['MakePIEDARemarkList']
        else: pass
        c1=const.RGBColor255['gray'] #['black']
        c2=const.RGBColor255['gold'] #['yellow']
        c3=const.RGBColor255['red']
        c4=const.RGBColor255['green']
        c5=const.RGBColor255['blue'] #magenta']
        c6=const.RGBColor255['white']
        itemlist=[['tot',c1],['es',c2],['ex',c3],['ctmix',c4],['di',c5],
                  ['1b',c6]] 
        lst=[]
        ncmp=self.GetNumberOfPIEDAComponents()
        if ncmp <= 1:
            lst.append(itemlist[0])
        else:
            lst.append(itemlist[0])
            for i in range(len(self.piedacmp)):
                if self.piedacmp[i]: lst.append(itemlist[i+1])
        return lst
           
    def MakeDataFor2D(self):
        pltdat2d=[] # [[[i,val,code],..],[[...]],...]
        for i in range(self.nfrg):
            if self.pltprp == 0: dat=self.MakeFragmentPIEDAData(i+1)
            if self.pltprp == 1: dat=self.MakeFragmentCTChargeData(i+1)
            tmpi=[]
            for j in range(self.nfrg):
                tmp=[]; tmp.append(dat[j][0]); tmp.append(dat[j][1])
                tmpi.append(tmp)
            pltdat2d.append(tmpi)

        for i in range(self.nfrg):
            dist=self.frgdist[i]
            for j in range(self.nfrg):
                pltdat2d[i][j]=pltdat2d[i][j]+[0]
                if self.molint: continue
                if self.pltprp == 0 and dist[j][1] < 0.00001:
                    pltdat2d[i][j][2]=2 
                if i == j: pltdat2d[i][j][2]=1 
                
        return pltdat2d
    
    def MakeFragmentCTChargeData(self,ifrg):
        fmoprp=self.fmoprp[ifrg-1]
        pltdat=copy.deepcopy(fmoprp)
        #if self.pltprp == 0:
        #    pltdat=self.MakeFragmentPIEDAData(pltdat)
        if self.pltprp == 2: pltdat=self.MakeMullBodyData(pltdat) # mulliken charge
        return pltdat

    def MakeFragmentPIEDAData(self,ifrg):
        pltdat=[]; ncmp=0
        ncmp=self.GetNumberOfPIEDAComponents()
        dat=copy.deepcopy(self.fmoprp[ifrg-1])
        ndat=len(dat)
        if ncmp == 0:
            for i in range(ndat):
                tmp=[]
                tmp.append(dat[i][0])
                tmp.append(dat[i][1])
                pltdat.append(tmp)
        elif ncmp == 1:
            icmp=0
            for i in range(len(self.piedacmp)):
                if self.piedacmp[i]:
                    icmp=i; break
            for i in range(ndat):
                tmp=[]
                tmp.append(dat[i][0])
                tmp.append(dat[i][icmp+2])
                #for j in range(2,len(dat[i])):
                #    if self.piedacmp[j-2]: tmp.append(dat[i][j])
                pltdat.append(tmp)  
        else:
            for i in range(ndat):
                tmp=[]; sumv=0.0
                tmp.append(dat[i][0])
                tmp.append(0.0)
                for j in range(2,len(dat[i])):
                    if self.piedacmp[j-2]:
                        sumv += dat[i][j]
                        tmp.append(dat[i][j])
                tmp[1]=sumv
                pltdat.append(tmp)
        return pltdat
    
    def GetNumberOfPIEDAComponents(self):
        ncmp=0
        for i in range(len(self.piedacmp)):
            if self.piedacmp[i]: ncmp += 1
        return ncmp
        
    def MakeFragmentMullikenData(self,ifrg):
        pltdat=[]
        for i in range(len(self.rbtmul)):
            self.mullbody[i]=self.rbtmul[i].GetValue()    
        fmoprp=copy.deepcopy(self.fmoprp[ifrg-1])
 
        for i in range(len(fmoprp)):
            tmp=[]
            tmp.append(fmoprp[i][0])
            if self.mullbody[0]: tmp.append(fmoprp[i][2])
            if self.mullbody[1]: tmp.append(fmoprp[i][2]-fmoprp[i][1])
            if self.mullbody[2]: tmp.append(fmoprp[i][3])
            if self.mullbody[3]: tmp.append(fmoprp[i][3]-fmoprp[i][2])
            pltdat.append(tmp)

        return pltdat

    def MakeAllMullikenData(self):
        # make plot data for all mulliken charge, all atoms.
        pltdat=[]
        for i in range(self.nfrg):
            #pltdat=self.MakeMullBodyData(pltdat)
            dat=self.MakeFragmentMullikenData(i+1)
            pltdat=pltdat+dat
        pltdat.sort(key=lambda x:x[0])
        #print pltdat
        return pltdat
    
    def MakeAllCTChergeData(self):
        # make plot data for all ct charge
        pltdat=[]
        for i in range(self.nfrg):
            chg=0.0; tmpi=[]
            for j in range(self.nfrg):
                chg += self.fmoprp[i][j][1]

            tmpi.append(i+1); tmpi.append(chg)
            pltdat.append(tmpi)            
        return pltdat

    def PrintData(self,idat):
        # print idat-th data in graph
        dat=str(idat-1)
        if idat > len(self.pltdat) or idat <= 0:
            self.parent.RunMethod("print 'data number out of range.'")
            return 
        name=self.graphname[self.pltprp]
        self.parent.RunMethod("print fuplt.graph['"+name+"'].pltdat["+dat+"]")
    
    def PrintMaxData(self):
        # print maximum value in graph
        name=self.graphname[self.pltprp]
        maxval=self.pltdat[0][1]
        idat=0
        for i in range(len(self.pltdat)):
            if self.pltdat[i][1] > maxval:
                maxval=self.pltdat[i][1]; idat=i
        dat=str(idat)
        self.parent.RunMethod("print fuplt.graph['"+name+"'].pltdat["+dat+"]")
    
    def PrintMinData(self):
        # print minimum value in graph
        name=self.graphname[self.pltprp]
        minval=self.pltdat[0][1]
        idat=0
        for i in range(len(self.pltdat)):
            if self.pltdat[i][1] < minval:
                minval=self.pltdat[i][1]; idat=i
        dat=str(idat)
        self.parent.RunMethod("print fuplt.graph['"+name+"'].pltdat["+dat+"]")
    
    def OnFocus(self,event):
        self.SetFocus()
        #self.DrawGraph(True)
    def OnPaint(self,event):
        wx.PaintDC(self.graph)
        self.graph.Refresh()
        self.graph.Update()
    
    def OnMove(self,event):
        print 'OnMove'
        return
        self.DrawGraph(False)
                   
    def OnSize(self,event):
        # Size handler
        self.Resize()
        
    def Resize(self):
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        self.pltpan.Destroy()
        self.CreateGraphPanel()
        self.DrawGraph(True) #False)
        
    def OnSizeChildGraph(self,event):
        self.ResizeChildGraph()
    
    def ResizeChildGraph(self):
        if not self.childgraphstat: return
        self.childgraph.Destroy()
        size=self.childgraphwin.GetClientSize() 
        wplt=size[0]; hplt=size[1]
        # when current graph is 1D, then create 2D as child
        if not self.onedmode:
            self.childgraph=graph.BarGraph(self.childgraphwin,-1,self,(0,0),(wplt,hplt),'white')
        else:
            self.childgraph=graph.TileGraph(self.childgraphwin,-1,self,(0,0),(wplt,hplt),'white')
        
        self.DrawGraph(True) #False) #True)
    
    def MouseLeftClick(self,pos):
        if not self.ctrlflag.GetCtrlFlag('molviewwin'): return
        if self.onedmode:
            self.iatm=-1
            i=self.graph.GetXValue(pos)
            if i < 0:
                mess='Clicked at outside of plot region.'
                self.parent.model.Message(mess,0,'black')
                return
            if i >= 0 and i <= len(self.pltdat):
                self.SetClickDataForMolView(i)
                
    def SetClickDataForMolView(self,i):
        i=int(i); ii=self.order[i]
        #if i >= 0 and i <= len(self.pltdat):
        #    if self.ctrlflag.GetCtrlFlag('molviewwin'):
        self.parent.model.SetSelectAll(False)
        mess=self.MakeGraphValueMess(ii)
        if self.pltprp == 2:
            self.iatm=self.pltdat[ii][0]
            self.parent.model.SetSelectedAtom(self.iatm-1,True)
        else:    
            frgnam=self.frgnam[ii]
            self.parent.model.SelectFragNam(frgnam,True)

        self.parent.model.Message(mess,0,'black')
        self.DraMolView()
    
    def OnClose(self,event):
        # set ctrlflag False and destroy graph panel
        self.Close()

    def Close(self):
        name=self.graphname[self.pltprp]
        try:
            self.ctrlflag.Set(name,False)
            self.ctrlflag.Set('molviewwin',False)
            self.ctrlflag.Set('controlpanel',False)
        except: pass
        try: self.parent.mdlwin.CloseRemarkWin()
        except: pass
        try: 
            self.parent.model.SaveAtomColor(False)
            self.parent.model.DrawMol(True)
        except: pass

        self.Destroy()
        
    def OnCloseChildGraph(self,event):
        # set flag False and destroy child graph panel
        if self.childgraphstat:
            self.childgraphstat=False
            self.childgraphwin.Destroy()
         
    def MenuGraph(self):
        # Menu items
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        submenu.Append(-1,"Save bitmap","Save bitmap on file")
        submenu.Append(-1,"*Print bitmap","Unfinished")
        submenu.Append(-1,"Quit","Close plot panel")
        menubar.Append(submenu,'File')
        # Edit
        submenu=wx.Menu()
        submenu.Append(-1,"Copy bitmap","Copy graph in clipboard.")
        submenu.Append(-1,"Clear clipboard","Clear clipboard")
        menubar.Append(submenu,'Edit')
        # Data
        submenu=wx.Menu()
        submenu.Append(-1,"Extract","Extract")
        menubar.Append(submenu,'Data')
        return menubar        

global fum
fup = Plot(fum.mdlwin,-1)

"""
#----------------------------------------
def start():
    app = wx.App(False)
    #const.SYSTEM=const.GetSYSTEM() #=lib.GetSystemInfo()
    #const.fup = Plot(None,-1,[0,0],'FU Plot')
    #const.fup.Show(True)
    fup = Plot(None,-1,[0,0],'FU Plot')
    fup.Show()
    app.MainLoop()

if __name__ == '__main__':
    app = wx.App(False)
    start()
    app.MainLoop()          
"""
