#!/bin/sh
# -*- coding: utf-8 -*- 

import os
import shutil
try: import psutil # downloaded from http://code.google.com/p/psutil/downloads/detail?name=psutil-1.0.1.win32-py2.7.exe&can=2&q=
except: pass
import getpass
import wxversion
wxversion.select("2.8")
import wx
import wx.py
import numpy
import copy
import datetime
import time

import molec
#import model
import draw
import const
import lib
import ctrl

class Customize_Frm(wx.Frame):
    """ Custamize class
    
    :param obj parent: parent object
    :param int id: object id (typically -1 or wx.AnyId)
    :param obj model: instance of Model class
    :param lst winpos: [posx(int),posy(int)]
    :param str winlabel: window label
    """
    def __init__(self,parent,id,model,winpos,winlabel):
        self.title='Custom Setting Panel'
        #winsize=(410,400) 
        winsize=lib.WinSize((410,400)) # 410,400
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX) #|wx.FRAME_FLOAT_ON_PARENT)       
        self.mdlwin=parent
        #xxself.ctrlflag=model.ctrlflag
        self.model=model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.winlabel=winlabel
        #self.platform=self.setctrl.GetParam('platform')
        self.SetBackgroundColour('light gray')
        #
        classnam='Customize_Frm'
        self.pagenamlst=['Setting','General','Model','Add-on','Shortcut','Project'] #,'Mouse','Misc']
        self.parampagedic={'Setting':0,'General':1,'Model':2,'Add-on':3,'Shortcut':4,'Project':5}
        self.pages=[self.Page0,self.Page1,self.Page2,self.Page3,self.Page4,self.Page5]
        self.pageinslst=len(self.pagenamlst)*[None]
        self.fileext=['.py','.general','.model','.add-on','.shortcut'] #,'.project']
        #
        self.customdir=self.setctrl.GetDir('Customize')
        self.prjdir=self.setctrl.GetDir('Projects')
        #
        self.curparamsetdic=self.MakeCurParamSetDic()
        self.paramsetfiledic=self.MakeParamSetFileDic()
        # statusbar
        self.statusbar=self.CreateStatusBar()        
        #
        self.notebook=wx.Notebook(self,wx.ID_ANY)
        self.pagepanels=[]
        self.curpage=0
        #
        self.gonewpage=True
        self.prvpage=0
        #
        self.CreatePagePanels()
        self.StatusMessage('Make parameter set file and set them in "Setting" file')    
        #self.Bind(wx.EVT_MENU,self.OnMenu)
        #self.Bind(wx.EVT_KEY_DOWN,self.OnKeyDown) 
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED,self.OnPageChanged)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGING,self.OnPageChanging)
        self.Show()

    def CreatePagePanels(self):
        npage=len(self.pagenamlst); pagecolor='light gray' #; pagecolors=npage*['light gray']
        # set panels
        for i in range(npage): 
            self.pagepanels.append(wx.Panel(self.notebook,wx.ID_ANY))
            self.pagepanels[i].SetBackgroundColour(pagecolor) #s[i])
            self.notebook.InsertPage(i,self.pagepanels[i],self.pagenamlst[i])
        # page method
        for i in range(npage): self.pages[i]()
             
    def Page0(self): # Setting
        self.pageinslst[0]=CustomSetting(self,self.pagepanels[0],self.model)
        
    def Page1(self): # General
        self.pageinslst[1]=CustomGeneral(self,self.pagepanels[1],self.model)  
        
    def Page2(self): # Model
        self.pageinslst[2]=CustomModel(self,self.pagepanels[2],self.model) 

    def Page3(self): # Add-on
        self.pageinslst[3]=CustomAddOns(self,self.pagepanels[3],self.model)
        
    def Page4(self): # Shortcut
        self.pageinslst[4]=CustomShortcut(self,self.pagepanels[4],self.model)

    def Page5(self): # Project
        self.pageinslst[5]=CustomProject(self,self.pagepanels[5],self.model,'Setting')
        
    def StatusMessage(self,mess):
        self.SetStatusText(mess)    
    
    def Message(self,mess):
        self.SetStatusText(mess)    

    def OnPageChanged(self,event):
        messlst=['Make/modify/delete "Setting" script','Make/modify/delete general parameters',
                 'Make/modify/delete model parameters','Make/modify/delete "Add-on" menus',
                 'Define/modify/delete shortcut-key','Make/modify/delete projects']
        if not self.gonewpage: newpage=self.notebook.ChangeSelection(self.prvpage)
        else:
            self.curpage=self.notebook.GetSelection()
            self.StatusMessage(messlst[self.curpage])
            self.pageinslst[self.curpage].Initialize()
            #event.Skip() # may need to work properly ?

    def OnPageChanging(self,event):
        self.prvpage=self.curpage
        self.gonewpage=True
        if not self.pageinslst[self.prvpage].IsSaved():
            try: 
                prvpage=self.pagenamlst[self.prvpage]
                mess='"'+prvpage+'" is not saved. Are you sure to move?'
            except: mess='previou page is not saved. Are you sure to move?'
            dlg=lib.MessageBoxYesNo(mess,"")
            if not dlg: self.gonewpage=False

    def MenuBar(self):
        filemenu=wx.Menu()
        submenu=wx.Menu()
        filemenu.Append(-1,"Load setting file","Load file")
        filemenu.AppendSeparator()
        filemenu.Append(-1,"Save","Save current settings")
        filemenu.Append(-1,"Save As","Save current settings")
        filemenu.AppendSeparator()
        filemenu.Append(-1,"Close","SClose the window")
        #filemenu.AppendSubMenu(submenu,"File","Load/Save setting file")
        editmenu=wx.Menu()
        editmenu.Append(-1,"Edit setting file","Edit/View setting file")
        #menu.AppendSubMenu(submenu,"edit","Edit setting file")
        menubar=wx.MenuBar()
        menubar.Append(filemenu,"File")
        menubar.Append(editmenu,"Edit")
        return menubar

    def OnMenu(self,event):
        menuid=event.GetId()
        label=self.menubar.GetLabel(menuid)
        if label == "Load setting file":
            print 'Load setting file'
        elif label == "Save":
            print 'Save'
        elif label == "Save As":
            print 'Save As'
        elif label == "Close":
            self.OnClose(1)
        elif label == "Edit setting file":
            print "Edit/View settting file"
        
    def OnClose(self,event):
        try: self.winctrl.Close(self.winlabel)
        except: pass
        self.Destroy()

    def OnKeyDown(self,event):
        if self.keyset.IsEnabled(): self.keyset.OnKeyDown(event)
        
    def MakeCurParamSetDic(self):
        curparamsetdic={}
        cursetfile=self.setctrl.GetSetFile()
        curset=os.path.split(cursetfile)[1]
        curprj=os.path.split(self.setctrl.GetCurPrj())[1]
        curparamsetdic["Setting"]=curset.split('.')[0]
        curparamsetdic["Project"]=curprj.split('.')[0]  
        cursetfile=os.path.expanduser(cursetfile)
        curfilelst=Customize_Frm.ReadSetFile(cursetfile)
        for i in range(len(curfilelst)):
            curparamsetdic[self.pagenamlst[i+1]]=curfilelst[i].split('.')[0]
        return curparamsetdic

    def ChangeCurFile(self,prmnam,curfile):
        self.curfiledic[prmnam]=curfile
        idx=self.panellabels(prmnam)
        self.pagefunc[idx].SetCurFileInComboBox(prmnam)
        
    def MakeParamSetFileDic(self):
        """ not completed """
        """ self.pagenamlst=['Setting','General','Model','Add-on','Shortcut','Project'] """
        paramsetfiledic={}
        for i in range(len(self.pagenamlst)-1):
            filelst=lib.GetFilesInDirectory(self.customdir,[self.fileext[i]])
            paramsetfiledic[self.pagenamlst[i]]=self.MakeParamSetName(filelst)
        # project files
        filelst=lib.GetFilesInDirectory(self.prjdir,[self.fileext[i]])
        paramsetfiledic['Project']=self.MakeParamSetName(filelst)
        
        return paramsetfiledic

    def ResetSettingFile(self,setnam,curparamsetdic):
        self.curparamsetdic=curparamsetdic
        # setting panel instance
        self.pageinslst[0].curparamsetdic=self.curparamsetdic
        # reset current param set
        if setnam == 'all' or setnam == 'General':
            self.pageinslst[1].ResetCurrentSet(self.curparamsetdic['General'])
        if setnam == 'all' or setnam == 'Model':
            self.pageinslst[2].ResetCurrentSet(self.curparamsetdic['Model'])
        if setnam == 'all' or setnam == 'Add-on':
            self.pageinslst[3].ResetCurrentSet(self.curparamsetdic['Add-on'])
        if setnam == 'all' or setnam == 'Shortcut':
            self.pageinslst[4].ResetCurrentSet(self.curparamsetdic['Shortcut'])
        # project panel instance ???
        self.pageinslst[5].SetCurSetFileInComboBox(self.curparamsetdic['Setting'])

    def GetParamSetFilelst(self,prmset,fileext):
        # prmset: Projects,...
        # fileext: '.project'
        filelst=[]
        prmdir=self.setctrl.GetDir(prmset)
        filelst=lib.GetFilesInDirectory(prmdir,[fileext])
        self.filelst=self.MakeParamSetName(filelst)
        return filelst
        
    def MakeParamSetName(self,filelst):
        for i in range(len(filelst)):
            head,tail=os.path.split(filelst[i])
            base,ext=os.path.splitext(tail)
            filelst[i]=base
        return filelst

    def ConvertParamsForCustomize(self,paramsdic,paramtypedic):
        modeldic={0:'line',1:'stick',2:'ball-and-stick',3:'CPK'}
        for prmnam,value in paramsdic.iteritems():
            if paramtypedic[prmnam] == 'dic-color':
                paramsdic[prmnam]=self.ConvertColor4To3InDic(paramsdic[prmnam])
            if paramtypedic[prmnam] == 'color': 
                value=numpy.array(value); value=255*value; value=value[:3]
                paramsdic[prmnam]=value
            if prmnam == 'mol-model' and modeldic.has_key(paramsdic[prmnam]): 
                paramsdic[prmnam]=modeldic[paramsdic[prmnam]]
        return paramsdic
                      
    def ConvertColor4To3InDic(self,colordic):
        for item,color in colordic.iteritems():
            color=numpy.array(color); color=255*color; color=color[:3]
            colordic[item]=color
        return colordic
                      
    def GetCurrentParamSet(self,setnam):
        if self.curparamsetdic.has_key(setnam): return self.curparamsetdic[setnam]
        else: return None
            
    def SetCurrentParamSet(self,setnam,curset):
        self.curparamsetdic[setnam]=curset
        self.pageinslst[0].ResetCurrentParamFile(setnam,curset)       
        
    def GetCurrentParamSetDic(self):
        return self.curparamsetdic
    
    def SetCurrentParamSetDic(self,paramsetdic):
        self.curparamsetdic=paramsetdic

    def AddExtToFilename(self,filename,filext):
        ns=filename.find(filext)
        if ns < 0: filename=filename+filext
        return filename
             
    def MakeFullPathName(self,filename,filext): #,panelnam):
        ns=filename.find(filext)
        if ns < 0: filename=filename+filext
        filename=os.path.join(self.customdir,filename)
        return filename

    def IsFileExists(self,filename):
        if os.path.exists(filename): return True
        else:
            mess='"'+filename+'" does not exist.'
            self.StatusMessage(mess)
            return False
                            
    def GetSelectedFileNameInCombo(self,comboboxobj):
        filename=comboboxobj.GetValue()
        #if len(filename) <= 0:
        #    mess='Input file name in the left window.'
        #    lib..MessageBoxOK(mess,"")
        return filename

    def MakeParamTypeDic(self,paramdata):
        paramtypedic={}
        for prmnam,data in paramdata.iteritems():
            paramtypedic[prmnam]=data[3]
        return paramtypedic 

    def MakeParamWidgetDic(self,paramobjdic): 
        paramwidgetdic={}
        for prmnam,lst in paramobjdic.iteritems():
            paramwidgetdic[prmnam]=[lst[0],lst[1],lst[2]]
        return paramwidgetdic

    def GetButtonColors(self,buttonobjdic):
        """ Get button color in RGB form
        
        :param dic buttonobjdic: {'varibale name:buttonobject,...}
        :return dic colordic: {'variable naem:color,...}
        """
        colordic={}
        for varnam,obj in buttonobjdic.iteritems():
            wxcolor=obj[0].GetBackgroundColour()
            colordic[varnam]=wxcolor.Get()
        return colordic

    def XXGetButtonColorRGB(self,buttonobj):
        """ Get button color and convert it to RGB(0-1)
        
        :param obj buttonobj: button object
        :return: color: [R,G,B] (R,G,B range 0-1)
        :rtype: lst
        """
        wxcolor=buttonobj.GetBackgroundColour() # wx.Colour object
        color=numpy.array(wxcolor.Get())/255.0 # convert to RGB [0-255]/255
        return color

    def SetColorOnButtons(self,colorobjdic,colordic): #,objlabel,varnamlst,colordic):
        """
        panel: self.atmpan,self.respan, self.chapan
        objlabel: 'element', 'residue','chain'
        varnamlst elmcolordic.keys(), ex. varnam=' H' for elmcolorlst
        coloddic  elmcolordic
        evthandler self.OnButtonColor
        colorobjdic[objlabel]=[varnam,btncol]
        """
        for item, color in colordic.iteritems(): colorobjdic[item][0].SetBackgroundColour(color)

    def ViewSelectedFile(self,cmbfil,filext):
        filename=cmbfil.GetStringSelection()
        if len(filename) <= 0: return
        filename=self.MakeFullPathName(filename,filext)
        ans=self.IsFileExists(filename)
        if not ans: return
        lib.Editor(filename) #1(self.platform,filename)

    def ViewFile(self,filename,filext):
        ans=self.IsFileExists(filename)
        if not ans: return
        lib.Editor(filename) #1(self.platform,filename)

    def DelSelectedFile(self,cmbfil,filext):
        filename=cmbfil.GetStringSelection()
        if len(filename) <= 0: return
        filename=self.MakeFullPathName(filename,filext)
        ans=self.IsFileExists(filename)
        if not ans: return
        os.remove(filename)

    @staticmethod
    def WriteProjectFile(filename,prjnam,prjitems):
        #prjitems=[prjpath,curdir,setting,createdby,createddate,comment]
        #prjdir=self.GetDir(self.panelnam)
        #prjfile=prjdat[0]+'.txt'
        #filename=os.path.join(prjdir,prjfile)
        f=open(filename,'w')
        f.write('# project file. '+lib.CreatedByText()+'\n')
        f.write('prjnam='+prjnam+'\n')
        f.write('prjpath='+prjitems[1]+'\n')
        f.write('curdir='+prjitems[2]+'\n')
        f.write('setting='+prjitems[3]+'\n')
        f.write('createdby='+prjitems[4]+'\n')
        f.write('createddate='+prjitems[5]+'\n')
        f.write('comment='+prjitems[6]+'\n')

        f.close()        

    @staticmethod         
    def CreateProjectDirectory(prjnam,prjdirnam):
        """ create project file 'fudir/Projects/prjnam.project' and project diretory ('prjrootdir/prjnam')
        and its subsirectories (/Images, /Draws and /Docs)
        
        :param str prjnam: project name
        :param str prjrootdir: root directory of the project. the project directory is
        prjrootdir/prjnam 
        :return: retcode: True for succeeded, False for Failed
        :rtype: bool
        """
        retmess=''
        prjsubdirs=['Docs','Images','Draws']
        # make project directory
        if not os.path.isdir(prjdirnam): 
            try: os.mkdir(prjdirnam)
            except:
                 retmess='Failed to create project dirctory "'+prjdirnam+'"'
        # make sub-directories
        if os.path.isdir(prjdirnam): 
            try:
                for d in prjsubdirs:
                    ddir=os.path.join(prjdirnam,d)
                    if not os.path.isdir(ddir): os.mkdir(ddir)
            except:
                retmess='Failed to create project sub-directories in "'+prjdirnam+'"'
        return retmess        

    @staticmethod
    def WriteParamSetFile(filename,text,paramtypedic,paramsdic):
        modeldic={'line':0,'stick':1,'ball-and-stick':2,'CPK':3}
        rgb=255.0 # r,g,b in Customize range 0-255
        paramlabel=paramtypedic.keys()
        f=open(filename,"w")
        f.write('# fu '+text+' '+lib.CreatedByText()+'\n')
        for prmnam in paramlabel:
            if not paramsdic.has_key(prmnam): continue
            f.write("'"+prmnam+"'"+'\n')
            if paramtypedic[prmnam] == 'dic-color':
                colordic=paramsdic[prmnam]
                for name, color in colordic.iteritems():
                    if not isinstance(name,str): name=str(name)
                    if prmnam == 'element-color':
                        if len(name) <= 1: name=name.rjust(2,' ')
                    f.write(name+' '+str(color[0]/rgb)+' '+str(color[1]/rgb)+' '+str(color[2]/rgb)+' 1.0\n')            
            elif paramtypedic[prmnam] == 'color':
                color=paramsdic[prmnam]
                f.write(str(color[0]/rgb)+' '+str(color[1]/rgb)+' '+str(color[2]/rgb)+' 1.0\n') 
            elif paramtypedic[prmnam] == 'int':
                f.write(str(paramsdic[prmnam])+'\n')
            elif paramtypedic[prmnam] == 'float':
                f.write(str(paramsdic[prmnam])+'\n')
            elif paramtypedic[prmnam] == 'bool':
                f.write(str(paramsdic[prmnam])+'\n')
            elif paramtypedic[prmnam] == 'model':
                if paramsdic[prmnam] == '': f.write('0\n')
                else: f.write(str(modeldic[paramsdic[prmnam]])+'\n')
            else: pass
        f.close()

    @staticmethod
    def ReadSetFile(filename):
        general=''; model=''; addon=''; shortcut=''
        if not os.path.exists(filename):
            return [general,model,addon,shortcut]
        f=open(filename,'r')
        for s in f.readlines():
            s=s.strip()
            if s[1:] == '#': continue
            if len(s) <= 0: continue
            items=s.split('(')
            if items[0] == 'fum.setctrl.LoadGeneralParamSet':
                general=items[1][:-1]; general=general[1:-1]
            if items[0] == 'fum.setctrl.LoadModelParamSet':
                model=items[1][:-1]; model=model[1:-1]
            if items[0] == 'fum.setctrl.LoadAddonMenuItems':    
                addon=items[1][:-1]; addon=addon[1:-1]
            if items[0] == 'fum.setctrl.LoadShortcut':
                shortcut=items[1][:-1]; shortcut=shortcut[1:-1]
        f.close()
        return [general,model,addon,shortcut]
    
    @staticmethod
    def XXReadParamSetFile(filename,paramtypedic):
        modeldic={'0':'line','1':'stick','2':'ball-and-stick','3':'CPK'}
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
                    colordic[name]=[r,g,b]
                elif paramtypedic[prmnam] == 'color':
                    items=s.split()
                    r=float(items[0]); g=float(items[1]); b=float(items[2])
                    paramdic[prmnam]=[r*255,g*255,b*255]
                elif paramtypedic[prmnam] == 'int':
                    paramdic[prmnam]=s.strip()
                elif paramtypedic[prmnam] == 'float': 
                    paramdic[prmnam]=s.strip()
                elif paramtypedic[prmnam] == 'bool': 
                    paramdic[prmnam]=booldic[s.strip()]
                elif paramtypedic[prmnam] == 'model':
                    model=modeldic[str(s.strip())]
                    paramdic[prmnam]=model  #modeldic[s.strip()]
                else: paramdic[prmnam]=s.strip() # 'str'
        f.close()
        
        return paramdic

