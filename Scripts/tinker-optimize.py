#!/bin/sh
# -*- coding: utf-8 -*- 
#-----------
#script: tinker-optimize.py
# ----------
# function: execute tinker optimize program
# usage: This script is executed in PyCrust shell.
#        >>> fum.fum.ExecuteAddOnScript('tinker-optimize.py',False)
# ----------
# change history
# modified for fu ver.0.2.0,18May2015
# the first version for fu ver.0.0.0, 23Del2015
# -----------

import os
import sys
import wx
import shutil 

import molec
#import model
import const
import lib
import subwin
import rwfile

import functools
import threading
import subprocess
import datetime
import time
import glob

def GetTinkerProgram(prgdir,prgnam):
    # TINKER Version 6.0 Executables for 64-bit Windows
    tinkerprogramdic={"alchemy":prgdir+"/alchemy.exe",
                    "analyze":prgdir+"/analyze.exe",
                    "anneal":prgdir+"/anneal.exe",
                    "archive":prgdir+"/archive.exe",
                    "correlate":prgdir+"/correlate.exe",
                    "crystal":prgdir+"/crystal.exe",
                    "diffuse":prgdir+"/diffuse.exe",
                    "distgeom":prgdir+"/distgeom.exe",
                    "document":prgdir+"/document.exe",
                    "dynamic":prgdir+"/dynamic.exe",
                    "gda":prgdir+"/\gda.exe",
                    "intedit":prgdir+"/intedit.exe",
                    "intxyz":prgdir+"/intxyz.exe",
                    "minimize":prgdir+"/minimize.exe",
                    "minirot":prgdir+"/minirot.exe",
                    "minrigid":prgdir+"/minrigid.exe",
                    "monte":prgdir+"/monte.exe",
                    "newton":prgdir+"/newton.exe",
                    "newtrot":prgdir+"/newtrot.exe",
                    "nucleic":prgdir+"/nucleic.exe",
                    "optimize":prgdir+"/optimize.exe",
                    "optirot":prgdir+"/optirot.exe",
                    "optrigid":prgdir+"/optrigid.exe",
                    "path":prgdir+"/path.exe",
                    "pdbxyz":prgdir+"/pdbxyz.exe",
                    "polarize":prgdir+"/polarize.exe",
                    "poledit":prgdir+"/poledit.exe",
                    "potential":prgdir+"/potential.exe",
                    "prmedit":prgdir+"/prmedit.exe",
                    "protein":prgdir+"/protein.exe",
                    "pss":prgdir+"/pss.exe",
                    "pssrigid":prgdir+"/pssrigid.exe",
                    "pssrot":prgdir+"/pssrot.exe",
                    "radial":prgdir+"/radial.exe",
                    "saddle":prgdir+"/saddle.exe",
                    "scan":prgdir+"/scan.exe",
                    "sniffer":prgdir+"/sniffer.exe",
                    "spacefill":prgdir+"/spacefill.exe",
                    "spectrum":prgdir+"/spectrum.exe",
                    "superpose":prgdir+"/superpose.exe",
                    "sybylxyz":prgdir+"/sybylxyz.exe",
                    "testgrad":prgdir+"/testgrad.exe",
                    "testhess":prgdir+"/testhess.exe",
                    "testpair":prgdir+"/testpair.exe",
                    "testrot":prgdir+"/testrot.exe",
                    "timer":prgdir+"/timer.exe",
                    "timerot":prgdir+"/timerot.exe",
                    "torsfit":prgdir+"/torsfit.exe",
                    "valence":prgdir+"/valence.exe",
                    "vibbig":prgdir+"/vibbig.exe",
                    "vibrate":prgdir+"/vibrate.exe",
                    "vibrot":prgdir+"/vibrot.exe",
                    "xtalfit":prgdir+"/xtalfit.exe",
                    "xtalmin":prgdir+"/xtalmin.exe",
                    "xyzedit":prgdir+"/xyzedit.exe",
                    "xyzint":prgdir+"/xyzint.exe",
                    "xyzpdb":prgdir+"/xyzpdb.exe",
                    "xyzsybyl":prgdir+"/xyzsybyl.exe" }

    return tinkerprogramdic[prgnam]

def GetFFNamesAndFiles(prmdir):
    # TINKER Version 6.0 Executables for 64-bit Windows
    ffnamelst=['TINY','AMBER94','AMBER96','AMBER98','AMBER99','AMBER99SB'] #,
               #'CHARMM19',
               #'CHARMM22','CHARMM22CMAP',
               #'DANG','HOCH','MM2','MM3','MM3PRO',
               #'OPLSAA',
               #'OPLSAAL',
               #'OPLSUA',
               #'SMOOTHAA',
               #'SMOOTHUA',
               #'WATER']
    fffiledic={'TINY':prmdir+"/tiny.prm",
               'AMBER94':prmdir+"/amber94.prm",
               'AMBER96':prmdir+"/amber96.prm",
               'AMBER98':prmdir+"/amber98.prm",
               'AMBER99':prmdir+"/amber99.prm",
               'AMBER99SB':prmdir+"/amber99sb.prm",
               #'CHARMM19':prmdir+"/charmm19.prm",
               #'CHARMM22':prmdir+"/charmm22.prm",
               #'CHARMM22CMAP':prmdir+"/charmm22cmap.prm",
               #'DANG':prmdir+"/dang.prm",
               #'HOCH':prmdir+"/hoch.prm",
               #'MM2':prmdir+"/mm2.prm",
               #'MM3':prmdir+"/mm3.prm",
               #'MM3PRO':prmdir+"/mm2.prm",
               #'OPLSAA':prmdir+"/oplsaa.prm",
               #'OPLSAAL':prmdir+"/oplsaal.prm",
               #'OPLSUA':prmdir+"/oplsua.prm",
               #'SMOOTHAA':prmdir+"/smoothaa.prm",
               #'SMOOTHUA':prmdir+"/smoothua.prm",
               #'WATER':prmdir+"/water.prm"
                }
    
    return ffnamelst,fffiledic

def GetFFDefaultFuncForm(ffname):
    #AMBER-FF94, FF-96, FF98, FF99, FF99SB
    amberdic={"vdwtype":"LENNARD-JONES",
              "radiusrule":"ARITHMETIC",
              "radiustype":"R-MIN",
              "radiussize":"RADIUS",
              "epsilonrule":"GEOMETRIC",
              "vdw-14-scale":"2.0",
              "chg-14-scale":"1.2",
              "electric":"332.0522173",
              "dielectric":"1.0"
                  }
    # CHARMM19, CHARMM22, HCARMM22CMAP
    charmmdic={
               "vdwtype":"LENNARD-JONES",
               "radiusrule":"ARITHMETIC",
               "radiustype":"R-MIN",
               "radiussize":"RADIUS",
               "epsilonrule":"GEOMETRIC",
               "vdw-14-scale":"1.0",
               "chg-14-scale":"1.0",
               "electric":"332.0716",
               "dielectric":"1.0"
               }
    #  OPLS-AA
    oplsaadic={
                "vdwindex":"TYPE",
                "vdwtype":"LENNARD-JONES",
                "radiusrule":"GEOMETRIC",
                "radiustype":"SIGMA",
                "radiussize":"DIAMETER",
                "epsilonrule":"GEOMETRIC",
                "torsionunit":"0.5",
                "imptorunit":"0.5",
                "vdw-14-scale":"2.0",
                "chg-14-scale":"2.0",
                "electric":"332.06",
                "dielectric":"1.0"
                }
    # OPLS-AA/L
    oplsaaldic={
                "vdwtype":"LENNARD-JONES",
                "radiusrule":"GEOMETRIC",
                "radiustype":"SIGMA",
                "radiussize":"DIAMETER",
                "epsilonrule":"GEOMETRIC",
                "torsionunit":"0.5",
                "imptorunit":"0.5",
                "vdw-14-scale":"2.0",
                "chg-14-scale":"2.0",
                "dielectric":"1.0"    
                }
    # OPLS-UA
    oplsuadic={
                "vdwtype":"LENNARD-JONES",
                "radiusrule":"GEOMETRIC",
                "radiustype":"SIGMA",
                "radiussize":"DIAMETER",
                "epsilonrule":"GEOMETRIC",
                "vdw-14-scale":"8.0",
                "chg-14-scale":"2.0",
                "electric":"332.06",
                "dielectric":"1.0"
               }
    # TINY
    tinydic={
               "vdwtype":"LENNARD-JONES",
               "radiusrule":"GEOMETRIC",
               "radiustype":"SIGMA",
               "radiussize":"RADIUS",
               "epsilonrule":"GEOMETRIC"
               }
    #MM2-1991
    mm2dic={
                "bondunit":"71.94",
                "bond-cubic":"-2.0",
                "bond-quartic":"1.25", #         !! TINKER
                "angleunit":"0.02191418",
                "angle-sextic":"0.00000007",
                "strbndunit":"2.51118",
                "opbendtype":"ALLINGER",
                "opbendunit":"0.02191418",
                "opbend-sextic":"0.00000007",
                "torsionunit":"0.5",
                "vdwtype":"BUCKINGHAM",
                "radiusrule":"ARITHMETIC",
                "radiustype":"R-MIN",
                "radiussize":"RADIUS",
                "epsilonrule":"GEOMETRIC",
                "a-expterm":"290000.0",
                "b-expterm":"12.5",
                "c-expterm":"2.25",
                "vdw-14-scale":"1.0",
                "chg-14-scale":"1.0",
                "electric":"332.0538",
                "dielectric":"1.5"
                }
    # MM3-2000
    mm3dic={
                "bondunit":"71.94",
                "bond-cubic":"-2.55",
                "bond-quartic":"3.793125", #     !! (7/12)*bond-cubic^2
                "angleunit":"0.02191418",
                "angle-cubic":"-0.014",
                "angle-quartic":"0.000056",
                "angle-pentic":"-0.0000007",
                "angle-sextic":"0.000000022",
                "strbndunit":"2.51118",
                "angangunit":"-0.02191418",
                "opbendtype":"ALLINGER",
                "opbendunit":"0.02191418",
                "opbend-cubic":"-0.014",
                "opbend-quartic":"0.000056",
                "opbend-pentic":"-0.0000007",
                "opbend-sextic":"0.000000022",
                "torsionunit":"0.5",
                "strtorunit":"-5.9975",
                "vdwtype":"MM3-HBOND",
                "radiusrule":"ARITHMETIC",
                "radiustype":"R-MIN",
                "radiussize":"RADIUS",
                "epsilonrule":"GEOMETRIC",
                "a-expterm":"184000.0",
                "b-expterm":"12.0",
                "c-expterm":"2.25",
                "vdw-14-scale":"1.0",
                "chg-14-scale":"1.0",
                "electric":"332.0538",
                "dielectric":"1.5"
                }
    # MM3-PROTEIN
    mm3prodic={
                "bondunit":"71.94",
                "bond-cubic":"-2.55",
                "bond-quartic":"3.793125", #        !! (7/12) * bond-cubic^2
                "angleunit":"0.02191418",
                "angle-cubic":"-0.014",
                "angle-quartic":"0.000056",
                "angle-pentic":"-0.0000007",
                "angle-sextic":"0.000000022",
                "strbndunit":"2.51118",
                "angangunit":"-0.02191418",
                "opbendtype":"ALLINGER",
                "opbendunit":"0.02191418",
                "opbend-cubic":"-0.014",
                "opbend-quartic":"0.000056",
                "opbend-pentic":"-0.0000007",
                "opbend-sextic":"0.000000022",
                "torsionunit":"0.5",
                "strtorunit":"-5.9975",
                "vdwtype":"MM3-HBOND",
                "radiusrule":"ARITHMETIC",
                "radiustype":"R-MIN",
                "radiussize":"RADIUS",
                "epsilonrule":"GEOMETRIC",
                "a-expterm":"184000.0",
                "b-expterm":"12.0",
                "c-expterm":"2.25",
                "vdw-14-scale":"1.0",
                "chg-14-scale":"1.0",
                "electric":"332.0538",
                "dielectric":"4.0",
                }
    ffnamedic={'TINY':'TINY','AMBER94':'AMBER','AMBER96':'AMBER',
               'AMBER98':'AMBER','AMBER99':'AMBER','AMBER99SB':'AMBER',
               'CHARMM19':'CHARMM','CHARMM22':'CHARMM','CHARMM22CMAP':'CHARMM',
               'MM2':'MM2','MM3':'MM3','MM3PRO':'MM3PRO',
               'OPLSAA':'OPLSAA','OPLSAAL':'OPLSAAL','OPLSUA':'OPLSUA',
               #'DANG':'DANG','HOCH':'HOCH',
               #'SMOOTHAA':'SMOOTH','SMOOTHUA':'SMOOTH','WATER':'WATER'
               }        
    if ffnamedic.has_key(ffname): name=ffnamedic[ffname]
    else:
        lib.MessageBoxOK("Not found. ffname="+ffname,"")
        return {}
    if name== 'AMBER': return amberdic
    if name == 'CHARMM': return charmmdic
    if name == 'TINY': return tinydic
    if name == 'MM2': return mm2dic
    if name == 'MM3': return mm3dic
    if name == 'MM3PRO': return mm3prodic
    if name == 'OPLSAA': return oplsaadic
    if name == "OPLSAAL": return oplsaaldic
    if name == 'OPLSUA': return oplsuadic 
    """
    self.atom=[]
    self.vdw=[]
    self.vdw14=[] # charmm22, charm22cmap
    self.vdwpr=[] # mm2, mm3
    self.bond=[]
    self.bond3=[] # mm2, mm3
    self.bond4=[] # mm2, mm3
    self.bond5=[] # mm3
    self.angle=[]
    self.angle3=[] # mm2,mm3
    self.angle4=[] # mm2,mm3
    self.angle5=[] # mm3
    self.angang=[] # mm3
    self.torsion=[]
    self.torsion4=[] # mm2,mm3
    self.torsion5=[] # mm3
    self.imptors=[] # amber
    self.improper=[] # charmm
    self.ureybrad=[] # charmm22cmap, opls-ua
    self.tortors=[] # charmm22cmap
    self.hbond=[] # mm3pro, mm3
    self.strbnd=[] # mm3pro, mm2, mm3:q
    self.opbend=[] # mm3pro, mm2, mm3
    self.strtors=[] # mm3pro, mm3
    self.dipole=[] # mm3pro, mm2, mm3
    self.dipole4=[] # mm3
    self.dipole5=[] # mm3
    self.piatom=[] # mm2, mm3
    self.pibond=[] # mm2, mm3
    self.pibond4=[] # mm3
    self.pibond5=[] # mm3
    self.electneg=[] # mm3
    self.charge=[]
    self.biotyp=[]
    """
class SetPathForTinker_Frm(wx.Dialog):
    def __init__(self,parent,id,setfile):
        self.title='Set TINKER program and parameter path'
        winsize=lib.WinSize((350,160)); winpos=(-1,-1)
        wx.Dialog.__init__(self, parent, id, self.title,size=winsize,pos=winpos) #,
        #       style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.FRAME_FLOAT_ON_PARENT)

        self.parent=parent
        self.model=parent.model
        #
        ext='.mac'
        self.text1="ex. program  '~/tinker-6.2.06/bin-mac64'"
        self.text2="ex. parameter '~/tinker-6.2.06/params'"
        if lib.GetPlatform() == 'WINDOWS': 
            ext='.win'
            self.text1="ex. program  'c://tinker-6.2.06//bin-win64'"
            self.text2="ex. parameter 'c://tinker-6.2.06//params'"
        if lib.GetPlatform() == 'LINUX': ext='.lnx'
        prgpath=os.path.join(self.model.setctrl.GetDir('Programs'),'tinker')
        self.prgfile=os.path.join(prgpath,'tinkerpath'+ext)
        self.tinpath,self.tinprm=TINKEROptimization_Frm.ReadTinkerProgramFile(self.prgfile)        
        #
        self.quit=False
        self.ctrlflag=self.parent.ctrlflag
        self.ctrlflag.Set('tinpathwin',True)
        #        
        self.size=self.GetSize()
        #
        self.CreatePanel()
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
                
    def CreatePanel(self):
        w=self.size[0]; h=self.size[1]
        self.panel=wx.Panel(self,wx.ID_ANY,pos=(-1,-1),size=(w,h))
        self.panel.SetBackgroundColour("light gray")
        yloc=8
        wx.StaticText(self.panel,-1,self.text1,pos=(20,yloc),size=(300,18))
        yloc += 20
        wx.StaticText(self.panel,-1,self.text2,pos=(20,yloc),size=(300,18))
        #wx.StaticText(self.panel,-1,"ex. 'c:/tinker-6.2.06/params'",pos=(170,yloc),size=(120,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"Program:",pos=(5,yloc),size=(60,18)) 
        self.tclprg=wx.TextCtrl(self.panel,-1,self.tinpath,pos=(70,yloc-2),size=(200,18))
        btnbrsprg=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(280,yloc-2),size=(50,20))
        btnbrsprg.Bind(wx.EVT_BUTTON,self.OnBrowsePrg)
        
        yloc += 25
        wx.StaticText(self.panel,-1,"Parameter:",pos=(5,yloc),size=(60,18)) 
        self.tclprm=wx.TextCtrl(self.panel,-1,self.tinprm,pos=(70,yloc-2),size=(200,18))
        btnbrsprm=wx.Button(self.panel,wx.ID_ANY,"browse",pos=(280,yloc-2),size=(50,20))
        btnbrsprm.Bind(wx.EVT_BUTTON,self.OnBrowsePrm)

        yloc += 25
        btnok=wx.Button(self.panel,wx.ID_ANY,"OK",pos=(90,yloc-2),size=(35,20))
        btnok.Bind(wx.EVT_BUTTON,self.OnOK)
        btnrmv=wx.Button(self.panel,wx.ID_ANY,"Clear",pos=(140,yloc-2),size=(45,20))
        btnrmv.Bind(wx.EVT_BUTTON,self.OnClear)
        btncan=wx.Button(self.panel,wx.ID_ANY,"Cancel",pos=(220,yloc-2),size=(50,20))
        btncan.Bind(wx.EVT_BUTTON,self.OnCancel)
    
    def OnBrowsePrg(self,event):
        dirname=lib.GetDirectoryName(self)
        if dirname != "": self.tclprg.SetValue(dirname)

    def OnBrowsePrm(self,event):
        dirname=lib.GetDirectoryName(self)
        if dirname != "": self.tclprm.SetValue(dirname)

    def OnApply(self,event):
        self.tinpath=self.tclprg.GetValue()
        self.tinprm=self.tclprm.GetValue()
        self.quit=False
        self.WriteProgramFile(self.prgfile)
        #
        mess='Tinker program file='+self.prgfile+'\n'
        mess=mess+'ProgramPath '+self.tinpath+'\n'
        mess=mess+'ParamsPath '+self.tinprm
        self.model.ConsoleMessage(mess)

    def WriteProgramFile(self,prgfile):
        f=open(prgfile,'w')
        text='ProgramPath '+self.tinpath+'\n'
        text=text+'ParamsPath '+self.tinprm+'\n'
        f.write(text)
        f.close()
        
    def GetQuit(self):
        return self.quit
    
    def GetProgDir(self):
        return self.tinpath
    
    def GetParamDir(self):
        return self.tinprm
    
    def OnClear(self,event):
        self.tclprg.SetValue("")
        self.tclprm.SetValue("")
    
    def OnCancel(self,event):
        self.ctrlflag.Set('tinpathwin',False)
        self.Destroy()
        
    def OnOK(self,event):
        self.OnApply(1)
        self.OnClose(1)
        
    def OnClose(self,event):
        self.ctrlflag.Set('tinpathwin',False)        
        self.Destroy()        

class ForceField():
    def __init__(self,ffname,fffile):
        self.ffname=ffname #ffname # AMBER-FF99
        self.fffile=fffile # file name of force field paramters
        self.pottermdic={} #self.ReadFFPotTerms()
        self.potoptdic={} #self.ReadFFPotOpts()
        self.pottermlst=[]
        """self.pottermdicsav=[] # a copy of pottermdic"""

    def ReadFFPotOptions(self):
        potopt = [
              ["vdwindex",11],["radiustype",10],["vdwtype",7],["radiusrule",10],
              ["radiustype",10],["radiussize",10],["epsilonrule",11],["vdw-14-scale",12],
              ["chg-14-scale",12],["electric",8],["dielectric",10],["torsionunit",11],
              ["imptorunit",10],["bondunit",8],["bond-cubic",10],["bond-quartic",12], #  MM2       !! TINKER
              ["angleunit",9],["angle-sextic",12],["strbndunit",10],["opbendtype",10], # mm2
              ["opbendunit",10],["opbend-sextic",13],["torsionunit",11],["a-expterm",9],
              ["b-expterm",9],["c-expterm",9],["strbndunit",10],["opbend-cubic",12],
              ["opbend-quartic",14],["opbend-pentic",13],["opbend-sextic",13],
              ["strtorunit",10],["angle-cubic",11],["angle-quartic",13],
              ["angle-pentic",12],["angle-sextic",12] ]

        optdic={}
        if not self.IsFFParamFileAvailable(): return

        f=open(self.fffile,"r")
        for s in f.readlines():
            ss=s.strip()
            for kw,nw in potopt:
                if ss.startswith(kw,0,nw):
                    item=ss.split()
                    if optdic.has_key(kw): continue #optdic[kw].append(item[1])
                    else: optdic[kw]=item[1]
        f.close()
        #print 'optdic',optdic
        #return optdic
        self.potoptdic=optdic
                
    def ReadFFPotTerms(self):
        # read parameter file
        # "atom" term: [[datnmb,type,cls,atmnam,atomic,mass,vale,com],...]
        # "bond" term: [[datnmb,cls1,cls2,bondk,bondr],...]
        # "angle" term: [[datnmb,cls1,cls2,cls3,anglek,anglea],...]
        # "torsion" term: [[datnmb,cls1,cls2,cls3,cls4,torsk1,torsa1,torsp1,
        #                   torsk2,torsa2,torsp2,torsk3,torsa3,torsp3],...]
        potterms=[["atom ",5],["vdw ",4],["vdwpr ",6],["vdw14 ",6],["bond ",5],["bond3 ",6],
                  ["bond4 ",6],["bond5 ",6],["angle ",6],["angle3 ",7],["angle4 ",7],
                  ["angle5 ",7],["angang ",7],["torsion ",8],["torsion4 ",9],
                  ["torsion5 ",9],["imptors ",8],["improper ",9],["tortors ",8],
                  ["ureybrad ",9],["hbond ",6],["strbnd ",7],["opbent ",7],["strtors ",8],
                  ["diploe ",7],["dipole4 ",8],["dipole5 ",8],["piatom ",7],["pibond ",7],
                  ["pibond5 ",8],["electneg ",9],["charge ",7],["biotype ",8] ]
        # note: 'DANG','HOCH','MM2','MM3','MM3PRO','OPLSUA','SMOOTHUA','TINY'
        # does not have atmcls data in "atom" data
        if not self.IsFFParamFileAvailable(): return
        #
        potdic={}
        f=open(self.fffile,"r")
        for s in f.readlines():
            ss=s.strip()
            for kw, nw in potterms:            
                if ss.startswith(kw,0,nw):
                    keywd=kw[:nw-1]
                    lst=self.SetParamsInList(keywd,ss)
                    if len(lst) <= 0: continue
                    if potdic.has_key(keywd): potdic[keywd].append(lst)
                    else: potdic[keywd]=[lst]
        f.close()
        #print 'potdic',potdic.keys()
        if potdic.has_key('atom'):
            atom=potdic['atom']
            
            if len(atom) > 0 and len(atom[0]) == 6: # this ff does not have atomcls data
                for i in range(len(atom)):          # so, add atmcls data for convenience
                    atmtyp=atom[i][0]; atom[i].insert(0,atmtyp)
            """
            # convert integer to string
            for i in range(len(atom)):
                atom[i][0]=str(atom[i][0]) # type
                atom[i][1]=str(atom[i][1]) # cls
                atom[i][5]=str(atom[i][5]) # vale
            """
            # replace element # with element name
            for i in range(len(atom)):
                atom[i][3]=const.ElmSbl[int(atom[i][3])].strip()
        # add parameter number
        self.pottermlst=potdic.keys()
        for term in self.pottermlst:
            param=potdic[term]
            for i in range(len(param)):
                param[i].insert(0,str(i+1))
        #print 'pottermlst',self.pottermlst
        #print 'potdic',potdic
        #return potdic
        self.pottermdic=potdic


    def IsFFParamFileAvailable(self):
        #if self.fffile == "":
        #    wx.MessageBox("Forcefield parametr file is not specified.","",style=wx.OK|wx.ICON_EXCLAMATION)
        #    return False       
        if not os.path.exists(self.fffile):
            lib.MessageBoxOK("Forcefield parameter file is not found. file="+self.fffile,"")
            return False           
        return True

    def FindParamNumber(self,clslst):
        # clslst: [csl1,cls2] for bond, [cls1,cls2,cls3] for angle,
        # and [cls1,cls2,cls3,cls4] for tortion
        paramnmb=0
        return paramnmb
    
    def FindAtmNam(self,clsnmb):
        atmnam=''
        atom=self.pottermdic['atom']
        for datnmb,typ,cls,nam,atmic,mass,vale,com in atom:
            if int(cls) == int(clsnmb):
                atmnam=nam; break
        return atmnam
    
    def FindAtmNamAtmicVale(self,clsnmb):
        atmatmic="XX"; atmnam=""; atmvale="-1"
        atom=self.pottermdic['atom']
        for datnmb,typ,cls,nam,atmic,mass,vale,com in atom:
            if int(cls) == int(clsnmb):
                atmatmic=atmic; atmnam=nam; atmvale=vale; break
        return atmnam,atmatmic,atmvale
    
    def SetPotTermDic(self,potdic):
        self.pottermdic=potdic
    
    def SetPotOptionDic(self,potopt):
        self.potoptdic=potopt

    def AddPotTermToDic(self,pottermname,potterm):
        self.pottermdic[pottermname]=potterm
        
    def AddPotOptToDic(self,potdic):
        self.potoptdic.update(potdic)                
    def MakeUniqueElmValeList(self):
        lst=[]
    
    def MakeUniqueNamClassList(self):
        lst=[]

    def SetParamsInList(self,kw,ss):
        lst=[]
        ns=ss.find('!')
        if ns >= 0: ss=ss[:ns-1]
        
        if kw == "torsion" and len(ss.split()) <= 5: return lst

        if kw == "atom":
            st,descri=self.PickupDescription(ss)
            item=st.split()
            #    atmtyp, atmnam,(class),atmic, mass,vale,descri
            for i in range(1,len(item)): lst.append(item[i])
            lst.append(descri)
        elif kw == "biotype":
            st,descri=self.PickupDescription(ss)
            item=st.split()
            #    Atmtyp, atmnam, atmic, mass, vale
            lst=[item[1],item[2],item[3],descri]
        else:
            item=ss.split()
            for i in range(1,len(item)):
                if item[i][0:1] == "!" or item[i][0:1] == "#": continue
                lst.append(item[i])
        #
        return lst
                    
    def GetFFPotTerm(self,term):
        if self.pottermdic.has_key(term):
            return self.pottermdic[term]
        else:
            lib.MessageBoxOK("Potential term not found. term="+term,"")
            return []
    
    def PickupDescription(self,ss):
        dq='"'; sq="'"
        st=ss.replace(sq,"~")
        descri=lib.GetStringBetweenQuotation(st)
        if len(descri) > 0:
            ns=ss.find(dq)
            if ns >= 0: s1=st[:ns]
            s2=st[ns+1:]
            ns=s2.find(dq)
            if ns >= 0:
                s2=s2[ns+1:]; st=s1+s2
            descri0=descri[0].replace("~","'")
            return st,descri0
        else:
            st=st.replace('~',sq)
            return st,""

    def GetFFPotOptions(self):
        return self.potformdic
       
    def GetFFPotTermList(self):
        termlst=self.pottermdic.keys()
        termlst.sort()
        return termlst
    
    def GetFFName(self):
        return self.forcefieldname
    
    def ListFFPotTerm(self,term):

        pass
    
    def GetFFAtmTypList(self):
        atmtyplst=[]
        #print 'pottermdic.keys',self.pottermdic.keys()
        atmtyplst=self.pottermdic['atom']

        #print 'atmtyplst',atmtyplst
        
        return atmtyplst
    
    def AddFFPotTerm(self,termname,termdata):
        if self.pottermdic.has_key(termname):
            ans=lib.MessageBoxYesNo(termname+"is already exists. Replace it?","")
            if not ans: return
        self.pottermdic[termname]=termdata
    
    def DelFFPotTerm(self,termname):
        del self.pottermdic[termname]
        
    def SetFFTerms(self,paramtext):
        text=paramtext
        self.ffterms=[]
        for s in text:
            value=self.PickupParamValue(s)
            if value == -1: continue                
            self.ffterms.append(value)
    
    def PickupOptionValue(self,line):
        value=-1
        text=line.strip()
        for kw,fmt in self.paramoptlst:
            nw=len(kw)
            if text.startswith(kw,0,nw):
                item=text.split()
                value=item[1]
                if fmt == "float": value=float(value)
                break
        return value                 
    
    def PickupFFTermName(self,line):    
        value=-1
        text=line.strip()
        for kw in self.fftermlst:
            nw=len(kw)
            if text.startswith(kw,0,nw):
                value=kw; break
        return value                 
    
    def GetFFTermParams(self,termname):
        term=[]; ns=len(termname)
        for s in self.paramtext:
            if s.strip().startswith(termname,0,ns):
                tmp=[]
                item=s.split()
                for t in item:
                    if t.isdigit: t=int(t)
                    elif t.replace('.','').isdigit: t=float(t)
                    tmp.append(t)
                term.append(tmp)
        return term

    def AddTermData(self,termname,data):
        pass

    def DelTermData(self,ternmame,data):
        pass

    def ChangeTermData(self,termname,data):
        pass
    
    def WriteForceFieldOnFile(self,filename):
        # termname: all=all terms
        pass
        
