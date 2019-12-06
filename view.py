#!/bin/sh
# -*- coding: utf-8

# fumodel Version histrory
# ver.0.1.2 (20Feb2014)

import sys
sys.path.insert(0,'.')
import wx
import os
import shutil
# import psutil
import datetime
import time
import platform
import subprocess
import functools
import threading
import glob
import numpy
import copy
import cPickle as pickel
import wx.glcanvas
import wx.py.crust
#from wx.lib.splitter import MultiSplitterWindow
import scipy
if int(scipy.__version__.split('.')[1]) >= 11:
    from scipy.sparse.csgraph import _validation # need for pyinstaller
    from scipy.optimize import minimize # need for pyinstaller
from operator import itemgetter

import const
import lib
import molec
import subwin
import ctrl
import draw
import graph
import cube
#try: import fortlib
#except: pass 
#import fmopdb
try: import fmopdb
except: pass
import fumodel

class View_Frm(wx.Frame):
    # fumodel Main Window
    """ Main window of fumodel
    
    :param obj parent: parent window object
    :param lst winpos: window position list, [x(int),y(int)]
    :param lst winsize: window size list, [width(int),hight(int)]
    :param obj model: controller object, 'model'(a instance of 'Model' class) is controller for fumodel
    """
    def __init__(self,parent,id,winpos=[],winsize=[]): #,model):
        #winsize=(640,400)
        super(View_Frm,self).__init__(parent,id,pos=winpos,size=winsize,
                                      name='FUMDLWIN')
        self.parent=parent
        # controller
        #elf.model=model
        self.model=parent
        # controllers
        self.winctrl=None
        self.draw=None
        self.canvas=None
        self.title=''
        #
        self.mousemode=None
        self.molchoice=None
        self.setctrl=None
        self.mousectrl=None
        self.menuctrl=None
        #
        self.textmess=None
        self.textmessage=''
        self.textcolor=[]
        #
        self.windowposition=winpos
        self.windowsize=winsize
        #
        self.textfont = wx.Font(8, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier 10 Pitch')
        self.font1 = wx.Font(10, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Consolas')
        self.textcol='black'
        # set frame font
        lib.SetFrameFont(self)
        """
        self.font=self.GetFont()
        
        print 'font family',self.font.GetFamily()
        print 'font size',self.font.GetPointSize()
        print 'font size',self.font.GetFaceName()
        self.font1 = wx.Font(8, wx.ROMAN, wx.NORMAL, wx.NORMAL, False, u'Roman')
        #self.font.SetPointSize(8)
        self.SetFont(self.font1)
        """
        
        #
        self.autoopenmolwin=True
        #self.molwinshape=0
        self.molwinshape=self.model.setctrl.GetParam('molchoice-win-shape')
        #self.muswinshape=0
        self.muswinshape=self.model.setctrl.GetParam('mousemode-win-shape')
        #
        self.winopendic={}
        self.fmomenu=False
        #!!!self.addmenu1=[]; self.addmenu2=[]
        #  initial setting, current status
        self.shlwin=True; self.openshlwin=True; self.hideshlwin=False
        self.molwin=True; self.openmolwin=False
        self.muswin=True; self.openmuswin=False
        self.remwin=False; self.openremwin=False
        self.remarkwin=None
        self.fmomenu=False
        self.Addmenu=False
        
        # Create StatusBar
        self.statusbar=self.CreateStatusBar()
        self.statusbar.SetFieldsCount(3)
        self.statusbar.SetStatusWidths([-8,-2,-1])      

        self.busyind=0
        self.busycount=0
        self.busyindicator=None
        #self.CreateBysyIndicator()
        self.BusyIndicator('Open')
        self.busyindicator.Bind(wx.EVT_LEFT_DOWN,self.ResetBusyIndicator)
        #self.BusyIndicator('Open')
        
        self.Show()
        
    def CreateViewPanel(self,model,fumode):
        # model(ins): Model instance
        # fumode(int): 0:for fumodel, 1:for fuplot     
        self.model=model
        self.setctrl=model.setctrl
        self.bgcolor=self.setctrl.GetParam('win-color') #bgcolor
        #self.fumode=fumode # fumode=0 for fumodel and =1 for fuPlot
        #self.fmomenu=fmomenu #fmomenu
        self.winctrl=model.winctrl
        self.mousectrl=model.mousectrl
        self.menuctrl=model.menuctrl
        #xxself.ctrlflag=model.ctrlflag
        self.title=self.model.fuversion
        lib.AttachIcon(self,const.FUMODELICON) # icon
        #
        self.framesize=self.GetClientSize()
        self.canvassize=[]
        # Create MenuBar
        fmomenu=self.model.setctrl.GetParam('fmo-menu') #fmomenu
        addon1menu=self.model.setctrl.GetParam('add-on1-menu') #addon1menu
        addon2menu=self.model.setctrl.GetParam('add-on2-menu') #addon2menu
        self.menuctrl.CreateMenuBar(fumode,fmomenu,addon1menu,addon2menu)
        self.SetMenuBar(self.menuctrl.menubar) # set menubar on the frame
        """ project. disabled 06Jan2016. Uncomment the following bloch for revive
        # project menu (post edit menu items)
        self.menuctrl.CreateProjectMenuItems()
        curprj=self.setctrl.GetCurPrj()
        self.menuctrl.CheckMenu(curprj,True)
        """
        # file history menu (post edit menu items)
        if self.model.filehistory.GetNumberOfData() > 0:
            self.menuctrl.CreateFileHistoryMenuItems()
        # Rmove FMO menu?
        if not self.model.setctrl.GetParam('fmo-menu'):
            self.menuctrl.RemoveMenuItem('FMO data')
        self.popmenu=None # PopupMenu
        #XXX#if not self.model.Ready(): self.menuctrl.EnableMenu(False)
        self.menuctrl.CheckMenu("Enable MessageBoxOK",True)

        # accept drop files
        droptarget=lib.DropFileTarget(self)
        self.SetDropTarget(droptarget)
        #self.canvas=draw.GLCanvas(self)
        
        self.draw=draw.MolDraw(self)
        self.canvas=self.draw.canvas
        self.model.draw=self.draw
        #self.canvas=draw.GLCanvas(self.draw) #self)
        # activate event handler for thread execution
        #subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)
        # set title
        self.SetTitle(self.title)
        self.winopendic={} # windows status flags
        # open mouse mode setting panel
        self.mousemode=MouseMode(self)
        if self.muswin: 
            self.mousemode.ChangeShape(self.muswinshape)
            self.OpenMouseModeWin()
        # molecule choice panel
        self.molchoice=MolChoice(self)
        if self.molwin: 
            self.molchoice.ChangeShape(self.molwinshape)
            self.OpenMolChoiceWin()
        # open pyshell win
        if self.shlwin:
            self.model.menuctrl.OnWindow('Open PyShell',True)
            #pyshell=self.model.winctrl.GetWin('Open PyShell')
            ##pyshell.Bind(wx.EVT_SIZE,self.OnResizePyShell)
        # set up  text message instance, 'textmess'
        self.SetUpTextMessage()
        # initialize glcanvas
        self.draw.Paint()
        # window event handlers
        self.Bind(wx.EVT_MENU,self.OnMenu)
        #
        self.Bind(wx.EVT_SET_FOCUS,self.OnFocus)
        #self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnterWindow)
        #??self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeaveWindow)
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_MOVE,self.OnMove)
        
        self.Bind(wx.EVT_ERASE_BACKGROUND,self.OnEraseBG)
        
        self.Bind(wx.EVT_ICONIZE,self.OnIconize)
        # mouse event handler
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        ###self.Bind(wx.EVT_MOTION,self.OnMouseMove)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        self.Bind(wx.EVT_RIGHT_UP,self.OnMouseRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnMouseLeftDClick)
        # keyboard event handlers
        self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown)   
        self.Bind(wx.EVT_KEY_UP,self.OnKeyUp)

    def OpenDropFiles(self,filenames):
        if len(filenames) <= 0: return
        extlst=['all']
        filelst=lib.ExpandFilesInDirectory(filenames,extlst)
        #
        for file in filelst:
            head,ext=os.path.splitext(file)
            if ext == '.gz': file=lib.ZipUnzipFile(file,False)
            self.model.ReadFiles(file,True,drop=True)
        
    def SetUpTextMessage(self):
        self.textmess=TextMessage(self,'update') # create a instance of 'TextMessage' class
        self.textmess.SetWinBGColor([]) # default: 'mdlwin' bgcolor
        self.textmess.SetTextBGColor([]) # default: yellow
        self.textmess.SetPos([10,80])

    def SetAutoOpenMolWin(self,on):
        if on: self.autoopenmolwin=True
        else: self.autoopenmolwin.False

    def GetAutoOpenMolWin(self):
        return self.autoopenmolwin

    def IsAutoOpenMolWin(self):
        return self.autoopenmolwin

    def SetMolWinFlag(self,on):
        if on: self.molwin=True
        else: self.molwin=False

    def SetMusWinFlag(self,on):
        if on: self.muswin=True
        else: self.muswin=False

    def SetRemWinFlag(self,on):
        if on: self.remwin=True
        else: self.remwin=False

    def IsMolWinOpen(self):
        return self.openmolwin

    def IsMusWinOpen(self):
        return self.openmuswin

    def IsRemWinOpen(self):
        return self.openremwin

    def SetMolChoiceWinShape(self,shape):
        if shape < 0 or shape > 1: return
        self.molwinshape=shape

    def SetMouseModeWinShape(self,shape):
        if shape < 0 or shape > 1: return
        self.muswinshape=shape
    
    def ChangeMouseModeWinBGColor(self,color=''):
        if len(color) == 0: color='light gray'
        self.mousemode.win.bgcolor=color
        self.mousemode.win.SetBackgroundColour(color)
        self.mousemode.win.Refresh()
                
    def ChangeAppearance(self,winsize,bgcolor,molwinshape,muswinshape,fmomenu,addonmenu):
        # not completed yet
        self.winsize=winsize
        self.bgcolor=bgcolor
        if self.openmdlwin: self.mdlwin.Destroy()
        fumode=0
        self.mdlwin.OpenMdlWin(self,fumode,fmomenu)
            
    def OnIconize(self,event):
        iconized=event.Iconized()
        pyshell=self.model.winctrl.GetWin('Open PyShell')
        if iconized: self.Iconize(True)
        else: 
            self.Raise()
            pyshell.SetRect(self.model.pyshellrect) 
            
    def OnThreadJobEnded(self,event):
        # EVT handler to recieve thread job end
        jobnam=event.message
        #self.fuprog.ThreadJobEnded(jobnam)
        self.model.ThreadJobEnded(jobnam)
    
    def SetRemarkPanelSize(self,pansize):
        self.wremarkpan=pansize[0]
        self.hremarkpan=pansize[1]

    def OpenRemarkPanel(self):
        # this panel is created on main window in FMOPlot_Frm
        size=self.GetClientSize()
        w=size.width; h=size.height
        xpos=w-82; ypos=40
        self.remarkpanel=wx.Panel(self.canvas,-1,pos=(xpos,ypos),size=(self.wremarkpan,self.hremarkpan))
        self.remarkpanel.SetBackgroundColour(self.bgcolor)
        self.openremwin=True
        #self.remarkpanel=remarkpanel

    def OpenMouseModeWin(self):
        
        self.mousemode.ChangeShape(self.muswinshape) # has problem
        self.mousemode.CreateWin()
        self.mousemode.SetOpen(True)
        self.openmuswin=True #self.mousemode.IsOpen()
        
    def CloseMouseModeWin(self):
        self.mousemode.DestroyWin()
        self.mousemode.SetOpen(False)
        self.openmuswin=False
        
    def OpenMolChoiceWin(self):
        self.molchoice.ChangeShape(self.molwinshape) # has problem
        self.molchoice.CreateWin()
        self.molchoice.SetOpen(True)
        self.openmolwin=self.molchoice.IsOpen()
        
    def CloseMolChoiceWin(self):
        self.molchoice.DestroyWin()
        self.openmolwin=False
        self.molchoice.SetOpen(False)
        
    def OpenRemarkWin(self):
        # this panel is created on main window in FMOPlot_Frm
        [w,h]=self.GetClientSize()
        [x,y]=self.GetScreenPosition()
        #[x,y]=self.GetPosition()
        x=x+w-80; y=y+100
        #xpos=w-82; ypos=40
        bgcolor=self.model.setctrl.GetParam('win-color')
        bgcolor=[255*bgcolor[0],255*bgcolor[1],255*bgcolor[2],1.0]
        self.remarkwin=Remark_Frm(self,-1,[x,y],(self.wremarkpan,self.hremarkpan),bgcolor)
        #self.remarkwin.SetBackgroundColour(bgcolor) #self.draw.bgcolor)
        #self.remarkpanel=remarkpanel
        ###self.remarkpanel=wx.Panel(self.remarkwin,-1,pos=(-1,-1),size=(self.wremarkpan,self.hremarkpan))
        ###self.remarkpanel.SetBackgroundColour(self.bgcolor)
        self.remarkwin.Show()
        ###self.ctrlflag.Set('*RemarkWin',True)
        self.openremwin=True

    def CloseRemarkWin(self):
        self.remarkwin.Destroy()
        self.openremwin=False
        self.model.SetSelectAll(False)
        self.model.SaveAtomColor(False)
        self.model.Message('',0,'')
        self.model.DrawMol(True)
            
    def OnMenu(self,event):
        # menu event handler
        self.menuctrl.OnMenu(event)

    def ChoiceMusMod(self,event):
        #<2013.2 KK>
        item=self.cboxmus.GetStringSelection()
        self.ctrl.input.CBChoice(item)
        self.cboxmus.SetStringSelection(item)
        self.canvas.SetFocus()
    
    def ChoiceSelMod(self,event):
        #<2013.2 KK>
        item=self.cboxselmod.GetStringSelection()
        self.ctrl.input.CBChoice(item)
        self.cboxselmod.SetStringSelection(item)
        self.canvas.SetFocus()
    
    def ChoiceSelObj(self,event):
        #<2013.2 KK>
        item=self.cboxselobj.GetStringSelection()
        self.ctrl.input.CBChoice(item)
        self.cboxselobj.SetStringSelection(item)
        self.canvas.SetFocus()
    
    def Message(self,message,loc,color):
        # message(str): text
        # loc(int): 0:1st, 1:2nd field in statusbar
        # color(wx.COLOUR): not used
        self.SetStatusText(message,loc)

    def SetProjectNameOnTitle(self,curprj):
        title=self.setctrl.title+'  [ Current Project: '+curprj+' ]'
        self.SetTitle(title)
        
    def ModeMessage(self,mess):
        #(x,y)=self.GetPosition()
        #print 'x,y',x,y
        #(w,h)=self.GetClientSize()
        #print 'w,h',w,h
        #pos=(x+w-50,y+h+10)
        #print 'pos',pos
        #text=wx.StaticText(self.canvas,-1,mess,pos=pos)
        #text.Show()
        self.SetStatusText(mess,1)
 
    def XXBusyIndicator(self,cmd,mess=''):
        """ Busy indicator on StatusBar(Gauge version)
            does not work as expected. 20Feb2016
        :param str cmd: 'Open','Close','On' or 'Off'
        """
        if cmd != 'Open' and self.busyindicator is None: return
        #
        if cmd == 'On':
            self.busyind += 1
            const.CONSOLEMESSAGE('Busy is called. cmd='+cmd+', busyind='+str(self.busyind))
            if self.busyind == 1: 
                self.busytimer.Start(20)            
                self.busyindicator.SetValue(self.busycount)
                self.busyindicator.Refresh()
            if len(mess) > 0: self.Message(mess,1,'')
        elif cmd == "Off":
            self.busyind -= 1
            const.CONSOLEMESSAGE('Busy is called. cmd='+cmd+', busyind='+str(self.busyind))
            if self.busyind <= 0:
                try: self.busytimer.Stop()
                except: pass
                try: 
                    self.busyindicator.SetValue(0)
                    self.busyindicator.Refresh()
                except: pass
                #self.busyind=0
                self.Message('',1,'')
        elif cmd == 'Open':
            if self.busyindicator is None: 
                rect=self.statusbar.GetFieldRect(2)
                pos=rect.GetPosition()
                posx=pos[0]+15; posy=pos[1]+5
                pansize=[30,10]; panpos=(posx,posy) #(pos[0]+15,pos[1]+5)
                self.busytimer=wx.Timer(self)
                self.Bind(wx.EVT_TIMER,self.OnBusyTimer,self.busytimer)
                self.busycount=0
                self.busyindicator=wx.Gauge(self.statusbar,-1,50,pos=panpos,
                            size=pansize,style=wx.GA_HORIZONTAL) #|wx.GA_SMOOTH)     
                self.busyindicator.SetBackgroundColour('white')
                self.busyindicator.Show()
                self.busyind=0
                self.Message('',1,'')
        elif cmd == 'Close':
            self.Message('',1,'')
            try: 
                self.busytimer.Stop()
                self.busytimer.Destroy()
            except: pass
            try: self.busyindicator.Destroy()
            except: pass

    def OnBusyTimer(self,event):
        if self.busytimer is None: return
        self.busycount += 1
        if self.busycount >= 80 : self.busycount=0 # 120
        self.busyindicator.SetValue(self.busycount)
        self.busyindicator.Refresh()
        
    def BusyIndicator(self,cmd,mess=''):
        """ Busy indicator on StatusBar (panel version)
        
        :param str cmd: 'Open','Close','On' or 'Off'
        :param str mess: message in the second field of status bar
        """
        if cmd == "On":
            self.busyind += 1
            self.busyindicator.SetBackgroundColour('green')
            self.busyindicator.Refresh()
            self.Message(mess,1,'')
        elif cmd == "Off":
            self.busyind -= 1
            if self.busyind <= 0:
                self.busyindicator.SetBackgroundColour('white')
                self.busyindicator.Refresh()
                self.busyind=0
                self.Message('',1,'')
                #self.busyindicator.Destroy()
        elif cmd == 'Open':
            if self.busyindicator is None:
                rect=self.statusbar.GetFieldRect(2)
                pos=rect.GetPosition()
                posx=pos[0]+15; posy=pos[1]+5
                pansize=[30,10]; panpos=(posx,posy) #(pos[0]+15,pos[1]+5)
                self.busyindicator=wx.Panel(self.statusbar,-1,pos=panpos,
                                            size=pansize,style=wx.BORDER)
                self.busyindicator.SetBackgroundColour('white')
                self.busyindicator.SetToolTipString('Left click to reset')
                self.busyindicator.Show()
                self.busyind=0
        elif cmd == "Close": 
            self.busyindicator.Destroy()
            self.busyind=0
    
    def ResetBusyIndicator(self,event):
        """ Reset busy indicator """
        self.busyind=1
        self.BusyIndicator('Off')
        event.Skip()
    
    def OnMove(self,event): 
        [x,y]=self.GetPosition()
        [w,h]=self.GetSize()
        dx=x-self.windowposition[0]; dy=y-self.windowposition[1]
        dw=w-self.windowsize[0]; dh=h-self.windowsize[1]
        if dx == 0 and dy == 0 and dw == 0 and dh == 0: return
        #
        if not self.model.setctrl.GetParam('pyshellwin-move-free'):
            try:
                winlabel='Open PyShell'
                if self.winctrl.IsOpened(winlabel) and not self.hideshlwin: 
                    self.winctrl.Resize(winlabel)
            except: pass
        #
        try:
            if self.mousemode.IsOpen(): self.mousemode.Resize(dx,dy)
                #self.mousemode.SetOpen(True)
        except: pass
        # molchoicewin
        try:
        #if test:
            #print 'molchoicewin isopen',self.molchoice.IsOpen()
            if self.molchoice.IsOpen(): self.molchoice.Resize(dx,dy)
                #self.molchoice.SetOpen(True)
        except: pass
        # for FMOViewer
        """
        if self.model.fumode == 1: # viewer mode
            self.parent.SaveCubeParams()
            try:
                pos=self.parent.cubewin.GetPosition()
                pos[0] += dx; pos[1] += dy
                self.parent.cubewin.Destroy()
                self.parent.OpenDrawCubeWin()
                self.parent.cubewin.SetPosition(pos)
                self.parent.ResetCubeParams()
            except: pass       
        """
        # textmessage win
        try: self.textmess.RecoverText()
        except: pass
        # for fuplot
        #try:
        if self.openremwin:
            try:
                remarkdata=self.remarkwin.GetRemarkData()
                self.CloseRemarkWin() #remarkwin.Destroy()
                self.OpenRemarkWin()
                #bgcolor=self.model.Getctrl.GetParam('win-color')
                #self.remarkwin.ChangeBackgroundColor(bgcolor)
                self.remarkwin.SetRemarkData(remarkdata)
                self.remarkwin.DrawColorRemark()
            except: pass

        self.windowposition=[x,y]
        self.windowsize=[w,h]
        
    def OnResize(self,event):
        self.OnMove(1)
        event.Skip()
        
    def OnPaint(self, event):
        if self.model.Ready(): return
        self.draw.Paint()
        
    def OnEraseBG(self, event):
        #<2013.2 KK>
        self.draw.EraseBG()

    # Keyboard event handler
    def OnKeyDown(self,event):
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        ###self.timer.Stop()
        keycode=event.GetKeyCode()
        self.mousectrl.KeyDown(keycode)
        
        event.Skip()
    # keyboard commands.
    def OnKeyUp(self,event):
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        keycode=event.GetKeyCode()
        self.mousectrl.KeyUp(keycode)
        
        event.Skip()

    def OnMouseLeftDClick(self,event):
        ###self.timer.Stop()
        pos=event.GetPosition()
        self.mousectrl.MouseLeftDClick(pos) #PopupMenu(pos)
        event.Skip()
        
    def OnMouseMove(self, event): 
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        #self.timer.Stop()
        pos=event.GetPosition()
        self.mousectrl.MouseMove(pos)
        event.Skip()
        
    def OnMouseLeftDown(self, event):                
        if self.model.mol is None: return
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        pos=event.GetPosition()
        self.mousectrl.MouseLeftDown(pos)
        #self.timer.Stop()
        event.Skip()

    def OnMouseLeftSClick(self, event):                
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        ###self.timer.Stop()
        #print 'single click'
        pos=self.ScreenToClient(wx.GetMousePosition())
        #pos=event.GetPosition()
        self.mousectrl.MouseLeftDown(pos)
        event.Skip()

    def OnMouseLeftUp(self,event): 
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        ###self.timer.Stop()
        self.mousectrl.MouseLeftUp()
        event.Skip()
    
    def OnMouseRightDown(self,event):
        if self.model.mol is None: return
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        #
        label='mdlpopupmenu'
        menulst,tiplst=self.menuctrl.PopupMenu()
        if len(menulst) <= 0: return
        retmethod=self.menuctrl.OnPopupMenu
        self.popupmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,menulst,tiplst)
        #                       #menulabel=label) #,winwidth=180) #,winwidth=200) 
        self.popupmenu.Show()
        self.popupmenu.SetFocus()
        """
        pos=self.GetPosition()
        winpos=[pos[0]+10,pos[1]+20]
        self.popup=subwin.PopupWindow_Frm(self,-1,self.model,winpos,'',menulst,tiplst)
        self.popup.Show()
        """
        ###14Jan### self.popupmenu.SetFocus()
        
        event.Skip()

    def OnMouseRightUp(self, event):
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        ###self.timer.Stop()
        pos=event.GetPosition()
        self.mousectrl.MouseRightUp(pos)

        event.Skip()

    def OnMouseWheel(self, event):
        if not self.model.Ready(): return
        if self.draw.Busy(): return
        ###self.timer.Stop()
        rot=event.GetWheelRotation()
        self.mousectrl.MouseWheel(rot)
        event.Skip()

    def OnEnterWindow(self,event):

        self.draw.canvas.SetFocus()

    def OnLeaveWindow(self,event):
        return
    
        self.ReleaseMouse()
        
    def OnFocus(self,event):
        #lib.ChangeCursor(self,0)
        event.Skip()

    def OnCloseFromFUTools(self):
         # close all subwindows    
        for w in wx.GetTopLevelWindows(): w.Close()
        self.model.ExitModel()  
        
    def OnClose(self,event):
        # close all subwindows and exit()  
        self.model.WriteIniFile()

        
        for w in wx.GetTopLevelWindows(): w.Close()
        self.model.ExitModel()  

        """
        if self.model.fumode != 3:
            # close all subwindows    
            for w in wx.GetTopLevelWindows(): w.Close()
            self.model.ExitModel()  
        elif self.model.fumode == 3: 
            for w in wx.GetTopLevelWindows(): 
                if w != self.winctrl.GetWin('Open PySHell'): w.Hide()
            self.Hide()
        else: 
            for w in wx.GetTopLevelWindows(): w.Close()            
            self.Destroy()
        """
        
