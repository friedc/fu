#!/bin/sh
# -*- coding:utf-8 

import os
#import psutil # downloaded from http://code.google.com/p/psutil/downloads/detail?name=psutil-1.0.1.win32-py2.7.exe&can=2&q=
import wxversion
wxversion.select("2.8")
import wx
# import FU modules
import fumodel
import view
import const
import lib
import molec
import graph

from numpy import *

try: import fucubelib
except: pass

class DrawOrbital():
    def __init__(self,parent,model,viewer):
    
        self.parent=parent
        self.model=model
        self.viewer=viewer
        self.orbitallst=[]
        
    def OpenDrawWin(self,orbitallst):    
        self.draworb=DrawOrbital_Frm(self.parent,-1,self.parent,self.viewer,orbitallst=orbitallst)
    
    def SetOrbitalList(self,orbitallst):
        self.orbitallst=orbitallst
        
    def SetMode(self,mode):
        self.mode=mode

    def SetViewer(self,viewer):
        self.viewer=viewer
    
class DrawOrbital_Frm(wx.MiniFrame):
    def __init__(self,parent,id,model,viewer,mode=0,winpos=[-1,-1],
                 orbitallst=[]): #,model,ctrlflag,molnam,winpos):
        """
        :param obj parent: parent object
        :param int id: object id
        :param obj model: an instance of "Model" (model.py)
        :param obj viewer: viewer instance
        :param int mode: 0 for stand alone, 1 for child (no menu)
        """       
        self.title='Orbital plotter'
        self.orbitallst=orbitallst
        
        self.magnify=False
        ###self.orbitallst=[[[-20,-15,-10,5,10,15]],[[-50,-20,-15,-10,5,10,15],[-15,-10,-5,8,10,12]]]
        #self.orbitallst=[[[-20,-15,-10,5,10,15]]]
        
        norbpanel=len(self.orbitallst)
        #if norbpanel <= 0: norbpanel=1 
        self.orbitalpanwidth=115
        winwidth=100+8+norbpanel*self.orbitalpanwidth
        if norbpanel <= 0: winwidth=110
        winsize=lib.MiniWinSize([winwidth,340]) #([100,355])
        self.norbpanel=norbpanel
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
                          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent
        self.mode=mode
        if mode == 1: 
            self.viewer=viewer
            #self.SetTransparent(100)
        self.model=model # model #parent.model
        #self.mdlwin=model.mdlwin
        #self.draw=self.mdlwin.draw
        #self.ctrlflag=model.ctrlflag
        self.ctrlflag={}
        """ need codes """
        self.homoorbnmblst=self.norbpanel*[3]
        self.maxorbnmblst=self.norbpanel*[20]
        
        self.plotterpanwidth=100
        self.orbitalpanwidth=115
        self.orbpanel=self.norbpanel*[None]
        self.orbtitle=self.norbpanel*['orbiatl']
        self.orbgraph=self.norbpanel*[None]
        self.orbcheck=self.norbpanel*[None]
        self.lumoplus=self.norbpanel*[0]
        self.minlumo=self.norbpanel*[0]
        self.maxlumo=self.norbpanel*[50]
        self.homominus=self.norbpanel*[0]
        self.minhomo=self.norbpanel*[0]
        self.maxhomo=self.norbpanel*[50]
        self.spin=self.norbpanel*['']
        self.widgetiddic={}
        self.curdata=0
        self.erangemin=-15.0
        self.erangemax=5.0
        # menu
        if self.mode == 0:
            menud=self.MenuItems() # method of MyModel class
            # Create menu using model.fuMenu class
            self.menubar=self.MenuItems() # create instance of fuMenu class
            self.SetMenuBar(self.menubar) # method of wxFrame class
            self.Bind(wx.EVT_MENU,self.OnMenu)
        # 
        self.bgcolor='light gray'
        #self.cubedataname=[]
        nulobj=CubeObj()        
        self.denobjdic={}; self.denobjdic[' ']=nulobj
        self.denobjlst=[] #[' ','den-cube-1','den-cube-2','den-cube-3']
        self.mepobjdic={}; self.mepobjdic[' ']=nulobj
        self.mepobjlst=[] #[' ','mep-cube-1','mep-cube-2','mep-cube-3']
        self.cubeobjdic={}; self.cubeobjdic[' ']=nulobj
        self.cubeobjlst=[]
        self.curden=' '
        self.curmep=' '
        self.curcube=' '
        #self.cubefile=''
        self.prptxt=['DENSITY','MEP','CUBE']
        self.property=0
        self.style=0 # 0:solid, 1:mesh
        self.ondraw=False
        self.superimpose=False
        self.xcubemin=0.0; self.xcubemax=0.0
        self.ycubemin=0.0; self.ycubemax=0.0
        self.zcubemin=0.0; self.zcubemax=0.0
        self.xcubecnt=0.0; self.ycubecnt=0.0; self.zcubecnt=0.0
        self.valuemin=0.0; self.valuemax=0.0
        self.nx=0; self.ny=0; self.nz=0
        # params for draw
        self.xmin=-1; self.xmax=-1
        self.ymin=-1; self.ymax=-1
        self.zmin=-1; self.zmax=-1
        self.value=0.05
        self.interpol=1
        self.minipo=1
        self.maxipo=4 # maximum degree of intepolation for cube data
        self.opacity=0.5 # 0-1        
        self.colortxt=['red','magenta','yellow','orange','brown','blue','cyan','green','purple',
                 'white','gray','black','---','palette']
        self.colorpos=self.colortxt[0]; self.rgbpos=const.RGBColor[self.colorpos]
        self.colorneg=self.colortxt[6]; self.rgbneg=const.RGBColor[self.colorneg]

        # polygons
        self.polyg=[]
        # create panel
        self.CreatePlotterPanel()
        
        for i in range(self.norbpanel): self.CreateOrbitalPanel(i)
        
        self.SetParamsToWidgets()
        #
        if self.mode == 1: self.GetCubeFileAndMakeCubeObjDic()
        #
        self.Show()
        # initialize view
        self.InitDrawOrbitalWin()
        #orbnmb=self.GetOrbitalNumberInTC()
        #self.SetOrbValueToOrbTC(self.curdata,orbnmb)
        # activate event handlers
        self.Bind(wx.EVT_CLOSE,self.OnClose)
    
    def InitDrawOrbitalWin(self):
        self.PlotEnergy()
        """ need codes for spin and orbital selection in graph """ # 
        #spinobj=self.GetSpinObject(self.cutdata)
                    
    def OpenInfoPanel(self):
        pos=self.GetPosition()
        winpos=pos; winsize=[80,40]
        self.tcinfo=wx.TextCtrl(None,-1,'',pos=winpos,size=winsize,style=wx.TE_MULTILINE)
        self.tcinfo.SetBackgroundColour('light gray')
        self.DispCubeDataInfo()
            
    def CreatePlotterPanel(self):
        size=self.GetClientSize()
        w=size[0]; h=size[1]
        w=self.plotterpanwidth
        hcb=const.HCBOX # height of combobox
        ff='%5.0f'
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(w,h)) #ysize))
        self.panel.SetBackgroundColour(self.bgcolor)
        # cubedata
        yloc=5; xloc=10
        #btninfo=wx.Button(self.panel,wx.ID_ANY,"Data info",pos=(xloc,yloc-2),size=(70,20))
        #btninfo.Bind(wx.EVT_BUTTON,self.OnInfo)
        #btninfo.SetToolTipString('Display plot data information')
        # style
        #yloc += 25
        ststyle=wx.StaticText(self.panel,-1,label='Style:',pos=(xloc,yloc),size=(35,18))
        ststyle.SetToolTipString('Choose drawing style')
        #yloc += 18
        #self.rbtsold=wx.RadioButton(self.panel,-1,"solid",pos=(xloc+10,yloc),size=(45,18),
        self.rbtsold=wx.RadioButton(self.panel,-1,"solid",pos=(xloc+40,yloc),size=(40,18),
                                   style=wx.RB_GROUP)
        self.rbtsold.Bind(wx.EVT_RADIOBUTTON,self.OnSolid)
        yloc += 18
        #self.rbtwire=wx.RadioButton(self.panel,-1,"wire",pos=(xloc+10,yloc),size=(45,18))
        self.rbtwire=wx.RadioButton(self.panel,-1,"wire",pos=(xloc+40,yloc),size=(40,18))
        self.rbtwire.Bind(wx.EVT_RADIOBUTTON,self.OnWire)
        self.rbtsold.SetValue(True)
        #
        yloc += 20
        wx.StaticText(self.panel,-1,"Value(abs):" ,pos=(xloc,yloc),size=(70,18))
        yloc += 20
        self.tcval=wx.TextCtrl(self.panel,-1,'',pos=(xloc+10,yloc),size=(70,18),
                              style=wx.TE_PROCESS_ENTER)
        self.tcval.Bind(wx.EVT_TEXT_ENTER,self.OnValue)
        self.tcval.SetToolTipString('Input value and "ENTER"')
        yloc += 25
        wx.StaticText(self.panel,-1,"Interp:" ,pos=(xloc,yloc),size=(45,18))
        self.spip=wx.SpinCtrl(self.panel,-1,value=str(self.interpol),pos=(xloc+45,yloc),size=(35,18),
                              style=wx.SP_ARROW_KEYS,min=self.minipo,max=self.maxipo)
        self.spip.Bind(wx.EVT_SPINCTRL,self.OnInterpolate)
        self.spip.SetToolTipString('Choose interpolation points number.')

        yloc += 20
        wx.StaticText(self.panel,-1,"Color:",pos=(xloc,yloc),size=(55,18))
        yloc += 20
        wx.StaticText(self.panel,-1,"+",pos=(xloc+5,yloc),size=(10,18))
        self.cbcolp=wx.ComboBox(self.panel,-1,'',choices=self.colortxt, \
                               pos=(xloc+20,yloc-3), size=(60,hcb),style=wx.CB_READONLY)             
        self.cbcolp.Bind(wx.EVT_COMBOBOX,self.OnColorPos)
        self.cbcolp.SetToolTipString('Choose color for positive value. "---" is dummy')

        yloc += 25
        wx.StaticText(self.panel,-1," -" ,pos=(xloc+5,yloc),size=(10,18))
        self.cbcoln=wx.ComboBox(self.panel,-1,'',choices=self.colortxt, \
                               pos=(xloc+20,yloc-3), size=(60,hcb),style=wx.CB_READONLY)              
        self.cbcoln.Bind(wx.EVT_COMBOBOX,self.OnColorNeg)
        self.cbcoln.SetToolTipString('Choose color for negative value. "---" is dummy')

        yloc += 25
        wx.StaticText(self.panel,-1,"Opacity:" ,pos=(xloc,yloc),size=(50,18))
        self.tcopa=wx.TextCtrl(self.panel,-1,('%4.2f' % self.opacity),pos=(xloc+50,yloc-2),size=(30,18),
                              style=wx.TE_PROCESS_ENTER)
        self.tcopa.SetToolTipString('Input opacity value (0-1) and "ENETR"')
        self.tcopa.Bind(wx.EVT_TEXT_ENTER,self.OnOpacity)
        
        #self.ckbimp.SetValue(self.superimpose)
        yloc += 20
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        #yloc += 25
        yloc += 8
        wx.StaticText(self.panel,-1,"Object:" ,pos=(xloc,yloc),size=(50,18))
        yloc += 18
        self.cmbobj=wx.ComboBox(self.panel,-1,'',choices=self.cubeobjlst, \
                               pos=(xloc+5,yloc), size=(75,hcb),style=wx.CB_READONLY)                      
        self.cmbobj.Bind(wx.EVT_COMBOBOX,self.OnObject)
        self.cmbobj.SetToolTipString('Choose object for operations')
        yloc += 25
        self.ckbimp=wx.CheckBox(self.panel,-1,"superimpose",pos=(xloc,yloc),size=(120,18))
        self.ckbimp.Bind(wx.EVT_CHECKBOX,self.OnSuperimpose)
        self.ckbimp.SetToolTipString('Check for superimpose objects')
        yloc += 25
        self.btndel=wx.Button(self.panel,wx.ID_ANY,"Del",pos=(xloc,yloc),size=(30,20))
        self.btndel.Bind(wx.EVT_BUTTON,self.OnDel)
        self.btndel.SetToolTipString('Remove object')
        self.btndraw=wx.Button(self.panel,wx.ID_ANY,"Draw",pos=(xloc+40,yloc),size=(45,20))
        self.btndraw.Bind(wx.EVT_BUTTON,self.OnDraw)
        self.btndraw.SetToolTipString('Draw cube data(toggle "on" and "off")')

    def CreateOrbitalPanel(self,idata):
        size=self.GetClientSize()
        w=size[0]; h=size[1]
        w=self.orbitalpanwidth
        xpanpos=self.plotterpanwidth+idata*self.orbitalpanwidth
        ff='%5.0f'
        # upper panel
        id=wx.NewId()
        panel=wx.Panel(self,id,pos=(xpanpos,0),size=(w,h)) #ysize))
        panel.SetBackgroundColour(self.bgcolor)
        self.widgetiddic[id]=[idata,'Panel',panel]
        # cubedata
        yloc=5; xloc=15
        #sttit=wx.StaticText(panel,-1,label=self.orbtitle[idata],pos=(xloc,yloc),size=(w-10,18))
        id=wx.NewId()
        label=wx.StaticText(panel,id,label=self.orbtitle[idata],pos=(xloc,yloc),size=(w-10,18))
        self.widgetiddic[id]=[idata,'Label',label]
        label.Bind(wx.EVT_LEFT_DOWN,self.OnOrbTitleLeftClick)
        label.SetToolTipString('L-Click to be avtive')
        wx.StaticLine(panel,pos=(0,0),size=(4,h),style=wx.LI_VERTICAL)
        #ststit.SetToolTipString('Choose drawing style')
        yloc += 25
        self.wplt=self.orbitalpanwidth-25 #90; 
        self.hplt=125
        id=wx.NewId()
        orbgraph=graph.EnergyGraph(panel,id,[xloc,yloc],[self.wplt,self.hplt],'white',retobj=self)        #yloc += 25
        orbgraph.SetToolTipString('L-Click a bar for select. L-Drag for move plot window')
        self.widgetiddic[id]=[idata,'Graph',orbgraph]
        #
        yloc += self.hplt+10
        id=wx.NewId()
        btnrdc=wx.Button(panel,id,"<",pos=(xloc,yloc),size=(20,20))
        btnrdc.Bind(wx.EVT_BUTTON,self.OnOrbReduce)
        btnrdc.SetToolTipString('"<" ("<") key press also reduces/magnifies')
        btnrdc.Bind(wx.EVT_KEY_DOWN,self.OnOrbKeyDown)
        self.widgetiddic[id]=[idata,'Reduce',btnrdc]
        id=wx.NewId()
        btnmag=wx.Button(panel,id,">",pos=(xloc+25,yloc),size=(20,20))
        btnmag.Bind(wx.EVT_BUTTON,self.OnOrbMagnify)
        self.widgetiddic[id]=[idata,'Magnify',btnmag]
        btnmag.SetToolTipString('"<" ("<") key press also reduces/magnifies')
        btnmag.Bind(wx.EVT_KEY_DOWN,self.OnOrbKeyDown)
        id=wx.NewId()
        btnset=wx.Button(panel,id,"Reset",pos=(xloc+50,yloc),size=(40,20))
        btnset.Bind(wx.EVT_BUTTON,self.OnOrbReset)
        btnset.SetToolTipString('Reset draw size')
        self.widgetiddic[id]=[idata,'Reset',btnset]
        yloc += 25
        wx.StaticLine(panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        storb=wx.StaticText(panel,-1,label='Orb:',pos=(xloc,yloc),size=(30,18))
        id=wx.NewId()
        tcorb=wx.TextCtrl(panel,id,str(self.homoorbnmblst[idata]),pos=(xloc+30,yloc),size=(35,18),
                              style=wx.TE_PROCESS_ENTER)
        tcorb.Bind(wx.EVT_TEXT_ENTER,self.OnEnterOrbitalNumber)
        tcorb.SetToolTipString('Input orbital number and "ENTER"')
        self.widgetiddic[id]=[idata,'Orb',tcorb]
        id=wx.NewId()
        btnab=wx.ToggleButton(panel,id,'',pos=(xloc+70,yloc),size=(20,20))
        btnab.Bind(wx.EVT_TOGGLEBUTTON,self.OnOrbSpin)
        btnab.SetToolTipString('Toggle switch for select alpha or beta orbitals(open shell only')
        self.widgetiddic[id]=[idata,'Spin',btnab]
        try:
            if len(self.data) == 1: btnab.Disable()
            else: 
                self.spin[idata]='a'
                btnab.SetLabel(self.spin[idata])
                btnab.Refresh()
        except: pass
        yloc += 25
        sthom=wx.StaticText(panel,-1,label='HOMO -',pos=(xloc,yloc),size=(45,18))
        id=wx.NewId()
        schom=wx.SpinCtrl(panel,id,value=str(self.homominus[idata]),pos=(xloc+45,yloc),size=(45,18),
                              style=wx.SP_ARROW_KEYS,min=self.minhomo[idata],max=self.maxhomo[idata])
        schom.Bind(wx.EVT_SPINCTRL,self.OnOrbHOMO)
        schom.SetToolTipString('Set orbital number relative to HOMO')
        self.widgetiddic[id]=[idata,'HOMO',schom]
        yloc += 25
        stlum=wx.StaticText(panel,-1,label='LUMO +',pos=(xloc,yloc),size=(45,18))
        id=wx.NewId()
        sclum=wx.SpinCtrl(panel,id,value=str(self.lumoplus[idata]),pos=(xloc+45,yloc),size=(45,18),
                              style=wx.SP_ARROW_KEYS,min=self.minlumo[idata],max=self.maxlumo[idata])
        sclum.SetToolTipString('Set orbital number relative to LUMO')
        sclum.Bind(wx.EVT_SPINCTRL,self.OnOrbLUMO)
        self.widgetiddic[id]=[idata,'LUMO',sclum]
        yloc += 25
        id=wx.NewId()
        btncls=wx.Button(panel,id,"Close",pos=(xloc-5,yloc),size=(45,20))
        btncls.Bind(wx.EVT_BUTTON,self.OnOrbClose)
        btncls.SetToolTipString('Close this panel')
        self.widgetiddic[id]=[idata,'Close',btncls]
        id=wx.NewId()
        btnapl=wx.Button(panel,id,"Aplly",pos=(xloc+50,yloc),size=(45,20))
        btnapl.Bind(wx.EVT_BUTTON,self.OnOrbApply)
        btnapl.SetToolTipString('Apply the orbital specified in "Orb" for draw')
        self.widgetiddic[id]=[idata,'Aplly',btnapl]
        #
        self.SetOrbLabelColor(self.curdata)

        #self.PlotEnergy()
        #self.RefreshGraphPanel()
    def OnOrbTitleLeftClick(self,event):
        id=event.GetId()
        self.curdata=self.widgetiddic[id][0]
        
        print 'id,curdata',id,self.curdata
        self.SetOrbLabelColor(self.curdata)
        event.Skip()
        
    def PlotEnergy(self):
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Graph':
                lst[2].SetYRange(self.erangemin,self.erangemax)
                lst[2].SetData(self.orbitallst[lst[0]])
                #lst[2].SetYAxisLabel('Energy (ev)')
                lst[2].Plot(True)

    def RefreshGraphPanel(self):
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Panel': 
                lst[2].Refresh(); lst[2].Update()
    # for orbital energy panel    
    def OnOrbSpin(self,event):
        id=event.GetId()
        value=self.widgetiddic[id][2].GetValue()
        if value: label='a'
        else: label='b'
        self.widgetiddic[id][2].SetLabel(label)
        self.spin[self.widgetiddic[id][0]]=value
    
    def SetLabelToSpinButton(self,idata,label):
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Spin': 
                if lst[0] == idata:
                    lst[2].SetLabel(label)
                    break

    def GetLabelOnSpinButton(self,idata):
        label=''
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Spin': 
                if lst[0] == idata:                
                    label=lst[2].GetLabel()
                    break
        return label
     
    def OnOrbKeyDown(self,event):
        # ascii:44:'<',46:'>', unicode: 60:'<',62:'>'
        keycode=event.GetKeyCode()
        if keycode == 46: self.ZoomEnergyGraph(self.curdata,True)
        elif keycode == 44: self.ZoomEnergyGraph(self.curdata,False)
                    
    def OnOrbMagnify(self,event):
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)
        self.ZoomEnergyGraph(idata,True)
    
    def GetGraphObj(self,idata):
        graphobj=None
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Graph' and lst[0] == idata:
                graphobj=lst[2]; break
        return graphobj
        
    def OnOrbReduce(self,event):
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)
        #
        self.ZoomEnergyGraph(idata,False)

    def ZoomEnergyGraph(self,idata,magnify):
        graphobj=self.GetGraphObj(idata)
        #
        ymin,ymax=graphobj.GetYRange()
        yinc=1.0
        if magnify: ymin += yinc; ymax -= yinc
        else: ymin -= yinc; ymax += yinc    
        #
        graphobj.SetYRange(ymin,ymax)
        graphobj.Plot(True)
    
    def SetFocusOnOrbPanel(self,idata):    
        
        print 'SetFocuson',idata
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Panel' and lst[0] == idata:
                panel=lst[2]; break
        panel.SetFocus()
    
    def SetOrbLabelColor(self,idata):
        # widgetiddic:{id:[idata,label,obj],...}
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Label':
                if lst[0] == idata: color='red'
                else: color='black'
                lst[2].SetForegroundColour(color)
                lst[2].Refresh()
                self.curdata=idata
            
    def OnOrbReset(self,event):
        # reset energy graph color
        graphobj=self.GetGraphObj(self.curdata)
        #
        ymin=self.erangemin
        ymax=self.erangemax
        graphobj.SetYRange(ymin,ymax)
        graphobj.Plot(True)

    def OnOrbApply(self,event):
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)
        value=0
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Orb' and lst[0] == idata:
                value=lst[2].GetValue()
                break
        print 'value in Apply',value
        
            
    def OnOrbClose(self,event):
        id=event.GetId()
        idata=self.curdata #self.widgetiddic[id][0]
        pos=self.GetPosition()
        
        try: del self.orbitallst[idata]
        except: pass
        
        self.parent.orbobj.SetOrbitalList(self.orbitallst)
        
        self.Destroy()
        
        self.parent.orbobj.OpenDrawOrbitalWin(self.orbitallst)
        self.SetPosition(pos)
        
    def GetOrbitalNumberInTC(self):
        idata=self.curdata
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Orb' and lst[0] == idata:
                orbnmb=lst[2].GetValue()
        orbnmb=int(orbnmb)
        return orbnmb        
            
    def OnEnterOrbitalNumber(self,event):
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)
        value=self.widgetiddic[id][2].GetValue()
        self.SetOrbValueToHOMOLUMO(idata,int(value))
        
    def OnOrbHOMO(self,event):    
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)

        value=self.widgetiddic[id][2].GetValue()
        orbnmb=self.homoorbnmblst[idata]-value
        if orbnmb <= 1: orbnmb=1
        self.SetOrbValueToOrbTC(idata,orbnmb)
    
    def SetOrbValueToHOMOLUMO(self,idata,value):
        homo=self.homoorbnmblst[idata]
        lumo=homo+1
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'HOMO' and lst[0] == idata:
                sval=homo-value
                if sval < 0: sval=0
                lst[2].SetValue(sval)
                lst[2].Refresh()          
            if lst[1] == 'LUMO' and lst[0] == idata:
                sval=value-lumo
                if sval < 0: sval=0
                lst[2].SetValue(sval)
                lst[2].Refresh()
                       
    def SetOrbValueToOrbTC(self,idata,orbnmb):
        for id,lst in self.widgetiddic.iteritems():
            if lst[1] == 'Orb' and lst[0] == idata:
                lst[2].SetValue(str(orbnmb))
                lst[2].Refresh()
        self.SetOrbValueToHOMOLUMO(idata,orbnmb)
    
        label=self.GetLabelOnSpinButton(idata)
        if label == 'a': spin=0
        elif label == 'b': spin=1
        else: spin=-1
        graphobj=self.GetGraphObj(idata)
        graphobj.SelectOrbital(spin,orbnmb)
        
    def SelectedOrbFromEnergyGraph(self,spin,orbnmb):
        self.SetOrbValueToOrbTC(self.curdata,orbnmb)
        if spin == 0: label='a'
        elif spin == 1: label='b'
        else: label=''
        self.SetLabelToSpinButton(self.curdata,label)
        
    def OnOrbLUMO(self,event):
        id=event.GetId()
        idata=self.widgetiddic[id][0]
        self.SetOrbLabelColor(idata)

        value=self.widgetiddic[id][2].GetValue()
        orbnmb=self.homoorbnmblst[idata]+1+value
        if orbnmb > self.maxorbnmblst[idata]: orbnmb=self.maxorbnmblst[idata]
        
        self.SetOrbValueToOrbTC(idata,orbnmb)
    # for cube plotter panel
    def OnDel(self,event): 
    
        if len(self.objectlst) <= 1:
            # can not delete but close all
            return
        
        object=self.ckbobj.GetValue().strip()
        # remove plot
        
        try: idx=self.objectlst.index(object)
        except: pass
        
        if idx >= 1:
            del self.objectlst[idx]
            self.ckhobj.SetValue(self.objectlst[idx-1])

            
    def OnObject(self,event):
        print 'curobj',self.curobj
        self.curobj=self.ckbobj.GetValue().strip()
            
    def OnSuperimpose(self,event):
        self.superimpose=self.ckbimp.GetValue()
        print 'superimpose',self.superimpose
        
    def GetCubeFileAndMakeCubeObjDic(self):
        filename=self.viewer.GetCubeFile()
        if os.path.exists(filename):
            base,ext=os.path.splitext(filename)
            self.cubefile=filename
            if ext == '.den' or ext == '.mep' or ext == '.cub':
                err=self.AddToCubeObjDic(filename)
            else:
                mess='The file "'+filename+'" is not cube data (ext should be ".mep" or ".den"'
                lib.MessageBoxOK(mess,"")
                self.OnClose(1)
        else:
            mess='Cube file is not found. filename="'+filename+'"'
            lib.MessageBoxOK(mess,"")
            self.OnClose(1)   

    def GetDrawPanelParams(self):
        #self.ondraw=self.btndraw.GetValue()
        return [self.style,self.value,self.interpol,self.colorpos,self.colorneg,
                self.opacity,self.ondraw]

    def SetDrawPanelParams(self,params): 
        self.style=params[0]; self.value=params[1]; self.interpol=params[2]
        self.colorpos=params[3]; self.colorneg=params[4]; self.opacity=params[5]
        self.ondraw=params[6]
        self.SetParamsToWidgets()
    
    def SetParamsToWidgets(self):
        self.rbtsold.SetValue(True)
        if self.style == 1: self.rbtwire.SetValue(True)
        self.tcval.SetValue(str(self.value))
        self.spip.SetValue(self.interpol)
        self.cbcolp.SetValue(self.colorpos) #StringSelection(self.colorpos)
        self.cbcoln.SetValue(self.colorneg) #StringSelection(self.colorneg)
        self.tcopa.SetValue(str(self.opacity))
        #self.btndraw.SetValue(self.ondraw)
        self.ckbimp.SetValue(self.superimpose)
              
    def OpenMolViewWin(self):
        fum=fumodel.Model()
        # open main window (mdlwin)
        winpos=[-1,-1]; winsize=[400,300]
        fum.OpenMdlWin(self,winpos,winsize) # parent

        #mdlwin=fuview.View_Frm(self,winpos,winsize,self.model)
        return fum
                  
    def OnSolid(self,event):
        self.style=0
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
    
    def OnWire(self,event):
        self.style=1
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)

    def OnXMin(self,event):
        value=self.tcxmin.GetValue()
        try: self.xmin=float(value)
        except:
            mess="error input for x.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnXMax(self,event):
        value=self.tcxmax.GetValue()
        try: self.xmax=float(value)
        except:
            mess="error input for x.range max. value."
            lib.MessageBoxOK(mess,"")     

    def OnYMin(self,event):
        value=self.tcymin.GetValue()
        try: self.ymin=float(value)
        except:
            mess="error input for y.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnYMax(self,event):
        value=self.tcymax.GetValue()
        try: self.ymax=float(value)
        except:
            mess="error input for y.range max. value."
            lib.MessageBoxOK(mess,"")     

    def OnZMin(self,event):
        value=self.tczmin.GetValue()
        try: self.zmin=float(value)
        except:
            mess="error input for z.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnZMax(self,event):
        value=self.tczmax.GetValue()
        try: self.zmax=float(value)
        except:
            mess="error input for z.range max. value."
            lib.MessageBoxOK(mess,"")     
        
    def OnValue(self,event):
        value=self.tcval.GetValue()
        try: self.value=float(value)
        except:
            mess="error input for Draw value."
            lib.MessageBoxOK(mess,"") 
            return    
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        #if self.ondraw: self.OnDraw(1)

    def OnInterpolate(self,event):
        self.interpol=self.spip.GetValue()
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
        #if self.ondraw: self.OnDraw(1)
         
    def OnOpacity(self,event):
        value=self.tcopa.GetValue()
        try: self.opacity=float(value)
        except:
            mess="error input for Opacity value (0-1)."
            lib.MessageBoxOK(mess,"") 
            return    
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        #if self.ondraw: self.OnDraw(1)

    def OnColorPos(self,event):
        color=self.cbcolp.GetValue()
        if color == '---': return
        self.rgbpos=self.GetColor(color,self.cbcolp)
        if len(self.rgbpos) <= 0: return
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
    
    def OnColorNeg(self,event):
        color=self.cbcoln.GetValue()
        if color == '---': return
        self.rgbneg=self.GetColor(color,self.cbcoln)
        if len(self.rgbneg) <= 0: return
        if self.ondraw: self.OnDraw(1)
        #if self.btndraw.GetValue(): self.OnDraw(1)   

    def GetColor(self,color,obj):
        if color == 'palette':
            obj.Disable(); obj.SetValue('---'); obj.Enable()
            rgbcol=lib.ChooseColorOnPalette(self,False,1.0) # parent,rgb255,opacity
            if len(rgbcol) <= 0: return []
            else: return rgbcol
        else: return const.RGBColor[color]
             
    def OnDensity(self,event):
        self.property=0
        self.cubcmb.SetItems(self.denobjlst)
        self.cubcmb.SetValue(self.curden)
        #
       
    def OnMEP(self,event):
        self.property=1
        self.cubcmb.SetItems(self.mepobjlst)
        self.cubcmb.SetValue(self.curmep)
        #

        
    def OnOthers(self,event):
        print 'property: others. not implemented yet.'
        self.property=2

    def MakePolygonData(self):  
        # make plolygon data
        # return polys: [polygon data]
        polys=[]
        #if self.property == 0: cubefile=self.denobjdic[self.curden].file
        #elif self.property == 1: cubefile=self.mepobjdic[self.curmep].file
        prop,obj=self.GetCurrentCubeObj()
        cubefile=obj.file
        if len(cubefile) <= 0:
            mess='No cube file for property='+prop
            lib.MessageBoxOK(mess,"MakePloygonData")              
            #self.btndraw.SetValue(False)
            #self.ondraw=False
            return []       
        value=self.value; intp=self.interpol
        try:
            polys=MC.CubePolygons(cubefile,value,intp)
        except:
            print 'Failed to create polygons in MakePolygonData.'
        return polys
  
    def OnInfo(self,event): 
        self.DispCubeDataInfo()
            
    def OnCubeData(self,event):
        if self.property == 0:
            self.curden=self.cubcmb.GetValue() #GetStringSelection()
        if self.property == 1:
            self.curmep=self.cubcmb.GetValue() #GetStringSelection()

    def GetCubeInfo(self):
        """ use GetCurrentCubeObj() instead """
        if self.property == 0:
            info=self.denobjdic[self.curden].info
        elif property == 1:
            attr=self.mepobjdic[self.curmep].info
        elif property == 2:
            attr=self.cubeobjdic[self.curcube].info
        return info    

    def SetCubeListToComboBox(self):
        if self.property == 0:
            info=self.denobjdic[self.curden].info
            objlst=self.denobjdic.keys()
            curdat=self.curden
        elif self.property == 1:
            info=self.mepobjdic[self.curmep].info
            objlst=self.mepobjdic.keys()
            curdat=self.curmep
        elif self.property == 2:
            info=self.cubepobjdic[self.curcube].info
            objlst=self.cubeobjdic.keys()
            curdat=self.curcube
            
        objlst.sort()
        #self.cubcmb.SetItems(objlst)
        #self.cubcmb.SetValue(curdat)
            
    def DispCubeDataInfo(self):
        f61='%6.1f'; f64='%6.4f'; fi4='%4d'
        #
        prop,obj=self.GetCurrentCubeObj()
        info=obj.info
        file=obj.file
        natoms=obj.natoms
        
        txt=[]
        txtprop='Property: '+prop+'\n'
        txtfile='Cube file: '+file+'\n'
        txtatm=' Number of atoms='+str(natoms)+'\n'
        txtcnt=' Center: x='+(f61 % info[0][0]).strip()
        txtcnt=txtcnt+',  y='+(f61 % info[0][1]).strip()
        txtcnt=txtcnt+',  z='+(f61 % info[0][2]).strip()+'\n'
        
        txtx=' x: min='+(f61 % info[1])+', max='+(f61 % info[2])+', nptx='+str(info[3])+'\n'
        txty=' y: min='+(f61 % info[4])+', max='+(f61 % info[5])+', npty='+str(info[6])+'\n'
        txtz=' z: min='+(f61 % info[7])+', max='+(f61 % info[8])+', nptz='+str(info[9])+'\n'

        txtval=' value: min= '+(f64 % info[10])
        txtval=txtval+', max= '+(f64 % info[11])+'\n'

        mess=txtprop+'\n'+txtfile+'\n'+txtatm+txtcnt+txtx+txty+txtz+'\n'+txtval
        lib.MessageBoxOK(mess,"Cube data information")

    def GetCurrentCubeObj(self):
        if self.property == 0: return 'Density',self.denobjdic[self.curden]
        elif self.property == 1: return 'MEP',self.mepobjdic[self.curmep]
        elif self.property == 2: return 'Cube',self.cubeobjdic[self.curcube]

    def OnRemove(self,event):
        label='cube-data' 
        self.draw.DelDrawData(label)
        self.model.TextMessage('',[])
        self.model.DrawMol(True)
    
    def OnDraw(self,event):
        f64='%6.4f'
        #if self.btndraw.GetValue(): #not self.ondraw: #
        test=True
        if test:
            # check molecular data in model
            if not self.model.mol:
                prop,obj=self.GetCurrentCubeObj()
                natoms=obj.natoms
                if natoms <= 0:
                    mess='No molecular data in model. Read structure data.'
                    lib.MessageBoxOK(mess,"DrawCubeData_Frm:OnDraw")              
                    #self.btndraw.SetValue(False)
                    self.ondraw=False
                    return
                else: 
                    self.BuildCubeMol()
                    name=self.model.mol.name
                    self.model.ConsoleMessage('"'+name+'" molecule was created using atom data in the cube file')                   
            label='cube-data'    
            # get value and opacity
            ###self.OnValue(1); self.OnOpacity(1)
            # parameters for draw
            params=[self.style,self.rgbpos,self.rgbneg,self.opacity]
            # make polygon data
            polyg=self.MakePolygonData()
            if len(polyg) <= 0: return
            # set polyg data to view
            self.draw.SetDrawData(label,'CUBE',[params,polyg])
            # message
            mess='Drawing '+self.prptxt[self.property]+', value='+('%8.3f' % self.value)
            self.model.Message(mess,0,'')
            self.model.ConsoleMessage(mess)
            # text message
            prop,obj=self.GetCurrentCubeObj()
            name=obj.name; name=name.split('.')[0]
            mess=prop+':'+name+','+'value='+(f64 % self.value)
            self.model.DrawMol(True)
            self.model.TextMessage(mess,[])
            self.ondraw=True           
        else: 
            self.OnRemove(1)
            self.ondraw=False

    def BuildCubeMol(self):
        # create 'mol' instance
        mol=molec.Molecule(self.model) 
        #
        prop,obj=self.GetCurrentCubeObj()
        atmcc=obj.atmcc
        mol.name=obj.name
        mol.inpfile=obj.file       
        mol.SetAtoms(atmcc) 
        #       
        self.model.molctrl.Add(mol)
        # clear self.savecc
        self.model.savatmcc.Clear()
        nmol=self.model.molctrl.GetNumberOfMols()
        if nmol > 0: self.model.menuctrl.EnableMenu(True)
        if nmol > 1:
            drwitems=self.draw.GetDrawObjs()
            self.mol.SaveDrawItems(drwitems)            
        self.model.curmol,self.model.mol=self.model.molctrl.GetCurrentMol()
        # add bond 
        self.model.AddBondUseBondLength()
        #
        self.model.SetUpDraw(True)
    
    def OnClose(self,event):
        # self.OnRemove(1)
        self.Destroy()

    def AddToCubeObjDic(self,filename):
        info,natoms,atmcc=self.ReadCubeFile(filename)
        if len(info) < 0: return 1
        head,name=os.path.split(filename)
        base,ext=os.path.splitext(name)
        if ext == '.mep': prp='MEP'
        elif ext == '.den': prp='Density'
        else: prp='Cube'
        # make cube object
        cube=CubeObj()
        cube.file=filename
        cube.info=info
        cube.name=name
        cube.atmcc=atmcc
        cube.natoms=natoms
        if prp == 'Density':
            self.denobjdic[name]=cube
            if self.denobjdic.has_key(' '): del self.denobjdic[' ']
            self.curden=name
            self.property=0
            #self.prprb1.SetValue(True)
        elif prp == 'MEP':
            self.mepobjdic[name]=cube
            if self.mepobjdic.has_key(' '): del self.mepobjdic[' ']
            self.curmep=name
            self.property=1
            #self.prprb2.SetValue(True)
        elif prp == 'Cube':
            self.cubeobjdic[name]=cube
            if self.cubeobjdic.has_key(' '): del self.cubeobjdic[' ']
            self.curcube=name
            self.property=2        
        return 0

    def ReadCubeFile(self,filename): # ,property):
        # read density and mep cube file
        # format: a comment and a blank lines are assumed at the head of the file
        # ' $END' line is needed at the end of the file.
        bhtoan=const.PysCon['bh2an']
        #
        info=[]; atmcc=[]; natoms=-1
        if not os.path.exists(filename):
            mess='file: '+filename+ 'not found.'
            lib.MessageBoxOK(mess,"ReadCubeFile")              
            return [],-1,[]
        f=open(filename,'r')
        # title and property
        """
        find=False; k=0
        while not find:
            s=f.readline()
            s=s.replace('\r',''); s=s.replace('\n','') 
            if s[:5] == ' $END': break
            item=s.split(':'); item[0]=item[0].strip()
            if s == '': k += 1
            else: k=0
            if k >= 10: break
            if item[0] == property: #'DENSITY':
                if property == 'DENSITY': prop=0
                if property == 'MEP': prop=1
                find=True; break
        if not find: return [],[] # -1,[],[]
        """
        # skip a comment line
        s=f.readline()
        # skip a blank line
        s=f.readline()
        # natoms,xmin,ymin,zmin
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split()
        natoms=int(item[0])
        xmin=float(item[1])
        ymin=float(item[2])
        zmin=float(item[3])
        # nx,dx, the same data for y and z
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); nx=int(item[0]); dx=float(item[1])
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); ny=int(item[0]); dy=float(item[2])
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); nz=int(item[0]); dz=float(item[3])
        xmax=xmin+nx*dx; ymax=ymin+ny*dy; zmax=zmin+nz*dz
        center=[(xmax+xmin)/2.0,(ymax+ymin)/2.0,(zmax+zmin)/2.0]
        # atmcc, [[an, x,y, and z],...]
        for i in range(natoms):
            s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','')             
            item=s.split()
            atmcc.append([int(item[0]),float(item[2])*bhtoan,float(item[3])*bhtoan,
                          float(item[4])*bhtoan])
        vmin=1000000.0; vmax=-1000000.0
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n',''); s=s.strip()
            if s == ' $END': break
            item=s.split()
            for val in item:
                try:
                    if float(val) > vmax: vmax=float(val)
                except: pass
                try:
                    if float(val) < vmin: vmin=float(val)
                except: pass
        f.close()
        #
        info.append(center)
        info.append(xmin); info.append(xmax); info.append(nx)
        info.append(ymin); info.append(ymax); info.append(ny)
        info.append(zmin); info.append(zmax); info.append(nz) 
        info.append(vmin); info.append(vmax)
        #
        return info,natoms,atmcc

    def OpenNotePad(self):
        if self.property == 0:
            filename=self.denobjdic[self.curden].file
        if self.property == 1:
            filename=self.mepobjdic[self.curmep].file
        if len(filename) <= 0:
            mess='cube file not found.'
            lib.MessageBoxOK(mess,"OpenNotePad")
        # open notepad
        else:
            lib.Editor(filename)
                   
    def MenuItems(self):
        # File
        submenu=wx.Menu()
        submenu.Append(-1,"Open","Open...")
        submenu.AppendSeparator()
        submenu.Append(-1,"Quit","Quit...")
        menubar.Append(submenu,'File')
        # View
        submenu=wx.Menu()
        submenu.Append(-1,"Cube data","Edit/View cube data")
       
        return menubar
        
        return menubar

    def OnMenu(self,event):
        # menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
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
                            self.model.ConsoleMessage(filename+' file not found. skipped.')
                        else:
                            base,ext=os.path.splitext(filename)
                            if ext == '.den' or ext == '.mep':
                                err=self.AddToCubeObjDic(filename)
                                if not err:
                                    self.model.ConsoleMessage('Read cube file: '+filename)
                                    ndat += 1
                            else:
                                mess='Can not read file with extention: "'+ext+'"'
                                lib.MessageBoxOK(mess,"OnMenu")
                                continue
                mess=str(ndat)+' '+prop+' cube data were read.'
                self.model.ConsoleMessage(mess)

        if item == "Quit":
            self.OnClose(1)
        # Edit menu
        if item == "Cube data":
            self.OpenNotePad()    

