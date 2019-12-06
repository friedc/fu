#!/bin/sh
# -*- coding:utf-8

# lib.py version history
# ver.0.2.0 (28Dec2014): minor changes were done.
# ver.0.1.2 (20Feb2014): the first version.

import wx
import wx.py.crust
import wx.lib.newevent
import numpy
import math
import os
import sys
import platform as platformos
import scipy
from pip._vendor.distlib.compat import ChainMap
from nt import lstat
if int(scipy.__version__.split('.')[1]) >= 11:
    from scipy.optimize import minimize
else:
    from scipy.optimize import optimize
import datetime
import time
import getpass
import glob
import copy
import types
import cPickle as pickel
try: import psutil
except: pass
import re
import gzip

import urllib2 # internet access
import ftplib
from ftplib import FTP 
import webbrowser

import networkx

import const
try: import fortlib
except: pass
import rwfile
import molec
import subwin

try: import win32com.client
except: pass

#---
import inspect
import PIL #, wx.imagedraw
#---
# system program
MACSCREENCAPTURE=''
EDITOR=''
#TIPS=True
# logging and result files
LOGGING=None
LOGFILE=''
RESULTFILE=''
FILENAMEDIC={}
# custom event
EVT_THREAD_ID=wx.NewId()

def EVT_THREADNOTIFY(win,handler):
    win.Connect(-1,-1,EVT_THREAD_ID,handler)

def THREAD_END():
    return EVT_THREAD_ID

def GetSystemInfo():
    return platformos.system().lower()
    #print 'node        :',platform.node()
    #print 'release     :',platform.release()
    #print 'version     :',platform.version()
    #print 'machine     :',platform.machine()
    #print 'procressor  :',platform.processor()
def GetFUModelVersionInfo():
    arch=' (32 bit)'
    if sys.maxsize > 2**32: arch=' (64 bit)'
    return const.FUMODELVER+' on Python '+platformos.python_version()+arch

def GetPlatform():
    """ Return platform
    
    :return: pltfrm(str),release(str) - pltfrm:'WINDOWS', 'MACOSX' or 'LINUX'
                                        release: e.g., '7' on Windows 
    """
    pltfrm='WINDOWS'
    pltfrmdic={'darwin':'MACOSX','win32':'WINDOWS','windows':'WINDOWS',
               'linux':'LINUX'}
    try:
        pltfrm=platformos.system().lower()
        if pltfrmdic.has_key(pltfrm): pltfrm=pltfrmdic[pltfrm] 
        else: pltfrm='LINUX'    
    except: pass
    return pltfrm

def GetPlatformAndRelease():
    """ Return platform
    
    :return: pltfrm(str),release(str) - pltfrm:'WINDOWS', 'MACOSX' or 'LINUX'
                                        release: e.g., '7' on Windows 
    """
    pltfrm='WINDOWS'
    pltfrmdic={'darwin':'MACOSX','win32':'WINDOWS','windows':'WINDOWS','linux':'LINUX'}
    try:
        pltfrm=platformos.system().lower()
        if pltfrmdic.has_key(pltfrm): pltfrm=pltfrmdic[pltfrm] 
        else: pltfrm='LINUX'    
    except: pass
    release=platformos.release().lower()
    return pltfrm,release

def SetHeightOfConboBox():
    pltfrm=GetPlatform()
    if pltfrm == 'LINUX': const.HCBOX=24

def SetFrameFont(frame):
    """ Set font on frame object
    
    :param obj frame: an instance of wx.Frame
    """
    size=8
    if GetPlatform() == 'LINUX':
        font=wx.Font(8,wx.ROMAN,wx.NORMAL,wx.NORMAL,False,u'Roman')
        frame.SetFont(font)
    else:
        font=frame.GetFont()
        font.SetPointSize(size)
        frame.SetFont(font)
    
def Memory(item,mb=True):
    """ Get system memory information
    
    :param str item: item:'total','available','percent','used','free','active', or 'inactive'
                           ('buffers' and 'cached' are not available in this version)
    :return: amount of memory in MB
    :rtype: float
    :note: psutil version 1.2.1 report the data.
    """
    try: mem=psutil.virtual_memory()
    except: return -1
    if mb: toMB=1000*1000
    else: toMB=1000*1000*1000 # GB
    if item == 'total': value=float(mem.total)
    elif item == 'available': value=float(mem.available)
    elif item == 'percent': value=float(mem.percent)
    elif item == 'used': value=float(mem.used)
    elif item == 'free': value=float(mem.free)
    elif item == 'active': value=float(mem.active)
    elif item == 'inactive': value=float(mem.inactive)
    #elif item == 'buffers': value=float(mem.buffers)
    #elif item == 'cached': value=float(mem.cached)
    else: return -1
    
    if item != 'percent': value /= toMB
    return value

def PathJoin(head,tail):
    """ os.path.join(head,tail) and replace backslash with '//' in pathname
    
    :param str head: head name
    :param str tail: tail name
    :return: pathname - head+'//'+tail
    """
    try:
        pathname=os.path.join(head,tail)
        pathname=ReplaceBackslash(pathname)
        return pathname
    except: return ''
    
def WRITELOG(classfunc,args,kwargs):
    """ Write executed function(method) on log file
    
    :param str classfunc: fnction(method) name
    :param dic args: args of the function
    :param dic kwargs: keyword srgs of the function
    """
    if not LOGGING: return
    if not os.path.exists(LOGFILE): return
    # check logging value
    if kwargs.has_key('logging'):
        if not kwargs['logging']: return
    # special treatment for Model.ConsoleMessage method
    if const.LOGGINGMETHODDIC.has_key(classfunc):
        if classfunc == 'Model.ConsoleMessage' or classfunc == 'Model.Message2' \
                         or classfunc == 'Plot.ConsoleMessage':
            items=args[1].split('\n')
            f=open(LOGFILE,'a')
            for argstr in items:
                argstr=argstr.replace('\\','//')
                argstr=argstr.replace('"',"'")
                text=const.LOGGINGMETHODDIC[classfunc]+'("'+argstr+'")\n'                
                f.write(text)
            f.close()
        else:
            arglst=list(args)[:]
            del arglst[0]
            argstr=''; filenamdic={}
            if len(arglst) > 0:
                for arg in arglst:
                    #if arg.strip() == '': continue
                    typ,value=ObjectToString(arg)
                    if not value:
                        print 'Program error: None type arg in lib.LOGGING',arg
                        continue
                    if value == 'unable to stringify':
                        print 'unable to get args in classfunc='+classfunc
                        return
                    if typ == 'filename':
                        name=''
                        for nam,val in FILENAMEDIC.iteritems():
                            if val == value: name=nam
                        if name == '':
                            nfile=len(FILENAMEDIC)
                            name='filename'+str(nfile)
                            FILENAMEDIC[name]=value
                        filenamdic[name]=(value); value=name
                    argstr=argstr+value+','
                if argstr[-1] == ',': argstr=argstr[:-1]
            if len(kwargs) > 0: 
                if len(argstr) > 0: argstr=argstr+','+KeyWordArgsToString(kwargs)
                else: argstr=KeyWordArgsToString(kwargs)
            ###moved to ObjectToString ### argstr=filter(lambda s: len(s) > 0,argstr.replace('\\','//')) 
            #
            f=open(LOGFILE,'a')
            ###if len(filenamdic) > 0:
            ###    for name,value in filenamdic.iteritems():
            ###        f.write(name+'='+value+'\n')
            text=const.LOGGINGMETHODDIC[classfunc]+'('+argstr+')\n'
            f.write(text)
            f.close()
    else: return
    
def FUNCCALL(func):
    def func_call(*args, **kwargs):
        """ [func.__name__, args, kwargs] """
        classobj=args[0]
        classnam=classobj.__class__.__name__
        classfunc=classnam+'.'+func.__name__       
        #
        WRITELOG(classfunc,args,kwargs)
        #
        return func(*args, **kwargs)
    return func_call

def CLASSDECORATOR(decorator):
    """ class decorator """
    def class_decorator(cls):
        for name, m in inspect.getmembers(cls, inspect.ismethod):
            setattr(cls, name, decorator(m))
        return cls
    return class_decorator

def METHODDECORATOR(func):
    """ method decorator for each method
   
     ['ReadFiles', (<__main__.Model instance at 0x0A668AF8>, 
     u'F:\\ps2\\3arca\\extract-res\\3arca-LHG664D.pdb', True), {}]
    """
    def func_call(*args, **kwargs):
        #
        arglst=list(args)[:]
        del arglst[0]
       
        funcname=func.__name__
        classfunc=funcname 
        #
        WRITELOG(classfunc,args,kwargs)
        #
        return func(*args, **kwargs)
    return func_call

def ListAllMethodsInClass(classobj,classname='',sort=False):
    """ List all method names in class
    
    :param obj classobj: module.class, e.g., molec.Atom
    :param str classname: class name for return, e.g., 'Atom'
    :return: classname(str) - class name
    :return: methds(lst) - list of method names
    """
    methods=[]
    lst=inspect.getmembers(classobj, predicate=inspect.ismethod)
    for name,obj in lst: methods.append(name)
    try: methods.remove('__init__')
    except: pass
    if sort: methods.sort()
    return classname,methods
    
def FontPixel(font):
    """ not coded yet 
    :param obj font: font object
    """
    fontwidth=8; fontheight=20
    return fontwidth,fontheight

def GetTextPixelSize(font,text):
    """Return text size in pixel
    
    :param obj font: fixed size wx.FONT object whose size is in pixel,
                     i.e. font.SetPixelSize([7,13])
    :param str text: text
    :return: wtext,htext - text width and height of 'text' in pixels 
    """
    wtext=-1; htext=-1; ntext=len(text)+1; hspace=1.1 # for 'NORMAL' 
    try: 
        wfont,hfont=font.GetPixelSize()
        wtext=ntext*wfont; htext=hfont*hspace
    except:
        font=GetFont(5); font.SetPixelSize([7,13]) # 'Teletye', 10pt
        fontwidth=7; fontheight=13
        wtext=ntext*fontwidth; htext=fontheight*hspace
    return wtext,htext

def GetFontSizeInPixel(font,winobj,text=''):
    """Return text size in pixel(WINDOWS only)
    
    :param obj font: wx.FONT object which size is in point
    :param obj winobj: wx.Window object
    :param str text: text
    :return: wfont,hfont - font width and height of 'text' in pixels 
    """
    if GetPlatform() != "WINDOWS":
        mess='This methid is for WINDOWS only.'
        MessageBoxOK(mess,'lib.GetFontSIzeInPixel)')
        return -1,-1
    w=-1; h=-1
    if text == '': text='A'
    dc=wx.WindowDC(winobj)
    dc.SetFont(font)
    wfont,hfont=dc.GetTextExtent(text)
    return wfont,hfont
        
def WinSize(winsize,menu=True):
    """ Convert window size from that of 'MACOSX' to 'WINDOWS'
    :return: winsize(lst) - windows size, [w,h]
    """
    wwin=winsize[0]; hwin=winsize[1]
    pltfrm,release=GetPlatformAndRelease()
    if pltfrm == 'MACOSX' and not menu: hwin=winsize[1]-30
    elif pltfrm == 'LINUX' and not menu: hwin=winsize[1]-30
    elif pltfrm == 'WINDOWS': 
        if release == '7': pass
        elif release == '8': 
            wwin=winsize[0]+20; hwin=winsize[1]+40
        elif release == '10':
            wwin=winsize[0]+20; hwin=winsize[1]+40
    else: pass 
    return [wwin,hwin]

def MiniWinSize(winsize):
    """ Convert window size from that of 'MACOSX' to 'WINDOWS'
    :return: winsize(lst) - windows size, [w,h]
    """
    winsize=WinSize(winsize)
    return winsize
    
    #if GetPlatform() == 'WINDOWS': return [winsize[0]+20,winsize[1]+30]
    #else: return winsize

def WinPos(parobj,dx=0,dy=50):
    winpos=[0,0]
    try:
        parpos=parobj.GetPosition()
        parsize=parobj.GetSize()
        winpos=[parpos[0]+parsize[0]+dx,parpos[1]+dy]
    except: pass
    return winpos
        
def AttachIcon(winobj,iconfile):
    """ Attach icon on Frame
    
    :param obj winobj: instance of window object
    :param str iconfile: icon file name
    :note: works only on Windows (does not work on X-Window)
    """
    if not winobj or iconfile == '': return
    platform=GetPlatform()
    if platform == 'MACOSX':
        try: icon=wx.Icon(iconfile,wx.BITMAP_TYPE_ICO)
        except: pass
    elif platform == 'WINDOWS':
        try: icon=wx.Icon(iconfile,wx.BITMAP_TYPE_ICO)
        except: pass
    else: # 'LINUX'
        try: icon=wx.Icon(iconfile,wx.BITMAP_TYPE_ICO)
        except: pass
    winobj.SetIcon(icon)

def GetHomeDirectory():
    """ Return HOME directory
    
    :return:home(str) - home directory name
    """
    if GetPlatform() == 'WINDOWS': home=r'C://'
    else: home=os.getenv('HOME') or os.getenv("HOMEDRIVE")    
    #home=os.path.expanduser("~")
    return home

def About(title,logofile):
    """ Open 'About' message box
    
    :param str title: title
    :note: logo file 'fumodel.png' should be in FUPATH/Icons directory.
    """
    if not os.path.exists(logofile): return
    #
    Copyright=const.COPYRIGHT
    Licence="The source code of the program is distributed under The BSD 2-Clause License.\n"
    Licence=Licence+"See http://opensource.org/licenses/BSD-2-Clause).\n"
    version=const.VERSION
    #
    info=wx.AboutDialogInfo()
    #logodir=self.setctrl.GetDir('Icons')
    #logofile='fumodel.png'
    #logofile=os.path.join(icondir,logofile)
    ###logofile=self.setctrl.GetFile('Icons','fumodel.png')
    if os.path.exists(logofile):
        info.SetIcon(wx.Icon(logofile, wx.BITMAP_TYPE_PNG))
    info.SetName(title)
    info.SetVersion(version) #'0.2.0')
    info.SetDescription(Copyright) # description)
    #info.SetCopyright('(C) 2015 xxxx')
    #info.SetWebSite('http://xxxx')
    info.SetLicence(Licence)
    info.AddDeveloper('FU User Group')
    #info.AddDocWriter('author name')
    #info.AddArtist('artist name')
    #info.AddTranslator('translator name')
    wx.AboutBox(info)
 
def SetSetCtrlObj(obj):
    const.SETCTRL=obj
    
def SetConsoleMessObj(obj):
    const.CONSOLEMESSAGE=obj

def SetMessageLevel(level):
    const.MESSAGELEVEL=level

def MessageBoxOK(mess,title='',parent=None):
    if parent is None: parent=const.MDLWIN
    enable=True; boxname=''
    try:  enable=const.SETCTRL.GetMessageBoxFlag(boxname)
    except: pass
    if not enable: 
        const.CONSOLEMESSAGE(title+': '+mess)
        return
    msgbox=subwin.MessageBox_Frm(parent=parent,title=title,message=mess,
                               model=const.MDLWIN.model)    
    msgbox.SetFocus()
    
def MessageBoxYesNo(mess,title=''):
    """ Open 'wx.MessageDialog'

    :param str mess: message text
    :param str title: title of the box
    :return: True for yes, False for no
    """
    SendAltKey()
    """
    if len(pos) <= 0: 
        [x,y]=wx.GetMousePosition()    
        winpos=[x+20,y+20] # ignored in MS WINDOWS
    """
    enable=True
    try:  enable=const.SETCTRL.GetMessageBoxFlag('YesNo')
    except: pass
    if not enable: 
        const.CONSOLEMESSAGE(title+': '+mess)
        return

    dlg=wx.MessageDialog(None,mess,title,
                         style=wx.YES_NO|wx.ICON_QUESTION|wx.STAY_ON_TOP)
    
    if dlg.ShowModal() == wx.ID_YES: return True
    else: return False
    #return dlg

def MessageBoxOKCancel(mess,title='',pos=[]):
    """  MessageBox with 'OK' and 'Cancel buttons
    
    :param str mess: message text
    :param str title: title of the box
    :return: True for OK, False for cancel
    """
    enable=True
    try:  enable=const.SETCTRL.GetMessageBoxFlag('OKCancel')
    except: pass
    if not enable: 
        const.CONSOLEMESSAGE(title+': '+mess)
        return

    if len(pos) <= 0: 
        [x,y]=wx.GetMousePosition()    
        pos=[x+20,y+20] # ignored in MS WINDOWS
    dlg=wx.MessageDialog(None,mess,caption=title,pos=pos,
                         style=wx.OK|wx.CANCEL|wx.STAY_ON_TOP)
    if dlg.ShowModal() == wx.ID_OK: return True
    else: return False
    
def MessageSelect(title='',case=0,mess=''):
    if case == 0: text='Please select atoms.'
    elif case == 1: text='Please select resdiue.'
    if len(mess) > 0: text=text+'\n'+mess
    MessageBoxOK(text,title)
        
def MessageFileNotFound(filename,case=0,title='',mess=''):
    if case == 0: text='Not found file='+filename
    else: text='Not found directory='+filename
    if len(mess) > 0: text=text+'\n'+mess
    MessageBoxOK(text,title)

def IsMoleculeObj(molobj):
    ans=True
    if molobj is None:
        mess='No molecule object. Please "Open" structure file or "New".'
        MessageBoxOK(mess,"")
        ans=False                      
    return ans

def CheckFileExists(filename,case=0,messbox=True):
    """ case=0 for file, =1 for directory"""
    ans=True
    if case == 0:
        if not os.path.exists(filename): ans=False
    else:
        if not os.path.isdir(filename): ans=False        
    if not ans and messbox: MessageFileNotFound(filename,case)
    return ans
        
def SendAltKey():
    return
    
    """ Send 'ALT' key (Wondows only) """
    if GetPlatform() != 'WINDOWS': return
    sendkey=win32com.client.Dispatch("WScript.Shell")
    sendkey.SendKeys("%",0)

def ChangeCursor(obj,curnmb):
    """ Change cursor
    
    :param obj obj: parent window object
    :param int curnmb: cursor number, 0-5
    """
    if curnmb == 0: curs=wx.StockCursor(wx.CURSOR_ARROW)  
    elif curnmb == 1: curs=wx.StockCursor(wx.CURSOR_CROSS)
    elif curnmb == 2: curs=wx.StockCursor(wx.CURSOR_WAIT)
    elif curnmb == 3: curs=wx.StockCursor(wx.CURSOR_HAND)
    elif curnmb == 4: curs=wx.StockCursor(wx.CURSOR_MAGNIFIER)
    elif curnmb == 5: curs=wx.StockCursor(wx.CURSOR_BULLSEYE)
    else: curs=wx.StockCursor(wx.NullCursor) 
   # obj.SetCursor(curs)
    if GetPlatform() == 'WINDOWS': obj.SetCursor(curs)
    else: wx.SetCursor(curs)