class Remark_Frm(wx.Frame):
    def __init__(self,parent,id,winpos,winsize,bgcolor=[]):
        wx.Frame.__init__(self,parent,id,pos=winpos,size=winsize,
                          style=wx.FRAME_FLOAT_ON_PARENT) #|wx.NO_BORDER) #,
        #       style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)
        #size=self.GetClientSize()
        #self.canvas=parent.canvas
        ###self.remarkwin=parent.remarkwin
        self.mdlwin=parent
        
        self.bgcolor=bgcolor
        if len(bgcolor) <= 0:
            self.bgcolor=self.mdlwin.model.setctrl.GetParam('win-color')
        #self.bgcolor=parent.bgcolor
        self.SetBackgroundColour(self.bgcolor)
        #self.panel=wx.Panel(self,-1,pos=(0,0),size=winsize)
        #self.panel.SetBackgroundColour(self.bgcolor)
        
        self.wremarkpan=parent.wremarkpan
        self.hremarkpan=parent.hremarkpan
        #
        self.remarkwin=None
        self.remarkbuffer=None
        self.remarkpanel=None
        self.remarkdata=[]
        self.textfont=None
        self.textcol=[]
        self.rankposi=0
        self.ranknega=0
        self.yrange=0
        self.extposivalue=0
        self.extnegavalue=0
        self.xloc=0; self.yloc=0; self.rem=[]
        #self.wcolorbox=self.fuprog.wcolorbox; self.hcolorbox=self.fuprog.hcolorbox
        self.wcolorbox=0
        self.hcolorbox=0
        self.width=80; self.hight=200 # remark panel size
        self.wcolorbox=0; self.hcolorbox=0
    
    def SetRemarkData(self,remarkdata):
        # for fuplot remark panel
        self.rem=remarkdata[0]
        self.xloc=remarkdata[1]
        self.yloc=remarkdata[2]
        self.width=remarkdata[3]
        self.hight=remarkdata[4]
        self.textfont=remarkdata[5]
        self.textcol=remarkdata[6]
        #self.bgcolordummy=remarkdata[7]
        self.wcolorbox=remarkdata[8]
        self.hcolorbox=remarkdata[9]
        self.rankposi=remarkdata[10]
        self.ranknega=remarkdata[11]
        self.yrange=remarkdata[12]
        self.extposivalue=remarkdata[13]
        self.extnegavalue=remarkdata[14]
        self.rankcolorposi=remarkdata[15]
        self.rankcolornega=remarkdata[16]
        self.extcolorposi=remarkdata[17]
        self.extcolornega=remarkdata[18]        
        #
        self.remarkdata=remarkdata

    def GetRemarkData(self):
        return self.remarkdata

    def DrawColorRemark(self):
        # for fuplot
        #canvsize=self.mdlwin.canvas.GetSize()
        canvsize=self.mdlwin.GetSize()
        wpan=canvsize[0]; hpan=canvsize[1]
        #
        xpos=wpan-82; ypos=40
        #
        self.remarkbuffer=wx.EmptyBitmap(self.width,self.hight) #(wpan,hpan)
        #dc=wx.BufferedDC(wx.ClientDC(self.remarkpanel),self.remarkbuffer) #(self.remarkpanel,self.remarkbuffer)
        dc=wx.BufferedDC(wx.ClientDC(self),self.remarkbuffer) #(self.remarkpanel,self.remarkbuffer)
        dc.Clear()
        # plot: True: on FMO plot panel, False: on Main Window
        wbox=self.wcolorbox; hbox=self.hcolorbox
        dc.SetFont(self.textfont)
        dc.SetTextForeground(self.textcol)
        #
        rankposi=self.rankposi
        ranknega=self.ranknega
        maxrankval=self.yrange 
        minrankval=-self.yrange
        # scaled out negative and positive energy
        extposival=self.extposivalue
        extnegaval=self.extnegavalue
        # make white rectangle for color scale
        rgb=self.bgcolor
        #rgb=const.RGBColor['black']
        dc.SetPen(wx.Pen(rgb)) #"white"))
        dc.SetBrush(wx.Brush(rgb,wx.SOLID))
        #hplt=self.hplt-self.htitle
        x0=self.xloc; y0=self.yloc
        dc.DrawRectangle(x0,y0,self.width,self.hight)
        # draw remark
        if len(self.rem) > 0:
            dc.DrawText(self.rem,x0,y0)
            y0 += 20
        # positive value
        x=x0+5; y=y0
        if extposival > 0.00001:
            dc.SetPen(wx.Pen(self.extcolorposi))
            dc.SetBrush(wx.Brush(self.extcolorposi))
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y-6
            if self.yrange > 1.0:
                txt=extposival; txt='% 4.1f' % txt
            else:
                txt=extposival; txt='% 4.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,y-4)

        y=y+hbox+4            
        yy=y
        if maxrankval > 0.0:
            delposi=self.yrange/3.0
            yy=yy+hbox*(rankposi-1)
            for i in range(rankposi):
                col=self.rankcolorposi[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,yy,wbox,hbox)
                if i == 0 or i == 3 or i == 6 or i == rankposi-1:
                    xtxt=x+20; ytxt=yy-4
                    if i == 0: txt=0.0
                    else: txt=delposi*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='% 4.1f' % txt
                    else:
                        txt='% 4.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,yy-4)
                yy -= hbox
                y += hbox
        # negative value
        if minrankval < 0.0:
            delnega=-self.yrange/3.0
            for i in range(1,ranknega): # skip zero
                col=self.rankcolornega[i]
                dc.SetPen(wx.Pen(col))
                dc.SetBrush(wx.Brush(col))
                dc.DrawRectangle(x,y,wbox,hbox)
                if i == 3 or i == 6 or i == ranknega-1:
                    xtxt=x+20; ytxt=y+4
                    txt=delnega*(float(i)/3.0)
                    if self.yrange > 1.0:
                        txt='%5.1f' % txt
                    else:
                        txt='%5.2f' % txt
                    xtxt += (6-len(txt))*6
                    dc.DrawText(txt,xtxt,ytxt-4)
                y += hbox
        if extnegaval < -0.00001:
            dc.SetPen(wx.Pen(self.extcolornega))
            dc.SetBrush(wx.Brush(self.extcolornega))
            y += 4
            dc.DrawRectangle(x,y,wbox,hbox)
            xtxt=x+20; ytxt=y+4
            txt=extnegaval
            if self.yrange > 1.0:
                txt='% 5.1f' % txt
            else:
                txt='% 5.2f' % txt
            xtxt += (6-len(txt))*6
            dc.DrawText(txt,xtxt,ytxt-4)
 
        self.Refresh()
        self.Update()

    def ChangeBackgroundColor(self,rgba):
        rgb=rgba[:3]
        for i in range(len(rgb)): rgb[i] *= 255.0
        self.bgcolor=rgb
        self.SetBackgroundColour(rgb)
        self.Refresh()
        