class DrawCubeData_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos,winsize,model,viewer,mode): #,model,ctrlflag,molnam,winpos):
        """
        :param obj parent: parent object
        :param int id: object id
        :param obj model: an instance of "Model" (model.py)
        :param obj viewer: viewer instance
        :param int mode: 0 for stand alone, 1 for child (no menu)
        """       
        self.title='Cube plotter'
        winsize=lib.MiniWinSize(winsize)
        #####winsize=[85,340]
        #parpos=parent.GetPosition()
        #parsize=parent.GetSize()
        #winpos=(parpos[0]+parsize[0]-winsize[0],parpos[1]+50)
        #if const.SYSTEM == const.MACOSX: winsize=[85,315]
        #if mode == 1: winsize[1] -= 25 # no menu in case of mode=1
        wx.MiniFrame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
                          style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT)
        self.mode=mode
        if mode == 1: 
            self.viewer=viewer
            #self.SetTransparent(100)
        self.model=model # model #parent.model
        self.mdlwin=model.mdlwin
        self.draw=self.mdlwin.draw
        self.ctrlflag=model.ctrlflag
        # menu
        if self.mode == 0:
            self.menubar=self.MenuItems() # method of MyModel class
            self.SetMenuBar(self.menubar) # method of wxFrame class
            self.Bind(wx.EVT_MENU,self.OnMenu)
        # 
        self.bgcolor='light gray'
        #self.cubedataname=[]
        nulobj=CubeObj()        
        self.denobjdic={}; self.denobjdic[' ']=nulobj
        self.denobjlst=[] #[' ','den-cube-1','den-cube-2','den-cube-3']
        self.mepobjdic={}; self.mepobjdic[' ']=nulobj
        self.mepobjlst=[] #[' ','mep-cube-1','mep-cube-2','mep-cube-3']
        self.cubeobjdic={}; self.cubeobjdic[' ']=nulobj
        self.cubeobjlst=[]
        self.curden=' '
        self.curmep=' '
        self.curcube=' '
        #self.cubefile=''
        self.prptxt=['DENSITY','MEP','CUBE']
        self.property=0
        self.style=0 # 0:solid, 1:mesh
        self.ondraw=False
        self.superimpose=False
        self.xcubemin=0.0; self.xcubemax=0.0
        self.ycubemin=0.0; self.ycubemax=0.0
        self.zcubemin=0.0; self.zcubemax=0.0
        self.xcubecnt=0.0; self.ycubecnt=0.0; self.zcubecnt=0.0
        self.valuemin=0.0; self.valuemax=0.0
        self.nx=0; self.ny=0; self.nz=0
        # params for draw
        self.xmin=-1; self.xmax=-1
        self.ymin=-1; self.ymax=-1
        self.zmin=-1; self.zmax=-1
        self.value=0.05
        self.interpol=1
        self.minipo=1
        self.maxipo=4 # maximum degree of intepolation for cube data
        self.opacity=0.5 # 0-1        
        self.colortxt=['red','magenta','yellow','orange','brown','blue','cyan','green','purple',
                 'white','gray','black','---','palette']
        self.colorpos=self.colortxt[0]; self.rgbpos=const.RGBColor[self.colorpos]
        self.colorneg=self.colortxt[6]; self.rgbneg=const.RGBColor[self.colorneg]

        # polygons
        self.polyg=[]
        # create panel
        self.CreatePanel()
        self.SetParamsToWidgets()
        #
        if self.mode == 1: self.GetCubeFileAndMakeCubeObjDic()
        #
        self.Show()
        # activate event handlers
        self.Bind(wx.EVT_CLOSE,self.OnClose)

    def OpenInfoPanel(self):
        pos=self.GetPosition()
        winpos=pos; winsize=[80,40]
        self.tcinfo=wx.TextCtrl(None,-1,'',pos=winpos,size=winsize,style=wx.TE_MULTILINE)
        self.tcinfo.SetBackgroundColour('light gray')
        self.DispCubeDataInfo()
            
    def CreatePanel(self):
        size=self.GetClientSize()
        w=size[0]; h=size[1]
        hcb=const.HCBOX
        ff='%5.0f'
        # upper panel
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(w,h)) #ysize))
        self.panel.SetBackgroundColour(self.bgcolor)
        # cubedata
        yloc=5; xloc=5
        #btninfo=wx.Button(self.panel,wx.ID_ANY,"Data info",pos=(xloc,yloc-2),size=(70,20))
        #btninfo.Bind(wx.EVT_BUTTON,self.OnInfo)
        #btninfo.SetToolTipString('Display plot data information')
        # style
        #yloc += 25
        ststyle=wx.StaticText(self.panel,-1,label='Style:',pos=(xloc,yloc),size=(35,18))
        ststyle.SetToolTipString('Choose drawing style')
        yloc += 18
        self.rbtsold=wx.RadioButton(self.panel,-1,"solid",pos=(xloc+10,yloc),size=(50,18),
                                   style=wx.RB_GROUP)
        self.rbtsold.Bind(wx.EVT_RADIOBUTTON,self.OnSolid)
        yloc += 18
        self.rbtwire=wx.RadioButton(self.panel,-1,"wire",pos=(xloc+10,yloc),size=(50,18))
        self.rbtwire.Bind(wx.EVT_RADIOBUTTON,self.OnWire)
        self.rbtsold.SetValue(True)
        #
        yloc += 20
        wx.StaticText(self.panel,-1,"Value(abs):" ,pos=(xloc,yloc),size=(70,18))
        yloc += 20
        self.tcval=wx.TextCtrl(self.panel,-1,'',pos=(xloc+10,yloc),size=(70,18),
                              style=wx.TE_PROCESS_ENTER)
        self.tcval.Bind(wx.EVT_TEXT_ENTER,self.OnValue)
        self.tcval.SetToolTipString('Input value and "ENTER"')
        yloc += 25
        wx.StaticText(self.panel,-1,"Interp:" ,pos=(xloc,yloc),size=(45,18))
        self.spip=wx.SpinCtrl(self.panel,-1,value=str(self.interpol),pos=(xloc+45,yloc),size=(35,18),
                              style=wx.SP_ARROW_KEYS,min=self.minipo,max=self.maxipo)
        self.spip.Bind(wx.EVT_SPINCTRL,self.OnInterpolate)
        self.spip.SetToolTipString('Choose interpolation points number.')

        yloc += 20
        wx.StaticText(self.panel,-1,"Color:",pos=(xloc,yloc),size=(55,18))
        yloc += 20
        wx.StaticText(self.panel,-1,"+",pos=(xloc+5,yloc),size=(10,18))
        self.cbcolp=wx.ComboBox(self.panel,-1,'',choices=self.colortxt, \
                               pos=(xloc+20,yloc-3), size=(60,hcb),style=wx.CB_READONLY)             
        self.cbcolp.Bind(wx.EVT_COMBOBOX,self.OnColorPos)
        self.cbcolp.SetToolTipString('Choose color for positive value. "---" is dummy')

        yloc += 25
        wx.StaticText(self.panel,-1," -" ,pos=(xloc+5,yloc),size=(10,18))
        self.cbcoln=wx.ComboBox(self.panel,-1,'',choices=self.colortxt, \
                               pos=(xloc+20,yloc-3), size=(60,hcb),style=wx.CB_READONLY)              
        self.cbcoln.Bind(wx.EVT_COMBOBOX,self.OnColorNeg)
        self.cbcoln.SetToolTipString('Choose color for negative value. "---" is dummy')

        yloc += 25
        wx.StaticText(self.panel,-1,"Opacity:" ,pos=(xloc,yloc),size=(50,18))
        self.tcopa=wx.TextCtrl(self.panel,-1,('%4.2f' % self.opacity),pos=(xloc+50,yloc-2),size=(30,18),
                              style=wx.TE_PROCESS_ENTER)
        self.tcopa.SetToolTipString('Input opacity value (0-1) and "ENETR"')
        self.tcopa.Bind(wx.EVT_TEXT_ENTER,self.OnOpacity)
        
        #self.ckbimp.SetValue(self.superimpose)
        yloc += 20
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        #yloc += 25
        yloc += 8
        stobj=wx.StaticText(self.panel,-1,"Object:" ,pos=(xloc,yloc),size=(50,18))
        stobj.SetToolTipString('Choose object for operation')
        yloc += 18
        self.cmbobj=wx.ComboBox(self.panel,-1,'',choices=self.cubeobjlst, \
                               pos=(xloc+5,yloc), size=(75,hcb),style=wx.CB_READONLY)                      
        self.cmbobj.Bind(wx.EVT_COMBOBOX,self.OnObject)
        yloc += 25
        self.ckbimp=wx.CheckBox(self.panel,-1,"superimpose",pos=(xloc,yloc),size=(120,18))
        self.ckbimp.Bind(wx.EVT_CHECKBOX,self.OnSuperimpose)
        self.ckbimp.SetToolTipString('Check for superimpose')
        yloc += 25
        self.btndel=wx.Button(self.panel,wx.ID_ANY,"Del",pos=(xloc,yloc),size=(30,22))
        self.btndel.Bind(wx.EVT_BUTTON,self.OnRemove)
        self.btndel.SetToolTipString('Remove object')
        self.btndraw=wx.Button(self.panel,wx.ID_ANY,"Draw",pos=(xloc+40,yloc),size=(45,22))
        self.btndraw.Bind(wx.EVT_BUTTON,self.OnDraw)
        self.btndraw.SetToolTipString('Draw cube data(toggle "on"/"off")')
    
    def OnObject(self,event):
        print 'curobj',self.curobj
        self.curobj=self.ckbobj.GetValue().strip()
            
    def OnSuperimpose(self,event):
        self.superimpose=self.ckbimp.GetValue()
        print 'superimpose',self.superimpose
        
    def GetCubeFileAndMakeCubeObjDic(self):
        filename=self.viewer.GetCubeFile()
        if os.path.exists(filename):
            base,ext=os.path.splitext(filename)
            self.cubefile=filename
            if ext == '.den' or ext == '.mep' or ext == '.cub':
                err=self.AddToCubeObjDic(filename)
            else:
                mess='The file "'+filename+'" is not cube data (ext should be ".mep" or ".den"'
                lib.MessageBoxOK(mess,"")
                self.OnClose(1)
        else:
            mess='Cube file is not found. filename="'+filename+'"'
            lib.MessageBoxOK(mess,"")
            self.OnClose(1)   

    def GetDrawPanelParams(self):
        #self.ondraw=self.btndraw.GetValue()
        return [self.style,self.value,self.interpol,self.colorpos,self.colorneg,
                self.opacity,self.ondraw]

    def SetDrawPanelParams(self,params): 
        self.style=params[0]; self.value=params[1]; self.interpol=params[2]
        self.colorpos=params[3]; self.colorneg=params[4]; self.opacity=params[5]
        self.ondraw=params[6]
        self.SetParamsToWidgets()
    
    def SetParamsToWidgets(self):
        self.rbtsold.SetValue(True)
        if self.style == 1: self.rbtwire.SetValue(True)
        self.tcval.SetValue(str(self.value))
        self.spip.SetValue(self.interpol)
        self.cbcolp.SetValue(self.colorpos) #StringSelection(self.colorpos)
        self.cbcoln.SetValue(self.colorneg) #StringSelection(self.colorneg)
        self.tcopa.SetValue(str(self.opacity))
        #self.btndraw.SetValue(self.ondraw)
        self.ckbimp.SetValue(self.superimpose)
              
    def OpenMolViewWin(self):
        fum=fumodel.Model()
        # open main window (mdlwin)
        winpos=[-1,-1]; winsize=[400,300]
        fum.OpenMdlWin(self,winpos,winsize) # parent

        #mdlwin=fuview.View_Frm(self,winpos,winsize,self.model)
        return fum
                  
    def OnSolid(self,event):
        self.style=0
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
        
    def OnWire(self,event):
        self.style=1
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
        
    def OnXMin(self,event):
        value=self.tcxmin.GetValue()
        try: self.xmin=float(value)
        except:
            mess="error input for x.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnXMax(self,event):
        value=self.tcxmax.GetValue()
        try: self.xmax=float(value)
        except:
            mess="error input for x.range max. value."
            lib.MessageBoxOK(mess,"")     

    def OnYMin(self,event):
        value=self.tcymin.GetValue()
        try: self.ymin=float(value)
        except:
            mess="error input for y.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnYMax(self,event):
        value=self.tcymax.GetValue()
        try: self.ymax=float(value)
        except:
            mess="error input for y.range max. value."
            lib.MessageBoxOK(mess,"")     

    def OnZMin(self,event):
        value=self.tczmin.GetValue()
        try: self.zmin=float(value)
        except:
            mess="error input for z.range min. value."
            lib.MessageBoxOK(mess,"")     

    def OnZMax(self,event):
        value=self.tczmax.GetValue()
        try: self.zmax=float(value)
        except:
            mess="error input for z.range max. value."
            lib.MessageBoxOK(mess,"")     
        
    def OnValue(self,event):
        value=self.tcval.GetValue()
        try: self.value=float(value)
        except:
            mess="error input for Draw value."
            lib.MessageBoxOK(mess,"") 
            return    
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)

    def OnInterpolate(self,event):
        self.interpol=self.spip.GetValue()
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
         
    def OnOpacity(self,event):
        value=self.tcopa.GetValue()
        try: self.opacity=float(value)
        except:
            mess="error input for Opacity value (0-1)."
            lib.MessageBoxOK(mess,"") 
            return    
        #
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)

    def OnColorPos(self,event):
        color=self.cbcolp.GetValue()
        if color == '---': return
        self.rgbpos=self.GetColor(color,self.cbcolp)
        if len(self.rgbpos) <= 0: return
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1)
    
    def OnColorNeg(self,event):
        color=self.cbcoln.GetValue()
        if color == '---': return
        self.rgbneg=self.GetColor(color,self.cbcoln)
        if len(self.rgbneg) <= 0: return
        #if self.btndraw.GetValue(): self.OnDraw(1)
        if self.ondraw: self.OnDraw(1) 

    def GetColor(self,color,obj):
        if color == 'palette':
            obj.Disable(); obj.SetValue('---'); obj.Enable()
            rgbcol=lib.ChooseColorOnPalette(self,False,1.0) # parent,rgb255,opacity
            if len(rgbcol) <= 0: return []
            else: return rgbcol
        else: return const.RGBColor[color]
             
    def OnDensity(self,event):
        self.property=0
        self.cubcmb.SetItems(self.denobjlst)
        self.cubcmb.SetValue(self.curden)
        #
       
    def OnMEP(self,event):
        self.property=1
        self.cubcmb.SetItems(self.mepobjlst)
        self.cubcmb.SetValue(self.curmep)
        #

        
    def OnOthers(self,event):
        print 'property: others. not implemented yet.'
        self.property=2

    def MakePolygonData(self):  
        # make plolygon data
        # return polys: [polygon data]
        polys=[]
        #if self.property == 0: cubefile=self.denobjdic[self.curden].file
        #elif self.property == 1: cubefile=self.mepobjdic[self.curmep].file
        prop,obj=self.GetCurrentCubeObj()
        cubefile=obj.file
        if len(cubefile) <= 0:
            mess='No cube file for property='+prop
            lib.MessageBoxOK(mess,"MakePloygonData")              
            #self.btndraw.SetValue(False)
            #self.ondraw=False
            return []       
        value=self.value; intp=self.interpol
        try:
            polys=MC.CubePolygons(cubefile,value,intp)
        except:
            print 'Failed to create polygons in MakePolygonData.'
        return polys
  
    def OnInfo(self,event): 
        self.DispCubeDataInfo()
            
    def OnCubeData(self,event):
        if self.property == 0:
            self.curden=self.cubcmb.GetValue() #GetStringSelection()
        if self.property == 1:
            self.curmep=self.cubcmb.GetValue() #GetStringSelection()

    def GetCubeInfo(self):
        """ use GetCurrentCubeObj() instead """
        if self.property == 0:
            info=self.denobjdic[self.curden].info
        elif property == 1:
            attr=self.mepobjdic[self.curmep].info
        elif property == 2:
            attr=self.cubeobjdic[self.curcube].info
        return info    

    def SetCubeListToComboBox(self):
        if self.property == 0:
            info=self.denobjdic[self.curden].info
            objlst=self.denobjdic.keys()
            curdat=self.curden
        elif self.property == 1:
            info=self.mepobjdic[self.curmep].info
            objlst=self.mepobjdic.keys()
            curdat=self.curmep
        elif self.property == 2:
            info=self.cubepobjdic[self.curcube].info
            objlst=self.cubeobjdic.keys()
            curdat=self.curcube
            
        objlst.sort()
        #self.cubcmb.SetItems(objlst)
        #self.cubcmb.SetValue(curdat)
    @staticmethod        
    def MakeCubeDataInfoText(file,prop,natoms,info):
        f61='%6.1f'; f64='%6.4f'; fi4='%4d'
        #
        #prop,obj=self.GetCurrentCubeObj()
        #info=obj.info
        #file=obj.file
        #natoms=obj.natoms
        
        txt=[]
        txtprop='Property: '+prop+'\n'
        txtfile='Cube file: '+file+'\n'
        txtatm=' Number of atoms='+str(natoms)+'\n'
        txtcnt=' Center: x='+(f61 % info[0][0]).strip()
        txtcnt=txtcnt+',  y='+(f61 % info[0][1]).strip()
        txtcnt=txtcnt+',  z='+(f61 % info[0][2]).strip()+'\n'
        
        txtx=' x: min='+(f61 % info[1])+', max='+(f61 % info[2])+', nptx='+str(info[3])+'\n'
        txty=' y: min='+(f61 % info[4])+', max='+(f61 % info[5])+', npty='+str(info[6])+'\n'
        txtz=' z: min='+(f61 % info[7])+', max='+(f61 % info[8])+', nptz='+str(info[9])+'\n'

        txtval=' value: min= '+(f64 % info[10])
        txtval=txtval+', max= '+(f64 % info[11])+'\n'

        mess=txtprop+'\n'+txtfile+'\n'+txtatm+txtcnt+txtx+txty+txtz+'\n'+txtval
        return mess

    def DispCubeDataInfo(self):
        f61='%6.1f'; f64='%6.4f'; fi4='%4d'
        #
        prop,obj=self.GetCurrentCubeObj()
        info=obj.info
        file=obj.file
        natoms=obj.natoms
        
        txt=[]
        txtprop='Property: '+prop+'\n'
        txtfile='Cube file: '+file+'\n'
        txtatm=' Number of atoms='+str(natoms)+'\n'
        txtcnt=' Center: x='+(f61 % info[0][0]).strip()
        txtcnt=txtcnt+',  y='+(f61 % info[0][1]).strip()
        txtcnt=txtcnt+',  z='+(f61 % info[0][2]).strip()+'\n'
        
        txtx=' x: min='+(f61 % info[1])+', max='+(f61 % info[2])+', nptx='+str(info[3])+'\n'
        txty=' y: min='+(f61 % info[4])+', max='+(f61 % info[5])+', npty='+str(info[6])+'\n'
        txtz=' z: min='+(f61 % info[7])+', max='+(f61 % info[8])+', nptz='+str(info[9])+'\n'

        txtval=' value: min= '+(f64 % info[10])
        txtval=txtval+', max= '+(f64 % info[11])+'\n'

        mess=txtprop+'\n'+txtfile+'\n'+txtatm+txtcnt+txtx+txty+txtz+'\n'+txtval
        lib.MessageBoxOK(mess,"Cube data information")

    def GetCurrentCubeObj(self):
        if self.property == 0: return 'Density',self.denobjdic[self.curden]
        elif self.property == 1: return 'MEP',self.mepobjdic[self.curmep]
        elif self.property == 2: return 'Cube',self.cubeobjdic[self.curcube]

    def OnRemove(self,event):
        try:
            label='cube-data' 
            self.mdlwin.draw.DelDrawObj(label)
            self.TextMessage('',[])
            self.model.DrawMol(True)
        except: pass
        
    def OnDraw(self,event):
        f64='%6.4f'
        #if self.btndraw.GetValue(): #not self.ondraw: #
        test=True
        if test:
            # check molecular data in model
            if not self.model.mol:
                prop,obj=self.GetCurrentCubeObj()
                natoms=obj.natoms
                if natoms <= 0:
                    mess='No molecular data in model. Read structure data.'
                    lib.MessageBoxOK(mess,"DrawCubeData_Frm:OnDraw")              
                    #self.btndraw.SetValue(False)
                    self.ondraw=False
                    return
                else: 
                    self.BuildCubeMol()
                    name=self.model.mol.name
                    self.ConsoleMessage('"'+name+'" molecule was created using atom data in the cube file')                   
            label='cube-data'    
            # get value and opacity
            ###self.OnValue(1); self.OnOpacity(1)
            # parameters for draw
            params=[self.style,self.rgbpos,self.rgbneg,self.opacity]
            # make polygon data
            try: self.mdlwin.BusyIndicator('On','Making polygons ...')
            except: pass
            polyg=self.MakePolygonData()
            try: self.mdlwin.BusyIndicator('Off')
            except: pass
            if len(polyg) <= 0: return
            # set polyg data to view
            self.draw.SetDrawData(label,'CUBE',[params,polyg])
            # message
            mess='Drawing '+self.prptxt[self.property]+', value='+('%8.3f' % self.value)
            self.Message(mess,0,'')
            self.ConsoleMessage(mess)
            # text message
            prop,obj=self.GetCurrentCubeObj()
            name=obj.name; name=name.split('.')[0]
            mess=prop+':'+name+','+'value='+(f64 % self.value)
            self.model.DrawMol(True)
            self.TextMessage(mess,[])
            self.ondraw=True           
        else: 
            self.OnRemove(1)
            self.ondraw=False

    def BuildCubeMol(self):
        # create 'mol' instance
        mol=molec.Molecule(self.model) 
        #
        prop,obj=self.GetCurrentCubeObj()
        atmcc=obj.atmcc
        mol.name=obj.name
        mol.inpfile=obj.file       
        mol.SetAtoms(atmcc) 
        #       
        self.model.molctrl.Add(mol)
        # clear self.savecc
        self.model.savatmcc.Clear()
        nmol=self.model.molctrl.GetNumberOfMols()
        if nmol > 0: self.model.menuctrl.EnableMenu(True)
        if nmol > 1:
            drwitems=self.draw.GetDrawObjs()
            self.mol.SaveDrawItems(drwitems)            
        self.model.curmol,self.model.mol=self.model.molctrl.GetCurrentMol()
        # add bond 
        self.model.AddBondUseBondLength()
        #
        self.model.SetUpDraw(True)
    
    def OnClose(self,event):
        self.OnRemove(1)
        self.Destroy()

    def AddToCubeObjDic(self,filename):
        info,natoms,atmcc=self.ReadCubeFile(filename)
        if len(info) < 0: return 1
        head,name=os.path.split(filename)
        base,ext=os.path.splitext(name)
        if ext == '.mep': prp='MEP'
        elif ext == '.den': prp='Density'
        else: prp='Cube'
        # make cube object
        cube=CubeObj()
        cube.file=filename
        cube.info=info
        cube.name=name
        cube.atmcc=atmcc
        cube.natoms=natoms
        if prp == 'Density':
            self.denobjdic[name]=cube
            if self.denobjdic.has_key(' '): del self.denobjdic[' ']
            self.curden=name
            self.property=0
            #self.prprb1.SetValue(True)
        elif prp == 'MEP':
            self.mepobjdic[name]=cube
            if self.mepobjdic.has_key(' '): del self.mepobjdic[' ']
            self.curmep=name
            self.property=1
            #self.prprb2.SetValue(True)
        elif prp == 'Cube':
            self.cubeobjdic[name]=cube
            if self.cubeobjdic.has_key(' '): del self.cubeobjdic[' ']
            self.curcube=name
            self.property=2        
        return 0

    def ReadCubeFile(self,filename): # ,property):
        # read density and mep cube file
        # format: a comment and a blank lines are assumed at the head of the file
        # ' $END' line is needed at the end of the file.
        bhtoan=const.PysCon['bh2an']
        #
        info=[]; atmcc=[]; natoms=-1
        if not os.path.exists(filename):
            mess='file: '+filename+ 'not found.'
            lib.MessageBoxOK(mess,"ReadCubeFile")              
            return [],-1,[]
        f=open(filename,'r')
        # title and property
        """
        find=False; k=0
        while not find:
            s=f.readline()
            s=s.replace('\r',''); s=s.replace('\n','') 
            if s[:5] == ' $END': break
            item=s.split(':'); item[0]=item[0].strip()
            if s == '': k += 1
            else: k=0
            if k >= 10: break
            if item[0] == property: #'DENSITY':
                if property == 'DENSITY': prop=0
                if property == 'MEP': prop=1
                find=True; break
        if not find: return [],[] # -1,[],[]
        """
        # skip a comment line
        s=f.readline()
        # skip a blank line
        s=f.readline()
        # natoms,xmin,ymin,zmin
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split()
        natoms=int(item[0])
        xmin=float(item[1])
        ymin=float(item[2])
        zmin=float(item[3])
        # nx,dx, the same data for y and z
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); nx=int(item[0]); dx=float(item[1])
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); ny=int(item[0]); dy=float(item[2])
        s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','') 
        item=s.split(); nz=int(item[0]); dz=float(item[3])
        xmax=xmin+nx*dx; ymax=ymin+ny*dy; zmax=zmin+nz*dz
        center=[(xmax+xmin)/2.0,(ymax+ymin)/2.0,(zmax+zmin)/2.0]
        # atmcc, [[an, x,y, and z],...]
        for i in range(natoms):
            s=f.readline(); s=s.replace('\r',''); s=s.replace('\n','')             
            item=s.split()
            atmcc.append([int(item[0]),float(item[2])*bhtoan,float(item[3])*bhtoan,
                          float(item[4])*bhtoan])
        vmin=1000000.0; vmax=-1000000.0
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n',''); s=s.strip()
            if s == ' $END': break
            item=s.split()
            for val in item:
                try:
                    if float(val) > vmax: vmax=float(val)
                except: pass
                try:
                    if float(val) < vmin: vmin=float(val)
                except: pass
        f.close()
        #
        info.append(center)
        info.append(xmin); info.append(xmax); info.append(nx)
        info.append(ymin); info.append(ymax); info.append(ny)
        info.append(zmin); info.append(zmax); info.append(nz) 
        info.append(vmin); info.append(vmax)
        #
        return info,natoms,atmcc

    def OpenNotePad(self):
        if self.property == 0:
            filename=self.denobjdic[self.curden].file
        if self.property == 1:
            filename=self.mepobjdic[self.curmep].file
        if len(filename) <= 0:
            mess='cube file not found.'
            lib.MessageBoxOK(mess,"OpenNotePad")
        # open notepad
        else:
            lib.Editor(filename)
    
    def ConsoleMessage(self,mess):
        try: self.model.ConsoleMessage(mess)
        except: print mess
    
    def Message(self,mess,loc,col):
        try: self.model.Message(mess,loc,col)
        except: print mess
    
    def TextMessage(self,mess,color):
        try: self.model.TextMessage(mess,color)
        except: print mess
            
    def MenuItems(self):
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        submenu.Append(-1,"Open","Open...")
        submenu.AppendSeparator()
        submenu.Append(-1,"Quit","Quit...")
        menubar.Append(submenu,'File')
        # View
        submenu=wx.Menu()
        submenu.Append(-1,"Cube data","Edit/View cube data")
       
        return menubar

    def OnMenu(self,event):
        # menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
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
                            self.ConsoleMessage(filename+' file not found. skipped.')
                        else:
                            base,ext=os.path.splitext(filename)
                            if ext == '.den' or ext == '.mep':
                                err=self.AddToCubeObjDic(filename)
                                if not err:
                                    self.ConsoleMessage('Read cube file: '+filename)
                                    ndat += 1
                            else:
                                mess='Can not read file with extention: "'+ext+'"'
                                lib.MessageBoxOK(mess,"OnMenu")
                                continue
                mess=str(ndat)+' cube data were read.'
                self.ConsoleMessage(mess)

        if item == "Quit":
            self.OnClose(1)
        # Edit menu
        if item == "Cube data":
            self.OpenNotePad()    

