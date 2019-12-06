#!/bin/sh
# -*- coding: utf-8

# fuctrl.py version history
# ver.0.2.0 (28Dec2014): the first version.
#                        Ctrl methods were collected from other modules.


import sys
#from nt import lstat
import cmd
sys.path.insert(0,'.')
import wxversion
wxversion.select("2.8")
import wx
import os
import shutil
#import psutil
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
import inspect
# fumodel menu handler
#from wx.lib.splitter import MultiSplitterWindow
import scipy
if int(scipy.__version__.split('.')[1]) >= 11:
    from scipy.sparse.csgraph import _validation # need for pyinstaller
    from scipy.optimize import minimize # need for pyinstaller
from operator import itemgetter

import fumodel
import const
import lib
import rwfile
import molec
import subwin
import ctrl
import draw
import graph
import cube
import build
import frag
#try: import fortlib
#except: pass 
#import fmopdb
try: import fmopdb
except: pass
import view
import custom

class MenuCtrl():
    def __init__(self,parent):
        self.model=parent # Model
        self.mdlwin=parent.mdlwin
        self.setctrl=self.model.setctrl
        self.classnam='MenuCtrl'
        
        self.menubar=None
        self.menulabeldic={} # {'label':[menuitem,toplabel],...]

        self.projectmenuitems=[]
        self.filehistorymenuitems=[]

        self.fumode=0
              
        self.shiftkeyDown=False
        self.ctrlkeydown=False
        self.mousleftdown=False
        
        self.mouseoperationmode=''
        
        self.selcirc=False; self.selrect=False
        self.selcntatm=-1; self.selinipos=[]
        self.focusselected=False
        # popup menu status flags
        self.secmod=self.model.mousectrl.GetSectionMode()
        self.atmnmb=False
        self.atmnam=False
        self.resnam=False
        self.xyzaxis=False
 
    def CreateMenuBar(self,fumode,fmomenu,addon1menu,addon2menu):
        """ Definition of menubar items
        
        :param int fumode: 0 for fumolde, 1 for fuplot
        :param bool fmomenu: True for activate, False for not.
        :param lst addmenu1: menu items for add-on menu 1
        :param lst addmenu2: menu items for add-on menu 2
        """
        #submenud=self.FileMenu()
        self.fumode=fumode
        self.toplabel=''
        mfil=self.CreateMenuFromList('File',self.FileMenu()) #self.FileMenu() # 'File' menus
        medt=self.CreateMenuFromList('Edit',self.EditMenu()) # 'Edit' menus
        mshw=self.CreateMenuFromList('Show',self.ShowMenu()) # 'Show' menus
        msel=self.CreateMenuFromList('Select',self.SelectMenu()) # 'Select' menus
        madd=self.CreateMenuFromList('Modeling',self.ModelingMenu()) # 'AddDel' mneus
        #mchg=self.CreateMenuFromList('Change',self.ChangeMenu()) # 'Change' menus
        mgrp=self.CreateMenuFromList('Group',self.GroupMenu()) # 'Group' mneus
        mutl=self.CreateMenuFromList('Utility',self.UtilityMenu()) # 'Report' menus
        mfmo=self.CreateMenuFromList('FMO',self.FMOMenu()) # 'FMO' menus
        mwin=self.CreateMenuFromList('Window',self.WindowMenu()) # 'Window' mneus
        mhlp=self.CreateMenuFromList('Help',self.HelpMenu()) # 'Help' menus
        mtol=self.CreateMenuFromList('Tools',self.ToolsMenu()) # not used
        mcmp=self.CreateMenuFromList('Compute',self.ComputeMenu()) # not used
        #
        if fumode == 1: # FMO Viewer mode
            menulst=[['File',mfil],['Edit',medt],['Show',mshw],['Select',msel]]
        elif fumode == 2: # simple viewer mode
            menulst=[['File',mfil],['Edit',medt],['Show',mshw],['Select',msel]]
        else: # fumode == 0:                  
            menulst=[['File',mfil],['Edit',medt],['Show',mshw],['Select',msel],
                     ['Modeling',madd],['Utility',mutl]]
            if fmomenu: menulst.append(['FMO',mfmo])
        # add add-on menus
        if len(addon1menu) > 0:
            addon1label=addon1menu[0]; menuitems=addon1menu[1]
            self.toplabel=addon1label
            maddon1=self.CreateMenuFromList(addon1label,menuitems)
            menulst.append([addon1label,maddon1])
        if len(addon2menu) > 0:
            addon2label=addon2menu[0]; menuitems=addon2menu[1]
            self.toplabel=addon2label
            maddon2=self.CreateMenuFromList(addon2label,menuitems)
            menulst.append([addon2label,maddon2])
        # add mwin and mhlp
        menulst.append(['Window',mwin])
        menulst.append(['Help',mhlp])
        # set menus to menubar
        menubar=wx.MenuBar()
        for toplabel,submenu in menulst: menubar.Append(submenu,toplabel)           
        #
        self.menubar=menubar
        #self.MakeMenuLabelDic()
        
    def GetMenuLabel(self,menuid):
        return self.menubar.GetLabel(menuid)

    def GetMouseOperationMode(self):
        return self.mouseoperationmode
    
    def GetTopMenu(self,label):
        # label(str): submenu label
        # return topmenu(str): top menu label
        toplabel=self.menulabeldic[label][1]
        return toplabel

    def CheckMenu(self,label,on):
        """ Check menu item
        
        :param str label: menu item label
        :param bool on: True for check, False for uncheck
        """
        if self.menulabeldic.has_key(label):
            menuitem=self.menulabeldic[label][0]
            if menuitem.IsCheckable(): menuitem.Check(on)
 
    def IsChecked(self,label):
        """ Return checked/unchecked status of menu item.
        
        :param str label: menu item label
        :return: True for checked, False for unchecked
        """
        # item(str): menu label
        # ret (bool): checked:True, unchecked:False
        if self.menulabeldic.has_key(label):
            menuitem=self.menulabeldic[label][0]
            return menuitem.IsChecked()
        else: False
 
    def IsCheckable(self,label):
        """ Return if a menu item is chackeable or not.
        
        :param str label: menu item label
        :return: True for checkable, False for uncheckable
        """
        menuitem=self.menulabeldic[label][0]
        return menuitem.IsCheckable()
    
    def IsDefined(self,label):
        """ Return a menu item is defined or not.
        
        :param str label: menu item label
        :return: True for defined, False for not defined
        """
        if self.menulabeldic.has_key(label): return True
        else: return False

    def UncheckAll(self):
        """ Uncheck all checkable menu items """
        for label,menuitemlabel in self.menulabeldic.iteritems():
            if not menuitemlabel[0].IsCheckable(): continue
            menuitemlabel[0].Check(False)
 
    def UncheckProjectMenuItems(self):
        """ Uncheck all project submenu items('File'-'Project-xxx').
        
        """ 
        for label,menuitemlabel in self.menulabeldic.iteritems():
            for prjnam in self.projectmenuitems:
                if prjnam == label: menuitemlabel[0].Check(False)
                   
    def EnableMenu(self,on):
        """ Enable/disable top menu items excluding 'those in 'exclude'.
        
        :param bool on: True to enabel all, False to disable except in 'exclude' list.
        :note: this routine is killed at 11Nov2015
        """
        return
        
        exclude={'File':True,'Window':True,'Help':True,'Add-on':True}
        nmb=self.menubar.GetMenuMoleculeInfo()
        for i in range(nmb):
            top=self.menubar.GetLabelTop(i)
            self.menubar.EnableTop(i,True)
            if not on and not exclude.has_key(top): 
                self.menubar.EnableTop(i,False)        

    def MenuHandlerDic(self):
        """ Retrun top menu event handler object dictionary.
        
        :return: menu handler object dictionary, {'menu label':event-handler-method-object,...}
        :rtype: dic
        """
        menuhandlerdic={"File": self.OnFile,"Edit": self.OnEdit,
                        "Show": self.OnShow,"Select": self.OnSelect,
                        "Modeling": self.OnModeling,"Utility": self.OnUtility,
                        "FMO": self.OnFMO,"Window": self.OnWindow,
                        "Help": self.OnHelp,"Hidden":self.OnHidden} 
        return menuhandlerdic
           
    def OnMenu(self,event):
        """ Menu event handler """
        # menubar items
        self.model.Message('')
        menuid=event.GetId()
        label=self.GetMenuLabel(menuid)
        """
        lablst=['Open','New']
        if not label in lablst:
            if self.model.mol is None: 
                mess='No molecules. Please open molecule files'
                lib.MessageBoxOK(mess,'MenuCtrl(OnMenu)')
                return
        """
        self.ExecMenu(label)
        
    def ExecMenu(self,label,bChecked=None):
        """ Execute menu item """
        if label[:1] == "*":
            self.model.Message("Sorry, this function is underconstruction.",
                               0,"black")
            return
        # Is item checked?
        try: bChecked=self.IsChecked(label)
        except: bChecked=False
        # top menu label
        try:
            topmenu=self.menulabeldic[label][1]
            menuhandlerdic=self.MenuHandlerDic()
        except: 
            mess='Not found menu item label='+label
            lib.MessageBoxOK(mess,'MenuCtrl(ExecMenu)')
            return
        #14Dec2015#if (topmenu != "File" and topmenu != 'Window' and topmenu != "Help" and topmenu != 'Add-on') and not self.model.Ready(): return
        #
        if menuhandlerdic.has_key(topmenu): 
            menuhandlerdic[topmenu](label,bChecked)
        else: self.OnAddons(label,bChecked)

    def OnFile(self,label,bChecked):   
        """ 'File' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked. 
        """
        # echo and log
        self.EchoAndLog('File',label,bChecked)
        # wild card
        wcard='pdb file(*.pdb;*.ent)|*.pdb;*.ent|xyz(*.xyz,*.xyzs,*.xyzfu)|'
        wcard=wcard+'*.xyz;*.xyzs;*.xyzfu|mol file(*.mol;*.sdf)|*.mol;*.sdf|'
        wcard=wcard+'zmatrix(*.zmt;*.zmtfu)|*.zmt;*.zmtfu|tinker(*.tin)|*.tin|'
        wcard=wcard+'fufiles(*.fuf,*.spl,*.mrg)|*.fuf;*.spl;*.mrg|'
        wcard=wcard+'fmoinput file(*.inp)|*.inp|'
        wcard=wcard+'frame data(*.frm)|*.frm|' #fragment(*.frg)|*.frg|'
        wcard=wcard+'gzip file(*.gz)|*.gz|All(*.*)|*.*'
        # for "Save all as" menu 
        filetype=["pdb files","mol files","sdf file","xyz files","xyzs file",
                  "xyzfu files","zmt files","zmtfu files"]
        # check menu
        self.CheckMenu(label,bChecked)

        name=self.model.setctrl.GetParam('defaultfilename')
        self.model.setctrl.SetParam('defaultfilename','')
        # File menu items 
        if label == "New":
            self.model.NewMolecule()
        elif label == "Open":
            filenamelst=lib.GetFileNames(self.mdlwin,wcard,'r',True,
                                         defaultname=name)
            if len(filenamelst) > 0: 
                #root,ext=os.path.splitext(filename)
                for filename in filenamelst:
                    head,ext=os.path.splitext(filename)
                    if ext == '.gz': filename=lib.ZipUnzipFile(filename,False)
                    self.model.ReadFiles(filename,True)
                    self.model.ChangePath(filename)
        elif label == "Merge":
            filename=lib.GetFileName(self.mdlwin,wcard,'r',True,
                                     defaultname=name)
            if len(filename) > 0: self.model.MergeToCurrent(filename)
        elif label == "Close current":
            self.model.RemoveMol(False) # current molecule
        elif label == "Close All":
            self.model.RemoveMol(True) # current molecule
        elif label == "Save":
            self.model.WriteFiles("",True,True)
        # "Save all as menu "
        elif label in filetype:
            """ Save as menu """
            dirname=lib.GetDirectoryName()
            if dirname != '': self.model.WriteAllAs(label,dirname)
        elif label == "Save As":
            filename=""; wildcard='all(*.*)|*.*'
            filename=lib.GetFileName(self.mdlwin,wildcard,'w',True,
                                     defaultname=name)
            if len(filename) < 0: return
            self.model.WriteFiles(filename,False,True)
            self.model.ChangeMolName(filename)
            self.model.ChangePath(filename)
        elif label == "Save Selected As":
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            if len(filename) < 0: return
            self.model.WriteFiles(filename,False,False)
        elif label == "Save All":
            filename=""
            if len(filename) < 0: return
            self.model.MenuFiles(label,filename)      
        elif label == "Save All As":
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            if len(filename) < 0: return
            self.model.MenuFiles(label,filename) 
        elif label == "Save canvas image":
            wcard='image(*.bmp;*.png;*.jpeg)|*.bmp;*.png;*.jpeg'
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            self.model.SaveCanvasImage(filename)        
        elif label == "Print canvas image":
            wildcard='image(*.bmp;*.png;*.pdf)|*.bmp;*.png;*.pdf'
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            self.model.PrintCanvasImage(filename)            
        elif label == "Save BDA data as":
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            if len(filename) < 0: return        
            self.model.SaveBDADataAs(filename)
        elif label == "Save fragment data as":
            filename=lib.GetFileName(self.mdlwin,wcard,'w',True,
                                     defaultname=name)
            if len(filename) < 0: return        
            self.model.SaveFragmentDataAs(filename)
            #self.mdlmgr.MenuFiles(label,filename) 
        elif label == "Save log":
            self.model.SaveLog(bChecked)
            """
            logfile=""
            if bChecked:
                wcardlog='log file(*.log)|*.log'
                dlg = wx.FileDialog(self.mdlwin, "Start log...", os.getcwd(),
                                    style=wx.OPEN, wildcard=wcardlog)
                if dlg.ShowModal() == wx.ID_OK:
                    logfile=dlg.GetPath()            
                #dlg.Destroy()        
                if len(logfile) < 0: return
                self.model.SaveLog(logfile,True)            
            else:
                self.model.SaveLog(logfile,False)
            """ 
        elif label == "*Utility":
            filename=""
            self.model.MenuFiles(label,filename)
        elif label == "Save bitmap": self.model.SaveMolBitmapOnFile()
        elif label == "Quit": self.model.ExitModel()
        elif label == 'New ...': # not used. moved to Hidden menu for future use
            self.model.setctrl.ProjectSetting('New project')
        elif label == 'Import': # not used. moved to Hidden menu for future use
            self.model.setctrl.ProjectSetting('Import project')
        #elif label == "Open existing": # project menu items
            pass
        elif label == "Enable MessageBox":
            self.model.setctrl.SetMessageBoxFlag('',bChecked)
        elif label == "Message level": self.model.setctrl.SetMessageLevel()
        
        elif label == 'Clear history': self.model.ClearFileHistory()
        elif os.path.dirname(label) != '':
            filename=label
            head,ext=os.path.splitext(filename)
            if ext == '.gz': filename=lib.ZipUnzipFile(filename,False)
            self.model.ReadFiles(filename,True)
            self.model.ChangePath(filename)
        else:
            # project menu items?
            try: idx=self.projectmenuitems.index(label)
            except: idx=-1
            if idx >= 0:
                label=self.projectmenuitems[idx]
                self.model.SwitchProject(label)
            else:
                mess=self.classnam+'(OnFile): '+'"'+label
                mess=mess+'" menu item is not defined'
                lib.MessageBoxOK(mess,"") 
            
    def OnEdit(self,label,bChecked):
        """  'Edit' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # echo and log
        self.EchoAndLog('Edit',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        #
        if label == "Copy mol object":  self.model.CopyMolToClipboard(False)
        elif label == "Cut and copy mol object": 
            self.model.CopyMolToClipboard(True)
        elif label == "Paste mol object": self.model.PasteMolFromClipboard()
        elif label == "Copy xyz text":  self.model.CopyMolXYZToClipboard()
        elif label == "Paste xyz text": self.model.PasteMolXYZFromClipboard()
        elif label == "Copy canvas image": 
            self.model.CopyCanvasImageToClipboard()
        elif label == "Clear clipboard": self.model.ClearClipboard()
        else:
            mess=self.classnam+'(OnEdit): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")

    def OnShow(self,label,bChecked):    
        """ 
        'Show' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # echo and log
        self.EchoAndLog('Show',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        # Show menu items
        if label == "Fit to screen": self.model.FitToScreen(True,True)
        elif label == "Reset rotation": self.model.ResetRotate()
        elif label == "Hide selected": self.model.HideSelected(bChecked)
        elif label == "Hide environment": self.model.HideEnvironment(bChecked) 
        #elif label == "Hide all peptide atoms":
        #    if not self.ctrlflag.ready: return #event.Skip()
        #    self.model.HidePeptideAtoms(bChecked)
        #    return
        elif label == "Hide hydrogen": self.model.HideHydrogen(bChecked)
        elif label == "Hide water": self.model.HideWater(bChecked)
        elif label == "Hide all atoms": self.model.HideAllAtoms(bChecked)
        elif label == "Selected only": self.model.ShowSelectedOnly(bChecked)
        elif label == "Side chain only": 
            self.model.ShowAASideChainOnly(bChecked)
        elif label == "Backbone only": self.model.ShowAABackboneOnly(bChecked)
        elif label == "All atom ": self.model.ShowAllAtom()
        # Main chain submanu
        elif label == "Tube": self.model.DrawChainTube(bChecked)
        elif label == "CAlpha": self.model.DrawChainCAlpha(bChecked)
        elif label == "Kite train": self.model.DrawChainKite(bChecked)
        # Label submenu in Show Menu
        elif label == "Element": self.model.DrawLabelElm(bChecked,0)
        elif label == "Atom number": self.model.DrawLabelAtm(bChecked,0)
        elif label == "Atom name": self.model.DrawLabelAtm(bChecked,1)
        elif label == "Atom name+number": self.model.DrawLabelAtm(bChecked,2)
        elif label == "Residue name": self.model.DrawLabelRes(bChecked,0)
        elif label == "Residue name+number": 
            self.model.DrawLabelRes(bChecked,1)
        elif label == "Chain name": self.model.DrawLabelChain(bChecked)
        elif label == "Formal charge":
            self.model.DrawFormalCharge(bChecked)
        elif label == "Remove all": self.model.DrawLabelRemoveAll(True)
        # distance
        elif label == "Mode(on/off)": self.model.SetDrawDistance(bChecked)
        elif label == "Remove": self.model.ClearDrawDistance()
        # Bond submenu in Show Menu
        elif label == "Multiple bond": self.model.DrawMultipleBond(bChecked)
        elif label == "Hydrogen Bonds": self.model.DrawHBOrVdwBond(bChecked)
        #if label == "vdW contact":
        #    self.model.DrawVdwBond(bChecked)
        elif label == "CH/pi contact":
            if bChecked: self.model.MenuShow('CH/pi contact',1)
            else: self.model.MenuShow('CH/pi contact',0)
        # FMO related  submenu  
        # Molecular model submenu in Show Menu
        elif label == "Line": self.model.ChangeDrawModel(0)
        elif label == "Stick": self.model.ChangeDrawModel(1)
        elif label == "Ball and stick": self.model.ChangeDrawModel(2)
        elif label == "CPK": self.model.ChangeDrawModel(3)
        elif label == "vdW surface": self.model.MenuShow("vdW surface",-1)
        elif label == "SA surface": self.model.MenuShow("SA surface",-1)
        elif label == "Stereo":
            if bChecked: self.model.SetStereo(True)
            else: self.model.SetStereo(False)
        elif label == "xyz-axis": self.model.DrawXYZAxis(bChecked)
        # Color submenu in Show Menu
        elif label == "by element": self.model.ChangeAtomColor(label)
        elif label == "by residue": self.model.ChangeAtomColor(label)
            #self.model.MenuShow("by residue")    
        elif label == "by fragment": self.model.ChangeAtomColor(label)
        elif label == "by group": self.model.ChangeAtomColor(label)
        elif label == "by chain": self.model.ChangeAtomColor(label)
        elif label == "on color palette": self.model.ChangeAtomColor(label)
        elif label == "Fog": self.model.FogEnable(bChecked)
        elif label == "Opacity":
            if bChecked: self.model.ChangeOpacity(0.5)
            else: self.model.ChangeOpacity(1.0)
        elif label == "Background color": self.model.ChangeBackgroundColor([])    
        elif label == 'Redraw': self.model.Redraw()
        elif label == 'Dump view': self.model.DumpDrawItems()
        elif label == 'Restore view': self.model.RestoreDrawItems()
        elif label == "One-by-One":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "SlideShowCtrl":
            if bChecked: self.mdlwin.winctrl.Open(label)
            else: 
                try: 
                    self.model.winctrl.GetWin(label).RemoveMdlWinMess()
                    self.mdlwin.winctrl.Close(label)
                except: pass
        elif label == "Redraw": self.model.DrawMol(True)
        else:
            mess=self.classnam+'(OnShow): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def OnWindow(self,label,bChecked):
        """ 'Window' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        # echo and log
        self.EchoAndLog('Window',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        # excute menu item
        if label == "Open ControlWin":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)    
        elif label == "Open PyShell":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Hide(label)
        
        elif label == "Show ToolsWin":
            pyshell=self.model.winctrl.GetWin('Open PyShell')
            if bChecked:
                try: pyshell.shell.run('fum.ShowToolsWin()')     
                except: pass
            else:
                try: pyshell.shell.run('fum.HideToolsWin()')     
                except: pass
        elif label == "Open EasyPlotWin":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label) 
        elif label == "ChildViewWin":
            """
            if self.ctrlflag.Get('ChildViewWin'):
                self.model.childwin.SetFocus()                
                self.Message('ChildMolView panel is open.',1,'black')
            else: self.model.OpenChildMolView()
            """
            return
        elif label == "Open MatPlotLibWin":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)    
        elif label == "Open MouseModeWin":
            if bChecked:
                self.mdlwin.muswin=True
                self.mdlwin.OpenMouseModeWin()
            else: 
                self.mdlwin.muswin=False
                self.mdlwin.CloseMouseModeWin()  
        elif label == "Open MolChoiceWin":
            if bChecked: 
                self.mdlwin.molwin=True
                self.mdlwin.OpenMolChoiceWin()
            else: 
                self.mdlwin.molwin=False
                self.mdlwin.CloseMolChoiceWin()
        
        #elif label == "Open ExecScriptWin":
        #    if bChecked: 
        #        win=subwin.ExecuteScript_Frm(self.mdlwin,winpos=[0,0])
        #        self.model.winctrl.SetOpenWin(label,win)
        #        self.model.winctrl.Open(label)
        #    else: self.model.winctrl.Close(label)
        
        #elif label == "Open ScriptEditor":
        #    if bChecked: self.model.winctrl.Open(label)
        #    else: self.model.winctrl.Close(label)    
            
        #elif label == "Operation guide":
        #    print 'Window Operation guide'
        
        #if label == "Open SettingWin":
        #    self.model.winctrl.OpenSettingWin()
        else:
            mess=self.classnam+'(OnWindow): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  
        
    def OnSelect(self,label,bChecked):
        """ 'Select' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # echo and log
        self.EchoAndLog('Select',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        if label == "Hydrogen atom": self.model.SelectHydrogen()        
        elif label == "Non bonded atom": self.model.SelectNonBonded()
        elif label == "Water molecule": self.model.SelectWater()
        elif label == "Non-AA residue": self.model.SelectNonAAResidue()
        elif label == "AA residue": self.model.SelectAAResidue()
        elif label == "Side chain": self.model.SelectAASideChain()
        elif label == "Backbone": self.model.SelectAABackbone()
        # Atoms/Residues
        elif label == "Ball-and-stick model atoms": 
            self.model.SelectAtomByModel(2)
        elif label == "CPK model atoms":
            self.model.SelectAtomByModel(3)
        elif label == "Atoms within distance": 
            self.model.SelectAtomsWithinDistance()
        elif label == "Resdiues within distance":
            self.model.SelectResiduesWithinDistance()
        #elif label == "Residues with missing atoms": 
        #    self.model.SelectResiduesWithMissingAtoms()
        elif label == "Read select file": self.model.SelectByFile()
        #
        elif label == "Complement": self.model.SelectComplement()
        elif label == "All show atoms": self.model.SelectAllShowAtom()
        elif label == "Select all": self.model.SelectAll(1)
        elif label == "Deselect all": self.model.SelectAll(0)
        elif label == "Environment": self.model.SelectEnv()
        # Object submenu in Select
        elif label == "Atom": 
            self.model.mousectrl.OnSwitchMouseMode('selobj',0)
        elif label == "Residue": 
            self.model.mousectrl.OnSwitchMouseMode('selobj',1)
        elif label == "Peptide chain": 
            self.model.mousectrl.OnSwitchMouseMode('selobj',2)
        elif label == "Group": 
            self.model.mousectrl.OnSwitchMouseMode('selobj',3)
        elif label == "Fragment": 
            self.model.mousectrl.OnSwitchMouseMode('selobj',4)
        elif label == "Molecule":
            #self.model.mousectrl.OnSwitchMouseMode('selobj',???)
            return
        # Multiple selection submenu
        elif label == "1-object": 
            self.model.mousectrl.OnSwitchMouseMode('selmod',0)     
        elif label == "2-objects": 
            self.model.mousectrl.OnSwitchMouseMode('selmod',1)
        elif label == "3-objects": 
            self.model.mousectrl.OnSwitchMouseMode('selmod',2)
        elif label == "4-objects": 
            self.model.mousectrl.OnSwitchMouseMode('selmod',3)
        elif label == "Unlimited": 
            self.model.mousectrl.OnSwitchMouseMode('selmod',4)
        elif label == "Box/Sphere(toggle)": # in "Sphere/Box selection":
            self.model.mousectrl.OnSwitchMouseMode('selmod',5)
        elif label == "Remove box/sphere":
            self.model.RemoveSelectSphere()
            self.model.RemoveSelectBox()
        # section mode
        elif label == 'Section mode':
            self.secmod=bChecked; title='Open ControlWin'
            if self.model.winctrl.IsOpened(title):
                self.model.winctrl.GetWin(title).SetSectionMode(bChecked)
            self.model.mousectrl.OnSwitchMouseMode('section',self.secmod)
            self.model.SetSection(bChecked) #self.secmod)
        elif label == "Preset color": 
            self.model.SetSelectedDisplayMethod(True)
        elif label == "Bold line": self.model.SetSelectedDisplayMethod(False)
        # "Selector" submenu
        elif label == "Tree":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "Name/Number":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "Radius":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        else:
            mess=self.classnam+'(OnSelect): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def OnModeling(self,label,bChecked):
        """ 'Modeling' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # echo and log
        checkstr='True'
        if not bChecked: checkstr='False'
        mess='fum.menuctrl.OnModeling("'+label+'",'+checkstr+')'
        if self.model.setctrl.GetEcho(): self.model.ConsoleMessage(mess)
        #if lib.LOGGING: self.model.WriteLogging(mess)
        #
        self.CheckMenu(label,bChecked)
        # save molecule object for undo
        if label != "Undo": self.model.SaveMol()
        # Undo
        if label == "Undo": self.model.RecoverMol() # self.molde.Undo()
        # Add hydrogen
        elif label == "Open add hydrogen panel": 
            self.model.ExecuteAddOnScript('add-hydrogens.py',False)
        #elif label == 'to all residues': self.model.AddHydrogenToAllResidues()
        elif label == "to polypeptide": self.model.AddHydrogenToAAResidue()
        elif label == "to water": self.model.AddHydrogenToWater()
        elif label == "to non-polypeptide(use frame data)": 
            atmlst=self.model.ListNonAAResidueAtoms()
            self.model.AddHydrogenUseFrameData(atmlst=atmlst)
        elif label == "to non-polypeptide(use bond length)": 
            self.model.AddHydrogenUseBondLength()
        elif label == "View summary": self.model.SummaryOfAddHydrogens()
        elif label == "View message log": self.model.ViewMessageLog()
        # Attach hydrogen(s)
        elif label == "1H": self.model.AttachHydrogen(label)
        elif label == "2H": self.model.AttachHydrogen(label)
        elif label == "3H": self.model.AttachHydrogen(label)
        # Replace hydrogen with
        elif label == "CH3": self.model.ReplaceWithGroupAtoms(label)
        elif label == "ACE": self.model.ReplaceWithGroupAtoms(label)
        elif label == "NME": self.model.ReplaceWithGroupAtoms(label)
        elif label == "GROUP": 
            self.model.ExecuteAddOnScript('model-builder.py',False)
        elif label == "Merged molecule": self.model.ConnectMergedGroup()
        #elif label == "with other resdiue": self.model.ReplaceNonAAResidue()
        elif label == "Residue(s)": self.model.RepalceWithSameResdiue()
        elif label == "Ligand in complex":
            #self.model.ExecuteAddOnScript('replace-ligand.py',False)
            build.ReplaceLigandInComplex(self.model)
        elif label == "Residue coordinates": 
            self.model.RepalceResdiueCoordinates()
        # Truncate protein
        elif label == "Open panel":
            build.TruncateProtein_Frm(self.model,-1)
        elif label == "Cap with hydrogens":
            build.TruncateProtein(cap=1,model=self.model)
        elif label == "Cap with ACE/NME":
            build.TruncateProtein(cap=0,model=self.model)
        elif label == "Use frame data ": self.model.AddBondUseFrameData()
        elif label == "Based on bond length ": 
            self.model.AddBondUseBondLength()
        elif label == "Based on valence ": self.model.AddBondMultiplicity(0)
        elif label == "S-S bond": self.model.AddSSBond()
        elif label == "vdW contact": self.model.MakeVdwContact()
        elif label == "Hydrogen bond": self.model.MakeHydrogenBond(True)
        #
        elif label == "Residue ": self.model.MenueAdd("residue")
        # Bond submenu
        elif label == "Bond multiplicity": self.model.AddBondMultiplicity()
        elif label == "Based-on bond length": self.model.AddBondMultiplicity(1)
        elif label == 'remove': self.model.RemoveBondMultiplicity()
        #Del ---------------------------------
        elif label == "Selected atoms": self.model.DeleteSelected()
        elif label == "Non-bonded atoms": self.model.DeleteNonBonded()
        elif label == "Hydrogen atoms": self.model.DeleteHydrogens()
        elif label == "Waters": self.model.DeleteWater()
        #elif label == "AA residues": self.model.DeleteAAResidue()
        #elif label == "Non-AA residues": self.model.DeleteNonAAResidue()
        elif label == "All bonds": self.model.DeleteBonds('all',True)
        elif label == "Bond multiplicities": 
            self.model.RemoveBondMultiplicity()    
        elif label == "Hydrogen_bonds": self.model.DeleteHydrogenBond()
        elif label == "vdW contacts": self.model.DeleteVdwBond()
        elif label == "TER in PDB data": self.model.DeleteAllTers()
        elif label == "Dummy atoms in ZMatrix": 
            self.model.DeleteAllDummyAtoms()
        # Change
        elif label == "Element ": self.model.ChangeElementAndLength()
        elif label == "Atom name ": self.model.ChangeAtomName()
        elif label == "Residue name ": self.model.ChangeResidueName()
        elif label == "Chain name ": self.model.ChangeChainName()
        elif label == "Group name ": self.model.ChangeGroupName()
        #elif label == "Old atom names to new ones": self.model.ChangeAtmNamToNew()
        #elif label == "New atom names to old ones": self.model.ChangeAtmNamToOld()
        elif label == "Bond length": self.model.ChangeBondLength()
        elif label == "Bond multiplicity": 
            #self.model.ChangeBondMultiplicity()
            mess='Press 1,2,3,4 key to make multiple bond'
            lib.MessageBoxOK(mess,'OnChange: Change bond multiplicity')
        # Charge
        elif label == "to AA residue": self.model.AssignAAAtomCharge()
        elif label == "Ion charge": self.model.ChangeCharge()      
        elif label == "to selected atom(s)": 
            self.model.ChangeChargeOfSelectedAtoms()
        elif label == "Clear ion chgrges": self.model.ClearAtomCharge()
        elif label == "Group charge": self.model.ChangeGroupCharge() 
        
        elif label == "Conformation": self.model.winctrl.Open(label) # ZMatrixPanel()
        #elif label == "Model builder": self.model.winctrl.Open(label)
        elif label == "Replace water with ion": 
            self.model.ReplaceWaterWithIon()
        # Build molecule
        elif label == "Open Model Builder": 
            self.model.winctrl.Open('ModelBuilder')
        elif label == "Open Peptide Builder": 
            self.model.winctrl.Open('PolypeptideBuilder')
         # Mutation
        elif label == "Open HIS Form Changer":
            self.model.winctrl.Open('HisFormChanger')
        elif label == "Open Mutate Panel": 
            self.model.winctrl.Open('MutateResidue')
        # Edit conformation
        elif label == "Open Rotate Bond Editor": 
            self.model.winctrl.Open('RotateBond')
        elif label == "Open Torsion Editor": self.model.winctrl.Open(label)
        elif label == "Open ZMatrix Editor":
            self.model.winctrl.Open('ZMatrixEditor')
        # "Box waters"
        elif label == "Immerse in box waters":
            self.model.winctrl.Open('BoxWater')
          # Update coordinates
        elif label == "from output file" or label == "from file":
            coordfile=""
            if label == "from output file": 
                wcard="optgeom(*.out;*.log)|*.out;*.log"
            elif label == "from file": wcard="xyz(*.xyz)|*.xyz"
            dlg=wx.FileDialog(self.mdlwin,"Open file...",os.getcwd(),
                              style=wx.OPEN,wildcard=wcard)
            if dlg.ShowModal() == wx.ID_OK: coordfile=dlg.GetPath()
            #dlg.Destroy()
            if len(coordfile) > 0: self.model.UpdateCoordinates(coordfile)
        elif label == "from clipboad(xyz)":
            self.model.UpdateCoordinatesFromClipboad()
        # ???
        elif label == "Renumber residue":
            print 'remuber resnmb'
        elif label == "Renumber atom":
            print 'renumber atmnmb'
        elif label == "Utility geometry": self.model.MoleculeInfoGeometry()
        else:
            mess=self.classnam+'(OnModeling): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def OnGroup(self,label,bChecked):    
        """ 
        'Group' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        # echo and log
        self.EchoAndLog('Group',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        # "Make group" submenu
        if label == "Selected atoms ":
            self.model.MenuGroup('selected atoms group')
        elif label == "do. with environment":
            self.model.MenuGroup('do. env selected atoms group')
        elif label == "Split at TER":
            self.model.MenuGroup('split at TER')
        elif label == "do. with environment ":
            self.model.MenuGroup('do. env split at TER')
        elif label == "Split by chain":
            self.model.MenuGroup('split at chain')
        elif label == "do. with environment  ":
            self.model.MenuGroup('do. env split at chain')
        # "Make molecule" submenu
        elif label == "Selected atoms  ":
            self.model.MenuGroup('select atoms   ') # three blanks
        elif label == "Split at TER ":
            self.model.MenuGroup('split at ter ')
        elif label == "Split by chain ":
            self.model.MenuGroup('split by chain ')
        # "Combine" submenu
        elif label == "all molecules":
            self.model.MenuGroup('all molecules')
        elif label == "all groups":
            self.model.MenuGroup('all groups')
        elif label == "By choose panel":
            self.model.OpenJionGroupWin()
        # "Rename/Remove" submenu
        elif label == "Remove all groups":
            self.model.MenuGroup('remove all groups')
        elif label == "Remove all molecules":
            self.model.MenuGroup('remove all molecules')
        elif label == "By popup panel":
            self.model.OpenRenameGroupWin()
        else:
            mess=self.classnam+'(OnGroup): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def EchoAndLog(self,topmenu,label,bChecked):
        checkstr='True'
        if not bChecked: checkstr='False'
        mess='fum.menuctrl.On'+topmenu+'("'+label+'",'+checkstr+')'
        if self.model.setctrl.GetParam('echo'): self.model.ConsoleMessage(mess)
        # if lib.LOGGING: self.model.WriteLogging(mess)
        
    def OnUtility(self,label,bChecked):    
        """ 
        'Utility' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # echo and log
        self.EchoAndLog('Utility',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        #
        if label == "Molecule info": self.model.MoleculeInfo()
       # Geometry
        elif label == "Short contact":
            self.model.ExecuteAddOnScript('short-contact-atoms.py',False)
        elif label == "Bond lengths":
            self.model.geom.Plot('Bond length')
        elif label == "Bond angles":
            self.model.geom.Plot('Bond angle')
        elif label == "Hydrogen_bond":
            self.model.geom.Plot('Hydrogen bond')
        elif label == "Peptide angles":
            self.model.UtilityGeometry(label)
        elif label == "vdW contact":
            self.model.UtilityGeometry(label)
        elif label == "CH/pi bond":
            self.model.UtilityGeometry(label)
        # PDB data
        elif label == "Plot B-factor":
            self.model.ExecuteAddOnScript('plot-b-factor.py',False)
        elif label == "Missing residue info": 
            self.model.PDBMissingResidueInfo()
        elif label == "Change atom names to new": 
            self.model.ChangeAtmNamToNew()
        elif label == "Change atom names to old": 
            self.model.ChangeAtmNamToOld()
        elif label == "Delete TER's": self.model.DeleteAllTers()
        #elif label == "Missing atom residues":
        #    self.model.ReportMissingAtomsInAAResidue()
        #elif label == "Open PDB tools panel":
        #    self.model.ShowToolsWin()
        #elif label == "Show ToolsWin":
        #    pyshell=self.model.winctrl.GetWin('Open PyShell')
        #    if bChecked:
        #        try: pyshell.shell.run('fum.ShowToolsWin()')     
        #        except: pass
        #    else:
        #        try: pyshell.shell.run('fum.HideToolsWin()')     
        #        except: pass
        elif label == "Split, join and extract":
            #self.model.ExecuteAddOnScript('split-and-join.py',False)
            self.model.winctrl.Open('SplitJoin')
        elif label == "Compare files":
            lib.MessageBoxOK('Under construction','')
        # others
        elif label == "Open EasyPlotWin":
            #if bChecked: self.model.winctrl.OpenEasyPlotWin()
            #else: self.model.winctrl.CloseEasyPlotWin()
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label) 
        elif label == "ChildViewWin":
            """
            if self.ctrlflag.Get('ChildViewWin'):
                self.model.childwin.SetFocus()                
                self.Message('ChildMolView panel is open.',1,'black')
            else: self.model.OpenChildMolView()
            """
            return
        elif label == "Open ExecScriptWin":
            if bChecked: 
                win=subwin.ExecuteScript_Frm(self.mdlwin,winpos=[0,0])
                self.model.winctrl.SetOpenWin(label,win)
                self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        
        elif label == "Open ScriptEditor":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)    
        elif label == "Open MatPlotLibWin":
            #if bChecked: self.model.winctrl.OpenMatPlotLibWin()
            #else: self.model.winctrl.CloseMatPlotLibWin()
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)    

        else:
            mess=self.classnam+'(OnUtility): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def OnFMO(self,label,bChecked):    
        """ 
        'FMO' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        ans=lib.IsMoleculeObj(self.model.mol)
        if not ans: return
        # check menu
        self.CheckMenu(label,bChecked)
        # echo and log
        self.EchoAndLog('FMO',label,bChecked)
        #
        #if self.model.frag is None:
        #    mess='Program error: "frg" instance is not created.'
        #    lib.MessageBoxOK(mess,'MenuCtrl(OnFMO)') 
        #    return
        # fragment object
        frgobj=self.model.frag
        if frgobj is None:
            mess='Fragment object is not availabel. Please check the '
            mess=mess+' "frag.py" module is imported in '
            mess=mess+'"fumodel" module.'
            lib.MessageBoxOK(mess,'MenuCtrl(OnFMO)')
            return
        ###if frgobj.name is None: frgobj.SetName(self.model.mol.name)
        # fragmentation polypeptide    
        if label == "Outline of fragmentation": frgobj.OutlineDocument()
        elif label == "Open fragment panel":
             frgobj.OpenFragmentationPanel()
        elif label == "One residue":
            frgobj.FragmentPolypeptide(0,drw=True)
            #self.model.menuctrl.CheckMenu("BDA points",True)
        elif label == "One residue except Gly":
            #self.model.FragmentAARes(1,True)
            frgobj.FragmentPolypeptide(1,drw=True)
            #self.model.menuctrl.CheckMenu("BDA points",True)
        elif label == "Two residues":
            #self.model.FragmentAARes(2,True)
            frgobj.FragmentPolypeptide(2,drw=True)
            #self.model.menuctrl.CheckMenu("BDA points",True)
        # fragment non-peptide
        elif label == "Split at Csp3": 
            frgobj.FragmentNonPeptideAuto()
            #self.model.menuctrl.CheckMenu("BDA points",True)
        elif label == "Open split panel": frgobj.OpenAutoFragmentPanel()
        elif label == "Open File setting panel":
            frgobj.OpenFragmentFilePanel()
        elif label == "into monomers": frgobj.FragmentIntoMonomers()
        elif label == "By BDA file": frgobj.OpenBDAFiles()
        #elif label == "By fragment file": frgobj.FragmentByFRGData()
        # fragment water
        elif label == "Water grouping":
            print 'Make water group for fragment'
        elif label == "Read entire BDA file": 
            frgobj.OpenBDAFileAndSetBDA()
        elif label == "Open BDA file panel": 
            frgobj.OpenFragmentFilePanel()
        # Clear
        elif label == "Clear BDA": frgobj.ClearBDA('selected')
        elif label == "All fragments": frgobj.ClearBDA('all')
        elif label == "BDA's in selected": frgobj.ClearBDA('selected')
        # fragment tools
        elif label == "Manual BDA setting":
            frgobj.ManualBDASetting(bChecked)
        elif label == "Join two fragments": frgobj.JoinTwoFragments()
        elif label == "Join selected to neighbor": 
            frgobj.JoinSelectedToNeighbor()
        elif label == "Merge selected": 
            frgobj.MergeSelectedFragments()
        elif label == "Select BDAs": frgobj.SelectBDAs()
        elif label == "Select small fragments":
            frgobj.SelectFragmentWithSize(True)
        elif label == "Select large fragments":
            frgobj.SelectFragmentWithSize(False)   
        elif label == "Plot fragment size": frgobj.PlotFragmentSize()
        elif label == "Plot size distribution": 
            frgobj.PlotFragmentSizeDistribution()
        elif label == "View fragment data": frgobj.ViewFragmentData()
        #elif label == "Clear charges": self.model.ClearAtomCharge()
        elif label == "Save BDAs": frgobj.SaveBDAOnFile('entire')
        elif label == "Fragment data": frgobj.SaveFrgFile()
         
        elif label == "Selected to 2nd layer": frgobj.AssignLayer(2)
        elif label == "Clear 2nd layer": frgobj.ClearLayer(2)
        elif label == "Selected to MM region": frgobj.AssignLayer(12)
        elif label == "Clear MM region": frgobj.ClearLayer(12)
        elif label == "Selected waters to EFP": frgobj.AssignLayer(11)
        elif label == "Clear EFP waters": frgobj.ClearLayer(11)
        # Attribute
        elif label == "Open setting panel":
                 frgobj.OpenAttribPanel()
                 #self.model.winctrl.FragmentAttribPanel()
        elif label == "Clear all attributes": 
            frgobj.DeleteAllFragmentAttributes()
        # Make input data submenu    
        elif label == "Make GAMESS input": self.model.OpenGamessPanel()
        # show submenu       
        elif label == "BDA points": frgobj.DrawBDAPoint(bChecked)
        elif label == "Paint fragment": frgobj.DrawFragmentByColor(bChecked)            
        # Atom charge submenu in Show Menu      
        elif label == "Formal charge": self.model.DrawFormalCharge(bChecked)
        elif label == "Fragment name": frgobj.DrawLabelFrgNam(bChecked)
        elif label == "Fragment charge": frgobj.DrawFragmentCharge(bChecked)
        elif label == "Remove above": frgobj.RemoveAllFragmentDrawItems()
        elif label == "Layer by color": frgobj.DrawLayer(bChecked)
        else:
            mess=self.classnam+'(OnFMO): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  

    def OnAddons(self,label,bChecked):  
        """ 
        'Add-on' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        # echo and log
        checkstr='True'
        if not bChecked: checkstr='False'
        mess='fum.menuctrl.OnAddons("'+label+'",'+checkstr+')'
        if self.model.setctrl.GetParam('echo'): self.model.ConsoleMessage(mess)
        if lib.LOGGING: self.model.WriteLogging(mess)
        # check menu
        self.CheckMenu(label,bChecked)

        if label.find('.py') > 0:
            self.model.ExecuteAddOnScript(label,bChecked)
        #elif label == 'Verbose petit script':
        #    self.setctrl.SetParam('verbose-petit-script',bChecked)
    
    def OnHelp(self,label,bChecked):    
        """ 
        'Help' menu event handler.
        
        :param str label: menu item label,
        :param bool bChecked: True for checked, False for unchecked.
        """
        # echo and log
        self.EchoAndLog('Help',label,bChecked)
        # check menu
        self.CheckMenu(label,bChecked)
        #
        if label == "About": self.model.AboutMessage()
        #elif label == "Version": self.Version()
        elif label == "Customize":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "PDB data":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "Frame data":
            if bChecked: self.model.winctrl.Open(label)
            else: self.model.winctrl.Close(label)
        elif label == "Key bindings": self.model.winctrl.Open(label)
        elif label == "View setting params": self.model.ViewSettingParams()
        elif label == "User's guide": self.model.winctrl.Open(label)
        elif label == "Tutorial": 
            self.model.helpctrl.Tutorial('tutorial',rootname='tutorial')
        elif label == "FU Document": self.model.winctrl.Open(label)
        elif label == "Programming tutorial": self.model.winctrl.Open(label)
        elif label == "Python/wxPython tutorial":
            self.model.winctrl.Open(label)
            self.model.HideWin()
            self.model.helpctrl.Tutorial('Python-tutorial',
                       rootname='Python/wxPython tutorial',navi=False)
        #elif label == "GAMESS document":
        #    self.model.ViewGAMESSDocument()
        else:
            mess=self.classnam+'(OnHelp): '+'"'+label
            mess=mess+'" menu item is not defined'
            lib.MessageBoxOK(mess,"")  
            
    def OnPopupWindow(self,winlabel,label):
        """  Not use. Chganged by the 'PopupMenu' method """
        if winlabel == 'MouseOperationModeWin':
            self.model.mousectrl.OnSwitchMouseMode(label,'False')
            self.mouseoperationmode=label
        if winlabel == 'AnnotationWin':
            pass
                
    def OnHidden(self,label,bChecked):
        """ Hidden menu event handler
        
        :param str label:
        :param bool bChecked:
        """
        # echo and log
        self.EchoAndLog('Hidden',label,bChecked)

        if label == 'Change mouse operation mode':
            self.model.mousectrl.SetShiftKeyDown(False) #shiftkeydown=False
            self.model.mousectrl.SetMouseLeftDown(False) #mouseleftdown=False
            #self.model.ModeMessage('ctrl-on')
            self.model.winctrl.Open('MouseOperationModeWin')
        #elif label == 'Reset mouse operation mode': #ESC key
        #    self.model.mousectrl.OnSwitchMouseMode('Off',False) # space key
        elif label == 'Close popup menu': # ESC key
            # For Mac and LINUX
            try: self.model.mdlwin.popupmenu.OnClose(1)
            except: pass
        elif label == 'Remove all labels': # space key
            self.model.DrawLabelRemoveAll(True,text=True)
        
        elif label == 'Change center of rotation':
            self.model.ChangeCenterOfRotation(True)
        elif label == 'Change mouse mode':
            pass
        # Make/delete bonds
        elif label == 'Delete bond':
            nsel,lst=self.model.ListSelectedAtom()
            if nsel == 2:
                atm1=lst[0]; atm2=lst[1]
                self.model.DeleteBondIJ(atm1,atm2)
            else: 
                mess='select two atoms to delete the bond.'
                self.model.Message(mess,0,'')

        elif label == "Make single bond":
            self.model.ChangeBondMultiplicity(1)            
        elif label == "Make double bond":
            self.model.ChangeBondMultiplicity(2)
        elif label == "Make triple bond":
            self.model.ChangeBondMultiplicity(3)
        elif label == "Make aromatic bond":
            self.model.ChangeBondMultiplicity(4)
        # Project
        elif label == 'Create new project':
            self.model.setctrl.ProjectSetting('New project')
        elif label == 'Import project':
            self.model.setctrl.ProjectSetting('Import project')          

        elif label == 'Magnify':
            self.model.ZoomByKey('magnify')
        elif label == 'Reduce':
            self.model.ZoomByKey('reduce')
        elif label == 'Move upward':
            self.model.TranslateByKey('up')
        elif label == 'Move downward':
            self.model.TranslateByKey('down')
        elif label == 'Move leftward':
            self.model.TranslateByKey('left')
        elif label == 'Move rightward':
            self.model.TranslateByKey('right')
        elif label == 'Save image':
            self.model.SaveCanvasImage('')
        elif label == 'Save view':
            self.model.SaveCurrentView()
        elif label == 'WhoAmI':
            print 'inspect[1][3]',inspect.stack()[1][3]
            print 'inspect[2][3]',inspect.stack()[2][3]
            print 'getargvalue',inspect.getargvalues(self.OnMenu)
            #print 'trace',inspect.trace()
            print 'call args of OnMenu',\
                             inspect.getcallargs(self.OnMenu(1),1,2,3)
            
            menuid=self.event.GetId()
            print 'menuid',menuid
            label=self.GetMenuLabel(menuid)
            print 'label',label
            topmenu=self.menulabeldic[label][1]
            menuhandlerdic=self.MenuHandlerDic()
            handler=menuhandlerdic[label]
            try: bChecked=self.IsChecked(label)
            except: bChecked=False
            print 'label,handler,bCheced',label,handler,bChecked
        
        elif label == 'Focus selected atoms':
            if self.focusselected: self.focusselected=False
            else: self.focusselected=True
            self.model.FocusSelectedAtoms(self.focusselected)
        # Select <- elif label == 'Deselect all': self.model.SelectAll(False)
        elif label == 'Remove rotation axis': 
            self.model.SetRotationAxis(on=False)
        
        elif label == 'Remove text': self.model.TextMessage('')
        
        elif label == 'Set rotation axis': 
            self.model.SetRotationAxis() #True) # axis-rot
        
        elif label == 'Select movable atoms':    
            self.model.SelectMovableAtoms(-1,-1)    
        
        elif label == 'Switch select object':
            selobj=self.model.mousectrl.GetSelObj()
            if selobj == 0: selobj=1
            else: selobj=0
            self.model.mousectrl.OnSwitchMouseMode('selobj',selobj)

        elif label == 'Switch select number':
            selmod=self.model.mousectrl.GetSelMode()
            if selmod == 4: selmod=1
            else: selmod=4
            self.model.mousectrl.OnSwitchMouseMode('selmod',selmod)
        elif label == 'Switch view/build mode':
            mdlmod=self.model.mousectrl.GetMdlMode()
            if mdlmod == 5: mdlmod=0
            elif mdlmod == 0: mdlmod=5
            #self.model.mousectrl.SetMdlMode(mdlmod)
            self.model.mousectrl.OnSwitchMouseMode('mdlmod',mdlmod)
            if self.model.winctrl.IsOpened('Model builder'):
                bldwin=self.model.winctrl.GetWin('Model builder')
                bldwin.SetCenterOfRotation(True)       
        elif label == 'Dump view': self.model.DumpCurrentView(True)
        elif label == 'Restore view': self.model.DumpCurrentView(False)
        
        else:
            mess=self.classnam+'(OnHidden): '+'"'+label
            mess=mess+'" menu item is not defined. '
            mess=mess+'Check your custom "shortcut-key definition" file='
            mess=mess+self.setctrl.GetShortcutKeyFile()
            lib.MessageBoxOK(mess,"")  
                               
    def FileMenu(self):
        """ Define submenue items for 'File' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='File'

        menuitems= (
                  # 'Project' submenu will be inserted at the top in the 'View_Frm' class
                  ("","",False),
                  ("New","Cretaed new molecule",False),
                  ("","",False),
                  ("Open","Open .pdb, .mht, .fuf files",False),
                  ("Merge","Merge into current molecule",False),
                  ("","",False),
                  ("Close current","Unfinished",False),
                  ("Close All","Unfinished",False),
                  ("","",False),
                  ("Save","Save current molecule in PDB file",False),
                  ("Save As","Save molecule",False),
                  ("Save All as", (
                      ("pdb files","Save all molecules in PDB file",False),
                      ("","",False),
                      ("mol files","Save all molecules in MDL Mol file",False),
                      ("sdf file","Save all molecules in sdf file",False),
                      ("","",False),
                      ("xyz files","Save all molecules in xyz file",False),
                      #("xyzs file","Save all molecules in xyzs file",False),
                      ("xyzfu files","Save all molecules in xyzfu file",False),
                      ("","",False),
                      ("zmt files","Save all molecules in zmt file",False),
                      ("zmtfu files","Save all molecules in zmtfu file",
                       False))),
                  #("Save Selected As","Save selected atoms",False),
                 # ("","",False),
                 # ("*Save All","Unfinished",False),
                 # ("*Save All As","Save molecules",False),
                 # ("","",False),
                 # ("*Save Fragment","Unfinished",False),
                 # ("Fragment data", (
                 #     ("Save fragment data as","Save fragment data",False),
                 #     ("Save BDA data as","Save BDA data",False))),
                  ("","",False),
                 #("*Save messages","Save messages on file",True),
                 # ("","",False),
                  ("Save canvas image","Save canvas image on file",False),
                  ("","",False),
                  ("Save log","Save log on file",True),
                  #("Print canvas image","SPrint canvas image",False),
                 #("Screen image", (
                 #     ("*Print","Unfinished",False),
                 #     ("Save bitmap","Save screen bitmap data on file",False))),
                  ("","",False),
                  ("Enable MessageBox","Turn On/Off MessageBox",True),
                  #("Message level","Change message level",False),
                  ("","",False),
                  ("Quit","Quit",False)
                  )

        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def EditMenu(self):
        """
        Define submenue items for 'Edit' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Edit'
        if self.fumode == 1: # fuplot mode
            menuitems= (
                      ("Copy canvas image","Copy canvas image to clipboard",
                                                                      False),
                      ("","",False),
                      ("Clear clipboard","Clear clipboard",False)
                      )
    
        else: # fumodel mode and sinple viewer mode
            menuitems= (
                      ("Molecule object", (
                          ("Copy mol object","Copy molecule object to clipboard",False),
                          ("Cut and copy mol object","Cut selected atoms and copy to clipboard",False),
                          ("Paste mol object","Paste molecule object in clipboard",False))),
                      ("","",False),
                      ("xyz data", (
                          ("Copy xyz text","Copy molecule xyz data to clipboard",False),
                          ("Paste xyz text","Paste molecule xyz data in clipboard",False))),
                      ("","",False),
                      ("Copy canvas image","Copy canvas image to clipvoard",False),
                      ("","",False),
                      ("Clear clipboard","Clear clipboard",False)
                      )
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def ShowMenu(self):
        """
        Define submenue items for 'Show' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Show'
        menuitems= (
                  ("Fit to screen","Fit to screen",False),
                  ("Reset rotation","Reset rotation",False),
                  ("","",False),
                  ("Hide", (
                      ("Hide hydrogen","Hide hydrogen atoms",True),
                      ("Hide water","Hide water molecules",True),
                      ("Hide selected","Hide selected atoms",True),
                      ("","",False),
                      ("Hide all atoms","Hide all atoms",True))),
                  #("Hide environment","not supported yet",True),
                  #("Hide all peptide atoms","Hide all peptide atoms",True),
                  ("","",False),
                  ("Selected only","Show only selected atoms",True),
                  ("Side chain only","Hide amino acid side chain atoms",True),
                  ("Backbone only","Show only backbone atoms",True),
                  ("","",False),
                  ("All atom ","Show all atoms",False),
                  ("","",False),  
                  ("Peptide chain", (
                      ("CAlpha","Show peptide chain in C-alpha connections",True),
                      ("Tube","Show peptide chain in tube",True),)),
                      #("Kite train","Show peptide main chain in kite train",True))),
                  ("","",False),
                  ("Label", (
                      ("Element","show element name",True),
                      ("Atom number","show atom sequence number",True),
                      ("Atom name","show atom name",True),
                      ("Atom name+number","show atom name+number",True),
                      ("Residue name","show residue name",True),
                      ("Residue name+number","show residue name+number",True),
                      ("Chain name","show chain name",True),
                      ("","",False),
                      ("Formal charge","show formal atomic charge",True),
                      ("","",False),
                      ("Remove all","remove all labels",False))),
                  ("Distance", (
                      ("Mode(on/off)","Draw distance between selected two atoms",True),
                      ("Remove","Remove distance labels",False))),
                  #("Axis","PMI axis to selected atom group",True),
                  ("","",False),   
                  ("Bond", (
                      ("Multiple bond","Draw multiple bond",True),
                      ("","",False),
                      ("Hydrogen Bonds","draw hydrogen bond or vdW  contacts",True))),
                      #("vdW contact","Unfinished",True),
                      #("*CH/pi contact","Unfinished",True))),
                  ("Molecular model", (
                      ("Line","Line model",False),
                      ("Stick","Stick model",False),
                      ("Ball and stick","Ball-stick model",False),
                      ("CPK","CPK model",False),
                      ("","",False), 
                      #("*vdW surface","van der Waals surface",True),
                      #("*SA surface","Solvent accessible surface",True),
                      #("","",False), 
                      ("Stereo", "Stereo view",True))),
                  ("","",False),
                  ("xyz-axis","xyz axis",True),
                  ("","",False),
                  ("Color", (
                       ("by element","Color atoms by element",False),
                       ("by residue","Color atoms by residue color",False),
                       ("by chain","Color atoms by chain color",False),
                       ("by fragment","Color atoms by fragment color",False),
                       ("by group","Color atoms by group color",False),
                       ("on color palette","Pop-up color setting panel",False),
                       ("","",False),
                       ("Fog","Color gradient",True),
                       ("Opacity","Set opactity",True),
                       ("","",False),
                       ("Background color","Change background color",False))),
                  ("","",False),
                  ("Viewer", (
                       ("SlideShowCtrl","Open slaide show control panel",True),
                       ("One-by-One","Select on-by-one",True))),
                  ("","",False),
                  ("Dump current view", (
                       ("Dump view","Save current draw items on file",False),
                       ("Restore view","Restore draw items from file",False))),
                  ("Redraw","Redraw",False) 
                    )
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def SelectMenu(self):
        """
        Define submenue items for 'Select' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Select'
        menuitems= (
                  ("Hydrogen atom","Select all hydrogens",False),
                  ("Non bonded atom","Select non-bonded atoms",False),
                  ('','',False),
                  ("Water molecule","Select all water molecules",False),
                  ("Non-AA residue","Select all non-amino acid residues",False),
                  ("AA residue","Select all amino acid residues",False),
                  ("Side chain","Select backbone atoms",False),
                  ("Backbone","Select backbone atoms",False),
                  ('','',False),
                  ("Atoms/Residues", (
                      ("All show atoms","Select all show atoms",False), 
                      ("Ball-and-stick model atoms",
                                         "Select ball-and-stick atoms",False),
                      ("CPK model atoms","Select CPK atoms",False), 
                      ('','',False),
                      ("Atoms within distance",
                           "Select atoms within distance from selectes",False),
                      ("Resdiues within distance",
                               "Select resdiues within distance form selected",
                                                                      False),
                      ('','',False),
                      ("Read select file","Read select file",False))),
                  ('','',False),
                  ("Complement","Select Complement",False),
                  ("Deselect all","Deselect all atoms",False),
                  #("All show atoms","Select all show atoms",False), 
                  ("Select all","Select all atoms",False),                   
                  ("","",False),
                  #("Environment","Select environment atoms",False),                   
                  #("","",False),
                  ("Select object", (
                      ("Atom","selection by atom",False),
                      ("Residue","selection by residue",False),
                      ("Peptide chain","selection by peptide chain",False),
                      ("Group","selection by group",False),
                      ("Fragment","select fragment",False))),
                  ("Multiple selection", (
                      ("1-object", "1-object selection mode",False),
                      ("2-objects", "2-objects selection mode",False),
                      ("3-objects", "3-objects selection mode",False),
                      ("4-objects","4-objects selection mode",False),
                      ("Unlimited","Unlimited selection mode",False),
                      ("","",False),
                      ("Box/Sphere(toggle)","Sphere/box selection mode. Toggle",False),
                      ("Remove box/sphere","Remove Sphere/box",False))),
                  ("Section mode","Section mode on/off",True),
                  ("","",False),
                  #("Display method", (
                  #    ("Preset color","Display selected atoms in color",False),
                  #    ("Bold line","Display selected atoms in bold line",False))),
                  #("","",False),
                  ("Selector", (
                      ("Tree","Pop-up tree selector panel",True),
                      ("Name/Number","Pop-up name/number selector panel",True),))
                  #    ("","",False),
                  #    ("*One-by-One","Pop-up one-by-one selector panel",False))),
                  )        
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def ModelingMenu(self):
        """
        Define submenue items of 'Modeling' menu
        
        :return: menuitems(lst) - submenu item list
        """
        self.toplabel='Modeling'
        menuitems=(
                  ("Undo","Undo",False),
                  ("","",False),
                  #("Add hydrogens","Add hydrogens to polypeptides,waters and other redisues",False),
                  ("Add hydrogens", (
                      ("Open add hydrogen panel","Open add hydrogen panel",
                           False),
                      #("to all residues","Add hydrogen to all resdiues",False),
                      ("","",False),
                      ("to polypeptide",
                           "Add hydrogen to polypeptides and waters",False),
                      ("to non-polypeptide(use frame data)",
                           "Add hydrogen to non-polypeptides and waters",False),
                      ("to non-polypeptide(use bond length)",
                           "Add hydrogen to non-polypeptides and waters",False),
                      ("to water","Add hydrogen to water molecule",False),
                      ("","",False),
                      ("View summary",
                           "View summary of hydrogen addition",False),
                      ("View message log","View message log",False))),
                  ("","",False),
                  ("Attach hydorogen(s)", (
                      ("1H","Add one hydrogen at a selected atom",False),
                      ("2H","Add two hydrogens at a selected",False),
                      ("3H","Add three hydrogens at a selected atom",False))),
                  ("","",False),
                  ("Replace hydrogen with", (
                      ("CH3","",False),
                      ("ACE","",False),
                      ("NME","",False),
                      ("GROUP","Open 'Model builder'",False),
                      ("","",False),
                      ("Merged molecule",
                          "Selected H(H-X) with merged molecule",False))),
                  ("Replace", (
                      ("Ligand in complex","",False),
                      #("with other resdiue","",False),
                      ("Residue(s)","",False),
                      ("","",False),
                      ("Residue coordinates","Change coordinates of redisue",
                                 False))),
                  ("","",False),
                  ("Truncate protein", (
                      #("Open panel","Open panel",False),
                      #("","",False),
                      ("Cap with hydrogens","Cap with hydrogens",False),
                      ("Cap with ACE/NME","Cap with ACE/NME",False))),
                  ("","",False),
                  ("Add bond", (
                      ("Use frame data ","",False),
                      ("Based on bond length ","",False),
                      ("Based on valence ","",False),
                      #("","",False),
                      #("S-S bond","",False),
                      ("","",False),
                      ("Hydrogen bond","",False),
                      ("vdW contact","",False),
                      #("","",False),
                      #("Bond multiplicity","Set bond multiplicity",False),
                      )),
                  ("","",False),
                  ("Delete", (
                      ("Selected atoms","Delete selected atoms",False),
                      ("Non-bonded atoms","Detele non-bonded atoms",False),
                      ("Hydrogen atoms","Delete hydrogen atoms",False),
                      ("","",False),
                      ("Waters","Delete all water molecules",False),
                      ("","",False),
                      ("All bonds","",False),
                      ("Bond multiplicities","",False),
                      ("","",False),
                      ("Hydrogen_bonds","",False),
                      ("vdW contacts","",False),
                      ("","",False),
                      ("TER in PDB data","",False),
                      ("Dummy atoms in ZMatrix","",False))),
                  ("","",False),
                  #("Assign charge", (
                  #    ("to AA residue","Assign charge",False),
                  #    ("to Ions","Assign charge to ion",False),
                  #    ("to selected atom(s)","Assing charges to selected atoms"
                  #                                                 ,False),
                  #    ("","",False),
                  #    ("Clear charges","Clear charges of all atoms",False))),
                  ("Change", (
                      ("Ion charge","Assign charge to ion",False),
                      ("Clear ion chgrges",
                                "Clear ion charges of selected atoms",False),
                      ("","",False),
                      ("Element ","",False),
                      ("Atom name ","",False),
                      ("Residue name ","",False),
                      ("Chain name ","",False),
                      ("Group name ","",False),
                      #("","",False),
                      #("Old atom names to new ones","",False),
                      #("New atom names to old ones","",False),
                      ("","",False),
                      ("Bond length","",False),
                      ("Bond multiplicity","",False))),
                      #("","",False),
                      #("Group charge","",False))),              
                  ("","",False),
                  ("Build molecule", (
                      ("Open Model Builder","",False),
                      ("Open Peptide Builder","",False))),
                  ("","",False),
                  ("Mutate amino acid residue", (
                      ("Open HIS Form Changer","",False),
                      ("Open Mutate Panel","",False))),
                  ("","",False),
                  ("Edit Conformation", (
                      ("Open Rotate Bond Editor","",False),
                      ("Open Torsion Editor","",False),
                      ("Open ZMatrix Editor","",False))),
                  ("","",False),
                  ("Immerse in box waters","",False),
                  ("","",False),
                  ("Update coordinates", (
                      ( "from file",
                            "Replace coordinates with these in xyz file",False),
                      ( "from output file",
                            "Replace coordinates with in output file",False),
                      ( "from clipboad(xyz)",
                        "Replace coordinates with these in clipboad",False))),                  
                )
        #                           
        return menuitems

    def GroupMenu(self):
        """
        Define submenue items for 'Group' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Group'
        menuitems= (
                  ("Make group", (                 
                      ("Selected atoms ","Unfinished",False),
                      ("do. with environment","Unfinished",False),
                      ("","",False),
                      ("Split at TER","Unfinished",False),
                      ("do. with environment ","Unfinished",False),
                      ("","",False),
                      ("Split by chain","Unfinished",False),
                      ("do. with environment  ","Unfinished",False))),
                  ("Make molecule", (
                      ("Selected atoms  ","Unfinished",False),
                      ("Split at TER ","Unfinished",False),
                      ("Split by chain ","Unfinished",False))),                                
                  ("","",False),
                  ("Combine", (
                      ("all molecules","Unfinished",False),
                      ("all groups","Unfinished",False),
                      ("By choose panel","Pop-up choose panel",False))),
                  ("","",False),
                  ("Rename/Remove", (
                      ("Remove all groups","Unfinished",False),
                      ("Remove all molecules","Unfinished",False),
                      ("By popup panel","Pop-up panel",False),
                      ("","",False),
                      ("Dummy","dummy",False))),          
                  )      
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def UtilityMenu(self):
        """
        Define submenue items for 'Utility' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Utility'
        menuitems= (
                  ("Molecule info", "Molecule information",False),
                  ("","",False), 
                  ("Geometry", (
                       ("Short contact","",False),
                       ("","",False),
                       ("Bond lengths","Plot bond lengths",False),
                       ("Bond angles","Plot bond anglesd",False),
                       #("Torsion angles","Unfinished",False),
                       #("Peptide angles","Unfinished",False),
                       ("","",False),
                       ("Hydrogen_bond","Plot hydrogen bonds",False))),
                       #("vdW contact","",False),
                       #("CH/pi bond","",False))),    
                  ("","",False),
                  ("PDB data", (
                       ("Missing residue info",
                                'Missing residue info in PDB file',False),
                       #("","",False),
                       ("Plot B-factor","Plot b factor",False),
                       #("","",False),
                       ("Delete TER's","",False),
                       ("","",False),
                       ("Change atom names to new","",False),
                       ("Change atom names to old","",False),
                       ("","",False),
                       ("Split, join and extract","Split/join/extract pdb data",
                                 False),
                       ("Compare files","Compare pdb files",False))),
                  ("","",False),                  #["Open ChildWin,"Chaild view window",True],            
                  ("Open EasyPlotWin","plot data in output file",True),
                  #["Open MatPlotLibWin","Open matplotlib panel",True],             
                  ("Open ExecScriptWin","Open execute script panel",True),
                  ("Open ScriptEditor","Open script editor",True),
                  )
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def FMOMenu(self):
        """
        Define submenue items for 'FMO' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='FMO'
        if self.fumode == 2: # fuplot mode
            menuitems= (
                      ("Show", (
                          ("BDA points","Show BDA of FMO",True),
                          ("Formal charge",
                              "Show formal charges for FMO fragmentation",True),
                          ("Fragment name","Label fragment name",True),
                          ("","",False),
                          ("Layer by color","Show by layer color",True))),
                      )
        else:
            menuitems= (
                      ("Outline of fragmentation","Document,False",False),
                      ("","",False),
                      ("Open fragment panel","Open fragmentatin panel",
                                                                    False),
                      ("","",False),
                      ("Fragment polypeptide into", (
                          ("One residue","divie into one residues",False),
                          ("One residue except Gly",
                                 "divide into one except gly",False),
                          ("Two residues",
                                "divide into two amino acid residues",False))),                      
                      ("Fragment non-peptide", (
                          ("Split at Csp3",
                           "automatic fragment at sp3 carbons",False),
                          ("Open split panel","Open panel",False),
                          ("","",False),
                          ("into monomers",
                               "Fragment system into connected group",False))), 
                          #("By BDA file","Read BDA file",False),
                          #("Open File setting panel","Open panel",False))),
                          #("By fragment file","Read fragment file",False))),                 
                      #("Fragment water", (                      
                      #    ("1 molecule/fragment","",False),
                      #    ("*Water grouping",
                      #           "Grouping waters as fragment ",False))),
        
                      ("","",False),
                      ("Fragment By BDA file", (
                           ("Read entire BDA file",
                                       "Read BDA file of entire system",False),
                           ("Open BDA file panel","Read BDA file",False))),
                      ("","",False),
                      ("Clear BDA","Clear BDAs(Fragments)",False),
                                 # all fragments","Clear all BDA's and fragments",
                           #False),
                      #     ("BDA's in selected",
                      #            "Clear BDA's in selected atoms",False),
                      #     ("All fragments","Clear all fragments",False))),
                      ("","",False),
                      ("Fragment tools", (
                          ("Manual BDA setting","Manual fragment mode",True),
                          ("","",False),
                          ("Join two fragments","Join selected two fragments",
                                       False),
                          #("Join selected to neighbor",
                          #    "Join selected fragments to neighbor",False),
                          #("Merge selected","Merge selected fragments",False),
                          ("","",False),
                          ("Select BDAs","Select BDAs",False),
                          ("Select small fragments",
                                 "Select small fragment",False),
                          ("Select large fragments",
                                 "Select large fragment",False),
                          ("","",False),
                          ("Plot fragment size","Plot fragment size",False),
                          ("Plot size distribution",
                                 "Plot size distribution",False))),
                      #    ("BDA data","Save BDA data",False),
                      #    ("Fragment data","Save Fragment data",False))),
                      ("","",False),
                      ("Fragment attribute", (
                          ("Open setting panel",
                                 "popup property assignment panel",False),
                          ("","",False),
                          ("Clear all attributes",
                                 "Clear all attribute assignment",False))),
                      ("View fragment data","View data",False),
                      ("","",False),
                      ("Save BDAs","Save fragment data",False),
                      ("","",False),    
                      ("Show", (
                          ("BDA points","Show BDA of FMO",True),
                          ("Paint fragment",
                              "Show atoms in fragment color",True),
                          #("Formal charge",
                          #    "Show formal charges for FMO fragmentation",True),
                          ("Fragment name","Label fragment name",True),
                          ("Fragment charge","Draw fragment charges",True),
                          ("","",False),
                          ("Remove above",
                                 "Remmove BDA, Paint, Charge, name",False))),
                          #("","",False),
                          #("Layer by color","Show layer in color",True))),
                      )
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def WindowMenu(self):
        """
        Define submenue items for 'Window' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Window'
        menuitems= [
                  ["Open MouseModeWin","Open mouse mode panel",True],
                  ["Open MolChoiceWin","Open molecule choice panel",True],
                  ["","",False],
                  ["Open PyShell","Open PyShell/PyCrust panel",True],
                  #["Open ToolsWin","Open tools panel",True],
                  ["","",False],
                  ["Open ControlWin","Pop-up control panel",True],
                  #["","",False],                  #["Open ChildWin,"Chaild view window",True],            
                  #["Open EasyPlotWin","plot data in output file",True],
                  #["Open MatPlotLibWin","Open matplotlib panel",True],             
                  #["","",False],
                  #["Open ExecScriptWin","Open execute script panel",True],
                  #["Open ScriptEditor","Open script editor",True],
                  
                  ]
        #if self.model.setctrl.GetParam('tools'):
        #    toolswin=["Show ToolsWin","Show/Hide tools panel",True]
        #    menuitems.append(["","",False])
        #    menuitems.append(toolswin)
            
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems             

    def HelpMenu(self):
        """
        Define submenue items for 'Help' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Help'
        menuitems= (
                  ("About","About",False),
                  #("Version","version",False),
                  ("","",False),
                  ("Documents", (
                      ("Key bindings","Display key bindings table",False),
                      ("View setting params","View current settin gparameters",
                              False),
                      ("","",False),
                      ("User's guide","Open fumodel users document",False),
                      ("Tutorial","Open FU/FMO tutorial",False),
                      #("","",False),
                      #("Python/wxPython tutorial","Open Python/wxPython tutorial",False),
                      ("","",False),
                      ("Programming tutorial","Programming tutorial",False),
                      ("FU Document","Open HTML document of FU",False))),                 
                  ("","",False),
                  ###("Customize",
                  ###       "Customize paramters and set them setting file",True),
                  #("","",False),
                  #("Search keyword","Serch keyword",False),
                  #("","",False),
                  #("*Open operation guide","Not supported yet",False),
                  #("","",False),
                  #("WEB site visit","Unfinished",False),
                  ###("","",False),
                  ("Frame data",
                        "Download frame data(monomers) form pdb.ftp site",True),
                  ("PDB data","Download pdb file form PDBj ftp site",True),
                  #("","",False),
                  #("Tests","Test fumodel functions",False),
                  )
        #mset= ("Setting", (
        #          #("Paramters","Parameters",False),
        #          ("GAMESS path","Path and command of GAMESS",False),))
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def ToolsMenu(self):
        """
        Define submenue items for 'Tools' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Tools'
        menuitems= (
                  ("Overlay", (
                      ("Use selected three atoms","Unfinished",True),
                      ("Use all heavy atoms","Unfinished",True),
                      ("Use all atoms","Unfinished",True))),
                  ("RMS fit", (
                      ("Selected atom","Unfinished",True),
                      ("All heavy atoms","Unfinished",True),
                      ("All atoms","Unfinished",True))),
                  )
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def HiddenMenu(self):
        """
        Define submenue items for 'Hidden' menu. This is not a real menu
             and only accessed by shortcut-key.
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Hidden'
        menuitems= (
                  ("Hidden", (
                      ('Change mouse operation mode',
                             "Change mouse operation mode",False),
                      ('Reset mouse operation mode',
                             "Reset mouse operation mode",False),
                      ('Change center of rotation',
                             'Change center of rotation',False),
                      ('','',False),
                      ('Delete bond',
                             'delete bond between selected two atoms',False),
                      ('Make single bond',
                             'Make single between selected two atoms',False),
                      ('Make double bond',
                             'Make double between selected two atoms',False),
                      ('Make triple bond',
                             'Make triple between selected two atoms',False),
                      ('Make aromatic bond',
                             'Make aromatic between selected two atoms',False),
                      ('','',False),
                      ('Create new project','Open new project panel',False),
                      ('Import project','Open import project panel',False),
                      ('','',False),
                      ('Magnify','Magnify',False),
                      ('Reduce','Reduce',False),
                      ('','',False),
                      ('Move upward','Move upward',False),
                      ('Move downward','Move downward',False),
                      ('Move leftward','Move leftward',False),
                      ('Move rightward','Move rightward',False),
                      ('','',False),
                      ('Save image','Save canvas image on file',False),
                      ('','',False),
                      ('Dump view','dump view,False'),
                      ('Restore view','restore view,False'),
                      ('','',False),
                      ('WhoAmI','Find current execution method',False))),
                  )
        return menuitems
  
    def ComputeMenu(self):
        """
        Define submenue items for 'Compute' menu
        
        :return: submenu items
        :rtype: lst
        """
        self.toplabel='Compute'
        menuitems= (
                  ("GAMESS", (
                      ("Use internal data","use internally generated input data"
                            ,False),
                      ("Read input file","read GAMESS input file",False))),
                  )
                  #("MOPACK","Unfinished",False),
                  #("TINKER","Unfinished",False)))
        # create menu object
        #menu=self.CreateMenuFromList(self.toplabel,menuitems)        
        return menuitems

    def PopupMenu(self):
        self.toplabel='Popup'
        menulst=[]; tiplst=[]
        if self.model.mol is None or len(self.model.mol.atm) <= 0:
            #menulst.append('Build molecule:')
            #tiplst.append('label')
            lst=['Open Model Builder','Open Peptide Builder']
            menulst=menulst+lst
            tiplst=tiplst+['','']
            return menulst,tiplst                 
        #
        selnmb,sellst=self.model.ListSelectedAtom()
        # selobj: 0:atom, 1:residue, 2:chain, 3:group, 4:fragment(FMO)
        selobj=self.model.mousectrl.GetSelObj()
        if selobj == 0 and selnmb == 1:
            if self.model.mol.atm[sellst[0]].elm == ' H': 
                menulst.append('Replace hydrogen with:')
                tiplst.append('label')
                lst=['   CH3','   ACE','   NME']
                menulst=menulst+lst
                tiplst=tiplst+['methyl group','acetyl group','N-methyl amide']
            else:
                menulst.append('Attach hydrogen:'); tiplst.append('label')
                lst=['   1H','   2H','   3H']
                menulst=menulst+lst
                tiplst=tiplst+['one hydrogen','two hydorgens','thre hydrogens']
            menulst.append('Change:'); tiplst.append('label')
            menulst.append('   atom name')
            tiplst.append('change atom name')
            menulst.append('   element'); tiplst.append('change element')
            menulst.append('   ion charge')
            tiplst.append('change ion(atom) chargelabel')
        elif selobj == 0 and selnmb == 2:
            if not self.model.mousectrl.IsRotAxisSet():
                menulst.append('Set rotation axis'); tiplst=tiplst+['']
            #if not self.model.draw.IsDrawLabel('Distance'):
            #if self.model.mousectrl.GetMdlMode() == 1:
                menulst.append('Draw distance'); tiplst=tiplst+['']            
            menulst.append('Bond:'); tiplst=tiplst+['label']
            if sellst[1] in self.model.mol.atm[sellst[0]].conect:
                lst=['   delete','   to single','   to double',
                     '   to triple']; tiplst=tiplst+4*['']
            else:
                lst=['   single','   double','   triple']
                tiplst=tiplst+3*['']
            menulst=menulst+lst
        if selobj == 1 and selnmb > 0:
            menulst.append('Change residue name'); tiplst=tiplst+[''] 
        if selobj == 3 and selnmb > 0:
            menulst.append('Change group name'); tiplst=tiplst+[''] 
        #
        if self.model.draw.IsDrawLabel('Distance'):
            menulst.append('Remove distance'); tiplst=tiplst+['']
        if self.model.draw.IsDrawLabel('Tube'):
            menulst.append('Remove chain tube'); tiplst=tiplst+['']
        if self.model.mousectrl.IsRotAxisSet():
            menulst.append('Remove rotation axis'); tiplst=tiplst+['']
            menulst.append('Select movable atoms'); 
            tiplst=tiplst+['select movable atoms around the axis']
        if self.model.mousectrl.GetSelMode() == 5:
            menulst.append('Quit bulk selection')
            tiplst=tiplst+['quit the bulk selection mode']
        if self.model.draw.IsDrawLabel('selectsphere'):
            menulst.append('Remove sphere')
            tiplst=tiplst+['remove selection sphere']
        if self.model.draw.IsDrawLabel('Message'):
            menulst.append('Remove text')
            tiplst=tiplst+['remove text in screen']
        #
        if self.model.draw.IsDrawLabel('Hydrogen Bonds'):
            menulst.append('Remove hydrogen bonds'); tiplst=tiplst+['']
        menulst.append('Show:'); tiplst.append('label')
        lst=['   selected only','   show all','   hide hydrogen',
             '   hide water','   atom number','   residue name',
             '   hydrogen bonds']
        tiplst=tiplst+7*['']
        if not self.model.draw.IsDrawLabel('Tube'):
            lst.append('   chain tube')
            tiplst.append('draw peptide chain tube')
        menulst=menulst+lst
        if selnmb > 0:
            menulst.append('Deselect all'); tiplst=tiplst+['']
        
        return menulst,tiplst
        
    def OnPopupMenu(self,cmd,label):
        if cmd[-1:] == ':': return
        self.model.Message('') # clear status bar
        # Modeling
        # 'New' molecule
        if cmd == 'Open Model Builder': 
            self.OnModeling('Open Model Builder',False)
        elif cmd == 'Open Peptide Builder': 
            self.OnModeling('Open Peptide Builder',False)
        # number of select atoms > 0
        elif cmd == '   1H': self.OnModeling('1H',False)
        elif cmd == '   2H': self.OnModeling('2H',False)
        elif cmd == '   3H': self.OnModeling('3H',False)
        elif cmd == '   CH3': self.OnModeling('CH3',False)
        elif cmd == '   ACE': self.OnModeling('ACE',False)
        elif cmd == '   NME': self.OnModeling('NME',False)
        elif cmd == '   atom name': self.OnModeling('Atom name ',False)
        elif cmd == '   element': self.OnModeling('Element ',False)
        elif cmd == '   ion charge': self.OnModeling('Ion charge',False)
        elif cmd == 'Change residue name': 
            self.OnModeling('Residue name ',False)
        elif cmd == 'Change group name': self.OnModeling('Group name ',False) 
        # Show
        elif cmd == '   selected only': self.OnShow('Selected only',True) 
        elif cmd == '   show all': self.OnShow('All atom ',True) 
        elif cmd == '   hide hydrogen': self.OnShow('Hide hydrogen',True)
        elif cmd == '   hide water': self.OnShow('Hide water',True)
        elif cmd == '   chain tube': self.OnShow('Tube',True)
        elif cmd == '   atom number': self.OnShow('Atom number',True)
        elif cmd == '   residue name': self.OnShow('Residue name+number',True)
        elif cmd == '   hydrogen bonds': self.model.DrawHBOrVdwBond(True)
        elif cmd == 'Draw distance': 
            if self.model.menuctrl.IsChecked('Mode(on/off)'): on=False
            else: on=True
            self.OnShow('Mode(on/off)',on)
        elif cmd == 'Remove distance': self.OnShow('Remove',True)
        elif cmd == 'Remove chain tube': self.OnShow('Tube',False)
        elif cmd == 'Remove sphere': self.OnShow('Tube',False)
        elif cmd == 'Remove hydrogen bonds': self.model.DrawHBOrVdwBond(False)
        # Select
        elif cmd == 'Remove sphere': self.OnSelect('Remove box/sphere',False)
        elif cmd == 'Quit bulk selection': 
            self.OnSelect('Box/Sphere(toggle)',False)
        elif cmd == 'Deselect all': self.OnSelect('Deselect all',False)
        # Hidden
        elif cmd == 'Set rotation axis': 
            self.OnHidden('Set rotation axis',False)
        elif cmd == 'Remove rotation axis': 
            self.OnHidden('Remove rotation axis',False)
        elif cmd == 'Select movable atoms': 
            self.OnHidden('Select movable atoms',False)
        elif cmd == 'Remove text': self.OnHidden('Remove text',False)
        
        elif cmd == '   delete': self.OnHidden('Delete bond',False)
        elif cmd == '   single' or cmd == '   to single': 
            self.OnHidden('Make single bond',False)
        elif cmd == '   double' or cmd == '   to double': 
            self.OnHidden('Make double bond',False)
        elif cmd == '   triple' or cmd == '   to triple': 
            self.OnHidden('Make triple bond',False)
        else:
            mess='Not defined menu item="'+cmd+'"'
            lib.MessageBoxOK(mess,'menuctrl(OnPopupMenu)')
        
    def PrependProjectMenu(self,prjnamlst,helplst):
        """ Prepend project menu
        
        :param lst prjnamlst: submenu item list
        :param lst help: list of tips for submenu items 
        """
        self.toplabel='File'
        filemenu=self.menubar.GetMenu(0)
        submenu=wx.Menu()
        for i in range(len(prjnamlst)):
            label=prjnamlst[i]; help=helplst[i]
            menuitem=submenu.AppendCheckItem(-1,label,help=help) #helpString=help)
            self.menulabeldic[label]=[menuitem,self.toplabel]
        filemenu.PrependMenu(-1,'Project',submenu)

    def PrependFileHistoryMenu(self,hisnamlst,helplst):
        """ Prepend project menu
        
        :param lst prjnamlst: submenu item list
        :param lst help: list of tips for submenu items 
        """
        self.toplabel='File'
        filemenu=self.menubar.GetMenu(0)
        submenu=wx.Menu()
        for i in range(len(hisnamlst)):
            label=hisnamlst[i]; help=helplst[i]
            menuitem=submenu.Append(-1,label,help=help) #helpString=help)
            self.menulabeldic[label]=[menuitem,self.toplabel]
        submenu.AppendSeparator()
        label='Clear history'
        menuitem=submenu.Append(-1,label,help='Clear history')
        self.menulabeldic[label]=[menuitem,self.toplabel]
        filemenu.PrependMenu(-1,'File history',submenu)

    def RemoveMenuItem(self,toplabel):
        """ Remove top menu item
        
        :param str toplabel: menu item label
        """
        filemenu=self.menubar.GetMenu(0)
        fileid=filemenu.FindItem(toplabel)
        removeitem=filemenu.Remove(fileid)
        
    def CreateMenuFromList(self,toplabel,submenud):
        """ Create menu using item lsit
        
        :param str toplabel: top menu item label
        :param lst submenud: list of submenu items
        :seealso: i.e. EditMenu() for submenu item list
        """
        # toplebel: dummy.
        menu = wx.Menu()
        for item in submenud:
            if len(item) == 2:
                label=item[0]
                submenu=self.CreateMenuFromList(label,item[1])
                newid=wx.NewId()
                menu.AppendMenu(newid,label,submenu)
            else: self.CreateMenuItem(menu,*item)
        return menu

    def SetProjectMenuItems(self,projectmenuitems):
        """ Set submenu items to 'File-Project' menu
        
        :param lst projectmenuitems: project submenu items
        """
        self.projectmenuitems=projectmenuitems
        
    def GetProjectMenuItems(self):
        """ Return project menu items
        
        :return: project menu items(self.projectmenuitems)
        """
        return self.projectmenuitems
    
    def CreateProjectMenuItems(self):
        """ Create project menu items
        """
        prjnamlst=[]; helplst=[]
        # set project menu items
        prjdatlst=self.setctrl.GetProjectNameList()
        #prjnamlst.append('None')
        helplst.append('This is not project')
        for prjdat in prjdatlst:
            prjnamlst.append(prjdat[0])
            #if prjdat[0] == 'None': continue
            text=prjdat[4][:80]
            helplst.append(text)
        prjnamlst=['None']+prjnamlst
        helplst=['none project']+prjnamlst
        self.PrependProjectMenu(prjnamlst,helplst)
        curprj=self.setctrl.GetParam('curprj')
        self.CheckMenu(curprj,True)
        self.projectmenuitems=prjnamlst

    def CreateFileHistoryMenuItems(self):
        """ Create file history menu items
        """
        hisnamlst=[]; helplst=[]
        prjdatlst=self.setctrl.GetProjectNameList()
        hislst=self.model.filehistory.Get()
        helplst.append('This is file history')
        for hisdat in hislst:
            if len(hisdat) <= 0: continue
            hisnamlst.append(hisdat)
            helplst.append(hisdat)
        self.PrependFileHistoryMenu(hisnamlst,helplst)
        self.filehistorymenuitems=hisnamlst

    def CreateMenuItem(self,menu,label,status,kind):
        if not label:
            menu.AppendSeparator()
            return
        if kind: checkbox=wx.ITEM_CHECK
        else: checkbox=wx.ITEM_NORMAL
        newid=wx.NewId()
        menuitem=menu.Append(newid,label,status,checkbox)
        self.menulabeldic[label]=[menuitem,self.toplabel]

    def MakeMenuLabelDic(self):
        """ Make menu label dictionary from menud data defined in 
            'XXXXMneu'(i.e. 'FileMene') method
        
        :return: {'Top menu label':['summenu label:subsubmenu label','tips'],..}
        :rtype: dic
        :see: 'PickUpMenuLabel'
        :note: uses temporally variables,self.toplabel,self.sublabel, 
            self.tempflag, and self.memulabellst 
        """
        self.toplabel=''; self.sublabel=''; self.tempflag=False
        toplabel=['File','Edit','Show','Select','Modeling','Utility',
                  'FMO','Window','Hidden']
        menudmethod=[self.FileMenu,self.EditMenu,self.ShowMenu,self.SelectMenu,
                self.ModelingMenu,self.UtilityMenu,self.FMOMenu,self.WindowMenu,
                self.HiddenMenu]
        #
        self.menulabellst=[]
        for i in range(len(toplabel)):
            self.toplabel=toplabel[i]; self.sublabel=''
            menud=menudmethod[i]()
            label=menud[0]
            self.PickUpMenuLabel(label,menud)
        # make dictionary
        menulabeldic={}
        for label in self.menulabellst:
            if len(label) <= 0: continue
            items=label.split('-',1)
            if len(items) == 1: items.append('')
            topsub=items[0].split(':',1)
            if topsub[0] == 'Hidden': topsub[1]=topsub[1].replace('Hidden:','')
            if menulabeldic.has_key(topsub[0]): 
                menulabeldic[topsub[0]].append([topsub[1][1:],items[1]])
            else:
                menulabeldic[topsub[0]]=[]
                menulabeldic[topsub[0]].append([topsub[1][1:],items[1]])                 
        return toplabel,menulabeldic

    def PickUpMenuLabel(self,label,menud):
        """ not used. 04Dec2014
        Pick up menu labels in menud data defined in 
            'XXXXMneu'(i.e. 'FileMene') method
        
        :param str label: menu label
        :param lst menud: menud data
        :see: 'MakeMenuLabelDic'
        :note: uses temporally variables,self.toplabel,self.sublabel, 
            self.tempflag, and self.memulabellst
        """
        for item in menud:
            if len(item) == 2:
                label=item[0]
                self.sublabel=self.sublabel+':'+label
                self.PickUpMenuLabel(label,item[1])
                self.tempflag=True
            else:
                if len(item[0]) > 0:
                    text=self.toplabel+':'+self.sublabel+':'+item[0]+'-'+item[1]
                    self.menulabellst.append(text)
                if self.tempflag:
                    loc=self.sublabel.rfind(':')
                    if loc >= 0: self.sublabel=self.sublabel[:loc]
                self.tempflag=False

    def ListMenuItems(self,toplabel):
        """ List submenu items
        
        :param str toplabel: top menu label
        :return: itemlst(lst) or itemdic(dic)
        """
        itemlst=[]; itemdic={}
        if toplabel =='all':
            for label,lst in self.menulabeldic.iteritems():
                if not itemdic.has_key(lst[1]): itemdic[lst[1]]=[]
                itemdic[lst[1]].append(label)
            return itemdic
        else:
            for label,lst in self.menulabeldic.iteritems():
                if lst[1] == toplabel: itemlst.append(label)
            return itemlst
        
                             
# Mouse and keyboard input controller
class MouseCtrl():
    def __init__(self,parent):
        self.model=parent # Model
        self.mdlwin=parent.mdlwin
        self.setctrl=parent.setctrl
        # initialize mouse status
        self.ctrlkeydown=False; self.shiftkeydown=False
        self.mouserightdown=False; self.mouseleftdown=False
        # items for combobox
        self.musmoditems=['rotate','translate','zoom','x-rotate','y-rotate',
                          'z-rotate','inplane-rot','axis-rot','--------',
                          'set axis']
        self.selmoditems=['1-object','2-objects','3-objects','4-objects',
                          'unlimited','box/sphere']
        self.selobjitems=['atom','residue','side chain','chain','group',
                          'fragment']
        # items for 'ModelModeWin' subwindow
        self.modenamlst=['Off', # model mode off
                         'Show Distance', # 'Show'-'Distance'-'Mode(on/off)'
                         'Sphere/Box Selection', #mouse mode: cntlkeydown=True/False
                         'Make bond', # cretae/delete bond by mouse L-Click
                         'Section mode', # section select mode
                         'Change Geometry', # change geometry mode  
                         ]
        # Note:  (WINDOWS only)Button cliked event does not happen
        # when the same item as previous selection is selected.
        # therefore, rather redandant item 'Cancel' is added.
        if lib.GetPlatform() == 'WINDOWS': self.modenamlst.append('Cancel')
        self.tooltips=['Turn off model mode',
                       'Bulk selection by mouse L-drag',
                       'Draw distance between selected two atoms',
                       'Change geometry by mouse L-drag',
                       'Section select by mouse wheel',
                       ]
        self.winbgcolor=['light gray','pale green','yellow']
        # initialize variables
        self.posatmx=[]; self.posatmy=[]; self.pntatm=-1
        self.posx=0.0; self.posy=0.0; self.pos=wx.Point(0,0)
        #?self.pa=-1; self.pntatmhis=[]
        self.pa=-1;
        self.pntatmhis=lib.ListStack(self); self.pntatmhis.SetMaxDepth(10) #4)
        self.rotaxispnts=[] # [pnt1,pnt2] axis deninition points for rotation
        self.rotaxisatms=[] # [atm1,atm2]
        #self.posx=0; self.posy=0 # current mouse position
        # selection control flags
        #self.isctrldown=False; self.isshiftdown=False
        self.selinipos=[]
        self.selcirc=False; self.selrect=False #; self.srect=[]; self.scirc=[]
        #
        self.musmodtxt=['free','translate','zoom','x','y','z','inplane','axis']
        self.mdlmod=0 # 0: None, 1: Show disrtance, 2:Sphere/Box selection, 
        #               3:Make bond, 4:Section mode,5:Change geometry, 6:Build
        self.musmod=0 # 0:rotation,1:translatiton, 2:zoom, 3:rotation around Z
        self.selmod=0 # 0:single, 1:dual,2:triple,3:quadruple, 4:multiple, 5:shphere/box
        self.selobj=0 # 0:atom, 1:residue,2:side chain,3:chain,4:group,5:fragment(FMO)
        self.secmod=0 # 0:False, 1:True
        self.bdamod=0 # 0:False, 1:True
        # key staus
        self.ctrlkey=False
        self.shiftkey=False
        self.altkey=False
        self.vkey=False
        # sensitivity
        self.sensitive=1.0
        # save variables
        self.musmodsav=0; self.selmodsav=0; self.selobjsav=0
        
    def IsRotAxisSet(self):
        if len(self.rotaxispnts) > 0: return True
        else: return False
    
    def OnSwitchMouseMode(self,item,value):
        """ Switch mouse mode
        
        :param str item: 'musmod','selmod',selobj','section', and 'sphere/box'
        :param int value: mode number
        """
        if item  == 'musmod':
            return
            #if musmod == 7: self.model.SetRotationAxis(True) # axis-rot
            #else:
            #    if self.musmod == 7: self.model.SetRotationAxis(False) 
        elif item == 'mdlmod':
            self.SetMdlMode(value)
        
        elif item == 'selmod':
        # selmod 0:1-obj,1:2-obj,2:3-obj, 3:4-obj, 5:unlimit, 'sphere/box'
            self.SetSelMode(value)
            self.SetSelModeSelection(value)
            return
        elif item == 'selobj':
            # value 0:atom,1:residu,2:peptide chain,3:group,4:fragment
            self.SetSelObj(value)
            self.SetSelObjSelection(value)
            return        
        elif item == 'section':
            # value True or False
            self.SetSectionMode(value)
            return           
        # the following items are set in 'ModelMOdeWin' subwindow
        elif item == 'Off': # turn off model modes
            self.model.TextMessage('','')
            self.ResetModelMode()
            ###self.model.RemoveDrawMessage('modemessage')
            return
        elif item == 'Show Distance':
            self.mdlmod=1
            self.selobjsav=self.selobj
            self.selmodsav=self.selmod
            self.OnSwitchMouseMode('selmod',1)
            self.OnSwitchMouseMode('selobj',0)
            self.model.menuctrl.OnShow("Mode(on/off)",True)
            #self.model.DrawMessage('modemessage',item,'',[],[])
        elif item == 'Sphere/Box Selection':
            self.model.TextMessage('[Sphere/Box Selection','yellow')
            self.mdlmod=2
            #self.SetCtrlKeyDown(True)
            #self.model.DrawMessage('modemessage',item,'',[],[])
        elif item == 'Make bond':
            self.model.TextMessage('[Make Bond]: ','yellow')
            self.mdlmod=3
            self.selobjsav=self.selobj
            self.selmodsav=self.selmod
            self.OnSwitchMouseMode('selmod',1)
            self.OnSwitchMouseMode('selobj',0)
            #self.model.DrawMessage('modemessage',+item+,'',[],[])
        elif item == 'Section mode':
            self.mdlmod=4
            self.model.menuctrl.OnSelect('Section mode',True)
        elif item == 'Change Geometry':
            #self.model.TextMessage('[Change Geometry]: ','yellow')
            self.mdlmod=5
            self.model.mousectrl.SetMdlMode(self.mdlmod)
            #wx.MessageBox("Worning: You are in the change coordinate mode.","Ctrl-key pressed mode",
            #              style=wx.OK|wx.ICON_EXCLAMATION)
            #bgcolor=self.setctrl.GetParam('win-color-geom-mode')
            #self.model.ChangeBackgroundColor(bgcolor)
            self.model.SaveAtomCC()
        #self.model.TextMessage('['+item+']','yellow')
        #self.model.DrawMessage('modemessage',item,'',[],[])

    def ResetModelMode(self):
        self.model.TextMessage('')
        if self.mdlmod == 1: 
            self.model.menuctrl.OnShow("Mode(on/off)",False)# 'Show distance'
        #elif self.mdlmd == 2: # 'Sphere/Box selection'
            
        elif self.mdlmod == 3: # 'Make Bond'
            self.RecoverSelMode(); self.RecoverSelObj()
        elif self.mdlmod == 4: 
            self.model.menuctrl.OnSelect('Section mode',False) #'Section mode'
        elif self.mdlmod == 5: # 'Change geometry'
            pass
            #bgcolor=self.setctrl.GetParam('win-color')
            #self.model.ChangeBackgroundColor(bgcolor)
            #self.model.mdlwin.ChangeMouseModeWinBGColor('light gray')
        #
        self.mdlmod=0
        self.model.mdlwin.ChangeMouseModeWinBGColor(self.winbgcolor[0])
        self.SetCtrlKeyDown(False)
                    
    def SetCirclePosition(self,pos):
        self.circleposition=pos

    def GetCirclePosition(self):
        return self.circleposition

    def GetSelectSphereCenter(self):
        return self.selcntatm
    
    def Reset(self):
        #self.ctrlkeydown=False; self.shiftkeydown=False
        self.mouserightdown=False; self.mouseleftdown=False
        #
        self.posatmx=[]; self.posatmy=[]; self.pntatm=-1
        self.posx=0.0; self.posy=0.0; self.pos=wx.Point(0,0)
        #?self.pa=-1; self.pntatmhis=[]
        self.pa=-1; self.pntatmhis.Clear()
        # selection control flags
        self.isctrldown=False; self.isshiftdown=False
        self.selinipos=[]; self.selcirc=False; self.selrect=False; 
        self.srect=[]; self.scirc=[]
        self.lclickcir=False; self.lclickrec=False; self.dragselected=False
        #
        self.musmod=0; self.selmod=0; self.selobj=0; self.secmod=0; 
        self.bdamod=0 
        self.SetMouseMode(self.musmod)
        self.SetMouseModeSelection(self.musmod)
        self.SetSelMode(self.selmod)
        self.SetSelModeSelection(self.selmod)
        self.SetSelObj(self.selobj)
        self.SetSelObjSelection(self.selobj)

    def GetMouseModeItems(self):
        return self.musmoditems
    def GetSelModeItems(self):
        return self.selmoditems
    def GetSelObjItems(self):
        return self.selobjitems        
    def GetMouseMode(self):
        return self.musmod

    def GetSelMode(self):

        return self.selmod
    
    def GetMdlMode(self):
        return self.mdlmod
    
    def GetSelObj(self):
        
        return self.selobj
    
    def SetRotationMode(self,rotmod):
        """ rotmod: 0: free,1:translate,2: 3:zoom, 4:x-rot, 5:y-rot, 6:z-rot
        7:inplane, 8:axis"""
        if rotmod < 0 or rotmod > 8: return
        self.musmod=rotmod
    
    def SetMouseMode(self,musmod,delarrow=True):
        # musmod(int): 0:rotation, 1:translation, 2:zoom, 3:rotation in xy-plane
        self.musmodsav=self.musmod
        if musmod == 9:
            self.model.SetRotationAxis() #True) # axis-rot
            musmod=self.musmodsav
        elif musmod == 7: # axis rotation
            if len(self.rotaxispnts) > 0: 
                self.model.DrawAxisArrow(True,[self.rotaxispnts],drw=False)
            if len(self.rotaxispnts) == 2:
                self.model.draw.SetCenterOfRot(self.rotaxispnts[1])
            else: self.model.draw.SetCenterOfRot(self.rotaxispnts[1])
            #           
            self.model.DrawMol(True)
        else: 
            if self.mdlwin.draw.IsDrawObj('rot-axis') and delarrow:
                self.model.DrawAxisArrow(False,[],drw=True)
                #self.model.DrawMol(True)      
        #else:
        #    if self.musmod == 7: self.model.SetRotationAxis(False) 
        self.musmod=musmod
                
    def SetMouseModeSelection(self,musmod):
        # musmod(int): 0:rotation, 1:translation, 2:zoom, 3:rotation in xy-plane
        try: self.mdlwin.mousemode.SetMouseModeSelection(musmod)
        except: pass

    def SetMdlMode(self,mdlmod):
        self.mdlmod=mdlmod
        if mdlmod == 5: 
            if len(self.rotaxispnts) > 0: self.musmod=7                
        else: self.musmod=0
        self.SetMouseModeSelection(self.musmod)
        self.mdlwin.mousemode.win.ChangeModeButton(self.mdlmod)
            
    def SetSelMode(self,selmod):
        # selmod(int): 0:single,1:dual,2:triple,3:quadruple,5:multiple
        ###if self.selmod == 5: self.model.RemoveSelectSphere()
        
        self.selmod=selmod; self.selmodsav=selmod
        self.SetSelModeSelection(selmod)

        #??if selmod != 1: self.model.SetDrawDistanceMode(False)
        #if selmod == 5: 
        #    #self.model.SetDrawSelSphereBox(True)
        #    mess='Press "shift" key (toggle) '
        #    mess=mess+'to switch to this mode and L-Drag.'
        #    wx.MessageBox(mess,"",style=wx.OK|wx.ICON_INFORMATION)
        #???else: self.model.SetDrawSelSphereBox(False)
        self.pntatmhis.Clear()
        #if self.selmod <= 3: self.pntatmhis.SetMaxDepth(self.selmod+1)
        """
        if selmod == 5: # shhere/box selection mode on/off (toggle)
            self.model.mousectrl.KeyDown(306)
        """
               
    def RecoverSelMode(self):
        self.selmod=self.selmodsav
        self.SetSelModeSelection(self.selmod)

    def RecoverMouseMode(self):
        self.musmod=self.musmodsav
        #self.SetMouseMode(self.musmod)
        self.SetMouseModeSelection(self.musmod)
       
    def RecoverMouseMode0(self,delarrow=True):
        self.musmod=0
        self.SetMouseMode(0,delarrow)
        self.SetMouseModeSelection(0)
       
    def SetSelModeSelection(self,selmod):
        # selmod(int): 0:single,1:dual,3:triple,4:quadruple,5:multiple
        try: self.mdlwin.mousemode.win.SetSelModeSelection(selmod)
        except: pass
        
    def SetSelObj(self,selobj):
        # selobj(int): 0:atom, 1:residue, 2:chain, 3:group, 4:fragment
        self.selobj=selobj; self.selobjsav=selobj
        ###??? 14Mar2015 ??? if selobj != 0: self.model.SetDrawDistanceMode(False)

    def RecoverSelObj(self):
        self.selobj=self.selobjsav
        self.SetSelObjSelection(self.selobj)
           
    def SetSelObjSelection(self,selobj):
        try: self.mdlwin.mousemode.win.SetSelObjSelection(selobj)
        except: pass
        # selobj(int): 0:atom, 1:residue, 2:chain, 3:group, 4:fragment
    def SetSensitive(self,sensitive):
        self.sensitive=sensitive
            
    def GetSensitive(self):
        return self.sensitive
        
    def SetBDAMode(self,value):
        self.bdamod=value

    def SetCtrlKeyDown(self,on):
        self.ctrlkeydown=on
        mess='ctrl-on'
        if not on: mess=''
        self.model.ModeMessage(mess)

    def SetMouseLeftDown(self,on):
        self.mouseleftdown=on
        
    def SetShiftKeyDown(self,on):
        self.shiftkeydown=on
                        
    def SetSectionMode(self,value):
        self.secmod=value
        self.model.SaveSection(value)
        
    def GetSectionMode(self):
        return self.secmod
    
    def GetDragSelected(self):
        return self.dragselected
    def SetDragSelected(self,value):
        self.dragselected=value
    def GetSelectSphere(self):
        return self.selectcircle
    def SetSelectSphere(self,value):
        self.selectcircle=value
    def GetSelectBox(self):
        return self.selectsquare
    def SetSelectBox(self,value):
        self.selectsquare=value    
        
    def SetRotationAxisPnts(self,on,pnts):
        if on: self.rotaxispnts=pnts
        else: self.rotaxispnts=[]
    
    def SetRotationAxisAtoms(self,atms):
        self.rotaxisatms=atms
        
    def GetRotationAxisAtoms(self):
        return self.rotaxisatms
        
    def GetRotationAxisPnts(self):
        return self.rotaxispnts
 
    def MouseMove(self,pos):
        # mouse move
        if self.model.mol is None: return
        if not self.model.Ready(): return
        #
        self.mousemove=True
        #musmodtxt=['free','translate','zoom','x','y','z','inplane','axis']
        #
        dif=pos-self.pos
        dif[0] *= self.sensitive; dif[1] *= self.sensitive
        self.pos=pos
        if self.mouseleftdown:
            ###if self.shiftkey and self.musmod != 8:
            ###    if self.mdlmod == 5: self.model.TranslateSelected(dif)
            ###    else: self.model.Translate(dif) # translation
            ###    return
            #if self.ctrlkeydown: # change coordinates of selectted atoms
            if self.mdlmod == 5:# change geometry 
                label='Conformation'
                if self.model.winctrl.IsOpened(label): #'ZmatWin'):
                    win=self.model.winctrl.GetWin(label)
                    win.ChangeGeometry(dif)
                #""" connect on put (does not work) """
                #elif self.model.winctrl.IsOpened('Model builder'):
                #    self.model.ConsoleMessage('mousemove.')
                #    grppairlst=self.model.FindContactGroupsIn2D()
                #    if len(grppairlst) > 0: self.model.ConnectMols(grppairlst)
                
                if self.shiftkey: self.model.TranslateSelected(dif)
                else:
                    if self.musmod == 1: self.model.TranslateSelected(dif)
                    elif self.musmod == 2: self.model.Zoom(-5*dif[0]) #zoom
                    else: self.model.RotateSelected(self.musmodtxt[self.musmod],
                                                    dif) # rotation                    
                    return
            #elif self.shiftkeydown: # bulk selection        
            ###elif self.mdlmod == 2: # bulk selection
            if self.selmod == 5:
                if self.selcirc and self.selcntatm >= 0:
                    #if self.selcntatm >= 0:
                    self.model.SelectBySphere(pos[0],pos[1],self.selcntatm) 
                if self.selrect and len(self.selinipos) > 0:                     
                    inix=self.selinipos[0]; iniy=self.selinipos[1]
                    self.model.SelectByBox(inix,iniy,pos[0],pos[1])            
            else:
                if self.musmod == 8: return # set axis mode. not for move            if self.shiftkey and self.musmod != 8:
                if self.shiftkey: self.model.Translate(dif)
                else:
                    if self.musmod == 1: self.model.Translate(dif)
                    elif self.musmod == 2: self.model.Zoom(-5*dif[0]) #zoom
                    else: self.model.Rotate(self.musmodtxt[self.musmod],dif) # rotation                    
        #self.pos=pos
    
    def GetRotateAxis(self):
        return self.musmodtxt[self.musmod]
    def MouseLeftDown(self,pos):
        #<2013.2 KK>        
        if not self.model.Ready(): return
        else:
            if self.model.IsDrawBusy(): return
        if self.model.mol is None: return
        #
        self.mouseleftdown=True
        self.pntatm=self.model.GetClickedAtom(pos)
        if self.model.IsSelectedAtom(self.pntatm): # unselect the selected object
            self.pntatmhis.Clear()
            self.pntatmhis.Push(self.pntatm) 
            self.model.SelectByClick(self.pntatmhis.Get(),False)
            return

        if self.mdlmod == 6: # build mode
            ###if self.model.ModelBuild("IsBuildingMol"):
            self.model.PutBuildingMol(pos)
            return
        
        #if self.shiftkeydown:
        if self.mdlmod == 2:
            self.model.RemoveSelectBox()
            self.model.RemoveSelectSphere()
        #self.selinipos=pos; self.selcntatm=-1
        if self.pntatm >= 0: 
            #xxxself.PointedAtomHis(self.pntatm)
            self.pntatmhis.Push(self.pntatm)
            pntatmhis=self.pntatmhis.Get()
            self.model.SelectByClick(pntatmhis,True)
            nhis=self.pntatmhis.GetNumberOfData()
            #if self.shiftkeydown:  # select atom
            if self.mdlmod == 2:
                self.selcirc=True; self.selrect=False; self.selinipos=[]
                self.selcntatm=self.pntatm
                #self.model.RemoveSelectBox()
                return
            if self.mdlmod == 3 and nhis == 2:
                self.model.menuctrl.OnHidden("Make single bond",False)
                return
            else:
                nhis=self.pntatmhis.GetNumberOfData()
                self.pntatmhis.Save()
                if self.bdamod and self.selmod == 1 and nhis == 2:
                        baatm=self.pntatmhis.Pop()
                        bdatm=self.pntatmhis.Pop()                        
                        self.model.frag.InputBDABAA(bdatm,baatm)
                        #return
                elif (self.selmod == 1 or self.selmod == 4) and \
                      self.selobj == 0 and nhis == 2: # and self.model.dispdist:
                    atm0=self.pntatmhis.Pop(); atm1=self.pntatmhis.Pop()
                    self.model.MsgAtomDistance(atm0,atm1)
                    ###???10Feb2016???self.pntatmhis.SetSaved()
                elif (self.selmod == 2 or self.selmod == 4) and \
                      self.selobj == 0 and nhis == 3: # and self.model.dispdist: 
                    #pntatmsav=self.pntatmhis.GetSaved()
                    atm2=self.pntatmhis.Pop(); atm1=self.pntatmhis.Pop()
                    atm0=self.pntatmhis.Pop()
                    self.model.MsgAtomAngle(atm0,atm1,atm2)
                    self.pntatmhis.SetSaved()
                elif (self.selmod == 3 or self.selmod == 4) and \
                      self.selobj == 0 and nhis == 4: # and self.model.dispdist: 
                    #pntatmsav=self.pntatmhis.GetSaved()
                    atm3=self.pntatmhis.Pop(); atm2=self.pntatmhis.Pop()
                    atm1=self.pntatmhis.Pop(); atm0=self.pntatmhis.Pop()
                    self.model.MsgAtomTorsion(atm0,atm1,atm2,atm3)
                    label='Conformation'
                    print 'self.model.winctrl.win[label]', \
                       self.model.winctrl.GetWin(label)
                    if self.model.winctrl.IsOpened(label):
                        win=self.model.winctrl.GetWin(label)
                        win.SetZMPoints(atm0,atm1,atm2,atm3)
                    self.pntatmhis.SetSaved()
                elif (self.selmod == 0 or self.selmod == 4) and \
                      self.selobj == 0 and nhis == 1:
                    #pntatmsav=self.pntatmhis.GetSaved()
                    atm=self.pntatm
                    self.model.MsgAtomLabel(atm,False)
                        #self.pntatmhis.SetSaved()
                #if self.selobj > 0: # residue
                #    self.model.MsgSelectedObj(self.selobj,self.pntatm)
                
                if self.selmod == 5:
                    #self.selcirc=True; self.selcntatm=self.pntatm

                    self.selcirc=True; self.selrect=False #??False
                    self.selcntatm=self.pntatm
                    self.selinipos=[] #pos[:] #[0]=pos[0]; self.selinipos[1]=pos[1]
                    
                    return 
        else:
            #if self.shiftkeydown:
            ###if self.mdlmod == 2:
            if self.selmod == 5:
                self.selcirc=False; self.selrect=True #??False
                self.selcntatm=-1
                #self.model.RemoveSelectSphere()
                #self.selinipos=pos[:]
                #x,y,dummy=self.mdlwin.draw.GetWorldCoordOfRasPos2(possav[0],possav[1])
                self.selinipos=pos[:] #[0]=pos[0]; self.selinipos[1]=pos[1]
                                
    def MouseLeftUp(self):
        if not self.model.Ready(): return
        if self.model.IsDrawBusy(): return
        #
        self.mouseleftdown=False # clear select flags
        #self.selcirc=False
        #self.selrec=False
        
    def MouseLeftDClick(self,pos):
        if self.model.mol is None: return
        selflg=False
        nsel,lst=self.model.ListSelectedAtom()
        if nsel <= 0: selflg=True

        self.model.SelectAll(selflg); self.pntatmhis.Clear()        
        self.model.Message('',0,'')
        return

        # pos(lst): mouse position [x(int),y(int)] in pixels
        nsel=self.model.MoleculeInfoSelectedAtoms()
        if nsel == 1:
            print 'nsel=1',nsel
        elif nsel == 2:
            print 'nsel=2',nsel
        else:
            print 'nsel=else',nsel

    def MouseRightDown(self,pos):
        #<2013.2 KK>
        if self.model.mol is None: return
        if not self.model.Ready(): return
        if self.model.IsDrawBusy(): return
        # save cc for recover
        #????if self.shiftkeydown: self.model.SaveAtomCC()       
        self.mouserightdown=True
        self.mousemove=False
        #
        
        # popupdat=[label,menulst,tiplst,retmethd]
        if self.model.ctrlflag.IsDefined('popupmenu'):
            self.model.ctrlflag.Get('popupmenu')()
            """
            popupdat=self.model.ctrlflag.Get('popupmenu')
            menulst=popupdat[1]; tiplst=popupdat[2]; retmethod=popupdat[3]
            #self.model.menuctrl.OnHidden('Change mouse operation mode',False)
            #if len(popupdat) > 0:
            self.model.ConsoleMessage('pos x='+str(pos[0])+', y='+str(pos[1]))
            lbmenu=subwin.ListBoxMenu_Frm(self.model.mdlwin.canvas,-1,[],[],
                                retmethod,menulst,tiplst)
            """
    def MouseRightUp(self,pos):
        # pos(lst): mouse position [x,y] in pixels
        if not self.model.Ready(): return
        if self.model.IsDrawBusy(): return
        #
        #??self.model.menuctrl.OnHidden('Change mouse operation mode',False)
        """
        pa=self.model.GetClickedAtom(pos)
        if pa >= 0:
            if self.selobj == 0: self.model.SelectAtomBySeqNmb([pa],0)
            if self.selobj == 1: self.model.SelectResByAtmSeqNmb(pa,0)
            if self.selobj == 2: self.model.SelectChainByAtmSeqNmb(pa,0)               
            if self.selobj == 4: self.model.SelectFragByAtmSeqNmb(pa,0)
        else:    
            if not self.mousemove:
                if self.model.CountSelectedAtoms() > 0:
                    #?self.model.SelectAll(0); self.pntatmhis=[] #mousectrl.SetPointedAtomHis([])
                    self.model.SelectAll(0); self.pntatmhis.Clear() #mousectrl.SetPointedAtomHis([])
        """
        #if self.mdlwin.HasCapture(): self.ReleaseMouse()
        self.mouserightdown=False
              
    def MouseWheel(self,rot):
        # rot(int): rotation angles of mouse wheel
        if self.model.mol is None: return
        if not self.model.Ready(): return
        if self.model.IsDrawBusy(): return
        #
        if self.secmod or self.mdlmod == 4: self.model.SetSectionZByMouse(rot)
        else:
            self.model.Zoom(rot)
            self.mdlwin.OnPaint(1)
            
    def GetWinPosition(self,xdel,ydel):
        # xdel(int),ydel(int): mouse movement in pixels
        if not self.model.Ready(): return
        selfpos=self.GetScreenPosition()       
        x=selfpos[0]+self.size[0]-70; y=selfpos[1]+100
        x=x+xdel; y=y+ydel; pos=[x,y]; winpos=tuple(pos)
        return winpos

    def GetModelModeWinItems(self):
        return self.modenamlst,self.tooltips
        
    def KeyDown(self,keycode):
        """ handler of key press (not completed yet).
            keycode(int): keyboard code """
        if self.model.mol is None: return
        if not self.model.Ready(): return
        else:
            if self.model.IsDrawBusy(): return
        #keycode = event.GetKeyCode()
        selmod=self.selmod #mousemode.GetSelMode()
        #
        keychar=lib.KeyCodeToASCII(keycode)        
        if keychar == '': keychar=lib.UniCodeToChar(keycode)   
        shortcutkeydic=self.setctrl.GetParam('shortcut-key')
        keydic=self.model.menuctrl.MenuHandlerDic()
        #      
        if keycode == 27: #'esc'
            #self.model.menuctrl.OnHidden('Reset mouse operation mode',False)
            self.model.menuctrl.OnHidden('Close popup menu',False)
        #elif keychar == 'ctrl': # open mouse operation mode change panel
        elif keycode == 32: # space 
            self.model.DrawLabelRemoveAll(True,True)
        
        elif keycode == 308: # open mouse operation mode change panel
            #self.model.menuctrl.OnHidden('Change mouse operation mode',False)
            self.ctrlkey=True
            self.model.menuctrl.OnHidden('Switch view/build mode',False)
            """
            mdlmod=self.mdlmod
            if mdlmod == 5: 
                self.mdlmod=0; self.SetMdlMode(self.mdlmod)
                #self.model.ctrlflag.Del('draw-torsion-angle')
                ###self.model.TextMessage('')
            elif mdlmod == 0: 
                self.mdlmod=5; self.SetMdlMode(self.mdlmod)
            
            if self.model.winctrl.IsOpened('Model builder'):
                bldwin=self.model.winctrl.GetWin('Model builder')
                if self.mdlmod == 5: bldwin.SetCenterOfRotation(True)
                #bldwin.SetMdlModeButton(self.mdlmod)
            """
        #elif keychar == 'shift': # 'Show'-'xyz-axis'
        elif keycode == 306: #'shift': # 'Show'-'xyz-axis'
            #if self.model.menuctrl.IsChecked(label): on=False
            #else: on=True
            #self.model.menuctrl.CheckMenu(label,on)
            #self.model.menuctrl.OnShow('xyz-axis',on)
            self.shiftkey=True
            
        elif keycode == 127: # del
            self.model.menuctrl.OnModeling("Selected atoms",False)
            
        elif keycode == 307: # alt key
            self.altkey=True
        else:
            if shortcutkeydic.has_key(keychar):
                topmenu=shortcutkeydic[keychar][0]
                label=shortcutkeydic[keychar][1]
                check=False
                if len(shortcutkeydic[keychar]) >= 3: 
                    ckeck=shortcutkeydic[keychar][2]
                if keydic.has_key(topmenu): keydic[topmenu](label,check)
        return            
        """ -------------------- """        
                
        if keycode == self.KeyName['quitdraw']:
            self.model.Message('Quit darw. press q-key to resume.',0,'')
            #??self.ctrlflag.quitdraw=True
        elif keycode == self.KeyName['rotate']: # 'r' self.KeyName['rotate']:
            #ms=self.musmod #mousemode.GetMouseMode()
            #if ms == 0: self.musmod=1
            #if ms == 1: self.musmod=0
            #if ms == 2: self.musmod=0
            print 'rotate'
            self.SetMouseMode(0)
            self.SetMouseModeSelection(0)
            #if ms == 2: self.ctrlflag.musmod=0
            #self.SetCBoxItem('musmod',self.ctrlflag.musmod)
            #self.SetWrkFlg('musmod',0)
        elif keycode == self.KeyName['trans']:
            ms=self.musmod #mousemode.GetMouseMode()
            if ms == 1: self.musmod=0
            if ms != 1: self.musmod=1
            if ms == 2: self.musmod=0
        elif keychar == 'f': #self.KeyName['fitscreen']:
            self.model.menuctrl.OnShow("Fit to screen",False)
        elif keychar == 'c': #code == self.KeyName['center']:
            #self.model.ChangeCenterOfRotation(True)
            self.model.menuctrl.OnHidden('Change center of rotation',False)
        elif self.mdlmod == 3 and (keycode >= 48 and keycode <= 52): # 0-4: del bond, 1: add single, 2:double, 3:triple, 4:aromatic bonds
            #pntatmhis=self.pntatmhis #mousectrl.GetPointedAtomHis()
            nbnd=keycode-48
            menulabel=['Delete bond','Make single bond','Make double bond',
                       'Make triple bond','Make aromatic bond']
            self.model.menuctrl.OnHidden(menulabel[nbnd])
            #self.model.ChangeBondMultiplicity(keycode-48)
            return
            """
            pntatmhis=self.pntatmhis.Get() #mousectrl.GetPointedAtomHis()
            if len(pntatmhis) <= 2:
                bondkind=['single','double','triple','aromatic']
                nsel,lst=self.model.ListSelectedAtom()
                if nsel == 2:
                    atm1=lst[0]; atm2=lst[1]
                    
                    atmpair=[]; atmpair.append(atm1); atmpair.append(atm2)
                    bndknd=bondkind[keycode-49]
                    self.model.ChangeBondKind(atmpair,bndknd)
            else:
                mess='select two atoms to make the bond.'
                self.model.Message(mess,0,'')            
            return    
            """
    def KeyUp(self,keycode):
        if self.model.mol is None: return
        if keycode == 308: self.ctrlkey=False
        elif keycode == 306: 
            self.shiftkey=False
            if self.mdlmod == 5:
                winlabel='ModelBuilderWin'
                if self.model.winctrl.IsOpened(winlabel):
                    win=self.model.winctrl.GetWin(winlabel)
                    win.SetCenterOfRotation(True)
        elif keycode == 307: 
            self.altkey=False

    @staticmethod
    def XXKeyAssign():
        """ Set Command keys """
        NameOfKeyCode={
                # status related command
                'ctrl':308 , # 'ctrl', used with a key for select
                'shift':306 , # 'shift', used with a key for build
                'rotate':82, # 'r', rotation
                'trans':84, # 't', translation
                'fitscreen':70, # 'f', fit to screen
                'center':67, # 'c', set center of rotation at a selected atom
                'bondkind':[48,49,50,51,52], # '0','1','2','3','4'
    
                
                'single':83, # 's', single atom selection
                'dual':84, # 't', two atoms selection
                'atom':65, # 'a', select by atom     
                       
                'quitdraw':81, # quit draw flag on/off (toggle)
                'zero':48, # "0"
                'KBMview':49, # '1,keyboard mode: move
                'KBMselect':50, # '2',keyboard mode: select
                'KBMmodify':51, # '3',keyboard mode: build
                'esc':27, # turn off teunmod
                'rarrow':316, # right arrow
                'larrow':314, # left arrow
                'space':32, # space
                'alt':307, # alt-key in Wondows and command-key in Mac
                # in view mode
                'zoom':90, # 'z', zoom
                'rotzaxis':69, # 'e', rotate around Z axis
                'origin':79, # 'o', back rotational center to origin
                'shwcom':77, # 'm' show center of mass(toggle switch)
                #'shwpmi':-1, # '?' show pmi vector
                'shwatmlbl':83, # 's',show atom label (toggle)            
                #'shwdist':68, # 'd' show distance
                'shwchain':81, # 'q' show chain (toggle)
                # in select mode (selmod)
                'single':83, # 's', single atom selection
                'dual':84, # 't', two atoms selection
                'multi':78, # 'n', multiple atom selection
                # selection object (selobj) 
    
                'residue':82, # 'r', select by residue
                'group':71, # 'g', select by group/molecule
                #'chain':67, # 'c' select by peptide chain
                'selewin':87, # 'w', pop up select panel
                # in modify mode
                'addbond':65, # 'a', make bond between two selected atoms
                'addhatom':72, # 'h' add H atom at single selected atom
                'delatom':75, # 'k', delete selected atom (one atm being selected)
                'delbond':68, # 'd', delete bond between two seletcted atoms
                'elmchange':69,# 'e', change element for a selected atom 
                #'dispatom':65, # 'a', display atom name and number
                #'dispresidue':82, # 'r', display residurename and number
                #'buildwin':87, # 'w' pop up window dor buld related commands
                # special key for ???
                'delete':127 # 'del', usage is not decided yet.
                # miscellaneous
                 } 
        return NameOfKeyCode 

    @staticmethod
    def XXKeyCodeToASCII(keycode):
        """ Convert keycode to character
        
        :param int keycode:
        :return: key character
        :rtype: str
        """
        keytable={27:'esc', 32:'space', 127:'del', 
                  44:'<',46:'>',91:'[',93:']',64:'@',
                  48:'0', 49:'1', 50:'2', 51:'3', 52:'4', 53:'5',
                  54:'6', 55:'7', 56:'8', 57:'9',
                  65:'a', 66:'b', 67:'c', 68:'d', 69:'e', 70:'f', 71:'g', 
                  72:'h', 73:'i', 74:'j', 75:'k', 76:'l', 77:'m', 78:'n', 
                  79:'o', 80:'p', 81:'q', 82:'r', 83:'s', 84:'t', 85:'u', 
                  86:'v', 87:'w', 88:'x', 89:'y', 90:'z' }
        if keytable.has_key(keycode): return keytable[keycode]
        else: return ''

    @staticmethod
    def XXUniCodeToChar(keycode):
        # 27:esc, 32:space, 8:del,1?:ctrl, 16:shift,?:alt,314:left arrow,316:right arrow,
        # 315:up arrow, 317:down arrow, 32:space
        # 340-349: f1-f10
        codetable={48: '0', 49: '1', 50: '2', 51: '3', 52: '4', 53: '5',
                   54: '6', 55: '7', 56: '8', 57: '9', 97: 'a', 98: 'b', 
                   99: 'c', 100: 'd', 101: 'e', 102: 'f', 103: 'g', 104: 'h', 
                   105: 'i', 106: 'j', 107: 'k', 108: 'l', 109: 'm', 110: 'n', 
                   111: 'o', 112: 'p', 113: 'q', 114: 'r', 115: 's', 116: 't', 
                   117: 'u', 118: 'v', 119: 'w', 120: 'x', 121: 'y', 122: 'z',
                   340:'f1',341:'f2',342:'f3',343:'f4',344:'f5',
                   345:'f6',346:'f7',347:'f7',348:'f9',349:'f10',
                   316:'up',317:'down',314:'left',316:'right', # arrow keys
                   13:'entr',8:'del',9:'tab',27:'esc',32:'space',
                   35:'#',36:'$',37:'%',38:'&',42:'*',43:'+',45:'-',61:'=',
                   63:'?',64:'@',91:'[',93:']',123:'{',125:'}',60:'<',62:'>',
                   51:'shift',315:'up arrow',317:'down arrow',314:'left arrow',
                   316:'right arrow'}
        
        if codetable.has_key(keycode): return codetable[keycode]
        else: return ''
        
class SettingCtrl():
    def __init__(self,parent,fuversion):
        # initial setting (winow appearance and fudatafiles)
        self.model=parent
        self.classnam='SettingCtrl'
        self.title=fuversion
        # fuversion
        self.message=fuversion+'...'+lib.DateTimeText()+'\n'
        # print system information
        self.platform=lib.GetPlatform()
        self.SettingMessage('Platform: '+self.platform)
        self.SettingMessage('Python sys.version: '+sys.version)
        self.SettingMessage('wxPython version: '+wx.VERSION_STRING+'\n')
        # inidat:[inidir,iniprj,winpos,winsize,shlpos,shlsize,fudataset,hislst]
        self.initdic=self.model.initdic
        self.message=self.message+'>>> Initiall Setting:\n'
        # get 'FUSOURTHROOT'
        self.fusrcdir=self.initdic['srcpath'] #'FUSOURCEPATH'
        #self.fusrcdir=os.getenv(fusrcdir)
        self.fusrcdir=lib.ReplaceBackslash(self.fusrcdir)
        mess='Source path='+str(self.fusrcdir)
        self.SettingMessage(mess)
        scriptdir='Scripts'
        self.scriptdir=lib.PathJoin(self.fusrcdir,scriptdir)
        toolsdir='Tools'
        self.toolsdir=lib.PathJoin(self.fusrcdir,toolsdir)
        # fufiles setting: search FUFILESDIR environment variable and set fufiles
        self.fudir=self.initdic['FUDATASET']
        #self.home=os.getenv('HOME') or os.getenv("HOMEDRIVE")
        self.home=lib.GetHomeDirectory()
        self.fudirs=['Scratch','FUdata','Projects','Customize','Programs',
                     'PDBs','FUdocs','Molecules','Frames','Filters',#'Icons',
                     'Logs','Tests'] #,'Docs','Images','Draws']    
        self.prjdirs={'Docs':True,'Images':True,'Draws':True} # not completed 25Nov2014
        #
        self.prjdir=self.fudir
        #       
        self.fufiles={} # fufiles:fupath/fudirs[i]/filename
        #self.prjfiles={}
        loggingmethodfile='Customize//logging.method'
        self.loggingmethodfile=lib.PathJoin(self.fudir,loggingmethodfile)
        self.srcpath=''
        self.inidir=''
        self.iniprj=''
        self.iniset=''
        self.curprj=''
        self.curdir=''
        self.params={}
        #???self.paramtypedic={} # not used
        self.ctrlwinmenu=[]
        self.winpos=[-1,-1]
        self.winsize=[640,400]
        # default parameters
        self.params=self.SetDefaultParams() #self.DefaultParams()
        self.myparams={} # for user
        self.SettingMessage('FUDATASET='+self.fudir)
        #self.SettingMessage('fufiles: '+self.fudir)
        # 
        self.SetFUDirsAndFiles() # set fufiles: search directory/files in fudir
        self.SetProjectFiles()   # set project files in fufiles
        self.prjdatdic={} #self.MakeProjectDataDic() # project data dictionary
        # set objects to const module
        lib.SetSetCtrlObj(self)
        lib.SetConsoleMessObj(self.model.ConsoleMessage)
        lib.SetMessageLevel(self.GetParam('message-level'))
        #
        self.InitialSetting()
        #
        self.model.curprj=self.curprj
        self.model.curdir=self.curdir
        #
        # attribute variables to be accessed from the 'Atom' class ('atm' instance) 
        # Do not use the 'GetParam' method, becouse it is very slow for many operations for 'Atom'
        self.molmodel=self.GetParam('mol-model')
        self.bondthick=self.GetParam('bond-thick')
        self.bondthickbs=self.GetParam('bond-thick-bs')
        self.atomradius=self.GetParam('atom-sphere-radius')
        self.vdwraddic=self.GetParam('vdw-radius')
        self.elmcolordic=self.GetParam('element-color')

    def InitialSetting(self):
        """ Set initial paramters in 'fumodel.ini' file"""
        self.srcpath=self.initdic['srcpath']
        self.inifile=self.initdic['inifile']
        self.inifile=lib.ReplaceBackslash(self.inifile)
        self.inidir=self.initdic['inidir']
        self.iniprj=self.initdic['iniprj']
        self.winpos=self.initdic['winpos']
        self.winsize=self.initdic['winsize']
        shlpos=self.initdic['shlpos']
        shlsize=self.initdic['shlsize']
        hislst=self.initdic['hislst']
        #
        self.model.SetFileHistory(hislst)
        if len(shlpos) > 0: self.SetParam('shell-win-pos',shlpos)
        if len(shlsize) > 0: self.SetParam('shell-win-size',shlsize)        
        #
        if self.iniprj == '': self.iniprj='None'
        # set initial projec
        self.inidir=lib.ExpandUserFileName(self.inidir)

        self.SettingMessage('fumodel.ini file='+self.inifile)
        # set current project
        self.setfile=''
        self.curprj=self.iniprj
        #
        self.prjdatdic=self.MakeProjectDataDic() # project data dictionary

        if self.curprj != 'None':
            #self.inifilename=self.curprj+'.project'
            #self.prjroot,self.setfile,self.curdir=self.GetProjectSetFile(self.curprj)
            #self.prjdatdic=self.MakeProjectDataDic()  
            self.prjdir=self.prjdatdic[self.curprj][1]
            if self.prjdir == '': self.prjroot=self.fupath
            #self.prjdir=os.path.join(self.prjroot,self.curprj)
            self.setfile=self.prjdatdic[self.curprj][4]
            print 'prjdir,curprj,setfile',self.prjdir,self.curprj,self.setfile
            
            self.SettingMessage('prjdir: '+self.prjdir)
            # check project directory
            self.prjdir=lib.ExpandUserFileName(self.prjdir)
            if not os.path.isdir(self.prjdir):
                mess='Project directory "'+self.prjdir+'" is not found. Would '
                mess=mess+'you like to continue? if yes,'
                mess=mess+'the directory will be created.'
                dlg=lib.MessageBoxYesNo(mess,"")
                if not dlg: return
                else:
                    retmess=custom.Setting_Frm.CreateProjectDirectory(
                                                        self.curprj,self.prjdir)
                    if len(retmess) > 0:
                        mess='Failed to create "'+self.prjdir+'"'
                        lib.MessageBoxOK(mess,"")
                        return
                    self.SettingMessage('project directory "'+self.prjdir+
                                        '" was created.')
            self.InitialProjectSetting(self.curprj) 
        else:
            prjpath=self.fudir #self.fupath
            self.setfilename='fumodelset.py' # for 'None' project
            self.setfile=os.path.join(self.fudir,self.setfilename)
            self.setfile=lib.ReplaceBackslash(self.setfile)
        # make frame data dictonary
        self.framedatdic=self.MakeFrameDataDic() # make farme data from files in 'Frams' directory
        #
        self.SettingMessage('curprj='+self.curprj)
        self.SettingMessage('setting script file='+self.setfile)
        #self.message=self.message+'Initiall Setting:\n'
        # change current directory
        if self.inidir == '': self.inidir=os.getcwd()
        try: os.chdir(self.inidir)
        except: pass
        self.curdir=self.inidir #os.getcwd()
        self.SettingMessage('curdir='+self.curdir)
        #
        self.DefineIconFiles()

    def DefineIconFiles(self):
        """ Set icon file name in 'const' module """
        def IconFile(name):
            icondir=os.path.join(self.srcpath,'Icons')
            file=os.path.join(icondir,name)
            file=lib.ReplaceBackslash(file)
            return file
        #
        const.FUMODELICON=IconFile('fumodel.ico')
        const.FUPLOTICON=IconFile('fuplot.ico')
        const.FUTOOLSICON=IconFile('futools.ico')
        const.FMOVIEWERICON=IconFile('fmoviewer.ico')
        const.FUMODELLOGO=IconFile('fumodel60.png')
        const.FUPLOTLOGO=IconFile('fuplot60.png')
        const.FUTOOLSLOGO=IconFile('futools60.png')

    def FragmentAttributeList(self):
        """
        
        :SeeAlso: GetFragmentAttributeValueDic(),GetFragmentAttributeTipDic() 
        """
        
        attriblst=['charge','layer','active','spin'] #,'spin','SCFTYP','MPLEVL',
                   #'DFTTYP','CITYP','CCTYP','TDTYP','SCFFRG','IEXCIT']
        return attriblst           
    
    def FragmentAttributeDefaultDic(self):
        defaultdic={'charge':'1','layer':'1','actve':'0','spin':'1'}
                    #'MULT':'1','IACTAT':'1','LAYER':'1',
                    #'SCFTYP':'RHF','MPLEVL':'0','DFTTYP':'NONE','CITYP':'NONE',
                    #'CCTYP':'NONE','TDTYP':'NONE','SCFFRG':'RHF','IEXCIT':'0'}
        return defaultdic    
    
    def FragmentAttributeValueDic(self):
        """
        
        :SeeAlso: GetFragmentAttributeList()
        """
        # fragment attribute values
        attribvaluedic={
                  'charge':['0','-1','-2','1','2'],
                  'layer':['2','3','1'],
                  'active':['0','1'],
                  'spin':['1','2','3','4','5','6'] }
                  #'FRGNAM':[], # to be filled at init
                  #'IFREEZ':['FREEZE','ACTIVE'],
                  #'ICHARG':['0','-1','-2','1','2'],
                  #'MULT':['1','2','3','-1','-2','-3'], #selcted
                  #'IACTAT':['False','True'],
                  #'LAYER':['2','3','1'], #selcted
                  #'SCFTYP':['RHF','UHF','ROHF','GVB','MCSCF','NONE'],
                  #'MPLEVL':['0','2'],
                  #'DFTTYP':['NONE','B3LYP','BLYP','BOP'], # selected items
                  #'CITYP':['NONE','CIS','SFCIS','ALDET','ORMAS','FSOCI','GENCI',
                  #         'GUGA'],
                  #'CCTYP':['NONE','CCSD(T)','R-CC','CR-CC','EOM-CCSD','CR-EOM'], #selected     
                  #'TDTYP':['NONE','EXCITE','SPNFLP'],
                  #'SCFFRG':['RHF','MCSCF'],
                  #'IEXCIT':['0','1','2']
                  #}
        
        return attribvaluedic
        
    def FragmentAttributeTipDic(self):
        """
        
        :SeeAlso: GetFragmentAttributeList()
        """
        # Fragmet attribute tips
        attribtipdic={
                  #'FRGNAM':'Fragment name', # to be filled at init
                  #'IFREEZ':'IFREEZ in $STATPT for RUNTYP=OPTIMIZE',
                  'ICHARG':['0','-1','-2','1','2'],
                  'MULT':['1','2','3','-1','-2','-3'], #selcted
                  'DOMAIN':'Domain for FMO/FD,FDD',
                  'LAYER':'Layer for multi-layer FMO (MFMO). max=5',
                  'SCFTYP':['RHF','UHF','ROHF','GVB','MCSCF','NONE'],
                  'MPLEVL':['0','2'],
                  'DFTTYP':['NONE','B3LYP','BLYP','BOP'], # selected items
                  'CITYP':['NONE','CIS','SFCIS','ALDET','ORMAS','FSOCI','GENCI',
                           'GUGA'],
                  'CCTYP':['NONE','CCSD(T)','R-CC','CR-CC','EOM-CCSD','CR-EOM'],
                  'TDTYP':['NONE','EXCITE','SPNFLP'],
                  'SCFFRG':['RHF','MCSCF'],
                  'IEXCIT':['0','1','2']
                      }
        return attribtipdic
                             
    def MakeFrameDataDic(self):
        #frmfiles=self.GetFilesList('Frames')
        framedir=self.GetDir('Frames')
        if len(framedir) <= 0:
            self.SettingMessage('MakeFrameDataDic: no "Frames" directory')
            return {}
        frmfiles=lib.GetFilesInDirectory(framedir,['.frm'])
        if len(frmfiles) <= 0: return {}
        framedatdic={}  
        for fil in frmfiles:
            resnam,condat=rwfile.ReadFrameFile(fil)
            if resnam == "": continue
            if framedatdic.has_key(resnam):
                mess='MakeFrameDataDic: duplicate frame data. name="'+resnam+'"'
                self.SettingMessage(mess)
            framedatdic[resnam]=condat
        self.framedatdic=framedatdic
        return framedatdic
        
    def SetFrameData(self,name,frmdat,replace=True):
        if not replace and self.framedatdic.has_key(name):
            mess='frame data "'+name+'" already exists. Would you like to '
            mess=mess+'replace?'
            #dlg=wx.MessageBox(mess,"",style=wx.YES_NO|wx.ICON_QUESTION)
            dlg=lib.MessageBoxYesNo(mess,'')
            if not dlg: return            
        self.framedatdic[name]=frmdat
        
    def GetFrameData(self,name):
        if self.framedatdic.has_key(name): return self.framedatdic[name]
        else: 
            mess='frame data "'+name+'" is not found.'
            lib.MessageBoxOK(mess,"")            
            return []
                   
    def GetFrameDataDic(self):
        return self.framedatdic

    def SetFrameDataDic(self,framedatdic):
        self.framedatdic=framedatdic
                                 
    def ChangeProject(self,prjnam):
        """ Change project
        
        :param str prjnam: project name
        :return: True for changed, False for unchanged project
        :rtype: bool
        """
        #self.prjdatdic=self.MakeProjectDataDic(prjnam)
        if not self.prjdatdic.has_key(prjnam): 
            return False,'project is not defined'
        # default parameters
        self.params=self.SetDefaultParams()
        #
        # prjdatadic:{prjnam:[prjnam,prjpath,curdir,prjfile,setfile,createdby,createddate,comment]
        if prjnam != 'None':
            prjfile=self.prjdatdic[prjnam][3]
            #prjdir=self.GetDir('Projects')
            #ns=prjnam.rfind('.project')
            #if ns <=0: filename=filename+'.project'
            #filename=os.path.join(prjdir,filename)
            if not os.path.exists(prjfile):
                mess='"'+prjnam+'" project is not defined.'+prjfile
                lib.MessageBoxOK(mess,"")
                self.curprj='None'  
                return False,mess
            #if not initial:
            self.curprj=prjnam
            self.inidir=self.prjdatdic[self.curprj][2]
            try: os.chdir(self.inidir)
            except: pass
            self.curdir=os.getcwd()
            self.prjdir=self.prjdatdic[self.curprj][1] 
            self.setfile=self.prjdatdic[self.curprj][4] #self.GetProjectSetFile(self.curprj)
            
            self.SettingMessage('setfile in ChangeProject: '+self.setfile)
            self.SettingMessage('prjdir in ChangeProject: '+self.prjdir)
            
            prjfile=self.prjdatdic[self.curprj][3]
            print 'prjdatdic in ChangeProject',self.prjdatdic
            print 'prjfile,prjdir,setfile,curdir in ChangeProject', \
                   prjfile,self.prjdir,self.setfile,self.curdir
            #
            shellmess=self.ExecuteSettingScript(self.setfile)
            #
            self.InitialProjectSetting(self.curprj)
            ###self.LoadProjectMolecules(self.curprj)
        else:
            self.iniprj='None'
            self.InitialSetting()
            shellmess=[]
                  
        return True,shellmess

    def GetProjectFile(self,curprj): 
        prjfile=''
        for file in self.fufiles['Projects']:
            head,tail=os.path.split(file)
            base,ext=os.path.splitext(tail)
            if base == curprj: prjfile=file
        return prjfile

    def GetProjectFileList(self): 
        prjfilelst=[]
        prjdir=self.GetDir('Projects')
        if prjdir =='': return []
        prjfiles=lib.GetFilesInDirectory(prjdir,['.project'])
        if prjfiles == '': return []
        for filnam in prjfiles: prjfilelst.append(filnam)
        prjfilelst.sort()
        return prjfilelst
              
    def ExecuteSettingScript(self,setfile):
        if len(setfile) <= 0:
            self.SettingMessage('Setting script file=None')
            return
        ns=setfile.find('.py')
        if ns <= 0:
            setfile=setfile+'.py'
            setfile=os.path.join(self.GetDir('Customize'),setfile)
        #self.SettingMessage('Setting script file='+setfile)
        scrdir=self.GetDir('Scratch')
        scrfile=os.path.join(scrdir,'setting.out')  # not used
        setfile=lib.ExpandUserFileName(setfile)
        if not os.path.exists(setfile): 
            return 'Not found setfile "'+setfile+'"'
        size=[640,200]; title='Running setting script'
        pycrust=wx.py.shell.ShellFrame(parent=None,id=100,size=size,title=title)
        retmess=lib.ExecuteScript1(pycrust.shell,setfile)
        mess='# Execute setting script file:\n'
        if retmess.find('Traceback') >= 0: 
            errmess=retmess.find('execfile')
            mess=mess+retmess[errmess:]
            text='Error occured in setting script file='+setfile+'.\n'
            text=text+'View the error message in PyShell console window.'
            lib.MessageBoxOK(text,'SettingCtrl(ExecuteSettingScript)')        
        else: 
            f=open(setfile,'r')
            for s in f.readlines(): mess=mess+s
            f.close()
        # set attribute variables for speedup access from 'Moelecule' instance
        self.molmodel=self.GetParam('mol-model')
        self.bondthic=self.GetParam('bond-thick')
        self.atomradius=self.GetParam('atom-sphere-radius')
        self.vdwraddic=self.GetParam('vdw-radius')
        self.elmcolordic=self.GetParam('element-color')        
        
        return mess

    def UpdateDicParams(self):
        dicparams=['element-color','vdw-radius','aa-residue-color',
                   'aa-chain-color','shortcut-key']
        for prmnam in dicparams:
            default=self.GetDefaultDicParam(prmnam)
            custom=self.params[prmnam]
            default.update(custom)
            self.params[prmnam]=default

    def GetDefaultDicParam(self,prmnam):
        #dicparams=['element-color','vdw-radius','aa-residue-color','aa-chain-color','shortcut-key']
        defaultdic={}
        if prmnam == 'vdw-radius': defaultdic=SettingCtrl.DefaultVdwRadius()
        elif prmnam == 'element-color': 
            defaultdic=SettingCtrl.DefaultElementColor()
        elif prmnam == 'aa-residue-color': 
            defaultdic=SettingCtrl.DefaultAAResidueColor()
        elif prmnam == 'aa-chain-color': 
            defaultdic=SettingCtrl.DefaultAAChainColor()
        elif prmnam == 'custom-shortcut-key': 
            defaultdic=SettingCtrl.CustomShortcutKey(),
        elif prmnam == 'reserved-shortcut-key': 
            defaultdic=SettingCtrl.ReservedShortcutKey(),
        elif prmnam == 'shortcut-key': 
            defaultdic=SettingCtrl.CustomShortcutKey()
            defaultdic.update(SettingCtrl.ReservedShortcutKey())
        return defaultdic
  
    def GetDefaultParam(self,prmnam):
        default=self.SetDefaultParams() #DefaultParams()
        if not default.has_key(prmnam): return None
        else: return default[prmnam]

    def SetParam(self,name,value):
        
        #if self.params.has_key(name):
        self.params[name]=value
        # update attribute
        if name == 'mol-model': self.molmodel=value
        if name == 'bond-thick': self.bondthic=value
        if name == 'atom-sphere-radius': self.atomradius=value
        if name == 'vdw-radius': self.vdwraddic=value
        if name == 'element-color': self.elmcolordic=value
        #else:
        #    mess='"'+name+'" parameter is not defined in "setctrl.params" dictionary.\n'
        #    mess=mess+'Use the "SetMyParam" method for user definition parameter.'
        #    self.model.ConsoleMessage(mess)
    def SetParamsInFile(self,filename):
        """ needs debug 04Jan2016 """
        if not os.path.exists(filename):
            mess='Not found file='+filename
            return
        nprm=0
        f=open(filename,'r')
        for s in f.readlines():
            s=s.strip()
            nc=s.find('#')
            if nc >= 0: s=s[:nc]
            if s[:1] == '#': continue
            key,value=lib.GetKeyAndValue(s,recoverlist=True)
            self.params[key]=value
            nprm += 1
        f.close()    
        mess=str(nprm)+' parametere in '+filename+' are set'
        self.model.ConsoleMessage(mess)
        
    def SetShortcutKey(self,keycharacter,topmenu,menuitem,checkable,comment):
        """ Set shortcut key
        
        :param str keycharacter: key character
        :param str topmenu: top menu label
        :param str menuitem: submenu item
        :param bool checkable: True for checkable, 
                               False for uncheckable menuitem
        :param str commnet: comment string
        """
        #'i':['Hidden','Save image',False,'in "standard mode']
        self.params['shortcut-key'][keycharacter]=[topmenu,menuitem,checkable,
                                                   comment]
        return self.params['shortcut-key'][keycharacter]

    def DelShortcutKey(self,keycharacter):
        """ Set shortcut key
        
        :param str keycharacter: keycar
        """
        if self.params['shortcut-key'].has_key(keycharacter):
            del self.params['shortcut-key'][keycharacter]     
            return 'RemoveShortcutKey: deleted "'+keycharacter+'" key bind.'
        else:
            return 'RemoveShortcutKey: key "'+keycharacter+'" not found.'
    
    def ModelModes(self):
        modelst=['select-bulk']
             
    def SetDefaultParams(self):
        params={}
        table=self.TableOfParameters()
        for prmnam,lst in table.iteritems(): params[prmnam]=lst[0]
        return params
    
    def ListParams(self,filename=''):
        text='# Parameters in ctrl.SettingCtrl:\n'
        prms=self.params.keys()
        prms.sort()
        for prm in prms: text=text+prm+'='+str(self.params[prm])+'\n'
        #print prms
        if filename == '':
            print text
        else:
            f=open(filename,'w')
            f.write(text)
            f.close
            mess='ctrl.SetCtrl: params are saved on file='+filename
            self.model.ConsoleMessage(mess)
        
    def ListSettingParams(self):
        text=''
        prms=self.params.keys()
        prms.sort()
        for prm in prms: text=text+prm+'='+str(self.params[prm])+'\n'
        return text
    
    def MakeParamTypeDic(self):
        paramtypedic={}
        table=self.TableOfParameters()
        for prmnam,lst in table.iteritems(): paramtypedic[prmnam]=lst[1]
        return paramtypedic

    def MakeParamTipsDic(self):
        paramtipsdic={}
        table=self.TableOfParameters()
        for prmnam,lst in table.iteritems(): paramtipsdic[prmnam]=lst[2]
        return paramtipsdic
        
    def GetParamTypeDic(self):
        return self.paramtypedic
                 
    def TableOfParameters(self):
        """
        Definition of parameters
        
        :return: dictionary of paramentes, {'parameter name':value,....}
        :rtype: dic
        """
        params={
        # general
        'platform':[self.platform,'str','plattform'],
        #'win-pos':[-1,-1], # window position
        'win-size':[[640,400],'size','main window (mdlwin) size'],
        'win-size-w':[640,'int','only for internal use'],
        'win-size-h':[400,'int','only for internal use'],
        'shell-win-pos':[[],'size','pyshell window position'],
        'shell-win-size':[[640,200],'size','pyshell window size'],
        'win-color':[[0.0,0.0,0.0,1.0],'color',
                     'background color of main window (mdlwin)'],
        'win-color-geom-mode':[[0.0,0.0,0.0,1.0],'color', 
                               'background color of mdlwin in change geometry mode'],
        'helpwin-bgcolor':[[253,255,206],'color',
                           'background color of help window'],
        'helpwin-fgcolor':[[0.0,0.0,0.0],'color',
                           'foregrounf color of help window'],
        'open-mouse-mode-win':[True,'bool',
                               'open mouse mode window at starting'],
        'mousemode-win-shape':[0,'int',
                    'shape of mouse mode window. 0:horizontal, 1:vertical'],
        'molchoice-win-shape':[0,'int',
                     'shape of mol choice window. 0:horizontal, 1:vertical'],
        'open-mol-choice-win':[True,'bool',
                               'open mol choice window at starting'],
        'pyshellwin-move-free':[False,'bool',
                                'pyshell win move together with mdlwin'],
        'projects':[{},'dic','used to store project data. internal use only.'],
        #'initial-project':'',
        #'initial-curdir':'',
        #'initila-setfile':'',
        #'curdir':'',
        #'curprj':'', 
        #'cursetfile':'', # current setting file
        'font':[0,'font',
                'use the "lib.GetFont(family,size)" to obtain font object'],
        'text-font-size':[8,'int','font size'],
        'text-font':[0,'font', 
                'use the "lib.GetFont(family,size)" to obtain font object'],
        'text-font-size':[8,'int','font size'],
        'text-font-color':[[0.0,0.0,0.0],'color','text color(black)'], #black
        'text-message-color':[[1.0,1.0,0.0,1.0],
                              'color','text message color(yellow)'], 
        'image-format':['png','str','image data format to save canvas image'],
        'image-bgcolor':[[1.0,1.0,1.0,1.0],
                         'color','background color in capture canvas image'],
        'echo':[False,'bool','echo executed menu'],
        'messageboxok':[True,'bool','enable/disable MessageBoxOK'],
        'messageboxyesno':[True,'bool','enable/disable MessageBoxYesNo'],
        'messageboxokcancel':[True,'bool','enable/disable MessageBoxOKCancel'],
        'redirect':[True,'bool','redirect stdout and stderr to shell console'],
        'warning':[True,'bool','worrning message'],
        'dump-draw-items':[False,'bool',
                           'dump draw items when closing molecule'], # dump draw items on close molecule
        'max-undo':[3,'int',
                    'max. number of undo in change geometry operations'],
        'max-undo-zmt':[3,'int','max. number of undo in Z-matrix editor'],
        'max-file-history':[10,'int','max. number of file history'],
        'del-image-files':[True,'bool',
                           'delete files in "Images" folder without asking'], 
        'del-scratch-files':[True,'bool',
                'delete scratch files in "Scratch" directory at starting'],
        'pycrust-shell':[False,
                         'bool','shell choice. True: PyCrust, False: PyShell'],
        'fmo-menu':[True,'bool','activate "FMO" menu'],
        'add-on1-menu':[[],'menu',
              'add-on menu item data given by "setting" script or "Customize"'],
        'add-on2-menu':[[],'menu',
            'second add-on menu item data given by "setting" script"'],
        'control-win-menu':[self.DefaultControlWinMenu(),
                            'method','menu items in "ControlWin"'],
        'tools':[False,'bool','Tools commands enable(True)/disabel(False)'],
        'hide-mdlwin':[False,'bool','Hide mdlwin(main) window'],
        # modeling
        'auto-add-hydrogens':[False,'bool',
            'enable add hydrogens to polypeptides at reading structure data'],
        'auto-del-ters':[False,'bool',
                         'delete "TER"s in PDB data at reading file'],
        'use-fmoutil':[True,
                       'bool','use fmoutil to add hydrogens to polypeptide'],
        'tinker-atom-name':[False,'bool','change atom name for "TINKER"'],
        'tinker-atom-order':[False,'bool','change atom order for "TINKER"'],     
        # atom params
        'mol-model':[0,'model',
                     'molecular model. 0:line,1:stcik,2:ball-and-stick, 3:CPK'],
        'element-color':[SettingCtrl.DefaultElementColor(),
                         'dic-color','element color dictionary'],
        'atom-sphere-radius':[0.3,'float','shere radius of atom'],
        'vdw-radius':[SettingCtrl.DefaultVdwRadius(),
                      'dic-float','dictionary of van-der-waals radius'],
        'bond-thick':[1,'int',
                      'bond thickness in line, stick model'],
        'bond-thick-bs':[0.5,'float',
                      'bond thickness in ball-and-stic model'],
        # draw params
        'fog':[False,'bool','apply "Fog" effect'], # fog 
        'select-color':[[0.0,1.0,0.0,1.0],'color','color for selected atoms'],
        'env-atom-color':[[0.68,0.02,0.64,1.0],
                          'color','color for environment atoms'],
        'sel-box-color':[[0.0,1.0,0.0,0.3],
                         'color','color for box selected region'],
        'sel-sphere-color':[[0.0,1.0,0.0,0.3],
                            'color','color for sphere selected region'],
        'draw-message-font':[0,'int',
           'use the "GetBitmapFont(style)" staticmethod to obtain font object'],
        'draw-message-color':[[0.0,1.0,0.0,1.0],
                              'color','color of messeges on glcanvas'], 
        'mode-message-color':[[1.0,1.0,1.0,1.0],
                              'color','text color for "mode message"'], # mode message color
        'aa-chain-color':[SettingCtrl.DefaultAAChainColor(),
                          'dic-color','polypeptide chain color'],
        'aa-residue-color':[SettingCtrl.DefaultAAResidueColor(),
                            'dic-color','amino-acid residue color'],

        'rot-axis-arrow-thick':[1,'int','thickness of rotation axis'], 
        'rot-axis-arrow-head':[0.2,'float','ratio of arrow head'],
        'rot-axis-arrow-color':[[1.0,1.0,0.0,1.0],
                                'color','color for rotation-axis'],
        'draw-torsion-angle':[False,'bool','draw torsion angle when axis rot'],        
        'beep-short-contact':[0.8,'bool','beep when short contact occured'],
        'label-color':[[0.0,1.0,0.0],'color',
                       'label (elm,atmnam,resnam,..) color on glcanvas'],
        'extra-bond-thick':[1,'int','thickness for extra bond'],
        'hydrogen-bond-thick':[1,'int','thickness for hydrohgen-bond'],
        'hydrogen-bond-color':[[0.0,1.0,1.0,1.0],'color','hydrogen-bond color'], # cyan
        'vdw-bond-color':[[0.0,1.0,1.0,1.0],'color','color for vdw-contact'], #cyan
        'stick-radius':[0.2,'float',
                        'radius for stick in "stik" and "ball-and-stic model'],
        'ball-radius':[0.4,'float','ball radius for "ball-and-stick" model'],
        'cpk-radius-scale':[1.0,'float','scale for vdw radius'],
        
        'aa-tube-color':[[1.0,1.0,1.0,1.0],'color','color of polupeptide tube'],
        'aa-tube-radius':[0.2,'float','radius of polypeptide tube'],
        'calpha-line-thick':[1,'int','line thickness of CAlpha chain'],
        'vib-vec-arrow-thick':[1,'int','thickness of arrow'],
        'vib-vec-arrow-head':[0.25,'float','arrow head raitio'],
        'vib-vec-arrow-color':[[1.0,1.0,0.0,1.0],'color','arrow color'],
        
        'xyz-axis-thick':[1,'int','thickeness of xyz-axis line'],

        'stereo-eye':[1,'int','stereo eye choice. 1:cross, 2:parallel'],
        # shortcut key definition
        'custom-shortcut-key':[SettingCtrl.CustomShortcutKey(),
                            'method','dictionary data for shortcut key assign'],
        'reserved-shortcut-key':[SettingCtrl.ReservedShortcutKey(),
                            'method','dictionary data for shortcut key assign'],
        'shortcut-key':[SettingCtrl.ShortcutKey(),
                        'dic-int','dictionary data for shortcut key assign'],
        'zoom-speed':[10,'int','spped for zoom by key'], # picxel
        'translate-speed':[2,'int','spped for translate by key'], # pixcel
        # pdb-ftp-server to get monomer (frame) data
        'pdb-monomer-ftp-server':[['ftp.wwpdb.org','guest','',
             'pub/pdb/data/monomers'],'lst','pdb-ftp server to get frame data'],
        'pdb-model-ftp-server':[['ftp.pdbj.org','anonymous','','model'],
                                'lst','pdb-ftp server to get model data'],
        'pdb-site':['http://www.rcsb.org/pdb/home/home.do','str','URL of PDB'],
        'check-pdb-atmnam':[True,'bool','Check atmnam of PDB is new?'],
        # misc
        'output-filter':['','str','default filter file for reading output'],
        'save-log':[False,'bool','save log file flag'],
        'logfile-dir':[None,'str','logfile directory'],
        'logging-method-file':[self.loggingmethodfile,'str',
                               'logging method definition file'],
        'suppress-message':[False,'bool','suppress message'],
        'message-level':[1,'int','Message level, 0(minimum)-5(maximum)'],
        # fragmentation
        'split-option':[[0,1],'lst',
               'allow to split at option bonds in auto fragmentation'],
        # variables
        'defaultfilename':['','str','default file name in ;ib.GetFileNmae'],
        # constants
        #'radian2degree' : [57.29577951,'float','conversion factor for radian-to-degree'],
        #'degree2radian' : [0.017453292,'float','conversion factor for degree-to-radian'],
        #'bohr2angatrom' : [0.529917724,'float','conversion factor for bhor-to-angstrom'],
        #'angatrom2bohr' : [1.8870854,'float','conversion factor for angstrom-to-bhor'],
        }
        return params

    @staticmethod
    def DefaultControlWinMenu():
        menulst=[
            ['',''], # the first item
            ['select hydrogens','Select-Hydrogen atom'], 
            ['select waters','Select-Water molecule'],
            ['select complement','Select-Complement'],
            ['show selected only','Show-Selected only'],
            ['hide hydrogens','Show-Hide hydrogen'],
            ['show all','Show-All atom '],
            ['show peptide chain','Show-Tube'],
            ['dump draw item','Show-Dump'],
            ]
        return menulst

    @staticmethod
    def DefaultElementColor():
        color = {' H':[0.8,0.8,0.8,1.0],
                  ' C':[0.5,0.5,0.5,1.0],
                  ' N':[0.0,0.47,0.94,1.0], #[0.5,0.5,1.0,1.0],
                  ' O':[1.0,0.0,0.0,1.0],
                  ' S':[1.0,1.0,0.0,1.0],
                  'CL':[0.0,1.0,1.0,1.0], # cyan ... anion color
                  'NA':[1.0,1.0,0.0,1.0], # yellow ... cation color
                  'MG':[1.0,1.0,0.0,1.0], # yellow
                  'MN':[1.0,1.0,0.0,1.0], # yellow
                  'FE':[1.0,1.0,0.0,1.0], # yellow          
                  'CA':[0.5,0.0,0.0,1.0], # brown,[1.0,1.0,0.0,1.0], # yellow
                  ' X':[0.0,0.5,1.0,1.0], # dummy atom
                  'ZZ':[0.5,0.5,0.5,1.0], # unkown element
                  'XX':[0.0,0.0,0.0,1.0], # black, TER atom
                  'SL':[0.0,1.0,0.0,1.0], # green, selected atom
                  'EV':[1.0,0.0,0.6,1.0], # magenta,environment atoms
                  'EX':[0.0,1.0,1.0,1.0], # cyan, extra bond
                  '??':[1.0,0.0,0.6,1.0]  # unidentified atom
                 }
        return color  

    @staticmethod
    def DefaultVdwRadius():
        """ Caution! unknown values are arbitrary set to 1.8 angstroms """
        vdwrad={' H':1.20,'HE':1.20,'LI':1.37,'BE':1.45,' B':1.45,
                ' C':1.50,' N':1.50,' O':1.40,' F':1.35,'NE':1.30,
                'NA':1.57,'MG':1.36,'AL':1.25,'SI':1.17,' P':1.80,
                ' S':1.75,'CL':1.70,'AR':1.80,' K':1.80,'CA':1.80,
                'SC':1.80,'TI':1.80,'V ':1.80,'CR':1.80,'MN':1.80,
                'FE':1.80,'CO':1.80,'NI':1.80,'CU':1.80,'ZN':1.80,
                'GA':1.80,'GE':1.80,'AS':1.80,'SE':1.80,'BR':1.80,
                'KR':1.80,'RB':1.80,'SR':1.80,' Y':1.80,'ZR':1.80,
                'NB':1.80,'MO':1.80,'TC':1.80,'RU':1.80,'RH':1.80,
                'PD':1.80,'AG':1.80,'CD':1.80,'IN':1.80,'SN':1.80,
                'SB':1.80,'TE':1.80,' I':1.80,'XE':1.80,'CS':1.80,
                'BA':1.80,'LA':1.80,'CE':1.80,'PR':1.80,'ND':1.80,
                'ZZ':1.80,'XX':0.0, # 'ZZ': unkown, 'XX': TER Atom
                }
        return vdwrad   
        
    @staticmethod
    def DefaultAAResidueColor():
        # rainbow color: #FF8000,#FF8000,#FFFF00,#009900,#0000FF,#0000CC,#6600CC
        #rescolor={'GLY':[1.0,0.0,0.0,1.0],'ALA':[1.0,0.66,1.0,1.0],'VAL':[1.0,1.0,0.0,1.0],
        #          'PHE':[0.0,0.60,0.0,1.0],'ILE':[0.0,0.0,1.0,1.0],'LEU':[0.0,0.0,0.80,1.0],
        #          'PRO':[0.40,0.0,0.80,1.0],'MET':[1.0,1.0,1.0,1.0],
        #          'ASP':[1.0,0.0,0.0,1.0],'GLU':[1.0,0.66,1.0,1.0],'LYS':[1.0,1.0,0.0,1.0],
        #          'ARG':[0.0,0.60,0.0,1.0],'SER':[0.0,0.0,1.0,1.0],'THR':[0.0,0.0,0.80,1.0],
        #          'TYR':[0.40,0.0,0.80,1.0],'CYS':[1.0,1.0,1.0,1.0],
        #          'ASN':[1.0,0.0,0.0,1.0],'GLN':[1.0,0.66,1.0,1.0],'HIS':[1.0,1.0,0.0,1.0],
        #          'TRP':[0.0,0.60,0.0,1.0],'HIP':[0.0,0.0,1.0,1.0],'HIE':[0.0,0.0,0.80,1.0],
        #          'HID':[0.40,0.0,0.80,1.0],'CYX':[1.0,1.0,1.0,1.0],
        #          '???':[1.0,0.0,0.0,1.0]
        #         }
        rescolor={'GLY':[1.0,0.0,0.0,1.0],'ALA':[1.0,0.66,1.0,1.0],
                  'VAL':[0.92,0.77,0.06,1.0],
                  'PHE':[0.0,0.60,0.0,1.0],'ILE':[0.0,0.81,0.92,1.0],
                  'LEU':[0.60,0.39,0.99,1.0],
                  'PRO':[0.40,0.0,0.80,1.0],'MET':[1.0,1.0,1.0,1.0],
                  'ASP':[1.0,0.0,0.0,1.0],'GLU':[1.0,0.66,1.0,1.0],
                  'LYS':[0.92,0.77,0.06,1.0],
                  'ARG':[0.0,0.60,0.0,1.0],'SER':[0.0,0.81,0.92,1.0],
                  'THR':[0.0,0.0,0.80,1.0],
                  'TYR':[0.40,0.0,0.80,1.0],'CYS':[0.75,0.75,0.75,1.0],
                  'ASN':[1.0,0.0,0.0,1.0],'GLN':[1.0,0.66,1.0,1.0],
                  'HIS':[0.92,0.77,0.06,1.0],
                  'TRP':[0.0,0.60,0.0,1.0],'HIP':[0.0,0.0,1.0,1.0],
                  'HIE':[0.0,0.0,0.80,1.0],
                  'HID':[0.40,0.0,0.80,1.0],'CYX':[0.75,0.75,0.75,1.0],
                  '???':[1.0,0.0,0.0,1.0]
                 }
        return rescolor

    @staticmethod
    def DefaultAAChainColor():
        # rainbow color: #FF8000,#FF8000,#FFFF00,#009900,#0000FF,#0000CC,#6600CC
        #chaincolor={0:[1.0,0.0,0.0,1.0],1:[1.0,0.66,1.0,1.0],2:[1.0,1.0,0.0,1.0],
        #          3:[0.0,0.60,0.0,1.0],4:[0.5,0.5,1.0,1.0],5:[0.0,0.0,0.80,1.0],
        #          6:[0.40,0.0,0.80,1.0],7:[1.0,1.0,1.0,1.0]
        #          }
        chaincolor={0:[1.0,0.0,0.0,1.0],1:[1.0,0.66,1.0,1.0],
                    2:[0.92,0.77,0.06,1.0], #[1.0,1.0,0.0,1.0],
                  3:[0.0,0.60,0.0,1.0],4:[0.0,0.81,0.92,1.0],
                  5:[0.41,0.52,0.97,1.0],
                  6:[0.60,0.39,0.99,1.0],7:[0.75,0.75,0.75,1.0]
                  }
        return chaincolor
    @staticmethod
    def CustomShortcutKey():
        """ sortcut-key assignment (custom)
        
        :return: shortcutkeydic-{keychar(str):[top menu(str),menuname(str)],...}
        :rtype: dic
        """
        customkeydic={  'f':['Show','Fit to screen',False,'in all modes'], # in standard mode
                        'c':['Hidden','Change center of rotation',False,
                             'in all modes'], # in standard mode
                        '0':['Hidden','Delete bond',False,
                             'in "Make Bond" mode'], # in mdlmod=3
                        '1':['Hidden','Make single bond',False,
                             'in "Make Bond" mode'], # in mdlmod=3
                        '2':['Hidden','Make double bond',False,
                             'in "Make Bond" mode'], # in mdlmod=3
                        '3':['Hidden','Make triple bond',False,
                             'in "Make Bond" mode'], # in mdlmod=3
                        '4':['Hidden','Make aromatic bond',False,
                             'in non "standard" mode'], # in mdlmod=3
                        #'space':['Hidden','Reset mouse operation mode',False,'in non "standard" mode'],
                        'space':['Hidden','Remove all labels',False,
                                 'in any mode'],
                        'esc':['Hidden','Close popup menu',False,
                               'close popup menu(For Mac and LINUX'], 
                        '>':['Hidden','Magnify',False,'in "standard mode'],
                        '<':['Hidden','Reduce',False,'in standard mode'],
                        'up arrow':['Hidden','Move upward',False,
                                    'in "standard mode'],
                        'down arrow':['Hidden','Move downward',False,
                                      'in "standard mode'],
                        'left arrow':['Hidden','Move leftward',False,
                                      'in "standard mode'],
                        'right arrow':['Hidden','Move rightward',False,
                                       'in "standard mode'],
                        #'q':['Select','Remove sphere/box',False,'in "Sphere/Box selection" mode'], # in mdlmod != 'standard'
                        'i':['Hidden','Save image',False,'in "standard mode'],
                        'j':['Hidden','Dump view',False,'in "standard mode'],
                        'k':['Hidden','Restore view',False,
                             'in "standard mode'],
                        #'v':['Hidden','Save view',False,'Save current view params on logfile'],
                        #'v':['Hidden','Focus selected atoms',False,'Focus selcted atoms'],
                        'z':['Hidden','Focus selected atoms',False,
                             'Focus selcted atoms'],
                        's':['Select','Deselect all',False,
                             'Deselect all atoms'],
                        'a':['Hidden','Switch select object',False,
                             'Switch select object "Atom"<->"Residue"'],
                        #'r':['Select','Residue',False,'Set select object to "Residue"'],
                        #'u':['Select','Unlimited',False,'Set select object number to "Unlimit"'],
                        'w':['Hidden','Switch select number',False,
                             'Switch select number "2-objects"<->"Unlimit"'],
                        'd':['Select','Remove box/sphere',False,
                             'Remove bulk selection sphere/box'],
                        }        
        return customkeydic
    @staticmethod
    def ReservedShortcutKey():
        """ sortcut-key assignment(reserved)
        
        :return: shortcutkeydic-{keychar(str):[top menu(str),menuname(str)],...}
        :rtype: dic
        """
        reservedkeydic={'ctrl':['None','None',
                                'Switch "view mode"<->"build mode"'], 
                        'shift':['None','None',
                                 'Temporary switch mouse move to "translate"'], 
                        #'esc':['Hidden','Reset mouse operation mode',''],
                        'space':['None','None','Remove labels'],
                        'del':['None','None','Delete selected atoms']
                        }       
        return reservedkeydic
    @staticmethod
    def ShortcutKey():
        shortcutkeydic=SettingCtrl.CustomShortcutKey()
        shortcutkeydic.update(SettingCtrl.ReservedShortcutKey())
        return shortcutkeydic
                
    def GetControlWinMenu(self):
        """
        Default menu items for 'ControlWin' subwindow
        
        :return: menulst: [['item label','View menu item label'],,,]
        :rtype: lst
        """
        menulst=SettingCtrl.DefaultControlWinMenu()
        if len(self.ctrlwinmenu) > 0: menulst=self.ctrlwinmenu
        return menulst

    def ClearUserControlWinMenu(self):
        self.ctrlwinmenu=[]

    def GetDefaultControlWinMenu(self):
        return SettingCtrl.DefaultControlWinMenu()

    def GetElementColor(self,elm):
        param=SettingCtrl.DefaultElementColor()
        param.update(self.elmcolor)
        color=param[elm]
        return color
    
    def SetElementColor(self,elm,color):
        self.elmcolor[elm]=color
        self.elmcolordic=self.GetElementColorDic()

    def GetProjectNameList(self):
        """ make project names in 'Project' directory for Create 'File'-'Project' menu items
        
        :return: prjnamlst: prjnamlst:['prjject name',...]
        :rtype: lst
        :see: fuctrl.MenuCtrl.CreateProjectMenuItems method
        """
        """
        prjnamlst=[]; prjfilelst=[]
        prjdir=self.GetDir('Projects')
        if prjdir =='': return []
        prjfiles=lib.GetFilesInDirectory(prjdir,['.project'])
        if prjfiles == '': return []
        for filnam in prjfiles: prjfilelst.append(filnam)
        prjfilelst.sort()
        """
        prjfilelst=self.GetProjectFileList()
        prjnamlst=[]
        for filnam in prjfilelst:
            head,tail=os.path.split(filnam)
            base,ext=os.path.splitext(tail)
            prjnam=self.ReadProjectFile(filnam)
            prjnamlst.append(prjnam)
        return prjnamlst

    def GetFrameDataList(self):
        """ Get frame data list in 'FUDIR/Frames' directory
        
        :return: framelst:[monomer-name(str),...]
        :rtype: lst
        """
        framelst=[]
        framedir=self.GetDir('Frames')
        framefiles=lib.GetFilesInDirectory(framedir,['.frm'])
        #for filnam in framefiles: framefilelst.append(filnam)
        framefiles.sort()
        for filnam in framefiles:            
            head,tail=os.path.split(filnam)
            base,ext=os.path.splitext(tail)
            framelst.append(base)
        return framelst

    def GetFilesList(self,name):
        filelst=[]
        files=self.fufiles[name]
        for filnam in files: filelst.append(filnam)
        filelst.sort()
        return filelst

    def MakeProjectDataDic(self):
        """ used in 'custom.CustomProject' 
        
        :return: prjdatdic[prjnam]=[prjnam,prjdir,curdir,prjfile,setfile,createdby,createddate,comment]
        :rtype: dic
        """
        prjdatdic={}
        prjfiledir=self.GetDir('Projects')
        prjfilelst=self.GetProjectFileList()
        for filnam in prjfilelst:            
            head,tail=os.path.split(filnam)
            base,ext=os.path.splitext(tail)
            prjdat=self.ReadProjectFile(filnam)
            prjdat[1]=os.path.join(prjdat[1],base)
            prjfile=os.path.join(prjfiledir,tail)
            prjdat.insert(3,prjfile) # insert 'prjfile' before 'setfile'
            prjdatdic[base]=prjdat
        # add 'None' project
        prjdatdic['None']=['None',self.fudir,self.curdir,'',
                           self.setfile,'','','']
        return prjdatdic

    def GetProjectPath(self,prjnam):
        if not self.prjdatdic.has_key(prjnam):
            return ''
        return self.prjdatdic[prjnam][1]        
        
    def GetProjectDataList(self):
        
        prjfilelst=self.GetProjectFileList()
        prjdatlst=[]
        for filnam in prjfilelst:            
            head,tail=os.path.split(filnam)
            base,ext=os.path.splitext(tail)
            prjdat=self.ReadProjectFile(filnam)
            prjdatlst.append(prjdat)
        return prjdatlst

    def ReadProjectFile(self,filename):
        prjdat=[]; prjnam=''; prjpath=''; createdby=''; createddate=''
        comment=''
        curdir=''; setfile=''
        if not os.path.exists(filename): return prjdat
        f=open(filename,'r')
        for s in f.readlines():
            s=s.strip()
            if s[:1] == '#': continue
            items=s.split('=')
            if len(items) >= 2:
                itemnam=items[0].strip()
                value=items[1].strip()
                # 'prjnam' is deleted. See fucostom.CostomizeProject.WriteProjectFile()
                if itemnam == 'prjnam': prjnam=value
                if itemnam == 'prjpath': prjpath=value
                if itemnam == 'curdir': curdir=value
                if itemnam == 'setting': setfile=value          
                if itemnam == 'createdby': createdby=value
                if itemnam == 'createddate': createddate=value
                if itemnam == 'comment': comment=value
        f.close()
        #if prjnam == '': # or prjdir == '':
        #    mess=self.classnam+'(ReadProjectFile): missing project name in "'+filename+'"'
        #    wx.MessageBox(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)            
        head,tail=os.path.split(filename)
        base,ext=os.path.splitext(tail)
        prjnam=base
        prjdat=[prjnam,prjpath,curdir,setfile,createdby,createddate,
                comment]
        return prjdat
        
    def ProjectSetting(self,mode):
        """ Open project setting window.
        
        :param str mode: 'New' or 'Import'
        """
        winlabel=mode
        self.model.winctrl.OpenCreateProjectWin(winlabel)

    def CreateIniFile(self,filename):
        #prjdir=self.GetDir('Projects')
        #filename=os.path.join(prjdir,'None.project')
        f=open(filename,'w')
        f=open(filename,'w')
        f.write('# project file. '+lib.CreatedByText()+'\n')
        #f.write('prjnam='+prjnam+'\n')
        f.write('prjdir='+self.fupath+'\n')
        f.write('createdby=\n')
        f.write('createddate=\n')
        f.write('comment=\n')
        f.write('curdir=\n')
        f.write('setting=\n')
        f.close()
        
    def GetVdwRadius(self,elm):
        radius=self.params['vdw-radius'][elm]
        return radius
    
    def SetVdwRadius(self,elm,radius):
        self.params['vdw-radius'][elm]=rdius

    def ClearUserVdwRadius(self):
        self.vdwrad={}

    def GetAAResidueColor(self,resnam):
        color=self.params['aa-residue-color'][resnam]
        return color
    
    def SetAAResidueColor(self,resnam,color):
        self.params['aa-residue-color'][resnam]=color
        
    def ClearUserAAResidueColor(self):
        self.aarescolor={}

    def MakeFullPathNameOfParamFile(self,prmnam,ext):
        """
        :param str ext: ext='.shortcut'
        """
        filename=prmnam
        ns=prmnam.find(ext)
        if ns < 0: filename=prmnam+ext
        dir=self.GetDir('Customize')
        filename=os.path.join(dir,filename)       
        return filename
    
    def LoadGeneralParamSet(self,prmnam):
        # setnam='general' or 'model'
        paramtypedic=self.MakeParamTypeDic() #self.paramtypedic #SettingCtrl.ParamTypeDic()
        filename=self.MakeFullPathNameOfParamFile(prmnam,'.general')
        if not os.path.exists(filename): 
            mess='(LoadGeneralParamSet): file '
            mess=mess+'"'+filename+'" does not exist.'
            self.SettingMessage(self.classnam+mess)
            return
        paramdic=SettingCtrl.ReadParamSetFile(filename,paramtypedic)
        #self.SettingMessage(self.classnam+'(SetParamSet): file '+'"'+filename+'" was loaded.')
        self.params.update(paramdic)
        
    def LoadModelParamSet(self,prmnam):
        # setnam='general' or 'model'
        paramtypedic=self.MakeParamTypeDic() #self.paramtypedic # SettingCtrl.ParamTypeDic()
        filename=self.MakeFullPathNameOfParamFile(prmnam,'.model')
        if not os.path.exists(filename): 
            mess='(LoadModelParamSet): file '+'"'+filename+'" does not exist.'
            self.SettingMessage(self.classnam+mess)
            return
        paramdic=SettingCtrl.ReadParamSetFile(filename,paramtypedic)

    def LoadAddonMenuItems(self,addonnam):
         filename=self.MakeFullPathNameOfParamFile(addonnam,'.add-on')
         if not os.path.exists(filename): 
            mess='(SetAddonMenuItems): file '+'"'+filename+'" does not exist.'
            self.SettingMessage(self.classnam+mess)
            return '',[]
         addon,menulabel,menuitemlst=SettingCtrl.ReadAddonMenuFile(filename)
         self.SetParam(addon,[menulabel,menuitemlst])
    
    def LoadShortcut(self,prmsetnam):
        filename=self.MakeFullPathNameOfParamFile(prmsetnam,'.shortcut')
        if not os.path.exists(filename): 
            mess='(SetShortcut): file '+'"'+filename+'" does not exist.'
            self.SettingMessage(self.classnam+mess)
            return
        paramdic=SettingCtrl.ReadShortcutKeyFile(filename)
        #self.SettingMessage(self.classnam+'(SetShortcut): file '+'"'+filename+'" was loaded.')
        paramdic.update(SettingCtrl.ReservedShortcutKey())
        self.params['shortcut-key']=paramdic

    def GetShortcutKeyFile(self):
        if self.setfile == '': return ''
        setfile=os.path.join(self.GetDir('Customize'),self.setfile)
        print 'setfile',setfile
        [general,model,addon,shortcut]=custom.Customize_Frm.ReadSetFile(setfile)
        shortcut=shortcut+'.shortcut'
        return os.path.join(self.GetDir('Customize'),shortcut) 
         
    def SetAAChainColor(self,chaincolordic):
        """Set Chain color dictonary
        
        :param dic chaincolordic: {0:[1.0,0.0,0.0,1.0],1:[1.0,0.66,1.0,1.0],...}
        """
        self.aachaincolor=chaincolor
        self.params['aa-chain-color']=chaincolordic
        
    def ClearUserAAChainColor(self):
        self.aachaincolor=SettingCtrl.DefaultAAChainColor()
                    
    def SettingMessage(self,mess):
        self.message=self.message+'     '+mess+'\n'

    def GetSettingMessage(self):
        return self.message

    def GetParam(self,name):
        """Return draw parameters. See the 'DefaultDrawParams' method.
        
        :param str name: parameter name
        :return: parameter value
        :rtype: any
        """
        #default=self.DefaultParams()
        if self.params.has_key(name): value=self.params[name]
        else: value=None
        if name == 'font':
            if self.params.has_key('font-size'): size=self.params['font-size']
            else: size=default['font-size']
            value=lib.GetFont(value,size)
        if name == 'draw-message-font': value=lib.GetBitmapFont(value)
        return value
   
    def GetElementColorDic(self):
        colordic=self.params['element-color']
        return colordic

    def GetVdwRadiusDic(self):
        radiusdic=self.params['vdw-radius']
        return radiusdic
    
    def GetCurDir(self):
        return self.curdir

    def GetCurPrjPath(self):
        return self.prjdir
       
    def GetCurPrj(self):
        return self.curprj
 
    def GetSetFile(self):
        return self.setfile
          
    def GetTestFile(self):
        testfile=''
        if not self.fufiles.has_key('test'): return testfile
        files=self.fufiles['test']
        for file in files:
            base,ext=os.path.splitext(file)
            if ext == '.lst':
                testfile=file; break
        return testfile

    def GetIniDir(self):
        return self.inidir
    
    def GetIniProj(self):
        return self.iniprj

    def SetEcho(self,on):
        """ Set 'echo' on/off. Equivalent to 'SetParam('echo',on).
        
        :param bool on: Tryue for echo on, False for echo off.
        """   
        self.params['echo']=on
        
    def GetEcho(self):
        """ Return 'echo' value. Equivalent to 'GetParam('echo').
        
        :return: True for echo on, False for echo off.
        :rtype: bool
        """
        return self.params['echo']
    
    def SetMessageBoxFlag(self,name,on):
        if name == 'all':
            names=['','YesNo','OKCancel'] # '':'OK'
        else: names=[name]
        for name in names:
            messbox='messagebox'+name; messbox=messbox.lower()
            self.params[messbox]=on
            self.model.menuctrl.CheckMenu("Enable MessageBox"+name,on)

    def SetMessageLevel(self):
        messlevel=wx.GetTextFromUser('Enter message level, 0(minimum) to 5(maximum)', 'Set Message Level')
        try: messlevel=int(messlevel.strip())
        except:
            if len(messlevel) <= 0: return
            else:
                mess='Wrong input data. input='+messlevel
                lib.MessageBoxOK(mess,'SetCtrl(SetMessageLevel)')
                return
        self.SetParam('message-level',messlevel)
        lib.SetMessageLevel(messlevel)
    
    def GetMessageBoxFlag(self,name):
        messbox='messagebox'+name; messbox=messbox.lower()
        return self.params[messbox]

    def SetRedirect(self,on):
        """ On/Off redirect Stdout and Stderr to shell console. This function is useful in dubugging.
        
        :param bool on: True for enable redirect, False for disable
        """
        self.peram['redirect']=on

    def SetScreenCaputueProgForMac(self,prgpath):
        """ Set ScreenCaputure program path (MACOSX only)
        
        :param str prgpath: program path. default='/usr/sbin/sceencaputure'.
        """
        if lib.GetPlatform() != 'MACOSX':
            mess='setctl.SetScreenCaptureProgForMac: MACOSX only'
            self.model.ConsoleMessage(mess) 
        lib.MACSCREENCAPTURE=prgpath

    def SetEditorProg(self,prgpath):
        """ Set editor program path (MACOSX and LINUX only).
        
        :param str prgppath: program path. default="open -a TextEdit" for MAXOSX,
         and "open /user/bin/vim" for LINUX (LINUX is not tested)
        """
        lib.EDITOR=prgpath
        if len(lib.EDITOR) > 0:
            mess='Editor program(setctl.SetEditorProg): '+lib.EDITOE
            self.model.ConsoleMessage(mess) 
                      
    def GetRedirect(self):
        """ return current redirect status
        
        :return: True for redirect enabled, False for disabled
        :rtype: bool
        """
        return self.param['redirect']
    
    def GetShortcutKeyChar(self,cmd):
        """ e.g., cmd='Save image', return: 'i' """
        shortcutkeydic=self.GetParam('shortcut-key')
        for keynam,lst in shortcutkeydic.iteritems():
            if lst[1] == cmd: return keynam
        return None
        
    def SetMyParam(self,prmnam,value):
        """ Set value to 'stectrl.myparams' dictionary
        
        :param str prmnam: name of parameter
        :param any value: value of the prmnam
        """
        self.myparams[prmnam]=value
        
    def GetMyParam(self,prmnam):
        """ Get value of parameter in 'setctrl.myparams' dictionary
        
        :param str prmnam: name of parameter
        :return: value(any) - value of prmnam.
        """
        if self.myparams.has_key(prmnam): return self.myparams[prmnam]
        else: return ''
            
    def DelMyParam(self,prmnam):
        """ Delete parameter in 'setctrl.myparams' dictionary
        
        :param str prmnam: name of parameter or 'all"
        """
        if prmnam == 'all': self.myparams={}
        else:
            if self.myparams.has_key(prmnam): del self.myparams[prmnam]
            else: pass

    def ListMyParam(self,prmnam):
        """ List value of paramter in myparams dictionary
        
        :param str prmnam: name of parameter or 'all'
        """
        if prmnam == 'all':
            if len(self.myparams) > 0:
                print 'All paramters in "setctrl.myparams":'
                print self.myparams
            else: print 'No parameter is set in "setctrl.myparams".'
        else:
            if self.myparams.has_key(prmnam):
                print 'Value of myparam in "setctrl.myparams"='+prmnam
                print self.myparams[prmnam]
            else:
                print 'myparam "'+prmnam+'" is not defined in "setctrl.myparams".'        
            
    def ReadIniFile(self,inifile):
        """ Read initial setting file, 'fumodel.ini' file in 'FuFilesDirectory' directory.
        
        :return: initial directry
        :rtype: str
        :return: initial project
        :rtype: str
        :return: winpos-initial position of 'mdlwin' window, [xpos(int),ypos(int)] in pixels
        :rtype: lst
        :return: winsize-initial size of 'mdlwin' window, [width(int),height(int)] in pixels
        :rtype: lst
        """
        def TextToList(text):
            text=text.replace(" ","")
            text=text.replace("'",""); text=text.replace('"','')
            hislst=lib.StringToList(text)
            return hislst
        #inifile=os.path.join(self.fudir,self.inifilename)
        inidir=''; iniprj='' #; iniset=''; inicur=''; 
        winpos=[]; winsize=[]; hislst=[]; shlpos=[]; shlsize=[]
        find=False; text=''
        if os.path.exists(inifile):
            f=open(inifile,'r')
            for s in f.readlines():
                if len(s) <= 0: continue
                if s[0:1] == "#": continue
                if find:
                    text=text+s.strip()
                    if text[-1:] == ']':
                        find=False
                        hislst=TextToList(text)
                items=s.split('=')
                if len(items) >= 2:
                    if items[0].strip() == 'inidir': inidir=items[1].strip()
                    if items[0].strip() == 'iniprj': iniprj=items[1].strip()
                    #if items[0].strip() == 'iniset': iniset=items[1].strip()
                    if items[0].strip() == 'winpos':
                        posxy=items[1].split(',')
                        winpos.append(int(posxy[0])) 
                        winpos.append(int(posxy[1]))
                    if items[0].strip() == 'winsize':
                        sizexy=items[1].split(',')
                        winsize.append(int(sizexy[0])) 
                        winsize.append(int(sizexy[1]))
                    if items[0].strip() == 'pyshellpos':
                        posxy=items[1].split(',')
                        shlpos=[int(posxy[0]),int(posxy[1])]
                    if items[0].strip() == 'pyshellsize':
                        sizexy=items[1].split(',')
                        shlsize=[int(sizexy[0]),int(sizexy[1])]
                    if items[0].strip() == 'filehistory':
                        text=text+items[1].strip()
                        if text[-1:] == ']':
                            find=False
                            hislst=TextToList(text)
                        else: find=True
            f.close()         
        if len(winpos) <= 0: winpos=self.winpos
        if len(winsize) <= 0: winsize=self.params['win-size']
        #
        return inidir,iniprj,winpos,winsize,shlpos,shlsize,hislst

    def InitialProjectSetting(self,prjnam):
        self.inidir,self.winpos,self.winsize=self.ReadProjectIniFile(prjnam)
               
    def ReadProjectIniFile(self,prjnam):
        """ Read initial setting file, 'fumodel.ini' file in 'FuFilesDirectory' directory.
        
        :return: initial directry
        :return: initial project
        :return: winpos - initial position of 'mdlwin' window, [xpos(int),ypos(int)] in pixels
        :return: winsize - initial size of 'mdlwin' window, [width(int),height(int)] in pixels
        :rtype: str,str,lst,lst
        """
        inidir=''; winpos=[]; winsize=[]
        prjpath=self.GetProjectPath(prjnam)
        inifile=prjnam+'.ini'
        inifile=os.path.join(prjpath,inifile)
        inifile=lib.ExpandUserFileName(inifile)
        if not os.path.exists(inifile):
            print 'project inifile does not exist. inifile=',inifile
            return inidir,winpos,winsize
        if os.path.exists(inifile):
            f=open(inifile,'r')
            for s in f.readlines():
                if len(s) <= 0: continue
                if s[0:1] == "#": continue
                items=s.split('=')
                if len(items) >= 2:
                    if items[0].strip() == 'inidir': inidir=items[1].strip()
                    #if items[0].strip() == 'iniprj': iniprj=items[1].strip()
                    #if items[0].strip() == 'iniset': iniset=items[1].strip()
                    if items[0].strip() == 'winpos':
                        posxy=items[1].split(',')
                        winpos.append(int(posxy[0]))
                        winpos.append(int(posxy[1]))
                    if items[0].strip() == 'winsize':
                        sizexy=items[1].split(',')
                        winsize.append(int(sizexy[0]))
                        winsize.append(int(sizexy[1]))
            f.close()         
        if len(winpos) <= 0: winpos=self.winpos
        if len(winsize) <= 0: winsize=self.params['win-size']
        return inidir,winpos,winsize

    def LoadProjectMolecules(self,prjnam):
        """ Read initial setting file, 'fumodel.ini' file in 'FuFilesDirectory' directory.
        
        :return: initial directry
        :rtype: str
        :return: initial project
        :rtype: str
        :return: winpos - initial position of 'mdlwin' window, [xpos(int),ypos(int)] in pixels
        :rtype: lst
        :return: winsize - initial size of 'mdlwin' window, [width(int),height(int)] in pixels
        :rtype: lst
        """
        curmolnam=''; molfilelst=[]
        prjpath=self.GetProjectPath(prjnam)
        inifile=prjnam+'.ini'
        inifile=os.path.join(prjpath,inifile)
        inifile=lib.ExpandUserFileName(inifile)
        if not os.path.exists(inifile):
            print 'project inifile does not exist. inifile=',inifile
        if os.path.exists(inifile):
            f=open(inifile,'r')
            for s in f.readlines():
                if len(s) <= 0: continue
                if s[0:1] == "#": continue
                items=s.split('=')
                if len(items) >= 2:
                    if items[0].strip() == 'current molecule': 
                        curmolnam=items[1].strip()
                    if items[0].strip() == 'molecule': 
                        molfilelst.append(items[1].strip())
            f.close() 
        #              
        if len(molfilelst) > 0: 
            for file in molfilelst: self.model.ReadFilesPDB(file,False) #True)
            curmol=0
            for i in range(len(molfilelst)):
                head,tail=os.path.split(molfilelst[i])
                #base,ext=os.path.splitext(tail)
                if tail == curmolnam:
                    curmol=i; break
            self.model.molctrl.SwitchCurMol(curmol,Tue,True)   
            self.curmol=curmol
            #self.model.curmol=curmol
      
    @staticmethod
    def ReadParamSetFile(filename,paramtypedic):
        #modeldic={'0':'line','1':'stick','2':'ball-and-stick','3':'CPK'}
        booldic={'True':1,'False':0}
        if not os.path.exists(filename): return
        paramdic={}; colordic={}; prmnam=''
        f=open(filename,"r")
        for s in f.readlines():
            s=s.strip()
            if len(s) <= 0: continue
            if s[:1] == '#': continue
            ns=s.find('#')
            if ns > 0: 
                s=s[:ns]; s=s.strip()
            if s[:1] == "'" or s[:1] == '"':
                if len(colordic) > 0: paramdic[prmnam]=colordic
                s=s[1:]; prmnam=s[:-1]
                colordic={}
                continue
            else:
                if not paramtypedic.has_key(prmnam):
                    print 'Program error in "SerringManager:ReadParamSetFile"'
                    return                   
                if paramtypedic[prmnam] == 'dic-color':
                    items=s.split()
                    name=items[0].strip()
                    if prmnam == 'element-color':
                        if len(name) <= 1: name=name.rjust(2,' ')
                    if prmnam == 'aa-chain-color':
                        name=int(name)
                    else: 
                        if not isinstance(name,str): name=str(name)
                    r=float(items[1]); g=float(items[2]); b=float(items[3])
                    a=float(items[4])
                    colordic[name]=[r,g,b,a]
                elif paramtypedic[prmnam] == 'color':
                    items=s.split()
                    r=float(items[0]); g=float(items[1]); b=float(items[2])
                    a=float(items[3])
                    paramdic[prmnam]=[r,g,b,a]
                elif paramtypedic[prmnam] == 'int':
                    paramdic[prmnam]=s.strip()
                elif paramtypedic[prmnam] == 'float': 
                    paramdic[prmnam]=float(s.strip())
                elif paramtypedic[prmnam] == 'bool': 
                    paramdic[prmnam]=booldic[s.strip()]
                elif paramtypedic[prmnam] == 'model':
                    model=int(s.strip())
                    paramdic[prmnam]=model  #modeldic[s.strip()]
                else: paramdic[prmnam]=s.strip() # 'str'
        f.close()
        
        return paramdic

    @staticmethod
    def ReadShortcutKeyFile(filename):
        if not os.path.exists(filename): return
        keydic={}; found=False; header='shortcut-key'
        f=open(filename,"r")
        for s in f.readlines():
            s=s.replace('\r',''); s=s.replace('\n','')
            s=s.strip()
            if len(s) <= 0: continue
            if s[:1] == '#': continue
            if s[:1] == '"' or s[:1] == "'":
                if found: break
                if s[1:-1] == header: found=True; continue
            if not found: continue
            items=s.split(' ',1)
            key=items[0].strip(); menu=items[1] # menu: top menu:submenu:subsub menu
            topsub=menu.split(':',2); top=topsub[0].strip()
            sub=topsub[1].strip()
            check=False
            if len(topsub) >=3: 
                check=topsub[2]
                if check == 'True': check=True
            keydic[key]=[top,sub,check] # the same list data as keyassigneddic
        f.close()
        return keydic

    @staticmethod
    def ReadAddonMenuFile(filename):
        addon=''; menulabel=''; menuitemlst=[]
        found=False
        f=open(filename,"r")
        for s in f.readlines():
            s=s.strip()
            if len(s) <= 0: continue
            if s[:1] == '#': continue
            if not found and (s[:1] == "'" or s[:1] == '"'):
                found=True
                addon=s[1:-1]
                continue
            if found:
                if s[:1] == "'" or s[:1] == '"': break
                ns=s.find('menulabel')
                if ns >= 0:
                    items=s.split('='); menulabel=items[1].strip()
                    continue
                submenudat=s.split()
                check=False
                if submenudat[2].strip() == 'True': check=True
                menuitemlst.append([submenudat[0],submenudat[1],check]) #submenudat[2]])
        f.close()
        return addon,menulabel,menuitemlst
            
    def SetFUDirsAndFiles(self):
        """ Search fu environment variable 'FUDIR' 
        and set directory/files and data used in the program. """
        # fufiles
        if not os.path.exists(self.fudir): return
        for d in self.fudirs:
            ddir=os.path.join(self.fudir,d)
            if not os.path.isdir(ddir): os.mkdir(ddir)
            files=lib.GetFilesInDirectory(ddir,['all'])
            self.fufiles[d]=files
        self.DeleteFilesInDir('Scratch') # delete scratch files

    def SetProjectFiles(self):
        # project files
        for d in self.prjdirs:
            ddir=os.path.join(self.prjdir,d)
            if not os.path.isdir(ddir): os.mkdir(ddir)
            files=lib.GetFilesInDirectory(ddir,['all'])
            self.fufiles[d]=files
        if len(self.fufiles['Images']) > 0:
            if not self.GetParam('del-image-files'):
                mess='there are image files in the "fufiles/image" directory. '
                mess=mess+'Would you like to delete them?'
                dlg=lib.MessageBoxYesNo(mess,"fumdodel:Initial Setting")
                if dlg: self.DeleteFilesInDir('Images') 
            else: self.DeleteFilesInDir('Images')                     
                       
    def IsDfined(self,name):
        if self.fufiles.has_key(name): return True
        else: return False

    def IsFileExists(self,name,filename):
        try: 
            idx=self.fufiles[name].index(filename)
            if idx < 0: return False
            else: return True
        except: return False
                
    def GetFUPath(self):
        return self.fupath
    
    def GetFUDir(self):
        return self.fudir

    def GetEnv(self):
        fuenv=self.fuenv
        if not fuenv: fuenv='None'
        return fuenv
    
    def GetDir(self,name):
        if name == 'Scripts': return self.scriptdir
        elif name == 'Tools': return self.toolsdir
        #
        if self.prjdirs.has_key(name):
            dir=os.path.join(self.prjdir,name)
            if os.path.isdir(dir): return dir
            else: return os.path.join(self.fudir,name)
        else:
            if not self.fufiles.has_key(name): return ''
            else:
                if len(self.fufiles[name]) <= 0: 
                    return os.path.join(self.fudir,name)
                file=self.fufiles[name][0]
                head,tail=os.path.split(file)
                return head

    def GetIconBmp(self,name,imgfrm='.png'):
        iconbmp=''
        iconfile=name+imgfrm
        #icondir=self.model.setctrl.GetDir('Icons')
        icondir=os.path.join(self.fusrcdir,'Icons')
        iconfile=os.path.join(icondir,iconfile)
        iconfile=lib.ReplaceBackslash(iconfile)
        if os.path.exists(iconfile): 
            iconbmp=wx.Bitmap(iconfile,wx.BITMAP_TYPE_ANY)
        return iconbmp

    def GetScriptDir(self):
        return self.scriptdir
    
    def GetToolsDir(self):
        return self.toolsdir
    
    def ChangeScriptsDir(self,scriptdir):
        name='Scripts'
        if len(scriptdir) <= 0:
            self.model.ConsoleMessage('Directory name is null.')
            return
        #scrdir=os.path.join(rootdir,name)
        scriptdir=lib.ExpandUserFileName(scriptdir)
        if not os.path.isdir(scriptdir):
            mess='Directory "'+scriptdir+'" does not exist.'
            self.model.ConsoleMessage(mess)
            return 
        #files=lib.GetFilesInDirectory(scrdir,['all'])
        #self.fufiles[name]=files
        self.scriptdir=scriptdir
        mess='"Scripts" directory has changed to "'+scriptdir+'".'
        self.model.ConsoleMessage(mess)

    def ChangeToolsDir(self,toolsdir):
        name='Tools'
        if len(toolsdir) <= 0:
            self.model.ConsoleMessage('Directory name is null.')
            return
        #scrdir=os.path.join(rootdir,name)
        toolsdir=lib.ExpandUserFileName(toolsdir)
        if not os.path.isdir(toolsdir):
            mess='Directory "'+toolsdir+'" does not exist.'
            self.model.ConsoleMessage(mess)
            return 
        #files=lib.GetFilesInDirectory(scrdir,['all'])
        #self.fufiles[name]=files
        self.toolsdir=toolsdir
        mess='"Tools" directory has changed to "'+toolsdir+'".'
        self.model.ConsoleMessage(mess)
        
    def ChangeImagesDir(self,rootdir):
        name='Images'
        if len(rootdir) <= 0:
            self.model.ConsoleMessage('Directory name is null.')
            return
        imgdir=os.path.join(rootdir,name)
        imgdir=lib.ExpandUserFileName(imgdir)
        if not os.path.isdir(imgdir): 
            self.model.ConsoleMessage('Directory "'+imgdir+'" does not exist.')
            return
        files=lib.GetFilesInDirectory(imgdir,['all'])
        self.fufiles[name]=files
        mess='"'+name+'" root directory has changed to "'+rootdir+'".'
        self.model.ConsoleMessage(mess)
        
    def SetNameFiles(self,name,filelst):
        self.fufiles[name]=filelst

    def GetFilesOfName(self,name):
        if self.fufiles.has_key(name): return self.fufiles[name]
        else: return []
 
    def GetFile(self,name,filename):
        filnam=''
        for fil in self.fufiles[name]:
            head,tail=os.path.split(fil)
            if tail == filename:
                filnam=fil; break
        return filnam
    
    def GetDataFileInFUdocs(self,filename):
        """ Return data file path in FUDATASET//FUdocs
        
        :param str filename: file name or 'all'
        :return: filepath(str) or filepathlst(lst)
        """
        datdir=os.path.join(self.fudir,'FUdocs//data')
        if filename == 'all':
            filepathlst=lib.GetFilesInDirectory(datdir)
            return filepathlst
        else:
            filepath=os.path.join(datdir,filename)
            filepath=lib.ReplaceBackslash(filepath)
            return filepath
        
    def GetNames(self):
        lst=[]
        for item,value in self.fufiles.iteritems(): lst.append(item)
        return lst

    def DeleteFilesInDir(self,dirnam):
        nfil=len(self.fufiles[dirnam])
        if not self.fufiles.has_key(dirnam) or nfil <= 0: return
        dirnam=os.path.join(self.fudir,dirnam)
        lib.DeleteFilesInDirectory(dirnam,'all')
        mess='All files ('+str(nfil)+') in '+dirnam+' were deleted.'
        self.SettingMessage(mess)
        self.fufiles[dirnam]=[]

    def GetParamSetFiles(self,paramsetnam):
        filextdic={'General':'.general','Model':'.model',
                   'Shortcut':'.shortcut','Add-on':'*.add-on',
                   'Setting':'.py','Project':'.project'}
        if not filextdic.has_key(paramsetnam):
            print '"'+paramsetname+'" is not defines'
            return
        paramset=[]
        if paramsetnam == 'Project':
           pass
        else:
           pass 
        return paramset

    def GetParamSetNames(self,paramsetnam):
        filextdic={'General':'.general','Model':'.model',
                   'Shortcut':'.shortcut','Add-on':'*.add-on',
                   'Setting':'.py','Project':'.project'}
        if not filextdic.has_key(paramsetnam):
            print '"'+paramsetname+'" is not defines'
            return
        paramset=[]
        if paramsetnam == 'Project':
           pass
        else:
           pass 
        return paramset

    def GetEditorProgramPath(self):
        prgtxt='editor.txt'; editor=''
        if const.SYSTEM == const.WINDOWS or const.SYSTEM == const.WIN32: 
            keywrd='WINDOWS'
        elif const.SYSTEM == const.MACOSX: keywrd='MACOSX'
        elif const.SYSTEM == fucons.LINUX: keywrd='LINUX'
        #
        editorfile=self.model.setctrl.GetFile('progs',prgtxt)
        if len(editorfile) > 0:
            f=open(editorfile,'r')
            for s in f.readlines():
                s=s.strip()
                if s[:1] == '#': continue
                items=s.split(':')
                if len(items) < 2: continue
                key=items[0].strip()
                if key == keywrd:
                    editor=items[1].strip(); break
            f.close()
        #
        if len(editor) <= 0:
            mess="Editor program is not set for "+const.SYSTEM+". "
            mess=mess+"Set program path by 'Help'-'Setting' menu."
            lib.MessageBoxOK(mess,"")
            return
        return editor

    @staticmethod
    def GetFont(family,size):
        """ Fonts
        
        :param int style: 0-5.
        :param int size: default:8
        :return: wx.Font object
        :rtype: obj
        """
        if size <= 0: size=8
        if family == 0: font=wx.Font(size, 
               wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier')     
        elif family == 1: font=wx.Font(size, 
               wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Decorative')
        elif family == 2: font=wx.Font(size, 
               wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Script')
        elif family == 3: font=wx.Font(size, 
               wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Swiss')
        elif family == 4: font=wx.Font(size, 
               wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Modern')
        elif family == 5: font=wx.Font(size, 
               wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Teletype')
        else: font=wx.Font(size, wx.FONTFAMILY_DEFAULT, 
               wx.FONTSTYLE_NORMAL,
               wx.FONTWEIGHT_BOLD, False, 'Courier')     
        return font
    
    @staticmethod 
    def GetBitmapFont(style):
        """ Bitmap fonts
        
        :param int style: 0-6.
        :return: bitmap font object
        :rtype: obj
        """
        if style == 0: bmpfont=GLUT_BITMAP_8_BY_13, # 8 by 13 pixel
        elif style == 1: bmpfont=GLUT_BITMAP_9_BY_15,
        elif style == 2: bmpfont=GLUT_BITMAP_TIMES_ROMAN_10,
        elif style == 3: bmpfont=GLUT_BITMAP_TIMES_ROMAN_24,
        elif style == 4: bmpfont=GLUT_BITMAP_HELVETICA_10,
        elif style == 5: bmpfont=GLUT_BITMAP_HELVETICA_12,
        elif style == 6: bmpfont=GLUT_BITMAP_HELVETICA_18,
        else: bmpfont=GLUT_BITMAP_8_BY_13
        return bmpfont
                       
# subwindow windows manager
class WinCtrl():
    """ Subwindows manager
    
    :param obj parent: instance of parent object
    """
    def __init__(self,parent):
        self.model=parent # Model
        self.mdlwin=parent.mdlwin
        self.menuctrl=parent.menuctrl
        self.mousectrl=parent.mousectrl
        #
        self.openwin=None
        self.winlabel=''
        self.openwindic={}
        self.pycrustshell=self.model.setctrl.GetParam('pycrust-shell') #'setctrl.pycrustshell # Treu:pycrust,False:pyshell

    def Message(self,mess,loc,color):
        """ Statusbar Message
        
        :param str mess: message text
        :param int loc: statusbar field, 0 or 1
        :param str color: wx.color name. Dummy.
        """
        self.model.Message(mess,loc,color)
 
    def OpenEditor(self,filename):
        """ Open editor ('NotePad' in Windows, 'TextEdit' in Mac OSX, 
        these are defined in FUDIR/Programs/editor.txt and 
        read in 'Setting(GetEditorProgramPath)'.
        
        :param str filename: file to be opened by the editor
        """  
        if not os.path.exists(filename):
            mess='model.winctrl(OpenEditor): File "'+filename+'" is not found.'
            lib.MessageBoxOK(mess,"")
            return            
        editor=self.model.setctrl.GetEditorProgramPath()
        if len(editor) <= 0:
            mess="Editor program is not found."
            lib.MessageBoxOK(mess,"")
            return
        if lib.GetPlatform() == 'WINDOWS':
            #os.spawnv(os.P_NOWAIT,"C:\\Windows\\System32\\notepad.exe",["notepad.exe"+' '+filename])       
            os.spawn(os.P_NOWAIT,editor,["notepad.exe"+' '+filename])
        elif lib.GetPlatform() == 'MACOSX': os.system(editor+' '+filename) 
        elif lib.GetPlatform() == 'LINUX': 
            os.system('/usr/bin/vim'+' '+filename)          

    def IsOpened(self,name):
        # winnam(str): subwindow's instance name
        # ret (bool): True for Opened, False for not opened.
        if not self.openwindic.has_key(name): return False
        #if not self.openwindic[name]: return
        else: return True
 
    def CloseWin(self,name):
        self.openwindic[name]=None
        self.CheckMenuItem(name,False)

    def SetOpened(self,name,ins):
        # name(str): item name
        # ins(ins): instance of window
        self.openwindic[name]=ins
        self.CheckMenuItem(name,True)

    def GetOpened(self):
        """ Return opend window instance in dictionary.
        
        :return: dictionary of window instance 
        :rtype: obj
        """
        windic={}
        for nam, win in self.openwindic.iteritems():
            if not win: continue
            windic[nam]=win
        return windic

    def GetOpenedName(self):
        """ Return opened window names.
        
        :return: list of window name 
        :rtype: lst
        """
        names=[]
        for nam, win in self.openwindic.iteritems():
            if not win: continue
            names.append(nam)
        return names   
 
    def GetWin(self,label):
        if self.openwindic.has_key(label): return self.openwindic[label]
        elif label == 'Show ToolsWin':
            return wx.FindWindowByName('FUTOOLSWIN')
        else: 
            if wx.FindWindowByName(label): return wx.FindWindowByName(label)
            else: return None
    
    def GetOpenedWin(self):
        return self.openwindic
        
    def SetWin(self,winlabel,winobj):
        self.openwindic[winlabel]=winobj
        
    def SetOpenWin(self,winlabel,win):
        """
        
        :param obj win: window object
        """
        self.openwin=win
        self.winlabel=winlabel
    
    def ClearOpenWin(self):
        self.openwin=None
        self.winlabel=''
            
    def ResetSubWin(self):
        pass
               
    def CloseAll(self):
        # ??? except mousemodewin , molchoicewin
        pass

    def CheckMenuItem(self,winlabel,on):
        """ Check/uncheck 'winlabel' menu item.
        
        :param str winlabel: window label,
        :param bool on: Trur for check, False for uncheck """
        self.model.menuctrl.CheckMenu(winlabel,on)
 
    def Open(self,winlabel,openmethod=None):
        """ open subwindow named 'winlabel' which is the same as menu item label.
        
        :param str winlabel: name of subwindow """
        # default position of subwindow
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        nwin1=len(self.openwindic)-1
        winpos=pos; winpos[0] += size[0]+20*nwin1; winpos[1] += 50+20*nwin1
        # check opened
        if self.IsOpened(winlabel):
            win=self.openwindic[winlabel]
            if win != None:
                try: win.Show()
                except: pass
                try: win.SetFocus()
                except: pass
                return
        # open 'winlabel' window
        if openmethod: 
            # open method in external script
            win=openmethod()
        elif winlabel == 'Open ControlWin':
            win=self.OpenControlWin(winlabel)
        elif winlabel == 'Open PyShell':
            win=self.OpenPyShell(winlabel)
        elif winlabel == 'Open MatPlotLibWin':
            win=self.OpenMatPlotLibWin(winlabel)
        elif winlabel == 'Open EasyPlotWin':
            win=self.OpenEasyPlotWin(winlabel)
        elif winlabel == 'Open ScriptEditor':
            win=self.OpenTextEditor(winlabel)
        elif winlabel == 'Show ToolsWin':
            win=self.OpenToolsWin(winlabel)
        elif winlabel == "FU Document":
            win=self.OpenDocument(winlabel)
        elif winlabel == 'Programming tutorial':
            win=self.OpenProgrammingGuide(winlabel)
        elif winlabel == 'Key bindings':
            win=self.OpenKeyBindingsHelp(winlabel)
        elif winlabel == "User's guide":
            win=self.OpenUsersGuide(winlabel)
        elif winlabel == 'Tutorial':
            win=self.OpenTutorialWin(winlabel)
        elif winlabel == 'Customize':
            win=custom.Customize_Frm(self.mdlwin,-1,self.model,winpos,winlabel)            
        elif winlabel == 'Frame data':
            win=subwin.FrameData_Frm(self.mdlwin,-1,winpos,winlabel)
        elif winlabel == 'PDB data':
            win=subwin.PDBData_Frm(self.mdlwin,-1,winpos,winlabel)
        #elif winlabel == 'Model builder':
        #    win=subwin.ModelBuilder_Frm(self.mdlwin,-1,winpos,winlabel)
        elif winlabel == 'Open Torsion Editor':
            #win=subwin.ZMatrixPanel_Frm(self.mdlwin,-1,self.model,winpos,winlabel)
            win=build.TorsionEditor_Frm(self.mdlwin,-1,self.model,winpos,
                                        winlabel)
        elif winlabel == 'Tree': # tree selector panel
            win=self.OpenTreeSelector(winlabel)
        elif winlabel == 'Name/Number': # Name/Number selector panel
            win=self.OpenNameSelector(winlabel)
        elif winlabel == 'One-by-One':
            win=subwin.OneByOneViewer_Frm(self.model,-1)
            #win=self.OpenOneByOneViewer(winlabel)
        elif winlabel == 'Immerse in box waters':
            win=self.OpenWaterBoxPanel(winlabel)
        #if winlabel == 'AddHydrogenWin':
        elif winlabel == 'MouseOperationModeWin':
            win=self.OpenMouseOperationModeWin(winlabel)
        elif winlabel == 'SlideShowCtrl':
            win=subwin.SlideShowCtrl_Frm(self.model,-1)
            #win=self.OpenSlideShowCtrl(winlabel)
        #elif winlabel == "Mutate AA residue":
        #    win=self.OpenMutateAAResWin(winlabel)          
        elif winlabel == 'HisFormChanger':
            win=subwin.HisFormChanger_Frm(self.model,-1,winlabel=winlabel)        
        elif winlabel == 'MutateResidue':
            win=build.MutateAAResudes_Frm(self.model,-1,winlabel=winlabel)
        elif winlabel == 'RotateBond':
            win=build.RotateBond_Frm(self.model,-1,winlabel=winlabel)
        elif winlabel == 'BoxWater':
            win=build.WaterBox_Frm(self.model,-1,winlabel=winlabel)
        elif winlabel == 'ZMatrixEditor':
            win=build.ZMatrixEditor_Frm(self.model,-1,winlabel=winlabel)
        elif winlabel == 'ModelBuilder':
            win=build.ModelBuilder_Frm(self.model,-1)
        elif winlabel == 'PolypeptideBuilder':
            win=build.Polypeptide_Frm(self.model,-1)
        # Utility
        elif winlabel == 'SplitJoin':
            win=build.SplitAndJoinPDBFile_Frm(self.model,-1)
        #
        elif winlabel == 'Tests':
            pass
            #win=subwin.Tests_Frm(self.mdlwin,-1,winpos,winlabel)
        else:
            if self.openwin and self.winlabel != '': 
                win=self.openwin; winlabel=self.winlabel
                self.openwin=None; self.winlabel=''
            else:
                mess='Open window method is not defined.'
                self.model.ConsoleMessage(mess)
                return
        #win=subwin.ControlPanel_Frm(self.mdlwin,-1,self.model,winpos,winlabel)
        #win.Show()
        self.CheckMenuItem(winlabel,True)  
        if win != None: self.openwindic[winlabel]=win
        # attach icon
        iconfile=const.FUMODELICON #self.model.setctrl.GetFile('Icons','fumodel.ico')
        try: 
            icon=wx.Icon(iconfile,wx.BITMAP_TYPE_ICO)
            win.SetIcon(icon)
        except: pass
       
    def Close(self,winlabel): 
        """ close subwindow named 'winlabel' which is the same as menu item label.
        
        :param str winlabel: name of subwindow """
        #
        mess='fum.winctrl.Close("'+winlabel+'")'
        if self.model.setctrl.GetEcho(): self.model.ConsoleMessage(mess)
        if lib.LOGGING: self.model.WriteLogging(mess)
        #
        try: self.openwindic[winlabel].Destroy()
        except: pass
        
        try: del self.openwindic[winlabel]
        except: pass
        self.CheckMenuItem(winlabel,False) 

    def Hide(self,winlabel):  
        try:
            self.openwindic[winlabel].Hide()
            self.CheckMenuItem(winlabel,False) 
        except: pass

    def Resize(self,winlabel):
        shlwin=self.GetWin(winlabel)
        size=shlwin.GetSize()
        pos=shlwin.GetPosition()
        if winlabel == 'Open PyShell':
            text=shlwin.shell.GetText()
            lastpos=shlwin.shell.GetLastPosition() #GetLineCount()
            self.Close(winlabel)
            self.Open(winlabel)
            shlwin=self.GetWin(winlabel)
            shlwin.SetSize(size)
            shlwin.shell.SetText(text)
            shlwin.shell.ShowPosition(lastpos-10)        #
        shlwin.Update()
           
    def XXOpenSlideShowCtrl(self,winlabel):
        [x,y]=self.mdlwin.GetScreenPosition()
        [w,h]=self.mdlwin.GetSize() #GetClientSize()
        xpos=w+10 #-232
        position=[0,50]

        winpos=[x+xpos+position[0],y+position[1]]
        
        winsize=[]
        win=subwin.SlideShowCtrl_Frm(self.mdlwin,-1,winpos,winsize)
        return win
    
    def OpenControlWin(self,winlabel):
        """ Open control panel(ControlWin). 
        
        :param str winlabel: window label-'Open ControlWin'
        """
        #if self.IsOpened('*ControlWin'): return
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        winsize=lib.WinSize((155,330))
        winpos=[0,0]; winpos[0]=pos[0]+size[0]; winpos[1]=pos[1]+80           
        if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+75
        winpos=tuple(winpos)
        win=subwin.ControlPanel_Frm(self.mdlwin,-1,self.model,winpos,winlabel) #,self.openwindic,wrkmolnam,winpos)
        win.Show()
        #self.openwindic.Setopenedflag('controlpanel',True)
        #self.model.menuctrl.CheckMenu('Open ControlWin',True)
        #self.model.menuctrl.CheckMenu('Open ControlWin',True)
        #self.mdlwin.SetWinOpen('ContrilWin',True)
        return win
        #self.openwindic['*ControlWin']=self.ctrlwin
      
    def OpenToolsWin(self,winlabel):
        """ Open console application tools panel(ToolsWin). """
        self.model.Message('Sorry, the function is not implemented yet.',0,'')
        win=None
        return win

    def OpenPyShell(self,winlabel):
        """ Open pyshell window(PyCrust). 
        
        :param str winlabel: window label-'Open PyShell'
        """
        title='PyShell in FU'
        winsize=self.model.setctrl.GetParam('shell-win-size')
        winpos=self.model.setctrl.GetParam('shell-win-pos')
        if len(winpos) <= 0: 
            size=self.mdlwin.GetSize()
            if lib.GetPlatform() == 'WINDOWS': size[1] -= 20
            pos=self.mdlwin.GetScreenPosition()
            winpos=[0,0]; winpos[0]=pos[0]; winpos[1]=pos[1]-winsize[1]
            if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+25
        parent=self
        #if self.fumode == -1: parent=None
        if self.pycrustshell: 
            win=wx.py.crust.CrustFrame(parent=self.mdlwin,pos=winpos,
                                       size=winsize,title=title,
                style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)          
        else: win=wx.py.shell.ShellFrame(parent=self.mdlwin,pos=winpos,
                                         size=winsize,title=title,
                style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER)
        win.Bind(wx.EVT_CLOSE,self.OnClosePyShell)
        if self.model.setctrl.GetParam('redirect'): 
            win.shell.redirectStdout(True) # truble occurd in Windows. so, moveed to Model.OpenMdlWin().
            win.shell.redirectStderr(True)
        win.Show()
        return win

    def OnClosePyShell(self,event):
        """ Close PyShell window
        
        :param evt event: Menu event
        """
        winlabel='Open PyShell'
        mdlwin=wx.FindWindowByName('FUMDLWIN')
        if mdlwin.IsShown(): self.Close(winlabel)
        else: 
            #self.model.ChangeFUMode(0)
            self.model.mdlwin.OnCloseFromFUTools()
        
    def OpenEasyPlotWin(self,winlabel):
        """ open easy plot window(EasyPlotWin). """
        if self.IsOpened('Open EasyPlotWin'):
            self.easypltwin.SetFocus(); return
        winpos=[0,0]; winsiz=[750,300]
        title='Plot Output'
        win=subwin.ExecProg_Frm(self.mdlwin,-1,self.model,winpos,winsiz,title,
                                winlabel)
        # remove several menu items
        win.menubar.Remove(3) # remove two succesive items
        win.menubar.Remove(3) # need this
        menu=win.menubar.GetMenu(0)
        itemtxt=["Save log as","Output on display","Load output file",
                 "View output file"]
        for txt in itemtxt:
            id=menu.FindItem(txt)
            item=menu.FindItemById(id)
            menu.DeleteItem(item)     
        items=menu.GetMenuItems()
        nsep=4; isep=0
        for item in items:
            if item.IsSeparator():
                menu.RemoveItem(item); isep += 1
                if isep == nsep: break
        #
        win.Show()
        return win
        #self.openwindic['*EasyPlotWin']=self.easypltwin

    def OpenMatPlotLibWin(self,winlabel):
        """ open MatPlotLib window(MatPlotLibWin). """
        if self.IsOpened('Open MatPlotLibWin'):
            self.mpl.SetFocus(); return
        parentpos=self.mdlwin.GetPosition()
        parentsize=self.mdlwin.GetSize()
        winpos=[parentpos[0]+160,parentpos[1]+parentsize[1]-10] #+50]
        winsize=lib.WinSize((640,500))
        win=subwin.MatPlotLib_Frm(self.mdlwin,-1,self.model,winpos,winsize,
                                  winlabel)
        win.Show()
        return win
        #self.model.menuctrl.CheckMenu('Open MatPlotLib',True)
        #self.openwindic['*MatPlotLibWin']=self.mplwin

    def OpenChildMolView(self):
        #if self.openwindic.has_keyCtrlFlag('childviewwin'):
        #if self.mdlwin.IsWinOpen('ChildViewWin'):
        if self.IsOpened('ChildViewWin'):
            self.childwin.SetFocus(); return
        #
        self.childwin=subwin.ChildMolView_Frm(self.mdlwin,-1,self.model)
        self.childwin.Show(True)
        self.childwin.Redraw()
        self.child=1; self.shwsync=0
        self.openwindic['ChildViewWin']=self.childwin

    def XXFragmentAttribPanel(self):
        """ open layer assginment panel(LayerWin)."""
        if self.IsOpened('FragAttribWin'):
            try: self.layerwin.SetFocus()
            except: pass
            return
        try:
            self.model.SaveLayerData(True)
            self.model.SaveAtomColor(True)
        except: pass
        #winpos=self.mdlwin.GetScreenPosition()
        #winpos=[winpos[0]-10,winpos[1]+80]
        self.layerwin=frag.FragmentAttribSetting_Frm(self.model,-1,self.model)
        self.layerwin.Show()
        self.openwindic['FragAttribWin']=self.layerwin
        try: self.model.SaveAtomColor(True)
        except: pass

    def XXCloseFragmentAttribPanel(self):
        try: del self.openwindic['FragAttribWin']
        except: pass
        self.model.SaveAtomColor(False)
        
    def OpenAtomTypePanel(self):
        if self.IsOpened('AtmtypWin'):
            self.atmtypwin.SetFocus(); return
        winpos=self.mdlwin.GetScreenPosition()
        winpos=[winpos[0]-10,winpos[1]+80]
        self.atmtypwin=subwin.AssignAtomType_Frm(self.mdlwin,-1,self.model,
                                                 winpos)
        self.atmtypwin.Show()
        self.openwindic['AtmtypWin']=self.atmtypwin

    def CloseAtomTypePanel(self):
        self.openwindic['AtmtypWin']=None
              
    def OpenAtomChargePanel(self):
        if self.IsOpened('AtomChargeWin'):
            self.atmchgwin.SetFocus(); return
        winpos=self.mdlwin.GetScreenPosition()
        winpos=[winpos[0]-10,winpos[1]+80]
        self.atmchgwin=subwin.AtomChargeInput_Frm(self.mdlwin,-1,self,winpos)
        self.atmchgwin.Show()
        self.DrawFormalCharge(True)
        self.openwindic['AtomChargeWin']=self.atmchgwin

    def CloseAtomChargePanel(self):
        self.openwindic['AtomChargeWin']=None
        
    def OpenTreeSelector(self,winlabel):
        """ open tree selector panel(TreeSelWin). """
        #if self.IsOpened('TreeSelWin'):
        #    self.treewin.SetFocus(); return
        winpos=self.mdlwin.GetPosition()
        winpos[0]=winpos[0]-150; winpos[1]=winpos[1]-50
        if winpos[0] < 10: winpos[0]=10
        if winpos[1] < 10: winpos[1]=10
        win=subwin.TreeSelector_Frm(self.mdlwin,-1,self.model,winpos,winlabel) #,self,self.openwindic,wrkmolnam)
        win.Show()
        return win
        #self.openwindic['TreeSelWin']=self.treewin
    def OpenMutateAAResWin(self,winlabel):
        winpos=[]
        win=build.MutateAAResudes_Frm(self.mdlwin,-1,winpos)   
        win.Show()
        return win
    
    def OpenMouseOperationModeWin(self,winlabel):
        #winpos=self.model.mdlwin.ScreenToClient(wx.GetMousePosition())
        winpos=wx.GetMousePosition()
        winpos[0] -= 20; winpos[1] -= 20
        menulst,tipslst=self.mousectrl.GetModelModeWinItems()
        win=subwin.PopupWindow_Frm(self.mdlwin,-1,self.model,winpos,winlabel,
                                   menulst,tipslst)
        win.Show()
        return win

    def OpenCreateProjectWin(self,winlabel):
        """ Open project path window. """
        winpos=[-1,-1]
        win=subwin.CreateProject_Frm(self.mdlwin,-1,self.model,winpos,winlabel) #,self,self.openwindic,wrkmolnam)
        win.Show()
        return win
        #self.openwindic['NameSelWin']=self.namewin
            
    def OpenNameSelector(self,winlabel):
        """ open name/number selector panel(NameSelWin). """
        # winpo(lst): [xpos(int),ypos(int)]
        #if self.IsOpened('NameSelWin'):
        #    self.namewin.SetFocus(); return
        winpos=self.mdlwin.GetPosition()
        winpos[0]=winpos[0]-170; winpos[1]=winpos[1]-50
        if winpos[0] < 10: winpos[0]=10
        if winpos[1] < 10: winpos[1]=10
        win=subwin.NameSelector_Frm(self.mdlwin,-1,self.model,winpos,winlabel) #,self,self.openwindic,wrkmolnam)
        win.Show()
        return win
        #self.openwindic['NameSelWin']=self.namewin

    def XXOpenOneByOneViewer(self,winlabel):
        # Open OneByOneSelector panel
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        winsize=lib.WinSize((155,116))
        winpos=[0,0]; winpos[0]=pos[0]+size[0]-80; winpos[1]=pos[1]+100           
        if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+55
        win=subwin.OneByOneViewer_Frm(self.model,-1,winpos) #,self,self.openwindic,wrkmolnam)
        win.Show()
        return win

    def OpenDocument(self,winlabel):
        fudocsdir=self.model.setctrl.GetDir('FUdocs')
        filename=os.path.join(fudocsdir,"program-guide//document//index.html")
        filename=filename.replace('\\','//')
        if not os.path.exists(filename):
            mess='HTML file not found. file='+filename
            lib.MessageBoxOK(mess,'ViewFUDocument')
            return
        lib.ViewHtmlFile(filename)
        return None

    def OpenProgrammingGuide(self,winlabel):
        fudocsdir=self.model.setctrl.GetDir('FUdocs')
        filename=os.path.join(fudocsdir,
                    "program-guide//wxfu-tutorial//wxfu-tutorial.html")
        filename=filename.replace('\\','//')
        if not os.path.exists(filename):
            mess='HTML file not found. file='+filename
            lib.MessageBoxOK(mess,'ViewFUDocument')
            return
        lib.ViewHtmlFile(filename)
        return None

    def OpenTutorialWin(self,winlabel):
        """ not used. see model.helpctrl instance """ 
        #pyshell=self.model.winctrl.GetWin('Open PyShell')
        pos=self.mdlwin.GetScreenPosition()
        #winpos=[pos[0]+20,pos[1]+20]; winsize=[500,300]; tw=140; 
        #                         title='ToolsHelp'
        winlabel='Tutorial'
        title='Tutorial'; rootname='Tutorial guide'
        viewer='html'
        if lib.GetPlatform() != 'WINDOWS': viewer='text'
        win=subwin.Tutorial_Frm(self.model.mdlwin,-1,[],[],winlabel=winlabel,
                                title=title,rootname=rootname,viewer=viewer)        
        return win
    
    def OpenKeyBindingsHelp(self,winlabel):
        docdir=self.model.setctrl.GetDir('FUdocs')
        docdir=os.path.join(docdir,'fumodel')
        keybindfile=os.path.join(docdir,'keybindings.txt')
        title='Key bindings'
        win=subwin.TextViewer_Frm(self.model.mdlwin,winsize=[530,400],
                                  title=title,textfile=keybindfile)
                 
    def OpenUsersGuide(self,winlabel):
        helpdir=self.model.setctrl.GetDir('FUdocs')
        helpdir=os.path.join(helpdir,'users-guide')
        pltfrm=lib.GetPlatform()
        if pltfrm == 'MACOSX' or pltfrm == 'LINUX':
            contentsfile='users-guide.html'
            contentsfile=os.path.join(helpdir,contentsfile)
        else:
            contentsfile='users-guide.contents'
            contentsfile=os.path.join(helpdir,contentsfile)
        if not os.path.exists(contentsfile):
            mess='Not found contentsfile='+contentsfile
            lib.MessageBoxOK(mess,'Model(UsersGuide')
            return None
        if pltfrm == 'MACOSX' or pltfrm == 'LINUX':
            win=None
            lib.ViewHtmlFile(contentsfile)
        else:
            winpos=[]; winsize=[]; treewidth=200
            title="FU User's Guide"; root="User's Guide"
            expandall=False; winlabel="User's guide"
            win=subwin.HtmlViewerWithTreeIndex_Frm(self.mdlwin,-1,title=title,
                      treewidth=treewidth,winlabel=winlabel,rootname=root,
                      contentsfile=contentsfile,expandall=expandall)
        return win

    def OpenRadiusSelector(self):
        if self.IsOpened('RadiusSelWin'):
            self.radiwin.SetFocus(); return
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        winsize=lib.WinSize((155,125))
        winpos=[0,0]; winpos[0]=pos[0]+size[0]-60; winpos[1]=pos[1]+80           
        if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+35
        winpos=tuple(winpos)
        self.radiwin=subwin.RadiusSelector_Frm(self.mdlwin,-1,self.model,
                                               winpos)
        #,self,self.openwindic,wrkmolnam)
        self.radiwin.Show()
        self.openwindic['RadiusSelWin']=self.radiwin

    def OpenRenameGroupWin(self):
        if self.IsOpened('RenameGrpWin'):
            self.rengrpwin.SetFocus(); return
        self.rengrpwin=subwin.GroupRename_Frm(self.mdlwin,-1,self.model) #,self.openwindic,wrkmolnam)
        self.rengrpwin.Show()
        self.openwindic['RenameGrpWin']=self.rengrpwin

    def OpenJoinGroupWin(self):
        if self.IsOpened('JoinGrpWin'):
            self.joingrpwin.SetFocus(); return
        self.joingrpwin=subwin.GroupJoin_Frm(self.mdlwin,-1,self.model) #,self.openwindic,wrkmolnam)
        self.joingrpwin.Show()
        self.openwindic['JoinGrpWin']=self.joingrpwin

    def OpenAddHydrogenWin(self,scrdir=''):
        #if self.IsOpened('AddHydrogenWin'):
        #    self.addhydrogenwin.SetFocus(); return
        if len(scrdir) <= 0: scrdir=self.mdlwin.model.setctrl.GetDir('Scratch')
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        winsize=lib.WinSize((400,400))
        winpos=[0,0]; winpos[0]=pos[0]+size[0]-100; winpos[1]=pos[1]+120           
        if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+75
        winpos=tuple(winpos)
        win=subwin.HydrogenAddition_Frm(self.mdlwin,-1,self.model,winpos,
                                        scrdir) #self,self.openwindic,wrkmolnam,winpos,savfile)
        win.Show()
        #self.watboxwin.MakeModal(True)
        self.openwindic['AddHydrogenWin']=win

    def CloseAddHydrogenPanel(self):
        try: del self.openwindic['AddHydrogenWin']
        except: pass
        
    def OpenWaterBoxPanel(self,winlabel):
        #if self.IsOpened('WaterBoxWin'):
        #    self.watboxwin.SetFocus(); return
        pos=self.mdlwin.GetScreenPosition()
        size=self.mdlwin.GetClientSize()
        winsize=lib.WinSize((400,400))
        winpos=[0,0]; winpos[0]=pos[0]+size[0]-100; winpos[1]=pos[1]+120           
        if winpos[1] <= 0: winpos[1]=pos[1]+size[1]+75
        win=build.WaterBox_Frm(self.mdlwin,-1,self.model,winpos,winlabel)
        win.Show()
        return win
        #self.watboxwin.MakeModal(True)
        #self.openwindic['WaterBoxWin']=self.watboxwin
    def OpenTextEditor(self,winlabel):
        #retmethod=self.ReturnFromTextEditor
        winpos=[0,0] #wx.GetMousePosition()
        winsize=[480,300]
        parent=self.mdlwin
        retmethod=None; mode='Edit'; title=winlabel
        text=''
        win=subwin.TextEditor_Frm(parent,-1,winpos,winsize,title,text,
                                  retmethod,mode=mode,scriptmode=True)
        win.Show()
        return win
        
    def OpenExePrgWin(self):
        if self.IsOpened('ExeProgWin'): return
        winpos=[0,0]; winsiz=[750,300]
        title='Execute Program'
        self.exeprgwin=subwin.ExecProg_Frm(self.mdlwin,-1,self.model,winpos,
                                           winsiz,title)
        self.exeprgwin.Show()
        self.openexeprgwin=True
        self.openwindic['ExeProgWin']=self.exeprgwin

    def CloseExeProgWin(self):
        try: 
            self.openwindic['ExeProgWin'].Destroy()
            self.openwindic['ExeProgWin']=None
        except: pass

    def OpenFragmentBDAWin(self):
        if self.IsOpened('FragBDAWin'):
            self.bdawin.SetFocus(); return
        self.bdawin=subwin.FragmentByBDA_Frm(self.mdlwin,-1)
        self.openwindic['FragBDAWin']=self.bdawin
        self.bdawin.Show()

# molecules
class MolCtrl():
    def __init__(self,parent):
        self.model=parent
        #self.mdlwin=parent.mdlwin
        self.classnam='MolCtrl'
        #
        #self.mollst=[] # the list stores fuMole instamces
        #self.molnamlst=[]
        #self.moldic={} #{'molnam:inxed, ...}
        self.molnamlst=[]
        self.mollst=[]
        self.curmol=-1 # the index of current active molecule
        self.seriesmollst=[]
        # default atom params
        #self.curmolnam=''
        #self.mhtdatadic={}
        #self.bdadatadic={}
        #self.files=[]
    def IsExist(self,molnam):
        if molnam in self.molnamlst: return True
        else: False
    
    def SetSeriesMolList(self,seriesmollst):
        self.seriesmollst=seriesmollst
        
    def GetSeriesMolList(self):
        return self.seriesmollst
        
    def Add(self,mol,mess=True):
        # mol(ins): Molecule instance
        if mess:
            if mol.name in self.molnamlst:
                mess='Molecule: '+mol.name+' exists.'
                self.model.Message2(mess)
                mess=mess+' Switch to current?'
                retcode=lib.MessageBoxYesNo(mess,"")
                if retcode:
                    self.curmol=self.molnamlst.index(mol.name)
                    self.SwitchCurMol(self.curmol,True,True)
                #dlg.Destroy()
                return
            #
        self.molnamlst.append(mol.name)
        self.mollst.append(mol)
        self.curmol=len(self.molnamlst)-1
        # auto open molwin
        if self.model.mdlwin.molchoice.open:
            # add item to molchoice box and set select item
            self.model.mdlwin.molchoice.Add(mol.name)
            self.SetMolSelection(mol.name)
        else: self.AutoOpenMolChoiceWin()      

    def Del(self,idx):
        # idx(int): mol index
        if idx < 0 or idx >= len(self.molnamlst):
            mess='Molecule index is out of range.'
            self.ConsoleMessage(self.WarningMess('Del',mess))
            return
        else: 
            try: self.model.mdlwin.molchoice.Del(idx)
            except: pass
            del self.molnamlst[idx]
            del self.mollst[idx]
            self.curmol=idx-1
            if self.curmol < 0: self.curmol=len(self.molnamlst)-1
            if self.curmol < 0: self.ClearMol()
            # auto open molwin                      
            if self.model.mdlwin.molchoice.open and self.curmol >= 0:
                self.selectmol=self.molnamlst[self.curmol]
                self.model.mdlwin.molchoice.SetSelection(self.curmol)
            if self.model.mdlwin.GetAutoOpenMolWin(): 
                self.AutoOpenMolChoiceWin()
  
    def SetMolSelection(self,name):
        if self.model.mdlwin.molchoice.open:
            #if not self.mdlwin.cbwin.cboxmol: return
            #self.mdlwin.molchoice.Add(name)
            self.model.mdlwin.molchoice.SetMolSelection(name)
    
    def DelByName(self,molnam):
        # molnam(str): molecule name
        try:
            idx=self.molnamlst.index(molnam)
            self.Del(idx)
        except:
            mess=molnam+' is not found.'
            self.ConsoleMessage(self.WarningMess('DelByName',mess))
        
    def ClearMol(self):
        # clear all mol instance
        self.molnamlst=[]; self.mollst=[]; self.curmol=-1
        # auto open molwin
        if self.model.mdlwin.molchoice.open:
            self.model.mdlwin.molchoice.Clear()
        self.AutoOpenMolChoiceWin()
     
    def ClearMht(self):
        # clear mhtdic
        self.mhtdatadic.clear()
    
    def ChangeName(self,oldnam,newnam):
        # oldmolnam(str): old mole name
        # newmolnam(str): new mole name
        try:
            idx=self.molnamlst.index(oldnam)
            self.molnamlst[idx]=newnam
            self.mollst[idx].name=newnam
            if self.model.mdlwin.molchoice.open:
                self.model.mdlwin.molchoice.Rename(oldnam,newnam) 
        except:
            mess=oldnam+ ' is not found.'
            self.Message(mess,0,'')
        
    def GetMolIndex(self,molnam):
        # molnam(str): name of mole
        # ret idx(int): index
        try: idx=self.molnamlst.index(molnam)
        except: idx=-1
        return idx

    def GetCurrentMol(self):
        # ret curmol(int): current mol index
        # ret mol(ins): corrent mol instance
        if self.curmol < 0 or self.curmol >= len(self.molnamlst):
            return -1,molec.Molecule(self.model)
        else: return self.curmol,self.mollst[self.curmol]

    def GetCurrentMolIndex(self):
        return self.curmol
    
    def GetMol(self,idx):
        # idx(int): index in mollst
        # ret molnam[str]: mol name
        if idx < 0 or idx >= len(self.molnamlst): 
            return molec.Molecule(self.model)
        else: return self.mollst[idx]
 
    def GetMolNameList(self):
        # ret molnamlst(lst): list of mole names
        return self.molnamlst

    def ResetMol(self,molobj):
        self.mollst[self.curmol]=molobj
    
    def SetMol(self,idx,mol):
        """
        
        :param obj mol: Molecule object
        """
        try: self.mollst[idx]=mol
        except:
            mess="Failed to set mol. wrong index="+str(idx)
            lib.MessageBoxOK(mess,'molctrl.SetMol')
        
    def GetNumberOfMols(self):
        # ret nmole(int): number of moles in moldic
        return len(self.molnamlst)

    def GetMolName(self,idx):
        # idx(int): index
        # ret molnam(str): mole name
        if idx < 0 or idx >= len(self.molnamlst): return ''
        return self.molnamlst[idx]

    def GetCurrentMolName(self):
        # ret molnam(str): current mol name
        if self.curmol >= 0: return self.molnamlst[self.curmol]
        else: return ''

    def SwitchCurMol(self,curmol,fit,drw):
        """ change current molecue
        
        :param int curmol: molecule number to be set current
        :param bool fit: True for fit screen, False for do not
        :see: 'fumodel.Moleclue.SwitchMol' method
        """
        # switch currrent molecule(wrk)
        # curmol(int): index of molecule
        if curmol < 0: return
        #if curmol == self.curmol: return # comment out for draw project molecules 06Jan2015(kk)
        self.curmol=curmol
        #mol=self.GetMol(self.curmol)
        #self.model.SwitchMol(self.curmol,mol,fit,drw)
        self.model.SwitchMol(self.curmol,fit,drw)
        molnam=self.GetCurrentMolName()
        self.SetMolSelection(molnam)

    def AutoOpenMolChoiceWin(self):
        # open/close molchoice window
        if self.GetNumberOfMols() > 1:
            if self.model.mdlwin.IsAutoOpenMolWin() and \
                                     not self.model.mdlwin.IsMolWinOpen():
                self.model.mdlwin.SetMolWinFlag(True)
                self.model.mdlwin.OpenMolChoiceWin()
        else:
            if self.model.mdlwin.IsAutoOpenMolWin() and \
                                     self.model.mdlwin.IsMolWinOpen():
                self.model.mdlwin.SetMolWinFlag(False)
                self.model.mdlwin.CloseMolChoiceWin()

    def WarningMess(self,methodnam,mess):
        mess='Warning('+self.classnam+'('+methodnam+'):'+mess

    def ConsoleMessage(self,mess):
        # mess(str): see fumodel.ConsoleMessage()
        try: self.model.ConsoleMessage(mess)
        except: print mess

    def Message(self,mess,dev,color):
        # mess(str),dev(int),color(lst): see fumodel.Message()
        try: self.model.Message(mess,dev,color)
        except: print mess
    

class HelpCtrl(object):
    """ Help and tutorial controller 
    
    :Note: Assumes that the subdirectries in FUDATASET/FUdocs haveing
    contents file(\'.contents) is a help directory. The subdirectory name is used
    as helpname. 
    The structure of the help directory is assumed to be,
    ./directoryname(used as the helpname)
      xxxx.contents(contents file)
         ./html(html directory)
             xxxx.html(html file)
         ./img (image directory)
             xxxx.gif (image file used in html file)
         ./pyfile(Script and demo files directory)
             xxxx.demo (demo script file)
             xxxx.py (tutorial script file) 
    """
    def __init__(self,parent,parentwin=None):
        self.model=parent
        self.mdlwin=self.model.mdlwin
        self.parentwin=parentwin
        #
        self.cntfiledic={} # {dirname:filename,...}
        self.cntfiledic=self.MakeContentsFileDic()
        #
        self.helpwin=None
        self.tutwin=None
        self.scriptwin=None
    
    def MakeContentsFileDic(self):
        """ Search contents files(.contents) in subdirectory of 
        FUDATASET/FUdocs directory
        
        :return: cntfiledic(dic) - {dirname(str):filename(str),..}   
        """
        docdir=self.model.setctrl.GetDir('FUdocs')
        cntfiledic={}
        dirlst=lib.GetDirectoriesInDirectory(docdir)
        if len(dirlst) <= 0: return
        for dirname in dirlst:
            helpname=os.path.split(dirname)[1]
            filelst=lib.GetFilesInDirectory(dirname)
            for filename in filelst:
                base,ext=os.path.splitext(filename)
                if ext == '.contents': cntfiledic[helpname]=filename        
        return cntfiledic
        
    def SetContentFile(self,helpname,cntfile):
        """ appned contentsfile
        
        :param str helpname: helpname
        :param str cntfile: full path name of contentsfile
        """
        self.helpname=helpname
        self.cntfile=cntfile
        if os.path.exists(cntfile):
            self.cntfiledic[helpname]=cntfile
        else:
            mess='Not found contents file='+cntfile
            lib.MessageBoxOK(mess,'HelpCtrl(SetContentsFile')
        
    def Help(self,helpname):
        """ Open help window
        
        :param str helpname: helpname(the firectory name in FUDATASET//FUdocs
        :param str item: items defined in helpname.contents in the helpname firctory
        """
        
        self.helpwin=self.OpenHelp(helpname)
        
    def Tutorial(self,helpname,rootname='',navi=True,expandall=False):
        """ Open tutorial panel
        
        :param str helpname: helpname
        """
        viewer='html'
        if lib.GetPlatform() == 'MACOSX': viewer='text'
        self.tutwin=self.OpenTutorial(helpname,rootname=rootname,
                                         navi=navi,viewer=viewer,
                                         expandall=expandall)
    
    def GetHtmlFile(self,helpname):
        """ Get help HTML file
        
        :params str helpname: helpname
        :return: htmlfile (The first html file of helpname group)
        """
        htmlfile=''
        if not self.cntfiledic.has_key(helpname): return ''
        cntfile=self.cntfiledic[helpname]
        contentslst,textdic,htmldic= \
                            rwfile.ReadContentsFile(cntfile,retscript=False)
        if htmldic.has_key(helpname): htmlfile=htmldic[helpname]
        #elif htmldic.has_key(item): htmlfile=htmldic[item]
        else: return ''
        helpdir=lib.GetFileNameDir(cntfile)
        htmlfile=lib.PathJoin(helpdir,htmlfile)   
        if not os.path.exists(htmlfile): return ''
        if lib.GetPlatform() == 'WINDOWS': htmlfile=htmlfile.replace('//','\\')
        return htmlfile
            
    def OpenHelp(self,helpname):
        """ Open help window
        
        :param str helpname: helpname
        """
        if self.helpwin:
            [wd,hd]=self.helpwin.GetSize()
            self.helpwin.Destroy()
        htmlfile=self.GetHtmlFile(helpname)
        if htmlfile == '':
            mess='Not found Help document='+helpname #htmlfile
            lib.MessageBoxOK(mess,helpname)
            return
        wd=640; ysize=400; dx=0; dy=0
        winobj=self.parentwin
        if not winobj: 
            winobj=self.mdlwin
            dx=20; dy=80
        [x,y]=winobj.GetPosition()
        [w,h]=winobj.GetSize()
        if dy == 0: 
            dy=h; dx=0
        winpos=[x+dx,y+dy]; winsize=[wd,ysize]
        #selname=self.treepan.GetItemText(self.treepan.GetSelection())
        title='Help: '+helpname
        helpwin=subwin.HtmlViewer_Frm(winobj,winpos=winpos,winsize=winsize,
                                      htmlfile=htmlfile,fumodel=self.model)

        return helpwin

    def GetTutorialContents(self,helpname):
        """ Get tutorial contents including symbolic helpname
        
        :param str helpname: helpname
        """
        contentslst=[]; textdic={}; htmldic={}; scriptdic={}; demodic={}
        if self.cntfiledic.has_key(helpname):
            cntfile=self.cntfiledic[helpname]
            contentslst,textdic,htmldic,scriptdic,demodic= \
                                rwfile.ReadContentsFile(cntfile,retscript=True)
            helpdir=lib.GetFileNameDir(cntfile)
            textdic=self.SetFullPathNameInFileDic(helpdir,textdic)
            htmldic=self.SetFullPathNameInFileDic(helpdir,htmldic)
            scriptdic=self.SetFullPathNameInFileDic(helpdir,scriptdic)
            demodic=self.SetFullPathNameInFileDic(helpdir,demodic)
        #
        cntlst=[]
        for i in range(len(contentslst)):
            lst=contentslst[i]
            name=lst[0]
            if name[:1] == '@':
                tname=name[1:]
                if not self.cntfiledic.has_key(tname): continue
                cfile=self.cntfiledic[tname]
                clst,tdic,hdic,sdic,ddic= \
                                rwfile.ReadContentsFile(cfile,retscript=True)
                helpdir=lib.GetFileNameDir(cfile)
                tdic=self.SetFullPathNameInFileDic(helpdir,tdic)
                hdic=self.SetFullPathNameInFileDic(helpdir,hdic)
                sdic=self.SetFullPathNameInFileDic(helpdir,sdic)
                ddic=self.SetFullPathNameInFileDic(helpdir,ddic)
                #
                lst=clst[0]
                textdic.update(tdic)
                htmldic.update(hdic)
                scriptdic.update(sdic)
                demodic.update(ddic)
            cntlst.append(lst)
        return cntlst,textdic,htmldic,scriptdic,demodic
    
    def SetFullPathNameInFileDic(self,helpdir,filedic):
        """ make full path names of files in xxxdic
        
        :param str helpdir: contents file's directory name
        :param dic filedir: directory of filename
        :return: filedic - dirctory of filename
        """
        for name,file in filedic.iteritems():
            file=lib.PathJoin(helpdir,file)        
            if lib.GetPlatform() == 'WINDOWS': file=file.replace('//','\\')
            filedic[name]=file
        return filedic
    
    def OpenTutorial(self,helpname,rootname='',navi=True,
                        viewer='html',expandall=False):
        """ Open tutorial window
        
        :param str helpname: helpname
        """
        contentslst,textdic,htmldic,scriptdic,demodic= \
                            self.GetTutorialContents(helpname)
        if len(contentslst) <= 0:
            mess='No tutorial contents for helpname='+helpname
            lib.MessageBoxOK(mess,'helpctrl(OpenTutorial)')
            return
        if len(scriptdic) <= 0 and len(demodic) <= 0:
            mess='Tutorials are not available for '+helpname
            lib.MessageBoxOK(mess,'helpctrl(OpenTutorial)')
            return
        winlabel='Tutorial'
        title='Tutorial'
        title=title+':'+helpname
        width=240
        nitems=len(contentslst)+1
        for lst in contentslst: nitems += len(lst[1])
        height=nitems*16+100
        if height > 500: height=500
        winsize=[width,height]
        tutwin=subwin.Tutorial_Frm(self.mdlwin,-1,[],winsize,winlabel=winlabel,
                            title=title,navimode=navi,viewer=viewer,
                            expandall=expandall)        
        tutwin.SetContentsData(rootname,contentslst,textdic,htmldic,scriptdic,
                               demodic)
        tutwin.Show()
        
        return tutwin
    
    def GetDocumentFile(self,helpname):
        pass
        
    def IsDocument(self,helpname):
        """ Check documents(html file)
        
        :return: True if document file is availabel, False for is not 
        """
        a,b,htmldic,d,e=self.GetTutorialContents(helpname)
        if len(htmldic) <= 0: return False
        else: return True

    def IsTutorial(self,helpname):
        """ Check tutorial scripts (.py and .demo)
        
        :return: True if tutorial script is availabel, False for is not 
        """
        a,b,c,scriptdic,demodic=self.GetTutorialContents(helpname)
        if len(scriptdic) <= 0 and len(demodic) <= 0: return False
        else: return True
    
    def LoadFileIntoScriptEditor(self,scriptfile):
        self.model.menuctrl.OnWindow('Open ScriptEditor',True)
        self.scriptwin=self.model.winctrl.GetWin('Open ScriptEditor')
        self.scriptwin.SetWinTitle("ScriptEditor(HelpCtrl)")
        #self.scriptwin.btnexp.Disable()
        #self.scriptwin.ckbstp.Disabel()
        self.scriptwin.LoadTextFromFile(scriptfile)
         
    def CloseScriptEditor(self):
        self.model.menuctrl.OnWindow('Open ScriptEditor',False)
    
    def CloseDescriWin(self):
        try: self.tutwin.descriwin.Destroy()
        except: pass
    
    def Close(self):
        """ Close help and tutorial windows
        
        """
        try: self.helpwin.OnClose(1)
        except: pass
        try: self.tutwin.OnClose(1)
        except: pass

        