# mol choice win manager
class MolChoice(object):
    def __init__(self,parent):
        self.mdlwin=parent
        self.model=parent.model
        self.molctrl=parent.model.molctrl
        #
        self.win=None
        self.open=False
        self.muspos=[0,0]
        self.position=[0,46] #40] #46]
        self.winpos=[0,0]
        #self.winsize=lib.WinSize([150,90]) #     [130,50]
        self.winsize0=lib.WinSize([150,90]) 
        self.winsize1=lib.WinSize([150,115])
        self.shape=0
        self.wbox=120
        self.molnamlst=[]
        self.selectmol=''

    def CreateWin(self):
        if self.open: 
            self.win.SetFocus()
            return
        else:
            winpos=[] #self.GetPosition()
            if self.shape == 0: winsize=self.winsize0
            elif self.shape == 1: winsize=self.winsize1
            self.win=MolChoice_Frm(self.mdlwin,-1,winpos,winsize,self,
                                   self.shape)
            self.win.Show()
            self.molnamlst=[]
            self.molnamlst=self.molctrl.GetMolNameList()
            if len(self.molnamlst) > 0:
                self.selectmol=self.molctrl.GetCurrentMolName()
                self.win.cboxmol.SetItems(self.molnamlst)
                self.win.cboxmol.SetStringSelection(self.selectmol)    
            self.open=True
            #xxself.model.menuctrl.Check('Open MolChoiceWin',True)
            self.model.menuctrl.CheckMenu('Open MolChoiceWin',True)
        #self.model.winctrl.SetOpened('Open MolChoiceWin',self.win)

    def DestroyWin(self):
        try: self.win.Destroy()
        except: pass
        self.open=False
        #xxself.model.menuctrl.Check('Open MolChoiceWin',False)
        self.model.menuctrl.CheckMenu('Open MolChoiceWin',False)
        #self.model.winctrl.CloseWin('Open MolChoiceWin')
        
    def GetPosition(self):
        [x,y]=self.mdlwin.GetScreenPosition()
        [w,h]=self.mdlwin.GetSize() #GetClientSize()
        xpos=w-237 #232
        if self.shape != 0: xpos=w-132
        winpos=[x+xpos+self.position[0],y+self.position[1]]
        #winpos=[x+xpos+self.position[0],y] # for put on window title
        return winpos

    def Resize(self,dx,dy):
        self.winsize=self.win.GetSize()
        pos=self.win.GetPosition()
        self.DestroyWin()
        self.CreateWin()
        if self.shape == 1:
            pos[0] += dx; pos[1] += dy
            self.win.SetPosition(pos)
                   
    def SetPosition(self,winpos):
        self.winpos=winpos
    
    def SetOpen(self,on):
        if on: self.open=True
        else: self.open=False
        
    def IsOpen(self):
        return self.open
    
    def GetShape(self):
        return self.shape
    
    def SetShape(self,shape):
        self.shape=shape
        
    def ChangeShape(self,shape):
        self.shape=shape
        self.winsize=lib.WinSize([150,90])  #[130,70]
        #if lib.GetPlatform() == 'WINDOWS': self.winsize=[150,90]
        winpos=self.GetPosition()
        self.ChangePosition(winpos)
        
    def ChangePosition(self,winpos):
        self.winpos=winpos
        self.DestroyWin()
        self.CreateWin()
        
    def SetWBox(self,wbox):
        self.wbox=wbox
        
    def GetWBox(self):
        return self.wbox
    
    def SetMolNameList(self,molnamlst):
        self.molnamlst=molnamlst
        try: self.win.cboxmol.SetItems(molnamlst)
        except: pass

    def GetMolNameList(self):
        #self.molnamlst=self.win.cboxmol.GetItems()
        return self.molnamlst

    def Rename(self,oldnam,newnam):
        try:
            self.molnamlst=self.molctrl.GetMolNameList()
            #idx=self.molnamlst.index(oldnam)
            #self.molnamlst[idx]=newnam
            self.win.cboxmol.SetItems(self.molnamlst)
            self.SetMolSelection(newnam)
        except: pass

    def SetMolSelection(self,name):
        try:
            self.win.cboxmol.SetStringSelection(name)
            self.selectmol=name
        except: pass
        
    def SetSelection(self,nmb):
        # nmb(int): index of self.molnamlst
        self.win.cboxmol.SetSelection(nmb)
        self.selectmol=self.molnamlst[nmb]
              
    def GetSelection(self):
        nmb==self.win.GetSelection()
        self.selectmol=self.molnamlst.index(nmb)
        return self.selectmol
 
    def GetMolSelection(self):
        try: self.selectmol=self.win.cboxmol.GetStringSelection()
        except:
            if len(self.molnamlst) > 0: self.selectmol=self.molnamlst[0]
            else: self.selectmol=''
        return self.selectmol
    
    def ChoiceMol(self,name,fit,drw):
        if name == '': curmol=-1
        else: curmol=self.molnamlst.index(name)
        self.molctrl.SwitchCurMol(curmol,fit,drw)

    def ChoiceNextMol(self,name,fit,drw):
        if name == '': curmol=-1
        else:
            idx=self.molnamlst.index(name)
            curmol=idx+1
            if curmol >= len(self.molnamlst): curmol=0
            self.SetSelection(curmol)
            
        self.molctrl.SwitchCurMol(curmol,fit,drw)   

    def ChoicePrevMol(self,name,fit,drw):
        if name == '': curmol=-1
        else:
            idx=self.molnamlst.index(name)
            curmol=idx-1
            if curmol < 0: curmol=len(self.molnamlst)-1
            self.SetSelection(curmol)     
        self.molctrl.SwitchCurMol(curmol,fit,drw)

    def Add(self,molnam):
        try: self.win.cboxmol.Append(molnam)
        except: pass
        self.molnamlst=self.molctrl.GetMolNameList()
        #self.molnamlst=self.GetMolNameList()
        self.selectmol=self.GetMolSelection()
            
    def DelByName(self,molnam):
        try:
            i=self.molnamlst.index(molnam)
            self.Del(i)
        except: pass
 
    def Del(self,nmb):
        if nmb < 0 or nmb > len(self.molnamlst)-1: return
        try: self.win.cboxmol.Delete(nmb)
        except: pass
        self.molnamlst=self.molctrl.GetMolNameList()
        if len(self.molnamlst) <= 0: self.Clear()

    def Clear(self):
        self.molnamlst=[]
        self.selectmol=''
        if self.open:
            self.DestroyWin()
            self.CreateWin()
        