class CustomSetting():
    """ Setting setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj model: instance of 'Model' class
    """
    def __init__(self,parent,pagepanel,model):
        self.classnam='SettingModel'
        self.panelnam='Setting'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model #parent.model #self.parent.model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #
        self.saved=True
        self.saveas=False
        self.rename=False
        # itemlabels: ['General','Model','Add-on','Shortcut']
        self.itemlabels=self.parent.pagenamlst
        del self.itemlabels[0] # Setting
        try: del self.itemlabels[4] # Project
        except: pass
        self.genfile=''
        self.modelfile=''
        self.addon1file=''
        self.addon2file=''
        self.fmoflag=False      
        self.curparamsetdic=self.parent.curparamsetdic
        #
        self.curset=self.parent.curparamsetdic[self.panelnam] #self.parent.curset
        self.curprj='None'
        self.paramsetfiledic=self.parent.paramsetfiledic
        #
       # create setting panel
        self.CreatePanel()
        # set data on widgets
        self.OnProject(-1)
                     
    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        self.panel=self.pagepanel
        self.viewiddic={}; self.comboboxlabeldic={}; self.statictextdic={} #self.browseiddic={}; self.tcliddic={}
        hcb=const.HCBOX
        yloc=10; xloc=0
        # create file button
        title='Setting file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(10,yloc),size=(90,18)) 
        sttip.SetToolTipString('Select setting name(file,*setting)')
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(100,yloc-2),size=(200,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnSetFile)  
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        
        self.cmbfil.SetItems(self.paramsetfiledic[self.panelnam])
        #self.cmbfil.SetValue(self.curset)
        self.cmbfil.SetStringSelection(self.curparamsetdic[self.panelnam])
        #self.cmbfil.SetStringSelection(self.cursetfile)
        btnview=wx.Button(self.panel,-1,"View",pos=(320,yloc-2),size=(40,20))
        btnview.SetToolTipString('View or edit the file with editor')
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile) 
        #  
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL) 
        yloc += 10
        text="Param set in the loaded setting file: "+'"'+self.curparamsetdic[self.panelnam]+'"'
        self.stseting=wx.StaticText(self.panel,-1,text,pos=(xloc+10,yloc),size=(w-20,18))
        yloc += 25; # general
        for label in self.itemlabels:
            text=label+' params set file '+'"'+self.curparamsetdic[label]+'"'
            stlabel=wx.StaticText(self.panel,-1,text,pos=(xloc+20,yloc),size=(w-120,18))
            self.statictextdic[label]=stlabel
            yloc += 20
            wx.StaticText(self.panel,-1,'change to',pos=(xloc+80,yloc),size=(70,18))
            #ID=wx.NewId()               
            cmb=wx.ComboBox(self.panel,-1,"",pos=(xloc+150,yloc-4),size=(180,hcb))
            cmb.SetItems(['None']+self.paramsetfiledic[label])
            cmb.SetStringSelection(self.curparamsetdic[label])
            cmb.Bind(wx.EVT_COMBOBOX,self.OnParamFile)
            self.comboboxlabeldic[label]=cmb
            ID=wx.NewId()
            btn=wx.Button(self.panel,ID,"View",pos=(xloc+345,yloc-4),size=(40,20))
            btn.Bind(wx.EVT_BUTTON,self.OnViewParamSetFile)
            self.viewiddic[ID]=[label,btn]        
            yloc += 20
        # put buttons
        pos=[-1,yloc]
        self.butnpan=CommonActionButtons(self.parent,self.pagepanel,self,pos)
        yloc += 40
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL) 
        yloc += 15
        # setting button
        btncur=wx.Button(self.panel,-1,"Apply as current setting",pos=(130,yloc-2),size=(150,20))
        btncur.Bind(wx.EVT_BUTTON,self.OnSetCurrent)
        yloc += 25
        sttip=wx.StaticText(self.panel,-1,'to project: ',pos=(30,yloc),size=(60,18)) 
        sttip.SetToolTipString('Select project for settings')
        self.cmbprj=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(100,yloc-2),size=(200,hcb))
        self.cmbprj.Bind(wx.EVT_COMBOBOX,self.OnProject)
        self.cmbprj.SetItems(self.paramsetfiledic['Project'])
        self.cmbprj.SetValue(self.curprj) #SetStringSelection(self.curparamsetdic['Project'])
        btnviewprj=wx.Button(self.panel,-1,"View",pos=(320,yloc-2),size=(40,20))
        btnviewprj.SetToolTipString('View or edit the file with editor')
        btnviewprj.Bind(wx.EVT_BUTTON,self.OnViewProjectFile) 
        #self.butnpan.btndefa.Disable()
      
    def Initialize(self):
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        #self.prjfilelst=self.parent.paramsetfiledic[self.panelnam]
        #self.prjfilelst=['None']+self.prjfilelst
        #prjdir=self.setctrl.GetDir('Projects')
        #prjfilelst=lib.GetFilesInDirectory(prjdir,['.project'])
        #self.prjfilelst=self.parent.MakeParamSetName(prjfilelst)
        #self.prjfilelst=['None']+self.prjfilelst
        self.prjfilelst=self.parent.GetParamSetFilelst('Projects','.project')
        self.curset=self.parent.curparamsetdic[self.panelnam]
        self.curprj='None' #self.curparamsetdic['Project'] #self.parent.curprj #os.path.split(self.curprjfile)[1]
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetValue(self.curset)
        self.cmbprj.SetItems(self.prjfilelst)
        self.cmbprj.SetValue(self.curprj)
        #if self.curset == "":
        #    self.cmbfil.SetValue(self.curset)
        #    self.LoadDefault()
        #    mess='No paramter set file. Default param set is loaded.'
        #    wx.MessageBox(mess,"",style=wx.OK|wx.ICON_EXCLAMATION)           
        #else: self.cmbfil.SetStringSelection(self.curset)
        #
        self.OnSetFile(1)
        #
        self.saveas=False
        self.saved=True

    def OnSetCurrent(self,event):        
        # setfile name
        setnam=self.cmbfil.GetValue()
        setfile=setnam+'.py'
        setfile=self.parent.MakeFullPathName(setfile,'.py')
        if not os.path.exists(setfile): self.SaveFile()
        # project name
        prjnam=self.cmbprj.GetValue()
        if len(prjnam) <= 0: 
            self.parent.Message('No project name in "to project" window.')
            return
        prjdir=self.setctrl.GetDir('Projects')
         # rewrite "setting" file name in project file
        filename=prjnam+'.project'
        filename=os.path.join(prjdir,filename)
        if not os.path.exists(filename):
            self.parent.Message('project file "'+filename+'" does not exists.')
            return
        prjitems=self.setctrl.ReadProjectFile(filename)          
        #prjitems=[prjpath,curdir,setting,createdby,createddate,comment]
        #prjitems[5]=setnam
        #
        Customize_Frm.WriteProjectFile(filename,prjnam,prjitems)
        # rewrite fumodel.ini file
        
        
        self.parent.Message('"'+prjnam+'" project is set as current in fumodel.ini file.')
        self.saved=True        
        
    def OnSetFile(self,event):
        # get setfile in combobox
        setfile=self.cmbfil.GetValue()
        self.curparamsetdic[self.panelnam]=setfile
        setfile=setfile+'.py'
        filename=os.path.join(self.parent.customdir,setfile)
        setdat=self.parent.ReadSetFile(filename)
        for i in range(len(self.itemlabels)): self.curparamsetdic[self.itemlabels[i]]=setdat[i]
        #
        for label,cmb in self.comboboxlabeldic.iteritems():
            cmb.SetStringSelection(self.curparamsetdic[label])
        # set labels
        text="Param set in the loaded setting file: "+'"'+self.curparamsetdic[self.panelnam]+'"'
        self.stseting.SetLabel(text)
        for label, obj in self.statictextdic.iteritems():
            text=label+' params set file '+'"'+self.curparamsetdic[label]+'"'
            obj.SetLabel(text)
        # reset curparamset in all pagepanels
        if event != -1: self.parent.ResetSettingFile('all',self.curparamsetdic)

        self.parent.Message('Saved "'+filename+'".')
        self.saved=True

    def OnParamFile(self,event):
        #ID=event.GetId()
        #cmb=self.comboboxiddic[ID][1]
        #label=self.comboboxiddic[ID][0]
        for prmnam, cmb in self.comboboxlabeldic.iteritems():
            curset=cmb.GetStringSelection()
            self.curparamsetdic[prmnam]=curset
            self.parent.ResetSettingFile(prmnam,self.curparamsetdic)

    def ResetCurrentParamFile(self,setnam,curset):
        #comboboxlabeldic={}
        #for id, labobj in self.comboboxiddic.iteritems():
        #    comboboxlabeldic[labobj[0]]=labobj[1]
        return
    
        if not self.comboboxlabeldic.has_key(setnam): return
        self.comboboxlabeldic[setnam].SetStringSelection(curset)

    def OnProject(self,event):
        curprj=self.cmbprj.GetStringSelection()
        filename=curprj+'.project'
        filename=os.path.join(self.parent.prjdir,filename)
        if not os.path.exists(filename): return
        # prjdat:[prjdir,createdby,createddate,comment,curdir,setting]
        prjdat=self.setctrl.ReadProjectFile(filename)
        setfile=prjdat[6]
        self.curparamsetdic['Setting']=setfile
        self.cmbfil.SetStringSelection(setfile)
        
        self.OnSetFile(event)

    def OnNewFile(self,event):
        self.parent.Message('')
        if not self.saveas and not self.rename: return
        setnam=self.cmbfil.GetValue() #GetStringSelection()
        print 'setnam',setnam
        if len(setnam) <= 0: 
            self.parent.Message('No file name in "Setting file" window')
            return
        try: idx=self.paramsetfiledic[self.panelnam].index(setnam) #self.filelst.index(setnam)
        except: idx=-1
        if idx >= 0:
            mess='the name is duplicate. please input a different name'
            lib.MessageBoxOK(mess,"")
            return
        #
        if self.rename: 
            retcode=self.Rename(self.curset,setnam)
            self.cmbfil.SetValue(self.curset)      
        if self.saveas:
            self.SaveFile()
            #
            self.curset=setnam
            self.filelst.append(self.curset)
            self.cmbfil.SetItems(self.paramsetfiledic[self.panelnam])
            self.cmbfil.SetStringSelection(self.curset)
            #
            self.parent.Message('Created new setting file '+'"'+setnam+'"')
            # update 'Model' current and filelst
            self.parent.SetCurrentParamSet(self.panelnam,self.curset)
            #self.parent.paramsetfiledic[self.panelnam]=self.filelst
            #
            self.saveas=False
        #
        self.saveas=False 
        self.rename=False

    def OnViewFile(self,event):
        self.parent.ViewSelectedFile(self.cmbfil,'.py') #,self.panelnam)

    def OnViewParamSetFile(self,event):
       ID=event.GetId()
       label=self.viewiddic[ID][0]; cmb=None
       #for key, labobj in self.comboboxlabeldic.iteritems():
       #    if labobj[0] == label: cmb=labobj[1]; break
       if self.comboboxlabeldic.has_key(label): cmb=self.comboboxlabeldic[label]
       else: cmb=None
       filext='.'+label.lower()
       self.parent.ViewSelectedFile(cmb,filext)
        
    def OnViewProjectFile(self,event):
        filename=self.cmbprj.GetValue()
        filename=filename+'.project'
        filename=os.path.join(self.parent.prjdir,filename)
        self.parent.ViewFile(filename,'.project')
        
    def ClearAllTextInTCL(self):
        for key, value in self.tcliddic.iteritems(): 
            print 'label',value[0]
            value[1].SetValue('')

    def SetCurFileInComboBox(self,prmnam):
        for key,lst in self.comboboxlabeldic.iteritems():
            if key == prmnam: lst.SetValue(self.curfiledic[prmnam])

    def Apply(self):
        self.saved=True
        pass

    def IsSaved(self):
        return self.saved

    def Undo(self):
        self.saved=True
    
    def Cancel(self):
        mess='Setting was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True

    def GetParamsFromWidgets(self):
        """
        :return lst paramset: paramset:[general param set name,model param set name,
        'add-on menu items,'shortcut definition name]
        """
        # itemlabels: ['General','Model','Add-on','Shortcut']
        self.paramsdic={}
        for label in self.itemlabels:
            prmset=self.comboboxlabeldic[label].GetValue()
            if len(prmset) > 0: self.paramsdic[label]=prmset

    def Rename(self,oldnam,newnam):
        customdir=self.setctrl.GetDir('Customize')
        oldfile=os.path.join(customdir,oldnam+'.py')
        newfile=oldfile.replace(oldnam,newnam)
        if os.path.exists(newfile):
            mess='the file "'+newfile+' " already exists. try a diferent name.'
            self.parant.Message(mess)
            return False
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+oldnam+'" to "'+newnam+'"'
            return False
        idx=self.filelst.index(oldnam)       
        if idx >= 0: 
            #self.filelst[idx]=newnam
            self.paramsetfiledic[self.panelnam][idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+oldnam+'" to "'+newnam+'"')
            return False          
        self.curset=newnam
        # set items to widget
        self.cmbfil.SetItems(self.paramsetfiledic[self.panelnam]) #self.filelst)
        self.cmbfil.SetValue(self.curset)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        #self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('Renamed '+'"'+oldnam+'" to "'+newnam+'"')            
        return True

    def RenameFile(self):
        self.rename=True
        mess='Input name in "Setting file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                                            
    def SaveFile(self):
        self.saveas=False
        self.GetParamsFromWidgets()
        if len(self.paramsdic) <= 0:
            self.parent.Message('Nothing to write in setting file')
            return           
        filename=self.cmbfil.GetValue()
        if len(filename) <= 0: 
            self.parent.Message('No file name in "Setting file" window')
            return
        filename=self.parent.MakeFullPathName(filename,'.py')
        print 'filename in save',filename 
        self.lblgen='fum.setctrl.LoadGeneralParamSet('
        self.lblmdl='fum.setctrl.LoadModelParamSet('
        self.lblsht='fum.setctrl.LoadShortcut('
        self.lbladd='fum.setctrl.LoadAddonMenuItems('
        textlst=[]
        if os.path.exists(filename):
            # read
            f=open(filename,'r')
            for s in f.readlines(): textlst.append(s)
            f.close()
            textlst=self.UpdateParamSetInSetting(textlst)
        else:
            for prmnam,prmfile in self.paramsdic.iteritems():
                if prmnam == 'General':
                    textlst.append(self.lblgen+"'"+prmfile+"')\n")
                elif prmnam == 'Model':
                    textlst.append(self.lblmdl+"'"+prmfile+"')\n")
                elif prmnam == 'Shortcut':
                    textlst.append(self.lblsht+"'"+prmfile+"')\n")
                elif prmnam == 'Add-on':
                    textlst.append(self.lbladd+"'"+prmfile+"')\n")           
        # write
        f=open(filename,'w')
        for s in textlst: f.write(s)
        f.close()
        
    def UpdateParamSetInSetting(self,textlst):
        newtextlst=[]
        ngen=len(self.lblgen); nmdl=len(self.lblmdl); nsht=len(self.lblsht); nadd=len(self.lbladd)
        for text in textlst:
            ns=text.find(self.lblgen)
            if ns >= 0 and self.paramsdic.has_key('General'):
                head=text[:ns+ngen]; ne=text.find(')'); tail=text[ne:]
                text=head+"'"+self.paramsdic['General']+"'"+tail+'\n'
                newtextlst.append(text); continue
            ns=text.find(self.lblmdl)
            if ns >= 0 and self.paramsdic.has_key('Model'):
                head=text[:ns+nmdl]; ne=text.find(')'); tail=text[ne:]
                text=head+"'"+self.paramsdic['Model']+"'"+tail+'\n'
                newtextlst.append(text); continue
            ns=text.find(self.lblsht)
            if ns >= 0 and self.paramsdic.has_key('Shortcut'):
                head=text[:ns+nsht]; ne=text.find(')'); tail=text[ne:]
                text=head+"'"+self.paramsdic['Shortcut']+"'"+tail+'\n'
                newtextlst.append(text); continue
            ns=text.find(self.lbladd)
            if ns >= 0 and self.paramsdic.has_key('Add-on'):
                head=text[:ns+nadd]; ne=text.find(')'); tail=text[ne:]
                text=head+"'"+self.paramsdic['Add-on']+"'"+tail+'\n'
                newtextlst.append(text); continue
            newtextlst.append(text)                     
        return newtextlst

    def LoadDefault(self):
        for prmnam, cmb in self.comboboxlabeldic.iteritems(): cmb.SetValue('None')        
            
    def SaveFileAs(self):
        self.saveas=True
        mess='Input file name in "Setting file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')

    def DelFile(self):
        self.parent.DelSelectedFile(self.cmbfil,'.py')
        setnam=self.cmbfil.GetValue()
        self.filelst.remove(setnam)
        self.cmbfil.SetItems(self.filelst)
        if len(self.filelst) > 0: self.curset=self.filelst[0]
        else: self.curset=''
        self.cmbfil.SetStringSelection(self.curset)
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('setting file "'+setnam+'" was deleted')   
                    
    def Cancel(self):
        mess='Setting was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True

