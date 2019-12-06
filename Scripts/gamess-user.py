#!/bin/sh
# -*- coding: utf-8 -*- 
#
#-----------
# module name: gamess-user.py
# ----------
# function: Assist input data generation for GAMESS
# usage: This script is executed in PyShell console.
#        >>> fum.ExecuteScript1('gamess-user.py',False)
# ----------
# change history
# modified for fu ver.0.2.0 18May2015
# the first version for fu ver.0.0.0 23Del2015
# -----------

import os
import sys
import wx
import glob
###import wx.grid
#from wx.lib.combotreebox import ComboTreeBox

import shutil 
import functools
import threading
import subprocess
import datetime
import time
import copy
import numpy
#import filecmp

sys.path.insert( 0, '..//')
#import fumodel
import molec
import const
import lib
import subwin
import rwfile

class GMSUser(object):
    def __init__(self,parent,mode='beginner'):
        """
        Main program of GMSUser
        
        :param obj parent: parent object
        :param str mode: 'beginner' or 'expert'
        
        This program requires following data files,
        1.inputdoc.txt ... GAMESS Inputdoc text (FUPATH/Programs/gamess/gamessdoc/)
        2.userinputdoc.txt ... Input definition for GMSBeginner(FUPATH/Programs/gamess/gamessdoc/)
        3.index.html ... GAMESS HTML docment... (FUPATH/Programs/gamess/gamessdoc/_build/html/index.html)
        4.gamesspath.mac(.win) ... GAMESS program path file (FUPATH/Programs/gamess/)
        """
        #self.gmsuser=parent
        self.model=parent
        self.mdlwin=parent.mdlwin

        self.mode=mode
        #
        self.model=None
        self.gmspath=''
        self.gmscmd=''
        self.gmsarg=''
        self.gmsscrdir=''
        self.gmsexamdir=''
        if self.mdlwin:
            self.model=self.mdlwin.model
            self.model=self.mdlwin.model
            self.setctrl=self.model.setctrl
            self.winctrl=self.model.winctrl
            self.mol=self.model.mol 
            self.childobj=self.model.childobj     
            self.childobj.Set('gamess-user',self)
            self.ctrlflag=self.model.ctrlflag
            #
            self.prgfile=self.GetGAMESSPrgFile()
            self.SetUpGAMESSFiles(self.prgfile)
        #        
        self.flags=lib.DicVars(self)
        #
        self.atomlabelwithnmb=True # option for coordinate format in input file
        self.readfilename=''
        self.writefilename=''
        #        
        self.maxlistboxmenuheight=400
        self.expertwinsize=[300,450]
        self.beginnerwinsize=[275,460]
        self.expertwin=False
        self.beginnerwin=False
        self.beginner=None
        self.expert=None
        self.texteditor=False
        self.exeprgwin=None
        #
        self.winpos=[]
        self.winsize=[]
        self.fontheight=15 #16
        #
        #self.openexeprgwin=False
        self.exewinlabel='ExecProgWin'
        self.flags.Set(self.exewinlabel,False)
        self.openexeprgwin=False
        self.openexebatchwin=False
        # font color 
        self.setcolor=wx.RED #wx.BLUE #wx.CYAN
        self.unsetcolor=wx.BLACK
        self.needcolor=(165, 42, 42) # brown
        self.namelst=[]
        
        # GMS input.txt file
        inputdocfile,userdocfile,self.gmsdochtml=self.GetGAMESSDocFiles()
        mess='fuplot doc files:\n'
        mess=mess+'inputdocfile='+inputdocfile+'\n'
        mess=mess+'userinputdocfile='+userdocfile+'\n'
        mess=mess+'gmsdochtml='+self.gmsdochtml
        self.model.ConsoleMessage(mess)        
        #
        self.gmsinpobj=GMSInput(self,inputdocfile)
        self.gmsdoc=self.gmsinpobj.gmsdoc
        self.ExtractGMSDocData(self.gmsdoc)
        # FMOInput class object
        self.fmoinpobj=FMOInputText(self,self.model)
        # indispensable name groups
        self.initialnamelst=['$CONTRL','$SYSTEM','$BASIS','$DATA']
        # input group name list
        self.inputnamelst=self.initialnamelst
        # variables in name group
        self.namvarlst=self.gmsinpobj.DefaultNamVars(self.inputnamelst)
        # variables in name group which can be input from GMSExpert_Frm
        self.inpnamvardic=self.SetInputNameVars(self.namvarlst) 
        # Set values to all variables
        self.inputvaldic=self.gmsinpobj.DefaultValues(self.namelst)
        # text type data
        self.textvaldic={}
        #
        self.allinputnames=self.initialnamelst
        # for GMSgeginner
        userdoc=self.gmsinpobj.ReadInputDocText(userdocfile)
        self.ExtractUserGMSDocData(userdoc)
        self.userinputvaldic=copy.deepcopy(self.uservarvaldic)        
        self.usertextvaldic={}
        # information of gamess input file
        self.inputfileinfo=''
        # initial current name group in GMSExpert_Frm
        #self.curname=self.inputnamelst[0]
        self.prvdir=''
        
        """ set for debug """
        self.madeinput=True
        self.gmsinputfile=''
        self.inputfilelst=[]
        self.outputfilelst=[]
        self.createdinputfilelst=[]
        #self.prgfile=self.GetGAMESSPrgFile()
        self.jobnmb=0
        self.inpfilecopylst=[]
        #
        self.jobtitle=''
        self.coordinternal=False
        self.coordfile=False
        self.fragdatafromfu=False
        self.spin='1'
        self.charge='0'
        self.nlayer=1
        self.basis='STO-3G'
        self.wave='RHF'
        self.wavelayer=5*['']; self.wavelayer[0]=self.wave
        self.basislayer=5*['']; self.basislayer[0]=self.basis
        self.nbasislayer=1 
        self.grimmdisp=False
        self.properties=''
        self.prvproperties=''
        self.nodes='1'
        self.cores='1'
        self.memory='1'
        self.disk='256'
        # scratch files/$:_
        self.gmsscrextlst=['.dat','.trj','.rst','.efp']
        # Open input panel
        ###self.timer=wx.Timer()
        #self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
        #
        if not self.ctrlflag.Get('gamess-user'):
            self.ctrlflag.Set('gamess-user',True)
            if self.mode == 'beginner': self.OpenBeginnerWin(self.mdlwin)
            elif self.mode == 'expert': 
                try: self.openexeprgwin=self.beginner.openexeprgwin
                except: pass
                self.OpenExpertWin(self.mdlwin,mode,self.inputnamelst)
        else:
            mess='gamess-user.py is running!'
            lib.MessageBoxOK(mess,'gamess-user.py')            
    
    def SetUpGAMESSFiles(self,prgfile):
        self.gmspath,self.gmscmd,self.gmsarg,self.gmsscrdir, \
                             self.gmsexamdir=self.ReadProgramPathFile(prgfile)
        #
        self.rungmscmd=os.path.join(self.gmspath,self.gmscmd)
        self.rungmscmd=self.rungmscmd+' '+self.gmsarg
        gmsitems=self.rungmscmd.split(' ')
        head,tail=os.path.split(gmsitems[0])
        self.gmsdir=head
        #self.gmsexamdir=os.path.join(self.gmsdir,'tests')
        prgdir=self.setctrl.GetDir('Programs')
        prgdir=os.path.join(prgdir,'gamess')
        self.fmoexamdir=os.path.join(prgdir,'fmoexamples')
        mess=     'GMSUser script: GAMESS PATH='+self.gmsdir+'\n'
        mess=mess+'                 gmsprgfile='+self.prgfile+'\n'
        mess=mess+'                   rngmscmd='+self.rungmscmd+'\n'
        mess=mess+'                     scrdir='+self.gmsscrdir+'\n'
        mess=mess+'               gmsexampledir='+self.gmsexamdir+'\n'
        mess=mess+'               fmoexampledir='+self.fmoexamdir
        self.model.ConsoleMessage(mess)
        #
        self.gmspath=os.path.expanduser(self.gmspath)
        self.gmsscrdir=os.path.expanduser(self.gmsscrdir)
        self.gmsexamdir=os.path.expanduser(self.gmsexamdir)

    def ReadProgramPathFile(self,prgfile):
        path=""; cmd=""; arg=""; scr=""; tests=""
        if os.path.exists(self.prgfile):
            f=open(self.prgfile,"r")
            for s in f.readlines():
                s=s.strip()
                if s[:1] == '#': continue
                #print 'ss.find("program"),ss.find("GAMESS")',ss.find("program"),ss.find("GAMESS")
                if s[:4].upper() == "PATH": # and ss.find("GAMESS") >= 0:
                    items=s.split(' ',1)
                    if len(items) >= 2:
                        path=items[1].strip()
                if s[:3].upper() == "CMD":
                    items=s.split(' ',1)
                    if len(items) >= 2:
                        cmd=items[1].strip()
                if s[:4].upper() == "ARGS":
                    items=s.split(' ',1)
                    if len(items) >= 2:
                        arg=items[1].strip()
                if s[:3] == "SCR":
                    items=s.split(' ',1)
                    if len(items) >= 2:
                        scr=items[1].strip()
                if s[:5] == "TESTS":
                    items=s.split(' ',1)
                    if len(items) >= 2:
                        tests=items[1].strip()
                    
            f.close()
        return path,cmd,arg,scr,tests
         
    def ExtractGMSDocData(self,gmsdoc):
        self.grouplst=gmsdoc[0]
        self.grouptipsdic=gmsdoc[1]
        self.namelst=gmsdoc[2]
        self.namegroupdic=gmsdoc[3]
        self.nametipsdic=gmsdoc[4]
        self.varlstdic=gmsdoc[5]
        self.varvaldic=gmsdoc[6]
        self.varvaltipsdic=gmsdoc[7]
        self.requireddic=gmsdoc[8]
        self.conflictdic=gmsdoc[9]
        self.needdic=gmsdoc[10]
    
        #print 'conflictdic',self.conflictdic

    def ExtractUserGMSDocData(self,userdoc):
        #print 'usernamelst',userdoc[2]
        #print 'namelst:gmsuserdoc[2]',gmsuserdoc[2]
        #print 'namegrp:gmsuserdoc[3]',gmsuserdoc[3]
        #print 'varlst:gmsuserdoc[5]',gmsuserdoc[5]
        #print 'varval:gmsuserdoc[6]',gmsuserdoc[6]
        
        self.usernamelst=userdoc[2]
        #self.usernamegroupdic=userdoc[3]
        self.uservarlstdic=userdoc[5] 
        #print 'uservarlstdic',userdoc[5]
        self.uservarvaldic=userdoc[6]
        #print 'uservarvaldic',userdoc[6]
    
    def OpenBeginnerWin(self,mdlwin):
        """ may be called from experttWin to switch"""
        #print 'OpenBeginnerWin'
        if self.beginnerwin: return
        if len(self.inputnamelst) <= 0: return
        #
        parpos=[100,100] #self.GetPosition()
        winpos=[100,100]
        #winsize=self.expertwinsize
        #
        self.mode='beginner'
        self.beginner=GMSBeginner_Frm(mdlwin,-1,self)
        self.beginnerwin=True
        self.beginner.Show()

    def OpenExpertWin(self,mdlwin,inputnamelst,winpos=[100,100]):
        if self.expertwin: return
        if len(inputnamelst) <= 0: return
        #
        parpos=[100,100]
        winpos=winpos
        winsize=self.expertwinsize
        if len(inputnamelst) <= 0: self.allinputnamelst
        self.mode='expert'
        #
        self.expert=GMSExpert_Frm(mdlwin,-1,self,self.mode,inputnamelst,winpos=winpos)
        self.expertwin=True
        self.expert.Show()

    def CloseExpertWin(self):
        self.expert.Destroy()
        self.expertwin=False
        
    def CloseBeginnerWin(self):
        self.beginner.Destroy()
        self.beginnerwin=False

    def GetCreatedInputFileList(self):
        return self.createdinputfilelst
    
    def SetCreatedInputFileList(self,filelst):
        self.createdinputfilelst=filelst
    
    def SaveInput(self):
        # check layer
        if self.nlayer > 1:
            nlayer,layerlst=self.model.frag.ListAtomLayer()
            if nlayer != self.nlayer:
                mess='Layer data are inconsistent between "Wave function" and'
                mess=mess+' "Fragment" attribute.\n'
                mess=mess+'Please reset layers by "FMO"-"Fragment attribute" '
                mess=mess+' menu.'
                lib.MessageBoxOK(mess,'GMSUser(SaveInput)')
                return
        retmess=''
        wcard='input file(*.inp)|*.inp|All(*.*)|*.*'
        name=self.model.setctrl.GetParam('defaultfilename')
        self.model.setctrl.SetParam('defaultfilename','')
        filename=lib.GetFileName(None,wcard,'w',True,defaultname=name)
        if len(filename) <= 0: return
        self.SaveInputFile(filename)

    def SaveInputFile(self,filename,check=True):
        
        curdir=lib.ChangeToFilesRootDir(filename)
        #inptext=self.MakeCurrentText()
        """
        if self.inputvaldic.has_key('$FMO:NFRAG'):
            if self.inputvaldic['$FMO:NFRAG'][1] == self.setcolor:
                self.SetAllFMOValueFromFU() 
        
        text=self.gmsinpobj.MakeInputDataText(self.allinputnames,
                                              self.inputvaldic,self.textvaldic)
        """
        text=self.MakeCurrentText()

        if self.textvaldic.has_key('$FMOXYZ:$FMOXYZ'):
            #if self.textvaldic['$FMOXYZ:$FMOXYZ'][1] == self.setcolor:
            rescom=self.fmoinpobj.FMOResidueTextFromFU()
            text=text+'\n'+rescom
        retmess=self.gmsinpobj.SaveInputFile(filename,text)
        
        self.gmsinputfile=filename
        if check:
            if filename in self.createdinputfilelst:
                mess='The same input file exists. Would you like to replace it?'
                retcode=lib.MessageBoxYesNo(mess,'')
                if not retcode: return
                #if dlg.ShowModal() == wx.ID_NO: return
                #dlg.Destroy()
                self.createdinputfilelst.remove(filename)
        self.createdinputfilelst.append(filename)

        if len(retmess) <= 0:
            retmess='Created GMS input file. file='+filename
        try: 
            self.expert.statusbar.SetStatusText(retmess)
        except: 
            try: self.model.Message2(retmess)
            except: lib.MessageBoxOK(retmess,'GMSUser:SaveInput')

    def GetGAMESSDocFiles(self):
        dochtmlfile=''; inputdocfile=''; userinputdocfile=''
        if self.mdlwin:
            prgdir=self.model.setctrl.GetDir('Programs')            
            gamessdir=os.path.join(prgdir,'gamess')
            docdir=os.path.join(gamessdir,'gamessdoc')
            dochtml='html//index.html'
            dochtmlfile=os.path.join(docdir,dochtml)
            inputdoc='inputdoc-txt//inputdoc.txt'
            inputdocfile=os.path.join(docdir,inputdoc)
            userinputdoc='inputdoc-txt//userinputdoc.txt'
            userinputdocfile=os.path.join(docdir,userinputdoc)
        return inputdocfile,userinputdocfile,dochtmlfile
        
    def GetGAMESSPrgFile(self):
        prgfile=''
        if self.mdlwin:
            prgdir=self.model.setctrl.GetDir('Programs')            
            gamessdir=os.path.join(prgdir,'gamess')
            pathfile='gamesspath.mac'
            if lib.GetPlatform() == 'WINDOWS': pathfile='gamesspath.win'
            prgfile=os.path.join(gamessdir,pathfile)
            prgfile=os.path.expanduser(prgfile)
        return prgfile  

    def OpenListBoxMenu(self,parent,retmethod,menulst,tiplst,submenudic,subtipdic,menulabel='LBMenu'):
        [x,y]=wx.GetMousePosition()
        winpos=[x+20,y]
        winheight=len(menulst)*self.fontheight+10
        if winheight > self.maxlistboxmenuheight:
            winheight=self.maxlistboxmenuheight
        winsize=[100,winheight]
        menulabel=menulabel
        #self.listboxmenu=lib.ListBoxMenu_Frm(self,-1,winpos,winsize,menulabel,menulst,tiplst)
        listboxmenu=subwin.ListBoxMenu_Frm(parent,-1,winpos,winsize,retmethod,
                                        menulst,tiplst=tiplst,submenudic=submenudic,
                                        subtipdic=subtipdic,menulabel=menulabel)
        #self.openlistboxmenu=True
        return listboxmenu
          
    def ViewGAMESSDocument(self):
        """ View GAMESS input document.
        
        :note: The HTML file should be set in 'setting' script,
        'fum.ctrl.SetParam('gms-document','file-name')
        """
        if not os.path.exists(self.gmsdochtml):
            mess='HTML file not found. file='+self.gmsdochtml
            lib.MessageBoxOK(mess,'ViewGamessDocument')
            return
        lib.ViewHtmlFile(self.gmsdochtml)

    def SetCoordFromFU(self):
        namvar='$DATA:$DATA'
        #molname,text=self.TextCoordFromFU()
        text=''; molname=''
        #try: 
        #curmol,mol=self.model.molctrl.GetCurrentMol()  # Molecule instance in fumodel
        mol=self.model.mol
        molname=mol.name
        print 'mol.name',mol.name
        #except: return
        #
        ff12='%12.6f'; fi4='%4d'; natm=len(mol.atm); form='%0'+str(len(str(natm)))+'d'
        #text=text+molname+'\n'
        #text=text+'C1\n'
        i=0
        for atom in mol.atm:
            elm=atom.elm; an=const.ElmNmb[elm]; san=fi4 % an
            x=ff12 % atom.cc[0]; y=ff12 % atom.cc[1]; z=ff12 % atom.cc[2]
            i += 1
            if self.atomlabelwithnmb: elm=elm+(form % i)
            text=text+4*' '+elm+' '+san+' '+x+' '+y+' '+z+'\n'
        text=text[:-1]
        #
        if len(text) <= 0:
            mess='Falied to get coordinate data from FU.'
            lib.MessageBoxOK(mess,'GMSUser:SetCoordFromFU')
        else:
            self.jobtitle=molname
        if text[-1] == '': text=text[:-1]
        text=molname+'\n'+' C1\n'+text
        self.SetTextDataToInputValDic(namvar,text)
        self.jobtitle=molname
        return text

    def TextDataFromFU(self,namvar):
        text=''; molname=''
        try:  molname,mol=self.mdlwin.model.GetMol()  # Molecule instance in fumodel
        except: return
        
        #print 'TextDataFromFU, namvar',namvar
        
        #
        if namvar == '$DATA:$DATA':
            text=self.SetCoordFromFU()
        elif namvar == '$FMOXYZ:$FMOXYZ':
            text=self.FMOXYZFromFU()
        elif namvar == '$FMO:INDAT':
            text=self.FMOIndatFromFU()
        
        
        
        if len(text) <= 0:
            mess='Falied to get '+namvar+' data from FU.'
            lib.MessageBoxOK(mess,'GMSUser:TextDataFromFU')
        else:
            self.jobtitle=molname
            #self.SetCoordTextToInputValDic(text)
        
        if len(text) > 0: self.SetTextDataToInputValDic(namvar,text)
        #
        return

    def SetValueFromFU(self,namvar):
        """ is called from GMSExpert.OnSelectedValue """
        # $DATA:$DATA or $FMO,
        items=namvar.split(':')
        name=items[0]
        group=self.FindGroupNameOfName(name)
        
        #print 'namvar,group',namvar,group
        
        if namvar == '$DATA:$DATA':
            self.SetCoordFromFU()
            return
        
        if group == 'Fragment':
            self.SetFMOValueFromFU(namvar)
            return
        #mess='Can not get "'+namevar+'" data from FU'
        #lib.MessageBoxOK(mess,'GMSUser:SetValueFromFU')
        if namvar == '$STATPT:IFREEZ':
             atmlst=self.GetSelectedAtomsFromFU()
             if len(atmlst) <= 0: return
             natm,text=self.IFREEZTextFromFU(atmlst)
             self.SetInputValue(namvar,text,True)
        
        if namvar == '$STATPT:IACTAT':
             atmlst=self.GetSelectedAtomsFromFU()
             if len(atmlst) <= 0: return
             text=self.IACTATTextFromFU()
             self.SetInputValue(namvar,text,True)
                       
    def FindGroupNameOfName(self,name):
        """ Return group name of name group
        
        :param str name: name
        :return: grpnam(str) - group name
        """
        grpnam=''
        for nam,group in self.namegroupdic.iteritems():
            if nam == name:
                grpnam=group; break
        return grpnam
            
    def SetValueFromFile(self,namvar):
        """ 
        """
        wildcard='input data(*.txt)|*.txt|All(*.*)|*.*'
        filename=lib.GetFileName(None,wildcard,"r",True,"")
        if len(filename) <= 0: return # cancel
        if not os.path.exists(filename):
            mess='file "'+filename+'" not found.'
            lib.MessageBoxOK(mess,'GMSExpert:SetValueFromFile')
            return
        text=''
        #
        f=open(filename,'r')
        for s in f.readlines(): 
            ss=s.strip()
            if ss[:1] == '#': continue
            text=text+s
        f.close()
        #
        text=text.rstrip()
        self.SetTextDataToInputValDic(namvar,text)
        
    def SetValueFromEditor(self,namvar):
        """ This method open text editor and input value is set in the ReturnFromTextEditor method
        """
        namvarval='Edit '+namvar+':TEXT'
        text=''
        self.OpenTextEditor(namvarval,text,'Edit')

    def SetAllFMOValueFromFU(self):
        if not self.model.mol:
            mess='Molecule is not ready in fumodel.'
            lib.MessageBoxOK(mess,'GMSUser(SetAllFMOValueFromFU)')
            return
        # required FMO data
        namvarlst=['$FMOXYZ:$FMOXYZ','$FMOHYB:$FMOHYB','$FMOBND:$FMOBND',
                   '$DATA:$DATA','$FMO:FRGNAM','$FMO:INDAT','$FMO:ICHARG',
                   '$FMO:LAYER']
        wavetypelst=['SCFTYP','DFTTYP','MPLEVL','CITYP','CCTYP','TDTYP']
        
        method=self.beginner.comboboxdic['Method'].GetValue()
        if method == 'MFMO': 
            namvarlst.append('$FMO:LAYER')
            namvarlst.append('$FMO:NLAYER')
        if method == 'TDDFT': namvarlst.append('$FMO:IEXCIT')
        #nlayer=len(self.gmsuser.basislayer)
        #if nlayer > 1: namvarlst.append('LAYER')        
        for namvar in namvarlst: self.SetFMOValueFromFU(namvar)
        #self.tcltit.StValue(self.gmsuser.jobtitle)
        bdalst=self.model.frag.ListBDA() #BAA()
        #if self.inputvaldic.has_key('$FMOBND:$FMOBND'):
        #    print 'self.inputvaldic[$FMOBND]',self.inputvaldic['$FMOBND:$FMOBND']
        #    if self.inputvaldic['$FMOBND:$FMOBND'][1] == self.unsetcolor or \
        if len(bdalst) <= 0:
                self.inputvaldic['$FMOHYB:$FMOHYB']=['INPUT',self.unsetcolor]
                self.inputvaldic['$FMOBND:$FMOBND']=['INPUT',self.unsetcolor]

    def SetFMOValueFromFU(self,namvar):
        """
        
        :param str namandvar: name group:variable name, e.g., $FMO:INDAT or 'all'
        
        text='indat=1,2,3,4,5'
        +varval NBODY [2] <--- set in Method selection
        +varval NLAYER [1]
        *varval NFRAG []
        +varval LAYER  [None,INPUT,FILE,FROMFU]
        *varval FRGNAM [INPUT,FILE,FROMFU]
        *varval INDAT  [INPUT,FILE,FROMFU]
        +varval ICHARG [None,INPUT,FILE,FROMFU]
        +varval MULT   [None,INPUT,FILE,FROMFU]
                IACTAT [True,False] -> 
                BASIS
        """
        if not self.fmoinpobj.IsFUModelReady():
            mess='fumodel is not ready'
            lib.MessageBoxOK(mess,'GMSUser(SetFMOValueFromFU')
            return
        #
        #namvar='$FMOXYZ:$FMOXYZ'
        if namvar == '$FMOXYZ:$FMOXYZ': # or namandvar == 'all':
            molname,text=self.fmoinpobj.FMOXYZTextFromFU()
            self.jobtitle=molname
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)
                self.SetJobTitleToWidget(molname)
        
        #namvar='$FMOHYB:$FMOHYB'
        elif namvar == '$FMOHYB:$FMOHYB': # or namandvar == 'all':           
            #baslst=[self.basis]
            #if self.nlayer > 1: baslst= self.basislayer

            text=self.fmoinpobj.FMOHYBTextFromFU(self.basislayer)
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)
        #namvar='$FMOBND:$FMOBND'
        elif namvar == '$FMOBND:$FMOBND': # or namandvar == 'all':
            #baslst=[self.basis]
            #if self.nlayer > 1: baslst= self.basislayer
            text=self.fmoinpobj.FMOBNDTextFromFU(self.basislayer)
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)
        #namvar='$DATA:$DATA'
        elif namvar == '$DATA:$DATA': # or namandvar == 'all':
            job=self.jobtitle
            basdatlst=[]
            #baslst=[self.basis]
            #if self.nlayer > 1: baslst= self.basislayer
            for bas in self.basislayer:
                if bas == '': continue
                basdat=self.beginner.MakeBasisData(bas)
                basdatlst.append(basdat)
            text=self.fmoinpobj.FMODATATextFromFU(job,basdatlst)
            if len(text) > 0:
                self.SetTextDataToInputValDic(namvar,text)
        #namvar='$FMO:FRGNAM'; nfrgvar='$FMO:NFRAG'
        elif namvar == '$FMO:FRGNAM': # or namandvar == 'all':
            nfrg,text=self.fmoinpobj.FMOFrgnamTextFromFU()
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)
                #self.SetInputValue(namvar,text,True)
                self.SetInputValue('$FMO:NFRAG',str(nfrg),True)     
        elif namvar == '$FMO:INDAT':
            text=self.fmoinpobj.FMOIndatTextFromFU()
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)
        elif namvar == '$FMO:LAYER': # or namandvar == 'all':
            ndat,text=self.fmoinpobj.FMOAttribTextFromFU('layer')
            nlayer=1
            if len(text) > 0:
                nlayer=self.MaxValueInIntegerString(text)
                if nlayer >= 1 and len(text) > 0:
                    text='     LAYER(1)='+text
                    self.SetTextDataToInputValDic(namvar,text)
                    self.SetInputValue('$FMO:NLAYER',str(nlayer),True)
                    self.beginner.SetMethod('MFMO')
                    self.nlayer=nlayer
                    self.beginner.EnableLayerWidgets(True)
                    self.RemoveInputNameAndVals('$BASIS',[])
        elif namvar == '$FMO:ICHARG':
            text=self.fmoinpobj.FMOFrgchgTextFromFU()
            if len(text) > 0: 
                self.SetTextDataToInputValDic(namvar,text)

        #namvar='$FMO:'+var type
        else:
            
        #fmovallst=['INDAT','ICHARG','MULT','LAYER']
        #for val in fmovallst:
        #    namvar='$FMO:'+val
        #    if namandvar == namvar or namandvar == 'all':
            attrib=namvar.split(':')[1].strip()
            ndat,text=self.fmoinpobj.FMOAttribTextFromFU(attrib)
            if ndat > 0: self.SetTextDataToInputValDic(namvar,text)

    def SetFMOPCMData(self):
        mess='Please input $PCM, $PCMCAV, $TESCAV,.. data in "Option" panel'
        lib.MessageBoxOK(mess,'Gamess-user(SetFMOPCMData')
        return
                      
        
    def MaxValueInIntegerString(self,string):
        ivalue=[]
        items=string.split(',')
        for s in items: ivalue.append(int(s))
        maxvalue=max(ivalue) 
        return maxvalue
        
    def GetSelectedAtomsFromFU(self):
        nsel,atmlst=self.model.ListSelectedAtom()
        if nsel <= 0:
            mess='No selected atoms. Please select atoms and try again.'
            lib.MessageBoxOK(mess,'GMSUser(IFREEZTextFromFU')
        return atmlst        
          
    def IFREEZTextFromFU(self,atmlst):
        freezlst=[]
        natm=len(atmlst)
        for i in atmlst:
            freezlst.append(3*i+1)
            freezlst.append(3*i+2)
            freezlst.append(3*i+3)
        header='  IFREEZ(1)='; sep=','; width=-1; colu=5; nw=10
        #text=lib.NumericListToText(frgchglst,header,sep,width,colu,nw)
        text=lib.NumericListToText(freezlst,header,sep,width,colu,nw) 
        text=text.rstrip()
        return natm,text
        
    def IACTATTextFromFU(self,select=True):
        """ select: True for selected atoms
                    False for from mol.atm.active
        """
        if select:
            actlst=self.model.ListTargetAtoms()
        else:
            actlst=[]
            for atom in self.model.mol.atm:
                if atom.active: actlst.append(atom.seqnmb)
        actlst=[x+1 for x in actlst]
        header='  IACTAT(1)='; sep=','; width=-1; colu=5; nw=10
        #text=lib.NumericListToText(frgchglst,header,sep,width,colu,nw)
        text=lib.NumericListToText(actlst,header,sep,width,colu,nw) 
        text=text.rstrip()
        return text
        
    def SetCoordFromFile(self,filename):
        #xyzatm: [[label,natm,atmnam,alt,resnam,chain,6:resnmb,
        #7[fx,fy,fz],focc,fbfc,10elm,chg],...]
        root,ext=os.path.splitext(filename)     
        if ext == '.pdb' or ext == '.ent':
            xyzatm,pdbcon=rwfile.ReadPDBAtom(filename)
        elif ext == '.xyz':
            mess='Read file='+filename
            xyzatm,bond,resfrg=rwfile.ReadXYZAtom(filename)
        if len(xyzatm) <= 0:
            mess='Falied to get coordinate data from file. file='+filename
            lib.MessageBoxOK(mess,'GMSUser:SetCoordFromFile')
            return ''
        #
        text=''
        ff12='%12.6f'; fi4='%4d'; natm=len(xyzatm); form='%0'+str(len(str(natm)))+'d'
        text=text+filename[:70]+'\n'
        text=text+'C1\n'
        i=0
        for atmdat in xyzatm:
            elm=atmdat[10]; an=const.ElmNmb[elm]; san=fi4 % an
            x=ff12 % atmdat[7][0]; y=ff12 % atmdat[7][1]; z=ff12 % atmdat[7][2]
            i += 1
            if self.atomlabelwithnmb: elm=elm+(form % i)
            text=text+4*' '+elm+' '+san+' '+x+' '+y+' '+z+'\n'
        #
        self.jobtitle=filename
         
        ###self.SetCoordTextToInputValDic(text)
        #
        return text

    def SetTextDataToInputValDic(self,namvar,text):
        #self.AddInputName('$DATA')
        #namvar='$DATA:$DATA'
        #namvarval=namvar+':TEXT' #$DATA:$DATA:TEXT'
        items=namvar.split(':')
        name=items[0].strip()
        """
        try: idx=self.inputnamelst.index(name)
        except: self.inputnamelst.append(name)
        try: idx=self.allinputnames.index(name)
        except: self.allinputnames.append(name)
        """
        if not name in self.inputnamelst: self.inputnamelst.append(name)
        if not name in self.allinputnames: self.allinputnames.append(name)
        
        #self.textvaldic[namvarval]=text
        #self.inputvaldic[namvar]=['TEXT',self.setcolor]
        set=True
        if len(text) <= 0: set=False
        self.changed=True
        #self.textvaldic[namvarval]=text
        self.textvaldic[namvar]=text
        #print 'textvaldic in SetTextDataToInputValDic',self.textvaldic
        self.inputvaldic[namvar]=['TEXT',self.setcolor]
        #self.SetTextValue(namvarval,text)
        #self.SetInputValue(namvar,'TEXT',set)
        #
        #self.SetInputData(self.inputnamelst,self.inputvaldic,self.textvaldic)        

    def SetJobTitleToWidget(self,jobtitle):
        #print 'jobtitle in SetJObTitleToWidgte',jobtitle
        self.jobtitle=jobtitle
        if self.mode == 'expert' and self.expertwin: self.expert.tclinfo.SetValue(self.jobtitle)
        if self.beginnerwin: 
            self.beginner.tcltit.SetValue(self.jobtitle)
            self.beginner.tcltit.Refresh()
        
    def SetInputValue(self,namvar,value,set):
        """ Set value to 'inputvaldic' dictionary
        
        :param str varvalnam: 'name:var' string
        :param str value: value string 
        :param bool set: True for set, False for unset (only change value color).
        :example args: '$FMOPRP:IPIEDA','1',True
        """
        textvaltyp=['TEXT','INPUT','FILE','FROMFU']
        #if not self.inputvaldic.has_key(namvar):
        self.UnsetConflictVars(namvar,value)
        #
        #print 'namvar,value,set',namvar,value,set

        items=namvar.split(':')
        name=items[0].strip()
        #if set:
        if not name in self.inputnamelst: self.inputnamelst.append(name)
        if not name in self.allinputnames: self.allinputnames.append(name)
        #
        if not self.IsInputNamVar(namvar):
            #lib.MessageBoxOK('key error:'+namvar,'GMSUser:SetInputValue')
            #return
            items=namvar.split(':'); varlst=[]
            name=items[0].strip(); varlst.append(items[1].strip())
            self.AddInputNameAndVars(name,varlst)
        #self.SetValueToInputNamVar(namvar,value,set)
        if set: color=self.setcolor
        else: color=self.unsetcolor
        # check value type
        valtyp=self.inputvaldic[namvar][0]
        if valtyp in textvaltyp:
            self.textvaldic[namvar]=value # text
            if not set: val='INPUT'
            else: val='TEXT'
            self.inputvaldic[namvar]=[val,color]
        else:
            #print 'Non-TEXT: namvar,val,color',namvar,value,color
            if not set: value=self.GetDefaultValue(namvar)
            self.inputvaldic[namvar]=[value,color]
        
    def RemoveUnsetFromInputNamelst(self,name):
        """ Remove name in inputnamelst and allinputnamelst, if all values are unset.
        
        :param str name: name of name group
        """
        varlst=[]
        if self.varlstdic.has_key(name): varlst=self.varlstdic[name]
        else: return
        
        nset=0
        for var in varlst:
            namvar=name+':'+var
            if self.inputvaldic[namvar][1] != self.unsetcolor: nset += 1
        if nset > 0:
            #try: 
            #    idx=self.inputnamelst.index(name)
            #    del self.inputnamelst[idx]
            #except: pass
            if name in self.inputnamelst: self.inputnamelst.remove(name)
            
            #try:
            #    idx=self.allinputnames.index(name)
            #    del self.allinputnames[idx]
            #except: pass
            if name in self.allinputnames: self.allinputnames.remove(name)
        
    def UnsetConflictVars(self,namvar,value):
        namvarval=namvar+':'+value
        for symbol,namvarvallst in self.conflictdic.iteritems():
            #try: 
            if namvarval in namvarvallst:
                #idx=namvarvallst.index(namvarval)    
                #print 'namvarvallst',namvarvallst
                for namvarval in namvarvallst:
                    items=namvarval.split(':')
                    if len(items) <= 2: continue
                    namv=items[0].strip()+':'+items[1].strip()
                    if namv != namvar: continue
                    #val=items[2].strip()
                    #if val == value:
                    defval=self.GetDefaultNamVarValue(namvar)
                    if defval == '': continue
                    self.inputvaldic[namvar]=[defval,self.unsetcolor]
            #except: pass

    def GetDefaultNamVarValue(self,namvar):
        value=''
        name=namvar.split(':')[0].strip()
        varlst=self.varlstdic[name]
        for var in varlst:
            namv=name+':'+var
            if namv != namvar: continue
            if self.varvaldic.has_key(namvar): value=self.varvaldic[namvar]
        #print 'value in GetDefaultNamVar',value
        return value             
    
    def GetRequiredNames(self,namvar,value):
        """
        :param str namvar: name+variable, e.g., '$CONTRL:RUNTYP'
        :param str value: variable value, e.g., 'OPTIMIZE' for '$CONTRL:RUNTYP'
        :return: reqlst - list of required name group
        """
        reqnamlst=[]
        for namvarval,namelst in self.requireddic.iteritems():
            items=namvarval.split('=')
            namv=items[0].strip()
            ns=namv.find('!')
            if ns >= 0: 
                noteq=True; namv=namv[:ns].strip()
            else: noteq=False
            if namv != namvar: continue
            if len(items) >= 2 and value != '': 
                val=items[1].strip()
                if noteq:
                    if val == value: continue
                else:
                    if val != value: continue
            reqnamlst=reqnamlst+namelst
        #
        return reqnamlst

    def GetSettedNamVarValue(self,namvar):
        val=''    
        if self.inputvaldic.has_key(namvar):
            varvallst=self.inputvaldic[namvar]
            #for varval in varvallst:
            if varvallst[1] != self.unsetcolor:
                val=varvallst[0].strip()
        return val
                
    def GetDefaultValue(self,namvar):
        value=''
        if self.varvaldic.has_key(namvar): 
            val=self.varvaldic[namvar]
            items=self.gmsinpobj.SplitValues(val)
            value=items[0]
        return value
        
    def GetInputNameList(self):
        return self.inputnamelst
    
    def GetNumberOfInputNames(self):
        return len(self.inputnamelst)
    
    def GetNumberOfInputValues(self):
        return len(self.inputvaldic)
    
    def IsInputNamVar(self,namvar):
        if self.inputvaldic.has_key(namvar): return True
        else: return False
    
    def IsInputName(self,name):
        if name in self.inputnamelst: return True
        else: return False
    
    def AddInputNameAndVars(self,name,varlst):
        """
        if 'name' exists, its varlst will be replaced. 
        """    
        if name[:1] != '$': return 
        if len(name) <= 0: return
        #
        #try: idx=self.inputnamelst.index(name)
        #except: self.inputnamelst.append(name)
        if not name in self.inputnamelst: self.inputnamelst.append(name)
        #self.AllInputNames(self.inputnamelst,True)
        # set allinpunames
        for name in self.inputnamelst:
            #try: idx=self.allinputnames.index(name)
            #except: self.allinputnames.append(name)
            if not name in self.allinputnames: self.allinputnames.append(name)
        #
        #print 'inputvaldic{CTRL:MP2 In ADD',self.inputvaldic['$CONTRL:MP2']
        #print 'varlst in AddInputName 0',varlst
        if len(varlst) <= 0: varlst=self.varlstdic[name]
        #print 'varlst in AddInputName 1',varlst
        #valdic=self.gmsinpobj.GetDefaultVarValDic(name,varlst)
        valdic=self.gmsinpobj.DefaultValues([name])
        self.inputvaldic.update(valdic)

        if not self.inpnamvardic.has_key(name): self.inpnamvardic[name]=[]
        if len(varlst) <= 0: varlst=self.varlstdic[name]
        
        self.inpnamvardic[name]=varlst
        #self.inpnamvardic[name].append(name)
        self.inputnamvarlst=self.gmsinpobj.DefaultNamVars([name])
        
    def RemoveInputNameAndVals(self,name,varlst):
        if name[:1] != '$': return
        try: self.inputnamelst.remove(name)
        except: pass
        #
        if len(varlst) == 0: varlst=self.gmsinpobj.varlstdic[name]
        for var in varlst:
            namvar=name+':'+var           
            if self.inputvaldic.has_key(namvar): 
                del self.inputvaldic[namvar]
            if self.textvaldic.has_key(namvar): 
                del self.textvaldic[namvar]
 
    def AllInputNames(self,inputnamelst,add):
        """ store all inputnames
        
        :param bool add: True for add, False for remove
        """
        if add:
            for name in inputnamelst:
                if not name in self.allinputnames: self.allinputnames.append(name) 
                #try: idx=self.allinputnames.index(name)
                #except: self.allinputnames.append(name)
        else:
            for name in inputnamelst:
                if name in self.allinputnames: self.allinputnames.remove(name)
                #try: 
                #    idx=self.allinputnames.index(name)
                #    del self.allinputnames[idx]
                #except: pass

    def ResetAllInputNames(self):
        #print 'resetallinputnames'    
        self.initialnamelst=['$CONTRL','$SYSTEM','$BASIS','$DATA']
        # input group name list
        self.inputnamelst=self.initialnamelst
        # variables in name group
        self.namvarlst=self.gmsinpobj.DefaultNamVars(self.inputnamelst)
        # variables in name group which can be input from GMSExpert_Frm
        self.inpnamvardic=self.SetInputNameVars(self.namvarlst) 
        # Set values to all variables
        self.inputvaldic=self.gmsinpobj.DefaultValues(self.namelst)

        #self.inputnamelst=['$CONTRL','$SYSTEM','$BASIS','$DATA']
        self.allinputnames=self.inputnamelst
        #self.inputvaldic=self.gmsinpobj.DefaultValues(self.inputnamelst) #self.namelst)
       
        #print 'inputvaldic',self.inputvaldic
        self.textvaldic={}
    
    def RemoveInputNameVars(self,name,varlst):
        retmess=''
        if set: color=self.setcolor
        else: color=self.unsetcolor
        if not self.inputvaldic.has_key(namvar):
            retmess='GMSInput(RemoveInputNamVar): namvar "'+namvar+'" is not defined.'
            return
        del self.inputvaldic[namvar]
        return retmess
    
    def ResetInputNames(self,namelst):
        print 'resetinputnames'
        
            
    def ResetInputNameVals(self,name,varlst):
        """
        
        :param str name: name group, e.g., '$CONTRL'
        :param lst varlst: if len(varlst)=0, all variables in the name group are reset
        """
        pass
    
    def SetDataToInputNamVar(self,namvar,valdat):
        """
        
        :param str namvar:
        :param str data: [value,color]
        :SeeAlso: SetInputNameVars
        """
        retmess=''
        if not self.inputvaldic.has_key(namvar):
            retmess='GMSInput(SetValueToInputNamVar): namvar "'+namvar+'" is not defined.'
            return
        self.inputvaldic[namvar]=valdat
        return retmess

    def SetInputNameVars(self,namvarlst):
        """
        
        :param str namvar:
        :param str data: [value,color]
        :SeeAlso: SetInputNameVars
        """
        inpnamvardic={}
        for namelst in namvarlst: # [[$CONTRL,NPRINT...],...]
            if len(namelst) > 0:
                name=namelst[0]
                inpnamvardic[name]=[]
                for i in range(1,len(namelst)):
                    inpnamvardic[name].append(namelst[i])
        return inpnamvardic
                
    def PresetInputnames(self):
        namelst=[]
        for name, value in self.needdic.iteritems():
            if name.find(':') < 0: namelst.append(name)
        return namelst    
    
    def SetInputValuesFromTextEditor(self,inputtext):

        if len(inputtext) <= 0:
            mess='Empty text'
            lib.MessageBoxOK(mess,'GMSUser(SetInputValuesFromTextEditor)' )
            return
        #        
        textlst=inputtext.split('\n')
        inpdatlst,inputvaldic=self.ReadGMSInputText(textlst)        
        self.MakeInputValDic(inpdatlst,inputvaldic)

        self.coordinternal=False
        self.coordfile=True
        #if self.mode == 'beginner': 
        self.beginner.ChangeCoordButtonColor()
        self.beginner.SetUserGroups()
        """ draw the molecular model on fumodel """
        
    def ReadInputFileAndSetInputValues(self,filename):
        if not os.path.exists(filename):
            retmess='GMSInput(ReadInputFile): File not found. file='+filename
            return 'file not found. file="'+filename+'"'
        
        retmess=''
        #retmess,inpdatlst,inputvaldic=self.ReadVarValsInGMSInputFile(filename)    
        #text=self.MakeTextFromGMSInputFile(filename)
        text=''
        f=open(filename,'r')
        for s in f.readlines(): text=text+s   
        f.close()
        # read text from file
        if len(text) <= 0:
            mess='GMSInput(ReadInputFile): File not found. file='+filename
            lib.MessageBoxOK(mess,'GMSUser(ReadInputFileAndSetInputValues)' )
            return
        #
        textlst=text.split('\n')
        #while '' in textlst: textlst.remove('')
        #
        inpdatlst,inputvaldic=self.ReadGMSInputText(textlst)  
        self.MakeInputValDic(inpdatlst,inputvaldic)
        
        if self.inputvaldic.has_key('$FMOXYZ:$FMOXYZ'):
            if self.inputvaldic['$FMOXYZ:$FMOXYZ'][1] != self.unsetcolor:
                #self.CreateNewMolecule(filename)
                molnam=lib.MakeMolNamFromFileName(filename)
                if self.model.molctrl.IsExist(molnam):
                    mess='Molecule name "'+molnam+"' exists in fumodel. Close it and try again."
                    lib.MessageBoxOK(mess,'GMSUser(ReadInputFileAndSetInputValues)')
                    return
                self.model.ReadFiles(filename,True)
                #coord,frgdic=self.ReadFMOInputFile(filename)         
                self.beginner.OnCoordinateFromFU(1)
        
        self.jobtitle=filename
        return retmess

    def FindFragmentVarName(self,namvardic,s):                
        #namvardic={'$FMOXYZ':'$FMOXYZ','FRGNAM(1)=':'FRGNAM','INDAT(1)=':'INDAT',
        #           'ICHARG(1)=':'ICHARG','$FMOBND':'$FMOBND',
        #           'LAYER(1)=':'LAYER','MULT(1)=':'MULT','SCFTYP(1)=':'SCFTYP','DFTTYP(1)=':'DFTTYP',
        #           'MPLEVL(1)=':'MPLEVL','CITYP(1)=':'CITYP','CCTYP(1)=':'CCTYP','TDTYP(1)=':'TDTYP',
        #           'DOMAIN(1)=':'DOMAIN'}
        found=0
        namvar=''; datlst=[]
        for nam,val in namvardic.iteritems():
            ns=s.find(nam)
            if ns >= 0:
                found=1
                namvar=val
                if nam[:1] != '$':
                    s=s.replace(nam,'',1)
                    s=s.replace('$END','')
                    s=s.strip()
                    datlst=lib.SplitStringData(s)
                    while '' in datlst: datlst.remove('')
                break
        #
        if found == 0 and s[:1] == '$': found=-1
        if found == 0 and s.find('=') >= 0: found=-1
        # 
        return found,namvar,datlst
        
    def ReadGMSInputText(self,inputtextlst):
        inpdatlst=[]; inputvaldic={}
        if len(inputtextlst) <= 0: return [],{}
        #
        comstr='!'; namestr=' $'; endstr=' $END'; com='COMMENT'; text='TEXT'
        #
        find=False
        for s in inputtextlst:
            s=s.rstrip()
            #s=s.rstrip()
            s=s.upper()
            s5=s[:5]; s2=s[:2]; s1=s[:1]
            ss=s[:]; ss=ss.lstrip()
            if ss[:3] == '---':
                find=False
                continue
            if s1 == comstr: # keep comment lines
                #if not inputvaldic.has_key(com): inputvaldic[com]=[]
                #s=s.rstrip()+'\n'
                #inputvaldic[com].append(s)
                continue
            if s5.upper() == endstr:
                find=False; continue
            if s2 == namestr:
                find=True; s=s.strip(); items=s.split(' ')
                name=items[0].upper()
                if not inputvaldic.has_key(name): 
                    inputvaldic[name]=[]; inpdatlst.append(name)
                nitems=len(items)
                if nitems > 1:
                    if items[nitems-1].upper() == '$END': 
                        find=False; nitems -= 1
                    for i in range(1,nitems): 
                        item=items[i].strip()
                        if item != '': inputvaldic[name].append(item.upper())
                continue
            if find:
                s=s.strip(); items=s.split(','); nitems=len(items)
                if nitems > 1:
                    if items[nitems-1].upper() == '$END': 
                        find=False; nitems -= 1
                    for i in range(nitems): 
                        item=items[i].strip()
                        if item != '': inputvaldic[name].append(item.upper())              
                if nitems == 1: inputvaldic[name].append(s+'\n')
        # Note: The following two lines work for '$DATA' but may not be reliable for others 
        for name,varval in inputvaldic.iteritems():
            if len(varval) <= 0: continue
            if name == '$DATA' or varval[0].find('=') < 0: varval[0]='TEXT='+varval[0] #.rstrip()+'\n'       
        """
        if inputvaldic.has_key('$FMOXYZ'):
            print '$FMOXYZ is treated',name
            text=inputvaldic['$FMOXYZ']
            inputvaldic['$FMOXYZ']=text[-1].rstrip()
        """
        return inpdatlst,inputvaldic

    def MakeInputValDic(self,inpdatlst,inputvaldic):
        """ 
        
        """
        savetext=copy.deepcopy(self.textvaldic)
        #
        newinputvaldic=self.gmsinpobj.DefaultValues(inpdatlst)
        newinputnamelst=inpdatlst
        newtextvaldic={}
        self.inputfileinfo=''
        for name,varvallst in inputvaldic.iteritems():
            # text data. case $DATA:$DATA
            val=varvallst[0]
            if val[:5] == 'TEXT=':
                if val[5:6] == '!': continue
                namvar=name+':'+name
                namvarval=namvar+':'+val
                text=''
                for varval in varvallst:
                    if varval[:1] == '!': continue
                    text=text+varval             
                text=text.replace('TEXT=','',1)
                newtextvaldic[namvar]=text.rstrip()
                self.inputfileinfo=varvallst[0].strip().replace('TEXT=','',1) #[:120]
                val=val.replace('TEXT=','',1)
                newinputvaldic[namvar]=['TEXT',self.setcolor] #[val,self.needcolor]
            # namvar=val and namvar=TEXT type
            else: 
                varvaltxt=[]; txtidx=len(varvallst)*[False]
                i=-1
                for varval in varvallst: 
                    varval=varval.replace('$END','')
                    varval=varval.replace('$end','')
                    items=varval.split('=',1)
                    nitems=len(items)
                    #if nitems == 1: continue
                    if nitems == 2:
                        iscomma=items[1].find(',')
                        i += 1
                        varvaltxt.append(varval)
                        if iscomma < 0: txtidx[i]=False
                        else: txtidx[i]=True                   
                    elif nitems == 1:
                        txt=items[0]; lastdat=varvaltxt[i].rstrip()
                        #if len(varvaltxt[i]) > 0 and varvaltxt[i][-1] != ',': txt=','+items[0]
                        if len(lastdat) > 0 and lastdat[-1] != ',': txt=','+items[0]
                        varvaltxt[i]=varvaltxt[i]+'  '+txt+'\n'
                        txtidx[i]=True
                i=-1
                for varval in varvaltxt: 
                    i += 1
                    items=varval.split('=',1)
                    nitems=len(items)
                    if nitems != 2: continue # no variable name
                    namvar=name+':'+items[0].strip()
                    val=items[1].strip()
                    if txtidx[i]:
                        vars=namvar.split(':')
                        varnam=vars[0].strip()
                        if len(vars) > 1: varnam=vars[1].strip()
                        ns=namvar.find('(')
                        if ns >= 0: namvar=namvar[:ns]; namvar=namvar.strip()
                        val='  '+varnam+'='+val
                        #val=val.replace('$END\n','')
                        newtextvaldic[namvar]=val.rstrip()
                        newinputvaldic[namvar]=['TEXT',self.setcolor] #[val,self.needcolor]
                    else: 
                        newinputvaldic[namvar]=[val,self.setcolor]
        #
        self.inputnamelst=newinputnamelst
        self.inputvaldic=newinputvaldic
        self.textvaldic=newtextvaldic
        self.allinputnames=self.inputnamelst

    def OpenExampleFile(self,case):
        """ 
        :param str case: 'GMS' for GAMESS tests example, 'FMO' for FMO example
        """
        #self.examdir='c://gamess.64//tests'
        
        #if self.mode == 0: 
        #    title='GMSBeginner_Frm:OpenExamplefile'
        #    try: parwin=self.beginner
        #    except:parwin=self.expert
        #else: 
        #    title='GMSExpert_Frm:OpenExamplefile'
        #    try: parwin=self.expert
        #    except: parwin=self.beginner
        #print 'Entered in OpenExampleFile, mode',self.mode
        prvdir=os.getcwd()
        if self.mode == 'beginner': parwin=self.beginner
        else: parwin=self.expert
        title='OpenExamoleFile'
        if case == 'GMS':
            if not os.path.isdir(self.gmsexamdir):
                mess='Example directory "'+self.gmsexamdir+'" does not exist.'
                lib.MessageBoxOK(mess,title)
                return
            examdir=self.gmsexamdir
        elif case == 'FMO':
            if not os.path.isdir(self.fmoexamdir):
                mess='Example directory "'+self.fmoexamdir+'" does not exist.'
                lib.MessageBoxOK(mess,title)
                return
            examdir=self.fmoexamdir
        
        ext=['.inp']
        examfiles=lib.GetFilesInDirectory(examdir,ext)
        if len(examfiles) <= 0:
            mess='No examlpe files in directory "'+examdir
            lib.MessageBoxOK(mess,title)
            return
        # set coordinate flags
        self.coordinternal=False
        self.coordfile=True
        try: self.beginner.ChangeCoordButtonColor()
        except: pass
        #
        menulst,tiplst,self.gmsexamlst=self.MakeInputExampleList(examfiles)
        # open menu
        menulst=['<close>','']+menulst
        tiplst=['','']+tiplst
        winpos=wx.GetMousePosition()
        winsize=[420,200]
        exammenu=subwin.ListBoxMenu_Frm(parwin,-1,winpos,winsize,
                 self.LoadSelectedSelectExample,menulst,tiplst=tiplst)
        #print 'tiplst',tiplst
        os.chdir(prvdir)

    def MakeInputExampleList(self,examfiles):
        """ Make list of exqmple input file names
        
        :param lst examfiles: example input file list
        :return: menulst,tiplst,gmsexamls:[[examtitle, file],...]
        examtitle: 'Exam01(The first line)'+'comment in the second line in the file'
        """
        gmsexamlst=[]; menulst=[]; tiplst=[]
        for file in examfiles:
            tip=''
            f=open(file,'r')
            i=0; title=''; com=''
            for s in f.readlines():
                s=s.strip()
                if i == 0: 
                    title=s[1:].replace('.','').strip()
                    title=title.replace(' ','').upper()
                elif i == 1: com=s[1:].strip()
                i += 1
                tip=tip+s+'\n'
            tip=tip.rstrip()
            tiplst.append(tip)
            item=title+':'+com[:80]
            gmsexamlst.append([item,file])
            menulst.append(item)
            f.close()    
        return menulst,tiplst,gmsexamlst

    def LoadSelectedSelectExample(self,example,menulabel):
        if example == '<close>' or example == '': return
        #
        curdir=os.getcwd()
        example=example.strip()
        filename=''
        for exam, file in self.gmsexamlst:
            if exam == example: filename=file
        if len(filename) <= 0:
            mess='Failed to get example file for exam='+example
            lib.MessageBoxOK(mess,'GMSExpert_Frm:LoadSelectedExample')
            return
        mess='Open example input='+example+'\n'
        mess=mess+'example input file='+filename
        try: self.model.ConsoleMessage(mess)
        except: pass
        #        
        if self.mode == 'beginner': self.beginner.LoadGAMESSInputFile(filename)
        #if self.mode == 1: self.expert.OpenInputFile(filename,0)
        if self.mode == 'expert': self.expert.LoadGMSInputFile(filename)
        os.chdir(curdir)
        
    def RemoveInputName(self,name,varlst):
        if name[:1] != '$': return
        self.RemoveInputNameAndVals(name,varlst)

    def MakeCurrentText(self):
        """ View current input data
        """
        if self.inputvaldic.has_key('$FMO:NFRAG'):
            if self.inputvaldic['$FMO:NFRAG'][1] == self.setcolor:
                self.SetAllFMOValueFromFU() 

        text=self.gmsinpobj.MakeInputDataText(self.allinputnames,
                                              self.inputvaldic,self.textvaldic)
        return text

    def ViewCurrentData(self):
        """ View current input data
        """
        if self.texteditor:
            try: self.editor.SetFocus()
            except: pass
            return
        """
        if self.inputvaldic.has_key('$FMO:NFRAG'):
            if self.inputvaldic['$FMO:NFRAG'][1] == self.setcolor:
                self.SetAllFMOValueFromFU() 

        text=self.gmsinpobj.MakeInputDataText(self.allinputnames,
                                              self.inputvaldic,self.textvaldic)
        """
        text=self.MakeCurrentText()
        #label='View input data: '+self.readfilename
        title='View current input data'
        self.OpenTextEditor(title,text,'Edit')
        self.texteditor=True

    def RemoveParenthesis(self,text):
        if text.strip() == '[]': return '' 
        if text[:1] == '[': text=text[1:]
        if text[-1] == ']': text=text[:-1]
        text=text.strip()
        return text
         
    def OpenTextEditor(self,title,text,mode):
        ##if len(mode) == 0: mode='Edit'
        retmethod=self.ReturnFromTextEditor
        winpos=wx.GetMousePosition()
        winsize=[480,300]
        parent=self.beginner
        if self.mode == 'expert': parent=self.expert
        self.texteditor=True
        self.editor=subwin.TextEditor_Frm(parent,-1,winpos,winsize,title,text,
                                          retmethod,mode=mode)
    
    def ReturnFromTextEditor(self,title,text,cancel):
        """ Receive return value form 'TextEditor_Frm'
        
        :param str title: menu title
        :param str text: text data
        """        
        self.texteditor=False
        #
        return
        
        if cancel: return
        #
        namvarval=title.split(' ',1)[1].strip()
        
        if title[:23] == 'View current input data':
            #print 'Return from view current input data'
            self.SetInputValuesFromTextEditor(text)
        
        elif title[:4] == 'Edit':
            items=namvarval.split(':')
            name=items[0]
            namvar=items[0]+':'+items[1]
            if len(text) > 0:
                self.SetTextDataToInputValDic(namvar,text)
                self.changed=True
                self.expert.SetValueToGridCell('TEXT',self.setcolor)
            else:
                if self.textvaldic.has_key(namvar): del self.textvaldic[namvar]
                if self.inputvaldic.has_key(namvar): self.inputvaldic[namvar]=['INPUT',self.unsetcolor] 
                self.expert.SetValueToGridCell('INPUT',self.unsetcolor)
            ### does not work ! self.expert.SetDataToGridTable(name)
        else: pass
        savefile=self.editor.GetSaveFileName()        
        self.gmsinputfile=savefile
        
    def DeleteAllGAMESSScratch(self):
        for file in glob.glob(os.path.join(self.gmsscrdir,"*.*")):
            base,ext=os.path.splitext(file)
            if ext in self.gmsscrextlst:
                try: 
                    os.remove(file)
                    mess=file+' in '+self.gmsscrdir+' has been deleted.'
                    self.model.ConsoleMessage(mess)
                except: pass
    
    def DeleteGAMESSScratch(self,basename):
        for ext in self.gmsscrextlst:
            file=os.path.join(self.gmsscrdir,basename+ext)
            if os.path.exists(file):
                try: 
                    os.remove(file)
                    mess=file+' in '+self.gmsscrdir+' has been deleted.'
                    self.model.ConsoleMessage(mess)
                except: pass
                      
    def RunGAMESS(self,parent,check=True):
        """ Run GAMESS
        
        :param obj parent: parent object for execution shell to be created in 
        subwin.ExeProg_Frm
        """ 
        gmsinputfile=self.gmsinputfile
        if gmsinputfile == '':
            mess='The input file is not created.'
            lib.MessageBoxOK(mess,'GMSUser(RunGAMESS')
            return
        if not os.path.exists(gmsinputfile):
            mess="Input file '"+gmsinputfile+"' not found."
            lib.MessageBoxOK(mess,"")
            return                              
        self.gmsoutputfile=gmsinputfile.replace('.inp','.out')
        
        if check:
            if os.path.exists(self.gmsoutputfile):
                retcode=lib.MessageBoxYesNo(self.gmsoutputfile+" exsists. Delete it?","")
                if not retcode: return
            #if dlg == wx.NO: 
            #    dlg.Destroy(); return
        #self.inputfilelst.append(self.gmsinputfile)
        #self.outputfilelst.append(self.gmsoutputfile) 
        self.cudir=os.getcwd()
        if self.SetExecInputFile(self.gmsinputfile):
            ###self.OpenExePrgWin(parent)
            """
            gmspath=lib.GetProgramPath(self.prgfile,"GAMESS","program") 
            gmsitems=gmspath.split(' ')
            print 'gmspath',gmspath
            print 'gmsitems',gmsitems
            """
            if self.rungmscmd == "":
                lib.MessageBoxOK("GAMESS is not found. Please set program path and command from 'Setting' menu.","")   
                return
    
            rungmscmd=self.rungmscmd.replace('$ncores',self.cores)
            #print 'rungmscmd',rungmscmd
    
            self.ExecuteGAMESS(rungmscmd,gmsinputfile,self.inpfilecopylst)           
            #self.gmsgeginner.runbt.Disable()
            #self.gmsexpert.runbt.Disable()
    def SetExecInputFile(self,filename):
        output=filename.replace('.inp','.out')
        if output in self.outputfilelst:
            mess='There is input/output file with the same name as "'+filename+'". Please change the file name.'
            lib.MessageBoxOK(mess,'GMSUser(SetExecInputFile')
            return False
        if not filename in self.inputfilelst: self.inputfilelst.append(filename)
        return True
    
    def SetInputFileForRun(self,filename):
        if not os.path.exists(filename):
            mess='File "'+filename+'" does not exist.'
            lib.MessageBoxOK(mess,'GMSUser(SetInputFileForRun')
            return
        self.gmsinputfile=filename
        
    def GetExecInputFileList(self):
        return self.inputfilelst
    
    def GetExecOutputfileList(self):
        return self.outputfilelst
    
    def SetExecOutputFile(self,filename):
        self.outputfilelst.append(filename)
    
    def SetExecOutputOnDispaly(self,on):
        stat='on'
        if not on: stat='off'
        try:
            self.exeprgwin.SetOutputOnDisplay(on)
            mess='Turn '+stat+' output on display in ExecProgWin'
        except:
            mess='Failed to turn '+stat+' output on display in ExeProgWin' 
        try: self.model.Message2(mess)
        except: pass
    
    def OpenExecBatchWin(self):
        if self.openexebatchwin:
            self.execbatwin.SetFocus()
            return
        joblst=[]
        for file in self.createdinputfilelst:
            outfile=file.replace('.inp','.out',1)
            if not outfile in self.outputfilelst: joblst.append(file)
        #
        self.execbatwin=subwin.ExecuteBatchJob_Frm(self.beginner,self.ExecuteBatch,
                        prgname='GAMESS',joblst=joblst,onclose=self.CloseExecuteBatch)
        self.openexebatchwin=True
        
    def ExecuteBatch(self,inpfilelst):
        print 'inpfle lst',inpfilelst
        if len(inpfilelst) <= 0:
            mess='No input files are selected for compute.'
            lib.MessageBoxOK(mess,'')
            return
        if self.mode == 'beginner': parent=gmsuser.beginner
        elif self.mode == 'expert': parent=gmsuser.expert
       
        for inpfile in inpfilelst:
            self.gmsinputfile=inpfile
            self.RunGAMESS(parent)
    
    def CloseExecuteBatch(self):
        self.openexebatchwin=False
            
    def OpenExePrgWin(self,parent):
        """ Create instance of subwin.ExeProg_Frm class
        
        :param obj parent: parent object
        """
        #winlabel='ExecProgWin'
        #if self.winctrl.GetWin(winlabel): return
        #if self.mode == 'beginner':
        #    if self.beginner.openexeprgwin: return
        #elif self.mode == 'expert': 
        #    if self.expert.openexeprgwin: return
        title="Run GAMESS"
        if self.flags.Get(self.exewinlabel): 
            self.exeprgwin.SetFocus()
            return
        #if self.openexeprgwin: return
        #self.winlabel='ExecProgWin'
        winpos=[0,0]; winsiz=[750,300]
        self.exeprgwin=subwin.ExecProg_Frm(parent,-1,self.model,winpos,winsiz,title,
                                           self.exewinlabel,onclose=self.OnCloseExePrgWin)
        self.exeprgwin.Show()
        #self.openexeprgwin=True
        self.flags.Set(self.exewinlabel,True)
        #if self.mode == 'beginner': self.beginner.openexeprgwin=True
        #else: self.expert.openexeprgwin=True    
    def OnCloseExePrgWin(self):
        
        self.flags.Set(self.exewinlabel,False)
        try:
            mess='Exec Program Window was closed at '+lib.DateTimeText()
            self.model.ConsoleMessage(mess)
        except: pass
        try:
            joblst=self.exeprgwin.GetCancelledJobList()
            if len(joblst) > 0:
                mess='Cancelled jobs:\n'
                for txt in joblst: mess=mess+txt+'\n'
                mess=mess[:-1]
                self.model.ConsoleMessage(mess)
        except: pass
        try:
            joblst=self.exeprgwin.GetKilledJobList()
            if len(joblst) > 0:
                mess='Killed jobs:\n'
                for txt in joblst: mess=mess+txt+'\n'
                mess=mess[:-1]
                self.model.ConsoleMessage(mess)
        except: pass
        try:
            joblst=self.exeprgwin.GetDoneJobList()
            mess='Executed jobs:\n'
            if len(joblst) > 0:                   
                for txt in joblst: mess=mess+txt+'\n'
                mess=mess[:-1]
            else: mess=mess+'No job was executed.'
            self.model.ConsoleMessage(mess)          
        except: pass
            
        
    def ExecuteGAMESS(self,rungmscmd,inpfile,inpfilecopylst): 
        """ Excute exeprgwin.ExecuteProgram method to run GAMESS
        
        :param str prgfile: a file written program path, args, etc.
        (e.g. 'FUPATH/Programs/gamess/gamesspath.win' file)
        :param str inpfile: input file name
        :param lst inpfilecopylst: list for store input file name coped to GAMESSPATH
        """
        self.prvdir=os.getcwd()
        
        title='ExecuteGAMESS'
        #self.gmspath=gmspath
        self.jobnmb += 1
        plt=[]; prg=[]; arg=[] 
        wrkdir=""
        prgtxt=rungmscmd
        items=prgtxt.split(' ',1)
        #print 'items',items
        
        prgnam=items[0].strip() #prgtxt[:ns]
        prgnam=os.path.expanduser(prgnam)
        base,ext=os.path.split(prgnam)
        self.gmsdir=os.path.expanduser(base)
        #
        argtxt=items[1].strip() #prgtxt[ns+1:]
        #print 'prgnam,self.gmsdir,argtxt',prgnam,self.gmsdir,argtxt
        # copy input file into gamess directory if needed
        #    
        if self.mode == 'beginner': 
            parent=self.beginner
            self.openexeprgwin=self.beginner.openexeprgwin
        elif self.mode == 'expert': 
            parent=self.expert
            self.openexeprgwin=self.beginner.openexeprgwin
            
        self.OpenExePrgWin(parent)
        #    
        self.gmsoutputfile=inpfile.replace('.inp','.out')
        #if os.path.exists(self.gmsoutputfile):   
        #    retcode=lib.MessageBoxYesNo(self.gmsoutputfile+" is already exsist. Delete it?","")
        #    print 'retcode',retcode
        #    if not retcode: return   
        ###self.OpenExePrgWin()
        #
        base,ext=os.path.split(inpfile)
        self.gmsinputtmp=os.path.join(self.gmsdir,ext) 
        #self.gmsinputtmp=ext       
        #
        tmp=os.path.normcase(self.gmsinputtmp)
        tmp=os.path.expanduser(tmp)
        inp=os.path.normcase(inpfile)
        if os.path.normpath(tmp) != os.path.normpath(inp):
            try:
                shutil.copyfile(inpfile,self.gmsinputtmp)
                inpfilecopylst.append(self.gmsinputtmp)
            except:
                lib.MessageBoxOK("Failed to copy input file."+tmp+","+inp,"")
                return               
        if prgnam.find("runwingms") >= 0: self.wingamess=True
        else: self.wingamess=False
        #        
        outfile=self.gmsoutputfile
        head,tail=os.path.split(self.gmsinputtmp)
        
        argtxt=argtxt.replace('$inputfile',tail) #self.gmsinputtmp)        
        # delete scratch files
        
        scrfil,exe=os.path.splitext(tail)
        tmp=os.path.join(self.gmsscrdir,scrfil+".dat")
        if self.wingamess:
            if os.path.exists(tmp) and not os.access(tmp,os.W_OK):
                mess="Can not remove GAMESS scratch file:"+tmp1+". It may be used in other process."
                mess=mess+" Please delete it by hand and try again."
                lib.MessageBoxOK(mess,"")
                return        
        else: self.DeleteGAMESSScratch(scrfil)
        #
        prg.append(prgnam)
        arg.append(argtxt)
        #plt.append({})
        pltdic={};
        #if run == 'optimization':
        #    title='Optimization ['+self.molnam+']'
        #    if self.pltene:
        #        pltdic={'fromkw':"ITER EX",'tokw':"",'xitemno':0, 'yitemno':1,
        #                'title':title,'xlabel':'iterations','ylabel':'energy in a.u.'} 
        #    if self.pltgrd:
        #        pltdic={'fromkw':"Iter",'tokw':"???",'xitemno':0, 'yitemno':2,
        #                'title':title,'xlabel':'iterations','ylabel':'grad in a.u.'}
        #else: # single point
        #    title='Single point ['+self.molnam+']'
        #    if self.pltene:
        #        pltdic={'fromkw':"ITER EX",'tokw':"",'xitemno':1, 'yitemno':4,
        #                'title':title,'xlabel':'iterations','ylabel':'energy in a.u.'} 
                    
        plt.append(pltdic)   
        #
        jobid="gamess"
        if self.wingamess: jobid="wingamess"
        wrkdir=os.path.expanduser(self.gmsdir)
        self.pdir=wrkdir
        job=[jobid,prg,arg,plt,wrkdir,outfile]
        #
        if not self.exeprgwin.GetComputeStatus():
            mess="Running ... "+jobid+" starts at "+lib.DateTimeText()+" with input file="+self.gmsinputfile
            #self.model.Message(mess,0,"")       
            self.model.ConsoleMessage(mess)
            self.exeprgwin.SetStatusText(mess,0)
            #
            self.prvdir=os.getcwd()
            self.exeprgwin.ClearJobQueue()
            self.exeprgwin.SetJobInQueue(job)
            self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,outfile)
            #
        else:       
            mess="A program is running. This job will be executed later.\n"
            mess=mess+"Put on queue ... "+jobid+"  at "+lib.DateTimeText()+" with input file="+self.gmsinputfile
            #lib.MessageBoxOK(mess,"")
            try: self.model.ConsoleMessage(mess)
            except: lib.MessageBoxOK(mess,"")
            
            self.exeprgwin.SetJobInQueue(job)
        
    def ThreadJobEnded(self,jobnam,jobcmd,killed):
        #self.exeprgwin.SetStatusText('',0)
        if jobnam == "gamess" or jobnam == "wingamess":
            """
            filename=self.inpfilecopylst[0]
            try:
                os.remove(filename)
                del self.inpfilelst[0]
            except: pass    
            """
            if jobnam == "wingamess":
                try:
                    # copy output file
                    base,name=os.path.split(self.gmsoutputfile)
                    wingmstmp="C:/wingamess/"+name
                    shutil.copyfile(wingmstmp,self.gmsoutputfile)
                    os.remove(wingmstmp)
                except:
                    mess="Failed to get output file of WinGamess."
                    lib.MessageBoxOK(mess,"")
                
                if os.path.exists(self.gmsoutputfile):
                    self.exeprgwin.AppendTextFromFile(self.gmsoutputfile)
                
            os.chdir(self.prvdir)
            
            if killed: mess=jobnam+" was killed at "
            else: mess=jobnam+" ended at "
            mess=mess+lib.DateTimeText()+".\n"
            mess=mess+'cmd='+jobcmd+".\n"
            mess=mess+'output='+self.gmsoutputfile
            #self.model.Message(mess,0,"")
            self.model.ConsoleMessage(mess)
            #winlabel='ExePrgWin'
            if not killed: self.SetExecOutputFile(self.gmsoutputfile)
            #self.openexeprgwin=False
        os.chdir(self.prvdir)

    def OpenSettingGAMESSPanel(self,parent):
        if parent.gmssetwin: return
        winpos=parent.GetPosition()
        prgnam="GAMESS"
        item=['program','argument']
        remark=['c:\\gamess.64\\','version 11']
        self.gmssetwin=SetPathAndCmdForGAMESS_Frm(parent,-1,winpos,self.prgfile,
                                                  prgnam,item,remark)
        self.gmssetwin.SetProgramPath()
        parent.gmssetwin=True
        # get new path
        self.gmspath,self.gmscmd,self.gmsarg,self.gmsscr,self.gmstests= \
            self.gmssetwin.GetGAMESSPathAndCMD()     

    def OpenInputFile(self,filename):
        """
        
        :param str filename: file name
        """
        retmess=self.ReadInputFileAndSetInputValues(filename)
        #retmess,inpdatlst,inputvaldic=rwfile.ReadGMSInputFile(filename)    
        #if len(inputvaldic) <= 0: return
        
        #if not os.path.exists(filename):
        if len(retmess) > 0:
                mess='File not found. file='+filename
                lib.MessageBoxOK(mess,'OpenInputFile')
                return
        #self.gmsinpobj.inputnamelst,self.gmsinpobj.inputvaldic,self.textvaldic= \
        #        self.gmsinpobj.MakeInputValDic(inpdatlst,inputvaldic,case)

        self.inputfileinfo=self.gmsinpobj.GetInputFileInfo()
        self.jobtitle=self.inputfileinfo
        head,tail=os.path.split(filename)
        self.jobtitel=tail
        
        self.SetJobTitleToWidget(filename[:70])
        
        self.coordinternal=False
        self.coordfile=True

    def HelpMessage(self):
        mess='Input variable definition files are in FUDATASET/Programs/'
        mess=mess+'gamess/gamessdoc/inputdoc-txt/'
        lib.MessageBoxOK(mess,'gamess-user.py help message')
           