class TINKEROptimization_Frm(wx.Frame):
    def __init__(self,parent,id):
        self.title='TINKER Optimization'
        winpos=[-1,-1]; winsize=lib.WinSize((280,380)) #((275,355))
        #if const.SYSTEM == const.MACOSX: winsize=(275,355)
        wx.Frame.__init__(self,parent,id,self.title,pos=winpos,size=winsize,
               style=wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX)      
        # ctrlflag
        #self.fum=fum
        self.mdlwin=parent
        self.ctrlflag=parent.model.ctrlflag
        #if self.ctrlflag.GetCtrlFlag('tinoptwin'):
        #    self.Destroy()
        #    return
        #if self.ctrlflag.GetCtrlFlag('tinoptwin'): 
        #    self.OnClose(0)
        #self.ctrlflag.SetCtrlFlag('tinoptwin',True)
                
        #self.setfile=parent.model.setfile
        self.model=parent.model
        if not self.model.mol:
            mess='No molecule data. Open pdb/xyz file in fumodel.'
            lib.MessageBoxOK(mess,"")
            self.OnClose(1)                       
        self.mol=self.model.mol
        self.molnam=self.mol.name
        self.molnam,ext=os.path.splitext(self.molnam)
        scriptdir=self.model.setctrl.GetDir('Scripts')
        self.rmsfitscript="rms-fit.py"
        self.rmsfitscript=os.path.join(scriptdir,self.rmsfitscript)
        self.ctrlflag.Set('tinpathwin',False)
        #self.model.ConsoleMessage("Loaded TINKER_optimize script")
          # set icon
        try: lib.AttachIcon(self,const.FUMODELICON)
        except: pass
        #
        ###self.notepadexe="C:/Windows/System32/notepad.exe"
        # scratch directory
        #self.scrdir=self.model.exedir+"/scr"
        #if not os.path.isdir(self.scrdir): os.mkdir(self.scrdir)
        self.scrdir=self.model.setctrl.GetDir('Scratch')
        self.basenam=os.path.join(self.scrdir,"tinker-"+self.molnam)
        # Menu
        self.menubar=self.MenuItems()
        self.SetMenuBar(self.menubar)
        self.Bind(wx.EVT_MENU,self.OnMenu)
 
        self.mess=''
        self.inputfmt="xyz" # 'pdb' ot 'xyz'
        #self.pdbfile=""
        #self.xyzfile=""
        self.potoptiondic={}
        #
        self.mechanicerr=False
        self.quit=False
        #err,self.tinkerprgdir,self.tinkerprmdir=GetTinkerPrgAndPrmDir(self.setfile)

        self.tinkerprgdir=""; self.tinkerprmdir=""
        self.prgfile=self.GetTinkerPrgFile()
        self.GetTinkerPrgAndPrmDir()
        #
        self.filename=""
        self.openexeprgwin=False
        self.ffname="AMBER99"
        self.uterms=[]
        self.utermdic={}
        self.tinkeratoms=[]
        self.pdbatoms=[]
        self.tgtff=None
        #
        self.var="Cartesian"
        self.varlst=["Cartesian","internal","rigid body"]
        #
        self.prgnam="newton"
        self.methodlst=[]
        self.method="A" # auto
        
        self.ffnamelst,self.fffiledic=GetFFNamesAndFiles(self.tinkerprmdir)
                
        self.tinprglst,self.tinprgdic=self.SetTinkerOptPrg()
        self.xyzprglst,self.intprglst,self.rgdprglst=self.SetOptPrgList()        
        self.filename=self.fffiledic[self.ffname]
        self.fffile=self.filename
        #
        self.rmsgrd=0.1 # for rough optimization!
        self.maxiter=1000
        self.updatesteps=1
        self.dielec=1.0     # for amber
        self.vdw14scale=2.0 # for amber
        self.chg14scale=1.2 # for amber
        self.tinzmt=[]
        self.rigidbody=[]
        self.active=[]
        self.optmol=None
        self.overlay=False
        self.multichain=False
        if len(self.model.ListChainName()) > 1: self.multichain=True
        #
        self.err=False
        self.pdbfile=""; self.seqfile=""; self.xyzfile=""
        self.intfile=""; self.outfile=""; self.keyfile=""
        self.xyz2file=""; self.int2file=""; self.tmpfile=""
        self.anlfile=""
        self.savsel=[]
        self.SetTempIOFiles()
        self.DeleteTempIOFiles()
        #
        ret=self.ConvertPDBForTinker()
        if ret: self.OnClose(1) #Destroy()
        #
        self.savmol=self.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        #
        self.pltene=False; self.pltgrd=False; self.pltnon=True; self.pltgeo=False
        #
        self.CreatePanel()
        
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        
        # Event handler to receive message when child thread ends
        subwin.ExecProg_Frm.EVT_THREADNOTIFY(self,self.OnThreadJobEnded)

        self.Show()
           
    def CreatePanel(self):
        [w,h]=self.GetClientSize()
        xsize=w; ysize=h
        self.panel=wx.Panel(self,-1,pos=(-1,-1),size=(xsize,ysize)) #ysize))
        self.panel.SetBackgroundColour("light gray")
        hcb=const.HCBOX
        yloc=10

        wx.StaticText(self.panel,-1,"Forcefield:",pos=(10,yloc),size=(60,18)) 
        self.cmbff=wx.ComboBox(self.panel,-1,'',choices=self.ffnamelst, \
                               pos=(70,yloc-2),size=(115,hcb),style=wx.CB_READONLY)                      
        #self.SetForceField()
        self.cmbff.SetStringSelection(self.ffname)
        self.cmbff.Bind(wx.EVT_COMBOBOX,self.OnFFChoice)
        btnprm=wx.Button(self.panel,wx.ID_ANY,"Other",pos=(200,yloc-2),size=(60,22))
        btnprm.Bind(wx.EVT_BUTTON,self.OnOpenPrmFile)
        # threshold, maxcycle, 
        yloc += 25
        wx.StaticText(self.panel,-1,"charge 1-4 scale:",pos=(25,yloc),size=(100,18)) 
        self.tclchg14=wx.TextCtrl(self.panel,-1,str(self.chg14scale),pos=(135,yloc),size=(50,18))
        #self.tclgrd.Bind(wx.EVT_TEXT,self.OnGradientInput)
        #
        yloc += 25
        wx.StaticText(self.panel,-1,"vdW 1-4 scale:",pos=(25,yloc),size=(100,18)) 
        self.tclvdw14=wx.TextCtrl(self.panel,-1,str(self.vdw14scale),pos=(135,yloc),size=(50,18))
        yloc += 25
        wx.StaticText(self.panel,-1,"dielectric:",pos=(25,yloc),size=(100,18)) 
        self.tcldielec=wx.TextCtrl(self.panel,-1,str(self.dielec),pos=(135,yloc),size=(50,18))
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"Variables:",pos=(10,yloc),size=(50,18)) 
        self.cmbvar=wx.ComboBox(self.panel,-1,'',choices=self.varlst, \
                               pos=(65,yloc-2),size=(80,hcb),style=wx.CB_READONLY)                      
        self.cmbvar.SetStringSelection(self.var)
        self.cmbvar.Bind(wx.EVT_COMBOBOX,self.OnVariable)
        self.btnrgd=wx.Button(self.panel,wx.ID_ANY,"def rigid body",pos=(160,yloc-2),size=(100,22))
        self.btnrgd.Bind(wx.EVT_BUTTON,self.OnDefRigidBody)
        if self.var != "rigid body": self.btnrgd.Disable()
        #
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),style=wx.LI_HORIZONTAL)                
        yloc += 8
        wx.StaticText(self.panel,-1,"Program:",pos=(10,yloc),size=(50,18)) 
        self.cmbprg=wx.ComboBox(self.panel,-1,'',choices=self.tinprglst, \
                               pos=(65,yloc-2),size=(80,hcb),style=wx.CB_READONLY)                      
        self.SetOptProgram()
        self.cmbprg.SetStringSelection(self.prgnam)
        self.cmbprg.Bind(wx.EVT_COMBOBOX,self.OnOptProgram)
                
        wx.StaticText(self.panel,-1,"method:",pos=(150,yloc),size=(45,18)) 
        self.cmbmet=wx.ComboBox(self.panel,-1,'',choices=self.methodlst, \
                               pos=(200,yloc-2),size=(60,hcb),style=wx.CB_READONLY)                      
        self.SetOptMethod()
        self.cmbmet.SetStringSelection(self.method)
        # threshold, maxcycle, 
        yloc += 25
        wx.StaticText(self.panel,-1,"RMS gradient convergence:",pos=(25,yloc),size=(160,18))  
        self.tclgrd=wx.TextCtrl(self.panel,-1,str(self.rmsgrd),pos=(185,yloc),size=(50,18))
        #self.tclitr.Bind(wx.EVT_TEXT,self.OnMaxCycleInput)
        yloc += 25
        wx.StaticText(self.panel,-1,"maximum cycles:",pos=(25,yloc),size=(100,18)) 
        self.tclitr=wx.TextCtrl(self.panel,-1,str(self.maxiter),pos=(130,yloc),size=(50,18))
        #wx.StaticText(self.panel,-1,"RMS gradient (kcal/A/mol):",pos=(25,yloc),size=(150,18))
        #self.tclgrd.Bind(wx.EVT_TEXT,self.OnGradientInput)
        #        
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        wx.StaticText(self.panel,-1,"Plot:",pos=(10,yloc),size=(30,18)) 
        self.rbtene=wx.RadioButton(self.panel,-1,"energy",pos=(45,yloc),style=wx.RB_GROUP) #size=(60,18))
        self.rbtene.SetValue(self.pltene)
        self.rbtgrd=wx.RadioButton(self.panel,-1,"gradient",pos=(115,yloc)) #,size=(60,18))
        self.rbtgrd.SetValue(self.pltgrd)
        self.rbtnoplt=wx.RadioButton(self.panel,-1,"none",pos=(185,yloc)) #,size=(60,18))
        self.rbtnoplt.SetValue(self.pltnon)
        #btnopt.Bind(wx.EVT_BUTTON,self.OnPltOptions)
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,2),style=wx.LI_HORIZONTAL)
        yloc += 8
        self.btnreset=wx.Button(self.panel,wx.ID_ANY,"Reset",pos=(20,yloc-2),size=(50,22))
        self.btnreset.Bind(wx.EVT_BUTTON,self.OnReset)
        #
        self.btnexe=wx.Button(self.panel,wx.ID_ANY,"Exec",pos=(80,yloc-2),size=(50,22))
        self.btnexe.Bind(wx.EVT_BUTTON,self.OnExecute)
        self.btnovl=wx.Button(self.panel,wx.ID_ANY,"Overlay",pos=(140,yloc-2),size=(50,22))
        self.btnovl.Bind(wx.EVT_BUTTON,self.OnOverlay)
        self.btnfit=wx.Button(self.panel,wx.ID_ANY,"RMS fit",pos=(200,yloc-2),size=(50,22))
        self.btnfit.Bind(wx.EVT_BUTTON,self.OnRMSFit)
        self.btnovl.Disable(); self.btnfit.Disable()
        #btnkil=wx.Button(self.panel,wx.ID_ANY,"Kill",pos=(100,yloc-2),size=(50,22))
        #btnkil.Bind(wx.EVT_BUTTON,self.OnKill)
        yloc += 25
        wx.StaticLine(self.panel,pos=(0,yloc),size=(w,4),style=wx.LI_HORIZONTAL)
        yloc += 12
        wx.StaticText(self.panel,-1,"Coordinates:",pos=(10,yloc),size=(75,18)) 
        self.btnupd=wx.Button(self.panel,wx.ID_ANY,"Update",pos=(90,yloc-2),size=(50,22))
        self.btnupd.Bind(wx.EVT_BUTTON,self.OnUpdate)
        self.btnund=wx.Button(self.panel,wx.ID_ANY,"Undo",pos=(150,yloc-2),size=(40,22))
        self.btnund.Bind(wx.EVT_BUTTON,self.OnUndo)
        self.btnupd.Disable(); self.btnund.Disable()
        wx.StaticLine(self.panel,pos=(200,yloc-12),size=(4,38),style=wx.LI_VERTICAL)
        btncan=wx.Button(self.panel,wx.ID_ANY,"Close",pos=(210,yloc-2),size=(50,22))
        btncan.Bind(wx.EVT_BUTTON,self.OnClose)
    
    def GetTinkerPrgFile(self):
        prgfile=''
        if self.mdlwin:
            prgdir=self.model.setctrl.GetDir('Programs')            
            tinkerdir=os.path.join(prgdir,'tinker')
            pathfile='tinkerpath.mac'
            if lib.GetPlatform() == 'WINDOWS': pathfile='tinkerpath.win'
            elif lib.GetPlatform() == 'MACOSX': pathfile='tinkerpath.mac'
            prgfile=os.path.join(tinkerdir,pathfile)
            prgfile=os.path.expanduser(prgfile)
        return prgfile  

    @staticmethod
    def ReadTinkerProgramFile(prgfile):
        prmdir=''; prgdir=''
        f=open(prgfile)
        for s in f.readlines():
            s=s.strip()
            if s[:1] == '#': continue
            if s[:10] == 'ParamsPath':
                items=lib.SplitStringAtSpaces(s)
                prmdir=items[1].strip()
            if s[:11] == 'ProgramPath':
                items=lib.SplitStringAtSpaces(s)
                prgdir=items[1].strip()
        f.close()
        return prgdir,prmdir
        
    def GetTinkerPrgAndPrmDir(self):
        #self.tinkerprgdir=lib.ReadSetFile(self.setfile,"program","TINKER")
        #self.tinkerprmdir=lib.ReadSetFile(self.setfile,"parameter","TINKER")          

        if not os.path.exists(self.prgfile):
            mess='No tinkerpath file in FUDATASET/Programs/tinker/.'
            lib.MessageBoxOK(mess,'tinker-optimize.py(GetTinkerPrgAndPrmDir')
            return
       # self.tinkerprgdir=lib.GetProgramPath(self.prgfile,"TINKER","program")
       # self.tinkerprmdir=lib.GetProgramPath(self.prgfile,"TINKER","parameter")          
        self.tinkerprgdir,self.tinkerprmdir=TINKEROptimization_Frm.ReadTinkerProgramFile(self.prgfile)
        mess='prgfile='+self.prgfile+'\n'
        mess=mess+'tinkerprgdir='+self.tinkerprgdir+'\n'
        mess=mess+'tinkerprmdir='+self.tinkerprmdir+'\n'
        mess=mess+'molname='+self.molnam
        self.model.ConsoleMessage(mess)

        if not os.path.isdir(self.tinkerprgdir) or not os.path.isdir(self.tinkerprmdir):
            lib.MessageBoxOK("TINKER path is wrong. Please reset.","")
            tinpath=SetPathForTinker_Frm(self,-1,self.prgfile) #self.tinkerprgdir,self.tinkerprmdir)
            tinpath.ShowModal()
            if tinpath.GetQuit(): self.OnClose(1)
            self.tinkerprgdir=tinpath.GetProgDir()
            self.tinkerprmdir=tinpath.GetParamDir()
            
    def SetTinkerOptPrg(self):
        prgdic={}
        prglst=["newton","newtrot","minimize","minirot","minrigid","optimize",
             "optirot","optrigid"]
        for p in prglst: prgdic[p]=GetTinkerProgram(self.tinkerprgdir,p)
        
        return prglst,prgdic
 
    def SetOptPrgList(self):
        xyzprglst=[]; intprglst=[]; rgdprglst=[]
        pxyz=["newton","minimize","optimize"]
        pint=["newtrot","minirot","optirot"]
        prgd=["optrigid","minrigid"]
        for p in pxyz:
            if self.tinprgdic.has_key(p): xyzprglst.append(p)
        for p in pint:
            if self.tinprgdic.has_key(p): intprglst.append(p)
        for p in prgd:
            if self.tinprgdic.has_key(p): rgdprglst.append(p)
        return xyzprglst,intprglst,rgdprglst
    
    def SetTempIOFiles(self):
        self.pdbfile=self.basenam+".pdb"
        self.seqfile=self.basenam+".seq"
        self.xyzfile=self.basenam+".xyz"
        self.xyz2file=self.basenam+".xyz_2"
        self.intfile=self.basenam+".int"
        self.int2file=self.basenam+".int_2"
        self.outfile=self.basenam+".out"
        self.keyfile=self.basenam+".key"
        self.anlfile=self.basenam+".anl"
        self.tmpfile=self.basenam+".tmp"
            
    def OnOpenPrmFile(self,event):
        prmfile=""
        wcard="TINKER paramter file(*.prm)|*.prm"
        #dlg=wx.FileDialog(self,"Open file...",os.getcwd(),style=wx.OPEN,wildcard=wcard)
        #if dlg.ShowModal() == wx.ID_OK: prmfile=dlg.GetPath()
        prmfile=lib.GetFileName(self,wcard,"r",True,"")
        #if prmfile == "":
        #    mess="Failed to open file. File/directory name can not be decoded by utf8."
        #    wx.MessageBox(mess,"",style=wx.OK|wx.ICON_INFORMATION)
        #    return
        if prmfile == "": return
        base,ext=os.path.splitext(prmfile) 
        head,prmnam=os.path.split(base)
        #print 'prmnam',prmnam
        if not self.fffiledic.has_key(prmnam): self.ffnamelst.append(prmnam)
        self.fffiledic[prmnam]=prmfile
        self.cmbff.SetItems(self.ffnamelst)
        
        self.cmbff.SetValue(prmnam)
        self.fffile=prmfile
        self.SetFFOptions()

    def SetFFOptions(self):
        optdic=self.ReadFFPotOptions(self.fffile)
        if optdic.has_key("chg-14-scale"): self.chg14scale=optdic["chg-14-scale"]
        else: self.chg14scale=1.0 
        self.tclchg14.SetValue(str(self.chg14scale))
        if optdic.has_key("vdw-14-scale"): self.vdw14scale=optdic["vdw-14-scale"]
        else: self.vdw14scale=1.0
        self.tclvdw14.SetValue(str(self.vdw14scale))
        if optdic.has_key("dielectric"): self.dielec=optdic["dielectric"]
        else: self.dielec=1.0
        self.tcldielec.SetValue(str(self.dielec))
    
    def OnFFChoice(self,event):
        self.ffname=self.cmbff.GetStringSelection()
        self.fffile=self.fffiledic[self.ffname]

        self.SetFFOptions() 
        #self.curff=ForceField(self.ffname,self.fffile)
    
    def MakeTinkerZmt(self):    
        #self.DeleteTempIOFiles()
        #self.model.wrk.WritePDBMol(self.pdbfile,"","",True)
        err=self.ExecutePDBXYZ()
        if err: return
        #print 'xyzfile',os.path.exists(self.xyzfile)
        err=self.ExecuteXYZINT()
        if err: return
        #print 'intfile',os.path.exists(self.intfile)
        if os.path.exists(self.intfile):
            self.tinzmt=rwfile.ReadTinkerZmt(self.intfile)    
 
    def ExecuteINTXYZ(self):
        self.err=False
        prg=GetTinkerProgram(self.tinkerprgdir,"intxyz")
        if not os.path.exists(prg):
            lib.MessageBoxOK("Not found TINKER INTXYZ program.","")
            return
        #prmfile=self.fffiledic[self.ffname]
        cmd=prg+" "+self.intfile
        #print 'cmd in pdbxyz',cmd
        self.execprg=False
        cmd=cmd+" > "+self.outfile
        #err0=os.system(cmd)
        err0=subprocess.call(cmd,shell=True)
        err1=self.CheckOutput()
        err=err0 or err1
        if err:
            mess="Error occured in TINKER INTXYZ.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."
            lib.MessageBoxOK(mess,"")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return
        return err
    
    def ExecutePDBXYZ(self):
        prg=GetTinkerProgram(self.tinkerprgdir,"pdbxyz")
        if not os.path.exists(prg):
            lib.MessageBoxOK("Not found TINKER PDBXYZ program.","")
            return

        self.err=False
        if not os.path.exists(self.pdbfile):
            #self.model.DeleteAllTers()
            #self.model.wrk.WritePDBMol(self.pdbfile,"","",True) 
            ret=self.ConvertPDBForTinker()

        prmfile=self.fffiledic[self.ffname]
        chain=""
        if self.multichain: chain=" ALL"
        cmd=prg+" "+self.pdbfile+chain+" "+prmfile
        
        #print 'cmd in pdbxyz',cmd
        self.execprg=False
        cmd=cmd+" > "+self.outfile
        #err0=os.system(cmd)
        err0=subprocess.call(cmd,shell=True)
        err1=self.CheckOutput()
        err=err0 or err1
        if err:
            mess="Error occured in TINKER PDBXYZ.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."
            lib.MessageBoxOK(mess,"")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return
        return err
    
    def ResNumberDic(self,reslst):
        resnmbdic={}
        for i in range(len(reslst)):
            seq=0
            for res,nmb in reslst[i]:
                seq += 1; name=res+":"+str(nmb)+":"+str(i)
                resnmbdic[name]=seq
        return resnmbdic
            
    def BackResNumber(self,resnmbdic):
        ncha=1; chain0=self.mol.atm[0].chainnam
        for atom in self.mol.atm:
            if atom.chainnam != chain0:
                ncha += 1; chain0=atom.chainnam
            name=atom.resnam+":"+str(atom.resnmb)+":"+str(ncha)
            if not resnmbdic.has_key(name):
                print 'program error',name
            atom.resnmb=resnmbdic[name]
                
    def ConvertPDBForTinker(self):
        #
        nonaares=self.model.ListNonAAResidue(True)
        if len(nonaares) > 0:
            mess='The molecule has non-AA residues. Is it OK to delete them?'
            yesno=lib.MessageBoxYesNo(mess,"")
            if not yesno: return 1
        # tinker PDBXYZ
        prg=GetTinkerProgram(self.tinkerprgdir,"pdbxyz")
        if not os.path.exists(prg):
            lib.MessageBoxOK("Not found TINKER PDBXYZ program.","")
            return 0     
        self.err=False
        #nonaares=self.model.ListNonAAResidue(True)
        self.model.DeleteAllTers()        
        self.model.RenameHis()
        #self.model.ReorderHydrogensIntoTinker()
        self.mol.DelHydrogen([])
        
        natm=len(self.mol.atm)
        self.mol.WritePDBMol(self.pdbfile,"","",True)              
        # tinker PDBXYZ
        prmfile=self.fffiledic[self.ffname]
        chain=""
        if self.multichain: chain=" ALL"
        cmd=prg+" "+self.pdbfile+chain+" "+prmfile
        #print 'cmd in pdbxyz',cmd
        self.execprg=False
        cmd=cmd+" > "+self.outfile
        #err0=os.system(cmd)
        err0=subprocess.call(cmd,shell=True)
        err1=self.CheckOutput()
        err=err0 or err1
        if err:
            mess="Error occured in TINKER PDBXYZ.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."            
            lib.MessageBoxOK(mess,"")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return 1
        os.remove(self.basenam+".pdb") 
        #
        err1=self.ExecuteXYZPDB(self.xyzfile)
        if err1:
            mess="Error occured in TINKER XYZPDB.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."            
            lib.MessageBoxOK("mess","")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return 1           
        err=err or err1
        #
        self.pdbatoms,fuoptdic=rwfile.ReadPDBMol(self.pdbfile)
        #
        if len(self.pdbatoms[0]) <= 0:
            lib.MessageBoxOK("No atoms in TINKER pdbfile.","")            
            self.OnClose(1); return
        self.mol.SetPDBMol(self.pdbatoms)
        #
        self.SetSelectTemp(self.model.mol.atm,True)
        self.model.AddBondUseBondLength()
        selectedreslst=self.model.ListResidue(False)        
        #print 'selectedres',selectedreslst
                
        #self.model.SetSelectAll(False)
        """ not completed. should do after minimization """
        #self.BackResNumber(resnmbdic)
        #if len(selectedreslst) > 0:
        #    self.model.SetSelectResidue(selectedreslst,True)
        """ above method """            
        
        self.mol.AddBondUseBL([])
        self.SetSelectTemp(self.model.mol.atm,False)
        
        #self.model.FitToScreen(False)
        self.model.DrawMol(True)
        #
        if len(nonaares) > 0:
            self.model.ConsoleListList("Non-AA residues were deleted in TINKER.",nonaares)
        mess="Atom name and atom order were changed in TINKER.\n"
        mess=mess+"All hydrogen atoms were re-attached in TINKER."
        self.model.ConsoleMessage(mess)
        #
        return 0

    def ExecuteXYZPDB(self,xyzfile):
        prg=GetTinkerProgram(self.tinkerprgdir,"xyzpdb")
        if not os.path.exists(prg):
            lib.MessageBoxOK("Not found TINKER INTPDB program.","")
            return

        self.err=False
        prmfile=self.fffiledic[self.ffname]
        cmd=prg+" "+xyzfile+" "+prmfile
        #print 'cmd in xyzpdb',cmd
        self.execprg=False
        cmd=cmd+" > "+self.outfile
        #err0=os.system(cmd)
        err0=subprocess.call(cmd,shell=True)
        err1=self.CheckOutput()
        err=err0 or err1
        if err:
            mess="Error occured in TINKER XYZPDB.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."            
            lib.MessageBoxOK(mess,"")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return
        return err

    def ExecuteXYZINT(self):
        self.err=False
        prg=GetTinkerProgram(self.tinkerprgdir,"xyzint")
        if not os.path.exists(prg):
            lib.MessageBoxOK("Not found TINKER XYZINT program.","")
            return
    
        cmd=prg+" "+self.xyzfile+" A 'fu-temp'"
        #print 'cmd in xyzint',cmd
        self.execprg=False
        cmd=cmd+" > "+self.outfile
        #err0=os.system(cmd)
        err0=subprocess.call(cmd,shell=True)
        err1=self.CheckOutput()
        err=err0 or err1
        if err:
            mess="Error occured in TINKER XYZINT.\n"
            mess=mess+"Delete all tempollary files in fu scratch directory."
            lib.MessageBoxOK(mess,"")
            #os.spawnv(os.P_NOWAIT,self.notepadexe,["notepad.exe"+' '+self.outfile])
            return
        return err
    
    def CheckOutput(self):
        err=False
        """ """
        self.model.ConsoleMessage('outfile='+self.outfile)
        f=open(self.outfile,"r")
        for s in f.readlines():
            if s.find('Error in') >= 0:
                err=True; break
        f.close()
        return err
        
    def DeleteTempIOFiles(self):
        # remove temporaly files used in tinker calculations
        try:
            for name in glob.glob(self.basenam+".*"): os.remove(name)
        except: lib.MessageBoxOK("Failed to delete temporally files","")
    
    def OnDefRigidBody(self,event):
        if len(self.rigidbody) <= 0:
            lib.MessageBoxOK("No rigid body groups are defined.","")
            return                

    def OnVariable(self,event):
        var=self.var
        self.var=self.cmbvar.GetStringSelection()
        if var != self.var:
            self.DeleteTempIOFiles()
            #self.model.DeleteAllTers()
            #self.model.mol.WritePDBMol(self.pdbfile,"","",True)
            ret=self.ConvertPDBForTinker()
            if ret: return
            
        if self.var == "Cartesian":
            self.prgnam="newton"; self.btnrgd.Disable()
        elif self.var == "internal": # ZMT
            self.prgnam="newtrot"; self.btnrgd.Disable()
            self.MakeTinkerZmt()
        elif self.var == "rigid body":
            lib.MessageBoxOK("Sorry. Rigid-body optimization is not supported yet.","")
            return
    
            self.prgnam="optrigid"; self.btnrgd.Enable()
        #
        #self.cmbprg.SetStringSelection(self.prgnam)
        self.SetOptProgram()
        self.SetOptMethod()
        
    def OnOptProgram(self,event):
        self.prgnam=self.cmbprg.GetStringSelection()
        self.SetOptMethod()
               
    def OnFFOptions(self,event):
        # open option panel
        pass
    
    def SetOptProgram(self):
        if self.var == "Cartesian": self.cmbprg.SetItems(self.xyzprglst)
        elif self.var == "internal": self.cmbprg.SetItems(self.intprglst)        
        else: self.cmbprg.SetItems(self.rgdprglst)    
        self.cmbprg.SetStringSelection(self.prgnam)
        
    def SetOptMethod(self):
        self.methodlst=[]
        self.method=""
        if self.prgnam == "newton" or self.prgnam == "newtrot":
            self.cmbmet.Enable()
            meth=["A","Newton","TNCG","DTNCG"]
            for m in meth: self.methodlst.append(m)
            self.method="A"
            #
            self.cmbmet.SetItems(self.methodlst)
            self.cmbmet.SetStringSelection(self.method)
        else: self.cmbmet.Disable()

    def OnRMSFit(self,event):
        if len(self.optmol.atm) <= 0:
            lib.MessageBoxOK("No optimized mol data is availabel.","")
            return
        # allow to update
        self.btnupd.Enable(); self.btnund.Enable()
        #for atom in self.model.mol.mol: atom.color=const.ElmCol['EX'] # cyan
        if not self.overlay:
            opttmp=self.optmol.CopyAtom() #copy.deepcopy(self.optmol.atm)
            self.model.MergeMolecule(opttmp,False)
            #self.optmol.atm=optsav
        #
        self.model.SelectAll(True)
        self.model.ExecuteScript1(self.rmsfitscript)

        #self.model.DrawMol(True)
    
    def OnOverlay(self,event):
        if len(self.optmol.atm) <= 0:
            lib.MessageBoxOK("No optimized mol data is availabel.","")
            return            
        # allow to update
        self.btnupd.Enable(); self.btnund.Enable()
        #for atom in self.model.mol.mol: atom.color=const.ElmCol['EX'] # cyan
        self.savmol=self.model.mol.CopyAtom() #copy.deepcopy(self.model.mol.atm)
        optsav=self.optmol.CopyAtom() #copy.deepcopy(self.optmol.atm)
        self.model.MergeMolecule(self.optmol.atm,False)
        #self.optmol.atm=copy.deepcopy(optsav)
        self.optmol.atm=optsav #copy.deepcopy(optsav)
        self.overlay=True
        self.btnfit.Enable()
 
        self.model.DrawMol(True)
    
    def OnUpdate(self,event):        
        self.model.mol.atm=self.optmol.CopyAtom() #copy.deepcopy(self.optmol.atm)
        self.model.DrawMol(True)
        mess="The coordinates were updated."
        self.model.Message(mess,0,"")
        self.model.ConsoleMessage(mess)
        
    def OnUndo(self,event):
        self.overlay=False
        self.model.mol.atm=self.savmol #copy.deepcopy(self.savmol)
        self.model.DrawMol(True)
        mess="The coordinate update was cancelled."
        self.model.Message(mess,0,"")
        self.model.ConsoleMessage(mess)
    
    def MakeOptimizedMol(self):
        geofile=self.xyzfile
        if self.var != "Cartesian":
            self.err=self.ExecuteINTXYZ()
            if self.err:
                mess="Error occured in TINKER INTXYZ.\n"
                mess=mess+"Delete all tempollary files in fu scratch directory."
                lib.MessageBoxOK(mess,"")
                return            
        geofile=self.GetMaxFile(geofile)
        if os.path.exists(self.pdbfile): os.remove(self.pdbfile)
        savoutfile=self.outfile
        self.outfile=self.tmpfile

        self.ExecuteXYZPDB(geofile)
        #pdbatoms=rwfile.ReadPDBMol(self.pdbfile)
        pdbatoms,fuoptdic=rwfile.ReadPDBMol(self.pdbfile)
        self.outfile=savoutfile

        # tinatm: [[seq,atmnam,xyz,type,con],...]
        #tinatm=rwfile.ReadTinkerXYZ(geofile)
        #return tinatm
        #tinatm=self.GetOptimizedCC()
        self.optmol=molec.Molecule(self.model)
        self.optmol.SetPDBMol(pdbatoms)
        self.SetSelectTemp(self.optmol.atm,True)
        self.optmol.AddBondUseBL([])
        self.SetSelectTemp(self.optmol.atm,False)
        
        self.btnovl.Enable()

    def SetSelectTemp(self,mol,sel):
        if sel:
            self.savsel=[]
            for atom in mol: self.savsel.append(atom.select)
            atom.select=True
        else:
            for i in range(len(mol)): mol[i].select=self.savsel[i]
        
    def GetMaxFile(self,geofile):
        maxnmb=0; nmb=[0]
        for name in glob.glob(geofile+"_*"):
            if name.split("_")[1].isdigit():
                nmb.append(name.split("_")[1])         
        #print 'nmb',nmb
        maxnmb=max(nmb)
        if maxnmb == 0: return geofile
        else: return geofile+"_"+str(maxnmb)            
    
    def OnExecute(self,event):
        self.btnexe.Disable()
        #
        self.SetActiveAtoms()
        if len(self.active) <= 0:
            lib.MessageBoxOK("No active atoms.","")
            return            
            
        self.maxiter=int(self.tclitr.GetValue())
        self.MakeKeyFile()
        if self.var == "Cartesian":
            if not os.path.exists(self.xyzfile):
                if not os.path.exists(self.pdbfile):
                    #self.model.DeleteAllTers()
                    #self.model.mol.WritePDBMol(self.pdbfile,"","",True)
                    ret=self.ConvertPDBForTinker()
                    if ret: return
                self.ExecutePDBXYZ()
                
        else:
            if not os.path.exists(self.intfile): self.ExecuteXYZINT()

        #self.maxiter=int(self.tclitr.GetValue())
        self.rmsgrd=float(self.tclgrd.GetValue())
        self.pltene=self.rbtene.GetValue()
        self.pltgrd=self.rbtgrd.GetValue()
        #self.pltno=self.rbtnoplt.GetValue()
        self.btnupd.Disable(); self.btnund.Disable()
        self.btnovl.Disable(); self.btnfit.Disable()
        self.btnreset.Disable()
        #
        self.ExecTinkerOptimize()

    def OnReset(self,event):
        self.btnupd.Disable(); self.btnund.Disable()
        self.btnovl.Disable(); self.btnfit.Disable()
        self.DeleteTempIOFiles()
        #
        self.mol=self.model.mol
        
        self.molnam=self.mol.name
        ret=self.ConvertPDBForTinker()
        #
        self.savmol=self.mol.CopyAtom() #copy.deepcopy(self.mol.atm)
        self.overlay=False
        #
        self.optmol=None
        #try: del self.optmol
        #except: pass
        #
        self.multichain=False
        if len(self.model.ListChainName()) > 1: self.multichain=True

    def CompressIntForTinker(self,idata):
        dat=idata[:]
        for i in range(len(dat)): dat[i] += 1
        dattxt=lib.IntegersToString(dat)
        datlst=dattxt.split(",")
        dat=[]
        for s in datlst:
            if s.find("-") >= 0:
                ss=s.split("-"); ss[0]="-"+ss[0]
                dat.append(ss[0]); dat.append(ss[1]) 
            else: dat.append(s)
        return dat
            
    def MakeKeyFile(self):
        act=self.CompressIntForTinker(self.active)
        #
        f=open(self.keyfile,"w")
        f.write("parameters "+self.fffile+"\n")
        f.write("\n")
        f.write("maxiter "+str(self.maxiter)+"\n")
        f.write("\n")
        #
        text="active "; ndat=0
        for i in range(len(act)):
            seq=act[i]
            if len(text) >= 65:
                f.write(text+"\n")
                ndat=0
                text="active "    
            text=text+str(seq)+" "
            ndat += 1
        if ndat > 0: f.write(text+"\n")
        f.write("\n")
        f.close()
        
    def SetActiveAtoms(self):
        self.active=[]
        lst=self.model.ListTargetAtoms()
        if self.var == "Cartesian":
            for i in lst: self.active.append(i)    
            
    def OnAssignFF(self,event):
        if len(self.inputfmt) <= 0:
            lib.MessageBoxOK("Open pdb or xyz file.","")
            return
        if self.ffname == "":
            lib.MessageBoxOK("Specify force filed.","")
            return            
        
        base,ext=os.path.splitext(self.filename) 
        tgtffname=base; tgtfffile=base+'.prm'
        self.tgtff=ForceField(tgtffname,tgtfffile)
        if os.path.exists(tgtfffile): os.remove(tgtfffile)
        #
        if self.inputfmt == 'pdb':
            #base,ext=os.path.splitext(self.pdbfile)
            self.ExecTinkerPDBXYZAndAnalyze(self.pdbfile,self.ffname)
            return
        # read tinker.xyz file
        tinkeratom=rwfile.ReadTinkerXYZ(self.xyzfile)
        if len(tinkeratom) <=0:
            lib.MessageBoxOK("No atoms in xyzfile. Please check the file.","")
            return            

        atomterm=self.MakePotAtomTerm()

        self.tgtff.AddPotTermToDic('atom',atomterm)
        # check atomcls assigned to all atoms
        assignedall=True
        for datnmb,type,cls,atmnam,atomic,mass,vale,com in atomterm:
            if cls == 0:
                assignedall=False; break
        if not assignedall:       
            self.uterms=['atom'] #!!!; self.utermdic=self.tgtff.pottermdic
            self.OpenAssignFFParamPanel()
        else:
            self.ExecTinkerAnalyze(self.xyzfile,self.ffname)
            
            self.anlfile=self.xyzfile.replace('.xyz','.anl')
            if not os.path.exists(self.anlfile):
                mess="Error occured in TINKER ANALYZE.\n"
                mess=mess+"Delete all tempollary files in fu scratch directory."
                lib.MessageBoxOK(mess,"")
    def MakePotAtomTerm(self):
        # tinkeratom: [[seq,atmnam,xyz,type,con],...]
        # potatomterm:[[datnmb,type,cls,atmnam,atomic,mass,vale,com],...]
        atomterm=[]; pdbelm=[]
        # get elements
        print 'pdbatoms in makepotatomterm',self.pdbatoms
        npdb=self.pdbatoms[0]
        for i in range(npdb):
            elm=self.pdbatoms[8][i]
            if elm == 'XX': continue
            pdbelm.append(elm)
        for i in range(len(self.tinkeratoms)): #seq,atmnam,xyz,type,con in self.tinkeratom:
            seq=self.tinkeratoms[i][0]; atmnam=self.tinkeratoms[i][1]
            elm=pdbelm[i]; atomic=const.ElmNmb[elm]
            mass=const.ElmMas[elm]; vale=len(self.tinkeratoms[i][4])
            type=self.tinkeratoms[i][3]
            if type == 0: ctype=""
            else: ctype=str(type) 
            atomterm.append([seq,type,type,atmnam,atomic,mass,vale,""])
        return atomterm
    
    def OpenAssignFFParamPanel(self):
        if len(self.tgtff.pottermdic['atom']) <= 0:
            lib.MessageBoxOK("No molecular data.","")
            return
        if len(self.ffname) <= 0:
            lib.MessageBoxOK("No force field is specified.","")
            return
        winsize=lib.WinSize([800,520]); winpos=[-1,-1]
        ffparamwin=AssignFFParam_Frm(self,-1,winpos,winsize)
        ffparamwin.Show()
      
    def ExecTinkerPDBXYZAndAnalyze(self,pdbfile,ffname):
        prg=[]; arg=[]; plt=[{}]
        base,ext=os.path.splitext(pdbfile)
        xyzfile=base+'.xyz'
        seqfile=base+'.seq'
        
        if os.path.exists(xyzfile): os.remove(xyzfile)
        if os.path.exists(seqfile): os.remove(seqfile)
        self.xyzfile=xyzfile
        # execute Tinker PDBXYZ to create xyzfile)
        prgtxt=GetTinkerProgram(self.tinkerprgdir,"pdbxyz")
        ffparamfile=self.fffiledic[ffname]
        prg.append(prgtxt)
        chain=""
        if self.multichain: chain=" ALL"
        arg.append(pdbfile+chain+" "+ffparamfile)
        # Tinker Analyze to create anlfile
        self.anlfile=base+'.anl'
        wrkdir=""
        prgnam=GetTinkerProgram(self.tinkerprgdir,"analyze")
        argtxt=self.xyzfile+" "+ ffparamfile+" P A"
        plt.append({})
        prg.append(prgnam)
        arg.append(argtxt)        
        #
        if not self.openexeprgwin: self.OpenExePrgWin()
        jobid="pdbxyz-analyze"
        self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,self.anlfile)
        
    def OpenExePrgWin(self):
        winpos=[0,0]; winsiz=[750,300]
        title='Run TINKER Optimize'; winlabel='tinker-optimize'
        self.exeprgwin=subwin.ExecProg_Frm(self,-1,self.model,winpos,winsiz,
                                           title,winlabel,onclose=self.CloseExePrgWin)
        self.exeprgwin.Show()
        self.openexeprgwin=True

    def CloseExePrgWin(self):
        self.openexeprgwin=False
        try: self.exeprgwin.Destroy()
        except: pass

    def OnThreadJobEnded(self,event):
        self.btnexe.Enable()
        #
        jobnam=event.jobid
        jobcmd=event.message
        killed=event.killed
        #
        try: self.exeprgwin.f.close()
        except: pass
        #self.exeprgwin.SetStatusText('',0)

        if jobnam == "pdbxyz-analyze":
            self.GetParameters(jobnam); return
        if jobnam == "analyze":
            print 'analyze was over'
            self.GetParameters(jobnam); return
        if jobnam == 'pdbxyz':
            pass
            #print 'pdbxyz was over.'
        if jobnam == 'optimize':
            mess="Tinker optimization on "+self.molnam+" ended at "+lib.DateTimeText()
            #self.model.ConsoleMessage(mess)
            self.model.ConsoleMessage(mess)
            #print 'optimze was over'
            self.optmol=None
            self.err=True
            
            if self.var == "Cartesian":
                #self.xyz2file=self.xyzfile+"_2"
                if os.path.exists(self.xyz2file): self.err=False
            else:
                #self.int2file=self.intfile+"_2"
                if os.path.exists(self.int2file): self.err=False
            #
            self.GetAndPrintResults()
            if not self.err:
                #self.btnupd.Enable(); self.btnund.Enable()
                self.MakeOptimizedMol()
                self.btnovl.Enable(); self.btnfit.Enable()
            #
            self.btnreset.Enable()
            
    
    def GetAndPrintResults(self):
        endmess=""; iterd=[]
        self.mechanicerr=False
        it="Iter   "
        fv="Final Function Value"
        fr="Final RMS Gradient"
        fn="Final Gradient Norm"
        et="elapsed time="
        m1="Incomplete Convergence"
        m2="Normal Termination"
        mk="MECHANIC  --" 
        #
        endmess=""; finval=-1; finrms=-1; finnrm=-1; etime=-1; niter=-1
        m1m=""; m2m=""; mkm=""
        #
        f=open(self.outfile)
        find=False; enditr=False
        i=0; nblk=0
        for s in f.readlines():
            i += 1
            s=s.replace('\r',''); s=s.replace('\n','')
            if s.find(mk) >= 0:
                mkm=s; break # there are unassigned potential parameters
            if find and s == "":
                nblk += 1
                if nblk == 2: enditr=True
                continue
            if find and not enditr:
                niter=int(s.split()[0]); continue
            ns=s.find(it)
            if not find and ns >= 0:
                find=True; continue
            if s == "": continue
            if not find or not enditr: continue
            if s.find(fv) >= 0: finval=float(s.split()[4])
            if s.find(fr) >= 0: finrms=float(s.split()[4])
            if s.find(fn) >= 0: finnrm=float(s.split()[4])
            if s.find(et) >= 0: etime=float(s.split()[3])
            if s.find(m1) >= 0: m1m=s
            if s.find(m2) >= 0: m2m=s
        f.close()
        #
        if len(mkm) > 0:
            endmess=mkm.strip()
            self.mechanicerr=True
            mess="\n"+"Tinker optimization is unable."+"\n"
            mess=mess+mkm+"\n"
            self.model.ConsoleMessage(mess)
            #
            lib.MessageBoxOK(mess,"")
            #mess=mess+"Do you want to assign forcefield parameters?"
            #yesno=wx.MessageBox(mess,"",style=wx.YES_NO|wx.ICON_QUESTION)
            #if yesno == wx.YES:
            #    self.exeprgwin.Close(1)
                
            #    self.tinkeratoms=rwfile.ReadTinkerXYZ(self.xyzfile)            
            #    self.pdbatoms=rwfile.ReadPDBMol(self.pdbfile)
                        
            #    self.ExecTinkerAnalyze(self.xyzfile,self.ffname)
                
            #    print 'pdbatoms',self.pdbatoms
                
            #    self.OpenAssignFFParamPanel()
            #else: return
            return

        if len(m1m) > 0: endmess=m1m.strip()
        elif len(m2m) > 0: endmess=m2m.strip()
        else: endmess="Unknown error occured."
        actall=False
        lst=self.active
        nact=len(self.active); natm=len(self.mol.atm)
        if nact == natm: actall=True
        else: 
            atm=self.CompressIntForTinker(lst)
            atmtxt=""
            for i in atm: atmtxt=atmtxt+str(i)+","
            atmtxt=atmtxt[:len(atmtxt)-1]
        mess="\n"+"Tinker optimization summary"+"\n"
        mess=mess+"molecule: "+self.molnam+"\n"
        mess=mess+"forcefield: "+self.ffname+"\n"
        mess=mess+"variable: "+self.var+"\n"
        if actall: mess=mess+"active atoms: all"+"\n"
        else: mess=mess+"active atoms: "+atmtxt+"\n"
        mess=mess+"program: "+self.prgnam+" (option: "+self.method+")"+"\n"
        mess=mess+"maxiter: "+str(self.maxiter)+"\n"
        mess=mess+"rms gradient threshold: "+str(self.rmsgrd)+"\n"
        mess=mess+"termination: "+endmess+"\n"
        mess=mess+"iteration number: "+str(niter)+"\n"
        mess=mess+"elpsed time: "+str(etime)+" (sec)"+"\n"
        mess=mess+"final function value: "+str(finval)+"\n"
        mess=mess+"final rms gradient: "+str(finrms)+"\n"
        mess=mess+"final gradient norm: "+str(finnrm)
        self.model.ConsoleMessage(mess)

    def GetParameters(self,jobnam):
        #if execpdbxyz:
        if not os.path.exists(self.xyzfile):
            mess="PDBXYZ failed to create xyz file. Please check the input pdb file."
            lib.MessageBoxOK(mess,"")
            return
        # read tinker xyz file, tinatm[[seq,atmnam,[x,y,z],type,con],...] 
        self.tinkeratoms=rwfile.ReadTinkerXYZ(self.xyzfile)
        #print 'tinkeratom in getparam',self.tinkeratoms
        if len(self.tinkeratoms) <= 0: self.MakeTinkerAtoms()
        
        if not self.IsAllAtmTypAssigned():
            # Open AtmTypAssignPanel
            mess="There are unassigned-atmtyp atoms. Do you want to assign atmtyp?"
            ans=lib.MessageBoxYesNo(mess,"")
            if not ans: return
            #!!for atom in self.mol.mol:
            #!!    atom.ffatmtyp=self.tinkeratoms[atom.seqnmb][3]
            atom=self.MakePotAtomTerm()
            #print 'atom',atom
            self.tgtff.AddPotTermToDic("atom",atom)
            
            self.OpenAssignFFParamPanel()
            return
        
        
        print 'anlfile',self.anlfile
        
        if not os.path.exists(self.anlfile):
            ans=lib.MessageBoxOK("Errors occured in Analyze. Please check xyz input file.","")
            if ans == wx.NO: return

        self.uterms=self.FindUnassignedTerm(self.anlfile)
        
        # there are unassigned paramters
        if len(self.uterms) > 0:
            mess="There are unassigned potential terms. Do you want to define them?"
            ans=lib.MessageBoxOK(mess,"")
            if ans == wx.NO: return
            elif ans == wx.YES:
                if self.openexeprgwin: self.CloseExePrgWin()

                self.utermdic=self.ReadUnassignedTermInfo(self.anlfile)
                #!!!
                self.tgtff.pottermdic.update(self.utermdic)
                self.OpenAssignFFParamPanel(); return
        # all parmaters are succssesifully assigned
        else:
            potdic=self.ReadTinkerAnalyzeFile(self.anlfile)
            print 'self.fffile',self.fffile
            self.potoptiondic=self.ReadFFPotOptions(self.fffile)
            print 'tgt pot options',self.potoptiondic
            self.prmfile=self.xyzfile.replace('.xyz','.prm')
            self.WriteTinkerPrmFile(self.prmfile,potdic,False)
            mess="Parameter file:"+self.prmfile+" is successfully created. Do you want to view the file?"
            ans=lib.MessageBoxYesNo(mess,"")
            if ans:
                os.spawnv(os.P_NOWAIT,"C:/Windows/System32/notepad.exe",
                                      ["notepad.exe"+' '+self.prmfile])          
            # destroy exeprgwin
            self.CloseExePrgWin()
    
    def MakeTinkerAtoms(self):
        self.tinkeratoms=[]
        npdb=len(self.pdbatoms[0])
        for i in range(npdb):
            elm=self.pdbatoms[8][i]
            if elm == 'XX': continue
            seq=i+1; atmnam=self.pdbatoms[2][i]; xyz=self.pdbatoms[0][i]
            type=0; con=self.pdbatoms[1][i]; del con[0]
            self.tinkeratoms.append([seq,atmnam,xyz,type,con])     

    def IsAllAtmTypAssigned(self):
        #tinkeratom[[seq,atmnam,[x,y,z],type,conect],...] 
        for seq,atmnam,xyz,type,con in self.tinkeratoms:
            #print 'seq,type',seq,type
            if type == 0: return False
        return True
    
    def ReadFFPotOptions(self,fffile):
        potopt = [
              ["vdwindex",11],["radiustype",10],["vdwtype",7],["radiusrule",10],
              ["radiustype",10],["radiussize",10],["epsilonrule",11],["vdw-14-scale",12],
              ["chg-14-scale",12],["electric",8],["dielectric",10],["torsionunit",11],
              ["imptorunit",10],["bondunit",8],["bond-cubic",10],["bond-quartic",12], #  MM2       !! TINKER
              ["angleunit",9],["angle-sextic",12],["strbndunit",10],["opbendtype",10], # mm2
              ["opbendunit",10],["opbend-sextic",13],["torsionunit",11],["a-expterm",9],
              ["b-expterm",9],["c-expterm",9],["strbndunit",10],["opbend-cubic",12],
              ["opbend-quartic",14],["opbend-pentic",13],["opbend-sextic",13],
              ["strtorunit",10],["angle-cubic",11],["angle-quartic",13],
              ["angle-pentic",12],["angle-sextic",12] ]

        optdic={}
        f=open(fffile,"r")
        for s in f.readlines():
            ss=s.strip()
            for kw,nw in potopt:
                if ss.startswith(kw,0,nw):
                    item=ss.split()
                    if optdic.has_key(kw): continue #optdic[kw].append(item[1])
                    else: optdic[kw]=item[1]
        f.close()
        #print 'optdic',optdic
        #return optdic
        return optdic
                

    def WriteTinkerPrmFile(self,prmfile,potdic,ap):
        # ap: True for append, False for write
        termlst=potdic.keys()
        print 'termlst',termlst
        for termnam in termlst:
            print 'term',potdic[termnam]
        if ap: f=open(prmfile,"a")
        else: f=open(prmfile,"w")

        f.write("parameters       NONE\n")
        f.write("\n")
        # atmtpe
        """Atom  Symbol  Type  Class  Atomic   Mass  Valence  Description"""
        """1     N3     386     20     7    14.010    4     N-Term THR N"""
        # write options
        if potdic.has_key('atomorg'): atom=potdic['atomorg']
        for key in self.potoptiondic:
            text=key+'  '+self.potoptiondic[key]+'\n'
            f.write(text)
        f.write('\n')
        # write potential paramteres
        for termnam in termlst:
            if termnam == "atomprg": continue
            term=potdic[termnam]
            if len(term) <= 0: continue
            if termnam == 'atom':
                for seq,atmnam,type,cls,atomic,mass,vale,com in term:
                    #type=term[i][3]; atmnam=term[i][1]; com='"'+term[i][7]+'"'
                    #elm=term[i][4]; mass=term[i][5]; vale=term[i][6]
                    text="atom"
                    text=text+"  "+type+"  "+cls+"  "+atmnam+"  "+'"'+com+'"  '+atomic+"  "+ \
                         mass+"  "+vale
                    f.write(text+"\n")
                f.write("\n")
            if termnam == 'vdw':
                for atmseq,cls,size,epsi,cm in term:
                    text="vdw"
                    #cls=atom[int(atmseq)-1][3]
                    text=text+"  "+cls+"  "+size+"  "+epsi
                    if cm != '': text=text+"  !!"+cm
                    f.write(text+"\n")
                f.write("\n")
            if termnam == 'bond':
                #print 'bond term',term
                for datnmb,cls1,cls2,bondk,bondr,cm in term:
                    text="bond"
                    #cls1=atom[int(atm1)-1][3]; cls2=atom[int(atm2)-1][3]
                    text=text+"  "+cls1+"  "+cls2+"  "+bondk+"   "+bondr
                    if cm != '': text=text+"  !!"+cm
                    f.write(text+"\n")
                f.write("\n")
            if termnam == "angle":
                for datnmb,cls1,cls2,cls3,anglek,anglea,cm in term:
                    text="angle"
                    #cls1=atom[int(atm1)-1][3]; cls2=atom[int(atm2)-1][3]
                    #cls3=atom[int(atm3)-1][3]
                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+anglek+"   "+anglea
                    if cm != '': text=text+"  !!"+cm
                    f.write(text+"\n")
                f.write("\n")
            if termnam == 'torsion':
                """# datnmb,atm1,atm2,atm3,atm4,torsk1,torsa1,torsp1,torsk2,torsa2,torsp2, \
                #         torsk3,torsa3,torsp3 in term: """
                nlen=len(term)
                for i in range(len(term)):
                    nlen=len(term[i])-1
                    cls1=term[i][1]; cls2=term[i][2]; cls3=term[i][3]; cls4=term[i][4]                
                    text="torsion"
                    #cls1=atom[int(atm1)-1][3]; cls2=atom[int(atm2)-1][3]
                    #cls3=atom[int(atm3)-1][3]; cls4=atom[int(atm4)-1][3]    
                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+cls4
                    if nlen >= 6:
                        torsk1=term[i][5]; torsa1=term[i][6]; torsp1=term[i][7]
                        text=text+"  "+torsk1+"   "+torsa1+"  "+torsp1 
                    if nlen >= 9:
                        torsk2=term[i][8]; torsa2=term[i][9]; torsp2=term[i][10]
                        text=text+"  "+torsk2+"   "+torsa2+"  "+torsp2 
                    if nlen >=12:
                        torsk3=term[i][11]; torsa3=term[i][12]; torsp3=term[i][13]
                        text=text+"  "+torsk3+"   "+torsa3+"  "+torsp3 
                    if term[i][nlen-1] != "": text=text+"  !!"+term[i][nlen-1]
                    
                    f.write(text+"\n")                        
                f.write("\n")
            
            if termnam == "imptors": # amber style improper
                for datnmb,cls1,cls2,cls3,cls4,torsk1,torsa1,torsp1,cm in term:
                    text="imptors"
                    #cls1=atom[int(atm1)-1][3]; cls2=atom[int(atm2)-1][3]
                    #cls3=atom[int(atm3)-1][3]; cls4=atom[int(atm4)-1][3]    

                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+cls4+ \
                         "  "+torsk1+"  "+torsa1+"  "+torsp1
                    if cm != "": text=text+"   !!"+cm
                    f.write(text+"\n")
                f.write("\n")
            if termnam == "charge":
                for datnmb,cls1,chg, cm in term:
                    text="charge"
                    #cls1=atom[int(atm1)-1][3]
                    text=text+"  "+cls1+"  "+chg
                    if cm != "": text=text+"  !!"+cm
                    f.write(text+"\n") 
                f.write("\n")
        f.close()
        

    
    def ReadTinkerAnalyzeFile(self,anlfile):
        # read output file of Tinker ANALYZE program
        # return pottermdic: {'termname':paramlst,...}, termname='atom','bond',...
        potdic={}
        # AMBER FF case
        keywdlst=['Atom Type Definition Parameters :',
                  'Van der Waals Parameters :',
                  'Bond Stretching Parameters :',
                  'Angle Bending Parameters :',
                  'Improper Torsion Parameters :',
                  'Torsional Angle Parameters :',
                  'Atomic Partial Charge Parameters :']
        #termlst=[]
        atom=False; atomterm=[]
        vdw=False; vdwterm=[]
        bond=False; bondterm=[]
        angle=False; angleterm=[]
        imptors=False; imptorsterm=[]
        torsion=False; torsionterm=[]
        charge=False; chargeterm=[]
        #
        f=open(anlfile,"r")
        for s in f.readlines():
            s=s.replace("\n",""); s=s.replace("\r","")
            if s.startswith(keywdlst[0],1,34): # atom type
                atom=True; nl=0; continue
            if s.startswith(keywdlst[1],1,27): # vdw
                vdw=True; nl=0; continue
            if s.startswith(keywdlst[2],1,29): # bond
                bond=True; nl=0; continue
            if s.startswith(keywdlst[3],1,27): # angle
                angle=True; nl=0; continue
            if s.startswith(keywdlst[4],1,30): # imptors
                imptors=True; nl=0; continue
            if s.startswith(keywdlst[5],1,29): # torsion
                torsion=True; nl=0; continue
            if s.startswith(keywdlst[6],1,35): # charge
                charge=True; nl=0; continue

            if atom:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        atom=False; continue
                    else:
                        self.ReadAnlAtoms(s,atomterm); continue
            if vdw:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        vdw=False; continue
                    else:
                        self.ReadAnlParams(s,vdwterm); continue
            if bond:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        bond=False; continue
                    else:
                        self.ReadAnlParams(s,bondterm); continue
            if angle:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        angle=False; continue
                    else:
                        self.ReadAnlParams(s,angleterm); continue
            if imptors:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        imptors=False; continue
                    else:
                        self.ReadAnlParams(s,imptorsterm); continue
            if torsion:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        torsion=False; continue
                    else:
                        self.ReadAnlTorsions(s,torsionterm); continue
            if charge:
                nl += 1
                if nl < 4: continue
                else:
                    if s == "":
                        charge=False; continue
                    else:
                        self.ReadAnlParams(s,chargeterm); continue
        f.close()

        if len(vdwterm) > 0:
            potdic['vdw']=self.ExtractUniqueVdwPrm(vdwterm,atomterm)
        if len(bondterm) > 0:
            potdic['bond']=self.ExtractUniqueBondPrm(bondterm,atomterm)
        if len(angleterm) > 0:
            potdic['angle']=self.ExtractUniqueAnglePrm(angleterm,atomterm)
        if len(imptorsterm) > 0:
            potdic['imptors']=self.ExtractUniqueImptorsPrm(imptorsterm,atomterm)
        if len(torsionterm) > 0:
            potdic['torsion']=self.ExtractUniqueTorsionPrm(torsionterm,atomterm)
        if len(chargeterm) > 0:
            potdic['charge']=self.ExtractUniqueChargePrm(chargeterm,atomterm)
        # atom type should be treated last!
        if len(atomterm) > 0:
            potdic['atomorg']=atomterm
            potdic['atom']=self.ExtractUniqueAtomPrm(atomterm)
        #
        #self.pottermdic=potdic
        return potdic
            
    
    def ReadAnlAtoms(self,s,atom):
        #Atom  Symbol  Type  Class  Atomic   Mass  Valence  Description
        # "1     N3     386     20     7    14.010    4     N-Term THR N"
        s1=s[:50]
        s2=s[54:].replace('\n','')
        item=s1.split()
        atom.append(item+[s2])

        
    def ReadAnlParams(self,s,param):
        """ vdw"""
        # Atom Number       Size   Epsilon   Size 1-4   Eps 1-4   Reduction
        # 1        1           1.8750    0.1700
        """ bond """
        # Atom Numbers                         KS       Bond
        #1        1     2                      367.000    1.4710
        """ angle """
        #Atom Numbers                      KB      Angle   Fold    Type
        #1        2     1     5                 50.000   109.500
        """ imptors """
        # Atom Numbers           Amplitude, Phase and Periodicity^
        # 1        2    17     3     4              10.500   180.0   2
        """ charge """
        # Atom Number             Charge
        #1        1                   0.1812

        s=s.replace('\n','')
        item=s.split()
        param.append(item)
    
    def ReadAnlTorsions(self,s,torsion):
        """ torsion """
        #Atom Numbers           Amplitude, Phase and Periodicity        
        #12        8     2     3     4       0.800   0/1   0.080 180/3
        s=s.replace('\n','')
        item=[]
        tmp=s.split()
        for i in range(len(tmp)):
            ns=tmp[i].find('/')
            if ns >= 0:
                tt=tmp[i].split('/')
                item.append(tt[0]); item.append(tt[1])
            else: item.append(tmp[i])
        torsion.append(item)

    def CheckAtmclsAssigned(self,filename):
        #tinkeratom[[seq,atmnam,[x,y,z],type,conect],...] 
        mess1="Undefined Atom Types or Classes"
        mess2="Atoms with an Unusual Number of Attached Atoms"
        mess3="MECHANIC  --  Some Required Potential Energy Parameters are Undefined"
        f=open(filename,"r")
        for s in f.readlines():
            if s.find(mess1) >= 0: 
                return mess1
            if s.find(mess2) >= 0: 
                return mess2
            if s.find(mess3) >= 0: 
                return mess3
        return "ok"
            
    def FindUnassignedTerm(self,filename):
        uterms=[]
        keywd=[
               #!! ["Undefined Atom Types or Classes","atom"],
               ["Undefined Bond Stretching","bond"],
               ["Undefined Angle Bending","angle"],
               ["Undefined Torsional","torsion" ]]
        f=open(filename)
        for s in f.readlines():
            for kw,tm in keywd:
                if s.strip().find(kw) >= 0:
                    uterms.append(tm)
        return uterms
            
    def ReadUnassignedTermInfo(self,anlfile):    
        unasgnpottermdic={}
        unasgnbond=[]; unasgnangle=[]; unasgntorsion=[]     
        self.nbnd=0; self.nang=0; self.ntor=0
        f=open(anlfile,"r")
        for s in f.readlines():
            if s.strip().startswith('Bond',0,4):
                unasgnbond.append(self.GetBondInfo(s))
            if s.strip().startswith('Angle',0,5):
                unasgnangle.append(self.GetAngleInfo(s))
            if s.strip().startswith('Torsion',0,7):
                unasgntorsion.append(self.GetTorsionInfo(s))
        
        if len(unasgnbond) > 0: unasgnpottermdic['bond']=unasgnbond
        if len(unasgnangle) > 0: unasgnpottermdic['angle']=unasgnangle
        if len(unasgntorsion) > 0: unasgnpottermdic['torsion']=unasgntorsion
        return unasgnpottermdic
    
    def GetAtomInfo(self,line,nmb):
        pass    
    def GetBondInfo(self,line):
        # seqnmb1,atmnam1,seqnmb2,atmnmb2, atmcls1,atmcls2
        self.nbnd += 1
        item=line.split()
        seqnam=item[1].split('-')
        seqnmb1=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam1=seqnam[1]
        seqnam=item[2].split('-')
        seqnmb2=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam2=seqnam[1]
        atmcls1=item[3] #int(item[3])
        atmcls2=item[4] #int(item[4])

        bondk="" #str(0.0)
        bondr="" #str(0.0)
        #return [seqnmb1,atmnam1,seqnmb2,atmnam2,atmcls1,atmcls2,
        #        bondk,bondr]
        return [str(self.nbnd),seqnmb1,atmnam1,seqnmb2,atmnam2,atmcls1,atmcls2,
                bondk,bondr,""]
        
    def GetAngleInfo(self,line):
        # seqnmb1,atmnam1,seqnmb2,atmnmb2,seqnmb3,atmnam3,atmcls1,atmcls2,atmcls3
        self.nang += 1
        item=line.split()
        seqnam=item[1].split('-')
        seqnmb1=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam1=seqnam[1]
        seqnam=item[2].split('-')
        seqnmb2=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam2=seqnam[1]
        seqnam=item[3].split('-')
        seqnmb3=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam3=seqnam[1]
        atmcls1=item[4] #int(item[4])
        atmcls2=item[5] #int(item[5])
        atmcls3=item[6] #int(item[6])
        anglek="" #str(0.0)
        anglea="" #str(0.0)
        return [str(self.nang),seqnmb1,atmnam1,seqnmb2,atmnam2,seqnmb3,atmnam3,atmcls1,
                atmcls2,atmcls3,anglek,anglea,""]
        
    def GetTorsionInfo(self,line):
        # seqnmb1,atmnam1,seqnmb2,atmnmb2,seqnmb3,atmnam3,atmcls1,atmcls2,atmcls3
        self.ntor += 1
        item=line.split()
        seqnam=item[1].split('-')
        seqnmb1=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam1=seqnam[1]
        seqnam=item[2].split('-')
        seqnmb2=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam2=seqnam[1]
        seqnam=item[3].split('-')
        seqnmb3=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam3=seqnam[1]
        seqnam=item[4].split('-')
        seqnmb4=seqnam[0] #int(seqnam[0])-1 # internal numbering
        atmnam4=seqnam[1]
        atmcls1=item[5] #int(item[5])
        atmcls2=item[6] #int(item[6])
        atmcls3=item[7] #int(item[7])
        atmcls4=item[8] #int(item[8])
        torsa1="" #str(0.0)
        torsp1="" #"0/0"
        torsa2="" #str(0.0)
        torsp2="" #"0/0"
        torsa3="" #str(0.0)
        torsp3="" #"0/0"
        
        return [str(self.ntor),seqnmb1,atmnam1,seqnmb2,atmnam2,seqnmb3,atmnam3,
                seqnmb4,atmnam4,atmcls1,atmcls2,atmcls3,atmcls4,
                torsa1,torsp1,torsa2,torsp2,torsa3,torsp3,""]
        
    def ExecTinkerPDBXYZ(self,pdbfile,ffname):
        #if len(self.mol.mol) <= 0:
        #    wx.MessageBox("Number of atoms is zero.","",style=wx.OK|wx.ICON_EXCLAMATION)
        #    return

        if not os.path.exists(pdbfile):
            lib.MessageBoxOK("Not found pdb file. Please open pdb file.","")
            return
        plt=[]; prg=[]; arg=[]   
        wrkdir=""
        prgnam=GetTinkerProgram(self.tinkerprgdir,"pdbxyz") #"e:/winfort/tinker/bin-win64/pdbxyze"
        ffparamfile=self.fffiledic[ffname]
        chain=""
        if self.multichain: chain=" ALL"
        argtxt=self.pdbfile+chain+" "+ ffparamfile #"e:/winfort/tinker/params/"+ffname+".prm"
        plt.append({})
        prg.append(prgnam)
        arg.append(argtxt)
        outfile="" #pdbfile.replace('.xyz','.tmp') #self.pdbfile.replace('.pdb','.tmp')
        if not self.openexeprgwin: self.OpenExePrgWin()
            # open output window
            #winpos=[0,0]; winsiz=[750,300]
            #self.exeprgwin=subwin.ExecProg_Frm(self,-1,winpos,winsiz)
            #self.exeprgwin.Show()
            #self.openexeprgwin=True
        #
        jobid="pdbxyz"
        self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,outfile)


    def ExecTinkerAnalyze(self,xyzfile,ffname):
        #if len(self.mol.mol) <= 0:
        #    wx.MessageBox("Number of atoms is zero.","",style=wx.OK|wx.ICON_EXCLAMATION)
        #    return

        if not os.path.exists(xyzfile):
            mess="Not found xyz file. Please assingn atmtyp before calling this routine."
            lib.MessageBoxOK(mess,"")
            return
        plt=[]; prg=[]; arg=[] 
        wrkdir=""
        prgnam=GetTinkerProgram(self.tinkerprgdir,"analyze") #"e:/winfort/tinker/bin-win64/analyze"
        ffparamfile=self.fffiledic[ffname]
        argtxt=self.xyzfile+" "+ffparamfile+" P A"
        plt.append({})
        prg.append(prgnam)
        arg.append(argtxt)
        #self.anlfile=xyzfile.replace('.xyz','.anl')
        if not self.openexeprgwin: self.OpenExePrgWin()
            # open output window
            #winpos=[0,0]; winsiz=[750,300]
            #self.exeprgwin=subwin.ExecProg_Frm(self,-1,winpos,winsiz)
            #self.exeprgwin.Show()
            #self.openexeprgwin=True
        #
        jobid="analyze"
        self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,self.anlfile)

    def ExecTinkerOptimize(self):
        #if len(self.mol.mol) <= 0:
        #    wx.MessageBox("Number of atoms is zero.","",style=wx.OK|wx.ICON_EXCLAMATION)
        #    return
        prgnam=GetTinkerProgram(self.tinkerprgdir,self.prgnam)
        if not os.path.exists(prgnam):
            lib.MessageBoxOK("Not found program. program="+prgnam,"")
            return        
        if self.var == "Cartesian": inpfile=self.xyzfile
        else: inpfile=self.intfile   
        if not os.path.exists(inpfile):
            lib.MessageBoxOK("Not found input file. file="+inpfile,"")
            return
        plt=[]; prg=[]; arg=[] 
        wrkdir=""
        #prgnam=prgnam=GetTinkerProgram(self.tinkerprgdir,"analyze") #"e:/winfort/tinker/bin-win64/analyze"
        ffparamfile=self.fffiledic[self.ffname]
        if self.var == "Cartesian":
            if self.prgnam == "newton":
                argtxt=inpfile+" "+self.method+" A "+str(self.rmsgrd)
            else:
                argtxt=inpfile+" "+str(self.rmsgrd)
        else:
            if self.prgnam == "newtrot":
                argtxt=inpfile+" 0 "+self.method+" A "+str(self.rmsgrd)
            else:
                argtxt=inpfile+" 0 "+str(self.rmsgrd)
        # plot option
        pltdic={}; title='Optimization ['+self.molnam+']'
        if self.pltene:
            pltdic={'fromkw':"Iter",'tokw':"???",'xitemno':0, 'yitemno':1,
                    'title':title,'xlabel':'step','ylabel':'energy in kcal/mol'} 
        if self.pltgrd:
            pltdic={'fromkw':"Iter",'tokw':"???",'xitemno':0, 'yitemno':2,
                    'title':title,'xlabel':'step','ylabel':'grad in kcal/A/mol'}
        plt.append(pltdic) 
        prg.append(prgnam)
        arg.append(argtxt)
        #arg.append(inpfile+" A A 0.1")
        #self.anlfile=xyzfile.replace('.xyz','.anl')
        if not self.openexeprgwin: self.OpenExePrgWin()
            # open output window
            #winpos=[0,0]; winsiz=[750,300]
            #self.exeprgwin=subwin.ExecProg_Frm(self,-1,winpos,winsiz)
            #self.exeprgwin.Show()
            #self.openexeprgwin=True
        # run one job at a time (can not use jobqeue)
        mess="Tinker optimization on "+self.molnam+" started at "+lib.DateTimeText()
        self.model.ConsoleMessage(mess)
        self.model.Message(mess,0,'')
        jobid="optimize"
        self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,self.outfile)

    def OpenEditor(self,filename):
        if len(filename) <= 0 or not os.path.exists(filename):
            mess=filename+' is not exist.'
            self.model.Message2(mess) #,0,"Tinker Optimize(OpenEditor)")
        # open editor
        else:
            lib.Editor(filename)
    
    def SaveAllFiles(self):   
        basename=""; savelst=[]
        files=[self.pdbfile,self.xyzfile,self.intfile,self.keyfile,self.outfile]
        for savefile in files:
            if not os.path.exists(savefile): continue
            base,ext=os.path.splitext(savefile)
            if basename == "":
                
                filename=""; wildcard=savefile+'|*'+ext
                dlg = wx.FileDialog(self, "Save as...", os.getcwd(),
                                    style=wx.SAVE, wildcard=wildcard)
                if dlg.ShowModal() == wx.ID_OK:
                    filename=dlg.GetPath()            
                dlg.Destroy()        
                if len(filename) < 0: return
                if basename == "": basename,ext0=os.path.splitext(filename)
            else: filename=basename+ext
            #
            savelst.append([filename])
            shutil.copyfile(savefile,filename)
        fum.ConsoleListList("saved files:",savelst)
    
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
        shutil.copyfile(savefile,filename)

    def DeleteScratchFiles(self):
        try:
            for name in glob.glob(self.scrdir+"\\*.*"): os.remove(name)
        except: lib.MessageBoxOK("Failed to delete "+name,"")
    
    def HelpMessage(self):
        mess='Tinker molecular modeling package: http://dasher.wustl.edu/tinker/'    
        lib.MessageBoxOK(mess,'Tinker Optimization')

    def MenuItems(self):
        # Menu items
        menubar=wx.MenuBar()
        # File menu   
        submenu=wx.Menu()
        submenu.Append(-1,"Open","Open tinker xyz file")
        submenu.AppendSeparator()
        # Save temp files as
        subsubmenu=wx.Menu()
        subsubmenu.Append(-1,"all files","Save all temporaly files")
        subsubmenu.Append(-1,"pdb file","Save temporaly pdb file")
        subsubmenu.Append(-1,"xyz file","Save temporaly xyz file")
        subsubmenu.Append(-1,"int file","Save temporaly int file")
        subsubmenu.Append(-1,"key file","Save temporaly key file")
        subsubmenu.Append(-1,"out file","Save temporaly out file")
        submenu.AppendMenu(-1,"Save temp files as",subsubmenu)
        submenu.AppendSeparator()
        # Delete temp file
        subsubmenu=wx.Menu()
        subsubmenu.Append(-1,"del all files","Delete all temporaly files")
        subsubmenu.Append(-1,"del out file","Delete temporaly out files")
        subsubmenu.Append(-1,"del pdb file","Delete temporaly pdb files")
        subsubmenu.Append(-1,"del xyz file","Delete temporaly xyz files")
        subsubmenu.Append(-1,"del int file","Delete temporaly int files")
        subsubmenu.Append(-1,"del key file","Delete temporaly key files")
        submenu.AppendMenu(-1,"Delete temp file",subsubmenu)
        submenu.AppendSeparator()
        #
        submenu.Append(-1,"Delete all files in scratch directory","")
        submenu.AppendSeparator()
        submenu.Append(-1,"Close", "Close tinker optimize panel")
        menubar.Append(submenu,"File")
        # Edit
        submenu=wx.Menu()
        submenu.Append(-1,"parameter file","view/edit parameter file")
        submenu.AppendSeparator()
        submenu.Append(-1,"temp pdb file","view/edit temp pdb file")
        submenu.Append(-1,"temp xyz file","view/edit temp xyz fiel")
        submenu.Append(-1,"temp int file","view/edit temp int file")
        submenu.Append(-1,"temp key file","view/edit temp key file")
        submenu.Append(-1,"temp out file","view temp output file")
        menubar.Append(submenu,"Edit/View")
        # Help
        submenu=wx.Menu()
        submenu.Append(-1,'Document','Help document')
        submenu.AppendSeparator()
        submenu.Append(-1,"Setting","Set TINKER program/parameter directory")
        menubar.Append(submenu,'Help')

        return menubar      

    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        menuitem=self.menubar.FindItemById(menuid)
        item=menuitem.GetItemLabel()
        
        if item == "Open":
            wildcard='tinker xyz(*.xyz,*.tin)|*.xyz;*.tin|All(*.*)|*.*'
            filename=lib.GetFileName(self,wildcard,"r",True,"")
            if len(filename) > 0: 
                root,ext=os.path.splitext(filename)
                self.tinmol=rwfile.ReadTinkerXYZ(filename)
        
        if item == "Save": #xxx.ffp (force field parameter
            self.mol.WriteTinkerXYZ(self.filename)
            
        if item == "Save as":
            wildcard='xyz(*.xyz),tin(*.tin)|*.tin;*.xyz|All(*.*)|*.*'
            self.savefile=lib.GetFileName(self,wildcard,"w",True,"")
            if len(self.savefile) > 0: 
                self.mol.WriteTinkerXYZ(self.savefile)
        
        if item == "Read anlfile":
            anlfile='e:/fu-sample/1crnhadd.anl'
            prmfile='e:/fu-sample/1crnhadd.prm'
            potdic=self.ReadTinkerAnalyzeFile(anlfile)
            self.WriteTinkerPrmFile(prmfile,potdic,False)

        # file-save as
        if item == "all files":
            self.SaveAllFiles()
        if item == "pdb file":
            self.SaveFile(self.pdbfile)
        if item == "xyz file":
            self.SaveFile(self.xyzfile)
        if item == "int file":
            self.SaveFile(self.intfile)
        if item == "key file":
            self.SaveFile(self.keyfile)
        if item == "out file":
            self.SaveFile(self.outfile)
        # file-delete
        if item == "del all files":
            self.DeleteTempIOFiles()
            self.btnreset.Enable()
            
        if item == "del pdb file":
            try: os.remove(self.pdbfile)
            except: lib.MessageBoxOK("Failed to delete "+self.pdbfile,"")

        if item == "del out file":
            try: os.remove(self.outfile)
            except: wx.MessageBox("Failed to delete "+self.outfile,"")

        if item == "del xyz file":
            try: os.remove(self.xyzfile)
            except: lib.MessageBoxOK("Failed to delete "+self.xyzfile,"")

        if item == "del int file":
            try: os.remove(self.intfile)
            except: lib.MessageBoxOK("Failed to delete "+self.intfile,"")

        if item == "del key file":
            try: os.remove(self.keyfile)
            except: lib.MessageBoxOK("Failed to delete "+self.keyfile,"")

        if item == "Delete all files in scratch directory":
            self.DeleteScratchFiles()
        # Edit
        if item == "parameter file":
           self.OpenEditor(self.fffile)
        if item == "temp pdb file":
            self.OpenEditor(self.pdbfile)
        if item == "temp xyz file":
            self.OpenEditor(self.xyzfile)
        if item == "temp int file":
            self.OpenEditor(self.intfile)
        if item == "temp key file":
            self.OpenEditor(self.keyfile)
        if item == "temp out file":
            self.OpenEditor(self.outfile)
            
        if item == "Setting":
            if self.ctrlflag.Get('tinpathwin'): return
            setp=SetPathForTinker_Frm(self,-1,self.prgfile)
            setp.Show()
            self.ctrlflag.Set('tinpathwin',True)
        
        if item == "Help": self.HelpMessage()
        
        if item == "Close":
            self.OnClose(0)
        
        if item == "Atom type":
            self.OpenAtmTypPanel()
        
        if item == "FF parameters":
            self.OpenAssignFFParamPanel()
                   
        if item == "Tinker PDBXYZ":
            self.ExecTinkerPDBXYZ()

        if item == "Tinker analyze":
            self.ExecTinkerAnalyze()
            
        if item == "pdbxyz-newton":
            prg=[]; arg=[]; plt=[]
            #prg.append("e:/winfort/tinker/bin-win64/pdbxyz")
            #arg.append("e:/fu-tinker/test/1crnhadd.pdb e:/winfort/tinker/params/amber99.prm")
            #plt.append({})
            self.xyzfile="e:/fu-tinker/test/1crnhadd.xyz"
            prg.append("e:/winfort/tinker/bin-win64/newton")
            arg.append(self.xyzfile+" A A 0.1") #e:/winfort/tinker/params/amber99.prm A A 0.1") # > e:/fu-tinker/test/test10.out")
            #pltdic={'winpos':[-1,-1],'winsize':[640,250],'every':0,
            #        'fromkw':"Iter",'tokw':"\n",'xitemno':0,'yitemno':1,
            #        'xform':'int','yform':'float','title':'Newton optimization',
            #        'xlabel':'iteratin','ylabel':'energy in kcal/mol'} # full specification     
            pltdic={'fromkw':"Iter",'tokw':"???",'xitemno':0, 'yitemno':1} # medium
            #pltdic={'xitemno':0, 'yitemno':1} # minimum 
            plt.append(pltdic) 
            # do not make cycle files
            #f=open('e:/winfort/tinker/kktest/fu-temp.key','w')
            #f.write('overwrite'+'\n')
            #f.close()

            if not self.openexeprgwin: self.OpenExePrgWin()
                # open output window
                #winpos=[0,0]; winsiz=[750,300]
                #self.exeprgwin=subwin.ExecProg_Frm(self,-1,winpos,winsiz)
                #self.exeprgwin.Show()
                #self.openexeprgwin=True    
            jobid=2
            self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,"","e:/fu-tinker/test/test10.out")
                    
            """
            tinmol=rwfile.ReadTinkerXYZ("e:/winfort/tinker/kktest/futmptmp.xyz")
            self.mol.SetTinkerAtoms(tinmol) #,False)
            self.mol.WriteTinkerXYZ("e:/winfort/tinker/kktest/futmp.xyz")
            
            plt.append({})
            prg.append("e:/winfort/tinker/bin-win64/analyze")
            arg.append("e:/winfort/tinker/kktest/futmp.xyz e:/winfort/tinker/params/tiny.prm G")
            #pltdic={'winpos':[-1,-1],'winsize':[640,250],'every':0,
            #        'fromkw':"Iter",'tokw':"\n",'xitemno':0,'yitemno':1,
            #        'xform':'int','yform':'float','title':'Newton optimization',
            #        'xlabel':'iteratin','ylabel':'energy in kcal/mol'} # full specification     
            #pltdic={'fromkw':"Iter",'tokw':"???",'xitemno':0, 'yitemno':1} # medium
            #pltdic={'xitemno':0, 'yitemno':1} # minimum 
            #plt.append(pltdic) 
            # do not make cycle files
            f=open('e:/winfort/tinker/kktest/futmp.key','w')
            f.write('debug'+'\n')
            f.close()
            """
            
        if item == 'Cancel':
            if not self.openexeprgwin: return
            self.exeprgwin.KillProcess() #process.kill()
            #self.exeprgwin.OnClose(1)
            #self.openexeprgwin=False

    def OnClose(self,event):
        if self.openexeprgwin:
            lib.MessageBoxOK("'Execute Program Window' is active. Please close it.","")
            return
        self.ctrlflag.Set('tinoptwin',False)
        self.Destroy()