def GetFont(family,size=8):
    """ Get fonts
    
    :param int style: 0-5.
    :param int size: default:8
    :return: font(obj) - wx.Font object
    """
    if family == 0: font=wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Courier')     
    elif family == 1: font=wx.Font(size, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Decorative')
    elif family == 2: font=wx.Font(size, wx.FONTFAMILY_SCRIPT, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Script')
    elif family == 3: font=wx.Font(size, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Swiss')
    elif family == 4: font=wx.Font(size, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Modern')
    elif family == 5: font=wx.Font(size, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Teletype')
    else: font=wx.Font(size, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL,
           wx.FONTWEIGHT_NORMAL, False, 'Roman')     
    return font

def KeyCodeToASCII(keycode):
    """ Convert keycode to character
    
    :param int keycode: key code
    :return: keychar(str) - key character
    """
    keytable={27:'esc', 32:'space', 127:'del', 
              44:'<',46:'>',91:'[',93:']',64:'@',
              48:'0', 49:'1', 50:'2', 51:'3', 52:'4', 53:'5',
              54:'6', 55:'7', 56:'8', 57:'9',
              65:'a', 66:'b', 67:'c', 68:'d', 69:'e', 70:'f', 71:'g', 72:'h', 73:'i',
              74:'j', 75:'k', 76:'l', 77:'m', 78:'n', 79:'o', 80:'p', 81:'q', 82:'r',
              83:'s', 84:'t', 85:'u', 86:'v', 87:'w', 88:'x', 89:'y', 90:'z' }
    if keytable.has_key(keycode): return keytable[keycode]
    else: return ''

def UniCodeToChar(keycode):
    """ Convert unicode keycode to character
    
    :param int keycode: key code
    :return: keychar - key character
    """
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
               35:'#',36:'$',37:'%',38:'&',42:'*',43:'+',45:'-',61:'=',63:'?',64:'@',
               91:'[',93:']',123:'{',125:'}',60:'<',62:'>',
               51:'shift',315:'up arrow',317:'down arrow',314:'left arrow',
               316:'right arrow'}
    
    if codetable.has_key(keycode): return codetable[keycode]
    else: return ''
    
def ChooseColorOnPalette(parent,rgb255,opacity):
    """ Get color in color palette
    
    :param bool rgb255: True for rgb values 0-255, False for 0-1
    :param float opacity: add opacity value to [r,g,b] color list if opacity >= 0
    :return: rbgcol(lst) - [r,g,b] or [r,g,b,opacity]
    """
    SendAltKey()
    # open color parette
    dlg=wx.ColourDialog(parent)
    dlg.GetColourData().SetChooseFull(True)
    if dlg.ShowModal() == wx.ID_OK:
        coldat=dlg.GetColourData()
        col=coldat.GetColour().Get()
        col=list(col)
        if not rgb255:
            col[0]=float(col[0])/float(255); col[1]=float(col[1])/float(255)
            col[2]=float(col[2])/float(255)
        rgbcol=col #+[1.0]
        if opacity >= 0: rgbcol=rgbcol+[opacity]
    else: rgbcol=[]
    dlg.Destroy()
    return rgbcol

def IsLowerCase(string):
    """ Return True if all characters in 'string' are lower case """
    ans=True
    for s in string:
        if s.isupper():
            ans=False; break     
    return ans

def AreSameBaseNames(filnam1,filnam2):
    """ Retrun True if the two file names have the same base name """
    def SplitBase(name):
        head,tail=os.path.split(name)
        base,ext=os.path.splitext(tail)
        return base
    ans=False
    base1=SplitBase(filnam1).lower()
    base2=SplitBase(filnam2).lower()
    if base1 == base2: ans=True
    return ans

def AtmNamToElm(atmnam):
    """ Return element name of 'atmnam'
    
    :param str atmnam: atom name in PDB form
    :return: elm(str) - element name in right adjusted two characters
    """
    # 2013.2 KK
    # make element data from atmnam data in pdb
    # return element name, elm
    elmchr2={'HE':0,'LI':1,'BE':2,'NE':3,'NA':4,'MG':5,'AL':6,'SI':7,'CL':8,
             'AR':9,'CA':10,'SC':11,'TI':12,'CR':13,'MN':14,'FE':15,'CO':16,
             'NI':17,'CU':18,'ZN':19,'GA':20,'GE':21,'AS':22,'SE':23,'BR':24,
             'KR':25,'RB':26,'SR':27,'ZR':28,'NB':29,'MO':30,'TC':31,'RU':31,
             'RH':33,'PD':34,'AG':35,
             #'CD':36,
             'IN':37,'SN':38,'SB':39,'TE':40,
             'XE':41,'CS':42,'BA':43,'LA':44,
             #'CE':45,
             'PR':46,'ND':47,'PM':48,
             'SM':49,'EU':50,'GD':51,'TB':52,'DY':53,'HO':54,'ER':55,'TM':56,
             'YB':57,'LU':58,'HF':59,'TA':60,'RE':61,'OS':62,'IR':63,'PT':64,
             'AU':65,'HG':66,'TL':67,'PB':68      }  
    
    tmp=atmnam[0:2]
    if tmp == 'HE' or tmp == 'HG' or tmp == 'HO' or tmp == 'HF': elm=' H'
    elif elmchr2.has_key(tmp): elm=tmp #[0:2]
    else:
        tmp=tmp.strip()
        if tmp[0:1].isdigit(): elm=' '+tmp[1:2]
        else: elm=' '+tmp[0:1]
    
    if not const.ElmNmb.has_key(elm):
        mess='Failed to get element from atmnam='+atmnam
        print mess
        print 'elm',elm
        
        elm='??'
        #wx.MessageBox(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)
    return elm
    
def ChangeLength(cc0,cc1,r):
    """
    change coordinates 'cc1'(p0) at length 'r' from 'cc0'(p1) along p0-p1
    
    :param lst cc0: coordinates of p0
    :param lst cc1: coordinates of p1
    :param float r: distance between p0 and p1
    :return: [x(float),y(float),z(float)](lst) - new coordinate of p1
    """
    if r < 0.5:
        print 'Error (ChangeLength): too short distance. r=',r
        return
    r0=math.sqrt((cc0[0]-cc1[0])**2+(cc0[1]-cc1[1])**2+(cc0[2]-cc1[2])**2)
    ratio=r/r0
    x=ratio*(cc1[0]-cc0[0])+cc0[0]
    y=ratio*(cc1[1]-cc0[1])+cc0[1]
    z=ratio*(cc1[2]-cc0[2])+cc0[2]
    return [x,y,z]

    
def Optimizer(Efunc,x0,method='L-BFGS-B',jac=None,optns={}):
    """
    Efunc(x,count)
    
    See the scipy.optimize.minimize manual for options
    """
    const.CONSOLEMESSAGE('Entered in lib.Optimizer')
    methlst=['Nelder-Mead','Powell','CG','BFGS','Newton-CG','Anneal','L-BFGS-B',
             'TNC', 'COBYLA', 'SLSQP'] # scipy.Optimoze.Minimize in scipy ver0.16?
    if not method in methlst:
        mess='Not found method='+method
        MessageBoxOK(mess,'lib.Optimizer')
        return None
    nvar=len(x0)
    const.CONSOLEMESSAGE('lib.Optimizer nvar='+str(nvar))
    if nvar <= 0:
        mess='No variables'
        MessageBoxOK(mess,'lib.Optimizer')
        return None   
    
    optcg = {'maxiter' : False,    # default value.
            'disp' : True, #True,    # non-default value.
            'gtol' :1e-2, #1e-5,    # default value.
            'eps' : False }#1.4901161193847656e-08}  # default value.
    optpw = {'maxiter' : False,    # default value.
            'disp' : True, #True,    # non-default value.
             }
    count=0
    opts=optcg
    if method == 'Powell': opts=optpw
    const.CONSOLEMESSAGE('lib.Optimizer #1')
    if int(scipy.__version__.split('.')[1]) >= 11: # for Scipy 0.11.x or later
        const.CONSOLEMESSAGE('lib.Optimizer scipy version >11')
        result = minimize(Efunc,x0=x0, method=method,options=optns) #,
                        #args=(count))
    else: # for Scipy 0.10.x
        const.CONSOLEMESSAGE('lib.Optimizer scipy version old')
        if method == 'CG':
            result = optimize.fmin_cg(Efunc, p0, # args = (count),
                                  gtol = optcg['gtol'], epsilon = optcg['eps'],
                                  maxiter = optcg['maxiter'], disp = optcg['disp'])
        elif method == 'Powell':
            result = optimize.fmin_powell(Efunc, p0, #args = (count),
                                      maxiter = optpw['maxiter'], disp = optpw['disp'])
        else:
            print 'Error unknown minimization method. method = ', method
            return None
    return result

class RMSFitCC(object):
    """ RMS fit """
    def __init__(self,parent):
        """ performs RMS fit of two coordinate sets, cc0 and cc1
        :param obj parent: parent window object
        """
        self.cc0=[]; self.mass0=[]
        self.cc1=[]; self.mass1=[]
        self.dcnt=[]; self.cnt=[]; self.rot=[]
        self.etime=0; self.rmsd=0; self.ndat=0; self.chisq=0
        # minimization method: "CG" or 'Powell'
        self.method="CG"
    
    def ResetParams(self):    
        self.cc0=[]; self.mass0=[]
        self.cc1=[]; self.mass1=[]
        self.dcnt=[]; self.cnt=[]; self.rot=[]
        self.etime=0; self.rmsd=0; self.ndat=0; self.chisq=0
    
    def SetCCAndMass(self,cc0,cc1):
        self.cc0=cc0
        for i in xrange(len(cc0)): self.mass0.append(1.0)
        self.cc1=cc1
        for i in xrange(len(cc1)): self.mass1.append(1.0)
        
    def SetMethod(self,method):
        self.method=method
    
    def PerformRMSFit(self,messmethod=None):
        err=0; chisq=0.0; dcnt=[]; cnt=[]; rot=[]; etime=0; ndat=0; rmsd=0.0
        if len(self.cc0) <= 0 or len(self.cc1) <= 0:
            err=1; return err,etime,ndat,rmsd,chisq,dcnt,cnt,rot
        # start minimization of chisq
        time1=time.clock() # turn on timer
        #
        cc0=self.cc0; mass0=self.mass0; cc1=self.cc1; mass1=self.mass1
        com0,eig0,vec0=CenterOfMassAndPMI(mass0,cc0)
        com1,eig1,vec1=CenterOfMassAndPMI(mass1,cc1)
        dcnt=[com0[0]-com1[0],com0[1]-com1[1],com0[2]-com1[2]]
        # move center fo target aoms
        for cc in cc1:
            cc[0] += dcnt[0]; cc[1] += dcnt[1]; cc[2] += dcnt[2]
        # initial values, translation (xc,yc,zc) and euler angles (a,b,c) 
        p0=[0.0,0.0,0.0,0.0,0.0,0.0]
        # choice of optimization method
        #'Nelder-Mead', 'Powell', 'CG', 'BFGS', 'Newton-CG', 'Anneal', 'L-BFGS-B'
        #'TNC', 'COBYLA', 'SLSQP'
        method=self.method
        #method='CG' #'Powell' #'Powell' seems faster than 'CG' for this problem
        optcg = {'maxiter' : None,    # default value.
                'disp' : False, #True,    # non-default value.
                'gtol' :1e-2, #1e-5,    # default value.
                'eps' : 1.4901161193847656e-08}  # default value.
        optpw = {'maxiter' : None,    # default value.
                'disp' : False, #True,    # non-default value.
                 }
        opts=optcg
        if method == 'Powell': opts=optpw
        if int(scipy.__version__.split('.')[1]) >= 11: # for Scipy 0.11.x or later
            result = minimize(self.FuncChisqCC, p0, method = method, options = opts,
                            args=(self.cc0, self.cc1))
        else: # for Scipy 0.10.x
            if method == 'CG':
               result = optimize.fmin_cg(self.FuncChisqCC, p0, args = (self.cc0, self.cc1),
                                      gtol = optcg['gtol'], epsilon = optcg['eps'],
                                      maxiter = optcg['maxiter'], disp = optcg['disp'])
            elif method == 'Powell':
                result = optimize.fmin_powell(self.FuncChisqCC, p0, args = (self.cc0, self.cc1),
                                          maxiter = optpw['maxiter'], disp = optpw['disp'])
            else:
                print 'Error unknown minimization method. method = ', method
                return
        #
        p = p0
        if int(scipy.__version__.split('.')[1]) >= 11: # for Scipy 0.11.x or later
            p = result.x
        else: # for Scipy 0.10.x
            p = result.xopt
        cnt=[p[0],p[1],p[2]]
        rot=[p[3],p[4],p[5]]
        chisq=self.FuncChisqCC(p,cc0,cc1)
        # print result
        rmsd=math.sqrt(chisq/float(len(cc1)))
        ndat=len(cc1)
        time2=time.clock()
        etime=time2-time1
        etime=int(etime) # elapsed time in sec.
        # mess out
        if messmethod is not None:
            emin=etime/60.0; semin='%6.2f' % emin 
            mess="Elasped time in RMS fit: "+str(etime)+" sec ("+semin
            mess=mess+" min) by method= "+method+"\n"
            srmsd="%6.3f" % rmsd; schisq='%6.3f' % chisq
            mess=mess+"RMSD(A),ndata: "+srmsd+","+str(len(cc1))
            messmethod(mess)
        return err,etime,ndat,rmsd,chisq,dcnt,cnt,rot

    def FuncChisqCC(self,p,cc0,cc1):
        # p: parameters to bedetermined, cc0: reference coordinates, cc1:target coordinates
        global dialog
        xc=p[0]; yc=p[1]; zc=p[2] # translation vector
        a=p[3]; b=p[4]; c=p[5] # euler angles
        res=0.0
        u=RotMatEul(a,b,c)
        cnt=[xc,yc,zc]
        cct=RotMol(u,cnt,cc1)
        try: res=fortlib.chisq_cc(cc0,cct) # Fortran routine
        except:
            print "Non-Fortran code is running"
            for i in xrange(len(cc1)):
                res=res+(cct[i][0]-cc0[i][0])**2+(cct[i][1]-cc0[i][1])**2+(cct[i][2]-cc0[i][2])**2
        return res

def ComputeRMSD(cc0,cc1):
    """ Compute root-mean-square deviation
    
    """
    # p: parameters to bedetermined, cc0: reference coordinates, cc1:target coordinates
    try: chisq=fortlib.chisq_cc(cc0,cc1) # Fortran routine
    except:
        print "Non-Fortran code is running"
        for i in xrange(len(cc1)):
            chisq=chisq+(cc1[i][0]-cc0[i][0])**2+(cc1[i][1]-cc0[i][1])**2+(cc1[i][2]-cc0[i][2])**2
    rmsd=math.sqrt(chisq/float(len(cc1)))
    return rmsd

class OpenText_Frm(wx.Frame):
    def __init__(self,parent,id,winpos,winsize,title,textlst):
        self.title=title
        wx.Frame.__init__(self,parent,id,title,pos=winpos,size=winsize)   
    
        self.textlst=textlst
        self.selected=''
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnSize)
        
    def CreatedPanel(self):
        pass
    
    def OnCancel(self,event):
        return ''
    
    def OnOpen(self,event):
        self.selected=self.btnopn.GetValue()
        self.OnClose(1)
    
    def OnSize(self,event):
        pass
    
    def OnClose(self):
        return self.selected
        self.Destroy()
    
class TextBuffer():
    """ Text buffer for memory file
    
    """
    def __init__(self,parent,model):
        self.parent=parent
        self.model=model # Model class in fumodel
        # 
        self.textbuffdic={}
        self.curtext=''
    
    def StoreTextInArchiveFile(self,archfile):
        textbuffdic={}
        f=open(archfile,'r')
        find=False; name=''
        for s in f.readlines():
            ss=s.strip()
            if ss[:1] == '#': continue
            if not find and ss[:8] == 'MEMFILE:':
                find=True
                name=ss.split(':')[1].strip()
                if name == '': continue
                textbuffdic[name]=''
            else:
                if ss[:6] == 'ENDMEM':
                    find=False; continue
                if not textbuffdic.has_key(name): continue
                textbuffdic[name]=textbuffdic[name]+s
        f.close()
        #
        self.textbuffdic.update(textbuffdic)

    def SaveTextOnArchiveFile(self,archfile,remark=''):
        f=open(archfile,'w')
        mess='# Memory file backup archive. '+CreatedByText()+'\n#\n'
        f.write(mess)
        if len(remark) > 0: f.write(remark)
        for name,text in self.textbuffdic.iteritems():
            f.write('MEMFILE: '+name+'\n')    
            f.write(text)
            f.write('ENDMEM\n')
        f.close()
            
    def Open(self):
        textname=''
        textlst=self.ListTextNames()
        textname=subwin.GetTextName(textlst)
        if textname == '': return # cancel
        mess='(Open) textname="'+textname+'".'
        self.Message(mess)
        self.curtext=textname
        if not self.textbuffdic.has_key(textname):
            self.textbuffidc[textname]=''
    
    def OpenNewText(self,textname):
        if textname == '': textname='temp'
        if self.textbuffdic.has_key(textnam):
            mess='TextName "'+textname+'" exists. Clear it?'
            dlg=MessageBoxYesNo(mess,'TextBuffer(OpenNewText)')
            if dlg.ShowModal() == wx.ID_NO: return
        self.textbuffidc[textname]=''
             
    def Message(self,mess):
        mess='TextBuffer'+mess
        try: self.model.ConsoleMessage(mess)
        except: print mess
        
    def Close(self):
        mess='(Close) textname="'+self.curtext+'".'
        self.Message(mess)
        self.curtext=''
        
    def GetText(self,textnam):
        if self.textbuffdic.has_key(textnam):
            self.curtext=textnam
            return self.textbuffdic[self.curtext]
        else: return ''
    
    def GetCurTextName(self):
        return self.curtext
    
    def IsOpened(self):
        if self.curtext == '':
            mess='No text is opened.'
            self.Message(mess)
            return False
        return True
        
    def SaveText(self,text):
        if self.IsOpened():
            self.textbuffdic[self.curtext]=text
            mess='(SavedText): text="'+self.curtext+'".'
            self.Message(mess)
        
    def SaveTextAs(self,textname,text):
        if self.textbuffdic.has_key(textname):
            mess='"'+textname+'" is exists. Overwrite it?'
            dlg=MessageBoxYesNo(mess,"TextBuffer(SaveTextAs)")
            if dlg.ShowModal() == wx.ID_NO: return
        self.textbuffdic[textname]=text
    
    def WriteFile(self,filename):
        if self.IsOpened():
            text=self.textbuffdic[self.curtext]
            f=open(filename,'w')
            f.write(text)
            f.close()
            mess='(WriteFile): "'+self.curtext+'" is written on file='+filename+'.'
    
    def LoadFile(self,filename):
        if not os.path.exists(filename):
            mess='(LoadText): file "'+filename+'" not found.'
            self.Message(mess)
        head,tail=os.path.split(filename)
        base,ext=os.path.splitext(tail)
        text=''
        f=open(filename,'r')
        for s in f.readlines(): text=text+s
        f.close
        self.textbuffdic[base]=text
        mess='(LoadText): Load text. textname="'+base+'" from file='+filename
        self.Message(mess)
    
    def ListTextNames(self):
        namlst=self.textbuffdic.keys()
        return namlst
    
    def ListText(self):
        if self.IsOpened():
            text=self.textbuffdic[self.curtext]           
            mess='(ListText): List TextName='+self.curtext+'\n'+text
            try: self.model.ConsoleMessage(mess)
            except: print mess
    
    def RenameText(self,newname):
        if self.IsOpened():
            if self.textbuffdic.has_key(newname):
                mess='(RenameText): Name="'+newname+'" exists. Overwrite it?'
                dlg=MessageBoxYesNo(mess,'TextBuffer(RenameText)')
                if dlg.ShowModal() == wx.ID_NO: return
                dlg.Destroy()
                del self.textbuffdic[newname]
            text=self.textbuffdic[self.curtext]
            del self.textbuffdic[self.curtext]
            self.textbuffdic[newname]=text
            mess='(RenameText): "'+self.curtext+'" is renamed "'+newname+'".'      
            self.Message(mess)
            self.curtext=newtext
    
    def DeleteText(self,textname):
        if textname == 'all': self.textbuffdic={}
        elif self.textbuffdic.has_key(textname):
            del self.textbuffdic[textname]
            mess='(Delete): "'+textname+'" is deleted.'
            self.Message(mess)
        else:
            mess='(Delete): No TextName='+textname+'.'
            self.Message(mess)
            
def NormalVector(p1,p2,p3):
    """
    Normal vector of triangle,(p1,p2,p3)
    
    :param lst p1,p2,p3: pi(i=1,3) [x(float),y(float),z(float)]
    :return: normal - normal vector [x(float),y(float),z(float)]
    """
    p1=numpy.array(p1); p2=numpy.array(p2); p3=numpy.array(p3)
    v=numpy.cross(p3-p2,p2-p1)
    vn=numpy.linalg.norm(v)
    if vn > 0: normal=v/vn
    else: normal=[1.0,0.0,0.0]
    return normal

def NormalVector4P(p1,p2,p3,p4):
    """ Normal vector of rectangle,(p1,p2,p3,p4)
    
    :param lst p1,p2,p3,p4: pi(i=1,4) [x(float),y(float),z(float)]
    :return: normal(lst) - normal vector [x(float),y(float),z(float)]
    """
    p1=numpy.array(p1); p2=numpy.array(p2)
    p3=numpy.array(p3); p4=numpy.array(p4)
    v1=numpy.cross(p3-p2,p2-p1); v1=v1/numpy.linalg.norm(v1)
    v2=numpy.cross(p4-p3,p3-p2); v2=v2/numpy.linalg.norm(v2)
    v=v1+v2
    normal=v/numpy.linalg.norm(v)
    return normal

def ToggleSW(var):
    """
    Interchange True and False 
    
    :param bool var: True or False
    :return: switched 'var' value
    :rtype: bool
    """
    if var: var=False
    else: var=True
    return var

class ToggleSwitch():
    def __init__(self,parent):
        self.itemlst=[]
        self.vardic={}

    def ResetAllVars(self):
        self.itemlst=[]
        for item in self.itemlst:
            self.vardic[item]=0

    def Reset(self,varnam):
            self.vardic[varnam]=0

    def SW(self,varnam):
        if self.vardic.has_key(varnam):
            curnmb=self.vardic[varnam]+1
            if curnmb >= len(self.itemlst): curnmb=0
            return curnmb
        else: return -1

    def GetCurrentNmb(self,varnam):
        return self.vardic[varnam]

    def GetCurrentItem(self,varnam):
        curnmb=self.vardic[varnam]
        return self.itemlst[curnmb]

    def GetItemList(self):
        return self.itemlst
        
    def SetCurrentNmb(self,varnam,curnmb):
        self.vardic[varnam]=curnmb

    def SetCurrentItem(self,varnam,curitem):
        try: idx=self.itemlst.index(curitem)
        except: idx=-1
        self.vardic[varnam]=idx
        
    def SetItemList(self,itemlst):
        self.itemlst=itemlst
        for item in self.itemlst:
            self.vardic[item]=0

def GetMinMaxValuesFromUser(tiptext='',default=''):
    def ErrorMessage(text):
        mess='Wrong input data. text='+text
        MessageBoxOK(mess,'lib.GetMinMaxValuesFromUser')
        return None,None
    #
    larger=None; smaller=None; absval=False
    if len(tiptext) <= 0:
        tiptext='Enter values (ex. "<3.0,>1.0 '
        tiptext=tiptext+'or <<3.0,<<1.0 for absolute value"):'
    text=wx.GetTextFromUser(tiptext,'GetDataFromUser',default)
    if len(text) <= 0: return larger,smaller,absval
    items=text.split(',')
    for i in range(len(items)):
        s=items[i].strip()
        if s[:2] == '>>':
            absval=True; larger=s[2:].strip()
            try: larger=float(larger)
            except: 
                larger,smaller=ErrorMessage(text); break
        if s[:1] == '>' and s[:2] != '>>':
            larger=s[1:].strip()
            try: larger=float(larger)
            except: 
                larger,smaller=ErrorMessage(text); break
        if s[:1] == '<<':
            absval=True
            smaller=s[1:].strip()
            try: smaller=float(smaller)
            except: 
                larger,smaller=ErrorMessage(text); break
        if s[:1] == '<' and s[:2] != '<<':
            smaller=s[1:].strip()
            try: smaller=float(smaller)
            except: 
                larger,smaller=ErrorMessage(text); break
    #          
    return larger,smaller,absval

def GetValueFromUser(message,caption='',default=0.0):
    value=None
    text=wx.GetTextFromUser(message,caption=caption,
                              default_value=str(default))
    try: value=float(text.strip())
    except: 
        mess='Wrong input. Only floating point value is accepted.'
        lib.MessageBoxOK(mess,'lib.GetValueFromUser')
    return value
                                    
def ExtractDataByValue(datlst,larger,smaller,absval):
    extracted=[]
    if larger is None and smaller is None:
        extracted=datlst[:]
        return extracted
    for i in range(len(datlst)):
        val=datlst[i]
        if absval: val=abs(val)
        if larger is not None and smaller is not None:
            if val > larger and val < smaller: extracted.append(i)
        elif larger is not None and smaller is None:
            if val > larger: extracted.append(i)
        elif larger is None and smaller is not None:
            if val < smaller: extracted.append(i)
    return extracted

def GetFileNames(parent,wcard='',rw='r',check=False,defaultname='',message=''):
    """ Get file name (multiple selection)
    
    :param obj parent: parent object
    :param str wcard: wild card
    :param str rw: 'r' for read, 'w' for write
    :param bool check: True for check the file existence, False for do not.
    :param str defaultname: default name to be set
    :return: filenames(lst) - [filename1(str),filename2(str),...]
    :seealso: 'lib.GetFileName','lib.GetFileNamesWithNumber'
    """
    #if GetPlatform() == 'WINDOWS': SendAltKey()
    #
    filenames=[]
    if wcard == "": wcard="All(*.*)|*.*"
    if rw == "": rw="r"
    if check == "": check=True
    if len(message) <= 0 and rw == 'r': message='Open file...'
    if len(message) <= 0 and rw == 'w': message='Save file...'
    try:
        if rw == "r": dlg=wx.FileDialog(parent,message,os.getcwd(),style=wx.FD_OPEN|wx.FD_MULTIPLE,wildcard=wcard)
        elif rw == "w": dlg=wx.FileDialog(parent,message,os.getcwd(),style=wx.FD_SAVE,wildcard=wcard)  
        if len(defaultname) > 0: dlg.SetFilename(defaultname)
        if dlg.ShowModal() == wx.ID_OK:
            filenames=dlg.GetPaths()
            if len(filenames) > 0:
                for filename in filenames:
                    if rw == "w" and os.path.exists(filename) and check:
                        MessageBoxYesNo("%s file exists. Overwrite?" % filename,"File exist!")
                        if not wx.YES: return []
        dlg.Destroy()
    except:
        mess="Failed to open file. File/directory name can not be decoded by utf8."
        MessageBoxOK(mess,"")
        filenames=[]
    filenames=PickUpASCIINames(filenames)
    filenames=ReplaceBackslash(filenames)
    return filenames

def GetFileName(parent=None,wcard='',rw='',check=False,defaultname='',
                message=""):
    """ Get file name (single selection)
    
    :param obj parent: parent object
    :param str wcard: wild card
    :param str rw: 'r' for read, 'w' for write
    :param bool check: True for check the file existence, False for do not.
    :param str defaultname: default name to be set
    :return: filename(str) - file name
    :seealso: 'lib.GetFileNames','lib.GetFileNamesWithNumber'
    """
    filename=""
    if wcard == "": wcard="All(*.*)|*.*"
    if rw == "": rw="r"
    if check == "": check=True
    if len(message) <= 0 and rw == 'r': message='Open file...'
    if len(message) <= 0 and rw == 'w': message='Save file...'
    try:
        if rw == "r": 
            dlg=wx.FileDialog(parent,message,os.getcwd(),
                              style=wx.FD_OPEN|wx.FD_MULTIPLE,wildcard=wcard)
        elif rw == "w": 
            dlg=wx.FileDialog(parent,message,os.getcwd(),style=wx.FD_SAVE,
                              wildcard=wcard)
               
        if len(defaultname) > 0: dlg.SetFilename(defaultname)
        
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath() #filename=dlg.GetFilename()    
            if len(filename) > 0:
                if rw == "w" and os.path.exists(filename) and check:
                    MessageBoxYesNo("%s file exists. Overwrite?" % filename,"File exist!")
                    if not wx.YES: return ''
        dlg.Destroy()
    except:
        mess="Failed to open file. File/directory name can not be decoded by utf8."
        MessageBoxOK(mess,"")
        filename=''
    if not IsAllASCII(filename): filename=''
    else: filename=ReplaceBackslash(filename)
    return filename

def GetFileNamesWithNumber(parent=None,wcard='',rw='r',check=False,defaultname='',message=''):
    """ Get file names with the same base name as choosen file in a directory.
    i.e. files whose name are 'basename.number' will be returned in a list.
    
    :param obj parent: parent object
    :param str wcard: wild card
    :param str rw: 'r' for read, 'w' for write
    :param bool check: True for check the file existence, False for do not.
    :param str defaultname: default name to be set
    :return: filenames(lst) - [filename1(str),filename2(str),...]
    :seealso: 'lib.GetFileName','lib.GetFileNames'
    """
    ###if GetPlatform == 'WINDOWS': SendAltKey()

    filename=""; filenames=[]
    if wcard == "": wcard="All(*.*)|*.*"
    if rw == "": rw="r"
    if check == "": check=True
    if message == '' and rw == 'r': message="Open file..."
    if message == '' and rw == 'w': message="Save file..."
    try:
        parent.Hide()
        
        if rw == "r": dlg=wx.FileDialog(parent,message,os.getcwd(),style=wx.FD_OPEN|wx.FD_MULTIPLE,wildcard=wcard)
        elif rw == "w": dlg=wx.FileDialog(parent,message,os.getcwd(),style=wx.FD_SAVE,wildcard=wcard)  
        if len(defaultname) > 0: dlg.SetFilename(defaultname)
        if dlg.ShowModal() == wx.ID_OK:
            filename=dlg.GetPath() #filename=dlg.GetFilename()    
            if len(filename) > 0:
                if rw == "w" and os.path.exists(filename) and check:
                    MessageBoxYesNo("%s file exists. Overwrite?" % filename,"File exist!")
                    if not wx.YES: return ''
        dlg.Destroy()
    except:
        mess="Failed to open file. File/directory name can not be decoded by utf8."
        MessageBoxOK(mess,"")
        filename=''
    if filename == '': return ['']
    # get files with sequence numbers
    head,tail=os.path.split(filename)
    base,ext=os.path.splitext(tail)
    basename=tail
    if ext[1:].isdigit(): basename=base
    # get all files in this directory
    fileslst=GetFilesInDirectory(head,['all'])
    for file in fileslst:
        if file.find(basename) > -1: filenames.append(file)
    filenames.sort()
    #
    return filenames

def GetFileNameDir(filename):
    """ Return directory name of filename
    
    :param str filename: file name
    :return: dirname(str) - directory name
    """
    dirname=''
    if not os.path.exists(filename): return dirname
    dirname,tail=os.path.split(filename)
    return dirname

def ExpandUserFileName(userfile):
    if platformos.system().upper() == 'WINDOWS': 
        userfile=userfile.replace('~','C:')
    else: userfile=os.path.expanduser(userfile)
    return userfile

def CompressUserFileName(fullpath):
    """ Replace home directory name by '~/User'
    
    :param str fullpath: full path name
    :return: filename(str) - compressed path name
    """
    home=os.getenv('HOME') or os.getenv("HOMEDRIVE")
    n=fullpath.find(home)
    if n < 0: return fullpath
    filename=fullpath.replace(home,'~',1)
    return filename

def ChangeToFilesRootDir(filename):
    root,ext=os.path.splitext(filename)
    curdir=GetFileNameDir(filename)
    if os.path.isdir(curdir): 
        os.chdir(curdir)        
        return curdir
    else: return os.getcwd()

def GetDirectoryName(parent=None):
    """ Open filer to get directory
    
    :param obj parent: parent window object
    :return: dirname(str) - directory name
    """
    if GetPlatform() == 'WINDOWS': SendAltKey()
    try:
        dlg=wx.DirDialog(parent,"Get dir...",os.getcwd(),style=wx.DD_DEFAULT_STYLE)
        if dlg.ShowModal() == wx.ID_OK: dirname=dlg.GetPath() #filename=dlg.GetFilename()    
        else: dirname=''
        dlg.Destroy()
    except:
        mess="Failed to get directory. directory name could not be decoded by utf8."
        MessageBoxOK(mess,"")
        dirname=''
    return dirname

def DeleteFilesInDirectory(dirname,ext):
    """ Delete files with extenton 'ext(e.g. .scr)' in directory 'dirname'
    
    :param str dirname: directory name
    :param str ext: 'all', 'digit' for numbers, and ext string of file descriptor
    """
    for name in glob.glob(os.path.join(dirname,"*")):
        if ext == 'all':
            try: os.remove(name)
            except: pass
        elif ext == 'digit': # assume '.000'
            root,fext=os.path.splitext(name)
            if fext[1:].isdigid():
                try: os.remove(name)
                except: pass
        else: 
            root,fext=os.path.splitext(name)
            if fext == ext:
                try: os.remove(name)
                except: pass

def ReplaceBackslash(filename):
    """ Repacel backslash with '//' in file name
    
    :param str or lst filename: filename or filenames in list
    :return: filename(str or lst)
    """
    if isinstance(filename,types.StringType): 
        filename=filter(lambda s: len(s) > 0,filename.replace('\\','//')) 
    elif isinstance(filename,types.ListType):
        lst=[]
        for name in filename: 
            name=filter(lambda s: len(s) > 0, name.replace('\\','//')) 
            lst.append(name)
        filename=lst
    return filename

def PickUpASCIINames(filename):
    """ Pickup ASCII file name(s)
    
    :param str or lst filename: filename or filename list
    :return: filename(str or lst)
    """
    if isinstance(filename,types.StringType): 
        if not IsAllASCII(filename): return ''
    elif isinstance(filename,types.ListType):
        lst=[]
        for name in filename: 
            if not IsAllASCII(name): continue
            lst.append(name)
        filename=lst
    return filename
        
def BaseNameInFileName(filename):
    """ Return base name of file name
    
    :param str filename: file name
    :reurn: base(str) - base name of the file
    """
    base,ext=os.path.splitext(filename)
    return base
        
def SplitFileName(filename):
    """ Split file name into head,tail,base,ext
    
    :return: head(str),tail(str),base(str),ext(str) of filename
    """
    head,tail=os.path.split(filename)
    base,ext=os.path.splitext(tail)
    return head,tail,base,ext

def ExpandFilesInDirectory(filedirnames,extlst=['all']):
    """ expand filenames in directory
    
    :param lst filedirnames: list of files or directories or mixed
    :param lst extlst: list of filename extension to pick up
    :reurn: filenamelst - list of all filenames 
    """
    filenamelst=[]
    all=False
    if extlst[0] == "all" or ".*": all=True
    if len(filedirnames) <= 0: return filenamelst
    for file in filedirnames:
        if os.path.isdir(file):
            filesindir=GetFilesInDirectory(file,extlst)
            for fil in filesindir: filenamelst.append(fil)
        else:
            base,ext=os.path.splitext(file)
            if all: filenamelst.append(file)
            else: 
                if ext in extlst: filenamelst.append(file)
    filenamelst=ReplaceBackslash(filenamelst)
    return filenamelst
        
def GetFilesInDirectory(dirnam,extlst=['all']):
    """Get all files with extention '.ext' in directory 'dirnam'
    
    :param str dirnam: directory name
    :param lst extlst: extension list, like ['.pdb', '.xyz',...]. 
    :return: filelst - [filename1(str),filename2(str),...]
    :note: if ext == ['all'], all files are returned
    """
    filelst=[]
    if dirnam == '': return []
    if not os.path.isdir(dirnam): return []
    all=False
    if extlst[0] == 'all' or extlst[0] == '.*': all=True
    if not os.path.isdir(dirnam):
        mess=dirnam+" directory is not found."
        MessageBoxOK(mess,"")
        return []        
    for name in glob.glob(os.path.join(dirnam,"*")):
        if name == "": continue
        if all: filelst.append(name)
        else: 
            base,ext=os.path.splitext(name)
            if ext in extlst: filelst.append(name)
    filelst=PickUpASCIINames(filelst)
    filelst=ReplaceBackslash(filelst)
    #
    return filelst

def GetDirectoriesInDirectory(dirnam):
    """Get all directories in directory 'dirnam'
    
    :param str dirnam: directory name
    :return: dirlst - [dirname1(str),dirname2(str),...]
    """
    dirlst=[]
    if dirnam == '': return []
    if not os.path.isdir(dirnam): return []
    #
    for name in glob.glob(os.path.join(dirnam,"*")): #dirnam+"//*"):
        if name == "": continue
        if os.path.isdir(name): dirlst.append(name)
    dirlst=ReplaceBackslash(dirlst)
    #
    return dirlst

def Editor(filename):
    """ Open system editor
    
    :param str filename: filename to be opened
    """
    platform=GetPlatform()
    if platform == 'WINDOWS':
        # wordpad.exe
        os.spawnv(os.P_NOWAIT,"C://Program Files//Windows NT//Accessories//wordpad.exe",["wardpad.exe"+' '+filename])
        # notepad.exe
        #os.spawnv(os.P_NOWAIT,"C://Windows//System32//notepad.exe",["notepad.exe"+' '+filename])
    elif platform == 'MACOSX':
        prg="open -a TextEdit"
        os.system(prg+" "+filename)
    elif platform == 'LINUX':
        prg="/usr/bin/vim"
        os.system(prg+" "+filename)
    else: 
        MessageBoxOK("lib:Editor(): Editor is not defined for "+platform,"")
        return

def ViewHtmlFile(htmlfile):
    """ View HTML file with default browser of a system
    
    :param str htmlfile: html file
    """
    if GetPlatform() == 'WINDOWS':
        webbrowser.open(htmlfile)
    elif GetPlatform() == 'MACOSX':
        prg="open -a Safari"
        os.system(prg+" "+htmlfile)
    elif GetPlatform() == 'LINUX':
        prg="/usr/bin/iceweasel"
        os.system(prg+" "+htmlfile)
    else:
        mess='I do not know HTML browser.'
        MessageBoxOK(mess,"ViewGAMESSDocument")  
        
def ScreenCaputure(filename):
    """ Execute screen capture program(Mac OSX only)
    
    """
    platform=GetPlatform()
    if platform == 'MACOSX':
        os.system("open /usr/sbin/screencapture -m -C -T0 -x ~/ss/filename")

def ImageThumnail(img,imgsize):
    """ Change size of image object
    
    :param obj img: image object
    :param lst imgsize: [width(int),hight(int)] in pixcels
    :return: image object 
    """
    img.thumbnail(imgsize) #, Image.ANTIALIAS)  
    return img
            
def ExecuteScript1(runshell,script): #,args=''):
    """ Excecute script file (python program)
    
    :param obj runshell: python shell instance
    :param str script: script file name
    :return: out(str) - shell output
    """
    # replace backslash
    script=script.replace('\\','//')
    if not os.path.exists(script):
        mess="Script file '"+script+"' is not found."
        MessageBoxOK(mess,"")
        return          
    method='execfile('+"'"+script+"'"+')'
    mess="Running '"+script+"' ..."
    runshell.run(method)
    out=runshell.GetText()
    return out

def ConsoleInputOfFileNames(prompt='',check=True,wcard=''):
    """ Input file names in shell console. File names deleimiter is a space or a comma. 
        Filename "*" will open filer.

    :param str prompt: prompt message
    :param bool check: True for check exsistence, False do not    
    :param str wcard: wild card
    :return: filelst(lst) - list of filenames
    """
    filename=''; filelst=[]
    print '+++ enter file names(delim=space or comma) '+prompt
    # read file name
    filename=sys.stdin.readline()
    filename=filename.strip() 
    if filename == '': return filelst
    # Remove quorts #filename=self.RemoveQuots(filename)
    filename=RemoveQuots(filename)
    #
    if filename[:1] == '*':
        items=filename.split('.')
        if len(items) <= 1:
           if wcard == '': wcard='all(*.*)|*.*'
        else:
            ext=items[1].strip()
            if ext == '*': wcard='all(*.*)|*.*'
            else: wcard=ext+'(*.'+ext+')|*.'+ext
        # open filer
        filelst=GetFileNames(None,wcard,'r',check,'')                
    else: filelst=SplitStringAtSpacesOrCommas(filename)
    # replace backslash in filename
    #for i in range(len(filelst)):
    filelst=PickUpASCIINames(filelst)
    filelst=ReplaceBackslash(filelst)
    #
    if check:
        exsistfiles=[]
        for file in filelst:
            if not os.path.exists(file):
                print 'File not found. file=',file
            else: 
                if not file in exsistfiles: exsistfiles.append(file)
                else:
                    print 'Removed duplicate filename. file=',file
        filelst=exsistfiles  
    return filelst

def ConsoleInputOfDirectoryName(prmptmess='',check=True):
    """ Input file directory in shell console. Directory name "*" will open filer.

    :param str prompt: prompt message
    :param bool check: True for check exsistence, False do not    
    :return: dirname(str) - directory name
    """
    # read directory name
    dirname=''
    print '+++ enter directory name '+prmptmess
    dirname=sys.stdin.readline()
    dirname=RemoveNull(dirname)
    if len(dirname) <= 0: return dirname
    dirname=RemoveQuots(dirname)
    if dirname[:1] == '*': 
        dirname=GetDirectoryName(None)
        if dirname == '': return dirname
    dirname=ReplaceBackslash(dirname)
    if check:
        if not os.path.isdir(dirname) and dirname != '':
            print 'directory not found. directory name=',dirname
            print 'would you like to create?'
            ans=ConsoleInputOfIntegerOption('1:yes, 2:no',1,2,1)
            if ans == 1:
                os.mkdir(dirname)
                print 'directory is created. directory=',dirname
            else: pass 
    return dirname

def ConsoleInputOfIntegerOption(promptmess,minopt=1,maxopt=2,defopt=1):
    """ Input option in sehll console
    
    :param str promptmess: prompt message, e.g., '1:yes, 2: no, 3:quit'
    :param int minopt: minimum option number
    :param int maxopt: maximum option number, e.g., maxopt=3 for the above example
    :param int defopt: deftalt option number(apply to only ENTER key press)
    :return: opt(int) - entered option number
    """
    print '+++ enter optin number '+promptmess
    #opt=sys.stdin.readline()
    opt=sys.stdin.readline()
    opt=RemoveNull(opt)
    if opt == '': opt=defopt
    try: opt=int(opt)
    except: opt=defopt
    if opt > maxopt or opt < minopt: opt=defopt
    return opt

def ConsoleInputOfStringData(prmptmess=''):
    """ Input string data in shell console. Deleimiter is a space or a comma.
    
    :param str promptmess: prompt message
    :return: strlst(lst) - lits of strimg data
    """
    # input strings: separator can be space ' ' or comma ','.
    strlst=[]
    print '+++ enter strings(delim=space or comma) '+prmptmess
    #data=sys.stdin.readline()
    string=sys.stdin.readline()
    string=RemoveNull(string)
    string=RemoveQuots(string)    
    strlst=SplitStringAtSpacesOrCommas(string)
    return strlst

def SuppressBlanks(text):
    """ Replace succesive blanks with a blank
    
    :param str text: string
    :return: string
    :rtype: str
    """
    outtext=''
    for s in text.split(): outtext=outtext+s+' '
    return outtext.strip()

def PickUpValue(dat,varnam):
    """ Return string just after 'varnam' and before ',' in 'dat'.
    
    :param str dat: data string
    :param str varnam: string
    :return: 'varnam'
    :rtype: str
    """
    value=''
    nv=len(varnam)
    ist=dat.find(varnam)
    if ist >= 0: value=dat[ist+nv:]
    ied=value.find(',')
    if ied >= 0: value=value[:ied]
    return value                 

def PickUpTextBetween(text,startstr,endstr):
    """ Pick up lines between lines having "stratstr" and "endstr" strings
    
    :param str text: text data
    :param str startstr: start string
    :param str endstr: end string
    :return: text list
    :rtype: lst
    """
    rtext=""; start=False
    for ss in text:
        s=ss.strip(); s.replace('\n','')
        if start:
            if endstr != "":
                if s.find(endstr) >=0: start=False
            else:
                if s.strip() == "": start=False
            if not start: continue
        if not start:
            if startstr != "":
                if s.find(startstr) >=0: start=True
            else:
                if s.strip() == "": start=True
            if start: continue
        if start: rtext=rtext+ss+"\n"
    return rtext

def CopyTextToClipboard(text):
    cbobj=wx.TextDataObject()
    cbobj.SetText(text)
    wx.TheClipboard.Open()
    wx.TheClipboard.Clear() # clear clipboard
    wx.TheClipboard.SetData(cbobj)
    #wx.TheClipboard.Flush()
    wx.TheClipboard.Close()

def PasteTextFromClipboard():
    """ Pasete text from clipboad
    
    :return str text: 
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
                const.CONSOLEMESSAGE(mess)
            wx.TheClipboard.Close()
            if not ok: return ''
        except:
            mess='Failed to open clipboard.'
            const.CONSOLEMESSAGE(mess)
            return ''
    return text

def CopyScreenBitmapToClipboard(rect):
    """ Copy screen image to clipboard 
    
    :param obj winobj: wx.Frame object
    """       
    sdc=wx.ScreenDC()
    sw,sh=sdc.Size.Get()
    bmp=wx.EmptyBitmap(sw,sh)
    mdc=wx.MemoryDCFromDC(sdc)
    mdc.SelectObject(bmp)
    
    x=rect[0]; y=rect[1]; w=rect[2]; h=rect[3]
    
    mdc.Blit(x,y,w,h,sdc,0,0)
    mdc.SelectObject(wx.NullBitmap)
    #
    CopyBitmapToClipboard(bmp)
    #
    print 'Screen Bitmap is copied to clipboard.'

def CopyBitmapToClipboard(bmp):
    """ Copy canvas bitmap image to clipboard
    
    :param obj bmp: bitmap image object
    :return: retmess(str) - error message
    """
    retmess=''
    data=wx.BitmapDataObject()
    data.SetBitmap(bmp)
    try:
        wx.TheClipboard.Open()
        wx.TheClipboard.Clear() # clear clipboard
        wx.TheClipboard.SetData(data)
        #wx.TheClipboard.Flush()
        wx.TheClipboard.Close()
    except:
        mess='Error: failed to copy bitmap data to clipboard'
    return retmess

def SaveBitmapAsFile(filename,bmp):
    """ Save bitmap image on file
    
    :param str filename: filename
    :param obj bmp: bitmap object
    """
    bmp.SaveFile(filename,wx.BITMAP_TYPE_BMP)

def FindGrpNmb(ia,grplst):
    # find group number of atom ia
    ig=-1
    if len(grplst) <= 0: return ig
    for i in xrange(len(grplst)):
        for j in grplst[i]:
            if j == ia:
                ig=i; break 
    return ig

def Distance(p1,p2):
    """ Compute distance between two points
    
    :param lst p1: point coordinate
    :param lst p1: point coordinate
    :return: diatance(foat) - distance between p1 and p2
    """
    return math.sqrt((p2[0] - p1[0]) ** 2 +
                     (p2[1] - p1[1]) ** 2 +
                     (p2[2] - p1[2]) ** 2)

def CalcPositionWithNewBL(cc0,cc1,r):
    """ Return point coordinate being distance 'r' from cc0 point along cc0-cc1
    
    :param lst cc0: coordinate of point
    :param lst cc1: coordinate of point
    :param float r: distance between point and cc0
    :return: cc(lst) - coordinate of point, [x(float),y(float),z(float)]
    """
    r0=Distance(cc0,cc1); fc=r/r0
    x=fc*(cc1[0]-cc0[0])+cc0[0]
    y=fc*(cc1[1]-cc0[1])+cc0[1]
    z=fc*(cc1[2]-cc0[2])+cc0[2]
    cc=[x,y,z]
    return cc

def HSVtoRGB(HSVcol):
    """ Convert HSVcol=(H,S,V) color data to RGB(R,G,B) color data

    :param lst HSVcol: [H(float),S(float),V(float)]
    :return: RGBcol(lst) - [R(int),G(int),B(int)], int(0-255)
    :note: H:Hue, S:Saturation,Value.Lightness,Brightness). http://en.wikipedia.org/wiki/HSL_and_HSV
    """
    # H:Hue, S:Saturation,Value.Lightness,Brightness)
    # H:Hue, S:Saturation,Value.Lightness,Brightness)
    # H:0-359(360=0), S:0-1; V:0-1
    # reference: http://en.wikipedia.org/wiki/HSL_and_HSV    
    c=255.0; R=0; G=0; B=0
    H=HSVcol[0]; S=HSVcol[1]; V=HSVcol[2]
    Hi=int((H/60.0) % 6.0)  # residue
    f=H/60.0-int(H/60); p=V*(1.0-S); q=V*(1.0-f*S); t=V*(1.0-(1.0-f)*S)
    if S != 0:
        if Hi == 0: R=V; G=t; B=p
        if Hi == 1: R=q; G=V; B=p
        if Hi == 2: R=p; G=V; B=t
        if Hi == 3: R=p; G=q; B=V
        if Hi == 4: R=t; G=p; B=V        
        if Hi == 5: R=V; G=p; B=q
    R=int(c*R); G=int(c*G); B=int(c*B)
    RGBcol=[R,G,B]        
    return RGBcol

def RGBtoHSV(rgbcol):
    """ Convert color data from RGB to HSV.
    may be wrong some where (10Nov.2012)
    """
    H=0; S=1.0; V=1.0
    frgb=255; fhsv=60; eps=0.000001
    R=rgbcol[0]/frgb; G=rgbcol[1]/frgb; B=rgbcol[2]/frgb
    rgblst=[R,G,B]
    maxrgb=max(rgblst); minrgb=min(rgblst); delta=maxrgb-minrgb
    if delta < eps: 
        hsvcol=(0,0.01,0.75); return hsvcol
    if maxrgb < eps:
        hsvcol=(0,0.01,0.0); return hsvcol
    if abs((maxrgb-R)) <= eps: H=fhsv*(G-B)/delta+0
    if abs((maxrgb-G)) <= eps: H=fhsv*(B-R)/delta+120
    if abs((maxrgb-B)) <= eps: H=fhsv*(R-G)/delta+240
    if H < 0.0: H += 360
    if H > 360: H= (H % 360)
    S=delta/maxrgb   
    hsvcol=[H,S,V]
    return hsvcol
    
def GetExeDir(program):
    exedir=os.getcwd()
    exedir=os.path.abspath(exedir)
    dirnam=os.path.dirname(program)
    dirnam=os.path.abspath(dirnam)
    return dirnam

def GetIconFile(exedir,iconname):
    iconfile=os.path.join(exedir,iconname)
    if not os.path.exists(iconfile):    
        return ""
    else: return iconfile

def MakeFileNameWithDateTime(basename,extname,compact=True):
    # make file name with date and time, 'basename+datetime'.
    # extname, like '.log'
    dt=DateTimeText()
    dt=dt.replace('/','-'); dt=dt.replace(' ','-'); dt=dt.replace(':','-')    
    if compact:
        dt=dt[2:]; dt=dt.replace('-','')
    filename=basename+dt+extname
    return filename

def MakeFileNameFromResDat(resdat):
    filename=''
    resnam,resnmb,chain=UnpackResDat(resdat)
    if chain.islower(): chain='L'+chain
    elif chain.isupper(): chain='U'+chain
    filename=resnam+'-'+str(resnmb)+'-'+chain
    return filename
    
def GetResDatFromFileName(filename):
    items=filename.split('-')
    if len(items) < 3:
        #mess='Wrong file name='+filename
        #MessageBoxOK(mess,'lib.GetResDatFromFileName')
        return None
    resnam=items[0]; chain=items[2]
    if chain[:1] == 'U': chain=chain[1:].upper()
    elif chain [:1] == 'L': chain=chain[1:].lower()
    resdat=resnam+':'+items[1]+':'+chain
    return resdat
            
def MakeMolNamFromFileName(filename):
    """ Make molecue name from filename
    
    :param str filename: fielname
    :return: molnam(str) - molecule name, the base name of the file
    """
    head,tail=os.path.split(filename)
    molnam,ext=os.path.splitext(tail)

    return molnam

def MergeTwoMols(mol1,mol2): #,check):
    """ not used """
    # merge mol to corrent work mol
    grpnam=mol1.mol[0].grpnam
    norg=len(mol1.mol)
    nres=mol1.mol[len(mol1.mol)-1].resnmb
    """
    if check:
        nsht=self.CheckShortContact(mol1,mol2)
        if nsht > 0:
            #srmin='%6.3f' % rmin
            mess='Merge: Short contact occured.' 
            mess=mess+' number of short contacts='+str(nsht)
            #mess=mess+', rmin='+srmin
            ok=wx.MessageBox(mess,"",style=wx.OK|wx.CANCEL|wx.ICON_EXCLAMATION)
            if ok == wx.CANCEL:
                dlg.Destroy(); return
    """
    #print 'mol2',mol2
    for atom in mol2.atm:
        #print 'atom.seqnmb,elm',atom.seqnmb,atom.elm
        atom.seqnmb += norg
        atom.atmnmb=atom.seqnmb
        atom.grpnam=grpnam
        atom.resnmb += nres
        #atom.select=True
        # renumber conect data
        for j in range(len(atom.conect)):
            atom.conect[j] += norg
        # renumber fragment data
        if atom.frgbaa >= 0:
            atom.frgbaa += norg
        mol1.atm.append(atom)
    
    return mol1
                    
def GetProgramPath(prgfile,prgnam,item):
    # get program path in "setfile"
    # setfile format: program GAMESS c:\gamess.64 ...
    if not os.path.exists(prgfile):
        MessageBoxOK('prgfile="'+prgfile+'"is not found.',"")        
        return []
    nprg=len(prgnam); nitem=len(item)
    f=open(prgfile)
    prgdat=''
    for s in f.readlines():
        if len(s) <= 0: continue
        ns=s.find('#')
        if ns > 0: s=s[:ns]
        s=s.strip()
        if len(s) == 0: continue
        if s[0:1] == '#': continue
        np=s.find(prgnam)
        if np >= 0:
            term=s.split(' ')
            del term[0]
            if nitem > 0:
                if term[0].strip() == item:
                    del term[0]
                    prgdat=' '.join(term)
            else:
                prgdat=' '.join(term)    
    f.close()
    
    return prgdat

def GetWinSizeInFile(filename,var):
    #xsize=800; ysize=640; var='fumodel.winsize' # 'fumodel.winsize = (440,300)'
    size=[]
    if not os.path.exists(filename): return size
    nvar=len(var)
    f=open(filename)
    for s in f.readlines():
        if len(s) == 0: continue
        if s[0:1] == "#": continue
        v=s.find(var)
        if v >= 0:
            s=s[v+nvar:]; e=s.find('=')
            if e >= 0:
                s=s[e+1:]; i=s.find("("); j=s.find(")")
                if i >= 0 and j >= 0: s=s[i+1:j]               
                item=s.split(",")
                size=[int(item[0]),int(item[1])]
                break 
    return size

def SplitStringData(data):
    """ do not use this method. use 'SplitStringAtSpacesOrCommas() method """
    item=[]
    data=RemoveNull(data)
    if len(data) <= 0: item.append('')
    else:
        if data.find(',') >= 0:
            item=data.split(',')
            for i in range(len(item)): item[i].strip()
        else: item=data.split()
    return item

def RemoveNull(text):
    """ Remove'\n' and '\r' in string
    
    :param str text: string
    :return: text(str) - string
    """
    text=text.replace('\n',''); text=text.replace('\r','')
    text=text.strip()
    return text

def RemoveQuots(string):
    """ Remove quotes at both ends of a string
    
    :param str string: string
    :return: string(str) - string
    """
    if string[:1] == '"' or string[:1] == "'": string=string[1:]
    if string[-1] == '"' or string[-1] == "'": string=string[:-1]        
    return string
   
def GetStringBetweenQuotation(string):
    """ Pick up strings between quotations in 'string'
    
    :param str string: string data
    :return: strlst(lst) - list of strings
    """
    strlst=[]; quo="'"; dquo='"'
    while len(string) > 0:
        qs=string.find(quo); ds=string.find(dquo)
        if qs < 0 and ds < 0: string=''
        if qs >=0 and qs > ds: 
            string=string[qs+1:]
            qe=string.find(quo)
            if qe >=0:
                ss=string[:qe]; strlst.append(ss)
                string=string[qe+1:]
        if ds >=0 and ds > qs: 
            string=string[ds+1:]
            qe=string.find(dquo)
            if qe >=0:
                ss=string[:qe]; strlst.append(ss)
                string=string[qe+1:]

    return strlst

def GetStringBetweenChars(string,startchar,endchar):
    """ Pick up strings between startchar and endchar in 'string'
    
    :param str string: string data
    :param str startchar: strat character
    :param str endchar: end character
    :return: text(str) - string
    """
    text=''
    st=string.find(startchar)
    ed=string.find(endchar)
    if st < 0 or ed < 0: return text
    if st >= ed: return text
    text=string[st+1:ed]
    return text

def GetKeyAndValue(keydat,conv=True,recoverlist=False):
    """ Return keywrd and value in string
    
    :param str keydat: string including 'keywrd=value'
    :param bool conv: True for convert(str->obj), False do not
    :return: keywrd(str),value(str) - keyword and value 
    """
    key=''; value=''
    if len(keydat) > 0:
        keydat.strip()
        item=keydat.split('=')
        key=item[0].strip()
        value=''; islst=False
        if len(item) > 1:
            value=item[1].strip()
            if value[:1] == '[':
                ns=value.find(']')
                if ns < 0: print 'error (GetKeyAndValue): imbalanced [].'
                value=value[1:ns]
                if recoverlist: 
                    value=StringToList('['+value+']'); islst=True
            if not islst and conv: 
                if value.isdigit(): value=int(value)
                elif value.replace('.','').isdigit(): value=float(value)
                else:
                    if value[:1] == "'" or value[:1] == '"': value=value[1:]
                    if value[-1:] == "'" or value[-1:] == '"': value=value[:-1]
    return key,value
        
def ReadPathInFile(filename):
    """ Read directory names in file
    
    :param str filename: file name
    :return: pathnam(str) - path name
    """
    # read directory name in file "filename"
    pathnam=''
    if os.path.exists(filename):
        f=open(filename,'r')
        for s in f.readlines():
            if len(s) <= 0: continue
            if s[0:1] == "#": continue
            pathnam=s.strip(); break
        f.close()
    return pathnam

def WriteDirectoryOnFile(dirnam,filename):
    """ Write directory name on file
    
    :param str dirnam: directory name
    :param str filename: file name
    """
    #
    f=open(filename,"w")
    f.write(dirnam)
    f.close
               
def SplitAtTER(mnam,pdbmol):
    """
    # 2013.2 KK
    # return molnamdic, moldatdic, delcondic
    # molnamdic: splitted mol name, moldatdic: splitted mol dat, 
    # delcondic: covalent bonds between splited molecules (need to ecover total system)
    # molcomdic: center of mass and three heavy atom coordinates(need to ercover original coordinates)
    """
    molnamdic={}; moldatdic={}; delcondic={}
    nmol=-1; nati=0; moldat=[]; natm=len(pdbmol)
    for i in xrange(natm):
        nati += 1
        if nati == 1:
            ini=pdbmol[i][1][0]
        moldat.append(list(pdbmol[i]))
        #
        elm=pdbmol[i][3][0]
        lasta=False
        if i == natm-1: lasta=True
        if elm == 'XX' or (lasta and len(moldat)) > 0:
            dellst=[]
            for j in xrange(len(moldat)): 
                #dellst=[]
                tmp=list(moldat[j][1])
                kk=-1; deltmp=[]
                for k in range(len(moldat[j][1])):
                    kk += 1
                    moldat[j][1][k] -= ini
                    tmp[kk] -= ini
                    if tmp[kk] >= nati or tmp[kk] < 0:
                        del tmp[kk]; kk -= 1             
                        deltmp.append(moldat[j][1][0]+ini)
                        deltmp.append(moldat[j][1][k]+ini)
                        #
                        dellst.append(deltmp)
                moldat[j][1]=tmp
                #
            nmol += 1
            moldatdic[nmol]=moldat
            nmb='%02d' % nmol
            molnamdic[nmol]=mnam+'_'+nmb
            delcondic[nmol]=dellst
            moldat=[]
            nati=0
        
    return molnamdic,moldatdic,delcondic
    
def AtmNamElm(atmnam):
    """ Make element data from atmnam data in pdb
    
    :param str atmnam: atom name of PDB form
    :return: elm(str) - element name)right adjusted two characters)
    """
    # return element name, elm
    elmchr2={'HE':0,'LI':1,'BE':2,'NE':3,'NA':4,'MG':5,'AL':6,'SI':7,'CL':8,
             'AR':9,'CA':10,'SC':11,'TI':12,'CR':13,'MN':14,'FE':15,'CO':16,
             'NI':17,'CU':18,'ZN':19,'GA':20,'GE':21,'AS':22,'SE':23,'BR':24,
             'KR':25,'RB':26,'SR':27,'ZR':28,'NB':29,'MO':30,'TC':31,'RU':31,
             'RH':33,'PD':34,'AG':35,
             #'CD':36,
             'IN':37,'SN':38,'SB':39,'TE':40,
             'XE':41,'CS':42,'BA':43,'LA':44,
             #'CE':45,
             'PR':46,'ND':47,'PM':48,
             'SM':49,'EU':50,'GD':51,'TB':52,'DY':53,'HO':54,'ER':55,'TM':56,
             'YB':57,'LU':58,'HF':59,'TA':60,'RE':61,'OS':62,'IR':63,'PT':64,
             'AU':65,'HG':66,'TL':67,'PB':68      }  
    """
    elm="12"
    if atmnam[0:2] in elmchr2:
        elm.replace('12',atmnam[0:2])
    else:
        elm=elm.replace('1',atmnam[1:2])
        elm=elm.replace('2',' ')
        if elm == ' D': elm=' H'
    """
    tmp=atmnam[0:2]
    if elmchr2.has_key(tmp):
        elm=tmp[0:2]
    else:
        tmp.strip()
        elm=' '+tmp[1:2]
    #
    return elm

def ConvertPDBAtmNam(tonew):
    """ Return dictionary of new and old PDB atom names.
    
    :param bool tonew: True for old to new name, False for new to old name
    :return: atmnamdic(dic) - atom name dictonary {[new(or old),old(new)],...}
    """
    atmnamdic={}
    old2new=[['1HB ',' HB1'],['2HB ',' HB2'],['3HB ',' HB3'],
             ['1HA ',' HA1'],['2HA ',' HA2'],[' HA3',' HA3'],
             ['1HG2','HG21'],['2HG2','HG22'],['3HG2','HG23'],
             ['1HD1','HD11'],['2HD1','HD12'],['3HD1','HD13'],
             ['1HD2','HD21'],['2HD2','HD22'],['3HD2','HD23'],
             ['1HG1','HG11'],['2HG1','HG12'],['3HG1','HG13'],
             ['1HG2','HG21'],['2HG2','HG22'],['3HG2','HG23'],
             ['1HG ',' HG1'],['2HG ',' HG2'],['3HG ',' HG3'],
             ['1HE2','HE21'],['2HE2','HE22'],['3HE2','HE23'],
             ['1HD ',' HD1'],['2HD ',' HD2'],['3HD ',' HD3'],
             ['1HH1','HH11'],['2HH1','HH12'],['3HH1','HH13'],
             ['1HH2','HH21'],['2HH2','HH22'],['3HH2','HH23'],
             ['1HE ',' HE1'],['2HE ',' HE2'],['3HE ',' HE3'],
             ['1HZ ',' HZ1'],['2HZ ',' HZ2'],['3HZ ',' HZ3']       
             ]

    if tonew:
        for old,new in old2new: atmnamdic[old]=new
    else: 
        for old,new in old2new: atmnamdic[new]=old
    
    return atmnamdic
    
def RotMol(u,cnt,coord):
    """ Transform coordinates by transformation matrix.
    
    :param lst u: transformation matrix
    :param lst cnt: center of rotation coordinate, [x(float),y(float),z(float)]
    :param lst coord: list of coordinates, [x(float),y(float),z(float)],...]
    :return: xyz(lst) - coordinate list, [x(float),y(float),z(float)],...]
    """
    xyz=[]
    for i in xrange(len(coord)):
        cc=[]; cd=[]
        cc=numpy.zeros(3); cd=numpy.zeros(3)
        cc=numpy.subtract(coord[i],cnt)
        cd=numpy.add(cd,cnt)        
        ###
        cc[0]=coord[i][0]-cnt[0]
        cc[1]=coord[i][1]-cnt[1]
        cc[2]=coord[i][2]-cnt[2]
        u=numpy.array(u); cc=numpy.array(cc)      
        cd=numpy.dot(u,cc)
        cd[0] += cnt[0]; cd[1] += cnt[1]; cd[2] += cnt[2]
        ###
        xyz.append(cd)
    # 
    return xyz
        
def RotMatX(a):
    """ Return rotation matrix around x-axis
    
    :param float a: rotation angles
    :return: ux(lst) - rotation matrix
    """

    cosa=numpy.cos(a); sina=numpy.sin(a)
    ux=numpy.identity(3,numpy.float64)
    ux[1,1]=cosa; ux[1,2]=sina; ux[2,2]=cosa; ux[2,1]=-sina
    return ux

def RotMatY(b):
    """ Return rotation matrix around y-axis
    
    :param float b: rotation angles
    :return: uy(lst) - rotation matrix
    """
    cosa=numpy.cos(b); sina=numpy.sin(b)
    uy=numpy.identity(3,numpy.float64)
    uy[0,0]=cosa; uy[0,2]=sina; uy[2,2]=cosa; uy[2,0]=-sina
    return uy

def RotMatZ(c):
    """ Return rotation matrix around z-axis
    
    :param float c: rotation angles
    :return: uz(lst) - rotation matrix
    """
    cosa=numpy.cos(c); sina=numpy.sin(c)
    uz=numpy.identity(3,numpy.float64)
    uz[0,0]=cosa; uz[0,1]=sina; uz[1,1]=cosa; uz[1,0]=-sina
    return uz

def RotMatEul(a,b,c):
    """ Return rotation matrix of euler angles
    
    :param float a: angle alpha
    :param float b: angle beta
    :param float c: angle gamma
    :return: matrix(lst) - rotation matrix
    :note: not tested. July27,2012.
    """
    u=numpy.identity(3,numpy.float64)
    sa=numpy.sin(a); ca=numpy.cos(a); sb=numpy.sin(b)
    cb=numpy.cos(b); sc=numpy.sin(c); cc=numpy.cos(c)      
    u[0,0]= cb*cc-ca*sb*sc; u[0,1]=-sc*cb-ca*sb*cc; u[0,2]= sa*sb
    u[1,0]= sb*cc+ca*cb*sc; u[1,1]=-sc*sb+ca*cb*cc; u[1,2]=-sa*cb
    u[2,0]= sa*sc; u[2,1]= sa*cc; u[2,2]= ca      
    return u

def AngleT(ra,rb):
    """ Compute angle between two vectoes
    
    :param lst ra,rb: vector [x(float),y(float),z(float)]
    :return: angle(float) - angle in radian
    :note: not tested(July27,2012) 
    """
    # return angle t between two vectors ra and rb """
    t=0.0; eps12=1.0e-12; eps18=1.0e-18; tone=0.9999999999
    ra2=numpy.dot(ra,ra); rra=numpy.sqrt(ra2)
    rb2=numpy.dot(rb,rb); rrb=numpy.sqrt(rb2)
    rab=numpy.subtract(ra,rb); rab2=numpy.dot(rab,rab); rarb=rra*rrb
    if rab2 < eps18 or rarb < eps12: return t
    t=(ra2+rb2-rab2)/(2.0*rarb)
    if t > tone: t=tone
    if t < -tone: t=-tone
    if abs(t) < eps12: t=0.0
    t=numpy.arccos(t)
    return t    

def TorsionAngleT(cc1,cc2,cc3,cc4):
    # dihedral angle of atm0-atm1-atm2-atm3 in radians
    angle=0.0
    x1=cc1[0]; y1=cc1[1]; z1=cc1[2]
    x2=cc2[0]; y2=cc2[1]; z2=cc2[2]
    x3=cc3[0]; y3=cc3[1]; z3=cc3[2]
    x4=cc4[0]; y4=cc4[1]; z4=cc4[2]
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
    return angle

def TorsionRotation(cc1,cc2,cc3,angle):
    """ Rotate cc1 by angle in cc1-cc2-cc3 torsion angle
    
    :param lst cc1,cc2,cc3: coordinate list, [x(float),y(float),z(float)]
    :param float angle: torsion angle
    :return: xyz(lst) - coordinates [x(float),y(float),z(float)] of cc1
    """
    v=numpy.subtract(cc2,cc3)
    u=RotMatAxis(v,angle) # v:axis, a:angle
    cnt=cc2
    xyz=RotMol(u,cnt,cc1)
    return xyz

def RotMatAxis(v,t):
    """ Return  transfomation matrix u for rotation by t (radian) around vector v.
    
    :param lst v: axis vector, [x(float),y(float),z(float)]
    :param float t: rotation angle
    :return: u(lst) - transformatiom matrix
    """
    eps12=1.0e-12
    u=numpy.identity(3)
    if abs(t) < eps12: return u
    v2=numpy.dot(v,v)
    if v2 < eps12 : return u
    v /= numpy.sqrt(v2)
    cost=numpy.cos(t); sint=numpy.sin(t); cosx=1.0-cost
    u[0][0]=v[0]*v[0]*cosx+cost
    u[0][1]=v[0]*v[1]*cosx-v[2]*sint
    u[0][2]=v[0]*v[2]*cosx+v[1]*sint
    u[1][0]=v[0]*v[1]*cosx+v[2]*sint
    u[1][1]=v[1]*v[1]*cosx+cost
    u[1][2]=v[1]*v[2]*cosx-v[0]*sint
    u[2][0]=v[0]*v[2]*cosx-v[1]*sint
    u[2][1]=v[1]*v[2]*cosx+v[0]*sint
    u[2][2]=v[2]*v[2]*cosx+cost

    return u

def RotMatPnts(refpnt,newpnt):
    """ Return transformation matrix u to transform three coordinates to new three points
    
    :param lst refpnt: coordinate of reference point, [[x1(float),y1(float),z1(float)],...] 
    :param lst newpnt: coordinate of new point, [[x1(float),y1(float),z1(float)],..] 
    :return: u(lst) - transformation matrix
    """
    epst=1.0e-9
    u=numpy.identity(3); u1=numpy.identity(3); u2=numpy.identity(3)
    ra=numpy.zeros(3); rb=numpy.zeros(3); rc=numpy.zeros(3)
    npnt=len(refpnt)
    xr1=numpy.array(refpnt[0]); xr2=numpy.array(refpnt[1])
    xn1=numpy.array(newpnt[0]); xn2=numpy.array(newpnt[1])
    if npnt >= 3:
        xr3=numpy.array(refpnt[2])
        xn3=numpy.array(newpnt[2])
    ra=numpy.subtract(xr2,xr1); rb=numpy.subtract(xn2,xn1)
    t=AngleT(ra,rb)

    if abs(t) > epst:
        rc=numpy.cross(ra,rb)
        u1=TrnMat(rc,ra,rb)
    if npnt <= 2: return u1
    ra=numpy.subtract(xr3,xr1); rb=numpy.subtract(xr2,xr1)
    t=AngleT(ra,rb)
    if abs(t) < epst or abs(t-numpy.pi) < epst: return u1
    ra=numpy.dot(u1,ra); 
    rb=numpy.subtract(xn2,xn1); rc=numpy.subtract(xn3,xn1)
    u2=TrnMat(rb,ra,rc)
    u=numpy.dot(u2,u1)
    return u
     
def TrnMat(ra,ri,rf):
    """ Return transformation matrix u to transform vector ri to rf around axis ra, i.e. rf=u*ri.
    
    :param lst ra: axis vector for rotation, [x(float),y(float),z(float)]
    :param lst ri: initial vector, [x(float),y(float),z(float)]
    :param lst rf: final vetor, [x(float),y(float),z(float)]
    :return: u(lst) - transfoemation matrix
    """
    ey=[0.0,1.0,0.0]; ez=[0.0,0.0,1.0]
    u=numpy.zeros(3)
    raxyz=numpy.zeros(3); rixyz=numpy.zeros(3); rfxyz=numpy.zeros(3)
    vec=numpy.zeros(3); v1=numpy.identity(3); u1=numpy.identity(3)
    raxyz[0]=ra[0]; raxyz[1]=ra[1]; raxyz[2]=0.0
    t=AngleT(raxyz,ey); vec=numpy.cross(raxyz,ey)
    if vec[2] < 0.0: t=2.0*numpy.pi-t
    cost=numpy.cos(t); sint=numpy.sin(t)
    v1[0][0]=cost; v1[0][1]=-sint; v1[1][0]=sint; v1[1][1]=cost 
    ra=numpy.dot(v1,ra); ri=numpy.dot(v1,ri); rf=numpy.dot(v1,rf)
    v2=numpy.identity(3)
    t=AngleT(ra,ez); vec=numpy.cross(ra,ez)
    if vec[0] < 0.0: t=2.0*numpy.pi-t
    cost=numpy.cos(t); sint=numpy.sin(t)
    v2[1][1]=cost; v2[1][2]=-sint; v2[2][1]=sint; v2[2][2]=cost
    ri=numpy.dot(v2,ri); rf=numpy.dot(v2,rf)
    v3=numpy.identity(3)
    rixyz[0]=ri[0]; rixyz[1]=ri[1]; rixyz[2]=0.0
    rfxyz[0]=rf[0]; rfxyz[1]=rf[1]; rfxyz[2]=0.0
    t=AngleT(rixyz,rfxyz); vec=numpy.cross(rixyz,rfxyz)
    if vec[2] < 0.0: t=2.0*numpy.pi-t
    cost=numpy.cos(t); sint=numpy.sin(t)
    v3[0][0]=cost; v3[0][1]=-sint; v3[1][0]=sint; v3[1][1]=cost
    u1=numpy.dot(numpy.transpose(v1),numpy.transpose(v2))
    u=numpy.dot(u1,v3)
    u1=numpy.dot(u,v2)
    u=numpy.dot(u1,v1)
    return u

def CenterOfMassAndPMI(atmas,coord):
    """ Compute center-of-mass ccordinate and proncepal moment of inertia.
    
    :param lst atoms: atomic mass
    :param lst coord: coordinate list [[x(float),y(float),z(float),...]
    :return: com - center of mass coordinate [x(float),y(float),z(float)]
    :retun: eig(lst) - eigenvalue list of moment of inertia matrix
    :return: vac(lst) - eigenvector lsit of moment of inertia matrix
    """
    pmi=numpy.array([[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]])
    mx=0.0; my=0.0; mz=0.0; sm=0.0
    for i in xrange(len(atmas)):
        ms=atmas[i]
        x=coord[i][0]; y=coord[i][1]; z=coord[i][2]
        mx += ms*x; my += ms*y; mz += ms*z; sm += ms
    # center of mass
    sm=1.0/sm
    com=[mx*sm,my*sm,mz*sm]
    # moment of inertia tenosr
    for i in xrange(len(atmas)):
        ms=atmas[i]*sm
        x=coord[i][0]-com[0]
        y=coord[i][1]-com[1]
        z=coord[i][2]-com[2] 
        pmi[0][0] += ms*(y*y+z*z)
        pmi[1][1] += ms*(z*z+x*x)
        pmi[2][2] += ms*(x*x+y*y)
        pmi[0][1] -= ms*x*y
        pmi[0][2] -= ms*x*z
        pmi[1][2] -= ms*y*z   
    pmi[1][0]=pmi[0][1]; pmi[2][0]=pmi[0][2]; pmi[2][1]=pmi[1][2]     
    # note: vec[:][i] is eigen vector corrsponding to eigenvalue eig[i].
    #       and the eigenvalues are not ordered in acending (random)    
    try:
        eig,vec=numpy.linalg.eig(pmi)
        seig=[[0,eig[0]],[1,eig[1]],[2,eig[2]]]
        seig.sort(key=lambda x:x[1])
        order=[seig[0][0],seig[1][0],seig[2][0]]
        svec=numpy.array([[0.0,0.0,0.0],[0.0,0.0,0.0],[0.0,0.0,0.0]])
        for i in range(3):
            for j in range(3): svec[i][j]=vec[j][i]
        eig[0]=seig[0][1]; eig[1]=seig[1][1]; eig[2]=seig[2][1]
        for i in range(3):
            for j in range(3): vec[i][j]=svec[order[i]][j]
        # now vec[i][:] is eigenvector corresponding to i-th eigenvalue 
        return com,eig,vec
    except:
        mess=" coord data may be wrong" 
        return [],[],[]
    
def CovalentBondedAtomList(elm,coord):
    """ Return covalen bonded atom pairs and bond length
    
    :param lst elm: [' H','NA',...]
    :param lst coord: coordinates, [[x(float),y(float),z(float)],...]
    :return: bndlst(lst) - atom pair i,j and distance r,[i(int),j(int),r(float)]
    """
    nat=len(coord); bndlst=[]
    for i in xrange(nat):
        xi=coord[i][0]; yi=coord[i][1]; zi=coord[i][2]
        try:
            cri=const.ElmCov[elm[i]]
        except:
            print "Program error in ElmCov: elm=",elm
            continue
        for j in xrange(i+1,nat):
            xj=coord[j][0]; yj=coord[j][1]; zj=coord[j][2]
            crj=const.ElmCov[elm[j]]
            rij=numpy.sqrt((xi-xj)**2+(yi-yj)**2+(zi-zj)**2)
            crij=cri+crj; fac=1.10 #1.05
            if rij < crij*fac:
                tmp=[]
                tmp.append(i); tmp.append(j); tmp.append(rij)
                bndlst.append(tmp)
    return bndlst

def InterResdueDistance(ires,jres):
    """ not used """
    # shortest interatomic contact between two residues ires and jres
    return 'xxx'

def DihedralAngle(iatm,jatm,katm,latm):
    """ not used """
    # return dihedral angle of iatm-jatom-katm-latm.
    print 'xxx'
    #return angle(in degrees?)
def TorsionAngle(cc1,cc2,cc3,cc4):
    """ Compute tortion angle
    
    :param lst cc1,cc2,cc3,cc4: coordinate lists [x,y,z] of four atoms (angstroms)
    :return: angle(float) - dihedral angle of atm0-atm1-atm2-atm3 in radians
    """
    angle=0.0
    x1=cc1[0]; y1=cc1[1]; z1=cc1[2]
    x2=cc2[0]; y2=cc2[1]; z2=cc2[2]
    x3=cc3[0]; y3=cc3[1]; z3=cc3[2]
    x4=cc4[0]; y4=cc4[1]; z4=cc4[2]
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
    return angle

def BendingAngle(cc1,cc2,cc3):
    """ Compute bending angle of cc1-cc2-cc3
     
    :param lst cc1,cc2,cc3: coordinate list [x,y,z] of three atoms (angstroms) 
    :return: angle(float) - angle of cc1-cc2-cc3 in radian
    """
    r21=numpy.array(cc1)-numpy.array(cc2)
    r32=numpy.array(cc3)-numpy.array(cc2)
    numpy.array(r21); numpy.array(r32) 
    angle=AngleT(r21,r32)
    return angle
        
def DihedralAngleOfCA(ires,jres,kres,lres):
    """ not used """
    # dihedral angle of four CA atoms
    print 'Use DihedralAngle Method'
#    return angle(in degrees?)
def DihedralAngleMainChain():
    """ not used """
    # return phi,psi,omega angles
    print ' use DihedralAngle Method'

def OrientOrg(pdborg,pdbdrv):
    # copied as wfwin.OrgOrient
    print 'lenpdborg,lenpdbderiv',len(pdborg),len(pdbdrv)
    nat1=0
    nat3=len(pdborg)-2
    nat2=nat3/2
    
    nat2=241
    nat3=818 
    coordorg=[]
    coordorg.append(list(pdborg[nat1][0]))
    coordorg.append(list(pdborg[nat2][0]))
    coordorg.append(list(pdborg[nat3][0]))
    resorg1=pdborg[nat1][2][2]; resnmborg1=pdborg[nat1][2][3]; atm1=pdborg[nat1][2][0]
    resorg2=pdborg[nat2][2][2]; resnmborg2=pdborg[nat2][2][3]; atm2=pdborg[nat2][2][0]
    resorg3=pdborg[nat3][2][2]; resnmborg3=pdborg[nat3][2][3]; atm3=pdborg[nat3][2][0]
    pntn=[]; pntr=[]
    coord=[]
    for i in xrange(len(pdbdrv)):
        res=pdbdrv[i][2][2]; nmb=pdbdrv[i][2][3]; atm=pdbdrv[i][2][0]
        if res == resorg1 and nmb == resnmborg1 and atm == atm1:
            coord.append(list(pdbdrv[i][0]))

        if res == resorg2 and nmb == resnmborg2 and atm == atm2:
            coord.append(list(pdbdrv[i][0]))

        if res == resorg3 and nmb == resnmborg3 and atm == atm3:
            coord.append(list(pdbdrv[i][0]))

    pntn=[]; pntr=[]
    for i in range(3):
        pntr.append(numpy.subtract(coord[i],coord[0]))
        pntn.append(numpy.subtract(coordorg[i],coordorg[0]))

    print 'org[0]',coordorg[0][0],coordorg[0][1],coordorg[0][2]
    print 'drv[0]',coord[0][0],coord[0][1],coord[0][2]
    print 'org[1]',coordorg[1][0],coordorg[1][1],coordorg[1][2]
    print 'drv[1]',coord[1][0],coord[1][1],coord[1][2]
    print 'org[2]',coordorg[2][0],coordorg[2][1],coordorg[2][2]
    print 'drv[2]',coord[2][0],coord[2][1],coord[2][2]

    u=RotMatPnts(pntr,pntn)
    coordx=[]; rc=[]
    rc.append(0.0)
    rc.append(0.0)
    rc.append(0.0)
    for i in xrange(len(pdbdrv)):
        cc=numpy.subtract(pdbdrv[i][0],coord[0])
        coordx.append(cc)
    coordx=RotMol(u,rc,coordx)                   
    print 'coordx[0]',coordx[0][0],coordx[0][1],coordx[0][2]
    print 'coordx[1]',coordx[1][0],coordx[1][1],coordx[1][2]
    print 'coordx[2]',coordx[2][0],coordx[2][1],coordx[2][2]
    for i in xrange(len(pdbdrv)):
        pdbdrv[i][0]=numpy.add(coordx[i],coordorg[0])
        
    print 'drv[0]',pdbdrv[0][0],pdbdrv[0][1],pdbdrv[0][2]
    print 'drv[1]',pdbdrv[1][0],pdbdrv[1][1],pdbdrv[1][2]
    print 'drv[2]',pdbdrv[2][0],pdbdrv[2][1],pdbdrv[2][2]

    return pdbdrv              

def SplitRes(molnam,pdbmol):
    """ split pdbmol data at null resnam. """   
    # return molnamdic, moldatdic, delcondic
    # molnam: name of pdb molecule, pdbmol: pdbmol data
    # molnamdic: splitted mol name, moldatdic: splitted mol dat, 
    # delcondic: covalent bonds between splited molecules (need to ecover total system)
    # molcomdic: center of mass and three heavy atom coordinates(need to ercover original coordinates)
    # lst: 1,1129,... for split 1-1128,1129-1125,1191-2035,...
    molnamdic={}; moldatdic={}
    nmol=0; nati=0; moldat=[]; natm=len(pdbmol)
    pres=pdbmol[0][2][2]; pnmb=pdbmol[0][2][3]; nati=0; ini=0

    for i in xrange(natm):
        res=pdbmol[i][2][2]; resnmb=pdbmol[i][2][3]
        if res != pres or resnmb != pnmb:
            #
            nmb='%03d' % nmol
            molnamdic[nmol]=molnam+'_'+nmb
            ini=moldat[0][1][0]
            for j in xrange(len(moldat)):
                for k in range(len(moldat[j][1])):
                    moldat[j][1][k] -= ini
            moldatdic[nmol]=moldat
            #
            moldat=[]
            nati=0
            nmol += 1
        pres=res; pnmb=resnmb
        nati += 1
        moldat.append(list(pdbmol[i]))
        
    if len(moldat) > 0: 
        #nmol += 1
        ini=moldat[0][1][0]
        for j in xrange(len(moldat)):
            for k in range(len(moldat[j][1])):
                moldat[j][1][k] -= ini
        moldatdic[nmol]=moldat
        nmb='%03d' % nmol
        molnamdic[nmol]=molnam+'_'+nmb
            
    return molnamdic,moldatdic

def ExtractWaters(molnam,pdbmol):
    """ Separate solute(s) and  waters in PDB Data.
    
    :param str molnam: molecule name
    :param lst pdbmol: pdbmol data
    :return: watdat(lst) - pdbmol data of waters
    :return: moldat(lst) - pdbmol data of silute(s)
    :seealso: lib.ReadPDBMol() for 'pdbmol' data
    """
    watdat=[]; moldat=[]; natm=len(pdbmol); nwat=0; nmat=0
    nhyd=0; nheavy=0
    for i in xrange(natm):
        res=pdbmol[i][2][2]
        if pdbmol[i][3][0] == 'XX': continue
        if res == 'HOH' or res == 'WAT':
            nwat += 1
            watdat.append(list(pdbmol[i]))
        else:
            nmat += 1
            elm=pdbmol[i][3][0]
            if elm == ' H': nhyd += 1
            else: nheavy += 1
            moldat.append(list(pdbmol[i]))     
    print ' Number of water and solute atoms: nwat, nmat',nwat,nmat
    print ' Numerof hydrogen and heavy atoms in solute',nhyd,nheavy
    return watdat,moldat
    
def DateTimeText():
    """ return date and time in the form of '2013/12/08 09:51:34'
    
    :return: datetime(str) - datetime in string
    """
    date=datetime.datetime.today()
    return date.strftime("%Y/%m/%d %H:%M:%S")

def CreatedByText():
    """ return user name, date and time
    
    :return: string(str)  - 'created by user-name at 2013/12/08 09:51:34'
    :seealso: DateTimeText()
    """

    text='Created by '+getpass.getuser()+' at '+DateTimeText()
    return text

def WritePDB(pdbmol,filename,con):
    """ Write PDB file
    
    :param lst pdbmol: pdbmol data
    :param str filename: filename
    :param bool con: True for write connect data, False for not
    :seealso: lib.ReadPDBMol() for 'pdbmol' data
    """
    con=False # True case is not completed
    
    blk=' '; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; ff8='%8.3f'; ff6='%6.2f'
    ires=0
    conect=[]
    f=open(filename,'w')
    #d=datetime.datetime.now()
    s='REMARK Created by fu at '+DateTimeText()+'\n' #'\r'+'\n'
    f.write(s)
    natm=len(pdbmol[0])
    for i in xrange(natm):
        #s=blk*80
        s=MakePDBAtomRecord(pdbmol,i)
        s=s+'\n'
        f.write(s)
    # CONECT
    if con:
        for i in range(len(conect)):
            if len(conect) > 0:   
                s='CONECT'
                #s=s+fi5 % atom.seqnmb
                #for j in range(len(atom.conect)):
                #    s=s+fi5 % atom.conect[j]
                s=s+'\n'
                f.write(s)
    f.write('END'+'\n')
    
    f.close()

def MakePDBAtomRecord(pdbmol,i):
    """ Make string for PDB 'ATOM' record.
    
    :param lst pdbmol: pdbmol data
    :param int i: i-th atom
    :return: string(str) - PDB 'ATOM' record
    """
    blk=' '; fi4='%4d'; fi3='%3d'; fi2='%2d'; fi5='%5d'; ff8='%8.3f'; ff6='%6.2f'    
    s=blk*80; ires=0
    seqnmb=i+1
    cc=pdbmol[0][i]; connect=pdbmol[1][i]; atmnam=pdbmol[2][i]
    atmnmb=pdbmol[3][i]; resnam=pdbmol[4][i]; resnmb=pdbmol[5][i]
    chainnam=pdbmol[6][i]; altloc=pdbmol[7][i]; elm=pdbmol[8][i]
    focc=pdbmol[9][i]; bfc=pdbmol[10][i]; charge=pdbmol[11][i]
    #
    if elm == 'XX':
        s='TER'+3*blk
        st=fi5 % seqnmb
        s=s+st[0:5] # s[6:11], atom seq number
        s=s+blk
        st=4*blk 
        s=s+st[0:4] # s[12:16] atmnam  
        st=altloc 
        s=s+blk  #s=s+st[0:1] # s[16:17], alt location           
        st=resnam 
        s=s+st[0:3] # s[17:20], resnam
        s=s+blk+chainnam 
    else:        
        rec='HETATM'
        if const.AmiRes3.has_key(resnam):
            ires += 1; rec='ATOM  '
        s=rec[0:6] # s[0:6], rec name
        st=fi5 % seqnmb
        s=s+st[0:5] # s[6:11], atom seq number
        s=s+blk
        st=atmnam+4*blk
        s=s+st[0:4] # s[12:16] atmnam  
        st=altloc
        s=s+blk  #s=s+st[0:1] # s[16:17], alt location           
        st=resnam+3*blk
        s=s+st[0:3] # s[17:20], resnam
        s=s+blk+chainnam
        st=fi4 % resnmb+4*blk
        s=s+st[0:4] #s[22:26] resnumb
        s=s+blk # s[26:27], anchar 
        s=s+3*blk
        s=s+ff8 % cc[0] ##s[30:38] x coord
        s=s+ff8 % cc[1] #s[38:46] y coord
        s=s+ff8 % cc[2] #s[46:54] z coord
        s=s+ff6 % focc #s[54:60] occupancy
        s=s+ff6 % bfc #s[60:66] temperature factor
        s=s+10*blk
        st=elm
        st=st.strip(); st=st.rjust(2)+2*blk
        s=s+st[0:2] #s[76:78] element
        s=s+fi2 % charge #s[78:80] charge
        #
    return s

def ResolveResidueName(res):
    """ Separate residue name, number and chain in 'res'. 
    
    :param str res: full residue name used in FU ('resnam:resnmb:chain')
    :return: resnam(str),resnmb(int),chain(str) - residue name, residue number, chain name
    :seealso: lib.PackResDat()
    """
    # res: resnam:resnmb:chain -> resnam,resnum, chain name
    resnam=''; resnmb=-1; chain=''
    if len(res) > 0:
        item=res.split(':')
        resnam=item[0]
        if len(item) > 1:
            if item[1][0] == '*': resnmb=-1
            else: resnmb=int(item[1]) 
        if len(item) > 2:
            chain=item[2]
    return resnam,resnmb,chain
 
def CenterOfMassCC(mass,cc):
    """ Compute center-of-mass ccordinate
    
    :param lst mass: list of mass
    :param lst cc: coordinate list [[x(float),y(float),z(float),...]
    :return: coord(lst) - center of mass coordinate [x(float),y(float),z(float)]
    """
    # mass:[mass1,mass2,...]
    # cc:[cc1[x,y,z],cc2[x,y,z],..]
    coord=copy.deepcopy(cc)
    com,eig,vec=CenterOfMassAndPMI(mass,coord)
    #self.com=com[:]
    pp1=vec[0]; pp2=vec[1]; pp3=vec[2]
    for i in xrange(len(coord)):
        coord[i][0] -= com[0]; coord[i][1] -= com[1]; coord[i][2] -= com[2]
    # rotarion matrix, rot
    ze=[0.0,0.0,0.0]; p1=[ze,pp3]
    zaxis=[0.0,0.0,1.0]; p2=[ze,zaxis]
    u=RotMatPnts(p1,p2)
    pp2=numpy.dot(u,pp2)
    xaxis=numpy.array([1.0,0.0,0.0])
    t=AngleT(pp2,xaxis)
    v=RotMatZ(-t)
    rot=numpy.dot(v,u)
    # rotate molecule
    ctr=[0.0,0.0,0.0]
    coord=RotMol(rot,ctr,coord)
    
    return coord

def ExpandResList(reslst,molobj):
    """ Expand resdat
    
    :param str reslst: list of resdat,['ALAL:*:*', 'ALAL:10:* 'ALAL:10:A',
                                           'ALAL:*:A',..]
    :return resdatlst: resdatlst - expanded resdat ,[ALAL:10:A,ALAL:12:A,..]
    """
    def RemoveQuort(text):
        text=text.replace("'",'')
        text=text.replace('"','')
        return text
    
    def AppendToList(molobj,resitems,case):
        # case 1: UNL, 2: UNL:10, 3: UNL:10:A, 4: UNL:*:A
        reslst=[]; donedic={}
        for atom in molobj.atm:
            res=atom.resnam; nmb=atom.resnmb; cha=atom.chainnam
            resdat=ResDat(atom)
            if donedic.has_key(resdat): continue
            if case == 1: # UNL
                resnam=resitems[0]
                if res == resnam: reslst.append(resdat)
            elif case == 2: # UNL:10 or UNL:10:*
                resnam=resitems[0]; resnmb=resitems[1]
                if res == resnam and nmb == resnmb: reslst.append(resdat)
            elif case == 3: # UNL:10:A    
                resnam=resitems[0]; resnmb=resitems[1]; chain=resitems[2]
                if res == resnam and nmb == resnmb and cha == chain:
                    reslst.append(resdat)
            elif case == 4: # UNL:*:A
                resnam=resitems[0]; chain=resitems[2]
                if res == resnam and cha == chain: reslst.append(resdat)
            else: pass
            donedic[resdat]=True
        return reslst

    def ErrorMessage(case,res):
        if case == 0: mess='Wrong resnam='+res
        elif case == 1: mess='Wrong resnum='+res
        MessageBoxOK(mess,'Lib.ExpandResDatList')
    #
    resdatlst=[]
    for res in reslst:
        res=RemoveQuort(res)
        items=res.split(':')
        nitems=len(items); resitems=[]
        for i in range(len(items)):
            if i == 1:
                try:
                    nmb=int(items[1]); resitems.append(nmb)
                except: resitems.append(-1)
            else: resitems.append(items[i].strip())    
        if len(resitems[0]) <= 0: 
            ErrorMessage(0); return []
        if nitems == 1: lst=AppendToList(molobj,resitems,1)
        elif nitems >= 2:
            if items[1].strip() == '*': 
                lst=AppendToList(molobj,resitems,1)
            else: lst=AppendToList(molobj,resitems,2)
        elif nitems == 3:
            if items[1].strip() == '*' and items[2].strip() == '*': 
                lst=AppendToList(molobj,resitems,1)
            elif items[1].strip() == '*' and items[2].strip() != '*':
                lst=AppendToList(molobj,resitems,4)
            elif items[1].strip() != '*' and items[2].strip() == '*':
                lst=AppendToList(molobj,resitems,2)        
        resdatlst=resdatlst+lst
        
    return resdatlst

def ResDat(atom):
    """ Return 'res' data
    
    :param obj atom: 'ATOM' instance
    :return: resdat(str) - 'res' data ('resnam:'resnmb:chain')
    :seealos: molec.Atom() class for 'ATOM', lib.PackResDat() for 'res' data
    """
    # atom: Atom instance. 
    # ret resdat: resnam:resnmb:chain
    return atom.resnam+':'+str(atom.resnmb)+':'+atom.chainnam

def ResDatP(pdbatmdat):
    # pdbatmatm: list element of pdbatm
    # ret resdat: resnam:resnmb:chain
    return pdbatmdat[4]+':'+str(pdbatmdat[6])+':'+pdbatmdat[5]

def ElementNameFromString(text,messout=False):
    elmnam=text.strip()
    if len(elmnam) <= 0: return ''
    if len(elmnam) == 1: elmnam=' '+elmnam
    elif len(elmnam) > 2: elmnam=elmnam[:2]
    elmnam=elmnam.upper()
    if not elmnam in const.ElmSbl:
        mess='Wrong elemet name='+elmnam
        if messout: MessageBoxOK(mess,'lib.ElementNameFromString')
    return elmnam

def AtmNamFromString(text):
    atmnam=text.strip(); name=''
    if len(text) <= 0: return ''
    for i in range(len(atmnam)):
        if atmnam[i:i+1] == '_': name=name+' '
        else: name=name+atmnam[i:i+1]
    if len(name) > 4: name=name[:4]
    atmnam=name.upper()
    return atmnam
    
def MakeResDatLstP(pdbatm):
    resdatlst=[]; resdatdic={}    
    for atm in pdbatm:
        resdat=ResDatP(atm)
        if resdatdic.has_key(resdat): continue
        else: resdatdic[resdat]=True; resdatlst.append(resdat)
    return resdatlst

def PickUpResAtmP(resdat,pdbatm):
    resatm=[]
    for atm in pdbatm:
        res=ResDatP(atm)
        if res == resdat: resatm.append(atm)
    return resatm

def MakeResAtmNamDicP(resatm):
    # resatm: atom data in pdbatm form
    # resatmnamdic: {atmnam:seq number of atoms,...}
    resatmnamdic={}
    for i in xrange(len(resatm)): resatmnamdic[resatm[i][2]]=i
    return resatmnamdic
                    
def PackResDat(resnam,resnmb,chain):
    """ Return 'res' data
    
    :param str resnmb: residue name
    :param int resnmb: residue number
    :param str chain: chain name
    :return: resdat(str) - residue name data ('resnam:resnmb:chain')
    :seealso: lib.UnpackResDat()
    """
    return resnam+':'+str(resnmb)+':'+chain
    
def UnpackResDat(resdat):
    """ Unpack 'res' data 
    
    :param str resdat: 'res' data
    :return: resnam(str),resnmb(int),chain(str)
    :seealso: lib.PackResDat()
    """
    # resdat: resnam:resnmb:chain -> resnam,resnum, chain name
    resnam=''; resnmb=-1; chain=''
    if len(resdat) > 0:
        item=resdat.split(':')
        resnam=item[0]
        if len(item) > 1:
            if item[1][0] == '*': resnmb=-1
            else: resnmb=int(item[1]) 
        if len(item) > 2:
            chain=item[2]
        else: chain=' '
    return resnam,resnmb,chain

def FindNearbyAtoms(cc0,cclst):
    # cc0: [x,y,x] list of target atom
    # cclst: coordinate list, [[x1,y1,z1],[x2,y2,z2],..] of surrounding atoms 
    # iatm: sequence number of nearest atoms in cclst
    # rmin: distance from target atom to nearest atom 
    r=[]; iatm=-1; rmin=100000.0; rmax=100000.0
    if len(cc0) <= 0 or len(cclst) <= 0: return iatm,rmin 
    try:
        npair,iatm,jatm,r=fortlib.find_contact_atoms0(cc0,cclst,0.0,rmax)
    except:
        for i in xrange(len(cclst)):
            r.append(Distance(cc0,cclst[i]))    
    if len(r) > 0: 
        iatm=numpy.argmin(r)
        rmin=min(r)

    return iatm,rmin
    
def CheckResDatForm(reslst,full):
    """ Is 'res' data in full form
    
    :param lst reslst: residue list
    :param bool full: True for check full form
    :return: ans(bool) - True or False
    """
    ans=True
    for res in reslst:
        item=res.split(':')
        if len(item) != 3:
            ans=False; break
    return ans 

def CheckShortContact2(mol1,mol2):
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
    return nsht #,rmin

def ListPDBResSeq(pdbmol,skipter,skipwat):
    """ Make residue sequence list
    :param lst pdbmol: 'pdbmol' data
    :param bool skipter: True for skip 'TER', False for not 
    :param bool skipwat: True for skip waters, False for not
    :return: resseqlst(lst) - [[resnam(str),resnmb(int),atmnam(str),chain(str)],...]
    """
    resseqlst=[]; nati=-1; natm=len(pdbmol)
    for i in xrange(natm):
        resnam=pdbmol[i][2][2]; resnmb=pdbmol[i][2][3]
        if skipwat:
            if resnam == 'HOH' or resnam == 'WAT': continue
        if skipter: continue
        atmnam=pdbmol[i][2][0]; chain=pdbmol[i][2][4]
        nati += 1
        resseqlst.append([resnam,resnmb,atmnam,chain])
    return resseqlst

def CatTextInFiles(filelst):
    """ Cancatinate text in files
    
    :param lst filelst: file name list, [filename1,filename2,...]
    """
    text=''
    if len(filelst) <= 0: return text
    for file in filelst:
        if not os.path.exists(file):
            text=text+'#### Not found file='+file
        else:
            f=open(file,'r')
            s=f.read()
            f.close()
            text=text+s
    return text
    
def ReadData(filename,sep):
    # format: label= dat1 dat2 ...(separated by blanks)
    # sep(str): label separator, i.e. '='
    # ret: datdic(dict): data dict
    datdic={}
    if sep == '': sep=' '
    f=open(filename,"r")
    for s in f.readlines():
        if len(s) <= 0: continue
        s=s.replace('\r',''); s=s.replace('\n',''); s=s.strip()
        if s[0:0] == "#": continue
        ns=s.find(sep)
        item=s[:ns]; val=s[ns+1:].strip()
        datdic[item]=val
    f.close()

    return datdic

def SplitTextData(text,sep,form):
    # test(str): text data
    # sep(str): separator, i.e. ','
    # form(str): "float","int",or "str"
    # ret datlst(list): list of splitted data
    if sep == '': sep=','
    if sep != ' ' and text.find(sep) >= 0: text=text.replace(sep,' ')
    datlst=text.split()
    for i in xrange(len(datlst)):
        s=datlst[i].strip()
        try:
            if form == 'float': s=float(s)
            if form == 'int': s=int(s)
        except:
            MessageBoxOK("SplitTextData: error in data format.","")
            break
        datlst[i]=s
    return datlst
        
def WriteSetFile(setfile,item,prgnam,text):
    # item: "program","parameter", or "argument"
    # format of setfile data: "program TINKER directry"
    #                         "paerameter TINKER prameter directory"
    if not os.path.exists(setfile):
        MessageBoxOK("File not exists. file= "+setfile,"")
        return
    if len(text) <= 0:
        MessageBoxOK("Empty data is not set in 'setfile'.","")
        return        
    itmprg=item+"&"+prgnam
    itmprgdic={} 
    # read
    f=open(setfile,"r")
    for s in f.readlines():
        ss=s; ss=ss.strip()
        dat=ss.split()
        if len(dat) <= 2: continue
        nam=dat[0]+"&"+dat[1]
        itmprgdic[nam]=dat[2]
        if len(dat) > 3:
            for i in range(3,len(dat)): itmprgdic[nam]=itmprgdic[nam]+"&"+dat[i]
    f.close()
    #
    itmprgdic[itmprg]=text
    # rewrite
    itmprglst=itmprgdic.keys()
    itmprglst.sort()
    #
    f=open(setfile,"w")
    for namprg in itmprglst: 
        namdat=namprg.split("&")
        nam=namdat[0]; prg=namdat[1]
        txt=itmprgdic[namprg]
        txtdat=txt.split("&")
        text=txtdat[0]
        for i in range(1,len(txtdat)): text=text+" "+txtdat[i]           
        dat=nam+" "+prg+" "+text
        f.write(dat+"\n")
    f.close()
    
def ReadTinkerAtomType(ffname,fffile):
    """ Read TINKER paramter file
    
    :param str ffname: Force field name
    :param str fffile: TINKER params file
    :return: ffatmtyplst(lst) - params list, [[typnmb,clsnmb,atmnam,coment,elm,mass,valence],...]
    :note: TINKER, http://dasher.wustl.edu/tinker/
    """
    dquo='"'
    ffatmtyplst=[]
    f=open(fffile,'r')    
    inc=1
    if ffname =='DANG' or ffname == 'HOCH': inc=0
    if ffname == 'MM2' or ffname == 'MM3' or ffname == 'MM3PRO': inc=0
    if ffname == 'OPLSUA' or ffname == 'SMOOTHUA': inc=0
    if ffname == 'TINY': inc=0
    seq=0
    for s in f.readlines():
        s=s.replace('\r','')
        s=s.replace('\n','')
        s=s.strip()
        if len(s) <= 0: continue
        if s[0:1] == '#': continue
        if s[0:4] == "atom" or s[0:4] == "ATOM":
            ds1=s.find(dquo); s1=s[ds1+1:]; ds2=s1.find(dquo) 
            coment=s[ds1+1:ds1+ds2+1]; coment.strip()
            ss=s[:ds1]+s[ds1+ds2+2:]
            item=ss.split()
            typnmb=int(item[1])
            if inc == 1: clsnmb=item[2]
            else: clsnmb=typnmb
            atmnam=item[2+inc]
            elmnmb=int(item[3+inc]); elm=const.ElmSbl[elmnmb]
            mass=float(item[4+inc])
            valence=int(item[5+inc]) # valence            
            seq += 1
            ffatmtyplst.append([typnmb,clsnmb,atmnam,coment,elm,mass,valence])
    return ffatmtyplst

def ChemFormula(elmlst):
    """ Make chemical formula from element list and return it
    
    :param lst elmlst: list of elements
    :return: chemlst(lst) - chemical formula in list
    :return: chemstring(str) - chemical formula in string
    """
    chemlst=[]; chemstring=''
    edic={}; nh=0; nc=0
    for elm in elmlst:
        if elm == ' H': nh += 1
        elif elm == ' C': nc +=1
        else:
            if edic.has_key(elm): edic[elm] += 1
            else: edic[elm]=1
    chemlst=edic.keys() #list(edic.items())
    chemlst.sort()
    if nh > 0: chemlst=[(' H',nh)]+chemlst
    if nc > 0: chemlst=[(' C',nc)]+chemlst
    for s,i in chemlst: 
        s=s.strip()
        if s == 'XX': continue
        if i == 1: chemstring=chemstring+s+'1 '
        else: chemstring=chemstring+s+str(i)+' '
    return chemlst,chemstring

def CompressIntData(expnint):
    """ return compressed integer data (See ExpnIntDat)
    i.e. 1,3,4,5, 10,11,12, 18,... -> 1,3 -5,10 -12,18,...
    
    :param lst expnint: list of integers
    :return: cmplst(lst) - compressed list of integers
    :seealso: ExpandIntData()
    """
    compint=[]; n=len(expnint)
    if n <= 0: return compint
    compint.append(expnint[0]); ni=0
    for i in xrange(1,n):
        if expnint[i] == expnint[i-1]+1: ni += 1
        else:
            if ni == 1:
                compint.append(expnint[i-1]); ni=0
                #compint.append(expnint[i])
            elif ni > 1:
                compint.append(-expnint[i-1]); ni=0
            compint.append(expnint[i]); ni=0
    if ni > 1: compint.append(-expnint[n-1])
    if ni == 1: compint.append(expnint[n-1])
    return compint

def ExpandIntData(compint):
    """ return expanded integer list
    i.e., 1,3 -5, 10 -12, 18,... -> 1, 3,4,5, 10,11,12, 18,...
    
    :param lst compint: commrest integer list
    :return: expnint(lst) - expanded integers list
    :seealso: CompressIntData()
    """
    expnint=[]
    if len(compint) < 0: return expnint
    for i in compint:
        if i >=0:
            expnint.append(i); prv=i
        else:
            ip=-(i+prv)
            for j in xrange(ip): expnint.append(prv+j+1)
    return expnint

def ReadKeywordListInFile(setfile,keyword,type):
    """ read list data in the expression of 'keyword=list' in 'setfile'.
    
    :param str setfile: file name
    :param lst ketword: keyword
    :param str tyep: 'list' or 'dict'
    :return: dat(str) - string data of list
    :return: mess(str) - error message
    """
    mess=''; cchr='#'  # a character for commnets
    lchr='['; rchr=']'
    if type == 'dict':
        lchr='{'; rchr='}'
    if not os.path.exists(setfile): return
    lkey=len(keyword)
    f=open(setfile)
    dat=''; leftpar=0; rightpar=0; found=False
    for s in f.readlines():
        s=s.replace('\r',''); s=s.replace('\n','')
        s=RemoveCommentInString(s,cchr)
        if len(s) <= 0: continue
        if not found:
            if s[:lkey] != keyword: continue
            found=True; items=s.split('=')
            if len(items) > 1: s=items[1].strip()
            else: s=''
            s=RemoveCommentInString(s,cchr)
            dat=dat+s
            for ss in s:
                if ss.find(lchr): leftpar += 1
                if ss.find(rchr): rightpar += 1
            if (leftpar > 0 or rightpar > 0) and leftpar == rightpar:
                break
            else: continue
        else:
            for ss in s:
                if ss.find(lchr): leftpar += 1
                if ss.find(rchr): rightpar += 1
            dat=dat+s
            if (leftpar > 0 or rightpar > 0) and leftpar == rightpar:
                break
    f.close()
    #
    if not found: dat=lchr+rchr
    if leftpar != rightpar:
        dat=lchr+rchr
        mess='lib(ReadKeywordListInFile):'+'"'+keyword+'" list data is wrong in file='+setfile
    #
    return dat,mess

def RemoveCommentInString(string,comchr):
    """ remove string after 'comchr' in 'string'.
    
    :param str string: string data,
    :param str comchr: a character,
    :return: str(str) - string data
    """
    if len(comchr) <= 0: comchr='#'
    str=string.strip()
    cm=str.find(comchr)
    if cm > 0: str=str[:cm]; str=str.strip()
    return str

def LoadPyShell():
    global PYSHELL
    PYSHELL=wx.py.crust.CrustFrame(None)

def StringToListObj(varname,string,type):
    """ convert string to container type object (list or dictionary)
    
    :param str string: string data
    :param lst type: 'list' or 'dict'
    :return: (lst or dic) glovalvar(global variable): containor type variable
    :Note: this routine create 'varname' global variable]
    :caution: this routine works only in main module(model.py) """
    # check parenthese
    global globalvar
    globalvar=varname
    lchr='['; rchr=']'
    if type == 'dict': lchr='{'; rchr='}'
    leftp=0; rightp=0
    for s in string:
        if s == lchr: leftp += 1
        if s == rchr: rightp += 1
    if leftp == rightp: dat=string
    else:dat=lchr+rchr
    #pycrust=wx.py.crust.CrustFrame(None)
    PYSHELL.shell.run(globalvar+'='+dat)  

def StringToList(string,conv=False):
    """ convert list form string to list
    
    :param str string: string data, i.e. '[1,2,3]'
    :param bool conv: True for convert elements to value, False for do not
    :return: lst(lst) - list of strings
    """
    # check parenthese
    string.strip()
    if string[:1] == '[': string=string[1:]
    if string[-1] == ']': string=string[:-1]
    lst=SplitStringAtSeparator(string,',')
    lst=filter(lambda s: s != ',', lst)
    if conv:
        vallst=[]
        for val in lst: vallst.append(StringToValue(val))
        lst=vallst
    return lst 

def StringToList2(string,conv=False):
    """ conver list form string to list
    
    :param str string: string data, i.e. '[[1,2,3],...]'
    :param bool conv: True for convert elements to value, False for do not
    :return: lst(lst) - list of strings
    """
    string.strip()
    lst=[]; lst1=[]; lst2=[]
    foundlp=False; foundrp=False
    for s in string:
        if s == ' ': continue
        if s =='[':
            foundlp=True
            if not foundrp: lst=[]
        if s == ']':
            foundrp=True
            if foundlp:
                lst1.append(lst)
    if conv:
        vallst=[]
        for val in lst: vallst.append(StringToValue(val))
        lst=vallst
    
    
    return lst 

def StringToDict(string,conv=True):
    """ conver list form string to dictionary
    
    :param str string: string data, i.e. '{a:1,b:2}'
    :param bool conv: True for convert elements to value, False for do not
    :return: dic(dic) - dictionary of strings
    """
    dic={}
    # check parenthese
    string.strip()
    if string[:1] == '{': string=string[1:]
    if string[-1] == '}': string=string[:-1]    
    strlst=SplitStringAtSeparator(string,',')
    for varval in strlst:
        var,val=SplitVariableAndValue(varval,sep=':')
        if conv:
            var=StringToValue(var)
            val=StringToValue(val)
        dic[var]=val
    return dic 

def StringToValue(string):
    """ Convert string to bool,int,or float data
    
    :param str string: string
    :return: value(bool,int,or float) - value
    """
    string=string.strip()
    if string == 'True': value=True
    elif string == 'False': value=False
    elif StringType(string) == 'int': value=int(string)
    elif StringType(string) == 'float': value=float(string)
    else: value=string
    return value

def StringType(string):
    """ return string type, 'int','float','str' 
    
    :param str string: string
    :return: type(str) - 'int', 'float', or 'str'
    """
    temp=string.strip()
    if temp.isdigit(): return 'int'
    try:
        float(temp)
        return 'float'
    except ValueError: return 'str'

def ConvertStringToValue(string,vartyp):
    """ Convert string to value
    
    :param str string: a string
    :param str vartyp: type of value, 'str','int','float', or 'bool'
    :return: value(valtype value) or None if type error occured.
    """
    value=None
    if vartyp == 'int': 
        try: value=int(string)
        except: value=None
    elif vartyp == 'float': 
        try: value=float(string)
        except: value=None
    elif vartyp == 'bool': 
        try:value=str(string)
        except: value=None
    elif vartyp == 'str': value=string
    return value
    
def IsAllASCII(string):
    # reference: http://winter-tail.sakura.ne.jp/pukiwiki/index.php?FrontPage
    ans=False
    pattern=re.compile(r'[^\x20-\x7E]')
    obj=re.search(pattern,string) #" abcdefghijklmnopqrstuvwxyz!#$&'()[]@")
    if obj == None: ans=True
    return ans

def RemoveNonASCIIChars(string):
    # reference: http://winter-tail.sakura.ne.jp/pukiwiki/index.php?FrontPage
    result=''
    for s in string:
        if s == ' ' or s == '\n': result=result+s
        elif s == '*' or s == ',' or s == '.': result=result+s
        elif s == '[' or s == ']': result=result+s
        elif s == '(' or s == ')': result=result+s
        elif s == '<' or s == '>': result=result+s
        elif s == '-' or s == '+': result=result+s
        elif s == '/' or s == '_': result=result+s
        elif s == '#' or s == '!': result=result+s
        elif s == '"' or s == "'": result=result+s
        else:
            if ord(s) < 48 or ord(s) > 127: s='?'
            else: result=result+s
    return result
    
def SplitStringAtSpaces(string):
    """ split string at spaces
    
    :param str string: string
    :return: strlst(lst) - list of splited strings
    """
    return filter(lambda s: len(s) > 0, string.split(' '))    

def SplitStringAtSeparator(string,sep):
    """ split string at commas
    
    :param str string: string
    :param str sep: separator character
    :return: strlst(lst) - list of splited strings
    """
    #return filter(lambda s: len(s) > 0, string.split(sep))    
    strlst=[]; items=string.split(sep)
    for s in items: strlst.append(s.strip())
    return strlst

def SplitStringAtSpacesOrCommas(string):
    """ split string at spaces or commas
    
    :param str string: string
    :return: strlst(lst) - list of splited strings
    """
    strlst=filter(lambda s: len(s) > 0, re.split(r'\s|,',string))
    return strlst

def SplitVariableAndValue(string,sep='='):
    """ Return variable name nad value in string, i.e. 'var=value'.
    
    :param str string: string data
    :return: varnam(str) - variable name
    :return: varvasl(str) - value
    """
    var=''; val=''
    ns=string.find(sep)
    if ns >= 0:
        varval=string.split(sep)
        var=varval[0].strip()
        try: val=varval[1].strip()
        except: val=''
    return var,val
    
def SplitVariablesAndValues(string,itemsep=';',eqsep='='):
    """ Return variable name nad value in string, i.e. 'var=value'.
        Each item should be separated by blank(s), not a commma!
    
    :param str string: string data
    :return: varvaldic(dict) - varvaldic={varnam1:value1,...}
    :SeeAlso: lib.SplitVariableAndValue()
    """
    varvaldic={}
    items=SplitStringAtSeparator(string,itemsep) #OrCommas(string)
    for varval in items:
        var,val=SplitVariableAndValue(varval,sep=eqsep)
        varvaldic[var]=val
    return varvaldic
    
def StringToInteger(strdata):
    """ Convert string data to integers.
    
    :param str strdata: "3-6,8,.."
    :return: list(lst) - [3,4,5,6,8,...]
    :seealso: IntegersToText()
    """
    data=""; datalst=[]; sublst=[]; intdata=[]
    if len(strdata) <= 0: return intdata
    data=strdata.replace(","," ")
    datalst=data.split()
    prv=1
    try:
        for s in datalst:
            siz=len(s)
            if s == '-':
                prv=-1; continue
            else:
                loc=s.find("-")
                if loc <= 0:
                    intdata.append(prv*int(s)); prv=1 
                elif loc == siz-1:
                    intdata.append(prv*int(s[0:loc])); prv=-1
                else:
                    intdata.append(prv*int(s[0:loc]))
                    intdata.append(-1*int(s[loc+1:siz]))
                    prv=1
    except:
        print 'lib.StringToInteger: Error in string data. "'+strdata+'".'
        return []
    intdata=ExpandIntData(intdata)           
    return intdata    

def IntegersToString(intdat):
    """ Convert integers to a string
    
    :param lst intdat: list of integers, [i(int),j(int),...]
    :return: text(str) - 'i,j,...'
    :seealso: StringToInteger()
    """
    text=''; intdic={}
    for i in intdat: intdic[i]=1
    intv=intdic.keys()
    if len(intv) > 0:
        intv.sort()
        compint=CompressIntData(intv)
        nint=len(compint); nd=nint % 2
        for i in range(0,nint-1,2):
            ii=compint[i]; iii=compint[i+1]
            if iii < 0: text=text+str(ii)+str(iii)+','
            else: text=text+str(ii)+','+str(iii)+','
        ns=len(text); text=text[:ns-1]
        if nd != 0:
            if compint[nint-1] < 0:
                text=text+str(compint[nint-1])
            else:
                if text == '': text=str(compint[nint-1])
                else: text=text+','+str(compint[nint-1])
    return text

def ToText(value):
    """ Covert int/float to a string
    
    :param any value: int or float.
    :return: string(str)
    """
    if not isinstance(value,str): text=str(value)
    else:text=value
    return text   

def InvertKeyAndValueInDic(dicobj):
    invdic={}
    for i in dicobj: invdic[dicobj[i]]=i
    return invdic
    
def DictToText(dic):
    """ Use 'DictToString' """
    # dic(dict):
    # ret text(str)
    if not isinstance(dic,dict): return '{}'
    if len(dic) < 0: return '{}'
    text=''
    for key,value in dic.items():
        #skey=key; sval=value
        skey=ToText(key) #if not instance(key,str): skey=str(key)
        sval=ToText(value) #if not isinstance(value,str): sval=str(value)
        text=text+"'"+skey+"'"+':'+sval+',' 
    n=text.rfind(',')
    if n >= 0: text=text[:n] 
    text='{'+text+'}'
    return text

def DictToString(dic):
    """ Convert dictionary to a string
    
    :param dic dic: dictionary (value should be string)
    :return: text(str) - '{'key':'value',...}' 
    """
    # dic(dict):
    # ret text(str)
    if not isinstance(dic,dict): return '{}'
    if len(dic) < 0: return '{}'
    text=''
    for key,value in dic.items():
        #skey=key; sval=value
        skey=ToText(key) #if not instance(key,str): skey=str(key)
        sval=ToText(value) #if not isinstance(value,str): sval=str(value)
        text=text+"'"+skey+"'"+':'+sval+',' 
    n=text.rfind(',')
    if n >= 0: text=text[:n] 
    text='{'+text+'}'
    return text

def KeyWordArgsToString(kwdic):
    kwstr=''
    if len(kwdic) <= 0: return kwstr
    for name,value in kwdic.iteritems():
        typ,val=ObjectToString(value)
        kwstr=kwstr+name+'='+val+','
    kwstr=kwstr[:-1]
    return kwstr

def ListToText(txtlst,sep=','):
    """ Convert list to a string
    
    :param lst txtlst: list (element shoud be string)
    :param str sep' character(s)
    :return: text(str) - 'elemnet+sep+element...'
    """
    text=''
    if sep == '': sep=' '
    for s in txtlst: text=text+s+sep
    n=text.rfind(sep)
    if n >= 0: text=text[:n]
    text='['+text+']'
    return text

def CompareTwoLists(lst1,lst2):
    """ Compare two lists
    
    :param lst lit1: [a,b,...]
    :param lst lst2: [x,y,..]
    :return: True for identival, False for not
    """
    ans=True
    if len(lst1) != len(lst2): return False
    for i in range(len(lst1)):
        if lst1[i] != lst2[i]: ans=False; break
    return ans
    
def ListToString(txtlst,sep=','):
    """ Convert list to a string
    
    :param lst txtlst: list (element shoud be string)
    :param str sep' character(s)
    :return: text(str) - 'elemnet+sep+element...'
    """
    text=''
    for s in txtlst: 
        typ,val=ObjectToString(s)
        text=text+val+sep
    n=text.rfind(sep)
    if n >= 0: text=text[:n]
    text='['+text+']'
    return text

def BoolToString(value):
    if value: string='True'
    else: string='False'
    return string
    
def NumericListToText(intlst,header,sep,width,colu,nw):
    # intlst: [1,2,3,..], sep:separtor, i.e. ','
    strlst=[]
    wid=width
    if width < 0:
        maxval=max(intlst); wid=len(str(maxval))+1
    for i in intlst:
        strlst.append(str(i))
    text=StringListToText(strlst,header,sep,wid,colu,nw)
    return text

def StringListToText(strlst,header,sep,width,colu,nw):    
    # strlst: ['a','b','c',...], width:element width
    # example: header='  frgnam(1)='; sep=','; width=-1; colu=5; nw=5
    text=''
    blk=' '; eol='\n'
    nt=len(strlst); nl=nt/nw+1; nh=len(header)
    ic=-1; k=-1 
    while ic < nt-1:
        k += 1; hd=header
        if k > 0: hd=nh*blk
        line=colu*blk+hd
        for j in range(nw):
            ic += 1
            stri=strlst[ic]; ns=len(stri)
            if width > 0:
                if ns < width: stri=(width-ns)*blk+stri
                elif ns > width: stri=str[:width]
            if ic >= nt-1:
                line=line+stri; break
            else: line=line+stri+sep
        text=text+line+eol
    return text       
    
def PrintNumericList(filnam,intlst,header,sep,width,colu,nw):
    # intlst: [1,2,3,..], sep:separtor, i.e. ','
    strlst=[]
    wid=width
    if width < 0:
        maxval=max(intlst); wid=len(str(maxval))+1
    for i in intlst:
        strlst.append(str(i))
    PrintStringList(filnam,strlst,header,sep,wid,colu,nw)

def PrintStringList(fildev,strlst,header,sep,width,colu,nw):    
    # strlst: ['a','b','c',...], width:element width
    blk=' '; eol='\n'
    nt=len(strlst); nl=nt/nw+1; nh=len(header)
    ic=-1; k=-1 
    while ic < nt-1:
        k += 1; hd=header
        if k > 0: hd=nh*blk
        line=colu*blk+hd
        for j in range(nw):
            ic += 1
            stri=strlst[ic]; ns=len(stri)
            if width > 0:
                if ns < width: stri=(width-ns)*blk+stri
                elif ns > width: stri=str[:width]
            if ic >= nt-1:
                line=line+stri; break
            else: line=line+stri+sep
        if fildev == 'stdout': print line+eol
        else: fildev.write(line+eol)

def ReadKeywordValueInFile(filename,keyword):
    """ Get value in the expression of keyword=vlaue in file
    
    :param str filenname: file name
    :param str keywors: keyword string
    :return: value(str) - value string
    """
    value=None; lenkey=len(keyword)
    if not os.path.exists(filename): return value
    fmomenu=False; found=False
    f=open(filename)
    dat=''; lenkey=len(keyword); leftpar=0; rightpar=0
    for s in f.readlines():
        cm=s.find('#')
        if cm > 0: s=s[:cm]
        s=s.strip()
        if len(s) == 0: continue
        items=s.split()
        for item in items:
            if item[:lenkey] == keyword:
                found=True; value=item.split('=')[1]; value=value.strip()
                break
    f.close()
    if not found: value=None
    return value

def ReadKeywordInFile(filename,keywrd,col1,col2,datcollst):
    """ Pick up data in file. data in line: keywrd(col1-col2)... coli1-coli2,varnam,format
    
    :param str filename: filename
    :param str keywrd: startswith  col1-col2
    :param int col1: begin column
    :param int col2: end column
    :param lst datcollst: [[coli,colj,varnam,format],[...],,,,]
    :return: err(bool)
    :return: valuedic(dic) - data dictionary
    """
    newl='\n'
    err=0; eof=False; valuedic={}  
    try:
        fmo=open(filename)
    except IOError:
        MessageBoxOK("Failed to open file. file="+filename,"")
        err=1
    else:
        #loop=True
        for s in fmo.readlines():
            if s.startswith(keywrd,col1,col2): 
                mess="Failed to read keyword "+"'"+keywrd+"'"+' in file='+filename+'.\n'
                for i in xrange(len(datcollst)):
                    scol=datcollst[i][0] # start column
                    ecol=datcollst[i][1] # end column
                    vnam=datcollst[i][2] # variable name
                    fmt=datcollst[i][3]  # format of the data
                    dat=s[scol:ecol] 
                    dat=dat.strip() # string
                    if fmt == 'integer':
                        try: dat=int(dat)
                        except:
                            MessageBoxOK(mess,"")
                            dat=0; pass
                    if fmt == 'float':
                        try: dat=float(dat)
                        except:
                            MessageBoxOK(mess,"")
                            dat=0.0; pass
                    if fmt == 'logical':
                        try: dat=True
                        except:
                            dlg=MessageBoxOK(mess,"")
                            dat=False; pass
                    # set value
                    if valuedic.has_key(vnam):
                        valuedic[vnam].append(dat)
                    else:
                        valuedic[vnam]=[]; valuedic[vnam].append(dat)
                    #valuedic[vnam]=dat
                #loop=False
            #if not loop: break
        fmo.close()
    
    return err,valuedic

def IntegersInLine(lst,nmbinline):
    linelst=[]; k=0; tmp=[]
    for i in lst:
        tmp.append(i); k += 1
        if k == nmbinline:
            linelst.append(tmp); tmp=[]; k=0
    if len(tmp) > 0: linelst.append(tmp)
    
    return linelst
    
def ReadPDBAtom(filpdb):
    """ Pick up "ATOM", "HETATM", "TAR" and "CONECT" data in pdb file
    
    :param str filpdb: pdb file name
    :return: pdbatm(lst) - pdb atom data
    :return: pdbcon(lst) - connect data
    """
    reca='ATOM  '; rech='HETATM'; rect='TER'; blk=' '
    natm=0; ncon=0; pdbatm=[]; pdbcon=[]; pdbdat=[]; pdbmol=[]
    try:
        fpdb=open(filpdb)
    except IOError:
        mess='Error(ReadPDBAtom): File not found. file name='+filpdb
        #dlg=wx.MessageBox(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)
        print mess
        return [],[]
    else:        
        natm=0; pdbatm=[]
        # atom data with dummy con data         
        for s in fpdb.readlines():
            ns=s.find('#') 
            if ns > 0: s=s[:ns]
            s=s.replace('\r','')
            s=s.replace('\n','')
            ns=len(s); s=s+(80-ns)*' '
            atmrec=0
            if s.startswith(reca,0,6) or \
                           s.startswith(rech,0,6):                  
                label=s[0:6]
                atmrec=1
                try:
                    atmnmb=int(s[6:11])
                except: atmnmb=0
                atmnam=s[12:16]
                alt=s[16:17]
                if alt != blk and alt != 'A': continue
                natm += 1
                resnam=s[17:20]
                chain=s[21:22]
                resnmb=0
                try:
                    if s[22:26] != blk*3:
                        resnmb=int(s[22:26])
                except:
                    resnmb=0
                # s[26:27]=Achar???
                # the followin two lines are special code for HyperChem ver.7
                if s[54:55] != blk:
                    s=s[0:27]+s[28:]+blk
                fx=float(s[30:38])
                fy=float(s[38:46])
                fz=float(s[46:54])
                focc=0.0
                try:
                    if s[54:60] != blk*6:
                        focc=float(s[54:60])
                except:
                    focc=0.0
                fbfc=0.0
                try:
                    if s[60:66] != blk*6:
                        fbfc=float(s[60:66])
                except:
                    fbfc=0.0
                elmdat=s[76:78]  # kk
                #if s[76:78] == blk*2:
                elm=fuMole.AtmNamElm(atmnam)
                if elm == '??' and len(elmdat) > 0: elm=elmdat
                #if len(elmdat) > 0: elm=elmdat
                #else: elm=fuMole.AtmNamElm(atmnam)
                chg=0.0
                try:
                    if s[78:80] != blk*2:  # kk
                        chg=int(s[78:80])
                except:
                    chg=0                      
            elif s.startswith(rect,0,3):
                label='TER   '
                atmrec=1
                natm += 1
                atmnam=blk*4;
                atmnam=natm
                try:
                    if s[6:11] != blk*5: atmnmb=int(s[6:11])
                except: atmnmb=int(natm)
                try: resnam=s[17:20]
                except: resnam='   '
                try: chain=s[21:22]
                except: chain=' '
                #if s[22:26] != blk*3:
                #    resnmb=int(s[22:26])
                #else:
                #    resnmb=0
                resnmb=0
                alt=blk; fx=0.0; fy=0.0; fz=0.0
                elm='XX'; focc=0.0; fbfc=0.0; chg=0 
                try:
                    if s[7:12] != blk*5: atmnmb=int(s[6:11])
                except: atmnmb=natm
                #iconi.append(natm)
            else: continue
            ###if not atmrec: continue
            #label=s[0:6]
            dat=[label,natm,atmnam,alt,resnam,chain,resnmb,[fx,fy,fz],focc,fbfc,elm,chg]
            pdbatm.append(dat)
        # read conect data
        natm=len(pdbatm)
        reccon='CONECT'; ncon=0; pdbcon=natm*[]
        fpdb.seek(0)  
        for s in fpdb.readlines():
            s=s.replace('\r','')
            s=s.replace('\n','')
            if s[0:1] == '#': continue
            if s.startswith(reccon,0,6):
                ns=len(s); s=s+(80-ns)*' '
                ncon += 1       
                item=[]; con=[]
                if s[6:11] != blk*5:
                    item.append(int(s[6:11]))
                if s[11:16] != blk*5:
                    item.append(int(s[11:16]))
                if s[16:21] != blk*5:
                    item.append(int(s[16:21]))
                if s[21:26] != blk*5:
                    item.append(int(s[21:26]))
                if s[26:31] != blk*5:
                    item.append(int(s[26:31]))
                if len(item) > 0:
                    for i in range(len(item)):
                        con.append(int(item[i])-1)
                pdbcon.append(con)            
        fpdb.close()                         
        if len(pdbatm) < 0 :
            mess="Error(ReadPDBAtom): No ATOM records in "+filpdb
            #dlg=wx.MessageBox(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)
            print mess

        return pdbatm,pdbcon

class ListStack():
    """ Stack data in list
    
    :param obj parent: parent object
    """
    def __init__(self,parent):
        self.parent=parent
        #
        self.title='ListStack'
        self.stack=[]
        self.save=[]
        self.maxdepth=2

    def SetTitle(self,title):
        # set title
        # title(str): title text
        self.title=title

    def GetTitle(self):
        # get title
        # ret title(str): title
        return self.title
          
    def Push(self,data,dup=False):
        # push data
        # data(any): data for stack
        if data in self.stack and not dup: self.stack.remove(data)
        self.stack=[data]+self.stack
        if len(self.stack) > self.maxdepth: del self.stack[self.maxdepth]
        
    def Pop(self):
        # pop data
        # ret(any): data. if no data, return None
        if len(self.stack) <= 0: return None
        data=self.stack[0]
        del self.stack[0]
        return data
        
    def Clear(self):
        # clear stack
        self.stack=[]
        self.save=[]
    
    def Del(self,idx):
        # idx(int): delete idx-th data in stack
        del self.stack[idx]
        
    def Save(self):
        self.save=self.stack[:]
    
    def GetSaved(self):
        return self.save
            
    def SetSaved(self):
        self.stack=self.save[:]
        
    def Get(self):
        # get all stacked data
        # ret stack(lst): all staked data in list
        return self.stack

    def Set(self,stack):
        # set all satck data
        # stack(lst): stacked data in lsits
        self.stack=stack
    
    def SetMaxDepth(self,value):
        # set maximum number of depth
        # value(int): number
        self.maxdepth=value
        
    def GetMaxDepth(self):
        # get maximum stack depth
        # ret(int): maximum number of depth
        return self.maxdepth

    def GetNumberOfData(self):
        # get number of data in stack
        # ret (int): number of data
        return len(self.stack)
        
class DicVars():
    """  Variables dictionary class
    
    :param obj parent: parent object
    """
    def __init__(self,parent,title='DicVars'):
        self.parent=parent
        self.vars={}
        self.title=title

    def SetTitle(self,title):
        # set title
        # title(str): title text
        self.title=title

    def GetTitle(self):
        # get title
        # ret title(str): title text
        return self.title
    
    def Get(self,name):
        # get item value
        # name(str): item name
        # ret(any): data
        if not self.vars.has_key(name): return False
        else: return self.vars[name]

    def Set(self,name,value):
        # set item value
        # name(str): item name
        # value(any): item value
        self.vars[name]=value

    def Del(self,name):
        # delete item
        # name(str): item name
        if self.vars.has_key(name): del self.vars[name]
        else: pass

    def DelByNameList(self,namelst):
        """ delete ites in "namelst".'
        namelst(lst): list of item names """
        for nam in namelst:
            if self.vars.has_key(nam): del self.vars[nam]

    def AppendList(self,name,data):
        if not self.vars.has_key(name): 
            lib.MessageBoxOK('No data name='+name,'lib.DicVar(AppendList')
            return
        if not isinstance(self.vars[name],types.ListType):
            lib.MessageBoxOK('Is not List. name='+name,'lib.DicVar(AppendList')
            return
        self.vars[name].append(data)
        
    def Clear(self):
        # clear vars
        self.vars={}

    def GetAll(self):
        # get all items in dictionary
        # ret vars(dic): dictionary of all items
        return self.vars

    def SetAll(self,vars):
        # replace all items with 'vars'
        # vars(dic): new items dictionary
        self.vars=vars

    def ResetValues(self,exclude):
        # reset item values except 'exclude'.
        # exclude(lst): ['*',...] do not reset items whose first charcters are in the list. 
        for item,value in self.vars.iteritems():
            for s in exclude:
                ObjectType
                if item[:1] == s: continue
                if isinstance(value,types.DictType): value={}
                elif isinstance(value,types.ListType): value=[]
                elif isinstance(value,types.TupleType): value=()
                elif isinstance(value,types.StringType): value=''
                elif isinstance(value,types.IntType): value=0
                elif isinstance(value,types.FloatType): value=0.0
                elif isinstance(value,types.BooleanType): value=False
                elif isinstance(value,types.FunctionType): value=None
                elif isinstance(value,types.MethodType): value=None
                elif isinstance(value,types.InstanceType): value=None
                elif isinstance(value,types.ModuleType): value=None
                else: value=None

    def DelItemsWithChr(self,chr):
        """ delete items whose leading characters 'chr' in name.
            chr(str): string """
        nchr=len(chr); dellst=[]
        for item,value in self.vars.iteritems():
            if item[:nchr] ==chr: dellst.append(item)
        for item in dellst: del self.vars[item]
      
    def IsDefined(self,name):
        # check item name in vars
        # name(str): item name
        # ret ans(bool): True for defined, False for not defined
        if self.vars.has_key(name): ans=True
        else: ans=False
        return ans

    def GetNames(self):
        # make list of item names
        # ret name(lst): item name list (sorted)
        name=[]
        for item, value in self.vars.iteritems(): name.append(item)
        name.sort()
        return name

    def ListNames(self,maxchr,quot):
        # list item names
        # maxchr(int): maximum number of characters in a line
        # quot(bool): True with quotation, False without quotation
        # ret namlst(lst): text list
        names=self.ListNames()
        namlst=[]; txt=''
        for nam in names:
            if quot: nam="'"+nam+"'"
            tmp=txt+nam+","
            if len(tmp) > maxchr:
                namlst.append(txt); txt=nam+','
            else: txt=tmp
        if len(txt) > 0:
            txt=txt[:-1]; namlst.append(txt)
        return namlst
                                               
    def Print(self,name):
        # print value of item with name
        # name(str): item name
        if not self.vars.has_key(name):
            mess=self.title+': '+name+' is not defined.'
        else: mess=self.title+': '+name+'='+ToText(self.vars[name])
        try: self.parent.ConsoleMessage(mess)
        except: print mess
                          
    def PrintAll(self):
        # print all item values
        mess='"'+self.title+'":'
        try: 
            self.parent.ConsoleMessage(mess)
            text=DictToText(self.vars)
            self.parent.ConsoleMessage(text)
        except: print mess,self.vars

def ObjectToString(object):
    """ Conver object to string
    
    :param obj object: object
    :return: typ(str) - object type
    :return: value(str) - object string
    """
    value=None; typ=None
    # filename type
    try:
        head,tail=os.path.split(object)
        base,ext=os.path.splitext(tail)
        if ext in const.FUFILEEXT:
            value='"'+object+'"' 
            value=filter(lambda s: len(s) > 0,value.replace('\\','//'))        
            typ='filename'
            return typ,value
    except: pass
    if isinstance(object,types.DictType): 
        typ='dict'; value=DictToString(object)
    elif isinstance(object,types.ListType): 
        typ='list'; value=ListToString(object)
    elif isinstance(object,types.TupleType): 
        typ='tuple'; value=ListToString(list(object))
    elif isinstance(object,types.StringType): 
        typ='str'; value='"'+object+'"'
    # bool type should be cheked before int type
    elif isinstance(object,types.BooleanType): 
        typ='bool'; value=BoolToString(object)
    elif isinstance(object,types.IntType): 
        typ='int'; value=str(object)
    elif isinstance(object,types.FloatType): 
        typ='float'; value=str(object)
    else: # isinstance(object,types.ClassType): 
        #try:
        typ='object'
        name=type(object).__name__
        if name == 'Point': 
            typ='point'; value=ListToString(list(object))
            return typ,value
        elif name == 'NoneType': return 'obj','None'
        elif name == 'PyEventBinder': value='unable to stringify'
        elif name == 'Menu': value='unable to stringify'
        elif name == 'MenuBar': value='unable to stringify'
        elif name == 'CommandEvent': value='unable to stringify'            
        elif name == 'Frame': value='unable to stringify'
        elif name == 'SizeEvent': value='unable to stringify'
        elif name == 'wxFont': value='unable to stringify'
        elif name == 'Icon': value='unable to stringify'
        #except:
        else:
            ### print 'else object type',name
            try: # message ?
                value='"'+object+'"'
            except: value='unable to stringify'
        
    return typ,value

def IsNumeric(object):
    ans=False
    if isinstance(object,types.IntType) or isinstance(object,types.FloatType): ans=True
    return ans
    
def ObjectType(object):
    """ Return object type
    
    :param obj object: object
    :return: type(str) - object type, 'dict','list','tuple','str','bool','int','float',
                                      'function','method','instance','module',None(non type)
    """
    if isinstance(object,types.DictType): type='dict'
    elif isinstance(object,types.ListType): type='list'
    elif isinstance(object,types.TupleType): type='tuple'
    elif isinstance(object,types.StringType): type='str'
    # bool type should be cheked before int type
    elif isinstance(object,types.BooleanType): type='bool'
    elif isinstance(object,types.IntType): type='int'
    elif isinstance(object,types.FloatType): type='float'
    elif isinstance(object,types.FunctionType): type='function'
    elif isinstance(object,types.MethodType): type='method'
    elif isinstance(object,types.InstanceType): type='instance'
    elif isinstance(object,types.ModuleType): type='module'
    else: type=None
    return type

class SettingProgramPath_Frm(wx.Frame):
    def __init__(self,parent,id,prgfile,prgname,prgargs,remark):
        self.title='Setting '+prgrame+' path and argument'
        winsize=(400,155); winpos=(-1,-1)
        wx.Frame.__init__(self, parent, id, self.title,size=winsize,pos=winpos,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent
        self.model=parent.model #self.parent.model
        self.ctrlflag=self.parent.ctrlflag

        self.remark=remark
        self.MakeModal(True)
        self.prgfile=self.model.setmgr.GetFile('progs','gamess.txt')
        
        print 'self.prgfile',self.prgfile
        
        self.size=self.GetSize()
        #self.gmspath="c:\\gamess.64\\rungms.bat"
        #self.gmsarg="13-64.intel.linux.mkl 1 0"   
        self.gmspath=""; self.gmsarg=""
        gms,text,self.gmspath,self.gmsarg=self.ReadGAMESSPathInSetFile(True)

        self.setpath=False
        self.quit=False
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
                
    def CreatePanel(self):
        w=self.size[0]; h=self.size[1]
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        yloc=8
        text1=self.remark[0]
        wx.StaticText(self.panel,-1,"     ex. 'c:/gamess.64/rungms.bat' and '13-64.intel.linux.mkl 1 0'",pos=(5,yloc),size=(380,18))
        yloc += 20
        text2=self.remark[1]
        wx.StaticText(self.panel,-1,"     ex. 'c:/wingamess/runwingms.bat' and '11 1 0'",pos=(5,yloc),size=(380,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"Path:",pos=(10,yloc),size=(60,18)) 
        self.tclpath=wx.TextCtrl(self.panel,-1,self.gmspath,pos=(75,yloc-2),size=(245,18))
        btnbrws=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(330,yloc-2),size=(50,20))
        btnbrws.Bind(wx.EVT_BUTTON,self.OnBrowse)
        
        yloc += 25
        wx.StaticText(self.panel,-1,"Arguments:",pos=(10,yloc),size=(65,18)) 
        self.tclcmd=wx.TextCtrl(self.panel,-1,self.gmsarg,pos=(80,yloc-2),size=(295,18))
        yloc += 25
        btnok=wx.Button(self.panel,wx.ID_ANY,"OK",pos=(100,yloc-2),size=(35,20))
        btnok.Bind(wx.EVT_BUTTON,self.OnOK)
        btnrmv=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(150,yloc-2),size=(45,20))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnClear)
        btncan=wx.Button(self.panel,wx.ID_ANY,"Cancel",pos=(240,yloc-2),size=(50,20))
        btncan.Bind(wx.EVT_BUTTON,self.OnCancel)

    def SetProgramPath(self):
        self.CreatePanel()
        self.Show()

    def OnBrowse(self,event):
        wcard="All(*.*)|*.*"
        pathname=GetFileName(self,wcard,"r",True,"")
        if pathname != "": self.tclpath.SetValue(pathname)
                
    def OnApply(self,event):
        self.gmspath=self.tclpath.GetValue()
        self.gmsarg=self.tclcmd.GetValue()
        if not os.path.exists(self.gmspath):
            mess="Path '"+self.gmspath+"' not found. Enter again?."
            dlg=MessageBoxYesNo(mess,"")
            if dlg == wx.YES:
                self.setpath=False; return
            else:
                self.quit=True; self.gmspath=""; self.gmsarg=""
                self.setpath=False
                self.Close(1)
        else:
            self.quit=False
            exenam="gamess."+self.gmsarg.split()[0]+".exe"
            pathnam,exe=os.path.split(self.gmspath)
            gmsexe=os.path.join(pathnam,exenam) #"gamess."+exenam+".exe"
            #
            if not os.path.exists(gmsexe):
                mess="GAMESS executable '"+gmsexe+"' not found. Re-enter."
                dlg=MessageBoxOK(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)
                return
            else:
                self.SetGAMESSPathAndArgInSetFile(True)
                self.setpath=True; self.quit=False

    def OnClear(self,event):
        self.gmspath=self.tclpath.SetValue("")
        self.gmsarg=self.tclcmd.SetValue("")
    
    def OnCancel(self,event):
        self.ctrlflag.Set('gmssetwin',False)
        self.MakeModal(False)
        self.Destroy()

    def ReadGAMESSPathInSetFile(self,add):
        gmspath=""; gmsarg=""; found=False; text=[]; gmsdat=""
        gms="GAMESS program "+self.gmspath+" $inpfile "+self.gmsarg
        if os.path.exists(self.prgfile):
            f=open(self.prgfile,"r")
            for s in f.readlines():
                ss=s; ss=ss.strip()
                #print 'ss.find("program"),ss.find("GAMESS")',ss.find("program"),ss.find("GAMESS")
                if ss.find("program") >= 0: # and ss.find("GAMESS") >= 0:
                    found=True; gmsdat=ss
                    if add: text.append(gms)
                else: text.append(s)
            f.close()
        if not found: gms=""
        if len(gmsdat) > 0:
            item=gmsdat.split()
            if len(item) >=2: gmspath=item[1]
            if len(item) >=4: gmsarg=item[3]
            if len(item) >=5: gmsarg=gmsarg+' '+item[4]
            if len(item) >=6: gmsarg=gmsarg+' '+item[5]
        return gms,text,gmspath,gmsarg
         
    def SetGAMESSPathAndArgInSetFile(self,add):
        # add: True for add or update, False: delete
        # read
        found=True
        gms,text,gmspath,gmsarg=self.ReadGAMESSPathInSetFile(True)
        if len(gms) <= 0: found=False
        # write
        f=open(self.prgfile,"w")
        for s in text:
            if found and s.find('GAMESS') >=0: continue
            f.write(s) #+'\n')
        if add:
            gms="GAMESS program "+self.gmspath+" $inpfile "+self.gmsarg
            f.write(gms+'\n')
        f.close()
        
    def OnOK(self,event):
        self.OnApply(1)
        self.OnClose(1)
        
    def OnClose(self,event):
        if not self.setpath:
            mess="Do you want to keep GAMESS path and command in fumolde.set file."
            dlg=MessageBoxYesNo(mess,"")
            if dlg == wx.YES:
                #if wx.YES:
                self.SetGAMESSPathAndArgInSetFile(True)
                self.setpath=True
            else: pass
        self.ctrlflag.Set('gmssetwin',False)
        
        self.MakeModal(False)
        self.Destroy()        

def GetMonomersFromPDBFTPServer(ftpserver,monomerlst,savedir):
    """ access ftp://ftp.wwpdb.org/pub/pdb/data/momomers and download monomer data (called 'frame' data in FU)
    
    :param lst server: [server(str),user(str),passwd(str),monomerpath(str)]
    :param lst monomerlst: ['FK5','AA0',...], monomer name by three charcters
    :param str savedir: directory name to save(file name will be 'monomername.frm')
    :return: mess(str) - message
    :return: savedlst(lst) - lists of successful monomers.
    :return: failedlst(lst) - list of failed monomers.
    """
    defserver=['ftp.wwpdb.org','guest','','pub/pdb/data/monomers']
    if len(ftpserver) <= 0: ftpserver=defserver
    methodnam='lib.DownloadMononersFromPDBFTPServer'
    if len(monomerlst) <= 0: 
        mess=methodnam+': no monomers in "monomerlst"'; return mess,[],[]
    if not os.path.isdir(savedir):
        mess=methodnam+': directory "'+savedir+'" does not exist'; return mess,[],[]
    mess=''; savedlst=[]; failedlst=[]
    server=ftpserver[0] #'ftp.wwpdb.org'
    user=ftpserver[1];passwd=ftpserver[2]  #'guest'; ''
    monomerpath=ftpserver[3] #'pub/pdb/data/monomers'
    try:
        ftpserver = FTP(server,user,passwd)
        ftpserver.cwd(monomerpath)
        for monomer in monomerlst:
            try:
                savefile=monomer+'.frm'
                savefile=os.path.join(savedir,savefile)
                if not os.path.isfile(savefile):
                    with open(savefile,'wb') as f:
                        ftpserver.retrbinary('RETR '+monomer, f.write)
                savedlst.append(monomer)
            except: failedlst.append(monomer)
        # close ftp server
        ftpserver.quit()
    except ftplib.all_errors, e:
        err=methodnam+': Errors. '
        print err
        print 'error code:',e
    return mess,savedlst,failedlst

def GetPDBFilesFromPDBj(ftpserver,pdbidlst,savedir):
    #dlg=wx.MessageBox(mess,"AccessPDBj",style=wx.OK|wx.ICON_EXCLAMATION)
    #MessageBoxOK(mess,"AccessPDBj") #,style=wx.OK|wx.ICON_EXCLAMATION)
    #return
    defserver=['ftp.pdbj.org','anonymous','','model']
    if len(ftpserver) <= 0: ftpserver=defserver
    methodnam='lib.GetPDBFilesFromPDBj'
    if len(pdbidlst) <= 0: 
        mess=methodnam+': no pdbid in "pdbidlstlst"'; return mess,[],[]
    if not os.path.isdir(savedir):
        mess=methodnam+': directory "'+savedir+'" does not exist'; return mess,[],[]
    mess=''; savedlst=[]; failedlst=[]
    server=ftpserver[0] #'ftp.wwpdb.org'
    user=ftpserver[1];passwd=ftpserver[2]  #'guest'; ''
    modelpath=ftpserver[3] #'pub/pdb/data/monomers'
    try:
        ftpserver = FTP(server,user,passwd)
        ftpserver.cwd(modelpath)
        for pdbid in pdbidlst:
            pdbfile='pdb'+pdbid+'.ent.gz'
            try:
                savefile=pdbfile
                savefile=os.path.join(savedir,savefile)
                if not os.path.isfile(savefile):
                    with open(savefile,'wb') as f:
                        ftpserver.retrbinary('RETR '+pdbfile, f.write)
                savedlst.append(pdbfile)
            except: failedlst.append(pdbfile)
        # close ftp server
        ftpserver.quit()
    except ftplib.all_errors, e:
        err=methodnam+': Errors. '
        print err
        print 'error code:',e
    return mess,savedlst,failedlst

def CaptureWindowW(winobj,child):
    """ Caputure window(mdlwin or canvas) image(WINDOWS only)
    
    :param obj winobj: wx.Frame object
    :param bool child: True for the window has parent, False for does not.
    :return: img(obj) - wx.Image object
    """
    retmess='lib.CaptureWindowW: '
    if GetPlatform() == 'MACOSX':
        RETMESS=retmess+'This method is for WINDOWS or LINUX.'
        return retmess,None
    [x,y]=winobj.GetPosition()
    if child: [x,y]=winobj.ClientToScreen([x,y])
    [w,h]=winobj.GetSize()
    y += 25; h -= 25
    dcScreen = wx.ScreenDC()
    bmp = wx.EmptyBitmap(w,h)
    memDC = wx.MemoryDC()
    memDC.SelectObject(bmp)
    memDC.Blit(0,0,w,h,dcScreen,x,y)
    memDC.SelectObject(wx.NullBitmap)
    #img = bmp.ConvertToImage()      
    retmess=''
    img=bmp.ConvertToImage() 
    return retmess,img

def CaptureWindowM(rect):
    """ Caputure window(mdlwin or canvas) image (MACOSX only)
    
    :param obj winobj: wx.Frame object
    :param lst rect: screen rectangle, [x(int),y(int),w(int),h(int)]
    :return: img(obj) - wx.Image object
    """
    retmess='lib.CaptureWindowM: '
    img=None
    if GetPlatform() != 'MACOSX':
        RETMESS=retmess+'This method is for MACOSX only.'
        return
    prg=MACSCREENCAPTURE
    if not os.path.exists(prg): prg='/usr/sbin/screencapture'
    if not os.path.exists(prg):
        retmess=retmess+prg+'is not found.'
        return retmess,img
    if len(rect) <= 0:
        rectstr=' -R0,0,640,400'
    else:    
        rectstr=' -R'+str(rect[0])+','+str(rect[1])+','+str(rect[2])+','+str(rect[3])
    try:
        # copy image data to clipboard using the 'screencapture' program
        prg=prg+' -m -o -c -T0 -x '+rectstr
        try:
            os.system(prg)
            retmess=retmess+'Image data was saved on "'+filename+'".'
        except: retmess=retmess+'Failed to capture window image.'
        # pasted image data from clipboard
        bmpobj=wx.BitmapDataObject()
        clipbd=wx.Clipboard()
        clipbd.Open()
        ok=clipbd.GetData(bmpobj)
        #clipbd.Clear()
        clipbd.Close()
        bmp=bmpobj.GetBitmap()
        img=bmp.ConvertToImage() 
    except: retmess=retmess+'Failed to capture window image.'
    
    return retmess,img

def SaveImageOnFile(filename,img): # ,imgtyp):
    """ Save image data in file
    
    :param str filename: base name of output file, The extension should indicate image type,
    '.bmp','.png','.jpeg','.pcx','.pnm', or '.xpm',('.ico','.cur', for WINDOWS only)
    :param obj img: wx.Image object
    :return: retmess(str) - return message
    """
    retmess='lib.SaveImageOnFile: '
    platform=GetPlatform()
    # supported imgform=['bmp','png','jpeg','pcx','pnm','xpm','ico','cur']    retmess='lib.SaveImageOnFile: '
    base,ext=os.path.splitext(filename)
    if ext == '': imgtyp='bmp'
    else: imgtyp=ext[1:]
    imgtyp=imgtyp.lower()
    #filename=basefilename+'.'+imgtyp
    if imgtyp == 'bmp': img.SaveFile(filename, wx.BITMAP_TYPE_BMP)        
    elif imgtyp == 'png': img.SaveFile(filename, wx.BITMAP_TYPE_PNG)
    # not wor # elif imgtyp == 'tiff': img.SaveFile(filename,  wx.BITMAP_TYPE_TIFF)
    elif imgtyp == 'jpeg': img.SaveFile(filename, wx.BITMAP_TYPE_JPEG)
    elif imgtyp == 'pcx': img.SaveFile(filename, wx.BITMAP_TYPE_PCX)
    elif imgtyp == 'pnm': img.SaveFile(filename, wx.BITMAP_TYPE_PNM)
    elif imgtyp == 'xpm': img.SaveFile(filename, wx.BITMAP_TYPE_XPM)
    elif imgtyp == 'ico' and platform == 'WINDOWS': img.SaveFile(filename, wx.BITMAP_TYPE_ICO)
    elif imgtyp == 'cur' and platform == 'WINDOWS': img.SaveFile(filename, wx.BITMAP_TYPE_CUR)
    else:
        retmess=retmess+'Unknown image format "'+imgtyp+'".' 
        return retmess
    retmess=retmess+'Image data was saved on "'+filename+'".'
    return retmess
    
def ScreenCaptureMac(rect,filenamebase):
    """ Execute 'screencaputre' program in MacOSX to capture window/canvas.
    
    :param lst rect: screen rectangle, [x(int),y(int),w(int),h(int)]
    :param str filenamebase: base filename to save. if the name is 'clipboard', image goes to clipboard
    :return: mess(str) - return message
    :note: output image format is 'png' and the extension '.png' will be added to 'filenamebase'.
    """
    retmess='lib.ScreenCaptureMac: '
    if GetPlatform() != 'MACOSX':
        RETMESS=retmess+'This method is for MACOSX only.'
        return
    prg=MACSCREENCAPTURE
    if not os.path.exists(prg): prg='/usr/sbin/screencapture'
    if not os.path.exists(prg):
        retmess=retmess+prg+'is not found.'
        return retmess
    if len(rect) <= 0:
        rectstr=' -R0,0,640,400'
    else:    
        rectstr=' -R'+str(rect[0])+','+str(rect[1])+','+str(rect[2])+','+str(rect[3])
    if filenamebase == 'clipboard': 
        prg=prg+' -m -o -c -T0 -x '+rectstr; filename=filenamebase
    else: 
        filename=filenamebase+'.png'
        prg=prg+rectstr+' -m -o -T0 -x '+filename
    try:
        os.system(prg)
        retmess=retmess+'Image data was saved on "'+filename+'".'
    except: retmess=retmess+'Failed to capture window image.'
    
    return retmess

def Zip(filename):
    """ make zip file(filename -> filename.gz)
    
    :param str filename: filename to zip
    """
    outfile=ZipUnzipFile(filename,True,message=True)

def Unzip(filename):
    """ Unzip file ( .gz -> base name file) 
    
    :param str filename: zip filename(.gz)
    """
    outfile=ZipUnzipFile(filename,False,message=True)

def ConvertToZip(filename):
    """ Convert to zip file(filename -> filename.gz)
    
    :param str filename: filename to zip
    """
    outfile=ZipUnzipFile(filename,True,delinpfile=True,message=True)
    
def ConvertToUnzip(filename):
    """ Convert to unzip file ( .gz -> base name file) 
    
    :param str filename: zip filename(.gz)
    """
    outfile=ZipUnzipFile(filename,False,delinpfile=True,message=True)

def ZipUnzipFile(filename,zip,delinpfile=False,check=True,message=False):
    """
    :param str filename: plane or zip(.gz) file name
    :param bool zip: True for make zip, False for unzip
    """
    outfile=''
    if not os.path.exists(filename):
        mess='input file='+filename+' not found.'
        MessageBoxOK(mess,'lib.ZipUnzipFile')
        return outfile
    if zip: outfile=filename+'.gz'
    else: 
        head,tail=os.path.split(filename)
        base,ext=os.path.splitext(tail)
        outfile=os.path.join(head,base)
    if check:
        if os.path.exists(outfile):
            mess='output file='+outfile+' exists. Would you like to overwrite it?'
            dlg=MessageBoxYesNo(mess,'lib.zipfile')
            if dlg == wx.ID_NO: return mess
            dlg.Destroy()
    if zip:
        planefile=filename; zipfile=outfile
        mess='Created zipfile='+outfile+', source file='+filename
    else:
        planefile=outfile; zipfile=filename
        mess='Created plane file='+outfile+', source zipfile='+filename
    retcode=ZipFile(planefile,zipfile,zip,check=check,message=False)
    # zip/unzip file
    """
    if zip: # zip
        f=open(filename,"r")
        d=f.read()
        f.close()
        f = gzip.open(outfile,"wb",9)  # filename, mode, compress level(1-9)
        f.write(d)
        f.close()
        mess='Created zipfile='+outfile+', source file='+filename
    else: # unzip
        f=gzip.open(filename,"rb")
        d=f.read()
        f.close()
        f=open(outfile,"w")
        f.write(d)
        f.close()
        mess='Created plane file='+outfile+', source zipfile='+filename
    """
    if delinpfile: 
        os.remove(filename)
        mess=mess+'\nDeleted sourcefile='+filename
    if message: print 'lib.ZipUnzipFile: ',mess
    
    if retcode: return outfile
    else: return ''
   
def ZipFile(planefile,zipfile,zip,check=True,message=False):
    """ Zip/unzip file
    
    :param str planefile: plane file name
    :param str zipfile: zipfile name (.gz)
    :param bool zip: True for make zip, False for unzip
    :return: retcode(bool) - True for succceded, False for failed
    """
    retcode=False; mess=''
    if zip:
        inpfile=planefile; outfile=zipfile
    else:
        inpfile=zipfile; outfile=planefile
    if not os.path.exists(inpfile):
        mess='input file='+inpfile+' not found.'
        MessageBoxOK(mess,'lib.ZipFile')
    if os.path.exists(outfile) and message:
        mess='output file='+outfile+' exists. Would you like to overwrite it?'
        dlg=MessageBoxYesNo(mess,'lib.zipfile')
        if dlg == wx.ID_NO: return retcode
        dlg.Destroy()
    # zip/unzip file
    if zip: # zip
        f=open(planefile,"r")
        d=f.read()
        f.close()
        f = gzip.open(zipfile,"wb",9)  # filename, mode, compress level(1-9)
        f.write(d)
        f.close()
        mess='Created zipfile='+zipfile+', source file='+planefile
        retcode=True
    else: # unzip
        f=gzip.open(zipfile,"rb")
        d=f.read()
        f.close()
        f=open(planefile,"w")
        f.write(d)
        f.close()
        mess='Created plane file='+planefile+', source zipfile='+zipfile
        retcode=True
    if message: print 'lib.ZipFile: '+mess
    return retcode

class DropFileTarget(wx.FileDropTarget):
    """ Drag-and-drop files 
    
    Usage:
    In def __init__ method of a window object,
    1. droptarget=lib.DropFileTarget(self)
    2. self.SetDropTarget(droptarget)
    3. make OpenDropFiles(filenames) method in the window object
    """
    def __init__(self,winobj):
        wx.FileDropTarget.__init__(self)
        self.winobj=winobj        

    def OnDropFiles(self,x,y,filenames):
        self.winobj.OpenDropFiles(filenames)

class AAResidueAtoms():
    def __init__(self,parent,resdatadir,hydrogens=True):
        self.parent=parent
        self.resdatadir=resdatadir
        self.hydrogens=hydrogens
        self.resnamlst=["ALA","ARG","ASN","ASP","CYS",
                        "GLN","GLU","GLY","HIS","ILE",
                         "LEU","LYS","MET","PHE","PRO",
                         "SER","THR","TRP","TYR","VAL",
                         "ACE","NME","HIP","HID","HIE"]
        # amino acid structure data file
        self.laafile=os.path.join(self.resdatadir,'l-aa-residues.pdb')
        self.daafile=os.path.join(self.resdatadir,'d-aa-residues.pdb')
        self.laaccdic=self.SetAADic(self.laafile,hydrogens)
        self.daaccdic=self.SetAADic(self.daafile,hydrogens)

    def GetResidueAtomData(self,resnam,chirality):
        """
        
        :param str resnam: residue name
        :param str chirality: 'L' or 'D'
        :return: resdata(lst) - [[elm(str),atmnam(str),[x,y,z]],..]
        """
        if chirality == 'L': return self.laaccdic[resnam]
        else: return self.daaccdic[resnam]
    
    def GetResDataDir(self):
        return self.resdatadir
    
    def SetAADic(self,aafile,hydrogens):
        """
        
        :param bool hydrogens: True for including hydrogens, False for not
        """
        pdbmol,fuoptdic=rwfile.ReadPDBMol(aafile)
        aadic={}
        natm=len(pdbmol[0])
        for res in self.resnamlst:
            for i in range(natm):
                if pdbmol[4][i] == res:
                    if not hydrogens and pdbmol[8][i] == " H": continue
                    if not aadic.has_key(res): aadic[res]=[]
                    aadic[res].append([pdbmol[8][i],pdbmol[2][i],pdbmol[0][i]]) # elm,atmnam,cc
        return aadic
    
def ZMToCC(zelm,zpnt,zprm,removedummy=False):
    """ Zmatrix to Cartessian
    
    :param lst zelm: list of element, [elm1(str*2),elm2(str*2),...]
    :param lst zpnt: point list, [[p1(int),p2(int),p3(int)],...]
    :param lst zprm: geom param list, [length(float),angle(float),torsion(float)],..]
    :return: zmtatm(lst) - list of atom coordinate, [[elm(str*2),x(float),y(float),z(float)],...]
    """
    torad=const.PysCon['dg2rd']
    zmtatm=[]
    nz=len(zpnt)    
    if nz <= 0: return zmtatm # no atom
    #
    # first atom
    iz=0
    zmtatm.append([zelm[iz],0.0,0.0,0.0])
    if nz <= 1: return zmtatm # one atom
    # second atom
    iz=1; x=0.0; y=0.0
    z=zprm[iz][0] 
    zmtatm.append([zelm[iz],x,y,z])
    if nz <= 2: return zmtatm # two atoms
    # third atom
    # convert degrees to radians
    iz=2
    zprm[iz][1]=zprm[iz][1]*torad
    j0=zpnt[iz][0] #-1
    x=zprm[iz][0]*numpy.sin(zprm[iz][1])+zmtatm[j0][1]
    y=0.0
    z=zprm[iz][0]*numpy.cos(zprm[iz][1])+zmtatm[j0][3]
    zmtatm.append([zelm[iz],x,y,z])
    if nz <= 3: return zmtatm
    # convert degrees to radians and reduce point number by 1
    for i in range(3,nz):
        zprm[i][1]=zprm[i][1]*torad; zprm[i][2]=zprm[i][2]*torad
        ###zpnt[i][0] -= 1; zpnt[i][1] -= 1; zpnt[i][2] -= 1
    #
    for j in range(3,nz):
        j0=zpnt[j][0]            
        j1=zpnt[j][1]
        j2=zpnt[j][2]
        p0=[zmtatm[j0][1],zmtatm[j0][2],zmtatm[j0][3]]
        p1=[zmtatm[j1][1],zmtatm[j1][2],zmtatm[j1][3]]
        p2=[zmtatm[j2][1],zmtatm[j2][2],zmtatm[j2][3]]
        r=zprm[j][0]
        # add the atom on normal line of p0-p1-p2
        cc=NormalVector(p0,p1,p2)
        x0=zmtatm[j0][1]
        y0=zmtatm[j0][2]
        z0=zmtatm[j0][3]
        cc=[r*cc[0]+x0,r*cc[1]+y0,r*cc[2]+z0]
        # adjust bond angle
        ax=NormalVector(cc,p0,p1)        
        da=zprm[j][1]-numpy.pi/2.0
        u=RotMatAxis(ax,da)        
        [cc]=RotMol(-u,p0,[cc])
        # adust torsion angle
        ta0=TorsionAngle(cc,p0,p1,p2)
        dt=ta0-zprm[j][2]
        ax=[p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]]
        u=RotMatAxis(ax,dt)
        [cc]=RotMol(u,p0,[cc])
        #        
        zmtatm.append([zelm[j],cc[0],cc[1],cc[2]])
    # remove dummy atoms         
    zmt=[]
    for elm,x,y,z in zmtatm:
        if removedummy and elm == ' X': continue
        zmt.append([elm,x,y,z])
    
    #if displace != 0 and len(zmt) >= 2: zmt[1][2] += displace
        
    zmtatm=zmt
    
    return zmtatm
  