class GMSExpert_Frm(wx.Frame):
    #def __init__(self,mdlwin,id,gmsuser,mode,namvarlst,inputvaldic,textvaldic,gmsdoc,
    def __init__(self,mdlwin,id,gmsuser,mode,inputnamelst,
                 winpos=[-1,-1],winsize=[]): #winsize=[300,400]):
        """ 
        
        :param int mode: 0 for input and 1 for manual mode
        :param lst gmsdoc: gamess inputdoc data. 
        :seealso: ReadGMSInputDocText() static method for gmsdoc
        """
        title='GAMESS Assist For Expert'
        if mode == 0: title='Option Inputer'
        winpos=winpos
        if len(winpos) <= 0 and mdlwin:
            try: 
                [x,y]=mdlwin.GetPosition()
                [w,h]=mdlwin.GetSize()
                winpos=[x+w,y+20]
            except: winpos=winpos
        if len(winsize) <= 0: winsize=lib.WinSize([300,400])
        #if fu:
        #if const.SYSTEM == const.MACOSX: winsize=(275,445)
        if not mdlwin:
            wx.Frame.__init__(self,None,id,title,pos=winpos,size=winsize,
                              style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER) #|wx.FRAME_FLOAT_ON_PARENT)        #
        else:
            wx.Frame.__init__(self,mdlwin,id,title,pos=winpos,size=winsize,
                              style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)        #
        #
        self.gmsuser=gmsuser
        self.gmsinpobj=self.gmsuser.gmsinpobj
        self.mdlwin=mdlwin
        self.icon=None
        self.model=None
        if self.mdlwin: self.model=self.mdlwin.model
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        self.winsize=winsize
        # control flag for 'lib.ListBoxMenu_Frm' instance

        self.mode=mode
        
        #self.openexeprgwin=False
        #self.mode=1
        # Menu deleted
        if self.mode == 'expert':
            self.menubar=self.ExpertMenuItems()
            self.SetMenuBar(self.menubar)
            # statusbar
            #self.statusbar=self.CreateStatusBar()
            self.statusbar=self.CreateStatusBar()
            #self.statusbar.SetStatusText('Open mode: '+self.mode)
            self.openexeprgwin=self.gmsuser.openexeprgwin
        # 
        self.fontheight=self.gmsuser.fontheight
        self.setcolor=self.gmsuser.setcolor
        self.unsetcolor=self.gmsuser.unsetcolor
        self.needcolor=self.gmsuser.needcolor
        #
        self.panelbgcolor="light gray"
        self.maxlistboxmenuheight=400
        # need modification for text data e.g., $DATA
        
        # variavles for keeping input data from GMSExpert_Frm
        gmsdoc=self.gmsuser.gmsdoc
        #self.ExtractGMSDocData(gmsdoc)
        # text type data
        ###self.textvaldic=self.gmsuser.textvaldic #{}
        # variable=value type data
        ###self.inputvaldic=self.gmsuser.inputvaldic
        # input group name list
        self.inputnamelst=inputnamelst #self.gmsuser.inputnamelst
        #print 'inputnamelst',inputnamelst
        #print 'inpnamvardic',self.gmsuser.inpnamvardic
        #print 'inputvaldic[$CONTRL:MP2',self.gmsuser.inputvaldic['$CONTRL:MP2']
        # variables in group name allowed to input from the GMSExpert_Frm
        ###self.inpnamvardic=self.gmsuser.inpnamvardic
        
        self.curname=self.inputnamelst[0]
        #print 'inputnamelst',self.inputnamelst
        # need modification for text data e.g., $DATA
        """ #just for debug
        self.gmsuser.inpnamvardic['$DATA']=['$DATA']
        textval='[INPUT,FILE]'
        textval='[INPUT,FILE,FROMFU]'
        self.gmsuser.inputvaldic['$DATA:$DATA']=textval
        """ #end comment
        
        self.inputfileinfo=self.gmsuser.jobtitle
        self.readfilename=''
        self.writefilename=''
        #  
        #inputnamelst=['$CONTRL','$DATA']
        #self.namvarlst=namvarlst # form argument. ['RHF','RHF-D','DFT','DFT-D','MP2']
        #self.inpnamvardic=self.gmsuser.inpnamvardic
        #if len(self.namvarlst) <= 0:
        #    self.inputnamelst=self.gmsuser.DefaultInputNames()
        ###print 'namvarlst in GMSExpert',namvarlst
        
        ####if len(namvarlst) > 0: 
        ###    self.inputnamelst=namvarlst
        #else:
        #=self.SetInputNameVars(self.namvarlst)
        
        self.addnamelst=['None']+self.gmsuser.grouplst
        #self.inputvaldic=self.DefaultValues()
        
        ##self.curname=self.gmsuser.curname
        self.donenamedic={}
        self.donenamedic[self.curname]=True
        self.curvar=''; self.curval=''        
        self.openlistboxmenu=False
        self.selectedrow=0
        self.selectedcol=0
        self.undolst=[]
        #
        self.ctrlpanel=None
        self.inputpanel=None
        self.CreatePanel()
        self.OnSelected(1)
        #
        self.wingamess=False
        self.gmsinputfile=self.gmsuser.gmsinputfile
        self.savgmsinputfile=self.gmsinputfile
        self.jobnmb=0
        self.inpfilecopylst=[]
        self.gmssetwin=False
        self.madeinput=self.gmsuser.madeinput
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_MENU,self.OnExpertMenu)    
        #
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)
        self.Show()

    def CreatePanel(self):
        winsize=self.GetClientSize()
        width=winsize[0]; height=winsize[1]
        panpos=(-1,-1)
        panheight=winsize[1] #-35
        # panel
        self.panel=wx.Panel(self,-1,pos=panpos,size=winsize)
        self.panel.SetBackgroundColour(self.panelbgcolor)
        yloc=0
        #
        if self.mode == 'expert':
            panheight=winsize[1]-35
            xloc=10; yloc=5
            sttit=wx.StaticText(self.panel,-1,"title:",pos=(xloc,yloc),size=(30,20)) 
            sttit.SetToolTipString('Input job title and hit "ENETR"')  
            self.tclinfo=wx.TextCtrl(self.panel,-1,self.gmsuser.jobtitle,pos=(xloc+35,yloc),size=(width-55,25),
                                    style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
            yloc += 30
            wx.StaticLine(self.panel,pos=[0,yloc],size=[winsize[0],2],style=wx.LI_HORIZONTAL)
            yloc += 5
        #self.tclinfo.Bind(wx.EVT_TEXT_ENTER,self.OnPropertyInput)
        self.ctrlpanpos=[0,yloc] #[0,0]
        ctrlpanwidth=100 # 80
        self.ctrlpansize=[ctrlpanwidth,panheight-yloc]
        self.CreateCtrlPanel(self.ctrlpanpos,self.ctrlpansize)
        #
        wx.StaticLine(self.panel,pos=[ctrlpanwidth+7,yloc],size=[2,panheight-yloc],style=wx.LI_VERTICAL)
        #
        inpxloc=ctrlpanwidth+20
        inppanwidth=width-inpxloc
        inppanpos=[inpxloc,yloc] #[inpxloc,0]
        inppansize=[inppanwidth,panheight-yloc]
        self.CreateInputerPanel(inppanpos,inppansize)
        #
        if self.mode == 'expert':
            yloc=height-35
            wx.StaticLine(self.panel,pos=[0,yloc],size=[width,2],style=wx.LI_HORIZONTAL)
            #wx.StaticLine(self.panel,pos=[90,yloc],size=[2,height-yloc],style=wx.LI_VERTICAL)
            yloc += 8
            btnrun =wx.ToggleButton(self.panel,-1,"RunGMS",pos=[10,yloc],size=(55,20))        
            btnrun.Bind(wx.EVT_TOGGLEBUTTON,self.OnRunGAMESS)
            btnrun.SetToolTipString('Run GAMESS after saving input data')  
            wx.StaticLine(self.panel,pos=[75,yloc-10],size=[2,yloc+30],style=wx.LI_VERTICAL)            
            btnview =wx.ToggleButton(self.panel,-1,"View",pos=[90,yloc],size=(50,20))        
            btnview.Bind(wx.EVT_TOGGLEBUTTON,self.OnView)     
            btnview.SetToolTipString('View current input data on memory')  
            btnsav =wx.Button(self.panel,-1,"Save",pos=[155,yloc],size=(50,20))        
            btnsav.Bind(wx.EVT_BUTTON,self.OnSave)
            btnsav.SetToolTipString('Save input data on file')  
            btncls =wx.Button(self.panel,-1,"Close",pos=[220,yloc],size=(50,20))        
            btncls.Bind(wx.EVT_BUTTON,self.OnClose)
            btncls.SetToolTipString('Close the panel')  
    
    def CreateCtrlPanel(self,panpos,pansize):
        
        self.ctrlpanel=wx.Panel(self.panel,-1,pos=panpos,size=pansize)
        self.ctrlpanel.SetBackgroundColour(self.panelbgcolor)
        #
        height=pansize[1]; 
        width=pansize[0]
        xloc=10; yloc=5 #panpos[1]+5
        btnheight=120; lbheight=pansize[1]-btnheight
        lbheight=len(self.gmsuser.inputnamelst)*self.fontheight+10
        maxlbheight=pansize[1]-btnheight-50
        if lbheight > maxlbheight: lbheight=maxlbheight
        lbsize=[pansize[0]-10,lbheight]
        #
        wx.StaticText(self.ctrlpanel,-1,"Select:",pos=(xloc,yloc),size=(50,20)) 
        yloc += 20
        
        self.selectbox=wx.ListBox(self.ctrlpanel,-1,choices=self.gmsuser.inputnamelst,
                                  pos=[xloc,yloc],size=lbsize,
                                  style=wx.LB_SINGLE|wx.LB_HSCROLL) #wx.LB_NEEDED_SB (vertical scroll bar)
        self.selectbox.SetStringSelection(self.curname)
        self.selectbox.Bind(wx.EVT_RIGHT_DOWN,self.OnSelectRightClick)
        if self.donenamedic.has_key(self.curname):
            try: idx=self.gmsuser.inputnamelst.index(self.curname)
            except: idx=-1
            # is not suppoted in WINDOWS ?
            if idx >= 0: self.selectbox.SetItemForegroundColour(idx,self.setcolor)
        yloc += lbsize[1]+10
        wx.StaticLine(self.ctrlpanel,pos=[8,yloc],size=[width-2,2],style=wx.LI_HORIZONTAL)
        yloc += 8
        # buttons
        self.btnrmv=wx.Button(self.ctrlpanel,-1,"Remove",pos=[15,yloc],size=(60,20))
        self.btnrmv.SetToolTipString('Remove selected name group')        
        self.btnrmv.Bind(wx.EVT_BUTTON,self.OnCtrlRemove)
        yloc +=25
        wx.StaticLine(self.ctrlpanel,pos=[8,yloc],size=[width-2,2],style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.ctrlpanel,-1,'Add:',pos=(10,yloc),size=(40,20))                      
        yloc +=20
        self.tcladd=wx.TextCtrl(self.ctrlpanel,-1,'',pos=(15,yloc),size=(80,18),
                                style=wx.TE_PROCESS_ENTER)
        self.tcladd.Bind(wx.EVT_TEXT_ENTER,self.OnCtrlAdd)
        self.tcladd.Bind(wx.EVT_TEXT,self.OnTextEntered)
        self.tcladd.SetToolTipString('Input name group and hit "ENTER"')  
        yloc +=22
        wx.StaticLine(self.ctrlpanel,pos=[8,yloc],size=[width-2,2],style=wx.LI_HORIZONTAL)
        yloc += 8
        self.btnundo =wx.Button(self.ctrlpanel,-1,"Undo",pos=[20,yloc],size=(50,20))        
        self.btnundo.Bind(wx.EVT_BUTTON,self.OnCtrlUndo)
        self.btnundo.SetToolTipString('Undo Remove/Add once')  
        if len(self.undolst) <= 0: self.btnundo.Disable()
        # event handlers
        self.selectbox.Bind(wx.EVT_LISTBOX,self.OnSelected)
        self.selectbox.Bind(wx.EVT_LISTBOX_DCLICK,self.OnDClicked)
    
    def OnTextEntered(self,event):
        pass
        ##self.gmsuser.OnTextEntered(event)
               
    def CreateInputerPanel(self,panpos,pansize):
        self.inputpanel=wx.Panel(self.panel,-1,pos=panpos,size=pansize)
        self.inputpanel.SetBackgroundColour(self.panelbgcolor)
        #
        height=pansize[1]
        btnheight=25; btnyloc=pansize[1]-btnheight
        gridwidth=pansize[0]-10
        gridheight=pansize[1]-btnheight-30
        xloc=0; yloc=5
        #
        title="Input values in : "+self.curname
        stinp=wx.StaticText(self.inputpanel,-1,title,pos=(xloc,yloc),size=(gridwidth,20)) 
        stinp.SetToolTipString('Select a cell and input value directly or R-click to pop up select items/tip')  
        yloc += 20
        # craeted Variable Table
        gridpos=[xloc,yloc]; gridsize=[gridwidth,gridheight]
        nrow=len(self.gmsuser.inpnamvardic[self.curname])
        self.CreateGridPanel(self.inputpanel,gridpos,gridsize,nrow)
        self.SetDataToGridTable(self.curname)
        # buttons
        yloc=btnyloc
        btnrsetall=wx.Button(self.inputpanel,-1,"Reset all",pos=(20,yloc),size=(60,20))
        btnrsetall.Bind(wx.EVT_BUTTON,self.OnInputResetAll)
        btnrsetall.SetToolTipString('Reset all values to defaults')  
        btnrset=wx.Button(self.inputpanel,-1,"Reset",pos=(100,yloc),size=(50,20))
        btnrset.Bind(wx.EVT_BUTTON,self.OnInputReset)
        btnrset.SetToolTipString('Reset selected value to default')  
        #btndeft=wx.Button(self.inputpanel,-1,"Default",pos=(100,yloc),size=(50,20))
        #btndeft.Bind(wx.EVT_BUTTON,self.OnInputDefault)

    def CreateGridPanel(self,panel,panpos,pansize,nrow):
        self.gridpanel=wx.Panel(self.inputpanel,-1,pos=panpos,size=pansize)
        self.gridpanel.SetBackgroundColour('white')
        self.grid=wx.grid.Grid(self.gridpanel,-1,pos=[0,0],size=pansize)
        self.grid.EnableGridLines(False)
        self.grid.SetColLabelSize(0)
        self.grid.SetRowLabelSize(0)

        try: self.grid.ShowScrollbars(wx.SHOW_SB_DEFAULT,wx.SHOW_SB_NEVER)
        except: pass
        
        self.grid.DisableDragCell()
        #self.grid.EnableCellEditControl(False)
        #self.grid.DisableDragColMove()
        #self.grid.SetSelectionBackground('white')
        
        self.grid.CreateGrid(nrow+1,3)
        self.grid.SetColSize(0,60)
        self.grid.SetColSize(1,20)
        self.grid.SetColSize(2,60)
        for i in range(nrow): self.grid.SetRowSize(i,22)
        # make the first col read-only
        self.grid.SetReadOnly(0,1,isReadOnly=True)
        for i in range(nrow+1): 
            self.grid.SetReadOnly(i,0,isReadOnly=True)
            self.grid.SetReadOnly(i,1,isReadOnly=True)
            
        #self.grid.Bind(wx.grid.EVT_GRID_SELECT_CELL,self.OnGridCellSelect)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK,self.OnGridCellSelect)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK,self.OnGridRightClick)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_CHANGE,self.OnGridCellChange)

    def OnSelectRightClick(self,event):
        pos=event.GetPosition()
        try:
            idx=self.selectbox.HitTest(pos)
            item=self.gmsuser.inputnamelst[idx]
            name=item+':'+item
            mess=''
            if self.gmsuser.varvaltipsdic.has_key(name):
                mess=self.gmsuser.varvaltipsdic[name] #nametipsdic[item]
                mess=self.gmsuser.RemoveParenthesis(mess)
                self.selectbox.SetSelection(idx)
            if len(mess) <= 0: mess='No description available.'
            lib.MessageBoxOK(item+':\n'+mess,'GAAMESS Inputer')
            self.selectbox.SetSelection(idx,select=False)
        except: pass

    def OnInputResetAll(self,event):
        """ Set all values to defaults
        
        """
        value=''; icolm=2; menulabel=''
        nrow=self.grid.GetNumberRows()
        for i in range(nrow):
            self.selectedrow=i; self.selectedcol=icolm
            #varnam=self.grid.GetCellValue(self.selectedrow,0)
            #if len(varnam.strip()) <= 0: continue
            self.OnSelectValue(value,menulabel)

    def OnInputReset(self,event):
        """ Set selcted value to default
        
        """
        ###self.gmsuser.inputnamelst=self.PresetInputnames()
        value=''; menulabel=''
        self.OnSelectValue(value,menulabel)

    def OnSelectValue(self,value,menulabel):
        self.returnvalue=value
        self.openlistboxmenu=False   
        if value == '<close>': return # or value == '': return
        #if value == '': value=self.gmsuser.GetDefaultValue(curnamvar)
        #self.grid.SetCellValue(self.selectedrow,self.selectedcol,value)
        if value.upper() == 'NONE': 
            self.SetDataToGridTable(self.curname)
            return
        curvarnam=self.grid.GetCellValue(self.selectedrow,0)
        if len(curvarnam.strip()) <= 0: return
        #
        curnamvar=self.curname+':'+curvarnam
        valuecolor=self.setcolor
        setvalue=True
        if value == '': setvalue=False
        if not setvalue: 
            value=self.gmsuser.GetDefaultValue(curnamvar)
            valuecolor=self.unsetcolor
        self.grid.SetCellValue(self.selectedrow,self.selectedcol,value)
        # self.curnamvar <- set in OnGridRightClick
        if value == 'FROMFU':
            #self.gmsuser.TextDataFromFU(curnamvar)
            #self.gmsuser.SetFMOValueFromFU(curnamvar)
            self.gmsuser.SetValueFromFU(curnamvar)
            
            self.SetDataToGridTable(self.curname)
            self.gmsuser.coordinternal=True
            self.gmsuser.coordfile=False
            return
        elif value == 'FILE':
            self.gmsuser.SetValueFromFile(curnamvar)
            self.SetDataToGridTable(self.curname)
            self.gmsuser.coordinternal=False
            self.gmsuser.coordfile=True

            return
        elif value == 'INPUT':
            self.gmsuser.SetValueFromEditor(curnamvar)
            self.SetDataToGridTable(self.curname)
            return
        else: # var=val form input
            #curvarnam=self.grid.GetCellValue(self.selectedrow,0)
            #curnamvar=self.curname+':'+curvarnam
            items=value.split(':')
            if len(items) >= 2: value=items[1].strip()
            #self.gmsuser.inputvaldic[namvar]=[value,self.setcolor]
            #set=True
            #if value == '': set=False
            retmess=self.gmsuser.SetInputValue(curnamvar,value,setvalue)
            self.grid.SetCellValue(self.selectedrow,self.selectedcol,value)
            self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,valuecolor)
            #if self.gmsuser.requireddic.has_key(curnamvar):
            reqnamlst=self.gmsuser.GetRequiredNames(curnamvar,value)
            for name in reqnamlst:
                self.gmsuser.AddInputNameAndVars(name,[])
            
            self.ctrlpanel.Destroy()
            self.CreateCtrlPanel(self.ctrlpanpos,self.ctrlpansize)
            
            self.changed=True
            if self.mode == 'beginner':
                self.gmsuser.beginner.SetSelectedValueToComboBox(self.curname,curvarnam,value)
    
    def OnGridCellChange(self,event):
        self.selectedrow=event.GetRow()
        self.selectedcol=event.GetCol()
        if self.selectedcol != 2: return    
        value = self.grid.GetCellValue(self.selectedrow,self.selectedcol)
        curvarnam=self.grid.GetCellValue(self.selectedrow,0)
        #
        self.curnamvar=self.curname+':'+curvarnam
        value=value.strip()
        #self.gmsuser.inputvaldic[self.curnamvar]=[value,self.setcolor]
        retmess=self.gmsuser.SetInputValue(self.curnamvar,value,True)
        self.grid.SetCellTextColour(self.selectedrow,self.selectedcol,self.setcolor)
        self.changed=True
    
    def OnSelectName(self,value,menulabel):
        self.openlistboxmenu=False
        if value == '<close>' or value == '': return
        #try: idx=self.gmsuser.inputnamelst.index(value)
        #except: idx=-1
        #if idx >= 0:
        if value in self.gmsuser.inputnamelst:
            mess='The name group '+value+' is alredy selected.'
            lib.MessageBoxOK(mess,'Add button')
            return
        self.gmsuser.inputnamelst.append(value)
        self.curname=value
        self.SetDataToGridTable(self.curname)
        self.undolst=['CtrlAdd',self.curname,None]
        self.panel.Destroy()
        self.CreatePanel()

    def OpenListBoxMenu(self,retmethod,menulst,tiplst,submenudic,subtipdic):
        listboxmenu=self.gmsuser.OpenListBoxMenu(self,retmethod,menulst,tiplst,
                                submenudic,subtipdic,menulabel='LBMenu')
        """
        [x,y]=wx.GetMousePosition()
        winpos=[x+20,y]
        winheight=len(menulst)*self.fontheight+10
        if winheight > self.maxlistboxmenuheight:
            winheight=self.maxlistboxmenuheight
        winsize=[100,winheight]
        
        #self.listboxmenu=lib.ListBoxMenu_Frm(self,-1,winpos,winsize,menulabel,menulst,tiplst)
        listboxmenu=subwin.ListBoxMenu_Frm(self,-1,winpos,winsize,retmethod,
                                        menulst,tiplst=tiplst,submenudic=submenudic,
                                        subtipdic=subtipdic,menulabel='Test')
        """
        self.openlistboxmenu=True
        return listboxmenu
                  
    def PackCurNames(self):
        namvarval=self.curname+':'+self.curvar+':'+self.curval
        return namvarval
    
    def PackNamVarNames(self):
        namvar=self.curname+':'+self.curvar
        return namvar
            
    def UnpackNames(self,namvarval):
        name=''; varnam=''; valnam=''           
        items=namvarval.sprit(':')
        if len(items) >= 1: name=items[0]           
        if len(items) >= 2: varnam=items[1]
        if len(items) >= 3: valnam=items[2]           
        return name,varnam,valnam

    def UnpackValName(self,namvarval):
        valnam=''           
        items=namvarval.sprit(':')
        if len(items) >= 3: valnam=items[2]           
        return valnam
                                                        
    def SelectedMenuLabel(self,label):
        self.selectedmenulabel=label 

    def SetInputNameList(self,inputnamelst):
        self.gmsuser.inputnamelst=inputnamelst
        
    def OnGridRightClick(self,event):
        
        if self.openlistboxmenu: return        
        #
        self.grid.SetGridCursor(self.selectedrow,self.selectedcol)
        self.grid.SetCellBackgroundColour(self.selectedrow,self.selectedcol,'light blue')
        self.grid.SetReadOnly(self.selectedrow,self.selectedcol,isReadOnly=False)