class MolChoice_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos,winsize,mymgr,shape):
        # window position
        if len(winpos) <= 0:
            winpos=parent.canvas.GetScreenPosition()
            parwinsize=parent.GetClientSize()
        if shape == 0:
            wbox=mymgr.GetWBox()  
            wwin=wbox+115; winsize=(wwin,28) #; winpos[0] -= (wbox-120) # default wwin=230
            winpos[0] += (parwinsize[0]-wwin) #winsize[0]
            wx.MiniFrame.__init__(self,parent,id,pos=winpos,size=winsize,
                                  style=wx.FRAME_FLOAT_ON_PARENT)
        else:
            winpos[0] += parwinsize[0]
            wx.MiniFrame.__init__(self,parent,id,pos=winpos,size=winsize,
                  style=wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)
            self.SetTitle('MolChoice')
        self.mdlwin=parent
        self.mymgr=mymgr  # MolChoice
        self.cboxmol=None
        # initialize variables
        self.panelpos=(2,2)
        self.winsize=winsize
        self.shape=shape
        self.panel=None
        self.helpname='MolCoice'
        # set font
        self.font=self.GetFont()
        self.font.SetPointSize(8)
        self.SetFont(self.font)
        # set color
        self.fgcolor='black'
        self.bgcolor='light gray' #'gray'
        self.SetBackgroundColour(self.bgcolor)
        
        #self.shwhideh=False
        #self.shwbda=False
        #self.shwballstic=False
        #self.shhbond=False
        self.shwitemdic={"BDA points":False,"Hide hydrogen":False,
                         "Hydrogen Bonds":False}
        # create panel
        self.CreatePanel()
        self.Show()
        # event handlers
        #??self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnterWindow)
        #??self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeaveWindow)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
    def CreatePanel(self):
        if self.shape == 0: self.CreatePanel0()
        elif self.shape == 1: self.CreatePanel1()        
        self.cboxmol.SetItems(self.mymgr.molnamlst)
        self.cboxmol.SetStringSelection(self.mymgr.selectmol)

    def CreatePanel0(self):
        # pulldown mol choice
        htext=20; hbox=const.HCBOX #18
        btnsize=[8,8]
        if lib.GetPlatform() == 'WINDOWS': btnsize=[10,10]
        xloc=self.panelpos[0]; yloc=self.panelpos[1]
        clsbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc),size=btnsize)
        clsbtn.SetBackgroundColour('red')
        clsbtn.Bind(wx.EVT_BUTTON,self.OnClose)
        clsbtn.SetToolTipString('Close')
        shpbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc+10),size=btnsize)
        shpbtn.SetBackgroundColour('white')
        shpbtn.Bind(wx.EVT_BUTTON,self.OnShape)
        shpbtn.SetToolTipString('Change style')
        xloc += 14
        st0=wx.StaticText(self,wx.ID_ANY,'Molecule:',pos=(xloc,yloc+2),size=(55,htext))
        st0.SetFont(self.font)
        st0.SetForegroundColour(self.fgcolor)
        st0.Bind(wx.EVT_LEFT_DOWN,self.OnLeftDown)
        st0.Bind(wx.EVT_RIGHT_DOWN,self.OnRightDown)
        wbox=self.mymgr.GetWBox()
        self.cboxmol=wx.ComboBox(self,-1,'',
                           pos=(xloc+56,yloc),size=(wbox,hbox),style=wx.CB_READONLY|wx.WANTS_CHARS)
        self.cboxmol.Bind(wx.EVT_COMBOBOX,self.OnChoiceMol)
        #self.cboxmol.Bind(wx.EVT_COMBOBOX_DROPDOWN,self.OnDropDown)
        #self.cboxmol.Bind(wx.EVT_RIGHT_DOWN,self.RightDown)
        
        self.cboxsqbt1=wx.Button(self,wx.ID_ANY,"<",pos=(xloc+wbox+60,yloc+2),size=(15,15))
        self.cboxsqbt1.Bind(wx.EVT_BUTTON,self.OnChoicePrevMol)        
        self.cboxsqbt2=wx.Button(self,wx.ID_ANY,">",pos=(xloc+wbox+78,yloc+2),size=(15,15))
        self.cboxsqbt2.Bind(wx.EVT_BUTTON,self.OnChoiceNextMol)        
    
    def RightDown(self,event):
        print 'right is down'
      
    def OnDropDown(self,event):
        print 'DropDown'    
        
    def CreatePanel1(self):
        # menubar
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)

        [w,h]=self.GetClientSize()
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(w,h))
        htext=20; hbox=const.HCBOX 
        btnsize=[8,8]
        if lib.GetPlatform() == 'WINDOWS': btnsize=[10,10]
        #??xloc=self.panelpos[0]; yloc=self.panelpos[1]
        xloc=5; yloc=5
        clsbtn=wx.Button(self.panel,wx.ID_ANY,"",pos=(xloc,yloc),size=btnsize)
        clsbtn.SetBackgroundColour('red')
        clsbtn.Bind(wx.EVT_BUTTON,self.OnClose)
        clsbtn.SetToolTipString('Close')
        shpbtn=wx.Button(self.panel,wx.ID_ANY,"",pos=(xloc,yloc+10),size=btnsize)
        shpbtn.SetBackgroundColour('white')
        shpbtn.Bind(wx.EVT_BUTTON,self.OnShape)
        shpbtn.SetToolTipString('Change style')
        xloc += 14
        st0=wx.StaticText(self.panel,wx.ID_ANY,'Molecule:',pos=(xloc,yloc+2),size=(55,htext))
        st0.SetFont(self.font)
        st0.SetForegroundColour(self.fgcolor)
        self.cboxsqbt1=wx.Button(self.panel,wx.ID_ANY,"<",pos=(xloc+65,yloc),size=(15,htext))
        self.cboxsqbt1.Bind(wx.EVT_BUTTON,self.OnChoicePrevMol)        
        self.cboxsqbt2=wx.Button(self.panel,wx.ID_ANY,">",pos=(xloc+90,yloc),size=(15,htext))
        self.cboxsqbt2.Bind(wx.EVT_BUTTON,self.OnChoiceNextMol)        
        xloc=5; yloc += 22; wbox=w-10
        self.mymgr.SetWBox(wbox)
        self.cboxmol=wx.ComboBox(self.panel,-1,'',
                           pos=(xloc,yloc),size=(wbox,hbox),style=wx.CB_READONLY|wx.WANTS_CHARS)
        self.cboxmol.Bind(wx.EVT_COMBOBOX,self.OnChoiceMol)

    def OnLeftDown(self,event):
        wbox=self.mymgr.GetWBox()
        wbox += 10
        self.mymgr.SetWBox(wbox)
        self.mymgr.DestroyWin()
        self.mymgr.CreateWin()
        
    def OnRightDown(self,event):
        wbox=self.mymgr.GetWBox()
        wbox -= 10
        self.mymgr.SetWBox(wbox)
        self.mymgr.DestroyWin()
        self.mymgr.CreateWin()

    def OnResize(self,event):
        if self.shape == 1:
            try:
                self.panel.Destroy()
                self.CreatePanel1() 
                self.SetMinSize([50,self.mymgr.winsize1[1]])
                self.SetMaxSize([2000,self.mymgr.winsize1[1]])
                self.cboxmol.SetItems(self.mymgr.molnamlst)
                self.cboxmol.SetStringSelection(self.mymgr.selectmol)
            except: pass
    def OnClose(self,event):
        self.mymgr.DestroyWin()
        self.mymgr.SetOpen(False)
  
    def OnShape(self,event):
        shape=self.mymgr.GetShape()
        if shape == 0: shape=1
        elif shape == 1: shape=0
        self.mymgr.ChangeShape(shape)

    def OnEnterWindow(self,event):
        #self.CaptureMouse()
        #self.SetFocus()
        return
        #self.SetFocus()
        self.CaptureMouse()
        #self.SetFocus()
        
    def OnLeaveWindow(self,event):
        #self.ReleaseMouse()
        #self.mdlwin.SetFocus()
        return
    
        self.ReleaseMouse()
        self.mdlwin.SetFocus()
        
    def OnChoiceMol(self,event):
        try: name=self.cboxmol.GetStringSelection()
        except: name=''
        self.mymgr.ChoiceMol(name,False,False) #True) #True)

        self.DrawShowItems()
        event.Skip()
        
    def OnChoiceNextMol(self,event):
        if len(self.cboxmol.GetItems()) <= 0: name=''
        else: name=self.cboxmol.GetStringSelection()
        self.mymgr.ChoiceNextMol(name,False,False) #True) #True)
        
        self.DrawShowItems()
        
    def OnChoicePrevMol(self,event):
        if len(self.cboxmol.GetItems()) <= 0: name=''
        else: name=self.cboxmol.GetStringSelection()
        self.mymgr.ChoicePrevMol(name,False,False) #True) #True)

        self.DrawShowItems()
        
    def DrawShowItems(self):
        for item,value in self.shwitemdic.iteritems():
            meth=self.mdlwin.model.menuctrl.OnShow
            if item == "BDA points": meth=self.mdlwin.model.menuctrl.OnFMO
            #if item == "Ball and stick" and not value: 
            #    item="Line"; value=True
            meth(item,value)
    
    def SetAllShowItems(self,on):
        for item,value in self.shwitemdic.iteritems():
            self.shwitemdic[item]=on
            # check menu items
            menu=self.menubar.GetMenu(0)
            menuid=menu.FindItem(item)
            for id in range(1,5): menu.Check(id,on)
    
    def HelpDocument(self):
        self.mdlwin.model.helpctrl.Help(self.helpname)
    
    def Tutorial(self):
        self.mdlwin.model.helpctrl.Tutorial(self.helpname)
        
    def MenuItems(self):
        """ Menu and menuBar data """
        # Menu items
        menubar=wx.MenuBar()
        # File
        submenu=wx.Menu()
        submenu.Append(1,"Show BDA points",kind=wx.ITEM_CHECK)
        submenu.Append(2,"Hide hydrogens",kind=wx.ITEM_CHECK)
        ###submenu.Append(3,"Ball and stick",kind=wx.ITEM_CHECK)
        submenu.Append(4,"Hydrogen Bonds",kind=wx.ITEM_CHECK)
        submenu.AppendSeparator()
        submenu.Append(-1,"Set all","Set on all items")
        submenu.Append(-1,"Reset","Set off all items")
        #submenu.Append(-1,'Close selected','Close selected molecules')     
        menubar.Append(submenu,'Show')
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.Append(-1,'Tutorial','Tutorial')
        menubar.Append(submenu,'Help')
        #
        return menubar

    def BallAndStick(self,on):
        if on: model=2
        else: model=0
        for atom in self.model.mol.atm: atom.model=model
        
    def OnMenu(self,event):
        """ Menu event handler """
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        bChecked=self.menubar.IsChecked(menuid)

        # File menu items
        if item == "Show BDA points": 
            #self.shwitemdic["BDA points"]=bChecked
            self.BallAndStck(bChecked)
            #self.DrawShowItems()
        elif item == "Hide hydrogens": 
            self.shwitemdic["Hide hydrogen"]=bChecked
            self.DrawShowItems()
        elif item == "Ball and stick": 
            self.shwitemdic["Ball and stick"]=bChecked
            self.DrawShowItems()
        elif item == "Hydrogen Bonds":
            self.shwitemdic["Hydrogen Bonds"]=bChecked
            self.DrawShowItems()
        #
        elif item == "Set all": 
            self.SetAllShowItems(True)
            self.DrawShowItems()
        elif item == "Reset": 
            self.SetAllShowItems(False)
            self.DrawShowItems()
        elif item == 'Close selected': pass
        # Help
        elif item == "Document": self.HelpDocument()
        elif item == "Tutorial": self.Tutorial()