class CustomModel():
    """ Model setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj model: instance of 'Model' class
    """
    def __init__(self,parent,pagepanel,model):
        self.classnam='SettingModel'
        self.panelnam='Model'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model #parent.model #self.parent.model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #
        self.saved=True
        self.newfile=False
        self.rename=False
        self.itemcolordic={} # rgb:0-255
        #     
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        #
        self.paramtypedic=self.setctrl.MakeParamTypeDic()
        """ note: rewrite the program using paramtipsdic """
        self.paramtipsdic=self.setctrl.MakeParamTipsDic()
        # setup default parameters
        self.defaultparamsdic=self.GetDefaultModelParams()
        
        self.paramsdic=copy.deepcopy(self.defaultparamsdic)
        # define values in panels
        self.modellst=['line','stick','ball-and-stick','CPK']
        self.model=self.paramsdic['mol-model']
        self.bndthick=self.paramsdic['bond-thick']
        self.atmsphererad=self.paramsdic['atom-sphere-radius']
        self.hbcolor=self.paramsdic['hydrogen-bond-color']
        self.hbthick=self.paramsdic['hydrogen-bond-thick']
        self.tubecolor=self.paramsdic['aa-tube-color']
        self.tuberad=self.paramsdic['aa-tube-radius']
        #
        self.elmcolordic=self.defaultparamsdic['element-color']
        self.elmnamlst=self.elmcolordic.keys()
        self.rescolordic=self.defaultparamsdic['aa-residue-color']
        self.resnamlst=self.rescolordic.keys()
        self.chaincolordic=self.defaultparamsdic['aa-chain-color']
        self.chainnamlst=self.chaincolordic.keys()
        # create panel
        self.CreatePanel()
        # make type and widget object dictionary
        paramobj=self.ParamObjDefinition()
        self.paramwidgetdic=self.parent.MakeParamWidgetDic(paramobj)
        #
        self.Initialize()
             
    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        self.panel=self.pagepanel
        hcb=const.HCBOX
        yloc=10
        # create file button
        title='Model param set file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(10,yloc),size=(140,18)) 
        sttip.SetToolTipString('Select model parameter set name(file,*.model)')
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(150,yloc-2),size=(180,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnFile)
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetStringSelection(self.curset)
        btnview=wx.Button(self.panel,-1,"View",pos=(350,yloc-2),size=(40,20))
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile) 
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL) 
        yloc += 10
        wx.StaticText(self.panel,-1,"Default model:",pos=(10,yloc),size=(90,18)) 
        self.cmbmdl=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(100,yloc-2),size=(120,hcb))
        self.cmbmdl.SetItems(self.modellst)
        yloc += 25
        wx.StaticText(self.panel,-1,"Atom sphere radius:",pos=(10,yloc),size=(120,18))      
        self.tclatmrad=wx.TextCtrl(self.panel,-1,'',pos=(140,yloc-2),size=(30,18))
        wx.StaticText(self.panel,-1,"bond thickness:",pos=(195,yloc),size=(95,18))      
        self.tclbndthck=wx.TextCtrl(self.panel,-1,'',pos=(295,yloc-2),size=(30,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"Hydrogen bond color:",pos=(10,yloc),size=(120,18))  
        self.btnhbcol=wx.Button(self.panel,wx.ID_ANY,"",pos=(140,yloc-2),size=(20,15))
        self.btnhbcol.Bind(wx.EVT_BUTTON,self.OnButtonColor)
        wx.StaticText(self.panel,-1,"bond thickness:",pos=(175,yloc),size=(90,18))       
        self.tclhbthick=wx.TextCtrl(self.panel,-1,str(self.hbthick),pos=(275,yloc-2),size=(30,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"Chain tube color:",pos=(10,yloc),size=(120,18))  
        self.btntubecol=wx.Button(self.panel,wx.ID_ANY,"",pos=(140,yloc-2),size=(20,15))
        self.btntubecol.Bind(wx.EVT_BUTTON,self.OnButtonColor) 
        wx.StaticText(self.panel,-1,"tube thickness:",pos=(175,yloc),size=(90,18))       
        self.tcltuberad=wx.TextCtrl(self.panel,-1,'',pos=(275,yloc-2),size=(30,18))
        yloc += 20
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL)  
        yloc += 10; yloc0=yloc; height=100
        self.colorpanelobjdic={}
        # elm color panel
        xloc=25; xloc0=xloc
        yloc=yloc0; width1=100
        wx.StaticText(self.panel,-1,"Element color",pos=(xloc+10,yloc),size=(80,18)) 
        yloc += 20
        elmpan,colorobjdic=self.CreateColorButtonPanel([xloc,yloc],[width1,height],
                         'element',self.elmnamlst,self.elmcolordic)
        self.colorpanelobjdic['element']=[elmpan,colorobjdic,[xloc,yloc],[width1,height]]
        # res color panel
        xloc += width1+25; width2=100; yloc=yloc0; xloc1=xloc
        wx.StaticText(self.panel,-1,"Residue color",pos=(xloc+10,yloc),size=(80,18)) 
        yloc += 20
        # chain color panel
        respan,colorobjdic=self.CreateColorButtonPanel([xloc,yloc],[width2,height],
                         'residue',self.resnamlst,self.rescolordic)
        self.colorpanelobjdic['residue']=[respan,colorobjdic,[xloc,yloc],[width2,height]]
        xloc += width2+25; width3=100; yloc=yloc0; xloc2=xloc
        wx.StaticText(self.panel,-1,"Chain color",pos=(xloc+10,yloc),size=(80,18)) 
        yloc += 20
        chapan,colorobjdic=self.CreateColorButtonPanel([xloc,yloc],[width3,height],
                         'chain',self.chainnamlst,self.chaincolordic)
        self.colorpanelobjdic['chain']=[chapan,colorobjdic]
        # elm add/del button
        self.inputtcldic={}; self.adddelbtnlst=[]
        yloc=yloc0+height+30; xloc0 -= 5
        self.CreateAddDelButton(0,(xloc0,yloc-2))
        # res add/del button
        yloc=yloc0+height+30; xloc1 -= 5
        self.CreateAddDelButton(2,(xloc1,yloc-2))
        # chain add/del button
        yloc=yloc0+height+30; xloc2 -= 5
        self.CreateAddDelButton(4,(xloc2,yloc-2))
        yloc=yloc+20
        # put common buttons
        pos=[-1,yloc]
        self.butnpan=CommonActionButtons(self.parent,self.pagepanel,self,pos)          

    def CreateAddDelButton(self,addbtnnmb,pos):
        xloc=pos[0]; yloc=pos[1]
        ID=wx.NewId()
        tclinp=wx.TextCtrl(self.panel,ID,'',pos=(xloc,yloc),size=(30,18),style=wx.TE_PROCESS_ENTER)
        tclinp.Bind(wx.EVT_TEXT_ENTER,self.OnInputItem)
        self.inputtcldic[ID]=[addbtnnmb,tclinp] # 0: add button number
        btnadd=wx.ToggleButton(self.panel,wx.ID_ANY,"Add",pos=(xloc+40,yloc-2),size=(30,20))
        btnadd.Bind(wx.EVT_TOGGLEBUTTON,self.OnAddDelButton)
        btnadd.SetValue(True)
        self.adddelbtnlst.append(btnadd)
        btndel=wx.ToggleButton(self.panel,wx.ID_ANY,"Del",pos=(xloc+80,yloc-2),size=(30,20))
        btndel.Bind(wx.EVT_TOGGLEBUTTON,self.OnAddDelButton)
        self.adddelbtnlst.append(btndel)
        
    def CreateColorButtonPanel(self,pos,size,label,itemnamlst,colordic):
        colpan=wx.ScrolledWindow(self.panel,-1,pos=pos,size=size) #style=wx.VSCROLL)
        colpan.SetScrollbars(1,1,1,30*20) #(2*len(self.elmnamlst)+1)*20)
        colpan.SetBackgroundColour('white')
        
        colpan.SetScrollRate(5,20)
        colorobjdic=self.CreateColorButtonsOnPanel(
                            colpan,label,itemnamlst,colordic)
        return colpan,colorobjdic

    def CreateColorButtonsOnPanel(self,panel,objlabel,varnamlst,colordic):
        """
        panel: self.atmpan,self.respan, self.chapan
        objlabel: 'element', 'residue','chain'
        varnamlst elmcolordic.keys()
        coloddic  elmcolordic
        evthandler self.OnButtonColor
        """
        yloc=8
        panel.Scroll(0,0)
        colorobjdic={}
        for varnam in varnamlst:
            svarnam=varnam
            if not isinstance(varnam,str): svarnam=str(varnam)
            text=wx.StaticText(panel,-1,str(varnam),pos=(15,yloc),size=(25,18))
            if self.itemcolordic.has_key(varnam):
                color=self.itemcolordic[varnam]
                text.SetForegroundColour(color)
            btncol=wx.Button(panel,-1,"",pos=(50,yloc-2),size=(20,15))
            color=colordic[varnam]
            ##color=255*numpy.array(color)
            btncol.SetBackgroundColour(color)
            btncol.Bind(wx.EVT_BUTTON,self.OnButtonColor)
            colorobjdic[varnam]=[btncol,text]
            yloc += 20
        return colorobjdic

    def DestroyColorButtonsOnPanel(self,colorobjdic):
        for item,objs in colorobjdic.iteritems():
            objs[0].Destroy(); objs[1].Destroy()
       
    def Initialize(self):
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        if self.curset == "":
            self.cmbfil.SetValue(self.curset)
            self.LoadDefault()
            mess='No parameter set file. Default param set is loaded.'
            self.parent.Message(mess)
        else: self.cmbfil.SetStringSelection(self.curset)
        #
        ##self.OnFile(1)
        #
        self.newfile=False
        self.rename=False
        self.saved=True
                     
    def ParamObjDefinition(self):
        paramobj={'mol-model':['ComboBox',self.cmbmdl,None,'model'],
                      'atom-sphere-radius':['TextCtrl',self.tclatmrad,None,'float'],
                      'bond-thick':['TextCtrl',self.tclbndthck,None,'int'],
                      'hydrogen-bond-color':['Button',self.btnhbcol,None,'color'],
                      'hydrogen-bond-thick':['TextCtrl',self.tclhbthick,None,'int'],
                      'aa-tube-color':['Button',self.btntubecol,None,'color'],
                      'aa-tube-radius':['TextCtrl',self.tcltuberad,None,'float'],
                      'element-color':['Method',self.parent.GetButtonColors,self.colorpanelobjdic['element'][1],'dic-color'],
                                       #self.elmcolorobjdic,'dic-color'],
                      'aa-residue-color':['Method',self.parent.GetButtonColors,self.colorpanelobjdic['residue'][1],'dic-color'],
                                          #self.rescolorobjdic,'dic-color'],
                      'aa-chain-color':['Method',self.parent.GetButtonColors,self.colorpanelobjdic['chain'][1],'dic-color']
                                        #self.chaincolorobjdic,'dic-color']
                       }
        return paramobj

    def GetParamsFromWidgets(self):
        self.newparamdic={}
        for prmnam, widget in self.paramwidgetdic.iteritems():
            if widget[0] == 'TextCtrl': self.newparamdic[prmnam]=widget[1].GetValue()
            elif widget[0] == 'ComboBox': self.newparamdic[prmnam]=widget[1].GetValue()
            elif widget[0] == 'Button': 
                wxcolor=widget[1].GetBackgroundColour() # wx.Colour object
                self.newparamdic[prmnam]=wxcolor.Get() # convert to RGB [0-255]
            elif widget[0] == 'Method': self.newparamdic[prmnam]=widget[1](widget[2])               
            else: print 'Error: widget in GetParamsFromWidget. param name=',prmnam   

    def SetParamsToWidgets(self,paramsdic):
        """ note: color intensitiy of r,g, and b, ranges from 0 to 255! """
        for prmnam, value in paramsdic.iteritems():
            
            if not self.paramwidgetdic.has_key(prmnam): continue
            
            widget=self.paramwidgetdic[prmnam]
            if widget[0] == 'TextCtrl':  widget[1].SetValue(str(value))
            elif widget[0] == 'ComboBox': widget[1].SetValue(str(value))
            elif widget[0] == 'Button': widget[1].SetBackgroundColour(value[:3]) # wx.Colour object
            elif widget[0] == 'Method':
                if prmnam == 'element-color':
                    colordic=paramsdic['element-color']
                    colorobjdic=self.colorpanelobjdic['element'][1]
                    self.parent.SetColorOnButtons(colorobjdic,colordic)
                elif prmnam == 'aa-residue-color':
                    colordic=paramsdic['aa-residue-color']
                    colorobjdic=self.colorpanelobjdic['residue'][1]
                    self.parent.SetColorOnButtons(colorobjdic,colordic)
                elif prmnam == 'aa-chain-color':
                    colordic=paramsdic['aa-chain-color']
                    colorobjdic=self.colorpanelobjdic['chain'][1]
                    self.parent.SetColorOnButtons(colorobjdic,colordic)               
            else: print 'Error: widget in SetParamsToWidget. param name=',parnam
                                            
    def CountModifiedParams(self):
        nmody=0
        for prmnam, value in self.currentparams.iteritems():
            if self.newparamdic.has_key(prmnam):
                if self.currentparams[prmnam] != self.newparamdic[prmnam]: nmody += 1
        return mnody
           
    def LoadDefaultElmColor(self):
        """ not used """
        colordic=ctrl.SettingCtrl.DefaultElementColor()
        for item,color in colordic.iteritems():
            color=numpy.array(color); color=255*color; color=color[:3]
            colordic[item]=color
        return colordic
    
    def LoadDefaultResColor(self):
        """ not used """
        colordic=ctrl.SettingCtrl.DefaultAAResidueColor()
        for item,color in colordic.iteritems():
            color=numpy.array(color); color=255*color; color=color[:3]
            colordic[item]=color
        return colordic
    
    def LoadDefaultChainColor(self):
        """ not used """
        colordic=ctrl.SettingCtrl.DefaultAAChainColor()()
        for item,color in colordic.iteritems():
            color=numpy.array(color); color=255*color; color=color[:3]
            colordic[item]=color
        return colordic
    
    def LoadDefault(self):
        self.parent.Message('')
        self.paramsdic=copy.deepcopy(self.defaultparamsdic)
        self.cmbfil.SetValue('')
        self.SetParamsToWidgets(self.paramsdic)

    def GetDefaultModelParams(self): 
        defaultdic={}    
        for prmnam,type in self.paramtypedic.iteritems():                
            defaultdic[prmnam]=self.setctrl.GetDefaultParam(prmnam)            
            if defaultdic[prmnam] == None: print 'Not found prmnam=',prmnam
        defaultdic=self.parent.ConvertParamsForCustomize(defaultdic,self.paramtypedic)
        return defaultdic
                 
    def OnAddDelButton(self,event):
        self.parent.Message('')
        obj=event.GetEventObject()
        btnnmb=self.adddelbtnlst.index(obj)
        modnmb=btnnmb % 2
        stat=obj.GetValue()
        notstat=not stat
        if modnmb == 0 and stat: self.adddelbtnlst[btnnmb+1].SetValue(notstat)
        if modnmb == 0 and notstat: self.adddelbtnlst[btnnmb+1].SetValue(stat)
        if modnmb == 1 and stat: self.adddelbtnlst[btnnmb-1].SetValue(notstat)
        if modnmb == 1 and notstat: self.adddelbtnlst[btnnmb-1].SetValue(stat)

    def OnInputItem(self,event):   
        self.parent.Message('')    
        itemnmbdic={0:0,2:1,4:2}; itemnamlst=['element','residue','chain']
        paramnamdic={'element':'element-color','residue':'aa-residue-color','chain':'aa-chain-colr'}
        #
        ID=event.GetId()
        self.parent.Message('')
        #
        input=self.inputtcldic[ID][1].GetValue()
        if input == '': return
        #        
        nmb=self.inputtcldic[ID][0] # nmb:0 'element', 2:'residue', 4: 'chain'
        itemnmb=itemnmbdic[nmb] # item number: 0 'element', 1:'residue', 2:'chain'
        item=itemnamlst[itemnmb]
        # scroll position
        [x,y]=self.colorpanelobjdic[item][0].GetViewStart()
        oldcolorobjdic=self.colorpanelobjdic[item][1]
        # upper case
        if item == 'element':
            input=input.upper(); input=input.rjust(2,' ')
        elif item == 'residue':
            input=input.upper(); input=input.ljust(3,' ')
        else:
            if not input.isdigit():
                self.parent.Message('Wrong input data. "'+input+'". Integers only')
                return
            else: input=int(input)
        # add/del
        addbtn=self.adddelbtnlst[nmb]
        add=addbtn.GetValue()
        # add or del input element in item
        namlst,colordic=self.AddDelParamItem(add,item,input)
        if len(namlst) <= 0: 
            self.inputtcldic[ID][1].SetValue('')
            return
        # destroy item color panel
        self.DestroyColorButtonsOnPanel(oldcolorobjdic)
        # re-create item color panel      
        pan=self.colorpanelobjdic[item][0]
        colorobjdic=self.CreateColorButtonsOnPanel(pan,item,namlst,colordic)
        self.colorpanelobjdic[item]=[pan,colorobjdic]
        # reset widgetdic
        prmnam=paramnamdic[item]
        self.paramwidgetdic[prmnam]=['Method',self.parent.GetButtonColors,colorobjdic]
        # set scrolled position   
        if add:
            idx=namlst.index(input)
            x=0; y=(idx-1)*20
        self.colorpanelobjdic[item][0].Scroll(x,y)
        # clear input text control
        self.inputtcldic[ID][1].SetValue('')
        self.saved=False
                                           
    def AddDelParamItem(self,add,item,input):
        # itemnmb: 0 'element', 1:'residue', 2: 'chain'
        # get scroll position
        [x,y]=self.colorpanelobjdic[item][0].GetViewStart()
        # check duplicate
        colorobjdic=self.colorpanelobjdic[item][1]
        if add and colorobjdic.has_key(input):
            self.parent.Message('item "'+input+'" already exists.')
            return [],{}
        if not add and not colorobjdic.has_key(input):
            self.parent.Message('item "'+input+'" does not exist.')
            return [],{}
        #       
        defcolor=[0,0,0] # black
        if item == 'element':
            if add: self.elmcolordic[input]=defcolor
            else:
                if input == 'XX' or input == '??':
                    self.parent.Message('Do not delete "'+input+'".')
                    return
                del self.elmcolordic[input]
            self.paramsdic['element-color']=self.elmcolordic
            #self.paramsdic=self.parent.ConvertParamsForCustomize(self.paramsdic,self.paramtypedic)
            self.elmnamlst=self.elmcolordic.keys()
            namlst=self.elmnamlst
            namlst.sort()
            colordic=self.elmcolordic
        elif item == 'residue':
            if add: self.rescolordic[input]=defcolor
            else: 
                if input == '???':
                    self.parent.Message('Do not delete "'+input+'".')
                    return
                del self.rescolordic[input]
            self.paramsdic['aa-residue-color']=self.rescolordic
            self.resnamlst=self.rescolordic.keys()
            namlst=self.resnamlst
            namlst.sort()
            colordic=self.rescolordic
        elif item == 'chain':
            if add: self.chaincolordic[input]=defcolor
            else: del self.chaincolordic[input]
            self.paramsdic['aa-chain-color']=self.chaincolordic
            self.chainnamlst=self.chaincolordic.keys()
            namlst=self.chainnamlst
            namlst.sort()
            colordic=self.chaincolordic
        self.itemcolordic[input]=[255,0,0]
        
        return namlst,colordic
        
    def OnButtonColor(self,event):
        self.saveas=False
        self.parent.Message('')
        obj=event.GetEventObject()
        color=lib.ChooseColorOnPalette(self.parent,True,-1)
        if color != None:
            obj.SetBackgroundColour(color)
            obj.Refresh()
              
    def OnFile(self,event):
        self.parent.Message('')
        self.saveas=False
        if not self.saved:
            mess='Current parameter set is not saved. Are you sure to move?.'
            dlg=lib.MessageBoxYesNo(mess,"")
            if not dlg: 
                self.cmbfil.SetValue(self.curset)
                return
        #           
        curset=self.cmbfil.GetValue()
        filename=curset
        if len(filename) <= 0: return
        filename=self.parent.MakeFullPathName(filename,'.model')
        ans=self.parent.IsFileExists(filename)
        if not ans: return
        # load params
        paramsdic=ctrl.SettingCtrl.ReadParamSetFile(filename,self.paramtypedic)
        # convert color 4 to 3 components
        paramsdic=self.parent.ConvertParamsForCustomize(paramsdic,self.paramtypedic)
        # update paramsdic
        self.paramsdic=copy.deepcopy(self.defaultparamsdic)
        self.paramsdic.update(paramsdic)
        # make color dic
        self.elmcolordic=self.paramsdic['element-color']
        self.elmnamlst=self.elmcolordic.keys()
        self.rescolordic=self.paramsdic['aa-residue-color']
        self.resnamlst=self.rescolordic.keys()
        self.chaincolordic=self.paramsdic['aa-chain-color']
        self.chainnamlst=self.chaincolordic.keys()
        # clear itemcolordic
        self.itemcolordic={}
        #try:
        for item in ['element','residue','chain']:
            self.DestroyColorButtonsOnPanel(self.colorpanelobjdic[item][1])
         # re-created item color panel      
        pan=self.colorpanelobjdic['element'][0]
        colorobjdic=self.CreateColorButtonsOnPanel(pan,'element',self.elmnamlst,self.elmcolordic)
        self.colorpanelobjdic['element']=[pan,colorobjdic]
        pan=self.colorpanelobjdic['residue'][0]
        colorobjdic=self.CreateColorButtonsOnPanel(pan,'residue',self.resnamlst,self.rescolordic)
        self.colorpanelobjdic['residue']=[pan,colorobjdic]
        pan=self.colorpanelobjdic['chain'][0]
        colorobjdic=self.CreateColorButtonsOnPanel(pan,'chain',self.chainnamlst,self.chaincolordic)
        self.colorpanelobjdic['chain']=[pan,colorobjdic]
        #except: pass
        # make type and widget object dictionary
        paramobj=self.ParamObjDefinition()
        self.paramwidgetdic=self.parent.MakeParamWidgetDic(paramobj)

        # set color on buttoms
        self.SetParamsToWidgets(self.paramsdic)
        # update parent curset
        self.curset=curset
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        
    def ResetCurrentSet(self,curset):
        self.curset=curset
        self.cmbfil.SetStringSelection(self.curset)
        self.OnFile(1)
        
    def OnNewFile(self,event):    
        self.parent.Message('')
        if not self.saveas and not self.rename: return
        setnam=self.cmbfil.GetValue() 
        if len(setnam) <= 0: 
            self.parent.Message('No file name ')
            return
        try: idx=self.filelst.index(setnam)
        except: idx=-1
        if idx >= 0:
            mess='the name is duplicate. please input a different name'
            lib.MessageBoxOK(mess,"")
            return
        if self.rename: 
            retcode=self.Rename(self.curset,setnam)
            self.cmbfil.SetValue(self.curset)      
        if self.saveas:
            self.SaveFile()
            #
            self.curset=setnam
            self.filelst.append(self.curset)
            self.cmbfil.SetItems(self.filelst)
            self.cmbfil.SetValue(self.curset)
    
            self.parent.Message('Created new parameter set '+'"'+setnam+'"')
            # update 'Model' current and filelst
            self.parent.SetCurrentParamSet(self.panelnam,self.curset)
            self.parent.paramsetfiledic[self.panelnam]=self.filelst
            self.saveas=False
        #
        self.saveas=False 
        self.rename=False
 
    def Rename(self,oldnam,newnam):       
        customdir=self.setctrl.GetDir('Customize')
        oldfile=os.path.join(customdir,oldnam+'.model')
        newfile=oldfile.replace(oldnam,newnam)
        if os.path.exists(newfile):
            mess='the file "'+newfile+' " already exists. try a diferent name.'
            self.parant.Message(mess)
            return False
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+oldnam+'" to "'+newnam+'"'
            return False
        idx=self.filelst.index(oldnam)       
        if idx >= 0: self.filelst[idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+oldnam+'" to "'+newnam+'"')
            return False          
        self.curset=newnam
        # set items to widget
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetValue(self.curset)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('Renamed '+'"'+oldnam+'" to "'+newnam+'"')            
        return True

    def OnViewFile(self,event):
        self.parent.Message('')
        self.parent.ViewSelectedFile(self.cmbfil,'.model') #,self.panelnam)

    def IsSaved(self):
        return self.saved

    def XXApply(self):
        pass
        
    def Cancel(self):
        self.saveas=False
        mess='Model parameter assignment was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True

    def DelFile(self):
        self.saveas=False
        self.parent.Message('')
        self.parent.DelSelectedFile(self.cmbfil,'.model')
        setnam=self.cmbfil.GetValue()
        self.filelst.remove(setnam)
        self.cmbfil.SetItems(self.filelst)
        if len(self.filelst) > 0: self.curset=self.filelst[0]
        else: self.curset=''
        self.cmbfil.SetStringSelection(self.curset)
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('param set file "'+setnam+'" was deleted') 

    def RenameFile(self):
        self.rename=True
        mess='Input name in "Model param set file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                                  
    def SaveFile(self):
        self.saveas=False
        self.parent.Message('')
        self.GetParamsFromWidgets()
        filename=self.cmbfil.GetValue()
        if len(filename) <= 0: 
            self.parent.Message('No file name in param set file window')
            return
        #
        filename=self.parent.MakeFullPathName(filename,'.model')
        print 'filename in save',filename 
        text='model parameters'    
        Customize_Frm.WriteParamSetFile(filename,text,self.paramtypedic,self.newparamdic)
        #
        self.parent.Message('Saved "'+filename+'".')
        self.saved=True

    def SaveFileAs(self):
        self.saveas=True
        mess='Input param set name in "Add-on menu file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                     
class CustomShortcut():
    """ Shortcut setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj model: instance of 'Model' class
    """
    def __init__(self,parent,pagepanel,model):
        
        self.classnam='SettingAddOn'
        self.panelnam='Shortcut'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model #parent.model #self.parent.model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #
        self.saved=True
        self.saveas=False
        self.rename=False
        
        self.selectedcolumn=-1
        self.menuitem=''
        self.menuitemlst=[]
        #
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        # reserved shortcutkey
        self.reservedkeydic=ctrl.SettingCtrl.ReservedShortcutKey()
        self.keyassigneddic={}
        #
        self.menutoplst,self.menulabeldic=self.menuctrl.MakeMenuLabelDic()
        self.menulabeldic['All']=['','']
        if len(self.menutoplst) > 0: self.menuitem=self.menutoplst[0]
        else: self.menuitem=''
        # create panel
        self.CreatePanel()
        # read shortcut key file
        self.OnFile(1)

    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        self.panel=self.pagepanel
        hcb=const.HCBOX
        yloc=10
        # create file button
        title='Shortcut definition file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(10,yloc),size=(140,18)) 
        sttip.SetToolTipString('Select shortcut definotion name(file,*.shortcut)')
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(150,yloc-2),size=(180,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnFile)
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetStringSelection(self.curset) #self.curparamsetdic['Shortcut'])
        btnview=wx.Button(self.panel,-1,"View",pos=(350,yloc-2),size=(40,20))
        btnview.SetToolTipString('View/Edit the file with editor')
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile) 
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL) 
        yloc += 10
        wx.StaticText(self.panel,-1,"Select top menu:",pos=(10,yloc),size=(110,18)) 
        self.cmbmenu=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(130,yloc-2),size=(120,hcb))
        self.cmbmenu.Bind(wx.EVT_COMBOBOX,self.OnMenuItem)
        self.cmbmenu.SetItems(self.menutoplst)
        self.cmbmenu.SetValue(self.menuitem)
        btncurset=wx.Button(self.panel,-1,"View all",pos=(270,yloc-2),size=(80,20))
        btncurset.SetToolTipString('View settings in all top menus')
        btncurset.Bind(wx.EVT_BUTTON,self.OnViewAll) 
        xsize=w-20 #self.sashposition
        ysize=h-100
        ###if lib.GetPlatform() == 'WINDOWS': hpanlst=h-195
        yloc=yloc+25; ybtn=150 # 25
        xpanlst=xsize-10 #550
        hpanlst=h-yloc-ybtn #170
        self.lstctrl=wx.ListCtrl(self.panel,-1,pos=(10,yloc),size=(xpanlst,hpanlst), #250),
                                 style=wx.LC_REPORT) #|wx.LC_EDIT_LABELS) # LC_SINGLE_SEL
        self.lstctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnSelected)
        self.lstctrl.SetToolTipString('Select a line and push keyboard key ("space" key cancels)')
        self.lstctrl.Bind(wx.EVT_LIST_KEY_DOWN,self.OnKeyDown)        
        self.lstctrl.InsertColumn(0,'#',width=40,format=wx.LIST_FORMAT_RIGHT)
        self.lstctrl.InsertColumn(1,'key',width=45,format=wx.LIST_FORMAT_CENTER)
        self.lstctrl.InsertColumn(2,'submenu label',width=200)
        self.lstctrl.InsertColumn(3,'tip or top menu label',width=200)
        # set string item
        yloc=300
        pos=[-1,yloc]
        self.butnpan=CommonActionButtons(self.parent,self.pagepanel,self,pos)          

    def Initialize(self):
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        if self.curset == "":
            self.cmbfil.SetValue(self.curset)
            self.LoadDefault()
            mess='No parameter set file. Default param set is loaded.'
            self.parent.Message(mess)          
        else: self.cmbfil.SetStringSelection(self.curset)
        #
        if self.curset == '': self.LoadDefault()
        else: self.OnFile(1)
        #
        self.saveas=False
        self.saved=True
   
    def SetStringData(self,menuitem):
        if menuitem == '': return
        # delete all items
        self.lstctrl.DeleteAllItems()
        #
        self.selectcolumn=-1; i=0; nkey=0
        indx=self.lstctrl.InsertStringItem(200,'')
        for i in range(len(self.menulabeldic[menuitem])):
            label=self.menulabeldic[menuitem][i][0]
            tip=self.menulabeldic[menuitem][i][1]
            keychar=''
            for key, lst in self.keyassigneddic.iteritems():
                if self.menuitem == 'All':
                    if lst[1] == label:
                        keychar=key; break 
                else:
                    if lst[0] == self.menuitem and lst[1] == label: 
                        keychar=key; break
            #if apply and key == '': continue
            indx=self.lstctrl.InsertStringItem(200,str(i+1))
            self.lstctrl.SetStringItem(indx,1,keychar)
            self.lstctrl.SetStringItem(indx,2,label)
            self.lstctrl.SetStringItem(indx,3,tip)
            if keychar != '': nkey += 1
            i += 1

    def OnSelected(self,event):
        self.saveas=False
        self.selectedcolumn=self.lstctrl.GetFirstSelected()
        self.parent.StatusMessage('')

    def OnKeyDown(self,event):
        self.saveas=False
        if self.selectedcolumn <= 0: return  
        keycode=event.GetKeyCode()
        if keycode == 32: keychar=''  # space key
        else: keychar=ctrl.MouseCtrl.UniCodeToChar(keycode) # the widget uses unicode(not ASCII)
        #print 'keycode,keychar',keycode,keychar         
        if keycode != 32 and self.keyassigneddic.has_key(keychar):
            mess='the key is already assigned to "'+self.keyassigneddic[keychar][0]
            mess=mess+':'+self.keyassigneddic[keychar][1]+'"'           
            self.parent.StatusMessage(mess)
            return
        item=self.lstctrl.GetItem(self.selectedcolumn,1)
        prvkeychar=item.GetText()
        #if prvkeychar == 'ctrl' or prvkeychar == 'shift' or prvkeychar == 'esc': # self.reservedkeydic.has_key(keychar):
        if len(prvkeychar) > 1:
            mess='you can not change this key! If you want to change the key, specify it in "setting script".'
            lib.MessageBoxOK(mess,"")
            return            
        if keychar == '' and self.keyassigneddic.has_key(prvkeychar):
            del self.keyassigneddic[prvkeychar]
        item=self.lstctrl.GetItem(self.selectedcolumn,2)
        submenu=item.GetText() #GetStringItem(self.selectedcolumn,1)
        item=self.lstctrl.GetItem(self.selectedcolumn,3)
        tiportopmenu=item.GetText() #self.lstctrl.GetStringItem(self.selectedcolumn,2)
        if keychar != '':
            if self.menuitem == 'All': self.keyassigneddic[keychar]=[tiportopmenu,submenu,''] 
            else: self.keyassigneddic[keychar]=[self.menuitem,submenu,tiportopmenu] 
        if self.menuitem == 'All': self.lstctrl.DeleteItem(self.selectedcolumn)
        else: self.lstctrl.SetStringItem(self.selectedcolumn,1,keychar) 
        self.saved=False

    def OnMenuItem(self,event):
        self.saveas=False
        self.menuitem=self.cmbmenu.GetValue()
        self.SetStringData(self.menuitem)

    def OnViewAll(self,event):
        self.saveas=False
        if self.menuitem == 'All': return
        self.menuitem='All'
        self.cmbmenu.SetValue(self.menuitem)  
        self.menulabeldic['All']=[]
        for key, lst in self.keyassigneddic.iteritems():
            self.menulabeldic['All'].append([lst[1],lst[0]])
        self.SetStringData(self.menuitem)
                   
    def OnFile(self,event):
        self.saveas=False
        curset=self.cmbfil.GetValue()
        filename=curset
        if len(filename) <= 0: return
        filename=self.parent.MakeFullPathName(filename,'.shortcut')
        ans=self.parent.IsFileExists(filename)
        if not ans: return
        
        self.curset=curset
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        
        self.keyassigneddic=ctrl.SettingCtrl.ReadShortcutKeyFile(filename)
        self.keyassigneddic.update(self.reservedkeydic)
        # set data on panel
        self.menuitem=''
        self.cmbmenu.SetValue('')
        self.OnViewAll(1)
        
    def ResetCurrentSet(self,curset):
        """ should be reset of apply (drawing in mdlwin)"""
        self.curset=curset
        self.cmbfil.SetStringSelection(self.curset)
        self.OnFile(1)
            
    def OnNewFile(self,event):
        self.parent.Message('')
        if not self.saveas and not self.rename: return
        setnam=self.cmbfil.GetValue()
        if len(setnam) <= 0: 
            self.parent.Message('No file name ')
            return
        try: idx=self.filelst.index(setnam)
        except: idx=-1
        if idx >= 0:
            mess='the name is duplicate. please input a different name'
            lib.MessageBoxOK(mess,"")
            return
        #
        if self.rename: 
            retcode=self.Rename(self.curset,setnam)
            self.cmbfil.SetValue(self.curset)      
        if self.saveas:
            self.SaveFile()
            #
            self.curset=setnam
            self.filelst.append(self.curset)
            self.cmbfil.SetItems(self.filelst)
            self.cmbfil.SetStringSelection(self.curset)
    
            self.parent.Message('Created newshortcut define file '+'"'+setnam+'"')
            #
            self.parent.SetCurrentParamSet(self.panelnam,self.curset)
            self.parent.paramsetfiledic[self.panelnam]=self.filelst
            self.saveas=False
        #
        self.saveas=False 
        self.rename=False
               
    def OnViewFile(self,event):
        self.saveas=False
        self.parent.ViewSelectedFile(self.cmbfil,'.shortcut')
        
    def IsSaved(self):
        return self.saved

    def Apply(self):
        pass
    
    def LoadDefault(self):
        self.saveas=False
        self.keyassigneddic=ctrl.SettingCtrl.CustomShortcutKey()
        self.keyassigneddic.update(self.reservedkeydic)
        self.cmbfil.SetValue('')
        self.menuitem=''
        self.OnViewAll(1)
               
    def DelFile(self):
        self.saveas=False
        self.parent.DelSelectedFile(self.cmbfil,'.shortcut')  
        setnam=self.cmbfil.GetValue()
        self.filelst.remove(setnam)
        self.cmbfil.SetItems(self.filelst)
        if len(self.fileslst) > 0: self.curset=self.filelst[0]
        else: self.curset=''
        self.cmbfil.SetStringSelection(self.curset)
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('parameter set '+'"'+setnam+'" was deleted') 
        
    def MakeKeyList(self):
        keylst=[]
        for key,lst in self.keyassigneddic.iteritems():
            keylst.append(key.ljust(10)+' '+lst[0]+':'+lst[1])
        keylst.sort()
        print 'keylst',keylst
        return keylst

    def Rename(self,oldnam,newnam):       
        customdir=self.setctrl.GetDir('Customize')
        oldfile=os.path.join(customdir,oldnam+'.shortcut')
        newfile=oldfile.replace(oldnam,newnam)
        if os.path.exists(newfile):
            mess='the file "'+newfile+' " already exists. try a diferent name.'
            self.parant.Message(mess)
            return False
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+oldnam+'" to "'+newnam+'"'
            return False
        idx=self.filelst.index(oldnam)       
        if idx >= 0: self.filelst[idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+oldnam+'" to "'+newnam+'"')
            return False          
        self.curset=newnam
        # set items to widget
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetValue(self.curset)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('Renamed '+'"'+oldnam+'" to "'+newnam+'"')            
        return True
                         
    def RenameFile(self):
        self.rename=True
        mess='Input name in "Shortcut define file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                                  
    def SaveFile(self):
        self.saveas=False
        filename=self.cmbfil.GetValue()
        if len(filename) <= 0: return
        if not self.saved:
            mess='"Apply" was applied.'
            self.parent.StatusMessage(mess)
            self.saved=True
        #nkey=self.UpdateStringData()
        keylst=self.MakeKeyList()
        filename=self.parent.MakeFullPathName(filename,'.shortcut')
        print 'filename',filename 

        self.WriteShortcutKeyFile(filename,keylst)
        
        print 'compressfilename',lib.CompressUserFileName(filename)
        self.parent.Message('Saved "'+filename+'".')
        
    def SaveFileAs(self):
        self.saveas=True
        mess='Input param set name in "Add-on menu file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
             
    def SaveFileAsOldCode(self):
        curdir=os.getcwd()
        os.chdir(self.parent.customdir)
        filename=lib.GetFileName(self.parent,'*.shortcut','w',True,'')
        os.chdir(curdir)
        if len(filename) <= 0: return
        ns=filename.find('.shortcut')
        if ns < 0: filename=filename+'.shortcut'
        keylst=self.MakeKeyList()
        self.WriteShortcutKeyFile(filename,keylst)      
         
    def WriteShortcutKeyFile(self,filename,keylst):
        f=open(filename,"w")
        f.write('# fu shortcut-key assignment '+lib.CreatedByText()+'\n') #created at '+lib.DateTimeText()+'\n')
        f.write('# key character and menu label(top label:sub label:subsub label)\n')
        f.write("'shortcut-key'\n")
        for label in keylst: f.write(label+':False\n')           
        f.close()

    def Cancel(self):
        mess='shortcut key assignment was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True
                                               