#        if self.curval != '':    
        curvarnam=''
        # If the val='TEXT', edit the text
        if self.selectedcol == 2: # and self.selectedrow != 0:
            curvarnam=self.grid.GetCellValue(self.selectedrow,0)
            curvarnam=curvarnam.strip()
            if len(curvarnam) <= 0: return        
            curvalnam=self.grid.GetCellValue(self.selectedrow,2)
            curvalnam=curvalnam.strip()
            namvar=self.curname+':'+curvarnam
            namvarval=namvar+':'+curvalnam
            if curvalnam == 'TEXT' and self.gmsuser.textvaldic.has_key(namvar):
                self.grid.SetReadOnly(self.selectedrow,self.selectedcol,isReadOnly=True)
                text=self.gmsuser.textvaldic[namvar]
                items=text.split('=')
                if len(items) >= 2: idx=1
                else: idx=0
                #text=' '+self.curname+'\n'+items[1].strip()+'\n $END\n' 
                text=items[idx] #.strip()
                if len(text) >= 0:
                    title='Edit '+namvarval #self.curname+':'+curvarnam+':'+curvalnam
                    self.gmsuser.OpenTextEditor(title,text,'Edit')
                    return            
            # select value
            tiplst=[]
            curvallst=self.curvaldic[curvarnam]
            # make tip list (will be used in 'ListBoxMenu'
            for val in curvallst:
                varval=curvarnam+':'+val
                if self.curvaltipdic.has_key(varval): 
                    text=self.curvaltipdic[varval]
                    text=self.gmsuser.RemoveParenthesis(text)
                    tiplst.append(text) #self.curvaltipdic[varval])
                else: tiplst.append('')
            menulst=['<close>','']
            ###if curvarnam != '': 
            menulst=menulst+self.curvaldic[curvarnam]
            tiplst=['','']+tiplst
            # submenu
            submenudic={}; subtipdic={}
            subtipdic=self.varsubtipdic
            for item in self.curvaldic[curvarnam]:
                if item == '': continue
                if self.varsubdic.has_key(item):
                    submenudic[item]=self.varsubdic[item]
                    submenudic[item]=['<close>','']+submenudic[item]
                    subtipdic[item]=['','']+subtipdic[item]
            # open listbox menu items
            menulabel='SelectValue'
            self.listboxmenu=self.OpenListBoxMenu(self.OnSelectValue,
                             menulst,tiplst,submenudic=submenudic,subtipdic=subtipdic)
            self.curnamvar=self.curname+':'+curvarnam
        if self.curvar != '':
            mess=''
            if self.curvartipdic.has_key(self.curvar): 
                mess=self.curvartipdic[self.curvar]
            if self.curvar == 'Example' and len(mess) > 0:
                self.gmsuser.OpenTextEditor('Example',mess,'View')
            else:
                if len(mess) <= 0: mess='No description available.'
                #lib.MessageBoxOK(self.curvar+':\n'+mess,'GAAMESS Inputer')
                lib.MessageBoxOK(self.curvar+':\n'+mess,'GAAMESS Inputer')  
            
    def OnGridCellSelect(self,event):

        self.grid.SetCellBackgroundColour(self.selectedrow,self.selectedcol,'white')
        
        self.selectedrow=event.GetRow()
        self.selectedcol=event.GetCol()

        #nrow=self.grid.GetNumberRows()
        self.grid.ClearSelection() 
        
        self.grid.SetGridCursor(self.selectedrow,self.selectedcol)
        
        if self.openlistboxmenu: 
            self.listboxmenu.Destroy()
            self.openlistboxmenu=False
        
        value = self.grid.GetCellValue(self.selectedrow,self.selectedcol)
        value=value.strip()
        self.curnam=''; self.curvar=''; self.curval=''
        if self.selectedcol == 0:
            #if self.selectedrow == 0: self.curnam=value 
            #else:       
            items=value.split('=',1); value=items[0].strip()
            self.curvar=value
        elif self.selectedcol == 2: self.curval=value

    def SetValueToGridCell(self,value,color): 
        #self.selectedrow=event.GetRow()
        #self.selectedcol=event.GetCol()
        self.grid.SetCellValue(self.selectedrow,2,value)
        self.grid.SetCellTextColour(color)

    def SetDataToGridTable(self,name):
        #
        varlst=self.gmsuser.varlstdic[name]
        if self.gmsuser.inpnamvardic.has_key(name):
            varlst=self.gmsuser.inpnamvardic[name]
        #self.curvallst=[]
        self.curvaldic={}; self.curvartipdic={}; self.curvaltipdic={}
        self.varsubdic={}; self.varsubtipdic={}
        #self.grid.SetCellValue(0,0,name)
        self.curnamtip=''
        if self.gmsuser.varvaltipsdic.has_key(name+':'+name): 
            self.curnamtip=self.gmsuser.varvaltipsdic[name+':'+name]
        #
        nrow=len(varlst)
        irow=-1
        for i in range(nrow):
            items=[]
            var=varlst[i].strip()
            varsubs=var.split('-',1)
            if len(varsubs) >= 2:
                if varsubs[1].isdigit() and var != '':
                    varpar=varsubs[0]
                    if not self.varsubdic.has_key(var): self.varsubdic[var]=[]
                    namvar=name+':'+var
                    val=self.gmsuser.varvaldic[namvar]
                    vallst=self.gmsinpobj.SplitValues(val)
                    self.varsubdic[var]=vallst
                    if not self.curvaldic.has_key(varpar): self.curvaldic[varpar]=[]
                    self.curvaldic[varpar].append(var)
                    for val in vallst:
                        # namvarval=$BASIS:GBASIS-1:STO
                        namvarval=self.curname+':'+var+':'+val
                        if not self.varsubtipdic.has_key(var): self.varsubtipdic[var]=[]
                        text=''
                        if self.gmsuser.varvaltipsdic.has_key(namvarval):
                            text=text+self.gmsuser.varvaltipsdic[namvarval]+'\n'
                        self.varsubtipdic[var].append(text)
                        #else: self.varsubtipdic[var].append('')
                #print 'self.varsubtipdic',self.varsubtipdic
                continue
            irow += 1
            items.append(var)
            namvar=name+':'+var
            if self.gmsuser.varvaltipsdic.has_key(namvar):
                self.curvartipdic[var]=self.gmsuser.varvaltipsdic[namvar]
            if var == 'Example': items.append('')
            else: items.append('=')
            # values
            vallst=[]
            if self.gmsuser.varvaldic.has_key(namvar):
                val=self.gmsuser.varvaldic[namvar]
                vallst=self.gmsinpobj.SplitValues(val)
                self.curvaldic[var]=vallst
            for val in vallst:
                namvarval=name+':'+var+':'+val
                varval=var+':'+val
                # value's tip
                if self.gmsuser.varvaltipsdic.has_key(namvarval):
                    self.curvaltipdic[varval]=self.gmsuser.varvaltipsdic[namvarval]         
            try: 
                value=self.gmsuser.inputvaldic[namvar][0]
                textcolor=self.gmsuser.inputvaldic[namvar][1]
                
            except: 
                value=''; textcolor=self.unsetcolor
                 
            items.append(value)
            for j in range(3): self.grid.SetCellValue(irow,j,items[j])
            self.grid.SetCellTextColour(irow,2,textcolor)
            self.grid.Refresh()
                        
    def MakeNameVarTipDic(self,name):
        vartipdic={}
        if not self.gmsuser.varvaldic.has_key(name): return vartipdic
        varlst=self.gmsuser.varvaldic[name]
        for var in varlst:
            namvar=name+':'+var
            if self.gmsuser.varvaltipsdic.has_key(namvar):
                vartipdic[var]=self.gmsuser.varvaltipsdic[namvar]           
        return vartipdic    
            
    def OnCtrlRemove(self,event):
        if len(self.gmsuser.inputnamelst) <= 1: 
            mess='Can not remove the last name group!'
            lib.MessageBoxOK(mess,'GMSExpert:OnCtrlRemove')
            return
        self.gmsuser.inputnamelst.remove(self.curname)
        dat=None
        #if self.gmsinpobj.inputvaldic.has_key(self.curname): dat=self.gmsinpobj.inputvaldic[self.curname]
        if self.gmsuser.IsInputNamVar(self.curname): dat=self.gmsuser.GetInputNamVar(self.curname)
        
        self.undolst=['CtrlRemove',self.curname,dat]
        #
        if self.donenamedic.has_key(self.curname): del self.donenamedic[self.curname]
        self.curname=self.gmsuser.inputnamelst[0]
        ###self.SetDataToGridTable(self.curname)
        #
        self.OnMove(1)
        #self.panel.Destroy()
        #self.CreatePanel()
        #self.btnundo.Enable()
        #if len(self.inputnamelst) <= 0: self.btnrmv.Disable()
        if self.gmsuser.GetNumberOfInputNames() <= 0: self.btnrmv.Disable()
        else: self.btnrmv.Enable()
              
    def OnCtrlUndo(self,event):
        if len(self.undolst) <= 0:
            mess='No data for undo.'
            lib.MessageBoxOK(mess,'GAMESS Inputer')
            return
        if self.undolst[0] == 'CtrlAdd':
            name=self.undolst[1]
            self.OnCtrlRemove(1)
            self.undolst=[]
        elif self.undolst[0] == 'CtrlRemove':
            name=self.undolst[1]
            self.gmsuser.inputnamelst.append(name)
            #self.gmsinpobj.inputvaldic[name]=self.undolst[2]
            remess=gmsuser.SetDataToInputNamVar(name,self.undolst[2])
            self.curname=name
            ####self.SetDataToGridTable(self.curname)
            self.undolst=[]
            #
            self.OnMove(1)
        
    def OnCtrlAdd(self,event):
        name=self.tcladd.GetValue()
        #try: idx=self.gmsuser.inputnamelst.index(name)
        #except: idx=-1
        #if idx >= 0:
        if name in self.gmsuser.inputnamelst:
            lib.MessageBoxOK('Duplicate name. The operation is canceled.','')
            self.tcladd.SetValue('')
            return
        if not self.gmsuser.varlstdic.has_key(name):
            lib.MessageBoxOK('Wrong name. The operation is canceled.','')
            self.tcladd.SetValue('')
            return
        #self.inputnamelst.append(name)
        self.gmsuser.AddInputNameAndVars(name,[])
        self.undolst=['CtrlAdd',self.curname,[]]
        self.curname=name
        ###self.SetDataToGridTable(self.curname)
        self.OnMove(1)
        
    def OnSelected(self,event):
        self.curname=self.selectbox.GetStringSelection()
        self.donenamedic[self.curname]=True
        if self.openlistboxmenu:
            self.listboxmenu.Destroy()
            self.openlistboxmenu=False
        self.panel.Destroy()
        self.CreatePanel()
        
    def OnDClicked(self,event):
        pass
    
    def OnSave(self,event):
        self.gmsuser.SaveInput()
        """
        wcard='input file(*.inp)|*.inp|All(*.*)|*.*'
        filename=lib.GetFileName(None,wcard,'w',True,'')
        if len(filename) > 0: 
            self.gmsuser.WriteInputFile(filename)
            #self.writefilename=filename
        """

    def OnView(self,event):
        """ View current input data
        """
        self.gmsuser.ViewCurrentData()
    
    def ChangeBackgroundColor(self):
        color=lib.ChooseColorOnPalette(self.panel,True,-1)
        #color=[255*col[0],255*col[1],255*col[2]]
        self.input.SetBackgroundColour(color)
        self.panel.SetBackgroundColour(color)
        self.ctrlpanel.SetBackgroundColour(color)
        self.inputpanel.SetBackgroundColour(color)
        
    def ChangeTextColor(self):
        color=lib.ChooseColorOnPalette(self.panel,True,-1)
        #color=[255*col[0],255*col[1],255*col[2]]
        self.input.SetForegroundColour(color)        
        
    def OnRunGAMESS(self,event):
        #print 'GMSExpert, RunGAMESS'
        self.gmsuser.RunGAMESS(self)   

    def OnThreadJobEnded(self,event):
        if self.gmsuser.mode == 'expert':
            jobnam=event.jobid
            jobcmd=event.message
            killed=event.killed
            
            print 'jobid,jobcmd in OnThreadEnd',jobid,jobcmd
            
            try: self.gmsuser.exeprgwin.f.close()
            except: pass
            
            self.gmsuser.ThreadJobEnded(jobnam,jobcmd,killed)
            #winlabel='ExePrgWin'
            #self.gmsuser.flags.Set(self.gmsuser.exewinlabel,False)
            #self.gmsuser.openexeprgwin=False
    
    def OnClose(self,event):
        try: self.gmsuser.expertwin=False
        except: pass
        try: self.listboxmenu.Destroy()
        except: pass
        try: self.gmsuser.editor.Destroy()
        except: pass
        if self.gmsuser.mode == 'expert':
            try: 
                self.gmsuser.childobj.Del('gamess-user')
                self.gmsuser.ctrlflag.Del('gamess-user')
            except: pass
        self.Destroy()
       
    def OnResize(self,event):
        self.OnMove(1)
        
    def OnMove(self,event):
        savopenlistctrlwin=self.openlistboxmenu
        self.panel.Destroy()
        if self.openlistboxmenu: 
            self.listboxmenu.Destroy()
            self.openlistboxmenu=False
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])
        self.CreatePanel()
        if savopenlistctrlwin: self.OnGridRightClick(1)
          
    def LoadGMSInputFile(self,filename):
        """
        
        :param int case: 0 for example, 1 for template
        """

        self.gmsuser.OpenInputFile(filename)
        self.inputfileinfo=self.gmsinpobj.GetInputFileInfo()               
        #self.SetJobTitleToWidget(filename[:70])
        mess='' #retmess    
        mess=mess+' file='+filename
        self.statusbar.SetStatusText(mess)
        self.readfilename=filename
        #
        self.SetDataToGridTable(self.curname)
        self.undolst=[]
        #
        self.OnMove(1)

    def Usage(self):
        text='How to input value:\n'
        text=text+'* Select an input cell by L-Click.\n'
        text=text+'* You can input a value directly in a selected cell.\n'
        text=text+'* R-Click on an input cell pups up submenu when available.\n'
        text=text+'* R-Click on a variable or input cell pops up tip string when available.\n'
        text=text+'* if a "TEXT" value has contents, R-Click opens editor.\n'
        text=text+'    if you want to open the submenu, clear the contents and R-Click again.\n' 
        lib.MessageBoxOK(text,'GAMESS Assist for Expert')
        
    def OnExpertMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.menubar.GetLabel(menuid)
        # File menu items
        if item == "Open input":
            wildcard='input file(*.inp)|*.inp|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"r",True,"")
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                #self.ReadFile(filename)
                self.gmsinputfile=filename
                ###self.OpenInputFile(filename,0)
                self.LoadGMSInputFile(filename)
        elif item == "Open GMS example": 
            self.gmsuser.OpenExampleFile('GMS')
        elif item == "Open FMO example": 
            self.gmsuser.OpenExampleFile('FMO')
            #filename='c://gamess.64//tests//exam01.inp'  
            #self.OpenInputFile(filename,0)        
        #elif item == "Load template":
            # not tested
        #    filename='c://gamess.64//tests//exam01.inp'
        #    self.OpenInputFile(filename,1)
        elif item == "Save input file":
            #print 'save input file'
            #wcard='input file(*.inp)|*.inp|All(*.*)|*.*'
            #filename=lib.GetFileName(None,wcard,'w',True,'')
            #if len(filename) > 0: 
            self.gmsuser.SaveInput()
        elif item == "Switch to beginner":
            self.gmsuser.CloseExpertWin()
            self.mode='beginner'
            self.gmsuser.OpenBeginnerWin(self.mdlwin) #,self.inputvaldic,self.textvaldic,self.gmsdoc)          
        elif item == "Delete all in gamess/scr":
            self.gmsuser.DeleteAllGAMESSScratch()
            
        elif item == "Close":
            self.OnClose(1)
        # Window menu
        elif item == "Open ExecProgWin":
            self.gmsuser.OpenExePrgWin(self)
        
        elif item == "Close ExecProgWin":
            try: self.gmsuser.exeprgwin.OnClose(1)
            except: pass        
        # Help menu items
        elif item == 'About':
            title='GAMESS Assist For Expert in FU ver.'
            lib.About(title,const.FUMODELLOGO)
        elif item == 'Help':
            self.gmsuser.HelpMessage()
        elif item == "Usage":
            self.Usage()
        # Setting    
        elif item == "Setting":
            self.gmsuser.OpenSettingGAMESSPanel(self)
        elif item == "Games input document":
            self.gmsuser.ViewGAMESSDocument()

    def ExpertMenuItems(self):
        menubar=wx.MenuBar()
        submenu=wx.Menu()
        # File menu
        #subsubmenu=wx.Menu()
        submenu.Append(-1,'Open input','OPen input file.')
        submenu.Append(-1,'Open GMS example','Open GAMESS example input file in /tests.')
        submenu.Append(-1,'Open FMO example','Open GAMESS example input file.')
        #submenu.Append(-1,'Load template','Load GAMESS input file as a template.')
        submenu.AppendSeparator()
        submenu.Append(-1,'Save input file','save GAMESS input file')
        submenu.AppendSeparator()
        submenu.Append(-1,"Switch to beginner","Switch to beginner input panel")
        submenu.AppendSeparator()
        submenu.Append(-1,"Delete all in gamess/scr","Delete GAMESS $DATA")
        submenu.AppendSeparator()
        submenu.Append(-1,'Close','Close the window')
        menubar.Append(submenu,'File')
        # Window menu
        #submenu=wx.Menu()
        #submenu.Append(-1,"Open ExecProgWin","Open ExecProg window")
        #submenu.Append(-1,"Close ExecProgWin","Close ExecProg window")
        #menubar.Append(submenu,'Window')        
        #Help
        submenu=wx.Menu()
        submenu.Append(-1,"About","Open about message")
        submenu=wx.Menu()
        submenu.Append(-1,"Help","Help")
        submenu.AppendSeparator()
        submenu.Append(-1,"Usage","Usage of GAMSSS Assist for Expert")
        submenu.AppendSeparator()
        submenu.Append(-1,"Setting","Set GAMESS program path")   
        submenu.AppendSeparator()
        ###submenu.Append(-1,"Games input document","Open GAMESS INPUT document")
        ###menubar.Append(submenu,'Help')
        return menubar