# mouse mode panel manager
class MouseMode(object):
    def __init__(self,parent):
        self.mdlwin=parent
        self.model=parent.model
        #     
        self.win=None
        self.open=False
        self.muspos=[0,0]
        self.position=[0,46]
        self.winpos=[0,0]
        self.winsize=[]
        #self.shape=0 # 0:horizontal,  1:vertical and movable
        self.shape=self.model.setctrl.GetParam('mousemode-win-shape')
        self.musmod=0 # 0:rotation,1:translatiton, 2:zoom, 3:rotation around Z
        # the following data are local. See mousectrl class
        self.selmod=0 # 0:1-object, 1:2-objects,2:3-objects,3:4-objects, 4:unlimited
        self.selobj=0 # 0:atom, 1:residue, 2:chain, 3:group, 4:fragment(FMO)
        self.secmod=0 # 0:False, 1:True
        self.bdamod=0 # 0:False, 1:True

    def CreateWin(self):
        if self.open: 
            self.win.SetFocus()
            return
        else:
            #winpos=self.mdlwin.canvas.GetScreenPosition()
            winpos=[]
            self.win=MouseMode_Frm(self.mdlwin,-1,winpos,self,self.shape)
            self.win.Show()
            self.open=True
            #xxself.model.menuctrl.Check('Open MouseModeWin',True)
            self.model.menuctrl.CheckMenu('Open MouseModeWin',True)
            #self.model.winctrl.SetOpened('Open MouseModeWin',self.win)
            if self.model.mousectrl.mdlmod == 5: 
                 color=self.model.mousectrl.winbgcolor[1]
                 self.win.SetBackgroundColour(color)      

    def SetOpen(self,on):
        if on: self.open=True
        else: self.open=False
        
    def DestroyWin(self):
        try: self.win.Destroy()
        except: pass
        self.open=False
        #xxself.model.menuctrl.Check('Open MouseModeWin',False)
        self.model.menuctrl.CheckMenu('Open MouseModeWin',False)
        #self.model.winctrl.CloseWin('Open MouseModeWin')
        
    def GetPosition(self):
        [x,y]=self.mdlwin.GetScreenPosition()
        winpos=[x+self.position[0],y+self.position[1]]        
        return winpos
    
    def SetPosition(self,winpos):
        self.winpos=winpos

    def Resize(self,dx,dy):
        pos=self.win.GetPosition()
        self.DestroyWin()
        self.CreateWin()
        if self.shape == 1:
            pos[0] += dx; pos[1] += dy
            self.win.SetPosition(pos)
        mdlmod=self.model.mousectrl.mdlmod
        if self.model.mousectrl.mdlmod == 5: 
             color=self.model.mousectrl.winbgcolor[1]
             self.win.SetBackgroundColour(color) 
             self.win.Refresh()     
    
    def SetMousePos(self,pos):
        self.muspos=pos
        
    def GetMousePos(self):
        return self.muspos
    
    def IsOpen(self):
        return self.open
    
    def GetShape(self):
        return self.shape
    
    def SetShape(self,shape):
        self.shape=shape
        
    def ChangeShape(self,shape):
        self.shape=shape
        winpos=self.GetPosition()
        self.ChangePosition(winpos)
    
    def ChangeBGColor(self,color=''):
        if len(color) == 0: color='light gray'
        self.win.bgcolor=color
        self.win.SetBackgroundColour(color)
        self.win.Refresh()
        
    def ChangePosition(self,winpos):
        self.winpos=winpos
        self.DestroyWin()
        self.CreateWin()
        
    def GetMouseModeItems(self):
        return self.musmoditems
    
    def GetSelModeItems(self):
        return self.selmoditems
    
    def GetSelObjectItems(self):
        return self.selobjitems

    def GetSelObject(self):
        return self.selobj

    def GetSelMode(self):
        return self.selmod
    
    def SetSelObject(self,value):
        self.selobj=value # need for Resize
        self.model.mousectrl.SetSelObj(value) # can not get mousectrl directly
 
    def SetSelObjSelection(self,value):
        #self.win.cboxselobj.SetSelection(value)
        self.win.SetSelObjSelection(value)

    def SetSelMode(self,value):
        self.selmod=value # need for Resize
        self.model.mousectrl.SetSelMode(value)
        
    def SetSelModeSelection(self,value):
        #self.win.cboxselmod.SetSelection(value)
        self.win.SetSelModeSelection(value)
                    
    def SetMouseMode(self,value):
        self.musmod=value # need for Resize
        self.model.mousectrl.SetMouseMode(value)

    def SetMouseModeSelection(self,value):
        #self.win.cboxmusmod.SetSelection(value)
        self.win.SetMouseModeSelection(value)
               
    def GetMuseMode(self):
        return self.musmod
    
    def GetSectionMode(self):
        return self.secmod
    
    def SetSectionMode(self,value):
        self.secmod=value
        self.model.mousectrl.SetSectionMode(value)
        
    def GetBDAMode(self):
        return self.bdamod
    
    def SetBDAMode(self,value):
        self.bdamod=value
        self.model.mousectrl.SetBDAMode(value)
 