class CustomAddOns():
    """Addon setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj model: instance of 'Model' class
    """
    def __init__(self,parent,pagepanel,model):
        self.classnam='SettingAddOn'
        self.panelnam='Add-on'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model #parent.model #self.parent.model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #
        self.saved=True
        self.saveas=False
        self.rename=False
        #
        self.addonlst=['add-on1-menu'] #['add-on1','add-on2']
        self.addonnmb=0
        self.filelst=[]
        self.curset=''
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        scriptdir=self.setctrl.GetDir('Scripts')
        scriptfilelst=lib.GetFilesInDirectory(scriptdir,['.py'])
        self.scriptnamlst,self.scriptdic=self.MakeScriptNameDic(scriptfilelst)
        #
        self.scriptchkboxdic={}
        self.menuchkboxdic={}
        self.menulabel=''
        self.submenulabel=''
        self.menuitemlst=[]
        self.checkedname=''

        self.addon1menu=[]
        self.addon1chkboxdic={}
        self.addon2menu=[]
        self.addon2chkboxdic={}
        # create panel
        self.CreatePanel()
        # set data on panel
        self.OnFile(1)     
          
    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        self.panel=self.pagepanel #wx.Panel(self.pagepanel,wx.ID_ANY,pos=[-1,-1],size=size)
        hcb=const.HCBOX
        yloc=10
        # load file button
        title='Add-on menu file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(10,yloc),size=(110,18)) 
        sttip.SetToolTipString('Select add-on menu definition name(file,*.add-on)')
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(130,yloc-2),size=(180,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnFile)
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        self.cmbfil.SetItems(self.filelst) #paramsetfiledic['Add-on'])
        self.cmbfil.SetStringSelection(self.curset) #self.curparamsetdic['Add-on'])
        btnview=wx.Button(self.panel,-1,"View",pos=(330,yloc-2),size=(40,20))
        btnview.SetToolTipString('View or edit the file with editor')
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile) 
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL)  
        yloc += 10
        # top/sub menu
        wx.StaticText(self.panel,-1,"Menu:",pos=(10,yloc),size=(35,18))    
        self.rbttop=wx.RadioButton(self.panel,-1,"top",pos=(50,yloc-2),size=(40,18),
                                   style=wx.RB_GROUP)
        self.rbtsub=wx.RadioButton(self.panel,-1,"sub",pos=(95,yloc-2),size=(50,18))
        self.rbtsub.Bind(wx.EVT_RADIOBUTTON,self.OnMenuLevel)
        self.rbttop.SetValue(True)
        # maenu labels
        stlbl=wx.StaticText(self.panel,-1,"Label(top,sub):",pos=(150,yloc),size=(90,18))
        #stlbl.SetToolTipString('Enter the top menu label for the add-on')     
        self.tclmenu=wx.TextCtrl(self.panel,-1,'',pos=(245,yloc-2),size=(70,20))
        self.tclmenu.SetValue(self.menulabel)
        self.tclsub=wx.TextCtrl(self.panel,-1,'',pos=(325,yloc-2),size=(70,20))
        self.tclsub.SetValue(self.submenulabel)
        yloc += 25; yloc0=yloc
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL)  
        width=w/2-25
        #wx.StaticLine(self.panel,pos=(width+15,yloc),size=(4,h-yloc),style=wx.LI_VERTICAL)  
        yloc += 10
        stscr=wx.StaticText(self.panel,-1,"Scripts",pos=(80,yloc),size=(80,18))
        stscr.SetToolTipString('All script files(*.py) in "Customize" directory')   
        stmenu=wx.StaticText(self.panel,-1,"Add-on Menu items",pos=(250,yloc),size=(150,18))
        stmenu.SetToolTipString('Selected scripts for the menu')   
        yloc += 20; height=165 #h-yloc-190
        #scriptpan=scrolled.ScrolledPanel(self.panel,-1,pos=[10,yloc],size=[w/2-15,hight],
        #                               style = wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER)
        #width=w/2-25
        # script list panel
        self.scriptpan=wx.ScrolledWindow(self.panel,-1,pos=[10,yloc],size=[width,height]) #,
                                       #style=wx.HSCROLL|wx.VSCROLL)
        self.scriptpan.SetScrollbars(1,1,2*width,(len(self.scriptnamlst)+1)*20)
        self.scriptpan.SetBackgroundColour('white')
        self.SetScriptItems()
        self.scriptpan.SetScrollRate(5,20)
        # menu item panel
        height1=height #-30
        self.menupan=wx.ScrolledWindow(self.panel,-1,pos=[width+35,yloc],size=[width,height1]) #,
                                       #style=wx.HSCROLL|wx.VSCROLL)
        self.menupan.SetScrollbars(1,1,2*width,(len(self.scriptnamlst)+1)*20)
        self.menupan.SetScrollRate(5,20)
        self.menupan.SetBackgroundColour('white')
        self.SetMenuItems()
        # script panel
        yloc += height+10
        self.btnchk=wx.ToggleButton(self.panel,wx.ID_ANY,"CheckAll",pos=(20,yloc-2),size=(60,20))
        self.btnchk.Bind(wx.EVT_TOGGLEBUTTON,self.OnCheckAll)
        self.btnchk.SetToolTipString('Check/Uncheck all items')
        btnadd=wx.Button(self.panel,wx.ID_ANY,"Add to menu",pos=(90,yloc-2),size=(80,20))
        btnadd.Bind(wx.EVT_BUTTON,self.OnAddToMenu)
        btnadd.SetToolTipString('Add cheked scripts to menu items')
        # menu panel
        #yloc -= 30
        xloc=w/2+20
        self.btnclear=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(xloc,yloc-2),size=(40,20)) # 215
        self.btnclear.Bind(wx.EVT_BUTTON,self.OnClearMenu)
        self.btnclear.SetToolTipString('Delete all items')
        btndel=wx.Button(self.panel,wx.ID_ANY,"Del",pos=(xloc+50,yloc-2),size=(30,20))
        btndel.Bind(wx.EVT_BUTTON,self.OnDelMenu)
        btndel.SetToolTipString('Remove checked items')
        btnup=wx.Button(self.panel,wx.ID_ANY,"Up",pos=(xloc+100,yloc-2),size=(30,20))
        btnup.Bind(wx.EVT_BUTTON,self.OnUp)
        btnup.SetToolTipString('Move upward')
        btndwn=wx.Button(self.panel,wx.ID_ANY,"Down",pos=(xloc+140,yloc-2),size=(40,20))
        btndwn.Bind(wx.EVT_BUTTON,self.OnDown)
        btndwn.SetToolTipString('Move downward')
        yloc += 25
        wx.StaticLine(self.panel,pos=(width+20,yloc0),size=(4,yloc-yloc0+5),style=wx.LI_VERTICAL)
        # put buttons
        pos=[-1,yloc]
        self.butnpan=CommonActionButtons(self.parent,self.pagepanel,self,pos)
        self.butnpan.btndefa.Disable()
        
    def Initialize(self):
        #prmset='Add-on'
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        if self.curset == "":
            self.cmbfil.SetValue(self.curset)
            self.LoadDefault()
            mess='No parameter set file. Default param set is loaded.'
            self.parent.Message(mess)
        else: self.cmbfil.SetStringSelection(self.curset)
        #
        if self.curset == '': self.LoadDefault()
        else: self.OnFile(1)
        #       
        self.saveas=False
        self.saved=True
   
    def SetScriptItems(self):
        #self.panel=panel
        #size=panel.GetSize(); w=size[0]; h=size[1]
        self.ClearScriptPanel()
        yloc=8
        for name in self.scriptnamlst:
            chkbox=wx.CheckBox(self.scriptpan,-1,name,pos=[10,yloc])
            self.scriptchkboxdic[name]=chkbox
            yloc += 20

    def ClearScriptPanel(self):
        for scrnam,widget in self.scriptchkboxdic.iteritems(): widget.Destroy()
        self.scriptchkboxdic={}

    def ClearMenuPanel(self):
        for scrnam,widget in self.menuchkboxdic.iteritems(): widget.Destroy()
        self.menuchkboxdic={}

    def SetMenuItems(self):
        self.ClearMenuPanel()
        yloc=8
        for i in range(len(self.menuitemlst)):
            name=self.menuitemlst[i]
            chkbox=wx.CheckBox(self.menupan,-1,name,pos=[10,yloc])
            self.menuchkboxdic[name]=chkbox
            #chkbox.SetValue(self.menuchecklst[i])
            if name == self.checkedname: chkbox.SetValue(True) 
            yloc += 20

    def OnMenuLevel(self,event):
        mess='Sorry, submenu definition is not supported yet in this panel. You can create a menu with submenus '
        mess=mess+'by defining it in setting script file.'
        lib.MessageBoxOK(mess,"")           
        self.rbttop.SetValue(True)
    
    def OnCheckAll(self,event):
        self.saveas=False
        value=False
        if self.btnchk.GetValue(): value=True #Check all, else uncheck all
        for scrnam,widget in self.scriptchkboxdic.iteritems(): widget.SetValue(value)
        
    def OnAddToMenu(self,event):
        self.saveas=False
        self.menuitemlst=[]; self.menuchecklst=[]
        for scrnam, chkbox in self.scriptchkboxdic.iteritems(): #[name]=[chkbox]
            if chkbox.GetValue():
               self.menuitemlst.append(scrnam)
               self.menuchecklst.append(False)
        print 'menuitemlst',self.menuitemlst
        self.SetMenuItems()

    def OnClearMenu(self,event):
        self.saveas=False
        self.menuitemlst=[]
        self.menuchecklst=[]
        self.SetMenuItems()
        return
        value=False
        if self.btnmenuchk.GetValue(): value=True #Check all, else uncheck all
        for scrnam,widget in self.menuchkboxdic.iteritems(): widget.SetValue(value)
        
    def OnDelMenu(self,event):
        """ Delete checked menu items
        """
        self.saveas=False
        dellst=[]
        for scrnam,widget in self.menuchkboxdic.iteritems(): 
            if widget.GetValue(): dellst.append([scrnam,widget])
        for scrnam,widget in dellst: 
            self.menuitemlst.remove(scrnam)
            self.menuchecklst.remove(scrnam)
        self.SetMenuItems()

    def FindCheckedIndexOfMenuNamList(self):
        self.checkedname=''
        for scrnam,widget in self.menuchkboxdic.iteritems(): 
            if widget.GetValue():
                self.checkedname=scrnam; break
        if self.checkedname != '':
            try: idx=self.menuitemlst.index(self.checkedname)
            except: idx=-1
        return idx        

    def CheckModified(self):
        pass
        
    def OnUp(self,event):
        self.saveas=False
        idx=self.FindCheckedIndexOfMenuNamList()
        if idx <= 0: return       
        self.menuitemlst[idx-1],self.menuitemlst[idx]=self.menuitemlst[idx],self.menuitemlst[idx-1]
        self.SetMenuItems()
        
    def OnDown(self,event):
        self.saveas=False
        idx=self.FindCheckedIndexOfMenuNamList()
        if idx < 0 or idx >= len(self.menuitemlst)-1: return
        self.menuitemlst[idx+1],self.menuitemlst[idx]=self.menuitemlst[idx],self.menuitemlst[idx+1]
        self.SetMenuItems()
        
    def MakeScriptNameDic(self,scriptfilelst):
        namelst=[]; namedic={}
        for script in scriptfilelst:
            head,tail=os.path.split(script); root,ext=os.path.splitext(tail)
            namedic[root]=script; namelst.append(root)
        return namelst,namedic
                
    def OnSelectAddOn(self,event):
        self.saveas=False
        self.addon=self.cmbaddon.GetValue()
        self.addonnmb=self.addonlst.index(self.addon)
        self.tclmenu.SetValue(self.addonlst[self.addonnmb])

    def OnFile(self,event):
        self.saveas=False
        curset=self.cmbfil.GetValue()
        filename=curset
        if len(filename) <= 0: return
        filename=self.parent.MakeFullPathName(filename,'.add-on')
        ans=self.parent.IsFileExists(filename)
        if not ans: return
        self.curset=curset
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.addon,self.menulabel,self.menulst=ctrl.SettingCtrl.ReadAddonMenuFile(filename)
        self.menuchecklst=[] #len(self.menulst)*[False]
        self.menuitemlst=[] #len(self.menulst)*['']
        for i in range(len(self.menulst)):
            self.menuitemlst.append(self.menulst[i][0])
            self.menuchecklst.append(self.menulst[i][2])
        self.SetMenuItems()
        self.CheckSelected()

        self.tclmenu.SetValue(self.menulabel)
        # not completeed # self.tclsub.SetValue(self.submenulabel)

    def CheckSelected(self):
        for scrnam,widget in self.scriptchkboxdic.iteritems():
            try: 
                idx=self.menuitemlst.index(scrnam)
                if idx >= 0: widget.SetValue(True)
            except: pass

    def LoadDefault(self):
        pass

    def ResetCurrentSet(self,curset):
        self.curset=curset
        self.cmbfil.SetStringSelection(self.curset)
        self.OnFile(1)
                    
    def OnViewFile(self,event):
        self.saveas=False
        self.parent.ViewSelectedFile(self.cmbfil,'.add-on')
        
    def IsSaved(self):
        return self.saved

    def Apply(self):
        pass
        
    def Clear(self):
        self.saved=False

    def DelFile(self):
        self.saveas=False
        self.parent.DelSelectedFile(self.cmbfil,'.add-on')
        setnam=self.cmbfil.GetValue()
        self.filelst.remove(setnam)
        self.cmbfil.SetItems(self.filelst)
        if len(self.filelst) > 0: self.curset=self.filelst[0]
        else: self.curset=''
        self.cmbfil.SetStringSelection(self.curset)
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('param set file "'+setnam+'" was deleted')
          
    def RenameFile(self):
        self.rename=True
        mess='Input name in "Add-on mneu file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                                  
    def Rename(self,oldnam,newnam):       
        customdir=self.setctrl.GetDir('Customize')
        oldfile=os.path.join(customdir,oldnam+'.add-on')
        newfile=oldfile.replace(oldnam,newnam)
        if os.path.exists(newfile):
            mess='the file "'+newfile+' " already exists. try a diferent name.'
            self.parant.Message(mess)
            return False
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+oldnam+'" to "'+newnam+'"'
            return False
        idx=self.filelst.index(oldnam)       
        if idx >= 0: self.filelst[idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+oldnam+'" to "'+newnam+'"')
            return False          
        self.curset=newnam
        # set items to widget
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetValue(self.curset)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('Renamed '+'"'+oldnam+'" to "'+newnam+'"')            
        return True

    def SaveFile(self):
        self.saveas=False
        #addon=self.cmbaddon.GetValue()  
        addon='add-on'      
        menulabel=self.GetMenuLabel()
        if len(menulabel) <= 0: return
        self.menulabel=menulabel
        filename=self.cmbfil.GetValue()
        if len(filename) <= 0: return
        # filename
        filename=self.parent.MakeFullPathName(filename,'.'+addon)
        print 'filename',filename 
        self.WriteAddonMenuFile(filename,addon,self.menulabel,self.menuitemlst,self.menuchecklst)
        #
        self.parent.Message('Saved "'+filename+'".')
        self.saved=True

    def GetMenuLabel(self):
        menulabel=''
        menulabel=self.tclmenu.GetValue()
        if len(menulabel) <= 0:
            mess='Input menu label in the "Menu label" window'
            lib.MessageBoxOK(mess,"")
            return ''   
        return menulabel
    
    def SaveFileAs(self):
        self.saveas=True
        mess='Input param set name in "Add-on menu file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')

    def OnNewFile(self,event):
        self.parent.Message('')
        if not self.saveas and not self.rename: 
            self.parent.Message('No file name ')
            return
        setnam=self.cmbfil.GetValue()
        if len(setnam) <= 0: return
        try: idx=self.filelst.index(setnam)
        except: idx=-1
        if idx >= 0:
            mess='the name is duplicate. please input a different name'
            lib.MessageBoxOK(mess,"")
            return
        #
        if self.rename: 
            retcode=self.Rename(self.curset,setnam)
            self.cmbfil.SetValue(self.curset)      
        if self.saveas:
            self.SaveFile()
            #
            self.curset=setnam
            self.filelst.append(self.curset)
            self.cmbfil.SetItems(self.filelst)
            self.cmbfil.SetStringSelection(self.curset)
    
            self.parent.Message('Created new parameter set '+'"'+setnam+'"')
            #
            self.parent.SetCurrentParamSet(self.panelnam,self.curset)
            self.parent.paramsetfiledic[self.panelnam]=self.filelst
            self.saveas=False
        #
        self.saveas=False 
        self.rename=False

    def WriteAddonMenuFile(self,filename,addon,menulabel,menuitemlst,checklst):
        f=open(filename,"w")
        f.write('# fu add-on menu items '+lib.CreatedByText()+'\n') 
        f.write("'"+addon+"'\n")
        f.write("menulabel="+menulabel+"\n")
        for i in range(len(menuitemlst)):
            item=menuitemlst[i]
            check='False'
            #?? if checklst[i]: check='True'           
            f.write(item+' tip '+check+'\n')           
        f.close()

    def Cancel(self):
        mess='Add-on menu assignment was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True
                