class GMSBeginner_Frm(wx.Frame):
    def __init__(self,mdlwin,id,gmsuser,winpos=[-1,-1]):
        """
        :param obj model: View_Frm (fumodel.py)
        """
        title='GAMESS Assist For Beginner'
        if mdlwin:
            try: 
                [x,y]=mdlwin.GetPosition()
                [w,h]=mdlwin.GetSize()
                winpos=[x+w,y+20]
            except: winpos=winpos
        else: winpos=winpos
        winsize=lib.WinSize([290,490]) #[280,440] #430]) # 455
        #if fu:
        #if const.SYSTEM == const.MACOSX: winsize=(275,445)
        if not mdlwin:
            wx.Frame.__init__(self,None,id,title,pos=winpos,size=winsize,
                  style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.RESIZE_BORDER) #|wx.FRAME_FLOAT_ON_PARENT)
        else:
            wx.Frame.__init__(self,mdlwin,id,title,pos=winpos,size=winsize,
                  style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX| \
                  wx.RESIZE_BORDER|wx.FRAME_FLOAT_ON_PARENT)
        self.gmsuser=gmsuser
        self.gmsinpobj=self.gmsuser.gmsinpobj
        self.mdlwin=mdlwin #model # fum
        self.model=None
        self.mol=None
        self.timer=None
        self.winsize=winsize
        self.prgfile=self.gmsuser.prgfile
        if self.mdlwin:
            self.model=self.mdlwin.model
            self.setctrl=self.model.setctrl
            self.winctrl=self.model.winctrl
            self.mol=self.model.mol
            self.childobj=self.model.childobj
            self.ctrlflag=self.model.ctrlflag
            #self.prgfile=self.model.setctrl.GetFile('Programs','gamess'+ext)
            mess='Read program file. file='+self.prgfile
            self.model.ConsoleMessage(mess)
        # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        #self.timer = wx.Timer(self)
        #self.Bind(wx.EVT_TIMER, self.update, self.timer)
        #self.timer.Start(5)
        #self.winlabel='GamessWin' 
        platform=lib.GetPlatform()
        #ext='.win'
        if platform == 'MACOSX': ext='.mac'
        elif platform == 'LINUX': ext='.lnx'
        #
        #self.inputer=None
        #self.openinputerwin=False
        #        
        self.openexeprgwin=False # set in ExeProgWin
        
        self.inputer=None
        self.openinputerwin=None
        self.inputerwinsize=[300,300]
        self.widgetstatusdic={}
        self.enablecharge=True
        self.enablebasis=True
        self.enablelayer=False
        #
        self.fontheight=self.gmsuser.fontheight
        self.setcolor=self.gmsuser.setcolor
        self.unsetcolor=self.gmsuser.unsetcolor
        self.needcolor=self.gmsuser.needcolor
        #        
        self.jobtitle=self.gmsuser.jobtitle #'job title'
        self.properties=self.gmsuser.properties
        #self.grimmdisp=False # note: used for toggle sw, since i can not change color of togglebutun
        self.choicelst=[]
        self.comboboxmenulst=['Method','Run','Wave','Basis','Solvent','Properties']
        #self.fmomenulst=['FMO2','FMO3','FMO1','MFMO','FMO/FD','FMO/IMOMM','EFMO']
        # used to keep item order in usernamelstdic
        self.fmomenulst=self.MakeGroupItemList('Method','FMO')
        
        self.choicedic={} # current choice dic in combobox {'Method':'FMO3',...}
        """ for debug """
        ###self.optionlst=['OPTIONS:$CONTRL','Coordinate:$ZMAT']
        
        self.wingamess=False
        self.gmsinputfile=self.gmsuser.gmsinputfile
        self.savgmsinputfile=self.gmsinputfile
        self.jobnmb=0
        self.inpfilecopylst=[]
        self.gmssetwin=False
        self.madeinput=self.gmsuser.madeinput
        #
        self.pos=self.GetScreenPosition()
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar) #self.menubar.menuitem)
        self.gmsmenu='None' 
        #
        #userdocfile=self.gmsuser.userdocfile
        #userdoc=self.gmsinpobj.ReadInputDocText(userdocfile)
        #userdoc=self.gmsuser.userdoc
        #self.ExtractUserGMSDocData(userdoc)
        #
        #self.userinputvaldic=copy.deepcopy(self.uservarvaldic)        
        #self.usertextvaldic={}
        self.usernamelst=self.gmsuser.usernamelst
        self.uservarlstdic=self.gmsuser.uservarlstdic
        self.uservarvaldic=self.gmsuser.uservarvaldic
        self.userinputvaldic=self.gmsuser.userinputvaldic
        self.usertextvaldic=self.gmsuser.usertextvaldic
        #self.basnam=self.gmsuser.basnam
        #self.spin=self.gmsuser.spin
        self.charge=self.gmsuser.charge
        self.grimmdisp=self.gmsuser.grimmdisp
        #self.pltene=False; self.pltgrd=False; self.pltnone=True                    
        #
        self.MakeWidgetData()
        self.SetInitialValues()
        self.CreatePanel()
        self.SetWidgets()
        #
        #self.Bind(wx.EVT_TIMER,self.OnTimer,self.timer)
        #self.Bind(wx.EVT_KEY_DOWN,self.OnQKeyDown) 
        #
        ###subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)
        #
        self.Bind(wx.EVT_MENU,self.OnMenu)
        self.Bind(wx.EVT_PAINT,self.OnPaint)
        self.Bind(wx.EVT_SIZE,self.OnResize)
        self.Bind(wx.EVT_MOVE,self.OnMove)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.Bind(wx.EVT_SET_FOCUS,self.OnFocus)
        #
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)  #self.timer=wx.Timer(self)
        #self.FUDONE=False
        #self.FUCANCELLED=False
        #
        self.Show()
    
    def XXupdate(self,event):
        print time.ctime()
        self.model.ConsoleMessage(time.ctime())
        
    def MakeGroupItemList(self,grpnam,item):
        """
        :param str grpnam:
        :param str item: 'FMO' or 'SEMIEMPIRICAL
        """
        itemlst=[]
        methodlst=self.gmsuser.uservarlstdic[grpnam]
        for meth in methodlst:
            items=meth.split(':')
            if len(items) < 2: continue
            if items[0].strip() == item:
                fmo=items[1].strip()
                if fmo == 'OPTION': continue
                itemlst.append(fmo)
        return itemlst
        
    def OnFocus(self,event):
        self.SetFocus()
               
    def MakeWidgetData(self):
        """
        self.usernamelst=['Method','OPTIONS','Job','Charge','Spin',
                     'Coordinate','Run','Wave','Basis',
                     'Solvent','Properties','Computer']
        """
        combobox=self.comboboxmenulst
        self.choicelstdic0={}; self.optiondic={}; self.submenudic={}
        
        #print 'uservarlstdic',self.uservarlstdic
        for name in combobox:
            self.choicelstdic0[name]=[]
            for varval in self.uservarlstdic[name]:
                if varval == 'OPTION':
                    self.optiondic[name]=True
                    continue
                items=varval.split(':',1)
                try: idx=self.choicelstdic0[name].index(items[0])
                except: idx=-1
                if idx < 0: self.choicelstdic0[name].append(items[0].strip())
                if len(items) >= 2:
                    namvarval=name+':'+varval
                    if not self.submenudic.has_key(namvarval):
                        self.submenudic[namvarval]=[]
                    self.submenudic[namvarval].append(items[1].strip())
        #self.choicelstdic0['Method'].insert(0,'None')
        #try: idx=self.choicelstdic0['Solvent'].index('None')
        #except: self.choicelstdic0['Solvent'].insert(0,'None')
        ###self.choicelstdic0['Properties'].insert(0,'None')
        
        self.choicelstdic=copy.deepcopy(self.choicelstdic0)
        #self.grimmdisp=False
        #
        """
        self.methodlst=self.choicelstdic['Method']
        self.runlst=self.choicelstdic['Run']
        self.wavelst=self.choicelstdic['Wave']
        self.basislst=self.choicelstdic['Basis']
        self.solventlst=['None']+self.choicelstdic['Solvent']
        self.propertieslst=['None']+self.choicelstdic['Properties']
        """
        #self.gmsrunmem='2'
        self.nlayer=1
        self.nbody=2
        
        #print 'choicelstdic',self.choicelstdic
        #print 'optiondic',self.optiondic
        #print 'submenudic',self.submenudic 
        
    def SetInitialValues(self):
        self.choicedic['Method']=self.choicelstdic['Method'][0]
        #self.method=self.methodlst[0]#
        self.jobtitle=self.gmsuser.jobtitle
        #self.run=self.runlst[0]
        self.choicedic['Run']=self.choicelstdic['Run'][0]
        #self.wave=self.wavelst[0]
        self.choicedic['Wave']=self.choicelstdic['Wave'][0]
        #self.basis=self.basislst[0]
        self.choicedic['Basis']=self.choicelstdic['Basis'][0]
        #self.solvent=self.solventlst[0]
        self.choicedic['Solvent']=self.choicelstdic['Solvent'][0]
        #self.properties=self.propertieslst[0]
        self.choicedic['Properties']=self.choicelstdic['Properties'][0]
        #self.gmsuser.grimmdisp=False
        self.spin='1'
        self.charge='0'
        #self.gmsrunmem='2'
        self.nlayer='1'
        #self.computer='1, 1, 2, 256'
        #self.gmsuser.nodes='1'
        #self.gmsuser.cores='1'
        #self.gmsuser.memory='1'
        #self.gmsuser.disk='256'

        self.nbody='2'
        #
        self.prvmethod=self.choicedic['Method']       
        # SetInputValue of 'Wave' and 'Basis'
        varval='Basis:'+self.choicedic['Basis']
        if self.uservarvaldic.has_key(varval):
            vals=self.uservarvaldic[varval]
            self.SetUserInputValues(vals,True)
        varval='Wave:'+self.choicedic['Wave']
        if self.uservarvaldic.has_key(varval):
            vals=self.uservarvaldic[varval]
            self.SetUserInputValues(vals,True)
        varval='Properties:'+self.choicedic['Properties']
        if self.uservarvaldic.has_key(varval):
            vals=self.uservarvaldic[varval]
            self.SetUserInputValues(vals,True)
        #
        self.gmsuser.properties='NPRINT=-5'
        self.gmsuser.prvproperties=self.gmsuser.properties
        #
        memory=str(int(self.gmsuser.memory)*1000/8-20)
        self.gmsuser.SetInputValue('$SYSTEM:MWORDS',memory,True)
        self.gmsuser.jobtitle=''
  
    def NoDocMessage(self):
        mess='GAMESSInput_Frm: No GAMESS Document data are available.'
        print mess
    
    def CreatePanel(self):
        
        self.comboboxdic={}; self.buttondic={}
        self.size=self.GetClientSize()
        w=self.size[0]; h=self.size[1]
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h),
                            style=wx.NO_BORDER) # wx.NO_BORDER disables wx.TAB_TRAVERSAL
        self.panel.SetBackgroundColour("light gray")
        xsize=w; ysize=h; wnmb=90; wtxt=140-wnmb; xtcl0=155; xtcl1=260; 
        #htcl=22; hcmb=20; wcmb=120
        #
        hcmb=20; wcmb=115
        yloc=5
        st11=wx.StaticText(self.panel,-1,"Method:",pos=(5,yloc+2),size=(50,20)) 
        st11.SetToolTipString('Select method')
        methodlst=self.choicelstdic['Method']
        cmbmeth=wx.ComboBox(self.panel,-1,'',choices=methodlst, \
                               pos=(60,yloc), size=(100,20),style=wx.CB_READONLY)                      
        cmbmeth.Bind(wx.EVT_COMBOBOX,self.OnComboBox)
        self.comboboxdic['Method']=cmbmeth
        cmbmeth.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #cmbmeth.SetValue(self.method)
        #st24=wx.StaticText(self.panel,-1,"n-layer",pos=(170,yloc+2),size=(45,18))
        #self.sclnlay=wx.SpinCtrl(self.panel,-1,value="1",pos=(215,yloc),size=(40,hcmb),
        #                      style=wx.SP_ARROW_KEYS,min=1,max=5)
        #self.sclnlay.Bind(wx.EVT_SPINCTRL,self.OnNLayer)
        wx.StaticLine(self.panel,pos=(170,yloc-5),size=(2,30),style=wx.LI_VERTICAL)
        btnopt=wx.Button(self.panel,-1,"OPTIONS",pos=(185,yloc),size=(70,22))
        btnopt.Bind(wx.EVT_BUTTON,self.OnButton) #ContrlOption)
        btnopt.SetToolTipString('Global options')
        self.buttondic['OPTIONS']=btnopt
        ##yloc2=33 # 30
        xloc=90; hcmb=20; wcmb=110
        yloc += 25
        sl12=wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        st22=wx.StaticText(self.panel,-1,"Job title:",pos=(5,yloc),size=(50,18)) 
        self.tcltit=wx.TextCtrl(self.panel,-1,self.gmsuser.jobtitle,pos=(60,yloc),size=(w-70,22))        
        self.tcltit.Bind(wx.EVT_TEXT,self.OnJobTitleChange)
        self.tcltit.Bind(wx.EVT_TEXT_ENTER,self.OnJobTitle)
        self.tcltit.SetValue(self.gmsuser.jobtitle)
        yloc += 30
        self.txtchg=wx.StaticText(self.panel,-1,"Charge:",pos=(5,yloc),size=(45,18)) 
        self.sclchg=wx.SpinCtrl(self.panel,-1,value="0.0",pos=(55,yloc),size=(52,hcmb),
                              style=wx.SP_ARROW_KEYS,min=-999)        
        self.sclchg.SetValueString(self.gmsuser.charge)
        #self.fmo=self.gmsrbt2.GetValue()
        ##if self.method != "MO": self.sclchg.Disable()
        self.txtspn=wx.StaticText(self.panel,-1,"Spin multiplicity:",pos=(120,yloc),size=(95,18))
        self.sclspn=wx.SpinCtrl(self.panel,-1,value="1",pos=(215,yloc),size=(45,hcmb),
                              style=wx.SP_ARROW_KEYS,min=1)
        self.sclspn.SetValueString(self.gmsuser.spin)
        # coordinate
        yloc += 25
        wx.StaticText(self.panel,-1,"Coordinate:",pos=(5,yloc+2),size=(70,18)) 
        #self.rbtcord1=wx.RadioButton(self.panel,-1,'internal',pos=(75,yloc+2),style=wx.RB_GROUP)
        #self.rbtcord2=wx.RadioButton(self.panel,-1,'read file',pos=(140,yloc+2))
        #self.rbtcord1.Bind(wx.EVT_RADIOBUTTON,self.OnCoordinate)
        self.btnintr=wx.Button(self.panel,-1,"From FU",pos=(75,yloc),size=(60,22))
        self.btnfile=wx.Button(self.panel,-1,"From file",pos=(140,yloc),size=(60,22))
        self.btnintr.Bind(wx.EVT_BUTTON,self.OnCoordinateFromFU)
        self.btnfile.Bind(wx.EVT_BUTTON,self.OnCoordinateFile)
        #self.btncord.SetStringSelection(self.coord)
        btncrd=wx.Button(self.panel,-1,"Option",pos=(210,yloc),size=(50,18))
        #self.btnrun.Disable()
        btncrd.Bind(wx.EVT_BUTTON,self.OnButton) #OnCoordinateOption)
        self.buttondic['Coordinate']=btncrd
        yloc += 25
        sl2=wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        #if self.method != "MO": self.sclspn.Disable()
        #
        ##yloc3=115 #122 #120 #115
        yloc += 5 #
        self.CreateRunTypePanel(yloc) #3)
        #
        yloc += 145
        sl3=wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        ##yloc4=yloc3+130 #128 #130 #112 #110
        yloc += 10 #8
        self.CreatePropertyPanel(yloc) #4)
        # computer
        ##yloc5=yloc4+140 #153 #150 #145
        yloc=h-95 #65 #90 #95 #105 #100
        #yloc += 70 #110 #130 #140 #=yloc5
        #self.CreateComputerPanel(yloc) #5)
        sl50=wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 10
        st50=wx.StaticText(self.panel,-1,"Computer nodes:",pos=(5,yloc+2),size=(100,18))
        #self.gmsbt5=wx.Button(self.panel,-1,">",pos=(w-18,yloc+7),size=(13,13))
        #self.gmsbt5.Bind(wx.EVT_BUTTON,self.GMSInputCompOptn)
        #   
        #st51=wx.StaticText(self.panel,-1,"nodes:",pos=(75,yloc+2),size=(40,18))
        self.tclnod=wx.TextCtrl(self.panel,-1,self.gmsuser.nodes,pos=(110,yloc),size=(40,20))        
        st52=wx.StaticText(self.panel,-1,"cores/node:",pos=(155,yloc+2),size=(70,18))
        self.tclcor=wx.TextCtrl(self.panel,-1,self.gmsuser.cores,pos=(230,yloc),size=(30,20))                
        self.tclnod.Bind(wx.EVT_TEXT,self.OnCompuNodes)
        self.tclcor.Bind(wx.EVT_TEXT,self.OnCompuCores)
        yloc += 25
        st53=wx.StaticText(self.panel,-1,"memory:",pos=(15,yloc+2),size=(50,18))
        self.tclmem=wx.TextCtrl(self.panel,-1,self.gmsuser.memory,pos=(70,yloc),size=(30,20))                
        #
        st54=wx.StaticText(self.panel,-1,"disk:",pos=(115,yloc+2),size=(30,18))
        self.tcldsk=wx.TextCtrl(self.panel,-1,self.gmsuser.disk,pos=(150,yloc),size=(50,20))                
        st531=wx.StaticText(self.panel,-1,"GB/node",pos=(205,yloc+2),size=(55,18))
        self.tclmem.Bind(wx.EVT_TEXT,self.OnCompuMemory)
        self.tcldsk.Bind(wx.EVT_TEXT,self.OnCompuDisk)
       #if self.method == "FMO": self.ckbpda.Disable()
        # Geometry input file
        ##yloc10=ysize-70 #62
        #yloc=h-35 #50 #45 # 38# += 55
        yloc += 25 #25
        linf=wx.StaticLine(self.panel,pos=(-1,yloc),size=(xsize,2),style=wx.LI_HORIZONTAL)    
        #yloc=h-28 #38 # += 8
        yloc += 8
        self.runbt=wx.Button(self.panel,wx.ID_ANY,"RunGMS",pos=(12,yloc),size=(55,20))
        self.runbt.Bind(wx.EVT_BUTTON,self.OnRunGAMESS)
        if not self.gmsuser.madeinput: self.runbt.Disable()
        hlv=h-yloc+5 #-2 #8
        linv=wx.StaticLine(self.panel,pos=(80,yloc-5),size=(2,hlv),style=wx.LI_VERTICAL)
        vwbt=wx.Button(self.panel,wx.ID_ANY,"View",pos=(90,yloc),size=(50,20))
        vwbt.Bind(wx.EVT_BUTTON,self.OnViewInput)
        apbt=wx.Button(self.panel,wx.ID_ANY,"Save",pos=(150,yloc),size=(50,20))
        apbt.Bind(wx.EVT_BUTTON,self.OnSave)
        clbt=wx.Button(self.panel,wx.ID_ANY,"Reset",pos=(210,yloc),size=(50,20))
        clbt.Bind(wx.EVT_BUTTON,self.OnReset)
    
    def CreateRunTypePanel(self,yloc):            
        # height=200
        yloc3=yloc
        w=self.size[0]; h=self.size[1]
        xloc=90 
        hcmb=20 # 25; 
        wcmb=105
        yloc += 3
        st31=wx.StaticText(self.panel,-1,"Run type:",pos=(5,yloc),size=(xloc,18)) 
        st31.SetForegroundColour("black")
        #self.runtypelst=self.abiruntypelst
        runlst=self.choicelstdic['Run']
        cmbrun=wx.ComboBox(self.panel,-1,'',choices=runlst, \
                               pos=(xloc+5,yloc), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        cmbrun.Bind(wx.EVT_COMBOBOX,self.OnComboBox) #RunInput)
        #cmbrun.SetValue(self.run)
        self.comboboxdic['Run']=cmbrun
        cmbrun.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        btnrun=wx.Button(self.panel,-1,"Option",pos=(xloc+wcmb+15,yloc),size=(50,18))
        #self.btnrun.Disable()
        btnrun.Bind(wx.EVT_BUTTON,self.OnButton)
        self.buttondic['Run']=btnrun
        #self.gmsbt1=wx.Button(self.panel,-1,">",pos=(xloc+wcmb+8,yloc),size=(13,13))
        #self.gmsbt1.Bind(wx.EVT_BUTTON,self.OnRunInputmore)
        ###self.cmbrun.SetStringSelection('energy')
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)        
        """
        yloc += 8
        st32=wx.StaticText(self.panel,-1,"Wave function:",pos=(5,yloc),size=(xloc,18)) 
        st32.SetForegroundColour("black")
        self.wfnlst=self.abiwfnlst
        self.cmbwfn=wx.ComboBox(self.panel,-1,'',choices=self.wfnlst, \
                               pos=(xloc+5,yloc), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        #self.cmbwfn.Bind(wx.EVT_COMBOBOX,self.OnInputWave)
        """
        yloc += 8
        st32=wx.StaticText(self.panel,-1,"Wave function:",pos=(5,yloc),size=(xloc,18)) 
        st32.SetForegroundColour("black")
        #self.wfnlst=self.abiwfnlst
        wavelst=self.choicelstdic['Wave']
        cmbwav=wx.ComboBox(self.panel,-1,'',choices=wavelst, \
                               pos=(xloc+5,yloc), size=(wcmb-35,hcmb),style=wx.CB_READONLY)                      
        cmbwav.Bind(wx.EVT_COMBOBOX,self.OnComboBox)
        #cmbwav.SetValue(self.wave)
        self.comboboxdic['Wave']=cmbwav
        cmbwav.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.cmbwfn.Bind(wx.EVT_COMBOBOX,self.OnInputWave)
        self.btndisp=wx.Button(self.panel,wx.ID_ANY,"-D",pos=(xloc+wcmb-25,yloc),size=(30,hcmb))
        self.btndisp.Bind(wx.EVT_BUTTON,self.OnButton) #Dispersion)
        self.btndisp.SetToolTipString("Use Gromm's empirical dispersion 2010")
        self.buttondic['-D']=self.btndisp
        if self.gmsuser.grimmdisp: self.btndisp.SetForegroundColour('red')
        else: self.btndisp.SetForegroundColour('black')
        #if self.method == "MO": self.cmbwfn.SetStringSelection('MP2(conventional')
        #if self.method == "FMO2": self.cmbwfn.SetStringSelection('RHF')
        btnwav=wx.Button(self.panel,-1,"Option",pos=(xloc+wcmb+15,yloc),size=(50,18))
        #self.gmsbt2.Disable()
        btnwav.Bind(wx.EVT_BUTTON,self.OnButton) #OnWaveOthers)
        self.buttondic['Wave']=btnwav
        yloc += 25
        self.txtbas=wx.StaticText(self.panel,-1,"Basis set:",pos=(5,yloc),size=(xloc,18)) 
        #st33.SetForegroundColour("black")
        #self.baslst=self.abibaslst
        basislst=self.choicelstdic['Basis']
        cmbbas=wx.ComboBox(self.panel,-1,'',choices=basislst, \
                               pos=(xloc+5,yloc), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        cmbbas.Bind(wx.EVT_COMBOBOX,self.OnComboBox)
        #cmbbas.SetValue(self.basis)
        self.comboboxdic['Basis']=cmbbas
        cmbbas.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.cmbbas.Bind(wx.EVT_COMBOBOX,self.OnInputBasis)
        #self.cmbbas.SetStringSelection('6-31G(d)')
        btnbas=wx.Button(self.panel,-1,"Others",pos=(xloc+wcmb+15,yloc),size=(50,18))
        #self.gmsbt3.Disable()
        btnbas.Bind(wx.EVT_BUTTON,self.OnButton)
        self.buttondic['Basis']=btnbas
        yloc += 25
        #layer apply
        self.txtlay=wx.StaticText(self.panel,-1,"Set to layer:",pos=(20,yloc),size=(70,18)) 
        self.scllay=wx.SpinCtrl(self.panel,-1,value="1",pos=(100,yloc),size=(40,20),
                              style=wx.SP_ARROW_KEYS,min=1,max=5)        
        self.scllay.Bind(wx.EVT_SPINCTRL,self.OnLayer)
        self.txtind=wx.StaticText(self.panel,-1,"",pos=(145,yloc+2),size=(10,18)) 
        #self.stlay.SetForegroundColour('gray')
        #self.scllay.Disable()
        self.btnlay=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(160,yloc),size=(45,20))
        self.btnlay.Bind(wx.EVT_BUTTON,self.OnLayerApply)
        self.btndel=wx.Button(self.panel,wx.ID_ANY,"Del",pos=(220,yloc),size=(35,18))
        self.btndel.Bind(wx.EVT_BUTTON,self.OnLayerDel)
        #self.btnlay.Disable()
        """
        yloc += 25
        wx.StaticText(self.panel,-1,"Empirical dispersion:",pos=(5,yloc+2),size=(120,18)) 
        cmbdisp=wx.ComboBox(self.panel,-1,'',choices=self.empdisplst, \
                               pos=(135,yloc), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        cmbdisp.Bind(wx.EVT_COMBOBOX,self.OnEmpiricalDisp)
        cmbdisp.SetStringSelection(self.empdisp)
        """
        yloc += 25
        wx.StaticLine(self.panel,pos=(-1,yloc),size=(w,2),style=wx.LI_HORIZONTAL)        
        yloc += 8
        #self.cmbslv.Disable()
        # solvent model
        st34=wx.StaticText(self.panel,-1,"Solvent model:",pos=(5,yloc+2),size=(xloc,18)) 
        st34.SetForegroundColour("black")
        solventlst=self.choicelstdic['Solvent']
        cmbslv=wx.ComboBox(self.panel,-1,'',choices=solventlst, \
                               pos=(xloc+5,yloc), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        cmbslv.Bind(wx.EVT_COMBOBOX,self.OnComboBox)
        #cmbslv.SetValue(self.solvent)
        self.comboboxdic['Solvent']=cmbslv
        cmbslv.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.cmbslv.SetStringSelection('None')
        btnslv=wx.Button(self.panel,-1,"Option",pos=(xloc+wcmb+15,yloc),size=(50,18))
        #self.gmsbt4.Disable()
        btnslv.Bind(wx.EVT_BUTTON,self.OnButton) #SolventOption)
        self.buttondic['Solvent']=btnslv
        
    def CreatePropertyPanel(self,yloc):
        w=self.size[0]; tcheight=self.size[1]-405 #375
        xloc=70 #90 
        hcmb=20 # 25; 
        wcmb=125

        yloc4=yloc; yloc41=yloc4-2; wh=22; ww=130
        #xloc=90; hcmb=20; wcmb=100
        stprp=wx.StaticText(self.panel,-1,"Properties:",pos=(5,yloc4),size=(60,18)) 
        stprp.SetToolTipString('Setect and/or input propeties directly (separated by a ",")')
        btnprp=wx.Button(self.panel,-1,"Option",pos=(xloc+wcmb+15,yloc4-2),size=(50,18))
        #self.gmsbt41.Disable()
        btnprp.Bind(wx.EVT_BUTTON,self.OnButton) #OnPropOthers)
        self.buttondic['Properties']=btnprp
        propertieslst=self.choicelstdic['Properties']
        cmbprp=wx.ComboBox(self.panel,-1,'',choices=propertieslst, \
                               pos=(xloc+5,yloc-2), size=(wcmb,hcmb),style=wx.CB_READONLY)                      
        cmbprp.Bind(wx.EVT_COMBOBOX,self.OnComboBox) #"Property)
        #cmbprp.SetValue(self.xxxxx)
        self.comboboxdic['Properties']=cmbprp
        cmbprp.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        #self.cmbprp.SetStringSelection('None')
        yloc += 25
        self.tclprp=wx.TextCtrl(self.panel,-1,'',pos=(10,yloc),size=(w-20,tcheight), # 25
                                style=wx.TE_MULTILINE|wx.TE_PROCESS_ENTER)
        self.tclprp.Bind(wx.EVT_TEXT_ENTER,self.OnProperty)
        self.tclprp.Bind(wx.EVT_TEXT,self.OnPropertiesChange)
        self.tclprp.SetValue(self.gmsuser.properties)
        #self.ckbden.Bind(wx.EVT_CHECKBOX,self.GMSInputDen)
        # FMO specific properties
        #yloc42=yloc41+3*wh+22
    
    def OnJobTitle(self,event):
        self.gmsuser.jobtitle=self.tcltit.GetValue().strip()
        self.tcltit.SetForegroundColour('black')
        
    def OnLayerDel(self,event):
        #ilay=self.scllay.GetValue()
        #if ilay == 1:
        #    mess='You can not delete the first layer'
        #    lib.MessageBoxOK(mess,'GMSBeginner(OnLayyerDel)')
        #    return
        self.ResetLayer()
        self.ShowLayerNumber()
        
    def ResetLayer(self):
        self.gmsuser.basislayer=5*[''] #[ilay]=''
        self.gmsuser.wavelayer=5*[''] #[ilay]=''
        self.gmsuser.basis='STO-3G' #self.gmsuser.basislayer[0]
        self.gmsuser.wave='RHF' #self.gmsuser.wavelayer[0]
        self.gmsuser.basislayer[0]=self.gmsuser.basis
        self.gmsuser.basislayer[0]=self.gmsuser.basis
        #
        self.comboboxdic['Basis'].SetValue(self.gmsuser.basis)
        self.comboboxdic['Basis'].Refresh()
        self.comboboxdic['Wave'].SetValue(self.gmsuser.wave)
        self.comboboxdic['Wave'].Refresh()
        self.gmsuser.nlayer=0
        self.scllay.SetValue(1)
        
    def OnJobTitleChange(self,event):
        self.tcltit.SetForegroundColour('gray')
        try: self.tclprp.SetForegroundColour('black')
        except:pass
        
    def OnComputerChange(self,event):
        #obj=event.GetEventObject()
        self.tclcomp.SetForegroundColour('gray')
        try: self.tclprp.SetForegroundColour('black')
        except: pass
        
    def OnPropertiesChange(self,event):
        #obj=event.GetEventObject()
        self.tclprp.SetForegroundColour('gray')
        
    def OnComputer(self,event):
        curval=self.computer.split(',')
        node=curval[0]; cores=curval[1]; memory=curval[2]; disk=curval[3]
        comp=self.tclcomp.GetValue()
        items=comp.split(',')
        if items[0] != '': nodes=items[0].strip()
        if len(items) >= 2 and items[1] != '': cores=items[1].strip()
        if len(items) >= 3 and items[2] != '': memory=items[2].strip()
        if len(items) >= 4 and items[3] != '': disk=items[3].strip()
        
        self.gmsuser.nodes=node
        self.gmsuser.cores=cores
        self.gmsuser.memory=memory
        self.gmsuser.disk=disk
        self.computer=nodes+', '+cores+', '+memory+', '+disk
        self.tclcomp.SetValue(self.computer)
        self.tclcomp.SetForegroundColour('black')
        #
        mem=str(int(self.gmsuser.memory)*1000/8-20)
        self.gmsuser.SetInputValue('$SYSTEM:MWORDS',mem,True)

    def OnCompuNodes(self,event):
        nodes=self.tclnod.GetValue()
        self.gmsuser.nodes=nodes.strip()
        
    def OnCompuCores(self,event):
        cores=self.tclcor.GetValue()
        self.gmsuser.cores=cores.strip()

    def OnCompuMemory(self,event):
        memory=self.tclmem.GetValue()
        self.gmsuser.memory=memory
        mem=str(int(self.gmsuser.memory)*1000/8-20)
        self.gmsuser.SetInputValue('$SYSTEM:MWORDS',mem,True)

    def OnCompuDisk(self,event):
        disk=self.tcldsk.GetValue()
        self.gmsuser.disk=disk.strip()

    def ResetChoiceList(self,cmbnam,value):
        """ Reset combobox choice list if needed
        
        :param obj cmbobj: combobox object
        :param str cmbnam: name of combobox stored in 'comboboxdic'
        :param str value: selected item in choice list        
        """
        cmbobj=self.comboboxdic[cmbnam]
        choicelst=copy.deepcopy(self.choicelstdic0[cmbnam])
        #try: idx=choicelst.index(value)
        #except: choicelst.append(value)
        if not value in choicelst: choicelst.append(value) 
        self.choicelstdic[cmbnam]=choicelst
        cmbobj.SetItems(choicelst)
        cmbobj.SetValue(value)
        cmbobj.Refresh()

    def EnableAllWidgets(self):
        # enable/disable widgets
        """
        !!! need set self.spin et al values for OnMove !!!
        
        :param str parmeth: parent method of selected 'Method'
        """
        
        for item,obj in self.comboboxdic.iteritems(): 
            obj.Enable(); self.widgetstatusdic['combo:'+item]=True    
        for item,obj in self.buttondic.iteritems(): 
            obj.Enable(); self.widgetstatusdic['button:'+item]=True
        # spin ctrl
        self.sclchg.Enable(); self.sclspn.Enable()
        #self.scllay.Disable(); self.stlay.SetForegroundColour('gray')
        # button color
        offcolor='black'; oncolor='red'
        self.btnintr.SetForegroundColour(offcolor)
        self.btnfile.SetForegroundColour(offcolor)
        self.btndisp.SetForegroundColour(offcolor)
        #
        #if parmeth == 'SEMIEMPIRICAL':
        self.comboboxdic['Basis'].Enable()
        self.btndisp.SetForegroundColour(offcolor)
        self.btndisp.Enable()
        #if parmeth == 'FMO':
        self.sclchg.Enable(); self.sclspn.Enable()
        self.EnableLayerWidgets(False)
            #self.scllay.Enable(); self.btnlay.Enable()
            #self.stlay.SetForegroundColour('black')
        self.enablecharge=True
        self.enablebasis=True
        self.enablelayer=True

        self.panel.Refresh()

    def GetWidgetValues(self):

        return
        
        
        
        
        
        # method
        curmeth=self.comboboxdic['Method'].GetValue()
        parmeth=self.GetParentMethod(curmeth)
        # jobtitle
        
        # spin ctrl
        ###self.sclchg.Enable(); self.sclspn.Enable()
        ###self.scllay.Disable(); self.stlay.SetForegroundColour('gray')
        ###self.btnlay.Disable()
        
        # dispersion
        self.GetAndSetDispersion()
        
        
        
        
        ###return
    
    
    
        for item,obj in self.comboboxdic.iteritems(): 
            obj.Enable(); self.widgetstatusdic['combo:'+item]=True    

        for item,obj in self.buttondic.iteritems(): 
            obj.Enable(); self.widgetstatusdic['button:'+item]=True
        # spin ctrl
        self.sclchg.Enable(); self.sclspn.Enable()
        self.scllay.Disable(); self.txtind.SetForegroundColour('gray')
        self.btnlay.Disable()
        # emprical disp
        offcolor='black'; oncolor='red'
        self.btnintr.SetForegroundColour(offcolor)
        self.btnfile.SetForegroundColour(offcolor)
        self.btndisp.SetForegroundColour(offcolor)
        #
        if parmeth == 'SEMIEMPIRICAL':
            self.comboboxdic['Basis'].Disable()
            self.btndisp.SetForegroundColour(offcolor)
            self.btndisp.Disable()
        if parmeth == 'FMO':
            self.sclchg.Disable(); self.sclspn.Disable()
            self.scllay.Enable(); self.btnlay.Enable()
            self.txtind.SetForegroundColour('black')
        self.panel.Refresh()
        
    def EnableLayerWidgets(self,enable):

        if enable:
            self.scllay.Enable(); self.btnlay.Enable(); self.btndel.Enable()
            self.txtlay.SetForegroundColour('black')
            self.btnlay.SetForegroundColour('black')
            self.btndel.SetForegroundColour('black')
            self.enablelayer=True
            self.ShowLayerNumber()
            self.OnLayer(1)
        else:
            self.scllay.Disable(); self.btnlay.Disable(); self.btndel.Disable()
            self.txtlay.SetForegroundColour('gray')
            self.btnlay.SetForegroundColour('gray')
            self.btndel.SetForegroundColour('gray')
            self.enablelayer=False
            self.gmsuser.nlayer=0
        self.txtlay.Refresh()
        self.scllay.Refresh(); self.btnlay.Refresh(); self.btndel.Refresh()
                        
    def EnableItemWidgets(self,item,enable):
        if enable:
            self.comboboxdic[item].Enable()
            self.widgetstatusdic['combo:'+item]=True
            self.buttondic[item].Enable()
            self.widgetstatusdic['button:'+item]=True
        else:
            self.comboboxdic[item].Disable()
            self.widgetstatusdic['combo:'+item]=False
            self.buttondic[item].Disable()
            self.widgetstatusdic['button:'+item]=False

    def EnableChargeSpinWidgets(self,enable):
        """ Enable/disable chrage and spin widgets
        
        :param bool enable: True for enable, False for disable
        """
        if enable:
            self.sclchg.Enable(); self.sclspn.Enable()
            self.txtspn.SetForegroundColour('black')
            self.txtchg.SetForegroundColour('black')
            self.enablecharge=True
        else:
            self.sclchg.Disable(); self.sclspn.Disable()
            self.txtspn.SetForegroundColour('gray')
            self.txtchg.SetForegroundColour('gray')
            self.enablecharge=False
        #self.sclchg.Refresh(); self.sclspn.Refresh()
        self.txtchg.Refresh();  self.txtspn.Refresh()  
    
    def EnableBasisWidgets(self,enable):
        """ Enable/disable chrage and spin widgets
        
        :param bool enable: True for enable, False for disable
        """
        if enable:
            self.comboboxdic['Basis'].Enable()
            self.buttondic['Basis'].SetForegroundColour('black')
            self.txtbas.SetForegroundColour('black')
            self.enablebasis=True
        else:
            self.comboboxdic['Basis'].Disable()
            self.buttondic['Basis'].SetForegroundColour('gray')
            self.txtbas.SetForegroundColour('gray')
            self.enablebasis=False
        #self.sclchg.Refresh(); self.sclspn.Refresh()
        self.txtbas.Refresh()
    
    def OnReset(self,event):
        self.ResetCoordButtonColor()
        self.gmsuser.ResetAllInputNames()
        self.SetInitialValues()
        

        #self.SetUserGroups()
        #self.comboboxdic['Method'].SetValue('ABINITIO')
        #method=self.comboboxdic['Method'].GetValue()
        self.gmsuser.jobtitle=''
        #self.tcltit.SetValue('')
        #self.GetAndSetProperties()
        #self.SetWidgets()
       
    def OnComboBox(self,event):

        obj=event.GetEventObject()
        #id=obj.GetId()
        item=''
        value=obj.GetValue()
        for label,object in self.comboboxdic.iteritems():
            if obj == object:
                item=label; break
        curmeth=self.comboboxdic['Method'].GetValue().strip()
        self.ComboBoxChoice(curmeth,item,value)
        
    def ComboBoxChoice(self,curmeth,item,value):    
        self.ResetChoiceList(item,value)
        #submenulst=self.MakeUserVarSubItemList(item,value)
        ###curmeth=self.comboboxdic['Method'].GetValue().strip()
        parmeth=self.GetParentMethod(curmeth)
        self.EnableAllWidgets()
        if curmeth == 'MFMO': self.EnableLayerWidgets(True)
        else: self.EnableLayerWidgets(False)
        #if curmeth == 'RESET':
        #    self.SetInitialValues()
        #    self.gmsuser.jobtitle=''

        
        if parmeth == 'SEMIEMPIRICAL':
            self.SetComboBoxChoiceList('Basis','None')
            self.EnableBasisWidgets(False)
            self.EnableItemWidgets('Basis',False)
        if parmeth == 'FMO': 
            self.EnableChargeSpinWidgets(False)
            self.gmsuser.coordinternal=False
            self.gmsuser.coordfile=False
            self.ChangeCoordButtonColor()
        
        
        #if curmeth != 'NFMO': self.EnableLayerWidgets(False)
        #print 'curmethod,prvmethod',curmeth,self.prvmethod
        varval=item+':'+value; vals=''

        if item == 'Method':
            #print 'parmeth in OnComboBox',parmeth
            winlabel=item+':'+value        
            submenulst=self.MakeUserVarSubItemList(item,value)
            #print 'submenulst',submenulst            
            
            if len(submenulst) > 2:  # '<close> and '' are in any case
                method=self.choicedic[item]
                menulabel=method+':'+value
                subtiplst=[]; submenudic={}; subtipdic={}
                #self.listboxmenu=self.gmsuser.OpenListBoxMenu(self,self.ReturnMethod,
                #                    submenulst,[],{},{},menulabel=winlabel)
                self.listboxmenu=self.gmsuser.OpenListBoxMenu(self,self.ReturnMethod,
                                            submenulst,subtiplst,submenudic,subtipdic,menulabel=winlabel)
            else:
                method=self.comboboxdic[item].GetValue()
                #print 'method',method
                self.SetComboBoxChoiceList('Method',value)
                #value=self.comboboxdic[item].GetValue()
                #
            if self.gmsuser.expertwin:
                self.inputer.OnClose(1)
                #namelst,namvarlstdic=
                namelst=self.SetOptionsForOPTIONS()
                self.gmsuser.expertwin=False
                self.OpenInputerWin('OPTIONS',namelst)
                #self.gmsuser.SetInputValue(namvar,value,True)
            #if curmeth != self.prvmethod and self.prvmethod != '':
            self.gmsuser.ResetAllInputNames()
            self.gmsuser.jobtitle=''
            self.GetAndSetProperties()
            #
            try: self.SetComboBoxChoiceList(item,obj.GetValue())
            except: pass
            #try: self.SetInitialValues()
            #except: pass
            try: self.SetWidgets()
            except: pass
            self.prvmethod=curmeth
            
        elif item == 'Run':
            self.run=value
            ###self.choicedic[item]=value
            #varval='Wave:'+value
            if self.uservarvaldic.has_key(varval):
                vals=self.uservarvaldic[varval]
                self.SetUserInputValues(vals,True)
        
        elif item == 'Wave':
            #print 'value',value
            self.wave=value
            """ """
            #submenulst=self.MakeUserVarSubItemList(item,value)
            submenulst=self.MakeVarSubItemListForWave(item,value)
            if len(submenulst) <= 0:
                if self.uservarvaldic.has_key(varval):
                    vals=self.uservarvaldic[varval]
                    self.SetUserInputValues(vals,True)
                ilayer=self.scllay.GetValue()
                ilayer=int(ilayer)
                #####self.gmsuser.wavelayer[ilayer-1]=value

            else:
                winlabel=item+':'+value
                self.listboxmenu=self.gmsuser.OpenListBoxMenu(self,self.ReturnMethod,
                                    submenulst,[],{},{},menulabel=winlabel)
        
        elif item == 'Basis':
            #print 'basis:value',value
            #self.basis=value
            self.SetComboBoxChoiceList('Basis',value)
            self.gmsuser.basis=value
            ilayer=self.scllay.GetValue()
            ilayer=int(ilayer)
            #####self.gmsuser.basislayer[ilayer-1]=value
            #varval='Basis:'+value
            if self.uservarvaldic.has_key(varval):
                vals=self.uservarvaldic[varval]
                self.SetUserInputValues(vals,True)
            #if parmeth == 'FMO' and self.fragdatafromfu:
            #    self.gmsuser.FMOBasisDataFromFU()
            
        elif item == 'Solvent':
            self.solvent=value
            if value.upper() == 'NONE': 
                set=False
                self.ResetUserGroupValues(item)
            else: 
                set=True
                if self.uservarvaldic.has_key(varval):
                    vals=self.uservarvaldic[varval]
                #print 'Solvent, varval,vals',varval,vals
            
                self.SetUserInputValues(vals,set)
            if parmeth == 'FMO': self.gmsuser.SetFMOPCMData()
            """ if Gradient: $PCM:PCMGRD, """
            
        elif item == 'Properties':
            #props=obj.GetValue()
            props=self.tclprp.GetValue().strip()
            if len(props) > 0: props=props+','
            if self.uservarvaldic.has_key(varval):
                vals=self.uservarvaldic[varval]
                set=True
                vallst=self.gmsinpobj.SplitValues(vals)
                valtxt=vallst[0].split(':')[1]
                props=props+valtxt
            props=self.RemoveDupProperty(props)
            self.gmsuser.properties=props #self.gmsuser.properties+','+props  
            self.tclprp.Clear()
            self.tclprp.SetValue(self.gmsuser.properties)
            self.tclprp.SetForegroundColour('black')
            self.tclprp.Refresh()
            #
            self.GetAndSetProperties()        
        else:
            print 'Program error in OnComboBox: item not found. item=',item
    
    def SetSelectedValueToComboBox(self,name,var,val):
        #name=name.strip(); var=var.strip(); val=val.strip()
        group=''
        for grpnam,varlst in self.uservarlstdic.iteritems():
            #try: 
            if var in varlst:
                #idx=varlst.index(var)
                group=grpnam; break
            #except: pass
        if name == '$BASIS': group='Basis'
        #print 'name,group,val',name,group,val
        if self.comboboxdic.has_key(group):
            
            #cmbobj=self.comboboxdic[group]
            self.ResetChoiceList(group,val)

    def SetUserInputValues(self,valstr,set):
        """
        
        :param bool set: True for set, False for unset
        """
        
        valstr=valstr.strip()
        items=self.gmsinpobj.SplitValues(valstr) # remove {} and split at ','
        nitems=len(items)
        for varval in items:
            varitems=varval.split('=')
            if len(varitems) == 1: # no '=' included
                pass # addo to option item
            else:
                namvar=varitems[0]
                value=varitems[1]
                self.gmsuser.SetInputValue(namvar,value,set)
    
    def ResetUserGroupValues(self,group):
        if len(group) <= 0: return
        if not self.uservarlstdic.has_key(group):
            mess='User group='+group+' is not defined'
            lib.MessageBoxOK(mess,'GMSBeginner:ResetUserGroupValues')
            return
        varlst=self.uservarlstdic[group]
        for varnam in varlst:
            grpvars=group+':'+varnam
            vartxt=self.uservarvaldic[grpvars]
            vars=self.gmsinpobj.SplitValues(vartxt)
            for namvar in vars: 
                nc=namvar.find('=')
                if nc >=0: namvar=namvar[:nc].strip()
                self.ResetUserInputValue(namvar)
                
    def ResetUserInputValue(self,namvar):
        """
        
        :param bool set: True for set, False for unset
        """
        value=self.gmsuser.GetDefaultNamVarValue(namvar)
        self.gmsuser.SetInputValue(namvar,value,False)
        #self.inputvaldic[namvar]=[defval,self.unsetcolor]
            
        return

    def DelNameInInput(self,name):
        if self.choicedic[name] != 'ABINITIO' and self.choicedic[name] != 'SEMIEMPIRICAL':
            del self.gmsuser.inputnamelst[name]
        """ del inputvaldic, textvaldic """

    def ReturnMethod(self,selected,winlabel):
        #print 'selected,winlabel',selected,winlabel
        
        items=winlabel.split(':')
        item=items[0].strip()
        value=items[1].strip()
        #self.SetComboBoxChoiceList(item,selected)
        #print 'item,value in returnmethod',item,value
        if item == 'Method':
            #
            if selected.upper() == 'NONE' or selected == '<cancel>' or selected == '': 
                self.SetComboBoxChoiceList(item,self.prvmethod)
                return
            self.SetComboBoxChoiceList(item,selected)
            if value == 'FMO':
                # set widget status
                if selected == 'MFMO': self.EnableLayerWidgets(True)
                #self.EnableChargeSpinWidgets(False)
                #
                fmoname=['$FMO','$FMOPRP']
                for name in fmoname: 
                    if not self.gmsuser.IsInputName(name):
                        self.gmsuser.AddInputNameAndVars(name,[])
                # FMO:IMOMM need '$QMMM' ???
                nbodydic={'FMO1':'1','FMO2':'2','FMO3':'3','MFMO':'2','FMO-IMOMM':'2'}
                if nbodydic.has_key(selected): nbody=nbodydic[selected]
                else: nbody='2'
                namvar='$FMO:NBODY'
                self.gmsuser.SetInputValue(namvar,nbody,True)

            elif value == 'SEMIEMPIRICAL':
                # set widget status
                #self.SetComboBoxChoiceList('Basis','None')
                #self.EnableItemWidgets('Basis',False)
                #
                unamvar='Method:'+value+':'+selected; namvarvaltxt=''
                if self.uservarvaldic.has_key(unamvar): 
                    namvarvaltxt=self.uservarvaldic[unamvar] 
                if len(namvarvaltxt) > 0:
                    namvarvaldic=self.GetUserNamVarValDic(namvarvaltxt)
                    set=True
                    if selected.upper() == 'NONE': set=False
                    for namvar,val in namvarvaldic.iteritems():
                        self.gmsuser.SetInputValue(namvar,val,set)
            else:
                namlst=self.uservarlstdic['Method:'+value]
                for name in namlst:
                    self.gmsuser.AddInputNameAndVars(name,[])

        elif item == 'Wave':
            if selected.upper() == 'NONE' or selected == '<cancel>' or selected == '': return
            self.SetComboBoxChoiceList(item,selected)
            namvar='$CONTRL:'+value
            #print 'namvar,selected in returnmethod',namvar,selected
            set=True
            if selected.upper() == 'NONE': set=False
            self.gmsuser.SetInputValue(namvar,selected,set)
            #
            ilayer=self.scllay.GetValue()
            ilayer=int(ilayer)
            self.gmsuser.wavelayer[ilayer]=selected
    
    def GetUserNamVarValDic(self,namvarvaltxt):
        """ usernamvartxt =[$BASIS:GBASIS=AM1] for SEMIEMPIRICAL:AM1
        :return: namvarvaldic - {namvar:val,...}, namvar '$BASIS:GBASIS'
        :return: value - value, e.g., 'AM1'
        """
        namvarvaldic={}
        if namvarvaltxt == '': return namvar,value
        namvarvallst=self.gmsinpobj.SplitValues(namvarvaltxt)
        for namvarval in namvarvallst:
            items=namvarval.split('=')
            namvar=items[0].strip()
            if len(items) >= 2: value=items[1].strip()
            else: value=''
            namvarvaldic[namvar]=value
        return namvarvaldic

    def MakeUserVarSubItemList(self,name,value):
        subitemlst=[]
        namvar=name+':'+value
        """
        for namvarval,val in self.submenudic.iteritems():
            items=namvarval.split(':')
            if len(items) <= 2: continue
            if len(items) >= 3:
                if items[0] != name: continue
                if items[1] != value: continue
                #if items[1] == 'OPTION': continue
                if items[2] == 'OPTION': continue
                subitemlst.append(items[2].strip())
        """
        # 'FMO' and 'SEMIEMPIRICAL' are treated specially just for keeping 
        # ordr of mneu item ( follow userinputdoc,xtx
        if namvar == 'Method:FMO':
            lst=[]; donedic={}
            fmomenulst=self.MakeGroupItemList('Method','FMO')
            for item in fmomenulst:
                lst.append(item); donedic[item]=True
            for item in subitemlst:
                if donedic.has_key(item): continue
                lst.append(item)
            subitemlst=lst
        elif namvar == 'Method:SEMIEMPIRICAL':
            lst=[]; donedic={}
            fmomenulst=self.MakeGroupItemList('Method','SEMIEMPIRICAL')
            for item in fmomenulst:
                lst.append(item); donedic[item]=True
            for item in subitemlst:
                if donedic.has_key(item): continue
                lst.append(item)
            subitemlst=lst
        else:
            for namvarval,val in self.submenudic.iteritems():
                items=namvarval.split(':')
                if len(items) <= 2: continue
                if len(items) >= 3:
                    if items[0] != name: continue
                    if items[1] != value: continue
                    #if items[1] == 'OPTION': continue
                    if items[2] == 'OPTION': continue
                    subitemlst.append(items[2].strip())

        if len(subitemlst) > 0: subitemlst=['None']+subitemlst
        return subitemlst

    def MakeVarSubItemListForWave(self,usergrpnam,varnam):
        """ usergrpnam=Wave, varnam=CITYP
        
        assume e.g., 'CITYP [$CONTRL:CITYP]' in 'Wave' group
        """
        itemlst=[]; namvar=''
        grpnamvar=usergrpnam+':'+varnam
        
        #print 'grpnamvar',grpnamvar
        if self.uservarvaldic.has_key(grpnamvar):
            namvar=self.uservarvaldic[grpnamvar]
        #print 'namvar',namvar
        if len(namvar) <= 0: return itemlst
        namvar=self.gmsuser.RemoveParenthesis(namvar)
        if self.gmsuser.varvaldic.has_key(namvar): 
            itemtxt=self.gmsuser.varvaldic[namvar]
            itemlst=self.gmsinpobj.SplitValues(itemtxt)
        #print 'itemlst in MakeVarSubItemListForWave',itemlst
        
        
        return itemlst
        
    def OnButton(self,event):

        # buttondic.keys:
        obj=event.GetEventObject()
        lab=obj.GetLabel()
        item=''
        for label,object in self.buttondic.iteritems():
            if obj == object:
                item=label; break
        #print 'item',item
        if self.gmsuser.expertwin: self.inputer.OnClose(1)
        if item == 'OPTIONS':
            wintitle='OPTIONS'
            self.SetOptionsForOPTIONS()
            self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) #,namvars)
            
        elif item == 'Coordinate':
            name='$CONTRL'; varlst=[]
            vartxt=self.uservarvaldic['Coordinate:OPTION']
            varitems=self.gmsinpobj.SplitValues(vartxt)
            for namvar in varitems:
                vars=namvar.split(':')
                if len(vars) >= 2: varlst.append(vars[1].strip())
            self.gmsuser.inpnamvardic={}
            self.gmsuser.inputnamelst=[]
            self.gmsuser.AddInputNameAndVars(name,varlst)
            wintitle='Options for '+item
            self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 

        elif item == 'Run':
           run=self.comboboxdic[item].GetValue()
           if run.upper() != 'NONE': 
               self.SetOptionsForUserGroup1(item,run)
               wintitle='Options for '+item
               self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 

        elif item == 'Wave':
            wave=self.comboboxdic[item].GetValue()
            """ for CCTYP ... $CCINP and $EOMINP """
            #self.SetOptionsForWavefunction(item,wave)
            self.SetOptionsForUserGroup1(item,wave)
            wintitle='Options for '+item
            self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 
            
        elif item == '-D':
            #print 'inputvaldic',self.gmsuser.inputvaldic
            if self.gmsuser.grimmdisp: self.gmsuser.grimmdisp=False
            else: self.gmsuser.grimmdisp=True
            self.ChangeDispButtonColor()
            self.GetAndSetDispersion()
            """
            if self.grimmdisp:
                self.gmsuser.SetInputValue('$DFT:DC','.T.',True)
                self.gmsuser.SetInputValue('$DFT:IDCVER','3',True)
            else:
                self.gmsuser.SetInputValue('$DFT:DC','.F.',False)
                self.gmsuser.SetInputValue('$DFT:IDCVER','3',False)     
            """
        elif item == 'Basis':
            bas=self.comboboxdic[item].GetValue()
            #print 'Basis option'
            #self.SetOptionsForWavefunction(item,wave)
            self.SetOptionsForUserGroup0(item,bas)
            wintitle='Options for '+item
            self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 

        elif item == 'Solvent':
           solv=self.comboboxdic[item].GetValue()
           if solv.upper() != 'NONE': 
               self.SetOptionsForUserGroup0(item,solv)
               wintitle='Options for '+item
               self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 
            
        elif item == 'Properties':
           prp=self.comboboxdic[item].GetValue()
           if prp.upper() != 'NONE': 
               self.SetOptionsForUserGroup1(item,prp)
               wintitle='Options for '+item
               self.OpenInputerWin(wintitle,self.gmsuser.inputnamelst) 
        else:
            print 'Program Error in OnButton: item not found. item=',item

    def GetAndSetBasis(self):
        userbasis=self.comboboxdic['Basis'].GetValue()
        
    
    def GetAndSetJobTitle(self):
        self.OnJobTitle(1)
            
    def GetAndSetRunType(self):
        pass
    
    def GetAndSetSpin(self):
        self.OnSpin()
        
    def GetAndSetCharge(self):
        self.OnCharge(1)
        
    def GetAndSetWaveFunction(self):
        pass
    
    def GetAndSetComputer(self):
        self.nodes=self.tclnod.GetValue()
        self.cores=self.tclcor.GetValue()
        self.memory=self.tclmem.GetValue()
        self.disk=self.tcldsk.GetValue()

    def GetAndSetMethod(self):
        method=self.comboboxdic['Method'].GetValue()
        
        
        #if method == 'FMO':
        
        nbodydic={'FMO1':'1','FMO2':'2','FMO3':'3','MFMO':'2','FMO-IMOMM':'2'}
        if nbodydic.has_key(selected): nbody=nbodydic[selected]
        else: nbody='2'
        namvar='$FMO:NBODY'
        self.gmsuser.SetInputValue(namvar,nbody,True)

    
    def GetAndSetDispersion(self):

        color=self.btndisp.GetForegroundColour()
        if color == 'red': self.gmsuser.grimmdisp=True #print 'test dispbutton color: red'
        if color == 'black': self.gmsuser.grommdisp=False #print 'test dispbutton color: black'
        #        
        if self.gmsuser.grimmdisp:
            self.gmsuser.SetInputValue('$DFT:DC','.T.',True)
            self.gmsuser.SetInputValue('$DFT:IDCVER','3',True)
        else:
            self.gmsuser.SetInputValue('$DFT:DC','.F.',False)
            self.gmsuser.SetInputValue('$DFT:IDCVER','3',False)     
        
    def SetOptionsForUserGroup0(self,grpnam,item):
        """ Set options for user group
        
        :param str grpnam: user group name, e.g.,'Solvent'
        :param str item: selected item in user group, e.g., 'PCM'
        :SeeAlso: SetOptionsForUserGroup1
        """
        self.gmsuser.inpnamvardic={}
        self.gmsuser.inputnamelst=[]
        if item.upper() == 'NONE': return
        if grpnam == 'Basis': 
            name='$BASIS'; varval=name
        else:
            varval=grpnam+':'+item; vals=''
            name='$'+item
        namvardic={}
        namvardic[name]=self.gmsuser.varlstdic[name]
        namvar=name
        # options
        optndic=self.GetUserOptions(grpnam,namvar)
        for name,optvarlst in optndic.iteritems():
            if not namvardic.has_key(name): namvardic[name]=[]
            namvardic[name]=namvardic[name]+optvarlst
        reqnamlst=self.gmsuser.GetRequiredNames(namvar,item)
        for name in reqnamlst: 
            if not namvardic.has_key(name): namvardic[name]=[]
            namvardic[name]=namvardic[name]+optvarlst
        #
        for name,varlst in namvardic.iteritems():
            self.gmsuser.AddInputNameAndVars(name,varlst)
                 
    def SetOptionsForUserGroup1(self,grpnam,item):
        """ Set selected variables in name group'
        
        :param str grpnam: user group name, e.g.,'Wave'
        :param str item: selected item in user group, e.g., 'CCTYP'
        :SeeAlso: SetOptionsForUserGroup0
        """
        self.gmsuser.inpnamvardic={}
        self.gmsuser.inputnamelst=[]
        if item.upper() == 'NONE': return
        varval=grpnam+':'+item; vals=''; namvar=''
        namvardic=self.MakeUserNameVarlstDic(varval)
        # options
        optndic=self.GetUserOptions(grpnam,namvar)
        for name,optvarlst in optndic.iteritems():
            if not namvardic.has_key(name): namvardic[name]=[]
            namvardic[name]=namvardic[name]+optvarlst
        # add required name group
        parnamvar=''
        if grpnam == 'Wave': parnamvar=self.GetParentWave(item)
        elif grpnam == 'Method': parnamvar=self.GetParentMethod(item)
        else: parnamvar=grpnam+':'+item
        grpitem=parnamvar.split(':')
        if len(grpitem) <= 1: grpitem=grpitem[0]
        else: grpitem=grpitem[1]
        grpvar=grpnam+':'+grpitem; namvar=''
        if self.uservarvaldic.has_key(grpvar):          
            namvar=self.uservarvaldic[grpvar]
            namvar=self.gmsuser.RemoveParenthesis(namvar)
        namvar=namvar.split('=')[0]
        reqnamlst=self.gmsuser.GetRequiredNames(namvar,item)
        for name in reqnamlst: 
            reqvarlst=self.gmsuser.varlstdic[name]
            if not namvardic.has_key(name): namvardic[name]=[]
            namvardic[name]=namvardic[name]+reqvarlst
        for name,varlst in namvardic.iteritems():
            self.gmsuser.AddInputNameAndVars(name,varlst)
    
    def MakeUserNameVarlstDic(self,grpnamvar):
        """
        
        :param str usergrpnamvar: user group name:var , e.g., 'Method:FMO'
        :return: namvardic - {name:[var,...],...}
        """
        namvardic={}; vals=''
        if self.uservarvaldic.has_key(grpnamvar):
            vals=self.uservarvaldic[grpnamvar]
        if len(vals) <= 0: return namvardic
        items=self.gmsinpobj.SplitValues(vals)
        for namvarval in items:
            namitems=namvarval.split(':')
            name=namitems[0].strip()
            #if donedic.has_key(name):
            #    namvardic[name]=[]
            #    continue
            if len(namitems) <= 1: continue
            varval=namitems[1].strip()
            vals=varval.split('=')
            if len(vals) >= 2:
                varlst=[vals[0]]
                namvar=name+':'+vals[0]
            else: varlst=self.gmsinpobj.SplitValues(varval)          
            if not namvardic.has_key(name): namvardic[name]=[]
            namvardic[name]=namvardic[name]+varlst
            
            #print 'namvardic in MakeUserNameVarlstDic',namvardic
            
            return namvardic

    def GetUserOptions(self,usergrpnam,namvar):
        optndic={}
        varnam=usergrpnam+':OPTION'
        dat=''
        if self.uservarvaldic.has_key(varnam): dat=self.uservarvaldic[varnam]
        if len(dat) <= 0: return optndic
        datitems=self.gmsinpobj.SplitValues(dat)
        #print 'datitems',datitems
        for txtdat in datitems: # txtdat:'$CONTRL:MPLEVL=[$CONTRL:SCFTYP]'
            items=txtdat.split('=')
            namv=items[0].strip(); onamvar=namv
            if namv != namvar: continue
            if len(items) >= 2: 
                onamvar=items[1].strip()
                """onamvar:[$CONTRL:SCFTYP', '$CCINP', '$EOMINP']  """
                namlst=self.gmsinpobj.SplitValues(onamvar)
                for namv in namlst:
                    varitems=namv.split(':')
                    name=varitems[0].strip(); var=''
                    if len(varitems) >= 2: var=varitems[1]
                    if not optndic.has_key(name): optndic[name]=[]
                    if var != '': optndic[name].append(var)
        
        #print 'optndic',optndic
        return optndic
    
    def SetOptionsForOPTIONS(self):
        """ Make namelst,namevardic for 'OPTIONS'

        :return: namelst  ['$CONTRL']
        :return: namvatlstdic - {'CONTROL':[var1,var2,...]}
        """
        self.gmsuser.inpnamvardic={}
        self.gmsuser.inputnamelst=[]

        method=self.comboboxdic['Method'].GetValue()
        methnam='Method:'+method

        # FMO
        #for grpnamvar,lst in self.uservarlstdic.iteritems():
        #    items=grpnamvar.split(':')
        #    if len(items) >= 3:
        #        if items[2].strip() == method: method='FMO'
        meth=self.GetParentMethod(method)
        #print 'meth in SetOptionsForOPTIONS',meth
        
        namvarlstdic={}
        name='$CONTRL'
        self.gmsuser.inputnamelst=[name]; namvarlstdic[name]=[]
        
        if meth != 'SEMIEMPRICAL':        
            varlst=self.uservarlstdic['OPTIONS']
            for var in varlst:
                if var == 'OPTION': continue
                namvarlstdic[name].append(var)
            self.gmsuser.AddInputNameAndVars(name,namvarlstdic[name])
            namtxt=self.uservarvaldic['OPTIONS:OPTION']
            namlst=self.gmsinpobj.SplitValues(namtxt)
            for name in namlst:
                self.gmsuser.AddInputNameAndVars(name,[])
                
        if meth == 'FMO': # and self.prvmethod != 'FMO':
            self.RemoveNameVarsOfPrvMethod()
            #for name in fmoname:
            #    #self.gmsuser.inputnamelst.append(name)
            #    self.gmsuser.AddInputNameAndVars(name,[])
            vartxt=self.uservarvaldic['Method:FMO:OPTION']
            varlst=self.gmsinpobj.SplitValues(vartxt)
            for name in varlst:
                #self.gmsuser.inputnamelst.append(name)
                self.gmsuser.AddInputNameAndVars(name,[])
            
        # other method, QMMM,DC,EL
        elif meth == 'SEMIEMPIRICAL':
            vartxt=self.uservarvaldic['Method:SEMIEMPIRICAL:OPTION']
            if vartxt != '[]':
                varlst=self.gmsinpobj.SplitValues(vartxt)
                #print 'SEMIEMPIRICAL:OPTION varlst',varlst
                namdic={}
                for namvar in varlst:
                    items=namvar.split(':')
                    name=items[0]; var=items[1]
                    if name != '$CONTRL': continue
                    if not namdic.has_key(name): namdic[name]=[]
                    namdic[name].append(var)
                    #self.gmsuser.inputnamelst.append(name)
                for name,varlst in namdic.iteritems():
                    self.gmsuser.AddInputNameAndVars(name,varlst)
            
        else:
            #print 'methnam',methnam
            if method != self.prvmethod: self.RemoveNameVarsOfPrvMethod()
            if self.uservarvaldic.has_key(methnam):
                varlst=self.uservarvaldic[methnam]        
                if varlst != '[]':
                    itemlst=self.gmsinpobj.SplitValues(varlst)
                    for var in itemlst:
                        if var == '': continue
                        var=var.strip()
                        #self.gmsuser.inputnamelst.append(var)
                        self.gmsuser.AddInputNameAndVars(var,[])
        self.prvmethod=meth

    def RemoveNameVarsOfPrvMethod(self):
        fmoname=['$FMO','$FMOPRP']
        #print 'prvmethod in RemoveNameVarsOfPrvMethod',self.prvmethod
        if self.prvmethod == 'FMO':
            for name in fmoname: self.gmsuser.RemoveInputName(name,[])
        else:
            name='Method:'+self.prvmethod
            if self.uservarvaldic.has_key(name):
                vartxt=self.uservarvaldic[name]
                      
                if vartxt != '[]':
                    itemlst=self.gmsinpobj.SplitValues(vartxt)
                    for var in itemlst:
                        var=var.strip()
                        if var == '': continue
                        self.gmsuser.RemoveInputName(var,[])

    def GetParentMethod(self,method):
        meth=method
        for namvar in self.uservarlstdic['Method']:
            namvarlst=self.gmsinpobj.SplitValues(namvar)
            for nam in namvarlst:
                items=nam.split(':')
                if len(items) < 2: continue
                if items[1] == method: meth=items[0].strip()
        return meth
    
    def GetParentWave(self,userval):
        parnamvar=''; parvar=''
        #print 'userval',userval
        wave='Wave'; found=False
        for uvartxt in self.uservarlstdic[wave]:
            if found: break
            varlst=self.gmsinpobj.SplitValues(uvartxt)
            for varnam in varlst:
                if found: break
                itemlst=self.MakeVarSubItemListForWave(wave,varnam)
                #itemlst=self.MakeUserVarSubItemList(wave,varnam)
                for var in itemlst:
                    if var == userval:
                        parvar=varnam
                        found=True; break
        if len(parvar) <= 0: return parnamvar
        namvartxt=self.uservarvaldic[wave+':'+parvar]
        namvarlst=self.gmsinpobj.SplitValues(namvartxt)
        name=namvarlst[0].split(':')[0]
        parnamvar=name+':'+parvar
        return parnamvar

    def MakeBasisData(self,basis):
        """ 
        :param str basis: Basis set name defined in userinputdoc.txt
        :return: basdat (lst) - [basbam(str),ngauss(str),ndfunc(str)]
        """
        if basis == '': return []
        basdatlst=[]
        uservarval='Basis:'+basis
        vals=''
        if self.uservarvaldic.has_key(uservarval):
            vals=self.uservarvaldic[uservarval]
        
        #print 'uservarval,vals',uservarval,vals
        
        vallst=self.gmsinpobj.SplitValues(vals)

        valdic={}
        for namvarval in vallst:
            varval=namvarval.split(':',1)
            items=varval[1].split('=')
            valdic[items[0]]=items[1]
        basnam=''; ngauss=''
        if valdic.has_key('GBASIS') and valdic.has_key('NGAUSS'):
            basnam=valdic['GBASIS']; ngauss=valdic['NGAUSS']
        ndfunc=''
        if valdic.has_key('NDFUNC'): ndfunc=valdic['NDFUNC']
        basdatlst=[basnam,ngauss,ndfunc]
        
        return basdatlst
    
    def GetBasisNDFUNCExponent(self,basnam,elm):
        expval=''; expdic={}
        uservarval='Basis:'+basnam+':NDFUNC'
        exptxt=''
        if self.uservarvaldic.has_key(uservarval):
            exptxt=self.uservarvaldic[uservarval]
        
        explst=self.gmsinpobj.SplitValues(exptxt)
        for elmexp in explst:
            #if elmexp[0] == "'": elmexp=elmexp[1:]
            #if elmexp[-1] == "'": elmexp=elmexp[:-1]
            items=elmexp.split(':')
            if len(items) < 2: continue
            elm=lib.AtmNamToElm(items[0])
            expdic[elm]=items[1]
        if expdic.has_key(elm): expval=expdic[elm]
        else: expval='Not defined in FU. Please manual edit this.' 
        return expval
        
    def ChangeDispButtonColor(self):
        btncolor='black'
        if self.gmsuser.grimmdisp: btncolor='red'  
        self.btndisp.SetForegroundColour(btncolor)
        
    def OnCoordinateFromFU(self,event):
        """ Event handler to get coordinate data from FU
        
        """
        method=self.comboboxdic['Method'].GetValue()
        self.CoordinateFromFU(method)
        
    def CoordinateFromFU(self,method,check=True):     
        nlayer,dumlst=self.model.frag.ListAtomLayer()
        if method == 'MFMO' and self.gmsuser.nbasislayer < nlayer:
            mess='Number of layers in fumodel='+str(nlayer)+'\n'
            mess=mess+'Input higher layer wavefunction/basis set.'
            lib.MessageBoxOK(mess,'GMSBeginner(OnCoordinateFromFU)')
            return
        parmeth=self.GetParentMethod(method).strip()
        
        if parmeth == 'FMO':
            nochgfrg=self.model.frag.ListNoneChargeFragment()
            if len(nochgfrg) > 0:
                mess='There are '+str(len(nochgfrg))+' unassigned charges in '
                mess=mess+'fragments.\n'
                mess=mess+'Are they all zeros?'
                ans=lib.MessageBoxYesNo(mess,'Fragment(SaveBDA')
                if ans: self.model.frag.SetAllFragmentCharges(0)
                else: return                   
            else: 
                self.gmsuser.SetAllFMOValueFromFU() #'$FMOXYZ:$FMOXYZ')
                self.gmsuser.fragdatafromfu=False
                self.tcltit.SetValue(self.gmsuser.jobtitle)
                
                #if not self.model.mol.IsAttribute('ICHARG'):
                #    frgchglst=self.model.ListFragmentCharge()
                #    self.model.mol.SetFragmentAttributeList('ICHARG',frgchglst)                
                """
                nochgfrg=self.model.frag.ListNoneChargeFragment()
                if len(nochgfrg) > 0:
                    mess='There are '+str(len(nochgfrg))+' unassigned charges in '
                    mess=mess+'fragments.\n'
                    mess=mess+'Are they all zeros?'
                    ans=lib.MessageBoxYesNo(mess,'Fragment(SaveBDA')
                    if ans: self.model.frag.SetAllFragmentCharges(0)
                    else: return
                """
        else: 
            text=self.gmsuser.SetCoordFromFU()
            self.tcltit.SetValue(self.gmsuser.jobtitle)
            
        self.gmsuser.coordinternal=True
        self.gmsuser.coordfile=False
        self.ChangeCoordButtonColor()
        
    def OnCoordinateFile(self,event):
        """ Event handler to read coordinate data from file
        
        """
        self.btnfile.SetForegroundColour('red')
        self.btnintr.SetForegroundColour('black')
        wcard='pdb file(*.pdb;*.ent)|*.pdb;*.ent|xyz(*.xyz)|*.xyz'
        filename=lib.GetFileName(None,wcard,'r',True,'')
        if len(filename) <= 0: 
            self.btnfile.SetForegroundColour('black')
            return
        #
        base,ext=os.path.splitext(filename)
        if ext == '.pdb' or ext == '.ent' or ext == 'xyz':
            self.mdlwin.model.ReadFiles(filename,True)
            self.gmsuser.SetCoordFromFU()
        else: self.gmsuser.SetCoordFromFile(filename)
        #
        #self.gmsuser.jobtitle=filename[:70]          
        #self.tcltit.SetValue(self.gmsuser.jobtitlee)
        self.gmsuser.SetJobTitleToWidget(filename[:70])
        self.gmsuser.coordinternal=False
        self.gmsuser.coordfile=True
        
        self.gmsuser.fragdatafromfu=False
        self.ChangeCoordButtonColor()
        
    def OnViewInput(self,event):
        """ View current input data """
        
        self.GetWidgetValues()
        
        method=self.comboboxdic['Method'].GetValue()  
        parmeth=self.GetParentMethod(method).strip()
        if parmeth == 'FMO':
            if not self.model.mol:
                mess='Molecule is not ready in fumodel.'
                lib.MessageBoxOK(mess,'GMSUser(SetAllFMOValueFromFU)')
                return
            self.gmsuser.SetAllFMOValueFromFU() 
        
        self.gmsuser.ViewCurrentData()
        
    def OpenInputerWin(self,wintitle,inputnamelst): #,namvarlst):     
        if self.gmsuser.expertwin: return
        if len(inputnamelst) <= 0: return
        
        parpos=self.GetPosition()
        parsize=self.GetSize()
        winpos=[parpos[0]+parsize[0],parpos[1]+20]
        winsize=self.inputerwinsize
        #print 'inputvaldic[$CONTRL:MP2 in OpenInputer',self.gmsuser.inputvaldic['$CONTRL:MP2']
        mode=0
        self.inputer=GMSExpert_Frm(self.mdlwin,-1,self.gmsuser,mode,inputnamelst,
                                   winpos=winpos,winsize=winsize)
                                   #self.inputvaldic,self.textvaldic,self.gmsdoc,winpos=winpos,winsize=winsize)
        self.gmsuser.expertwin=True

    def OnCoordinateOption(self,event):
        if len(self.gmsdoc) <= 0:
            self.NoDocMessage(); return

        try: self.selectbox.Destroy()
        except: pass
        #print 'Enter OnCoordOption',self.selectbox
        
        choicelst=['$ZMAT1','$ZMAT2','$ZMAT3']
        choicetip=['tip1','tip2','tip3']
        varlst=['$ZMAT:IZMAT','$ZMAT:DLC','$ZMAT:AUTO']
        vartip=[]
        valdic={'$ZMAT:IZMAT':[],'$ZMAT:DLC':[],'$ZMAT:AUTO':[]}
        valtipdic={'$ZMAT:IZMAT':'description',}
        title='Coordinate Option: '+self.datanem
        parpos=self.GetPosition()
        parsize=self.GetSize()
        winpos=[parpos[0]+parsize[0],parpos[1]+20]; winsize=[285,400]
        #
        inputdoc=[]
        inputer=Inputer_Frm(self,-1,winpos,winsize,title,0,inputdoc)

        done=False; ret=False


        #print 'ret',ret
        #print 'inputer.selected',inputer.selected
        #selectbox.Destroy()
        #while done == False:
        #    done=self.selectbox.done
        
        #self.selected=self.selectbox.selected
        
        #self.selectbox.Destroy()
            
        #print 'End coordoption',self.selected
        
    def ResetCoordButtonColor(self):
        self.gmsuser.coordinternal=False
        self.gmsuser.coordfile=False
        self.btnintr.SetForegroundColour('black')
        self.btnfile.SetForegroundColour('black')
    
    def ChangeCoordButtonColor(self):
        offcol='black'; oncol='red'
        self.btnintr.SetForegroundColour(offcol)
        self.btnfile.SetForegroundColour(offcol)
        if self.gmsuser.coordinternal: intrcol='red' #'brown'
        else: filecol='red' #'brown'
        if self.gmsuser.coordinternal: 
            self.btnintr.SetForegroundColour(intrcol)
        if self.gmsuser.coordfile: self.btnfile.SetForegroundColour(filecol)
              
    def ReturnValue(self,value,label):
        #print 'label,value',label,value
        if value == '<close>' or value == '':
            self.method=self.prvmethod
        else:
            self.method=self.prvmethod
            items=value.split(':',1)
            nitems=len(items)
            if label == 'Method': 
                if nitems == 1: ith=0
                elif nitems == 2: ith=1
                if items[ith] != '<close>' and items[ith] != '' : 
                    self.method=value
        self.SetItemsToMethod()

    def SetComboBoxChoiceList(self,name,choice):
        combo=self.comboboxdic[name]
        self.choicelstdic[name]=copy.deepcopy(self.choicelstdic0[name])
        #try: idx=self.choicelstdic0[name].index(choice)
        #except: self.choicelstdic[name].insert(0,choice)
        if not choice in self.choicelstdic[name]: self.choicelstdic[name].insert(0,choice)
        
        combo.SetItems(self.choicelstdic[name])
        combo.SetValue(choice)
        self.choicedic[name]=choice
        combo.Refresh()
        
    def RemoveDupProperty(self,props):
        properties=''; donedic={}
        items=self.gmsinpobj.SplitValues(props)
        
        for varval in items:
            var=varval.split('=')[0].strip()
            if donedic.has_key(var): continue
            properties=properties+varval+','
            donedic[var]=True
        if len(properties) > 0: properties=properties[:-1]
        return properties
    
    def GetAndSetProperties(self):
        prptxt=self.tclprp.GetValue().strip()
        prplst=self.gmsinpobj.SplitValues(prptxt)  
        prvprplst=self.gmsinpobj.SplitValues(self.gmsuser.prvproperties)   
        unsetvardic={}; alllst=[]
        for old in prvprplst:
            oldvar=old.split('=')[0].strip()
            find=False
            for new in prplst:
                newvar=new.split('=')[0].strip() 
                if newvar == oldvar: 
                    find=True; break
            if not find: 
                unsetvardic[oldvar]=True
                alllst.append(old)
        alllst=prplst+alllst
        for varval in alllst:
            var=''; val=''
            items=varval.split('=')
            var=items[0].strip()
            if var == '': continue
            if len(items) > 1: val=items[1].strip()
            if val == '': continue 
            uvarval='Properties:'+var
            set=True
            if unsetvardic.has_key(var): set=False
            if self.uservarvaldic.has_key(uvarval):
                vals=self.uservarvaldic[uvarval]
                vallst=self.gmsinpobj.SplitValues(vals)
                if len(vallst) <= 0: continue
                namvar=vallst[0]
                namvar=namvar.split('=')[0].strip()
                self.gmsuser.SetInputValue(namvar,val,set)
            else:
                mess=uvarval+' is not defined.'
                lib.MessageBoxOK(mess,'GMSBeginner(GetANdSetProperties')
            #
            self.gmsuser.prvproperties=prptxt    
    
    def OnProperty(self,event):       
        props=self.tclprp.GetValue().strip()
        props=self.RemoveDupProperty(props)
        items=self.gmsinpobj.SplitValues(props)
        mess=''; props=''
        for varval in items:
            var=varval.split('=')[0].strip()
            uvarval='Properties:'+var
            if not self.uservarvaldic.has_key(uvarval): mess=mess+var+','
            else: props=props+varval+','
        if len(mess) > 0:
            mess='Undefined variables: '+mess
            lib.MessageBoxOK(mess,'GMSBeginner(ObComboBox)')
        if len(props) > 0: props=props[:-1]
        self.gmsuser.properties=props
        self.tclprp.Clear()
        self.tclprp.SetValue(self.gmsuser.properties)
        self.tclprp.SetForegroundColour('black')
        self.tclprp.Refresh()
        #
        self.GetAndSetProperties()
                    
    def GetMaxLayer(self):
        lay=[]; maxlay=0
        for atom in self.mol.atm: lay.append(atom.layer)
        return max(lay)
            
    def OnLayer(self,event):
        ilay=int(self.scllay.GetValue())
        if ilay <= self.gmsuser.nlayer:
            self.comboboxdic['Wave'].SetValue(self.gmsuser.wavelayer[ilay-1])
            self.comboboxdic['Wave'].Refresh()
            self.comboboxdic['Basis'].SetValue(self.gmsuser.basislayer[ilay-1])
            self.comboboxdic['Basis'].Refresh()
        
    def OnLayerApply(self,event):
        lay=self.scllay.GetValue()
        ilay=int(lay)
        self.gmsuser.nbasislayer=max(ilay,self.gmsuser.nbasislayer)
        wave=self.comboboxdic['Wave'].GetValue()
        basis=self.comboboxdic['Basis'].GetValue()
        self.gmsuser.wavelayer[ilay-1]=wave
        self.gmsuser.basislayer[ilay-1]=basis
        #
        self.gmsuser.nlayer=max(ilay,self.gmsuser.nlayer)
        self.ShowLayerNumber()

    def ShowLayerNumber(self):
        """ Show layer number in red color """
        if self.enablelayer and self.gmsuser.nlayer > 0:
            self.txtind.SetLabel(str(self.gmsuser.nlayer))
            self.txtind.SetForegroundColour('red')
        else: self.txtind.SetLabel('')
        self.txtind.Refresh()
            
    def OnSpin(self,event):
        self.spin=str(self.sclspn.GetValue())
        self.gmsuser.spin=self.spin
        self.gmsuser.SetInputValue('$CONTRL:MULT',self.spin,True)
        
    def OnCharge(self,event):
        self.charge=str(self.sclchg.GetValue())
        self.gmsuser.charge=self.charge
        self.gmsuser.SetInputValue('$CONTRL:ICHARG',self.charge,True)

    def OpenEditor(self):
        filename=self.gmsinputfile
        if len(filename) <= 0:
            mess='GAMESS input file is not exist.'
            self.model.Message(mess,0,"")
        # open editor
        else:
            lib.Editor(filename)
         
    def OnNodes(self,event):
        self.nodes=self.tclnod.GetValue()
    def OnCores(self,event):
        self.cores=self.tclcor.GetValue()
    def OnMemory(self,event):
        self.memory=self.tclmem.GetValue()
    def OnDisk(self,event):
        self.disk=self.tcldsk.GetValue()

    def CheckFileExist(self,filename):
        exist=os.path.exists(filename)
        if exist: return True
        else:    
            #dlg=wx.MessageDialog(self,"%s ... file not found. Re-enter." % filename,
            #         "GAMESS INPUT ASISTANT",style=wx.OK|wx.ICON_EXCLAMATION)
            #if dlg.ShowModal() == wx.ID_OK:    
            mess="%s ... file not found. Re-enter." % filename
            lib.MessageBoxOK(mess,"GAMESS INPUT ASISTANT")
            return False
        
    def OnSave(self,event):
        self.GetWidgetValues()

        method=self.comboboxdic['Method'].GetValue()  
        parmeth=self.GetParentMethod(method).strip()
        if parmeth == 'FMO':
            if not self.model.mol:
                mess='Molecule is not ready in fumodel.'
                lib.MessageBoxOK(mess,'GMSUser(SetAllFMOValueFromFU)')
                return
            self.gmsuser.SetAllFMOValueFromFU() 
        
        self.gmsuser.SaveInput()
                         
    def OnPaint(self,event):
        event.Skip()
    
    def OnResize(self,event):
        self.OnMove(1)
        
    def OnMove(self,event):
        #savopenlistctrlwin=self.openlistboxmenu
        self.panel.Destroy()
        #if self.openlistboxmenu: 
        #    self.listboxmenu.Destroy()
        #    self.openlistboxmenu=False
        self.SetMinSize(self.winsize)
        self.SetMaxSize([self.winsize[0],2000])
        self.CreatePanel()
        #self.SetValueToComboBox()
        self.SetWidgets()
        #if savopenlistctrlwin: self.OnGridRightClick(1)

    def OnMouseWheel(self,event):
        pass
            
    def OnClose(self,event):
        self.Close()

        #if self.gmsuser.flags.Get(self.gmsuser.exewinlabel):
        #    mess='Execute program window is open. Please close it.'
        #    lib.MessageBoxOK(mess,'GMSBeginner(OnClose)')
        #    return
    def Close(self):
        try: self.gmsuser.expertwin=False
        except: pass
        
        try: self.gmsuser.expert.listboxmenu.Destroy()
        except: pass
        
        try: self.gmsuser.editor.Destroy()
        except: pass
        
        try: self.inputer.listboxmenu.Destroy()
        except: pass
        
        try: self.inputer.Destroy()
        except: pass

        try: self.gmsuser.execbatwin.Destroy()
        except: pass
        
        self.gmsuser.childobj.Del('gamess-user')
        self.gmsuser.ctrlflag.Del('gamess-user')
        
        self.Destroy()

    def LoadGAMESSInputFile(self,filename):
        """
        
        :param int case: 0 for input (1 for template, not supported)
        """
        self.gmsuser.OpenInputFile(filename)
        curdir=lib.ChangeToFilesRootDir(filename)
        
        self.tcltit.SetValue(filename[:70])
        self.readfilename=filename
        #
        self.gmsuser.coordinternal=False
        self.gmsuser.coordfile=True
        self.ChangeCoordButtonColor()
        
        self.SetUserGroups()
    
    def SetUserGroups(self):
        """ Set Widgets choice according to input data
         
        """
        unidentify='Unidentyfied'
        for grpnam in self.usernamelst:
            if grpnam == 'Method':
                self.choicedic[grpnam]='ABINITIO'
                found=False
                namvar='$FMO:NBODY'
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    found=True
                    self.choicedic[grpnam]='FMO'+val 
                    #print '$FMO:NBODY, val',val
                # Layer for FMO
                namvar='$FMO:NLAYER'
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    val=int(val)
                    if val > 1: 
                        self.choicedic[grpnam]='MFMO'
                        found=True
                        #print '$FMO:NLAYER',val
                if found: continue
                # SEMIEMPIRICAL
                namvar='$BASIS:GBASIS'
                semi=self.MakeGroupItemList(grpnam,'SEMIEMPIRICAL')
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    #try:
                    if val in semi:
                        #idx=semi.index(val)
                        self.choicedic[grpnam]=val
                        found=True
                    #except: pass
                if found: continue
                
                # Layer for FMO
                namvar='$DANDC:NSUBS'
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    self.choicedic[grpnam]='DANDC'
                    found=True
                if found: continue
                
                namvar='$ELG:NELONG'
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    self.choicedic[grpnam]='ELG'
                    found=True
                if found: continue
                
                """ need more codes ? """
                
                
            elif grpnam == 'Run':
                found=False
                namvar='$CONTRL:RUNTYP'
                val=self.gmsuser.GetSettedNamVarValue(namvar)
                if val != '':
                    runlst=self.gmsuser.uservarlstdic[grpnam]
                    #try:
                    if val in runlst:
                        #idx=runlst.index(val)
                        self.choicedic[grpnam]=val
                        found=True
                    else: self.choicedic[grpnam]=val
                else: self.choicedic[grpnam]=unidentify
            elif grpnam == 'Wave':
                found=False
                self.choicedic[grpnam]='RHF'
                wavelst=self.gmsuser.uservarlstdic[grpnam]
                for wave in wavelst:
                    if wave == 'OPTION': continue
                    unamvar=grpnam+':'+wave
                    if self.gmsuser.uservarvaldic.has_key(unamvar):
                        namvar=self.uservarvaldic[unamvar]      
                        namvar=self.gmsuser.RemoveParenthesis(namvar)
                        namvar=namvar.split('=')[0].strip()
                        val=self.gmsuser.GetSettedNamVarValue(namvar)
                        if val == '0' or val == '2': val='MP2'
                        if val != '':
                            #try:
                            if val in wavelst:
                                #idx=wavelst.index(val)
                                self.choicedic[grpnam]=val
                                found=True
                            #except: pass
                if not found: self.choicedic[grpnam]=unidentify
                
            elif grpnam == 'Basis':
                namvars=['$BASIS:GBASIS','$BASIS:NGAUSS','$BASIS:NDFUNC']
                values=['','','']
                for i in range(len(namvars)):
                    namvar=namvars[i]
                    values[i]=self.gmsuser.GetSettedNamVarValue(namvar)
                value=''
                if values[0] == 'STO' and values[1] == '3': value='STO-3G'
                if values[0] == 'N31' and values[1] == '6': 
                    value='6-31G'
                    if values[2] == '1': value='6-31G*'
                if values[0] == 'N311' and values[1] == '6':
                    value='6-311G'
                    if values[2] == '1': value='6-311G*'
                if value == '' and values[0] != '': value=values[0]+', '+values[1]
                if values[0] == 'CCD': value='cc-pVDZ'
                if values[0] == 'ACCD': value='aug-cc-pVDZ'
                if values[0] == 'CCT': value='cc-pVTZ'
                if values[0] == 'ACCT': value='aug-cc-pVTZ'                
                if value == '': value=unidentify
                self.choicedic[grpnam]=value
            elif grpnam == 'Solvent':
                namvars=['$PCM','$SVP','$EFRAG']
                value='None'
                for namvar in namvars:
                    solv=self.gmsuser.GetSettedNamVarValue(namvar)
                    if solv != '': value=solv
                self.choicedic[grpnam]=value
            elif grpnam == 'Properties':
                namvar='$CONTRL:NPRINT'
                value='NPRINT=-5'
                prop=self.gmsuser.GetSettedNamVarValue(namvar)
                if prop != '': value=prop
                self.tclprp.SetValue(value)
                self.tclprp.Refresh()         
            elif grpnam == 'Charge':
                namvar='$CONTRL:ICHARG'
                chg=self.gmsuser.GetSettedNamVarValue(namvar)
                if chg != '': 
                    value=chg; self.gmsuser.charge=chg
                    self.sclchg.SetValueString(self.gmsuser.charge)
                    self.sclchg.Refresh()
            elif grpnam == 'Spin':
                namvar='$CONTRL:MULT'
                mult=self.gmsuser.GetSettedNamVarValue(namvar)
                if mult != '': 
                    value=mult; self.gmsuser.spin=mult
                    self.sclspn.SetValueString(self.gmsuser.spin)
                    self.sclspn.Refresh()
            elif grpnam == 'Coordinate':
                pass    
            elif grpnam == 'Job':
                pass
            elif grpnam == 'Computer':
                pass
        #
        self.SetValueToComboBox()
    
    def SetMethod(self,meth):
        self.comboboxdic['Method'].SetValue(meth)
        
    def SetWidgets(self):
        # combobox
        #labeldic={'Method':[self.method,self.methodlst],
        #          'Run':[self.run,self.runlst],
        #          'Wave':[self.wave,self.wavelst],
        #          'Basis':[self.basis,self.basislst],
        #          'Solvent':[self.solvent,self.solventlst],
        #          'Properties':[self.properties,self.propertieslst]}
        try:       
            self.SetValueToComboBox() #obj,labeldic[label][0],labeldic[label][1])
            
            self.ChangeDispButtonColor()
            self.EnableChargeSpinWidgets(self.enablecharge)
            self.EnableLayerWidgets(self.enablelayer)
            self.EnableBasisWidgets(self.enablebasis)
            
            if self.gmsuser.coordinternal: self.gmsuser.SetCoordFromFU()
            self.ChangeCoordButtonColor()
            
            for item,status in self.widgetstatusdic.iteritems(): 
                items=item.split(':') # 'combo:item' or 'button:item'
                if items[0] == 'combo': obj=self.comboboxdic[items[1]]
                else: obj=self.comboboxdic[items[1]]
                if status: obj.Enable()
                else: obj.Disable()
        except: pass
        try:
            self.tcltit.SetValue(self.gmsuser.jobtitle)
            self.tcltit.SetForegroundColour('black')
            self.tcltit.Refresh()
            self.tclprp.SetValue(self.gmsuser.properties)
            self.tclprp.SetForegroundColour('black')
            self.tclprp.Refresh()
        except: pass
        self.Refresh()
    
    def SetValueToComboBox(self):
        """ Set value to ComboBox. 
        
        :param str name: item to be set value
        """
        for name,combo in self.comboboxdic.iteritems():
            #combo=self.comboboxdic[name]
            choice=self.choicedic[name]
            #try: idx=self.choicelstdic[name].index(choice)
            #except:
            if not choice in self.choicelstdic[name]:
                self.choicelstdic[name].insert(0,choice)
                self.comboboxdic[name].SetItems(self.choicelstdic[name])
            combo.SetValue(choice)
            combo.Refresh()

    def DefaultValuesFromFile(self,filename):
        """ not completed. not used"""
        if not os.path.exists(filename):
            title='GMSBeginner_Frm:ReadDefaultValues'    
            mess='File not found. file='+filname
            lib.MessageBoxOK(mess,title)
            return
        #
        self.ReadDefaultFile(filename)
        #
        self.basis='STO-3G'
        self.method='ABINITIO'
        self.wave='UHF'
        self.gmsuser.grimmdisp=True
        self.solvent='PCM'
        self.properties='PRINT'
        #
        self.SetWidgets()

    def ReadDefaultFile(self,filename):
        """ Read default values for GMSBeginner form file. not coded yet """
        return
    
    
        f=open(filenmae,'r')
        for s in f.readlines():
            pass
        f.close()
        
            
    def OnRunGAMESS(self,event):
        
        self.gmsuser.RunGAMESS(self)
        
               
    def OnThreadJobEnded(self,event):
        if self.gmsuser.mode == 'beginner':
            jobnam=event.jobid
            jobcmd=event.message
            killed=event.killed

            try: self.gmsuser.exeprgwin.f.close()
            except: pass
            
            self.gmsuser.ThreadJobEnded(jobnam,jobcmd,killed)
            #self.openexeprgwin=False
            #winlabel='ExePrgWin'
            #self.gmsuser.flags.Set(self.gmsuser.exewinlabel,False)
        event.Skip()
            
    def HelpDocument(self):
        helpname='gamess-user'
        self.model.helpctrl.Help(helpname)
    
    def Tutorial(self):
        helpname='gamess-user'
        self.model.helpctrl.Tutorial(helpname)
        
    def MenuItems(self):
        # Menu items
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        #submenu.Append(-1,"Open default","Open default value file")
        submenu.Append(-1,"Open input","Open GAMESS input file")
        submenu.Append(-1,"Open GMS example","Open GAMESS example input file in /tests")
        submenu.Append(-1,"Open FMO example","Open GAMESS example input file")
        #submenu.Append(-1,"Load template","Load GAMESS template input file")
        submenu.AppendSeparator()
        submenu.Append(-1,'Save input file','save GAMESS input file')
        submenu.AppendSeparator()        
        submenu.Append(-1,"Switch to expert","Switch to expert input panel")
        submenu.AppendSeparator()
        submenu.Append(-1,"Delete all in gamess/scr","Delete GAMESS $DATA")
        submenu.AppendSeparator()
        submenu.Append(-1,"Close","Close this panel")
        menubar.Append(submenu,'File')
        # View/Edit menu
        #submenu=wx.Menu()
        #submenu.Append(-1,"Input file by editor","view/edit input file by editor")
        #submenu.Append(-1,"Input file by input panel","view/edit input file by input panel")
        #submenu.AppendSeparator()
        #submenu.Append(-1,"Coordinate file by editor","view/edit input file by editor")
        #menubar.Append(submenu,'Edit')
        # Exec menu
        submenu=wx.Menu()
        submenu.Append(-1,"Open ExecBatchWin","Execute GMS batch")
        #submenu.AppendSeparator()
        #submenu.Append(-1,"Open ExecProgWin","Open ExecProg window")
        #submenu.Append(-1,"Close ExecProgWin","Close ExecProg window")
        menubar.Append(submenu,'ExecBatch')
        # Help menu
        submenu=wx.Menu()
        submenu.Append(-1,"About","Open about message")
        submenu.AppendSeparator()
        submenu.Append(-1,"Document","Open help document")
        submenu.Append(-1,"Tutorial","Open tutorial panel")
        submenu.AppendSeparator()
        ###submenu.Append(-1,"Games input document","Open GAMESS INPUT document")
        ###submenu.AppendSeparator()
        submenu.Append(-1,"Setting","Set GAMESS program path")
        menubar.Append(submenu,'Help')
        return menubar
    
    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        #
        name=self.model.setctrl.GetParam('defaultfilename')
        self.model.setctrl.SetParam('defaultfilename','')
        # 
        if item == "Close":
            self.OnClose(1)           
        elif item == "Open input":
            wildcard='input file(*.inp)|*.inp|All(*.*)|*.*'
            
            filename=lib.GetFileName(self,wildcard,"r",True,defaultname=name)
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                #self.ReadFile(filename)
                self.gmsinputfile=filename
                self.LoadGAMESSInputFile(filename)
        elif item == "Open GMS example": 
            self.gmsuser.OpenExampleFile('GMS')
        elif item == "Open FMO example": 
            self.gmsuser.OpenExampleFile('FMO')
        
        #elif item == "Open default":
        #    wildcard='default file(*.default)|*.inp|All(*.*)|*.*'
        #    filename=lib.GetFileName(self,wildcard,"r",True,"")
        #    if len(filename) > 0: 
        #        root,ext=os.path.splitext(filename)
        #        #self.ReadFile(filename)
        #        self.gmsdefaultfile=filename
        #        self.DefaultValuesFromFile(filename)
        #elif item == "Load template": self.LoadGAMESSInputFile(1)        
        elif item == "Save input file":
            #wildcard='inp(*.inp)|*.inp|All(*.*)|*.*'
            #filename=lib.GetFileName(self,wildcard,"w",True,"")
            #if len(filename) > 0: 
            self.gmsuser.SaveInput()
            #    self.MakeGMSInput(filename)
        # Edit     
        #elif item == "Input file by editor":
        #    pass

        #    self.runbt.Enable()
            
        #elif item == "Input file by input panel":
        #    print 'Edit input file by input editor'
        #    self.inputeditor=InputEditor_Frm(self,-1,[10,10],[400,300],'GAMESS Input Editor')

        #elif item == "Coordinate file by editor":
        #    print 'Edit coordinate file by editor'
        
        elif item == "Switch to expert":
            if self.inputer: self.inputer.OnClose(1)
            self.gmsuser.CloseBeginnerWin()
            self.gmsuser.mode=1
            winpos=self.GetPosition()
            for name in self.gmsuser.allinputnames: self.gmsuser.AddInputNameAndVars(name,[])
            inputnamelst=self.gmsuser.allinputnames
            self.gmsuser.OpenExpertWin(self.mdlwin,inputnamelst,winpos=winpos)
            
        elif item == "Close":
            self.OnClose(0)
        # ExecBatch
        elif item == "Open ExecBatchWin":
            self.gmsuser.OpenExecBatchWin()
        
        elif item == "Open ExecProgWin":
            self.gmsuser.OpenExePrgWin(self)
        
        elif item == "Close ExecProgWin":
            try: self.gmsuser.exeprgwin.OnClose(1)
            except: pass
         # Help menu items
        elif item == 'About':
            title='GAMESS Assist For Beginner in '
            lib.About(title,const.FUMODELLOGO)
        elif item == 'Document': self.HelpDocument()
        elif item == 'Tutorial': self.Tutorial()
        # Setting    
        elif item == "Setting":
            self.gmsuser.OpenSettingGAMESSPanel(self)
            
        elif item == "Games input document":
            self.gmsuser.ViewGAMESSDocument()
        
        elif item == "Delete all in gamess/scr":
            self.gmsuser.DeleteAllGAMESSScratch()