class AssignFFParam_Frm(wx.Frame):
    def __init__(self,parent,id,winpos,winsize):
        self.title='FF term paramerter assign'
        wx.Frame.__init__(self,parent,id,pos=winpos,size=winsize) #,

        [w,h]=self.GetClientSize()
        
        self.sashposition1=h/2
        self.hcmd=60
        self.todeg=const.Const['todeg']

        self.tgtff=parent.tgtff
        self.tinkeratoms=parent.tinkeratoms
        #!!self.pdbatoms=parent.pdbatoms
        #self.xloctgtmess=310; self.yloctgtmess=0
        ###self.xlocunasgn=245; self.ylocunasgn=0
        #
        self.parent=parent 
        #self.mol=parent.mol
        self.xyzfile=parent.xyzfile
        self.pdbfile=parent.pdbfile
        self.fffile=parent.fffile
        self.atmtyp=[] #parent.tinkeratms
        self.elmvaleclslst=[]
        self.MakeElmValeClassLst()
        #!!!self.uterms=parent.uterms
        # [seq,atmnam,xyz,type,con
        #self.view=parent.view
        #self.ctrlflag=model.ctrlflag
        #wrkmolnam=model.wrkmolnam
        #self.SetTitle(self.title+' ['+wrkmolnam+']')
        """
        # Menu
        menud=self.MenuItems()
        self.menubar=lib.fuMenu(menud)
        self.SetMenuBar(self.menubar.menuitem)
        self.ffamenu=self.menubar.menuitem
        self.Bind(wx.EVT_MENU,self.OnMenu)
        """
        # load force field name and its file name
        #self.SetFFNamesAndFiles()        
        #
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        #
        self.ffnamelst=self.parent.ffnamelst
        self.fffiledic=self.parent.fffiledic 
        # current ff
        self.ffname=self.parent.ffname
        #self.fffilename=self.fffiledic[self.ffname]
        #self.curff=ForceField(self.ffname,self.fffilename)
        # reference FF
        self.refffname=self.ffname
        self.reffffile=self.fffiledic[self.refffname]
        self.refff=ForceField(self.refffname,self.reffffile)
        self.refff.ReadFFPotTerms()
        self.MakeClassDescriDic()
        self.ffuniqcls=True
        #self.refffuniqcls=True # flag to lsit unique class only
        #
        
        #self.uterms=self.parent.uterms
        #self.curterm=self.uterms[0]
        #else: self.curterm=""
        #self.utermdic=self.parent.utermdic
        #?? test
        #self.utermdic['atom']=[]
        #self.uterms=parent.uterms
        #self.uterms=["atom"]+self.uterms
        
        self.tclprm=[] # list to sore tcl wegets
        self.paramdat=[-1]+6*[""]
        self.targetdat=""  
        #self.asgntermdic=parent.tgtff.pottermdic #parent.utermdic #{}
        #self.uterms=self.asgntermdic.keys()
        self.uterms=parent.tgtff.pottermdic.keys()
        #print 'pottermdic in ffassign',self.tgtff.pottermdic
        self.curterm=self.uterms[0]
        if len(self.uterms) > 1: self.RmvAtomInUterms()
        #self.ConvertUtermDic()
        self.ComputeGeometricalParams()
        self.curdat=-1
        #self.curuterm=self.uterms[0]
        #self.size=self.GetClientSize()
        #self.selwithvale=True
        #self.selwithclass=True
        #self.refselwithvale=True
        #self.refselwithclass=True
        #self.pattern=0
        self.listlistitem=['all','unassigned','assiged']
        self.listlist=0 # 0:all, 1:unassign, 2:assign
        self.listselformitem=['elm.vale(cls)','elm.vale','elm']
        self.listselform=1
        self.fflistselformitem=['elm.vale','elm']
        self.fflistselform=0
        self.ffselectitemauto=True
        self.selectitem='all'
        self.selectitemlst=[]
        self.selectitemdic={}
        self.ffselectitem='all'
        self.ffselectitemlst=[]
        self.ffselectitemdic={}
        self.curlistlst=[] # current listed data list
        self.ffcurlistlst=[]
        # atom list options
        self.atmtypdatnmbdic={}
        self.actatm=[]
        ##self.all=True # list all atoms
        
        #self.tablelst=['none','all'] # look up table for atmtyp
        #self.tbl='none'
        
        self.atmtypsav=0
        self.targetdicsav={}
        self.tgtatmsav=-1
        self.atmtypselected=False

        self.CreateSplitterWindow()
        self.CreateCmdPanel()
               
        self.Bind(wx.EVT_SIZE,self.OnSize)    
    
    
    def ComputeGeometricalParams(self):
        for i in range(len(self.uterms)):
            if self.uterms[i] == 'bond': self.ComputeBondLength()                
            if self.uterms[i] == 'angle': self.ComputeBendingAngle()   
            if self.uterms[i] == 'torsion': self.ComputeTorsionAngle()   
            if self.uterms[i] == 'imptors': self.ComputeImptorsAngle()   
    
    def ComputeBondLength(self):
        self.bondlengthdic={}
        natm=len(self.tinkeratoms)
        term=self.tgtff.pottermdic['bond']
        if natm <= 0 or len(term) <= 0: return
        #print 'bond term',term
        for i in range(len(term)):
            atm1=term[i][1]; atm2=term[i][3]
            ia1=int(atm1)-1; ia2=int(atm2)-1
            cc1=self.tinkeratoms[ia1][2]; cc2=self.tinkeratoms[ia2][2]
            r=lib.Distance(cc1,cc2)
            keyatm=atm1+'-'+atm2
            self.bondlengthdic[keyatm]=('%6.3f' % r)
        #print 'bondlengthdic',self.bondlengthdic
        
    def ComputeBendingAngle(self):
        self.bendingangledic={}
        natm=len(self.tinkeratoms)
        term=self.tgtff.pottermdic['angle']
        if natm <= 0 or len(term) <= 0: return
        for i in range(len(term)):
            atm1=term[i][1]; atm2=term[i][3]; atm3=term[i][5]
            ia1=int(atm1)-1; ia2=int(atm2)-1; ia3=int(atm3)-1
            cc1=self.tinkeratoms[ia1][2]; cc2=self.tinkeratoms[ia2][2]
            cc3=self.tinkeratoms[ia3][2]
            a=lib.BendingAngle(cc1,cc2,cc3)*self.todeg  
            keyatm=atm1+'-'+atm2+'-'+atm3
            self.bendingangledic[keyatm]=('%6.1f' % a)
        #print 'bendingangledic',self.bendingangledic
     
    def ComputeTorsionAngle(self):
        self.torsionangledic={}
        natm=len(self.tinkeratoms)
        term=self.tgtff.pottermdic['torsion']
        if natm <= 0 or len(term) <= 0: return
        for i in range(len(term)):
            atm1=term[i][1]; atm2=term[i][3]; atm3=term[i][5]; atm4=term[i][7]
            ia1=int(atm1)-1; ia2=int(atm2)-1; ia3=int(atm3)-1; ia4=int(atm4)-1
            cc1=self.tinkeratoms[ia1][2]; cc2=self.tinkeratoms[ia2][2]
            cc3=self.tinkeratoms[ia3][2]; cc4=self.tinkeratoms[ia4][2]
            a=lib.TorsionAngle(cc1,cc2,cc3,cc4)*self.todeg  
            keyatm=atm1+'-'+atm2+'-'+atm3+'-'+atm4
            self.torsionangledic[keyatm]=('%6.1f' % a)
        #print 'torsionangledic',self.torsionangledic

    def ComputeImptorsAngle(self):
        """ not comleted yet """
        self.imptorsangledic={}
        natm=len(self.tinkeratoms)
        term=self.tgtff.pottermdic['imptors']
        if natm <= 0 or len(term) <= 0: return

    def RmvAtomInUterms(self):
        for i in range(len(self.uterms)):
            if self.uterms[i] == 'atom':
                del self.uterms[i]; break                

    def MakeElmValeClassLst(self):
        self.elmvaleclslst=[] 
        elmlst,valelst=self.GetMolElmVale()
        #print 'elmlst',elmlst
        #print 'valelst',valelst
        """tinatm[[seq,atmnam,[x,y,z],type,con],...]""" 
        #tinatoms=fumole.fuMole.ReadTinkerXYZ(self.xyzfile)
        tinatoms=self.tinkeratoms
        for i in range(len(tinatoms)):
            elm=elmlst[i].strip(); vale=str(valelst[i]); type=str(tinatoms[i][3]); seq=tinatoms[i][0]
            self.elmvaleclslst.append([i+1,elm,vale,type])
        #print 'elmvaleclslst',self.elmvaleclslst

    def CreateSplitterWindow(self):
        # create splitwindow
        #hcmd=80
        size=self.GetClientSize()
        w=size[0]; h=size[1]
        xspl=w; yspl=h-self.hcmd ###h #-hcmd
        self.splwin1=wx.SplitterWindow(self,-1,size=(xspl,yspl), style=wx.SP_3D)
        self.splwin2=wx.SplitterWindow(self.splwin1)
        # upper panel
        xsize=w; xpos=0; ypos=0 #; ysize=h/3 #ysize=self.size[1] # ; xsize=self.size[0]
        xpos=0; ypos=0
        ysizeasgn=self.sashposition1
        self.panasgn=wx.Panel(self.splwin2,-1,pos=(xpos,ypos),size=(xsize,ysizeasgn)) #ysize))
        self.panasgn.SetBackgroundColour("light gray")
        # lower panel
        xpos=0; ypos=self.sashposition1 #1
        
        ###xsizeffprm=w; ysizeffprm=self.sashposition1 #1 #xsize-xpos
        xsizeffprm=w; ysizeffprm=self.sashposition1 #-self.hcmd #1 #xsize-xpos

        self.panffprm=wx.Panel(self.splwin1,-1,pos=(xpos,ypos),size=(xsizeffprm,ysizeffprm)) #ysize))
        self.panffprm.SetBackgroundColour("light gray")
        self.splwin1.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,self.OnSplitWin1Changed)
        self.splwin1.SplitHorizontally(self.splwin2,self.panffprm,sashPosition=self.sashposition1)
        # upper panel
        self.CreateAssignPanel()
        
        # lower panel
        self.CreateReferenceFFPanel()
        
    def CreateAssignPanel(self):
        [w,h]=self.panasgn.GetSize()
        #h=self.sashposition1 #2
        xsize=w #self.sashposition
        ysize=h
        xpanasgn=xsize-10 #550
        hcb=const.HCBOX
        # put weget
        yloc=5
        self.DisplayTitle()
        #
        yloc=yloc+25
        wx.StaticText(self.panasgn,-1,"ff-term:",pos=(10,yloc+2),size=(45,18)) 
        self.cmbtrm=wx.ComboBox(self.panasgn,-1,'',choices=[], \
                               pos=(60,yloc-2),size=(80,hcb),style=wx.CB_READONLY)                      
        self.cmbtrm.Bind(wx.EVT_COMBOBOX,self.OnListTerm)
        self.SetFFTermLst()
        #
        wx.StaticText(self.panasgn,-1,"select:",pos=(150,yloc+2),size=(40,18)) 
        self.cmbsel=wx.ComboBox(self.panasgn,-1,'',choices=[], \
                               pos=(190,yloc-2),size=(250,hcb),style=wx.CB_READONLY)                      
        self.cmbsel.Bind(wx.EVT_COMBOBOX,self.OnSelectItem)

        #btnbak=wx.Button(self.panasgn,wx.ID_ANY,"back",pos=(445,yloc),size=(40,18))
        #btnbak.Bind(wx.EVT_BUTTON,self.OnSelectItemBack)
        #btnnxt=wx.Button(self.panasgn,wx.ID_ANY,"next",pos=(495,yloc),size=(40,18))
        #btnnxt.Bind(wx.EVT_BUTTON,self.OnSelectItemNext)

        wx.StaticText(self.panasgn,-1,'form:',pos=(450,yloc+2),size=(35,18)) 
        self.cmbfrm=wx.ComboBox(self.panasgn,-1,'',choices=self.listselformitem, \
                               pos=(485,yloc-2),size=(90,hcb),style=wx.CB_READONLY)                      
        self.cmbfrm.Bind(wx.EVT_COMBOBOX,self.OnListSelForm)
        self.SetListSelForm()

        wx.StaticText(self.panasgn,-1,'list:',pos=(585,yloc+2),size=(20,18)) 
        self.cmblst=wx.ComboBox(self.panasgn,-1,'',choices=self.listlistitem, \
                               pos=(610,yloc-2),size=(75,hcb0),style=wx.CB_READONLY)                      
        self.cmblst.Bind(wx.EVT_COMBOBOX,self.OnListList)
        self.SetListAssign()
        self.cmbtrm.SetStringSelection(self.curterm)

        hsize=h-yloc-10
        #xsize=w-10; ysize=h-yloc-10 #yloc-10
        yloc=yloc+25
        ysizelc=h-yloc-5 #2 #self.sashposition2-yloc-2 #yloc-10
        xsizelc=w-150 #xsizelc=w-10; 
        self.lstctrl=wx.ListCtrl(self.panasgn,-1,pos=(5,yloc),size=(xsizelc,ysizelc), #xpanasgn,hsize),
                                 style=wx.LC_REPORT)
        self.lstctrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnDataSelected)
        
        self.SetItemNamesInAssignLC() 
        self.ListItemsInAssignLC(True)

        tcpos=[w-145,yloc]; tcsize=[140,ysizelc]
        self.asgntxt=wx.TextCtrl(self.panasgn,pos=tcpos,size=tcsize,style=wx.TE_MULTILINE) #|wx.TE_READONLY|wx.TE_NOHIDESEL)
        self.DispChemOnAssignTC()
        
        self.yloclstmess=yloc

    def DisplayTitle(self):
        xloc=5; yloc=5; xsize=800
        sa=[]
        sa.append("Forcefield: ")
        sa.append(self.ffname)
        sa.append(", Number of undefined parameters: ")
        for i in range(len(self.uterms)):
            tot=len(self.tgtff.pottermdic[self.uterms[i]])
            
            nmb=self.CountUndefinedParams(self.uterms[i]) #print 'uterms',self.uterms[i]
            #print 'asndic',self.asgntermdic[self.uterms[i]]
            #print 'tot',tot
            #print 'str(tot)',str(tot)
            sa.append(self.uterms[i]+"=")
            sa.append(str(nmb)+"/"+str(tot)+", ")
        text="".join(sa)
        n=len(text); text=text[:n-2]
        wx.StaticText(self.panasgn,-1,text,pos=(xloc,yloc),size=(xsize,18)) 
    
    def CountUndefinedParams(self,ffterm):
        nmb=-1
        term=self.tgtff.pottermdic[ffterm]
        if ffterm == 'atom':
            for seqnmb,typ,cls,nam,atmic,mass,vale,com in term:
                if cls == 0: nmb += 1
            nmb += 1
        elif ffterm == 'bond':
            for datnmb,atm1,nam1,atm2,nam2,cls1,cls2,bondk,bondr,rmk in term:
                #if bondk == "0.0" and bondr == "0.0": nmb += 1
                if bondk == "" and bondr == "": nmb += 1
            nmb += 1         
        elif ffterm == 'angle':
            for datnmb,atm1,nam1,atm2,nam2,atm3,nam3,cls1,cls2,cls3,anglek,anglea,rmk in term:        
                #if anglek == "0.0" and anglea == "0.0": nmb += 1
                if anglek == "" and anglea == "": nmb += 1
            nmb += 1
        elif ffterm == 'torsion':
            for datnmb,atm1,nam1,atm2,nam2,atm3,nam3,atm4,nam4,cls1,cls2,cls3,cls4, \
                        torsk1,torsa1,torsk2,torsa2,torsk3,torsa3,rmk in term:
                #if torsk1 == "0.0" and torsa1 == "0/0": nmb += 1
                if torsk1 == "" and torsa1 == "": nmb += 1
            nmb += 1
        return nmb

    def OnSelectItemNext(self,event):
        nmb=self.selectitemdic[self.selectitem]
        nitm=len(self.selectitemlst)
        if nmb == 1:
            ans=lib.MessageBoxYesNo("Hit bottom. Continue at top?.","")
            if ans: self.selectitem=self.selectitemlst[nitm-1]
            else: return
        else: self.selectitem=self.selectitemlst[nmb-1]
        self.cmbsel.SetStringSelection(self.selectitem)

        self.paramdat=[-1]+6*[""]
        self.SetParamDataInTC()

        
        self.OnSelectItem(1)
    
    def OnSelectItemBack(self,event):
        nmb=self.selectitemdic[self.selectitem]
        nitm=len(self.selectitemlst)
        if nmb == nitm-1:
            ans=lib.MessageBoxYesNo("Hit top. Continue at bottom?.","")
            if ans: self.selectitem=self.selectitemlst[1]
            else: return
        else: self.selectitem=self.selectitemlst[nmb+1]
        self.cmbsel.SetStringSelection(self.selectitem)

        self.paramdat=[-1]+6*[""]
        self.SetParamDataInTC()
        
        self.OnSelectItem(1)
    
    def SetListAssign(self):
        if self.listlist == 0:
            self.cmblst.SetStringSelection(self.listlistitem[0])
        if self.listlist == 1:
            self.cmblst.SetStringSelection(self.listlistitem[1])
        if self.listlist == 2:
            self.cmblst.SetStringSelection(self.listlistitem[2])

    def OnListList(self,event):
        item=self.cmblst.GetStringSelection()
        if item == self.listlistitem[0]: self.listlist=0
        if item == self.listlistitem[1]: self.listlist=1
        if item == self.listlistitem[2]: self.listlist=2
        self.ListItemsInAssignLC(True)
    
    def SetListSelForm(self):
        if self.listselform == 0:
            self.cmbfrm.SetStringSelection(self.listselformitem[0])
        if self.listselform == 1:
            self.cmbfrm.SetStringSelection(self.listselformitem[1])
        if self.listselform == 2:
            self.cmbfrm.SetStringSelection(self.listselformitem[2])
        #if self.listselform == 3:
        #    self.cmbfrm.SetStringSelection(self.listselformitem[3])
    
    def SetFFListSelForm(self):
        if self.fflistselform == 0:
            self.cmbfffrm.SetStringSelection(self.fflistselformitem[0])
        if self.fflistselform == 1:
            self.cmbfffrm.SetStringSelection(self.fflistselformitem[1])
        
    def OnListSelForm(self,event):
        item=self.cmbfrm.GetStringSelection()
        if item == self.listselformitem[0]: self.listselform=0 # elm.vale(class)
        if item == self.listselformitem[1]: self.listselform=1 # elm.vale
        if item == self.listselformitem[2]: self.listselform=2 # elm
        #if item == self.listselformitem[3]: self.listselform=3 # elm            
        self.selectitem='all'
        self.cmbsel.SetStringSelection('all')
        #self.SetSelectItem()
        self.ListItemsInAssignLC(True)
        #self.ListItemsInAssignLC()
    def OnFFListSelForm(self,event):
        item=self.cmbfffrm.GetStringSelection()
        if item == self.fflistselformitem[0]: self.fflistselform=0 # elm.vale(class)
        if item == self.fflistselformitem[1]: self.fflistselform=1 # elm.vale
        self.ffselectitem='all'
        self.cmbffsel.SetStringSelection('all')
        #self.SetSelectItem()
        self.ListItemsInRefFFLC(True)
        #self.ListItemsInAssignLC()
    
    def OnSelectItem(self,event):
        self.SetSelectAllItem(0)
        self.selectitem=self.cmbsel.GetStringSelection()
        #print ' onselectitem',self.selectitem    
        self.ListItemsInAssignLC(False)
        
        #print 'self.ffselectitemauto',self.ffselectitemauto
        if self.ffselectitemauto:
            self.ffselectitem=self.selectitem
            #print 'OnSelItem ff sel',self.ffselectitem
            self.cmbffsel.SetStringSelection(self.ffselectitem)
            self.ListItemsInRefFFLC(True)
            self.ListItemsInRefFFLC(False)

    def OnFFSelectItem(self,event):
        self.ffselectitem=self.cmbffsel.GetStringSelection()
        #print ' onffselectitem',self.ffselectitem
        if self.ffselectitemauto:
            self.ffselectitemauto=False
            self.ckbauto.SetValue(False)
        
        self.ListItemsInRefFFLC(False)
    
    def SetSelectItemForFF(self):
        self.ffselectitem=self.cmbffsel.GetStringSelection()
        if self.selectitem == 'all': self.ffselectitem='all'
        else:
            if self.listselform <= 1: # elm.vale(cls) and elm.vale
                self.fflistselform=0 # elm.vale
                self.ffselectitem=self.RmvClsFromText(self.selectitem)
            else: # elm
                self.fflistselform=1 # elm
                self.ffselectitem=self.RmvClsFromText(self.selectitem)
                self.ffselectitem=self.RmvValeFromText(self.ffselectitem)
            #!!self.cmbfffrm.SetStringSelection(self.fflistselformitem[self.fflistselform])        
        
        self.cmbffsel.SetStringSelection(self.ffselectitem)

        #print 'Set selectitem in for ff',self.ffselectitem
        #print 'Set form in for ff ',self.fflistselform
                        
    def RmvClsFromText(self,text):
        otext=text; i=1
        while i > 0:
            ns=otext.find('('); ne=otext.find(')')
            if ns < 0 and ne < 0: i=-1
            if ns >= 0 and ne >= 0: otext=otext[:ns]+otext[ne+1:]
        return otext

    def RmvValeFromText(self,text):
        otext=text; i=1
        while i > 0:
            ns=otext.find('.')
            if ns < 0: i=-1
            if ns >= 0: otext=otext[:ns]+otext[ns+1:]
        return otext
        
    def CreateReferenceFFPanel(self):
        # popup control panel
        [w,h]=self.panffprm.GetSize() #.GetClientSize()
        #print 'ffprm pan size',w,h
        
        ###xpos=self.sashposition+5
        #hcmd=100
        hcb=const.HCBOX
        ypos=0; ysize=h #h-hcmd #; xsize=self.size[0]; ysize=self.size[1]; xpos=555; 
        xpansize=w #-xpos #xsize-xpos
        yopt=165; ychg=5 #40 
        yloc=5
        wx.StaticText(self.panffprm,-1,"Reference forcefield:",pos=(5,yloc+2),size=(120,18)) 
        self.cmbff=wx.ComboBox(self.panffprm,-1,'',choices=[], \
                               pos=(130,yloc-2),size=(100,hcb),style=wx.CB_READONLY)                      
        self.SetForceField()
        
        self.cmbff.SetStringSelection(self.refffname)
        self.cmbff.Bind(wx.EVT_COMBOBOX,self.OnRefFFChoice)
        
        self.ckbffunq=wx.CheckBox(self.panffprm,-1,"unique-class",pos=(235,yloc),size=(85,18))
        self.ckbffunq.Bind(wx.EVT_CHECKBOX,self.OnFFUniqClass)
        self.ckbffunq.SetValue(self.ffuniqcls)

        #self.ckbffcls=wx.CheckBox(self.panffprm,-1,"uniqcls",pos=(240,yloc),size=(50,18))
        #self.ckbffcls.Bind(wx.EVT_CHECKBOX,self.OnFFUniqClass)
        #self.ckbffcls.SetValue(self.refffuniqcls)
        #if not self.refffname[0:5] == 'AMBER': self.ckbffcls.Disable()
        #yloc=yloc+22
        wx.StaticText(self.panffprm,-1,"select:",pos=(335,yloc+2),size=(40,18))         
        self.ckbauto=wx.CheckBox(self.panffprm,-1,"auto",pos=(380,yloc),size=(40,18))
        self.ckbauto.Bind(wx.EVT_CHECKBOX,self.OnFFSelectItemAuto)
        self.ckbauto.SetValue(self.ffselectitemauto)
        self.cmbffsel=wx.ComboBox(self.panffprm,-1,'',choices=[], \
                               pos=(425,yloc-2),size=(120,hcb),style=wx.CB_READONLY)                      
        self.cmbffsel.Bind(wx.EVT_COMBOBOX,self.OnFFSelectItem)
        self.SetFFSelectItem()
        #self.cmbffsel.SetStringSelection(self.ffselectitem)
        #btnffbak=wx.Button(self.panffprm,wx.ID_ANY,"back",pos=(455,yloc),size=(40,18))
        #btnffbak.Bind(wx.EVT_BUTTON,self.OnFFSelectItemBack)
        #btnffnxt=wx.Button(self.panffprm,wx.ID_ANY,"next",pos=(500,yloc),size=(40,18))
        #btnffnxt.Bind(wx.EVT_BUTTON,self.OnFFSelectItemNext)

        wx.StaticText(self.panffprm,-1,'form:',pos=(555,yloc+2),size=(35,18))
        self.cmbfffrm=wx.ComboBox(self.panffprm,-1,'',choices=self.fflistselformitem, \
                               pos=(590,yloc-2),size=(90,hcb),style=wx.CB_READONLY)
        self.cmbfffrm.Bind(wx.EVT_COMBOBOX,self.OnFFListSelForm)
        self.SetFFListSelForm() 


        #self.SetElmValeClsLst()      
        #wx.StaticText(self.panffprm,-1,"pattern:",pos=(600,yloc+2),size=(55,18)) 
        #self.cmbffpat=wx.ComboBox(self.panffprm,-1,'',choices=[], \
        #                       pos=(660,yloc-2),size=(70,20),style=wx.CB_READONLY)                      
        #self.cmbffpat.Bind(wx.EVT_COMBOBOX,self.OnFFPattern)
        #self.SetFFSelPattern()

        
        
        self.refatmtyplst=self.refff.GetFFAtmTypList()        
        #self.SetFFGroupLst()
        #self.SetFFElementLst()

        
        #self.cmbffelm.SetStringSelection(self.ffelm)
        #self.SetFFAtmClassLst()
        ysizelc=h-32 # 30 ### self.hcmd-30 #10 #5 #chg=xpansize-10 #540
        xsizelc=w-150 #10; #ylst=ysize-hcmd-5 #yopt-ychg-5
        yloc=yloc+22
        self.lstprm=wx.ListCtrl(self.panffprm,-1,pos=(5,yloc),size=(xsizelc,ysizelc),
                                 style=wx.LC_REPORT|wx.LC_SINGLE_SEL) #|wx.LC_NO_HEADER) #wx.LC_SINGLE_SEL|
        self.lstprm.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnRefFFDataSelected)
        self.SetItemNamesInRefFFLC()
        self.ListItemsInRefFFLC(True)
        
        #self.lstctyp.Bind(wx.EVT_LIST_ITEM_SELECTED,self.OnAtmTypSelected)
        tcpos=[w-145,yloc]; tcsize=[140,ysizelc]
        self.reftc=wx.TextCtrl(self.panffprm,pos=tcpos,size=tcsize,style=wx.TE_MULTILINE) #|wx.TE_READONLY|wx.TE_NOHIDESEL)

        #self.lowerpanloc=ylst+yloc+10

        #self.CreateCmdPanel()
    
    def OnFFUniqClass(self,event):
        self.ffuniqcls=self.ckbffunq.GetValue()

    def OnFFSelectItemAuto(self,event):
        self.ffselectitemauto=self.ckbauto.GetValue()
        self.SetSelectItemForFF()
        self.ListItemsInRefFFLC(False)
    
    def SetItemNamesInRefFFLC(self):
        # clear all items
        self.lstprm.DeleteAllColumns()
    
        self.lstprm.InsertColumn(0,'param',width=50)
        if self.curterm != "atom":
            self.lstprm.InsertColumn(1,'elm.vale',width=200)
        if self.curterm == 'atom':
            self.lstprm.InsertColumn(1,'atmnam',width=80)
            self.lstprm.InsertColumn(2,'type',width=50)
            self.lstprm.InsertColumn(3,'elm.vale',width=80)
            self.lstprm.InsertColumn(4,'class',width=50)
            self.lstprm.InsertColumn(5,'Description',width=150)
        elif self.curterm == "bond":
            self.lstprm.InsertColumn(2,'  k  ',width=60)
            self.lstprm.InsertColumn(3,'  r  ',width=60)
        elif self.curterm == "angle":
            if self.refffname[0:2] == 'MM':
                self.lstprm.InsertColumn(2,'  k1 ',width=60)
                self.lstprm.InsertColumn(3,'  a1 ',width=60)
                self.lstprm.InsertColumn(4,'  a2 ',width=60)
                self.lstprm.InsertColumn(5,'  a3 ',width=60)
            else:
                self.lstprm.InsertColumn(2,'  k  ',width=60)
                self.lstprm.InsertColumn(3,'  a  ',width=60)                
        elif self.curterm == 'torsion':
            self.lstprm.InsertColumn(2,'  k1 ',width=60)
            self.lstprm.InsertColumn(3,'a1/p1',width=60)
            self.lstprm.InsertColumn(4,'  k2 ',width=60)
            self.lstprm.InsertColumn(5,'a2/p2',width=60)
            self.lstprm.InsertColumn(6,'  k3 ',width=60)
            self.lstprm.InsertColumn(7,'a3/p3',width=60)
        elif self.curterm == 'imptors':
            self.lstprm.InsertColumn(2,'  k  ',width=60)
            self.lstprm.InsertColumn(3,' a/p ',width=60)
 
    def ListItemsInRefFFLC(self,makelst):
        if makelst: self.ffcurlistlst=[]
        
        self.paramdat=[-1]+6*[""]
        
        self.lstprm.DeleteAllItems()
        self.SetItemNamesInRefFFLC()
        termdic=self.refff.pottermdic
        self.refffdatnmblst=[]
        uniqdic={}
        #atom=self.refff.pottermdic['atom']
        #print 'bond',termdic['bond']
        if self.curterm == 'atom':
            nq=0
            for datnmb,type,cls,atmnam,atomic,mass,vale,com in termdic['atom']:
                #nam,elm,vale=self.refff.FindAtmNamAtmicVale(cls)
                #print 'atomic',atomic
                elm=atomic #const.ElmSbl[int(atomic)]
                text=elm+'.'+vale
                ctext=text+'/'+cls
                if uniqdic.has_key(ctext): continue
                else:
                    nq += 1; uniqdic[ctext]=datnmb
                
                lst=[elm,vale]
                if makelst: self.ffcurlistlst.append(lst)
                #print 'lst,Isselected',lst,self.IsFFSelected(lst)                
                if not makelst and not self.IsFFSelected(lst): continue
                
                index=self.lstprm.InsertStringItem(sys.maxint,datnmb)
                self.lstprm.SetStringItem(index,1,atmnam)
                self.lstprm.SetStringItem(index,2,type)
                self.lstprm.SetStringItem(index,3,text)
                self.lstprm.SetStringItem(index,4,cls)
                self.lstprm.SetStringItem(index,5,com)
                
                self.refffdatnmblst.append(int(datnmb)-1)
    
            if makelst: self.SetFFSelectItem()
            #if len(self.refffdatnmblst) > 0:
            #self.lstprm.Select(0,1) # data #, 1=on
            #self.OnRefFFDataSelected(0)
            #self.DispAtmTypDescription([])
            
        
        if self.curterm == 'bond':
            nq=0
            for datnmb,cls1,cls2,bondk,bondr in termdic['bond']:
                nam1,elm1,vale1=self.refff.FindAtmNamAtmicVale(cls1)
                nam2,elm2,vale2=self.refff.FindAtmNamAtmicVale(cls2)
                text=elm1+'.'+vale1+'-'+elm2+'.'+vale2
                ctext=text+'/'+bondk+'/'+bondr
                if uniqdic.has_key(ctext): continue
                else:
                    nq += 1; uniqdic[ctext]=datnmb
                
                lst=[elm1,vale1,elm2,vale2]
                if makelst: self.ffcurlistlst.append(lst)
                if not makelst and not self.IsFFSelected(lst): continue
                index=self.lstprm.InsertStringItem(sys.maxint,datnmb)
                self.lstprm.SetStringItem(index,1,text)
                self.lstprm.SetStringItem(index,2,bondk)
                self.lstprm.SetStringItem(index,3,bondr)
                
                self.refffdatnmblst.append(int(datnmb)-1)
    
            if makelst: self.SetFFSelectItem()
            #if len(self.refffdatnmblst) > 0:
            #self.lstprm.Select(0,1) # data #, 1=on
            #self.OnRefFFDataSelected(0)
            #self.DispAtmTypDescription([])
                
        elif self.curterm == 'angle':
            nq=0
            for i in range(len(termdic['angle'])):
                item=termdic['angle'][i]; n=len(item)
                datnmb=item[0]
                cls1=item[1]; cls2=item[2]; cls3=item[3]
                nam1,elm1,vale1=self.refff.FindAtmNamAtmicVale(cls1)
                nam2,elm2,vale2=self.refff.FindAtmNamAtmicVale(cls2)
                nam3,elm3,vale3=self.refff.FindAtmNamAtmicVale(cls3)
                text=elm1+'.'+vale1+'-'+elm2+'.'+vale2+'-'+elm3+'.'+vale3

                ctext=text
                for j in range(4,n): ctext=ctext+'/'+item[j]
                
                if uniqdic.has_key(ctext): continue
                else:
                    nq += 1; uniqdic[ctext]=datnmb
                
                lst=[elm1,vale1,elm2,vale2,elm3,vale3]
                if makelst: self.ffcurlistlst.append(lst)
                if not makelst and not self.IsFFSelected(lst): continue
                
                index=self.lstprm.InsertStringItem(sys.maxint,datnmb)
                self.lstprm.SetStringItem(index,1,text)
                ii=1
                for j in range(4,n):
                    ii += 1; self.lstprm.SetStringItem(index,ii,item[j]) #str(anglek))
                
                self.refffdatnmblst.append(int(datnmb)-1)
            
            if makelst: self.SetFFSelectItem()
            #if len(self.refffdatnmblst) > 0:
            #self.lstprm.Select(0,1) # data #, 1=on
            #self.OnRefFFDataSelected(0)
            #self.DispAtmTypDescription([])
                                
        elif self.curterm == 'torsion':
            #print 'termdic[torsion]',termdic['torsion']

            #for datnmb,cls1,cls2,cls3,cls4 in termdic['torsion']:
            nq=0
            for i in range(len(termdic['torsion'])):
                item=termdic['torsion'][i]; n=len(item)
                datnmb=item[0]

                cls1=item[1]; cls2=item[2]; cls3=item[3]; cls4=item[4]

                nam1,elm1,vale1=self.refff.FindAtmNamAtmicVale(cls1)
                nam2,elm2,vale2=self.refff.FindAtmNamAtmicVale(cls2)
                nam3,elm3,vale3=self.refff.FindAtmNamAtmicVale(cls3)
                nam4,elm4,vale4=self.refff.FindAtmNamAtmicVale(cls4)

                #text=elm1+'.'+vale1+'('+cls1+')-'+elm2+'.'+vale2+'('+cls2+')-'
                #text=text+elm3+'.'+vale3+'('+cls3+')-'+elm4+'.'+vale4+'('+cls4+')'
                text=elm1+'.'+vale1+'-'+elm2+'.'+vale2+'-'
                text=text+elm3+'.'+vale3+'-'+elm4+'.'+vale4
                ctext=text

                # keep current dispalied data number
                if n >= 6:
                    for j in range(5,n,3):
                        ctext=ctext+'/'+item[j]+'/'+item[j+1]+'/'+item[j+2]
                    
                if uniqdic.has_key(ctext): continue
                else:
                    nq +=1; uniqdic[ctext]=datnmb
                
                lst=[elm1,vale1,elm2,vale2,elm3,vale3,elm4,vale4]
                if makelst: self.ffcurlistlst.append(lst)
                if not makelst and not self.IsFFSelected(lst): continue
               
                index=self.lstprm.InsertStringItem(sys.maxint,datnmb) #str(nq))                
                self.lstprm.SetStringItem(index,1,text)                
                ii=1
                if n >= 6:
                    for j in range(5,n,3):   
                        ii += 1; self.lstprm.SetStringItem(index,ii,item[j])
                        ii += 1; self.lstprm.SetStringItem(index,ii,item[j+1]+'/'+item[j+2])
                
                self.refffdatnmblst.append(int(datnmb)-1)

                
            if makelst: self.SetFFSelectItem()
            
            # select the first data
            #if len(self.refffdatnmblst) > 0:
        self.lstprm.Select(0,1) # data #, 1=on
        self.OnRefFFDataSelected(0)
        #self.DispAtmTypDescription([])
                                        
    def DispAtmTypDescription(self,descri):
        try:
            self.reftc.Clear()
            if len(descri) <= 0: return
    
            sa=[]
            sa.append("Remarks of Atmtyp\n-------------\n")
            #if len(descri) <= 0: return
            for s in descri: sa.append(s+"\n")
            text="".join(sa)
            self.reftc.AppendText(text)
        except: pass
    
    def SetForceField(self):
        self.cmbff.SetItems(self.ffnamelst)
    
    def OnRefFFChoice(self,event):
        self.refffname=self.cmbff.GetStringSelection()
        self.fffile=self.fffiledic[self.refffname]
        #if self.refffname[0:5] == 'AMBER':
        #   self.ckbffcls.Enable()
        #    self.ckbffcls.SetValue(self.refffuniqcls)
        #else: self.ckbffcls.Disable()
        # atmtyplst.append([typnmb,atmnam,coment,elm,mass,valence])
        #self.refatmtyplst=lib.ReadTinkerAtomType(self.refffname,self.fffile)
        self.refff=ForceField(self.refffname,self.fffile)
        self.refff.ReadFFPotTerms()

        #if self.refffname[0:5] == 'AMBER' and self.refffuniqcls:
        #    self.refff.MakeUniqClassTerms(True)

        self.refatmtyplst=self.refff.GetFFAtmTypList()
        #print 'refatmtyplst',self.refatmtyplst        
        self.MakeClassDescriDic()
        self.AtmTypeDatNumDic()
        
        if self.ffselectitemauto: self.SetSelectItemForFF()
        else: self.ffselectitem='all'
             
        self.ListItemsInRefFFLC(True)
        ###self.ListItemsInRefFFLC(False)
        #self.ffgrp='all'
        #self.SetFFGroupLst()
        self.pramdat=[-1]+6*['']
        self.SetParamDataInTC()
        #self.ffelm='all'
        #self.SetFFElementLst()
        #self.ffcls='all'
        #self.SetFFAtmClassList()
        
        #self.ListFFAtomTypes()
    def MakeClassDescriDic(self):
        self.classdescridic={}
        refatmtyplst=self.refff.GetFFAtmTypList()
        for datnmb,typnmb,clsnmb,atmnam,elm,mass,valence,coment in refatmtyplst:
            self.classdescridic[clsnmb]=coment        
    
    def AtmTypeDatNumDic(self):
        self.atmtypdatnmbdic={}
        for i in range(len(self.refatmtyplst)):
            atmtypnmb=self.refatmtyplst[i][0]
            self.atmtypdatnmbdic[int(atmtypnmb)]=i
    
    def ExecANALYZE(self):
        if not os.path.exists(self.xyzfile):
            mess="Not found xyz file. Please assingn atmtyp before calling this routine."
            lib.MessageBoxOK(mess,"")
            return
        self.prmfile=self.xyz.replace('.xyz','prm')
        if os.path.exists(self.keyfile): os.remove(self.keyfile)
        
        self.anlfile=self.xyzfile.replace('.xyz','.anl')
        
        self.ReadAnalyzeFile(self.anlfile)
        print 'atom',self.atom
        print 'vdw',self.vdw
        print 'bond',self.bond
        print 'angle',self.angle
        print 'imptors',self.imptors
        print 'torsion',self.torsion
        print 'charge',self.charge
        
        self.WriteTinkerPrmFile(self.prmfile,False)
        
        self.parent.ExecTinkerAnalyze()

        """
        jobid="analyze"
        self.exeprgwin.ExecuteProgram(jobid,prg,arg,plt,wrkdir,self.anlfile)
        """
    def XXReadAnalyzeFile(self,anlfile):
        self.pottermdic={}
        # AMBER FF case
        keywdlst=['Atom Tyep Definition Parameters :',
                  'Van der Waals Parameters :',
                  'Bond Stretching Parameters :',
                  'Angle Bending Parameters :',
                  'Improper Torsion Parameters :',
                  'Torsional Angle Parameters :',
                  'Atomic Partial Charge Parameters :']
        self.termlst=[]
        #
        f=open(anlfile,"r")
        for s in f.readline():
            if s.startswith(keywdlst[0],1,34):
                self.atom=self.ReadAtom(f)
                if len(self.atom) > 0: self.termlst.append('atom')
            if s.startswith(keywdlst[1],1,27):
                self.vdw=self.ReadParams(f)
                if len(self.vdw) > 0: self.termlst.append('vdw')
            if s.startswith(keywdlst[2],1,29):
                self.bond=self.ReadParams(f)
                if len(self.bond) > 0: self.termlst.append('bond')
            if s.startswith(keywdlst[3],1,27):
                self.angle=self.ReadParams(f)
                if len(self.angle) > 0: self.termlst.append('angle')
            if s.startswith(keywdlst[4],1,30):
                self.imptors=self.ReadParams(f)
                if len(self.imptors) > 0: self.termlst.append('imptors')
            if s.startswith(keywdlst[5],1,29):
                self.torsion=self.ReadTorsion(f)
                if len(self.torsion) > 0: self.termlst.append('torsion')
            if s.startswith(keywdlst[5],1,35):
                self.charge=self.ReadParams(f)
                if len(self.charge) > 0: self.termlst.append('charge')    
        f.close()

        
    def ReadAtom(self,f):
        # format of the output
        #Atom  Symbol  Type  Class  Atomic   Mass  Valence  Description
        # "1     N3     386     20     7    14.010    4     N-Term THR N"
        dat=[]
        # skip three lines
        f.readlines()
        f.readlines()
        f.readlines()
        for s in f.readlines():
            if s == "/n": break
            s1=s[:50]
            s2=s[54:]
            item=s1.split()
            dat.append(item+[s2])
        return dat
        
    def ReadParams(self,f):
        """ vdw"""
        # Atom Number       Size   Epsilon   Size 1-4   Eps 1-4   Reduction
        # 1        1           1.8750    0.1700
        """ bond """
        # Atom Numbers                         KS       Bond
        #1        1     2                      367.000    1.4710
        """ angle """
        #Atom Numbers                      KB      Angle   Fold    Type
        #1        2     1     5                 50.000   109.500
        """ imptors """
        # Atom Numbers           Amplitude, Phase and Periodicity^
        # 1        2    17     3     4              10.500   180.0   2
        """ charge """
        # Atom Number             Charge
        #1        1                   0.1812

        dat=[]
        f.readlines(); f.readlines(); f.readlines()
        for s in f.readlines():
            if s == "/n": break
            item=s.split(); dat.append(item)
        return dat
    
    def ReadTorsion(self,f):
        """ torsion """
        #Atom Numbers           Amplitude, Phase and Periodicity        
        #12        8     2     3     4       0.800   0/1   0.080 180/3
        dat=[]
        f.readlines()
        f.readlines()
        f.readlines()
        for s in f.readlines():
            if s == "/n": break
            item=[]
            tmp=s.split()
            for i in range(len(tmp)):
                ns=tmp[i].find('/')
                if ns >= 0:
                    tmp=tmp.split('/')
                    item.append(tmp[0]); item.append(tmp[1])
                else: item.append(tmp[i])
            dat.append(item)
        
        return dat

    def XXWritePrmFile(self,prmfile):
        print 'termlst',self.termlst
        
        f=open(prmfile,"w")
        f.write("parameters       NONE\n")
        f.write("\n")
        # atmtpe
        """Atom  Symbol  Type  Class  Atomic   Mass  Valence  Description"""
        """1     N3     386     20     7    14.010    4     N-Term THR N"""
        for termnam in self.termlst:
            if termnam == 'atom':    
                for i in range(len(self.atom)):
                    type=self.atom[i][3]; atmnam=self.atom[i][1]; com='"'+self.atom[i][7]+'"'
                    elm=self.atom[i][4]; mass=self.atom[i][5]; vale=self.atom[i][6]
                    text="atom"
                    text=text+"  "+type+"  "+atmnam+"  "+'"'+com+'"  '+elm+"  "+ \
                         mass+"  "+vale
                    f.write(text+"\n")
                f.write("\n")
            if termnam == 'vdw':
                text="vdw"
                for atm,cls,size,epsi in self.vdw:
                    text=text+"  "+cls+"  "+size+"  "+epsi
                    f.write(text+"\n")
                f.write("\n")   
            if termnam == 'bond':
                text="bond"
                for datnmb,atm1,atm2,bondk,bondr in self.bond:
                    cls1=self.atom[int(atm1)-1][1]; cls2=self.atom[int(atm2)-1][1]
                    text=text+"  "+cls1+"  "+cls2+"  "+bondk+"   "+bondr
                    f.write(text+"\n")
                f.write("\n")
            if termnam == "angle":
                text="angle"
                for datnmb,atm1,atm2,atm3,anglek,anglea in self.angle:
                    cls1=self.atom[int(atm1)-1][1]; cls2=self.atom[int(atm2)-1][1]
                    cls3=self.atom[int(atm3)-1][1]
                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+anglek+"   "+anglea
                    f.write(text+"\n")
                f.write("\n")
            if termnam == 'torsion':
                text="torsion"
                for datnmb,atm1,atm2,atm3,atm4,torsk1,torsa1,torsp1,torsk2,torsa2,torsp2, \
                         torsk3,torsa3,torsp3 in self.torsion:
                    cls1=self.atom[int(atm1)-1][1]; cls2=self.atom[int(atm2)-1][1]
                    cls3=self.atom[int(atm3)-1][1]; cls4=self.atom[int(atm4)-1][1]    

                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+cls4+ \
                         "  "+torsk1+"   "+torsa1+"  "+torsk2+"   "+torsa2+"  "+torsk3+"   "+torsa3 
                f.write("\n")
            if termnam == "imptors": # charmm style improper
                text="imptors"
                for datnmb,atm1,atm2,atm3,atm4,torsk1,torsa1 in self.imptors:
                    cls1=self.atom[int(atm1)-1][1]; cls2=self.atom[int(atm2)-1][1]
                    cls3=self.atom[int(atm3)-1][1]; cls4=self.atom[int(atm4)-1][1]    

                    text=text+"  "+cls1+"  "+cls2+"  "+cls3+"  "+cls4+ \
                         "  "+torsk1+"   "+torsa1+"  "+torsk2+"   "+torsa2+"  "+torsk3+"   "+torsa3 
                f.write("\n")
            if termnam == "charge":
                text="charge"
                for datnmb,atm1,chg in self.charge:
                    cls1=self.atom[int(atm1)-1][1]
                    text=text+"  "+cls1+"  "+chg 
                f.write("\n")
        f.close()

    def OnAssignParam(self,event):
        self.SetAtmClsInTinkerAtoms()
        self.WriteTinkerXYZFile(self.xyzfile)
        self.parent.ExecTinkerAnalyze(self.xyzfile,self.ffname)
        # destroy this frame
        self.Destroy()
    
    def SetAtmClsInTinkerAtoms(self):
        # atomterm: [[seq,atomtype,atomclass,atmnam,atomic,mass,vale,""],...]
        # tinkeratoms: [seq,atmnam,xyz,type,con],...]
        atomterm=self.tgtff.pottermdic['atom']
        for i in range(len(self.tinkeratoms)):
            self.tinkeratoms[i][3]=atomterm[i][2]

    
    def WriteTinkerXYZFile(self,xyzfile):
        #   642 crambin
        #     1  N3    17.047000   14.099000    3.625000   124     2     5     6     7
        #
        fi6='%6d'; ff12='%12.6f';
        #mess='Failed to read TINKER xyz file. file='+xyzfile
        blk=' '
        #
        # tinkeratoms: [[seq,atmnam,xyz,type,con],...]
        f=open(xyzfile,'w') 
        # write the first line
        snatm=fi6 % len(self.tinkeratoms)# ; snatm=snatm.rjust(6)
        f.write(snatm+'\n') #+2*blk+self.molname+'\n')
        for seq,atmnam,xyz,type,con in self.tinkeratoms:
            #if atom.elm == 'XX': continue
            s=fi6 % (seq+1)
            #atmnam=atom.atmnam
            #if len(atom.ffatmnam) > 0: atmnam=atom.ffatmnam
            atm=atmnam+4*blk
            s=s+blk+atm[0:4]
            s=s+(ff12 % xyz[0])+(ff12 % xyz[1])+(ff12 % xyz[2])
            s=s+fi6 % type
            #con=atom.conect; con.sort()
            for i in con:
                ii=i+1; s=s+ (fi6 % ii)
            s=s+'\n'
            f.write(s)
        f.close()
        
                
    def CreateCmdPanel(self):
        ###[w,h]=self.panffprm.GetSize()
        
        [w,h]=self.GetClientSize()
        
        # Atom type assignment
        #self.hcmd=80
        #yloc=h-self.hcmd; yloc0=yloc
        xpos=0; ypos=h-self.hcmd
        self.pancmd=wx.Panel(self,-1,pos=(xpos,ypos),size=(w,self.hcmd)) #ysize))
        self.pancmd.SetBackgroundColour("light gray")
        
        yloc=0; xloc=0
        wx.StaticLine(self.pancmd,pos=(xloc,yloc),size=(w,4),style=wx.LI_HORIZONTAL)
        yloc=yloc+8; yloc1=yloc
        #xloc=0 #175
        
        wx.StaticText(self.pancmd,-1,"Parameters:",pos=(xloc+10,yloc+2),size=(70,18)) 
        tclprm0=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+85,yloc),size=(55,20))
        tclprm1=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+145,yloc),size=(55,20))
        tclprm2=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+205,yloc),size=(55,20))
        tclprm3=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+265,yloc),size=(55,20))
        tclprm4=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+325,yloc),size=(55,20))
        tclprm5=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+385,yloc),size=(55,20))
        self.btnprmclr=wx.Button(self.pancmd,wx.ID_ANY,"clear",pos=(xloc+460,yloc),size=(35,22))
        self.tclprm=[tclprm0,tclprm1,tclprm2,tclprm3,tclprm4,tclprm5]
        self.SetParamDataInTC()
        #btntgtall.Bind(wx.EVT_BUTTON,self.pancmd.OnTargetAll)
        yloc=yloc+25; xtgt=220; yloc2=yloc
        wx.StaticText(self.pancmd,-1,"Target data:",pos=(xloc+10,yloc+2),size=(70,18)) 
        self.tcltgt=wx.TextCtrl(self.pancmd,-1,"",pos=(xloc+85,yloc),size=(215,20))
        self.SetTargetDataInTC()
        #btntgtall=wx.Button(self.pancmd,wx.ID_ANY,"all",pos=(140,yloc-2),size=(35,22))
        self.btntgtclr=wx.Button(self.pancmd,wx.ID_ANY,"clear",pos=(xloc+335,yloc),size=(35,22))
        btnbak=wx.Button(self.pancmd,wx.ID_ANY,"back",pos=(xloc+390,yloc),size=(40,22))
        btnbak.Bind(wx.EVT_BUTTON,self.OnSelectItemBack)
        btnnxt=wx.Button(self.pancmd,wx.ID_ANY,"next",pos=(xloc+440,yloc),size=(40,22))
        btnnxt.Bind(wx.EVT_BUTTON,self.OnSelectItemNext)

        self.yloctgtmess=yloc; self.xloctgtmess=xloc+305

        self.btnapl=wx.Button(self.pancmd,wx.ID_ANY,"Apply",pos=(xloc+510,yloc-12),size=(50,22))
        self.btnapl.Bind(wx.EVT_BUTTON,self.OnFFApply)
        self.btnund=wx.Button(self.pancmd,wx.ID_ANY,"Undo",pos=(xloc+570,yloc-12),size=(50,22))
        self.btnund.Bind(wx.EVT_BUTTON,self.OnFFUndo)    

        xloc=w-145
        wx.StaticLine(self.pancmd,pos=(xloc-2,yloc1-5),size=(4,self.hcmd),style=wx.LI_VERTICAL)
        self.btnparam=wx.Button(self.pancmd,wx.ID_ANY,"Go assgin params",pos=(xloc+18,yloc1),size=(115,22))
        self.btnparam.Bind(wx.EVT_BUTTON,self.OnAssignParam)
        
        self.btncancel=wx.Button(self.pancmd,wx.ID_ANY,"Cancel",pos=(xloc+15,yloc2),size=(50,22))
        self.btnfin=wx.Button(self.pancmd,wx.ID_ANY,"Finish",pos=(xloc+85,yloc2),size=(50,22))
        if self.curterm != "atom": self.btnparam.Disable()
        self.btnfin.Bind(wx.EVT_BUTTON,self.OnFinish)
        self.btncancel.Bind(wx.EVT_BUTTON,self.OnCancel)

        #self.SetTargetAtoms([])
        ###yloc=yloc+25     
        ###wx.StaticLine(self.pancmd,pos=(xloc+2,yloc0),size=(2,self.hcmd),style=wx.LI_VERTICAL)
        ###wx.StaticText(self.pancmd,-1,"Show changed in:",pos=(10,yloc1+2),size=(100,18)) 
        ###self.cmbcol=wx.ComboBox(self.pancmd,-1,'',choices=self.colorlst, \
        ###                       pos=(115,yloc1),size=(55,20),style=wx.CB_READONLY)                      

        ###self.btnclrcol=wx.Button(self.pancmd,wx.ID_ANY,"clear color",pos=(10,yloc2),size=(70,22))
        ###self.btnclrprm=wx.Button(self.pancmd,wx.ID_ANY,"clear params",pos=(90,yloc2),size=(80,22))

        
        #self.DispUnassigned()
    def OnCancel(self,event):
        self.Destroy()
        
    def OnFinish(self,event):
        nuasn=0
        for term in self.uterms:        
            nuasn += self.CountUndefinedParams(term)
        if nuasn > 0:
            ans=lib.MessageBoxYesNo("There are undefined paramters. Continue to assign?.","")
            if ans: return
            else:

                prmfile=self.xyzfile.replace('.xyz','.prm')
                print 'finish prmfile',prmfile
                potdic=self.MakePotDicForPrmFile()
                shutil.copy(self.fffile,prmfile) 
                
                self.parent.WriteTinkerPrmFile(prmfile,potdic,True)
                
                #test self.parent.ExecTinkerAnalyze(self.xyzfile,self.ffname)
                
                self.Destroy()
    
    def MakePotDicForPrmFile(self):
        potdic={}
        for term in self.uterms:
            termlst=self.tgtff.pottermdic[term]
            if term == "bond":
                for i in range(len(termlst)):
                    del termlst[i][1:5]
                for i in range(len(termlst)):
                    if termlst[i][3] == "": termlst[i][3]="0.0"
                    if termlst[i][4] == "": termlst[i][4]="1.0"
            if term == "angle":
                for i in range(len(termlst)):
                    del termlst[i][1:7]
                for i in range(len(termlst)):
                    if termlst[i][4] == "": termlst[i][4]="0.0"
                    if termlst[i][5] == "": termlst[i][5]="1.0"

            if term == "torsion":
                for i in range(len(termlst)):
                    del termlst[i][1:9]
                for i in range(len(termlst)):
                    nterm=len(termlst)-1
                    for j in range(4,nterm,2):
                        try:
                            if termlst[i][j] == "":
                                termlst[i][j]="0.0"
                                termlst[i][j+1]="1.0"
                        except: pass
            if term == "imptors":
                for i in range(len(termlst)):
                    del termlst[i][1:9]
                for i in range(len(termlst)):
                    if termlst[i][4] == "": termlst[i][4]="0.0"
                    if termlst[i][5] == "": termlst[i][5]="1.0"

            potdic[term]=termlst
        return potdic

    def OnClose(self,event):
        self.splwin1.Destroy()
        self.pancmd.Destroy()

        self.Destroy()
            
    def OnFFApply(self,event):      
        #if self.ffname == "":
        #    wx.MessageBox("No Force filed specified.","",style=wx.OK|wx.ICON_EXCLAMATION)
        #    return
        if self.tclprm[0].GetValue() == "": return           
        #self.atmtyp=self.tcltyp.GetValue()        
        ###self.changedcolor=self.cmbcol.GetValue()
        self.GetTargetData() 
        #self.batch=True; self.rbtbat.SetValue(True)

        lst=self.targetdic.keys()
        self.lstctrl.Focus(max(lst))




        self.SetParameters()

        
        self.DisplayTitle()
   
        self.paramdat=[-1]+6*[""]
        self.SetParamDataInTC()
        #self.OnTargetClear(0)
        
        #self.DispUnassigned()
        
        #mess=str(self.NumberOfUnassigned())
        #wx.StaticText(self.pantyp,-1,mess,pos=(self.xlocunasgn,self.ylocunasgn),size=(60,18))         
    def SetParamDataInTC(self):
        try:
            for i in range(6): self.tclprm[i].SetValue(self.paramdat[i+1])
        except: pass
    def SetTargetDataInTC(self):
        self.tcltgt.SetValue(self.targetdat) 
            
    def SetParameters(self):
        # get input paramters
        paramnmb=str(int(self.paramdat[0])+1)
        if paramnmb <= 0: return

        self.paramdat=[-1]+6*[""]
        for i in range(6): self.paramdat[i+1]=self.tclprm[i].GetValue()
        if self.paramdat[1] == "" and self.paramdat[2] == "":
            lib.MessageBoxOK("No reference parameters.","")
            return
        #print 'params',self.paramdat
        
        #self.atmtypsav=self.atmtyp
        #self.targetdicsav=self.targetdic
        #self.updateddic={}
        
        targ=self.targetdic.keys()
        #targ.sort()
        #?? test
        if self.curterm == 'atom':
            #print 'targ',targ
            for datnmb in targ:
                self.tgtff.pottermdic['atom'][datnmb-1][2]=int(self.paramdat[1]) # cls
                self.tgtff.pottermdic['atom'][datnmb-1][7]=self.paramdat[2] # descri
            #print 'asgntermdic[atom]',self.tgtff.pottermdic['atom']
        if self.curterm == 'bond':
            for datnmb in targ:
                self.tgtff.pottermdic['bond'][datnmb-1][7]=self.paramdat[1]
                self.tgtff.pottermdic['bond'][datnmb-1][8]=self.paramdat[2]
                self.tgtff.pottermdic['bond'][datnmb-1][9]=self.refffname+' #'+paramnmb
            #print 'bond datnmb',datnmb
        if self.curterm == 'angle':
            #n=len(self.paramdat)    
            for datnmb in targ:
                for j in range(1,3): #len(self.paramdat)):
                    self.tgtff.pottermdic['angle'][datnmb-1][9+j]=self.paramdat[j]
                self.tgtff.pottermdic['angle'][datnmb-1][12]=self.refffname+' #'+paramnmb
        if self.curterm == 'torsion':
            n=len(self.paramdat)
            for datnmb in targ:
                #n=len(self.paramdat)
                for j in range(1,n): #len(self.paramdat)):
                    self.tgtff.pottermdic['torsion'][datnmb-1][12+j]=self.paramdat[j]
                self.tgtff.pottermdic['torsion'][datnmb-1][19]=self.refffname+' #'+paramnmb
        #self.updateddic[i]=True
        
        #for i in range(6): self.tclprm[i].SetValue('')
        #print 'targetdicsav',self.targetdicsav          
        #self.ListAtoms(self.changedcolor)
        
        
        self.ListItemsInAssignLC(False)

        self.paramdat=[-1]+6*[""]
        self.SetParamDataInTC()
       
    def ClearTargetTC(self):
        self.targetdat=""
        self.tcltgt.SetValue(self.targetdat)
        self.targetdic={}
        
    def GetTargetData(self):
        self.targetdic={}
        self.targetdat=self.tcltgt.GetValue()
        targ=lib.StringToInteger(self.targetdat)
        for i in targ: self.targetdic[i]=1
        
    def OnFFUndo(self,event):
        return
        #if self.batch:
        sel=[]
        targ=self.targetdicsav.keys()
        targ.sort()
        for i in targ:
            #ffatmtypold=self.mol.mol[i-1].ffatmtyp
            #print 'i,sav',i,self.targetdicsav[i][0]
            if len(self.targetdicsav[i]) < 3: continue
            self.mol.mol[i-1].ffatmtyp=self.targetdicsav[i][0]
            #ffnameold=self.mol.mol[i-1].ffname
            self.mol.mol[i-1].ffname=self.targetdicsav[i][1]
            #self.targetdicsav[i]=[ffatmtypold,ffnameold]
            self.mol.mol[i-1].ffatmnam=self.targetdicsav[i][2]
            sel.append(i)

        self.ListAtoms('black')
        
        lst=self.targetdicsav.keys()
        maxlst=max(lst)
        

        self.atmtypsav=0
        self.targetdicsav={}

        self.OnTargetClear(0)
        self.SetTargetAtoms(sel)
        
        self.lstprm.Focus(maxlst)    
        
        #self.DispUnassigned()
                    
   
    def OnDataSelected(self,event):
        try:
            nmbs=self.lstctrl.GetSelectedItemCount()
            #print 'dataselec',nmbs
            if nmbs <= 0: return
            sel=[]
            #for i in range(len(self.tgtff.pottermdic[self.curterm])):
            #self.datnmblst=[]
            for i in range(len(self.datnmblst)):
                if self.lstctrl.IsSelected(i): sel.append(self.datnmblst[i])
            self.curdat=sel[0]
            #print 'selecteddata',sel
            
            if self.curterm != 'atom': self.DispChemOnAssignTC()
            
            for i in range(len(sel)): sel[i] += 1
            targtxt=lib.IntegersToText(sel)
            self.tcltgt.SetValue(targtxt)
        
            nsel=len(self.datnmblst)
            self.DispNumberOfSelectedTarget(nsel)
        except: pass
    
    def DispNumberOfSelectedTarget(self,nsel):
        wx.StaticText(self.pancmd,-1,str(nsel),pos=(self.xloctgtmess,self.yloctgtmess+2),
                      size=(30,18)) 
        
    def OnRefFFDataSelected(self,event):
        self.paramdat=[0]+6*['']
        self.SetParamDataInTC()
        #self.SetParamters()
        
        #self.SetParamDataInTC()        
        if len(self.refffdatnmblst) <= 0:
            #try: self.DispAtmTypDescription([]) 
            #except: pass
            return
        #self.lstprm.Select(0,1)
        #nmbs=self.lstprm.GetSelectedItemCount()
        inmb=self.lstprm.GetFirstSelected()
        #print 'refffdata selec inum',inmb
        if inmb < 0:
            self.paramdat[0]=-1; return
        
        #intnmb=int(self.lstprm.GetItemText(inmb))
        datnmb=self.refffdatnmblst[inmb]
        #print 'datnmb',datnmb
        #print 'refffdatnmblst',self.refffdatnmblst
        termdic=self.refff.pottermdic
        #intnmb=int(datnmb)-1
        descri=[]
        if self.curterm == 'atom':
            cls=termdic['atom'][datnmb][1]
            com=termdic['atom'][datnmb][7]
            try:
                self.tclprm[0].SetValue(cls)
                self.paramdat[1]=cls
                self.paramdat[2]=com
            except: pass

        #print 'termdic',termdic[self.curterm]
        if self.curterm == 'bond':
            data1=termdic['bond'][datnmb][3]
            data2=termdic['bond'][datnmb][4]
            cls1=termdic['bond'][datnmb][1]
            cls2=termdic['bond'][datnmb][2]
            try:
                self.tclprm[0].SetValue(data1)
                self.tclprm[1].SetValue(data2)
                self.paramdat[1]= data1
                self.paramdat[2]= data2
                self.paramdat[0]=datnmb
            except: pass
            try: descri=[self.classdescridic[cls1],self.classdescridic[cls2]]
            except: descri=[]
        elif self.curterm == 'angle':
            data1=termdic['angle'][datnmb][4]
            data2=termdic['angle'][datnmb][5]
            cls1=termdic['angle'][datnmb][1]
            cls2=termdic['angle'][datnmb][2]
            cls3=termdic['angle'][datnmb][3]
            try:
                self.tclprm[0].SetValue(data1)
                self.tclprm[1].SetValue(data2)        
                self.paramdat[1]= data1
                self.paramdat[2]= data2
                self.paramdat[0]=datnmb
            except: pass
            try:
                descri=[self.classdescridic[cls1],self.classdescridic[cls2], \
                        self.classdescridic[cls3]]
            except: descri=[]
        
        elif self.curterm == 'torsion':
            data1=termdic['torsion'][datnmb][5]
            dataa=termdic['torsion'][datnmb][6]
            datab=termdic['torsion'][datnmb][7]
            data2=dataa+'/'+datab
            ndat1=True
            ndat2=False; ndat3=False
            if len(termdic['torsion'][datnmb]) > 8:
                data3=termdic['torsion'][datnmb][8]
                dataa=termdic['torsion'][datnmb][9]
                datab=termdic['torsion'][datnmb][10]
                data4=dataa+'/'+datab
                ndat2=True
            if len(termdic['torsion'][datnmb]) > 11:
                data5=termdic['torsion'][datnmb][11]
                dataa=termdic['torsion'][datnmb][12]
                datab=termdic['torsion'][datnmb][13]
                data6=dataa+'/'+datab
                ndat3=True
            try:
                if ndat1:
                    self.tclprm[0].SetValue(data1)
                    self.tclprm[1].SetValue(data2)        
                    self.paramdat[1]= data1
                    self.paramdat[2]= data2 
                if ndat2:                        
                    self.tclprm[2].SetValue(data3)
                    self.tclprm[3].SetValue(data4)        
                    self.paramdat[3]= data3
                    self.paramdat[4]= data4 
                if ndat3:
                    self.tclprm[4].SetValue(data5)
                    self.tclprm[5].SetValue(data6)        
                    self.paramdat[5]= data5
                    self.paramdat[6]= data6
            except: pass
            self.paramdat[0]=datnmb 
            
            #print "torsion datnmb",datnmb
            
            cls1=termdic['torsion'][datnmb][1]
            cls2=termdic['torsion'][datnmb][2]
            cls3=termdic['torsion'][datnmb][3]
            cls4=termdic['torsion'][datnmb][4]
            try:
                descri=[self.classdescridic[cls1],self.classdescridic[cls2], \
                        self.classdescridic[cls3],self.classdescridic[cls4]]
            except: descri=[]
        

        self.SetParamDataInTC()
        
        #try:
        #    self.tclprm[0].SetValue(data1)
        #    self.tclprm[1].SetValue(data2)        
        #except: pass
        try: self.DispAtmTypDescription(descri) 
        except: pass
               
    def DispChemOnAssignTC(self):
        try:
            self.asgntxt.Clear()
            if self.curdat < 0: return
            #
            if self.curterm == 'bond': self.DispChemBond()
            if self.curterm == 'angle': self.DispChemAngle()
            if self.curterm == 'torsion': self.DispChemTorsion()
        except: pass
    
    def FormatChem(self,frame,bonded):
        """ frame atom ['C'], bonded in lsit ["ch3","nh","oh","h"]
            frame bond ['C','O'], bonded [['ch3','oh','h'],['nh','oh']]
                  oh          ho nh
        makes ch3-C-nh     ch3-C-O-oh  bond C-C-C angle C-C-O C-C-C-O torsion
                  h            h h  
        """
        pass
    
    def DispChemBond(self):
        datnmb=self.tgtff.pottermdic['bond'][self.curdat][0]
        nam1=self.tgtff.pottermdic['bond'][self.curdat][2]
        nam2=self.tgtff.pottermdic['bond'][self.curdat][4]
        cls1=self.tgtff.pottermdic['bond'][self.curdat][5]
        cls2=self.tgtff.pottermdic['bond'][self.curdat][6]
        sa=[]
        sa.append('data no.'+str(datnmb)+'\n')
        sa.append('\n')
        sa.append('\n')
        sa.append('(H3C)-'+nam1+'--'+nam2+'-(CH3)'+'\n')
        sa.append('\n')
        sa.append('\n')
        sa.append(' '+cls1+','+cls2+'\n')
        text="".join(sa)
        self.asgntxt.AppendText(text)
        
    def DispChemAngle(self):
        sa=[]
        sa.append('\n')
        sa.append('        C '+'\n')
        sa.append('        | '+'\n')
        sa.append('(H3)-C--C--C-(H3)'+'\n')
        sa.append('        | '+'\n')
        sa.append('        N '+'\n')
        sa.append('71,72,73'+'\n')
        text="".join(sa)
        self.asgntxt.AppendText(text)

    def DispChemTorsion(self):
        sa=[]
        sa.append('\n')
        sa.append('        C  O'+'\n')
        sa.append('        |  | '+'\n')
        sa.append('(H3)-C--C--C--C-(H3)'+'\n')
        sa.append('        |  |'+'\n')
        sa.append('        N  C'+'\n')
        sa.append('71,72,73,76'+'\n')
        text="".join(sa)
        self.asgntxt.AppendText(text)
    
    def SetItemNamesInAssignLC(self):
        # clear all items
        self.lstctrl.DeleteAllColumns()
        if self.curterm != "atom": 
            self.lstctrl.InsertColumn(0,'data',width=50)
            self.lstctrl.InsertColumn(1,'atoms',width=100)
        if self.curterm == "atom":
            self.lstctrl.InsertColumn(0,'atom',width=50)
            self.lstctrl.InsertColumn(1,'atmnam',width=80)
            self.lstctrl.InsertColumn(2,'elm.vale',width=80)
            self.lstctrl.InsertColumn(3,'bonded atoms',width=100)
            self.lstctrl.InsertColumn(4,'class',width=50)
            self.lstctrl.InsertColumn(5,'remark',width=150)
        elif self.curterm == "bond":
            self.lstctrl.InsertColumn(2,'length',width=50)
            self.lstctrl.InsertColumn(3,'elm.vale(class or type)',width=220)
            self.lstctrl.InsertColumn(4,'  k  ',width=60)
            self.lstctrl.InsertColumn(5,'  r  ',width=60)
            self.lstctrl.InsertColumn(6,'remark',width=120)
        elif self.curterm == "angle":
            self.lstctrl.InsertColumn(2,'angle',width=50)
            self.lstctrl.InsertColumn(3,'elm.vale(class or type)',width=220)
            self.lstctrl.InsertColumn(4,'  k  ',width=60)
            self.lstctrl.InsertColumn(5,'  a  ',width=60)
            self.lstctrl.InsertColumn(6,'remark',width=120)
        elif self.curterm == 'torsion':
            self.lstctrl.InsertColumn(2,'angle',width=50)
            self.lstctrl.InsertColumn(3,'elm.vale(class or type)',width=220)
            self.lstctrl.InsertColumn(4,'  k1 ',width=60)
            self.lstctrl.InsertColumn(5,'a1/p1 ',width=60)
            self.lstctrl.InsertColumn(6,'  k2 ',width=60)
            self.lstctrl.InsertColumn(7,'a2/p2 ',width=60)
            self.lstctrl.InsertColumn(8,'  k3 ',width=60)
            self.lstctrl.InsertColumn(9,'a3/p3 ',width=60)
            self.lstctrl.InsertColumn(10,'remark',width=120)
        elif self.curterm == 'imptors':
            self.lstctrl.InsertColumn(2,'abgle',width=50)
            self.lstctrl.InsertColumn(3,'elm.vale(class or type)',width=220)
            self.lstctrl.InsertColumn(4,'  k  ',width=60)
            self.lstctrl.InsertColumn(5,' a/p ',width=60)
                
    def OnListTerm(self,event):
        self.curterm=self.cmbtrm.GetStringSelection()
        #print 'Onterm, curterm',self.curterm
        
        self.ListItemsInAssignLC(True)
        self.ListItemsInRefFFLC(True)
        #self.SetSelPattern()
        self.ListItemsInAssignLC(True)
        #self.SetSelectItem()
        self.pramdat=[-1]+6*['']
        self.SetParamDataInTC()
        
    def ListItemsInAssignLC(self,makelst):
        # makelst: make current listed data list, i.e. self.curlistlst
        self.paramdat=[-1]+6*[""]
        
        self.lstctrl.DeleteAllItems()
        self.SetItemNamesInAssignLC()
        self.datnmblst=[]
        if self.curterm == 'atom': self.ListElmValeClsForAtom(makelst)
        if self.curterm == 'bond': self.ListElmValeClsForBond(makelst)
        if self.curterm == 'angle': self.ListElmValeClsForAngle(makelst)
        if self.curterm == 'torsion': self.ListElmValeClsForTorsion(makelst)
        if self.curterm == 'imptos': self.ListElmValeClsForImptos(makelst)
        nlst=len(self.datnmblst)
        if nlst > 0: self.SetSelectAllItem(1)

    def SetSelectAllItem(self,on):
        # on=1 for select, 0:for deselect
        n=len(self.datnmblst)
        for i in range(n): self.lstctrl.Select(i,on)
        self.lstctrl.Focus(0)

    def ListElmValeClsForAtom(self,makelst):
        if makelst: self.curlistlst=[]
        term=self.tgtff.pottermdic['atom']
        #!!term=self.tgtff.pottermdic['atom']
        #print 'list elmvaleatom term',term
        for seqnmb,type,cls,atmnam,atomic,mass,vale,com in term:
            if self.listlist == 1:
                if cls != 0: continue #"": continue     
            elif self.listlist == 2:
                if cls == 0: continue #"": continue
            textatm=seqnmb+1 #str(atm1+1)+'-'+str(atm2+1)
            elm=const.ElmSbl[int(atomic)].strip() #self.elmvaleclslst[int(datnmb)-1][1]
            textelm=elm+'.'+str(vale)
            
            lst=[elm,str(vale),str(cls)] # cls]
            
            if makelst: self.curlistlst.append(lst)
            
            if not self.IsSelected(lst): continue
                
            index=self.lstctrl.InsertStringItem(sys.maxint,str(seqnmb+1))
            self.lstctrl.SetStringItem(index,1,atmnam)
            self.lstctrl.SetStringItem(index,2,textelm) #str(atm1+1)+'-'+str(atm2+1))
            self.lstctrl.SetStringItem(index,3,"bonded elms") # bonded 
            self.lstctrl.SetStringItem(index,4,str(cls))
            self.lstctrl.SetStringItem(index,5,com)
            self.datnmblst.append(seqnmb)
        
        if makelst: self.SetSelectItem()

    def BondedElm(self,conect):
        elmlst=[]
        for i in conect: elmlst.append(self.mol.mol[i].elm)
        chemlst,formula=lib.ChemFormula(elmlst)
        return formula
          
    def ListElmValeClsForImptors(self,makelst):
        pass
    
    def ListElmValeClsForBond(self,makelst):
        if makelst: self.curlistlst=[]
        #!!term=self.tgtff.pottermdic['bond']
        term=self.tgtff.pottermdic['bond']
        for datnmb,atm1,nam1,atm2,nam2,cls1,cls2,bondk,bondr,remark in term:
            if self.listlist == 1:
                if bondk != "": continue     
            elif self.listlist == 2:
                if bondk == "": continue
            textatm=atm1+'-'+atm2 #str(atm1+1)+'-'+str(atm2+1)
            elm1=self.elmvaleclslst[int(atm1)-1][1]
            elm2=self.elmvaleclslst[int(atm2)-1][1]
            vale1=self.elmvaleclslst[int(atm1)-1][2]
            vale2=self.elmvaleclslst[int(atm2)-1][2]
            textelm=elm1+'.'+vale1+'('+cls1+')-'+elm2+'.'+vale2+'('+cls2+')'
            
            lst=[elm1,vale1,cls1,elm2,vale2,cls2]
            
            if makelst: self.curlistlst.append(lst)
            
            if not self.IsSelected(lst): continue
            bl=self.bondlengthdic[textatm]    
            index=self.lstctrl.InsertStringItem(sys.maxint,datnmb)
            self.lstctrl.SetStringItem(index,1,textatm)
            self.lstctrl.SetStringItem(index,2,bl)
            self.lstctrl.SetStringItem(index,3,textelm) #str(atm1+1)+'-'+str(atm2+1))
            self.lstctrl.SetStringItem(index,4,bondk)
            self.lstctrl.SetStringItem(index,5,bondr)
            self.lstctrl.SetStringItem(index,6,remark)
            self.datnmblst.append(int(datnmb)-1)
        if makelst: self.SetSelectItem()
    
    def ListElmValeClsForAngle(self,makelst):
        if makelst: self.curlistlst=[]
        #!!term=self.tgtff.pottermdic['angle']
        term=self.tgtff.pottermdic['angle']
        for datnmb,atm1,nam1,atm2,nam2,atm3,nam3,cls1,cls2,cls3,anglek,anglea,remark in term:
            if self.listlist == 1:
                if anglek != "": continue     
            elif self.listlist == 2:
                if anglek == "": continue
            elm1=self.elmvaleclslst[int(atm1)-1][1]
            elm2=self.elmvaleclslst[int(atm2)-1][1]
            elm3=self.elmvaleclslst[int(atm3)-1][1]
            vale1=self.elmvaleclslst[int(atm1)-1][2]
            vale2=self.elmvaleclslst[int(atm2)-1][2]
            vale3=self.elmvaleclslst[int(atm3)-1][2]
            text=elm1+'.'+vale1+'('+cls1+')-'+elm2+'.'+vale2+'('+cls2+')-'
            text=text+elm3+'.'+vale3+'('+cls3+')'
            #angatm=str(int(atm1)+1)+'-'+str(int(atm2)+1)+'-'+str(int(atm3)+1)
            angatm=atm1+'-'+atm2+'-'+atm3
            lst=[elm1,vale1,cls1,elm2,vale2,cls2,elm3,vale3,cls3]
            
            if makelst: self.curlistlst.append(lst)
 
            if not self.IsSelected(lst): continue
            self.datnmblst.append(int(datnmb)-1)
            ba=self.bendingangledic[angatm]
            index=self.lstctrl.InsertStringItem(sys.maxint,datnmb)
            self.lstctrl.SetStringItem(index,1,angatm) #str(atm1+1)+'-'+str(atm2+1)+'-'+str(atm3+1))
            self.lstctrl.SetStringItem(index,2,ba)
            self.lstctrl.SetStringItem(index,3,text)
            self.lstctrl.SetStringItem(index,4,anglek)
            self.lstctrl.SetStringItem(index,5,anglea)       
            self.lstctrl.SetStringItem(index,6,remark)
        
        if makelst: self.SetSelectItem()
    
    def ListElmValeClsForTorsion(self,makelst):
        if makelst: self.curlistlst=[]
        #!!term=self.tgtff.pottermdic['torsion']
        term=self.tgtff.pottermdic['torsion']
        for datnmb,atm1,nam1,atm2,nam2,atm3,nam3,atm4,nam4,cls1,cls2,cls3,cls4, \
                torsk1,torsa1,torsk2,torsa2,torsk3,torsa3,remark in term:
            if self.listlist == 1:
                if torsk1 != "": continue     
            elif self.listlist == 2:
                if torsk1 == "": continue
            elm1=self.elmvaleclslst[int(atm1)-1][1]
            elm2=self.elmvaleclslst[int(atm2)-1][1]
            elm3=self.elmvaleclslst[int(atm3)-1][1]
            elm4=self.elmvaleclslst[int(atm4)-1][1]
            vale1=self.elmvaleclslst[int(atm1)-1][2]
            vale2=self.elmvaleclslst[int(atm2)-1][2]
            vale3=self.elmvaleclslst[int(atm3)-1][2]
            vale4=self.elmvaleclslst[int(atm4)-1][2]
            text=elm1+'.'+vale1+'('+cls1+')-'+elm2+'.'+vale2+'('+cls2+')-'
            text=text+elm3+'.'+vale3+'('+cls3+')-'+elm4+'.'+vale4+'('+cls4+')'
            atmtext=atm1+'-'+atm2+'-'+atm3+'-'+atm4
            lst=[elm1,vale1,cls1,elm2,vale2,cls2,elm3,vale3,cls3,
                                        elm4,vale4,cls4]
            if makelst: self.curlistlst.append(lst)

            if not self.IsSelected(lst): continue
            ta=self.torsionangledic[atmtext]
            index=self.lstctrl.InsertStringItem(sys.maxint,datnmb)
            #self.lstctrl.SetStringItem(index,1,str(atm1+1)+'-'+str(atm2+1)+'-'+str(atm3+1)+'-'+str(atm4+1))
            self.lstctrl.SetStringItem(index,1,atmtext)
            self.lstctrl.SetStringItem(index,2,ta)
            self.lstctrl.SetStringItem(index,3,text)
            self.lstctrl.SetStringItem(index,4,torsk1)
            self.lstctrl.SetStringItem(index,5,torsa1)
            self.lstctrl.SetStringItem(index,6,torsk2)
            self.lstctrl.SetStringItem(index,7,torsa2)
            self.lstctrl.SetStringItem(index,8,torsk3)
            self.lstctrl.SetStringItem(index,9,torsa3)
            self.lstctrl.SetStringItem(index,10,remark)
            self.datnmblst.append(int(datnmb)-1)
        if makelst: self.SetSelectItem()

    def SetSelectItem(self):
        # self.curlistlst=[ [elm1,..elmn,vale1,..valen,cls1,..clsn],,,]
        tmpdic={}
        for i in range(len(self.curlistlst)):
            text=''
            for j in range(0,len(self.curlistlst[i]),3):
                item=self.curlistlst[i]            
                text=self.MakeItemText(item)
            tmpdic[text]=1
        
        selectitemlst=tmpdic.keys()
        #print 'selectitemlst',selectitemlst
        if len(selectitemlst) <= 0: return
        selectitemlst.sort()
        selectitemlst=['all']+selectitemlst
        self.selectitemlst=selectitemlst
        self.selectitemdic={}
        for i in range(len(selectitemlst)):
            self.selectitemdic[selectitemlst[i]]=i
        
        self.cmbsel.Clear()
        self.cmbsel.SetItems(selectitemlst)
        self.selectitem='all'
        self.cmbsel.SetStringSelection(self.selectitem)
    
    def SetFFSelectItem(self):
        # self.curlistlst=[ [elm1,..elmn,vale1,..valen,cls1,..clsn],,,]
        seldic={}
        for i in range(len(self.ffcurlistlst)):
            text=''
            for j in range(0,len(self.ffcurlistlst[i]),3):
                item=self.ffcurlistlst[i]            
                text=self.MakeFFItemText(item)
            seldic[text]=1
        
        selectitemlst=seldic.keys()
        if len(selectitemlst) <= 0: return
        selectitemlst.sort()
        selectitemlst=['all']+selectitemlst
        self.ffselectitemlst=selectitemlst
        self.ffselectitemdic={}
        for i in range(len(selectitemlst)):
            self.ffselectitemdic[selectitemlst[i]]=i
        self.cmbffsel.Clear()
        
        #print 'set ff item itemlst',selectitemlst
        self.cmbffsel.SetItems(selectitemlst)
        
        self.cmbffsel.SetStringSelection(self.ffselectitem)

    def MakeItemText(self,itemlst):
        # lst=[elm1,vale1,cls1,..elmn,valen,clsn], (n=2,3,4 for bond,angle,
        #  torsion,respectively.
        text=''
        for i in range(0,len(itemlst),3):          
            if self.listselform == 0: # elm.vale(cls)
                text=text+itemlst[i]+'.'+itemlst[i+1]+'('+itemlst[i+2]+')'+'-'
            if self.listselform == 1: # elm.vale
                text=text+itemlst[i]+'.'+itemlst[i+1]+'-'
            #if self.listselform == 2: # elm(cls)
            #    text=text+itemlst[i]+'.'+itemlst[i+2]+'-'
            if self.listselform == 2: # elm
                text=text+itemlst[i]+'-'
        n=len(text); text=text[:n-1]
        
        return text
    
    def MakeFFItemText(self,itemlst):
        # lst=[elm1,vale1,cls1,..elmn,valen,clsn], (n=2,3,4 for bond,angle,
        #  torsion,respectively.
        text=''
        for i in range(0,len(itemlst),2):
            if self.fflistselform == 0: # elm.vale
                text=text+itemlst[i]+'.'+itemlst[i+1]+'-'
            if self.fflistselform == 1: # elm
                text=text+itemlst[i]+'-'
        n=len(text); text=text[:n-1]
        #print 'makeffitemtext',text
            
        return text
        
    def IsSelected(self,itemlst):
        #self.selectitem=self.cmbsel.GetStringSelection()
        if self.selectitem == 'all': return True
        itemtext=self.MakeItemText(itemlst)
        if itemtext == self.selectitem: return True
        else: return False
            
    def IsFFSelected(self,itemlst):
        self.ffselectitem=self.cmbffsel.GetStringSelection()
        
        if self.ffselectitem == 'all': return True

        itemtext=self.MakeFFItemText(itemlst)
        if itemtext == self.ffselectitem:
            #print 'itemtext,selctitem',itemtext,self.ffselectitem
            return True
        else: return False
    
    def GetMolElmVale(self):
        elmlst=[]; valelst=[]
        atom=self.tgtff.pottermdic['atom']
        for datnmb,type,cls,atmnam,atomic,mass,vale,com in atom:
            elm=const.ElmSbl[int(atomic)]
            elmlst.append(elm)
            valelst.append(vale)
        return elmlst,valelst
    
    def SetFFTermLst(self):
        #print 'self.uterms in assignff setfftermlst',self.uterms
        self.cmbtrm.SetItems(self.uterms)
        self.cmbtrm.SetValue(self.curterm)
                       
    def ListAtoms(self,col):
        self.lstctrl.DeleteAllItems()
        self.actatm=[]; color=col
        try: len(self.mol.mol)
        except:
            lib.MessageBoxOK("No atoms.","")
            return        
        self.condic={}; self.resdic={}
        #if self.all:
        for atom in self.mol.mol:
            if atom.elm == 'XX': continue
            #if self.typ != 'all' and self.typ != atom.ffatmtyp: continue
            if self.typ == 'unassigned' and atom.ffatmtyp != 0: continue
            if self.typ == 'assigned' and atom.ffatmtyp == 0: continue 
            if self.typ != 'all' and self.typ != 'unassigned' \
                and self.typ != 'assigned' and self.typ != atom.ffatmtyp: continue
            if self.res != 'all' and self.res != atom.resnam: continue
            if self.elm != 'all' and self.elm != atom.elm: continue
            if self.vale != 'all' and len(atom.conect) != self.vale: continue
            scon=self.BondedElm(atom.conect)
            if self.con != 'all' and self.con != scon: continue

            index=self.lstctrl.InsertStringItem(sys.maxint,str(atom.seqnmb+1))
            self.lstctrl.SetStringItem(index,1,atom.elm)
            self.lstctrl.SetStringItem(index,2,atom.resnam+str(atom.resnmb))
            self.lstctrl.SetStringItem(index,3,atom.atmnam)
            self.lstctrl.SetStringItem(index,4,str(len(atom.conect)))
            #scon=self.BondedElm(atom.conect)
            self.lstctrl.SetStringItem(index,5,scon)
            #self.lstctrl.SetStringItem(index,6,str(atom.ffcharge))
            self.lstctrl.SetStringItem(index,6,str(atom.ffatmtyp))
            if self.updateddic.has_key(atom.seqnmb+1): 
                if col == '': color=self.lstctrl.GetItemTextColour(index)
                self.lstctrl.SetItemTextColour(index,color)
            self.lstctrl.SetStringItem(index,7,str(atom.ffname))
            
            self.actatm.append(atom.seqnmb+1)
            
        mess='listed atoms: '+str(len(self.actatm))
        wx.StaticText(self.panlst,-1,mess,pos=(10,self.yloclstmess),size=(120,18)) 
        self.DispUnassigned()
    
    def OnSplitWin1Changed(self,event):
        self.sashposition1=self.splwin1.GetSashPosition()
        print 'sashpositon1',self.sashposition1
        print 'panasgn.size',self.panasgn.GetSize()
        #print 'panunasgn.size',self.panunasgn.GetSize()
        #print 'panffprm.size',self.panffprm.GetSize()
        
        
        self.OnSize(0)

    def OnSize(self,event):
        self.splwin1.Destroy()
        self.pancmd.Destroy()
        
        self.CreateSplitterWindow()
        self.CreateCmdPanel()

    def MenuItems(self):
        # Menu items
        mfil= ("File", (
                  ("Open","Open",0),
                  ("Save","",False),
                  ("Save as","",False),
                  ("Print","Unfinished",0),
                  ("Quit","Close plot panel",0)))
        mtst= ("Test", (
                   ("Do test","test codes",0),))     
        mexe= ("Execute", (
                  ("PDBXYZ","Tinker PDBXYZ program",0),
                  ))
        
        #mprm= ("Set parameter directory", (
        #          ("ff param","",0),
        #          ("ff internal","",0)))
        # msel= ("Select", (
        
        menud=[mfil,mtst,mexe]
        return menud        
    
    def OnMenu(self,event):
        # Menu event handler
        menuid=event.GetId()
        item=self.ffamenu.GetLabel(menuid)
        
        if item == "Open":
            print 'open'

        if item == "Save": #xxx.ffp (force field parameter
            self.prmfile=self.xyzfile.replace('.xyz','.prm')
            self.parent.WriteTinkerPrmFile(self.prmfile,self.tgtff.pottermdic,False)
        if item == "Save as":
            pass
        if item == "Quit":
            self.OnClose(0)
        if item == 'Exec PDBXYZ':
            self.ExecPDBXYZ()

        if item == "Do test":
            print 'Do test'
            filename=self.fffiledic['AMBER99']
            print 'amber file name',filename
            amb99text=ReadAmberParam(filename)
            print 'len amb99text',len(amb99text)
            print '[10]',amb99text[10]
            for i in range(len(amb99text)):
                print amb99text[i]

par=fum.mdlwin
tinopt=TINKEROptimization_Frm(par,-1)
tinopt.Show()