def CCToZM(molobj,zmtpnt=[]):
    """ Convert Cartessian coordinates to Z-Matrix 
    
    :param obj molobj: mol object of fu.
    :return: zelm(lst) - list of elements, [eml1(str*2),elm2(str*2),..]
    :return: zpnt(lst) - point list, [[p0(int),p1(int),p3(int)],...]
    :return: zprm(lst) - paramter list, [[length(float),angle(float),torsion(float)],...]
    """
    def FindConectAtom(iat,natm,molobj,atmlst,iatlst):
        kat=iat
        if len(iatlst) > 0: kat=iatlst[-1]
        jat=-1
        for i in molobj.atm[kat].conect:
            if i < iat and not i in iatlst: 
                jat=i; break
        if jat < 0:
            for j in range(iat):
                atom=molobj.atm[atmlst[j]]
                if kat in atom.conect:
                    if not j in iatlst:
                        jat=j; break
        if jat < 0:
            for j in range(iat):
                if not j in iatlst:
                    jat=j; break
        return jat
    
    todeg=const.PysCon['rd2dg']
    if len(zmtpnt) <= 0: 
        makepnt=True; zpnt=[]
    else: 
        makepnt=False; zpnt=zmtpnt
    #
    zelm=[]; zprm=[]
    natm=0; atmlst=[]
    for atom in molobj.atm:
        if atom.elm == 'XX': continue # skip TER
        natm += 1; atmlst.append(atom.seqnmb); zelm.append(atom.elm)
    # first atom
    if makepnt: zpnt.append([-1,-1,-1])
    #else: zpnt.append(zmtpnt[0])
    zprm.append(['','',''])
    if natm <= 1: return zelm,zpnt,zprm
    # second atom
    iat=atmlst[1]; iat0=atmlst[0]
    if makepnt: 
        zpnt.append([iat0,-1,-1])
    r=Distance(molobj.atm[iat].cc,molobj.atm[iat0].cc)
    zprm.append([r,'',''])
    if natm <= 2: return zelm,zpnt,zprm
    # third atom
    iat=atmlst[2]
    if makepnt:
        iatlst=[]
        for j in range(2):
            jat=FindConectAtom(iat,natm,molobj,atmlst,iatlst)        
            if jat < 0:
                mess='Failed to create point data at atom=3'
                MessageBoxOK(mess,'lib.CCToZM')
                return [],[],[]
            iatlst.append(jat)
        iat0=iatlst[0]; iat1=iatlst[1]
        zpnt.append([iat0,iat1,-1])
    #else:
    iat0=zpnt[2][0]; iat1=zpnt[2][1]
    r=Distance(molobj.atm[iat].cc,molobj.atm[iat0].cc)
    ang=BendingAngle(molobj.atm[iat].cc,molobj.atm[iat0].cc,molobj.atm[iat1].cc)
    zprm.append([r,ang*todeg,''])
    if natm <= 3: return zelm,zpnt,zprm
    # Fourth and later
    if makepnt:
        for i in range(3,natm):
            iatlst=[]; iat=atmlst[i]
            for j in range(3):
                jat=FindConectAtom(iat,natm,molobj,atmlst,iatlst)        
                if jat < 0:
                    mess='Failed to create point data at atom='+str(i)
                    MessageBoxOK(mess,'lib.CCToZM')
                    return [],[],[]
                iatlst.append(jat)
            zpnt.append(iatlst)
    # calc paramters
    for i in range(3,natm):
        iat=atmlst[i]; iat0=zpnt[i][0]; iat1=zpnt[i][1]; iat2=zpnt[i][2]
        r=Distance(molobj.atm[iat].cc,molobj.atm[iat0].cc)
        ang=BendingAngle(molobj.atm[iat].cc,molobj.atm[iat0].cc,molobj.atm[iat1].cc)
        tor=TorsionAngle(molobj.atm[iat].cc,molobj.atm[iat0].cc,molobj.atm[iat1].cc,
                                molobj.atm[iat2].cc)
        zprm.append([r,ang*todeg,tor*todeg])

    return zelm,zpnt,zprm