class GMSInput(object):
    def __init__(self,parent,docfile):
        """
        Set up GAMESS input data
        
        :param obj parent: parent object
        :param str docfile: GAMESS 'inputdoc.txt' file
        :Note: the 'inputdoc.txt' file is created by 'GenGMSDocText.py' 
        """
        self.parent=parent
        self.docfile=docfile
        # default colors for variables
        self.setcolor=wx.RED #wx.BLUE #wx.CYAN
        self.unsetcolor=wx.BLACK
        self.needcolor=(165, 42, 42) # brown
        self.writefilename=''
        # read GAMESSInputDoc.txt file
        self.gmsdoc=self.ReadInputDocText(self.docfile)
        # extract gmsdoc list elements
        self.grouplst=self.gmsdoc[0]
        self.grouptipsdic=self.gmsdoc[1]
        self.namelst=self.gmsdoc[2]
        self.namegroupdic=self.gmsdoc[3]
        self.nametipsdic=self.gmsdoc[4]
        self.varlstdic=self.gmsdoc[5]
        self.varvaldic=self.gmsdoc[6]
        self.varvaltipsdic=self.gmsdoc[7]
        self.valrequireddic=self.gmsdoc[8]
        self.valoptiondic=self.gmsdoc[9]
        self.needdic=self.gmsdoc[10]
        #
        """######
        print 'required',self.valrequireddic
        #self.namvarlst=[['$CONTRL','NPRINT','PUNCH','FRIEND','ISPHER','ITOL','ICUT','INTTYP','GRDTYP']]     
        # default inputnames
        self.namelst=['$CONTRL','$BASIS','$DATA','$SYSTEM']
        self.namvarlst=self.DefaultNamVars(self.namelst)
        # variables in name group which can be input from GMSExpert_Frm
        self.inpnamvardic=self.SetInputNameVars(self.namvarlst) 
        # variavles for keeping input data from GMSExpert_Frm
        # input group name list
        self.inputnamelst=self.namelst #self.DefaultInputNames()
        # variable=value type data
        self.inputvaldic=self.DefaultValues()
        # text type data
        self.textvaldic={}
        """#######
        
        self.inputfileinfo=''
        
    def SetFontColor(self,valcolor,needcolor,changedcolor):
        """ FOnt color for variables
        
        :param lst valcolor: color data [R,G,B,A] for unset variables
        :param lst needcolor: color data [R,G,B,A] for preset variables
        :param lst changedcolor: color data [R,G,B,A] for changed(input) variables 
        """
        self.setcolor=changedcolor
        self.unsetcolor=valcolor
        self.needcolor=needcolor
             
    def CheckAreAllRequireded(self):
        """ not coded yet"""
        missing=[]
        if len(missing) > 0:
            mess='There are missing data. Would you like to continue?'
            ans=lib.MessageBoxYesNo(mess,'GMSInput:MakeInputDataText')
            if not ans: return   
        return missing

    def GetGMSDoc(self):
        return self.gmsdoc
    
    def GetNamVarList(self):
        return self.namvarlst

    def GetInputNameList(self):
        return self.gmsuser.inputnamelst
    
    def SetNameVarList(self,namevarlst):
        self.namevarlst=namevarlst
    
    def DefaultNamVars(self,namelst):
        # namvarlst: [['$CONTRL','NPRINT','PUNCH',..],...]     
        namvarlst=[]
        for name in namelst:
            tmplst=[]
            tmplst.append(name)
            varlst=self.varlstdic[name]
            for var in varlst: tmplst.append(var)
            namvarlst.append(tmplst)  
        return namvarlst

    def DefaultNamVarList(self,name):
        # namvarlst: ['$CONTRL','NPRINT','PUNCH',..]   
        namvarlst=self.varlstdic[name]
        return namvarlst

    def GetDefaultVarValDic(self,name,varlst):
        """ if len(varlst)=0, use default varlst
        """
        # namvarlst: [['$CONTRL','NPRINT','PUNCH',..],...]     
        valdic={}; value=''
        if len(varlst) <= 0: varlst=self.varlstdic[name]
        for var in varlst:
            namvar=name+':'+var
            # values
            if self.varvaldic.has_key(namvar):
                val=self.varvaldic[namvar]
                vallst=self.SplitValues(val)
                value=vallst[0].strip()
                textcolor=self.unsetcolor
                if self.needdic.has_key(namvar):
                    textcolor=self.needcolor
            else: 
                value=''; textcolor=self.setcolor
            valdic[namvar]=[value,textcolor]
        return valdic
    
    def DefaultValues(self,namelst):
        defaultvaldic={}
        for name in namelst:
            if not self.varlstdic.has_key(name):
                pname=name[:-1]
                if not self.varlstdic.has_key(pname):
                    mess='Name group "'+name+'" is not defined'
                    print  mess
                    ### self.model.ConsoleMessage(mess)
                    varlst=[]                
                else: varlst=copy.deepcopy(self.varlstdic[pname])
            else: varlst=self.varlstdic[name]
            for var in varlst:
                namvar=name+':'+var
                # values
                if self.varvaldic.has_key(namvar):
                    val=self.varvaldic[namvar]
                    vallst=self.SplitValues(val)
                    value=vallst[0]
                    textcolor=self.unsetcolor
                    if self.needdic.has_key(namvar):
                        textcolor=self.needcolor
                else: 
                    value=''; textcolor=self.setcolor
                defaultvaldic[namvar]=[value,textcolor]
        
        return defaultvaldic

    def SplitValues(self,val):
        vallst=[]
        val=val.strip()
        if val == '[]': return ['']
        if val[:1] == '[': val=val[1:]
        if val[-1] == ']': val=val[:-1]
        items=val.split(',')
        for s in items: vallst.append(s.strip())
        return vallst 

    def GetInputFileInfo(self):
        return self.inputfileinfo

    def MakeInputDataText(self,inputnamelst,inputvaldic,textvaldic):
        """ Make gms input
        
        :param lst inputnamlst: input name group lsit
        :param dic inputvaldic: input variable value dictionary
        :param dic textvaldic: text type input data
        """
        #try: 
        if '$FMOXYZ' in inputnamelst:
            #idx=inputnamelst.index('$FMOXYZ')
            dolast='$FMOXYZ'
        else: dolast='$DATA'
        #except: dolast='$DATA'
        #print 'inputvaldic',self.inputvaldic
        #fmo=True
        #try: idx=inputnamelst.index('$FMO')
        #except: fmo=False
        if '$FMO' in inputnamelst: fmo=True
        else: fmo=False
        
        text=''
        # process not-TEXT data
        for name in inputnamelst:
            done=False
            if name[:1] != '$': continue
            if name == dolast: continue
            
            if fmo and name == '$BASIS': continue
            
            
            text=text+' '+name+'\n'; temp=3*' '
            nvar=0
            for namvar,datlst in inputvaldic.iteritems(): # lst:[val,color] 
                if datlst[1] == self.unsetcolor: continue
                if datlst[0] == 'TEXT': continue
                
                if datlst[0] == '': continue
                
                if namvar.split(':')[0] != name: continue
                nvar += 1
                var=namvar.split(':')[1]                
                varval=var+'='+datlst[0]
                temp=temp+varval+', \n'
                done=False
                if len(temp) < 55: temp=temp[:-1]
                else: 
                    text=text+temp; temp=3*' '
                    done=True
            temp=temp.strip()
            if not done and len(temp) > 0: text=text+3*' '+temp
            if text[-3:] == ', \n': text=text[:-3]
            if text[-1] == ',': text=text[:-1]
            text=text.rstrip()
            # process TEXT data
            for namvar,datlst in inputvaldic.iteritems():
                if datlst[1] == self.unsetcolor: continue
                if namvar.split(':')[0] != name: continue
                if datlst[0] != 'TEXT': continue
                temp=''
                if textvaldic.has_key(namvar):
                    val=textvaldic[namvar]
                    nvar += 1
                    temp=temp+'\n'+val
                text=text+temp
            text=text+'\n'+' $END\n'
            # remove empty name group
            if name != '$CONTRL' and nvar == 0:
                nc=text.rfind(name); text=text[:nc-1]
        # the last TEXT variable, '$DATA:$DATA' or '$FMOXYZ:$FMOXYZ'
        namvar=dolast+':'+dolast 
        if textvaldic.has_key(namvar):
            name=dolast
            #namvar=dolast+':'+dolast
            text=text+' '+name+'\n'
            txt=textvaldic[namvar]
            if not inputvaldic.has_key('$BASIS:GBASIS'): txt=txt+'\n'            
            if name == '$DATA': text=text+txt+'\n $END\n'
            elif name == '$FMOXYZ': 
                if txt[-1] == '\n': text=text+txt+' $END\n'
                else: text=text+txt+'\n $END\n'

        return text

    def RemoveLastNewLine(self,text):
        if text[-1] == '\n': text=text[:-1]
        return text
                
    def SaveInputFile(self,filename,text):
        ###text=self.MakeInputDataText()
        retmess=''
        if len(text) <= 0:
            retmess='No input data created.'
            #lib.MessageBoxOK(mess,'GMSInput:SaveInputFile')
            return retmess
        if len(filename) > 0:
            retmess=self.WriteInputFile(filename,text)
        return retmess

    def WriteInputFile(self,filename,text):
        mess='Failed to write file. file='+filename
        if len(filename) <= 0: return mess
        self.writefilename=filename    
        #
        f=open(filename,'w')
        f.write("! Created by FU-GMSUser at "+lib.DateTimeText()+"\n")
        f.write(text)
        f.close()
        #
        mess='GMSUser: Created input file= '+filename+'\n'      
        return mess
 
    def ReadInputDocText(self,docfile):
        """ The data managed in this calss are,
            (xxxlst keeps the item order and xxxdic the body of data)
            
            grouplst:     [group,...]
            grouptipsdic: {group:tips,...}
            
            namelst:      [name,...] for all name groups
            nametipsdic:  {name:tips,...]
            namegroupdic: {name:group,...}
        
            varlstdic:    {'name:varlst,...}, e.g. '$FRGRPL': ['NAME1', 'NAME2',        varvaltipsdic={} # {'name:var:val':tips,...],'$GEN:PURES:flag': '[flag to say that IROOT and...'],...}
                    varlst: [var,...] # for each name
            vartipsdic:   included in varvaltipsdic whose dic key is 'name:var' (missingg :val)   
            
            varvaldic:    {'name:var':val,..} {'$CONTRL:NPRINT': '[-7, -6,.. ]',..}
            varvaltipsdic:{'name:var:val':tips,...],'$GEN:PURES:flag': '[flag to say that IROOT and...'],...}
            
            valreqireddic:   {'name:var:val:[need name,...],...}
            valconflictdic:   {'symbol:[namvarval,...],...}
            
            needdic:    {'name:var:True(False),...}
        """   
        # check does docfile exist
        if not os.path.exists(docfile):
            mess='GAMESS doc file is not found. file='+docfile
            mess=mess+'\nUnabel to continue.'              
            lib.MessageBoxOK(mess,'GMSUser:ReadInputDocText')
            return []

        grouplst=[]; grouptipsdic={}
        namelst=[]; nametipsdic={}; namegroupdic={}
        varvaldic={}; varvaltipsdic={}; varlstdic={}; varlst=[]
        valrequireddic={}; valconflictdic={}; needdic={}
        # symbol in the first column should be '*'(required) or '+'(options)
        grphead='group ';  grptipshead='grouptip '
        namhead='name '; namtipshead='nametip '
        varhead='varval '; vartipshead='vartip '
        valrequiredhead='required '; valconflicthead='conflict '
        ngrphead=len(grphead); ngrptipshead=len(grptipshead)
        nnamhead=len(namhead); nnamtipshead=len(namtipshead)
        nvarhead=len(varhead); nvartipshead=len(vartipshead)
        nvalrequiredhead=len(valrequiredhead); nvalconflicthead=len(valconflicthead)
        #
        line=0; prvname=''; prvgroup=''
        f=open(docfile,'r')
        #
        for s in f.readlines():
            line += 1
            if s[:1] == '#': continue
            s=self.CutComment(s)
            s0=s[0]; ss=s[1:]
            #s=s.strip(); ss=s[1:]
            if len(s) <= 0: continue
            # @group
            if ss.startswith(grphead,0,ngrphead):
                s=self.CutComment(s)
                group,dat=self.GetHeaderDataInLine(grphead,s)
                if group == '': 
                    print 'Missing group name at line:'+str(line)+' - '+s
                    continue
                #if prvgroup != '':
                grouplst.append(group)
                if prvname != '': varlstdic[prvname]=varlst
                prvname=''; varlst=[]
            # group tips
            elif ss.startswith(grptipshead,0,ngrptipshead):                
                grouptips=''
                items=s.split(' ',1)
                if len(items) >= 2: grouptips=items[1]
                grouptipsdic[group]=grouptips
            # @name
            elif ss.startswith(namhead,0,nnamhead): 
                s=self.CutComment(s)
                name,dat=self.GetHeaderDataInLine(namhead,s)
                if name == '': 
                    print 'Missing name name at line:'+str(line)+' - '+s
                    continue
                namelst.append(name)
                namegroupdic[name]=group
                if s0 == '*': needdic[name]=True
                if prvname != '': varlstdic[prvname]=varlst
                varlst=[]; prvname=name
            # @name tips
            elif ss.startswith(namtipshead,0,nnamtipshead): 
                nametips=''
                items=s.split(' ',1)
                if len(items) >= 2: nametips=items[1]
                #nametips=nametips.replace('///','\n\r')
                nametips=nametips.rstrip()
                if nametips[:1] == '[': nametips=nametips[1:]
                if nametips[-1] == ']': nametips=nametips[:-1]           
                nametips=nametips.replace('///','\n\r')
                nametipsdic[name]=nametips
            # @varval
            elif ss.startswith(varhead,0,nvarhead):
                s=self.CutComment(s)
                var,val=self.GetHeaderDataInLine(varhead,s)
                if var == '': 
                    print 'Missing var name at line:'+str(line)+' - '+s
                    continue
                namvar=name+':'+var
                varvaldic[namvar]=val
                varlst.append(var)
                if s0 == '*': 
                    #print 'preset namvar',namvar
                    needdic[namvar]=True      
            # var tips
            elif ss.startswith(vartipshead,0,nvartipshead):
                varval,tips=self.GetHeaderDataInLine(vartipshead,s)
                tips=tips.rstrip()
                #tips=tips.replace('///','\n\r')
                if tips[:1] == '[': tips=tips[1:]
                if tips[-1] == ']': tips=tips[:-1]
                tips=tips.replace('///','\n\r')
                varvaltipsdic[name+':'+varval]=tips
            # @valneed: required names
            elif ss.startswith(valrequiredhead,0,nvalrequiredhead):    
                s=self.CutComment(s)
                nam,val=self.GetHeaderDataInLine(valrequiredhead,s)
                
                if not valrequireddic.has_key(nam): valrequireddic[nam]=[]
                items=self.GetRequiredOptionItems(val)
                for valnam in items: valrequireddic[nam].append(valnam)
            # @valoptn: option names
            elif ss.startswith(valconflicthead,0,nvalconflicthead): 
                s=self.CutComment(s)
                nam,val=self.GetHeaderDataInLine(valconflicthead,s)
                if not valconflictdic.has_key(nam): valconflictdic[nam]=[]
                items=self.GetRequiredOptionItems(val)
                for valnam in items: valconflictdic[nam].append(valnam)  
        f.close()
        # the last data
        if prvname != '': varlstdic[prvname]=varlst
        
        #print 'grouplst',grouplst
        #print 'grouptipsdic',grouptipsdic
        #print 'namelst',namelst
        #print 'nametipsdic',nametipsdic
        #print 'varlstdic',varlstdic
        #print 'varvaldic',varvaldic
        #print 'varvaltipsdic',varvaltipsdic
        return [grouplst,grouptipsdic,namelst,namegroupdic,nametipsdic
                ,varlstdic,varvaldic,varvaltipsdic,valrequireddic,valconflictdic,needdic]
    
    def CutComment(self,text):
        n=text.find('#')
        if n > 0: 
            text=text[:n].strip()
        return text
    
    def GetRequiredOptionItems(self,value):
        val=value
        
        if value[:1] == '[': val=value[1:]
        if val[-1] == ']': val=val[:-1] 
        items=val.split(',')
        for i in range(len(items)): items[i]=items[i].strip()
        
        #print 'value,items',value,items
        return items
                
    def GetHeaderDataInLine(self,keywrd,text):
        var=''; val=''
        items=text.split(' ',2)
        if len(items) < 2: return var,val
        if items[0][1:]+' ' != keywrd: return var,val
        else: var=items[1].strip()
        if len(items) < 3: return var,val
        else: val=items[2].strip()
        if len(items) >= 4: val=items[2].strip()+' '+items[3].strip()
        return var,val

    def PrtPCMNamGrp(self,fil):
        solv=self.cmbslv.GetValue()
        eol='\n'
        data=['$pcm      ','$pcmcav   ','$tescav   ','$pcmitr    ']
        if solv == "PCM":
            if self.run == 'gradient' or self.run == 'optimize':
                """
                mess='Sorry, PCM gradient input is not supported. '
                mess=mess+'Please post edit the generated input file.'
                lib.MessageBoxOK(mess,"")
                return
                """
                dat1=' $pcm solvnt=Water ief=-10 icomp=0 icav=1 idisp=1 ifmo=-1 $end'
                dat2=' $pcmcav radii=suahf $end'
                dat3=' $tescav ntsall=240 method=4 $end'
                #dat4=' $pcmgrd ipcder=3 '
                #dat5=' $disrep iclav=1 $end'
                fil.write(dat1+eol)
                fil.write(dat2+eol)
                fil.write(dat3+eol)
                #fil.write(dat4+eol)
                #fil.write(dat5+eol)
            else: # single point energy
                dat1=' $pcm solvnt=Water ief=-10 icomp=2 icav=1 idisp=1 ifmo=-1 $end'
                dat2=' $pcmcav radii=suahf $end'
                dat3=' $tescav ntsall=60 $end'
                fil.write(dat1+eol)
                fil.write(dat2+eol)
                fil.write(dat3+eol)
        