class MouseMode_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos,mymgr,shape):
        if shape == 0:
            winsize=(275,28) #(405,28)
            if len(winpos) <= 0: 
                if lib.GetPlatform() == 'WINDOWS':
                    winpos=parent.canvas.GetScreenPosition()
                else: 
                    winpos=parent.GetPosition()
                    winpos=[winpos[0],winpos[1]+45]
            #
            wx.MiniFrame.__init__(self,parent,id,pos=winpos,size=winsize,
                                  style=wx.FRAME_FLOAT_ON_PARENT) #|wx.CLOSE_BOX)
        else:
            #winsize=[85,160]
            #if lib.GetPlatform() == 'WINDOWS': winsize=[75,150]
            winsize=[75,150]
            if len(winpos) <= 0:
                winpos=parent.canvas.GetScreenPosition()
                winpos[1] += 5
            wx.MiniFrame.__init__(self,parent,id,pos=winpos,size=winsize,
                              style=wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT) #wx.FRAME_TOOL_WINDOW|
            self.SetTitle('Modes')
        #
        self.mdlwin=parent
        self.model=parent.model
        self.mymgr=mymgr  # MouseMode
        self.shape=mymgr.shape
        # initialize
        self.panelpos=(2,2)
        self.muspos=[0,0]; self.leftdown=False
        self.cboxmol=None
        self.musmod=0; self.selmod=0; self.selobj=0
        # set font
        self.font=self.GetFont()
        self.font.SetPointSize(8)
        self.SetFont(self.font)
        # set color
        self.fgcolor='black'
        self.bgcolor='light gray' #'gray'
        #self.bgcolor='pale green'
        self.SetBackgroundColour(self.bgcolor)
        # items for combobox defined in MouseCtrl class
        self.musmoditems=self.model.mousectrl.GetMouseModeItems()
        self.selmoditems=self.model.mousectrl.GetSelModeItems()
        self.selobjitems=self.model.mousectrl.GetSelObjItems()
        #self.musmoddic=self.MakeItemDic(self.musmoditems)
        #self.selmoddic=self.MakeItemDic(self.selmoditems)
        #self.selobjdic=self.MakeItemDic(self.selobjitems)
        self.mdlmod=self.model.mousectrl.mdlmod
        self.musmod=self.model.mousectrl.musmod
        self.selmod=self.model.mousectrl.selmod
        self.selobj=self.model.mousectrl.selobj
        # icons for bitmap button
        self.resetbmp=self.model.setctrl.GetIconBmp('reset')
        self.modebmp=self.model.setctrl.GetIconBmp('mode-view') # View/Build mode
        self.movebmp=self.model.setctrl.GetIconBmp('move') # MusMode
        self.selobjbmp=self.model.setctrl.GetIconBmp('selectobject') # SelObj
        self.selnmbbmp=self.model.setctrl.GetIconBmp('selectnumber') # SelMode
        self.bmpbtndic={}
        self.stbgcolor='White'
        # create panel
        self.CreatePanel()
        #xxx#self.SetComboBoxSelections()
        # event handlers
        #self.Bind(wx.EVT_SET_FOCUS,self.OnFocus)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        #??self.Bind(wx.EVT_ENTER_WINDOW,self.OnEnterWindow)
        #self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeaveWindow)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnLeftDown)
        self.Bind(wx.EVT_MOTION,self.OnMove)
        self.Bind(wx.EVT_SIZE,self.OnResize)
    
    def MakeItemDic(self,itemlst):
        itemdic={}; idx=-1
        for item in itemlst:
            idx += 1; itemdic[item]=idx
        return itemdic
    
    def SetComboBoxSelections(self):
        self.musmod=self.model.mousectrl.GetMouseMode()
        self.selmod=self.model.mousectrl.GetSelMode()
        self.selobj=self.model.mousectrl.GetSelObj()
        
        self.SetMouseModeSelection(self.musmod)
        self.SetSelModeSelection(self.selmod)
        self.SetSelObjSelection(self.selobj)
             
    def CreatePanel(self):
        if self.shape == 0: self.CreatePanel0()
        elif self.shape == 1: self.CreatePanel1()        
        
    def CreatePanel0(self):
        # pulldown mol choice
        htext=20; hbox=const.HCBOX # 18
        btnsize=[8,8]; hbmpbtn=25; wbmpbtn=40
        if lib.GetPlatform() == 'WINDOWS': btnsize=[10,10]
        # mouse move choice
        xloc=self.panelpos[0]; yloc=self.panelpos[1]
        # position and shape of panel
        clsbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc),size=btnsize)
        clsbtn.SetBackgroundColour(wx.RED) #'red')
        clsbtn.Bind(wx.EVT_BUTTON,self.OnClose)
        clsbtn.SetToolTipString('Close')
        shpbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc+10),size=btnsize)
        shpbtn.SetBackgroundColour(wx.WHITE) #'white')
        shpbtn.Bind(wx.EVT_BUTTON,self.OnShape)
        shpbtn.SetToolTipString('Change style')
        xloc += 14 #24 #xloc1=5
        self.btnmode=wx.BitmapButton(self,-1,bitmap=self.modebmp,pos=(xloc,yloc-2),size=(hbmpbtn,hbmpbtn))
        self.btnmode.Bind(wx.EVT_BUTTON,self.OnBuildMode) #ControlPanMdl)
        self.btnmode.SetToolTipString('Switch view(white) and build(green) mode')
        self.btnmode.SetLabel('BuildModeButton')
        #btnmode.Bind(wx.EVT_RIGHT_DOWN,self.OnTipString)
        wx.StaticLine(self,pos=(xloc+35,5),size=(2,18),style=wx.LI_VERTICAL)
        xloc += 40
        labellst=['MoveButton','SelObjButton','SelNmbButton']
        bmplst=[self.movebmp,self.selobjbmp,self.selnmbbmp]
        tiplst=['Switch mouse move functions, Rotate,Translate,..',
                 'Switch selection object, Atom, Residue,..',
                 'Switch number of object selection, 1,2,..']
        vallst=[self.musmoditems[self.musmod],self.selobjitems[self.selobj],self.selmoditems[self.selmod]]
        for i in range(len(labellst)):
            xloc += 10
            btn=wx.BitmapButton(self,-1,bitmap=bmplst[i],pos=(xloc,yloc-2),size=(wbmpbtn,hbmpbtn))
            btn.Bind(wx.EVT_BUTTON,self.OnBitmapButton) #ControlPanMdl)
            btn.SetLabel(labellst[i])
            btn.SetToolTipString(tiplst[i])
            val=' '+vallst[i][:1].upper()+vallst[i][1:2]
            btnst=wx.StaticText(self,-1,val,pos=(xloc+wbmpbtn-1,yloc),size=(20,22),
                                    style=wx.BORDER|wx.ST_NO_AUTORESIZE)
            btnst.SetBackgroundColour(self.stbgcolor)
            self.bmpbtndic[labellst[i]]=[btn,btnst]
            xloc += 60
        
    def OnBitmapButton(self,event):
        obj=event.GetEventObject()
        label=obj.GetLabel()
        if label == 'MoveButton':
            menulst=self.musmoditems; tiplst=[]
            retmethod=self.OnMusMode
        elif label == 'SelObjButton':
            menulst=self.selobjitems; tiplst=[]
            retmethod=self.OnSelObj
        elif label == 'SelNmbButton':
            #selmoditems:['1-object','2-objects','3-objects','4-objects','unlimited','bulk']
            menulst=self.selmoditems
            tiplst=['','','','','',
                    'Click one atom and drag for sphere selection. Click off-atom and drag for slab selection. Switch to the other mode to quit.']
            retmethod=self.OnSelMode
        
        self.lbmenu=subwin.ListBoxMenu_Frm(self,-1,[],[],retmethod,menulst,tiplst) #,winwidth=200)

    def ChangeModeButton(self,mdlmod):
        hbmpbtn=25
        pos=self.btnmode.GetPosition()
        self.btnmode.Destroy()
        if mdlmod == 0: bmp='mode-view'
        else: bmp='mode-build'
        modebmp=self.model.setctrl.GetIconBmp(bmp)
        self.btnmode=wx.BitmapButton(self,-1,bitmap=modebmp,pos=pos,size=(hbmpbtn,hbmpbtn))
        self.btnmode.Bind(wx.EVT_BUTTON,self.OnBuildMode) #ControlPanMdl)
        self.btnmode.SetToolTipString('Switch view(white) and build(green) mode')
        self.btnmode.SetLabel('BuildModeButton')
        self.btnmode.Refresh()
    
    def OnBuildMode(self,event):
        obj=event.GetEventObject()
        value=self.model.mousectrl.GetMdlMode()
        if value == 5: mdlmod=0
        elif value == 0: mdlmod=5
        self.model.mousectrl.SetMdlMode(mdlmod)
        #self.ChangeModeButton(obj,mdlmod)
        
    def CreatePanel1(self):
        htext=20; hbox=const.HCBOX # 18
        btnsize=[8,8]; hbmpbtn=25; wbmpbtn=40
        if lib.GetPlatform() == 'WINDOWS': btnsize=[10,10]
        # mouse move choice
        xloc=self.panelpos[0]; yloc=self.panelpos[1]
        xloc=5; yloc=5
        # position and shape of panel
        clsbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc),size=btnsize)
        clsbtn.SetBackgroundColour('red')
        clsbtn.Bind(wx.EVT_BUTTON,self.OnClose)
        clsbtn.SetToolTipString('Close')        
        shpbtn=wx.Button(self,wx.ID_ANY,"",pos=(xloc,yloc+10),size=btnsize)
        shpbtn.SetBackgroundColour('white')
        shpbtn.Bind(wx.EVT_BUTTON,self.OnShape)
        shpbtn.SetToolTipString('Change style')
        
        #st1=wx.StaticText(self,wx.ID_ANY,'MusMode:',pos=(xloc+14,yloc+4),size=(56,htext))    
        #st1.SetForegroundColour(self.fgcolor)
        xloc += 20
        self.btnmode=wx.BitmapButton(self,-1,bitmap=self.modebmp,pos=(xloc,yloc-2),size=(hbmpbtn,hbmpbtn))
        self.btnmode.Bind(wx.EVT_BUTTON,self.OnBuildMode) #ControlPanMdl)
        self.btnmode.SetToolTipString('Switch view and build mode')
        self.btnmode.SetLabel('BuildModeButton')

        yloc += 30
        labellst=['MoveButton','SelObjButton','SelNmbButton']
        bmplst=[self.movebmp,self.selobjbmp,self.selnmbbmp]
        tiplst=['Switch mouse drag functions, Rotate,Translate,..',
                 'Switch selection object, Atom, Residue,..',
                 'Switch number of object selection, 1,2,..']
        vallst=[self.musmoditems[self.musmod],self.selobjitems[self.selobj],self.selmoditems[self.selmod]]
        xloc=5
        for i in range(len(labellst)):
            #xloc += 10
            btn=wx.BitmapButton(self,-1,bitmap=bmplst[i],pos=(xloc,yloc-2),size=(wbmpbtn,hbmpbtn))
            btn.Bind(wx.EVT_BUTTON,self.OnBitmapButton) #ControlPanMdl)
            btn.SetLabel(labellst[i])
            btn.SetToolTipString(tiplst[i])
            val=' '+vallst[i][:1].upper()+vallst[i][1:2]
            btnst=wx.StaticText(self,-1,val,pos=(xloc+wbmpbtn-1,yloc),size=(20,22),
                                    style=wx.BORDER|wx.ST_NO_AUTORESIZE)
            btnst.SetBackgroundColour(self.stbgcolor)
            self.bmpbtndic[labellst[i]]=[btn,btnst]
            yloc += 30

    def OnMove(self,event):
        if not event.LeftIsDown(): return
        muspos=self.mymgr.GetMousePos()
        pos=event.GetPosition()
        mov=[(pos[0]-muspos[0]),(pos[1]-muspos[1])]
        self.mymgr.SetMousePos(pos)
        [x,y]=self.mdlwin.GetPosition()
        winpos=[x+mov[0],y+mov[1]]
        self.mymgr.ChangePosition(winpos)

    def OnResize(self,event):
        pass
    
    def OnLeftDown(self,event):
        self.leftdown=True
        self.muspos=event.GetPosition()
        self.mymgr.SetMousePos(self.muspos)

    def OnFocus(self,event):
        event.Skip()

    def OnEnterWindow(self,event):
        event.Skip()
        
    def OnLeaveWindow(self,event):
        event.Skip()
        
    def OnClose(self,event):
        self.mymgr.DestroyWin()
        self.mymgr.SetOpen(False)

    def OnShape(self,event):
        if self.shape == 0: self.shape=1
        elif self.shape == 1: self.shape=0
        self.mymgr.ChangeShape(self.shape)
    
    def SetButtonStatus(self,objst,item):
        val=' '+item[:1].upper()+item[1:2]
        objst.SetLabel(val)

    def OnMusMode(self,item,menulabel):
        if item == '---': return
        if item == 'axis-rot' and not self.model.mousectrl.IsRotAxisSet():
            mess='Rotation axis is not set. To set the axis, select two atoms and execute "set axis"'
            lib.MessageBoxOK(mess,'OnMusMode')
            return
        label='MoveButton'
        obj=self.bmpbtndic[label][0]
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)
        self.model.mousectrl.musmod=self.musmoditems.index(item) #self.musmoddic[item]
        if self.model.mousectrl.musmod == 8: # item == '--------':
            musmod=0 #self.musmod
            self.SetButtonStatus(objst,'rotate')
            self.SetMouseModeSelection(musmod)  
        self.mymgr.SetMouseMode(self.model.mousectrl.musmod)
           
    def OnSelMode(self,item,menulabel):
        if item == '---': return
        label='SelNmbButton'
        obj=self.bmpbtndic[label][0]
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)
        prvselmod=self.model.mousectrl.selmod
        newselmod=self.selmoditems.index(item)
        self.model.mousectrl.selmod=newselmod
        self.mymgr.SetSelMode(newselmod)
        # remove selection sphere if exist
        if newselmod == 5: self.model.SetSelectAll(False)
        if prvselmod == 5 and newselmod != 5: self.model.RemoveSelectSphere()
                
    def OnSelObj(self,item,menulabel):
        if item == '---': return
        label='SelObjButton'
        obj=self.bmpbtndic[label][0]
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)
        self.model.mousectrl.selobj=self.model.mousectrl.selobjitems.index(item) #self.selobjdic[item]
        self.mymgr.SetSelObject(self.model.mousectrl.selobj)

    def SetMouseModeSelection(self,musmod):
        item=self.musmoditems[musmod]
        label='MoveButton'
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)
        
    def SetSelModeSelection(self,selmod):
        item=self.selmoditems[selmod]
        label='SelNmbButton'
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)

    def SetSelObjSelection(self,selobj):
        item=self.selobjitems[selobj]
        label='SelObjButton'
        objst=self.bmpbtndic[label][1]
        self.SetButtonStatus(objst,item)