class CustomGeneral():
    """ General setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj model: instance of 'Model' class
    """
    def __init__(self,parent,pagepanel,model):
        self.classnam='SettingGeneral'
        self.panelnam='General'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model #parent.model #self.parent.model
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #
        self.saved=True
        self.saveas=False
        self.modified=False
        self.rename=False
        #
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        self.defaultparams={}
        self.paramsdic={}
        self.newparamdic={}
        #create panel  
        self.CreatePanel()
        # make type and widget object dictionary
        paramobj=self.ParamObjDefinition()
        self.paramtypedic=self.parent.MakeParamTypeDic(paramobj)
        self.paramwidgetdic=self.parent.MakeParamWidgetDic(paramobj)
    
    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        #self.panel=wx.Panel(self.pagepanel,wx.ID_ANY,pos=[-1,-1],size=size)
        self.panel=self.pagepanel
        hcb=const.HCBOX
        yloc=10
        # create file button
        title='General param set file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(10,yloc),size=(140,18)) 
        sttip.SetToolTipString('Select general parameter set name(file,*.general)')
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(150,yloc-2),size=(180,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnFile)
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetStringSelection(self.curset) #curparamsetdic[self.panelnam])
        btnview=wx.Button(self.panel,-1,"View",pos=(350,yloc-2),size=(40,20))
        btnview.SetToolTipString('View or edit the file with editor')
        btnview.Bind(wx.EVT_BUTTON,self.OnViewFile) 
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,4),style=wx.LI_HORIZONTAL)  
        yloc += 10
        wx.StaticText(self.panel,-1,"Windows",pos=(10,yloc),size=(120,18))         
        yloc += 20 # win-size
        wx.StaticText(self.panel,-1,"Main window size (W and H in pixcels): ",pos=(20,yloc),size=(230,18))      
        self.tclsizew=wx.TextCtrl(self.panel,-1,'',pos=(260,yloc-2),size=(40,18))
        self.tclsizeh=wx.TextCtrl(self.panel,-1,'',pos=(310,yloc-2),size=(40,18))
        yloc += 25 # win-color
        wx.StaticText(self.panel,-1,"Main window color: ",pos=(20,yloc),size=(115,18))          
        self.btnwincol=wx.Button(self.panel,wx.ID_ANY,"",pos=(140,yloc-2),size=(20,15))
        self.btnwincol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnWindowColor(obj=self.btnwincol))
        wx.StaticText(self.panel,-1,"In geometry edit mode: ",pos=(180,yloc),size=(145,18))          
        self.btngeocol=wx.Button(self.panel,wx.ID_ANY,"",pos=(330,yloc-2),size=(20,15))
        self.btngeocol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnWindowColorGeomMode)
        yloc += 25 # shell-win-size
        wx.StaticText(self.panel,-1,"Shell window size (W and H in pixcels): ",pos=(20,yloc),size=(230,18))      
        self.tclshlsizew=wx.TextCtrl(self.panel,-1,'',pos=(260,yloc-2),size=(40,18))
        self.tclshlsizeh=wx.TextCtrl(self.panel,-1,'',pos=(310,yloc-2),size=(40,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"MouseMode/MolChaice window shape: ",pos=(20,yloc),size=(220,18))
        self.rbthmus=wx.RadioButton(self.panel,-1,"horizontal",pos=(245,yloc-2),size=(80,18),
                                   style=wx.RB_GROUP)
        self.rbtvmus=wx.RadioButton(self.panel,-1,"vertical",pos=(330,yloc-2),size=(70,18))
        yloc += 25 #
        wx.StaticText(self.panel,-1,"Colors",pos=(10,yloc),size=(120,18))         
        yloc += 20 # select color
        wx.StaticText(self.panel,-1,"selected: ",pos=(20,yloc),size=(50,18))          
        self.btnselcol=wx.Button(self.panel,wx.ID_ANY,"",pos=(80,yloc-2),size=(20,15))
        self.btnselcol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnSelectColor)
        #yloc += 25 # sel-sphere color
        wx.StaticText(self.panel,-1,"sphere/box selected region: ",pos=(115,yloc),size=(165,18))          
        self.btnsphcol=wx.Button(self.panel,wx.ID_ANY,"",pos=(285,yloc-2),size=(20,15))
        self.btnsphcol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnSelSphereColor)
        stlabel=wx.StaticText(self.panel,-1,"label: ",pos=(325,yloc),size=(40,18))          
        stlabel.SetToolTipString('Element/atom/residure name/number color')
        self.btnlblcol=wx.Button(self.panel,wx.ID_ANY,"",pos=(365,yloc-2),size=(20,15))
        self.btnlblcol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnLabelColor)
        yloc += 25 # draw-message-color
        stmess=wx.StaticText(self.panel,-1,"mode message: ",pos=(20,yloc),size=(95,18))          
        stmess.SetToolTipString('Message color for mouse mode')
        self.btnmescol=wx.Button(self.panel,wx.ID_ANY,"",pos=(115,yloc-2),size=(20,15))
        self.btnmescol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnMessageColor)
        #yloc += 25 # rot-axis-arrow-color
        wx.StaticText(self.panel,-1,"rot-axis arrow: ",pos=(150,yloc),size=(90,18))          
        self.btnaxicol=wx.Button(self.panel,wx.ID_ANY,"",pos=(245,yloc-2),size=(20,15))
        self.btnaxicol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnRotAxisArrowColor)
        wx.StaticText(self.panel,-1,"vib-vec arrow: ",pos=(280,yloc),size=(90,18))          
        self.btnvibcol=wx.Button(self.panel,wx.ID_ANY,"",pos=(365,yloc-2),size=(20,15))
        self.btnvibcol.Bind(wx.EVT_BUTTON,self.OnButtonColor) #self.OnVibArrowColor)
        yloc += 25 #line thickness
        wx.StaticText(self.panel,-1,"Line thickness",pos=(10,yloc),size=(80,18))         
        #yloc += 20 
        wx.StaticText(self.panel,-1,"rot-axis arrow: ",pos=(110,yloc),size=(90,18))          
        self.tclrotaxi=wx.TextCtrl(self.panel,-1,'',pos=(205,yloc-2),size=(20,18))  
        wx.StaticText(self.panel,-1,"xyz-axis: ",pos=(250,yloc),size=(55,18))          
        self.tclxyzaxi=wx.TextCtrl(self.panel,-1,'',pos=(310,yloc-2),size=(20,18))  
        yloc += 25 # FMO menu
        wx.StaticText(self.panel,-1,"Misc",pos=(10,yloc),size=(40,18))     
        wx.StaticText(self.panel,-1,"FMO menu enable:",pos=(60,yloc),size=(105,18))          
        self.chkfmo=wx.CheckBox(self.panel,-1,"",pos=(170,yloc-2),size=(20,20))
        # stereo eye
        wx.StaticText(self.panel,-1,"Stereo eye:",pos=(205,yloc),size=(65,18))    
        self.rbtpara=wx.RadioButton(self.panel,-1,"parallel",pos=(275,yloc-2),size=(65,18),
                                   style=wx.RB_GROUP)
        self.rbtcross=wx.RadioButton(self.panel,-1,"cross",pos=(340,yloc-2),size=(65,18))
        yloc += 20
         #'max-undo'
        stundo=wx.StaticText(self.panel,-1,"Max undo:",pos=(20,yloc),size=(60,18)) 
        stundo.SetToolTipString("Max. number of undo for molecular structure change")          
        #self.chkundo=wx.CheckBox(self.panel,-1,"",pos=(80,yloc-2),size=(20,20))
        self.tclundo=wx.TextCtrl(self.panel,-1,"3",pos=(80,yloc-2),size=(20,18))
        # 'auto-add-hydrogens'
        stauto=wx.StaticText(self.panel,-1,"Auto add hydrogens:",pos=(120,yloc),size=(120,18)) 
        stauto.SetToolTipString("Add hydrogens to polypeptide when PDB data is read") 
        self.chkauto=wx.CheckBox(self.panel,-1,"",pos=(240,yloc-2),size=(20,20))
        #'dump-draw-items'
        stdump=wx.StaticText(self.panel,-1,"Dump draw items:",pos=(270,yloc),size=(110,18)) 
        stdump.SetToolTipString("Dump draw items at close") 
        self.chkdump=wx.CheckBox(self.panel,-1,"",pos=(375,yloc-2),size=(20,20))
        yloc += 20
        # put buttons
        pos=[-1,yloc]
        self.butnpan=CommonActionButtons(self.parent,self.pagepanel,self,pos)

    def Initialize(self):
        #prmset='General'
        self.filelst=self.parent.paramsetfiledic[self.panelnam]
        self.curset=self.parent.curparamsetdic[self.panelnam]
        if self.curset == "":
            self.cmbfil.SetValue(self.curset)
            self.LoadDefault()
            mess='No parameter set file. Default param set is loaded.'
            self.parent.Message(mess)
        else: self.cmbfil.SetStringSelection(self.curset)
        #
        if self.curset == '': self.LoadDefault()
        else: self.OnFile(1)
        #
        self.saveas=False
        self.saved=True
  
    def ParamObjDefinition(self):
        paramobj={'win-size-w':['TextCtrl',self.tclsizew,None,'int'],
                      'win-size-h':['TextCtrl',self.tclsizeh,None,'int'],
                      'win-color':['Button',self.btnwincol,None,'color'],
                      'win-color-geom-mode':['Button',self.btngeocol,None,'color'],
                      'shell-win-size-w':['TextCtrl',self.tclshlsizew,None,'int'],
                      'shell-win-size-h':['TextCtrl',self.tclshlsizeh,None,'int'],
                      'mousemode-win-shape':['RadioButton',self.rbthmus,None,'bool'],
                      'select-color':['Button',self.btnselcol,None,'color'],
                      'sel-sphere-color':['Button',self.btnsphcol,None,'color'],
                      'label-color':['Button',self.btnlblcol,None,'color'],
                      'mode-message-color':['Button',self.btnmescol,None,'color'],
                      'rot-axis-arrow-color':['Button',self.btnaxicol,None,'color'],
                      'vib-vec-arrow-color':['Button',self.btnvibcol,None,'color'],
                      'rot-axis-arrow-thick':['TextCtrl',self.tclrotaxi,None,'int'],
                      'xyz-axis-thick':['TextCtrl',self.tclxyzaxi,None,'int'],
                      'fmo-menu':['CheckBox',self.chkfmo,None,'bool'],
                      'stere-eye':['RadioButton',self.rbtpara,None,'bool'],
                      'max-undo':['TextCtrl',self.tclundo,None,'int'],
                      'auto-add-hydrogens':['CheckBox',self.chkauto,None,'bool'],
                      'dump-draw-items':['CheckBox',self.chkdump,None,'bool'] }                
        return paramobj

    def OnBrowseProject(self,event):
        self.prjnam=self.cmbprj.GetValue()

    def OnButtonColor(self,event):
        self.saveas=False
        obj=event.GetEventObject()
        color=lib.ChooseColorOnPalette(self.parent,True,-1)
        if color != None:
            obj.SetBackgroundColour(color)
            obj.Refresh()
              
    def OnFile(self,event):
        self.saveas=False
        curset=self.cmbfil.GetValue()
        filename=curset
        if len(filename) <= 0: return
        filename=self.parent.MakeFullPathName(filename,'.general')
        ans=self.parent.IsFileExists(filename)
        if not ans: return
        # load params
        self.paramsdic=ctrl.SettingCtrl.ReadParamSetFile(filename,self.paramtypedic)
        # convert color 4 to 3 components and r,g,b to 0-255
        self.paramsdic=self.parent.ConvertParamsForCustomize(self.paramsdic,self.paramtypedic)
        #self.ReadFileAndSetParams(self.curfile)
        ##self.paramsdic={}
        self.SetParamsToWidgets(self.paramsdic)
        # update parent curset
        self.curset=curset
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)

    def ResetCurrentSet(self,curset):
        self.curset=curset
        self.cmbfil.SetStringSelection(self.curset)
        self.OnFile(1)
        
    def OnNewFile(self,event):
        self.parent.Message('')
        if not self.saveas and not self.rename: return
        setnam=self.cmbfil.GetValue() #GetStringSelection()
        print 'setnam',setnam
        if len(setnam) <= 0: 
            self.parent.Message('No file name in param set file window')
            return
        try: idx=self.filelst.index(setnam)
        except: idx=-1
        if idx >= 0:
            mess='the name is duplicate. please input a different name'
            lib.MessageBoxOK(mess,"")
            return
        if self.rename: 
            retcode=self.Rename(self.curset,setnam)
            self.cmbfil.SetValue(self.curset)      
        #
        if self.saveas:
            self.SaveFile()
            #
            self.curset=setnam
            self.filelst.append(self.curset)
            self.cmbfil.SetItems(self.filelst)
            self.cmbfil.SetStringSelection(self.curset)
    
            self.parent.Message('Created new parameter set '+'"'+setnam+'"')
            # update 'Model' current and filelst
            self.parent.SetCurrentParamSet(self.panelnam,self.curset)
            self.parent.paramsetfiledic[self.panelnam]=self.filelst
            #
            self.saveas=False
        #
        self.saveas=False 
        self.rename=False

    def OnViewFile(self,event):
        self.parent.ViewSelectedFile(self.cmbfil,'.general')

    def IsSaved(self):
        return self.saved

    def GetParamsFromWidgets(self):
        self.newparamdic={}
        for prmnam, widget in self.paramwidgetdic.iteritems():
            if widget[0] == 'TextCtrl': self.newparamdic[prmnam]=widget[1].GetValue()
            elif widget[0] == 'RadioButton': self.newparamdic[prmnam]=widget[1].GetValue()
            elif widget[0] == 'CheckBox': self.newparamdic[prmnam]=widget[1].GetValue()
            elif widget[0] == 'Button': 
                wxcolor=widget[1].GetBackgroundColour() # wx.Colour object
                self.newparamdic[prmnam]=wxcolor.Get() # convert to RGB [0-255]
            else: print 'Error widget in GetParams'    

    def SetParamsToWidgets(self,paramsdic):
        """ note: color intensitiy of r,g, and b, ranges from 0 to 255! """
        for prmnam, value in paramsdic.iteritems():
            widget=self.paramwidgetdic[prmnam]
            if widget[0] == 'TextCtrl': 
                widget[1].SetValue(str(value))
            elif widget[0] == 'ComboBox': widget[1].SetValue(str(value))
            elif widget[0] == 'RadioButton': widget[1].SetValue(value)
            elif widget[0] == 'CheckBox': widget[1].SetValue(value)
            elif widget[0] == 'Button': 
                widget[1].SetBackgroundColour(value) # wx.Colour object                
            else: print 'Error: widget in SetParamsToWidget. param name=',parnam   

    def CountModifiedParams(self):
        nmody=0
        for prmnam, value in self.paramsdic.iteritems():
            if self.newparamdic.has_key(prmnam):
                if self.paramsdic[prmnam] != self.newparamdic[prmnam]: nmody += 1
        return mnody
    
    def Apply(self):
        pass

    def LoadDefault(self):
        self.saveas=False
        self.paramsdic=self.DefaultParams()
        self.cmbfil.SetValue('')
        self.SetParamsToWidgets(self.paramsdic)
                        
    def DefaultParams(self):
        defaultdic={}    
        for prmnam,type in self.paramtypedic.iteritems():
            if prmnam == 'win-size-w' or prmnam == 'win-size-h': continue
            if prmnam == 'shell-win-size-w' or prmnam == 'shell-win-size-h': continue
            defaultdic[prmnam]=self.setctrl.GetDefaultParam(prmnam)
            if type == 'color':
                 defaultdic[prmnam]=numpy.array(defaultdic[prmnam])*255
            if type == 'bool':
                 if defaultdic[prmnam] == 'True': defaultdic[prmnam]=True
                 else: defaultdic[prmnam]=False               
        [w,h]=self.setctrl.GetDefaultParam('win-size')
        defaultdic['win-size-w']=w; defaultdic['win-size-h']=h
        [w,h]==self.setctrl.GetDefaultParam('shell-win-size')
        defaultdic['shell-win-size-w']=w; defaultdic['shell-win-size-h']=h

        return defaultdic

    def RenameFile(self):
        self.rename=True
        mess='Input name in "General param set file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                                  
    def Rename(self,oldnam,newnam):       
        customdir=self.setctrl.GetDir('Customize')
        oldfile=os.path.join(customdir,oldnam+'.general')
        newfile=oldfile.replace(oldnam,newnam)
        if os.path.exists(newfile):
            mess='the file "'+newfile+' " already exists. try a diferent name.'
            self.parant.Message(mess)
            return False
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+oldnam+'" to "'+newnam+'"'
            return False
        idx=self.filelst.index(oldnam)       
        if idx >= 0: self.filelst[idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+oldnam+'" to "'+newnam+'"')
            return False          
        self.curset=newnam
        # set items to widget
        self.cmbfil.SetItems(self.filelst)
        self.cmbfil.SetValue(self.curset)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('Renamed '+'"'+oldnam+'" to "'+newnam+'"')            
        return True

    def SaveFile(self):
        self.GetParamsFromWidgets()
        filename=self.cmbfil.GetValue()
        if len(filename) <= 0: 
            self.parent.Message('No file name in param set file window')
            return
        if not self.saved:
            mess='"Apply" was applied.'
            self.parent.StatusMessage(mess)
            self.saved=True
        #ns=filename.find('.model')
        #if ns < 0: filename=filename+'.model'
        filename=self.parent.MakeFullPathName(filename,'.general')
        print 'filename in save',filename 
        text='general parameters'    
        Customize_Frm.WriteParamSetFile(filename,text,self.paramtypedic,self.newparamdic)
        #
        self.parent.Message('Saved "'+filename+'".')
        self.saved=True

    def SaveFileAs(self):
        self.saveas=True
        mess='Input param set name in "Add-on menu file" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
        
    def Clear(self):
        self.saved=False

    def DelFile(self):
        self.parent.DelSelectedFile(self.cmbfil,'.general')
        setnam=self.cmbfil.GetValue()
        self.filelst.remove(setnam)
        self.cmbfil.SetItems(self.filelst)
        if len(self.filelst) > 0: self.curset=self.filelst[0]
        else: self.curset=''
        self.cmbfil.SetStringSelection(self.curset)
        self.parent.SetCurrentParamSet(self.panelnam,self.curset)
        self.parent.paramsetfiledic[self.panelnam]=self.filelst
        self.parent.Message('param set file "'+setnam+'" was deleted')
         
    def Cancel(self):
        mess='General parameter assignment was canceled.'
        self.parent.StatusMessage(mess)
        self.saved=True
   