class SetPathAndCmdForGAMESS_Frm(wx.MiniFrame):
    def __init__(self,parent,id,winpos,prgfile,program,item,remark):
        self.title='Set '+program+' path,commad and argument'
        winsize=lib.MiniWinSize([400,190])  #; winpos=(-1,-1)
        wx.MiniFrame.__init__(self, parent, id, self.title,size=winsize,pos=winpos,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT)
        self.parent=parent # begginerwin or expertwin
        self.gmsuser=self.parent.gmsuser
        self.model=parent.model #self.parent.model

        self.remark=remark
        #self.MakeModal(True)
        self.prgfile=prgfile
        #print 'self.prgfile',self.prgfile
        
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        
        self.size=self.GetSize()
        #self.gmspath="c:\\gamess.64\\rungms.bat"
        #self.gmsarg="13-64.intel.linux.mkl 1 0"   
        self.gmspath=self.gmsuser.gmspath
        self.gmscmd=self.gmsuser.gmscmd
        self.gmsarg=self.gmsuser.gmsarg
        self.gmsscr=self.gmsuser.gmsscrdir  
        self.gmstests=self.gmsuser.gmsexamdir
        """
        if not os.path.isdir(self.gmspath): self.gmspath=self.GetDefaultGMS('gmspath')
        if not os.path.exists(self.gmscmd): 
            self.gmscmd=self.GetDefaultGMS('gmscmd')
            self.gmsarg=self.GetDefaultGMS('gmsarg')
        if not os.path.isdir(self.gmsscr): self.gmsscr=self.GetDefaultGMS('gmsscr')
        if not os.path.isdir(self.gmstests): self.gmsscr=self.GetDefaultGMS('gmstests')
        """
        #
        self.setpath=False
        self.quit=False
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        self.Show()
    
    def GetDefaultGMS(self,item):
        print 'default item is called',item
        platform=lib.GetPlatform()
        if platform =='WINDOWS':
            ext='.win'
            gmspath="c://gamess.64"
            gmscmd="rungms.bat"
            gmsarg='$inputfile 13-64.intel.linux.mkl $ncores 0'
            gmsscr="c://gamess.64/scr"   
            gmstests="c://gamess.64/tests"       
        elif platform =='MACOSX':
            ext='.mac'
            gmspath="~/gamess.64"
            gmscmd="rungms"
            gmsarg='$inputfile May12013R1 $ncores 0'
            gmsscr="~/gamess.64"
            gmstests="~/gamess.64/tests/standard"
        elif platform == 'LINUX': 
            ext='.lnx'
            gmspath="~/gamess.64"
            gmscmd="rungms.sh"
            gmsarg='$inputfile May12013R1 $ncores 0'
            gmsscr="~/gamess.64/scr"
            gmstests="~/gamess.64/tests/standard"
        #
        if item == 'gmspath': return gmspath
        elif item == 'gmscmd': return gmscmd
        elif item == 'gmsarg': return gmsarg
        elif item == 'gmsscr': return gmsscr
        elif item == 'gmstests': return gmstests
        else: return ''
        
    def CreatePanel(self):
        w=self.size[0]; h=self.size[1]
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        yloc=8
        #text1=self.remark[0]
        #wx.StaticText(self.panel,-1,"     ex. path: 'c:/gamess.64/', command: 'rungms.bat'",pos=(5,yloc),size=(380,18))
        #yloc += 20
        #text2=self.remark[1]
        #wx.StaticText(self.panel,-1,"         argument: '$inpfile 13-64.intel.linux.mkl $ncores 0",pos=(5,yloc),size=(380,18))
        #yloc += 25
        wx.StaticText(self.panel,-1,"Path:",pos=(10,yloc),size=(60,18)) 
        self.tclpath=wx.TextCtrl(self.panel,-1,self.gmspath,pos=(75,yloc-2),size=(245,18))
        btnbrwp=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(330,yloc-2),size=(50,20))
        btnbrwp.Bind(wx.EVT_BUTTON,self.OnBrowsePath)
        yloc += 25
        wx.StaticText(self.panel,-1,"Command:",pos=(10,yloc),size=(60,18)) 
        self.tclcmd=wx.TextCtrl(self.panel,-1,self.gmscmd,pos=(75,yloc-2),size=(245,18))
        btnbrwc=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(330,yloc-2),size=(50,20))
        btnbrwc.Bind(wx.EVT_BUTTON,self.OnBrowseCMD)
        
        yloc += 25
        wx.StaticText(self.panel,-1,"Arguments:",pos=(10,yloc),size=(65,18)) 
        self.tclarg=wx.TextCtrl(self.panel,-1,self.gmsarg,pos=(80,yloc-2),size=(295,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"Scratch:",pos=(10,yloc),size=(60,18)) 
        self.tclscr=wx.TextCtrl(self.panel,-1,self.gmsscr,pos=(75,yloc-2),size=(245,18))
        btnscr=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(330,yloc-2),size=(50,20))
        btnscr.Bind(wx.EVT_BUTTON,self.OnBrowseScratch)
        yloc += 25
        wx.StaticText(self.panel,-1,"tests:",pos=(10,yloc),size=(60,18)) 
        self.tcltests=wx.TextCtrl(self.panel,-1,self.gmstests,pos=(75,yloc-2),size=(245,18))
        btntests=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(330,yloc-2),size=(50,20))
        btntests.Bind(wx.EVT_BUTTON,self.OnBrowseTests)
        yloc += 30
        btnapl=wx.Button(self.panel,wx.ID_ANY,"Apply",pos=(100,yloc-2),size=(50,20))
        btnapl.Bind(wx.EVT_BUTTON,self.OnApply)
        btnrmv=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(170,yloc-2),size=(45,20))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnClear)
        btncan=wx.Button(self.panel,wx.ID_ANY,"Cancel",pos=(250,yloc-2),size=(50,20))
        btncan.Bind(wx.EVT_BUTTON,self.OnCancel)

    def SetProgramPath(self):
        self.CreatePanel()
        self.Show()

    def OnBrowsePath(self,event):
        pathname=lib.GetDirectoryName(self)
        if pathname != "": 
            self.tclpath.SetValue(pathname)
            self.gmspath=pathname

    def OnBrowseScratch(self,event):
        pathname=lib.GetDirectoryName(self)
        if pathname != "": 
            self.tclscr.SetValue(pathname)
            self.gmsscr=pathname

    def OnBrowseTests(self,event):
        pathname=lib.GetDirectoryName(self)
        if pathname != "": 
            self.tcltests.SetValue(pathname)
            self.gmstests=pathname

    def OnBrowseCMD(self,event):
        wcard="All(*.*)|*.*"
        filename=lib.GetFileName(self,wcard,"r",True,"")
        if filename != "": 
            self.tclcmd.SetValue(filename)
            self.gmscmd=filename
                         
    def OnApply(self,event):
        path=self.tclpath.GetValue().strip()
        cmd=self.tclcmd.GetValue().strip()
        arg=self.tclarg.GetValue().strip()
        scr=self.tclscr.GetValue().strip()
        tests=self.tcltests.GetValue().strip()
        #print 'path,cmd,arg',path,cmd,arg
        self.quit=False
        self.WriteProgramPathFile(self.prgfile,path,cmd,arg,scr,tests)
        self.setpath=True; self.quit=False
        self.gmsuser.gmspath=path
        self.gmsuser.gmscmd=cmd
        self.gmsuser.gmsarg=arg
        self.gmsuser.gmsscdirr=scr
        self.gmsuser.gmsexamdir=tests  
        
        self.gmsuser.prgfile=self.gmsuser.GetGAMESSPrgFile()
        self.gmsuser.SetUpGAMESSFiles(self.prgfile)         
        
        self.OnClose(1)

    def GetGAMESSPathAndCMD(self):
        return self.gmspath,self.gmscmd,self.gmsarg,self.gmsscr,self.gmstests     
        
    def OnClear(self,event):
        self.gmspath=self.tclpath.SetValue("")
        self.gmscmd=self.tclcmd.SetValue("")
        self.gmsarg=self.tclarg.SetValue("")
    
    def OnCancel(self,event):
        self.parent.gmssetwin=False
        #self.MakeModal(False)
        self.Destroy()

    def WriteProgramPathFile(self,prgfile,path,cmd,arg,scr,tests):
        # write
        f=open(prgfile,"w")
        comment='# Created at '+lib.DateTimeText()+'\n'
        f.write(comment)
        comment="# '$inputfile' and $ncores will be replaced with real values in gamess-user.py\n"
        f.write(comment)
        comment="# Note: The parametrs are case sensitive\n"
        f.write(comment)
        prg="PATH "+path+"\n"
        prg=prg+'CMD '+cmd+"\n"
        prg=prg+'ARGS '+arg+"\n"
        prg=prg+'SCR '+scr+"\n"
        prg=prg+'TESTS '+tests+"\n"       
        #
        f.write(prg)
        f.close()
        
    def OnClose(self,event):
        if not self.setpath:
            mess="Do you want to keep GAMESS path and command in fumodel.set file."
            retcode=lib.MessageBoxYesNo(mess,"")
            if retcode: # == wx.YES:
                #if wx.YES:
                self.WriteGAMESSPathFile(self.prgfile,self.path,self.cmd,self.arg,self.scr,self.tests)
                self.setpath=True
            else: pass
            #dlg.Destroy()
        
        self.parent.gmssetwin=False
        
        #self.MakeModal(False)
        self.Destroy()        

