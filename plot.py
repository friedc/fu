#!/bin/sh
# -*- coding:utf-8

import sys
sys.path.insert(0,'.')

import os
import copy
import wxversion
wxversion.select("2.8")
import wx
import wx.py.crust
#import psutil

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

class Plot(wx.Frame):
    # main program for draw FMO property graphs
    def __init__(self,parent,id,winpos,winlabel):
        winsize=lib.WinSize((390,275))
        #print 'SYSTEM',const.SYSTEM
        #if const.SYSTEM != const.WINDOWS: winsize=(400,300)
        self.title='FMO Viewer'
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
        #
        """ parent=None, model=None"""
        self.mdlwin=None
        self.model=None
        """   """
        self.draw=None
        
        self.platform=lib.GetPlatform()        
        self.winsize=winsize
        
        self.font=self.GetFont()
        self.font.SetPointSize(8)
        self.SetFont(self.font)

        self.program='fuplot.exe'
        self.inifile='fuplot.ini'
        # program directory
        self.exedir=lib.GetExeDir(self.program)
        # change directory
        #???self.curdir=lib.ChangeToPreviousDir(self.exedir,self.inifile)
        self.curdir=os.getcwd()
        # CtrlFlag instance
        self.ctrlflag=ctrl.CtrlFlag()
        # set Icon
        #iconfile=lib.GetIconFile(self.exedir,"fuplot.ico") 
        #if os.path.exists(iconfile):
        #    icon=wx.Icon(iconfile,wx.BITMAP_TYPE_ICO)
        #    self.SetIcon(icon)
        #
        size=self.GetClientSize()
        self.sashposition=size[0]/2
        #
        self.addmode=True
        self.datadic={}
              
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        self.bgcolor="white"
        self.SetBackgroundColour(self.bgcolor) 
        # Create Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.datnam=''
        self.pltprp=-1
        #self.molint=False
        self.piedadat=[]
        self.onebody=[]
        self.frgnam=[]
        self.mulcharge=[]
        self.ctcharge=[]
        # files
        self.openfiles=[]
        self.fileout=[]
        self.fileinp=[]
        self.filepdb=[]
        #
        self.graphnam=[]
        
        
        self.graph={}
        self.idmax=0
        self.fmodatadic={}
        self.drvdatadic={}
        #
        self.datalist=[]
        self.selected=''
        
        self.opendrvpan=False
        self.drvpan=None

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
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def CreatePropertyPanel(self):
        # create property choice panel on right hand side
        [w,h]=self.GetClientSize() #self.GetSize()
        xsize=w/2-25; ysize=h
        hcb=const.HCBOX
        #width=w/2-20; height=h
        xpos=w/2; ypos=0
        xloc=10; yloc=10
        self.prppan=wx.Panel(self,-1,pos=(xpos,ypos),size=(w/2,h)) #ysize))
        self.prppan.SetBackgroundColour("light gray")

        wx.StaticText(self.prppan,wx.ID_ANY,'Selected data for plot',pos=(xloc,yloc),size=(150,20)) 
        yloc += 20
        self.tcsel=wx.TextCtrl(self.prppan,-1,"",pos=(xloc,yloc),size=(xsize,20),
                               style=wx.TE_READONLY|wx.TE_MULTILINE) #|wx.HSCROLL) 
        #self.tclsel.Bind(wx.EVT_TEXT_ENTER,self.OnSelected)       
        self.tcsel.SetToolTipString('Data for plot')
        """self.WriteRemark()"""
        yloc += 30
        wx.StaticText(self.prppan,wx.ID_ANY,'Computational details',pos=(xloc,yloc),size=(140,20))
        self.btndetail=wx.Button(self.prppan,wx.ID_ANY,"View",pos=(xloc+135,yloc-2),size=(40,18))
        self.btndetail.Bind(wx.EVT_BUTTON,self.OnViewDetails)
        self.btndetail.SetToolTipString('View FMO options')
        yloc += 20
        wx.StaticText(self.prppan,wx.ID_ANY,'Total properties',pos=(xloc,yloc),size=(140,20))
        self.btnresult=wx.Button(self.prppan,wx.ID_ANY,"View",pos=(xloc+135,yloc),size=(40,18))
        self.btnresult.Bind(wx.EVT_BUTTON,self.OnViewResults)
        self.btnresult.SetToolTipString('View FMO results')
        
        xloc1=xloc+100
        yloc += 20
        wx.StaticText(self.prppan,wx.ID_ANY,'Plot FMO property',pos=(xloc,yloc),size=(100,20))
        yloc += 20
        self.cbprop=wx.ComboBox(self.prppan,-1,'',choices=[], \
                               pos=(xloc+10,yloc-3), size=(115,hcb),style=wx.CB_READONLY)             
        self.cbprop.Bind(wx.EVT_COMBOBOX,self.OnPlotFMOProp)
        self.cbprop.SetToolTipString('Choose FMO property to plot')
        self.btnviewprop=wx.Button(self.prppan,wx.ID_ANY,"View",pos=(xloc+135,yloc-2),size=(40,20))
        self.btnviewprop.Bind(wx.EVT_BUTTON,self.OnViewFMOProp)
        self.btnviewprop.SetToolTipString('View property by editor')
        yloc += 25
        self.btnplt=wx.Button(self.prppan,wx.ID_ANY,"Plot",pos=(40,yloc),size=(40,20))
        self.btnplt.Bind(wx.EVT_BUTTON,self.OnPlotFMOProp)
        self.btnplt.SetToolTipString('Plot property')
        self.btncls=wx.Button(self.prppan,wx.ID_ANY,"Close",pos=(100,yloc),size=(50,20))
        self.btncls.Bind(wx.EVT_BUTTON,self.OnCloseFMOProp)
        self.btncls.SetToolTipString('Close plot')

        
        """
        
        
        self.btnpie=wx.Button(self.prppan,wx.ID_ANY,"PIE/PIEDA",pos=(xloc+10,yloc),size=(75,20))
        self.btnpie.Bind(wx.EVT_BUTTON,self.OnPIE)
        self.btnpie.SetToolTipString('Plot PIE/PIEDA')
        self.btnctc=wx.Button(self.prppan,wx.ID_ANY,"CT charge",pos=(xloc1,yloc),size=(75,20))
        self.btnctc.Bind(wx.EVT_BUTTON,self.OnCTCharge)
        self.btnctc.SetToolTipString('Plot transfered charge in dimer')        
        #self.ckbpie=wx.CheckBox(self.prppan,-1,"PIE/PIEDA",pos=(xloc+5,yloc),size=(80,18))
        #self.ckbpie.SetValue(True)
        #self.ckbctc=wx.CheckBox(self.prppan,-1,"CT charge",pos=(xloc1,yloc),size=(80,18))
        yloc += 25
        self.btnmul=wx.Button(self.prppan,wx.ID_ANY,"Mulliken",pos=(xloc+10,yloc),size=(75,20))
        self.btnmul.Bind(wx.EVT_BUTTON,self.OnMulliken)
        self.btnmul.SetToolTipString('Plot Mulliken charge')
        self.btnmep=wx.Button(self.prppan,wx.ID_ANY,"MEP(ptc)",pos=(xloc1,yloc),size=(75,20))
        self.btnmep.Bind(wx.EVT_BUTTON,self.OnMEP)
        self.btnmep.SetToolTipString('Plot point charge eletrostatic potential')
        #self.ckbmul=wx.CheckBox(self.prppan,-1,"Mulliken",pos=(xloc+5,yloc),size=(80,18))
        #self.ckbesp=wx.CheckBox(self.prppan,-1,"MEP",pos=(xloc1,yloc),size=(80,18))
        #self.ckbesp.Disable()
        yloc += 25
        self.btnden=wx.Button(self.prppan,wx.ID_ANY,"Density",pos=(xloc+10,yloc),size=(75,20))
        self.btnden.Bind(wx.EVT_BUTTON,self.OnDensity)
        self.btnden.SetToolTipString('Plot density ditribution')
        self.btnorb=wx.Button(self.prppan,wx.ID_ANY,"Orbital",pos=(xloc1,yloc),size=(75,20))
        self.btnorb.Bind(wx.EVT_BUTTON,self.OnOrbital)
        self.btnorb.SetToolTipString('Plot monomer molecular orbital')
        #self.ckbden=wx.CheckBox(self.prppan,-1,"Density",pos=(xloc+5,yloc),size=(80,18))
        #self.ckbden.Disable()
        #self.ckborb=wx.CheckBox(self.prppan,-1,"Orbital",pos=(xloc1,yloc),size=(80,18))
        #self.ckborb.Disable()
        yloc += 25
        self.btnhomo=wx.Button(self.prppan,wx.ID_ANY,"HOMO-LUMO",pos=(xloc+10,yloc),size=(90,20))
        self.btnhomo.Bind(wx.EVT_BUTTON,self.OnHOMOLUMO)
        self.btnhomo.SetToolTipString('Plot monomer HOMO-LUMO energies')
        self.btndos=wx.Button(self.prppan,wx.ID_ANY,"DOS",pos=(xloc1+15,yloc),size=(60,20))
        self.btndos.Bind(wx.EVT_BUTTON,self.OnDos)
        self.btndos.SetToolTipString('Plot monomer density of states')
        #self.ckbden=wx.CheckBox(self.prppan,-1,"Monomers HOMO-LUMO s",pos=(xloc+5,yloc),size=(180,18))
        #self.ckbden.SetToolTipString('Monomers HOMO-LUMO energies')      
        yloc += 25
        self.btnchgc=wx.Button(self.prppan,wx.ID_ANY,"Charge coupling terms",pos=(xloc+10,yloc),size=(150,20))
        self.btnchgc.Bind(wx.EVT_BUTTON,self.OnChargeCoupling)
        self.btnchgc.SetToolTipString('Compute and plot charge coupling terms')

        #self.ckbden=wx.CheckBox(self.prppan,-1,"Monomer density of states",pos=(xloc+5,yloc),size=(180,18))
        #self.ckbden.SetToolTipString('Monomers density of states')      
        #yloc += 20
        #self.ckbcup=wx.CheckBox(self.prppan,-1,"Charge coupling elements",pos=(xloc+5,yloc),size=(180,18))
        #self.ckbcup.Disable()
        #self.ckbcup.SetToolTipString('Compute and plot charge coupling integrals')      
        """
        yloc += 30
        wx.StaticText(self.prppan,wx.ID_ANY,'Plot cube data',pos=(xloc,yloc),size=(90,20))
        self.btncube=wx.Button(self.prppan,wx.ID_ANY,"Open panel",pos=(xloc+95,yloc-2),size=(80,20))
        self.btncube.Bind(wx.EVT_BUTTON,self.OnOpenPlotCube)
        self.btncube.SetToolTipString('Open panel for MEP/Density plot')
        #btplt=wx.Button(self.prppan,wx.ID_ANY,"Plot",pos=(50,yloc1),size=(40,20))
        #btplt.Bind(wx.EVT_BUTTON,self.OnPlot)
        yloc += 25
        wx.StaticLine(self.prppan,pos=(0,yloc),size=(w/2,2),style=wx.LI_HORIZONTAL)
        yloc += 10
        btclr=wx.Button(self.prppan,wx.ID_ANY,"Close all plots",pos=(60,yloc),size=(80,20))
        btclr.Bind(wx.EVT_BUTTON,self.OnCloseAll)
        #
        self.btncube.Disable()
        self.EnableFMOButtons(False)
        #

    def CreateSelectDataPanel(self):
        # create select panel on left hand side
        [w,h]=self.GetClientSize()
        xpos=0; ypos=0
        xsize=w/2+10; ysize=h
        self.panel=wx.Panel(self,-1,pos=(xpos,ypos),size=(w/2,h))
        self.panel.SetBackgroundColour("light gray")
        width=w/2-20
        xloc=10; yloc=10
        wx.StaticText(self.panel,wx.ID_ANY,'Data list',pos=(xloc,yloc),size=(60,20)) 
        self.btnadd=wx.RadioButton(self.panel,-1,'add',pos=(xloc+60,yloc-5),style=wx.RB_GROUP)
        self.btnadd.Bind(wx.EVT_RADIOBUTTON,self.OnAddMode)
        self.btnadd.SetToolTipString('Add data mode')
        btnrep=wx.RadioButton(self.panel,-1,'replace',pos=(xloc+110,yloc-5))
        btnrep.Bind(wx.EVT_RADIOBUTTON,self.OnAddMode)
        btnrep.SetToolTipString('Replace data mode')
        wclb=w/2-xpos-30; hclb=h-135 #140
        yloc += 20
        self.lbdat=wx.ListBox(self.panel,-1,pos=(xloc+5,yloc),size=(wclb,hclb),
                                      style=wx.LB_HSCROLL|wx.LB_SORT) #
        self.lbdat.SetToolTipString('List of data obtained by filer')
        ###self.lbdat.InsertItems(self.datalist,0)
        """self.lbdat.Bind(wx.EVT_LISTBOX,self.OnSelectData)"""
        # command button
        #xloc=wclb/2; 
        yloc1=yloc+hclb+10
        btrmv=wx.Button(self.panel,wx.ID_ANY,"Remove",pos=(35,yloc1),size=(60,20))
        btrmv.Bind(wx.EVT_BUTTON,self.OnRemoveData)
        btrmv.SetToolTipString('Remove data from the list')
        btnclr=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(115,yloc1),size=(40,20))
        btnclr.Bind(wx.EVT_BUTTON,self.OnClearData)
        btnclr.SetToolTipString('Clear all data')
        yloc1 += 30
        btnview=wx.Button(self.panel,wx.ID_ANY,"View",pos=(20,yloc1),size=(40,20))
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile)
        btnview.SetToolTipString('View file by editor')
        btnset=wx.Button(self.panel,wx.ID_ANY,"Select for plot",pos=(80,yloc1),size=(100,20))
        btnset.Bind(wx.EVT_BUTTON,self.OnSelectForPlot)
        btnset.SetToolTipString('Set selected data to "Selected data for plot" window.')
        yloc1 += 25
        wx.StaticLine(self.panel,pos=(-1,yloc1),size=(w/2-5,2),style=wx.LI_HORIZONTAL) 
        # button to pop-up derived data creation panel 
        yloc1 += 10
        self.tbdrv=wx.Button(self.panel,-1,label='Make derived data',
                                   pos=(40,yloc1),size=(120,20)) 
        self.tbdrv.SetToolTipString('Open panel to make derived data')
        self.tbdrv.Bind(wx.EVT_BUTTON,self.OnOpenDerivedPanel)
        yloc1 += 50
        self.drvpanpos=[60,yloc1]; self.drvpansize=[wclb,80]
        if self.opendrvpan: self.OnOpenDerivedPanel(0)
        #
        wx.StaticLine(self.panel,pos=(w/2-5,0),size=(2,h),style=wx.LI_VERTICAL) 

    def MessageSelect(self):
        mess='Select a item'
        lib.MessageBoxOK("Select an item by clicking mouse left button.","",style=wx.OK|wx.ICON_EXCLAMATION)

    def GetCubeFile(self):
        name=self.tcsel.GetValue()
        filename=self.datadic[name]
        #name=name.split(':',1)
        #filename=name[1]
        base,ext=os.path.splitext(filename) 
        if ext == '.mep' or ext == '.den' or ext == '.cub': return filename
        else: return '' 
        
    def OnPIE(self,event):
        curfmodat=self.GetCurrentFMOData()
        nfrg=curfmodat.nfrg
        if nfrg <=1:
            dlg=lib.MessageBoxOK("No plot data, since the number of fragment=1.",
                    "",style=wx.OK|wx.ICON_EXCLAMATION)
            return
        if not curfmodat.pieda:
            dlg=lib.MessageBoxOK("No plot data, probably non-PIEDA job.",
                    "",style=wx.OK|wx.ICON_EXCLAMATION)
            return
        self.pltpie=True
        #self.pltpie=False; self.pltctchg=False; self.pltmulchg=False
        #self.pltespot=False; self.pltden=False; self.pltorb=False
        #
        prop=[1,0,0,0,0,0] # flags: [pie,ctc,mul,esp,den,orb], 1:True,0:False       
        # draw graph
        nprp=len(prop)-1
        for i in range(nprp,-1,-1):
            if prop[i]:
                self.pltprp=i
                name=self.graphnam[self.pltprp]
                if self.ctrlflag.GetCtrlFlag(name):
                    self.graph[name].SetFocus(); continue
                pos=(-1,-1); size=(660,360); oned=True; child=False
                self.graph[name]= \
                     graph.fuGraph(self,-1,pos,size,oned,self.pltprp,child)
                self.ctrlflag.SetCtrlFlag(name,True)
                self.graph[name].Show()
                #
                self.SetGraphData(self.pltprp)
                self.graph[self.graphnam[self.pltprp]].DrawGraph(True)

        if self.ctrlflag.GetCtrlFlag('pycrustwin'):                            
            self.RunMethod('fuplot.PrintFragmentName()')
    

    def OnPlotFMOProp(self,event):
        prop=self.cbprop.GetValue()
        print 'prop in OnFMOProp',prop
        if prop == 'PIE':
            pass
        elif prop == 'PIEDA':
            pass
            
    def OnCloseFMOProp(self,event):           
        prop=self.cbprop.GetValue()    
    def OnViewFMOProp(self,event):
        pass                   
    def OnCTCharge(self,event):
        print 'btnctc'
    def OnMulliken(self,event):
        print 'btnmul'
    def OnMEP(self,event):
        print 'btnmep'
        
    def OnDensity(self,event):
        print 'btnden'
    def OnOrbital(self,event):
        print 'btnorb'
    def OnHOMOLUMO(self,event):
        print 'btnhomo' 
    def OnDos(self,event):
        print 'btndos'
    def OnChargeCoupling(self,event):
        print 'btnchgc'

    def OnOpenPlotCube(self,event):
        # create model instance
        fumode=1
        self.model=fumodel.Model(fumode) # fumode=1
        # create mdlwin
        pos=self.GetPosition()
        size=self.GetClientSize()
        winpos=[pos[0]+size[0],pos[1]]
        winsize=lib.WinSize([480,370])
        self.model.OpenMdlWin(self,winpos,winsize) # parent
        self.model.mdlwin.SetTitle('FMO viewer')
        self.model.menuctrl.OnWindow("Open MolChoiceWin",False)
        self.model.menuctrl.OnWindow("Open MouseModeWin",False)
        #self.model.menuctrl.OnWindow("Open PyShell",False)
        self.model.mdlwin.hideshlwin=True
        self.model.winctrl.GetWin('Open PyShell').Hide()
        self.mdlwin=self.model.mdlwin
        self.draw=self.model.mdlwin.draw
        # position of text message
        pos=[150,50]
        if lib.GetPlatform() == 'WINDOWS': pos=[150,70]
        self.mdlwin.textmess.SetPos(pos)
        self.mdlwin.textmess.SetSize([winsize[0]-pos[0]-10,25])
        # open draw cube win    
        self.OpenDrawCubeWin()

    def SaveCubeParams(self):
        # params:[self.style,self.value,self.interpol,self.colorpos,self.colorneg,
        #        self.opacity,self.ondraw]
        self.drwcubeparams=self.cubewin.GetDrawPanelParams()
        
    def ResetCubeParams(self):
        # params:[self.style,self.value,self.interpol,self.colorpos,self.colorneg,
        #        self.opacity,self.ondraw]
        self.cubewin.SetDrawPanelParams(self.drwcubeparams)
              
    def OpenDrawCubeWin(self):
        mode=1 # no menu mode
        winsize=lib.WinSize([85,325])
        mdlwinpos=self.mdlwin.GetPosition()
        mdlwinsize=self.mdlwin.GetClientSize()
        winpos=[mdlwinpos[0],mdlwinpos[1]+50]
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
        
    def OnViewDetails(self,event):
        pass

    def OnViewResults(self,event):
        pass

    def OnSelectForPlot(self,event):
        selected=self.lbdat.GetStringSelection()
        if selected == '': self.MessageSelect()
        else: self.tcsel.SetValue(selected)
        base,ext=os.path.splitext(selected)
        file=self.datadic[selected]
        # open plot win
        if ext == '.den' or ext == '.mep' or ext == '.cub':
            self.btncube.Enable()
            self.EnableFMOButtons(False)
            #self.OnOpenPlotCube(1) #OpenPlotCubeWin(ext)
        else:
            self.btncube.Disable()
            self.EnableFMOButtons(True)
            self.tcsel.SetValue(selected)
            
            
            fmoprop=FMOProperty(base,file)
            
            fmoproplst=fmoprop.GetPropertyItems()
            self.cbprop.SetItems(fmoproplst)
            self.cbprop.SetSelection(0)
            
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

    def OnViewFile(self,event):
        selected=self.lbdat.GetStringSelection()
        if selected == '': self.MessageSelect()
        else:
            filename=self.datadic[selected]
            lib.Editor1(self.platform,filename)

    def OnAddMode(self,event):
        value=self.btnadd.GetValue()
        if value: self.addmode=True
        else: self.addmode=False

    def SetPropChoice(self):
        # set enable/disable to property choicebox
        self.pltpiedisable=True
        self.pltctchgdisable=True
        self.pltmulchgdisable=True
        self.pltespotdisable=True
        self.pltdendisable=True
        self.pltorbdisable=True
        # get fmodat of selected
        curfmodat=self.GetCurrentFMOData()
        if curfmodat.pieda: self.pltpiedisable=False

        #if curfmodat.dft:
        #    self.pltpiedisable=True
        #    self.ckbctc.SetValue(True)

        if curfmodat.ctchg: self.pltctchgdisable=False
        if curfmodat.mulchg: self.pltmulchgdisable=False
        if curfmodat.espot: self.pltespotdisable=False
        if curfmodat.density: self.pltdendisable=False
        if curfmodat.orbital: self.pltorbdisable=False    
        #
        if self.pltpiedisable: self.ckbpie.Disable()
        else: self.ckbpie.Enable()
        if self.pltctchgdisable: self.ckbctc.Disable()
        else: self.ckbctc.Enable()
        if self.pltmulchgdisable: self.ckbmul.Disable()
        else: self.ckbmul.Enable()
        if self.pltespotdisable: self.ckbesp.Disable()
        else: self.ckbesp.Enable()
        if self.pltdendisable: self.ckbden.Disable()
        else: self.ckbden.Enable()
        if self.pltorbdisable: self.ckborb.Disable()
        else: self.ckborb.Enable()

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
    
    def SetGraphData(self,pltprp):
        # set data on fuGraph instance
        datnam=self.selected
        onbody=[]; frgdist=[]
        molint=False
        if self.IsDerivedData(datnam): molint=True
        name=self.graphnam[pltprp]
        # graph data
        curfmodat=self.GetCurrentFMOData()
        nfrg=curfmodat.nfrg
        
        frgnam=curfmodat.frgnam
        frgdist=curfmodat.frgdist
        bdabaa=curfmodat.bdabaa
        indat=curfmodat.indat
        pdbfile=curfmodat.pdbfile
        pieda=curfmodat.pieda
        corr=curfmodat.corr
        natm=curfmodat.natm
        #
        if pltprp == 0: fmoprp=self.MakePIEDAPlotData()
        if pltprp == 1: fmoprp=self.MakeCTChargePlotData()
        if pltprp == 2: fmoprp=self.MakeMullikenPlotData()
        # set plot data on fuGraph instance
        piedacmp=[0,0,0,0,0]; mullbody=[0,0,0,0]
        if self.pltprp == 0 or self.pltprp == 1:
            if pieda: piedacmp=[1,1,1,0,0]
            if corr: piedacmp[3]=1
            if molint: piedacmp[4]=1
        if self.pltprp == 2:
            if len(fmoprp[0][0]) == 3: mullbody=[1,1,0,0]
            if len(fmoprp[0][0]) == 4: mullbody=[1,1,1,1] 
        self.graph[name].SetFMOProp(self.pltprp,datnam,molint,piedacmp,mullbody)
        self.graph[name].SetFMOPropData(natm,nfrg,frgnam,fmoprp,frgdist)
        self.graph[name].SetMolViewFragmentData(pdbfile,indat,bdabaa)

    def PrintFragmentName(self):
        curfmodat=self.GetCurrentFMOData()
        nfrg=curfmodat.nfrg
        frgnam=curfmodat.frgnam
        frgnamdic={}
        for i in range(len(frgnam)):
            frgnamdic[i+1]=frgnam[i]
        
    def OnSplitWinChanged(self,event):
        self.sashposition=self.splwin.GetSashPosition()
        self.OnSize(0)

    def OnPlot(self,event):
        if len(self.selected) <= 0:
            dlg=lib.MessageBoxOK("No data to plot. Open files first.",
                    "",style=wx.OK|wx.ICON_EXCLAMATION)
            return
        curfmodat=self.GetCurrentFMOData()
        nfrg=curfmodat.nfrg
        if nfrg <=1:
            dlg=lib.MessageBoxOK("No plot data, since the number of fragment=1.",
                    "",style=wx.OK|wx.ICON_EXCLAMATION)
            return
        if not curfmodat.pieda:
            dlg=lib.MessageBoxOK("No plot data, probably non-PIEDA job.",
                    "",style=wx.OK|wx.ICON_EXCLAMATION)
            return
        self.pltpie=False; self.pltctchg=False; self.pltmulchg=False
        self.pltespot=False; self.pltden=False; self.pltorb=False
        #
        prop=[0,0,0,0,0,0] # flags: [pie,ctc,mul,esp,den,orb] 
        if self.ckbpie.IsEnabled() and self.ckbpie.GetValue(): prop[0]=1
        if self.ckbctc.IsEnabled() and self.ckbctc.GetValue(): prop[1]=1
        if self.ckbmul.IsEnabled() and self.ckbmul.GetValue(): prop[2]=1
        #    
        if self.ckbesp.IsEnabled() and self.ckbesp.GetValue(): prop[3]=1
        if self.ckbden.IsEnabled() and self.ckbden.GetValue(): prop[4]=1
        if self.ckborb.IsEnabled() and self.ckborb.GetValue(): prop[5]=1
        # draw graph
        nprp=len(prop)-1
        for i in range(nprp,-1,-1):
            if prop[i]:
                self.pltprp=i
                name=self.graphnam[self.pltprp]
                if self.ctrlflag.GetCtrlFlag(name):
                    self.graph[name].SetFocus(); continue
                pos=(-1,-1); size=(660,360); oned=True; child=False
                self.graph[name]= \
                     graph.fuGraph(self,-1,pos,size,oned,self.pltprp,child)
                self.ctrlflag.SetCtrlFlag(name,True)
                self.graph[name].Show()
                #
                self.SetGraphData(self.pltprp)
                self.graph[self.graphnam[self.pltprp]].DrawGraph(True)

        if self.ctrlflag.GetCtrlFlag('pycrustwin'):                            
            self.RunMethod('fuplot.PrintFragmentName()')
    
    def MouseLeftClick(self,pos):
        if not self.ctrlflag.GetCtrlFlag('molviewwin'): return
        if self.onedmode:
            i=self.graph.GetXValue(pos)
            if i < 0:
                mess='Clicked at outside of plot region.'
                self.molview.Message(mess,0,'black')
                return
            i=int(i); i=self.order[i]
            if i >= 0 and i <= len(self.pltdat):
                if self.ctrlflag.GetCtrlFlag('molviewwin'):
                    self.molview.SetSelectAll(False)
                    mess=self.MakeFragValueMess(i)
                    frgnam=self.frgnam[i]
                    self.molview.SelectFragNam(frgnam,True)
                    #mess="Fragment="+frgnam+', plot data=['
                    #for i in range(len(self.pltdat)):
                    #mess=mess+'['
                    #for j in range(1,len(self.pltdat[i])):
                    #    mess=mess+'%7.2f' % self.pltdat[i][j]
                    #mess=mess+']'
                    self.molview.Message(mess,0,'black')
        

    def GetCurrentFMOData(self):
        # return curfmodat, the fmodat instance of selected data
        if not self.IsDerivedData(self.selected):
            curfmodat=self.fmodatadic[self.selected]
        else:
            drvdat=self.drvdatadic[self.selected]
            fmodatlst,cmpsign=self.ResolveDerivedData(drvdat)
            curfmodat=self.fmodatadic[fmodatlst[0]]
        return curfmodat

    def ListFMODataName(self):
        for name in self.fmodatadic:
            print self.fmodatadic[name].name
        
    def MakePIEDAPlotData(self):
        # make pieda for plot.
        # if molint=True, subtract component energy from those of complex
        tokcal=627.50 # Hartree to kcal/mol, for onbody energy conversion.
        nlayer=1
        onebody=[]
        molint=False
        if self.IsDerivedData(self.selected): molint=True
        curfmodat=self.GetCurrentFMOData()
        pieda=curfmodat.frgpieda
        onebody=curfmodat.onebody
        nfrg=curfmodat.nfrg
        if not molint: return pieda
        #
        pieda=copy.deepcopy(pieda)
        onebody=copy.deepcopy(onebody)
        drvdat=self.drvdatadic[self.selected]
        fmodat,cmpsign=self.ResolveDerivedData(drvdat)
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
        return pieda

    def MakeCTChargePlotData(self):
        #ctcharge=[]
        molint=False
        if self.IsDerivedData(self.selected): molint=True   
        curfmodat=self.GetCurrentFMOData()  
        ctcharge=curfmodat.ctcharge

        if not molint: return ctcharge
        ctcharge=copy.deepcopy(ctcharge)
        drvdat=self.drvdatadic[self.selected]
        fmodat,cmpsign=self.ResolveDerivedData(drvdat)
        nf=0 
        for i in range(1,len(fmodat)):
            datnam=fmodat[i]
            tmpchg=self.fmodatadic[datnam].ctcharge
            tmpnfrg=self.fmodatadic[datnam].nfrg
            for j in range(len(tmpchg)):
                if tmpnfrg == 1:
                    nf += 1; break
                for k in range(len(tmpchg[j])):
                    i0=j+nf
                    j0=k+nf
                    val=tmpchg[j][k][1]
                    ctcharge[i0][j0][1] += cmpsign[i]*val
            nf += tmpnfrg
        return ctcharge

    def MakeMullikenPlotData(self):
        curfmodat=self.GetCurrentFMOData()  
        mulcharge=curfmodat.mulliken
 
        molint=False        
        if self.IsDerivedData(self.selected): molint=True
        
        if not molint: return mulcharge
        mulcharge=copy.deepcopy(mulcharge)
        drvdat=self.drvdatadic[self.selected]
        fmodat,cmpsign=self.ResolveDerivedData(drvdat)
        nfrg=self.fmodatadic[fmodat[0]].nfrg
        nbody=len(mulcharge[0][0])
        nf=0
        for i in range(1,len(fmodat)):
            datnam=fmodat[i]
            tmpmulchg=self.fmodatadic[datnam].mulliken
            tmpnfrg=self.fmodatadic[datnam].nfrg
            if tmpnfrg == 1: # GMS mulliken
                for k in range(len(tmpmulchg)):
                    i0=nf; j0=k
                    for l in range(1,nbody):
                        mulcharge[i0][j0][l] += cmpsign[i]*tmpmulchg[k][1]
            else:
                for j in range(len(tmpmulchg)):
                    for k in range(len(tmpmulchg[j])):
                        i0=j+nf; j0=k+nf
                        for l in range(1,len(tmpmulchg[j][k])):
                            mulcharge[i0][j0][l] += cmpsign[i]*tmpmulchg[j][k][l]
            nf += tmpnfrg

        return mulcharge

    def OnRemoveData(self,event):     
        selected=self.lbdat.GetStringSelection()
        if self.datadic.has_key(selected): del self.datadic[selected]
        self.SetDataList()
        if selected == self.tcsel.GetValue(): self.tcsel.SetValue('')
        """
        for i in range(len(self.datalist)):
            if self.datalist[i] == self.selected:
                del self.datalist[i]; break
        self.lbdat.Set(self.datalist)
        self.selected=''
        self.tcrmk.Clear()
        self.OnPropClear(0)
        """
    def OnPropClear(self,event):

        if self.ckbpie.GetValue(): self.ckbpie.SetValue(False)
        if self.ckbctc.GetValue(): self.ckbctc.SetValue(False)
        if self.ckbmul.GetValue(): self.ckbmul.SetValue(False)
        if self.ckbesp.GetValue(): self.ckbesp.SetValue(False)
        if self.ckbden.GetValue(): self.ckbden.SetValue(False)
        if self.ckborb.GetValue(): self.ckborb.SetValue(False)
        
    def XXOnSelectData(self,event):
        self.selected=self.lbdat.GetStringSelection()
        if self.selected == '': return
        #
        self.WriteRemark()
        self.pltpie=1
        self.SetPropChoice()
        self.graph={}

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

    def OnOpenDerivedPanel(self,event):
        #
        if self.opendrvpan:
            self.drvpan.Destroy()
        #
        self.opendrvpan=True
        #[posx,posy]=self.GetPosition(); [wsize,hsize]=self.GetSize()
        #self.drvpanpos=[posx+wsize-100,posy+hsize-40]
        self.drvpan=subwin.DeriveDataInput_Frm(self,-1,self.drvpanpos)
        self.drvpan.Show()
    
    def AddDerivedDataDic(self,drvnam,drvcmp):

        if drvnam == '': return
        drvnam.strip()
        dup=self.IsDuplicateName(1,drvnam)
        if dup: return
        find=self.CheckDeriveComp(drvcmp)
        if not find: return
        #
        dataname=self.MakeDataName(drvnam)
        self.drvdatadic[dataname]=drvcmp
        #
        self.SetDataListInSelLB()
        self.lbdat.SetStringSelection(dataname)
        self.OnSelectData(0)

    def IsDerivedData(self,dataname):
        ret=False
        if self.drvdatadic.has_key(dataname): ret=True
        return ret

    def IsFMOProperty(self,dataname):
        ret=False
        if self.fmodatadic.has_key(dataname): ret=True
        return ret
      
    def CheckDeriveComp(self,drvcmp):
        find=False
        for cmpo in drvcmp:
            find=self.IsItemInDataDic(cmpo,self.fmodatadic)
            #
            if not find:
                find=self.IsItemInDataDic(cmpo,self.drvdatadic)
            if not find:
                dlg=lib.MessageBoxOK("No component data. "+cmpo,"")
        return find
    
    def IsItemInDataDic(self,item,datadic):
        ret=False
        idc,namec=self.GetIDAndName(item)
        lst=datadic.keys()
        for datnam in lst:
            id,name=self.GetIDAndName(datnam)
            if idc == id:
                ret=True; break
        return ret

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
        datalist=self.fmodatadic.keys()
        if len(self.drvdatadic) > 0:
            drvlist=self.drvdatadic.keys()
            datalist=datalist+drvlist
        datalist.sort()
        #
        return datalist
    
    def MakeFMOPropertyDic(self,curdir,files):
        fmodatadic={}
        #
        for filout in files:
            err,name,ext=self.GetNameAndExt(filout)
            if err: return
            if ext == '.out' or ext == '.log':
                dup=self.IsDuplicateName(0,name)
                #
                if dup: continue
                dataname=self.MakeDataName(name)
                # search for inp file
                filinp=''; filpdb=''
                for fil in files:
                    err,name1,ext1=self.GetNameAndExt(fil)
                    #
                    if err: continue
                    if ext1 == '.inp' and name1 == name:
                        filinp=fil
                    if (ext1 == '.ent' or ext1 == '.pdb') and name1 == name:
                        filpdb=fil
                #
                filout=os.path.join(curdir,filout)
                filinp=os.path.join(curdir,filinp)
                filpdb=os.path.join(curdir,filpdb)
                fmodatadic[dataname]=FMOProperty(dataname,filout,filinp,filpdb)
        return fmodatadic

    def GetNameAndExt(self,filename):
        err=True
        #name=''; ext=''
        ext=os.path.splitext(filename)[1]
        name=os.path.splitext(filename)[0]
        if len(ext) <= 0:
            dlg=lib.MessageBoxYesNo('Wrong file name, missing extention. '+filename+". Quit?","")
            if wx.YES:
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
        submenu.Append(-1,'Open GAMESS output','Open GAMESS output files (multiple files can be opened.)')
        submenu.Append(-1,'Open CUBE file','Open cube file')
        submenu.AppendSeparator()
        # Save FMO info
        subsubmenu=wx.Menu()
        subsubmenu.Append(-1,"Fragment size","fragment size")
        subsubmenu.Append(-1,"Timings","Timings")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,'FMO statics','FMO statics')
        subsubmenu.Append(-1,"PIE/PIEDA","PIEDA table")
        subsubmenu.Append(-1,"CT charges","CT charge table")
        subsubmenu.Append(-1,"Mulliken charges","Mulliken charges")
        subsubmenu.Append(-1,"MO energies","MO energies")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,"Charge coupling","Charge coupling")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,"All info","All info")
        submenu.AppendSubMenu(subsubmenu,'Save FMO info')
        # Save images
        subsubmenu=wx.Menu()
        subsubmenu.Append(-1,"Fragment size plot","fragment size plot")
        subsubmenu.Append(-1,"Timings plot","Timings plot")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,"PIE/PIEDA graph","PIEDA graph")
        subsubmenu.Append(-1,"CT charge graph","CT charge grapf")
        subsubmenu.Append(-1,"Mulliken charge graph","Mulliken charge graph")
        subsubmenu.Append(-1,"MO energie plot","MO energie plot")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,"Charge coupling plot","Charge coupling plot")
        subsubmenu.AppendSeparator()
        subsubmenu.Append(-1,"All graphs","All graphs")
        submenu.AppendSubMenu(subsubmenu,'Save Images')
                
        # Edit 'Copy Clipboard','Clear Clipboard'
        
        # Quit
        submenu.AppendSeparator()
        submenu.Append(-1,'Quit','Close the window')
        menubar.Append(submenu,'File')
        
        """
        mfil= ("File", (
                  ("Open","Open GAMESS-FMO input/output file",False),
                  ("","",False),
                  #("*Save bitmap","Save bitmap on file",False),
                  #("*Print bitmap","Unfinished",False),
                  ("Quit","Close plot panel",False)))
        mplt= ("Plot", (
                  ("PIE/PIEDA","Plot PIEDA in 1D",False),
                  ("CT charge","CT charge",False),
                  ("Mulliken charge", "Mulliken charge",False)))
            #("Density","density",False),
            #("*ES potential","Electrostatic potential",False),
            #("*Molecular orbital","Molecular orbital",False),                 
            #("","",False),
            #("*Monomer scf convergence","",False),
            #("*Monomer SCC convergence","",False),
            #("*Dimer SCF convergence","",False),
            #("*Optmization convergence","",False)))
        mrep= ("Report", (
                  ("PIE/PIEDA ","Plot PIEDA in 1D/2D",False),
                  ("CT charge ","PIEDA ct charge",False),
                  ("Mulliken charge ","Mulliken charge",False),
                  ("*ES potential ","Electrostatic potential",False),
                  ("*Molecular orbital ","Molecular orbital",False),                 
                  ("","",False),
                  ("Open setting panel","",False)))
        mwin= ("Window", (
                  #("Mol viewer","molecule viewer",False),
                  #("","",False),
                  ("PyCrust","python IDE",False),
                  ("","",False),
                  ("MatPlotLib","MatPlotLib",False)))
        mhlp= ("Help", (
                  ("About","licence remark",False),
                  ("Version","Version",False)))

        #menud=[mfil,mplt,mrep,mwin]
        menud=[mfil,mplt,mwin,mhlp]
        return menud
        """
        return menubar
 
    def OpenFiles(self,case):
        if case == "Open GAMESS output":
            wcard='Output file(*.out;*.log)|*.out;*.log|All(*.*)|*.*'
        elif case == 'Open CUBE file':
            wcard='Cube file(*.mep;*.den;*.cub)|*.mep;*.den;*.cub|All(*.*)|*.*'
        files=lib.GetFileNames(None,wcard,'r',True,'')
        #
        self.MakeDataDic(files)
        self.SetDataList()
        
    def MakeDataDic(self,files):
        if len(files) <= 0: return
        if not self.addmode: self.datadic={}
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
                if namedic[tail] == fil: continue
            nmb += 1; name=str(nmb)+':'+tail
            self.datadic[name]=fil

    def SetDataList(self):
        lst=[]
        for name,fil in self.datadic.iteritems(): lst.append(name)
        self.lbdat.Set(lst)
        self.lbdat.SetSelection(len(lst)-1)
                
    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        # File menu items
        if item == "Open GAMESS output": self.OpenFiles(item)
        if item == "Open CUBE file": self.OpenFiles(item)
        if item == "Save bitmap":
            print 'save bitmap on file'
        
        if item == "*Print bitmap":
            self.buffer=wx.EmptyBitmap(self.wplt,self.hplt)
            dc=wx.BufferedDC(None,self.buffer)
            dc.Clear() 
        if item == "Quit":
            self.OnClose(0)
        # plot menu items
        if item == "PIE/PIEDA":
            self.ckbpie.SetValue(True)
            self.ckbctc.SetValue(False)
            self.ckbmul.SetValue(False)
            self.OnPlot(0)
        if item == "CT charge":
            self.ckbpie.SetValue(False)
            self.ckbctc.SetValue(True)
            self.ckbmul.SetValue(False)
            self.OnPlot(0)
        if item == "Mulliken charge":
            self.ckbpie.SetValue(False)
            self.ckbctc.SetValue(False)
            self.ckbmul.SetValue(True)
            self.OnPlot(0) 
        # window menu items
        if item == "PyCrust":
            self.OpenPyCrustFrame()
        if item == "MatPlotLib":
            self.OpenMatPlotLibFrame()
        if item == 'About': lib.About('FMOviewer')
    
    def RunMethod(self,method):
        self.pycrust.shell.run(method)

    def Message(self):
        self.text='test message'
        print 'message: ',self.text

    def ConsoleMessage(self,mess):
        if not self.ctrlflag.GetCtrlFlag('pycrustwin'): return
        self.pycrust.shell.write(mess)
        self.pycrust.shell.run("")        
        #self.consolemessage=mess
        #method='fuplot.PrintMessage()'
        #self.pycrust.shell.run(method)
    
    def PrintMessage(self):
        print self.consolemessage

    def OnClosePyCrust(self,event):
        self.ctrlflag.SetCtrlFlag('pycrustwin',False)
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
        self.ctrlflag.SetCtrlFlag('pycrustwin',True)

    def OpenMatPlotLibFrame(self):
        if self.ctrlflag.GetCtrlFlag('matplotlibwin'):
            self.mpl.SetFocus(); return
        parentpos=self.GetPosition()
        parentsize=self.GetClientSize()
        winpos=[parentpos[0],parentpos[1]+parentsize[1]+50]
        winsize=lib.WinSize((600,450))
        self.mpl=fupanel.MatPlotLib_Frm(self,-1,self.ctrlflag,winpos,winsize)
        self.mpl.Show()
        self.ctrlflag.SetCtrlFlag('matplotlibwin',True)

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
        
        
        self.SavePropChoice(True)
        #self.splwin.Destroy()
        #self.CreateSplitWindow()

        
        self.SavePropChoice(False)
        if self.opendrvpan: self.OnOpenDerivedPanel(0)

    def OnClose(self,event):
        try: self.model.Quit()
        except: pass
        try: self.Destroy()
        except: pass

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
        self.graphnamtxt=['PIE/PIEDA','CTcharge','Mulliken','ESPot','Density','Orbital',
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
        self.gamessver=prpdic['gmsver']
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
        # fmopieda: pieda read by fuPlot.ReadFMOPIEDA(fmo output file)
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
                    tot=0.0; es=0.0; ex=0.0; ct=0.0; cr=0.0
                else:
                    tot=fmopieda[i][8]
                    es=fmopieda[i][9]
                    ex=fmopieda[i][10]
                    ct=fmopieda[i][11]
                    cr=0.0
                    if corr: cr=fmopieda[i][12]
                tmp.append(tot); tmp.append(es)
                tmp.append(ex); tmp.append(ct)
                
                tmp.append(cr)
                
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

#----------------------------------------
def start():
    app = wx.App(False)
    const.SYSTEM=const.GetSYSTEM() #=lib.GetSystemInfo()
    const.fup = Plot(None,-1,[-1,-1],'FU Plot')
    const.fup.Show(True)
    app.MainLoop()

if __name__ == '__main__':
    app = wx.App(False)
    start()
    app.MainLoop()          