class CustomProject():
    """ Peoject setting panel called in 'Setting_Frm' class
    
    :param obj parent: 'Setting_Frm'
    :param obj pagepanel: parent notebook panel.
    :param obj : instance of 'Model' class
    :param str mode: action mode. 'Setting','New', or 'Import'
    """
    def __init__(self,parent,pagepanel,model,prjmode):
        self.classnam='SettingProject'
        self.winlabel=prjmode
        self.panelnam='Project'
        self.parent=parent
        self.pagepanel=pagepanel
        self.model=model # parent.model instance
        self.winctrl=model.winctrl
        self.setctrl=model.setctrl
        self.menuctrl=model.menuctrl
        self.pagepanel.SetBackgroundColour('light gray')
        #self.winlabel='New'
        self.prjmode=prjmode
        self.mode=0
        #
        self.modelst=['New','Edit','Rename'] #,'Import']
        self.curprj=''
        self.prjdir='~/'
        self.saveas=False
        self.rename=False
        #self.newname=''
        #self.importdir=''
        # create panel
        self.CreatePanel()
        # initial settings
        self.Initialize()

    def CreatePanel(self):
        size=self.parent.GetSize(); w=size[0]; h=size[1]
        self.panel=wx.Panel(self.pagepanel,wx.ID_ANY,pos=[-1,-1],size=size)
        #self.panel.SetBackgroundColour('light gray')
        #self.panel=self.pagepanel # do not work. need new panel? seems working 19Nov2014
        hcb=const.HCBOX
        self.widgetobjdic={} # {prjdat nmb:widget,...}, nmb 0:prjdir,1:createdby, 2:createddate,3:comment,5:setting
        yloc=15
        # operations. this codes are not used
        #if self.prjmode == 'Setting':
        #    self.btnmode=wx.RadioBox(self.panel,wx.ID_ANY,"Operations",choices=self.modelst,pos=(35,yloc),
        #                        style=wx.RA_HORIZONTAL)
        #    self.btnmode.SetSelection(self.mode)
        #    self.btnmode.Bind(wx.EVT_RADIOBOX,self.OnMode)
        #    yloc += 50
        #if self.mode == 0: self.prjname=''
        # project file
        wx.StaticText(self.panel,-1,"Project name (Folder):",pos=(10,yloc),size=(140,18)) 
        self.cmbfil=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(160,yloc-2),size=(200,hcb))
        self.cmbfil.Bind(wx.EVT_COMBOBOX,self.OnFile)
        self.cmbfil.Bind(wx.EVT_TEXT_ENTER,self.OnNewFile)
        yloc += 25
        # directopry name
        #if self.mode == 0: self.dirname=''
        wx.StaticText(self.panel,-1,"Root dir.:",pos=(20,yloc),size=(80,18)) 
        self.tclpath=wx.TextCtrl(self.panel,-1,self.prjdir,pos=(100,yloc-2),size=(235,18))
        self.widgetobjdic[1]=self.tclpath
        self.btnbrws=wx.Button(self.panel,wx.ID_ANY,"Browse",pos=(340,yloc-2),size=(55,20))
        self.btnbrws.Bind(wx.EVT_BUTTON,self.OnBrowseDir)
        if self.mode == 2 or self.mode >= 4:
            self.tclpath.Disable(); self.btnbrws.Disable()
        yloc += 25
        # setfile
        title='Setting file:'
        sttip=wx.StaticText(self.panel,-1,title,pos=(20,yloc),size=(80,18)) 
        sttip.SetToolTipString('Select setting name(file,*setting)')
        self.cmbset=wx.ComboBox(self.panel,wx.ID_ANY,"",pos=(100,yloc-2),size=(200,hcb))
        self.cmbset.Bind(wx.EVT_COMBOBOX,self.OnSetFile)
        self.widgetobjdic[4]=self.cmbset
        self.btnview=wx.Button(self.panel,-1,"View",pos=(320,yloc-2),size=(40,20))
        self.btnview.SetToolTipString('View or edit the file with editor')
        self.btnview.Bind(wx.EVT_BUTTON,self.OnViewParamSetFile) 
        yloc += 25
        if self.mode == 1: self.createdby=getpass.getuser()
        wx.StaticText(self.panel,-1,"Created by:",pos=(20,yloc),size=(80,18)) 
        self.tclby=wx.TextCtrl(self.panel,-1,'',pos=(100,yloc-2),size=(230,18))
        self.widgetobjdic[5]=self.tclby
        self.btnuser=wx.Button(self.panel,wx.ID_ANY,"User",pos=(340,yloc-2),size=(55,20))
        self.btnuser.Bind(wx.EVT_BUTTON,self.OnUser)
        if self.mode >= 2: 
            self.tclby.Disable(); self.btnuser.Disable()
        yloc += 25
        wx.StaticText(self.panel,-1,"Created date:",pos=(20,yloc),size=(80,18))
        if self.mode == 1: self.createddate=lib.DateTimeText()
        self.tcldate=wx.TextCtrl(self.panel,-1,'',pos=(100,yloc-2),size=(230,18))
        self.widgetobjdic[6]=self.tcldate
        self.btnnow=wx.Button(self.panel,wx.ID_ANY,"Date",pos=(340,yloc-2),size=(55,20))
        self.btnnow.Bind(wx.EVT_BUTTON,self.OnDateTime)
        if self.mode >= 2: 
            self.tcldate.Disable(); self.btnnow.Disable()
        yloc += 25
        if self.mode == 0: self.comment=''
        hight=40
        if self.mode == 2 or self.mode == 3: hight=18
        wx.StaticText(self.panel,-1,"Comment:",pos=(20,yloc),size=(80,18)) 
        self.tclcmt=wx.TextCtrl(self.panel,-1,'',pos=(100,yloc-2),size=(290,hight),
                                style=wx.TE_MULTILINE)
        self.widgetobjdic[7]=self.tclcmt
        #if self.mode >= 2: self.tclcmt.Disable()
        if self. mode == 2:
            yloc1=yloc+25
            wx.StaticText(self.panel,-1,"New name:",pos=(10,yloc1),size=(80,18)) 
            self.tclnew=wx.TextCtrl(self.panel,-1,'new name here and hit "Enter"',
                                    pos=(100,yloc1-2),size=(290,22),style=wx.TE_PROCESS_ENTER)
            self.tclnew.Bind(wx.EVT_TEXT_ENTER,self.OnRename)#self.widgetobjdic['newname']=self.tclnew         
        if self.mode == 3:
            yloc2 = yloc+25
            wx.StaticText(self.panel,-1,"Import from:",pos=(10,yloc2),size=(80,18)) 
            self.tclimp=wx.TextCtrl(self.panel,-1,'directory name here',pos=(100,yloc2-2),size=(230,22))
            #self.widgetobjdic['import']=self.tclimp
            self.btnimp=wx.Button(self.panel,wx.ID_ANY,"Browse",pos=(340,yloc2-2),size=(55,20))
            self.btnimp.Bind(wx.EVT_BUTTON,self.OnImportDir)            
        #if self.mode >= 3: self.tclcmt.Disable()
        yloc += 50
        pos=[-1,yloc]
        # place buttons
        if self.prjmode == 'Setting':
            self.butnpan=CommonActionButtons(self.parent,self.panel,self,pos)
            self.butnpan.btndefa.Disable()
        else:
            btnok=wx.Button(self.panel,wx.ID_ANY,"OK",pos=(150,yloc-2),size=(50,20))
            btnok.SetToolTipString('Accept params in the panel. It is needed to push "Save" to keep them in a file')
            btnok.Bind(wx.EVT_BUTTON,self.OnOK)
            btncan=wx.Button(self.panel,wx.ID_ANY,"Cancel",pos=(220,yloc-2),size=(50,20))
            btncan.SetToolTipString('Reset params in the panel to initial values')
            btncan.Bind(wx.EVT_BUTTON,self.OnCancel)  

    def Initialize(self):
        # prjdatdic:{prjnam:[prjdir,createdby,createddate,comment,curdir,setting],...}
        #[prjnam,prjdir,curdir,prjfile,setfile,createdby,createddate,comment]
        self.prjdatdic=self.setctrl.MakeProjectDataDic()
        self.paramsetfiledic=self.MakeParamSetFileDic()
        self.prjfilelst=self.paramsetfiledic[self.panelnam]
        self.curparamsetdic=self.MakeCurParamSetDic()
        #
        self.curprj=self.curparamsetdic[self.panelnam]
        self.setfilelst=self.paramsetfiledic[self.panelnam]
        self.curset=self.curparamsetdic[self.panelnam]        
        self.prjlst=self.prjfilelst
        #
        self.cmbfil.SetItems(self.prjlst)
        self.cmbfil.SetValue(self.curprj)
        self.cmbset.SetItems(self.setfilelst)
        # enable/disable save button
        #self.ButtonEnable()
        #
        self.OnFile(1)
        #
        self.saveas=False
        self.rename=False
        self.saved=True
    
    def OnOK(self,event):
        """ not used """
        filename=self.cmbfil.GetValue() #self.tclname.GetValue()
        if len(filename) <= 0:
            mess='Input project name in the "Name(Folder)" window'
            lib.MessageBoxOK(mess,"")
            return
        self.saved=True
        self.SaveFileAs()
        #filename=self.tclname.GetValue()
        self.parent.Message('Project file was saved as '+'"'+filename+'"')
        self.parent.OnClose(1)
 
    def OnCancel(self,event):
        self.Cancel()
              
    def OnMode(self,event):
        # get object
        obj=event.GetEventObject()
        label=obj.GetStringSelection()
        #        
        self.panel.Destroy()      
        if label == 'New': self.mode=0 #; self.winlabel='Create new'
        elif label == 'Edit': self.mode=1 #; self.winlabel='Edit' 
        elif label == 'Rename': self.mode=2 # self.winlabel='Rename' 
        elif label == 'Import': self.mode=3 #; self.winlabel='Import' 
        #self.SetTitle('Project:'+self.winlabel)
        self.CreatePanel()
        self.ButtonEnable()
        
        self.cmbfil.SetItems(self.prjlst)
        self.cmbset.SetItems(self.setfilelst)
        self.cmbfil.SetValue(self.curprj)
        self.SetAllItemsInWidgets(self.curprj)
        self.OnFile(1)

    def ButtonEnable(self):
        if self.mode == 0: 
            self.butnpan.btnsav.Disable(); self.butnpan.btnsavas.Enable()
        elif self.mode == 1:
            self.butnpan.btnsav.Enable(); self.butnpan.btnsavas.Disable()
        elif self.mode == 2:
            self.butnpan.btnsav.Disable(); self.butnpan.btnsavas.Disable()

    def RenameFile(self):
        self.rename=True
        mess='Input name in "Project name" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                    
    def MakeParamSetFileDic(self):
        """ The same routine as in Cusutomize_Frm but needed for independent work """
        self.pagenamlst=['Setting','General','Model','Add-on','Shortcut','Project'] 
        self.fileext=['.py','.general','.model','.add-on','.shortcut','.project']
        self.customdir=self.setctrl.GetDir('Customize')
        self.prjdir=self.setctrl.GetDir('Projects')
        paramsetfiledic={}
        # param set files
        for i in range(len(self.pagenamlst)):
            filelst=lib.GetFilesInDirectory(self.customdir,[self.fileext[i]])
            paramsetfiledic[self.pagenamlst[i]]=self.MakeParamSetName(filelst)
        # project files
        filelst=lib.GetFilesInDirectory(self.prjdir,['.project'])
        paramsetfiledic[self.panelnam]=self.MakeParamSetName(filelst)
        return paramsetfiledic

    def MakeCurParamSetDic(self):
        """ The same routine as in Cusutomize_Frm but needed for independent work """
        curparamsetdic={}
        cursetfile=self.setctrl.GetSetFile()
        curset=os.path.split(cursetfile)[1]
        curprj=os.path.split(self.setctrl.GetCurPrj())[1]
        curparamsetdic[self.panelnam]=curset.split('.')[0]
        curparamsetdic["Project"]=curprj.split('.')[0]  
        cursetfile=os.path.expanduser(cursetfile)
        curfilelst=Customize_Frm.ReadSetFile(cursetfile)
        for i in range(len(curfilelst)):
            curparamsetdic[self.pagenamlst[i+1]]=curfilelst[i].split('.')[0]
        return curparamsetdic

    def MakeParamSetName(self,filelst):
        """ The same routine as in Cusutomize_Frm but needed for independent work """
        for i in range(len(filelst)):
            head,tail=os.path.split(filelst[i])
            base,ext=os.path.splitext(tail)
            filelst[i]=base
        return filelst

    def SetCurSetFileInComboBox(self,curset):
        self.curset=curset
        self.cmbfil.SetStringSelection(self.curset)
        self.OnSetFile(1)

    def OnSetFile(self,event):
       filename=self.cmbset.GetValue()
       filename=filename+'.py'
      
    def OnViewParamSetFile(self,event):
       #label=self.cmbset.GetValue()
       self.parent.ViewSelectedFile(self.cmbset,'.py')
        
    def OnBrowseDir(self,event):
        pathname=lib.GetDirectoryName(self.parent)
        if len(pathname) > 0: self.tclpath.SetValue(pathname)
        self.saved=False

    def OnImportDir(self,event):
        pathname=lib.GetDirectoryName(self.parent)
        if len(pathname) > 0: self.tclimp.SetValue(pathname)
        self.saved=False

    def OnFile(self,event):
        #try:
        prjnam=self.cmbfil.GetValue()
        if prjnam == '': return
        self.curprj=prjnam
        self.SetAllItemsInWidgets(self.curprj)
        self.saved=False
       
    def OnUser(self,event):
        self.createdby=getpass.getuser()
        self.tclby.SetValue(self.createdby)
 
    def OnDateTime(self,event):
        self.createddate=lib.DateTimeText()
        self.tcldate.SetValue(self.createddate)
       
    def OnDelAll(self,event):
        self.setctrl.DelAllProject()
        self.Initialize()

    def IsSaved(self):
        return self.saved

    def DelFile(self): # delete project file and directory
        prjnam=self.cmbfil.GetValue() #self.tclname.GetValue()
        if len(prjnam) <= 0:
            mess='Input project name in the "Name(Folder)" window'
            lib.MessageBoxOK(mess,"")
            return
        else:
            mess='Are you sure to delete '+'"'+prjnam+'" ?.'
            dlg=lib.MessageBoxYesNo(mess,"")
            if not dlg: return
        prjrootdir=self.prjdatdic[prjnam][1]
        prjdirnam=os.path.join(prjrootdir,prjnam)
        # delete project directory
        retcode=self.DeleteProjectDirectory(prjnam,prjdirnam)
        if not retcode: 
            mess='Failed to delete project directory "'+prjdirnam+'" '
            self.parent.Message(mess)
            return
        # delte project file
        retcode=self.DeleteProjectFile(prjnam)
        if not retcode: 
            mess='Failed to delete project file "'+prjnam+'" '
            self.parent.Message(mess)
            return
        #  delete prjnam in prjfilelst
        try:             
            idx=self.prjfilelst.index(prjnam)       
            if idx >= 0: del self.prjfilelst[idx]
        except: pass
        # set data on widget           
        self.cmbfil.SetItems(self.prjfilelst)
        if len(self.prjfilelst) > 0: self.curprj=self.prjfilelst[0]
        else: self.curprj=''
        self.cmbfil.SetValue(self.curprj)
        self.parent.SetCurrentParamSet(self.panelnam,self.curprj)
        self.parent.paramsetfiledic[self.panelnam]=self.prjfilelst
        del self.prjdatdic[prjnam]            
        self.OnFile(1)
        #
        self.parent.Message('project file "'+prjnam+'" and projetc directory "'+prjdirnam+'" was deleted.')        
        self.saved=True

    def GetAllItemsInWidgets(self):
        """ Get item values (1,3,4,5,6) in widgets
        
        :return: prjitemlst: [prjnam,prjpath,curdir,setfile,createdby,createddate,comment]
        :rtype: lst
        :see: fucustom.Customize_frm.WriteProjectFile static method 
        """
        prjitemlst=10*['']
        # i=1,3,4,5,6
        for i, obj in self.widgetobjdic.iteritems(): prjitemlst[i]=obj.GetValue()
        prjitemlst[0]=self.curprj
        if self.prjdatdic.has_key(self.curprj): prjitemlst[2]=self.prjdatdic[self.curprj][2]
        else: prjitemlst[2]=os.path.join(prjitemlst[1],self.curprj)
        if self.prjdatdic.has_key(self.curprj): prjitemlst[3]=self.prjdatdic[self.curprj][3]
        else: 
            prjfiledir=self.GetDir('Projects')
            prjitemlst[3]=os.path.join(prjfiledir,prjitemlst[0]+'.project')
        return prjitemlst

    def SetAllItemsInWidgets(self,prjnam):
        for i, obj in self.widgetobjdic.iteritems():
            obj.SetValue(self.prjdatdic[prjnam][i])

    def CheckProject(self,prjnam):
        subdirs=['Images','Draws','Docs']; issubdir=[]
        prjrootdir=self.prjdatdic[prjnam][1]
        prjdirnam=os.path.join(prjrootdir,prjnam)
        isprjdir=os.path.isdir(prjdirnam)       
        for d in subdirs:
            if os.path.isdir(prjdirnam): issubdir.append(True)
            else: issubdir.append(False)          
        isimgdir=issubdir[0]; isdrwdir=issubdir[1]; isdocdir=issubdir[2]
        return isprjdir,isimgdir,isdrwdir,isdocdir
                                
    def CheckDirectory(self,prjdir):
        ans=True
        if os.path.exists(prjdir) and os.path.isfile(prjdir):
            mess='Error: "'+prjdir+'" is not a directory but a file.'
            ok=lib.MessageBoxOK(mess,"")
            ans=False
        return ans

    def CheckDuplicate(self,newnam):
        dup=False; cancel=False
        if self.prjdatdic.has_key(newnam): dup=True
        else: dup=False
        if dup:
            mess='Duplicated project name: "'+newnam+'". Overwrite ?'
            ok=lib.MessageBoxOK(mess,"")
            if ok == wx.YES: cancel=False
            else: cancel=True
        return cancel   
                    
    def OnClear(self,event):
        for i, obj in self.widgetobjdic.iteritems():
            obj.SetValue(''); self.prjdatdic[self.curprj][i]=''
        self.prjdatdic[self.curprj][2]=''
        if self.mode == 2: self.tclnew.SetValue('')
        if self.mode == 3: self.tclimp.SetValue('')
        self.saved=False

    def Reset(self):
        pass

    def LoadDefault(self):
        pass
     
    def Cancel(self):
        mess='canceled.'
        self.parent.Message(mess)
        self.saved=True
        self.saveas=False
        self.rename=False

    def SaveFile(self):
        prjnam=self.cmbfil.GetValue() #self.tclname.GetValue()
        filename=prjnam
        if len(filename) <= 0: 
            self.parent.Message('No file name in "Project name" window')
            return
        self.curprj=prjnam
        # get data in widgets
        prjitems=self.GetAllItemsInWidgets()
        self.prjdatdic[self.curprj]=10*['']
        for i in range(len(prjitems)): self.prjdatdic[self.curprj][i]=prjitems[i]
        #
        ns=filename.find('.project')
        if ns < 0: filename=filename+'.project'
        prjdir=self.setctrl.GetDir('Projects')
        filename=os.path.join(prjdir,filename)
        # write project file
        Customize_Frm.WriteProjectFile(filename,self.curprj,prjitems)
        # create project directory if not exist
        prjrootdir=self.widgetobjdic[1].GetValue()
        if len(prjrootdir) > 0:
            prjdirnam=os.path.join(prjrootdir,prjnam)
            retmess=Customize_Frm.CreateProjectDirectory(prjnam,prjdirnam) 
            if len(retmess) > 0:
                self.parent.Message(retmess)      
        #
        self.parent.Message('Saved "'+filename+'".')
        self.saved=True
        
    def OnNewFile(self,event):   
        if not self.saveas and not self.rename: return
        newnam=self.cmbfil.GetValue()
        if len(newnam) <= 0: 
            self.parent.Message('No file name ')
            return
        cancel=self.CheckDuplicate(newnam)
        if cancel: return
        #
        if self.saveas: self.CreateNewProject(newnam)  
        if self.rename: 
            retcode=self.RenameProject(self.curprj,newnam)
            if not retcode: self.cmbfil.SetValue(self.curprj)      
        #
        self.saveas=False 
        self.rename=False
             
    def CreateNewProject(self,prjnam):       
        #
        dirpath=self.widgetobjdic[1].GetValue() # self.prjdatdic[prjnam][0]
        dirpath=os.path.expanduser(dirpath)
        if not os.path.isdir(dirpath):
            mess='Root directory "'+dirpath+'" does not exist. Input correct one in the "Root dir" window'
            lib.MessageBoxOK(mess,"")
            return
        dirnam=os.path.join(dirpath,prjnam)        
        retmess=Customize_Frm.CreateProjectDirectory(prjnam,dirnam)
        if len(retmess) > 0:   
            mess=retmess       
            mess=mess+'Do you want to continue?  if yes, you have to create the project directory '+'"'+dirnam+'" ?.'
            dlg=lib.MessageBoxOK(mess,"")
            if dlg == wx.NO: 
                self.cmbfil.SetValue(self.curprj)
                return        
        self.curprj=prjnam
        self.prjdatdic[self.curprj]=10*['']
        #
        self.SaveFile() # save projrct file and make prjdatadic
        #
        print 'rootdir',self.prjdatdic[self.curprj][1]
        self.prjfilelst.append(self.curprj)
        self.cmbfil.SetItems(self.prjfilelst)
        self.cmbfil.SetStringSelection(self.curprj)
        #
        self.parent.Message('Created new project '+'"'+prjnam+'"')
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curprj)
        self.parent.paramsetfiledic[self.panelnam]=self.prjfilelst
        #
        self.saveas=False

    def SaveFileAs(self):
        if self.mode != 0:
            self.parent.Message('Push "Save" button.')
            return
        self.saveas=True
        mess='Input name in "Project name" window and hit "Enter"'
        lib.MessageBoxOK(mess,"")
        self.cmbfil.SetValue('')
                                        
    def XXCreateProjectDirectory(self,prjnam,prjdirnam):
        """ create project file 'fudir/Projects/prjnam.project' and project diretory ('prjrootdir/prjnam')
        and its subsirectories (/Images, /Draws and /Docs)
        
        :param str prjnam: project name
        :param str prjrootdir: root directory of the project. the project directory is
        prjrootdir/prjnam 
        :return: retcode: True for succeeded, False for Failed
        :rtype: bool
        """
        retcode=True; mess=''
        prjsubdirs=['Docs','Images','Draws']
        # make project directory
        if not os.path.isdir(prjdirnam): 
            try: os.mkdir(prjdirnam)
            except:
                 mess='Failed to create project dirctory "'+prjdirnam+'"'
                 retcode=False
        # make sub-directories
        if os.path.isdir(prjdirnam): 
            try:
                for d in prjsubdirs:
                    ddir=os.path.join(prjdirnam,d)
                    if not os.path.isdir(ddir): os.mkdir(ddir)
            except:
                mess='Failed to create project sub-directories in "'+prjdirnam+'"'
                retcode=False
        self.parent.Message(mess)                                  
        return retcode           

    def OnClose(self,event):
        if not self.saved:
            mess="Not saved. Do you want to save project data?"
            dlg=lib.MessageBoxOK(mess,"")
            if dlg == wx.YES:
                #if wx.YES:
                prjdat=self.Projectdata()
                self.setctrl.SaveProjectDataList(prjdat)
                self.saved=True
            else: pass
        self.winctrl.CloseWin(self.winlabel)
        self.Destroy()        

    def DeleteProjectDirectory(self,prjnam,prjdirnam):
        """
        :param str prjnam: prjnam: used for delete /Projects/xxx.prject file
        :param str prjrootdir: project root directory used to remove project(prjrootdir/prjnam
         and sbdirectories(prjrootdir/prjnam/Images,/Draws, and /Docs)
        :return: retcode True for succeed and False for failed to delete
        :rtype: bool
        """
        retcode=True; mess=''
        if not os.path.isdir(prjdirnam):
             mess='Project directory "'+prjdirnam+'" does not exist'
        else:
            # remove project file in /Project directory
            try:
                shutil.rmtree(prjdirnam)
                mess='Project directory "'+prjdirnam+'" was deleted.'
            except:
                mess='Failed to delete project directory "'+prjdirnam+'"'
                retcode=False        
        self.parent.Message(mess)
        return retcode

    def DeleteProjectFile(self,prjnam):
        """
        :param str prjnam: prjnam: used for delete /Projects/xxx.prject file
        :param str prjrootdir: project root directory used to remove project(prjrootdir/prjnam
         and sbdirectories(prjrootdir/prjnam/Images,/Draws, and /Docs)
        :return: retcode True for succeed and False for failed to delete
        :rtype: bool
        """
        retcode=True; mess=''
        filename=prjnam+'.project'
        prjdir=self.setctrl.GetDir('Projects')
        filename=os.path.join(prjdir,filename)  
        # delete project file
        if not os.path.exists(filename): 
            mess='Project file "'+filename+'" does not exist'
        try: 
            os.remove(filename)
            mess='Project file "'+filename+'" was deleted.'
        except:
            mess='Failed to delete project file "'+filename+'"'
            retcode=False
        self.parent.Message(mess)
        return retcode

    def RenameProject(self,prjnam,newnam):       
        prjdir=self.setctrl.GetDir('Projects')
        olddir=self.prjdatdic[prjnam][1]
        olddirnam=os.path.join(olddir,prjnam)
        newdirnam=olddirnam.replace(prjnam,newnam)
        oldfile=os.path.join(prjdir,prjnam+'.project')
        newfile=oldfile.replace(prjnam,newnam)
        # remame project file name
        try: os.rename(oldfile,newfile)
        except:
            mess='Failed rename "'+prjnam+'" to "'+newnam+'"'
            return False
        self.curprj=newnam
        # rename project directory name
        if os.path.isdir(olddirnam): os.rename(olddirnam,newdirnam) #shutil.move(olddir,newdir)
        # rename prjdatdic
        idx=self.prjfilelst.index(prjnam)       
        if idx >= 0: self.prjfilelst[idx]=newnam
        else: 
            self.parent.Message('Error occured in renaming '+'"'+prjnam+'" to "'+newnam+'"')
            return False          
        # del prjnam in prjdatdic
        temp=self.prjdatdic[prjnam]
        self.prjdatdic[newnam]=temp
        del self.prjdatdic[prjnam]
        # set widget         
        self.cmbfil.SetItems(self.prjfilelst)
        self.cmbfil.SetValue(self.curprj)
        # update 'Project' current and filelst
        self.parent.SetCurrentParamSet(self.panelnam,self.curprj)
        self.parent.paramsetfiledic[self.panelnam]=self.prjfilelst
        self.parent.Message('Renamed '+'"'+prjnam+'" to "'+newnam+'"')            
        return True
      
    def DelAllProject(self):
        pass
    def EditProject(self,pdjdat):
        pass
    
    def XXWriteProjectFile(self,filename,prjnam,prjitems):
        #prjitems=[prjpath,createdby,createddate,comment,curdir,setting] #,curdir]  
        #prjdir=self.GetDir(self.panelnam)
        #prjfile=prjdat[0]+'.txt'
        #filename=os.path.join(prjdir,prjfile)
        f=open(filename,'w')
        f.write('# project file. '+lib.CreatedByText()+'\n')
        #f.write('prjnam='+prjnam+'\n')
        f.write('prjpath='+prjitems[0]+'\n')
        f.write('createdby='+prjitems[1]+'\n')
        f.write('createddate='+prjitems[2]+'\n')
        f.write('comment='+prjitems[3]+'\n')
        f.write('curdir='+prjitems[4]+' # not used.\n')
        f.write('setting='+prjitems[5]+'\n')
        f.close()        
         