class FMOInputText():
    def __init__(self,parent,fumodel):
        """
        Make FMO input text data
        
        :param obj parent: parent object. GMSUser class
        :param obj fumodel: Model class of FU
        """
        self.gmsuser=parent
        self.gmsdoc=parent.gmsdoc
        self.model=fumodel # FU Model instance
        #self.mol=self.model.mol
        # FMO name groups
        self.fmonamegrp=[]
        try: 
            idx=self.gmsuser.grouplst.index('Fragment')
            self.fmonamegrp=self.gmsuser.grouplst(idx)
        except: pass
        # read hybrid orbital file
        datdir=self.model.setctrl.GetDir('FUdata')
        self.hyborbfile=os.path.join(datdir,'hyborb.txt')
        #self.hyborbfile='c://fumodel0.2//FUdata//hyborb.txt'
        # option for FMOXYZ input text format 
        self.atomlabelwithnmb=self.gmsuser.atomlabelwithnmb


        text=self.FMOHYBTextFromFU(['cc-pVTZ','MINI'])

    def SetAtomLabelOption(self,on):
        """ Option flag for FMOXYZ atom label with sequential number
        
        :param bool on: True for set, False for unset
        """
        if on: self.atomlabelwithnmb=True
        else: self.atomlabelwithnmb=False
        
    def IsFUModelReady(self):
        if not self.model: return False
        else: return True
        
    def GetMolObjFromFU(self):
        molname=''; mol=None
        try: molname,mol=self.model.GetMol()  # Molecule instance in fumodel
        except: 
            mess='Failed to get mol object from fumodel.'
            lib.MessageBoxOK(mess,'FMOInput(GetMolObjFromFU')
        return molname,mol
        
    def IsFile(self,filename):
        if os.path.exists(filename): return True
        else:
            mess='File "'+filename+'" is not found.'
            lib.MessageBoxOK(mess,'FMOInput(IsFile)')
            return False

    def ReadHybOrb(self,basnam):
        if not os.path.exists(self.hyborbfile):
            mess='Hybrid orbital file "'+self.hyborbfile+'" not found.'
            lib.MessageBoxOK(mess,'FMOInputText:ReadHybOrb')
            return
        text=''; found=False
        f=open(self.hyborbfile,'r')
        try:
            line=0
            for s in f.readlines():
                line += 1
                if not found and s[0] == '$':
                    s=s.strip()
                    items=s.split(' ')
                    bas=items[1].strip()
                    if bas != basnam: continue
                    nbas=int(items[2].strip())
                    norb=int(items[3].strip())
                    s=s.strip()
                    text=text+2*' '+s.replace('$','')+'\n'
                    found=True; continue
                if found: 
                    s=s.strip()
                    if len(s) <= 0: break
                    if s[0] == '$': break
                    if s[:3] == '1 0' or s[:3] == '0 1': blk=5*' '
                    else: blk=8*' '
                    text=text+blk+s+'\n'
        except:
            mess='Read error at line='+str(line)+' in file "'+self.hyborbfile+'"'
            lib.MessageBoxOK(mess,'FMOInputText:ReadHybOrb')
        f.close()
        #
        return text
        
    def FMOXYZTextFromFile(self,filename):
        """ The same as SetCoordFromFile in GMSUser class """
        if not self.IsFile(filename): return
        root,ext=os.path.splitext(filename)     
        if ext == '.pdb' or ext == '.ent':
            xyzatm,pdbcon=rwfile.ReadPDBAtom(filename)
        elif ext == '.xyz':
            mess='Read file='+filename
            xyzatm,bond,resfrg=rwfile.ReadXYZAtom(filename)
        if len(xyzatm) <= 0:
            mess='Falied to get coordinate data from file. file='+filename
            lib.MessageBoxOK(mess,'GMSUser:SetCoordFromFile')
            return ''
        #
        text=''
        ff12='%12.6f'; fi4='%4d'; natm=len(xyzatm); form='%0'+str(len(str(natm)))+'d'
        text=text+filename[:70]+'\n'
        text=text+'C1\n'
        i=0
        for atmdat in xyzatm:
            elm=atmdat[10]; an=const.ElmNmb[elm]; san=fi4 % an
            x=ff12 % atmdat[7][0]; y=ff12 % atmdat[7][1]; z=ff12 % atmdat[7][2]
            i += 1
            if self.atomlabelwithnmb: elm=elm+(form % i)
            text=text+4*' '+elm+' '+san+' '+x+' '+y+' '+z+'\n'

        return filename,text

    def FMOXYZTextFromFU(self):
        molname,mol=self.GetMolObjFromFU()
        ff12='%12.6f'; fi4='%4d'; natm=len(mol.atm); form='%0'+str(len(str(natm)))+'d'
        #text=text+molname+'\n'
        #text=text+'C1\n'
        coordlst=[]
        i=0
        for atom in mol.atm:
            coordlst.append([atom.elm,atom.cc[0],atom.cc[1],atom.cc[2]])
            """
            elm=atom.elm; an=const.ElmNmb[elm]; san=fi4 % an
            x=ff12 % atom.cc[0]; y=ff12 % atom.cc[1]; z=ff12 % atom.cc[2]
            i += 1
            if self.atomlabelwithnmb: elm=elm+(form % i)
            text=text+4*' '+elm+' '+san+' '+x+' '+y+' '+z+'\n'
            """
        text=FMOInputText.MakeFMOXYZText(coordlst,self.atomlabelwithnmb)
        #text=text.rstrip()
        
        return molname,text
    @staticmethod
    def MakeFMOXYZText(coordlst,atomlabelwithnmb):
        text=''
        #
        natm=len(coordlst)
        ff12='%12.6f'; fi4='%4d'; form='%0'+str(len(str(natm)))+'d'
        #text=text+molname+'\n'
        #text=text+'C1\n'
        i=0
        for elm,x,y,z in coordlst:
            an=const.ElmNmb[elm]; san=fi4 % an
            x=ff12 % x; y=ff12 % y; z=ff12 % z
            i += 1
            if atomlabelwithnmb: elm=elm+(form % i)
            text=text+4*' '+elm+' '+san+' '+x+' '+y+' '+z+'\n'
        text=text[:-1]
        text=text.rstrip()
        #
        return text

    def FMOHYBTextFromFU(self,basnamlst):
        basnamlst=basnamlst+['MINI']
        text=''; temp=''
        for basnam in basnamlst:
            if basnam == '': continue
            temp=self.ReadHybOrb(basnam)
            if len(temp) <= 0:
                text=text+'Warnning: Hybrid orbitals for "'+basnam
                text=text+'" is not found.\nPlease create yourself.'
            else: text=text+temp
        text=text.rstrip()
        #text=text+'\n'
        return text    
    
    def FMOResidueTextFromFU(self):
        """ This is not input data but commens
        
        """
        eol='\n'
        name='!$RESIDUE\n'; end='!$END\n'
        resnamlst,resatmlst=self.model.ListResidueAtoms()
        header='  resnam(1)='; sep=','; width=-1; colu=5; nw=5
        text1=lib.StringListToText(resnamlst,header,sep,width,colu,nw) 
        sep=','; width=7; colu=5; nw=7
        header='  resatm(1)='
        temp=[]
        for i in range(len(resatmlst)): temp.append(resatmlst[i][-1]+1)
        text2=lib.NumericListToText(temp,header,sep,width,colu,nw) 
        
        atmnamlst=self.model.ListAtmNam()
        header='  atmnam(1)='; sep=','; width=-1; colu=5; nw=8
        text3=lib.StringListToText(atmnamlst,header,sep,width,colu,nw) 
        
        text=name+text1+text2+text3+end   
        
        text=text.replace('\n ','\n!')
        
        return text
            
    def FMOBNDTextFromFU(self,basnamlst):
        basnamlst=basnamlst+['MINI']
        frgbdalst=self.model.frag.ListBDA() #BAA()
        eol='\n'; blk=' '
        text=''
        if len(frgbdalst) <= 0: return text
        
        for i in range(len(frgbdalst)):
            ia=frgbdalst[i][0]+1; ib=frgbdalst[i][1]+1
            sa='%6d' % (-ia); sb='%6d' % ib
            line=2*blk+sa+2*blk+sb
            for j in range(len(basnamlst)):
                if basnamlst[j] == '': continue
                line=line+2*blk+''+basnamlst[j]
            #line=line+2*blk+'MINI'#line=line+2*blk+' CMINI'
            text=text+line+eol
        text=text.rstrip()
        test=text+'\n'
        return text

    def FMODATATextFromFU(self,jobtitle,basdatlst):
        """
        
        :param str jobtitle: job title
        :params lst basdat: [[basnam(str),ngauss(str),ndfunc(str)],...]
        :note: output text will be,
              C.1-1     6           (Element.layer-label, atomic number)
                 N311      6        (GBASIS,NGAUSS)
                   d 1 ; 1 0.650 1.0  (func, NDFUNC ; #, exponent, scale)
        """
        blk=' '; eol='\n'
        elmlst=self.model.ListElement()
        elmexp=self.gmsuser.beginner.GetBasisNDFUNCExponent('N31',' C')
        if len(jobtitle) <= 0: jobtitle='Job title'
        nlayer=self.gmsuser.nlayer
        text=3*' '+jobtitle+'\n'
        text=text+blk+'C1\n'
        for i in range(nlayer):
            for j in range(len(elmlst)):
                elm=elmlst[j]; ian=const.ElmNmb[elm]
                line=' '+elm
                line=line+'-'+str(i+1)+5*blk+str(ian)+eol
                basnam=basdatlst[i][0]
                ngauss=basdatlst[i][1]             
                line=line+6*blk+basnam+6*blk+ngauss+eol
                if basdatlst[i][2] != '':
                    elmexp=self.gmsuser.beginner.GetBasisNDFUNCExponent(basnam,elm)
                    if len(elmexp) > 0:
                        txt='d 1 ; 1 '+elmexp+' 1.0'
                        line=line+8*blk+txt+eol
                    else:
                        if elm != ' H': 
                            line=line+8*blk+'supply pol function data.'+eol
                text=text+line+eol
        text=text.rstrip()
        text=text+'\n'
        return text    
        
    def FMOAttribTextFromFU(self,attrib):
        ndat=0; text=''
        attriblst=['charge','layer','active','spin']
        
        if not attrib in attriblst:
            return 0,''
                
        attriblst=self.model.frag.GetFragmentAttribute(attrib)
        
        if len(attriblst) > 0:
            ndat=len(attriblst)
            if attrib == 'layer':
                for lay in attriblst: text=text+str(lay)+','
                text=text[:-1]
            if attrib == 'active':
                for lay in attriblst: text=text+str(lay)+','
                text=text[:-1]

        return ndat,text
        
    @staticmethod    
    def MakeAttribText(attlib):
        ndat=0; text=''
        attriblst=self.model.GetFragmentAttribute(attrib)
        if attrib in attliblst:
            ndat=len(attriblst)
            if len(attriblst) > 0:
                pass
        """ 
            if 'IFREEZ' in attriblst:
                ndat,text=self.gmsuser.MakeIFREEZText(attriblst)

        else:
            for val in attriblst: text=text+val
        if len(text) > 0:
            #
            header='  '+attrib+'(1)='; sep=','; width=-1; colu=5; nw=10
            #text=lib.NumericListToText(frglayerlst,header,sep,width,colu,nw) 
            text=lib.StringListToText(attriblst,header,sep,width,colu,nw) 
        """
        return ndat,text
    
    def FMOIndatTextFromFU(self):
        # frgatmlst:[[0,1,2,...].[8,9..],...] 
        frgatmlst=self.model.frag.ListFragmentAtoms()
        #print 'frgatmlst',frgatmlst
        text=FMOInputText.MakeIndatText(frgatmlst)
    
        return text
    @staticmethod
    def MakeIndatText(frgatmlst):
        eol='\n'
        text='       indat(1)= 0'+eol
        #self.frgatmlst,self.frgatmchg=self.model.ListFragmentAtom()
        # compress integer data and add '0' at the end of each fragment
        header=''; sep=''; width=8; colu=10; nw=7 #nw=8
        for i in range(len(frgatmlst)):
            lst=frgatmlst[i]
            lst=numpy.array(lst)+1
            cmpint=lib.CompressIntData(lst)
            cmpint.append(0)
            text=text+lib.NumericListToText(cmpint,header,sep,width,colu,nw) 
        return text

    def FMOFrgchgTextFromFU(self):
        #frgchglst=self.model.ListFragmentCharge()
        text=''
        ###frgchglst=self.model.mol.GetFragmentAttributeList('ICHARG')
        frgchglst=self.model.frag.ListFragmentCharge(aareschg=False)
        if len(frgchglst) <= 0:
            mess='Fragment charges are not defined. Set them by "FMO"-"Fragment attribute" menu.'
            lib.MessageBoxOK(mess,'FMOinputText(FMOFrgchgTextFromFU)')
            return        
        text=FMOInputText.MakeFrgchgText(frgchglst)
        return text
    @staticmethod
    def MakeFrgchgText(frgchglst):
        #print 'frgchglst',frgchglst
        header='  icharg(1)='; sep=','; width=-1; colu=5; nw=10
        #text=lib.NumericListToText(frgchglst,header,sep,width,colu,nw)
        text=lib.NumericListToText(frgchglst,header,sep,width,colu,nw) 

        return text
    
    def FMOFrgmultTextFromFU(self):
        """ not coded yet"""
        return ''
        frgmultlst=[]
        #print 'frgmultlst',frgmultlst
        header='  mult(1)='; sep=','; width=-1; colu=5; nw=10
        text=lib.StringListToText(fil,imul,header,sep,width,colu,nw) 
        return text
    
    def FMOFrgnamTextFromFU(self):   
        frgnamlst=self.model.frag.ListFragmentName()
        
        nfrg,text=FMOInputText.MakeFrgnamText(frgnamlst)
        
        return nfrg,text
    
        #frgnamlst=self.model.mol.GetFragmentAttributeList('FRGNAM')
    @staticmethod
    def MakeFrgnamText(frgnamlst):
        # frgnam should be 6-characters in GAMESS
        namlst=[]
        for frgnam in frgnamlst:
            if len(frgnam) > 6: namlst.append(frgnam[-6:])
            else: namlst.append(frgnam)
        # make text data
        header='  frgnam(1)='; sep=','; width=-1; colu=5; nw=5
        text=lib.StringListToText(namlst,header,sep,width,colu,nw) 
        nfrg=len(namlst)
        return nfrg,text
           
    def FMOBasisDataFromFU(self):
        print 'GetFMOBasisFromFU. $FMOBND,$FMOHYB and $DATA'
    
    def SetFMOPCMData(self):
        print 'SetFMOPCMData'


# main program              
parent=fum.mdlwin

mode='beginner'
gmsuser=GMSUser(fum,mode=mode)

              