def CoordFileConverter(fum,inpfile,outfile):
    """ Coordinate file formta converter
    
    
    !!! trial: rewite not to use mol object!!!
    
    :param str infile: input file name, '.pdb','.xyz','mol','sdf','.zmt'
    :param str outfile: output file name, '.pdb','.xyz','mol','.zmt'
    """
    frmlst=['.pdb','.xyz','.mol','.sdf','.zmt']
    mess=''
    if not os.path.exists(inpfile): mess='Not found input file='+inpfile
    base,ifrm=os.path.splitext(inpfile)
    base,ofrm=os.path.splitext(outfile)
    # input format
    if not ifrm in frmlst: mess='Unkown input file descriptor='+ifrm
    if not ofrm in frmlst: mess='Unkown output file descriptor='+ofrm
    if ifrm == ofrm: mess='Same format is specified in input and output. input='+ifrm+', output='+ofrm
    if len(mess) > 0: return mess
    # input format
    mol=molec.Molecule(fum)
    if ifrm == '.pdb':
        pdbmol,fuoptdic=rwfile.ReadPDBMol(inpfile)
        mol.SetPDBMol(pdbmol)
    elif ifrm == '.xyz':
        pass
    elif ifrm == '.mol':
        pass
    elif ifrm == '.sdf':
        pass
    elif ifrm == '.zmt':
        pass
    # output format
    if ofrm == '.pdb':
        pass
    elif ofrm == '.xyz':
        pass
    elif ofrm == '.mol':
        mol.WriteMolMol(outfile,resnam='',title='',comment='')
    elif ofrm == '.sdf':
        pass
    elif ofrm == '.zmt':
        title=mol.name
        zelm,zpnt,zprm=CCToZM(mol)
        rwfile.WriteZMTFile(outfile,title,zelm,zpnt,zprm)