class CommonActionButtons():
    """ Common bouttons in pagepanels
    
    :param obj parent: parent object
    :param int pagepanel: pagepanel number
    :param obj pageobj: page object
    :param lst pos: position [x(int),y(int)]
    """
    def __init__(self,parent,pagepanel,pageobj,pos):
        self.parent=parent # Setting_Frm
        self.pagepanel=pagepanel # pagepanel
        self.pageobj=pageobj
        self.btndefa=None
        self.btnsav=None
        self.btnsavas=None
        #
        self.pos=pos
        #
        self.CreatePanel()
        
    def CreatePanel(self):
        if len(self.pos) <= 0: self.pos=[-1,10]
        [w,h]=self.parent.GetSize(); size=[w,35]
        #panel=wx.Panel(self.pagepanel,-1,pos=self.pos,size=size) #style=wx.BORDER_SUNKEN) #RAISED) 
        panel=self.pagepanel
        #panel.SetBackgroundColour('light gray')
        yloc=self.pos[1]
        yloc += 5
        wx.StaticLine(panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 10
        # delete button
        btndel=wx.Button(panel,wx.ID_ANY,"Del",pos=(20,yloc-2),size=(30,20))
        btndel.Bind(wx.EVT_BUTTON,self.OnDelFile)
        btndel.SetToolTipString('Delete file')
        # rename button
        self.btnren=wx.Button(panel,wx.ID_ANY,"Rename",pos=(60,yloc-2),size=(60,20))
        self.btnren.Bind(wx.EVT_BUTTON,self.OnRenameFile)
        self.btnren.SetToolTipString('Rename file')        
        # load default button
        self.btndefa=wx.Button(panel,wx.ID_ANY,"Load default",pos=(130,yloc-2),size=(80,20))
        self.btndefa.SetToolTipString('Load default parameters')
        self.btndefa.Bind(wx.EVT_BUTTON,self.OnDefault)
        # save button     
        self.btnsav=wx.Button(panel,wx.ID_ANY,"Save",pos=(220,yloc-2),size=(40,20))
        self.btnsav.Bind(wx.EVT_BUTTON,self.OnSaveFile)
        self.btnsav.SetToolTipString('Write params to file')
        # saveas button
        self.btnsavas=wx.Button(panel,wx.ID_ANY,"Save as",pos=(270,yloc-2),size=(60,20))
        self.btnsavas.SetToolTipString('Save as')
        self.btnsavas.Bind(wx.EVT_BUTTON,self.OnSaveFileAs)
        # cancel button
        btncan=wx.Button(panel,wx.ID_ANY,"Cancel",pos=(340,yloc-2),size=(50,20))
        btncan.SetToolTipString('Making a fresh start. You can not cancel "Del","Save","Save as" operations')
        btncan.Bind(wx.EVT_BUTTON,self.OnCancel)

    def OnDefault(self,event):
        self.pageobj.LoadDefault()
    
    def OnCancel(self,event):
        self.pageobj.Cancel()

    def OnRenameFile(self,event):
        self.pageobj.RenameFile()
                
    def OnSaveFile(self,event):
        self.pageobj.SaveFile()    
          
    def OnSaveFileAs(self,event):
        self.pageobj.SaveFileAs()

    def OnDelFile(self,event):
        self.pageobj.DelFile()