class CubeObj():
    def __init__(self):
        # cube data object
        self.file=''  # null string
        self.name=' ' # a space
        # self.info: [center,xmin,xmax,nx,ymin,ymax,ny,zmin,zmax,nz,vmin,vmax]
        self.info=[[0.0,0.0,0.0], 0.0,0.0,0, 0.0,0.0,0, 0.0,0.0,0, 0.0,0.0]
        # self.atmcc: [[an,x,y,z],...]
        self.atmcc=[]
        self.natoms=-1

    def GetInfo(self):
        return self.info 
    
    def SetInfo(self,info):
        self.info=info
        
#class for Marching Cubes
class MC:
    midvtx = [
              [[0,0,0],[1,0,0]],
              [[0,1,0],[1,1,0]],
              [[0,0,0],[0,1,0]],
              [[1,0,0],[1,1,0]],
              [[0,0,1],[1,0,1]],
              [[0,1,1],[1,1,1]],
              [[0,0,1],[0,1,1]],
              [[1,0,1],[1,1,1]],
              [[0,0,0],[0,0,1]],
              [[1,0,0],[1,0,1]],
              [[0,1,0],[0,1,1]],
              [[1,1,0],[1,1,1]]
             ]

    cubepoly = [
                [],
                [[0,8,2]],
                [[3,9,0]],
                [[2,3,8],[3,9,8]],
                [[10,1,2]],
                [[8,10,0],[10,1,0]],
                [[0,3,9],[1,10,2]],
                [[1,3,9],[1,9,10],[8,10,9]],
                [[1,11,3]],
                [[3,1,11],[2,8,0]],
                [[0,1,9],[1,11,9]],
                [[2,1,11],[2,11,8],[9,8,11]],
                [[3,2,11],[2,10,11]],
                [[3,0,8],[3,8,11],[10,11,8]],
                [[0,2,10],[0,10,9],[11,9,10]],
                [[8,10,9],[9,10,11]],
                [[4,6,8]],
                [[0,4,2],[4,6,2]],
                [[8,4,6],[9,3,0]],
                [[9,4,6],[9,6,3],[2,3,6]],
                [[2,10,1],[6,4,8]],
                [[6,10,1],[6,1,4],[0,4,1]],
                [[0,3,9],[1,2,10],[4,6,8]],
                [[1,3,9],[1,9,10],[9,4,10],[4,6,10]],
                [[1,11,3],[4,6,8]],
                [[0,2,4],[2,4,6],[1,11,3]],
                [[0,9,1],[9,1,11],[4,6,8]],
                [[1,11,9],[1,9,2],[2,9,6],[4,6,9]],
                [[10,2,11],[2,11,3],[8,4,6]],
                [[6,10,11],[6,11,4],[4,11,0],[3,0,11]],
                [[0,2,1],[2,10,9],[9,10,11],[4,6,8]],
                [[9,4,6],[10,9,6],[9,10,11]],
                [[9,7,4]],
                [[4,9,7],[0,2,8]],
                [[4,0,7],[0,3,7]],
                [[4,8,2],[4,2,7],[3,7,2]],
                [[9,7,4],[10,1,2]],
                [[8,0,10],[0,10,1],[9,7,4]],
                [[3,0,7],[0,7,4],[2,10,1]],
                [[1,3,7],[1,7,10],[10,7,8],[4,8,7]],
                [[11,3,1],[9,4,7]],
                [[3,1,11],[2,0,8],[7,4,9]],
                [[1,11,7],[4,1,7],[1,4,0]],
                [[2,1,11],[2,11,8],[11,7,8],[7,4,8]],
                [[10,3,11],[2,10,3],[7,4,9]],
                [[3,0,2],[0,8,11],[11,8,10],[7,4,9]],
                [[2,10,11],[2,11,0],[0,11,4],[7,4,11]],
                [[7,4,8],[7,8,11],[10,11,8]],
                [[8,9,6],[9,7,6]],
                [[0,9,7],[0,7,2],[6,2,7]],
                [[8,0,3],[8,3,6],[7,6,3]],
                [[2,3,6],[6,3,7]],
                [[8,6,9],[6,9,7],[10,1,2]],
                [[9,7,6],[9,6,0],[0,6,1],[10,1,6]],
                [[8,0,9],[0,3,6],[6,3,7],[10,1,2]],
                [[6,10,1],[3,6,1],[6,3,7]],
                [[8,7,9],[6,8,7],[3,1,11]],
                [[0,9,4],[9,7,2],[2,7,6],[1,11,3]],
                [[0,1,11],[7,0,11],[6,0,7],[0,6,8]],
                [[1,11,7],[1,7,2],[6,2,7]],
                [[2,10,3],[3,10,11],[6,8,7],[7,8,9]],
                [[3,0,11],[0,10,11],[7,0,9],[6,0,7],[0,6,10]],
                [[8,0,6],[0,7,6],[10,0,2],[11,0,10],[0,11,7]],
                [[7,10,11],[7,6,10]],
                [[6,5,10]],
                [[10,6,5],[8,0,2]],
                [[6,5,10],[3,9,0]],
                [[2,8,3],[8,3,9],[6,5,10]],
                [[2,6,1],[6,5,1]],
                [[8,6,5],[8,5,0],[1,0,5]],
                [[2,1,6],[1,6,5],[3,9,0]],
                [[6,5,1],[6,1,8],[8,1,9],[3,9,1]],
                [[5,10,6],[1,3,11]],
                [[10,6,5],[8,2,0],[11,3,1]],
                [[0,11,1],[9,0,11],[10,6,5]],
                [[2,1,3],[1,11,8],[8,11,9],[6,5,10]],
                [[6,5,11],[3,6,11],[6,3,2]],
                [[8,6,5],[8,5,0],[5,11,0],[11,3,0]],
                [[2,6,5],[11,2,5],[9,2,11],[2,9,0]],
                [[6,5,11],[6,11,8],[9,8,11]],
                [[10,8,5],[8,4,5]],
                [[10,2,0],[10,0,5],[4,5,0]],
                [[4,8,5],[8,5,10],[0,3,9]],
                [[9,4,5],[9,5,3],[3,5,2],[10,2,5]],
                [[2,8,4],[2,4,1],[5,1,4]],
                [[0,4,1],[1,4,5]],
                [[2,8,6],[8,4,1],[1,4,5],[3,9,0]],
                [[1,3,9],[4,1,9],[1,4,5]],
                [[4,10,5],[8,4,10],[11,3,1]],
                [[10,2,8],[2,0,5],[5,0,4],[11,3,1]],
                [[8,4,10],[10,4,5],[9,0,11],[11,0,1]],
                [[10,2,5],[2,4,5],[11,2,1],[9,2,11],[2,9,4]],
                [[8,4,5],[8,5,2],[2,5,3],[11,3,5]],
                [[11,3,0],[11,0,5],[4,5,0]],
                [[0,2,9],[2,11,9],[4,2,8],[5,2,4],[2,5,11]],
                [[11,4,5],[11,9,4]],
                [[7,4,9],[6,10,5]],
                [[4,9,7],[0,8,2],[5,10,6]],
                [[3,4,7],[0,3,4],[5,10,6]],
                [[4,8,0],[8,2,7],[7,2,3],[5,10,6]],
                [[2,5,6],[1,2,5],[4,9,7]],
                [[8,6,10],[6,5,0],[0,5,1],[9,7,4]],
                [[0,3,4],[4,3,7],[1,2,5],[5,2,6]],
                [[4,8,7],[8,3,7],[5,8,6],[1,8,5],[8,1,3]],
                [[5,10,6],[1,11,3],[4,9,7]],
                [[0,8,2],[1,11,3],[4,9,7],[5,10,6]],
                [[11,7,9],[7,4,1],[1,4,0],[10,6,5]],
                [[4,10,6],[4,8,2],[1,4,2],[1,4,10],[5,11,7]],
                [[5,11,1],[11,3,6],[6,3,2],[4,9,7]],
                [[3,4,9],[3,0,8],[6,3,8],[6,3,4],[7,5,11]],
                [[4,11,7],[4,0,11],[5,11,6],[6,11,2],[0,2,11]],
                [[7,4,11],[6,5,11],[6,11,8],[4,11,8]],
                [[9,7,5],[10,9,5],[9,10,8]],
                [[0,9,7],[0,7,2],[7,5,2],[5,10,2]],
                [[0,3,7],[0,7,8],[8,7,10],[5,10,7]],
                [[5,10,2],[5,2,7],[3,7,2]],
                [[8,9,7],[5,8,7],[1,8,5],[8,1,2]],
                [[9,7,5],[9,5,0],[1,0,5]],
                [[2,8,1],[8,5,1],[3,8,0],[7,8,3],[8,7,5]],
                [[5,3,7],[5,1,3]],
                [[7,5,6],[5,10,9],[9,10,8],[3,1,11]],
                [[10,3,1],[10,2,0],[9,10,0],[9,10,3],[11,7,5]],
                [[10,7,5],[10,8,7],[11,7,1],[1,7,0],[8,0,7]],
                [[5,10,7],[1,11,7],[1,7,2],[10,7,2]],
                [[3,5,11],[3,2,5],[7,5,9],[9,5,8],[2,8,5]],
                [[11,3,5],[9,7,5],[9,5,0],[3,5,0]],
                [[2,8,0],[11,7,5]],
                [[11,7,5]],
                [[5,7,11]],
                [[0,8,2],[5,7,11]],
                [[5,7,11],[3,0,9]],
                [[2,9,3],[8,2,9],[11,5,7]],
                [[7,11,5],[10,2,1]],
                [[8,1,10],[0,8,1],[5,7,11]],
                [[1,2,10],[0,3,9],[5,7,11]],
                [[1,3,0],[3,9,10],[10,9,8],[5,7,11]],
                [[7,3,5],[3,1,5]],
                [[1,3,5],[3,5,7],[0,8,2]],
                [[5,7,9],[0,5,9],[5,0,1]],
                [[1,5,7],[9,1,7],[8,1,9],[1,8,2]],
                [[2,10,5],[7,2,5],[2,7,3]],
                [[0,8,10],[0,10,3],[3,10,7],[5,7,10]],
                [[0,2,10],[0,10,9],[10,5,9],[5,7,9]],
                [[5,7,9],[5,9,10],[8,10,9]],
                [[11,5,7],[4,8,6]],
                [[0,6,4],[2,0,6],[7,11,5]],
                [[9,0,3],[8,4,6],[11,5,7]],
                [[9,4,8],[4,6,3],[3,6,2],[11,5,7]],
                [[6,8,4],[2,10,1],[7,11,5]],
                [[6,10,2],[10,1,4],[4,1,0],[7,11,5]],
                [[3,9,0],[2,10,1],[7,11,5],[6,8,4]],
                [[6,11,5],[6,10,1],[3,6,1],[3,6,11],[7,9,4]],
                [[7,5,3],[5,3,1],[6,8,4]],
                [[2,0,6],[6,0,4],[3,1,7],[7,1,5]],
                [[11,7,9],[0,5,7],[1,5,0],[4,6,8]],
                [[6,9,4],[6,2,9],[7,9,5],[5,9,1],[2,1,9]],
                [[1,10,5],[7,2,10],[3,2,7],[6,8,4]],
                [[7,10,5],[7,3,10],[6,10,4],[4,10,0],[3,0,10]],
                [[7,8,4],[7,9,0],[2,7,0],[2,7,8],[6,10,5]],
                [[9,5,7],[9,4,6],[10,9,6],[10,9,5]],
                [[5,4,11],[4,9,11]],
                [[9,4,11],[4,11,5],[8,2,0]],
                [[0,3,11],[5,0,11],[0,5,4]],
                [[8,2,3],[8,3,4],[4,3,5],[11,5,3]],
                [[5,11,4],[11,4,9],[1,2,10]],
                [[0,8,1],[1,8,10],[4,9,5],[5,9,11]],
                [[9,3,11],[5,0,3],[4,0,5],[1,2,10]],
                [[5,3,11],[5,4,3],[1,3,10],[10,3,8],[4,8,3]],
                [[9,3,1],[9,1,4],[5,4,1]],
                [[7,9,3],[1,4,9],[5,4,1],[0,8,2]],
                [[5,4,1],[1,4,0]],
                [[4,8,2],[1,4,2],[4,1,5]],
                [[5,4,9],[3,5,9],[2,5,3],[5,2,10]],
                [[9,3,4],[3,5,4],[8,3,0],[10,3,8],[3,10,5]],
                [[0,2,10],[5,0,10],[0,5,4]],
                [[5,8,10],[5,4,8]],
                [[11,5,6],[8,11,6],[11,8,9]],
                [[9,11,5],[6,9,5],[2,9,6],[9,2,0]],
                [[8,0,3],[8,3,6],[3,11,6],[11,5,6]],
                [[11,5,6],[11,6,3],[2,3,6]],
                [[7,5,6],[8,11,5],[9,11,8],[10,1,2]],
                [[1,6,10],[1,0,6],[5,6,11],[11,6,9],[0,9,6]],
                [[5,2,10],[5,6,8],[0,5,8],[0,5,2],[1,3,11]],
                [[6,11,5],[6,10,1],[3,6,1],[3,6,11]],
                [[6,8,9],[6,9,5],[5,9,1],[3,1,9]],
                [[0,9,2],[9,6,2],[1,9,3],[5,9,1],[9,5,6]],
                [[5,6,8],[0,5,8],[5,0,1]],
                [[1,6,2],[1,5,6]],
                [[10,5,2],[5,3,2],[8,5,6],[9,5,8],[5,9,3]],
                [[10,5,6],[0,9,3]],
                [[5,2,10],[5,6,8],[0,5,8],[0,5,2]],
                [[10,5,6]],
                [[11,10,7],[10,6,7]],
                [[6,10,7],[10,7,11],[2,0,8]],
                [[11,7,10],[7,10,6],[9,0,3]],
                [[8,2,9],[9,2,3],[10,6,11],[11,6,7]],
                [[7,11,1],[2,7,1],[7,2,6]],
                [[6,7,11],[1,6,11],[0,6,1],[6,0,8]],
                [[5,11,1],[2,7,11],[6,7,2],[3,9,0]],
                [[9,1,3],[9,8,1],[11,1,7],[7,1,6],[8,6,1]],
                [[1,10,6],[1,6,3],[7,3,6]],
                [[11,1,10],[6,3,1],[7,3,6],[2,0,8]],
                [[9,0,1],[9,1,7],[7,1,6],[10,6,1]],
                [[2,1,8],[1,9,8],[6,1,10],[7,1,6],[1,7,9]],
                [[7,3,6],[6,3,2]],
                [[3,0,8],[6,3,8],[3,6,7]],
                [[7,9,0],[2,7,0],[7,2,6]],
                [[6,9,8],[6,7,9]],
                [[8,4,7],[11,8,7],[8,11,10]],
                [[2,0,4],[2,4,10],[10,4,11],[7,11,4]],
                [[6,4,7],[11,8,4],[10,8,11],[9,0,3]],
                [[11,4,7],[11,10,4],[9,4,3],[3,4,2],[10,2,4]],
                [[2,8,4],[2,4,1],[4,7,1],[7,11,1]],
                [[7,11,1],[7,1,4],[0,4,1]],
                [[11,0,3],[11,1,2],[8,11,2],[8,11,0],[9,4,7]],
                [[1,7,11],[1,3,9],[4,1,9],[4,1,7]],
                [[7,3,1],[10,7,1],[8,7,10],[7,8,4]],
                [[1,10,3],[10,7,3],[0,10,2],[4,10,0],[10,4,7]],
                [[4,7,8],[7,10,8],[0,7,9],[1,7,0],[7,1,10]],
                [[4,7,9],[2,1,10]],
                [[2,8,4],[7,2,4],[2,7,3]],
                [[7,0,4],[7,3,0]],
                [[7,8,4],[7,9,0],[2,7,0],[2,7,8]],
                [[4,7,9]],
                [[6,4,9],[6,9,10],[11,10,9]],
                [[5,6,4],[9,10,6],[11,10,9],[8,2,0]],
                [[11,10,6],[4,11,6],[0,11,4],[11,0,3]],
                [[6,4,10],[4,11,10],[2,4,8],[3,4,2],[4,3,11]],
                [[1,2,6],[1,6,11],[11,6,9],[4,9,6]],
                [[8,6,0],[6,1,0],[9,6,4],[11,6,9],[6,11,1]],
                [[3,11,0],[11,4,0],[2,11,1],[6,11,2],[11,6,4]],
                [[3,11,1],[8,6,4]],
                [[1,10,6],[1,6,3],[6,4,3],[4,9,3]],
                [[9,2,0],[9,3,1],[10,9,1],[10,9,2],[8,6,4]],
                [[1,10,6],[4,1,6],[1,4,0]],
                [[1,8,2],[1,10,6],[4,1,6],[4,1,8]],
                [[6,4,9],[3,6,9],[6,3,2]],
                [[6,0,8],[6,4,9],[3,6,9],[3,6,0]],
                [[2,4,0],[2,6,4]],
                [[8,6,4]],
                [[11,10,9],[9,10,8]],
                [[10,2,0],[9,10,0],[10,9,11]],
                [[8,0,3],[11,8,3],[8,11,10]],
                [[11,2,3],[11,10,2]],
                [[11,1,2],[8,11,2],[11,8,9]],
                [[9,1,0],[9,11,1]],
                [[11,0,3],[11,1,2],[8,11,2],[8,11,0]],
                [[3,11,1]],
                [[9,3,1],[10,9,1],[9,10,8]],
                [[9,2,0],[9,3,1],[10,9,1],[10,9,2]],
                [[0,10,8],[0,1,10]],
                [[2,1,10]],
                [[8,3,2],[8,9,3]],
                [[0,9,3]],
                [[2,8,0]],
                []
               ]

    # make polygon data from grid data
    @staticmethod
    def MakePolygons( moval, ex, ey, ez, boxmin,  thres, ndiv ):
        try:
            nx = len(moval)
            ny = len(moval[0])
            nz = len(moval[0][0])

            # interpolation
            nxdiv = (nx-1) * ndiv + 1
            nydiv = (ny-1) * ndiv + 1
            nzdiv = (nz-1) * ndiv + 1
            movaldiv = [[[0.0 for k in range(nzdiv)] for j in range(nydiv)] for i in range(nxdiv)]

            weight = [[[None for k in range(ndiv+1)] for j in range(ndiv+1)] for i in range(ndiv+1)]
            for ixdiv in range(0, ndiv+1):
                for iydiv in range(0, ndiv+1):
                    for izdiv in range(0, ndiv+1):
                        w = [[[0.0 for k in range(2)] for j in range(2)] for i in range(2)]
                        x = [0.0 for k in range(2)]
                        y = [0.0 for k in range(2)]
                        z = [0.0 for k in range(2)]
                        x[0] = float(ixdiv) / ndiv
                        y[0] = float(iydiv) / ndiv
                        z[0] = float(izdiv) / ndiv
                        x[1] = 1.0 - x[0]
                        y[1] = 1.0 - y[0]
                        z[1] = 1.0 - z[0]
                        for jx in range(2):
                            for jy in range(2):
                                for jz in range(2):
                                    w[jx][jy][jz] = x[1-jx] * y[1-jy] * z[1-jz]
                        weight[ixdiv][iydiv][izdiv] = w;

            for ix in range(nx-1):
                for iy in range(ny-1):
                    for iz in range(nz-1):
                        for ixdiv in range(ndiv+1):
                            for iydiv in range(ndiv+1):
                                for izdiv in range(ndiv+1):
                                    w = weight[ixdiv][iydiv][izdiv]
                                    v = 0.0
                                    for jx in range(2):
                                        for jy in range(2):
                                            for jz in range(2):
                                                v += moval[ix+jx][iy+jy][iz+jz] * w[jx][jy][jz]

                                    ixx = ix * ndiv + ixdiv
                                    iyy = iy * ndiv + iydiv
                                    izz = iz * ndiv + izdiv
                                    movaldiv[ixx][iyy][izz] = v
            moval = movaldiv
            nx = nxdiv
            ny = nydiv
            nz = nzdiv
            ex /= ndiv
            ey /= ndiv
            ez /= ndiv

            # determine each vertices wherther in/out of the threshold surface
            bvtx = [[[0 for k in range(nz)] for j in range(ny)] for i in range(nx)]
            for ix in range(0, nx):
                for iy in range(0, ny):
                    for iz in range(0, nz):
                        if moval[ix][iy][iz] > thres:
                            bvtx[ix][iy][iz] = 1

            polygons = []
            for ix in range(0, nx-1):
                for iy in range(0, ny-1):
                    for iz in range(0, nz-1):
                        posxyz = array([ix,iy,iz])
                        icube = 0
                        ibit = 1
                        for k in range(0, 2):
                            for j in range(0, 2):
                                for i in range(0, 2):
                                    icube += bvtx[ix+i][iy+j][iz+k] * ibit
                                    ibit *= 2

                        polys = MC.cubepoly[icube]
                        for triangle in polys:
                            midpos = []
                            for imid in range(0,3):
                                vtxs = MC.midvtx[ triangle[imid] ]
                                pos0 = array(vtxs[0])
                                pos1 = array(vtxs[1])
                                moval0 = moval[ix+vtxs[0][0]][iy+vtxs[0][1]][iz+vtxs[0][2]]
                                moval1 = moval[ix+vtxs[1][0]][iy+vtxs[1][1]][iz+vtxs[1][2]]
                                dif01 = moval0 - moval1
                                if dif01 * dif01 < 1e-20:
                                    pos = ( pos0 + pos1 ) * 0.5
                                else:
                                    dif0 = moval0 - thres
                                    dif1 = moval1 - thres
                                    pos = ( dif0 * pos1 - dif1 * pos0 ) / dif01
                                pos += posxyz
                                pos = pos[0] * ex + pos[1] * ey + pos[2] * ez
                                pos += boxmin
                                midpos.append( pos )

                            vec01 = midpos[1] - midpos[0]
                            vec02 = midpos[2] - midpos[0]
                            vnorm = cross(vec02, vec01)
                            v = linalg.norm(vnorm)
                            if v < 1e-10:
                                continue
                            vnorm /= v

                            midpos0 = midpos[0].tolist()
                            midpos1 = midpos[1].tolist()
                            midpos2 = midpos[2].tolist()
                            vnorm   = vnorm.tolist()
                            polygons.append( [ midpos0, midpos1, midpos2, vnorm ] )

        except BaseException, e:
            print e
            print "Failed to Make polygon data"
            return []

        return polygons

    # read cube file and return polygon data
    @staticmethod
    def CubePolygons( cubefile, thres, ndiv ):

        try:
            # read cube file
            f = open(cubefile, 'r')

            # comment
            line = f.readline()
            line = f.readline()

            # # of atoms, origin
            line = f.readline()
            vals = line.split()
            natm = int( vals[0] )
            boxmin = array( [ float(vals[1]), float(vals[2]), float(vals[3]) ] )

            # # of grids, cell size
            line = f.readline()
            vals = line.split()
            nx = int( vals[0] )
            ex = array( [ float(vals[1]), float(vals[2]), float(vals[3]) ] )
            line = f.readline()
            vals = line.split()
            ny = int( vals[0] )
            ey = array( [ float(vals[1]), float(vals[2]), float(vals[3]) ] )
            line = f.readline()
            vals = line.split()
            nz = int( vals[0] )
            ez = array( [ float(vals[1]), float(vals[2]), float(vals[3]) ] )

            # bohr to angstrom
            ex *= 0.529177249
            ey *= 0.529177249
            ez *= 0.529177249
            boxmin *= 0.529177249

            # position of atoms
            for i in range(natm):
                line = f.readline()

            # values
            vals = []
            while line:
                line = f.readline()
                vals.extend( line.split() )

            # pack into 3D array
            moval = [[[0.0 for k in range(nz)] for j in range(ny)] for i in range(nx)]
            ixyz = 0
            for ix in range(0, nx):
                for iy in range(0, ny):
                    for iz in range(0, nz):
                        v = float( vals[ixyz] )
                        moval[ix][iy][iz] = v
                        ixyz += 1

            f.close()

        except BaseException, e:
            print e
            print "File Read Error : ", cubefile
            return []

        try:
            maxpoly = 1000000
            polys1, npoly1 = fucubelib.make_polygons( moval, ex, ey, ez, boxmin,  thres, ndiv, maxpoly )
            if npoly1 == maxpoly:
                raise
            polys1 = polys1[:npoly1]
            polys2, npoly2 = fucubelib.make_polygons( moval, ex, ey, ez, boxmin, -thres, ndiv, maxpoly )
            if npoly2 == maxpoly:
                raise
            polys2 = polys2[:npoly2]
        except BaseException, e:
            print e
            print 'Failed to make polygons by fortran, try python routine'
            polys1 = MC.MakePolygons( moval, ex, ey, ez, boxmin,  thres, ndiv )
            polys2 = MC.MakePolygons( moval, ex, ey, ez, boxmin, -thres, ndiv )

        return [ polys1, polys2 ]