class TextMessage(object):
    """ Text message window
    
    :param obj parent: parent object
    :param int mode: mode:'standard' or 'update'. in the latter 'width' is fixed (used in fumodel:'TextWite'
    """
    def __init__(self,parent,mode):
        self.mdlwin=parent
        self.model=self.mdlwin.model
        #self.winctrl=self.model.winctrl
        #self.menuctrl=self.model.menuctrl
        self.setctrl=self.model.setctrl
        #
        self.winlabel='TextMessWin'
        self.mode=mode
        #
        self.win=None
        self.panel=None
        self.open=False
        #
        self.winpos=[]
        self.winsize=[]
        self.winbgcolor=''
        self.hight=25
        #[w,h]=self.mdlwin.GetCilentSize()
        self.width=0
        self.defaultfontsize=8
        self.defaultfont=wx.Font(self.defaultfontsize, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier 10 Pitch')
        # for normal, replace above with wx.FONTWEIGHT_NORMAL, False,...
        self.font=self.defaultfont
        self.fontsize=self.defaultfontsize
        self.textfgcolor='white'
        self.textbgcolor='balck'
        self.winbgcolor='black'
        self.mess=''
        self.move=0

    def WriteText(self,mess):
        if len(mess) <= 0:
            self.mess=''
            self.Close()
            return
        else:
            if self.win and self.mode == 'update': 
                self.UpdateText(mess); return
        self.Close()   
        #self.Clear()
        [x,y]=self.mdlwin.GetPosition()
        [w,h]=self.mdlwin.GetClientSize()
        winpos=[self.winpos[0]+x, self.winpos[1]+y]
        if len(mess) <= 0: return
        self.mess=mess
        #
        winsize=self.winsize #???
        #if len(winsize) <= 0:
        width=w-self.winpos[0]-20 #10
        if width < 10: return #width=20
        #hight=self.hight
        hight=25
        winsize=[width,hight]
        
        self.winsize=winsize #???
            
        winbgcolor=self.winbgcolor
        if len(winbgcolor) <= 0:
            winbgcolor=self.setctrl.GetParam('win-color')
            winbgcolor=numpy.array(winbgcolor[:3])*255
        #winbgcolor
        self.win=TextMessage_Frm(self.mdlwin,-1,self,winpos,winsize,mess,winbgcolor)
        #???self.win.SetTransparent(1) # if 0 fully transparent but does not recieve event!
        #
        self.win.Show()
        self.mdlwin.SetFocus() # need for WIndows
        self.open=True

    def UpdateText(self,mess):
        self.mess=mess
        self.win.textwin.Clear()
        self.win.textwin.WriteText(mess)
        self.win.Refresh()
        
    def RecoverText(self):
        self.Close()
        self.mode='notupdate'
        self.winsize=[]
        self.WriteText(self.mess)
        self.mode='update'
        
    def SetHight(self,hight):
        self.hight
    def SetWidth(self,width):
        [w,h]=self.mdlwin.GetClientSize()
        if width > w-30: width=w-30
        self.width=width
    def MoveWindow(self,dmove):
        self.curpos=self.win.GetPosition()
        if self.move:
            self.winpos=[self.curpos[0]+dmove[0],self.curpos[1]+dmove[1]]
        # destroy and create win    
        try: 
            self.win.Destroy()
            self.open=False
            try:
                self.CreateWin()
                self.open=True
            except: pass
        except: pass

    def Close(self):
        #??self.win.textwin.Destroy()
        try:
            self.win.Destroy()
            self.open=False
        except: pass

    def IsOpen(self):
        #if self.open: return True
        #else: return False
        if self.win: return True
        else: return False
                          
    def SetWinBGColor(self,color):
        self.winbgcolor=color
        """
        if len(color) <= 0: self.winbgcolor=self.setctrl.GetParam('win-color')            
        else: self.winbgcolor=color
        self.SetBackgroundColour(self.winbgcolor)
        """
    def SetPos(self,winpos):
        self.winpos=winpos

    def SetSize(self,winsize):
        self.winsize=winsize
        
    def SetFont(self,font):
        """ set font
        
        :param obj font: font: wx.font object
        """
        self.font=font
        self.font.SetPointSize(self.fontsize)
        #self.win.textwin.SetFont(self.font)

    def SetFontSize(self,fontsize):
        """ set font size
        
        :param int fontsize: fontsize in pointsize
        """
        self.fontsize=fontsize
        self.font.SetPointSize(self.fontsize)
        #self.win.textwin.SetFont(self.font)
        
    def SetTextColor(self,bgcolor,fgcolor): #,opacity):
        # opacity(int): 0:fully transparent, 255: fully opaque
        self.textbgcolor=bgcolor
        self.textfgcolor=fgcolor

    def SetTextFGColor(self,fgcolor):
        self.textfgcolor=fgcolor
    def SetTextBGColor(self,bgcolor):
        self.textbgcolor=bgcolor
        
    def SetTextColorByRGB(self,bgr,bgg,bgb,fgr,fgg,fgb):
        """
        :param int bgr,bgg,bgb: r,g,b for background color
        :param int fgb,fgg,fgb: r,g,b for foreground color
        """     
        self.textbgcolor=wx.Colour(red=bgr,green=bgg,blue=bgb,alpha=wx.ALPHA_OPAQUE)
        self.textfgcolor=wx.Colour(red=fgr,green=fgg,blue=fgb,alpha=wx.ALPHA_OPAQUE)

    def SetTextWinColorByRGB(self,r,g,b):
        """
        :param int r,g,b:
        """     
        self.winbgcolor=wx.Colour(red=r,green=g,blue=b,alpha=wx.ALPHA_OPAQUE)
     
    def Clear(self):
        if self.win: self.win.textwin.Clear()
        
class TextMessage_Frm(wx.Frame):
    def __init__(self,parent,id,mymgr,winpos,winsize,mess,winbgcolor):
        self.title='Text message panel'
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
                          style=wx.BORDER_NONE|wx.FRAME_FLOAT_ON_PARENT)
        self.mdlwin=parent
        self.model=self.mdlwin.model
        self.winctrl=self.model.winctrl
        self.setctrl=self.model.setctrl
        self.mymgr=mymgr
        #
        self.pos=winpos
        self.leftdown=False
        #
        panpos=[10,0]; pansize=[winsize[0]-20,winsize[1]]
        #self.SetTransparent(125) #alphaValue = 10 #255

        
        self.panel=wx.Panel(self,pos=[-1,-1],size=winsize)
        #self.panel.alphaValue = 10 #255

        #winbgcolor=self.setctrl.GetParam('win-color')
        #winbgcolor=numpy.array(winbgcolor[:3])*255
        self.SetBackgroundColour(winbgcolor)
        self.panel.SetBackgroundColour(winbgcolor) 
        
        self.textwin=wx.TextCtrl(self.panel,-1,pos=panpos,size=pansize)
        #self.textwin.Hide()
        self.textwin.SetTransparent(1) 
        
        
        font=self.mymgr.font
        if not font: font=self.mymgr.defaultfont
        #??self.textwin.SetFont(font)
        textbgcolor=self.mymgr.textbgcolor
        if len(textbgcolor) <= 0: textbgcolor=winbgcolor
        
        self.textwin.SetBackgroundColour(textbgcolor)
        self.textwin.SetForegroundColour(self.mymgr.textfgcolor)
        
        self.textwin.SetValue(mess) #WriteText(mess)
        ###self.textwin.Show()
        #
        #self.Bind(wx.EVT_LEAVE_WINDOW,self.OnLeaveWindow) # ???
        ##self.Bind(wx.EVT_SIZE,self.OnResize)
        ###self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_LEFT_DOWN,self.OnMouseLeftDown)
        #self.Bind(wx.EVT_LEFT_UP,self.OnMouseLeftUp)
        self.Bind(wx.EVT_MOTION,self.OnMouseMove) # move or resize
        #self.Bind(wx.EVT_RIGHT_DOWN,self.OnMouseRightDown)
        #self.Bind(wx.EVT_RIGHT_UP,self.OnMouseRightUp)
        self.Bind(wx.EVT_LEFT_DCLICK,self.OnMouseLeftDClick) # popup menu

    def OnMouseLeftDown(self,event):
        if not self.leftdown: return
        self.leftdown=True
        self.move=False
        self.resize=0
        [w,h]=self.win.GetSize()
        thd=float(h/3.0)
        pos=self.ScreenToClient(wx.GetMousePosition())
        if pos[0] > 0 and pos[0] < 10: self.move=True
        if pos[0] > w-10 and pos[0] < w:
            if pos[1] < thd: self.resize=0 # uppercorner
            elif pos[1] > thd: self.resize=1 #lower corner
            else: self.resize=2 # middle

    def OnMouseLeftUp(self,event):
        self.leftdown=False

    def OnMouseMove(self,event):
        pos=self.ScreenToClient(wx.GetMousePosition())
        if abs(self.pos[0]-pos[0]) <= 1 and abs(self.pos[1]-pos[1]) <= 1: 
            self.leftdown=False
            return
        self.leftdown=False
        dx=pos[0]-self.pos[0]; dy=pos[1]-self.pos[1]
        self.mymgr.MoveWindow([dx,dy])
        self.pos=pos

    def OnMouseLeftDClick(self,event):
        print 'double click'
        pos=event.GetPosition()

    def Resize(self):
        return

    def OnEnterWindow(self,event):
        #self.CaptureMouse()
        #self.SetFocus()
        return
        
    def OnLeaveWindow(self,event):
        return