#
def DerXYZEuler(alpha,beta,gamma):
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
    du[1][1][2]=-sb*cc-ca*cb*sc; du[1][2][2]= sc*sb-ca*cb*cc; du[1][3][2]= sa*cb
    du[2][1][2]= cb*cc-ca*sb*sc; du[2][2][2]=-sc*cb-ca*sb*cc; du[2][3][2]= sa*sb
    du[3][1][2]= zero;           du[3][2][2]= zero;           du[3][3][2]= zero
    # derivatives of transformation matrix with respect to gamma.
    du[1][1][3]=-cb*sc-ca*sb*cc; du[1][2][3]=-cc*cb+ca*sb*sc; du[1][3][3]= zero
    du[2][1][3]=-sb*sc+ca*cb*cc; du[2][2][3]=-cc*sb-ca*cb*sc; du[2][3][3]= zero
    du[3][1][3]= sa*cc;          du[3][2][3]=-sa*sc;          du[3][3][3]= zero
    return du
   
def Torque(cc1,cc2,ccp,g,mass=1.0):
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

    
def DispalyTip(parent,text,pos,sleeptime=0):
    tip=subwin.TipString(parent,text,pos=pos,
                     leaveclose=False,bgcolor='yellow')
    tip.SetText(text)
    if sleeptime > 0: 
        wx.Sleep(sleeptime); tip.Close()
    else: return tip
    #return tip

def NetXGraphObject(molobj):
    """ Return graph object created from "mol" object connect data
    
    :param obj molobj: 'mol' object
    :return: netx(obj) - networkx class
             G(object) - graph object
    """
    G=networkx.Graph()
    nodelst=[]; edgelst=[]
    for atom in molobj.atm:
        i=atom.seqnmb
        nodelst.append(i)
        for j in atom.conect:
            if j > i: continue
            edgelst.append([i,j])
    G.add_nodes_from(nodelst)
    G.add_edges_from(edgelst)

    return networkx,G

    