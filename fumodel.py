#!/bin/sh
# -*- coding: utf-8

import sys
from numpy import rank
from nt import lstat
sys.path.insert(0,'.')
import wx
import os
import shutil
#import psutil
import datetime
import time
import platform as platformos
###import subprocess
###import functools
###import threading
import glob
import copy
import cPickle as pickel
import wx.glcanvas
import wx.py.crust

#---
import inspect
import functools


import webbrowser

#from wx.tools import helpviewer
###import wx.grid
###from wx.lib.combotreebox import ComboTreeBox
#import filecmp
#from wx.lib.splitter import MultiSplitterWindow
import numpy
import scipy
if int(scipy.__version__.split('.')[1]) >= 11:
    from scipy.sparse.csgraph import _validation # need for pyinstaller
    from scipy.optimize import minimize # need for pyinstaller

try: import scipy.special._ufuncs_cxx
except: pass
import scipy.io.matlab.streams

from operator import itemgetter
#import networkx
# fu modules
import const
import lib
import rwfile
import molec
import subwin
import ctrl
import draw
import graph
import cube
import view
import custom
import build
import geom
import frag

importfortlib=True
importfmopdb=True
importfucubelib=True
try: import fortlib
except: importfortlib=False
#import fmopdb
try: import fmopdb
except: importfmopdb=False

try: import fucubelib
except: importfucubelib=False

@lib.CLASSDECORATOR(lib.FUNCCALL)
class Model_Frm(wx.MiniFrame):
    """ main program of FU """
    def __init__(self,parent,srcpath,fumode,*args,**kwargs):
        winpos=[0,0]; winsize=[300,100]
        wx.MiniFrame.__init__(self,parent,-1,'FU',pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)      
        self.title='fumodel'
        # Model class: main program and CONTROLLER in MVC model
        self.fuversion=const.VERSION
        self.title=self.fuversion
        self.fumode=fumode # 0:fumodel, 1:fuPlot; 2: simple viewer
        # initial paramters in fumodel.ini file 
        self.initdic=self.SetInitialParms(srcpath)
        # check FUDATASET
        fudir=self.initdic['FUDATASET']
        if not os.path.isdir(fudir):
            mess='Not found "FUDATASET". '+fudir
            mess=mess+' Unable to continue.\n'
            mess=mess+'Set the FUDATASET directory in "src//fumodel.ini" file.'
            mess=mess+' An exapmel is found in "FUADASET//FUdocs//file-format//'
            mess=mess+'" directory.'
            wx.MessageBox(mess)
            self.Quit()
        #
        self.pid=os.getpid() # used in making scratch file name
        self.curdir=''
        self.curprj=''
        # attribute variables
        self.classnam='Model'
        # instances
        self.parent=None
        self.mdlwin=None # VIEW in MVC model 
        self.molctrl=ctrl.MolCtrl(self)
        self.mol=None  # MODEL in MVC model
        self.curmol=None # current molecule
        #XXXself.frgdic={} # fragment object dict
        self.mousectrl=None # to be created in the 'OpenMdlWin' method
        self.menuctrl=None # to be created in the 'OpenMdlWin' method
        self.winctrl=None # to be created in the 'OpenMdlWin' method
        self.helpctrl=None # help controller
        self.filehistory=lib.ListStack(self)
        #
        self.setctrl=ctrl.SettingCtrl(self,self.fuversion) 
        # raise error if FUDATASET is not found
        if not os.path.isdir(self.setctrl.fudir): raise 'FUDATASET'
        # variable flags
        self.ctrlflag=lib.DicVars(self,title='fumodel-vars')
        self.childobj=lib.DicVars(self,title='fumodel-child-objs')
        # set max. file history
        maxhis=self.setctrl.GetParam('max-file-history')
        self.filehistory.SetMaxDepth(maxhis)
        # temporary variable strage
        self.mdlargs={}
        # mdlwin(a instance of 'View_Frm)
        self.suppressmess=False
        # set const.HCBOX: hieght of combobox
        lib.SetHeightOfConboBox()
        # set flags
        self.mdlwinID=None
        self.mdlshl=None
        self.ready=False
        # openinng panel
        self.CreatePanel()
        self.HideOpenningWin()
        self.Bind(wx.EVT_CLOSE,self.OnClose)
    
    def SetInitialParms(self,srcpath):
        """ read paramters in fumodel.ini file """
        initdic={}
        inifile=srcpath+'//fumodel.ini'
        if not os.path.exists(inifile):
            if platformos.system().upper() == 'WINDOWS': 
                initdic['FUDATASET']='~//FUDATASET-0.4.0'
            else: 
                initdic['FUDATASET']=lib.ExpandUserFileName('~//FUDATASET-0.4.0')
        else: initdic=rwfile.ReadIniFile(inifile)
        initdic['srcpath']=srcpath
        fudir=initdic['FUDATASET']
        initdic['FUDATASET']=lib.ExpandUserFileName(fudir)
        return initdic
    
    def SetFileHistory(self,filehislst):
        self.filehistory.Set(filehislst)
    
    def ClearFileHistory(self):
        self.filehistory.Clear()
        try: self.menuctrl.RemoveMenuItem('File history')
        except: pass
        
    def ChangeFUMode(self,fumode):
        curmode=self.fumode
        self.fumode=fumode
        #mess='fumode has changed from '+str(curmode)+' to '+str(self.fumode)
        #self.ConsoleMessage(mess)
            
    def OpenMdlWin(self,parent,winpos=[],winsize=[]):
        self.parent=parent
        # execute 'fusetting.py' script
        setfile=self.setctrl.GetSetFile()
        shellmess=self.setctrl.ExecuteSettingScript(setfile)
        # for save atom coordinates
        self.savatmcc=lib.ListStack(self)
        self.savatmcc.SetTitle('Stack atomic coordinates for undo')
        maxundo=self.setctrl.GetParam('max-undo')
        self.savatmcc.SetMaxDepth(maxundo)
        # for save mol object
        self.savmol=lib.ListStack(self)
        self.savmol.SetTitle('Stack molecule object for undo')
        maxundo=self.setctrl.GetParam('max-undo')
        self.savmol.SetMaxDepth(maxundo)
        #
        self.bndkndsw=lib.ToggleSwitch(self)
        self.bndkndsw.SetItemList(['single','double','triple','aromatic'])  
        #
        #winsize=self.setctrl.GetParam('win-size') #winsize
        #if winsize[0] <=0 or winsize[1] <= 0: winsize=self.setctrl.winsize
        #
        if len(winsize) <= 0:
            winsize=self.setctrl.winsize
            if winsize[0] < 400: winsize[0]=400
            if winsize[1] < 100: winsize[1]=100
        if len(winpos) <= 0: winpos=self.setctrl.winpos
        self.curdir=self.setctrl.curdir
        # create Model_View window
        self.mdlwinID=wx.NewId()
        self.mdlwin=view.View_Frm(parent,self.mdlwinID,winpos,winsize) #,self) # VIEW in MVC model 
        # open menu, mouse and window manager
        self.mousectrl=ctrl.MouseCtrl(self) # mouse-keyboard event handler
        self.menuctrl=ctrl.MenuCtrl(self) # menu event handler
        # self.menuctrl.OnSelect("Unlimited",False)
        self.winctrl=ctrl.WinCtrl(self) # window manager
        # open model view window
        self.mdlwin.CreateViewPanel(self,self.fumode) # VIEW in MVC model
        self.openmdlwin=True
        const.MDLWIN=self.mdlwin
        # set title
        self.curprj=self.setctrl.GetCurPrj()
        ###self.mdlwin.SetProjectNameOnTitle(self.curprj)
        # output setting message on Console
        message=self.setctrl.GetSettingMessage()
        self.ConsoleMessage(message)
        self.ConsoleMessage(shellmess)
        mess='End of initial settings for project "'+self.curprj+'"'
        self.ConsoleMessage(mess)
        self.winctrl.GetWin('Open PyShell').Update() # needs for MS WINDOWS
        #self.RunShellCmd('')
        shlwin=self.winctrl.GetWin('Open PyShell')
        self.mdlshl=shlwin.shell
        if self.setctrl.GetParam('redirect'):
            shlwin.shell.redirectStdout(True)
            shlwin.shell.redirectStderr(True)
        # check menu
        self.menuctrl.UncheckProjectMenuItems()
        self.menuctrl.CheckMenu(self.curprj,True)
        self.menuctrl.CheckMenu("Enable MessageBox",True)
        const.EXECMENU=self.menuctrl.ExecMenu
        # Text buffer (On memory file)
        self.textbuff=lib.TextBuffer(self.mdlwin,self)
        # check fortran modules
        self.CheckFortranModules() 
        # help controller
        self.helpctrl=ctrl.HelpCtrl(self)
        # turn ready on
        self.ready=True
        # read molecules
        self.molctrl.ClearMol()
        if self.fumode == 0 and self.curprj != 'None': 
            self.setctrl.LoadProjectMolecules(self.curprj)
        # logging
        self.SetLoggingMethod()
        savelog=self.setctrl.GetParam('save-log')
        self.SaveLog(savelog)
        # futools
        pyshell=self.winctrl.GetWin('Open PyShell')
        #self.pyshellrect=pyshell.GetRect()      
        fut=False
        if self.setctrl.GetParam('tools'):
            futools='futools.py'
            tlpyshell=wx.py.shell.ShellFrame(parent=None,id=200,pos=[0,0],
                                             size=[640,400])
            scrdir=self.setctrl.GetDir('Scripts')
            futools=os.path.join(scrdir,futools)
            lib.ExecuteScript1(tlpyshell.shell,futools)
            tlpyshell.Hide()
            self.HideToolsWin()
            pyshell.shell.prompt()
            text=tlpyshell.shell.GetText()
            if text.find('Error') >= 0: 
                fut=False
                self.ConsoleMessage('# Error occurred in "futool.py".')
                tlpyshell.Show()
                tlpyshell.SetFocus()
            else:
                self.setctrl.SetParam('pyshellwin-move-free',True) 
                pyshell.SetStatusText('Tools commands are availabel')
                if self.setctrl.GetParam('hide-mdlwin'): 
                    self.HideMdlWin()
                    self.ShowToolsWin()
            pyshell.shell.prompt()
        if not fut:
            self.setctrl.SetParam('tools',False)
            self.setctrl.SetParam('pyshellwin-move-free',False)      
            pyshell.SetStatusText('Tools commands are not availabel')
        #
        # geom
        self.geom=geom.Geometry(self.mdlwin)
        # fragment instance
        try: self.frag=frag.Fragment(self)
        except: self.frag=None
        # check logfile menu
        self.menuctrl.CheckMenu('Save log',self.setctrl.GetParam('save-log'))        
        # font
        self.SetTextFont()
        
    def SetPyShellWinMoveFree(self,on):
        self.setctrl.SetParam('pyshellwin-move-free',on)
        
    def ShowToolsWin(self):
        toolswin=wx.FindWindowByName('FUTOOLSWIN')
        if toolswin.IsShown(): toolswin.SetFocus()
        else: toolswin.Show()
        #self.menuctrl.CheckMenu('futools.py',True)

    def HideToolsWin(self):
        toolswin=wx.FindWindowByName('FUTOOLSWIN')
        try:
            if toolswin.IsShown(): toolswin.Hide()
            else: pass
        except: pass
        #self.menuctrl.CheckMenu('futools.py',False)
    
    def ShowMdlWin(self):
        pyshell=self.winctrl.GetWin('Open PyShell')
        loader=wx.FindWindowByName('FULOADER')
        setloader=wx.FindWindowById(100)
        toolsloader=wx.FindWindowById(200)
        toolswin=wx.FindWindowByName('FUTOOLSWIN')
        #tutorialwin=wx.FindWindowByName('Tutorial')
        donotlst=[pyshell,loader,setloader,toolsloader,toolswin]
        try:
            loader=wx.FindWindowByName('FULOADER')
            setloader=wx.FindWindowById(100)
            toolsloader=wx.FindWindowById(200)
            for w in wx.GetTopLevelWindows():
                if w in donotlst: continue
                #if w == pyshell or w == loader or w == setloader or \
                #                    w == toolsloader: continue
                w.Show()
            self.mdlwin.Show()
            self.hidemdlwin=False
        except: pass
        if toolswin.IsShown(): toolswin.CheckShowMdlWinMenu(True)
        
    def HideMdlWin(self):
        pyshell=self.winctrl.GetWin('Open PyShell')
        toolswin=wx.FindWindowByName('FUTOOLSWIN')
        tutorialwin=self.winctrl.GetWin('Tutorial')
        try:
            for w in wx.GetTopLevelWindows(): 
                if w== pyshell or w == toolswin or w == tutorialwin: continue 
                w.Hide()
            self.mdlwin.Hide()
            self.hidemdlwin=True
        except: pass
        if toolswin.IsShown(): toolswin.CheckShowMdlWinMenu(False)

    def HideWin(self):
        try: self.mdlwin.molchoice.win.Hide()
        except: pass
        try: self.mdlwin.mousemode.win.Hide()
        except: pass
        try: self.mdlwin.Hide()
        except: pass
        
    def ShowWin(self):
        try: self.mdlwin.Show()
        except: pass
        try: self.mdlwin.molchoice.win.Show()
        except: pass
        try: self.mdlwin.mousemode.win.Show()
        except: pass
        
    def CheckMemory(self):
        h.heap()
        

        
    def CheckFortranModules(self):
        # fortlib
        self.ConsoleMessage('')
        self.ConsoleMessage('# Import Fortran modules:')
        if not importfortlib:
            mess='Warning: Fortran module "fortlib" is not imported.'
            self.ConsoleMessage(mess)
        else: self.ConsoleMessage('"fortlib" is imported.')
        # fmopdb
        if not importfmopdb:
            mess='Warning: Fortran module "fmopdb" is not imported.'
            self.ConsoleMessage(mess)
        else: self.ConsoleMessage('"fmopdb" is imported.')
        # fucubelib
        if not importfucubelib:
            mess='Warning: Fortran module "fucubelib" is not imported.'
            self.ConsoleMessage(mess)
        else: self.ConsoleMessage('"fucubelib" is imported.')
        
    def Ready(self):
        #if not self.mol: return False
        #if len(self.mol.atm) <= 0: return False
        #if self.molctrl.GetNumberOfMols() <= 0: return False
        #return self.ready
    
        return self.ready

    def RunSetFile(self):
        """
        run setting script file
        """
        # initial setting (run 'fusetting.py')
        setfile=self.setctrl.GetSetFile()
        if os.path.exists(setfile):
            self.ConsoleMessage('Execute initial setting script.')
            self.RunScript(setfile)
        self.ready=True

    def Iconize(self,on):
        """
        iconize 'mdlwin' window
        
        :param bool on: True for iconize, False for restore 
        """
        if on and not self.mdlwin.IsIconized(): 
            self.mdlwin.Iconize(True)
            if self.mousectrl.mousemode.win: 
                self.mousectrl.mousemode.win.Iconize(True)
            if self.mousectrl.molchoice.win: 
                self.mousectrl.molchoice.win.Iconize(True)
        if not on and self.mdlwin.IsIconized(): 
            self.mdlwin.Iconize(False)
            if self.mousectrl.mousemode.win: 
                self.mousectrl.mousemode.win.Iconize(False)
            if self.mousectrl.molchoice.win: 
                self.mousectrl.molchoice.win.Iconize(False)

    def Quit(self):
        """
        destroy 'fu loader'(created in fu.py) and 'mdlwin' window
        """
        
        const.CONSOLEMESSAGE('Quit is called')
        
        
        try: wx.FindWindowByName('FULOADER').Destroy()
        except: pass
        try: self.mdlwin.Destroy()
        except: pass
        self.ExitModel() #sys.exit()
                 
    def ExitModel(self):
        """
        quit the program (execute sys.exit())
        """
        #self.WriteIniFile()
        try:
            if self.curprj != 'None': self.WriteProjectIniFile()
        except: pass
        try:
            if lib.LOGGING:
                mess='\nLogging stopped at '+lib.DateTimeText()+'\n'
                self.ConsoleMessage(mess)
        except: pass
        #except: pass
        #
        sys.exit()
        #wx.Exit()
                    
    def SetFMOMenuFlag(self,value):
        # value(bool): True for On, False for Off
        self.fmomenu=value

    def GetProgramPath(self,setfile,prgnam):
        if not os.path.exists(setfile): return
        #programpathdic={}
        f=open(setfile)
        for s in f.readlines():
            if len(s) <= 0: continue
            ns=s.find('#')
            if ns > 0: s=s[:ns]
            s=s.strip()
            if len(s) == 0: continue
            if s[0:1] == '#': continue
            if s[0:7] == 'program':
                s=s[7:]; s=s.strip(); sn=s
                ns=s.find(' '); sd=""
                if ns >= 0:
                    sn=sn[:ns]; sn=sn.strip()
                    s=s[ns+1:]; s.strip(); sd=s
                if sn == prgnam and len(sd) > 0:
                    #programname.append(sn)
                    #programpathdic[sn]=sd
                    prgpath=sd
        f.close()
        
        return prgpath
                         
    def GetPrgPath(self,setfile):
        if not os.path.exists(setfile): return
        f=open(setfile)
        for s in f.readlines():
            if len(s) <= 0: continue
            ns=s.find('#')
            if ns > 0: s=s[:ns]
            s=s.strip()
            if len(s) == 0: continue
            if s[0:1] == '#': continue
            if s[0:7] == 'program':
                s=s[7:]; s=s.strip(); sn=s
                ns=s.find(' '); sd=""
                if ns >= 0:
                    sn=sn[:ns]; sn=sn.strip()
                    s=s[ns+1:]; s.strip(); sd=s
                if len(sd) > 0:
                    self.programname.append(sn)
                    self.programpathdic[sn]=sd
        f.close()
 
    def ChangePath(self,filename):
        self.curdir=os.path.dirname(filename)
        #self.ConsoleMessage('change path: curdir='+self.curdir)
        self.setctrl.SetParam('curdir',self.curdir)
        self.WriteIniFile()

    def WriteIniFile(self):
        # write path name on file "filename
        inifile=self.setctrl.inifile
        mess='# fumodel.ini file '+lib.CreatedByText()+'\n'
        mess=mess+'# inidir: current directory.\n'
        #mess=mess+'# iniprj: current project. can be "None".\n'
        mess=mess+'# winpos: initial window position, "x,y" in pixels\n'
        mess=mess+'# winpos: initial window size, "x,y" in pixels\n'
        mess=mess+'# FUDATASET: default is C://FUDATASET(WINDOWS), and '
        mess=mess+'~//FUDATASET(MAC and LINUX)\n'
        mess=mess+'#\n'
        #
        if self.curdir == '': self.curdir=self.setctrl.GetFUPath()
        if lib.GetPlatform() != "WINDOWS":
            curdir=lib.CompressUserFileName(self.curdir) #self.setctrl.GetCurDir())
        else: curdir=self.curdir
        curdir=lib.ReplaceBackslash(self.curdir)
        #curprj=lib.CompressUserFileName(self.curprj) #self.setctrl.GetCurPrj())
        curprj=lib.ReplaceBackslash(self.curprj)
        #cursetfile=lib.CompressUserFileName(self.setctrl.GetSetFile())
        curdir='inidir='+curdir+'\n'
        #curprj='iniprj='+curprj+'\n'
        #cursetfile='iniset='+cursetfile+'\n'
        fudir=self.setctrl.fudir
        fudataset='FUDATASET='+fudir+'\n'
        pos=self.mdlwin.GetPosition()
        winpos='winpos='+str(pos[0])+','+str(pos[1])+'\n'
        size=self.mdlwin.GetSize()
        winsize='winsize='+str(size[0])+','+str(size[1])+'\n'
        win=self.winctrl.GetWin('Open PyShell')
        rect=win.GetRect()
        pyshellpos='pyshellpos='+str(rect[0])+','+str(rect[1])+'\n'
        pyshellsize='pyshellsize='+str(rect[2])+','+str(rect[3])+'\n'
        #
        f=open(inifile,"w")
        f.write(mess)
        f.write(fudataset)
        f.write(curdir)
        #f.write(curprj)
        f.write(winpos)
        f.write(winsize)
        f.write(pyshellpos)
        f.write(pyshellsize)
        #if nhis > 0: 
        hislst=self.filehistory.Get()
        nhis=len(hislst)
        f.write('# file history\n')
        f.write('filehistory=[\n')
        if nhis > 0:
            for i in range(nhis):
                text=''
                if i == nhis-1: text="'"+hislst[i].strip()+"'"
                else: text="'"+hislst[i].strip()+"',"
                f.write(text+'\n')
        f.write(']')
        f.close()

    def WriteProjectIniFile(self):
        """ Write project 'inifile' ('project-name.ini' in project directory).
        """
        nmol=self.molctrl.GetNumberOfMols()        
        if nmol <= 0: return

        prjpath=self.setctrl.GetProjectPath(self.curprj)
        inifile=self.curprj+'.ini'
        inifile=os.path.join(prjpath,inifile)
        if lib.GetPlatform() != 'WINDOWS': inifile=lib.ExpandUserFileName(inifile)
        print 'inifile in WriteProjectIniFile',inifile

        f=open(inifile,"w")
        mess='# '+inifile+' '+lib.CreatedByText()+'\n'
        mess=mess+'# inidir: current directory.\n'
        mess=mess+'# winpos: initial window position, "x,y" in pixels\n'
        mess=mess+'# winpos: initial window size, "x,y" in pixels\n'
        #
        
        if self.curdir == '': curdir=prjpath
        else: curdir=self.curdir
        if lib.GetPlatform() != "WINDOWS":
            curdir=lib.CompressUserFileName(curdir) #self.setctrl.GetCurDir())
        #cursetfile=lib.CompressUserFileName(self.setctrl.GetSetFile())
        curdir='inidir='+curdir+'\n'
        pos=self.mdlwin.GetPosition()
        winpos='winpos='+str(pos[0])+','+str(pos[1])+'\n'
        size=self.mdlwin.GetSize()
        winsize='winsize='+str(size[0])+','+str(size[1])+'\n'
        curmolnam=self.mol.name
        molfiles=[]
        for i in range(nmol): 
            file=self.molctrl.GetMol(i).outfile
            if file == '': file=self.molctrl.GetMol(i).inpfile
            molfiles.append(file)
        #
        f=open(inifile,"w")
        f.write(mess)
        f.write(curdir)
        f.write(winpos)
        f.write(winsize)
        # write loaded molecule files
        f.write('current molecule='+curmolnam+'\n')
        for filnam in molfiles: f.write('molecule='+filnam+'\n')      
        f.close()
                          
    def ModeMessage(self,mess):
        """ display message in 3-rd field of statusbar.
        
        :param str mess: message text
        """   
        self.mdlwin.ModeMessage(mess) 
             
    def Message(self,mess,loc=0,color=[0,0,0]):
        """ Write message on statusbar.
        
        :param str mess: message text
        :param int loc: statusbat field number (0,1,2)
        :param slt color: text color. not used
        :seealso: ModeMessage()
        """
        self.mdlwin.Message(mess,loc,color)

    def ConsoleMessage(self,mess,level=-1):
        """ Write message on PyShell console.
        
        :param str mess: message text
        """
        #funcnam='ConsoleMessage'
        #try: 
        #    mess=self.mdlargs[funcnam]
        #    print 'consolmess',self.mdlargs[funcnam]
        #except: mess=' mess is not set'
        if level <= 0: level=const.MESSAGELEVEL
        if level <= const.MESSAGELEVEL:
            try:
                if self.winctrl.IsOpened('Open PyShell'):
                    pyshell=self.winctrl.GetWin('Open PyShell')
                    pyshell.shell.write(mess+'\n')
                    pyshell.shell.prompt()
                    #pyshell.shell.run('')
                else: print mess
            except: print mess
        if lib.LOGGING: self.WriteLogging(mess)
        
        #if self.mdlargs.has_key(funcnam): del self.mdlargs[funcnam]

    def WriteLogging(self,text):
        if not os.path.exists(lib.RESULTFILE): return
        f=open(lib.RESULTFILE,'a')
        f.write(text+'\n')
        f.close()

    def Message2(self,mess,outlog=False):
        """ Write message on both statubar(field=0) and PyShell console.
        
        :param str  mess: message text
        :seealso: ConsoleMessage(), Message()
        """
        # mess(str): message text
        self.Message(mess,0,'')
        self.ConsoleMessage(mess)
        if outlog:         
            scrdir=self.setctrl.GetDir('Scratch')
            scrfile=os.path.join(scrdir,'message.log')
            f=open(scrfile,'a')
            f.write(mess+'\n')
            f.close()

    def WarningMess(self,classnam,methodnam,mess):
        # classnam(str): class name
        # methodnam(str): Name of method
        # mess(str): message
        # ret mess(str): string data
        mess='Warning('+self.classnam+'('+methodnam+'):'+mess
        return mess

    def ConsoleListList(self,mess,datlst):
        """ Write list texts PyShell console.
        
        :param str mess: message 
        :param lst txtlst: list of texts. [[text1,[item1,item2,...]],...]
        :seealso: ConsoleListText()
        """
        try:
            pyshell=self.winctrl.GetWin('Open PyShell')
            pyshell.shell.write(mess)
            ndat=len(datlst)
            if ndat > 0:
                pyshell.shell.write("[")
                for i in range(ndat):
                    mess=""
                    for j in range(len(datlst[i])): 
                        mess=mess+str(datlst[i][j])+","
                    nstr=len(mess); mess=mess[:nstr-1]            
                    if i == ndat-1: mess="["+mess+"]]"
                    else: mess="["+mess+"]," 
                    pyshell.shell.write(mess)
            pyshell.shell.run("")
        except:
            print mess
            print datlst
 
    def ConsoleListText(self,mess,txtlst):
        """ Write list text on PyShell console.
        
        :param str mess: message 
        :param lst txtlst: list of texts. [text1(str),...]
        """
        # txtlst: ['text1','text2',...]
        try:
            pyshell=self.winctrl.GetWin('Open PyShell')
            pyshell.shell.write(mess)
            text=','.join(txtlst)
            pyshell.shell.write(text)
        except:
            for txt in txtlst: print txt

    def TextMessage(self,mess,color=[],drw=True):
        """ Write message on canvas.
        
        :param str mess: message text
        :param lst color: dummy.
        """
        drwlabel='Message'
        """for label,font,left,xpos,top,ypos,color in drwdat: """ 

        if len(mess) > 0:
            color=self.setctrl.GetParam('text-message-color')
            drwlst=[]
            drwlst.append([mess,None,'left',20,'top',50,color])
            self.draw.SetDrawData(drwlabel,'MESSAGE',drwlst)

        else: self.draw.DelDrawObj(drwlabel) # remove draw data
        
        if drw: self.DrawMol(True)
        
    def RunScriptCmd(self,script):
        try:
            pyshell=self.winctrl.GetWin('Open PyShell')
            lib.ExecuteScript1(pyshell.shell, script)
        except: pass
        
    def SysCmd(self,cmd):
        """ Execute system command
        
        :param str cmd: command, i.e. 'dir' (equivalent to input 
        'os.chdir('dir')' on console.
        """
        #out=os.popen(cmd).read()
        #self.ConsoleMessage(out)      
        # the following codes cause 'connection' error
        proc=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=None,shell=True)
        output = proc.communicate()
        print output[0]
        
    def ExecuteAddOnScript(self,script,bChecked):
        
        scrdir=self.setctrl.GetDir('Scripts')
        pyshell=self.winctrl.GetWin('Open PyShell')
        #
        ###script=os.path.join(scrdir,script)
        scriptfile=scrdir+'//'+script
        if not os.path.exists(scriptfile):
            mess="Script file '"+scriptfile+"' is not found."
            lib.MessageBoxOK(mess,"")
        else:
            method='execfile('+"'"+scriptfile+"'"+')'
            mess="Running '"+script+"' ..."
            self.scriptcheck=bChecked
            self.Message2(mess)
            # run shell
            pyshell.shell.run(method)
            self.Message2(mess)
    
    def QuotationCMD(self):
        print '! command'
    
    def ExecuteToolsScript(self,script):
        
        scrdir=self.setctrl.GetDir('Tools')
        pyshell=self.winctrl.GetWin('Open PyShell')
        #
        ###script=os.path.join(scrdir,script)
        scriptfile=scrdir+'//'+script
        if not os.path.exists(scriptfile):
            #scrdir=self.setctrl.GetDir('PetitScripts')
            #scriptfile=scrdir+'//'+script
            if not os.path.exists(scriptfile):
                mess="Script file '"+script+"' is not found."
                lib.MessageBoxOK(mess,"")
                return
            #else:
            #    verbose=self.setctrl.GetParam('verbose-petit-script')
            #    self.RunPetitScript(script,verbose)
            #    return                
        method='execfile('+"'"+scriptfile+"'"+')'
        #mess="Running '"+script+"' ..."
        #self.scriptcheck=bChecked
        #self.Message2(mess)
        # run shell
        pyshell.shell.run(method)
        #self.pycrust.shell.runfile(script)
        #self.Message2(mess)

    def ExecuteScript1(self,script):
        # execute python program in pycrust shell
        # script(str): script file name
        pyshell=self.winctrl.GetWin('Open PyShell')
        lib.ExecuteScript1(pyshell.shell,script)
        #lib.ExecuteScript1(self.winctrl.pycrust.shell,script)

    def RunScript(self,script):
        # run python program in pyshell
        # script(str): script file name
        pyshell=self.winctrl.GetWin('Open PyShell')
        out=lib.ExecuteScript1(pyshell.shell,script)
        #out=lib.ExecuteScript1(self.winctrl.pycrust.shell,script)
    def RunShellCmd(self,cmd):
        pyshell=self.winctrl.GetWin('Open PyShell')
        try: pyshell.shell.run(cmd)
        except: pass
    
    def RunPetitScript(self,script,verbose):
        """
        :param str script: script file (.py)
        :param str verbose: True for verbose, False for not
        """    
        scrdir=self.setctrl.GetDir('PetitScripts')
        pyshell=self.winctrl.GetWin('Open PyShell')
        #
        ###script=os.path.join(scrdir,script)
        script=scrdir+'//'+script
        if not os.path.exists(script):
            mess="PetitScript file '"+script+"' is not found."
            lib.MessageBoxOK(mess,"")
            return
        if verbose:
            pyshell.shell.runfile(script)
        else:
            method='execfile('+"'"+script+"'"+')'
            mess="Running '"+script+"' ..."
            #self.scriptcheck=bChecked
            self.Message2(mess)
            # run shell
            pyshell.shell.run(method)

    def ExecuteMenu(self,menulabel,check):
        self.menuctrl.CheckMenu(menulabel,check)
        self.menuctrl.ExecMenu(menulabel)
        
    def SetSuppressMessage(self,on):
        self.suppressmess=on
            
    def GetSuppressMessage(self):
        return self.suppressmess
    
    def HideWin(self):
        """ Hide model view(mdlwin) window
        
        """
        try: self.mdlwin.Hide()
        except: pass
        try: self.mdlwin.mousemode.win.Hide()
        except: pass
        try: self.mdlwin.molchoice.win.Hide()
        except: pass
        
    def ShowMdlWin(self):
        """ Hide model view(mdlwin) window
        
        """

        try: self.mdlwin.Show()
        except: pass
        try: self.mdlwin.mousemode.win.Show()
        except: pass
        try: self.mdlwin.molchoice.win.Show()
        except: pass
            
    #def DrawPlotData(self,on,save,item,pltcol,ifrg):
    def DrawPlotData(self,funcnam):
        self.ctrlflag.Set('drawsphere',False)
        [on,save,item,pltcol,ifrg]=self.mdlargs[funcnam]
        if on and save: self.SaveAtomColor(True)
        if on:
            if item == 1: # fragment
                for i in xrange(len(pltcol)):
                    for j in xrange(len(self.mol.atm)):
                        nmb=self.mol.atm[j].frgnam[3:] # should number
                        #nmb=int(nmb)
                        try: nmb=int(nmb)
                        except: nmb=1
                        if (nmb-1) == i:
                            r=pltcol[i][0]/float(255); g=pltcol[i][1]/float(255)
                            b=pltcol[i][2]/float(255); col=[r,g,b,1.0]
                            self.mol.atm[j].color=col
            else: # atom
                drawspheredata=[]
                for i in xrange(len(pltcol)):
                    r=pltcol[i][0]/float(255); g=pltcol[i][1]/float(255)
                    b=pltcol[i][2]/float(255); col=[r,g,b,1.0]
                    tmp=[]
                    tmp.append(0.5) # sphere radius
                    tmp.append(col) # shere color
                    tmp.append(self.mol.atm[i].cc) # coordinate
                    drawspheredata.append(tmp)
                if ifrg >= 0:
                    for i in xrange(len(self.mol.atm)):
                        if self.mol.atm[i].elm == 'XX': continue
                        frg=self.mol.atm[i].frgnam
                        #nmb=int(frg[3:])
                        try: nmb=int(frg[3:]) 
                        except: nmb=-11
                        if nmb != ifrg:
                            drawspheredata[i][0]=0.2
                self.draw.SetDrawSphereList(True,drawspheredata)
            
            self.DrawMol(True)
   
        if not on and not save:
            self.SaveAtomColor(False)
            self.draw.SetDrawSphereList(False,[])
            self.DrawMol(True)

    def IsDrawBusy(self):
        # ret (bool): True for busy, False for not busy
        return self.draw.Busy()

    def IsSelectedAtom(self,ia):
        """ Is the atom 'ia' selected?
        
        :param bool retcode: retcode: True for selected atom, False for not
        """
        nsel,lst=self.ListSelectedAtom()
        ans= ia in lst
        return ans

    def ListUnselectedAtoms(self):
        if not self.mol.atm: return 0,[]
        nunsel=0; lst=[]
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if not atom.select: lst.append(i)
        nsel=len(lst)
        return nunsel,lst
                           
    def ChangeMaxUndo(self,maxundo):
        self.maxundo=maxundo
        self.setctrl.SetParam('max-undo',maxundo)
        self.savecc.SetMaxDeoth(maxundo)  
    # ----- Methods related Draw 
    def SetUpDraw(self,fit): 
        self.mousectrl.Reset()

        self.menuctrl.UncheckAll()
        on=self.setctrl.GetParam('messageboxok')
        self.menuctrl.CheckMenu("Enable MessageBoxOK",on)
        if self.setctrl.GetParam('save-log'): 
            self.menuctrl.CheckMenu('Save log',True)
        self.menuctrl.CheckMenu(self.curprj,True)
        
        self.draw.ResetDraw()
        # reset mouse status
    
        self.mousectrl.SetSelMode(4) #"0) # all mouse mode reset ??

        #
        self.winctrl.ResetSubWin()

        self.SetTextFont()
        #??self.GetMouSelMode()
        self.Message('',1,'')
        #self.fmocondat=[] #???
        #self.drawbda=[] #???
        # draw molecule
        if not self.suppressmess: self.MsgNumberOfAtoms(1)
        #
        ###self.draw.SetDrawObjs({}) 
        if fit: self.FitToScreen(True,True)
        
    def MsgNumberOfAtoms(self,dev=1):
        natm,nhev,nhyd,nter=self.mol.CountAtoms()
        #mess=self.wrkmolnam+': Number of atoms='+str(len(self.mol.atm))
        mess=self.mol.name+': Number of atoms='+str(len(self.mol.atm))
        comp=' (heavy:'+str(nhev)+',hydrogen:'+str(nhyd)+')'
        if nter > 0: comp=comp+' and '+str(nter)+' TER(s).'
        mess=self.mol.name+': Number of atoms='+str(natm)+comp
        if dev == 0 or dev == 2: self.Message(mess,0,'black')  
        if dev == 1 or dev == 2: self.ConsoleMessage(mess)
        
    def SetTextFont(self):
        """ not completed """
        #self.fontcol=self.mol.drwflg['atmlblcol']
        self.fontcol=self.setctrl.GetParam('text-font-color')
        #fontsize=self.mol.drwflg['text-font-size']  
        fontsize=self.setctrl.GetParam('text-font-size')      
        self.font = wx.Font(fontsize,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier 10 Pitch')
        self.textfont = wx.Font(8,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier 10 Pitch')
        # for normal, replace above with wx.FONTWEIGHT_NORMAL, False,...
        self.textfontcol='white'
        const.FUFONT=self.textfont

    def SaveCurrentView(self):
        viewitems=self.draw.GetViewItems()
        dictxt=lib.DictToText(viewitems)
        viewtxt='viewitems='+dictxt+'\n'
        mess='"Save view" command is accepted, but logfile is not open.'
        self.ConsoleMessage(mess)
            
    def DumpCurrentView(self,dump,drw=True):
        """Dump/recover current view items in FUDATASET/Scratch directory

        :param bool dump: True for dump, False for recover        
        :param bool drw: True for redraw molecule, False do not redraw
        """
        def MakeFileName(nmb):
            fuscr=self.setctrl.GetDir('Scratch')
            filename=self.mol.name+'-'+str(nmb)+'.drwpic'
            filename=os.path.join(fuscr,filename)
            return filename
        
        datlabel='viewdata'
        if dump:
            if not self.ctrlflag.IsDefined(datlabel): 
                self.ctrlflag.Set(datlabel,[])
            viewlst=self.ctrlflag.Get('viewdata')
            nmb=len(viewlst)
            filename=MakeFileName(nmb)
            self.DumpDrawItems(drwfile=filename)
            self.ctrlflag.AppendList(datlabel,filename)        
        else:
            viewlst=self.ctrlflag.Get('viewdata')
            if len(viewlst) <= 0:
                mess='No view data for molnam='+self.mol.name
                lib.MessageBoxOK(mess,'Model(DumpCurrntView)')
                return
            else:
                nmb=len(viewlst)-1
                filename=MakeFileName(nmb)
                if not os.path.exists(filename):
                    mess='Not found view file='+filename
                    lib.MessageBoxOK(mess,'Model(DumpCurrntView)')
                    try: self.ctrlflag[datlabel].remove(filename)
                    except: pass
                    return
                self.RestoreDrawItems(drwfile=filename)
            
    def DumpDrawItems(self,drwfile=''):
        # dump drawitems on file
        if drwfile == '':
            inpfile=self.mol.inpfile
            base,ext=os.path.splitext(inpfile)
            if len(ext) <= 0: drwfile='*'
            else: drwfile=self.mol.inpfile.replace(ext,'.drwpic')    
        if drwfile == '*':
            wcard='*drwpic(*.drwpic)|*.drwpic;all(*.*)|*.*'
            drwfile=lib.GetFileName(self.mdlwin,wcard,'w',False,'*.drwpic')
            if drwfile == '': return
        drwdic={}
        # drwfile(str): filename
        drwobjs=self.draw.GetDrawObjs()
        viewitems=self.draw.GetViewItems()
        atmprms=[]
        for atom in self.mol.atm:
            atmprms.append(atom.GetDrwParamDic())
        drwdic['drwobjs']=drwobjs
        drwdic['viewitems'] =viewitems
        drwdic['atmprms']=atmprms   
        #
        f=open(drwfile,'wb')
        pickel.dump(drwdic,f)
        f.close
        #
        mess='Draw items are saved. drwfile='+drwfile
        self.ConsoleMessage(mess)
        # change current directory
        curdir=lib.GetFileNameDir(drwfile)
        if os.path.isdir(curdir):
            self.curdir=curdir; os.chdir(self.curdir)

    def RestoreDrawItems(self,drwfile=''):
        # recover draw items from file. See the DumpDrawItems method
        if drwfile == '':
            inpfile=self.mol.inpfile
            base,ext=os.path.splitext(inpfile)
            if len(ext) <= 0: drwfile='*'
            else: drwfile=self.mol.inpfile.replace(ext,'.drwpic')    
        if drwfile == '*':
            wcard='drwpic(*.drwpic)|*.drwpic;all(*.*)|*.*'
            drwfile=lib.GetFileName(self.mdlwin,wcard,'r',False,'')
            if len(drwfile) <= 0: return
        # drwfile(str): file name
        if not os.path.exists(drwfile):
            mess='Draw pickel file, '+drwfile+' is not found.'
            self.ConsoleMessage(mess); return
        f=open(drwfile,'rb')
        drwitemdic=pickel.load(f)
        f.close()
        #
        drwobjdic=drwitemdic['drwobjs']
        viewitems=drwitemdic['viewitems']
        atmprms=drwitemdic['atmprms']
        
        natm=len(self.mol.atm)
        if len(atmprms) != natm:
            mess='The Draw item data does not match to the current molecule'
            lib.MessageBoxOK(mess,'Model(RestoreDrawItems)')
            return
        #
        self.RecoverDrawObjs(drwobjdic)
        self.draw.SetViewItems(viewitems)
        for i in range(len(self.mol.atm)):
            self.mol.atm[i].SetDrwParams(atmprms[i])
        #
        self.DrawMol(True)
        mess='View is recovered in drwfile='+drwfile
        self.ConsoleMessage(mess)
        # change current directory
        curdir=lib.GetFileNameDir(drwfile)
        if os.path.isdir(curdir):
            self.curdir=curdir; os.chdir(self.curdir)

    def ApplyCurrentModelToAll(self,all=True):
        """ Apply current molecule model to all other or the following molecules
        
        :param bool all: True for all, False for the following
        """       
        curmodel=self.mol.atm[0].model
        nmol=self.molctrl.GetNumberOfMols()
        if all: ist=0
        else: ist=self.curmol
        #
        for imol in range(ist,nmol):
            if imol == self.curmol: continue
            mol=self.molctrl.GetMol(imol)
            for i in range(len(mol.atm)): mol.atm[i].model=curmodel
        
    def ListDrawPickleFileContent(self,drwfile,item):
        """ List Data in DrawPickle file 
        
        :param str drwfile: filename
        :param str item: 'drawobjs','viewitems','atmprm', or 'all'
        """
        if not os.path.exists(drwfile):
            mess='File not found. file='+drwfile
            lib.MessageBoxOK(mess,'Model(ListDrawPickleFileContent)')
            return {}
        f=open(drwfile,'rb')
        drwitemdic=pickel.load(f)
        f.close()

        #print 'Items in draw pickle file=',drwfile
        if item == 'drwobjs': return drwitemdic['drwobjs']
        if item == 'viewitems': return drwitemdic['viewitems']
        if item == 'atmprm': return drwitemdic['atmprms']
        if item == 'all': return drwitemdic
             
    def SelectNonAARes(self,res,nmb):
        """ Select Non-amino acid residues.
        
        :param str res: residue name,
        :param int nmb: residue number 'resnmb' """
        self.SetSelectAll(False)
        for atom in self.mol.atm:
            if atom.resnam == res and atom.resnmb == nmb:
                atom.select=True
        self.DrawMol(True)
        self.UpdateChildView()
        
    def MakeNonAAResList(self):
        """ make non-amino acid residue list,
        
            :return: residue list
            :rtype: lst
            """
        reslst=[]; res=''; prvres=''; nmb=-1; blk=' '
        for atom in self.mol.atm:
            res=atom.resnam
            if const.AmiRes3.has_key(res): continue
            if res == 3*blk: continue
            nmb=atom.resnmb
            snmb='%04d' % nmb
            res=res+snmb
            if res == prvres:
                continue
            else:
                reslst.append(res)
                prvres=res
        return reslst

    def GetMaxResNmb(self):
        """ get the maximum resnmb. 
        
        :return: maximum residue number(resnmb) 
        :rtype: int
        """
        natm=len(self.mol.atm)
        maxresnmb=self.mol.atm[natm-1].resnmb
        return maxresnmb
    
    def GetMaxAtmNmb(self):
        """ Get the last atmnmb.
        
        :return: maximum atom number(atmnmb) 
        :rtype: int"""
        natm=len(self.mol.atm)
        maxatmnmb=self.mol.atm[natm-1].atmnmb
        #return maxatmnmb
        return natm
    
    def ChangeStickBold(self,bold):
        """ change bond stick boldness.
        
        :param int bold: boldness """
        #self.ctrlflag.Set('stickbold',bold)
        lst=self.ListTargetAtoms()
        for i in lst: self.mol.atm[i].thick=bold
        self.DrawMol(True)

    def ChangeAtmRad(self,scale):
        """ change scale of atom radius.
        
        :param float scale: scale value """  
        lst=self.ListTargetAtoms()
        for i in lst:
            self.mol.atm[i].atmradsc=scale
        self.DrawMol(True)
        
    def ChangeVdwRad(self,scale):
        """ change scale of vdw radius.
        
        :param float scale: scale value  """ 
        lst=self.ListTargetAtoms()
        for i in lst:
            self.mol.atm[i].vdwradsc=scale
        self.DrawMol(True)

    def ChangeBackgroundColor(self,rgb,logging=False):
        """ change background color. if rgb=[], color pallet will open.
        
        :param lst rgb: rgba color list
        """
        if rgb == None: return
        if len(rgb) <= 0:
            rgb=lib.ChooseColorOnPalette(self.mdlwin,False,1.0)
        if len(rgb) <= 0: return
        #if not rgb: return
        self.setctrl.SetParam('win-color',[rgb[0],rgb[1],rgb[2],rgb[3]])
        self.draw.SetBGColor([rgb[0],rgb[1],rgb[2],rgb[3]])
        # change background color of text message panel
        if self.mdlwin.textmess.IsOpen(): self.mdlwin.textmess.RecoverText()
        #self.draw.Paint()
        self.DrawMol(True)
        
        if self.mdlwin.remarkwin:
            self.mdlwin.remarkwin.ChangeBackgroundColor(rgb)
            self.mdlwin.remarkwin.DrawColorRemark()
        #
        drwobjs=self.draw.GetDrawObjs()
        self.mol.SetDrawObjs(drwobjs)
        viewitems=self.draw.GetViewItems()
        self.mol.SetViewItems(viewitems)
        
    def ChangeBondMultiplicity(self,bndknd):
        """
        Change bond multiplicity bwtween selected two atoms.
        
        :param int bndknd: 0:delete, 1:single, 2:double, 3:triple, 
        4:aromatic bonds
        """
        #print 'bndknd in ChageBondMultiplicity',bndknd
        textlst=['delete','single', 'double', 'triple', 'aromatic']
        mname='Model(ChangeBondMultiplicity): '
        if bndknd > 4: 
            mess=mname+'keycode "'+str(bndknd)+'" is not defined.'
            self.Message(mess,0,'')
            return
        nsel,lst=self.ListSelectedAtom()
        if nsel == 2:
            atm1=lst[0]; atm2=lst[1]
        else:
            mess=mname+'Select two atoms then hit number key.'
            self.Message(mess,0,'') 
            return
        if bndknd == 0: self.DeleteBondIJ(atm1,atm2)
        else: self.SetBondMultiplicity(atm1,atm2,bndknd)
        [atmdat1,atmdat2]=self.MakeAtmDat([atm1,atm2],False)
        if bndknd == 0: mess='bond is deleted between '+atmdat1+' and '+atmdat2
        else: mess=textlst[bndknd]+' between '+atmdat1+' and '+atmdat2
        self.TextMessage('[Make Bond]: '+mess,'yellow')
        self.mousectrl.pntatmhis.Clear()
        #
        self.DrawMol(True)
            
        """
            if kind <= 4: self.DrawMol(True)
                self.mdlwin.mdlmenu.Check('Hydrogen/vdW bond',True)
                #label self.draw.SetDrawExtraBondData(False,[])
                self.draw.SetDrawData('EXTRABOND','Hydrogen/vdW bond',[])  
                self.DrawHBOrVdwBond(True)
        """

    def MakeBondIJ(self,atm1,atm2,bndmulti):
        mname='Model(MakeBondIJ): '
        try:
            self.mol.atm[atm1].conect.append(atm2)
            self.mol.atm[atm1].bndmulti.append(bndmulti)        
            self.mol.atm[atm2].conect.append(atm1)
            self.mol.atm[atm2].bndmulti.append(bndmulti) 
        except:
            mess=mname+'Failed to make bond between atoms "'+str(atm1)+'" and "'+str(atm2)+'".'
            self.Message2(mess,0,'')

    def SetBondMultiplicity(self,atm1,atm2,bndmulti):
        mname='Model(SetBondMultiplicity): '
        try: idx1=self.mol.atm[atm1].conect.index(atm2)
        except: idx1=-1
        try: idx2=self.mol.atm[atm2].conect.index(atm1)
        except: idx2=-1

        # create bond
        if idx1 < 0 or idx2 < 0: self.MakeBondIJ(atm1,atm2,bndmulti)
        else:
            self.mol.atm[atm1].bndmulti[idx1]=bndmulti
            self.mol.atm[atm2].bndmulti[idx2]=bndmulti
         
    def SetBondKind(self,atm1,atm2,bndknd):
        nset=0
        bonddic={'single':1,'double':2,'triple':3,'aromatic':4,
                 'HB':5,'CH/pi':6,'vdw':7}
        #a1=self.mol.atm[atm1][1][0]; a2=self.mol.atm[atm2][1][0]
        try: kind=bonddic[bndknd]
        except: kind=1
        if kind > 4:
            self.mol.atm[atm1].extraconect.append(atm2)
            self.mol.atm[atm1].extrabnd.append(1) # hydrogenbond code
            self.mol.atm[atm2].extraconect.append(atm1)
            self.mol.atm[atm2].extrabnd.append(1) # hydrogen bond code    
            nset=1
        else:
            self.mol.AddBond(atm1,atm2,1)
            bnd1=self.FindBondSeqNmb(atm1,atm2)
            bnd2=self.FindBondSeqNmb(atm2,atm1)
            if (bnd1 < 0 or bnd2 < 0) or not bonddic.has_key(bndknd):
                self.Message('Program error(ChangeBondKind)',0,'red')
                return nset        
            else: kind=bonddic[bndknd]
            #if kind <= 4:
            self.mol.atm[atm1].bndmulti[bnd1]=kind
            self.mol.atm[atm2].bndmulti[bnd2]=kind
            nset=1
        return nset
    
    def FindBondSeqNmb(self,atm1,atm2):
        nseq=-1
        for i in xrange(len(self.mol.atm[atm1].conect)):
            if self.mol.atm[atm1].conect[i] == atm2:
                nseq=i; break
        return nseq-1
            
    def ResetPosAtm(self):
        # reset self.posatmx and self.posatmy.
        # this routine sholud be called when molecule is modified(add or del atoms)
        self.posatmx=[]; self.posatmy=[]
        natm=len(self.mol.atm)
        #for i in xrange(natm):
        #    self.posatmx.append(10000); self.posatmy.append(10000)  
        self.posatmx=natm*[10000]; self.posatmy=natm*[10000]

    def SelectNCofCutAA(self,drw=True):
        self.SetSelectAll(False)
        for atom in self.mol.atm:
            nb=len(atom.conect)
            atm=atom.atmnam
            if atm == ' N  ' and nb == 2 or atm == ' C  ' and nb == 2:
                atom.select=True
        if drw: self.DrawMol(True)

    def MakeGrpSelAtm(self,targetatm):
        """ not coded yet """
        # make group of selected atoms
        self.mol.atm
 
    def FindRadiusAtoms(self,radius,atmlst=[]):
        # find atoms within radius from selected atoms
        nadd=0; addlst=[] 
        if len(atmlst) <= 0: nsel,lst=self.ListSelectedAtom()
        else:
            nsel=len(atmlst); lst=atmlst[:]
        if nsel <= 0:
            mess='Nothing done. Select some atoms beforehand.'
            self.Message(mess,0,'')
            return nsel,lst
        try: # fortran code
            cc1=[]; cc2=[]; threshold=radius
            for i in lst:
                atomi=self.mol.atm[i]; cc=atomi.cc
                cc1.append(cc)
            index=[]
            for atomj in self.mol.atm:
                cc=atomj.cc; cc2.append(cc)
                index.append(atomj.seqnmb)       
            rmin=0.0; rmax=threshold
            cc1=numpy.array(cc1); cc2=numpy.array(cc2)
            nadd,tmplst=fortlib.find_contact_atoms(cc1,cc2,rmin,rmax)
            for i in range(nadd):
                if tmplst[i] < 0:
                    self.Message("Error in 'find_contact_atoms' medule.",0,
                                 "black")
                    nadd=0; addlst=[]; break
                ii=tmplst[i]; ii=index[ii]
                atom=self.mol.atm[ii] #tmplst[i]] #-1]
                if atom.elm == 'XX' or atom.select: continue
                addlst.append(ii) #tmplst[i])
      
        except: # original python code
            mess='Model(FindRadiusAtoms): Fortran routine is not available!'
            self.ConsoleMessage(mess)
            for i in lst:
                atomi=self.mol.atm[i]
                if atomi.elm == 'XX': continue
                cs=numpy.array(atomi.cc)
                for atomj in self.mol.atm:
                    if atomj.select: continue
                    cm=numpy.array(atomj.cc)
                    d2=(cm[0]-cs[0])**2+(cm[1]-cs[1])**2+(cm[2]-cs[2])**2
                    d=numpy.sqrt(d2) 
                    #d=numpy.dot(cs-cm,cs-cm); d=numpy.sqrt(d)
                    if d <= radius: 
                        addlst.append(atomj.seqnmb); nadd += 1
            #print 'failed fortran find_contact_atoms'
        #
        return nadd,addlst
   
    def FindRadiusResidue(self,radius,atmlst=[]):
        # find residues within radius from selected atoms
        try: # fortran code
            nadd,tmplst=self.FindRadiusAtoms(radius,atmlst=atmlst)
            lstsel=[]; adddic={}
            for i in tmplst:
                atom=self.mol.atm[i]
                resnam=atom.resnam
                resnmb=atom.resnmb
                res=resnam+':'+str(resnmb)
                adddic[res]=i
            nadd=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                res=atom.resnam+':'+str(atom.resnmb)
                if adddic.has_key(res):
                    lstsel.append(atom.seqnmb); nadd += 1  
        except: # original python code
            mess='Model(FindRadiusResidue): Fortran routine is not available!'
            self.ConsoleMessage(mess)
            nadd=0; lstsel=[]; adddic={} 
            if len(atmlst) <= 0: nsel,lst=self.ListSelectedAtom()
            else: 
                lst=atmlst; nsel=len(lst)
            if nsel <= 0:
                mess='Nothing done. Select some atoms beforehand.'
                self.Message(mess,0,'')
                return nsel,lst
            for i in lst:
                atomi=self.mol.atm[i]
     
                if atomi.elm == 'XX': continue
                resnam0=atomi.resnam
                resnmb0=atomi.resnmb
                res0=resnam0+':'+str(resnmb0)        
                cs=numpy.array(atomi.cc)
                for atomj in self.mol.atm:
                    if atomj.select: continue
                    cm=numpy.array(atomj.cc)
                    d2=(cm[0]-cs[0])**2+(cm[1]-cs[1])**2+(cm[2]-cs[2])**2 
                    d=numpy.sqrt(d2) 
                    #d=numpy.dot(cs-cm,cs-cm); d=numpy.sqrt(d)
                    if d <= radius: 
                        resnam=atomj.resnam
                        resnmb=atomj.resnmb
                        res=resnam+':'+str(resnmb)
                        if res != res0:
                            nadd += 1; adddic[res]=nadd
            addlst=adddic.keys()
            
            nadd=0
            for atom in self.mol.atm:
                resnam=atom.resnam; resnmb=atom.resnmb
                res=resnam+':'+str(resnmb)
                for s in addlst:
                    if res == s:
                        nadd += 1; lstsel.append(atom.seqnmb)
        
        return nadd,lstsel

    def FindRadiusResidue1(self,radius):
        # find residues within radius from selected atoms
        try: # fortran code
            nadd,tmplst=self.FindRadiusAtoms(radius)
            lstsel=[]; adddic={}
            for i in tmplst:
                atom=self.mol.atm[i]
                #resnam=atom.resnam
                #resnmb=atom.resnmb
                #chain=atom.chainnam
                #resdat=resnam+':'+str(resnmb)+':'+chain
                resdat=lib.ResDat(atom)
                adddic[resdat]=i
            nadd=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                #res=atom.resnam+':'+str(atom.resnmb)
                res=lib.ResDat(atom)
                if adddic.has_key(res):
                    lstsel.append(atom.seqnmb); nadd += 1  
        except: # original python code
            nadd=0; lstsel=[]; adddic={} 
            nsel,lst=self.ListSelectedAtom()
            if nsel <= 0:
                mess='Nothing done. Select some atoms beforehand.'
                self.Message(mess,0,'')
                return nsel,lst
            for i in lst:
                atomi=self.mol.atm[i]
     
                if atomi.elm == 'XX': continue
                res0=lib.ResDat(atomi)
                cs=numpy.array(atomi.cc)
                for atomj in self.mol.atm:
                    if atomj.select: continue
                    cm=numpy.array(atomj.cc)
                    d2=(cm[0]-cs[0])**2+(cm[1]-cs[1])**2+(cm[2]-cs[2])**2 
                    d=numpy.sqrt(d2) 
                    #d=numpy.dot(cs-cm,cs-cm); d=numpy.sqrt(d)
                    if d <= radius: 
                        res=lib.ResDat(atomj)
                        if res != res0:
                            nadd += 1; adddic[res]=nadd
            addlst=adddic.keys()
            
            nadd=0
            for atom in self.mol.atm:
                res=lib.ResDat(atom)
                for resdat in addlst:
                    if res == resdat:
                        nadd += 1; lstsel.append(atom.seqnmb)
        
        return nadd,lstsel
        
    def FindRadiusFragment(self,radius):
        # find residues within radius from selected atoms
        try: # fortran code
            nadd,tmplst=self.FindRadiusAtoms(radius)
            lstsel=[]; adddic={}
            for i in tmplst:
                atom=self.mol.atm[i]
                #resnam=atom.resnam
                #resnmb=atom.resnmb
                #chain=atom.chainnam
                #resdat=resnam+':'+str(resnmb)+':'+chain
                frg=atom.frgnam
                adddic[frg]=i
            nadd=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                #res=atom.resnam+':'+str(atom.resnmb)
                frgnam=atom.frgnam
                if adddic.has_key(frgnam):
                    lstsel.append(atom.seqnmb); nadd += 1  
        except: # original python code
            nadd=0; lstsel=[]; adddic={} 
            nsel,lst=self.ListSelectedAtom()
            if nsel <= 0:
                mess='Nothing done. Select some atoms beforehand.'
                self.Message(mess,0,'')
                return nsel,lst
            for i in lst:
                atomi=self.mol.atm[i]
     
                if atomi.elm == 'XX': continue
                #res0=lib.ResDat(atomi)
                frg0=atomi.frgnam
                cs=numpy.array(atomi.cc)
                for atomj in self.mol.atm:
                    if atomj.select: continue
                    cm=numpy.array(atomj.cc)
                    d2=(cm[0]-cs[0])**2+(cm[1]-cs[1])**2+(cm[2]-cs[2])**2 
                    d=numpy.sqrt(d2) 
                    #d=numpy.dot(cs-cm,cs-cm); d=numpy.sqrt(d)
                    if d <= radius: 
                        frg=atomj.frgnam
                        if frg != frg0:
                            nadd += 1; adddic[frg]=nadd
            addlst=adddic.keys()
            
            nadd=0
            for atom in self.mol.atm:
                frg=atom.frgnam
                for frgdat in addlst:
                    if frg == frgdat:
                        nadd += 1; lstsel.append(atom.seqnmb)
        return nadd,lstsel
        
    def SelectAtomsWithLargeBfactor(self,value):
        self.SetSelectAll(False)
        nsel=0
        for atom in self.mol.atm:
            if atom.bfc >= value: atom.select=True; nsel += 1
        self.DrawMol(True)
        return nsel
    
    def SelectByAtmPrpValue(self,vmin,vmax):
        self.SetSelectAll(False)
        nsel=0
        for atom in self.mol.atm:
            if atom.atmprp >= vmin and atom.atmprp <= vmax:
                atom.select=True; nsel += 1
        self.DrawMol(True)
        return nsel
            
    def SelectAtomByValue(self,atom,value,vmin,vmax,absol=False):
        self.SetSelectAll(False)
        nsel=0
        for i in range(len(atom)):
            val=value[i]
            if absol: val=abs(val)
            if val >= vmin and val <= vmax:
                self.mol.atm[atom[i]-1].select=True; nsel += 1
        self.DrawMol(True)
        return nsel

    def SelectEnv(self,selflg):
        # selflg: 0:deselect, 2:select
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.envflag == 1:
                atom.select=selflg; nsel += 1
        if nsel <=0: self.Message('No environment atom',0,'')
        self.DrawMol(True)
        self.UpdateChildView() #(False)
        return nsel
    
    def SelectMissingAtoms(self,selflg=True):
        #lst=self.ListTargetAtoms()
        nres,resdic=self.ListMissingAtomsOfAAResidue()
        #print 'resdic',resdic
        if nres <= 0:
            self.Message("No aa residue having missing atoms.",0,"")
            return
        self.SetSelectAll(False)
        for atom in self.mol.atm:
            res=atom.chainnam+'_'+atom.resnam+':'+str(atom.resnmb)
            if resdic.has_key(res): atom.select=True
        self.DrawMol(True)
        # !!! new one    
        chainlst=self.ListChain()

        for i in range(len(chainlst)):
            for res,nmb in reslst[i]:
                res=res+":"+str(nmb)+":"+chainlst[i][0]
                resdic[res]=selflg
        for atom in self.mol.atm:
            res=atom.resnam+":"+str(atom.resnmb)+":"+atom.chainnam
            if resdic.has_key(res): atom.select=resdic[res]    
    
    def SetSelectAtom0(self,seqlst,selflg):
        # atmlst(lst): ["atmnam",...] 
        # selflg(bool): True for select, False for deselect   
        if len(seqlst) <= 0: seqlst=self.ListTargetAtoms()
        for i in seqlst: self.mol.atm[i].select=selflg
    
    def SetSelectAtom1(self,res,selflg):
        # set select flag to residues by name and number list
        # res: resnam:resnmb:chain in string
        # selflg: -:deselect,1:selsect; 2:envselect
        nsel=0
        resnam,resnmb,chain=lib.ResolveResidueName(res)
        for atom in self.mol.atm:
            i=atom.seqnmb
            if atom.elm == 'XX': continue
            #if not self.mol.atm[i][5][1]: continue
            res=atom.resnam; nmb=atom.resnmb; chainnam=atom.chainnam
            #if resnam == '':
            #    if nmb == resnmb:
            #        nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1            
            #else:
            if chain == '':
                if res == resnam and nmb == resnmb:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1
            else:
                if res == resnam and nmb == resnmb and chainnam == chain:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1
                
        return nsel
        
    def SetSelectAtom2(self,atmnam,resdat,selflg):        # atmlst: ["atmnam",...] 
        # stmstr: string of atom numbers to select, 1,2,3,...
        # selflg: True for select, False for deselect   
        nsel=0
        for atom in self.mol.atm:
            res=lib.ResDat(atom)
            if res == resdat and atom.atmnam == atmnam:
                atom.select=selflg; nsel += 1
        return nsel
                       
    def SetSelectAtmNam(self,atmnam,selflg):
        for atom in self.mol.atm:
            if atom.atmnam == atmnam: atom.select=selflg
                   
    def SetSelectAtoms(self,atmlst,selflg):
        # atmlst(lst): ["atmnam",...] 
        # selflg(bool): True for select, False for deselect   
        atmdic={}
        for i in xrange(len(atmlst)):
            atmdic[atmlst[i]]=selflg
        for atom in self.mol.atm:
            if atmdic.has_key(atom.atmnam): atom.select=selflg
                
    def SelectAtomsWithEnv(self,atmlst,renv=4.0,drw=True):
        nadd,sellst=self.FindRadiusAtoms(renv,atmlst=atmlst)
        sellst=atmlst+sellst
        self.SelectAtomByList(sellst,drw)
        
    def SetSelectRes(self,resnam,resnmb,chain,selflg):
        # set select flag to residues by name and number list
        # selflg: -:deselect,1:selsect; 2:envselect
        nsel=0
        for atom in self.mol.atm:
            i=atom.seqnmb
            if atom.elm == 'XX': continue
            #if not self.mol.atm[i][5][1]: continue
            res=atom.resnam; nmb=atom.resnmb; chnam=atom.chainnam
            if resnam == '':
                if nmb == resnmb:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1            
            else:
                if res == resnam and nmb == resnmb and chnam == chain:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1
        return nsel

    def SetSelectNH3Term(self,selflg):
        target=self.ListTargetAtoms()
        resdatdic=self.FindTerminalRes('NH3',target)
        for i in target:
            atom=self.mol.atm[i]
            resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
            res=lib.PackResDat(resnam,resnmb,chain)
            if resdatdic.has_key(res):
                self.mol.atm[i].select=True
    
    def SetSelectCOOTerm(self,selflg):
        target=self.ListTargetAtoms()
        resdatdic=self.FindTerminalRes('COO',target)
        for i in target:
            atom=self.mol.atm[i]
            resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
            res=lib.PackResDat(resnam,resnmb,chain)
            if resdatdic.has_key(res):
                self.mol.atm[i].select=True
    
    def FindConnectedGroup(self,onlynatm=False):
        grpdic={}; natmlst=[]
        netx,G=lib.NetXGraphObject(self.mol)
        """
        G=networkx.Graph()
        nodelst=[]; edgelst=[]
        for atom in self.mol.atm:
            i=atom.seqnmb
            nodelst.append(i)
            for j in atom.conect:
                if j > i: continue
                edgelst.append([i,j])
        G.add_nodes_from(nodelst)
        G.add_edges_from(edgelst)
        """
        con=netx.connected_components(G)
        if onlynatm:
            natmlst=[len(x) for x in con]
            isol=netx.isolates(G)
            return natmlst,len(isol)
        else:
            conlst=[x for x in con]
            for i in range(len(conlst)):
                grpdic[i]=list(conlst[i])
            for i in range(len(grpdic)): grpdic[i].sort()
            return grpdic
            
    def Find14Atoms(self,atm1,atm2):
        """ Find 1,4 atoms of atm1-atm2 
        
        :param int atm1: atom seqence number
        :param int atm2: atom sequence number
        :return: pnts14(lst) - sequence number of atom, [atm11(int),atm1(int),
        atm2(int),atm22(int)]
        """
        #self.ConsoleMessage('Entered Find14Atom-1')
        pnts14=[]
        
        atom1=self.mol.atm[atm1]; atom2=self.mol.atm[atm2]
        if len(atom1.conect) <= 0 or len(atom2.conect) <= 0: return pnts14
        
        #self.ConsoleMessage('Find14-2')
        atmobj=[atom1,atom2]; pnts=[-1,-1]; avoid=[atm1,atm2]
        for i in range(2):
            for j in atmobj[i].conect:
                if self.mol.atm[j].elm == 'XX': continue
                if self.mol.atm[j].seqnmb in avoid: continue
                if self.mol.atm[j].elm != ' H':
                    pnts[i]=j; break
            #self.ConsoleMessage('Find14-3. pnts='+str(pnts[i]))
            if pnts[i] < 0: pnts[i]=atmobj[i].conect[0]
        pnts14=[pnts[0],atm1,atm2,pnts[1]]
        ok=True
        for i in pnts14:
            if i < 0: ok=False 
        #self.ConsoleMessage('Find1,4. pnts1,4='+str(pnts[0])+', '+str(pnts[1]))
        #
        if ok: return pnts14
        else: []
        
    def FindTerminalRes(self,term,targetlst):
        # term: 'NH3' or 'COO'
        resdic={}; resdatdic={}
        for i in targetlst:
            atom=self.mol.atm[i]
            resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
            if not const.AmiRes3.has_key(resnam): continue
            resdat=lib.PackResDat(resnam,resnmb,chain)
            if resdic.has_key(resdat): resdic[resdat].append(i)
            else: resdic[resdat]=[]; resdic[resdat].append(i)    
        if len(resdic) > 0:
            for resdat,lst in resdic.iteritems():
                for i in lst:
                    atom=self.mol.atm[i]
                    if term == 'NH3':
                        if atom.atmnam == ' N  ' and len(atom.conect) == 4:
                            resdatdic[resdat]=True
                    if term == 'COO':
                        if atom.atmnam == ' C  ':
                            foundo=False; foundoxt=False
                            for j in atom.conect:
                                if self.mol.atm[j].atmnam == ' O  ': foundo=True
                                if self.mol.atm[j].atmnam == ' OXT': 
                                    foundoxt=True
                            if foundo and foundoxt: resdatdic[resdat]=True
                        
        return resdatdic
    
    def SetSelectRes1(self,res,selflg):
        # set select flag to residues by name and number list
        # res: resnam:resnmb:chain in string
        # selflg: -:deselect,1:selsect; 2:envselect
        nsel=0
        resnam,resnmb,chain=lib.ResolveResidueName(res)
        for atom in self.mol.atm:
            i=atom.seqnmb
            if atom.elm == 'XX': continue
            #if not self.mol.atm[i][5][1]: continue
            res=atom.resnam; nmb=atom.resnmb; chainnam=atom.chainnam
            #if resnam == '':
            #    if nmb == resnmb:
            #        nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1            
            #else:
            if chain == '':
                if res == resnam and nmb == resnmb:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1
            else:
                if res == resnam and nmb == resnmb and chainnam == chain:
                    nsel += 1; self.SetSelectedAtom(i,selflg); nsel += 1
                
        return nsel

    def SelectRes(self,resnamlst,resnmblst,chainlst,selflg):
        # select residues by name and number list
        nsel=0; nres=len(resnamlst)
        if nres <= 0: return
        for i in range(nres):
            nam=resnamlst[i]; nmb=resnmblst[i]; chnam=chainlst[i]
            nsel += self.SetSelectRes(nam,nmb,chnam,selflg)
        if nsel > 0:
            
            
            print 'selectres is called'
            
            self.DrawMol(True)
            self.UpdateChildView()
    
    def UpdateChildView(self):
        """  not coded yet"""
        # uodate child view
        return # killed this function 11Oct2013 KK
    
    
        if not self.ctrlflag.Get('*ChildViewWin'): return
        self.childwin.Redraw() #UpdateView()
        self.mdlwin.canvas.SetCurrent()
        
    def SelectResByNmb(self,resnmblst,selflg):
        # select residues by residue number list, resnamlst
        nsel=0; nres=len(resnmblst)
        if nres <= 0: return
        for i in resnmblst:
            nsel += self.SetSelectRes('',i,'',selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
    
    def SelectResidueByNmb(self,ires,selflg):
        nsel=self.SetSelectRes('',ires,'',selflg)
        if nsel > 0: self.DrawMol(True)
    
    def SelectResByAtmSeqNmb(self,a,selflg):
        # select residue where a atom belongs
        #if not self.IsResNamDefined(): return
        resnam=self.mol.atm[a].resnam
        resnmb=self.mol.atm[a].resnmb
        chain=self.mol.atm[a].chainnam
        nsel=self.SetSelectRes(resnam,resnmb,chain,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
    
    def SelectChainByAtmSeqNmb(self,a,selflg):
        # select chain where a atom belongs
        chanam=self.mol.atm[a].chainnam
        self.SelectChainNam(chanam,selflg)

    def SelectAtomByNamNmb(self,atmnam,atmnmb,selflg):
        # select atom by atmnam and atmnmb
        nsel=0; nnmb=len(atmnmb); natm=len(atmnam)
        if natm <= 0: return
        for i in xrange(natm):
            for atomj in self.mol.atm:
                if atomj.elm == 'XX': continue
                atm=atomj.atmnam; nmb=atomj.atmnmb
                if nnmb > 0:
                    if atm == atmnam[i] and nmb == atmnmb[i]:
                        atomj.select=selflg; nsel += 1
                else:
                    if atm == atmnam[i]:
                        atomj.select=selflg; nsel += 1
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
    
    def SelectFragmentByNmb(self,frgnmb,on,drw=True):
        #sellst=[]
        for atom in self.mol.atm:
            if atom.frgnmb == frgnmb: atom.select=on
        if drw: self.DrawMol(True)
            
    def SetGroupEnvFlg(self,envlst):
        nenv=len(envlst)
        if nenv <= 0: return
        for atom in envlst:
            atom.envflag=1; atom.grpnam='temp'
    
    def SelectAtomByList(self,lst,selflg,reset=False,drw=True):
        # selectatoms by list lst
        if len(lst) < 0: return
        nsel=0
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if i in lst:
                nsel += 1; atom.select=True
            else:
                if reset: atom.select=False
        if nsel > 0 and drw:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
            
    def SelectAtomByModel(self,mdl=2,drw=True):
        """ Select atoms by model """
        if mdl > 3: return
        nsel=0
        for atom in self.mol.atm:
            if atom.model == mdl: 
                atom.select=True; nsel += 1
            #else: atom.select=False
        mess='Number of selected atoms='+str(nsel)
        self.Message(mess,0)
        if drw and nsel > 0: self.DrawMol(True)
        
    def SelectAtomByAtmNmb(self,lst,selflg):
        # selctted atoms by atmnmb in list; [atmnmb0,atmnmb1,...]
        # selflg=1 for select, =0 for deselect
        nsel=0
        nlst=len(lst)
        if nlst <= 0: return
        for atom in self.mol.atm:
            atmnmb=atom.atmnmb
            i=atom.seqnmb
            for nmb in lst:
                if atmnmb == nmb:
                    nsel += 1; self.SetSelectedAtom(i,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
            
    def SelectAtomBySeqNmb(self,lst,selflg):
        # selctted atoms by sequence number in list; [atmnmb0,atmnmb1,...]
        # selflg=1 for select, =0 for deselect
        nsel=len(lst)
        if nsel <= 0: return
        self.SelectAll(False,drw=False)
        for i in lst: self.mol.atm[i].select=True
        """
        for atom in self.mol.atm:
            atmseq=atom.seqnmb
            i=atom.seqnmb
            for seq in lst:
                if atmseq == seq:
                    nsel += 1; self.SetSelectedAtom(i,selflg)
        """
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
        return nsel

    def SelectResidueByList(self,lst,selflg):
        # select residue by lst: [[chainnam,resnam0,resnmb0],[resnam1,rennmb1],...]
        # selflg=1 for select, =0 for deselect
        nsel=0; nlst=len(lst)
        if nlst <= 0: return
        for chain,selnam,selnmb in lst:
            for atomj in self.mol.atm:
                j=atomj.seqnmb
                if atomj.elm == 'XX': continue
                if atomj.chainnam != chain: continue
                res=atomj.resnam; nmb=atomj.resnmb
                if selnmb > 0:
                    if res == selnam and nmb == selnmb:
                        self.SetSelectedAtom(j,selflg); nsel += 1
                else:
                    if res == selnam:
                        self.SetSelectedAtom(j,selflg); nsel += 1
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
        return nsel

    def SelectResidueByList1(self,reslst,selflg,accum=False,drw=True):
        # select residue by lst: [[chainnam,resnam0,resnmb0],[resnam1,rennmb1],...]
        # selflg=1 for select, =0 for deselect
        nsel=0
        if len(reslst) <= 0: return
        for atom in self.mol.atm:
            resdat=lib.ResDat(atom)
            if resdat in reslst: 
                atom.select=True; nsel += 1
            else: 
                if not accum: atom.select=False
        mess='Number of selected atoms='+str(nsel)
        self.ConsoleMessage(mess)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
        
        return nsel

    def SelectChainByList(self,lst,selflg):
        # select chain by lst: [chainnam0,chainnam1,...]
        # selflg=1 for select, =0 for deselect
        nsel=0; nlst=len(lst)
        if nlst <= 0: return
        for selnam in lst:
            for atomj in self.mol.atm:
                j=atomj.seqnmb
                if atomj.elm == 'XX': continue
                cha=atomj.chainnam
                if cha == selnam:
                    self.SetSelectedAtom(j,selflg); nsel += 1
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView() #(False)
        return nsel

    def SelectByClick(self,pntatmhis,selflg,messout=True):
        # select atom/residue/.. by mouse click        
        selmod=self.mousectrl.GetSelMode()
        if selmod != 4: self.SetSelectAll(False)
        txt='Selected'; mess=''
        if not selflg: txt='Deselected'
        #
        selobj=self.mousectrl.GetSelObj()
        ncyc=1
        if selmod == 1: ncyc=2
        elif selmod == 2: ncyc=3
        elif selmod == 3: ncyc=4
        if len(pntatmhis) < ncyc: ncyc=len(pntatmhis) 
        #if selected: ncyc=1
        #selobj=self.ctrlflag.Get('selobj')
        
        for ii in range(ncyc):
            atmseq=pntatmhis[ii]
            if selobj == 0: # atom
                self.mol.atm[atmseq].select=selflg
            elif selobj == 1 or selobj == 2: # residue
                resnam=self.mol.atm[atmseq].resnam
                resnmb=self.mol.atm[atmseq].resnmb
                chain=self.mol.atm[atmseq].chainnam
                resdat=lib.PackResDat(resnam,resnmb,chain)               
                if selobj == 1: 
                    mess=txt+' residue='+resdat
                    self.SelectResidue(resdat,selflg,drw=True)
                elif selobj == 2:
                    mess=txt+' side chain of residue='+resdat
                    self.SelectSideChainOfResidue(resdat,selflg,drw=True)
                self.Message(mess,0,'')
                return
            elif selobj == 3: # peptide chain
                chanam=self.mol.atm[atmseq].chainnam
                for atom in self.mol.atm:
                    if atom.elm == 'XX': continue
                    nam=atom.chainnam
                    if nam == chanam: atom.select=selflg
                mess=txt+' chainxxxx='+chanam
            elif selobj == 4: # group
                grpnam=self.mol.atm[atmseq].grpnam
                for atom in self.mol.atm:
                    if atom.elm == 'XX': continue
                    nam=atom.grpnam
                    if nam == grpnam: atom.select=selflg
                mess=txt+' group='+grpnam
            elif selobj == 5: # fragment
                frgnam=self.mol.atm[atmseq].frgnam
                #frgnmb=self.mol.atm[atmseq][7][1]
                natf=0
                for atom in self.mol.atm:
                    if atom.elm == 'XX': continue
                    nam=atom.frgnam
                    if nam == frgnam: # and nmb == frgnmb:
                        atom.select=selflg; natf += 1
                if natf > 0:
                    mess=txt+' fragment='+frgnam
                    mess=mess+'. number of atoms='+str(natf)+'.'
                    self.Message2(mess)
                else:
                    mess='No fragment.'
        nsel,lst=self.ListSelectedAtom()
        mess=mess+', number of selected atoms='+str(nsel)
        #if nsel > 0:
        self.DrawMol(True)
        self.UpdateChildView()
        ###self.Message(mess,0,'')
        
    def CountCharge(self):
        charge=0
        #for atom in self.mol.atm: charge += atom.charge
        aareschg=self.mol.CountChargeOfAARes([])
        ionchg=self.mol.CountIonCharge([])
        charge=aareschg+ionchg
        return charge
    
    def CountAtmNam(self,atm):
        # atm:atmnam (4 characters)
        natm=0
        for atom in self.mol.atm:
            if atom.atmnam == atm: natm += 1
        return natm

    def CountAtmNam1(self,atm):
        # atm:atmnam (4 characters)
        target=self.ListTargetAtoms()
        natm=0
        for i in target:
            atom=self.mol.atm[i]
            if atom.atmnam == atm: natm += 1
        return natm
    
    def CountNumberOfResidues(self):
        resdic={}
        for atom in self.mol.atm:
            resdat=lib.ResDat(atom)
            if resdic.has_key(resdat): continue
            resdic[resdat]=True
        return len(resdic)
        
    def CountResidue(self,res):
        nres=0
        resi=''; prvres=''; nmb=-1; blk=' '
        for atom in self.mol.atm:
            resi=atom.resnam
            #if not const.AmiRes3.has_key(res): continue
            if resi != res: continue
            nmb=atom.resnmb
            snmb='%04d' % nmb
            resi=resi+snmb
            if resi == prvres: continue
            else:
                nres += 1
                prvres=resi
        return res,nres

    def CountResidue1(self,res,allatm):
        # all: True for all, False for selected atoms with show property
        nres=0
        if allatm: target=range(len(self.mol.atm))
        else: target=self.ListTargetAtoms()
        resi=''; prvres=''; nmb=-1; blk=' '
        for i in target:
            atom=self.mol.atm[i]
            if not allatm and not atom.show: continue
            resi=atom.resnam
            #if not const.AmiRes3.has_key(res): continue
            if resi != res: continue
            nmb=atom.resnmb
            snmb='%04d' % nmb
            resi=resi+snmb
            if resi == prvres: continue
            else:
                nres += 1
                prvres=resi
        return res,nres
    
    def SelectAtomsWithinDistance(self,drw=True):
        value=lib.GetValueFromUser('Enter distance in Angstroms',
                  caption='SelectAtomsWithinDistance',default=4.0)
        if value is None: return
        nsel=self.SelectByRadius(0,value,True,drw=drw)
        
    def SelectResiduesWithinDistance(self,drw=True):
        value=lib.GetValueFromUser('Enter distance in Angstroms',
                  caption='SelectAtomsWithinDistance',default=4.0)
        if value is None: return        
        nsel=self.SelectByRadius(1,value,True,drw=drw)
        
    def SelectByRadius(self,selobj,radius,flgval,drw=True):
        """ Select atoms within radius from currently selected atoms
        
        :param int selobj: 0 for atom, 1 for residue
        :param float radius: radius in Angstroms
        :param bool flgval: True for select, False for unselect 
        """
        # select atoms/residues by mouse dragging
        nadd=0; lstsel=[]
        if radius < 0.5: return

        if selobj == 0: nadd,lstsel=self.FindRadiusAtoms(radius)
        elif selobj == 1: nadd,lstsel=self.FindRadiusResidue(radius)

        self.SelectAtomByList(lstsel,flgval)
        
        if nadd > 0 and drw: self.DrawMol(True)
        nsel,lst=self.ListSelectedAtom()
        mess='SelectByRadius: Number of selected atoms='+str(nsel)
        self.Message(mess)
        
        return nadd

    def SetSelectByRadius(self,selobj,radius,flgval):
        # select atoms/residues by mouse dragging
        nadd=0; lstsel=[]
        if radius < 0.5: return

        if selobj == 0: nadd,lstsel=self.FindRadiusAtoms(radius)
        elif selobj == 1: nadd,lstsel=self.FindRadiusResidue1(radius)
        if len(lstsel) < 0: return
        nsel=0
        for i in lstsel:
            nsel += 1; self.mol.atm[i].select=True
        return nsel
      
    def MakeEnvGrpByRadius(self,selobj,radius):
        nchg=0; lstgrp=[]
        if radius < 0.5: return
        
        if selobj == 0: nchg,lstgrp=self.FindRadiusAtoms(radius)
        elif selobj == 1: nchg,lstgrp=self.FindRadiusResidue(radius)
    
        if nchg > 0:
            self.MakeEnvByList(lstgrp)
            self.DrawMol(True)        
        return nchg

    def MakeEnvByList(self,lst):
        nchg=0
        for i in lst:
            nchg += 1; self.SetEnvGrpAtom(i,True)
        if nchg > 0: self.DrawMol(True)
        else: self.Message('No environment atoms to be assigned.',0,'black')
   
    def RemoveEnvGroup(self):
        nchg=0
        for atom in self.mol.atm:
            if atom.envflag:
                nchg += 1; self.SetEnvGrpAtom(atom.seqnmb,False)
        if nchg > 0: self.DrawMol(True)
        else: self.Message('No environmet atoms.',0,'black')
            
    def SetSelectedDisplayMethod(self,value):
        # not completed yet. 10Apr2013(KK)
        # selected atom display method, green colored or bold line.
        self.ctrlflag.Set('dispselectedbycolor',value)
        self.DrawMol(True)
            
    def SetEnvGrpAtom(self,ith,on):
        atom=self.mol.atm[ith]
        if on: # on env params
            atom.color=const.ElmCol['EV']
            atom.grpnam='env'
            #self.mol.atm[ith][6][1]=-1
            atom.grpchg=0.0
            atom.envflag=1
            atom.parnam=self.wrkmolnam
            #???self.mol.atm[ith][6][5]=-1 #self.mol.atm[ith][1][0]
        else: # unset env params
            elm=atom.elm
            atom.color=const.ElmCol[elm]
            atom.grpnam='trg'
            #self.mol.atm[ith][6][1]=-1
            atom.grpchg=0.0
            atom.envflag=0
            atom.parnam=''
            #???self.mol.atm[ith][6][5]=-1

    def ListTargetAtoms(self):
        # list target atoms to operation, selected atoms or all atoms
        # ret targetatm(lst): list of target atoms
        nsel,lst=self.ListSelectedAtom()
        targetatm=[]
        if len(lst) <= 0: #all atoms
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                if not atom.show: continue 
                targetatm.append(atom.seqnmb)
        else: targetatm=lst
        targetatm.sort()
        return targetatm
    
    def ListShowAtoms(self):
        atmlst=[]
        for atom in self.mol.atm:
            if atom.show: atmlst.append(atom.seqnmb)
        return atmlst 
            
    def CountSelectedAtoms(self):
        # count number of selected atoms
        # ret nsel(int): number of selected atoms 
        nsel=0
        if not self.mol.atm: return nsel
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if not atom.show: continue
            if atom.select > 0: nsel += 1
        return nsel
                 
    def MakeBondedAtomGroupList(self,lst):
        # make list of covalent bonded atom group.
        # condat: [[cc,conect,elm],..]
        # not completed !
        grplst=[]
        if len(lst) <= 0:
            for i in xrange(len(self.mol.atm)): lst.append(i)
        
        condat=[]
        for i in lst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            tmp=[]; tmp.append(atom.seqnmb)
            tmp.append(atom.conect)
            condat.append(tmp)
        grpdic={}; ngrp=-1
        for i in xrange(len(condat)):
            ia=condat[i][0]
            if grpdic.has_key(ia):
                ig=grpdic[ia]
            else:
                ngrp += 1; ig=ngrp
                grpdic[ia]=ngrp

        return grplst
    
    def FindGrpNmb(self,ia,grplst):
        # find group number of atom ia
        ig=-1
        if len(grplst) <= 0: return ig
        for i in xrange(len(grplst)):
            for j in grplst[i]:
                if j == ia:
                    ig=i; break 
        return ig
    
    def SaveAtomColor(self,save):
        if save:
            self.savatmcol=[]
            for atom in self.mol.atm:
                self.savatmcol.append(atom.color)
        else:
            try:
                for i in xrange(len(self.mol.atm)):
                    self.mol.atm[i].color=self.savatmcol[i]
            except:
                self.ChangeAtomColor("by element") #,[])

    def ListStrGroup(self,grplst):
        strgrp=''; ngrp=len(grplst)
        for i in xrange(len(grplst)):
            strgrp=strgrp+str(i)+':'
            natj=len(grplst[i])
            if i == ngrp-1: strgrp=strgrp+str(natj)+'.'
            else: strgrp=strgrp+str(natj)+', '
        return strgrp

    def SetTurnLst(self):        
        for i in range(len(self.molnam)):
            self.turnlst.append(i)
    
    def DrawMol(self,updated):
        if not self.ready: return
        #self.mdlwin.BusyIndicator('On','Drawing ...')
        drwlabelatm='atoms'
        drwlabelbnd='bonds'
        if updated:
            nshw=self.CountShowAtoms()
            atmcc=self.MakeAtomCCForDraw([])
            self.draw.SetAtomCC(atmcc) # need in drwa.SetCamera
            atmlst=self.MakeDrawAtomData([])
            if len(atmlst) > 0: 
                self.draw.SetDrawData(drwlabelatm,'ATOMS',atmlst)
            else: self.draw.DelDrawObj(drwlabelatm)
            # draw bond
            bndlst=self.MakeDrawBondData([])
            if len(bndlst) > 0: 
                self.draw.SetDrawData(drwlabelbnd,'BONDS',bndlst)
            else: self.draw.DelDrawObj(drwlabelbnd)
        
        #if self.mousectrl.GetMdlMode() == 5:
        #    self.DrawLabelElm(True,0,drw=False)
        #
        self.draw.SetUpdated(updated)
        self.draw.Draw() #OnPaint()
        self.draw.canvas.Refresh()
        #self.mdlwin.BusyIndicator('Off')
        
    def UpdateMolViewPos(self):
        eyepos,center,upward,ratio=self.draw.GetViewParams()
        self.mol.SetViewPos(eyepos,center,upward,ratio)
            
    def ListDrawAtom(self):
        ndrw=0; drwatmlst=[]
        for atom in self.mol.atm:
            if not atom.show: continue            
            ndrw += 1; drwatmlst.append(atom)
        return ndrw,drwatmlst
    
    def MakeAtmDat(self,atmlst,nameonly):
        # atmdat: atmnam:seqnmb-resnam:resnmb:chain
        atmdatlst=[]
        for i in atmlst:
            atmnam=self.mol.atm[i].atmnam
            atm="'"+atmnam+"':"+str(i+1)
            if nameonly:
                atmdatlst.append(atm)
            else:
                resnam=self.mol.atm[i].resnam; chain=self.mol.atm[i].chainnam
                resnmb=self.mol.atm[i].resnmb
                atmdatlst.append(atm+'-'+resnam+':'+str(resnmb)+':'+chain)
        return atmdatlst
        
    def MakeAtomLabel(self,atm,nameonly):
        # display atom label
        atmnam=self.mol.atm[atm].atmnam
        atmnam.strip()
        stratmnmb=str(self.mol.atm[atm].seqnmb+1)
        label='atom '+atmnam+','+stratmnmb
        if not nameonly:
            resnam=self.mol.atm[atm].resnam; chain=self.mol.atm[atm].chainnam
            strresnmb=str(self.mol.atm[atm].resnmb)
            label=label+','+resnam+':'+strresnmb+':'+chain
            sx=str(self.mol.atm[atm].cc[0])
            sy=str(self.mol.atm[atm].cc[1])
            sz=str(self.mol.atm[atm].cc[2])
            label=label+', Coord=('+sx+','+sy+','+sz+')'
        return label
    
    def MsgAtomLabel(self,atm,nameonly):
        # display atom label
        mess=self.MakeAtomLabel(atm,nameonly)
        self.Message(mess,0,'black')

    def AtomDistance(self,atm0,atm1):
        p1=self.mol.atm[atm0].cc
        p2=self.mol.atm[atm1].cc
        return lib.Distance(p1,p2)
        
    def AtomAngle(self,atm0,atm1,atm2):    
        # display angle between three atoms; <(atm1,atm0,atm2)
        atom0=self.mol.atm[atm0]; atom1=self.mol.atm[atm1]
        atom2=self.mol.atm[atm2]
        #r10=[]; r20=[]
        r01=numpy.array(atom0.cc)-numpy.array(atom1.cc)
        r21=numpy.array(atom2.cc)-numpy.array(atom1.cc)
        numpy.array(r01); numpy.array(r21) 
        angle=lib.AngleT(r01,r21)
        return angle

    def SaveMouseSelMode(self):
        self.ctrlflag.Set('selmodsav',self.ctrlflag.Get('selmod'))
        self.ctrlflag.Set('selobjsav',self.ctrlflag.Get('selobj'))

    def RecoverMouseSelMode(self):
        selmod=self.ctrlflag.Get('selmodsav')
        selobj=self.ctrlflag.Get('selobjsav')
        self.ctrlflag.Set('selmod',selmod); self.ctrlflag.Set('selobj',selobj)
        self.mousectrl.SetSelMode(selmod)
        self.mousectrl.SetSelModeSelection(selmod)
        self.mousectrl.SetSelObj(selobj)
        self.mousectrl.SetSelObjSelection(selobj)
       
    def SetMouseSelModeForTwo(self):
        self.ctrlflag.Set('selmod',1); self.ctrlflag.Set('selobj',0)
        self.mousectrl.SetSelMode(1) # dual
        self.mousectrl.SetSelModeSelection(1)
        self.mousectrl.SetSelObj(0) # atom
        self.mousectrl.SetSelObjSelection(0)

    def SetDrawDistance(self,on):
        """ this routine set flag on/off. actual drawing will be done in 
        MsgAtomDistance().
        
        :param bool on: True for turn on the mode, False for turn off. """
        if on:
            #self.SetDrawItemsAndCheckMenu('Mode(on/off)',True)
            self.SaveMouseSelMode()
            #?self.mousectrl.SetPointedAtomHis([])
            self.mousectrl.pntatmhis.Clear()
            self.ctrlflag.Set('pntatmhis',[])
            self.SetMouseSelModeForTwo()
            self.TextMessage('[Show:Distance]','yellow')
            #self.mousectrl.OnSwitchMouseMode('Show Distance',True)
            
            if not self.ctrlflag.IsDefined('Distance'): 
                self.ctrlflag.Set('Distance',{})
            self.mousectrl.mdlmod=1
            #self.DrawMessage('modemessage','Draw Distance','',[],[])
            #self.TextMessage('Draw Distance','white',True)
        else:
            self.RecoverMouseSelMode()
            #self.mousectrl.OnSwitchMouseMode('Off')
            #self.RemoveDrawMessage('modemessage')
            self.TextMessage('','')
            self.mousectrl.mdlmod=0
            #self.ctrlflag.Set('Mode(on/off)',[])
        self.SetDrawItemsAndCheckMenu('Mode(on/off)',on)
 
    def SetDrawDistanceData(self,drw=False):
        """ this routine set flag on/off. actual drawing will be done in 
        MsgAtomDistance().
        
        :param bool on: True for turn on the mode, False for turn off. """
        drwlabel='draw-distance'
        atmpairlst=self.ctrlflag.Get(drwlabel)
        if len(atmpairlst) <= 0: return
        drwlst=[]; drwline=[]; line=[]
        #
        stipple=[2,0xcccc]; thick=0.5
        for ia,ib in atmpairlst:
            if not self.mol.atm[ia].show: continue
            if not self.mol.atm[ib].show: continue
            cca=self.mol.atm[ia].cc[:]; ccb=self.mol.atm[ib].cc[:]
            dist=lib.Distance(cca,ccb)
            sdist=('%7.3f' % dist).strip()
            color=self.setctrl.GetParam('label-color') #self.mol.labelcolor
            pos=[0.5*(cca[0]+ccb[0]),0.5*(cca[1]+ccb[1]),0.5*(cca[2]+ccb[2])]
            drwlst.append([sdist,None,pos,color])
            line.append(cca); line.append(ccb)
        drwline.append([line,color,thick,stipple])
        self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
        self.draw.SetDrawData(drwlabel,'LINE',drwline)
        #self.TextMessage('[Distance] ','yellow')
 
    def ClearDrawDistance(self):
        """ remove distance labels """
        drwlabel='Distance' # for 'ctrlflag'
        #self.draw.SetDrawData(drwlabel,'LABEL',[])
        self.draw.DelDrawObj(drwlabel)
        self.ctrlflag.Set(drwlabel,{})
        self.SetDrawItemsAndCheckMenu('Remove',False)
        self.DrawMol(True)

    def DrawMultipleBond(self,on):
        drwlabel='Multiple bond' # for 'ctrlflag'
        self.ctrlflag.Set(drwlabel,on)
        #self.mdlwin.menu.Check(drwlabel,on)
        self.menuctrl.CheckMenu(drwlabel,on)
        self.DrawMol(True)
           
    def DrawVdwBond(self,on):
        drwlabel='Hydrogen/vdW bond' # for 'ctrlflag'
        if on:
            #self.drwvdwbnd=True
            vdwdat=self.ListVdwBond()
            if len(vdwdat) <= 0:
                mess='No hydrogen/vdw bonds. Execute "Add/Del(Add)"-"Bond"'
                mess=mes+'-"Hydrogen Bond" menu'
                lib.MessageBoxOK(mess,"")
                self.SetDrawItemsAndCheckMenu(drwlabel,False)
                return
            #self.ctrlflag.Set('Hydrogen/vdw bond',True)
            
            #label self.draw.SetDrawExtraBondData(True,vdwdat)
            self.draw.SetDrawData(drwlabel,'EXTRABOND',vdwdat)
        else:
            #self.drwvdwbnd=False
            #label self.draw.SetDrawExtraBondData(False,[])   
            self.draw.DelDrawObj(drwlabel) #,'EXTRABOND',[])            
            #self.ctrlflag.Set('Hydrogen/vdw bond',False)
        self.SetDrawItemsAndCheckMenu(drwlabel,on)
        self.DrawMol(True)
    
    def ListVdwBond(self):
        target=self.ListTargetAtoms()
        #thick=self.mol.extrabndthick; col=self.mol.vdwbndcolor
        thick=self.setctrl.GetParam('extra-bond-thick')
        col=self.setctrl.GetParam('hydrogen-bond-color')
        vdwlst=[]
        for i in target:
            if not self.mol.atm[i].show: continue
            cc0=self.mol.atm[i].cc
            for j in xrange(len(self.mol.atm[i].extraconect)):
                jj=self.mol.atm[i].extraconect[j]
                if jj <= i: continue
                if not self.mol.atm[jj].show: continue
                if self.mol.atm[i].extrabnd[j] == 2:
                    cc1=self.mol.atm[jj].cc
                    vdwlst.append([cc0,cc1,col,thick])
        return vdwlst

    def PDBMissingResidueInfo(self,itemlst=[],outfile='',viewout=True,
                              messout=False):
        def MakeResDatList(reslst):
            resdatlst=[]
            for lst in reslst:
                reschain=lst[1]+':'+str(lst[2])+':'+lst[0]
                resdatlst.append(reschain)
            return resdatlst
                      
        itemlst=['missing atoms',
                 'missing residues',
                 'unknown ligands',
                 ]
        
        pdbfile=self.mol.inpfile
        base,ext=os.path.splitext(pdbfile)
        if ext != '.pdb' and ext != '.ent':
            mess='The input file is not a PDB file='+pdbfile
            lib.MessageBoxOK(mess,'Model(PDBFileInfo)')
            return
        mess='PDB file='+pdbfile+'\n\n'
        text=mess
        for item in itemlst:
            if item == 'missing atoms':
                reslst=[]
                info,missingatoms=rwfile.ReadPDBMissingAtoms(pdbfile)
                if not info:
                    mess='The info is not availabel'
                elif len(missingatoms) <= 0:
                    mess='No missing atom residues'
                else: 
                    mess='Missing atom residues: \n'
                    reslst=[]
                    for lst in missingatoms:
                        resdat=lst[1]+':'+str(lst[2])+':'+lst[0]
                        reslst.append(resdat)
                    mess=mess+str(reslst)
                    #    if len(lst[3]) > 0:
                    #        atmlst=[]
                    #        mess=mess+'    Atom names in the resdiue: \n'
                    #        for atmnam in lst[3]: atmlst.append(atmnam)
                    #        mess=mess+'    '+str(atmlst)+'\n'
                if not viewout: return reslst
                if messout: self.ConsoleMessage(mess)
                text=text+mess+'\n\n'
            if item == 'missing residues':
                resdatlst=[]
                info,missingresidues=rwfile.ReadPDBMissingResidues(pdbfile)
                if not info:
                    mess='The info is not availabel'
                elif len(missingresidues) <= 0:
                    mess='No missing residues'
                else: 
                    resdatlst=[]
                    for lst in missingresidues:
                        reschain=lst[1]+':'+str(lst[2])+':'+lst[0]
                        resdatlst.append(reschain)
                    mess='Missing residues: \n'+str(resdatlst)  
                if messout: self.ConsoleMessage(mess)
                text=text+mess+'\n\n'
                if not viewout: return resdatlst
            if item == 'unknown ligands':
                unkres=[]
                for i in xrange(len(self.mol.atm)):
                    atom=self.mol.atm[i]
                    if atom.resnam == 'UNL':
                        resdat=lib.ResDat(atom)
                        if not resdat in unkres: unkres.append(resdat)
                if len(unkres) <= 0:
                    mess='No unknown residues("UNL")'
                else: mess='Unknown("UNL") residues: \n'+str(unkres)  
                if messout: self.ConsoleMessage(mess)
                text=text+mess+'\n\n'
                if not viewout: return unkres
        # open viewer
        if viewout:
            title='Missing Residues Info in PDB File'
            viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,menu=True)
            viewer.SetText(text)
        # write file
        if outfile != '':
            f=open(outfile); f.write(text); f.close()
 
    def MoleculeInfo(self,itemlst=[],outfile='',viewout=True,messout=False):
        # count
        if len(itemlst) <= 0:
            itemlst=["Number of atoms",
                     "Chemical formula",
                     "Total charge",
                     "Residues",
                     "Unique AA residues",
                     "Unique non-AA residues",
                     "Residue charge",
                     "Disconnected groups",
                     ]
        if self.mol is None: return
        text='Molecule info '+lib.DateTimeText()+'\n'
        text=text+'molecule='+self.mol.name+'\n'
        text=text+'file='+self.mol.inpfile+'\n\n'
        for item in itemlst:
            if item == "Number of atoms":
                nter=0; natm=0; nhyd=0
                for i in xrange(len(self.mol.atm)):
                    atom=self.mol.atm[i]
                    if atom.elm == 'XX': nter += 1
                    else:
                        if atom.elm == ' H': nhyd += 1
                        natm += 1
                mess='Total number of atoms'
                if nter > 0: mess=mess+' (excluding "TER")'
                mess=mess+'='+str(natm)+'\n'
                if nter > 0:
                    mess=mess+'   Number of "TER"='+str(nter)+'\n'
                if nhyd > 0:
                    mess=mess+'   Number of hydrogens='+str(nhyd)+'\n'
                #if messout: self.ConsoleMessage(mess)
                text=text+mess
            
            if item == 'Residues':
                # resiude
                chaindic={}; resdic={}
                reslst=self.ListResidue3('all')
                for resdat in reslst:
                    res,nmb,chain=lib.UnpackResDat(resdat)
                    if not resdic.has_key(res): resdic[res]=1
                    else: resdic[res] += 1
                    if not chaindic.has_key(chain): chaindic[chain]={}
                    if not chaindic[chain].has_key(res): chaindic[chain][res]=1
                    else: chaindic[chain][res] += 1
                mess='Total number of redisues='+str(len(reslst))+'\n'
                #if messout: self.ConsoleMessage(mess)
                text=text+mess
                reskind=['aa','non-aa','water']
                resmess=['amino acid residue','non-amino acid residue','water']
                mess=''
                for i in range(len(reskind)):
                    reslst=self.ListResidue3(reskind[i])
                    if len(reslst) > 0:
                        mess=mess+'   Number of '+resmess[i]+'='
                        mess=mess+str(len(reslst))+'\n'
                #if messout: self.ConsoleMessage(mess)
                text=text+mess
                
                resdickey=resdic.keys()
                resdickey.sort()
                messlst=[]
                for res in resdickey: messlst.append([res,resdic[res]])
                #if messout: self.ConsoleMessage('Resiude lsit:')
                text=text+'   Residue list:\n'
                #if messout: self.ConsoleMessage(str(messlst))    
                text=text+'   '+str(messlst)
                #if messout: self.ConsoleMessage('\n') 
                text=text+'\n'    
                # chain
                mess=''
                chainlst=chaindic.keys()
                text=text+'\n'
                mess='Number of chains='+str(len(chainlst))+'\n'
                if len(chainlst) == 1: mess=mess+'   Chain='+chainlst[0]+'\n'
                if len(chaindic) > 1:
                    chainlst.sort()
                    mess=mess+'\n'
                    mess='Total number of chains='+str(len(chainlst))+'\n'
                    for i in range(len(chainlst)):
                        chainnam=chainlst[i]; nres=0
                        resnamlst=chaindic[chainnam].keys()
                        resnamlst.sort(); reslst=[]
                        for j in range(len(resnamlst)):
                            res=resnamlst[j]; nmb=chaindic[chainnam][res]
                            reslst.append([res,nmb])
                            nres += nmb
                        mess=mess+'   Chain='+chainnam+'\n'
                        mess=mess+'   Number of residues='+str(nres)+'\n'
                        mess=mess+'   Residue list:\n'
                        mess=mess+'   '+str(reslst)+'\n'
                text=text+mess
                if messout: self.ConsoleMessage(text)
            
            if item == "Chemical formula":
                elmlst=[]
                for atom in self.mol.atm: elmlst.append(atom.elm)
                chemlst,chemstring=lib.ChemFormula(elmlst)
                mess='Chemical fomula: '+chemstring+'\n'
                if messout: self.ConsoleMessage(mess)
                text=text+mess
            if item == "Total charge":
                charge=self.CountCharge()
                mess='Total charge='+str(charge)+'\n'
                if messout: self.ConsoleMessage(mess)
                text=text+mess
            if item == "Disconnected groups":
                natmlst,nisolated=self.FindConnectedGroup(onlynatm=True)
                nwat=self.mol.CountWater([])
                mess='Number of '+item+'='+str(len(natmlst))+'\n'
                mess=mess+'    Number of waters='+str(nwat)+'\n'
                mess=mess+'    Nonbonded atoms(TER or ion?)='+str(nisolated)+'\n'
                if messout: self.ConsoleMessage(mess)
                text=text+mess
            if item == "Valence":
                pass
            if item == "Unique AA residues":
                pass
            if item == "Unique non-AA residues":
                pass
        # open viewer
        if viewout:
            title='Molecule Info'
            viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,menu=True)
            viewer.RemoveOpenMenu()
            viewer.SetText(text)
        # write file
        if outfile != '':
            f=open(outfile); f.write(text); f.close()
                
    def SummaryOfAddHydrogens(self):
        def MakeChemFormula(optn,resdat='',chainnam=''):
            """ optm='total','chain', or 'residue' """
            elmlst=[]
            if optn == 'total': 
                for atom in self.mol.atm: 
                    if atom.resnam in const.WaterRes: continue
                    elmlst.append(atom.elm)
            elif optn == 'chain':
                for atom in self.mol.atm:
                    if atom.resnam in const.WaterRes: continue
                    if atom.chainnam == chainnam: elmlst.append(atom.elm)
            elif optn == 'residue':
                for atom in self.mol.atm:
                    if lib.ResDat(atom) == resdat: elmlst.append(atom.elm)
            chemlst,chemstring=lib.ChemFormula(elmlst)
            return chemstring
            
        # count
        if self.mol is None: return
        blk3=3*' '; blk6=6*' '; fi6='%6d'
        text='Summary of hydrogen addition '+lib.DateTimeText()+'\n'
        text=text+'molecule='+self.mol.name+'\n'
        text=text+'file='+self.mol.inpfile+'\n\n'
        # total system
        chem=MakeChemFormula('total')
        text=text+'Total system(except waters): '+chem+'\n'
        # chains
        chainlst=self.ListChain()
        text=text+'Number of chains='+str(len(chainlst))+'\n'
        for i in range(len(chainlst)):
            chainnam=chainlst[i][0]
            text=text+blk3+'Chain number='+str(i+1)+', name='+chainnam
            chem=MakeChemFormula('chain',chainnam=chainnam)
            text=text+', '+chem+'\n'
            # residues
            resdatlst=self.ListResidue5(chainnam)
            text=text+blk3+'number of resdiues(except waters) in the chain='
            text=text+str(len(resdatlst))+'\n'    
            for j in range(len(resdatlst)):
                resdat=resdatlst[j]
                text=text+blk6+(fi6 % (j+1))+' '+resdat
                chem=MakeChemFormula('residue',resdat=resdat)
                text=text+', '+chem+'\n'                
        # waters
        watlst=self.ListWaterAtoms()
        text=text+'Number of waters='+str(len(watlst))+'\n'
        # check hydrogens
        if len(watlst) > 0:
            misslst=[]; atmnmbdic={}
            watres=self.ListResidue3(reskind='wat')
            for atom in self.mol.atm: #range(len(watlst)):
                if not atom.resnam in const.WaterRes: continue
                resdat=lib.ResDat(atom)
                if not atmnmbdic.has_key(resdat): atmnmbdic[resdat]=0
                atmnmbdic[resdat] += 1
            for resdat,nmb in atmnmbdic.iteritems():
                if nmb < 3: misslst.append(resdat)
            if len(misslst) > 0:
                text=text+blk3+'Missing hydrogen waters='+str(misslst)+'\n'
        text=text+'\n'
        # open viewer
        title='Add hydrogen summary'
        viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,menu=True)
        viewer.SetText(text)
        viewer.RemoveOpenMenu()
        
    def ViewMessageLog(self):
        scrdir=self.setctrl.GetDir('Scratch')
        messfile=os.path.join(scrdir,'message.log')
        if not os.path.exists(messfile):
            mess='No message log file='+messfile
            lib.MessageBoxOK(mess,'Model(ViewMessageLog)')
        else:
            title='View Message Log'
            viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,
                                         textfile=messfile,menu=True)
            viewer.RemoveOpenMenu()

    def ClearScreen(self):
        # Clear screen
        self.draw.ClearScreen()
 
    def DrawHBOrVdwBond(self,on,atmlst=[],addto=False,drw=True):
        drwlabel='Hydrogen Bonds' # for 'ctrlflag'
        if len(atmlst) <= 0:
            atmlst=self.ListTargetAtoms()
        if on:
            if not addto: self.draw.DelDrawObj(drwlabel) #,'EXTRABOND',[])  
            extdat=self.ListExtraBond(atmlst,within=False)
            if len(extdat) <= 0:
                allatms=range(len(self.mol.atm))
                extdatall=self.ListExtraBond(allatms)
                if len(extdatall) <= 0:
                    mess='No hydogen bond data. Please Execute "Modeling"-'
                    mess=mess+'"Add Bond"-"Hydrogen Bond" menu.'
                    #lib.MessageBoxOK(mess,"")
                    self.MakeHydrogenBond()
                    
                
                else:
                    mess='The selected atoms have no hydrogen bonds.'
                    self.ConsoleMessage(mess)
                self.SetDrawItemsAndCheckMenu(drwlabel,False)
                return
            mess='Number of hydrogen bonds='+str(len(extdat))
            if len(atmlst) == 1:
                mess=mess+' of atom number='+str(atmlst[0]+1)
            else: mess=mess+' of selected '+str(len(atmlst))+' atoms.'
            self.ConsoleMessage(mess)
            self.draw.SetDrawData(drwlabel,'EXTRABOND',extdat)
        else:
            #self.drwvdwbnd=False
            self.draw.DelDrawObj(drwlabel) #,'EXTRABOND',[])            
            #self.ctrlflag.Set('drawhydrogenbond',False)
        #self.menuctrl.CheckMenu(drwlabel,on)
        self.SetDrawItemsAndCheckMenu(drwlabel,on)
        if drw: self.DrawMol(True)
    
    def ListExtraBond(self,atmlst=[],within=True):
        def CheckDone(donedic,i,j):
            done=False
            ii=min(i,j); jj=max(i,j)
            idx=str(ii)+':'+str(jj)
            if donedic.has_key(idx): done=True
            return done
        
        target=atmlst
        if len(target) <= 0: target=self.ListTargetAtoms()
        #if all: target=range(len(self.mol.atm))
        #thick=self.extrabndthick; col=self.hydrogenbndcolor #[0.0,1.0,1.0,1.0] #cyan
        extlst=[]; donedic={}
        for i in target:
            if not self.mol.atm[i].show: continue
            cc0=self.mol.atm[i].cc
            thick=self.mol.atm[1].extrabndthick
            col=self.mol.atm[i].extrabndcolor
            for j in xrange(len(self.mol.atm[i].extraconect)):
                jj=self.mol.atm[i].extraconect[j]
                #if jj <= i: continue
                if CheckDone(donedic,i,jj): continue
                if not self.mol.atm[jj].show: continue
                if within:
                    if not jj in target: continue
                if self.mol.atm[i].extrabnd[j] != 0:
                    cc1=self.mol.atm[jj].cc
                    extlst.append([cc0,cc1,col,thick])
                    ii=min(i,jj); jj=max(i,jj)
                    donedic[str(ii)+':'+str(jj)]=True
        return extlst
    
    def ListAtomSequence(self,exceptter):
        lst=[]
        for atom in self.mol.atm:
            if exceptter and atom.elm == "XX": continue
            lst.append(atom.seqnmb)
        return lst
        
    def ListHydrogenBond(self):
        target=self.ListTargetAtoms()
        thick=self.mol.extrabndthick; col=self.mol.hydrogenbndcolor #[0.0,1.0,1.0,1.0] #cyan
        hbdlst=[]
        for i in target:
            if not self.mol.atm[i].show: continue
            cc0=self.mol.atm[i].cc
            for j in xrange(len(self.mol.atm[i].extraconect)):
                jj=self.mol.atm[i].extraconect[j]
                if jj <= i: continue
                if not self.mol.atm[jj].show: continue
                if self.mol.atm[i].extrabnd[j] == 1:
                    cc1=self.mol.atm[jj].cc
                    hbdlst.append([cc0,cc1,col,thick])
        return hbdlst
    
    def MsgSelectedObj(self,selobj,atm1):
        atom=self.mol.atm[atm1]
        resdat=lib.ResDat(atom)
        nsel,sellst=self.ListSelectedAtom()
        txt=', number of atoms='+str(nsel)
        mess='Selected '
        if selobj == 1:
            #resdat=lib.ResDat(atom)
            mess=mess+'residue='+resdat
        elif selobj == 2:
            mess=mess='side chain of residue='+resdat+txt

        elif selobj == 3:
            mess=mess='chain='+atom.chainnam+txt
        elif selobj == 4:
            mess=mess+'group='+atom.grpnam+txt
        elif selobj == 5:
            mess=mess+'fragment='+atom.frgnam+txt 
        self.Message(mess,0,'')
        
    def MsgAtomDistance(self,atm0,atm1):
        # draw interatomic distance
        # note: alos works as DrawDistance!
        drwlabel='Distance' # for 'ctrlflag'
        if atm0 == atm1: return
        ia=atm0; ib=atm1
        if atm1 < atm0:
            ia=atm1; ib=atm0
        cca=self.mol.atm[ia].cc; ccb=self.mol.atm[ib].cc
        dist=lib.Distance(cca,ccb)
        sdist=('%7.3f' % dist).strip()
        mess1='r='+sdist+', ' #('%5.2f' % dist).strip()
        #mess2='between '+self.MakeAtomLabel(ia,True)+' and '+self.MakeAtomLabel(ib,True)
        [atmdat1,atmdat2]=self.MakeAtmDat([ia,ib],False)
        mess2='between '+atmdat1+' and '+atmdat2
        self.Message(mess1+mess2,0,'black')
        # store atom numbers in distancedic for DrawDispance 
        #distancedic=self.distancedic   
        if self.ctrlflag.Get('Mode(on/off)'):
            if self.ctrlflag.IsDefined(drwlabel):
                distancedic=self.ctrlflag.Get(drwlabel)
                #if len(distancedic) > 0:
                if distancedic.has_key(ia):
                    for j in xrange(len(distancedic[ia])):
                        if distancedic[ia][j] == []:
                            del distancedic[ia][j]; break
                        elif distancedic[ia][j] == ib:
                            del distancedic[ia][j]; break
                        else: distancedic[ia].append(ib)
                else: distancedic[ia]=[ib] 
            else:
                distancedic={}; distancedic[ia]=[]; distancedic[ia].append(ib)
            self.ctrlflag.Set(drwlabel,distancedic)
            drwlst,drwline=self.MakeDrawDistanceData()
            #self.draw.SetDrawDistanceList(label,True,drwlst)
            #label self.draw.SetLabelList(label,True,drwlst)
            self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
            self.draw.SetDrawData(drwlabel,'LINE',drwline)
            self.TextMessage('[Show:Distance] '+mess2,'yellow')
            self.DrawMol(True)
   
    def MakeDrawDistanceData(self):
        drwlst=[]; drwline=[]; line=[]
        #distancedic=self.distancedic
        drwlabel='Distance' # for 'ctrlflag'
        stipple=[2,0xcccc]; thick=0.5
        distancedic=self.ctrlflag.Get(drwlabel)
        for ia in distancedic:
            if not self.mol.atm[ia].show: continue
            for ib in distancedic[ia]:
                if not self.mol.atm[ib].show: continue
                cca=self.mol.atm[ia].cc; ccb=self.mol.atm[ib].cc
                dist=lib.Distance(cca,ccb)
                sdist=('%7.3f' % dist).strip()
                #cc0=self.mol.atm[ia].cc
                #cc1=self.mol.atm[ib].cc
                color=self.setctrl.GetParam('label-color') #self.mol.labelcolor
                pos=0.5*(cca[0]+ccb[0]),0.5*(cca[1]+ccb[1]),0.5*(cca[2]+ccb[2])
                #pos=[pos2]
                drwlst.append([sdist,None,pos,color])
                line.append(cca); line.append(ccb)
        drwline.append([line,color,thick,stipple])
        return drwlst,drwline
    
    def MsgAtomTorsion(self,atm0,atm1,atm2,atm3):
        if atm0 == atm1: return
        if atm0 == atm2: return
        if atm0 == atm3: return
        if atm1 == atm2: return
        if atm1 == atm3: return
        if atm2 == atm3: return
        angle=self.TorsionAngle(atm0,atm1,atm2,atm3)
        angle=180.0*angle/3.14159
        sangl=('%5.2f' % angle).strip()
        mess='torsion angle='+sangl #('%5.2f' % angle).strip()
        lbl0=self.MakeAtomLabel(atm0,True)
        lbl1=self.MakeAtomLabel(atm1,True)
        lbl2=self.MakeAtomLabel(atm2,True)
        lbl3=self.MakeAtomLabel(atm3,True)
        mess=mess+' degrees, ('+lbl0+'), ('+lbl1+'), ('+lbl2+'), ('+lbl3+')'
        self.Message(mess,0,'black')
        
    
    def TorsionAngle(self,atm0,atm1,atm2,atm3,deg=False):
        """ Compute dihedral angle of atm0-atm1-atm2-atm3
        
        :param int atm0,atm1,atm2,atm3: atom seqence numbers
        :param bool deg: True in degrees, False for radians
        :return: angle(float) - torsion angle
        """
        angle=0.0
        x1=self.mol.atm[atm0].cc[0]; y1=self.mol.atm[atm0].cc[1]
        z1=self.mol.atm[atm0].cc[2]
        x2=self.mol.atm[atm1].cc[0]; y2=self.mol.atm[atm1].cc[1]
        z2=self.mol.atm[atm1].cc[2]
        x3=self.mol.atm[atm2].cc[0]; y3=self.mol.atm[atm2].cc[1]
        z3=self.mol.atm[atm2].cc[2]
        x4=self.mol.atm[atm3].cc[0]; y4=self.mol.atm[atm3].cc[1]
        z4=self.mol.atm[atm3].cc[2]
        a1=x2; b1=y2; c1=z2
        x1=x1-a1; y1=y1-b1; z1=z1-c1
        x3=x3-a1; y3=y3-b1; z3=z3-c1
        x4=x4-a1; y4=y4-b1; z4=z4-c1
        a1=y1*z3-y3*z1; b1=x3*z1-x1*z3; c1=x1*y3-x3*y1
        a2=y4*z3-y3*z4; b2=x3*z4-x4*z3; c2=x4*y3-x3*y4
        denom=(numpy.sqrt(a1*a1+b1*b1+c1*c1)*numpy.sqrt(a2*a2+b2*b2+c2*c2))
        if abs(denom) < 0.000001: denom = 0.000001
        ang=(a1*a2+b1*b2+c1*c2)/denom
        if abs(ang) > 1.0: ang=abs(ang)/ang
        angle=numpy.arccos(ang)
        sgn=x1*a2+y1*b2+z1*c2
        if sgn < 0.0: angle=-angle
        #
        if deg: angle *= const.PysCon['todeg']
        #
        return angle
                        
    def MsgAtomAngle(self,atm0,atm1,atm2):
        if atm0 == atm1: return
        if atm0 == atm2: return
        if atm1 == atm2: return
        angle=self.AtomAngle(atm0,atm1,atm2)
        angle=180.0*angle/3.14159
        sangl=('%5.2f' % angle).strip()
        mess='angle='+sangl #('%5.2f' % angle).strip()
        lbl0=self.MakeAtomLabel(atm0,True)
        lbl1=self.MakeAtomLabel(atm1,True)
        lbl2=self.MakeAtomLabel(atm2,True)
        mess=mess+' degrees, ('+lbl0+'), ('+lbl1+'),('+lbl2+')'
        self.Message(mess,0,'black')
        
    def ListChain(self,atmlst=[]):
        """ Retrun chain name and the first atom sequence number
        
        :return: chainlst - [[chain name,sequence number of the first atom],..]
        """
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        chainlst=[]; done={} # [name0,number0],[name1,numbe1],...]
        prv=""; nmb=0
        for i in lst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            chain=atom.chainnam
            if done.has_key(chain): continue
            chainlst.append([chain,i]); done[chain]=True
        #
        return chainlst

    def ListResidue(self,all):
        # all: True for all residues, False for selected only
        if len(self.mol.atm) < 0:
            self.Message('Open file first.',1,'black'); return
        reslst=[] # [[[resnam0,resnmb0],[resnam1,resnmb1],...],[[,],..],...
        tmp=[]; restmp=[]
        try:
            ini=0
            if not all:
                for i in xrange(len(self.mol.atm)):
                    if self.mol.atm[i].select:
                        ini=i; break
            prvcha=self.mol.atm[ini].chainnam
            prvres=self.mol.atm[ini].resnam; prvnmb=self.mol.atm[ini].resnmb
        except: return []
        restmp.append(prvres); restmp.append(prvnmb) #; restmp.append(prvcha) 
        tmp.append(restmp)
        for atom in self.mol.atm:
            elm=atom.elm
            if elm == 'XX': continue
            if not all and not atom.select: continue
            res=atom.resnam; nmb=atom.resnmb; cha=atom.chainnam
            if cha == prvcha:
                if res != prvres or nmb != prvnmb:
                    restmp=[]; restmp.append(res); restmp.append(nmb)#; restmp.append(cha)
                    tmp.append(restmp); prvres=res; prvnmb=nmb
            else:
                reslst.append(tmp)
                restmp=[]; restmp.append(res); restmp.append(nmb)#; restmp.append(cha)
                tmp=[]; tmp.append(restmp); prvcha=cha; prvres=res; prvnmb=nmb
        if len(tmp) > 0: reslst.append(tmp)
        return reslst

    def ListSelectedResidues(self):
        reslst=[]; donedic={}
        for atom in self.mol.atm:
            resdat=lib.ResDat(atom)
            if donedic.has_key(resdat): continue
            if atom.select:
                reslst.append(resdat); donedic[resdat]=True
        return reslst
        
    def ListResidue1(self,all):
        # all: True for all residues, False for selected only
        if len(self.mol.atm) < 0:
            self.Message('Open file first.',1,'black'); return
        reslst=[] # [[[resnam0,resnmb0],[resnam1,resnmb1],...],[[,],..],...
        tmp=[]; restmp=[]
        try:
            ini=0
            if not all:
                for i in xrange(len(self.mol.atm)):
                    if self.mol.atm[i].select:
                        ini=i; break
            prvcha=self.mol.atm[ini].chainnam
            prvres=self.mol.atm[ini].resnam; prvnmb=self.mol.atm[ini].resnmb
        except: return []
        restmp.append(prvres); restmp.append(prvnmb); restmp.append(prvcha) 
        #res=prvres+':'+str(prvnmb)+':'+prvcha
        tmp.append(restmp)
        for atom in self.mol.atm:
            elm=atom.elm
            if elm == 'XX': continue
            if not all and not atom.select: continue
            res=atom.resnam; nmb=atom.resnmb; cha=atom.chainnam
            if cha == prvcha:
                if res != prvres or nmb != prvnmb:
                    restmp=[]; restmp.append(res); restmp.append(nmb)
                    restmp.append(cha)
                    tmp.append(restmp); prvres=res; prvnmb=nmb
            else:
                reslst.append(tmp)
                restmp=[]; restmp.append(res); restmp.append(nmb)
                restmp.append(cha)
                tmp=[]; tmp.append(restmp); prvcha=cha; prvres=res; prvnmb=nmb
        if len(tmp) > 0: reslst.append(tmp)
        return reslst
    
    def ListResidue3(self,reskind):
        """ 
        
        :param str reskind: 'all','aa', 'non-aa', or 'water'
        """
        #lst=self.ListTargetAtoms()
        lst=range(len(self.mol.atm))
        reslst=[]; tmpdic={}
        watlst=['HOH','WAT','H2O']
        #for atom in self.mol.atm:
        for i in lst:
            atom=self.mol.atm[i]
            resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
            #if resnam == '   ': continue
            if reskind == 'aa' and not const.AmiRes3.has_key(resnam): continue
            elif reskind == 'non-aa' and const.AmiRes3.has_key(resnam): 
                continue
            elif reskind == 'water' and not resnam in const.WaterRes: continue 
            resdat=lib.ResDat(atom)
            if tmpdic.has_key(resdat): continue
            tmpdic[resdat]=True
            reslst.append(resdat)
        return reslst

    def ListResidue4(self,resnam):
        """
        
        :param str resnam: resnam, e.g., 'ALA'
        """
        resdatdic={}
        reslst=[]
        if len(resnam) < 0: return []
        for atom in self.mol.atm:
            if resnam == 'HIS':
                if not atom.resnam in const.HisRes: continue
            else: 
                if atom.resnam != resnam: continue
            resdat=lib.ResDat(atom)
            #if not resdatdic.has_key(resdat): resdatdic[resdat]=[]
            if not resdat in reslst: reslst.append(resdat)    
        return reslst
    
    def ListResidue5(self,chainnam,wat=False):
        """ List residues in chain """
        resdatdic={}; resdatlst=[]
        for atom in self.mol.atm:
            if atom.chainnam == chainnam:
                if not wat and atom.resnam in const.WaterRes: continue 
                resdat=lib.ResDat(atom)
                if resdatdic.has_key(resdat): continue 
                resdatdic[resdat]=True
                resdatlst.append(resdat)
        return resdatlst
    
    def ListNonAAResidue(self,wat=False,nameonly=False):
        # wat: True for NOn-AA res, False: not
        nonaareslst=[]
        reslst=self.ListResidue(True)
        if len(reslst) <= 0: return []
        for i in xrange(len(reslst)):
            for res,nmb in reslst[i]:
                if const.AmiRes3.has_key(res): continue
                if wat and (res == "WAT" or res == "HOH"): continue 
                if nameonly: nonaareslst.append(res)
                else: nonaareslst.append([res,nmb])

        return nonaareslst
    
    def ListWater(self,lst=[]):
        """ Return water resdiue list """
        # wat: True for NOn-AA res, False: not
        atmlst=lst
        if len(lst) <= 0: atmlst=self.ListTargetAtoms()
        watlst=[]; donedic={}
        for i in atmlst:
            atom=self.mol.atm[i]
            if atom.resnam in const.WaterRes:
                resdat=lib.ResDat(atom)
                if donedic.has_key(resdat): continue
                watlst.append(resdat); donedic[resdat]=True
        return watlst
    
    def ListAAResidueAtoms(self,lst=[]):
        atmlst=lst
        if len(lst) <= 0: atmlst=self.ListTargetAtoms()
        aaresatm=[]
        for i in atmlst:
            atom=self.mol.atm[i]; res=atom.resnam
            if const.AmiRes3.has_key(res): aaresatm.append(i)
        return aaresatm
    
    def ListWaterAtoms(self,lst=[]):
        atmlst=lst
        if len(lst) <= 0: atmlst=self.ListTargetAtoms()
        watatmlst=[]
        for i in atmlst:
            atom=self.mol.atm[i]
            if atom.resnam in const.WaterRes: 
                 watatmlst.append(atom.seqnmb)
        return watatmlst
                    
    def ListNonAAResidueAtoms(self,wat=False,atmlst=[]):
        # wat: True for NOn-AA res, False: not
        if len(atmlst) <= 0: atmlst=range(len(self.mol.atm))
        lstatm=[]
        for i in atmlst:
            atom=self.mol.atm[i]; res=atom.resnam
            if const.AmiRes3.has_key(res): continue
            if not wat and (res in const.WaterRes): continue 
            lstatm.append(i)
        return lstatm
    
    def ReportMissingAtomsInAAResidue(self):
        nres,missatmlstdic=self.ListMissingAtomsOfAAResidue()
        if nres <= 0:
            mess='No resdiues of missing atoms in '+self.mol.inpfile+'\n'
        else:
            mess='Missing atoms in '+self.mol.inpfile+'\n'
            mess=mess+'resdiue name, missing atom list'
            for res,atmlst in missingatmlstdic.iteritems():
                mess=mess+res+'\n'
                mess=mess+str(atmlst)+'\n'
        self.ConsoleMessage(mess)
            
    def ListMissingAtomsOfAAResidue(self):
        reslst=self.ListResidue(True) # [[chain0,res1,...],[chain1res,..
        nres=0; bkresdic={}
        for i in xrange(len(reslst)): #chain loop
            lst=reslst[i]
            for res,nmb in lst: # res loop
                if not const.AmiRes3.has_key(res): continue
                resatmlst=self.mol.MakeResAtomList(res,nmb,0)
                chain=self.mol.atm[resatmlst[0]].chainnam
                resatm=const.AmiResBnd[res].keys()
                islst=len(resatm)*[False]; misatm=[]
                for j in range(len(resatm)):
                    for k in resatmlst:                    
                        if resatm[j] == self.mol.atm[k].atmnam:
                            islst[j]=True; break
                nmis=0
                for j in range(len(resatm)):
                    if not islst[j]:
                        nmis += 1; misatm.append(resatm[j]) 
                if len(misatm) > 0:
                    res=chain+"_"+res+":"+str(nmb)
                    bkresdic[res]=misatm
                    nres += 1

        return nres,bkresdic

    def ListSSBond(self):
        # list ss bond ini the system
        lst=[]; ssdic={}; nss=0
        for atom in self.mol.atm:
            if atom.elm == " S": lst.append(atom.seqnmb)
        for i in lst:
            atom=self.mol.atm[i]
            for j in atom.conect:
                if self.mol.atm[j].elm == " S":
                    i1=i; i2=j
                    if i1 > i2:
                        i1=j; i2=i
                    ss=str(i1)+":"+str(i2)
                    chain1=self.mol.atm[i1].chainnam
                    res1=self.mol.atm[i1].resnam+":"+str(self.mol.atm[i1].resnmb)
                    atm1=self.mol.atm[i1].atmnam+":"+str(self.mol.atm[i1].atmnmb)
                    chain2=self.mol.atm[i2].chainnam
                    res2=self.mol.atm[i2].resnam+":"+str(self.mol.atm[i2].resnmb)
                    atm2=self.mol.atm[i2].atmnam+":"+str(self.mol.atm[i2].atmnmb)
                    ssdic[ss]=[chain1,res1,atm1,chain2,res2,atm2]
        nss=len(ssdic)
        return nss,ssdic
    
    def ListAtom(self):
        atmlst=[] # [[[atmnam0,atmnmb0],[atmnam1,atmnmb1],....],
        #           [[atmnami,atmnmbi],...],...
        tmp=[]
        if len(self.mol.atm) <= 0: return []
        atom0=self.mol.atm[0]
        prvcha=atom0.chainnam; prvres=atom0.resnam
        prvnmb=atom0.resnmb
        atmnam=atom0.atmnam; atmnmb=atom0.atmnmb
        #atmtmp=[]; atmtmp.append(atmnam); atmtmp.append(atmnmb); tmp.append(atmtmp)
        for atom in self.mol.atm:
            elm=atom.elm
            if elm == 'XX': continue
            res=atom.resnam; nmb=atom.resnmb
            atmnam=atom.atmnam; atmnmb=atom.seqnmb+1
            if res == prvres and nmb == prvnmb:
                atmtmp=[]; atmtmp.append(atmnam); atmtmp.append(atmnmb)
                tmp.append(atmtmp)
            else:
                atmlst.append(tmp)
                atmtmp=[]; atmtmp.append(atmnam); atmtmp.append(atmnmb)
                tmp=[]; tmp.append(atmtmp)
                prvres=res; prvnmb=nmb
        if len(tmp) > 0: atmlst.append(tmp)
        return atmlst

    def ListCationicMetals(self):
        ionlst=[]
        for i in xrange(len(self.mol.atm)):
            elm=self.mol.atm[i].elm
            if elm == '': continue
            if elm == 'XX': continue
            if const.CationChg.has_key(elm): ionlst.append(i)
        return ionlst

    def ListAnionicMetals(self):
        ionlst=[]
        for i in xrange(len(self.mol.atm)):
            elm=self.mol.atm[i].elm
            if elm == '': continue
            if elm == 'XX': continue
            if const.AnionChg.has_key(elm): ionlst.append(i)
        return ionlst
                      
    def ListElement(self):
        elmdic={}; elmlst=[]
        nknd=0
        for atom in self.mol.atm:
            elm=atom.elm
            if elm == '': continue
            if elm == 'XX': continue
            if not elmdic.has_key(elm):
                nknd += 1; elmdic[elm]=nknd
        if len(elmdic) > 0:
            elmlst=elmdic.keys(); elmlst.sort()
        return elmlst
    
    def ListAtomName(self):
        atmdic={}; atmlst=[]
        nknd=0
        for atom in self.mol.atm:
            atm=atom.atmnam
            elm=atom.elm
            if atm == '': continue
            if elm == 'XX': continue
            if not atmdic.has_key(atm):
                nknd += 1; atmdic[atm]=nknd
        if len(atmdic) > 0:
            atmlst=atmdic.keys(); atmlst.sort()
        
        return atmlst

    def ListAtmNam(self):
        atmlst=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            atmnam="'"+atom.atmnam+"'"
            atmlst.append(atmnam)
        return atmlst
    
    def ListAAResidueSequence(self):
        aareslst=[]; donedic={}
         
        
    def ListResidueName(self):
        resdic={}; reslst=[]
        nknd=0
        for atom in self.mol.atm:
            res=atom.resnam
            if res == '': continue
            if not resdic.has_key(res):
                nknd += 1; resdic[res]=nknd
        if len(resdic) > 0:
            reslst=resdic.keys(); reslst.sort()
        return reslst
        
    def ListUniqueResidueAndNumbers(self):
        """ List unique residues and it number in PDB data
        
        :return: resdic --- {resdur name:number,...}
        """
        resdic={}; tmpdic={}
        for atom in self.mol.atm:
            res=atom.resnam; nmb=atom.resnmb; chain=atom.chainnam
            if res == '': continue
            resdat=lib.PackResDat(res,nmb,chain)
            if not tmpdic.has_key(resdat): tmpdic[resdat]=1
        for resdat,dum in tmpdic.iteritems():
            res,nmb,chain=lib.UnpackResDat(resdat)
            if resdic.has_key(res): resdic[res] += 1
            else: resdic[res]=1
        return resdic
        
    def ListChainName(self):
        chadic={}; chalst=[]
        nknd=0
        for atom in self.mol.atm:
            cha=atom.chainnam
            if cha == '': continue
            if not chadic.has_key(cha):
                nknd += 1; chadic[cha]=nknd
        if len(chadic) > 0:
            chalst=chadic.keys(); chalst.sort()
        return chalst
    
    def ListPeptideChainAtoms(self,lst):
        chainlst=[]
        reslst=[]
        for i in lst:
            resnam=self.mol.atm[i].resnam
            if const.AmiRes3.has_key(resnam): reslst.append(i)
        if len(reslst) <= 0:
            self.Message("No peptide chain atoms.",0,"")
            return []
        """
        #
        prvchain=self.mol.atm[reslst[0]].chainnam; tmp=[]
        for i in reslst:
            if self.mol.atm[i].chainnam == prvchain:
                tmp.append(i)
            else:
                chainlst.append(tmp); prvchain=self.mol.atm[i].chainnam
                tmp=[]
        if len(tmp) > 0: chainlst.append(tmp)
        """
        chainlst.append(lst)
        
        return chainlst
       
    def ListGroupName(self):
        grpdic={}; grplst=[]
        nknd=0
        for atom in self.mol.atm:
            grp=atom.grpnam
            if grp == '': continue
            if not grpdic.has_key(grp):
                nknd += 1; grpdic[grp]=nknd
        if len(grpdic) > 0:
            grplst=grpdic.keys(); grplst.sort()
        return grplst

    def ListGroupAtoms(self,grpnam):
        grpatmlst=[]
        for atom in self.mol.atm:
            if atom.grpnam == grpnam: grpatmlst.append(atom.seqnmb)
        return grpatmlst

    def ListResidueAtoms(self):
        # frgatmlst:[[0,1,2,...].[8,9..],...]        
        fi3='%03d'
        resatmlst=[]; resdic={}; reslst=[]
        #
        prvnam=''; nfrg=-1
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            i=atom.seqnmb
            res=atom.resnam+':'+(fi3 % atom.resnmb)+':'+atom.chainnam
            if not resdic.has_key(res):
                resdic[res]=[]
                resdic[res].append(i)
                reslst.append(res)
            else: resdic[res].append(i)
        for res in reslst: resatmlst.append(resdic[res])

        return reslst,resatmlst

    def ListResDatAtmNam(self,resdat):
        # frgatmlst:[[0,1,2,...].[8,9..],...]        
        resatmlst=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            res=lib.ResDat(atom)
            if res == resdat: resatmlst.append(atom.atmnam)
        return resatmlst
                
    def ListResDatAtoms(self,resdat):
        # frgatmlst:[[0,1,2,...].[8,9..],...]        
        atmlst=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            res=lib.ResDat(atom)
            if res == resdat: atmlst.append(atom.seqnmb)
        return atmlst
                
    def SelectResiduesWithMissingAtoms(self,drw=True):
        mess=''
        resdat=self.PDBMissingResidueInfo(['missing atoms'],viewout=False)
        if len(resdat) > 0:
            nsel=0
            for atom in self.mol.atm:
                if not atom.show: continue
                res=lib.ResDat(atom)
                if res in resdat: 
                    atom.select=True; nsel += 1
                else: atom.select=False
            if nsel > 0:
                mess='Number of missing atom residues='+str(len(resdat))
                if drw: self.DrawMol(True)
        else: mess='No residues with missing atoms or no PDB information.'
        if len(mess) > 0: self.ConsoleMessage(mess)
        
    def SelectElmNam(self,elmnam,selflg):
        if elmnam == '': return
        nsel=0
        for atom in self.mol.atm:
            i=atom.seqnmb
            elm=atom.elm
            if elm == elmnam:
                nsel += 1; self.SetSelectedAtom(i,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
            
    def SelectAtmNam(self,atmnam,selflg):
        if atmnam == '': return
        nsel=0
        for atom in self.mol.atm:
            i=atom.seqnmb
            atm=atom.atmnam
            if atm == atmnam:
                nsel += 1; self.SetSelectedAtom(i,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()

    def IsResNamDefined(self):
        ans=False
        for atom in self.mol.atm:
            if len(atom.resnam.strip()) > 0: 
                ans=True; break
        if not ans:
            mess='Residue names are not defined.'
            self.Message(mess,0,'IsResNamDefined')
        return ans
                        
    def SelectResNam(self,resnam,selflg,drw=True):
        #if not self.IsResNamDefined(): return
        nsel=self.SetSelectResNam(resnam,selflg)
        if nsel <= 0:
            mess='no residues, '+resnam
            self.Message(mess,0,'')
        else:
            if selflg:
                mess='number of atoms in selected residue, '
                mess=mess+resnam+'='+str(nsel)
                self.Message(mess,0,'')
            if drw:
                self.DrawMol(True)
                self.UpdateChildView()

    def SelectResNam1(self,resnamlst,selflg):
        #if not self.IsResNamDefined(): return
        if len(resnamlst) <= 0: return
        n=0
        for resnam in resnamlst:
            nsel=self.SetSelectResNam(resnam,selflg)
            n += nsel
        if n <= 0:
            mess='no residues, '+resnam
            self.Message(mess,0,'')
        else:
            if selflg:
                mess='total number of atoms in selected residues='+str(n)
                self.Message(mess,0,'')
            self.DrawMol(True)
            self.UpdateChildView()

    def SetSelectResNam(self,resnam,selflg):
        # all: True for all, False for selected
        if resnam == '': return
        nsel=0
        for atom in self.mol.atm:
            if not atom.show: continue
            i=atom.seqnmb
            res=atom.resnam
            if res == resnam:
                nsel += 1;  self.SetSelectedAtom(i,selflg)
        if selflg:
            mess='number of atoms in selected residue, '+resnam+'='+str(nsel)
            self.Message(mess,0,'')
        return nsel

    def SetSelectResNam1(self,resnam,selflg,all):
        # all: True for all, False for selected
        if resnam == '': return
        if all: target=range(len(self.mol.atm))
        else: target=self.ListTargetAtoms()
        #
        nsel=0
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if not all and not atom.show: continue
            #i=atom.seqnmb
            #res=atom.resnam
            if atom.resnam == resnam:
                nsel += 1;  self.SetSelectedAtom(i,selflg)
        if selflg:
            mess='number of atoms in selected residue, '+resnam+'='+str(nsel)
            self.Message(mess,0,'')
        return nsel
    
    def SetSelectResDat(self,resdatdic,selflg):
        """
        
        :param dic resdatdic: {'resname or resdat:[atoname,...]
        """
        nsel=0
        for atom in self.mol.atm:
            res=atom.resnam
            resdat=lib.ResDat(atom)
            if resdatdic.has_key(res): resres=res
            elif resdatdic.has_key(resdat): resres=resdat
            else: continue
            if atom.atmnam in resdatdic[resres]: 
                    atom.select=selflg; nsel += 1
        return nsel

    def SetSelectResidue(self,resdat,on):
        res,nmb,cha=lib.UnpackResDat(resdat)
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if nmb < 0:
                if atom.resnam == res: 
                    atom.select=on; nsel += 1
            else:
                if atom.resnam == res and atom.resnmb == nmb and \
                                                  atom.chainnam == cha:
                    atom.select=on; nsel += 1

    def SelectResidue(self,resdat,on=True,drw=False,shwonly=True):
        """ Select residues
        
        :param str or lst resdat: resdat(str), resnam:resnmb:chain
        :param bool on: True for select, False for unselect
        :param bol drw: True for redraw, False for do not draw
        :param bool shwonly: True for show atoms only, False for all atoms
        """
        objtype=lib.ObjectType(resdat)
        if objtype == 'str': resdatlst=[resdat]
        elif objtype == 'list': resdatlst=resdat
        else:
            mess='Program error: wrong "resdat" objtype='+str(objtype)
            lib.MessageBoxOK(mess,'Model.SelectResidue')
            return
        nsel=0
        for residue in resdatlst:
            res,nmb,cha=lib.UnpackResDat(residue)
            nsel=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                if shwonly and not atom.show: continue
                sel=False
                if nmb == -1 and cha == '':
                    if atom.resnam == res: sel=True
                elif nmb != -1 and cha == '':
                    if atom.resnam == res and atom.resnmb == nmb: sel=True
                else:
                    if atom.resnam == res and atom.resnmb == nmb and \
                                              atom.chainnam == cha: sel=True
                if sel: atom.select=on; nsel += 1
        #
        if drw and nsel > 0: self.DrawMol(True)

    def SelectSideChainOfResidue(self,resdat,on=True,drw=False,shwonly=True):
        """ Select residue's side chain atoms
        
        :param str or lst resdat: resdat(str), resnam:resnmb:chain
        :param bool on: True for select, False for unselect
        :param bol drw: True for redraw, False for do not draw
        :param bool shwonly: True for show atoms only, False for all atoms
        """
        def SelectSide(seqnmb,on):
            self.mol.atm[seqnmb].select=on
            for i in self.mol.atm[seqnmb].conect:
                if self.mol.atm[i].elm == ' H': self.mol.atm[i].select=on        
        objtype=lib.ObjectType(resdat)
        if objtype == 'str': resdatlst=[resdat]
        elif objtype == 'list': resdatlst=resdat
        else:
            mess='Program error: wrong "resdat" objtype='+str(objtype)
            lib.MessageBoxOK(mess,'Model.SelectResidue')
            return
        nsel=0
        backbone=[' N  ',' CA ',' C  ',' O  ']
        for residue in resdatlst:
            res,nmb,cha=lib.UnpackResDat(residue)
            nsel=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                if atom.elm == ' H': continue
                if shwonly and not atom.show: continue
                #sel=False
                if nmb == -1 and cha == '':
                    if atom.resnam == res:
                        if not atom.atmnam in backbone: 
                            SelectSide(atom.seqnmb,on)
                elif nmb != -1 and cha == '':
                    if atom.resnam == res and atom.resnmb == nmb: 
                        if not atom.atmnam in backbone: 
                            SelectSide(atom.seqnmb,on)
                else:
                    if atom.resnam == res and atom.resnmb == nmb and \
                                              atom.chainnam == cha: 
                        if not atom.atmnam in backbone: 
                            SelectSide(atom.seqnmb,on)
                #if sel: atom.select=on; nsel += 1
        #
        if drw: self.DrawMol(True)

    def ListSelectedResidues(self,shwonly=True):
        """ list selected residues
        
        :param bool shwonly: True for show atoms only, False for all atoms
        :return: selected(lst) - [resdat1,resdat2,...], 
           resdat=chain:resnam:resnmb 
        """
        selected=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if shwonly and not atom.show: continue
            if not atom.select: continue
            resdat=lib.PackResDat(atom.resnam,atom.resnmb,atom.chainnam)
            if resdat in selected: continue
            else: selected.append(resdat)
        uniq=[]
        for resdat in selected:
            if resdat not in uniq: uniq.append(resdat)
            
        return uniq

    def SetSelectChainNam(self,chanam,selflg):
        if chanam == '': return
        nsel=0
        for atom in self.mol.atm:
            i=atom.seqnmb
            cha=atom.chainnam
            if cha == chanam:
                nsel += 1; self.SetSelectedAtom(i,selflg)
        return nsel
    
    def SelectChainNam(self,chanam,selflg):
        if chanam == '': return
        nsel=self.SetSelectChainNam(chanam,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
    
    def SelectGroup(self,grpnam,selflg):
        if grpnam == '': return
        nsel=0
        for atom in self.mol.atm:
            i=atom.seqnmb
            grp=atom.grpnam
            if grp == grpnam:
                nsel += 1; self.SetSelectedAtom(i,selflg)
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()

    def ListActiveAtoms(self):
        if not self.mol.atm: return 0,[]
        nact=0; lst=[]
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.active: lst.append(i)
            #if atom.select > 0: lst.append(i)
        nact=len(lst)
        return nact,lst
    
    def ListInactiveAtoms(self):
        if not self.mol.atm: return 0,[]
        ninact=0; lst=[]
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if not atom.active: lst.append(i)
            #if atom.select > 0: lst.append(i)
        ninact=len(lst)
        return ninact,lst
        
    def ListSelectedAtom(self):
        # count number of selected atoms
        if not self.mol.atm: return 0,[]
        nsel=0; lst=[]
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.select: lst.append(i)
            #if atom.select > 0: lst.append(i)
        nsel=len(lst)
        return nsel,lst
    
    def SetFramentICHARG(self):
        frgchglst=self.ListFragmentCharge()   
        self.mol.SetFragmentAttributeList('ICHARG',frgchglst)    
         
    def SetFragmentAttribute(self,frglst,attrib,value):
        self.mol.SetFragAttribute(frglst,attrib,value)
    
    def RecoverFragmentAttribute(self,attrib,attriblst):
        #self.mol.fragattribdic[attrib]=attriblst
        self.mol.SetFragmentAttributeList(attrib,attriblst)
    
    def DeleteFragmentAttribute(self,attrib):
        self.mol.DelFragAttribute(attrib)
        mess=attrib+' fragment attribute was deleted.'
        self.Message2(mess)
    
    def GetFragmentAttribute(self,attrib):    
        attriblst=[]
        if self.mol.fragattribdic.has_key(attrib): 
        #    attriblst=self.mol.fragattribdic[attrib]    
            attriblst=self.mol.GetFragmentAttributeList(attrib)
        return attriblst
    
    def CountShowAtoms(self):
        if self.mol is None: return 0
        nshw=0
        for atom in self.mol.atm:
            if atom.show: nshw += 1
        return nshw

    def CountEnvSelAtm(self):
        # count number of selected environment atoms
        nenv=0; lst=[]
        for atom in self.mol.atm:
            i=atom.seqnmb
            if atom.elm == 'XX': continue
            if atom.select == 2: lst.append(i)
            nenv=len(lst)
        return nenv,lst
    
    def GetMol(self,nameonly=False):
        if nameonly: return self.mol.name
        else: return self.mol.name,self.mol
    
    def GetClickedAtom(self,pos):
        # return atom number of a clicked atom at pos
        if not self.mol: return -1
        natm=len(self.mol.atm)
        pa=-1
        if natm <= 0: return pa
        if len(pos) <= 0: return pa
        delta=5 # pixcel
        for i in xrange(natm):
            if self.mol.atm[i].elm == 'XX': continue
            if not self.mol.atm[i].show: continue
            x=self.mol.atm[i].cc[0]; y=self.mol.atm[i].cc[1]
            z=self.mol.atm[i].cc[2]
            rx,ry=self.mdlwin.draw.GetRasterPositionOfAtom(x,y,z)
            if abs(rx-pos[0]) < delta and abs(ry-pos[1]) < delta:
                pa=i; break
        if pa >= 0: self.Message('',0,'')
        return pa 

    def SaveSection(self,on):
        # save hided atoms in section mode
        # on(bool): True for section mode on, False for off
        #if on: self.savhide=[]
        if on: self.ctrlflag.Set('savhide',[])
        else:
            #for i in self.savhide: self.mol.atm[i].select=True
            savhide=self.ctrlflag.Get('savhide')
            for i in savhide: self.mol.atm[i].select=True
            #self.ctrlflag.Del('savhide')
                    
    def SaveShwAtm(self,on):
    # value=True for save, False: back to saved
        if on:
            savshwatm=[]
            for atom in self.mol.atm: savshwatm.append(atom.show)
            self.ctrlflag.Set('savshwatm',savshwatm)
        else:
            savshwatm=self.ctrlflag.Get('savshwatm')
            for i in range(len(self.mol.atm)): 
                self.mol.atm[i].show=savshwatm[i]
    
    def SaveRasPosZ(self,on):
        # value(bool): True for save current, False recover to saved
        if on:
            self.draw.SetRasterPosition()
            rasposz=self.draw.GetAtomRasPosZ()
            savrasposz=rasposz[:] #self.draw.rasposz[:]
            self.ctrlflag.Set('savrasposz',savrasposz)
            rasposminz=min(rasposz)
            rasposmaxz=max(rasposz)
            self.ctrlflag.Set('rasposminz',rasposminz)
            self.ctrlflag.Set('rasposmaxz',rasposmaxz)
            tmp=[]
            for i in xrange(len(savrasposz)):
                if not self.mol.atm[i].show: continue
                tmp.append(savrasposz[i])
            if len(tmp) > 0:
                rasposmaxz=max(tmp); rasposminz=min(tmp)
                self.ctrlflag.Set('rasposminz',rasposminz)
                self.ctrlflag.Set('rasposmaxz',rasposmaxz)
            self.ctrlflag.Set('sectionz',rasposminz)
            self.Message('Section mode.',1,'black')
        else:
            self.Message('',1,'black')
            self.Message('',1,'black')
            self.ctrlflag.Del('sectionz')
            self.ctrlflag.Del('rasposminz')
            self.ctrlflag.Del('rasposmaxz')
            self.ctrlflag.Del('savrasposz')
            
    def SetSection(self,on):
        drwlabel='sectionmess'
        self.SaveShwAtm(on) 
        self.SaveRasPosZ(on)
        self.mousectrl.SetSectionMode(on)
        if on: self.TextMessage('[Select:Section]','yellow')
            #self.ModeMessage('section')
        else: 
            self.RemoveDrawMessage(drwlabel)
            #self.RemoveDrawMessage('modemessage')
            self.TextMessage('','')
            self.mousectrl.mdlmod=0
            self.ModeMessage('')
        
    def SetSectionZScale(self,scale):
        # scale: 0.0-1.0
        rasposminz=self.ctrlflag.Get('rasposminz')
        rasposmaxz=self.ctrlflag.Get('rasposmaxz')   
        range=rasposmaxz-rasposminz
        sectionz=rasposminz+range*scale
        self.ctrlflag.Set('sectionz',sectionz)
        self.DrawSection()

    def SetSectionZByMouse(self,rot):
        sectionz=self.ctrlflag.Get('sectionz')
        sectionz -= rot*0.001
        self.ctrlflag.Set('sectionz',sectionz)
        self.DrawSection()
                         
    def DrawSection(self):
        """ Draw section """
        drwlabel='sectionmess'
        if not self.mousectrl.GetSectionMode(): return
        # not completed yet!
        ff6='%6.3f'
        #self.sectionz=self.sectionz-rot*0.0002
        sectionz=self.ctrlflag.Get('sectionz')
        rasposminz=self.ctrlflag.Get('rasposminz')
        rasposmaxz=self.ctrlflag.Get('rasposmaxz')   
        secpos=(sectionz-rasposminz)/(rasposmaxz-rasposminz)
        if sectionz < rasposminz:
            sectionz=rasposminz
            self.ctrlflag.Set('sectionz',sectionz)
            self.Message('Selction reached maximum.',0,'')
            return
        elif sectionz > rasposmaxz:
            sectionz=rasposmaxz
            self.ctrlflag.Set('sectionz',sectionz)
            self.Message('Selction reached maximum.',0,'')
            return
        mess='Selction position: '+(ff6 % secpos) 
        self.Message(mess,0,'')
        # draw message
        drwtext=[]
        ratio=self.draw.ratio
        secz=sectionz*ratio
        minz=rasposminz*ratio
        maxz=rasposmaxz*ratio
        text='section z='+(ff6 % secz)+', minz='+(ff6 % minz)
        text=text+', maxz='+(ff6 % maxz)
        #self.DrawMessage(drwlabel,'Section mode',text,[],[]) # second:font,third:pos, fourth:color(default)
        self.TextMessage('[Select:Section] '+text,'yellow')
        savrasposz=self.ctrlflag.Get('savrasposz')
        nrasz=len(savrasposz)
        if nrasz <= 0: return
        nhid=0
        self.SaveShwAtm(False)
        savhide=[]
        for i in xrange(len(savrasposz)):
            #if i > nrasz-1: break
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if not atom.show: continue
            if savrasposz[i] < sectionz:
                nhid += 1; atom.show=False; savhide.append(i)
        self.ctrlflag.Set('savhide',savhide)

        self.DrawMol(True)

    def SetDeselectAll(self):
        nchg=0
        for atom in self.mol.atm:
            if not atom.show: continue
            i=atom.seqnmb
            nchg += 1; self.SetSelectedAtom(i,0)
        return nchg  

    def SelectBySphere(self,newx,newy,centeratm):
        [w,h]=self.draw.GetCanvasSize()
        newy=h-newy
        nsel=0 
        i0=centeratm
        atom0=self.mol.atm[i0]
        x0=atom0.cc[0]; y0=atom0.cc[1]; z0=atom0.cc[2]
        cx,cy,cz=self.draw.GetRasterPosition(x0,y0,z0)
        rsel=numpy.sqrt((newx-cx)**2+(newy-cy)**2)*self.draw.ratio
        selobj=self.mousectrl.GetSelObj() #Mode()
        try: # fortran code
            cc0=[]; cc1=[]; indx=[]
            for i in xrange(len(self.mol.atm)):
                atom=self.mol.atm[i]
                if atom.elm == 'XX': continue
                if not atom.show: continue
                cc1.append(atom.cc); indx.append(i)
            cc0.append(atom0.cc); rmin=0.0
            cc0=numpy.array(cc0); cc1=numpy.array(cc1)
            natm,iatm=fortlib.find_contact_atoms(cc0,cc1,rmin,rsel)
            if natm <= 0:
                self.ConsoleMessage('No atoms are within select radius='+str(rsel))
                return
            nsel=0
            for i in iatm:
                ii=indx[i]
                atom=self.mol.atm[ii]
                if selobj == 0:
                    nsel += 1; atom.select=True #self.SetSelectAtom0([ii],True)
                elif selobj == 1: # resdiue selection
                    resnam=atom.resnam
                    resnmb=atom.resnmb
                    chain=atom.chainnam
                    ns=self.SetSelectRes(resnam,resnmb,chain,True)
                    nsel += ns
                elif selobj == 2: # peptide chain
                    print 'chain: underconstraction'
                elif selobj == 3: # group
                    print 'group: underconstraction'
                elif selobj == 4: # fragment
                    print 'fragment: underconstraction'     
        except:
            mess='Model(SelectBySphere): Fortran routine is not available!'
            self.ConsoleMessage(mess)
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                if not atom.show: continue
                i=atom.seqnmb
                xi=atom.cc[0]; yi=atom.cc[1]; zi=atom.cc[2]
                dist=numpy.sqrt((xi-x0)**2+(yi-y0)**2+(zi-z0)**2)
                if dist <= rsel:
                    if selobj == 0:
                        nsel += 1; atom.select=True #self.SetSelectAtom0([i],True)
                    elif selobj == 1: # resdiue selection
                        resnam=atom.resnam
                        resnmb=atom.resnmb
                        chain=atom.chainnam
                        ns=self.SetSelectRes(resnam,resnmb,chain,True)
                        nsel += ns
                    elif selobj == 2: # peptide chain
                        print 'chain: underconstraction'
                    elif selobj == 3: # group
                        print 'group: underconstraction'
                    elif selobj == 4: # fragment
                        print 'fragment: underconstraction'      
        nsel=self.CountSelectedAtoms()
        srad='%-6.2f' % rsel; snmb='%-5d' % nsel
        mess='Select radius='+srad+', Number of selected atoms='+snmb
        self.Message(mess,1,'black') 
        self.TextMessage('[Select:Sphere]: '+mess,'yellow')
        self.DrawSelectSphere([x0,y0,z0],rsel,centeratm)

    def DrawSelectCircle(self,center,rsel):# not completed,centeratm):
        """
        Draw circle for sphere selection
        """
        drwlabel='selectcircle'
        ndiv=12
        color=[0.0,1.0,0.0,1.0]; stipple=[2,0xcccc]; thick=1
        srad='%-6.2f' % rsel
        drwdat=[]; drwtext=[] #; color[3]=0.5
        drwdat.append([ndiv,center,rsel,color,thick,stipple])
        #pos=[center[0]+rsel,center[1]+rsel,0.0]; font=None
        drwtext.append(['[Circle select]'+srad,None,center,color])
        #self.draw.SetDrawSelCircleList(True,drwdat,drwtext)
        self.draw.SetMultipleData(drwlabel,[['CIRCLE2D',drwdat],
                                   ['LABEL',drwtext]])
        #self.draw.SetDrawData('CIRCLE','selectcircle',True,drwdat)
        self.ctrlflag.Set(drwlabel,True)
        self.DrawMol(True)

    def RemoveSelectCircle(self):
        drwlabel='selectcircle'  # for 'ctrlflag'
        #self.draw.SetMultipleData(label,[['CIRCLE2D',False,[]],['LABEL',False,[]]])
        self.draw.DelDrawObj(drwlabel) 
        self.ctrlflag.Del(drwlabel)
        self.Message('',0,'')
        self.DrawMol(True)
                                   
    def DrawSelectSphere(self,center,rsel,catm):
        """
        Draw sphere for sphere selection (not used). Altanateve of 'DrawSelectCircle'.
        """
        drwlabel='selectsphere'
        srad='%-6.2f' % rsel; srad.strip()
        drwdat=[] ; drwtext=[]
        nslice=10 #15
        color=self.setctrl.GetParam('sel-sphere-color')
        drwdat.append([center,rsel,color,nslice])
        cc2d=self.draw.GetCoordinateAt('left',10,'top',40)
        messcolor=self.setctrl.GetParam('draw-message-color')
        atmlab=self.MakeAtomLabel(catm,False)
        #mess=22*' '+'rad='+srad+'from '+atmlab
        mess='rad='+srad+'from '+atmlab
        drwtext.append([mess,None,cc2d,messcolor])
        #self.draw.SetMultipleData(drwlabel,[['SPHERE',drwdat],
        #                                 ['LABEL2D',drwtext]])
        self.draw.SetDrawData(drwlabel,'SPHERE',drwdat)
        
        self.ctrlflag.Set(drwlabel,True)
        #xmin,xmax,ymin,ymax,unit=self.draw.GetCoordinateMinMax()
              
        self.DrawMol(True)

    def DrawMessageTest(self,drwlabel,modelabel,mess,pos,color):
        if len(pos) <= 0: pos=[10,40]
        #cc2d=self.draw.GetCoordinateAt('left',pos[0],'top',pos[1])
        if len(color) <= 0: color=self.setctrl.GetParam('draw-message-color')
        drwtext=[]
        mess='['+modelabel+'] '+mess
        drwtext.append([mess,None,'left',pos[0],'top',pos[1],color])
        self.draw.SetDrawData(drwlabel,'MESSAGE',drwtext) #LABEL2D',drwtext)
        self.ctrlflag.Set(drwlabel,True)
        self.DrawMol(True)

    def DrawMessage(self,drwlabel,modelabel,mess,pos,color,drw=True):
        if len(pos) <= 0: pos=[20,60]
        cc2d=self.draw.GetCoordinateAt('left',pos[0],'top',pos[1])
        if len(color) <= 0: color=self.setctrl.GetParam('draw-message-color')
        drwtext=[]
        mess='['+modelabel+'] '+mess
        drwtext.append([mess,None,cc2d,color])
        self.draw.SetDrawData(drwlabel,'LABEL2D',drwtext)
        self.ctrlflag.Set(drwlabel,True)
        if drw: self.DrawMol(True)

    def RemoveDrawMessage(self,drwlabel):
        self.draw.DelDrawObj(drwlabel) 
        self.ctrlflag.Del(drwlabel)
        self.Message('',0,'')
        self.DrawMol(True)
        
    def RemoveAllLabels(self,drw=True):
        # DrawLabel
        labeldic=self.draw.GetLabelDic()
        for label,value in labeldic.iteritems(): labeldic[label]=False
        #
        self.DrawLabelRemoveAll
        self.DrawLabelAtm(False,0,False)
        self.DrawLabelRes(False,0,False)
        self.DrawLabelFrgNam(False,False)
        self.DrawLabelGrpNam(False,False)
        #
        if drw: self.DrawMol(True)
        
    def RemoveSelectSphere(self):
        """
        Remove sphere of sphere selection (not used). Altanateve of 'RemoveSelectCircle'.
        """
        drwlabel='selectsphere' # for 'ctrlflag'
        self.draw.DelDrawObj(drwlabel)
        self.TextMessage('','') # remove 
        self.ctrlflag.Del(drwlabel)
        self.Message('',0,'')
        self.DrawMol(True)

    def RemoveSelectBox(self): #DrawSelectRectangle(self):
        drwlabel='selectbox'
        #self.draw.SetMultipleData(label,[['BOX',False,[]],['LABEL',False,[]]])
        self.draw.DelDrawObj(drwlabel) 
        self.TextMessage('','') # remove                           
        self.ctrlflag.Del(drwlabel)
        self.Message('',0,'') 
        self.DrawMol(True)
               
    def SelectByBox(self,inix,iniy,newx,newy):   
        # test to oick up world coordinates
        #wx,wy,wz=self.mdlwin.draw.GetWorldCoordOfRasPos2(newx,newy)
        #print 'newx,newy,wx,wy,wz',newx,newy,wx,wy,wz
        if len(self.mol.atm) <= 0: return
              
        selmod=self.mousectrl.GetSelMode()
        if selmod != 3: self.SetSelectAll(0)
        #
        [w,h]=self.draw.GetCanvasSize()

        ix=min(inix,newx); iy=min(iniy,newy)
        nx=max(inix,newx); ny=max(iniy,newy)
        
        #print 'ix,iy',ix,iy
        #print 'nx,ny',nx,ny
        #
        nsel=0 #; xras=[]; yras=[]; zras=[]
        #xc=[]; yc=[]; zc=[]; 
        rasminx=sys.float_info.max; rasmaxx=-sys.float_info.max
        rasminy=sys.float_info.max; rasmaxy=-sys.float_info.max
        rasminz=sys.float_info.max; rasmaxz=-sys.float_info.max
                
        selobj=self.mousectrl.GetSelObj()
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if not atom.show: continue
            x=atom.cc[0]; y=atom.cc[1]; z=atom.cc[2]
            rasx,rasy,rasz=self.draw.GetRasterPosition(x,y,z)
            rasy=h-rasy
            if (rasx >= ix and rasx <= nx) and (rasy >= iy and rasy <= ny):
                if selobj == 0:
                    #nsel += 1; self.SetSelectedAtom(i,1)
                    atom.select=True; nsel += 1
                    if rasx < rasminx:
                        rasminx=rasx; minx=i
                    if rasx > rasmaxx:
                        rasmaxx=rasx; maxx=i
                    if rasy < rasminy:
                        rasminy=rasy; miny=i
                    if rasy > rasmaxy:
                        rasmaxy=rasy; maxy=i
                    if rasz < rasminz:
                        rasminz=rasz; minz=i
                    if rasz > rasmaxz:
                        rasmaxz=rasz; maxz=i
                    #print 'rasz',rasz
                    #xras.append(xi); yras.append(yi); zras.append(zi)
                    #xc.append(x); yc.append(y); zc.append(z)
                elif selobj == 1: # resdiue selection
                    resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
                    ns=self.SetSelectRes(resnam,resnmb,chain,True)
                    nsel += ns
                elif selobj == 2: # peptide chain
                    print 'chain: underconstraction'
                elif selobj == 3: # group
                    print 'group: underconstraction'
                elif selobj == 4: # fragment
                    print 'fragment: underconstraction'
        #nsel,lst=self.ListSelectedAtom()
        nsel=self.CountSelectedAtoms()
        if nsel <= 0: return

        rasminy=h-rasminy
        rasmaxy=h-rasmaxy
        #print 'rasminx,rasminy,rasminz',rasminx,rasminy,rasminz
        #print 'rasmzxx,rasmazy,rasmaxz',rasmaxx,rasmaxy,rasmaxz

        x0,y0,z0=self.draw.UnProject(rasminx,rasminy,rasminz)
        x1,y1,z1=self.draw.UnProject(rasmaxx,rasmaxy,rasmaxz)
        z0=rasminz*self.draw.ratio
        z1=rasmaxz*self.draw.ratio
        #print 'x0,y0,z0',x0,y0,z0
        #print 'x1,y1,z1',x1,y1,z1
        
        rangex=abs(x1-x0); rangey=abs(y1-y0)
        sx='%-6.2f' % rangex; sy='%-6.2f' % rangey
        mess='Select rectangle. Area(dx,dy)=('+sx.strip()+','+sy.strip()+')' 
        mess=mess+'. Number of selected atoms='+str(nsel)
        self.Message(mess,1,'black')
        
        self.TextMessage('[Select:Box]: '+mess,'yellow')
        

        #self.DrawSelectBox([xmin,ymin,zmin],[xmax,ymax,zmax])
        #???self.DrawSelectBox([x0,y0,z0],[x1,y1,z1])
        #self.DrawMol(True)

    def DrawSelectBox(self,pnt1,pnt2):       
        """
        Draw box of box selection (not completed). Altanateve of 'DrawSelectSquare'
        
        :param lst pnt1: vertex [x0,y0]
        :param lst pnt2: vertex [x1,y1] facing the first vertex
        """
      
        print 'pnt1,pnt2',pnt1,pnt2
        xmin=pnt1[0]; ymin=pnt1[1]; zmin=pnt1[2]
        xmax=pnt2[0]; ymax=pnt2[1]; zmax=pnt2[2]
        x1=[xmin,ymax,zmax]
        x2=[xmax,ymax,zmax]
        x3=[xmax,ymin,zmax]
        x4=[xmin,ymin,zmax]
        
        x5=[xmin,ymin,zmin]
        x6=[xmax,ymin,zmin]
        x7=[xmax,ymax,zmin]
        x8=[xmin,ymax,zmin]
        #pos,rad,color,nslic
        drwlabel='test'
        drwdat=[]
        drwdat.append([x1,0.4,[1.0,0.0,0.0,1.0],15])
        drwdat.append([x2,0.4,[0.0,1.0,0.0,1.0],15])
        drwdat.append([x3,0.4,[1.0,1.0,0.0,1.0],15])
        drwdat.append([x4,0.4,[0.0,1.0,1.0,1.0],15])

        drwdat.append([x5,0.4,[1.0,0.0,0.0,0.5],15])
        drwdat.append([x6,0.4,[0.0,1.0,0.0,0.5],15])
        drwdat.append([x7,0.4,[1.0,1.0,0.0,0.5],15])
        drwdat.append([x8,0.4,[0.0,1.0,1.0,0.5],15])

        self.draw.SetDrawData(drwlabel,'SPHERE',drwdat)         

        self.DrawMol(True)
        return
    
    
        vertex=[x1[0],x1[1],x1[2]] 
        
        w=x0[0]-x1[0]
        h=x0[1]-x1[1]
        d=x0[2]-x1[2]

        #
        sx='%-6.1f' % w; sy='%-6.1f' % h #; sz='%-6.1f' % rangez
        sx=sx.strip(); sy=sy.strip()
        sbox='dxdy=('+sx+','+sy+')'   
        drwdat=[]; drwtext=[]
        color=self.setctrl.GetParam('sel-box-color')
        drwdat.append([vertex,w,h,d,color])
        textcolor=self.setctrl.GetParam('draw-message-color')
        drwtext.append([sbox,None,x0,color])
        drwlabel='selectbox'
        
        self.draw.SetMultipleData(drwlabel,[['BOX',drwdat],
                                   ['LABEL',drwtext]])
        self.ctrlflag.Set(drwlabel,True)
        
        self.DrawMol(True)
              
    def DrawSelectSquare(self,p0,p1):       
        """
        Draw box of selection
        
        :param lst pnt1: vertex [x0,y0]
        :param lst pnt2: vertex [x1,y1] facing the first vertex
        """
        print 'Draw selectsquare'
        #zmin=rasposminz; zmax=rasposmaxz
        ix=p0[0]; iy=p0[1]
        nx=p1[0]; ny=p1[1]
        rangex=abs((nx-ix))
        rangey=abs((ny-iy))
        #rangez=(zn-zi)*self.draw.ratio; ranegz=abs(rangez)
        sx='%-6.1f' % rangex; sy='%-6.1f' % rangey #; sz='%-6.1f' % rangez
        sx=sx.strip(); sy=sy.strip()
        sbox='dxdy=('+sx+','+sy+')'   
        #
        zmin=0.0 #self.draw.rasposzmin*self.draw.ratio
        zmax=self.draw.rasposzmax*self.draw.ratio
        print 'rasposminz,rasposmaxz',zmin,zmax 
        zmax=self.draw.rasposzmax
        xi=p0[0]; yi=p0[1]; zi=zmax
        xn=p1[0]; yn=p1[1]; zn=zmax
        #zmin=0.0; zmax=0.0
        print 'xi,yi,zi',xi,yi,zi
        print 'xn,yn,zn',xn,yn,zn
        
        nsel,lst=self.ListSelectedAtom()
        pos=self.mol.atm[lst[0]].cc
        
        color=[0.0,1.0,0.0,1.0]; stipple=[2,0xcccc]; thick=1
        drwdat=[]; drwtext=[]
        #drwdat.append([pos,[xn,yn,pos[2]],color,thick,stipple])
        drwdat.append([[xi,yi,zi],[xn,yn,zn],color,thick,stipple])
        textcolor=self.setctrl.GetParam('draw-message-color')
        drwtext.append([sbox,None,[xi,yi,zi],textcolor]) #[xi,yi,zmin],color])
        drwlabel='selectsquare'
        self.draw.SetMultipleData(drwlabel,[['SQUARE2D',True,drwdat],
                                   ['LABEL',True,drwtext]])
        self.ctrlflag.Set(drwlabel,True)
        
        self.DrawMol(True)
        #self.UpdateChildView()
                  
    def FitToScreen(self,center,drw):
        #if not self.ctrlflag.ready: return
        if center: self.draw.CenterMolecular(self.mol)
        self.draw.FitMolecular(self.mol)
        ###eyepos,center,upward,ratio=self.draw.GetViewParams()
        ###self.mol.SetViewPos(eyepos,center,upward,ratio)
        if drw: self.DrawMol(True)

    def FocusSelectedAtoms(self,on,drw=True):
        lst=self.ListSelectedAtom()
        if on:
            self.savviewitems=self.draw.GetViewItems()
            self.SetShowSelectedOnly(True)
            self.FitToScreen(True,False)
            self.SetShowSelectedOnly(False)
        else:
            self.draw.SetViewItems(self.savviewitems)
            try: del self.savviewitems
            except: pass
        if drw: self.DrawMol(True)
    
    def ResetRotate(self):
        # Reset rotation
        self.draw.ResetRotation()
        self.DrawMol(True)
    
    def AlignMoleculeToXYZAxis(self,drw=True):
        """ Align molecule to xyz axis
        

        """
        def CopyCC():
            cc=[]
            for i in range(len(self.mol.atm)): cc.append(self.mol.atm[i].cc[:])
            return cc   
        def SetNewCC(cc):
            for i in range(len(self.mol.atm)):
                self.mol.atm[i].cc=cc[i]
             
        lst=self.mousectrl.pntatmhis.GetSaved()
        lst.reverse()
        npnts=len(lst)
        if npnts <= 0: return
        # centering
        if npnts >= 1:
            p1=lst[0]; dcc=self.mol.atm[p1].cc[:]
            for i in range(len(self.mol.atm)):
                self.mol.atm[i].cc[0] -= dcc[0]
                self.mol.atm[i].cc[1] -= dcc[1]
                self.mol.atm[i].cc[2] -= dcc[2]        
        if npnts >= 2:
            cc=CopyCC()
            p2=lst[1]
            p1cc=numpy.array(self.mol.atm[p1].cc)
            p2cc=numpy.array(self.mol.atm[p2].cc)
            x3=10.0
            if p2cc[2] < 0.0: x3=-10.0
            p3cc=numpy.array([x3,0.0,0.0])
            vec21=p2cc-p1cc
            vec31=p3cc-p1cc
            da=lib.AngleT(vec21,vec31)
            ax=lib.NormalVector(p2cc,p1cc,p3cc)
            u=lib.RotMatAxis(ax,da)        
            p1pos=p1cc[:]
            cc=lib.RotMol(-u,p1pos,cc)
            SetNewCC(cc)
        if npnts >= 3:
            cc=CopyCC()
            p3=lst[2]
            p1cc=numpy.array(self.mol.atm[p1].cc)
            p2cc=numpy.array(self.mol.atm[p2].cc)
            p3cc=numpy.array(self.mol.atm[p3].cc)
            vec21=p2cc-p1cc; vec31=p3cc-p1cc
            r21=lib.Distance(p1cc,p2cc)
            r31=lib.Distance(p1cc,p3cc)
            a=lib.AngleT(vec21,vec31)
            newp1cc=p1cc
            newp2cc=newp1cc+[0.0,0.0,r21]
            newp3cc=newp1cc+[r31*numpy.cos(a),r31*numpy.sin(a),0.0]
            u=lib.RotMatPnts([p1cc,p2cc,p3cc],[newp1cc,newp2cc,newp3cc])        
            p1pos=p1cc[:]
            cc=lib.RotMol(-u,p1pos,cc)
            SetNewCC(cc)
        #   
        if drw: 
            drwlabel='xyz-axis'
            if self.draw.IsDrawObj(drwlabel):
                #self.draw.DelDrawObj(drwlabel) 
                self.DrawXYZAxis(True,False)
            self.DrawMol(True)    
        
    def ChangeCenterOfRotation(self,drw):
        nsel,sellst=self.ListSelectedAtom()
        if nsel != 1:
            mess='select one atom to define center of rotation.'
            self.Message(mess,0,'')
            return
        #center=self.mol.atm[sellst[0]].cc
        #self.draw.SetCenterOfRot(center)
        center=sellst[0]
        self.CenterOfRotation([center])
        #self.draw.FitMolecular()
        ###eyepos,center,upward,ratio=self.draw.GetViewParams()
        ###self.mol.SetViewPos(eyepos,center,upward,ratio)
        # message
        atmdatlst=self.MakeAtmDat([sellst[0]],False)
        mess='changed the center of rotation at '+atmdatlst[0]
        self.Message(mess,0,'')            
        #
        if drw: self.DrawMol(False)

    def CenterOfRotation(self,atmlst):
        if len(atmlst) <= 1: center=self.mol.atm[atmlst[0]].cc
        else:
            cc=[]; mass=[]
            for i in atmlst: 
                mass.append(1.0)
                cc.append(self.mol.atm[i].cc)
            center,eig,vec=lib.CenterOfMassAndPMI(mass,cc)
        self.draw.SetCenterOfRot(center)
        
    def ResetShowAtom(self,on):
        for i in xrange(len(self.mol.atm)):
            self.mol.atm[i].show=on

    def HideSelected(self,on):
        value=on
        if value:
            na=0
            for atom in self.mol.atm:
                if atom.select: # > 0:
                    atom.show=False
                    na += 1
            if na <= 0:
                mess='No select atoms.'; self.Message(mess,0,'black')
                #self.mdlwin.menu.Check('Hide selected',False)
                self.menuctrl.CheckMenu('Hide selected',False)
                return
            self.Message('Hide selected atoms',1,"black")
            nshw=0
            for atom in self.mol.atm:
                if atom.show: nshw += 1
        else:
            for atom in self.mol.atm:
                if atom.select > 0: atom.show=True
            self.shwselonly=0
            self.Message('',1,'')
        self.DrawMol(True)
    
    def HideHydrogen(self,on,drw=True):
        value=on
        nsel,lst=self.ListSelectedAtom()
        if value:
            nh=0
            self.shwhyd=True
            for atom in self.mol.atm:
                if nsel > 0 and not atom.select: continue
                if atom.elm == ' H':
                    atom.show=False; nh += 1
            if nh <= 0:
                #self.mdlwin.menu.Check('Hide hydrogen',True)
                self.menuctrl.CheckMenu('Hide hydrogen',True)
                return
            self.Message('Hide hydrogens',1,"black")
        else:
            for atom in self.mol.atm:
                if nsel > 0 and not atom.select: continue
                if atom.elm == ' H': atom.show=True
            self.Message('',1,'')
        if drw: self.DrawMol(True)
    
    def HideAllAtoms(self,on,drw=True):
        """ Hide all atoms
        
        :param bool on: True for hide, False for unhide
        """
        for atom in self.mol.atm: atom.show=not on
        if drw: self.DrawMol(True)
    
    def HideWater(self,on,drw=True):        
        #self.ResetShowAtom()
        nw=0; value=True
        if on: value=False
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue    
            res=atom.resnam
            if res == 'WAT' or res == 'HOH' or res == 'DOD':
                atom.show=value; nw += 1
        if nw <= 0:
            #self.mdlwin.menu.Check('Hide water',False)
            self.menuctrl.CheckMenu('Hide water',False)
            self.Message('No water molecules',0,'black')
            return
        if on: self.Message('Hide waters',1,"black")
        else: self.Message('',1,'')
        if drw: self.DrawMol(True)
             
    def HideEnvironment(self,on,drw=True):
        value=True
        if on: value=False
        nenv=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.envflag:
                atom.show=value; nenv += 1            
        if nenv <= 0:
            self.Message('No environment atoms',1,'black')
        else:
            if drw: self.DrawMol(True)

    def HidePeptideAtoms(self,on,drw=True):
        lst=self.ListTargetAtoms()
        if on:
            for i in lst:
                atom=self.mol.atm[i]
                if const.AmiRes3.has_key(atom.resnam):
                    atom.show=False        
            if drw: self.DrawMol(True)
        else:
            self.ShowAllAtom()
                                 
    def ShowAllAtom(self):
        self.ResetShowAtom(True)
        self.menuctrl.CheckMenu("Hide selected",False)
        #self.menuctrl.CheckMenu("Hide environment",False)
        self.menuctrl.CheckMenu("Hide hydrogen",False)
        self.menuctrl.CheckMenu("Hide water",False)
        self.menuctrl.CheckMenu("Selected only",False)
        self.menuctrl.CheckMenu("Backbone only",False)
        self.menuctrl.CheckMenu("Selected only",False)
        self.menuctrl.CheckMenu("Side chain only",False)

        self.FitToScreen(False,True)
        if self.ctrlflag.Get('drawbdapoint'): self.DrawBDAPoint(True)
        #else: self.DrawMol(True)
    
    def SetShowAll(self,shwflg):        
        for atom in self.mol.atm: atom.show=shwflg

    def SetStereo(self,on):
        if on:
            eye=self.setctrl.GetParam('stereo-eye') 
            self.ctrlflag.Set('stereo',True)
        else:
            eye=0; self.ctrlflag.Del('stereo')
        self.draw.SetStereoView(eye)
        self.draw.Paint()

    def SetShowAtom(self,shwflg):
        sellst=self.ListTargetAtoms()
        self.SetShowAll(False)
        for i in sellst: self.mol.atm[i].show=shwflg
            
    def SetRotationAxis(self,pnts=[],on=True): #,on):
        # on(bool): True for draw, False for do not draw
        #on=True # becouse arg 'on' was deleted
        # if len(self.mousectrl.GetRotationAxisPnts()): on=False
        #
        if len(pnts) <= 0: nsel,lst=self.ListSelectedAtom()
        else: 
            nsel=len(pnts); lst=pnts
        if on:
            ###nsel,lst=self.ListSelectedAtom()
            if nsel < 2:
                self.mousectrl.RecoverMouseMode()
                self.mousectrl.SetRotationAxisPnts(False,[]) 
                self.DrawAxisArrow(False,[])
                axispnts=self.mousectrl.GetRotationAxisPnts()
                if len(axispnts) <= 0:
                    mess='Select two/three atoms to define rotation axis. Try again.'
                    lib.MessageBoxOK(mess,"")
                    self.mousectrl.RecoverMouseMode0()
                    return
            elif nsel == 2:
                self.mousectrl.musmodsav=self.mousectrl.musmod
                atm1=lst[0]; atm2=lst[1]
                atms=[atm1,atm2]
                pnt1=self.mol.atm[atm1].cc[:]
                pnt2=self.mol.atm[atm2].cc[:]
                pnts=[pnt1[:],pnt2[:]]
                """
                #self.mol.atm[atm1].select=False
                #self.mol.atm[atm2].select=False
                #self.mousectrl.SetRotationAxisPnts(True,[pnt1,pnt2])
                #self.DrawAxisArrow(True,[[pnt1,pnt2]])
                #self.mousectrl.RecoverMouseMode()
                """
                self.DrawAxisArrow(True,[[pnt1,pnt2]])
                #self.mousectrl.RecoverMouseMode()
                #self.mousectrl.musmod=musmodsav
                #self.mousectrl.SetMouseModeSelection(musmodsav)
                #self.mdlwin.mousemode.win.SetMouseModeSelection(musmodsav)
            elif nsel >= 3: # nsel=3
                atms=self.mousectrl.pntatmhis.GetSaved()
                atms=atms[-3:]; atms.reverse()
                if len(atms) >= 3:
                    atm1=atms[0]; atm2=atms[1]; atm3=atms[2]
                    pnt1,pnt2=self.ArrowOfNormalTo3Atoms(atm1,atm2,atm3)
            #
            for i in atms: self.mol.atm[i].select=False    
            self.mousectrl.SetRotationAxisPnts(True,pnts) #[pnt1[:],pnt2[:]])
            self.mousectrl.SetRotationAxisAtoms(atms)
            self.DrawAxisArrow(True,[[pnt1,pnt2]])
            self.mousectrl.RecoverMouseMode0(False)
            #self.mousectrl.SetMouseMode(0)
            #self.mousectrl.SetMouseModeSelection(0)
        else:
            self.draw.RecoverCenterOfRot()
            self.mousectrl.SetRotationAxisPnts(False,[]) 
            self.DrawAxisArrow(False,[])
            self.FitToScreen(True,True)
    
    def ArrowOfNormalTo3Atoms(self,atm1,atm2,atm3):
        """ Return arrow tail and head coordinates
        
        :return: pnt1(lst) - arrow tail coordinates, [x(float),y(float),z(float)]
        :return: pnt2(lst) - arrow head coordinates, [x(float),y(float),z(float)]
        """
        pnt1=numpy.array(self.mol.atm[atm1].cc)
        pnt2=numpy.array(self.mol.atm[atm2].cc)
        pnt3=numpy.array(self.mol.atm[atm3].cc)
        pnts=[pnt1,pnt2,pnt3]
        cntr=pnt2[:]
        ax=lib.NormalVector(pnt1,pnt2,pnt3)
        ax=numpy.array(ax)
        pnt1=pnt2; pnt2=ax+pnt2
        return pnt1,pnt2
                     
    def DrawAxisArrow(self,on,pnts,drw=True):
        # on(bool): True for draw, False for do not draw
        # pnts(lst): [[pnt1(lst),pnt22(lst)],...]
        drwlabel='rot-axis'
        # color=[1.0,1.0,0.0,1.0]; thick=1; head=0.2
        color=self.setctrl.GetParam('rot-axis-arrow-color')
        thick=self.setctrl.GetParam('rot-axis-arrow-thick')
        head=self.setctrl.GetParam('rot-axis-arrow-head')
        if on:
            """
            if len(pnts[0]) == 3:
                pnt1=numpy.array(pnts[0][0])
                pnt2=numpy.array(pnts[0][1])
                pnt3=numpy.array(pnts[0][2])
                cnt=pnt2[:]
                vec=lib.NormalVector(pnt1,pnt2,pnt3)
                pnt1=pnt2; pnt2=vec+pnt2
                pnts=[[pnt1,pnt2]]
            """
            arrowdat=[]
            for lst in pnts:
                pnt1=lst[0]; pnt2=lst[1]
                arrowdat.append([pnt1,pnt2,color,thick,head])
            self.draw.SetDrawData(drwlabel,'ARROW',arrowdat)
        else:
            self.draw.DelDrawObj(drwlabel)
        if drw: self.DrawMol(True)

    def DrawAxis(self,drwlabel,on,pnts,drw=True):
        # on(bool): True for draw, False for do not draw
        # pnts(lst): [pnt1(lst),pnt22(lst)]
        #drwlabel='axis'
        color=[1.0,1.0,0.0]; thick=1; stipple=[2,0xcccc]
        if on:
            axislst=[]; pnt1=pnts[0]; pnt2=pnts[1]
            axislst.append(pnt1); axislst.append(pnt2)
            axislst.append(color)
            axislst.append(thick)
            axislst.append(stipple)
            self.draw.SetDrawData(drwlabel,'AXIS',axislst)
        else:
            self.draw.DelDrawObj(drwlabel) #,'AXIS',[])
        if drw: self.DrawMol(True)

    def DrawCubeData(self,on,property,cubefile,value,interpol,style,rgbpos,rgbneg,opacity):
        """ Draw cube data
        
        :param bool on:
        :param str property: 'MEP','Den'
        :param str cubefile: cube file name
        :param float value: plot value
        :param int inpterpol: interpllation points number
        :param int style: 0 for solid, 1 for mesh
        :param lst rgbpos: color [r,g,b] for positive value
        :param lst rgbneg: color [r,g,b] for negative value
        :param int opacity: opacity 0-1
        """
        label='cobe-data'
        if on:
            if not os.path.exists(cubefile):
                mess='cube file "'+cubefile+'" does not exist.'
                lib.MessageBoxOK(mess,"DrawCubeData")              
                return
            # parameters for draw
            params=[style,rgbpos,rgbneg,opacity]
            # make polygon data
            polyg=self.MakeDrawPolygonData(cubefile,value,interpol)
            # set polyg data to view
            #self.draw.SetDrawPolygonData(True,params,polyg)
            self.draw.SetDrawData(label,'CUBE',[params,polyg])
            # message
            mess='Drawing '+self.prptxt[self.property]+', value='+('%8.3f' % self.value)
            self.Message(mess,0,'')
            self.ConsoleMessage(mess)
        else: 
            self.draw.DelDrawObj(label)
        #
        self.DrawMol(True)

    def MakeDrawPolygonData(self,cubefile,value,interpolate):
        # make plolygon data
        # return polys: [polygon data]
        polys=[]
        if not os.path.exists(cubefile):
            mess='MakeDrawPolygonData: cube file "'+cubefile+'" does not exist.'
            lib.MessageBoxOK(mess,"MakeDrawPolygonData")              
            return []
        try:
            polys=cube.MC.CubePolygons(cubefile,value,intp)
        except:
            mess='MakeDrawPolygonData: Failed to create polygons.'
            self.Message(mess,0,'')
            self.ConsoleMessage(mess)
        return polys
         
    def DrawCircle(self):
        ndiv=12; center=[5.0,5.0,100.0]; thick=4; color=[1.0,0.0,0.0]

        radius=5.0; stipple=[2,0xcccc]
        drwdat=[]
        drwdat.append([ndiv,center,radius,color,thick,stipple])
        drwlabel='circle'
        self.draw.SetDrawCircleList(drwlabel,True,drwdat)
        self.DrawMol(True)
         
    def DrawXYZAxis(self,on,drw=True):
        # on(bool): True for draw axis, False for do not draw
        # drwdat(lst): [[xmin,xmax],[ymin,ymax],[zmin,zmax],xcolor,ycolor,zcolor,thick,
        # xclor,ycolor,zcolor,[stipplef,stipplep]]
        #glLineStipple(GLint factor, GLushort pattern)
        drwlabel='xyz-axis'
        if on:
            drwlst=self.MakeDrawXYZAxisData()
            self.draw.SetDrawData(drwlabel,'XYZAXIS',drwlst)
            self.SetDrawItemsAndCheckMenu(drwlabel,True)
        else:
            self.draw.DelDrawObj(drwlabel) #,'XYZAXIS',[])
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
        if drw: self.DrawMol(True)

    def MakeDrawXYZAxisData(self):
        drwlst=[]
        xmin,xmax,ymin,ymax,zmin,zmax=self.mol.FindMinMaxXYZ()
        cnt=self.draw.GetCenter()
        #x=[-1000,1000.0]; y=[-1000.0,1000.0]; z=[-1000.0,1000.0]
        xmrg=(xmax-xmin)*0.05; ymrg=(ymax-ymin)*0.05; zmrg=(zmax-zmin)*0.05
        x=[xmin-cnt[0]-xmrg,xmax-cnt[0]+xmrg]
        y=[ymin-cnt[1]-ymrg,ymax-cnt[1]+ymrg]
        z=[zmin-cnt[2]-zmrg,zmax-cnt[2]+zmrg]
        xcolor=[1.0,0.0,0.6]; ycolor=[1.0,1.0,0.0]; zcolor=[0.0,1.0,1.0]
        thick=1; stipple=[2,0xcccc]
        drwlst.append(x); drwlst.append(y); drwlst.append(z)
        drwlst.append(['x','y','z']) #; drwlst.append('y'); drwlst.append('z')
        drwlst.append(xcolor); drwlst.append(ycolor); drwlst.append(zcolor)
        drwlst.append(thick)
        drwlst.append(stipple)
        return drwlst
    
    def DrawBDAPoint(self,on):
        #
        drwlabel='BDA points'
        if on:
            drwdat=self.MakeDrawBDAData()
            nbda=len(drwdat)
            if nbda > 0:
                self.draw.SetDrawData(drwlabel,'BDAPOINT',drwdat)
                mess='Number of BDA points='+str(nbda)
                self.Message(mess,0,'')
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
            else:
                mess='No FMO/BDA points.'
                self.Message(mess,1,'black')
                self.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
                self.SetDrawItemsAndCheckMenu(drwlabel,False)   
        else:
            self.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            
        self.DrawMol(True)

    def SetDrawBDAPoint(self,on):
        drwlabel='BDA points'# for 'ctrlflag'
        lst=self.ListTargetAtoms()
        drwdat=[]
        if on:
            self.SetDrawItemsAndCheckMenu(drwlabel,True) #self.shwbda=True
            nbda=0
            drwdat=self.MakeDrawBDAData()
            nbda=len(drwdat)
            #label self.draw.SetDrawBDAPonitData(True,drwdat)
            self.draw.SeDrawData(drwlabel,'BDAPOINT',True,drwdat)
        else:
            #label self.draw.SetDrawBDAPonitData(False,[])
            self.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
            self.SetDrawItemsAndCheckMenu(drwlabel,False)

    def MakeAtomCCForDraw(self,lst):
        if self.mol is None: return []
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        atmcc=[]
        for i in lst:
            if self.mol.atm[i].show: atmcc.append([i,self.mol.atm[i].cc])
        return atmcc
       
    def MakeDrawAtomData(self,lst):
        """ Make draw data for atoms
        
        :param lst lst: target atom list.lst:[i(int),j(int),...] i,j,.. are atom sequence number
        :return: drwlst(lst) - [[i,model,cc,color,radius],..]
        i(int): atom sequence number
        model(int): molecular model. 0:line,1:stick,2:ball-and-stick, 3:CPK
        cc(lst): atomic coordinates, [x(float),y(float),z(float)]
        radius(float): sphere radius(atom radius or vdW radius for model=3)
        """
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        drwlst=[]; sphere=0
        for i in lst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            model=atom.model
            nbnd=0
            if len(atom.conect) > 0:
                for k in atom.conect:
                    try:
                        if self.mol.atm[k].show: nbnd += 1
                    except: pass
            if model == 3 or model == 2 or nbnd == 0:
                if atom.show:
                    col=atom.color
                    #opacity=atom.color[3]
                    #if atom.envflag:
                    #    col=self.setctrl.GetParam('env-atom-color')
                    #    col[3]=opacity
                    if atom.select:
                        col=const.ElmCol['SL']
                    #    col[3]=opacity
                    color=col # color
                    if model == 3: 
                        radius=atom.vdwrad*atom.vdwradsc
                        sphere += 1
                    else: radius=atom.atmrad*atom.atmradsc # radius
                    # non-bonded atom
                    if len(atom.conect) <= 0: radius *= 0.5
                    cc=atom.cc # coordinate
                    drwlst.append([i,model,cc,color,radius])
                    sphere += 1
        #
        if sphere > const.MAXSPHERE:
            if lib.GetPlatform() == 'WINDOWS':
                mess='Too many spheres, max='+str(const.MAXSPHERE)
                mess=mess+'. Unable to draw non-bonded atoms.\n'
                mess=mess+'Try to execute [Menu]"Modeling"-"Add bond"-'
                mess=mess+'"based on bond lengths" or close this molecule.'
                lib.MessageBoxOK(mess,'Model(MakeDrawAtomData)')
                drwlst=[]
        
        return drwlst
    
    def MakeDrawBondData(self,lst):
        """ Make draw data for bonds
        
        :param lst lst: taeget atom list. lst:[i(int),j(int),...] i,j,.. are atom sequence numbers
        :return: drwlst(lst) - [[i,model0,cc0,bndmulti0,cc0b,visible0,color0,thick0,
                                   jx,model1,cc1,bndmulti1,cc1b,visible1,color1,thick1],,,])
        i,j(int):sequence numbers of bonded atoms
        model0,modelj(int): molecular model. 0:line, 1:stick, 2:ball-and-stick, 3: CPK
        cc0,cc1(lst): atom coordinates of i and j, respectively
        bndmulti0,bondmulti1(int): bond multiplicity. 1:single, 2:double,3:triple, 4:aromatic bonds
        cc0b,cc1b(lst): coordinates of connected atoms to i and j, respectively. the data is used to  for drawing multiple bond.
        visible0,visible1(bool): True for draw, False for not draw
        color0,color1(lst): color data [R,G,B,A]
        thick0,thick1(int): bond thickness
        """
        drwlabel='Multiple bond' # for 'ctrlflag'
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        #
        drwlst=[]; donedic={}; sphere=0
        # covalent bonds
        for i in lst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if len(atom.conect) <= 0: continue
            visiblei=False
            if atom.show: visiblei=True
            visible0=visiblei
            model0=atom.model
            if model0 == 3: visible0=False # CPK model
            col=atom.color
            #opacity=atom.color[3]
            #if atom.envflag: 
            #    col=self.setctrl.GetParam('env-atom-color')
            #    col[3]=opacity
            if atom.select: 
                col=const.ElmCol['SL']
            #    col[3]=opacity
            color0=col # color          
            thick0=atom.thick # thickness
            if model0 == 2: thick0=atom.thickbs
            cc0=atom.cc # coordinate
            for j in range(len(atom.conect)):
                jx=atom.conect[j]
                ijmax=max(i,jx); ijmin=min(i,jx)
                ij=str(ijmin)+':'+str(ijmax)
                if donedic.has_key(ij): continue
                donedic[ij]=True
                try: atomjx=self.mol.atm[jx]
                except: 
                    mess='Error in connect data. iatm='+str(i)+', conatm='
                    mess=mess+str(jx)+' . Skiped in MakeDrawBondData.'
                    self.ConsoleMessage(mess)
                    continue
                if len(atomjx.conect) <= 0: continue
                visiblej=False
                if atomjx.show: visiblej=True
                model1=atomjx.model
                if model1 == 3: visiblej=False # CPK model
                if visiblei and visiblej:
                    bndmulti0=1; cc0b=[]
                    if self.ctrlflag.Get(drwlabel): # for multiple bond
                        bndmulti0=atom.bndmulti[j]
                        for k in atom.conect:
                            if k != jx:
                                cc0b=self.mol.atm[k].cc; break
                    seqnmb1=jx
                    visible1=visiblej
                    cc1=atomjx.cc
                    col=atomjx.color
                    #opacity=atomjx.color[3]
                    #if atomjx.envflag: 
                    #    col=self.setctrl.GetParam('env-atom-color')
                    #    col[3]=opacity
                    if atomjx.select: 
                        col=const.ElmCol['SL']
                    #    col[3]=opacity
                    color1=col
                    thick1=atomjx.thick
                    if model1 == 2: thick1=atomjx.thickbs
                    bndmulti1=1; cc1b=[]              
                    if self.ctrlflag.Get(drwlabel): # for multiple bond
                        bndmulti1=bndmulti0
                        if len(atomjx.conect) > 0:
                            for k in atomjx.conect:
                                if k != i:
                                    cc1b=self.mol.atm[k].cc; break
                    drwlst.append([i,model0,cc0,bndmulti0,cc0b,visible0,color0,thick0,
                                   jx,model1,cc1,bndmulti1,cc1b,visible1,color1,thick1])
            if model0 == 2 or model0 == 3: sphere += 1 
        #
        if sphere > const.MAXSPHERE:
            if lib.GetPlatform() == 'WINDOWS':
                mess='Too many spheres, max='+str(const.MAXSPHERE)
                mess=mess+'. Unable to draw non-bonded atoms.\n'
                mess=mess+'Try to execute [Menu]"Modeling"-"Add bond"-'
                mess=mess+'"based on bond lengths" or close this molecule.'
                lib.MessageBoxOK(mess,'Model(MakeDrawBondData)')
                drwlst=[]

        return drwlst

    def MakeDrawTubeData(self,lst):
        # lst(lst): target atom list. if [], all atoms are targetted. 
        chaindata=[]; reslst=[]
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        for i in lst:
            atom=self.mol.atm[i]
            res=atom.resnam
            if not const.AmiRes3.has_key(res): continue
            atm=atom.atmnam
            if atm != ' N  ' and atm != ' CA ' and atm !=' C  ': continue
            reslst.append(i)
        if len(reslst) <= 0: return []
        res=[]; ic=0
        prvchain=self.mol.atm[reslst[0]].chainnam
        #
        color=self.setctrl.GetParam('aa-tube-color') #self.mol.tube_color
        rad=self.setctrl.GetParam('aa-tube-radius') #self.mol.tube_rad
        for i in reslst:
            atom=self.mol.atm[i]
            atm=atom.atmnam
            chain=atom.chainnam
            if chain != prvchain:
                ii=(ic % 7)
                chaindata.append(res); res=[]
                prvchain=chain; ic += 1
            else:
                wt=1.0; cc=atom.cc
                if atm == ' CA ': wt=0.1
                res.append([cc,color,wt,rad])
        if len(res) > 0: chaindata.append(res)
        #
        return chaindata

    def MakeDrawCAlphaData(self,lst,linethick=-1):
        # lst(lst): target atom list. if [], all atoms are targetted. 
        if linethick < 0:
            linethick=self.setctrl.GetParam('calpha-line-thick')
        chaindata=[]; chaindic={}
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        ncalpha=0
        for i in lst:
            atom=self.mol.atm[i]
            res=atom.resnam
            if not const.AmiRes3.has_key(res): continue
            atm=atom.atmnam
            chainnam=atom.chainnam
            if atm != ' CA ': continue
            if not chaindic.has_key(chainnam): chaindic[chainnam]=[]
            chaindic[chainnam].append(i)
            ncalpha += 1
        if ncalpha <= 0: return []
        #
        colordic=self.setctrl.GetParam('aa-chain-color') #{1:color1,2:color2,...}
        ic=-1
        for chain,calst in chaindic.iteritems():
            ic += 1; chainlst=[]
            if ic >= len(colordic): ic=0
            color=colordic[ic]
            if len(calst) <= 1: continue
            for i in range(len(calst)-1):
                ia=calst[i]
                ja=calst[i+1]
                atomi=self.mol.atm[ia]
                atomj=self.mol.atm[ja]
                cci=atomi.cc; ccj=atomj.cc
                chainlst.append(cci) 
                chainlst.append(ccj)
            chaindata.append([chainlst,color,linethick,[]])
        return chaindata
          
    def MakeDrawBDAData(self):   
        #nsel,lst=self.ListSelectedAtom()
        lst=self.ListTargetAtoms()
        nbda=0; drwdat=[]; nslice=3
        for i in lst:
            atom=self.mol.atm[i]
            if not atom.show: continue
            if atom.frgbaa >= 0: 
                tmp=[] #draw.DrawBDAPointData()
                rad=0.2
                posa=numpy.array(atom.cc)
                atomib=self.mol.atm[atom.frgbaa]
                posb=numpy.array(atomib.cc)
                pos=posa+(posb-posa)*0.2 #+[-0.1,-0.1,0.0] # should be half of font size
                #tmp.append('*')
                #tmp..radius=rad
                #tmp.cc=pos
                color=[0.0,1.0,0.0]
                drwdat.append([rad,pos,color,nslice])
                nbda += 1
        return drwdat

    def DrawFormalCharge(self,on):
        # draw formal charges for FMO
        drwlabel='Formal charge'
        self.ctrlflag.Set(drwlabel,False)
        if on:
            nchg,drwdat=self.MakeDrawFormalChargeData()
            if nchg > 0:
                mess='Number of non-zero formal charges='+str(nchg)+'.'
                self.Message(mess,0,'black')
                #label self.draw.SetLabelList(label,True,drwdat)
                self.draw.SetDrawData(drwlabel,'LABEL',drwdat)
                self.SetDrawItemsAndCheckMenu(drwlabel,True)       
                self.ctrlflag.Set(drwlabel,True)
            else:
                mess='No non-zero formal charges.'
                self.Message(mess,1,'black')
                self.SetDrawItemsAndCheckMenu(drwlabel,False)
                self.ctrlflag.Set(drwlabel,False)
        else:
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            #label self.draw.SetLabelList(label,False,[])
            self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
            self.ctrlflag.Set(drwlabel,False)
        self.DrawMol(True)

    def SetDrawItemsAndCheckMenu(self,drwlabel,on):
        if on: self.ctrlflag.Set(drwlabel,True)
        else: self.ctrlflag.Del(drwlabel)
        if self.menuctrl.IsDefined(drwlabel) and self.menuctrl.IsCheckable(drwlabel):
            self.menuctrl.CheckMenu(drwlabel,on)
            
    def MakeDrawFormalChargeData(self):
        lst=self.ListTargetAtoms()
        nchg=0; drwdat=[]
        # drawlabeldata:label=drawlabel[i][0],pos=drawlabel[i][1];;color=drawlabel[i][2]  
        for i in lst:
            if not self.mol.atm[i].show: continue
            chg=self.mol.atm[i].frgchg+self.mol.atm[i].charge
            if abs(chg) < 0.001: continue 
            schg='%5.2f' % chg; schg=schg.strip()
            color=self.mol.atm[i].color
            pos=numpy.array(self.mol.atm[i].cc)
            lab=schg
            drwdat.append([lab,None,pos,color])
            nchg += 1
        return nchg,drwdat
              
    def DrawLabelRemoveAll(self,drw=True,text=False):
        """ rwmove all labels (element,atom,residue labels)
        
        :param bool drw: Treu for do, False do not draw"""
        # get draw labels from draw
        labeldic=self.draw.GetLabelDic()
        namelst=labeldic.keys()
        # clear label drawitems
        self.ctrlflag.DelByNameList(namelst)
        # uncheck menu items and clear draw data in draw
        for nam in namelst:
            #self.mdlwin.menu.Check(nam,False)
            self.menuctrl.CheckMenu(nam,False)
            #label self.draw.SetLabelList(nam,False,[])
            self.draw.DelDrawObj(nam) #,'LABEL',[])
        #
        if text:
            self.TextMessage('','')
        
        drwlabel='BDA points'
        if self.draw.IsDrawLabel(drwlabel):
            self.draw.DelDrawObj(drwlabel) #,'BDAPOINT',[])
            self.menuctrl.CheckMenu("BDA points",False)

        if drw: self.DrawMol(True)
           
    def DrawLabelAtm(self,on,case,drw=True):
        """ 
        Draw atom labels.
        
        :param bool on: True for draw, False for remove
        :param int case: 0:number, 1:name, 2:name+number 
        """
        namelst=['Atom number','Atom name','Atom name+number']
        if case < 0 or case > 3: case=0
        drwlabel=namelst[case]
        self.ctrlflag.Set(drwlabel,False)
        if on:
            # make draw data
            natm,drwlst=self.MakeDrawLabelAtomData(drwlabel)
            if natm > 0:
                # uncheck related menu items
                for name in namelst:
                    self.menuctrl.CheckMenu(name,False)
                    self.draw.DelDrawObj(name)
                # set darw data
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.drawlabelatm=True
                self.drawlabelatmcase=case
                self.ctrlflag.Set(drwlabel,True)
            else: self.menuctrl.CheckMenu(name[case],False)      
        else:
            # remove draw data
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
            self.drawlabelatm=False
        #
        if drw: self.DrawMol(True)
                       
    def DrawLabelElm(self,on,case,atmlst=[],drw=True):
        """
        Draw elemnt labels.
        
        :param bool on: True for draw, False for remove
        :param int case: dummy 
        """
        drwlabel='Element'
        self.ctrlflag.Set(drwlabel,False)
        if on:
            # make draw data
            nelm,drwlst=self.MakeDrawLabelElmData(drwlabel,atmlst)
            if nelm > 0:
                # set draw data
                self.drawlabelelm=True
                self.drawlabelelmcase=case
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.ctrlflag.Set(drwlabel,True)
            else: self.menuctrl.CheckMenu(drwlabel,False)
        else:
            # remove draw data
            self.drawlabelelm=False
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            self.draw.DelDrawObj(drwlabel)
            self.ctrlflag.Del(drwlabel)

        if drw: self.DrawMol(True)
        
    def DrawLabelRes(self,on,case,drw=True):
        """ 
        Draw residue labels.
        
        :param bool on: True for draw, False for remove
        :param int case: 0:name, 1:name+number 
        """
        if not self.IsResNamDefined(): return
        #
        namelst=['Residue name','Residue name+number']
        if case < 0 or case > 1: case=0
        drwlabel=namelst[case]
        lst=self.ListTargetAtoms()
        self.ctrlflag.Set(drwlabel,False)
        if on:
            # make draw data
            nres,drwlst=self.MakeDrawLabelResData(drwlabel)
            if nres > 0:
                # uncheck related menu items
                self.menuctrl.CheckMenu(namelst[0],False)
                self.menuctrl.CheckMenu(namelst[1],False)
                # delete draw data
                self.draw.DelDrawObj(namelst[0])
                self.draw.DelDrawObj(namelst[1])
                # set draw data
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                self.drawlabelres=True
                self.drawlabelrescase=case
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.ctrlflag.Set(drwlabel,True)
            else: self.menuctrl.CheckMenu(namelst[case],False)
        else:
            # remove draw data
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            self.draw.DelDrawObj(drwlabel)
            self.drawlabelres=False      
        if drw: self.DrawMol(True)

    def MakeDrawLabelAtomData(self,drwlabel,atmlst=[]):
        """ 
        Make draw data for 'Atom number','Atom name','Atom name+number'.
        
        :param lst drwlabel: 'Atom number','Atom name', or 'Aton name+number'.
        :return: [[drwlabel,cc,color],...] 
        :rtype: lst
        """
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        natm=0; drwlst=[]
        color=self.setctrl.GetParam('label-color') #'self.mol.labelcolor #[0.0,1.0,0.0]
        for i in lst:
            atom=self.mol.atm[i]
            #if atom.elm == "XX": continue
            if not atom.show: continue
            atm=atom.atmnam
            atm=atm.strip()
            snmb=str(atom.seqnmb+1).strip()
            #tmp=draw.DrawLabelData()
            cc=atom.cc[:]
            cc[0] += 0.1; cc[1] += 0.1; cc[2] += 0.1
            pos=numpy.array(cc) #atom.cc)
            if drwlabel == 'Atom number': lab=snmb
            elif drwlabel == 'Atom name': lab=atm
            elif drwlabel == 'Atom name+number': atm=atm+'_'; lab=atm+snmb
            else: lab=atm
            drwlst.append([lab,None,pos,color])
            natm += 1
        return natm,drwlst
    
    def MakeDrawLabelResData(self,drwlabel):
        # lsbel(str): 'Residue name','Residue name+number'
        lst=self.ListTargetAtoms()
        nres=0; drwlst=[]
        # drawlabeldata:label=drawlabel[i][0],pos=drawlabel[i][1];;color=drawlabel[i][2]  
        donedic={}
        color=self.setctrl.GetParam('label-color') #self.mol.labelcolor #[0.0,0.0,0.0]
        for i in lst:
            atom=self.mol.atm[i]
            res=atom.resnam; nmb=atom.resnmb
            sres=res.strip(); snmb=str(nmb).strip()
            rnam=sres+snmb
            aa=const.AmiRes3.has_key(res)
            if donedic.has_key(rnam): continue
            if aa:
                if not atom.atmnam == ' CA ': continue
            if not atom.show: continue
            #tmp=draw.DrawLabelData()
            posa=numpy.array(atom.cc)
            pos=posa+[0.1,0.2,0.1]
            if drwlabel == 'Residue name': lab=sres
            elif drwlabel == 'Residue name+number': lab=sres+snmb
            #tmp.color=[0.0,1.0,0.0]
            #tmp.append(self.mol.atm[i][2][0])
            drwlst.append([lab,None,pos,color])
            nres += 1; donedic[rnam]=i                  
        return nres,drwlst           

    def MakeDrawLabelElmData(self,drwlabel,atmlst=[]):
        """ drwlabel(str): dummy """
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        nelm=0; drwlst=[]
        color=self.setctrl.GetParam('label-color') #self.mol.labelcolor #[0.0,1.0,0.0]
        for i in lst:
            atom=self.mol.atm[i]
            #tmp=draw.DrawLabelData()
            if not atom.show: continue
            cc=atom.cc[:]
            cc[0] += 0.1; cc[1] += 0.1; cc[2] += 0.1
            posa=numpy.array(cc) #(atom.cc)
            pos=posa #+[0.2,0.2,0.2]
            elm=atom.elm; elm=elm.strip()
            lab=elm
            drwlst.append([lab,None,pos,color])
            nelm += 1
        return nelm,drwlst

    def SetDrawLabelElmData(self,drwlabel,atmlst=[]):
        nelm,drwlst=self.MakeDrawLabelElmData(drwlabel,atmlst=atmlst)
        if nelm > 0:
            # set draw data
            self.drawlabelelm=True
            #self.drawlabelelmcase=case
            self.SetDrawItemsAndCheckMenu(drwlabel,True)
            self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
            self.ctrlflag.Set(drwlabel,True)


    def DrawLabelChain(self,on,drw=True):
        drwlabel='Chain name'
        if on:
            nchain,drwlst=self.MakeDrawLabelChainData(drwlabel)            
            if nchain > 0:
                # set draw data
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.ctrlflag.Set(drwlabel,True)
            else: self.menuctrl.CheckMenu(drwlabel,False)    
        else:
            # remove draw data
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            self.draw.DelDrawObj(drwlabel)
            self.ctrlflag.Del(drwlabel)
        if drw: self.DrawMol(True)
        
    def MakeDrawLabelChainData(self,drwlabel,atmlst=[]):
        """ drwlabel(str): dummy """
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        nchain=0; drwlst=[]
        color=self.setctrl.GetParam('label-color') #self.mol.labelcolor #[0.0,1.0,0.0]
        chainlst=self.ListChain()
        for chain,i in chainlst:       
            cc=self.mol.atm[i].cc[:]
            cc[0] += 0.1; cc[1] += 0.1; cc[2] += 0.1
            pos=numpy.array(cc) #(atom.cc)
            lab=self.mol.atm[i].chainnam
            drwlst.append([lab,None,pos,color]); nchain += 1
        return nchain,drwlst

    def DrawLabelFrgNam(self,on,drw=True):
        drwlabel='Fragment name'
        self.ctrlflag.Set(drwlabel,False)
        if on:
            nfrg,drwlst=self.MakeDrawLabelFrgNamData()
            if nfrg > 0:
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                #label self.draw.SetLabelList(label,True,drwlst)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.ctrlflag.Set(drwlabel,True)
                self.drawlabelfrg=True
            else: return
        else:
            self.drawlabelfrg=False
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            #label self.draw.SetLabelList(label,False,[])
            self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
        
        if drw: self.DrawMol(True)
    
    def DrawLabelGrpNam(self,on,drw=True):
        drwlabel='Group name'
        self.ctrlflag.Set(drwlabel,False)
        if on:
            nfrg,drwlst=self.MakeDrawLabelGrpNamData()
            if ngrp > 0:
                self.SetDrawItemsAndCheckMenu(drwlabel,True)
                #label self.draw.SetLabelList(label,True,drwlst)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)
                self.ctrlflag.Set(drwlabel,True)
                self.drawlabelgrp=True
            else: return
        else:
            self.drawlabelgrp=False
            self.SetDrawItemsAndCheckMenu(drwlabel,False)
            #label self.draw.SetLabelList(label,False,[])
            self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
        
        if drw: self.DrawMol(True)
        
    def MakeDrawLabelGrpNamData(self):
        lst=self.ListTargetAtoms()
        ngrp=0; drwdat=[]
        donedic={}
        color=self.setctrl.GetParam('label-color') #self.mol.labelcolor #[0.0,1.0,0.0]
        for i in lst:
            atom=self.mol.atm[i]
            grp=atom.grpnam
            if grp == '': continue
            if not atom.show: continue
            if donedic.has_key(grp): continue
            donedic[grp]=i
            sgrp=grp.strip(); sgrp=sgrp.lower()
            posa=numpy.array(atom.cc)
            pos=posa+[0.1,-0.2,0.1]
            lab=sgrp
            drwdat.append([lab,None,pos,color])
            ngrp += 1
        return ngrp,drwdat

    def ChangeDrawModel(self,model):
        """ Change molecule model
        
        :param int model: model: LINE = 0, STICK = 1, BALL_STICK = 2, CPK = 3
        
        """
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0: 
            nsel=len(self.mol.atm)
            lst=range(nsel)                     
            #for atom in self.mol.atm: atom.model=model
        # warning on WINDOWS(32bit python)
        maxatmwin=const.MAXSPHERE #50000
        if lib.GetPlatform() == 'WINDOWS' and len(self.mol.atm) > maxatmwin:
           if model == 2 or model == 3:       
                mess='The number of selected atoms exceeds max. sphere number='
                mess=mess+str(maxatmwin)+'.\n'
                mess=mess+'Draw ball-and-stck or CPK model may cause crash'
                mess=mess+' due to the memory shortage.\n'
                mess=mess+'Whould you like to continue?'
                ans=lib.MessageBoxYesNo(mess,'Model(ChangeDrawModel)')
                if not ans: return
        # changer model
        for i in lst: self.mol.atm[i].model=model       
        #
        self.DrawMol(True)
                   
    def ChangeAtomColor(self,case): #,color):
        """
        nchg=0
        if case == 'by element': nchg=self.SetElementColor()
        elif case == 'by residue': nchg=self.SetResidueColor()
        elif case == 'by chain': nchg=self.SetChainColor()
        elif case == 'by fragment': nchg=self.SetFragmentColor()
        elif case == 'by group': nchg=self.SetGroupColor()
        elif case == "on color palette":
            rgbcol=lib.ChooseColorOnPalette(self.mdlwin,False,1.0)
            if len(rgbcol) <= 0: return
            nchg=self.SetChoosenColorToAtoms(rgbcol)
        else: 
            #rgbcol=const.RGBColor255[case]
            #rgbcol=rgbcol+[1.0]
            rgbcol=const.RGBColor[case]
            if len(rgbcol) <= 0: return
            nchg=self.SetChoosenColorToAtoms(rgbcol)
        """
        nchg=self.SetChangeAtomColor(case)
        #
        if nchg > 0: self.DrawMol(True)
    
    def SetChangeAtomColor(self,case): #,color):
        nchg=0
        if case == 'by element': nchg=self.SetElementColor()
        elif case == 'by residue': nchg=self.SetResidueColor()
        elif case == 'by chain': nchg=self.SetChainColor()
        elif case == 'by fragment': nchg=self.SetFragmentColor()
        elif case == 'by group': nchg=self.SetGroupColor()
        elif case == "on color palette":
            rgbcol=lib.ChooseColorOnPalette(self.mdlwin,False,1.0)
            if len(rgbcol) <= 0: return
            nchg=self.SetChoosenColorToAtoms(rgbcol)
        else: 
            #rgbcol=const.RGBColor255[case]
            #rgbcol=rgbcol+[1.0]
            rgbcol=const.RGBColor[case]
            if len(rgbcol) <= 0: return
            nchg=self.SetChoosenColorToAtoms(rgbcol)
        return nchg

    def SetElementColor(self):
        nsel,lst=self.ListSelectedAtom()
        nchg=0
        if nsel <= 0:
            for atom in self.mol.atm:
                if atom.envflag: continue
                elm=atom.elm
                if not const.ElmCol.has_key(elm): col=const.ElmCol['??']
                else: col=const.ElmCol[elm]
                nchg += 1; atom.color=col[:]
        else:
            for i in lst:
                atom=self.mol.atm[i]
                if atom.envflag: continue
                elm=atom.elm
                if not const.ElmCol.has_key(elm): col=const.ElmCol['??']
                else: col=const.ElmCol[elm]
                nchg += 1; atom.color=col[:]; atom.select=0
        return nchg
               
    def SetResidueColor(self):
        prvres=self.mol.atm[0].resnam
        rescolordic=self.setctrl.GetParam('aa-residue-color')
        if rescolordic.has_key(prvres): col=rescolordic[prvres]
        else: col=rescolordic['???']
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.envflag: continue
            res=atom.resnam
            if rescolordic.has_key(res): col=rescolordic[res]
            else: col=rescolordic['???']
            atom.color=col[:]
        return 1

    def SetFragmentColor(self):
        frgdic={}; nf=-1
        for atom in self.mol.atm:
            frgnam=atom.frgnam
            if frgdic.has_key(frgnam): continue
            nf += 1; icol=numpy.mod(nf,7)
            frgdic[frgnam]=icol
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.envflag: continue
            nam=atom.frgnam
            if nam == '': continue
            icol=frgdic[nam]
            col=const.FragmentCol[icol]
            atom.color=col[:]
        mess='Number of fragment='+str(len(frgdic))
        self.Message(mess,0,'')
        
        return 1

    def SetChainColor(self):
        ncha=0; natm=0; prvnam=self.mol.atm[0].chainnam
        col=const.ChainCol[7]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.envflag: continue
            nam=atom.chainnam
            if nam != prvnam:
                icol=(ncha % 7) #numpy.mod(ncha,7)
                col=const.ChainCol[icol]
                prvnam=nam; ncha += 1
            atom.color=col[:]
        return 1

    def SetGroupColor(self):
        ncha=0; natm=0; prvnam=self.mol.atm[0].grpnam
        col=const.ChainCol[7]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            nam=atom.grpnam
            if nam != prvnam:
                icol=(ncha % 7) #numpy.mod(ncha,7)
                col=const.GroupCol[icol]
                prvnam=nam; ncha += 1
            atom.color=col[:]
        return 1

    def SetChoosenColorToAtoms(self,color):
        if len(color) <= 0: return
        nsel,lst=self.ListSelectedAtom()
        nchg=0
        if nsel <= 0:
            for atom in self.mol.atm:
                if atom.envflag: continue
                nchg += 1; atom.color=color[:]
        else:
            for i in lst:
                atom=self.mol.atm[i]
                if atom.envflag: continue
                nchg += 1; atom.color=color[:]       
        return nchg

    def ChangeOpacity(self,opacity):
        # opacity(float): opacity 0.0-1.0
        lst=self.ListTargetAtoms()
        for atom in self.mol.atm: atom.color[3]=1.0
        for i in lst:
            if not self.mol.atm[i].show: continue
            self.mol.atm[i].color[3]=opacity
        self.DrawMol(True)
        #if opacity == 1.0: self.mdlwin.menu.Check('Opacity',False)
        if opacity == 1.0: self.menuctrl.CheckMenu('Opacity',False)
        else: self.menuctrl.CheckMenu('Opacity',True)

    def FogEnable(self,on):
        #if not on: self.draw.updated=True
        fogscale_max=100 # fixed in the 'Control_Frm' class

        self.ctrlflag.Set('Fog',True)
        #self.mdlwin.menu.Check('Fog',on)
        self.menuctrl.CheckMenu('Fog',on)
        #if self.ctrlflag.GetCtrlFlag('controlpanel'):
        #if self.mdlwin.IsWinOpen('ControlWin'): self.ctrlwin.fog=on
        if on:
            scale=20; self.draw.SetFogScale(on,scale)
        else: 
            scale=fogscale_max; self.draw.SetFogScale(on,scale)
        """
        try:
            print 'CtrlWin is opened',self.winctrl.IsOpened('*ControlWin')
            print 'getopend',self.winctrl.GetOpened()
            win=self.winctrl.GetWin('*ControlWin')            
            print 'win in FogEnabel',win
            win.SetFogScale(scale)
        except: pass
        """
        self.DrawMol(True)

    def Echo(self,on):
        self.setctrl.SetParam('echo',on)

    def SetFogScale(self,scale):
        # on(bool): True for fog enable, False for disable
        # scale(int): fog strength. 0-20, scale=20 for fog disable.
        #self.model.SetFogScale(False,self.fogscale_max)
        fogscale_max=100 # fixed in the 'Control_frm' class
        if scale == fogscale_max:
            self.draw.SetFogScale(False,fogscale_max)
            #self.mdlwin.menu.Check("Fog",False)
            self.menuctrl.CheckMenu("Fog",False)
        else:
            self.draw.SetFogScale(True,scale)
            #self.mdlwin.menu.Check("Fog",True)
            self.menuctrl.CheckMenu("Fog",True)
        self.DrawMol(True)

    def ShowOnlyResidues(self,resdatlst):
        """ Show only residues in resdatlst
        
        :param lst resdatlst: resdat(resnam:resnmb:chain) list.
        """
        self.SetShowAll(False)
        for resdat in resdatlst:
            atmlst=self.ListResDatAtoms(resdat)
            for i in atmlst: self.mol.atm[i].show=True
        self.DrawMol(True)
         
    def HideOnlyResidues(self,resdatlst):
        """ Hide only residues in resdatlst
        
        :param lst resdatlst: resdat(resnam:resnmb:chain) list.
        """
        self.SetShowAll(True)
        for resdat in resdatlst:
            atmlst=self.ListResDatAtoms(resdat)
            for i in atmlst: self.mol.atm[i].show=False
        self.DrawMol(True)
    
    def SetShowItems(self,on,items=[]):
        if len(items) <= 0:
            items=["BDA points","Hide hydrogen","Ball and stick",
                   "Hydrogen Bonds"]
            for item in items:
                meth=self.menuctrl.OnShow
                if item == "Hydrogen Bonds": meth=self.menuctrl.OnFMO
                meth(item,on)
             
    def ShowSelectedOnly(self,on):
        if on:
            na,lst=self.ListSelectedAtom()
            if na <= 0:
                self.Message('No selected atoms.',0,'blue')
                #self.mdlwin.menu.Check("Selected only",False)
                self.menuctrl.CheckMenu("Selected only",False)
                return
            self.ResetShowAtom(False)
            for atom in self.mol.atm:
                if atom.select: atom.show=True
            self.shwselonly=1
            #if na < self.maxgetatmpos: self.draw.getatmpos=True
            #self.mdlwin.menu.Check("Selected only",True)
            #self.mdlwin.menu.Check("Backbone only",False)
            #self.mdlwin.menu.Check("Side chain only",False)            
            self.menuctrl.CheckMenu("Selected only",True)
            self.menuctrl.CheckMenu("Backbone only",False)
            self.menuctrl.CheckMenu("Side chain only",False)            
        else:
            self.ResetShowAtom(True)
            self.shwselonly=0
            #if len(self.mol.atm) > self.maxgetatmpos:
            #    self.draw.getatmpos=False
            self.UpdateChildView()

        if self.ctrlflag.Get('drawbdapoint'):
            self.DrawBDAPoint(True)
        else:
            #self.DrawMol(True)
            self.FitToScreen(True,True)

    def SetShowSelectedOnly(self,on):
        if on:
            na,lst=self.ListSelectedAtom()
            if na <= 0:
                self.Message('No selected atoms.',0,'blue')
                #self.mdlwin.fumenuitemdic["Selected only"].Check(False)
                return
            self.ResetShowAtom(False)
            for atom in self.mol.atm:
                if atom.select: atom.show=True
            self.shwselonly=1
            #if na < self.maxgetatmpos: self.draw.getatmpos=True
            
        else:
            self.ResetShowAtom(True)
            self.shwselonly=0
            #if len(self.mol.atm) > self.maxgetatmpos:
            #    self.draw.getatmpos=False
            #self.UpdateChildView()

        #if self.ctrlflag.GetCtrlFlag('drawbdapoint'):
        #    self.DrawBDAPoint(True)
        #else:
        #    pass #self.DrawMol(True)
    
    
    def ShowAASideChainOnly(self,on):
        natm=0
        if on:
            self.ResetShowAtom(True)
            self.menuctrl.CheckMenu("Side chain only",True)
            self.menuctrl.CheckMenu("Backbone only",False)
            self.menuctrl.CheckMenu("Selected only",False)
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                atom.show=1
                atm=atom.atmnam
                natm += 1
                #if atm == ' CA ' or atm == ' N  ' or atm == ' C  ' or atm == ' O  ':
                if atm == ' N  ' or atm == ' C  ' or atm == ' O  ' \
                    or atm == ' HA ' or atm == ' H  ' or atm == ' CA ':           
                    atom.show=False
                    natm -= 1
            if natm > 0: 
                self.Message('Side chain only',1,"black")
                self.DrawMol(True)
        else: 
            self.ResetShowAtom(True); self.DrawMol(True)

    def ShowAABackboneOnly(self,on):
        natm=0
        if on:
            self.ResetShowAtom(True)
            self.menuctrl.CheckMenu("Backbone only",True)
            self.menuctrl.CheckMenu("Selected only",False)
            self.menuctrl.CheckMenu("Side chain only",False)

            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                res=atom.resnam
                if not const.AmiRes3.has_key(res): continue
                atm=atom.atmnam
                if atm == ' N  ':
                    atom.show=True; natm += 1
                elif atm == ' CA ':
                    atom.show=True; natm += 1                
                elif atm == ' C  ':
                    atom.show=True; natm += 1
                else: atom.show=False
        else:
            natm=1
            self.ResetShowAtom(True)
        if natm > 0: self.DrawMol(True)
 
    def DrawChainKite(self,on):
        """ test"""
        drwlabel='Kite'
        self.ctrlflag.Set(drwlabel,False)
        self.menuctrl.CheckMenu("Tube",False)
        if on:
            #tubedat=self.MakeDrawChainTubeData([])
            drwlst=self.MakeDrawKiteData([])
            if len(drwlst) > 0:
                
                self.draw.SetDrawData(drwlabel,'LINE2D',drwlst)
                # testself.draw.SetDrawData('LINE2D',label,True,drwlst)
                
                self.ctrlflag.Set(drwlabel,True)
            else: return
        else:
            self.draw.DelDrawObj(drwlabel) #,'LINE2D',[])
            #
        self.DrawMol(True)

    def MakeDrawKiteData(self,lst):
        # lst(lst): target atom list. if [], all atoms are targetted. 
        chaindata=[]; reslst=[]
        if len(lst) <= 0: lst=range(len(self.mol.atm))
        for i in lst:
            atom=self.mol.atm[i]
            res=atom.resnam
            if not const.AmiRes3.has_key(res): continue
            atm=atom.atmnam
            if atm != ' N  ' and atm != ' CA ' and atm !=' C  ': continue
            reslst.append(i)
        res=[]; ic=0
        prvchain=self.mol.atm[reslst[0]].chainnam
        #
        color=self.mol.tube_color
        rad=self.mol.tube_rad
        
        thick=5; stipple=[2,0xcccc]
        
        for i in reslst:
            
            pnts=[]
            
            
            atom=self.mol.atm[i]
            atm=atom.atmnam
            chain=atom.chainnam
            if chain != prvchain:
                ii=(ic % 7)
                chaindata.append([pnts,color,thick,stipple]); res=[]
                prvchain=chain; ic += 1
                pnts=[]
                if atm == ' CA ': pnts.append(atom.cc)
            else:
                wt=1.0; cc=atom.cc
                if atm == ' CA ': pnts.append(atom.cc)
                
                #res.append([cc,color,wt,rad])
        if len(pnts) > 0: chaindata.append([pnts,color,thick,stipple])
        #
        return chaindata
       
    def DrawChainTube(self,on):
        drwlabel='Tube'
        self.ctrlflag.Set(drwlabel,False)
        self.menuctrl.CheckMenu("CAlpha",False)
        self.menuctrl.CheckMenu("Kite train",False)
        self.menuctrl.CheckMenu("Tube",on)
        if on:
            drwlst=self.MakeDrawTubeData([])
            if len(drwlst) > 0:                
                self.draw.SetDrawData(drwlabel,'TUBE',drwlst)
                self.ctrlflag.Set(drwlabel,True)
            else: return
        else:
            self.draw.DelDrawObj(drwlabel) #,'TUBE',[])
            #
        self.DrawMol(True)
    
    def DrawChainCAlpha(self,on):
        """
        
        :param bool on: True for darw, False for do not
        :param lst color: [r(float),b(float),b(float),opacity(float)]
        """       
        drwlabel='CAlpha'
        self.ctrlflag.Set(drwlabel,False)
        self.menuctrl.CheckMenu("Tube",False)
        self.menuctrl.CheckMenu("Kite train",False)
        self.menuctrl.CheckMenu("CAlpha",on)
        if on:
            drwlst=self.MakeDrawCAlphaData([])
            if len(drwlst) > 0:                
                self.draw.SetDrawData(drwlabel,'LINE',drwlst)
                self.ctrlflag.Set(drwlabel,True)
            else: return
        else:
            self.draw.DelDrawObj(drwlabel) #,'TUBE',[])
            #
        self.DrawMol(True)

    def SetSelectOnebyOne(self,on):
        self.ctrlflag.Set('*OnebyoneSelWin',on)
        self.DrawMol(True)

    def SetSelectedAtom(self,ith,selflg):
        # selflg=0: deselect, =1: select, =2:select environmet
        if self.mol.atm[ith].elm == 'XX': return
        self.mol.atm[ith].select=selflg
    
    def SetSelectGroup(self,grpnam,on):
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.grpnam == grpnam: 
                atom.select=on; nsel += 1
    
    def MakeResGroup(self,resnam):
        """
        
        :param lst resnam: residue name, i.e. 'ALA'
        """
        self.ClearGroups()
        grpnmb=0; tmpdic={}
        for atom in self.mol.atm:
            if atom.resnam == resnam:
                resdat=lib.ResDat(atom)
                if not tmpdic.has_key(resdat): 
                    grpnmb += 1
                    tmpdic[resdat]=True
                atom.grpnam=resdat; atom.grpnmb=grpnmb
        return grpnmb

    def ClearGroups(self):
        for atom in self.mol.atm: 
            atom.grpnam='base'; atom.grpnmb=1
                   
    def SelectGroupByAtom(self,seqnmb):
        try: grpnam=self.mol.atm[seqnmb]
        except: return
        self.SetSelectAll(False)
        self.SetSelectGruoup(grpnam)
        self.DrawMol(True)
        
    def SelectHydrogen(self):
        nh=0
        for i in xrange(len(self.mol.atm)):
            if self.mol.atm[i].elm == 'XX': continue
            if self.mol.atm[i].elm == ' H':
                nh += 1; self.SetSelectedAtom(i,1)
        if nh <= 0: self.Message("No hydorgen atoms.",0,"")
        else:
            self.Message(str(nh)+" hydorgen atoms are selected.",0,"")
            self.DrawMol(True)
            self.UpdateChildView()

    def SelectHydrogens(self,on,drw=False):
        for atom in self.mol.atm:
            if atom.elm == ' H': atom.select=on
        if drw: self.DrawMol(True)
       
    def SelectNonBonded(self,drw=True):
        nn=0
        self.SetSelectAll(False)
        for i in xrange(len(self.mol.atm)):
            if self.mol.atm[i].elm == 'XX': continue
            if len(self.mol.atm[i].conect) == 0:
                nn += 1; self.SetSelectedAtom(i,1)
        if nn <= 0: self.Message("No non-bonded atoms.",0,"")
        else:
            self.Message(str(nn)+" non-bonded atoms are selected.",0,"")
            if drw:
                self.DrawMol(True)
                self.UpdateChildView()
        
    def ListNonBondedAtoms(self,atmlst=[],messout=True):
        if len(atmlst) <= 0: atmlst=self.ListTargetAtoms()
        lst=[]
        for i in atmlst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if len(atom.conect) == 0: lst.append(i)
        if messout:
            if len(lst) <= 0: mess='No non-bonded atoms'
            else:
                mess='Number of non-bonded atoms='+str(len(lst))
            self.Message(mess)
        return lst
        
    def SelectWater(self):
        nwat=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue    
            if not atom.show: continue
            res=atom.resnam
            if res == 'WAT' or res == 'HOH' or res == 'DOD':
                atom.select=True; nwat += 1
        if nwat > 0:
            self.Message(str(nwat)+' water atoms are selected',0,'black')
            self.DrawMol(True)
            self.UpdateChildView()
        else: self.Message('No water molecules',0,'black')

    def SelectMovableAtoms(self,p1,p2,autosel=True,drw=True,messout=True):
        def RecoverBond(p1,p2):
            self.mol.atm[p1].conect.append(p2)
            self.mol.atm[p2].conect.append(p1)
        def MovableGroupNumber(p):
            movgrp=-1
            for i in grplst:
                for j in grplst[i]:
                    if j == p: 
                        movgrp=i; break
                if movgrp >= 0: break
            return movgrp 
        #
        invertp=False
        if p1 < 0 or p2 < 0:
            pntlst=self.mousectrl.GetRotationAxisAtoms()
            if len(pntlst) >= 2:
                p1=pntlst[0]; p2=pntlst[1]
            else: return
        # multiple bond
        try: 
            idx=self.mol.atm[p1].conect.index[p2]
            if self.mol.atm[p1].bndmulti[p2] != 1: return
        except: pass

        self.mdlwin.BusyIndicator('On','Reading ..')

        nmove=-1
        #if autosel: 
        nmove=0
        # split mol at p1-p2
        connected=False
        if p2 in self.mol.atm[p1].conect: 
            self.mol.atm[p1].conect.remove(p2); connected=True
        if p1 in self.mol.atm[p2].conect: 
            self.mol.atm[p2].conect.remove(p1); connected=True
        #
        grplst=self.FindConnectedGroup()
        if len(grplst) <= 1:
            if connected: RecoverBond(p1,p2)
            mess='No movable atoms.'
            lib.MessageBoxOK(mess,'RotateBond_Frm(SelectMovableAtoms)')
            self.mdlwin.BusyIndicator('Off')
            return nmove
        else:
            movgrp1=MovableGroupNumber(p1)
            movgrp2=MovableGroupNumber(p2)
            if autosel:
                if movgrp1 >= 0 and movgrp2 >= 0:
                    movgrp=movgrp2
                    if len(grplst[movgrp2]) > len(grplst[movgrp1]): 
                        movgrp=movgrp1; invertp=True
                elif movgrp1 >= 0 and movgrp2 < 0: 
                    movgrp=movgrp1; invertp=True
                elif movgrp1 < 0 and movgrp2 >= 0: mobgrp=movgrp2
                else: movgrp=-1
            else: movgrp=movgrp2
            if movgrp < 0:
                if connected: RecoverBond(p1,p2)
                mess='Failed to find movable group'
                lib.MessageBoxOK(mess,'RotateBond_Frm(SelectMovableAtoms)')
                self.mdlwin.BusyIndicator('Off')
                return nmove
            self.SetSelectAll(False)
            nsel=0
            for i in grplst[movgrp]:
                self.SetSelectedAtom(i,True)
                nsel += 1
        #
        self.mol.atm[p1].select=False
        self.mol.atm[p2].select=False
        nsel,lst=self.ListSelectedAtom()
        # check are really movable
        err=False
        for i in lst:
            for j in self.mol.atm[i].conect:
                if j == p1 or j== p2: continue

                if not j in lst:
                    err=True; break
        if err:
            self.SetSelectAll(False); lst=[]
        if drw: self.DrawMol(True)
        #try: lst.remove(p1)
        #except: pass
        #try: lst.remove(p2)
        #except: pass
        # recover p1-p2 bond
        if connected: RecoverBond(p1,p2)
        #
        nmove=len(lst)
        #if nmove <= 0:
        #    mess='Please select atoms for move.'
        #    lib.MessageBoxOK(mess,'RotateBond_Frm(SelectMovableAtoms)')
        #else:
        if messout:
            mess='Axis '+str(p1)+'-'+str(p2)+': Number of movable atoms='
            mess=mess+str(nmove)
            self.ConsoleMessage(mess)
        self.mdlwin.BusyIndicator('Off')
        return nmove,invertp
    
    def SelectNonAAResidue(self):
        natm=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            res=atom.resnam
            if res == 'WAT' or res == 'HOH' or res == 'DOD': continue
            if not const.AmiRes3.has_key(res):
                self.SetSelectedAtom(atom.seqnmb,1); natm += 1
        if natm > 0:
            mess=str(natm)+' non-AA residue atoms are selected'
            self.Message(mess,0,'black')
            self.DrawMol(True)
            self.UpdateChildView()
        else:
            self.Message('NO non-AA residue atoms',0,'black')

    def SelectAAResidue(self):
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            res=atom.resnam
            if const.AmiRes3.has_key(res):
                nsel += 1; self.SetSelectedAtom(atom.seqnmb,1)
        if nsel > 0:
            self.Message(str(nsel)+' AA residue atoms are selected',0,'black')
            self.DrawMol(True)
            self.UpdateChildView()
        else:
            self.Message('No AA residue atoms',0,'black')
            
    def SelectAABackbone(self):
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            atom.select=False
            res=atom.resnam
            if const.AmiRes3.has_key(res):
                atm=atom.atmnam
                if atm == ' CA ' or atm == ' N  ' or atm == ' C  ':
                    atom.select=True
                    #self.SetSelectedAtom(atom.seqnmb,1)
                    nsel += 1
        if nsel > 0:
            self.Message(str(nsel)+' backbone atoms are selected',0,'black')
            self.DrawMol(True)
            self.UpdateChildView()
        else:
            self.Message('No backbone atoms',0,'black')
    
    def SelectAASideChain(self):
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue    
            res=atom.resnam
            if not const.AmiRes3.has_key(res): continue
            atom.select=1
            atm=atom.atmnam
            nsel += 1
            #if atm == ' CA ' or atm == ' N  ' or atm == ' C  ' or atm == ' O  ':
            if atm == ' N  ' or atm == ' C  ' or atm == ' O  ' \
                or atm == ' HA ' or atm == ' H  ':           
                atom.select=0
                nsel -= 1
        if nsel > 0: 
            mess='Select Side chain. Number of atoms='+str(nsel)
            self.Message(mess,1,"black")
            
            self.DrawMol(True)
            self.UpdateChildView()
        else: 
            self.Message('No side chain atoms',1,'black')        
        
    def SelectComplement(self,drw=True):
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if not atom.show: continue
            i=atom.seqnmb
            if atom.select == 0: self.SetSelectedAtom(i,1)
            elif atom.select == 1: self.SetSelectedAtom(i,0)
            elif atom.select == 2: self.SetSelectedAtom(i,0)
        if drw: self.DrawMol(True)
        self.UpdateChildView()

    def SetSelectComplement(self):
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if not atom.show: continue
            i=atom.seqnmb
            if atom.select == 0: self.SetSelectedAtom(i,1)
            elif atom.select == 1: self.SetSelectedAtom(i,0)
            elif atom.select == 2: self.SetSelectedAtom(i,0)
        
    def SelectAllShowAtom(self):
        nsel=0
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.show == 1:
                nsel += 1; atom.select=1
        if nsel > 0:
            self.DrawMol(True)
            self.UpdateChildView()
    
    def SelectAll(self,selflg,drw=True):
        #self.SetSelectAll(selflg)
        for atom in self.mol.atm: atom.select=selflg
        if not selflg: 
            self.mousectrl.pntatmhis.Clear()
            self.Message('Deselected all',0,'')
        if drw: self.DrawMol(True)
        self.UpdateChildView()
        
    def SetSelectAll(self,selflg):
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if not atom.show: continue
            atom.select=selflg
            #self.SetSelectedAtom(atom.seqnmb,selflg)
    @staticmethod
    def SetSelectAllAtom(mol,selflg):
        for atom in mol:
            if atom.elm == 'XX': continue
            if not atom.show: continue
            atom.select=selflg

    def DrawFragmentAttribute(self,attrib,value,withlabel,on):
        # attriblst: defined in the 'ctrl.GetFragmentAttributes' method
        #attriblst=['IFREEZ','DOMAIN(FD/FDD)','LAYER','MULT','ICHARG',
        #          'SCFTYP','MPLEVL','DFTTYP','CITYP','CCTYP','TDTYP','SCFFRG','IEXCIT']
        attribcol=[1.0,1.0,0.0,1.0]
        labelcol=self.setctrl.GetParam('label-color')
        drwlabel='Fragment name'
        if attrib == 'IACTAT':
            selatm=[]
            if on:
                self.SaveAtomColor(True)
                self.SetSelectAll(False)
                if value == 'True': stat='Active'
                else: stat='Inactive'
                
                for i in range(len(self.mol.atm)):
                    if value == 'True': 
                        if self.mol.atm[i].active: selatm.append(i)
                    else:
                        if not self.mol.atm[i].active: selatm.append(i)
                if len(selatm) > 0: self.SetSelectAtom0(selatm,True)

                mess='Number of '+stat+' atoms='+str(len(selatm))
                self.Message2(mess)
            else: 
                self.SaveAtomColor(False)
                self.SetSelectAtom0([],False)
                self.SetDrawItemsAndCheckMenu(drwlabel,False)
                #label self.draw.SetLabelList(label,False,[])
                self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
                self.DrawLabelRemoveAll(False)
            if withlabel and len(selatm) > 0: self.DrawLabelAtm(on,0)
            self.DrawMol(True)
        else:
            
            attriblst=self.GetFragmentAttribute(attrib)
            if len(attriblst) <= 0:
                mess='No fragment "'+attrib+'" is set'
                self.Message2(mess)
                self.DrawMol(True)
                return
            frgatmlst,frgnamlst,firstatmlst=   \
                                self.MakeAtomListOfFragAttrib(attriblst,value)
            if len(frgnamlst) <= 0:
                mess='No fragment with "'+attrib+'='+str(value)+'"'
                self.Message2(mess)
                return
            # set from menu
            if on:
                self.SaveAtomColor(True)
                """if attrib == 'LAYER':"""
                # set atom color
                for i in frgatmlst: self.mol.atm[i].color=attribcol
                
                if withlabel:
                    
                    self.SetDrawItemsAndCheckMenu(drwlabel,True)
                    drwlst=[]
                    for i in range(len(frgnamlst)): #attriblst:
                        lab=frgnamlst[i].strip(); lab=lab.lower()
                        firstatm=firstatmlst[i]
                        posa=numpy.array(self.mol.atm[firstatm].cc)
                        pos=posa+[0.1,-0.2,0.1]
                        drwlst.append([lab,None,pos,labelcol]) 
                    self.draw.SetDrawData(drwlabel,'LABEL',drwlst)          
            else: 
                self.SaveAtomColor(False)
                self.SetDrawItemsAndCheckMenu(drwlabel,False)
                #label self.draw.SetLabelList(label,False,[])
                self.draw.DelDrawObj(drwlabel) #,'LABEL',[])
            nfrg=0
            for val in attriblst: 
                if val == value: nfrg += 1
            mess='Number of fragmnets with "'+attrib+'='+str(value)+'": '
            mess=mess+str(nfrg)
            self.Message2(mess)
            
            self.DrawMol(True)

    def RemoveDrawFragmentAttribute(self):
        drwlabel='Fragment name'
        self.SaveAtomColor(False)
        self.SetSelectAll(False)
        self.draw.DelDrawObj(drwlabel)
        self.DrawLabelRemoveAll(False)
        self.SetDrawItemsAndCheckMenu(drwlabel,False)
        self.DrawMol(True)
        
    def MakeAtomListOfFragAttrib(self,attriblst,value):
        frgatmlst=[]; firstatmlst=[]; namlst=[]
        #frgnamlst=self.ListFragmentName()
        frgnamlst=self.GetFragmentAttribute('FRGNAM')
        i=-1
        for val in attriblst:
            i += 1
            if val == value:
                atmlst=self.MakeFrgAtmLst(frgnamlst[i])
                firstatmlst.append(atmlst[0])
                namlst.append(frgnamlst[i])
                for j in atmlst: frgatmlst.append(j)
                
        return frgatmlst,namlst,firstatmlst

    def ListSp3CCBonds(self,lst):
        #!!! Neded treatment of S-S bonds
        sp3cc=[]
        if len(lst) <= 0:
            for i in xrange(len(self.mol.atm)):
                if self.mol.atm[i].elm == "XX": continue
                lst.append(i)
        nbnd=0
        for i in lst:
            atomi=self.mol.atm[i]
            elmi=atomi.elm
            ia=i
            if elmi == ' C':
                if len(atomi.conect) <= 3: continue

                for j in xrange(len(atomi.conect)):
                    ib=atomi.conect[j]
                    if ib >= ia: continue
                    elmj=self.mol.atm[j].elm
                    if elmj == ' C':
                        if len(self.mol.atm[ib].conect) == 4: # sp3
                            nbnd += 1; sp3cc.append([ia,ib])
        #if nbnd > 0:
        #    mess=str(nbnd)+' Sp3 C-C bonds are found'
        #    self.Message(mess,0,'black')

        return sp3cc
    
    def Redraw(self):
        # !!!not working
        #w=self.mdlwin.canvassize[0]; h=self.mdlwin.canvassize[1]
        #self.mdlwin.canvas.glClear()
        self.draw.DispalyList=None
        self.draw.gl_initialized=False
        
        self.mdlwin.busyind=1
        self.mdlwin.BusyIndicator('Off')
        self.DrawMol(True)
     
    # ----- Methods related to Build
    def BuildMol(self,case,filename,addbond=False): #filnam,mol): # #
        # case(str): 'new','pdb','xyz','tin'
        # fiename(str): file name
        mol=molec.Molecule(self) 
        molnam=''
        root,ext=os.path.splitext(filename)
        if case == "new":
            nmol=self.molctrl.GetNumberOfMols()
            nmb='%04d' % (nmol+1)
            molnam="temp"+nmb; mol.parent="None" 
            filename=molnam
        elif case == "pdb": #'.ent' or ext == '.pdb':
            mol.BuildFromPDBFile(filename)
        elif case == 'xyz':
            xyzmol,bond,resfrg=rwfile.ReadXYZMol(filename)
            mol.SetXYZAtoms(xyzmol,bond,resfrg)        
        elif case == 'mol':
            #title,comment,resnam,molatm=rwfile.ReadMolFile(filename)
            moldat=rwfile.ReadMolFile(filename)
            mol.SetMolAtoms(moldat[0][3])
        elif case == 'zmt':
            """ debug """
            self.ConsoleMessage('BuildMol. zmt')

            title,zelm,zpnt,zprm,zvardic,zactivedic=rwfile.ReadZMTFile(filename)
            """ debug """
            self.ConsoleMessage('title='+title)
            
            zmtatm=lib.ZMToCC(zelm,zpnt,zprm)
            mol.SetZMTAtoms(zmtatm,active=zactivedic) #zmtdic=zmtdic)
            mol.zmtpnt=zpnt; mol.zvardic=zvardic; mol.zactivedic=zactivedic
            if addbond: mol.AddBondUseBL([])
        elif case == 'zmtfu':
            title,zelm,zpnt,zprm,zmtdic,extdat=rwfile.ReadZMTFile(filename,
                                                                  type='fu')
            zmtatm=lib.ZMToCC(zelm,zpnt,zprm)
            mol.SetZMTAtoms(zmtatm,active=zactivedic,extdat=extdat)
            mol.zmtpnt=zpnt; mol.zvardic=zvardic; mol.zactivedic=zactivedic
        elif case == 'tin':
            tinmol=rwfile.ReadTinkerXYZ(filename)
            mol.SetTinkerAtoms(tinmol) #,True)
        elif case == 'inp':
            xyzmol,frgnam,indat,bdalst,frgdic=rwfile.ReadFMOInputFile(filename)
            mol.SetFMOAtoms(xyzmol,frgnam,indat,bdalst)
            mol.fragattribdic=frgdic
            if frgdic.has_key('ICHARG'):
                mol.SetFragmentAttributeList('ICHARG',frgdic['ICHARG'])
            if frgdic.has_key('RESNAM') and frgdic.has_key('RESATM'):
                mol.SetResidueName(frgdic['RESATM'],frgdic['RESNAM'])
            if frgdic.has_key('ATMNAM'): mol.SetAtomName(frgdic['ATMNAM'])
            if frgdic.has_key('LAYER'): 
                mol.SetFragmentLayer(frgdic['LAYER'])
                mol.SetFragmentAttributeList('LAYER',frgdic['LAYER'])
            if frgdic.has_key('IACTAT'):
                mol.SetActives(frgdic['IACTAT'])
            mess='Number of fragments='+str(len(frgnam))
            self.ConsoleMessage(mess)
        #   
        mol.name=molec.Molecule.MakeMolNameWithExt(filename)
        mol.inpfile=filename
        # register new mol to MolCtrl
        self.molctrl.Add(mol)
        # clear self.savecc
        self.savatmcc.Clear()
        nmol=self.molctrl.GetNumberOfMols()
        if nmol > 0: self.menuctrl.EnableMenu(True)
        #if nmol > 1:
        #    drwitems=self.draw.GetDrawObjs()
        #    mol.SaveDrawItems(drwitems,False)

    def SwitchProject(self,prjnam):
        print 'curprj, prjnam in SwitchProject',self.curprj,prjnam
        #self.setctrl.SetParam('curprj',prjnam)
        # uncheck menu
        self.menuctrl.UncheckProjectMenuItems()
        if prjnam == self.curprj:
            self.menuctrl.CheckMenu(self.curprj,True)
            return
        #if not initial:
        mess='Are you sure to switch project to "'+prjnam+'"\n'
        #mess=mess+prjnam # commnet
        dlg=lib.MessageBoxYesNo(mess,"")
        if not dlg: 
            self.menuctrl.CheckMenu(self.curprj,True)
            return
        #
        print 'self.curprj,self.curdir',self.curprj,self.curdir
        
        if self.curprj != 'None': self.WriteProjectIniFile()
        
        prvprj=self.curprj
        # close all molecues
        self.SaveCurrentProject()
        print 'before remove mol'
        self.RemoveMol(True)
        #
        # write inifile
        self.curprj=prjnam
        self.WriteIniFile()
        
        ans,shellmess=self.setctrl.ChangeProject(prjnam)
        print 'ans',ans
        print 'shellmess',shellmess
        print 'after changeproject self.curprj,self.curdir',self.curprj, \
                      self.curdir
        if not ans:
            self.ConsoleMessage(mess)
            self.ConsoleMessage('Failed to switch project to "'+prjnam+'"')
            self.curprj=self.setctrl.curprj
            self.menuctrl.CheckMenu(self.curprj,True)
            return
        #        
        self.ConsoleMessage('Switched project: '+prjnam)
        self.curprj=self.setctrl.curprj
        self.curdir=self.setctrl.curdir
        # setting message
        self.ConsoleMessage(shellmess)
        self.ConsoleMessage('End of initial settings for "'+self.curprj+'"')
        # write inifile
        ##self.WriteIniFile()
        self.RestartProject()
        # for save data
        maxundo=self.setctrl.GetParam('max-undo')
        self.savatmcc.SetMaxDepth(maxundo)
        # re-create mdlwin
        self.mdlwin.Destroy()
        self.OpenMdlWin(None,[],[])
        # check menu
        self.mdlwin.SetProjectNameOnTitle(self.curprj)
        self.menuctrl.CheckMenu(prvprj,False)
        self.menuctrl.CheckMenu(self.curprj,True)
        
        ###self.setctrl.InitialProjectSetting(self.curprj) <-- in Setting_Frm.ChangeProject()
        ##self.molctrl.ClearMol()
        ##self.setctrl.LoadProjectMolecules(self.curprj)

    def SaveCurrentProject(self):
        pass
    
    def RestartProject(self):
        pass
    
    def PutBuildingMol(self,pos): # argval=pos
        #if self.mousectrl.GetMdlMode() != 6: return
        winobj=self.winctrl.GetWin('Model builder')
        winobj.PutMol(pos)

    def SwitchMol(self,curmol,fit,drw):
        """ Swictch current molecule to 'curmol'-th molecule
        
        :param int curmol: new current molecular number
        :param obj mol: new current 'Molecule' instance
        :param bool fit: True for fit to screen, False for do not
        :seealso: 'ctrl.MolCtrl.SwitchCurMol' method
        """
        labelatom='atoms'
        labelbond='bonds'
        # save draw items
        if curmol < 0:
            self.curmol=-1
            self.mol=molec.Molecule(self)
            self.ClearScreen()
        else:
            prvmol=self.mol.name
            drwobjs=self.draw.GetDrawObjs()
            #self.mol.SaveDrawItems(drwitems,False)
            self.mol.SetDrawObjs(drwobjs)
            viewitems=self.draw.GetViewItems()
            self.mol.SetViewItems(viewitems)
            
            ###self.draw.SetDrawObjs({})
            #
            self.curmol=curmol
            self.mol=self.molctrl.GetMol(self.curmol)
            mess='SwitchMol: Current molecule is switched from "'+prvmol
            mess=mess+'" to "'+self.mol.name+'".'
            #self.ConsoleMessage(mess)
            if drw: self.Message(mess,0,'')
            #
            self.SetUpDraw(fit)
            
            drwobjs=self.mol.GetDrawObjs()
            viewitems=self.mol.GetViewItems()

            if len(drwobjs) > 0:
                self.RecoverDrawObjs(drwobjs) # this calls DrawMol!!!
            if len(viewitems) > 0:
                self.draw.SetViewItems(viewitems)
            #
            if drw: self.DrawMol(True)
            
            self.NotifyToSubWin('SwitchMol')
            """
            if self.winctrl.IsOpened('ZMatrixViewer'):
                zmtwin=self.winctrl.GetWin('ZMatrixViewer')
                try:
                    wx.PostEvent(zmtwin,subwin.ThreadEvent('ZMatrixViewer',
                                    'SwitchMol',''))
                    self.ConsoleMessage('zmtwin='+str(zmtwin))
                except: 
                    self.ConsoleMessage('Failed PostEvent in SwitchMol')
            """
    
    def NotifyToSubWin(self,myname,destwindic={}):
        destdic=destwindic
        if len(destdic) <= 0:
            destdic=self.winctrl.GetOpenedWin()
        if len(destdic) <= 0: return
        for winlabel,winobj in destdic.iteritems():
            try: wx.PostEvent(winobj,subwin.ThreadEvent(winlabel,myname,''))
            except: pass
            #self.ConsoleMessage('NotifyToSubWin: winlabel='+winlabel)
                        
    def RecoverDrawObjs(self,drwobjdic):
        for drwlabel,lst in drwobjdic.iteritems():
            obj=lst[0]; data=lst[1]
            self.draw.SetDrawData(drwlabel,obj,data)
            self.SetDrawItemsAndCheckMenu(drwlabel,True) 
            
    def CapNCtermsWithHydrogens(self,drw=True):
        
        self.SelectNCofCutAA(drw=False)
        lst=self.ListTargetAtoms()
        
        self.mol.AddHydrogenToPeptideNC(lst)
        self.mol.RenumberAtmNmb()
        
        self.ResetPosAtm()
        if drw: self.DrawMol(True)
    
    def SelectAtomsWithMissingHydrogen(self,atmlst=[],drw=True,view=False):
        """ Not working. Need count hydrogens? """
        sellst=[]; text=''
        misslst,unchecklst=self.ListMissingHydrogenAtoms(atmlst)
        if len(misslst) <= 0: 
            mess='No missing hydrogen atoms'
            self.ConsoleMessage(mess)
            text=text+mess+'\n'
        else:
            mess='Possible missing hydrogen atoms[atnmb,nbond,elm,atmnam, '
            mess=mess+'resdat]'
            self.ConsoleMessage(mess)
            text=text+mess+'\n'
            lst=[]
            for i in misslst:
                atom=self.mol.atm[i]
                resdat=lib.ResDat(atom); nbnd=len(atom.conect)
                lst.append([i+1,nbnd,atom.elm,atom.atmnam,resdat])
            self.ConsoleMessage(str(lst))
            text=text+str(lst)+'\n'
            sellst=misslst
        if len(unchecklst) > 0:
            mess='Unchecked atoms[atnmb,nbond,elm,atmnam, resdat]'
            self.ConsoleMessage(mess)
            text=text+mess+'\n'
            lst=[]
            for i in unchecklst:
                atom=self.mol.atm[i]
                resdat=lib.ResDat(atom); nbnd=len(atom.conect)
                lst.append([i+1,nbnd,atom.elm,atom.atmnam,resdat])
            self.ConsoleMessage(str(lst))
            text=text+str(lst)+'\n'
            sellst=sellst+unchecklst
        #
        if len(sellst) > 0 and drw:
            self.SelectAtomBySeqNmb(sellst,True)
        if len(sellst) > 0 and view:
            text=text+'\n'
            title='Possible missing hydrogen atoms:\n'
            viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,menu=True)
            viewer.SetText(text)
        
    def ListMissingHydrogenAtoms(self,atmlst=[]):
        """ Not working. Need count hydrogens? """
        misslst=[]; unchecklst=[]
        if len(atmlst) <= 0: atmlst=self.ListTargetAtoms()
        for i in xrange(len(atmlst)):
            atom=self.mol.atm[i]
            elm=atom.elm
            if elm == 'XX': continue
            if elm == ' H': continue
            nbnd=len(atom.conect)
            if const.ElmBonds.has_key(elm):
                if not nbnd in const.ElmBonds[elm]: misslst.append(i)
            else: unchecklst.append(i)
        return misslst,unchecklst
        
    def DeleteBondBetweenNC(self):
        self.SetSelectAll(False)
        for atom in self.mol.atm:
            if not const.AmiRes3.has_key(atom.resnam): continue
            nb=len(atom.conect)
            atm=atom.atmnam
            # find NH2-CHO
            nhd=2
            if atom.resnam == 'PRO': nhd=1
            if atm == ' N  ':
                nh=self.mol.CountHydrogenOfAtom(atom.seqnmb)
                if nh == nhd: # NH2 is found
                    for j in atom.conect:
                        atomj=self.mol.atm[j]
                        if atomj.atmnam == ' C  ':
                            nhc=self.mol.CountHydrogenOfAtom(atomj.seqnmb)                          
                            if nhc == 1: # CHO is found
                                self.mol.DelBond(atom.seqnmb,atomj.seqnmb)
                                break
        
    def MakeVdwContact(self):
        target=self.ListTargetAtoms()
        #self.mol.MakeVdwBond(target)
        try:
            nvdw=self.mol.MakeVdwBond(target,False,False,True) # 1,3pos,1,4pos,1,5pos
            self.Message2("Number of vdW contacts found ="+str(nvdw))
        except:
            mess="Error in fortran module. Check source in src/f77/fortlib.f!"
            lib.MessageBoxOK(mess,"")
            return
        # Show the bonds
        if nvdw > 0: 
            #self.mdlwin.menu.Check('Hydrogen/vdW bond',True)
            self.menuctrl.CheckMenu('Hydrogen Bonds',True)
            self.DrawVdwBond(True) #
    
    def MakeHydrogenBond(self,drw=True):
        #target=self.ListTargetAtoms()      
        #self.Message2("Number of hydrogen bonds found ="+str(5))
        target=range(len(self.mol.atm))
        try:
            nbnd,hbnddic=self.mol.MakeHydrogenBond(target)
            self.Message2("Number of hydrogen bonds found="+str(nbnd))
        except:
            mess="Error in fortran module. Check source in src/f77/fortlib.f!"
            lib.MessageBoxOK(mess,"")
            return
        #self.DrawMol(True)
        if drw and nbnd > 0:
            #self.mdlwin.menu.Check('Hydrogen/vdW bond',True)
            self.menuctrl.CheckMenu('Hydrogen Bonds',True)
            self.DrawHBOrVdwBond(True)

    def ListSaltBridge(self):
        sbreslst=[]
        sbatmlst=self.FindSaltBridge()
        if len(sbatmlst) > 0:
            for i,j in sbatmlst:
                atomi=self.mol.atm[i]; atomj=self.mol.atm[j]
                resnami=atomi.resnam; resnmbi=atomi.resnmb
                chaini=atomi.chainnam
                resnamj=atomj.resnam; resnmbj=atomj.resnmb
                chainj=atomj.chainnam
                resdati=lib.PackResDat(resnami,resnmbi,chaini)
                resdatj=lib.PackResDat(resnamj,resnmbj,chainj)
                sbreslst.append([resdati,resdatj])
        lst=[]
        if len(sbreslst) <= 0:
            mess='no salt-bridges found'
            self.ConsoleMessage(mess)
        else:
            mess='number of salt-bridge='+str(len(sbreslst))+'\n'
            mess=mess+'list of salt-bridged residue pair\n'
            for resi,resj in sbreslst:
                mess=mess+resi+','+resj+'\n'
                lst=lst+[resi,resj]         
            self.ConsoleMessage(mess[:-1])
            """list of salt-bridged residue pairs"""
            print lst
           
    def MakeSaltBridge(self):
        sbatmlst=self.FindSaltBridge()
        if len(sbatmlst):
            for i,j in sbatmlst:
                self.mol.atm[i].extraconect.append(j)
                self.mol[i].extrabnd.append(3) # hydrogenbond code
                self.mol[j].extraconect.append(i)
                self.mol[j].extrabnd.append(3) # hydrogen bond code                    
        
    def DrawSaltBridge(self,shwflg):
        #
        target=self.ListTargetAtoms()
        self.mol.DelExtraBond(target)
        #        
        sbatmlst=self.MakeSaltBridge()
        if len(sbatmlst) <= 0:
            self.Message('no salt brides found.')
            return
        #self.mdlwin.menu.Check('Hydrogen/vdW bond',True)
        self.menuctrl.CheckMenu('Hydrogen Bonds',True)
        self.DrawHBOrVdwBond(True)
    
    def FindFirstAtomInSelected(self):
        first=0
        for atom in self.mol.atm:
            if atom.select:
                first=atom.seqnmb
                break 
        return first
            
    def FindSaltBridge(self):
        sbatmlst=[]
        target=self.ListTargetAtoms()
        try:
            nbnd,hbnddic=self.mol.MakeHydrogenBond(target)
        except:
            mess="Error in fortran module. Check source in src/f77/fortlib.f!"
            lib.MessageBoxOK(mess,"")
            return
        if nbnd <= 0:
            mess='no hydrogen bonds (salt-bridges) found.'
            self.ConsoleMessage(mess)
            return
        bndatmlst=[]; sbatmdic={}; donedic={}
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            if len(atom.extrabnd) > 0:
                for j in atom.extraconect: bndatmlst.append([i,j])
        #
        cationdic={'ARG':1,'LSY':1,'NH3':1}
        aniondic={'GLU':1,'ASP':1,'COO':1}
        atmdic={'ARG':{' NE ':1,' NH1':1,' NH2':1},'LYS':{' NZ ':1},
                'NH3':{' N  ':1},
                'GLU':{' OE1':1,' OE2':1},'ASP':{' OD1':1,' OD2':1},
                'COO':{' O  ':1,' OXT':1}}        
        for i,j in bndatmlst:
            atomi=self.mol.atm[i]; atomj=self.mol.atm[j]
            resnami=atomi.resnam; atmi=atomi.atmnam
            resnmbi=atomi.resnmb; chaini=atomi.chainnam
            resnamj=atomj.resnam; atmj=atomj.atmnam
            resnmbj=atomj.resnmb; chainj=atomj.chainnam
            resdati=lib.PackResDat(resnami,resnmbi,chaini)
            if self.mol.IsCOOTerm(resdati): resnami='COO'
            if self.mol.IsNH3Term(resdati): resnami='NH3'
            resdatj=lib.PackResDat(resnamj,resnmbj,chainj)
            if self.mol.IsCOOTerm(resdatj): resnamj='COO'
            if self.mol.IsNH3Term(resdatj): resnamj='NH3'
            if cationdic.has_key(resnami) and aniondic.has_key(resnamj):
                #print 'cationic1',resnami,resnmbi,resnamj,resnmbj
                if atmdic[resnami].has_key(atmi) and \
                                              atmdic[resnamj].has_key(atmj):
                    if not donedic.has_key(resdati+resdatj):
                        sbatmlst.append([i,j]); donedic[resdati+resdatj]=True
            elif cationdic.has_key(resnamj) and aniondic.has_key(resnami):
                #print 'cationic2',resnamj,resnmbi,resnami,resnmbj
                if atmdic[resnami].has_key(atmi) and \
                                               atmdic[resnamj].has_key(atmj):
                    if not donedic.has_key(resdatj+resdati):
                        sbatmlst.append([j,i]); donedic[resdatj+resdati]=True
        return sbatmlst
            
    def ChangeChainName(self,drw=True):
        """ Change chain name of selected atoms
        
        """
        chainnam=wx.GetTextFromUser('Enter chain name(ex. "A")',
                                    'Change chain name of selected atoms')
        chainnam=chainnam.lstrip()
        item=lib.GetStringBetweenQuotation(chainnam)
        newnam=item[0].strip()
        lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        oldnam=self.mol.atm[lst[0]].chainnam
        for i in lst:
            self.mol.atm[i].chainnam=newnam
        if draw: self.DrawLabelChain(True)
        mess='Chain name was changed from '+oldnam+'to '+newnam+' in '
        mess=mess+str(len(lst))+' atoms.'
        self.Message2(mess) #,0,"Black")

    def ChangeGroupName(self):
        groupnam=wx.GetTextFromUser('Enter group name(ex. "group1=group2")',
                                    'Change chain name')
        groupnam=groupnam.strip()
        oldnam,newnam=lib.SplitVariableAndValue(groupnam)
        #
        lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        for i in lst:
            if self.mol.atm[i].grpnam == oldnam: self.mol.atm[i].grpnam=newnam
        mess='Group name was changed from '+oldnam+' to '+newnam
        self.ConsoleMessage(mess)

    def ChangeResidueName(self):
        mess='Enter residue name,number,chain name(ex. "ARG:1:A")'
        res=wx.GetTextFromUser(mess, 'Change residue name')
        #res=lib.GetStringBetweenQuotation(res)
        res=res.strip()
        #item=res[0].split(",")
        #resnam=item[0].strip()
        #resnmb=-1
        resnam,resnmb,chain=lib.ResolveResidueName(res)
        #if len (item) == 2: resnmb=int(item[1])
        #resnam=resnam[0:3]
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            self.Message("No selected atom.",1,"Black")
            lib.MessageBoxOK(mess,'Model(changeResidueName')
            return
        for i in lst:
            self.mol.atm[i].resnam=resnam
            #self.mol.atm[i].resnmb=resnmb
            if chain != '': self.mol.atm[i].chainnam=chain
            if resnmb > 0: self.mol.atm[i].resnmb=resnmb
            #print 'i,self.mol.atm[i].resnmb,resnmb',i,self.mol.atm[i].resnmb,resnmb
            #if chain != '*': self.mol.atm[i].chainnam=chain
        mess='Readure name has changed to '+res+' of selected atoms'
        self.Message2(mess)
        #if self.draw.labelres: self.DrawLabelRes(True,0)
    
    def RenameResDat(self,atmlst,newlst):
        for i in range(len(atmlst)):
            resnam,resnmb,chain=lib.UnpackResDat(newlst[i])
            iatm=atmlst[i]
            self.mol.atm[iatm].resnam=resnam
            self.mol.atm[iatm].resnmb=resnmb
            self.mol.atm[iatm].chainnam=chain
            
    def ListResDat(self):
        resdatlst=[]
        for atom in self.mol.atm:
            resdatlst.append(lib.Resdat(atom))
        return resdatlst
    
    def RenameResidues(self,reslst,newlst):
        # reslst: [['GLY',1],...]
        # newlst: [['ALA',5],...]
        rendic={}
        for i in xrange(len(reslst)):
            rendic[reslst[i][0]+':'+str(reslst[i][1])]=[newlst[i][0],
                                                        newlst[i][1]]      
        for atom in self.mol.atm:
            res=atom.resnam+':'+str(atom.resnmb)
            if rendic.has_key(res):
                atom.resname=rendic[res][0]; atom.resnmb=rendic[res][1]
    
    def RenumberResidue(self):
        # reslst: [['GLY',1],...]
        # newlst: [['ALA',5],...]
        rendic={}
        for i in xrange(len(reslst)):
            rendic[reslst[i][0]+':'+str(reslst[i][1])]=[newlst[i][0],
                                                        newlst[i][1]]      
        for atom in self.mol.atm:
            res=atom.resnam+':'+str(atom.resnmb)
            if rendic.has_key(res):
                atom.resname=rendic[res][0]; atom.resnmb=rendic[res][1]
    
    def InputHisName(self):
        mess='Enter his name(ex. "All,HID","Selected,HIE","HIP,HID)'
        inp=wx.GetTextFromUser(mess,'Change HIS From')
        inp=inp.strip(); item=inp.split(',')
        if len(inp) <= 0: return
        mess=[]
        oldhis=item[0]; newhis=item[1]
        if len(item) < 2 or len(item) > 2:
            mess.append("Input error in number of data. input= '"+inp+"'.\n")
        if oldhis != "HIS" and oldhis != "HIP" and oldhis != "HID" and \
                   oldhis != "HIE" \
                   and oldhis != "All" and oldhis != "Selected":
            mess.append("Input error in old HIS. input= '"+inp+"'.\n")
        if newhis != "HIS" and newhis != "HIP" and newhis != "HID" and \
                   newhis != "HIE":
            mess.append("Input error in new HIS. input= '"+inp+"'.\n")
            lib.MessageBoxOK(mess,"")
            err=3
        if len(mess) > 0:
            text=""
            for s in mess: text=text+mess
            lib.MessageBoxOK(text,"")            
            return

        if oldhis == "All": self.ChangeAllHis(newhis,True)
        elif oldhis == "Selected": self.ChangeAllHis(newhis,False)
        else: self.ChangeHis(oldhis,newhis)
        
    def ChangeAllHis(self,newhis,all):
        if all: self.SetSelectAll(True)
        lst=self.ListSelectedAtom()
        hisatm=[]; hisatmdic={}
        for i in lst:
            res=self.mol.atm[i].resnam
            if res == "HIS" or res == "HID" or res == "HIE" or res == "HIP":
                resnam=self.mol.atm[i].resnam; resnmb=self.mol.atm[i].resnmb
                if hisatmdic.has_key(resnam+":"+str(resnmb)): continue
                hisatm.append([resnam,resnmb,self.mol.atm[i].seqnmb])
                hisatmdic[resnam+":"+str(resnmb)]=self.mol.atm[i].seqnmb
        if len(hisatm) <= 0:
            self.Message("No HIS residues are selected.",0,"")
            return
        nchng=0
        for i in range(len(hisatm)):
            res=hisatm[i][0]; nmb=hisatm[i][1]; ii=hisatm[i][2]
            hisnam=self.FindHisForm(ii,res,nmb)
            ie=ii+17
            if ie > len(self.mol.atm): ie=len(self.mol.atm)
            if hisnam != newhis:
                if hisnam == "HIP" and newhis == "HID": 
                    self.HIPToHID(res,nmb,ii)
                if hisnam == "HIP" and newhis == "HIE": 
                    self.HIPToHIE(res,nmb,ii)
                if hisnam == "HID" and newhis == "HIP": 
                    self.HIDToHIP(res,nmb,ii)
                if hisnam == "HID" and newhis == "HIE": 
                    self.HIDToHIE(res,nmb,ii)
                if hisnam == "HIE" and newhis == "HIP": 
                    self.HIEToHIP(res,nmb,ii)
                if hisnam == "HIE" and newhis == "HID": 
                    self.HIEToHID(res,nmb,ii)
                nchng += 1
        self.DrawMol(True)
        mess=str(nchng)+" '"+hisnam+"' were changed to '"+newhis+"'"
        self.Message(mess,0,"")
        self.ConsoleMessage(mess)
    
    def ChangeHisForm(self,resdat):    
    #def HIPToHID(self,res,nmb,ii):
    #    pass
    #def HIPToHIE(self,res,nmb,ii):
    #    pass
    #def HIDToHIP(self,res,nmb,ii):
    #    pass
    #def HIDToHIE(self,res,nmb,ii):
    #    pass
    #def HIEPToHIP(self,res,nmb,ii):
    #    pass
    #def HIEToHID(self,res,nmb,ii):
        pass
    
    def RenameHis(self):
        reslst=self.ListResidue(True)
        nhis=0; hisatm=[]
        for i in range(len(reslst)):
            for res,nmb in reslst[i]:
                if res == "HIS" or res == "HID" or res == "HIE" or res == "HIP":
                    for atom in self.mol.atm:
                        resi=atom.resnam; nmbi=atom.resnmb
                        if res == resi and nmb == nmbi:
                            hisatm.append([res,nmb,atom.seqnmb]); break
        if len(hisatm) <= 0: return
        #
        for i in range(len(hisatm)):
            res=hisatm[i][0]; nmb=hisatm[i][1]; ii=hisatm[i][2]
            hisnam=self.FindHisForm(ii,res,nmb)
            ie=ii+17
            if ie > len(self.mol.atm): ie=len(self.mol.atm)
            for j in range(ii,ie):
                if self.mol.atm[j].resnam != res or \
                                      self.mol.atm[j].resnmb != nmb: break
                self.mol.atm[j].resnam=hisnam
    
    def FindHisForm(self,ii,resnam,resnmb):
        hisnam="HIS"
        hd1=False; he2=False
        ie=ii+17
        if ie > len(self.mol.atm): ie=len(self.mol.atm)
        for j in range(ii,ie):
            resj=self.mol.atm[j].resnam; nmbj=self.mol.atm[j].resnmb
            if resj == resnam and nmbj == resnmb:
                atom=self.mol.atm[j]
                if atom.atmnam == ' HD1': hd1=True
                if atom.atmnam == ' HE2': he2=True

        if hd1 and not he2: hisnam='HID'
        if not hd1 and he2: hisnam='HIE'
        if hd1 and he2: hisnam='HIP'
        if not hd1 and not he2: hisnam='HIS'
       
        return hisnam
                   
    def RenameAtoms(self,atmlst,newlst):
        # atmlst: ["atmnam",...]
        # newlst: ["atmnam",...]
        atmdic={}
        for i in xrange(len(atmlst)):
            atmdic[atmlst[i]]=newlst[i]
        for atom in self.mol.atm:
            if atmdic.has_key(atom.atmnam): atom.atmnam=atmdic[atom.atmnam]    
        
    def RenameChains(self,namlst,newlst):
        # namlst: ["chainnam',...]
        # newlst: ["newname",...]
        namdic={}
        for i in range(len(namlst)):
            namdic[namlst[i]]=newlst[i]
        for atom in self.mol.atm:
            if namdic.has_key(atom.chainnam): 
                atom.chainnam=namdic[atom.chainnam]    
            
    def ChangeAtomName(self):
        mess='Enter atom name(ex. " CA ")'
        text=wx.GetTextFromUser(mess, 'Change atom name')
        if len(text) <= 0: return
        #atmnam=atmnam.strip()
        #atmnam=atmnam[1:4]
        items=lib.SplitStringAtSeparator(text,',')
        try: atmnam=lib.GetStringBetweenQuotation(items[0])[0]
        except:
            mess='Wrong atmnam input. Neglected.'
            self.Message(mess,0,'')
            return
        r=-1
        if len(items) > 1:
            try: r=float(items[1])
            except: pass
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            self.Message("No selected atom.",1,"Black")
            return
        for i in lst:
            self.mol.atm[i].atmnam=atmnam   #[0:5]
        self.DrawLabelAtm(True,1)
    
    
    def GetPointedAtoms(self):
        atmlst=self.mousectrl.pntatmhis.GetSaved()
        return atmlst
    
    def ChangeBondLength(self):
        mess='Enter bond length(e.g, 1.2, 0 for use default length)'
        text=wx.GetTextFromUser(mess, 'Change element name')
        if len(text) <= 0: return

        items=lib.SplitStringAtSpacesOrCommas(text)
        r=-1
        try: r=float(items[0])
        except: pass
        if r < 0:
            mess='Wrong bond distance data='+text
            self.ConsoleMessage(mess)
            return
        #nsel,lst=self.ListSelectedAtom()
        
        lst=self.GetPointedAtoms() # mousectrl.pntstmhis.Get()
        if len(lst) < 2:
            mess='Please select two atoms'
            lib.MessageBoxOK(mess,'Model:Change Bond length')
            return
        atm1=lst[0]; atm2=lst[1]
        self.ChangeLength(atm1,atm2,r,drw=False)
        
        self.DrawMol(True)
                
    def ChangeElementAndLength(self):
        mess='Enter element name[,length](ex. " O", 1.2)'
        text=wx.GetTextFromUser(mess, 'Change element name')
        if len(text) <= 0: return

        items=lib.SplitStringAtSpacesOrCommas(text)
        
        self.ConsoleMessage('items='+str(items))
        elmnam=lib.ElementNameFromString(items[0])
        self.ConsoleMessage('ChangeElementAndLength. elnmam='+elmnam)
        
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            lib.MessageBoxOK("Please select atoms","ChangeElementAndnLength")
            return

        self.ChangeElement(elmnam,lst,messout=True)
        
        r=-1 #; rchange=False
        if len(items) >=2:
            try: r=float(items[1]) #; rchange=True
            except: pass
        self.ConsoleMessage('ChangeElementAndLength. r='+str(r)) 
        #if r > 0: rcomp=True
        #else: rcomput=False
        self.ConsoleMessage('Before ChangeElement. elmnam='+elmnam)
        
        if r >= 0: 
            for atm1 in lst:
                atm2=-1
                for i in self.mol.atm[atm1].conect:
                    if self.mol.atm[i].elm == ' H': continue
                    if self.mol.atm[i].elm == 'XX': continue
                    if self.mol.atm[i].elm == ' X': continue
                    atm2=i; break
                if atm2 >= 0: self.ChangeLength(atm2,atm1,r,messout=True)
        self.DrawMol(True)
        
    def ChangeElement(self,elmnam,lst,drw=False,messout=False):
        self.ConsoleMessage('Entered in ChangeElement')

        for i in lst:
            elm1=self.mol.atm[i].elm
            self.mol.atm[i].elm=elmnam
            self.mol.atm[i].SetAtomParams(elmnam)
            
            #self.molctrl.ResetMol(self.mol)
            
            if messout:
                mess='Element '+elm1+' is changed to '+elmnam
                self.ConsoleMessage(mess)
        if drw:
            self.DrawMol(True)
            if self.draw.labelelm: self.DrawLabelElm(True,0)
    
    def ChangeLength(self,atm1,atm2,r,messout=False,drw=False):
        """ Change length between atm1 in lst1 and atm2 in lst2 by moving atom2
            along atm1-atm2 bond  
        
        """
        self.ConsoleMessage('Entered in ChangeLength')

        if r < 0: return
        elm1=self.mol.atm[atm1].elm
        cc1=self.mol.atm[atm1].cc
        elm2=self.mol.atm[atm2].elm
        cc2=self.mol.atm[atm2].cc
        if r == 0:
            try: r=const.ElmCov[elm1]+const.ElmCov[elm2]
            except: r=1.50
        cc=lib.ChangeLength(cc1,cc2,r)
        self.mol.atm[atm2].cc=cc
        if messout:
            mess='Changed length between '+str(atm1)+' and '+str(atm2)
            mess=mess+'. r='+'%6.3f' % r
            self.ConsoleMessage(mess)
        if drw:
            self.DrawMol(True)
            if self.draw.labelelm: self.DrawLabelElm(True,0)

    def InputAtomName(self,a):
        mess='Enter atom name(ex. " N  ")'
        atmnam=wx.GetTextFromUser(mess, 'Add atom name')
        #atmnam=lib.GetStringBetweenQuotation(atmnam)[0]
        maxnmb=self.mol.FindMaxAtmNmb()
        atmnam=atmnam[1:5]
        atmnmb=atmnam[5:]
        if len(atmnmb) <= 0:
            atmnmb=maxnmb+1
        else: atmnmb=int(atmnmb)
        self.mol.ChangeAtomName(self,a,atmnam,atmnmb)
    
    def DeleteVdwBond(self):
        lst=self.ListTargetAtoms()
        self.mol.DelVdwBond(lst)
        self.DrawVdwBond(False)
        #self.mdlwin.menu.Check('Hydrogen/vdW bond',False)        
        self.menuctrl.CheckMenu('Hydrogen Bonds',False)
        
    def DeleteHydrogenBond(self):
        drwlabel='Hydrogen Bonds'
        lst=self.ListTargetAtoms()
        self.mol.DelHydrogenBond(lst)
        self.DrawVdwBond(False)
        #self.mdlwin.menu.Check('Hydrogen/vdW bond',False)
        self.draw.DelDrawObj(drwlabel)
        self.menuctrl.CheckMenu(drwlabel,False)
                    
    def NewMolecule(self):
        # create new molecule, i.e. mol with no atoms        
        self.BuildMol("new",'') #[])
        #if self.curmol < 0: self.curmol=0
        #else:
        #    nmol=len(self.molnam)
        #    self.curmol=nmol-1
        #
        self.curmol,self.mol=self.molctrl.GetCurrentMol()
        self.SetUpDraw(True)
        #self.SetCurrentMol(curmol,mol)
        #self.SetUpDraw(True)
        self.DrawMol(True)
        
    def MakeSuperMolecule(self):
        """ New molecule woth all molecules """
        nmol=self.molctrl.GetNumberOfMols()
        if nmol <= 0: return
        molnamlst=[]
        # new molecule. bocomes current
        self.NewMolecule()
        # the first molecule
        mol=self.molctrl.GetMol(0)
        molnamlst.append(mol.name)
        atm=mol.CopyAtom()
        self.mol.atm=atm
        #self.mol.atm=mol.CopyAtom()
        #mol=mol.CopyMolecule()
        
        # merge molecules to the first
        for i in range(1,nmol):
            mol=self.molctrl.GetMol(i)
            atm=mol.CopyAtom()
            self.mdlargs['MergeMolecule']=atm
            self.MergeMolecule(None,False) #(atm,False)
            molnamlst.append(mol.name)
        # change default group name to molname
        curgrpdic={}
        i=-1
        for atom in self.mol.atm:
            grp=atom.grpnam
            if curgrpdic.has_key(grp): continue
            i += 1; curgrpdic[grp]=molnamlst[i]
        for atom in self.mol.atm:
            grp=atom.grpnam
            if curgrpdic.has_key(grp): atom.grpnam=curgrpdic[grp]
        #
        name=self.mol.name
        mess='Created supermolecue. Name='+name+', Number of atoms='
        mess=mess+str(len(self.mol.atm))
        self.Message2(mess)
        self.FitToScreen(True,True)
        #self.DrawMol(True)
        
    def PasteMolFromClipboard(self):
        # paste atoms in clipboard to current mol
        atm=[]
        if not wx.TheClipboard.IsOpened():
            try:
                cbobj=wx.TextDataObject()
                wx.TheClipboard.Open()
                ok=wx.TheClipboard.GetData(cbobj)
                if ok:
                    dumpmol=cbobj.GetText()
                    atm=dumpmol.encode('utf-8') # needs this!
                    atm=pickel.loads(atm)
                else: 
                    mess='No data in clipboard.'
                    self.Message(mess,0,'black')
                wx.TheClipboard.Close()
                if not ok: return
            except:
                mess='Failed to open clipboard.'
                self.Message(mess,0,'black')
                return
        if len(atm) <= 0: return
        try:        
            for i in range(len(atm)): atm[i].setctrl=self.setctrl
            #
            mess=str(len(atm))+" atoms are merged. total number of atoms="
            self.mdlargs['MergeMolecule']=atm
            self.MergeMolecule(None,True) #(atm,True)
            
            ntot,nhev,nhyd,nter=self.mol.CountAtoms()
            mess=mess+str(ntot)+" ["+str(nhev)+","+str(nhyd)+","+str(nter)+"]"
            self.Message2(mess)
            # clear self.savecc
            self.savcc=[]; self.savcclst=[]
            
            self.FitToScreen(True,False)        
        ###self.DrawMol(True)
        except:
            mess='Failed to paste molecule object, may be wrong data type in '
            mess=mess+'clipbload.'
            self.Message2(mess)

    def PasteAtomXYZFromClipboard(self):
        """ Pasete atom coordinates(xyz) from clipboad
        
        :return lst xyzmol: [[elm(str),x(float),y(float),z(float)],,,]
        """
        natm=0; xyzmol=[]
        text=''
        if not wx.TheClipboard.IsOpened():
            try:
                cbobj=wx.TextDataObject()
                wx.TheClipboard.Open()
                ok=wx.TheClipboard.GetData(cbobj)
                if ok:
                    text=cbobj.GetText()
                    text=text.encode('utf-8') # needs this!
                else: 
                    mess='No data in clipboard.'
                    self.Message(mess,0,'black')
                wx.TheClipboard.Close()
                if not ok: return
            except:
                mess='Failed to open clipboard.'
                self.Message(mess,0,'black')
                return
        if len(text) <= 0: return natm,xyzmol
        text=text.lstrip()
        textlst=text.split('\n')
        test=True
        try:
            for xyz in textlst:
                xyz=xyz.strip()
                if xyz == ' ': continue
                items=lib.SplitStringAtSpaces(xyz)
                if len(items) <= 0: continue
                i=0
                if len(items) >= 5: i=1
                elm=items[i]
                if elm.isdigit():
                    an=int(elm); elm=const.ElmSbl[an]
                elif elm.replace('.','').isdigit():
                    an=int(float(elm)+0.001); elm=const.ElmSbl[an]    
                if len(elm) <= 1: elm=' '+elm
                #id=1
                #if len(items) > 4: id=2
                x=float(items[i+1]); y=float(items[i+2]); z=float(items[i+3])
                xyzmol.append([elm,x,y,z])
            natm=len(xyzmol)
            mess='Copied xyz data from clipboard. natm='+str(natm)
            self.ConsoleMessage(mess)
        except:
            mess='Failed to get xyz data from clipboard. The data format may be'
            mess=mess+' wrong.\n'
            mess=mess+'format: [label(str),]elm(str),x(float),y(float),z(float)'
            lib.MessageBoxOK(mess,'Model.PasteAtomXYZFromClipboard')        
        return natm,xyzmol
             
    def PasteMolXYZFromClipboard(self):
        """ paste molecule coordinates(xyz) in clipboard and merge current mol
        
        coordinates(str): elm,(an(int)),x,y,z,\n... 
        """
        mol=molec.Molecule(self)
        """
        text=''
        if not wx.TheClipboard.IsOpened():
            try:
                cbobj=wx.TextDataObject()
                wx.TheClipboard.Open()
                ok=wx.TheClipboard.GetData(cbobj)
                if ok:
                    text=cbobj.GetText()
                    text=text.encode('utf-8') # needs this!
                else: 
                    mess='No data in clipboard.'
                    self.Message(mess,0,'black')
                wx.TheClipboard.Close()
                if not ok: return
            except:
                mess='Failed to open clipboard.'
                self.Message(mess,0,'black')
                return
        if len(text) <= 0: return
        text=text.lstrip()
        textlst=text.split('\n')
        test=True
        #try:
        if test:
            xyzmol=[]
            for xyz in textlst:
                xyz=xyz.strip()
                if xyz == ' ': continue
                items=lib.SplitStringAtSpaces(xyz)
                if len(items) <= 0: continue
                elm=items[0]
                if elm.isdigit():
                    an=int(elm); elm=const.ElmSbl[an]
                elif elm.replace('.','').isdigit():
                    an=int(float(elm)+0.001); elm=const.ElmSbl[an]    
                if len(elm) <= 1: elm=' '+elm
                id=1
                if len(items) > 4: id=2
                x=float(items[id]); y=float(items[id+1]); z=float(items[id+2])
                xyzmol.append([elm,x,y,z])
        """
        natm,xyzmol=self.PasteAtomXYZFromClipboard()
        if natm > 0:
            mol.SetXYZAtoms(xyzmol,[],[]) # bond,resfrg
            mol.AddBondUseBL([])
            self.mdlargs['MergeMolecule']=mol.atm
            self.MergeMolecule(None,False) #(mol.atm,False)
        else:
        #except:
            mess='Failed to paste molecular xyz text, may be wrong data type in'
            mess=mess+' clipbload.'
            self.ConsoleMessage(mess)
        
    def CopyMolToClipboard(self,cut):
        # copy selected atoms to clipboard
        # cut(bool): True for cut and copy, Falce for copy
        lst=self.ListTargetAtoms()
        nlst=len(lst)
        #cpy=self.mol.CopyMolecule()
        cpy=molec.Molecule(self)
        cpy.atm=self.mol.CopyAtom()
        if nlst > 0:
            alllst=xrange(len(cpy.atm))
            setdel=set(alllst)-set(lst)
            dellst=list(setdel)
            cpy.DelAtoms(dellst)
        # 
        if cut:
            self.mdlargs['DeleteTerAtHead']=cpy
            self.DeleteTerAtHead(None)
            self.DeleteSelected()
        #
        for i in range(len(cpy.atm)):            
            cpy.atm[i].parent=''
            cpy.atm[i].setctrl=''
                
        dumpmol=pickel.dumps(cpy.atm)
        cbobj=wx.TextDataObject()
        cbobj.SetText(dumpmol)
        try:
            wx.TheClipboard.Open()
            wx.TheClipboard.Clear() # clear clipboard
            wx.TheClipboard.SetData(cbobj)
            #wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
            mess=str(nlst)+" atoms are copied to clipboard."
            self.Message2(mess)
        except:
            mess='Faled to copy data to clipboard.'
            self.Message2(mess)
    
    def CopyMolXYZToClipboard(self):
        # copy selected atoms to clipboard
        # cut(bool): True for cut and copy, Falce for copy
        text=''; ff12='%12.8f'
        for atom in self.mol.atm:
            text=text+'  '+atom.elm+'  '
            text=text+(ff12 % atom.cc[0])+' '
            text=text+(ff12 % atom.cc[1])+' '
            text=text+(ff12 % atom.cc[2])+'\n '

        cbobj=wx.TextDataObject()
        cbobj.SetText(text)
        try:
            wx.TheClipboard.Open()
            wx.TheClipboard.Clear() # clear clipboard
            wx.TheClipboard.SetData(cbobj)
            #wx.TheClipboard.Flush()
            wx.TheClipboard.Close()
            mess=str(len(self.mol.atm))
            mess=mess+" xyz coordinates are copied to clipboard."
            self.Message(mess,0,'black')
        except:
            mess='Faled to copy xyz coordinate data to clipboard.'
            self.Message(mess,0,'black')
    
    def SaveMolBitmapOnFile(self):
        filename=""; wildcard='bmp(*.bmp)|*.bmp'
        dlg = wx.FileDialog(self.mdlwin, "Save as...", os.getcwd(),
                            style=wx.SAVE, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath()            
        dlg.Destroy()        
        if len(filename) < 0: return
        #
        size=self.mdlwin.GetClientSize()
        pos=self.mdlwin.GetPosition()
        width=size[0]; hight=size[1]-40
        bmp=wx.EmptyBitmap(width,hight)
        #windc=wx.WindowDC(self.mdlwin) # this does not refresh second copy 
        windc=wx.ScreenDC()
        memdc=wx.MemoryDC()

        memdc.SelectObject(bmp)
        memdc.Blit(0,0,width,hight,windc,pos[0]+8,pos[1]+80)
        #
        lib.SaveBitmapAsFile(filename,bmp)
        #
        self.Message('Bitmap is save on file='+filename,1,'black')
                      
    def CopyCanvasImageToClipboard(self):        
        """ Copy canvas image to clipboad(bitmap for WINDOWS and png for MACOSX) .
        """
        retmess='fumodel. CopyCanvasImageToClipboard: '
        platform=lib.GetPlatform()
        winobj=self.mdlwin.draw.canvas
        if platform == 'WINDOWS':
             retmess,img=lib.CaptureWindowW(winobj,True)
             bmp=img.ConvertToBitmap(32)
             retmess=lib.CopyBitmapToClipboard(bmp)
        elif platform == 'MACOSX':
            #winobj=self.mdlwin.draw.canvas
            [x,y]=winobj.ClientToScreen(winobj.GetPosition())
            [w,h]=winobj.GetClientSize()
            y += 60; h -= 60
            rect=[x,y,w,h]
            retmess=lib.ScreenCaptureMac(rect,'clipboard')
        else:
            retmess='fumodel.CopyCanvasImageToClipboard: The platform '
            retmess=retmess+platform+' is not supported.'  
            self.Message(mess,0,'black')
            return     
        mess=retmess
        if retmess == '': mess='Canvas bitmap image is copied to clipboard.'
        self.Message(mess,0,'black')
                
    def ClearClipboard(self):
        wx.TheClipboard.Clear()
        self.Message('Clipboard is emptied.',1,'black')
    
    def MergeToCurrent(self,filename,drw=True):
        # merge molecular data in filename to current molecule
        # filename(str): file name
        if self.molctrl.GetNumberOfMols() <= 0:
            self.Message('Merge: No current molecule to merge.',0,'black')
            return
        root,ext=os.path.splitext(filename) 
        tmpmol=molec.Molecule(self)
        molnam=molec.Molecule.MakeMolNameWithExt(filename)
        if ext == ".pdb" or ext == ".ent":
            pdbmol,fuoptdic=rwfile.ReadPDBMol(filename)
            tmpmol.SetPDBMol(pdbmol)
            self.mol.mergedfile=filename
            self.mol.mergedmolname=molec.Molecule.MakeMolNameWithExt(filename)
        elif ext == '.xyz':
            xyzmol,bond,resfrg=rwfile.ReadXYZMol(filename)
            tmpmol.SetXYZAtoms(xyzmol,bond,resfrg)
            self.mol.mergedfile=filename
            self.mol.mergedmolname=molec.Molecule.MakeMolNameWithExt(filename)
        elif ext == '.zmt':
            title,zelm,zpnt,zprm,zmtdic=rwfile.ReadZMTFile(filename)
            zmtatm=lib.ZMToCC(zelm,zpnt,zprm)
            tmpmol.SetZMTAtoms(zmtatm,pnts=zpnt,zmtdic=zmtdic)
            tmpmol.AddBondUseBL([])
            self.mol.mergedfile=filename
            self.mol.mergedmolname=molec.Molecule.MakeMolNameWithExt(filename)
        elif ext == '.mol':
            moldat=rwfile.ReadMolFile(filename)
            tmpmol.SetMolAtoms(moldat[0][3])
            self.mol.mergedfile=filename
            self.mol.mergedmolname=molec.Molecule.MakeMolNameWithExt(filename)
        # does fragment file exist?       
        """
        frgfile=root+'.frg'
        if os.path.exists(frgfile):
            natm=len(tmpmol.atm)
            resnam,bdalst,frgchglst,frgnamlst= \
                                          rwfile.ReadFrgDatFile(frgfile,natm)
            tmpmol.ClearBDABAA([])
            tmpmol.ResetBDADic()
            if len(bdalst) > 0:
                for i in xrange(len(bdalst)):
                    ia=bdalst[i][2]; ib=bdalst[i][3]
                    tmpmol.SetToBDADic(ia,ib)
                    tmpmol.atm[ia].frgbaa=ib    
                tmpmol.SetFragmentName()
            else:
                for i in range(len(tmpmol.atm)): 
                    tmpmol.atm[i].frgnam=frgnamlst[i]
            mess=molnam+" is merged with fragment data in "+frgfile
            self.ConsoleMessage(mess)
            if len(frgchglst) > 0: tmpmol.SetFragmentCharge(frgchglst)                    
        """
        tmpmol.name=molnam
        
        self.mdlargs['DeleteTerAtHead']=tmpmol
        self.DeleteTerAtHead(None)
        self.mdlargs['MergeMolecule']=tmpmol.atm        
        self.MergeMolecule(None,True) #(tmpmol.atm,True)
        #
        self.ConsoleMessage('merged file='+filename)
        self.MsgNumberOfAtoms(1)

        if drw: self.DrawMol(True)

    def MergeMolecule(self,mrgatm,check=True,drw=True):
        # merge molecule to corrent work mol instance
        # mrgatm(lst): ATOM instance list
        # check(bool): True for check short contacts, False do not check      
        fromargs=False
        if mrgatm == None:
            if not self.mdlargs.has_key('MergeMolecule'): return
            fromargs=True
            mrgatm=self.mdlargs['MergeMolecule']
        if len(self.mol.atm) == 0:  # new molecule
            for atom in mrgatm:
                atom.select=True
                self.mol.atm.append(atom)
            if drw: self.SetUpDraw(True)
        else:
            self.SetSelectAll(False) #Atom(self.mol.atm,False)
            ngrp=self.mol.atm[0].grpnam
            norg=len(self.mol.atm)
            ngrp,grpdic=self.MakeGroupDic(self.mol.atm)
            if check:
                molatm=self.mol.atm
                self.mdlargs['CheckShortContact2']=[molatm,mrgatm]
                nsht=self.CheckShortContact2(None,None) #self.mol.atm,mrgatm)
                if nsht > 0:
                    #srmin='%6.3f' % rmin
                    mess='Merge: Short contact occured.' 
                    mess=mess+' number of short contacts='+str(nsht)
                    #mess=mess+', rmin='+srmin
                    dlg=lib.MessageBoxOKCancel(mess,"")
                    if not dlg: return
            
            for atom in mrgatm:
                atom.seqnmb += norg
                atom.atmnmb=atom.seqnmb
                atom.grpnam='mrg'+str(ngrp+1)
                atom.select=True
                # renumber conect data
                for j in range(len(atom.conect)):
                    try: atom.conect[j] += norg
                    except: pass
                # renumber fragment data
                if atom.frgbaa > 0:
                    atom.frgbaa += norg
                self.mol.atm.append(atom)
        ###self.FitToScreen(False,False)
        # clear self.savecc
        #self.savcc=[]; self.savcclst=[]
        self.savatmcc.Clear() #self.ClearSaveCC()
        if drw:
            self.FitToScreen(False,False)
            self.DrawMol(True)
            self.mol.SetDrawObjs(self.draw.GetDrawObjs())
            self.mol.SetViewItems(self.draw.GetViewItems())
        
        if fromargs: del self.mdlargs['MergeMolecule']
    
    def ConnectMergedGroup(self):
        pntslst=self.mousectrl.pntatmhis.GetSaved()
        if len(pntslst) <= 1:
            mess='No selected atom data in pointed atom history.\n'
            mess=mess+'Please deselect all and select two atoms again.'
            lib.MessageBoxOK(mess,'Model(ConnectMergedGroup)')
            return
        self.mousectrl.pntatmhis.Clear()
        pntslst.reverse()
        atm1=pntslst[0]; atm2=pntslst[1]   
        self.ConnectGroups(atm1,atm2,select=True)
        
    def ConnectGroups(self,atm1,atm2,select=False,drw=True):
        """
        
        :param int atm1: sequence number of atom
        :param int atm2: sequence numer of atom. atm1 and atm2 are fused.
        :param bool select: Set select to merged atoms
        :param bool drw: Draw moelcues
        :return: connectedlst - list of connected atoms, 
                        [[atm1(int),atm2(int)],...]
        """
        connectedlst=[]
        #ngrp,grpnamdic,grpatmlstdic=self.FindGroupsOfAtoms([atm1,atm2])
        grpdic=self.FindConnectedGroup()
        ngrp=len(grpdic)
        found1=False; found2=False
        for ig,atmlst in grpdic.iteritems():
            if atm1 in atmlst: 
                grp1nam=str(ig); grp1atmlst=atmlst; found1=True
            if atm2 in atmlst: 
                grp2nam=str(ig); grp2atmlst=atmlst; found2=True
            if found1 and found2: break
        type=-1
        if len(grp2atmlst) < 2:
            type=3
            # add group is an atom
            connectedlst=self.ConnectGroupsType3(atm1,atm2)
        elif grp1nam == grp2nam:
            type=2
            # atm1 and atm2 belong to the same group
            connectedlst=self.ConnectGroupsType2(atm1,atm2,grp1nam,grp1atmlst)
        else: 
            type=1
            # hydrogen or heavy atom
            atm1ish=True
            if self.mol.atm[atm1].elm != ' H': atm1ish=False
            atm2ish=True
            if self.mol.atm[atm2].elm != ' H': atm2ish=False
            atm1h=self.FindConnectedHAtom(atm1)
            atm2h=self.FindConnectedHAtom(atm2)
            if atm1ish and atm2ish:
                # """ A-H...H-B """
                connectedlst=self.ConnectGroupsType1(atm1,atm2,grp1nam,grp2nam,
                                                     grp1atmlst,grp2atmlst)
            elif atm1ish and not atm2ish:
                # """ A-H...B- """
                if atm2h >= 0:
                    atm2=atm2h
                    connectedlst=self.ConnectGroupsType1(atm1,atm2,grp1nam,
                                                 grp2nam,grp1atmlst,grp2atmlst)
                else: 
                    pass
            elif not atm1ish and atm2ish:
                #""" -A...H-B """
                if atm1h >= 0:
                    atm1=atm1h
                    connectedlst=self.ConnectGroupsType1(atm1,atm2,grp1nam,
                                                 grp2nam,grp1atmlst,grp2atmlst)
                else:
                    pass
            elif not atm1ish and not atm2ish:
                #""" -A...B- """
                if atm1h >= 0 and atm2h >= 0:
                    pile=True
                    atm1=atm1h; atm2=atm2h
                    connectedlst=self.ConnectGroupsType1(atm1,atm2,grp1nam,
                                       grp2nam,grp1atmlst,grp2atmlst,pile=pile)
                else:
                    pass
        if drw and len(connectedlst) > 0:
            self.DrawLabelElm(False,0)
            self.DrawMol(True)
        
        return connectedlst,type
    
    def FindGroupsOfAtoms(self,atmlst):
        grpnamdic={}; grpatmlstdic={}
        for i in atmlst: 
            grpnamdic[i]=''; grpatmlstdic[i]=[]
        grplst=self.ListGroupName()
        grpdic={}
        for i in atmlst:
            for grpnam in grplst:
                grpatmlst=self.ListGroupAtoms(grpnam)
                if i in grpatmlst:
                    grpnamdic[i]=grpnam
                    grpatmlstdic[i]=grpatmlst
                    grpdic[grpnam]=True
        ngrps=len(grpdic)                

        return ngrps,grpnamdic,grpatmlstdic        
            
    def FindGroupsToWhichAtomsBelong(self,atatmlst):
        if len(atatmlst) < 1: return '','',[],[]

        basegrpatmlst=[]; addgrpatmlst=[]
        basegrp=''; addgrp=''
        grplst=self.ListGroupName()
        #
        grp1atm1=atatmlst[0][0]; grp2atm1=atatmlst[0][1]
        for i,j in atatmlst:
            for grpnam in grplst:
                grpatmlst=self.ListGroupAtoms(grpnam)
                if basegrp != '' and addgrp != '': break
                if grp1atm1 in grpatmlst: 
                    basegrp=grpnam; basegrpatmlst=grpatmlst
                if grp2atm1 in grpatmlst:
                    addgrp=grpnam; addgrpatmlst=grpatmlst
            if basegrp == addgrp:
                mess='Unable to connect, since the selected atoms belong to'
                mess=mess+' the same group. '
                lib.MessageBoxOK(mess,'Model.ConnectGroups')
                return '','',[],[]
        ok=True
        for i in range(1,len(atatmlst)):
            ii=atatmlst[i][0]; jj=atatmlst[i][1]  
            if not ii in basegrpatmlst:
                ok=False; break
            if not jj in addgrpatmlst:
                ok=False; break
        if ok:
            return basegrp,addgrp,basegrpatmlst,addgrpatmlst
        else:
            mess='Unable to connect, since the selected atoms belong to more '
            mess=mess+'than two groups. '
            lib.MessageBoxOK(mess,'Model.ConnectGroups')
            return '','',[],[]

    def FindConnectedHAtom(self,atm1):
        hatm=-1
        for i in self.mol.atm[atm1].conect:
            if self.mol.atm[i].elm == ' H':
                hatm=i; break
        return hatm

    def ConnectGroupsType3(self,atm1,atm2):
        connectedlst=[]
        elm1=self.mol.atm[atm1].elm
        elm2=self.mol.atm[atm2].elm
        if elm1 == ' H':
            self.ChangeElement(elm2,[atm1])
            self.ChangeLength(atm1,atm2,0)
            self.mol.DelAtoms([atm2])
        else:
            self.ChangeLength(atm1,atm2,0)
            self.mol.AddBond(atm1,atm2,1)
        connectedlst.append([atm1,atm2])
        return connectedlst
            
    def ConnectGroupsType1(self,atm1,atm2,grp1nam,grp2nam,grp1atmlst,
                           grp2atmlst,pile=False,select=True):
        """ connect separated two groups at one site, -A-H and H-B- -> -A-B- """
        
        """:param lst pile: [atma(int),atmb(int)], put atmb on atma """
        connectedlst=[]
        #grplst=self.ListGroupName()
        #basegrp=''; addgrp=''
        grp1atm1=atm1; grp2atm1=atm2
        basegrpnam=grp1nam; addgrpnam=grp2nam
        if basegrpnam == '' or addgrpnam == '': return
        basegrpatmlst=grp1atmlst; addgrpatmlst=grp2atmlst
        grp1atm2=self.mol.atm[grp1atm1].conect[0]
        for i in self.mol.atm[grp1atm1].conect:
            if self.mol.atm[i].elm != ' H': 
                grp1atm2=i; break     
        elm2=self.mol.atm[grp1atm2].elm
        grp1atm2nam='grp1atm2'
        self.mol.atm[grp1atm2].atmtxt=grp1atm2nam
        grp1atm1cc=numpy.array(self.mol.atm[grp1atm1].cc)
        grp1atm2cc=numpy.array(self.mol.atm[grp1atm2].cc)
        grp2atm1cc=numpy.array(self.mol.atm[grp2atm1].cc)
        grp2atm2=self.mol.atm[grp2atm1].conect[0]       
        grp2atm2cc=numpy.array(self.mol.atm[grp2atm2].cc)
        elm4=self.mol.atm[grp2atm2].elm
        grp2atm2nam='grp2atm2'
        self.mol.atm[grp2atm2].atmtxt=grp2atm2nam
        # elongate the bond
        rbnd=const.ElmCov[elm2]+const.ElmCov[elm4]
        grp1atm1pos=lib.CalcPositionWithNewBL(grp1atm2cc,grp1atm1cc,rbnd)
        rorg=lib.Distance(grp1atm1cc,grp1atm2cc)
        self.mol.atm[grp1atm1].cc=grp1atm1pos[:]
        # translate molobj.atomsbuildatms
        dcc=[grp2atm2cc[0]-grp1atm1pos[0],grp2atm2cc[1]-grp1atm1pos[1],
             grp2atm2cc[2]-grp1atm1pos[2]]
        cc=[]
        for i in addgrpatmlst:
            for j in range(3): 
                self.mol.atm[i].cc[j] -= dcc[j]
            cc.append(self.mol.atm[i].cc[:])
            if select: self.mol.atm[i].select=True
        #
        grp2atm1cc=numpy.array(self.mol.atm[grp2atm1].cc)
        grp2atm2cc=numpy.array(self.mol.atm[grp2atm2].cc)
        vec12=grp1atm1cc-grp1atm2cc
        vec34=grp2atm1cc-grp2atm2cc
        da=lib.AngleT(vec34,vec12)
        ax=lib.NormalVector(grp1atm2cc,grp1atm1cc,grp2atm1cc) # (atm2cc,atm1pos,atm3cc
        u=lib.RotMatAxis(ax,da)        
        cc=lib.RotMol(-u,grp1atm1pos,cc)
        ii=-1
        for i in addgrpatmlst: 
            ii += 1
            self.mol.atm[i].cc=cc[ii]
        dellst=[]
        if pile:
            # put atmb on atma
            cca=numpy.array(self.mol.atm[grp1atm2].cc)
            ccb=numpy.array(self.mol.atm[grp2atm2].cc)
            dcc=cca-ccb
            for i in addgrpatmlst:
                atom=self.mol.atm[i]
                atom.cc[0] += dcc[0]; atom.cc[1] += dcc[1]; atom.cc[2] += dcc[2]
            self.mol.DelBond(grp1atm2,grp2atm2)
            for ic in self.mol.atm[grp2atm2].conect:
                self.mol.atm[grp1atm2].conect.append(ic)
            
            dellst.append(grp2atm2)
        #
        dellst=dellst+[grp1atm1,grp2atm1]
        dellst.sort()
        self.mol.DelAtoms(dellst)
        # connected bond
        if pile: connectedlst=[]
        else:
            grp1atm2=self.FindAtomSeqnmbOfAtmtxt(grp1atm2nam,False)
            grp2atm2=self.FindAtomSeqnmbOfAtmtxt(grp2atm2nam,False)
            self.mol.AddBond(grp1atm2,grp2atm2,1) # bond multiplicty=1
            connectedlst.append([grp1atm2,grp2atm2])
        #
        self.mol.atm[grp1atm2].atmtxt=''
        self.mol.atm[grp2atm2].atmtxt=''
        #
        return connectedlst

    def FindAtomSeqnmbOfAtmtxt(self,atmtxt,reset=True):
        seqnmb=-1
        for atom in self.mol.atm:
            if atom.atmtxt == atmtxt:
                seqnmb=atom.seqnmb; break
        if reset and seqnmb >= 0: self.mol.atm[seqnmb].atmtxt=''
        return seqnmb
        
    def ConnectGroupsType2(self,atm1,atm2,grpnam,grpatmlst,select=True):
        """ connect two sites within a group, -A-H and B- -> -A-B- """
        def Message():
            mess='Sorry, I can not treat this case.'
            lib.MessageBoxOK(mess,'Model(ConnectGroupsType2)')
        #
        connectedlst=[]
        # find shared heavy atom
        atm3=-1
        for i in grpatmlst:
            atom=self.mol.atm[i]
            if atm1 in atom.conect and atm2 in atom.conect:
                atm3=atom.seqnmb; break
        if atm3 < 0:
            #mess='Sorry, I can not treat this case.'
            #lib.MessageBoxOK(mess,'Model(ConnectGroupsType2)')
            Message()
            return connectedlst
        
        atm1cc=numpy.array(self.mol.atm[atm1].cc)
        atm2cc=numpy.array(self.mol.atm[atm2].cc)
        atm3cc=numpy.array(self.mol.atm[atm3].cc)
        #
        atm3c=[]
        for i in self.mol.atm[atm3].conect:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.elm == ' H': continue
            atm3c.append(atom.seqnmb)
        if len(atm3c) <= 0:
            Message()
            return connectedlst
        atm2c=[]
        for i in self.mol.atm[atm2].conect:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.seqnmb == atm3: continue
            atm2c.append(atom.seqnmb)
        self.mol.DelBond(atm2,atm3)
        for i in atm3c: self.mol.DelBond(atm3,i)
        
        movatmlst=[]
        grpdic=self.FindConnectedGroup()
        for ig,atmlst in grpdic.iteritems():
            if atm2 in atmlst:
                movatmlst=atmlst; break
        movatmlst.append(atm2)
        cc=[]
        for i in movatmlst:
            tmpcc=self.mol.atm[i].cc
            cc.append([tmpcc[0],tmpcc[1],tmpcc[2]])
        
        #self.mol.AddBond(atm2,atm3)
        for i in atm3c: self.mol.AddBond(atm3,i)
        for i in atm2c: self.mol.AddBond(atm1,i)
        #
        if len(movatmlst) <= 2: # needs atoms other than atm2,atm3
            Message()
            return []
        
        vec13=atm1cc-atm3cc
        vec23=atm2cc-atm3cc
        da=lib.AngleT(vec13,vec23)
        ax=lib.NormalVector(atm1cc,atm2cc,atm3cc) # (atm2cc,atm1pos,atm3cc
        u=lib.RotMatAxis(ax,da)
        cc=lib.RotMol(u,atm3cc,cc)
        ii=-1
        for i in movatmlst: 
            ii += 1
            self.mol.atm[i].cc=cc[ii]
        #
        dellst=[atm2]; atmlst=[atm1,atm2]
        for i in range(2):
            for j in self.mol.atm[atmlst[i]].conect:
                if self.mol.atm[j].elm == ' H':
                    dellst.append(j); break
        dellst.sort()
        self.mol.DelAtoms(dellst)
        connectedlst=[atm1,atm3]
       
        return connectedlst
               
    def FindContactGroupsIn2D(self,delta=5):
        """
        
        :param int delta: pixel number
        """
        if not self.winctrl.IsOpened('ModelBuilderWin'): return []
        
        grppairlst=[]
        delta2=delta*delta
        grplst=self.ListGroupName()
        ngrp=len(grplst)
        if len(grplst) <= 0: return
        # group pair loop
        for ig in range(ngrp-1):
            grp1=grplst[ig]
            short=False
            grplst1=self.ListGroupAtoms(grp1)
            for jg in range(ig+1,ngrp):
                grp2=grplst[jg]
                grplst2=self.ListGroupAtoms(grp2)
                for i in grplst1:
                    cc=self.mol.atm[i].cc[:]
                    ax,ay,az=self.mdlwin.draw.GetRasterPosition(cc[0],cc[1],
                                                                cc[2])
                    for j in grplst2:
                        cc=self.mol.atm[j].cc[:]
                        bx,by,bz=self.mdlwin.draw.GetRasterPosition(cc[0],cc[1],
                                                                    cc[2])
                        r2=(ax-bx)**2+(ay-by)**2
                        if r2 < delta2: short=True
            if short: grppairlst.append([grp1,grp2])
        return grppairlst

    def FindRotatableBonds(self,exclude=True):
        """ Find rotable bonds
        
        :param bool exclude: True for excluding multiple bonds, False for all 
                             bonds
        :return: bondlst - [[i(int),j(int)],...]
        """
        sellst=self.ListTargetAtoms()
        if len(sellst) <= 0: return
        donedic={}; bondlst=[]
        for i in sellst:
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.elm == ' H': continue
            if len(atom.conect) <= 1: continue
            for j in range(len(atom.conect)):
                jj=atom.conect[j]
                atomj=self.mol.atm[jj]
                if atomj.elm == 'XX': continue
                if atomj.elm == ' H': continue
                if len(atomj.conect) <= 1: continue
                if donedic.has_key(str(i)+':'+str(jj)): continue
                if donedic.has_key(str(jj)+':'+str(i)): continue
                if exclude and atom.bndmulti[j] > 1: continue
                # delete bond i-j
                coni=atom.conect[:]; conj=atomj.conect[:]
                atom.conect.remove(jj)
                atomj.conect.remove(i)
                #
                grpdic=self.FindConnectedGroup()
                foundi=False; foundj=False
                for grpnmb,lst in grpdic.iteritems():
                    if i in lst:
                        igrp=grpnmb; foundi=True
                    if jj in lst:
                        jgrp=grpnmb; founj=True
                    if foundi and foundj: break
                if igrp != jgrp:
                    bondlst.append([jj,i])
                    donedic[str(i)+':'+str(jj)]=True
                # recover i-j bond    
                atom.conect=coni[:]
                atomj.conect=conj[:]
                
        return bondlst
                
    def CheckShortContact2(self,mol1,mol2):
        fromargs=False
        if mol1 == None:
            if not self.mdlargs.has_key('CheckShortContact2'): return
            mol1=self.mdlargs['CheckShortContact2'][0]
            mol2=self.mdlargs['CheckShortContact2'][1]
            fromarng=True
        nsht=0 #; rmin=10000.0
        try: # fortran module
            cc1=[]; cc2=[]; threshold=0.5
            natm1=0; natm2=0
            for atom in mol1:
                if atom.elm == 'XX': continue
                cc1.append(atom.cc); natm1 += 1
            for atom in mol2:
                if atom.elm == 'XX': continue
                cc2.append(atom.cc); natm2 += 1
            rmin=0.0; rmax=threshold
            cc1=numpy.array(cc1); cc2=numpy.array(cc2)
            nsht,iatm=fortlib.find_contact_atoms(cc1,cc2,rmin,rmax)
        except: # python code
            for atom1 in mol1:
                for atom2 in mol2:
                    cc1=atom1.cc
                    cc2=atom2.cc
                    r=lib.Distance(cc1,cc2)
                    if r < 0.5:
                        nsht += 1
                        # if r < rmin: rmin=r
        if fromargs: del self.mdlargs['CheckShortContact2']

        return nsht #,rmin

    def CheckShortContact(self,rmax,bell=False):
        npair=0 #; rmin=10000.0
        iatm=[]; jatm=[]; rij=[]
        test=True
        try: # fortran module
            cc=[]; natm=0
            for atom in self.mol.atm:
                if atom.elm == 'XX': continue
                cc.append(atom.cc); natm += 1
            rmin=0.0; iopt=0 # rerurn rij in distance
            cc=numpy.array(cc)
            npair,iatm,jatm,rij=fortlib.find_contact_atoms2(cc,rmin,rmax,0)
        except: # python code
            print 'Non-Fortran routine is executed!'
            for atom1 in self.mol.atm:
                if atom1.elm == "XX": continue
                for atom2 in self.mol.atm:
                    if atom2.elm == "XX": continue
                    if atom2.seqnmb >= atom1.seqnmb: continue 
                    cc1=atom1.cc
                    cc2=atom2.cc
                    r=lib.Distance(cc1,cc2)
                    if r < rmax:
                        npair += 1
                        iatm.append(atom1.seqnmb); jatm.append(atom2.seqnmb)
                        rij.append(r)
        # beep when short contacts are found
        if npair > 0 and bell: wx.Bell()
        
        return npair,iatm,jatm,rij

    def CheckAAResConect(self):
        discon=[]; first=True
        # make AA resdic
        for i in range(len(self.mol.atm)):    
            atom=self.mol.atm[i]
            res=atom.resnam
            if not const.AmiRes3.has_key(res): continue
            atm=atom.atmnam; nb=len(atom.conect)
            resnam=res+':'+str(atom.resnmb)+':'+atom.chainnam
            if atm == ' N  ' and first:
                first=False; continue
            if atm == ' N  ' and nb != 3:
                discon.append([atm,str(i+1),resnam])
            if atm == ' CA ' and nb != 4:
                discon.append([atm,str(i+1),resnam])
            if atm == ' C  ' and nb != 3:
                discon.append([atm,str(i+1),resnam])
        return discon

    def CheckAAResBond(self):
        discon=[]; first=True
        for i in range(len(self.mol.atm)):    
            atom=self.mol.atm[i]
            res=atom.resnam; atmnam=atom.atmnam
            con=atom.conect; nb=0
            for j in con:
                if self.mol.atm[j].elm != ' H': nb += 1
            if not const.AmiRes3.has_key(res): continue
            resnam=res+':'+str(atom.resnmb)+':'+atom.chainnam
            if atmnam == ' N  ' and first:
                first=False; continue            
            if atmnam == ' OXT': continue
            if atom.elm == 'XX': continue
            if atom.elm == ' H':
                if nb != 1: discon.append([atmnam,str(i+1),resnam])
                continue
            aabnddic=const.AmiResBndNmb[res]
            try:
                nbnd=aabnddic[atmnam]
                if nb != nbnd: discon.append([atmnam,str(i+1),resnam])
            except:
                mess='Unknown atom name '+atmnam+' in residue '+resnam
                self.ConsoleMessage(mess)
        return discon

    def MakeGroup(self,grpnam):
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            lib.MessageBoxOK("Select atoms for the group.","Model(MakeGroup)")
            return
        if len(grpnam) <= 0:
            grpnam=self.MakeDefaultGroupName()
            if self.winctrl.IsOpened('Open ControlWin'):
                self.winctrl.GetWin('Open ControlWin').DispGroupName(grpnam)
        for i in lst: self.mol.atm[i].grpnam=grpnam

    def MakeDefaultGroupName(self):
        ngrp,grpdic=self.MakeGroupDic(self.mol.atm)
        grpnam='grp'+('%03d' % (ngrp+1))
        return grpnam
   
    @staticmethod                
    def MakeGroupDic(atm):
        grpdic={}; ngrp=0
        for atom in atm:
            grpnam=atom.grpnam
            if not grpdic.has_key(grpnam):
                grpdic[grpnam]=ngrp; ngrp += 1
        return ngrp,grpdic
    
    def MakeResDatLst(self):
        resdatlst=[]; resdatdic={}    
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            resdat=lib.ResDat(atom)
            if resdatdic.has_key(resdat): continue
            else: resdatdic[resdat]=True; resdatlst.append(resdat)
        return resdatlst

    def MakeResAtmLst(self,resdat):
        resatmlst=[]   
        for i in xrange(len(self.mol.atm)):
            atom=self.mol.atm[i]
            res=lib.ResDat(atom)
            if res == resdat: resatmlst.append(i)
        return resatmlst
    
    def MakeSymbolicZmt(self):
        zmtdic={}
        
        # zmtdic=self.mol.zmtdic
        
        return zmtdic
    
    def PickUpResAtm(self,resdat):
        # resatm: mol data 
        # resdat: resnam:resnumb:chain
        resatm=[]
        for atom in self.mol.atm:
            res=lib.ResDat(atom)
            if res == resdat: resatm.append(atom)
        return resatm
    
    def MakeResAtmNamDic(self,resatm):
        # resatmnamdic: {atmnam:seq number of atoms,...}
        resatmnamdic={}
        for i in xrange(len(resatm)):
            resatmnamdic[resatm[i].atmnam]=i
        return resatmnamdic
    
    def Zoom(self,zoom):
        self.draw.Zoom(zoom)
        self.draw.Paint()
        ##if self.draw.IsDrawLabel('Message:MESSAGE'): self.DrawMol(True)
        #else: self.draw.Paint()
        #self.DrawMol(False)
    def ZoomByKey(self,case):
        """ zoom drawn molecule by keyboard key, '>' key for mgnify, '<' key for
                            reduce
        
        :param str case: 'magnify' or 'reduce'
        """
        speed=self.setctrl.GetParam('zoom-speed')
        if case == 'magnify': self.draw.Zoom(-speed)
        else: self.draw.Zoom(speed)
        self.draw.Paint()

    def Rotate(self,axis,rot):
        if axis == 'axis':
            pnts=self.mousectrl.GetRotationAxisPnts()
            if len(pnts) <= 0:
                self.SetRotationAxis()
                self.mousectrl.RecoverMouseMode()
                return
            ang=rot[0]*rot[0]+rot[1]*rot[1]
            if rot[0] < 0: ang=-ang
            if len(pnts) == 2:
                pnt1=pnts[0]; pnt2=pnts[1]    
                vec=[pnt2[0]-pnt1[0],pnt2[1]-pnt1[1],pnt2[2]-pnt1[2]]         
                rotmat=lib.RotMatAxis(vec,0.01*ang)
            else:
                pnt1=numpy.array(pnts[0])
                pnt2=numpy.array(pnts[1])
                pnt3=numpy.array(pnts[2])
                #cnt=pnt2[:]
                vec=lib.NormalVector(pnt1,pnt2,pnt3)
                pnt1=pnt2; vec=vec+pnt2; vec=vec-pnt1
                rotmat=lib.RotMatAxis(vec,0.01*ang)
                
            self.draw.RotateByMatrix(rotmat)
        else: 
            #pnts=self.mousectrl.GetRotationAxisPnts()
            #if len(pnts) >= 2: self.mousectrl.SetRotationAxisPnts(True,pnts)
            self.draw.MouseRotate(axis,rot)
            
        self.SetDrawItemsToSeriesMol()
        
        self.draw.Paint()
    
    def SetDrawItemsToSeriesMol(self):
        return
        
        
        seriesmol=self.molctrl.GetSeriesMolList()
        if self.mol in seriesmol:
            drawitems=self.mol.GetDrawItems()
        for mol in seriesmol:
            mol.SetDrawItems(drawitems)
            
    def Translate(self,tran):
        """ translate drawn molecule
        
        :param int tran: move length in pixels
        """
        self.draw.MouseTranslate(tran)
        self.draw.Paint()

    def TranslateByKey(self,case):
        """ translate drawn molecule by keyboard key, 'left arrow' key for 
         'leftward' 'right arrow' key for rightward, 'up arrow' key for upward,
         'down arrow' key for downward
        
        :param str case: 'up','down','left',or 'right'
        """
        tran=self.setctrl.GetParam('translate-speed')
        if case == 'up': self.Translate([0,-tran])       
        elif case == 'down': self.Translate([0,tran])   
        elif case == 'left': self.Translate([-tran,0])   
        else: self.Translate([tran,0])       
        
    def RotateSelected(self,axis,dif):
        """ rotate selected atoms. note that the coordinates will be changed.
        
        :param str axis: 'free', 'inplane', 'axis', 'x','y', or 'z'
        :param int dif: angles to rotate in pixels
        """
        # dif=[dx,dy]
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0: 
            mess='No selected atoms for move.'
            lib.MessageBoxOK(mess,'Model(RotateSelected)')
            return
        vecdic={'x':[1.0,0.0,0.0],'y':[0.0,1.0,0.0],'z':[0.0,0.0,1.0]}
        cntr=self.draw.GetCenter() #center
        agl=dif[0]*dif[0]+dif[1]*dif[1] # rotation angles
        if dif[0] < 0: agl=-agl
        #if self.mousectrl.GetMdlMode() == 5:
        #    self.TextMessage('[Change geometry]: move selected atoms ...'+axis,'yellow')
            #self.mdlwin.ChangeMouseModeWinBGColor('pale green')
        #
        if axis == 'free':
            vec=self.MouseMoveVector(dif)
            u=self.MouseRotMatrix(vec,dif)
        elif axis == 'inplane':
            eye,ctr,upw,ratio=self.draw.GetViewParams()
            vec=numpy.array(eye)*dif[0]
            u=self.MouseRotMatrix(vec,dif)
        elif axis == 'axis': # axis defined by two atoms
            pnts=self.mousectrl.GetRotationAxisPnts()[:]
            if len(pnts) <= 1: 
                mess='Rotation axis points are not defined. Select two atoms '
                mess=mess+'and try again.'
                self.Message(mess,0,'')
                return
            elif len(pnts) == 2:
                pnt1=numpy.array(pnts[0])
                pnt2=numpy.array(pnts[1])
                vec=[pnt2[0]-pnt1[0],pnt2[1]-pnt1[1],pnt2[2]-pnt1[2]]
                u=lib.RotMatAxis(vec,0.01*agl)
                cnt=pnt1[:]
            else: # three points
                pnt1=numpy.array(pnts[0])
                pnt2=numpy.array(pnts[1])
                pnt3=numpy.array(pnts[2])
                cnt=pnt2[:]
                vec=lib.NormalVector(pnt1,pnt2,pnt3)
                pnt1=pnt2; vec=vec+pnt2; vec=vec-pnt1
                u=lib.RotMatAxis(vec,0.01*agl)
        else: # axis='x','y', or 'z'
            vec=vecdic[axis]
            u=lib.RotMatAxis(vec,0.01*agl)
        #        
        u=numpy.array(u)
        coord=[]; cx=0.0; cy=0.0; cz=0.0
        for i in lst:
            atom=self.mol.atm[i]
            coord.append([atom.cc[0],atom.cc[1],atom.cc[2]])
        try: xyz=lib.RotMol(u,cnt,coord)
        except:
            mess='Rotation center is not set. If you are using "Bond Rorater",'
            mess=mess+' Please push the "On" button.'
            lib.MessageBoxOK(mess,'Model(RotateSelected)')
            return
        ii=0
        for i in lst:
            atom=self.mol.atm[i]
            atom.cc[0]=xyz[ii][0]; atom.cc[1]=xyz[ii][1]; atom.cc[2]=xyz[ii][2]
            ii += 1
        #        
        drwlabel='draw-torsion-angle'
        if self.setctrl.GetParam(drwlabel):
            """ does not work! 22Jan2016 """
            atms=self.mousectrl.GetRotationAxisAtoms()
            atoms=[]
            if len(atms) == 2:
                pnts4=self.Find14Atoms(atms[0],atms[1])      
                p1=pnts4[0]; p2=pnts4[1]; p3=pnts4[2]; p4=pnts4[3]
                ang=self.TorsionAngle(p1,p2,p3,p4,deg=True)
                angtxt='%5.1f' % ang
                text='[Torsion angle] '
                text=text+str(p1+1)+'-'+str(p2+1)+'-'+str(p3+1)+'-'+str(p4+1)
                text=text+'='+'%5.1f' % ang
                self.TextMessage(text,drw=False)
                atmlst=[p1,p2,p3,p4]
                nlbl,drwlst=self.MakeDrawLabelAtomData('Atom number',
                                                           atmlst=atmlst)
                self.draw.SetDrawData(drwlabel,'LABEL',drwlst)        
                
        # check short contact
        varnam='beep-short-contact'
        rmax=self.setctrl.GetParam(varnam)
        if rmax > 0:
            rmax=self.ctrlflag.Get(varnam)
            npair,iatm,jatm,rij=self.CheckShortContact(rmax,bell=True)        
        #if axis == 'axis': self.NotifyToSubWin('RotateSelected')
    
        self.DrawMol(True)

    def TranslateSelected(self,dif,drw=True):
        """ translate selected atoms. note that the coordinates will be changed.
        
        :param lst dif: move vector, [delta x(int), delta y(int)], delta's in 
                        pixels
        """
        # dif=[dx,dy]
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0: 
            mess='No selected atoms.'
            self.Message(mess,0,'')
            return
        #if self.mousectrl.GetMdlMode() == 5:
        #    self.TextMessage('[Change geometry]: move selected atoms','yellow')
        mov=self.MouseMoveVector(dif)
        for i in lst:
            atom=self.mol.atm[i]
            atom.cc[0] += mov[0]; atom.cc[1] += mov[1]; atom.cc[2] += mov[2]

        if self.ctrlflag.IsDefined('draw-distance'): self.SetDrawDistanceData()
        #drwlab='draw-torsion-angle'
        #if self.ctrlflag.IsDefined(drwlab): 
        #    self.draw.SetDrawData(drwlab,'LABEL',[])         
        if drw: self.DrawMol(True)
    
    def MouseMoveVector(self,dif):
        """ calculate orthnormal vector of mouse move
        
        :param lst dif: mouse move distance, [delta x(int),delta y(int)].
        :return: orthogonal vector of mouse move, [x(float),y(float)]
        :rtype: lst
        """
        dif[1] = -dif[1]
        eye,ctr,upw,ratio=self.draw.GetViewParams()
        ctr=numpy.array(ctr); eye=numpy.array(eye); upw=numpy.array(upw)
        ec = ctr - eye
        # x unit vector in canvas
        nvc = numpy.cross(ec, upw)
        nvc /= numpy.linalg.norm(nvc)
        # moved vector
        vec = (nvc * dif[0] + upw * dif[1]) * ratio
        return vec

    def MouseRotMatrix(self,vec,dif):
        """ transformation matrix for rotation around 'vec'
        
        :param lst vec: axis vector, [x(float),y(float),z(float)]
        :param lst dif: mouse movement vector, [xmov(int),ymov(int)]
        :return: 3*3 matrix, [[[v11(float),v12(float),.]..,[...,v33(float)]]]
        :rtype: lst
        :seealso: lib.RotMatAxis()
        """
        nrm=dif[0]*dif[0]+dif[1]*dif[1]
        if nrm < 0.00000001: return numpy.identity(3,numpy.float64)
        PI2=numpy.pi*2.0
        t = numpy.sqrt(dif[0]*dif[0]+dif[1]*dif[1])*PI2/360.0
        rotmat=lib.RotMatAxis(vec,t)
        return rotmat
    
    def ChangeMolName(self,filename):
        ###if self.molmolnam[0:4] != 'temp': return
        newnam=molec.Molecule.MakeMolNameWithExt(filename)
        self.RenameMolecule(self.mol.name,newnam)

    def RenameMolecule(self,oldnam,newnam):
        """ rename molecule
        
        :param str oldnam: old name
        :param str newnam: new name
        """
        idx=self.molctrl.GetMolIndex(oldnam)
        if idx >= 0:
            self.molctrl.ChangeName(oldnam,newnam)
        else:
            mess='Error(RenameMolecule): molecule name '+oldnam+' is not found.'
            self.Message(mess,0,'')
    
    def RenameGroup(self,oldnam,newnam):
        for atom in self.mol.atm:
            if atom.grpnam == oldnam: atom.grpnam=newnam
        
    def ReadBDADat(self,filename):
        """ Read BDA file and make fragments for FMO
        
        :param str filename: file name
        """
        molnam,bdalst=rwfile.ReadBDADatFile(filename)
        self.bdadatdic[molnam]=bdalst
        #
        self.FragmentByBDADat()
    
    #@lib.LOGGINGFUNCTIONCALL
    def ReadFiles(self,filename,draw,logging=True,drop=False):
        #self.moldrw.SetUpDraw(self.filename
        #if self.ctrlflag.GetCtrlFlag('exeprgwin'):
        #    if self.exeprgwin.GetComputeStatus() and len(self.pdir) > 0:
        #        os.chdir(self.curdir)
        if len(filename) <= 0: return
        
        #lst=lib.ReplaceBackslash([filename])
        #filename=lst[0]
        # check file extension
        root,ext=os.path.splitext(filename)
        if not lib.IsLowerCase(ext):
            mess='Please use lower case for file extension in FU'
            mess=mess+', "'+ext+'" -> '+'"'+ext.lower()+'".'
            lib.MessageBoxOK(mess,'Model(ReadFiles)')
            return
        
        self.mdlwin.BusyIndicator('On','Reading ..')
        #
        self.filehistory.Push(filename)
        try: self.menuctrl.RemoveMenuItem('File history')
        except: pass
        self.menuctrl.CreateFileHistoryMenuItems()
        # write log file
        #if self.setctrl.GetParam('save-log'): #self.setctrl.GetParam('save-log'):
        #    drawtxt='False'
        #    if draw: drawtxt='True'
            #file=lib.ReplaceBackslash(filename)
            ###mess='fum.ReadFiles("'+file+'",'+drawtxt+")"
            ###const.LOGDEV.write(mess+'\n\n')    
        #
        if not drop:
            curdir=os.getcwd()
            os.path.join(curdir,filename)
            root,ext=os.path.splitext(filename)
            curdir=lib.GetFileNameDir(filename)
            if os.path.isdir(curdir):
                self.curdir=curdir
                os.chdir(self.curdir)
        else: root,ext=os.path.splitext(filename)
        #
        donedrw=False
        if ext == '.fuf' or ext == '.spl' or ext == '.mrg':
            filelst=self.ReadFilesFuf(filename)
            if len(filelst) <= 0:
                self.Message('no files in fuf file. skipped.',0,'')
            else:
                if ext == '.mrg':
                    self.ReadFilesPDB(filelst[0],True)
                    for i in range(1,len(filelst)):
                       self.MergeToCurrent(filelst[i],False) 
                else:
                    for file in filelst:
                        base,fufext=os.path.splitext(file)
                        if fufext == '.pdb' or ext == '.ent':
                            self.ReadFilesPDB(file,True)
                        elif fufext == '.frm':
                            resnam,condat=rwfile.ReadFrameFile(file)
                            #self.framedatdic[resnam]=condat
                            self.setctrl.SetFrameData(resnam,condat)
                        elif fufext == '.frg':
                            pass # to be coded
                        elif fufext == '.bda':
                            pass # to be coded
            self.mdlwin.BusyIndicator('Off')
            return
        
        elif ext == '.pdb' or ext == '.ent':
            self.ReadFilesPDB(filename,True)
            self.NotifyToSubWin('ReadFiles')
            self.mdlwin.BusyIndicator('Off')
            return
        elif ext == '.xyz' or ext =='.xyzfu' or ext == '.tin' \
                 or ext == '.inp' or ext == '.mol' or ext == '.zmt' or \
                 ext == '.zmtfu':
            mess='Read file='+filename
            #self.mdlwin.SetTitle(self.title + '   [' + filename + ']')
            #self.shlwin.MessWinMess(mess,'black')
            self.Message(mess,0,'black')
            
            self.ConsoleMessage(mess)
            
            if ext == '.xyz': self.BuildMol('xyz',filename)
            elif ext == '.xyzfu': self.BuildMol('xyz',filename)
            elif ext == '.tin': self.BuildMol('tin',filename)
            elif ext == '.inp': self.BuildMol('inp',filename)
            elif ext == '.mol': self.BuildMol('mol',filename)
            elif ext == '.zmt': self.BuildMol('zmt',filename,addbond=True)  
            elif ext == '.zmtfu': self.BuildMol('zmtfu',filename)
            if self.curmol < 0: self.curmol=0
            else:
                nmol=self.molctrl.GetNumberOfMols() #len(self.molnam)
                self.curmol=nmol-1
            self.curmol,self.mol=self.molctrl.GetCurrentMol()
            if ext == '.inp': 
                self.AddBondUseBondLength()
                self.menuctrl.OnFMO("BDA points",True) # does not work
            #   
            if draw and not donedrw:
                # done in setupdraw self.FitToScreen(False)
                self.SetUpDraw(True)
                self.DrawMol(True)
                donedrw=True
                self.mol.SetDrawObjs(self.draw.GetDrawObjs())
                self.mol.SetViewItems(self.draw.GetViewItems())
                if ext == '.inp': self.menuctrl.OnFMO("BDA points",True)
            
            self.NotifyToSubWin('ReadFiles')
            ###return
        elif ext == '.sdf':
            self.BuildMolFromSDFFile(filename)
            self.NotifyToSubWin('ReadFiles')
        elif ext == '.xyzs':
            #print 'xyzs file',filename
            self.BuildMolFromXYZsFile(filename)
            self.NotifyToSubWin('ReadFiles')
            #return
        elif ext == '.frm':
            resnam,condat=rwfile.ReadFrameFile(filename)
            #self.framedatdic[resnam]=condat
            self.setctrl.SetFrameData(resnam,condat)
            mess='Frame data is read. file='+filename
            self.ConsoleMessage(mess)
            self.mdlwin.BusyIndicator('Off')
            return
        elif ext == '.frg':
            if not self.mol: return
            natm=len(self.mol.atm)
            try: 
                resnam,bdalst,frgchglst,frgnamlst= \
                                           rwfile.ReadFrgDatFile(filename,natm)
            except:
                mess='Failed to apply fragment data. frgfile='+filename
                self.ConsoleMessage(mess)
                self.mdlwin.BusyIndicator('Off')
                return               
            self.SetBDAToWrkMol(resnam,bdalst)
            self.SetFrgNamToWrkMol(frgnamlst)                
            self.mol.SetFragmentCharge(frgchglst) # newly added
            self.mol.CreateFrgConDat()
            if self.ctrlflag.Get('drawbda'):
                self.DrawBDAPoint(True)
            mess='Read '+filename+'.\n'
            mess=mess+'Number of BDAs='+str(len(bdalst))+'\n'
            mess=mess+'Number of fragments='+str(self.CountFragments())
            #self.Message2(mess) #,0,'')
            self.ConsoleMessage(mess)
            self.mol.SetDrawObjs(self.draw.GetDrawObjs())
            self.mol.SetViewItems(self.draw.GetViewItems())
            
            self.mdlwin.BusyIndicator('Off')
            return
        #elif ext == '.bda':
        #    if not self.mol: return
        #    self.LoadBDABAA(filename)
        #    bdalst=self.ListBDABAA()
        #    mess='Read file '+filename+'. '+str(len(bdalst))
        #    mess=mess+' BDA points were set.\n'
            #self.Message2(mess)
        #    mess=mess+'Number of BDAs='+str(len(bdalst))+'\n'
        #    mess=mess+'Number of fragments='+str(self.CountFragments())
        #    self.ConsoleMessage(mess)
        #    return

        else:
            mess='The extension is not defined in fumodel. File= '+filename+'.'              
        
        self.mdlwin.BusyIndicator('Off')
        self.ctrlflag.Set('ready',True)

    def BuildMolFromSDFFile(self,filename):
        #xyzmol,bond,resfrg=rwfile.ReadXYZMol(filename)
        moldatlst=rwfile.ReadMolFile(filename)
        self.BuildMultipleMols(moldatlst,filename,moldattyp='sdf',addbond=False)
    
    def BuildMolFromXYZsFile(self,filename):
        #xyzmol,bond,resfrg=rwfile.ReadXYZMol(filename)
        xyzmollst=rwfile.ReadXYZsMol(filename)
        self.BuildMultipleMols(xyzmollst,filename,moldattyp='xyz')

    def BuildMolFromXYZs(self,xyzmollst,filename,drw=True):    
        bond=[]; resfrg=[]; seriesmol=[]
        idat=0; nmol=0
        for xyzmol in xyzmollst: 
            if len(xyzmol) <= 0: continue
            idat += 1
            mol=molec.Molecule(self) 
            mol.SetXYZAtoms(xyzmol,bond,resfrg)
                
            molnam=molec.Molecule.MakeMolNameWithExt(filename)
            mol.name=molnam+'#'+str(idat)
            mol.inpfile=filename
            mol.AddBondUseBL([])
            # register new mol to MolCtrl
            self.molctrl.Add(mol,mess=False)
            #
            self.curmol,self.mol=self.molctrl.GetCurrentMol()
            self.SetUpDraw(True)
            self.DrawMol(True)
            drwobjs=self.draw.GetDrawObjs()
            self.mol.SetDrawObjs(drwobjs)
            viewitems=self.draw.GetViewItems()
            self.mol.SetViewItems(viewitems)
            
            seriesmol.append(mol)
            # clear self.savecc
            self.savatmcc.Clear()
            nmol=self.molctrl.GetNumberOfMols()
            if nmol > 0: self.menuctrl.EnableMenu(True)

        self.curmol,self.mol=self.molctrl.GetCurrentMol()
        mess='Number of coordinate data in "'+filename+'"='+str(nmol)
        self.Message2(mess)
        
        self.molctrl.SetSeriesMolList(seriesmol)
        if self.curmol < 0: self.curmol=0
        else:
            nmol=self.molctrl.GetNumberOfMols() #len(self.molnam)
            self.curmol=nmol-1
        
        #if draw and not donedrw:
        # done in setupdraw self.FitToScreen(False)
        self.SetUpDraw(True)
        if drw: self.DrawMol(True)
            
    def BuildMultipleMols(self,moldatlst,filename,moldattyp='xyz',addbond=True):
        """ Build multiple mol objects
        
        :param str moldattyp: 'xyz' or 'sdf'
        """
        bond=[]; resfrg=[]; seriesmol=[]
        idat=0; nmol=0
        for moldat in moldatlst: 
            if len(moldat) <= 0: continue
            idat += 1
            mol=molec.Molecule(self) 
            if moldattyp == 'xyz': 
                mol.SetXYZAtoms(moldat,bond,resfrg)        
                molnam=molec.Molecule.MakeMolNameWithExt(filename)
                mol.name=molnam+'#'+str(idat)                
            elif moldattyp == 'sdf':
                title=moldat[0]; molatm=moldat[3]
                mol.SetMolAtoms(molatm)
                mol.inpfile=filename; mol.name=title
            mol.inpfile=filename
            if addbond: mol.AddBondUseBL([])
            # register new mol to MolCtrl
            self.molctrl.Add(mol,mess=False)
            #
            self.curmol,self.mol=self.molctrl.GetCurrentMol()
            self.SetUpDraw(True)
            self.DrawMol(True)
            drwobjs=self.draw.GetDrawObjs()
            self.mol.SetDrawObjs(drwobjs)
            viewitems=self.draw.GetViewItems()
            self.mol.SetViewItems(viewitems)
            
            seriesmol.append(mol)
            # clear self.savecc
            self.savatmcc.Clear()
            nmol=self.molctrl.GetNumberOfMols()
            if nmol > 0: self.menuctrl.EnableMenu(True)

        self.curmol,self.mol=self.molctrl.GetCurrentMol()
        mess='Number of molecule data in "'+filename+'"='+str(nmol)
        self.Message2(mess)
        
        self.molctrl.SetSeriesMolList(seriesmol)
        if self.curmol < 0: self.curmol=0
        else:
            nmol=self.molctrl.GetNumberOfMols() #len(self.molnam)
            self.curmol=nmol-1
        
        #if draw and not donedrw:
        # done in setupdraw self.FitToScreen(False)
        self.SetUpDraw(True)
        self.DrawMol(True)
        
            
    def ReadFilesFuf(self,fuffile):
        filelst=[]
        f=open(fuffile,'r')
        for s in f.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s[:1] == '#': continue
            ns=s.find('#') 
            if ns >= 0: s=s[:ns]
            s=s.strip()
            if len(s) <= 0: continue
            filelst.append(s)
        f.close()
        
        return filelst
     
    def ReadFilesPDB(self,filename,draw):
        donedrw=False
        if not os.path.isfile(filename):
            mess='file not found. file='+filename
            self.Message(mess,0,'')
            self.ConsoleMessage(mess)
            return
        mess='Read file='+filename
        #self.mdlwin.SetTitle(self.title + '   [' + filename + ']')
        self.Message(mess,0,'black')          
        self.ConsoleMessage(mess)
        #
        info,missatoms=rwfile.ReadPDBMissingAtoms(filename)
        if len(missatoms) > 0:
            mess='PDB info: there are '+str(len(missatoms))
            mess=mess+' missing atom residues!'
            self.ConsoleMessage(mess)
        #missres=molec.Molecule.ReadPDBMissingResidues(filename)
        info,missres=rwfile.ReadPDBMissingResidues(filename)
        if len(missres) > 0:
            mess='PDB info: there are '+str(len(missres))+' missing residues!'
            self.ConsoleMessage(mess)
        #ssbond=molec.Molecule.ReadPDBSSBonds(filename)
        ssbond=rwfile.ReadPDBSSBonds(filename)
        if len(ssbond) > 0:
            interss=0
            for i in range(len(ssbond)):
                if ssbond[i][0] != ssbond[i][3]: interss += 1 
            mess="PDB info: there are "+str(len(ssbond))+" SS bonds."
            if interss > 0:
                mess=mess+" Number of inter-chain SS bonds= "+str(interss)
            self.ConsoleMessage(mess)
        self.BuildMol('pdb',filename)
        self.curmol,self.mol=self.molctrl.GetCurrentMol()
        #
        if len(missatoms) > 0 or len(missres) > 0:
            lib.MessageBoxOK("PDB info: there are missing atoms/residues.","")
        # check atmnam
        if self.setctrl.GetParam('check-pdb-atmnam'):
            ans=self.IsPDBAtmNamNew()
            if not ans:
                self.ChangeAtmNamToNew()
                mess='atmnam is old type. Converted to new one.\n'
                mess=mess+'If you save the file, atmnams are replaced with new.'
                lib.MessageBoxOK(mess,'Model(ReadFilesPDB)')
        # delete TERS
        if self.setctrl.GetParam('auto-del-ters'): self.DeleteAllTers()
        #
        if self.setctrl.GetParam('auto-add-hydrogens'): #self.autoaddhydrogen:
            # add hydrogen to polypeptide
            nres=self.mol.CountAAResAtoms()
            err=0
            if nres > 0:
                cpy=self.mol.CopyMolecule()
                # python code -> fortran
                # comment self.DeleteBondBetweeNC
                # comment nw=self.mol.CountWater()
                # comment if nw > 0: AddHydrogenToWaterMol()
                # change ctrl module, if item == "H and bond to AA residue": 
                #                  to Fortran code
                #err=self.mol.AddHydrogenToProtein([])
                err=0
                #if self.usefmoutil: self.OpenAddHydrogenWin(False)
                if self.setctrl.GetParam('use-fmoutil'):
                    scrdir=self.setctrl.GetDir('Scratch') 
                    print 'scrdir',scrdir
                    self.winctrl.OpenAddHydrogenWin(scrdir)
                else: err=self.mol.AddHydrogenToProtein([])
                print 'addhydroegen'
                if err == 1:
                    mess="Program error: unable to treat multiple peptide"
                    mess=mess+" chains. "
                    self.Message(mess,0,"")
                    self.mol=cpy

                if self.setctrl.GetParam('tinker-atom-order'): #'self.tinkeratomorder:
                    self.ReorderHydrogensIntoTinker()
                if self.setctrl.GetParam('tinker-atom-name'): #self.tinkeratmnam:
                    self.RenameAtmNamIntoTinker()
                
            self.MsgNumberOfAtoms(1)
            donedrw=False
            ###self.DrawMol(True)
            
        if self.setctrl.GetParam('tinker-atom-order'): #self.tinkeratomorder:
            self.ReorderHydrogensIntoTinker()
            #print 'tinekrorder'
        if self.setctrl.GetParam('tinker-atom-name'): #self.tinkeratmnam:
            self.RenameAtmNamIntoTinker()
            #print 'tinker name'
        if draw and not donedrw: # and not donedrw:
            #print 'DrawMol in PDB'
            self.SetUpDraw(True)
            self.mol.SetDrawObjs(self.draw.GetDrawObjs())
            self.mol.SetViewItems(self.draw.GetViewItems())
                  
    def AutoAddHydrogens(self,on):
        """ use 'SetParam' """
        #self.autoaddhydrogen=on # on: [True/False]
        self.setctrl.SetParam('auto-add-hydrogens',on)
        
    def UseFMOUtil(self,on):
        """ use 'SetParam' """
        self.setctrl.SetParam('use-fmoutil',on)
    
    def UpdateMol(self,mol):
        for atom in mol:
            for j in xrange(len(atom.conect)):
                atom.conect[j] += 1

    def WriteAllAs(self,filetype,savedir):
        """ Save all molecules  
        
        :param str filetype: "pdb files","mol files",...
        :param str savedir: directory name to make files
        """
        fileextdic={"pdb files":".pdb","mol files":".mol","sdf files":".sdf",
                 "xyz files":".xyz","xyzs files":".xyzs","xyzfu files":".xyzfu",
                 "zmt files":".zmt","zmtfu files":"zmtfu"}
        if not os.path.isdir(savedir):
            mess='Not found directory='+savedir+'.\n'
            mess=mess+'Would you like to ctreate it?'
            ans=lib.MessageBoxYesNo(mess,'Model(WriteAllAs)')
            if not ans: return
            else: os.mkdir(savedir)
        #
        nmol=self.molctrl.GetNumberOfMols()
        for i in range(nmol):
            mol=self.molctrl.GetMol(i)
            filename=mol.inpfile
            head,tail=os.path.split(filename)
            base,ext=os.path.splitext(tail)
            filename=base+fileextdic[filetype] #'.pdb'
            filename=os.path.join(savedir,filename)
            #mol.WritePDBMol(filename,"","",True)
            self.WriteFiles(filename,False,True,mol) # save=True, all=True, nolobj=mol
            #mess='Save file='+filename
            #self.ConsoleMessage(mess)

    def WriteFiles(self,filename,save,all,molobj=None,check=True):
        # save=True for "Save" and =False for "Save As"
        # all: True for all atoms, False for selected atoms only
        extlst=['.gz','.ent','.pdb','.xyz','.xyzfu','.xyzs','.tin','.mol',
                '.zmt','.zmtfu','.drwpic']
        if molobj == None: molobj=self.mol
        if len(filename) <= 0: filename=molobj.inpfile
        #
        gzfile=''
        root,ext=os.path.splitext(filename)
        if not ext in extlst:
            mess='Not supported file descriptor. ext='+ext
            lib.MessageBoxOK(mess,'Model(WriteFiles)')
            return
        # gz file ?
        if ext == '.gz':
            gzfile=filename
            filename=root
        #
        if save:
            filename=molobj.inpfile
            root,ext=os.path.splitext(filename) 
            self.Message('Save file='+filename,0,'black')
        """
        else: # SaveAs:
            self.Message('Save as file='+filename,0,'black')
            exist=os.path.exists(filename)
            if exist and check:
                retcode=lib.MessageBoxYesNo("%s ... file alredy exist. Overwrite?" % filename,'')
                #if dlg.ShowModal() != wx.ID_YES:
                if not retcode: return
                #if dlg != wx.ID_YES:
                #    dlg.Destroy(); return
        """
        # need to keep current mol data
        tmp=molobj.CopyMolecule()
        if ext == '.ent' or ext == '.pdb':
            if all:
                molobj.RenumberConDat()
                molobj.WritePDBMol(filename,"","",True)
            else:
                pass # to be coded here
                
        elif ext == '.xyz' or ext == '.xyzfu':
            self.DeleteAllTers()
            molobj.RenumberConDat()
            if ext == '.xyzfu': molobj.WriteXYZMol(filename,True,False)
            elif ext == '.xyz': molobj.WriteXYZMol(filename,False,False)
        elif ext == '.xyzs': self.WriteXYZs(filename)
        elif ext == '.tin':
            self.DeleteAllTers()
            molobj.RenumberConDat()
            molobj.WriteTinkerXYZ(filename)
        elif ext == '.mol':
            if len(molobj.atm) < 1000:
                molobj.WriteMolMol(filename,resnam='',title='',comment='')
            else: lib.MessageBoxOK('Too many atoms. Max=1000','WriteFiles')
        elif ext == '.zmt' or ext == '.zmtfu':
            title=molobj.name+' '+lib.DateTimeText()
            zelm,zpnt,zprm=lib.CCToZM(molobj)
            extdat=[]  
            if ext == '.zmtfu':
                for atom in molobj.atm:
                    extdat.append([atom.atmnam,lib.ResDat(atom),atom.conect,
                                   atom.bndmulti])
            zvardic={}; activedic={}
            rwfile.WriteZMTFile(filename,title,zelm,zpnt,zprm,zvardic=zvardic,
                                extdat=extdat)
        #    
        molobj.atm=tmp.atm
        molobj.outfile=filename
        # save draw items
        if self.setctrl.GetParam('dump-draw-items'): #self.dumpdrw:
            drwfile=filename.replace(ext,'.drwpic')
            self.DumpDrawItems(drwfile)                    
        # change current directory
        curdir=lib.GetFileNameDir(filename)
        if os.path.isdir(curdir):
            self.curdir=curdir; os.chdir(self.curdir)
        #
        if gzfile != '':
            if os.path.exists(filename):
                mess=''
                retcode=lib.ZipUnzipFile(filename,True,delinpfile=True,
                                         check=True,message=True)          
            else: 
                mess='Faled to make plane file="'+filename+'" and gzfile="'
                mess=mess+gzfile
        else: mess='Saved file='+filename
        if len(mess) > 0: self.ConsoleMessage(mess)

    def WriteXYZs(self,filename):
        """ Write xyzs file
        
        :param str filename: filename
        :param bool bond: True for write bond data, False do not
        """
        blk=' '; blk2=2*blk; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'
        ff8='%8.3f'; ff6='%6.2f'
        ff12='%12.6f'; sq="'"; non="'None'"
        d=datetime.datetime.now()
        #
        f=open(filename,'w')
        nmol=self.molctrl.GetNumberOfMols()
        for i in range(nmol):
            molobj=self.molctrl.GetMol(i)
            mess=' xyz file: Created by fu. DateTime='
            s=str(i)+mess+lib.DateTimeText()+'\n'  #'\r'+'\n'
            f.write(s); f.write('\n')
            # label,elm,x,y,z
            for atom in molobj.atm:
                #s=blk*80
                s=''
                s=s+(fi5 % (atom.seqnmb)) # label
                s=s+blk2+atom.elm # elm
                s=s+ff12 % atom.cc[0] # x
                s=s+ff12 % atom.cc[1] # y
                s=s+ff12 % atom.cc[2] # z
                s=s+'\n'
                f.write(s)
            f.write('\n')
        f.close()

    def RemoveMol(self,allmol):
        #Remove molecule
        #if len(self.molnam) <=0: return
        if allmol: # remove all molecules
            self.molctrl.ClearMol()
            self.Message("All molecules are removed.",1,'black')
            self.curmol,self.mol=self.molctrl.GetCurrentMol()
            #self.SetCurrentMol(curmol,mol)
            #self.SetUpDraw(False)
            #self.DrawMol(True)
        else: # remove current molecules
            delmol=self.mol.name
            self.molctrl.Del(self.curmol)  # delete first
            self.curmol,self.mol=self.molctrl.GetCurrentMol()
            if self.curmol < 0:
                self.molctrl.ClearMol()
                self.curmol,self.mol=self.molctrl.GetCurrentMol()
                #self.SetCurrentMol(curmol,mol)
                #self.SetUpDraw(False)
                #self.DrawMol(True)
                self.Message(delmol+" molecule has been removed.",1,'black')
                self.Message("No molecule.",1,'black')
            else:
                #self.SetCurrentMol(curmol,mol)                
                drwobjs=self.mol.GetDrawObjs()
                viewitems=self.mol.GetViewItems()
                if len(drwobjs) > 0:
                    self.RecoverDrawObjs(drwobjs) # this calls DrawMol!!!
                if len(viewitems) > 0:
                    self.draw.SetViewItems(viewitems)
                #drwitems=self.GetDrawObjs()
                #self.RecoverDrawItems(drwitems)
        
        if self.molctrl.GetNumberOfMols() <= 0: self.menuctrl.EnableMenu(False)
        
        self.SetUpDraw(True)
        self.DrawMol(True)

    def SetFragmentFMOInp(self,frgnam,indat,bdabaa):
        # set fragment data according to GAMESS-FMO input data
        if len(self.mol.atm) <= 0:
            mess='No molecule data.'
            self.Message(mess,1,'black')
            return
        # remove TERs
        self.DeleteAllTers()
        #
        bdadic={}
        for i,j in bdabaa:
            bdadic[i-1]=j-1
        for i in xrange(len(indat)):
            for j in indat[i]:
                jj=j-1
                self.mol.atm[jj].frgnam=frgnam[i]
                if bdadic.has_key(jj):
                    self.mol.atm[jj].frgbaa=bdadic[jj]
    
    def AssignIonChg(self,chg):
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            mess='No selected atoms.'
            self.Message(mess,1,'black')
            return
        for i in lst:
            self.mol.atm[i].frgchg=chg
        
        if self.shwfchg: self.DrawFormalCharge(True)


    def UpdateCoordinatesFromFile(self,ccfile):
        pass
        
    def UpdateCoordinatesFromClipboad(self):
        """ Update atom coordinates of current molecule with xyz data 
              in clipboad
        """
        xyzmol=[]
        natm,xyzdat=self.PasteAtomXYZFromClipboard()
        for i in range(len(xyzdat)):
            xyzmol.append([xyzdat[i][1],xyzdat[i][2],xyzdat[i][3]])
        #
        if natm > 0:
            # save coordinates to recover
            self.SaveAtomCC()
            nupd,devcc=self.UpdateAtomCC(xyzmol)
        if natm == 0 or nupd == 0:
            mess='Failed to update coordinates with those in clipboad'
            self.ConsoleMessage(mess)
            return
        #
        self.DrawMol(True)
        #lib.MessageBoxOK("Coordinates were changes.","")
        mess="Coordinates of "+str(nupd)+" atoms were updated with those in "
        mess=mess+"clipboad\n"
        mess=mess+"Deviation between old and new coordinates= "
        mess=mess+("%8.4f" % devcc)+" (A)."
        self.ConsoleMessage(mess)
        
    def UpdateCoordinates(self,ccfile,drw=True):
        """ read GMS output file and update coordinates of current molecule
        
        :param str ccfile: file name of GMS geometry optimization output file
        """
        if self.mol == None: return

        if not os.path.exists(ccfile):
            mess="File '"+ccfile+"' not found."
            lib.MessageBoxOK(mess,"")
            return
        base,ext=os.path.splitext(ccfile)
        
        target=self.ListTargetAtoms()
        ntrg=len(target)
        xyzmol=[]
        if ext == ".out" or ext == ".log":
            ret,ian,xyzmol=rwfile.ReadGMSOptGeom(ccfile)  
            if ret == 2:
                mess="No optimized coordinates in the output= "+ccfile
                return                
            #
            if ret == 1:
                mess="Geometry is not converged! Do you want to update?"
                dlg=lib.MessageBoxYesNo(mess,"")
                if not dlg: return

        elif ext == ".xyz":
            xyzdat,bond,resfrg=rwfile.ReadXYZMol(ccfile)
            for i in range(len(xyzdat)):
                xyzmol.append([xyzdat[i][1],xyzdat[i][2],xyzdat[i][3]])
            # xyzmol: elm,x,y,z
        else:
            mess='The file extension "'+ext+'" is not supproted.'
            lib.MessageBoxOK(mess,'fumodel(UpdateCoordinatesFromFile)')
            return
        # save coordinates to recover
        self.SaveAtomCC()
        nupd,devcc=self.UpdateAtomCC(xyzmol)
        if nupd == 0:
            mess='Falied to update coordinate. coord file='+ccfile
            self.ConsoleMessage(mess)
            return
        #
        if drw: self.DrawMol(True)
        #lib.MessageBoxOK("Coordinates were changes.","")
        mess="Coordinates of "+str(nupd)+" atoms were updated with those "
        mess=mess+"in file, "+ccfile+'\n'
        mess=mess+"Deviation between old and new coordinates= "
        mess=mess+("%8.4f" % devcc)+" (A)."
        self.ConsoleMessage(mess)

    def UpdateAtomCC(self,newxyz):
        """ Replace atom coordinates with newxyz 
                       (the target is selected atoms only) 
        
        :param lst newxyz: [[x(float),y(float),z(float)],...]
        :return int nupd: nupd - number of updated atoms
        :reurn float devcc: devcc - root-mean deviation between old and new 
                                    coordinates
        """ 
        nupd=0; devcc=0.0
        # check number of atoms
        target=self.ListTargetAtoms()
        ntrg=len(target)
        if len(newxyz) != ntrg:
            mess='Unable to update coordinates:\n'
            mess=mess+'The number of target atoms='+str(ntrg)+'\n'
            mess=mess+'The number of atoms in newxyz='+str(len(newxyz))
            lib.MessageBoxOK(mess,"")
            return nupd,devcc

        ii=-1; dif=0.0
        for i in target:
            atom=self.mol.atm[i]
            ii += 1
            dif=dif+(atom.cc[0]-newxyz[ii][0])**2+ \
                    (atom.cc[1]-newxyz[ii][1])**2+ \
                    (atom.cc[2]-newxyz[ii][2])**2
            atom.cc[0]=newxyz[ii][0]; atom.cc[1]=newxyz[ii][1]
            atom.cc[2]=newxyz[ii][2]
        nupd=i+1
        devcc=numpy.sqrt(dif)/float(nupd)
        
        return nupd,devcc

    def ClearSaveAtomCC(self):
        self.savatmcc.Clear()

    def SaveAtomCC(self,all=False):
        """ save atomic coordinates for recover
        
        :seealso: RecoverAtomCC()
        :note: use SaveMol for save all Atoms
        """
        if all: savlst=range(len(self.mol.atm))
        else: savlst=self.ListTargetAtoms()
        savcc=[]
        for i in savlst: 
            cc=self.mol.atm[i].cc
            savcc.append([cc[0],cc[1],cc[2]])
        self.savatmcc.Push([savlst,savcc])
    
    def RecoverAtomCC(self,drw=True):
        """ recover saved coordinates
        
        :seealso: fumodel.Model.SaveAtomCC()
        """
        if self.savatmcc.GetNumberOfData() <= 0:
            lib.MessageBoxOK("No saved coordinates to recover.","")
            return          
        lstlst=self.savatmcc.Pop()
        savlst=lstlst[0]; savcc=lstlst[1]
        k=-1
        for i in savlst:
            k += 1
            self.mol.atm[i].cc[0]=savcc[k][0]
            self.mol.atm[i].cc[1]=savcc[k][1]
            self.mol.atm[i].cc[2]=savcc[k][2]
        #
        if self.ctrlflag.Get('shwbda'): #self.shwbda:
            self.DrawBDAPoint(False)
            self.DrawBDAPoint(True)

        if drw: self.DrawMol(True)
    
    def ClearSaveMol(self):
        self.savmol.Clear()
                    
    def SaveMol(self,all=True):
        """ save Molecule object for recover
        
        :seealso: fumodel.Model.RecoverMol()
        """
        """
        if all: savlst=range(len(self.mol.atm))
        else: 
            savlst=self.ListTargetAtoms()
            savcc=[]
            for i in savlst: savcc.append(self.mol.atm[i].cc[:])
        """
        if self.mol is None: return
        #molobj=self.mol.CopyMolecule()
        molidx=self.molctrl.GetCurrentMolIndex()
        molobj=self.mol.CopyMolecule()
        self.savmol.Push([molidx,molobj])
    
    def RecoverMol(self,drw=True):
        """ recover Molecule object
        
        :param bool drw: True for draw, False for do not draw
        :seealso: fumodel.Model.SaveMol()
        """
        if self.savmol.GetNumberOfData() <= 0:
            lib.MessageBoxOK("No saved mol object to recover.","")
            return          

        [molidx,molobj]=self.savmol.Pop()
        self.mol=molobj.CopyMolecule()        
        #self.molctrl.SetMol(molidx,self.mol)
        #self.savmol.Clear()
        if drw: self.DrawMol(True)
    
    def ExtractResiduesInMol(self,resdatlst,savedir,drw=True,messout=True):
        def RemoveQuort(text):
            text=text.replace("'",'')
            text=text.replace('"','')
            return text

        if len(resdatlst) <= 0:
            mess='No residues'
            lib.MessageBoxOK(mess,'Model(ExtractResidueInMol)')
            return
        ans=lib.CheckFileExists(savedir,case=1)
        if not ans: return
        # resolve '*' in resdatlst
        resdatlst=lib.ExpandResList(resdatlst,self.mol)       
        #
        basename=self.mol.name
        nc=basename.rfind('.')
        if nc >= 0: basename=basename[:nc]
        basename=os.path.join(savedir,basename)
        parnam=self.mol.name; parfile=self.mol.inpfile
        filelst=[]; failedlst=[]
        for resdat in resdatlst:
            resatmlst=self.ListResDatAtoms(resdat)
            if len(resatmlst) <= 0: 
                failedlst.append(resdat); continue
            res,nmb,chain=lib.UnpackResDat(resdat)
            file=basename+'-'+res+'-'+str(nmb)+'-'+chain+'.pdb'
            filelst.append(file)
            molobj=molec.Molecule(self)
            for i in resatmlst: molobj.atm.append(self.mol.atm[i])
            ###molobj.RenumberAtmNmbAndConDat()
            molobj.WritePDBMol(file,parnam,parfile,True)
        return filelst,failedlst
    
    def JoinSplitFiles(self,pdbfile,splfile,drw=True,messout=True):
        filelst=[]
        if os.path.exists(splfile):
            filelst=[]
            f=open(splfile)
            for s in f.readlines():
                s=s.strip()
                nc=s.find('#')
                if nc >= 0: s=s[:nc].strip()
                if len(s) <= 0: continue
                if s[:1] == '#': continue
                file=lib.ReplaceBackslash(s)
                filelst.append(file)
        if len(filelst) < 0:
            mess='No files in filelst.'
            lib.MessageBoxOK(mess,'Model(JoinPDBFiles)')
            return
        # check file exsists
        nolst=[]
        for file in filelst:
            if not os.path.exists(file): nolst.append(file)
        if len(nolst) > 0:
            mess='Not found files='+str(nolst)
            lib.MessageBoxOK(mess,'Model(JoinPDBFiles)')
            return
        #
        self.mdlwin.BusyIndicator('On','Joining files ..')
        self.ReadFiles(filelst[0],False)
        for i in range(1,len(filelst)):
            file=filelst[i]
            molobj=molec.Molecule(self)
            molobj.BuildFromPDBFile(file)
            self.MergeMolecule(molobj.atm,True,False)
        #
        if len(pdbfile) > 0: 
            self.mol.WritePDBMol(pdbfile,'','',False)
            self.mol.inpfile=pdbfile
            head,tail=os.path.split(pdbfile)
            base,ext=os.path.splitext(tail)
            self.mol.name=base
        if messout:
            mess='\nCreated PDB file='+pdbfile+'\n'
            mess=mess+'used splfile='+splfile+', number of joined files='
            mess=mess+str(len(filelst))
            self.ConsoleMessage(mess)
        #
        self.MsgNumberOfAtoms(1)
        #
        if drw: self.DrawMol(True)
        self.mdlwin.BusyIndicator('Off')
         
    def MergeByFiles(self,filelst,drw=True,messout=True):
        def NotFoundMessage(file):
            mess='Not found file='+file
            lib.MessageBoxOK(mess,'Model(MergeByFiles)')
        
        if len(filelst) <= 0: return
        if not os.path.exists(filelst[0]): 
            NotFoundMessage(filelst[0])
            return
        merged=[]
        self.ReadFilesPDB(filelst[0],True)
        merged.append(filelst[0])
        for i in range(1,len(filelst)):
           if not os.path.exists(filelst[i]): NotFoundMessage(filelst[i])
           else:
               merged.append(filelst[i])
               self.MergeToCurrent(filelst[i],False)
        if messout:
            self.ConsoleMessage('Merged files='+str(merged))   
        if drw: self.DrawMol(True)
    
    def SplitMolAtTER(self,savedir,load=True,con=False):
        ans=lib.CheckFileExists(savedir,case=1)
        if not ans: return
        teratmlst=[]; atmlst=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX':
                if len(atmlst) > 0: teratmlst.append(atmlst)
                atmlst=[]; continue
            atmlst.append(atom.seqnmb)
        if len(atmlst) > 0: teratmlst.append(atmlst)
        if len(teratmlst) <= 1:
            mess='Not splitted since there is no/one "TER" in the moelcule.'
            self.ConsoleMessage(mess)
            return
        basename=self.mol.name
        nc=basename.rfind('.')
        if nc >= 0: basename=basename[:nc]
        basename=os.path.join(savedir,basename)
        parnam=self.mol.name
        parfile=lib.ReplaceBackslash(self.mol.inpfile.strip())
        filelst=[]; failedlst=[]
        k=0
        for atmlst in teratmlst:
            if len(atmlst) <= 0: 
                failedlst.append(resdat); continue
            k += 1
            file=basename+'-'+('%03d' % k)+'.pdb'
            file=lib.ReplaceBackslash(file)
            filelst.append(file)
            molobj=molec.Molecule(self)
            for i in atmlst: molobj.atm.append(self.mol.atm[i])
            molobj.WritePDBMol(file,parnam,parfile,con)
        # write split file
        if len(filelst) > 0:
            filename=basename+'-ter.spl'
            title='Split at TER'
            #rwfile.WriteSplitFile(filename,filelst,title,parfile)
            text='# Split at ters: parent pdb file='+parfile+'\n'
            text=text+'# Created by fu at '+lib.DateTimeText()+'\n'
            text=text+'#\n'
            for file in filelst: text=text+file+'\n'
            f=open(filename,'w'); f.write(text); f.close()
        
        mess='\nSplit at ter: number of created files='+str(len(filelst))+'\n'
        mess=mess+'Created file list='+str(filelst)+'\n'
        mess=mess+'Split files file(.spl)='+filename
        self.ConsoleMessage(mess)
        
        return filelst,failedlst
    
    def SplitMolIntoChains(self,savedir,load=True,con=False):
        ans=lib.CheckFileExists(savedir,case=1)
        if not ans: return
        chainatmlst=[]; atmlst=[]
        chaindic={}; chainlst=[]
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            chain=atom.chainnam
            if not chaindic.has_key(chain):
                chaindic[chain]=[]; chainlst.append(chain)
            else: chaindic[chain].append(atom.seqnmb) 
        if len(chainlst) <= 1:
            mess='Not splitted since there is no/one "chain" in the moelcule.'
            self.ConsoleMessage(mess)
            return
        basename=self.mol.name
        nc=basename.rfind('.')
        if nc >= 0: basename=basename[:nc]
        basename=os.path.join(savedir,basename)
        parnam=self.mol.name
        parfile=lib.ReplaceBackslash(self.mol.inpfile.strip())
        filelst=[]; failedlst=[]
        for chain in chainlst:
            atmlst=chaindic[chain]
            if len(atmlst) <= 0: 
                failedlst.append(resdat); continue
            if chain.islower(): chainlbl='l'+chain
            elif chain.isupper(): chainlbl='u'+chain 
            file=basename+'-'+chainlbl+'.pdb'
            file=lib.ReplaceBackslash(file)
            filelst.append(file)
            molobj=molec.Molecule(self)
            for i in atmlst: molobj.atm.append(self.mol.atm[i])
            molobj.WritePDBMol(file,parnam,parfile,con)
        # write split file
        if len(filelst) > 0:
            filename=basename+'-chain.spl'
            title='Split into chains'
            #rwfile.WriteSplitFile(filename,filelst,title,parfile)
            text='# Split into chains: parent pdb file='+parfile+'\n'
            text=text+'# Created by fu at '+lib.DateTimeText()+'\n'
            text=text+'#\n'
            for file in filelst: text=text+file+'\n'
            f=open(filename,'w'); f.write(text); f.close()
        
        mess='\nSplit into chains: number of created files='
        mess=mess+str(len(filelst))+'\n'
        mess=mess+'Created file list='+str(filelst)+'\n'
        mess=mess+'Split files file(.spl)='+filename
        self.ConsoleMessage(mess)
        
        return filelst,failedlst
    
    def SplitMolIntoWatAndRest(self,savedir,load=True,con=False):
        ans=lib.CheckFileExists(savedir,case=1)
        if not ans: return
        watdic={'wat':[],'rest':[]}
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.resnam in const.WaterRes: watdic['wat'].append(atom.seqnmb)
            else: watdic['rest'].append(atom.seqnmb)
        if len(watdic['wat']) <= 0:
            mess='Not splitted since there is no "water" in the moelcule.'
            self.ConsoleMessage(mess)
            return
        basename=self.mol.name
        nc=basename.rfind('.')
        if nc >= 0: basename=basename[:nc]
        basename=os.path.join(savedir,basename)
        parnam=self.mol.name
        parfile=lib.ReplaceBackslash(self.mol.inpfile.strip())
        filelst=[]; failedlst=[]
        name=['rest','wat']; fileext=['-rest.pdb','-wat.pdb']
        for i in range(2):
            atmlst=watdic[name[i]]
            if len(atmlst) <= 0: 
                failedlst.append(name[i]); continue
            file=basename+fileext[i]
            file=lib.ReplaceBackslash(file)
            filelst.append(file)
            molobj=molec.Molecule(self)
            for i in atmlst: molobj.atm.append(self.mol.atm[i])
            molobj.WritePDBMol(file,parnam,parfile,con)
            # write split file
        if len(filelst) > 0:
            filename=basename+'-wat-rest.spl'
            title='Split into waters and rest'
            #rwfile.WriteSplitFile(filename,filelst,title,parfile)
            text='# Split into watesr and the rest: parent pdb file='
            text=text+parfile+'\n'
            text=text+'# Created by fu at '+lib.DateTimeText()+'\n'
            text=text+'#\n'
            for file in filelst: text=text+file+'\n'
            f=open(filename,'w'); f.write(text); f.close()
        
        mess='\nSplit into waters and rest: number of created files='
        mess=mess+str(len(filelst))+'\n'
        mess=mess+'Created file list='+str(filelst)+'\n'
        mess=mess+'Split files file(.spl)='+filename
        self.ConsoleMessage(mess)
        
        return filelst,failedlst
                
    def SplitMolIntoProChemWat(self,savedir,load=True,con=False):
        ans=lib.CheckFileExists(savedir,case=1)
        if not ans: return
        prodic={'pro':[],'chem':[],'wat':[]}; 
        for atom in self.mol.atm:
            if atom.elm == 'XX': continue
            if atom.resnam in const.WaterRes: prodic['wat'].append(atom.seqnmb)
            elif const.AmiRes3.has_key(atom.resnam):
                prodic['pro'].append(atom.seqnmb)
            else: prodic['chem'].append(atom.seqnmb)
        basename=self.mol.name
        nc=basename.rfind('.')
        if nc >= 0: basename=basename[:nc]
        basename=os.path.join(savedir,basename)
        parnam=self.mol.name
        parfile=lib.ReplaceBackslash(self.mol.inpfile.strip())
        filelst=[]; failedlst=[]
        name=['pro','chem','wat']; fileext=['-pro.pdb','-chem.pdb','-wat.pdb']
        for i in range(3):
            atmlst=prodic[name[i]]
            if len(atmlst) <= 0: 
                failedlst.append(name[i]); continue
            file=basename+fileext[i]
            file=lib.ReplaceBackslash(file)
            filelst.append(file)
            molobj=molec.Molecule(self)
            for i in atmlst: molobj.atm.append(self.mol.atm[i])
            molobj.WritePDBMol(file,parnam,parfile,con)
            # write split file
        if len(filelst) > 0:
            filename=basename+'-pro-chem-wat.spl'
            title='Split into pro, chem and wat'
            #rwfile.WriteSplitFile(filename,filelst,title,parfile)
            text='# Split into pro-chem-wat: parent pdb file='+parfile+'\n'
            text=text+'# Created by fu at '+lib.DateTimeText()+'\n'
            text=text+'#\n'
            for file in filelst: text=text+file+'\n'
            f=open(filename,'w'); f.write(text); f.close()

        mess='\nSplit into pro-chem-wat: number of created files='
        mess=mess+str(len(filelst))+'\n'
        mess=mess+'Created file list='+str(filelst)+'\n'
        mess=mess+'Split files file(.spl)='+filename
        self.ConsoleMessage(mess)
        
        return filelst,failedlst
                
    @staticmethod
    def SplitAtTER(molnam,pdbmol):
        # split pdbmol data at TER and create new molecules.
        # return molnamdic, moldatdic, delcondic
        # molnam: name of pdb molecule, pdbmol: pdbmol data
        # molnamdic: splitted mol name, moldatdic: splitted mol dat, 
        # delcondic: covalent bonds between splited molecules (need to ecover total system)
        # molcomdic: center of mass and three heavy atom coordinates(need to ercover original coordinates)
        molnamdic={}; moldatdic={}; delcondic={}; molcomdic={}
        nmol=-1; nati=0; moldat=[]; natm=len(pdbmol)
        for i in xrange(natm):
            nati += 1
            if nati == 1:
                ini=pdbmol[i][1][0]
            moldat.append(list(pdbmol[i]))
            elm=pdbmol[i][3][0]
            lasta=False
            if i == natm-1: lasta=True
            if elm == 'XX' or (lasta and len(moldat)) > 0:
                dellst=[]
                for j in xrange(len(moldat)): 
                    tmp=list(moldat[j].conect)
                    kk=-1; deltmp=[]
                    for k in xrange(len(moldat[j].conect)):
                        kk += 1
                        moldat[j].conect[k] -= ini
                        tmp[kk] -= ini
                        if tmp[kk] >= nati or tmp[kk] < 0:
                            del tmp[kk]; kk -= 1             
                            deltmp.append(moldat[j].seqnmb+ini)
                            deltmp.append(moldat[j].conect[k]+ini)
                            dellst.append(deltmp)
                    moldat[j].conect=tmp

                nmol += 1
                moldatdic[nmol]=moldat
                nmb='%03d' % nmol
                molnamdic[nmol]=molnam+'_'+nmb
                delcondic[nmol]=dellst
                moldat=[]
                nati=0
        return molnamdic,moldatdic,delcondic

    @staticmethod
    def SplitWater(molnam,pdbmol):
        # split water molecules. Sister routine of SplitAtTER
        molnamdic={}; moldatdic={}; molcomdic={}
        moldat=[]; natm=len(pdbmol)
        nmol=0; nati=0
        for i in xrange(natm):
            res=pdbmol[i][2][2]        
            if res != 'HOH' and res != 'WAT' and res != 'DOD':
                nati += 1
                moldat.append(list(pdbmol[i]))
        moldatdic[nmol]=moldat
        nmb='%03d' % nmol
        molnamdic[nmol]=molnam+'_'+nmb
        nmol=1; moldat=[]; nwat=0
        for i in xrange(natm):
            res=pdbmol[i][2][2]        
            if res == 'HOH' or res == 'WAT' or res == 'DOD':
                moldat.append(list(pdbmol[i]))
                nati += 1
                if pdbmol[i][3][0] == 'O ': nwat += 1
        moldatdic[nmol]=moldat
        nmb='%03d' % nmol
        #molnamdic[nmol]=molnam+'_'+nmb
        molnamdic[nmol]=molnam+'_wat'
        #mess='Number of water molecules='+str(nwat)+' out of '+str(natm)+' atoms.'
        #self.Message(mess,0,'black')
        return molnamdic,moldatdic
        
    def MakeNewMol(self,case):
        if case == 'selected atoms':
            print 'molselatoms'
        if case == 'auto':
            condat=[]
            for atom in self.mol.atm:
                i=atom.seqnmb           
                tmp=[]
                tmp.append(atom.cc[:])
                tmp.append(atom.conect[:])
                elm=self.mol.atm[i].elm; tmp.append(elm)
                condat.append(tmp)
            grplst=self.MakeBondedAtomGroupList(condat)

    def OriginalOrient(self,pdborg,pdbnew):
        ret=1
        nati=[]
        nat1=0; nat3=len(pdborg)/2; nat2=nat3/4
        nati.append(nat1); nati.append(nat2); nati.append(nat3)
        coordorg=[]; resorg=[]; resnmborg=[]; atmnmborg=[]
        for i in range(3):
            coordorg.append(list(pdborg[nati[i]][0]))
            resorg.append(pdborg[nati[i]][2][2])
            resnmborg.append(pdborg[nati[i]][2][3])
            atmnmborg.append(pdborg[nati[i]][2][1])                 
        pntn=[]; pntr=[]
        coord=[]
        for i in xrange(len(pdbnew)):
            res=pdbnew[i][2][2]; nmb=pdbnew[i][2][3]; atmnmb=pdbnew[i][2][1]
            if res == resorg[0] and nmb == resnmborg[0] and \
                                                    atmnmb == atmnmborg[0]:
                coord.append(list(pdbnew[i][0]))
                #
                break
        for i in xrange(len(pdbnew)):
            res=pdbnew[i][2][2]; nmb=pdbnew[i][2][3]; atmnmb=pdbnew[i][2][1]
            if res == resorg[1] and nmb == resnmborg[1] and \
                                                     atmnmb == atmnmborg[1]:
                coord.append(list(pdbnew[i][0]))
                break
        for i in xrange(len(pdbnew)):
            res=pdbnew[i][2][2]; nmb=pdbnew[i][2][3]; atmnmb=pdbnew[i][2][1]
            if res == resorg[2] and nmb == resnmborg[2] and \
                                                      atmnmb == atmnmborg[2]:
                coord.append(list(pdbnew[i][0]))
                break
        if len(coord) != 3:
            ret=0
        pntn=[]; pntr=[]
        for i in range(3):
            pntr.append(numpy.subtract(coord[i],coord[0]))
            pntn.append(numpy.subtract(coordorg[i],coordorg[0]))
        u=lib.RotMatPnts(pntr,pntn)
        coordx=[]
        rc=numpy.zeros(3)
        for i in xrange(len(pdbnew)):
            cc=numpy.subtract(pdbnew[i][0],coord[0])
            coordx.append(cc)
        coordx=lib.RotMol(u,rc,coordx)                   
        for i in xrange(len(pdbnew)):
            pdbnew[i][0]=numpy.add(coordx[i],coordorg[0])     
        return ret         

    def AddHydrogenUseFrameData(self,wat=False,drw=True,atmlst=[]):
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        #framedatdic=self.setctrl.GetFrameDataDic()
        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass

        framedatdic=self.DownloadFrameData(lst)
        
        if len(framedatdic) <= 0:
            self.Message('AddHydrogenUseFrameData: no frame data.',0,'black')
            self.mdlwin.BusyIndicator('Off')
            return
        if not wat:
            for watres in const.WaterRes:
                if framedatdic.has_key(watres): del framedatdic[watres]
        self.mol.AddBondUseFrame(lst,framedatdic)
        self.mol.AddHydrogenUseFrame(lst,framedatdic)
        #
        self.ResetPosAtm() 
        if drw: self.DrawMol(True) 
        
        try: self.mdlwin.BusyIndicator('Off')
        except: pass

    def AddBoxWaters(self):
        if len(self.mol.atm) <= 0:
            lib.MessageBoxOK("No molecular data.","")
            return  
        self.OpenWaterBoxPanel()
                   
    def AddBondUseFrameData(self,drw=True):
        lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        framedatdic=self.setctrl.GetFrameDataDic()
        if len(framedatdic) <= 0:
            self.Message('AddHydrogenUseFrameData: no frame data.',0,'black')
            return
        self.mol.AddBondUseFrame(lst,framedatdic)

        self.ResetPosAtm() 
        if drw: self.DrawMol(True)    

    def DownloadFrameData(self,lst,messout=True):
        """ Download monomer (frame) data from pdb-ftp-site
        
        :param lst lst: lst:target atoms (selected atoms) list
        :seealso: 'lib.GetMonomersFromPDBFTPServer' method
        """
        if messout:
            mess='Frame data information(Model.DownloadFrameData):\n'            
            self.ConsoleMessage(mess)
        #
        framedatdic=self.setctrl.GetFrameDataDic()
        # check frame data
        noframedic={}; text=''; existlst=[]
        for i in lst:
            atom=self.mol.atm[i]
            resnam=atom.resnam; resnmb=atom.resnmb; chain=atom.chainnam
            #resdat=lib.ResDat(atom)
            if const.AmiRes3.has_key(resnam): continue
            if resnam in const.WaterRes: continue
            if not framedatdic.has_key(resnam): noframedic[resnam]=True
            else:
                if not resnam in existlst: existlst.append(resnam)                
        if messout and len(existlst) > 0:
            mess='Frame data in FUDATASET//Frames directory will be used for '
            mess=mess+'residues,\n'+str(existlst)
            self.ConsoleMessage(mess)
        if len(noframedic) > 0:
            searchlst=noframedic.keys()
            for res in searchlst: text=text+','+res
            ###mess='Frame data are not found for '+text+'. Would you like to '
            ###mess=mess+'download them from pdb:ftp site?'
            ###dlg=lib.MessageBoxYesNo(mess,"")  
            ###if not dlg: return framedatdic
            ###else:
            framedir=self.setctrl.GetDir('Frames')
            downlst=noframedic.keys()
            ftpserver=self.setctrl.GetParam('pdb-monomer-ftp-server')    
            mess,saved,failed=lib.GetMonomersFromPDBFTPServer(ftpserver,
                                                          downlst,framedir)
            if messout:
                if len(mess) > 0: 
                    self.ConsoleMessage('OnDownload message: '+mess)
                else: 
                    mess='succeeded='+str(saved)+', failed='+str(failed)
                    self.ConsoleMessage('Downloaded monomer data: '+mess)
            framedatdic=self.setctrl.MakeFrameDataDic()
        return framedatdic
    
    def AddBondMultiplicity(self,clearmulti=True,drw=True):
        # case=0 for based-on valence, =1 for bond length
        #self.bndmulti=[] # {'single':1,'double':2,'triple':3,'aromatic'}
        def FreeValence(case,atom):
            elm=atom.elm; nval=0
            try: maxval=const.ElmValence[elm]
            except: return None
            if case == 0: nval=len(atom.conect)
            elif case == 1:
                for k in range(len(atom.conect)): 
                    try: nval += atom.bndmulti[k]
                    except: return None
            remval=maxval-nval
            if remval < 0: remval=None
            return remval
        # clar bndmulti data
        if clearmulti:
            self.RemoveBondMultiplicity(drw=False)
        #
        lst=self.ListTargetAtoms()
        elmdic={' O':True,' S':True}
        # bond in ring
        netk,G=lib.NetXGraphObject(self.mol)
        klst=netk.k_components(G)
        try: 
            ringlst=[list(x) for x in klst[2]]
        except: ringlst=[]
        #
        if len(ringlst) > 0:
            for i in range(len(ringlst)):
                nlst=len(ringlst[i])
                if nlst != 5 and nlst != 6: continue
                for j in ringlst[i]:
                    atomj=self.mol.atm[j]
                    remvalj=FreeValence(0,atomj)
                    if remvalj != 1: continue
                    for k in range(len(atomj.conect)):
                        kk=atomj.conect[k]
                        if not kk in ringlst[i]: continue
                        atomk=self.mol.atm[kk]
                        remvalk=FreeValence(0,atomk)
                        if remvalk != 1: continue
                        try: 
                            idx=atomk.conect.index(j)
                            atomk.bndmulti[idx]=4
                        except: continue
                        if remvalk == 1 or atomk.bndmulti[k] == 4: 
                            atomk.bndmulti[idx]=4
                            atomj.bndmulti[k]=4 # aromatic
        #if drw: self.DrawMultipleBond(True)
        #return
        #  the other bonds     
        for i in lst:
            atom=self.mol.atm[i]
            if atom.elm == ' H': continue
            remvali=FreeValence(1,atom)        
            if remvali is None: continue
            maxvali=const.ElmValence[atom.elm]
            for j in range(len(atom.conect)):
                if atom.bndmulti[j] == 4: continue
                jj=atom.conect[j]
                atomj=self.mol.atm[jj]
                if atomj.elm == ' H': continue
                try: maxvalj=const.ElmValence[atomj.elm]
                except: continue
                remvalj=FreeValence(1,atomj)               
                if remvalj is None < 0: continue
                incmulti=min(remvali,remvalj)
                if atom.bndmulti[j]+incmulti > maxvali: continue              
                atom.bndmulti[j] += incmulti
                try: idx=atomj.conect.index(i)
                except: continue
                if atomj.bndmulti[idx]+incmulti > maxvalj: continue
                atomj.bndmulti[idx] += incmulti       
        # draw
        if drw: self.DrawMultipleBond(True)
                        
    def RemoveBondMultiplicity(self,atmlst=[],drw=True):
        drwlabel='Multiple bond'
        lst=atmlst
        if len(atmlst) <= 0: lst=self.ListTargetAtoms()
        for i in lst:
            atom=self.mol.atm[i]
            for j in range(len(atom.bndmulti)): atom.bndmulti[j]=1
        self.ctrlflag.Set(drwlabel,False)
        self.menuctrl.CheckMenu(drwlabel,False)
        
        if drw: self.DrawMultipleBond(False)
    
    def AddHydrogenToAAByFMOPDB(self,pdbfile,keep,nterm,cterm,his,wat,
                                drw=True):
        # FMOPDB: Fortran code
        #add hydrogen atoms to residues
        #nterm =0 protonate N-terminus, =1 no
        #cterm =0 protonate C-terminus, =1 no
        #not supported iprot  =0 protonate ASP and GLU, =1 no
        #his =0 protonate, =1 neutral(H at ND1), =2 neutral(H at NE2)
        #keep =0 keep original H's, =1 no. throw out
        #not supported ihpos  =0 insert H atoms after heavy atoms, =1 at standard position        
        # wat =0 delete, =1 add hydrogen 
        #self.ctrlflag.SetCtrlFlag('busy',True)
        #self.busy=True
        self.Message("Running AddHydrogen ...",0,"")

        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass
        
        #pdbfile=self.mol.inpfile
        #nterm=0; cterm=1; his=0; keep=1; gluasp=1 # always 1 for gluasp 
        try: atmnmb,atmnam,resnam,chainnam,resnmb,cc,ian,natm= \
               fmopdb.pdbmolout(pdbfile,nterm,cterm,1,his,keep,wat)
        except: natm=-1
        #print 'natm from Fortran',natm
        if natm <= 0:
            mess="Failed to add hydrogens by FMOPDB."
            self.Message(mess,0,"")
            return natm
        nter=0; pdbmol=[]; elm=[]; conect=[]; alt=[]; occ=[]; bfc=[]; chg=[]
        coord=[]; atmname=[]; resname=[]; chainname=[]
        atmnumber=[]; resnumber=[]
        for i in xrange(natm):
            elmtmp=const.ElmSbl[ian[i]]
            if elmtmp == "  ":
                elmtmp="XX"; nter += 1
            elm.append(elmtmp)
            conect.append([i])
            coord.append([cc[i][0],cc[i][1],cc[i][2]])
            atmname.append(atmnam[i][0]+atmnam[i][1]+atmnam[i][2]+atmnam[i][3])
            atmnumber.append(int(atmnmb[i]))
            resname.append(resnam[i][0]+resnam[i][1]+resnam[i][2])
            resnumber.append(int(resnmb[i]))
            chainname.append(chainnam[i][0])
            conect.append([i])
            alt.append(" "); occ.append(1.0); bfc.append(0.0); chg.append(0.0)
        #
        pdbmol=[coord,conect,atmname,atmnumber,resname,resnumber,chainname,
                alt,elm,occ,bfc,chg]
        #    
        self.mol.SetPDBMol(pdbmol)
        if wat == 0: self.mol.DelWater([])
        #
        self.SetSelectAll(False)
        lst=self.ListTargetAtoms()
        self.mol.AddBondUseBL(lst)
        for atom in self.mol.atm:
            if atom.elm == ' H': atom.select=True
        #
        self.MsgNumberOfAtoms(2)        
        #
        #self.ctrlflag.SetCtrlFlag('busy',False)
        self.busy=False
        if drw: self.DrawMol(True)
        self.Message("",0,"")
        try: self.mdlwin.BusyIndicator('Off')
        except: pass
        
        return natm

    def AddMissingNterm(self,drw=False):
        def ErrorMessage(i,resdat):
            mess='No connects of atom='+str(i)+'. Unable to continue.'
            lib.MessageBoxOK(mess,'Model(CheckMissingNterm)')
                 
        def Renumber(ith):
            for i in xrange(ith,len(self.mol.atm)):
                self.mol.atm[i].seqnmb += 1
                if len(self.mol.atm[i].conect) > 0:
                    for j in range(len(self.mol.atm[i].conect)):
                        self.mol.atm[i].conect[j] += 1

        def InsertAtom(ith,coord,resdat):
            Renumber(ith)
            atom=molec.Atom(self.mdlwin)
            elm=' N'; atom.elm=elm; atom.SetAtomParams(elm)
            atom.cc=coord[:]; atom.conect=[ith+1] #; atom.select=True
            atom.atmnam=' N  '; atom.seqnmb=ith
            resnam,resnmb,chain=lib.UnpackResDat(resdat)
            atom.resnam=resnam; atom.resnmb=resnmb; atom.chainnam=chain
            self.mol.atm.insert(ith,atom)
        #
        failedlst=[]
        missn=[]; missnres=[]; donedic={}
        for atom in self.mol.atm:
            if not const.AmiRes3.has_key(atom.resnam): continue
            if atom.elm == 'XX': continue
            resdat=lib.ResDat(atom)
            if donedic.has_key(resdat): continue
            if atom.atmnam != ' N  ':
                missn.append(atom.seqnmb); missnres.append(resdat)
            donedic[resdat]=True    

        if len(missnres) > 0:
            mess='N atom is missing in residues:\n'
            mess=mess+str(missnres)
            self.ConsoleMessage(mess)
            # add N
            rnc=1.47; nadd=0
            for i in range(len(missn)):
                iat=missn[i]+nadd
                resdat=missnres[i]
                ncon=len(self.mol.atm[iat].conect)
                try: 
                    con1=self.mol.atm[iat].conect[0]
                except:
                    ErrorMessage(iat,resdat); failedlst.append(resdat)
                    continue
                if ncon == 1: # no CB
                     atmlst=[iat,con1]
                     nh,coord=self.mol.GetCCAddAtmType3A1(atmlst,rnc)
                     InsertAtom(iat,coord[0],resdat); nadd += 1
                elif ncon == 2: # is CB 
                    try: con2=self.mol.atm[iat].conect[1]
                    except:
                        ErrorMessage(iat,resdat); failedlst.append(resdat)
                        continue
                    atmlst=[iat,con1,con2]
                    nh,coord=self.mol.GetCCAddAtmType2A1(atmlst,rnc)
                    InsertAtom(iat,coord[0],resdat); nadd += 1
                elif ncon == 3: # are CB and H
                    try: con2=self.mol.atm[iat].conect[1]
                    except:
                        ErrorMessage(iat,resdat); failedlst.append(resdat)
                        continue
                    try: con3=self.mol.atm[iat].conect[2]
                    except:
                        ErrorMessage(iat,resdat); failedlst.append(resdat)
                        continue
                    atmlst=[iat,con1,con2,con3]
                    nh,coord=self.mol.GetCCAddAtmType1A1(atmlst,rnc)
                    InsertAtom(iat,coord[0],resdat); nadd += 1
        #
        if drw: self.DrawMol(True)
        return failedlst
        
    def AddHydrogenToAAResidue(self,drw=True,atmlst=[],checknterm=True):
        """ Add hydrogens to AA residues """
        self.busy=True
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        if len(lst) <= 0:
            self.Message("No atoms are seletced for add hydrogen.",0,"")
            return
        #
        self.mdlwin.BusyIndicator('On','Adding hydrogens ..')
        # add bond
        self.mol.AddBondUseBL(lst)
        # add n if missing        
        if checknterm:
            failedlst=self.AddMissingNterm()
            if len(failedlst) > 0:
                mess='Failed to add N term atom in residues:\n'
                mess=mess+str(failedlst)
            else: mess='N atoms were added successfully.'
            self.ConsoleMessage(mess)
        #
        nhtotal=0; nhchainlst=[]
        # self.usefmoutil=False
        if self.setctrl.GetParam('use-fmoutil'): #self.usefmoutil: 
            try:
                scrdir=self.setctrl.GetDir('Scratch')
                self.build.AddHydrogen_Frm(self.mdlwin,-1,self,scrdir) # Fortran code        
                #self.ctrlflag.SetCtrlFlag('busy',False)
                self.Message("Running fmoutil to add hydrogens ...",0,"")
                self.busy=False
                self.mdlwin.BusyIndicator('Off')
                return
            except:
                mess='fmoutil is failed in AddHydrogenToAAResidue). '
                mess=mess+'Python code is used.'
                self.ConsoleMessage(mess)
                nhtotal,nhchainlst=self.mol.AddHydrogenToProtein(lst,
                                                                 addbond=False)
        else:
            nhtotal,nhchainlst=self.mol.AddHydrogenToProtein(lst,addbond=False)
        #
        self.Message("Running AddHydrogenToAAResidue ...",0,"")

        mess="Number of hydrogen atoms added: "+str(nhtotal)+". Each chain ["
        for i in nhchainlst: mess=mess+str(i)+','
        ns=len(mess); mess=mess[:ns-1]+"]"
        self.Message(mess,0,"")
        if len(nhchainlst) > 0:
            mess="Warning: there are multiple polypeptide chains in this"
            mess=mess+" system. Please check "
            mess=mess+"attached hydrogens at each N- and C-termins."
            self.ConsoleMessage(mess)
        #
        #if self.setctrl.GetParam('tinker-atom-order'): #self.tinkeratomorder:
        #    self.ReorderHydrogensIntoTinker()
        #if self.setctrl.GetParam('tinker-atom-name'): #self.tinkeratmnam:
        #    self.RenameAtmNamIntoTinker()
        # print number of atoms on console
        self.MsgNumberOfAtoms(1)       
        #
        self.ResetPosAtm()        
        #??self.ctrlflag.SetCtrlFlag('busy',False)
        
        #
        if drw: self.DrawMol(True)
        self.Message("",0,"")
        self.mdlwin.BusyIndicator('Off')
        
    def AddHydrogenToWater(self,drw=True,atmlst=[]):
        #??self.ctrlflag.SetCtrlFlag('busy',True)
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        if len(lst) <= 0: return

        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass
        
        self.mol.AddHydrogenToWaterMol(lst)
        
        self.ResetPosAtm()        

        #??self.ctrlflag.SetCtrlFlag('busy',False)
        if drw: self.DrawMol(True)
        
        try: self.mdlwin.BusyIndicator('Off')
        except: pass
    
    def SelectByFile(self,drw=True):
        """ Select atoms/residues in select file"""
        def RemoveQuort(text):
            text=text.replace("'",'')
            text=text.replace('"','')
            return text
        
        filename=lib.GetFileName(None,wcard='',rw='r')
        if filename == '': return
        if not os.path.exists(filename):
            mess='Not found file='+filename
            retrun
        #
        reslst=[]; atmlst=[]; found=False
        text=''
        f=open(filename,'r')
        for s in f.readlines():
            ns=s.find('#')
            if ns >= 0: s=s[:ns]
            s=s.strip()
            if len(s) <= 0: continue
            if found:
                text=text+s
                if s[-1:] == ']':
                    text=RemoveQuort(text)
                    key,lst=lib.GetKeyAndValue(text,
                                               conv=False,recoverlist=True)
                    text=''; found=False
                continue
            #
            ns=s.find('=')
            if ns > 0:
                if s[-1:] == ']':
                    s=RemoveQuort(s)
                    key,lst=lib.GetKeyAndValue(s,
                                               conv=False,recoverlist=True)
                else: 
                    text=s; found=True
                continue
        f.close()
        if key == 'reslst': reslst=lst
        elif key == 'atmlst': 
            atmlst=[int(x) for x in lst]        
        if len(atmlst) <= 0 and len(reslst) <= 0:
            mess='No atoms/residues in file='+filename
            lib.MessageBoxOK(mess,'Model(SelectAtomsInFile)')
            return
        #
        if len(reslst) > 0:
            self.SelectResidue(reslst,True,drw=False)
        if len(atmlst) > 0:
            self.SelectAtomByList(atmlst,True,drw=False)
        #    
        if drw: self.DrawMol(True)
            
    def AddHydrogenToAllResidues(self,drw=True,atmlst=[]):
        """ not tested """
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        if len(lst) <= 0: return

        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass
        
        self.AddHydrogenToAAResidue(drw=False,atmlst=lst)
        
        resdatlst=self.ListResidue3('non-aa')
        if len(resdatlst) > 0:
            self.AddHydrogenToNonAAResidue(drw=False,atmlst=lst)
        
        resdatlst=self.ListResidue3('water')
        if len(resdatlst) > 0: self.AddHydrogenToWater(drw=False,atmlst=lst)
        #
        if drw: self.DrawMol(True)
        try: self.mdlwin.BusyIndicator('Off')
        except: pass
    
    def XXAddHydrogenToNonAAResidue(self,wat=True,drw=True,atmlst=[]):
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        if len(lst) <= 0: return

        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass

        framedatdic=self.DownloadFrameData(lst)
        nonaareslst=self.ListNonAAResidue(wat=wat,nameonly=True)
        nofrmlst=[]; frmlst=[]; mess=''
        for res in nonaareslst:
            if not framedatdic.has_key(res): 
                if not res in nofrmlst: nofrmlst.append(res)
            else: 
                if not res in frmlst: frmlst.append(res)
        if len(frmlst) > 0:
            self.AddHydrogenUseFrameData(drw=False,atmlst=lst)
            mess='Hydrogens are added using frame data='+str(frmlst)+'\n'
            mess=mess+str(frmlst)
        allatm=range(len(self.mol.atm))
        lst=self.ListNonBondedAtoms(atmlst=allatm)
        if len(lst) > 0:
            self.AddHydrogenUseBondLength(drw=False,atmlst=lst)
            mess='Tried to add hydrogens base on bond lengths for residues:\n'
            mess=mess+str(nofrmlst)
        if len(mess): self.ConsoleMessage(mess)
        #
        self.ResetPosAtm() 
        if drw: self.DrawMol(True) 
        
        try: self.mdlwin.BusyIndicator('Off')
        except: pass
                
    def AddHydrogens(self,resknd=['aa','non-aa','wat'],frame=True,
                                  bondlength=False,drw=True):
        """ Add hydrogens to non-peptide residues
        
        :param lst atmlst: target atomlist(all or selected atoms)
        :param lst resknd: list of target residue kind
        :param bool frame: True for use frame data, False do not
        :param bool bondlength: True for use bondlength, False do not
        :param bool drw: True for redraw molecule, False for do not.
        """
        def NoResMessage(kind):
            mess='No '+kind+ 'resdiues'
            self.ConsoleMessage(mess)

        #lst=atmlst
        #if len(lst) <= 0: atmlst=range(self.mol.atm) #  self.ListTargetAtoms()
        #if len(atmlst) <= 0: return
        atmlst=range(len(self.mol.atm))
        if len(atmlst) <= 0: return
        #
        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass
        time1=time.clock() # turn on timer
        mess='"AddHydorgens" starts at '+lib.DateTimeText()
        self.ConsoleMessage(mess)
        #
        if 'all' in resknd: resknd=['aa','non-aa','wat']
        if 'aa' in resknd: 
            atmlst=range(len(self.mol.atm))
            aaresatm=self.ListAAResidueAtoms(atmlst)
            if len(aaresatm) <= 0: NoResMessage('aa')
            else:
                self.Message('Adding hydrogens to AA residues')
                self.AddHydrogenToAAResidue(atmlst=aaresatm,drw=False)
        if 'non-aa' in resknd:
            #self.SelectAtomByList(atmlst,True,reset=True,drw=False)
            atmlst=range(len(self.mol.atm))
            chmatmlst=self.ListNonAAResidueAtoms(wat=False,atmlst=atmlst)
            if len(chmatmlst) <= 0: NoResMessage('non-aa')
            else:
                if frame:
                    self.Message('Adding hydrogens to non-AA residues(frame')
                    self.AddHydrogenUseFrameData(atmlst=chmatmlst,drw=False)
                if bondlength:
                    self.Message('Adding hydrogens to non-AA residues(BL')
                    #self.SelectAtomByList(chmatmlst,True,reset=True,drw=False)
                    atmlst=range(len(self.mol.atm))
                    chmatmlst=self.ListNonAAResidueAtoms(wat=False,
                                                         atmlst=atmlst)
                    self.AddHydrogenUseBondLength(atmlst=chmatmlst,drw=False)
        if 'wat' in resknd:
            #self.SelectAtomByList(atmlst,True,reset=True,drw=False)
            atmlst=range(len(self.mol.atm))
            watatmlst=self.ListWaterAtoms(atmlst)
            if len(watatmlst) <= 0: NoResMessage('wat')
            else:
                self.Message('Adding hydrogens to waters')
                self.AddHydrogenToWater(atmlst=watatmlst,drw=False)
        #
        self.Message('Ended Add hydrogens')
        time2=time.clock(); etime=time2-time1
        mess='"AddHydrogens" ends at '+lib.DateTimeText()
        self.ConsoleMessage(mess)
        mess='Elapsed time='+str(etime)
        self.ConsoleMessage(mess)
        #
        if drw: self.DrawMol(True) 
        
        try: self.mdlwin.BusyIndicator('Off')
        except: pass
                
    def AddHydrogenUseBondLength(self,drw=True,atmlst=[]):
        #??self.ctrlflag.SetCtrlFlag('busy',True)
        self.Message('Running Add Bonds ...',0,'')
        targetatm=atmlst
        if len(targetatm) <= 0: targetatm=self.ListTargetAtoms()
        if len(targetatm) <= 0: return
        #
        try: self.mdlwin.BusyIndicator('On','Adding hydrogens...')
        except: pass

        self.mol.AddBondUseBL(targetatm)
        self.mol.AddHydrogenUseBL(targetatm)
        
        self.ResetPosAtm()
        #??self.ctrlflag.SetCtrlFlag('busy',False)

        if drw: self.DrawMol(True)
        self.Message('',0,'')
        try: self.mdlwin.BusyIndicator('Off')
        except: pass

    def AddBondUseBondLength(self,drw=True):
        #??self.ctrlflag.SetCtrlFlag('busy',True)
        targetatm=self.ListTargetAtoms()
        #
        self.mdlwin.BusyIndicator('On','Adding bonds ..')
        
        
        self.mol.AddBondUseBL(targetatm)
        
        self.mdlwin.BusyIndicator('Off','')
        
        self.ResetPosAtm()
        #??self.ctrlflag.SetCtrlFlag('busy',False)        
        if drw: self.DrawMol(True)
    
    def SetBonds(self):
        targetatm=self.ListTargetAtoms()
        self.mol.AddBondUseBL(targetatm)
        self.ResetPosAtm()
        
    def AttachHydrogen(self,group,atmlst=[]):
        myname='Model(AttachHydrogen)'
        lst=atmlst; group=group.strip()
        if len(lst) <= 0: nsel,lst=self.ListSelectedAtom()
        # check selected atoms
        if len(lst) <= 0:
            mess='Select atom(s) to be attached hydrogen(s)'
            lib.MessageBoxOK(mess,myname)
            return
        hgrplst=['1H','2H','3H']
        #mgrplst=['-CH3','-ACE','-NME']
        if group in hgrplst: 
            if group == '1H': self.mol.AddGroup1Hydrogen(lst)
            elif group == '2H': self.mol.AddGroup2Hydrogen(lst)
            elif group == '3H': self.mol.AddGroup3Hydrogen(lst)
        #elif group in mgrplst:
        #    self.ReplaceXHWithXGroup(group,lst)
        
        else: return
        #                    
        self.ResetPosAtm()
        self.DrawMol(True)
            
    def ReplaceWithGroupAtoms(self,group,atmlst=[]):
        myname='Model(ReplaceWithGrouAtoms)'
        lst=atmlst; group=group.strip()
        if len(lst) <= 0: nsel,lst=self.ListSelectedAtom()
        # check selected atoms
        if len(lst) <= 0:
            mess='Select hydrogen atom(s) to be replaced with a functional'
            mess=mess+' group'
            lib.MessageBoxOK(mess,myname)
            return
        mgrplst=['CH3','ACE','NME']
        if group in mgrplst:
            self.ReplaceXHWithXGroup(group,lst)
        else:
            mess='Not supported functional group='+group
            lib.MessageBoxOK(mess,myname)
        #                    
        self.ResetPosAtm()
        
    def ReplaceXHWithXGroup(self,group,atmlst=[]):
        def FindAttachAtom(i):
            atmi=-1; atmtxt='basegrp'+str(i)
            for i in xrange(len(self.mol.atm)):
                if self.mol.atm[i].atmtxt == atmtxt:
                    atmi=i; break
            return atmi
        
        def DelAtmTxt(i):
            atmtxt='basegrp'+str(i)
            for i in xrange(len(self.mol.atm)):
                if self.mol.atm[i].atmtxt == atmtxt:
                   self.mol.atm[i].atmtxt=''; break
        lst=atmlst
        if len(lst) <= 0: return
        myname='Model(AddGroupAtoms)'    
        grplst=['CH3','ACE','NME']
        files=['ch4.mol','ace.mol','nme.mol']
        # check mol file
        try: idx=grplst.index(group)
        except: return
        molfile=files[idx]
        moldir=self.setctrl.GetDir('Molecules')
        molfile=os.path.join(moldir,molfile)
        if not os.path.exists(molfile):
            mess='Not found molfile='+molfile
            lib.MessageBoxOK(mess,myname)
            return
        moldat=rwfile.ReadMolFile(molfile)
        moldat=moldat[0]
        #
        title=moldat[0]; comment=moldat[1]; resnam=moldat[2]
        molatm=moldat[3]
        mol=molec.Molecule(self)
        mol.SetMolAtoms(molatm,resnam=resnam)
        iatm=0
        for atom in mol.atm:
            if atom.elm != ' H': continue
            if len(atom.conect) > 0: 
                iatm=atom.seqnmb; break
        for i in xrange(len(self.mol.atm)):
            self.mol.atm[i].atmtxt=''
            if i in lst: 
                self.mol.atm[i].atmtxt='basegrp'+str(i)
        for i in lst:
            atm1=FindAttachAtom(i)
            if atm1 <= 0:
                mess='Failed to attach '+group+' at '+lst[i]
                lib.MessageBoxOK(mess,myname)
                continue
            nmol0=len(self.mol.atm)
            atm2=iatm+nmol0
            tmpatm=mol.CopyAtom()
            self.MergeMolecule(tmpatm,True,drw=False)
            self.ConnectGroups(atm1,atm2,drw=True)
            self.mol.atm[atm1].atmtxt=''
        
    def ReplaceNonAAResidue(self,drw=True):
        """ Replace a component moeclue with that in a file"""    
        
        wcard='pdb file(*.pdb)|*.pdb'
        pdbfile=lib.GetFileName(wcard=wcard,rw='r',check=True)
        if len(pdbfile) <= 0: return
        nsel,sellst=self.ListSelectedAtom()
        if nsel <= 0:
            #mess='No selected component molecules.'
            lib.MessageSelect('Model(RepalceNonAAResidue)',1)
            return
        resdatlst=self.ListSelectedResidues()
        resdat=resdatlst[0]
        resatmlst=self.ListResDatAtoms(resdat)
        # check link
        linked=False
        for i in resatmlst:
            atom=self.mol.atm[i]
            for j in atom.conect:
                if not j in resatmlst:
                    linked=True; break
        if linked:
            mess='Selected resdiue is linked to the other part.'
            lib.MessageBoxOK(mess,'Model(ReplaceNonAAResidue)')            
            return
        natm=len(self.mol.atm); nresatm=len(resatmlst)
        if nresatm <= 0: 
            mess='No atoms in resdat='+resdat
            lib.MessageBoxOK(mess,'Model(ExtratctPartsOfMolObject)')
            return
        # match the center of mass
        mass=nresatm*[1.0]; cc=[]
        for i in resatmlst: cc.append(self.mol.atm[i].cc[:])
        comcc0,eig,vec=lib.CenterOfMassAndPMI(mass,cc)
        # mol object of read molecue
        molobj=molec.Molecule(self)
        molobj.BuildFromPDBFile(pdbfile)
        newresdat=lib.ResDat(molobj.atm[0])
        mass=len(molobj.atm)*[1.0]; cc=[]
        for i in range(len(molobj.atm)):
            cc.append(molobj.atm[i].cc[:])
        comcc,eig,vec=lib.CenterOfMassAndPMI(mass,cc)
        for i in range(len(molobj.atm)):
            for j in range(3):
               molobj.atm[i].cc[j] += (comcc0[j]-comcc[j])
        # split current molecule
        molobjs=self.SplitMolObject(resatmlst,molobj)
        self.mol.atm=[]
        # merge parts
        for obj in molobjs:
            if obj is None: continue
            self.MergeMolecule(obj.atm,True,drw=False)
        self.SetSelectResidue(newresdat,True)
        # reset current molobject
        idx=self.molctrl.GetCurrentMolIndex()
        self.molctrl.SetMol(idx,self.mol)
        #
        if drw: self.DrawMol(True)
        #
        mess='"'+resdat+'" was replaced with the residue "'+newresdat
        mess=mess+'" in pdbfile='+pdbfile+'\n'
        self.ConsoleMessage(mess)
        self.MsgNumberOfAtoms(1)
        
    def ListHeavyAtoms(self,atmlst=[]):
        lstatm=[]
        if len(atmlst) <= 0: atmlst=self.ListTargetAtoms()
        for i in xrange(len(atmlst)):
            atom=self.mol.atm[i]
            if atom.elm == 'XX': continue
            if atom.elm == ' H': continue
            lstatm.append(i)
        return lstatm
        
    def CompareAAResidueSequence(self,molobj,filename,messout=True):
        ans=True; mess=''; diflst=[]
        aareslst0=self.mol.ListAAResSeq()
        aareslst1=molobj.ListAAResSeq()        
        if len(aareslst0) == len(aareslst1):
            for i in xrange(len(aareslst0)):
                res0=aareslst0[i]; res1=aareslst1[i]
                if res0 in const.HisRes: res0='HIS'
                if res1 in const.HisRes: res1='HIS'
                if res0 != res1: diflst.append([res0,res1])
            if len(diflst) > 0:        
                mess=mess+'The AA residue sequence is not same between current '
                mess=mess+'and that in '+filename+'\n'
                ans=False
        else:
            mess=mess+'Number of AA residues is different between currrent '
            mess=mess+' and in '+filename+'\n'
            ans=False
        if messout and len(mess)> 0: self.ConsoleMessage(mess)
        return ans,diflst
    
    def RepalceWithSameResdiue(self,pdbfile='',drw=True):
        """ Repalce missing atom residue with complete one
            the first 3 atoms are rms-fitted """
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
            
    def RepalceResdiueCoordinates(self,pdbfile='',drw=True):
        def GetPDBFile():
            wcard='PDB file(*.pdb)|*.pdb'
            mess='Open PDB file of resdiues to be replaced'
            pdbfile=lib.GetFileName(wcard=wcard,rw='r',message=mess)    
            if len(pdbfile) <= 0: return ''
            if not os.path.exists(pdbfile):
                mess='Not found file='+pdbfile
                lib.MessageBoxOK(mess,'Model(ReplaceResidues)') 
                pdbfile=''
            return pdbfile  
        #
        if pdbfile == '':
            pdbfile=GetPDBFile()
            if pdbfile == '': return
        #
        newresmol=molec.Molecule(self)
        newresmol.BuildFromPDBFile(pdbfile)
        newreslst=newresmol.ListResidues()
        newatmdic={}
        for resdat in newreslst:
            atmobjlst=newresmol.ListResidueAtoms(resdat)
            newatmdic[resdat]=atmobjlst
        oldatmlstdic={}
        for resdat in newreslst:
            for atom in self.mol.atm:
                res=lib.ResDat(atom)
                if res == resdat:
                    if not oldatmlstdic.has_key(resdat): 
                        oldatmlstdic[resdat]=[]
                    oldatmlstdic[resdat].append(atom.seqnmb)
        changelst=[]
        for resdat in newreslst:
            if not oldatmlstdic.has_key(resdat): continue
            changelst.append(resdat)
            newatmobjlst=newatmdic[resdat]
            oldatmlst=oldatmlstdic[resdat]
            for i in range(len(oldatmlst)):
                atom=self.mol.atm[oldatmlst[i]]
                atom.cc=newatmobjlst[i].cc[:]
                atom.select=True
        if len(changelst) <= 0:
            mess='Residues in pdbfile are not in current molecule.\n'
        else: 
            mess='Coordinates have changed of residues:\n'
            mess=mess+str(changelst)+'\n'
        mess=mess+'Replace pdbfile='+pdbfile
        self.ConsoleMessage(mess)
        #
        if drw: self.DrawMol(True)

    def RepalceResdiues(self,pdbfile='',drw=True):
        """ Not completed. 05Apr2016. Repalce residues """
        def GetPDBFile():
            wcard='PDB file(*.pdb)|*.pdb'
            mess='Open PDB file of resdiues to be replaced'
            pdbfile=lib.GetFileName(wcard=wcard,rw='r',message=mess)    
            if len(pdbfile) <= 0: return ''
            if not os.path.exists(pdbfile):
                mess='Not found file='+pdbfile
                lib.MessageBoxOK(mess,'Model(ReplaceResidues)') 
                pdbfile=''
            return pdbfile
        
        def SplitMolObjIntoResMol(molobj):
            """ split a component molecule """
            resmoldic={}
            resdatlst=molobj.ListResidues()
            for resdat in resdatlst:
                atmobjlst=molobj.ListResidueAtoms(resdat)
                if len(atmobjlst) <= 0: continue
                resmol=molec.Molecule(self)
                for atom in atmobjlst: resmol.atm.append(atom)
                resmoldic[resdat]=resmol
            return resmoldic
        
        def CompareAtoms(newresmol,oldresmol):
            dellst=[]; atmnamlst=[]; newnamlst=[]; missatmlst=[]
            for atom in oldresmol.atm: atmnamlst.append(atom.atmnam)
            for atom in newresmol.atm:
                atmnam=atom.atmnam
                if not atmnam in atmnamlst: dellst.append(atom.seqnmb) 
            if len(dellst) > 0: newresmol.DelAtoms(dellst)
            for atom in newresmol.atm: newnamlst.append(atom.atmnam)
            for atmnam in atmnamlst:
                if not atmnam in newnamlst: missatmlst.append(atmnam)
            return newresmol,missatmlst
        #
        if pdbfile == '':
            pdbfile=GetPDBFile()
            if pdbfile == '': return
        # create mol objects of current mol
        oldresmoldic=SplitMolObjIntoResMol(self.mol)
        oldreslst=self.mol.ListResidues()
        # create residue mol object
        newmolobj=molec.Molecule(self)
        newmolobj.BuildFromPDBFile(pdbfile)
        newresmoldic=SplitMolObjIntoResMol(newmolobj)
        # comapre residues in old and new
        dellst=[]
        for resdat,newresmol in newresmoldic.iteritems():
            if oldresmoldic.has_key(resdat):
                oldresmol=oldresmoldic[resdat]
                modmol,misslst=CompareAtoms(newresmol,oldresmol)
                if len(misslst) > 0:
                    mess='There are '+str(len(misslst))+' missing atoms in '
                    mess=mess+'replace pdb file.\n'
                    self.ConsoleMessage(mess+str(misslst))
                    mess=mess+'Would you like to continue?'
                    ans=lib.MessageBoxYesNo(mess,'Model(ReplaceResidues)')
                    if not ans: return
                newresmoldic[resdat]=modmol                                   
            else: dellst.append(resdat)
        # delete residues in newresmoldic
        if len(dellst) > 0:
            mess=''
            for resdat in dellst: 
                del newresmoldic[resdat]    
                mess=mess+resdat+' is not in current molecule. skipped.\n'
            self.ConsoleMessage(mess)
        if len(newresmoldic) < 0:
            mess='pdbfile does not have common residues in the current '
            mess=mess+'moelcue.'
            self.ConsoleMessage(mess)
            return
        # replace residues
        represlst=[]
        self.mol=molec.Molecule(self)
        firstres=oldreslst[0]
        if newresmoldic.has_key(firstres):
            self.mol.atm=newresmoldic[firstres].atm
            represlst.append(firstres)
        else: self.mol.atm=oldresmoldic[firstres].atm
        # 
        for i in range(1,len(oldreslst)):
            resdat=oldreslst[i]
            if newresmoldic.has_key(resdat): 
                mrgatm=newresmoldic[resdat].atm
                represlst.append(resdat)
            else: mrgatm=oldresmoldic[resdat].atm
            self.MergeMolecule(mrgatm,check=True,drw=False)    
        # select replaced reidues
        self.SelectResidueByList1(represlst,True,drw=False) 
        # reset current molobject
        idx=self.molctrl.GetCurrentMolIndex()
        self.molctrl.SetMol(idx,self.mol)
        #
        mess=str(len(represlst))+' residues were replaced.\n'
        mess=mess+'Replaced residues: '+str(represlst)+'\n'
        mess=mess+'in pdbfile='+pdbfile
        self.ConsoleMessage(mess)
        self.MsgNumberOfAtoms(1)
        #
        if drw: self.DrawMol(True)
            
    def SplitMolObject(self,resatmlst,molobj):
        """ split a component molecule """
        partobj=molec.Molecule(self)
        natm=len(self.mol.atm); nresatm=len(resatmlst)
        atm0=resatmlst[0]
        part1obj=None; part2obj=None
        if atm0 == 0: part1obj=None
        elif atm0+nresatm == natm-1: partobj2=None
        else:
            part1obj=molec.Molecule(self)
            part2obj=molec.Molecule(self)
        if part1obj is not None:
            k=-1
            for i in range(0,atm0):
                atom=self.mol.atm[i]; k += 1; atom.seqnmb=k
                part1obj.atm.append(atom)
        for i in range(len(molobj.atm)):
            atom=molobj.atm[i]; atom.seqnmb=i; atom.select=True
            partobj.atm.append(atom)
        if part2obj is not None:
            k=-1
            for i in range(atm0+nresatm,natm):
                atom=self.mol.atm[i]; k += 1; atom.seqnmb=k
                part2obj.atm.append(atom)
        #
        return part1obj,partobj,part2obj
    
    def AddGroup1H(self):
        #Add one H at selected atom
        #bndlst=[]; 
        nh=0
        lst=self.ListTargetAtoms()
        self.mol.AddGroup1Hydrogen(lst)

        self.ResetPosAtm()
        self.DrawMol(True)
   
    def AddGroup2H(self):
        #Add one H at selected atom
        #bndlst=[];
        nh=0
        lst=self.ListTargetAtoms()
        self.mol.AddGroup2Hydrogen(lst)
        #
        self.ResetPosAtm()
        self.DrawMol(True)
        
    def AddGroup3H(self):
        #Add H3 at selected atom
        lst=self.ListTargetAtoms()
        self.mol.AddGroup3Hydrogen(lst)
        self.ResetPosAtm()
        #
        self.DrawMol(True)
 
    def AddGroupCH3(self):
        print 'AddGroupCH3'

    def AddGroupACE(self):
        print 'AddGroupACE'

    def AddGroupNME(self):
        print 'AddGroupNME'

    def DeleteSelected(self,drw=True):
        
        nsel,lst=self.ListSelectedAtom()
        if nsel <= 0:
            mess='No selected atoms'
            self.Message(mess,0,'blue')
            return
        #
        # the old codes are commented
        #nd=0
        #for i in lst:  
        #    ia=i-nd
        #    self.mol.DelAtom(ia); nd += 1
        self.mol.DelAtoms(lst)
        #self.FitToScreen(False)
        if drw: self.DrawMol(True)
                                     
    def DeleteWater(self,atmlst=[],drw=True):
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        self.mol.DelWater(lst)
            
        #self.FitToScreen(False)
        if drw: self.DrawMol(True)
    
    def DeleteNonBonded(self,atmlst=[],drw=True):
        #nsel,lst=self.ListSelectedAtom()
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        self.mol.DelNonBonded(lst)

        self.FitToScreen(False,drw)
        #self.DrawMol(True)
      
    def DeleteHydrogens(self,atmlst=[],drw=True):
        lst=atmlst
        if len(lst) <= 0: lst=self.ListTargetAtoms()
        self.mol.DelHydrogen(lst)      
        self.FitToScreen(False,drw)
        #self.DrawMol(True)
    
    def DeleteAllTers(self,drw=True):
        dellst=[]
        for i in xrange(len(self.mol.atm)):
            if self.mol.atm[i].elm == 'XX': dellst.append(i)
        if len(dellst) > 0: 
            self.mol.DelAtoms(dellst)
            mess=str(len(dellst))+" TERs were deleted."
            self.Message2(mess)
            if drw: self.DrawMol(True)
        else:
            mess="No TER's were found."
            self.Message(mess,0,"black")
    
    def DeleteAllDummyAtoms(self,drw=True):
        dellst=[]
        for i in xrange(len(self.mol.atm)):
            if self.mol.atm[i].elm == ' X': dellst.append(i)
        if len(dellst) > 0: 
            self.mol.DelAtoms(dellst)
            mess=str(len(dellst))+" Dummy atoms were deleted."
            self.Message(mess,0,"black")
            if drw: self.DrawMol(True)
        else:
            mess='No dummy atoms were found'
            self.Message(mess,0,"black")    
        
    def DeleteTerAtHead(self,mol,drw=True):
        fromargs=False
        if mol == None:
            if not self.mdlargs.has_key('DeleteTerAtHead'): return
            mol=self.mdlargs['DeleteTerAtHead']
            fromargs=True
        nter=0; head=True
        try:
            while head:
                if mol.atm[0].elm == 'XX':
                    nter += 1; mol.DelAtoms([0])
                else: head=False
        except: pass
        
        if nter > 0:
            mess=str(nter)+"TERs at head part are deleted."
            self.Message(mess,0,"black")
            if drw: self.DrawMol(True)
        if fromargs: del self.mdlargs['DeleteTerAtHead']

    def DeleteBonds(self,kind,drw=True): 
        bond=False; extrabond=False
        lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        if kind == 'all':  # tentative
            self.mol.DelAllKindBonds(lst)
            if drw: self.DrawMol(True)
            return
        # the folowing codes are imcomplet, 8Apr2013[KK}
        else:
            nbnd=0; lstdel=[]
            nlst=len(lst)
            if nlst > 0:
                n=len(lst)
                for i in xrange(n-1):
                    ii=i #self.mol.atm[lst[i]].seqnmb
                    
                    for j in xrange(i+1,n):
                        jj=j #self.mol.atm[lst[j]].seqnmb
                        try:
                            self.mol.DelBond(ii,jj); nbnd += 1
                            bond=True
                        except: pass
                        try:
                            extrabond=True
                            self.mol.DelHydrogenBond([ii,jj])
                            self.DrawVdwBond(False)

                            #self.mol.DelExtraBond([ii,jj]); nbnd += 1
                        except: pass
            if nbnd <= 0:
                self.Message('No '+kind+' bonds',0,'black')
                return
            if nbnd > 0 and drw: self.DrawMol(True)
                #if bond: self.DrawMol(True)
                #if extrabond:
                #    self.draw.SetDrawExtraBondData(False,[])  
                #    self.DrawHBOrVdwBond(True)

    
    def DeleteBondIJ(self,atm1,atm2,drw=True):
        try:
            self.mol.DelBond(atm1,atm2)
            if drw: self.DrawMol(True)
        except: pass
        """
        try:
            self.mol.DelExtraBond([atm1,atm2]) #DelHydrogenBond([atm1,atm2])
            self.DrawHBOrVdwBond(True) #self.DrawVdwBond(True)
        except: pass
        """

    def ClearLayer(self,layer,drw=True):
        drwlabel='Layer by color'
        self.SaveLayerData(True)
        if layer == 999:
            for i in xrange(len(self.mol.atm)):
                self.mol.atm[i].layer=1
                self.mol.atm[i].color=self.savatmcol[i]
        else:    
            lst=self.ListTargetAtoms()
            for i in lst:
                if self.mol.atm[i].layer == layer:
                    self.mol.atm[i].layer=1
                    self.mol.atm[i].color=self.savatmcol[i]
        if self.ctrlflag.Get(drwlabel) and drw: self.DrawMol(True)

    def DelAllFragmentAttributes(self):
        # attriblst: defined in the 'subwin.FragmentAttrib_Frm' class
        #attriblst=['IFREEZ','DOMAIN(FD/FDD)','LAYER','MULT','ICHARG',
        #          'SCFTYP','MPLEVL','DFTTYP','CITYP','CCTYP','TDTYP','SCFFRG','IEXCIT']
        attriblst=self.setctrl.FragmentAttributeList()
        for attr in attriblst:
            self.DelFragmentAttribute(attr)        

    def SaveLayerData(self,save):
        if self.mol is None: return
        if save:
            self.savlayer=[]
            for atom in self.mol.atm:
                self.savlayer.append(atom.layer)
        else:
            for i in xrange(len(self.mol.atm)):
                self.mol.atm[i].layer=self.savlayer[i]
    
    def IsPDBAtmNamNew(self):
        ans=True
        oldnamlst=const.AtmNamOldToNew.keys()
        for atom in self.mol.atm:
            if const.AmiRes3.has_key(atom.resnam): continue
            if atom.atmnam in oldnamlst:
                ans=False; break
        return ans
        
    def ChangeAtmNamToNew(self):
        for atom in self.mol.atm:
            res=atom.resnam; atmnam=atom.atmnam
            if not const.AmiRes3.has_key(res): continue
            if const.AtmNamOldToNew.has_key(atmnam):
                atom.atmnam=const.AtmNamOldToNew[atmnam]
    
    def ChangeAtmNamToOld(self):
        NewToOld=lib.InvertKeyAndValueInDic(const.AtmNamOldToNew)
        for atom in self.mol.atm:
            res=atom.resnam; atmnam=atom.atmnam
            if not const.AmiRes3.has_key(res): continue
            if NewToOld.has_key(atmnam):
                atom.atmnam=NewToOld[atmnam]

    def ChangeChargeOfSelectedAtoms(self,drw=True,messout=True):
        inpchg=wx.GetTextFromUser('Enter charge, ex. "1.0" do not tyoe ")',
                                  'Change charges of selected atoms')        
        nchg=0
        for atom in self.mol.atm:
            if atom.select:
                atom.charge=float(inpchg); nchg += 1     
        mess=str(nchg)+' atom charges were changed.'
        self.Message(mess,0,'')
        if messout: self.ConsoleMessage(mess)
        if drw: self.DrawFormalCharge(True)
            
    def ChangeCharge(self):
        """ Change Ion charge """
        if self.mol is None: return
        if len(self.mol.atm) <= 0: return
        label=['!seq#','!atmnam','!resdat','!element','charge']
        width=[60,60,80,60,60]
        chgdat=self.MakeIonChargeData()
        if len(chgdat) <= 0:
            mess='No ions.'
            lib.MessageBoxOK(mess,'Model(ChangeCharge)')
            return
        chgwin=subwin.GetInputFromUser_Frm(self.mdlwin,-1,'Set Ion Charges',
                       model=self,labels=label,values=chgdat,
                       cellwidth=width,retmethod=self.RetChangeCharge)

    def MakeIonChargeData(self):
        chgdat=[]
        for atom in self.mol.atm:
            if not const.IonAtmChg.has_key(atom.elm): continue
            elm=atom.elm
            #if elm == ' H' or elm == ' O' or elm == ' S': continue
            #    if len(atom.conect) > 0: continue
            seq=atom.seqnmb; atmnam=atom.atmnam; resdat=lib.ResDat(atom)
            elm=atom.elm; charge=atom.charge
            chgdat.append([seq+1,atmnam,resdat,elm,charge])
        return chgdat
        
    def RetChangeCharge(self,retmess,chgdat,messout=True):
        if retmess == 'OnApply':
            if len(chgdat) <= 0: return
            mess='Changed ion chages:\n'
            for i in range(len(chgdat)):
                chgdati=chgdat[i]
                seq=chgdati[0]-1; atmnam=chgdati[1]; resdat=chgdati[2]
                elm=chgdati[3]; charge=chgdati[4]
                self.mol.atm[seq].charge=charge
                mess=mess+str(seq+1)+', '+atmnam+', '+resdat+', charge='+str(charge)
                mess=mess+'\n'
            if messout: self.ConsoleMessage(mess)    
        elif retmess == 'OnClose':
            pass
            
    def ChangeGroupCharge(self):
        lib.MessageBoxOK('Sorry, not implemented yet.', 'ChangeGroupCharge')
                
    def SaveFragmentDataAs(self,filename):
        #
        if len(filename) <=0: return       
        #self.mol.WriteFrgDat(filename)
        molnam,resnam,bdalst,frgtbl,frglst=self.mol.MakeFrgDatForWrite()
        rwfile.WriteFrgDatFile(filename,molnam,resnam,bdalst,frgtbl,frglst)
    
    def ReadBDABAA(self,filename):
        """
        :return: natm(int) --- number of atoms
        :return: bdalst(lst) --- [[bda(str),baa(str)],...]
        """
        natm=0; bdastrlst=[]
        if not os.path.exists(filename):
            mess='BDA file does not exist. file='+filename
            self.ConsoleMessage(mess)
            return natm,bdastrlst
        f=open(filename,'r')
        i=0
        for s in f.readlines():
            s=s.strip()
            if s[:1] == '#': continue
            nc=s.rfind('#')
            if nc >= 0: s=s[:nc]; s=s.strip()
            if len(s) <= 0: continue
            i += 1
            if i == 1: natm=int(s)
            else:
                items=s.split(',')
                if len(items) < 2:
                    mess='Error in reading bda file at line'+str(i)+' in file='+filename
                    self.ConsoleMessage(mess)
                    return 0,[]
                bdastrlst.append([items[0].strip(),items[1].strip()])
        f.close()
        
        return natm,bdastrlst
             
    def ReorderHydrogensIntoTinker(self):
        newmol=molec.Molecule(self)
        lst=[]
        for i in xrange(len(self.mol.atm)): lst.append(i)
        natm=len(self.mol.atm)
        i=0; na=0; nres=0; nresatm=0; iatm=-1
        while na < natm:
            i += nresatm
            ia=lst[i]
            resnam=self.mol.atm[ia].resnam
            resnmb=self.mol.atm[ia].resnmb
            nres += 1
            nresatm,resdat,atmnamdic=self.mol.ExtractAARes(resnam,resnmb,ia) 
            #ReorderAtomsInResidue(resdat)
            for atom in resdat:
                if atom.elm == ' H': continue
                iatm += 1; atom.seqnmb=iatm
                newmol.mol.append(atom)
            for atom in resdat:
                if atom.elm != ' H':continue
                iatm += 1; atom.seqnmb=iatm
                newmol.mol.append(atom)
            na += nresatm
        
        self.mol=newmol
        # make bond data
        lst=[]
        for i in xrange(len(self.mol)): lst.append(i)
        self.mol.DelAllKindBonds(lst)
        self.mol.AddBondUseBL(lst)
        
    def RenameAtmNamIntoTinker(self):
        natm=len(self.mol.atm)
        #i=0; na=0; nres=0; nresatm=0
        for ia in xrange(natm):
            #i += nresatm
            resnam=self.mol.atm[ia].resnam
            resnmb=self.mol.atm[ia].resnmb
            #nres += 1
            nresatm,resdat,atmnamdic=self.mol.ExtractAARes(resnam,resnmb,ia) 
            for atom in resdat:
                if atom.elm != ' H':continue
                atmnam=atom.atmnam
                atmnam=atmnam.lstrip()
                ns=len(atmnam)
                atmnam=atmnam[0:ns]; atmnam=atmnam.strip(); ms=len(atmnam)
                if atmnam[0:1].isdigit():
                    atmnam=atmnam[1:ms]+atmnam[0:1]+'    '
                    if ns < 4: atmnam=(4-ns)*' '+atmnam
                    atmnam=atmnam[0:4]
                    atom.atmnam=atmnam          
            #na += nresatm
          
    def AssignAAAtomCharge(self,drw=True):
        if not self.mol.AssignAAResAtmChg():
            mess='Fragmentation is not ready, since molecule is modified!'
            mess=mess+' Save as PDB and Open it aggain.'
            self.Message(mess,1,'blue')                
        else:
            self.Message('Assigned formal charge to AA residues',0,'black') 
        if drw: self.DrawFormalCharge(True)
        
    def ManualBDASetting(self,on):
        # on(bool): True for turn on BDA mode, False for turn off
        selmod=self.mousectrl.GetSelMode()
        selobj=self.mousectrl.GetSelObj()
        if on: 
            self.mol.CreateFrgConDat()
            self.mousectrl.SetBDAMode(True)
            #?self.mousectrl.SetPointedAtomHis([])
            self.mousectrl.pntatmhis.Clear()
            self.ctrlflag.Set('pntatmhis',[])
            self.SaveMouseSelMode()
            self.SetMouseSelModeForTwo()
            self.Message('Manual fragmentation',1,'black')
            #self.mdlwin.menu.Check('BDA points',True) 
            self.SetDrawItemsAndCheckMenu('BDA points',True)          
        else:
            self.mousectrl.SetBDAMode(False)
            self.RecoverMouseSelMode()
            self.Message('',1,'black')
            #self.mdlwin.menu.Check('BDA points',False)    
            #self.draw.SetDrawBDAPonitData(False,[])
            #self.DrawMol(True)
            #
    def ClearBDA(self):
        # clear BDAs
        lst=self.ListTargetAtoms()
        if len(lst) <= 0: return
        self.mol.ClearBDABAA(lst)
        self.mol.ClearFragmentName()
        self.mol.SetFragmentName()
        #self.SetSelectAll(False)
        drwlabel="Paint fragment"
        if self.ctrlflag.Get(drwlabel): self.ShowFragmentByColor(False)
        drwlabel="BDA points"
        if self.ctrlflag.Get(drwlabel): self.DrawBDAPoint(False)
            
    def ClearAtomCharge(self,drw=True,messout=True):
        # clear charges for counting fragment charge
        lst=self.ListTargetAtoms()
        self.mol.ClearFormalCharge(lst)
        if drw: self.DrawFormalCharge(True)
        if messout:
            mess='Atom charges were set to 0 of '+str(len(lst))+' atoms'
            self.ConsoleMessage(mess)
    
    def BondLengthInfo(self,elmi='',elmj='',view=True,plot=False,
                        outfile='',messout=True):
        def Skip(elmi,elmj,ielm,jelm):
            skip=False
            if elmi != '':
                if ielm != elmi and jelm != elmi: skip=True
            if elmi != '' and elmj != '':
                if ielm != elmi or jelm != elmi: skip=True
                if ielm != elmj or jelm != elmj: skip=True
            return skip
        #            
        blk='  '; fi4='%4d'; fi6='%6d'; ff8='%8.3f'
        if elmi == '' and elmj != '':
            elmi=elmj; elmj=''
        if elmi != '': elmi=lib.ElementNameFromString(elmi)
        if elmj != '': elmj=lib.ElementNameFromString(elmj)
        elmlst=self.ListElement()
        mess=''
        if not elmi in elmlst:
            mess=mess+'Not founf elmi="'+elmi+'"\n'
        if not elmj in elmlst:
            mess=mess+'Not founf elmj="'+elmi+'"\n'
        if messout and len(mess) > 0:
            lib.MessageBoxOK(mess,'Model(PrintBondLength)')
        #
        bnddic=self.ComputeBondLength()
        ndat=len(bnddic)
        between=''
        if elmi != '':
            between='between elements "'+elmi+'" and '
            if elmj == '': between=between+'all elements\n'
            else: between=between+'"'+elmj+'"'
        title='Bond Length'
        if len(between) > 0: title=title+' '+between
        #
        text=''
        if view or outfile != '':
            text='Bond length in '+self.mol.inpfile+'\n'
            if len(between) > 0: text+'    '+between+'\n'
            text=text+'data #,r(A) and atom number,element,atom name,'
            text=text+'residue(name:number:chain) for atom i and j\n'
            k=0
            for i in xrange(ndat):
                r=bnddic[i][0]; itemi=bnddic[i][1]; itemj=bnddic[i][2]        
                if Skip(elmi,elmj,itemi[1],itemj[1]): continue
                k += 1
                text=text+(fi6 % k)+blk # data number
                text=text+(ff8 % r)+blk # r
                texti=(fi4 % (itemi[0]+1))+blk+itemi[1]+blk+itemi[2]+blk+itemi[3]
                textj=(fi4 % (itemj[0]+1))+blk+itemj[1]+blk+itemj[2]+blk+itemj[3]
                if itemi[1] == ' H': text=text+textj+blk+texti+blk
                else: text=text+texti+blk+textj+blk
                text=text+'\n'
        # plot
        if plot:
            k=0; x=[]; y=[]; pairlst=[]
            for i in xrange(ndat):
                r=bnddic[i][0]; itemi=bnddic[i][1]; itemj=bnddic[i][2]        
                if Skip(elmi,elmj,itemi[1],itemj[1]): continue
                atmi=itemi[0]; atmj=itemj[0]
                k += 1
                x.append(k); y.append(r); pairlst.append([atmi,atmj])
            #
            pltbl=subwin.PlotAndSelectAtoms(self.mdlwin,-1,self,
                                            "Plot bond length","atom pair")
            pltbl.SetGraphType("bar")
            pltbl.SetColor("b")
            pltbl.NewPlot()
            pltbl.PlotXY(x,y)
            pltbl.SetAtomPairList(pairlst)
            #title='Bond Length'
            #if len(between) > 0: title=title+' '+between
            pltbl.PlotTitle(title)
            pltbl.PlotXLabel('Data numbers')
            pltbl.PlotYLabel('Length(Angstrom)')
        # view
        if view:
            self.menuctrl.OnWindow("Open EasyPlotWin",True)
            win=self.winctrl.GetWin("Open EasyPlotWin")
            win.SetTitle(title)
            win.ClearText()
            win.outtext.AppendText(text)
        # write on file
        if outfile != '':
            text='# Created by fu at '+lib.DateTimeText()+'\n'+text
            f=open(outfile,'w'); f.write(text); f.close
        
        return text                    

    def ComputeBondLength(self,rmin=-1,rmax=-1):
        def AtomItem(i):
            seqi=self.mol.atm[i].seqnmb; resi=lib.ResDat(self.mol.atm[i])
            elmi=self.mol.atm[i].elm; atmi=self.mol.atm[i].atmnam
            return [seqi,elmi,atmi,resi]
        def BondIdx(i,j):
            minij=min(i,j); maxij=max(i,j)
            idx=str(minij)+':'+str(maxij)
            return idx
                
        bnddic={}; natm=len(self.mol.atm); npair=0; donedic={}
        # fortran code
        try:
            if rmin < 0: rmin=0.5
            if rmax < 0: rmax=3.0
            cc=[]; iopt=0
            for i in xrange(natm): cc.append(self.mol.atm[i].cc)
            cc=numpy.array(cc)
            npair,iatm,jatm,rij=fortlib.find_contact_atoms2(cc,rmin,rmax,iopt)
            count=-1
            for k in xrange(npair):
                i=iatm[k]; j=jatm[k]; r=rij[k]
                if self.mol.atm[i].elm == 'XX': continue
                if self.mol.atm[j].elm == 'XX': continue
                if not j in self.mol.atm[i].conect: continue
                idx=BondIdx(i,j)
                if donedic.has_key(idx): continue
                itemi=AtomItem(i); itemj=AtomItem(j) 
                count += 1
                bnddic[count]=[r,itemi,itemj]
                donedic[idx]=True
        except:
            mess='Model:ComputeBondDistance: running python code'
            self.ConsoleMessage(mess)
            count=-1
            for i in xrange(natm):
                if self.mol.atm[i].elm == 'XX': continue
                itemi=AtomItem(i); cci=self.mol.atm[i].cc
                for j in self.mol.atm[i].conect:
                    idx=BondIdx(i,j)
                    if donedic.has_key(idx): continue
                    itemj=AtomItem(j); ccj=self.mol.atm[j].cc
                    r=lib.Distance(cci,ccj)                
                    count += 1
                    bnddic[count]=[r,itemi,itemj]
                    donedic[idx]=True  
        return bnddic
        
    def AccessPDBj(self):
        print 'AccessPDBj: Sorry, not implemented'
        lib.AccessPDBj()

    def SaveCanvasImage(self,filename,imgwidth=-1):
        """ Save canvas image on file
        
        :param str filename: extension should be '.bmp','png', or '.pdf'
        if not give (''), filename will be created. 
        """
        # close MouseModeWin if it is open
        ismousewin=self.mdlwin.IsMusWinOpen()
        ismolwin=self.mdlwin.IsMolWinOpen()
        if ismousewin: self.mdlwin.mousemode.win.Hide()
        if ismolwin: self.mdlwin.molchoice.win.Hide()        
        #
        bgcolor=self.mol.GetBGColor()
        #if bgcolor == None: bgcolor=self.setctrl.GetParam('win-color')
        imgcolor=self.setctrl.GetParam('image-bgcolor')
        samecolor=True
        for i in range(len(bgcolor)):
            if bgcolor[i] != imgcolor[i]: samecolor=False
        #if not self.IsTheSameColor(bgcolor,imgcolor):
        if not samecolor:
            self.ChangeBackgroundColor(imgcolor)
            self.DrawMol(True)
        # capture window image
        platform=lib.GetPlatform() 
        if platform == 'WINDOWS' or platform == 'LINUX':
            winobj=self.mdlwin.draw.canvas
            retmess,img=lib.CaptureWindowW(winobj,True)
        elif platform == 'MACOSX':
            winobj=self.mdlwin.draw.canvas
            [x,y]=winobj.ClientToScreen(winobj.GetPosition())
            [w,h]=winobj.GetClientSize()
            y += 60; h -= 60
            rect=[x,y,w,h]
            retmess,img=lib.CaptureWindowM(rect)
        else:
            img=None
            retmess='fumodel.SaveCanvasImage:The platform '+platform+' is not supported.'  
        # convert bmp to wx.Image object
        #img=bmp.ConvertToImage() 
        if img:
            if imgwidth > 0:
                lib.MessageBoxOK('Sorry. Changing image size is underconstructio!')
                """ debug """
                #self.ConsoleMessage('imgwidth='+str(imgwidth))
            
                #size=img.GetSize()
                #ratio=float(imgwidth)/float(size[0])
                #imgheight=int(size[1]*ratio)
                #imgsize=[imgwidth,imgheight]
                
                """ debug """
                #self.ConsoleMessage('resized imgwidth,imgheight='+str(imgwidth)+','+str(imgheight))
                
                #img=lib.ImageThumnail(img,imgsize)
                """ debug """
                #self.ConsoleMessage('After ImageThimbnail')

            # make file name using datetime
            if len(filename) <= 0:
                date=datetime.datetime.today()
                fuimgdir=self.setctrl.GetDir('Images')
                molnam=self.mol.name
                imgtyp=self.setctrl.GetParam('image-format')
                #file=molnam+'-'+date.strftime("%Y%m%d%H%M%S")+'.'+imgtyp
                base,ext=os.path.splitext(molnam)
                file=lib.MakeFileNameWithDateTime(base+'-','.'+imgtyp)
                filename=os.path.join(fuimgdir,file)
            retmess=lib.SaveImageOnFile(filename,img) #,imgtyp)
        #
        if not self.suppressmess: self.Message2(retmess)
        # reopen mousemodewin and molchoicewin
        if ismousewin: self.mdlwin.mousemode.win.Show()
        if ismolwin: self.mdlwin.molchoice.win.Show()        
        if not samecolor:
            self.ChangeBackgroundColor(bgcolor)

    def PrintCanvasImage(self):
        """ !!! needs codes !!! Print canvas image 
        """
        pass

    def SetLoggingMethod(self):
        self.ConsoleMessage('')
        self.ConsoleMessage('# logging:')
        logmethfile=self.setctrl.GetParam('logging-method-file')
        #self.ConsoleMessage('logmethfile='+'"'+logmethfile+'"')
        if len(logmethfile) <= 0:
            curdir=os.getcwd()
            custmdir=self.setctrl.GetDir('Customize')
            os.chdir(custmdir)
            wcard='method (*.method)|*.method'
            mess='Select logging method definition file'
            file=lib.GetFileName(self.mdlwin,wcard,'r',True,'',message=mess)
            if file != '': logmethfile=file
            os.chdir(curdir)
        if len(logmethfile) > 0: const.LOGGINGMETHODDIC=rwfile.ReadLoggingMethodFile(logmethfile)
        if len(const.LOGGINGMETHODDIC) <= 0:
            mess='# No logging methods are defined in file="'+logmethfile+'".'
            self.ConsoleMessage(mess)
        else:
            methnmb=len(const.LOGGINGMETHODDIC.keys())
            mess='# Logging methods are read.\n'
            mess=mess+'# Number of methods='+str(methnmb)+' in logmethfile="'+logmethfile+'".'
            self.ConsoleMessage(mess)

    def SaveLog(self,on,logfile=''):
        if len(const.LOGGINGMETHODDIC) <= 0:
            mess='# No logging methods are defined in file='+logmethfile
            self.ComsoleMessage(mess)
            self.setctrl.SetParam('save-log',False)
            self.menuctrl.CheckMenu('Save log',False)
            return
        self.setctrl.SetParam('save-log',on)
        self.menuctrl.CheckMenu('Save log',on)
        #self.Echo(on)
        if on:
            # open log and result file
            if logfile == '':
                logdir=self.setctrl.GetDir('Logs') 
                base='fu-'; ext='.logging'
                logfile=lib.MakeFileNameWithDateTime(base,ext)       
                logfile=os.path.join(logdir,logfile)
            else: pass
            resultfile=logfile.replace('.logging','.result')
            if not os.path.exists(logfile):
                text='# fu logging\n'
                text=text+'# '+lib.CreatedByText()+'\n'
                text=text+'# result file='+resultfile+'\n'
                f=open(logfile,'w')
                f.write(text)
                f.close()
            if not os.path.exists(resultfile):
                text='# fu results\n'
                text=text+'# '+lib.CreatedByText()+'\n'
                text=text+'# logging file='+logfile+'\n'
                f=open(resultfile,'w')
                f.write(text)
                f.close()
            #
            self.ctrlflag.Set('logfile',logfile)
            self.ctrlflag.Set('resultfile',resultfile)
            lib.LOGGING=True
            lib.LOGFILE=logfile
            lib.RESULTFILE=resultfile
            lib.FILENAMEDIC={}
            mess='\nLogging starts. logfile='+logfile+'\n'
            mess=mess+'resultfile='+resultfile+'\n'
            self.ConsoleMessage(mess)
        else: 
            # close log file
            if len(lib.FILENAMEDIC) > 0:
                f=open(lib.LOGFILE,'r')
                text=f.readlines()
                f.close()
                # replace filename with name
                text1=[]
                for s in text:
                    for name,filename in lib.FILENAMEDIC.iteritems():
                        ns=s.find(filename)
                        if ns >= 0: s=s.replace(filename,name)
                    text1.append(s)
                text=text1
                # 
                text.insert(3,'#\n')
                text.insert(4,'# files used in this session\n')
                i=4
                for name,filename in lib.FILENAMEDIC.iteritems():
                    i += 1
                    text.insert(i,name+'='+filename+'\n')
                text.insert(i+1,'#\n')
                f=open(lib.LOGFILE,'w')
                for s in text: f.write(s)
                f.close()
            mess='\nLogging stopped at '+lib.DateTimeText()+'\n'
            mess=mess+'logfile='+lib.LOGFILE
            self.ConsoleMessage(mess)
            self.ctrlflag.Del('logfile')
            self.ctrlflag.Del('resultfile')
            lib.LOGGING=False
            lib.LOGFILE=''
            lib.RESULTFILE=''
            lib.FILENAMEDIC={}
    
    def ViewSettingParams(self):
        text='# Current setting parameters '+lib.DateTimeText()+'\n'
        text=text+'# All parameters are redefined in the "fumodelset.py" '
        text=text+' script\n'
        text=text+'# which is executed at the activation\n\n'
        text=text+self.setctrl.ListSettingParams()
        title="Setting paramters"; winsize=[640,400]
        viewer=subwin.TextViewer_Frm(self.mdlwin,title=title,text=text,
                                     winsize=winsize,menu=True)
        viewer.RemoveOpenMenu()
        
    def HelpDocument(self):
        """ helpfile: *.hhp or *.zip """
        #helpfile='h://FUDATASET//FUdocs//fumodeldoc//testing.hhp'
        helpdir=self.setctrl.GetDir('FUdocs')
        helpdir=os.path.join(helpdir,'fumodel')
        book='fumodel-usersdoc.hhp'
        helpfile=os.path.join(helpdir,book)
        helpfile=lib.ReplaceBackslash(helpfile)
        if not os.path.exists(helpfile):
            mess='Not found helpfile='+helpfile
            lib.MessageBoxOK(mess,'Model(UsersGuide)')
            return
        curdir=os.getcwd()
        os.chdir(helpdir)
        self.htmlhelpctrl=wx.html.HtmlHelpController() #parentWindow=self.mdlwin)      
        retcode=self.htmlhelpctrl.AddBook(book)
        if retcode: 
            self.htmlhelpctrl.DisplayContents()
            self.htmlhelpctrl.DisplayIndex()
            self.htmlhelpctrl.Display("sub book")
        os.chdir(curdir)
        ##wx.tools.helpviewer.main(helpfile)
        
    def OnShowHelpContents(self,event):
        """ Event handler of wx.html.HtmlHelpConytroller(cteated by UsersGuide) """ 
        self.htmlhelpctrl.DisplayContents()
        self.htmlhelpctrl.DisplayIndex()
        self.htmlhelpctrl.Display("sub book")

    def AboutMessage(self):
        """ Open 'About' message box
        
        :param str title: title
        :note: icon file 'fumodel.png' should be in FUPATH/Icons directory.
        """
        #iconfile=self.setctrl.GetFile('Icons','fumodel.png')
        title='fumodel in '
        lib.About(title,const.FUMODELLOGO)

    def CreatePanel(self):
        # fu logo
        bitmap=self.FULogo()
        self.SetBackgroundColour('lighyt gray')
        self.SetTitle('Openning FU')
        wx.StaticBitmap(self,-1,bitmap,(30,20),(40,28))
        wx.StaticText(self,-1,'Welcome to FU ...',pos=(90,30),size=(180,22)) 
        # timer    
        self.timer=wx.Timer(self)
        self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
        self.count=0
        self.prgbar=wx.Gauge(self,-1,pos=(200,30),size=(60,10),
                             style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)     
        self.timer.Start(20)
        #     
        self.Show()
    
    def OnTimer(self,event):
        self.count += 1
        if self.count >= 120 : self.count=0
        self.prgbar.SetValue(self.count)
    
    def OnClose(self,event):
        try: self.timer.Stop()
        except: pass
        self.Quit()
    
    def HideOpenningWin(self):
        try: self.timer.Stop()
        except: pass
        self.Hide()
        
    def FULogo(self):
        """ This file was generated by C:\Python27\Scripts\img2py """
        from wx.lib.embeddedimage import PyEmbeddedImage
        # source image file="FUDATASET//fu4028.png"
        fu4028 = PyEmbeddedImage(
        "iVBORw0KGgoAAAANSUhEUgAAACgAAAAcCAYAAAATFf3WAAAAAXNSR0IArs4c6QAAAARnQU1B"
        "AACxjwv8YQUAAAAJcEhZcwAADsIAAA7CARUoSoAAAAh8SURBVFhHzVgLbFTHFT379r/rXa/t"
        "XZvFv1ITjCGJaQsEEFSiqQrBNIUAhrZpcFJIqqZRKpGojUgl1OZD2gQQARGpQQ0NpJBGClIk"
        "QwMVpC3GccDm42AwNviDvfauP7vr/f9ez7x9jXGLqkJbiTO6fjPv3bn3zp1778xaIxO4iyGp"
        "z7sWEwwc9Y9gNDiijoBoLATfkFcdAZlMHB7vgDr6z+D1eRGMBNXRv0ckFoNnYKL8L7Z4+ey3"
        "EAoGMCy1wFY8iMe+8Qb+sP8YRuJtMJd34/sLfo6j9Z3oG20Fii7inV278dU59ytCbgVfjw9H"
        "fnwEna2daDW2onRZKXZs36F+/Ve8/+yz6G1txSUaeJYmnW5qgjknB5pIOCYvLzuFacOliMOH"
        "QXyOFhzEN7ELFiTQj3PowAmU4FuYjnnoQxM8aMNpvIq9b/8eT/xwnapiHKHeEFrKWuBi62Pr"
        "ZdvJhvuA5gvNKlcWwjuNGzciLxJB1GrF514v2vr78cpnn6Hr+nVIF/+aRMnw12CDA3rYYSQV"
        "oJgGlXNsVca5VFSGe5TvBmXsRD5m41evbM1quQkZttBrIVSzOdlsbBa2r7O1XGxBc9NEA0db"
        "WlCRTqO4pAQWoxE2gwF5djummUx4e/duSHlGK1XmwO1wwaazQwMdA9MIp9UChyGfI70ydhh1"
        "cJpz2TeQTJyTB29/BIOD4zEqkPamoT2m5Xc7nHYncjQ5nG3kLAOmsNUfqlc5s0hduoT83FzY"
        "CgvhtNlg1OthIk3Ky8Pf6ushZVLCJC2ifsFtoDkmjrSgxxFJhpGmR2T+jSQ0CMdjZEoLRm5+"
        "HHpzBkVFhULPOEzkKEnzewLhcBgxOUbuFJJsYbbyynKVMQuNy4VoPI5oMIhwNIoEvZlMpZS+"
        "0+2GNOK6hpNLt+KTR7fjzA9+i/Zlh3FjXiO6dGconAowRLFeDMm9GMl4EMUIxjDAOGzHmhUr"
        "VDXj0Nv1wAYosTeQHoCfLcA2yuZlq32iVuXMwlRRAU8igcHRUQyFQhijsX5Sl9+Px59/Htrv"
        "7Vm+5deP1qHzkT+he+kJDFQ0I1I0iE7PUbg8c3GZ6dCGPzMa3TQ0gR4mzRkcwfIVs7Bv3y5o"
        "tVpVVRapML27JQ5XuwtWyYqwssgY08+Hq2yVVZWYcd8MlZsJde4cHO1XkOcsoDs18ItkSSbR"
        "MzLCEuWDJGW44hSQK+dCO0Blogxxu4OaXpxf9Bx+9psHca37KD6VN+Onf5yM2k2laGx6Cx99"
        "eBAGBvQ/Q47KyHRolJizMI4Nkpkxq1Ni2cpY77jQoXJmkaYRRi25rXbGnhGShgEmSTAbjOjr"
        "6uLcKLmGgcBAAGk/40uMx0ge4Jn1T+Hx576DL5VVCFmoWb0Iv3j9aTwwZ64yvhW0Th1SSy0U"
        "KcMzloY/w1immiBjt5+rf2jtMpUzC8O0KgxxUUODY/AGkox7CWMJqg+OYeGShzhTxPw/SBQl"
        "QRQqnpMKSti5PWjY9KVbGQwSxVgpppqiH+FzG9/EYTHrVM4sNIZhpKWdSMsvQdbsIN971P0x"
        "YukIyu6Zyjk55JoEWCdboc3nFotxHikfeP3dN4UMoJ/uDEUYRX6myDDVsN/P1yQmGyFKDbeB"
        "X1LDjI93DjNigWKLjDxNggUnydopo4jvPjr4Pv+OI3nlOIqMPJyKtChyZJBjyMBukvFl2nBw"
        "93bhQbqL1SMVCyOToBsZj1y+4kV39SwlcFE8Ge3rF1LBDBZxJ2raV6GwmK9JL754lcxCtZNU"
        "wzR2IO3Io0ncWsqKcyfi7IsCJdbiLi3l35vgKEOcuuLc5hiZhTkpmhEh2fKdNDBEAwYKEPdU"
        "Qx6dyfibwiShQjrkJ2ueosTJFOKC6SvzeFJV0tkOTM+dinttdDapqspMLfeSOGAh1tv5qKtD"
        "Nx+ifAT4FMayPHKm8DrdfhOCnuvw0fIeXxJ9fhl+rmSE1E39azc8Dc2JuCwvpgSdsFzMPc+j"
        "qO0s8O5O/GjtSux5+ZdZSbeBIE+H8MyZIkrg5w508fCnRHxKOlZWjivnL8DmECuhb2o1cFbS"
        "H3EtOnxptDCamllJPjwPNLScoQf1tMycgtUmQ2vqpKUkow+waHCy8ZQi5HYhd3Yy7iiGR5aZ"
        "Zyr3SCEeTtB7h/GXk8fZA67duAILGXUsLQ6HmWcxc4E5ZGf1CvG7xztCA6PCp6z2PFPTo6wv"
        "EUZMgM9AAGtrGFN3AP2sWQjQcyEW3CFmkdhmL/OvYgmwblMIG55ZhQP769DTNx2frAYu2NII"
        "3AgxD4AwYy/MHbVySVPKS2gg40Q5eEU6UiB4DipPXh4XzZ6d1XibsDARAg8/jCvsXyMNMQAf"
        "PASs4XWwcipvXdOBjs59WFANlJUBl5mLH9CT3WEmC+noOWBZ7TpMqayigbzaiHQ0k1NyMhPF"
        "uIDHDg/xzdu2KQrvBNMOH0Zo00swvsBg59oXrjLDyLUbuIVOFysZy4jBpIe7QI8S5lmAdWkv"
        "M34/i8LqjRvw3iHWQ0ISdRniUp1hLIrnTf2M6N8hxAm94LXNuH9LAb3ATQrLE8SL6iWQ4ThN"
        "Ysnk2S28XYJX3xx3jKQbY7x1dyPKq3aGBzR4oxDxJ9698OSTKtudQU8rh3rnoreX2ToYU8SK"
        "aOLxC15W2E/yPpmEMGGMai/x18TCBxbBZBQlKwtpPu/9q4Vhp5ixvGLj8mXgwAE8VluLmiWM"
        "6v8ShYU7cPWqG7y0KOIbG7NUWroKDQ1Ae7viC/Buir4+Hfb+bo86M4svfjQdoIQPTp+GxOXW"
        "zZmDb69cqTD8LxDnRbehYRfOnv2YOVmFxYu/i/nz59GTXTh+/GW0tbXD7V6J9es3wmKxqrOy"
        "mPDDPc7MFTCydv0/EI1GeEUz8w6pBiCRTGZodBRW/mC6FSYYeDfiLv/PAvB3isaIzRpkElEA"
        "AAAASUVORK5CYII=")
        return fu4028.GetBitmap()
